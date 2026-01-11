"""
Reasoning Agent - Uses Claude API to verify claims against evidence.

For each claim in evidence/{claim_id}.json, sends to Claude API
and saves verdict to verdicts/{claim_id}.json.

Features:
- Exponential backoff retry on API failures
- Proper logging instead of print statements
- Graceful error handling
"""

import json
import os
import time
import logging
import random
from pathlib import Path
from dotenv import load_dotenv
from anthropic import Anthropic, APIError, RateLimitError, APIConnectionError

# Load environment variables
load_dotenv()

# ============================================================================
# Logging Configuration
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('reasoning_agent.log', mode='a')
    ]
)
logger = logging.getLogger('reasoning_agent')

# ============================================================================
# Configuration
# ============================================================================
EVIDENCE_DIR = Path("evidence")
OUTPUT_DIR = Path("verdicts")
RATE_LIMIT_DELAY = 0.5  # seconds between API calls

# Retry configuration
MAX_RETRIES = 5
BASE_DELAY = 1.0  # Initial delay in seconds
MAX_DELAY = 60.0  # Maximum delay between retries

# Claude configuration
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
API_KEY = os.getenv("ANTHROPIC_API_KEY")

# System prompt for reasoning - strict JSON output
SYSTEM_PROMPT = """You are a strict, precise local reasoning assistant. You will output EXACTLY one valid JSON object and nothing else. Do not add text, commentary, or markdown. Use double quotes for strings, no trailing commas, and valid JSON arrays even if empty."""


def build_user_prompt(claim_data: dict) -> str:
    """Build the user prompt with claim and evidence in structured format."""
    evidence = claim_data["evidence"]
    claim_id = claim_data["claim_id"]
    claim_text = claim_data["claim_text"]
    
    # Build evidence sections with full metadata
    evidence_sections = []
    for i, ev in enumerate(evidence, 1):
        text = ev['text'][:2000]  # Truncate if needed
        evidence_sections.append(
            f'Evidence {i}:\n'
            f'BOOK: "{ev["book"]}"\n'
            f'CHUNK_IDX: {ev["chunk_idx"]}\n'
            f'CHAR_START: {ev.get("char_start", 0)}\n'
            f'CHAR_END: {ev.get("char_end", 0)}\n'
            f'TEXT:\n"""\n{text}\n"""'
        )
    
    evidence_text = "\n\n".join(evidence_sections)
    num_evidence = len(evidence)
    
    return f'''CLAIM_ID: "{claim_id}"
CLAIM_TEXT: "{claim_text}"

EVIDENCE ({num_evidence} passages). Each passage has BOOK, CHUNK_IDX, CHAR_START, CHAR_END, TEXT:
{evidence_text}

TASK:
Based only on the {num_evidence} evidence passages above, decide whether the CLAIM_TEXT is "supported", "contradicted", or "undetermined".

Return a single JSON object with **exactly** the following keys and types:

{{
  "claim_id": "<string>",
  "verdict": "supported" | "contradicted" | "undetermined",
  "confidence": <float>,
  "supporting_spans": [
    {{
      "book": "<string>",
      "chunk_idx": <int>,
      "char_start": <int>,
      "char_end": <int>,
      "text": "<string>"
    }}
  ],
  "contradicting_spans": [
    {{ "book": "...", "chunk_idx": 0, "char_start": 0, "char_end": 0, "text": "..." }}
  ],
  "reasoning": "<one-sentence justification, max 30 words>"
}}

DECISION RULES (must follow):
1. "supported" if evidence contains direct text that entails the claim.
2. "contradicted" if any evidence explicitly negates or makes the claim impossible.
3. Otherwise "undetermined".
4. If both support and contradiction are present, choose "contradicted" only if contradiction is explicit and direct.
5. Confidence should reflect strength: strong entailment/contradiction -> >=0.75; weak signals -> 0.40-0.74; no clear signal -> <=0.39.
6. If unsure, use "undetermined" with confidence <= 0.50.
7. The "reasoning" field must be a single concise sentence citing which evidence.

OUTPUT RULES (strict):
- Produce JSON only. No extra whitespace outside JSON.
- Use empty arrays [] for spans when none apply.
- Strings must be properly escaped and under 400 characters for "reasoning".
- Numeric fields must be numbers (no quotes).'''


def exponential_backoff_delay(attempt: int) -> float:
    """Calculate delay with exponential backoff and jitter."""
    delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
    # Add jitter (±25%)
    jitter = delay * 0.25 * (2 * random.random() - 1)
    return delay + jitter


def call_claude_with_retry(client: Anthropic, claim_data: dict) -> dict:
    """
    Call Claude API with exponential backoff retry logic.
    
    Retries on:
    - Rate limit errors (429)
    - API connection errors
    - Server errors (5xx)
    """
    user_prompt = build_user_prompt(claim_data)
    claim_id = claim_data["claim_id"]
    
    last_error = None
    
    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}]
            )
            
            # Extract response text
            response_text = response.content[0].text.strip()
            
            # Parse JSON (handle potential markdown code blocks)
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                json_lines = [l for l in lines if not l.startswith("```")]
                response_text = "\n".join(json_lines)
            
            verdict = json.loads(response_text)
            
            # Ensure claim_id is correct
            verdict["claim_id"] = claim_id
            
            if attempt > 0:
                logger.info(f"Claim {claim_id}: Succeeded after {attempt + 1} attempts")
            
            return verdict
            
        except RateLimitError as e:
            last_error = e
            delay = exponential_backoff_delay(attempt)
            logger.warning(f"Claim {claim_id}: Rate limited, retrying in {delay:.1f}s (attempt {attempt + 1}/{MAX_RETRIES})")
            time.sleep(delay)
            
        except APIConnectionError as e:
            last_error = e
            delay = exponential_backoff_delay(attempt)
            logger.warning(f"Claim {claim_id}: Connection error, retrying in {delay:.1f}s (attempt {attempt + 1}/{MAX_RETRIES})")
            time.sleep(delay)
            
        except APIError as e:
            # Check if it's a retryable server error (5xx)
            if hasattr(e, 'status_code') and 500 <= e.status_code < 600:
                last_error = e
                delay = exponential_backoff_delay(attempt)
                logger.warning(f"Claim {claim_id}: Server error {e.status_code}, retrying in {delay:.1f}s (attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(delay)
            else:
                # Non-retryable API error (4xx except 429)
                logger.error(f"Claim {claim_id}: API error (non-retryable): {e}")
                return create_error_verdict(claim_id, f"API error: {str(e)}")
                
        except json.JSONDecodeError as e:
            logger.warning(f"Claim {claim_id}: Failed to parse JSON response: {e}")
            return create_error_verdict(claim_id, f"Failed to parse model response: {str(e)}")
            
        except Exception as e:
            logger.error(f"Claim {claim_id}: Unexpected error: {e}")
            return create_error_verdict(claim_id, f"Unexpected error: {str(e)}")
    
    # All retries exhausted
    logger.error(f"Claim {claim_id}: All {MAX_RETRIES} retries exhausted. Last error: {last_error}")
    return create_error_verdict(claim_id, f"Max retries exceeded: {str(last_error)}")


def create_error_verdict(claim_id: str, error_message: str) -> dict:
    """Create a verdict dict for error cases."""
    return {
        "claim_id": claim_id,
        "verdict": "undetermined",
        "confidence": 0.0,
        "supporting_spans": [],
        "contradicting_spans": [],
        "reasoning": error_message
    }


def main():
    """Main entry point for reasoning agent."""
    logger.info("=" * 60)
    logger.info("REASONING AGENT - Claim Verification")
    logger.info("=" * 60)
    
    # Check API key
    if not API_KEY:
        logger.error("ANTHROPIC_API_KEY not set. Create .env file with your API key.")
        print("ERROR: ANTHROPIC_API_KEY not set. Create .env file with your API key.")
        print("  Copy .env.example to .env and add your key.")
        return
    
    # Check evidence directory
    evidence_files = list(EVIDENCE_DIR.glob("*.json"))
    if not evidence_files:
        logger.error(f"No evidence files found in {EVIDENCE_DIR}/")
        print(f"ERROR: No evidence files found in {EVIDENCE_DIR}/")
        print("  Run retriever_agent.py first.")
        return
    
    logger.info(f"Found {len(evidence_files)} evidence files")
    logger.info(f"Using model: {CLAUDE_MODEL}")
    print(f"Found {len(evidence_files)} evidence files")
    print(f"Using model: {CLAUDE_MODEL}")
    
    # Initialize client
    client = Anthropic(api_key=API_KEY)
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check for already processed files (resumable)
    processed = set(f.stem for f in OUTPUT_DIR.glob("*.json"))
    remaining = [f for f in evidence_files if f.stem not in processed]
    
    if processed:
        logger.info(f"{len(processed)} already processed, {len(remaining)} remaining")
        print(f"  {len(processed)} already processed, {len(remaining)} remaining")
    
    # Statistics
    stats = {"supported": 0, "contradicted": 0, "undetermined": 0, "errors": 0}
    
    # Process claims
    logger.info(f"Processing {len(remaining)} claims...")
    print(f"\nProcessing {len(remaining)} claims...")
    
    for i, evidence_file in enumerate(remaining):
        with open(evidence_file, "r", encoding="utf-8") as f:
            claim_data = json.load(f)
        
        # Call Claude with retry
        verdict = call_claude_with_retry(client, claim_data)
        
        # Update stats
        if "error" in verdict.get("reasoning", "").lower() or "retries" in verdict.get("reasoning", "").lower():
            stats["errors"] += 1
        else:
            stats[verdict["verdict"]] = stats.get(verdict["verdict"], 0) + 1
        
        # Save result
        output_file = OUTPUT_DIR / f"{claim_data['claim_id']}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(verdict, f, indent=2, ensure_ascii=False)
        
        # Progress update
        if (i + 1) % 10 == 0 or i == len(remaining) - 1:
            logger.info(f"Processed {i + 1}/{len(remaining)} - Last: {verdict['verdict']} ({verdict.get('confidence', 0):.2f})")
            print(f"  Processed {i + 1}/{len(remaining)} - Last: {verdict['verdict']} ({verdict.get('confidence', 0):.2f})")
        
        # Rate limiting
        if i < len(remaining) - 1:
            time.sleep(RATE_LIMIT_DELAY)
    
    # Summary
    logger.info("=" * 60)
    logger.info(f"Verdicts saved to {OUTPUT_DIR}/")
    print("=" * 60)
    print(f"Verdicts saved to {OUTPUT_DIR}/")
    
    # Load all verdicts for final summary
    verdicts = [json.load(open(f)) for f in OUTPUT_DIR.glob("*.json")]
    supported = sum(1 for v in verdicts if v["verdict"] == "supported")
    contradicted = sum(1 for v in verdicts if v["verdict"] == "contradicted")
    undetermined = sum(1 for v in verdicts if v["verdict"] == "undetermined")
    
    logger.info(f"Summary - Supported: {supported}, Contradicted: {contradicted}, Undetermined: {undetermined}")
    print(f"  Supported: {supported}")
    print(f"  Contradicted: {contradicted}")
    print(f"  Undetermined: {undetermined}")
    
    if stats["errors"] > 0:
        logger.warning(f"Errors encountered: {stats['errors']}")
        print(f"  Errors: {stats['errors']}")


if __name__ == "__main__":
    main()
