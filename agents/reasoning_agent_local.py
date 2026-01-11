"""
Local Reasoning Agent - Uses Ollama for fully local LLM inference.

No external API calls - runs entirely on your machine using Ollama.
Supports GPU acceleration with NVIDIA GPUs.

Requirements:
    1. Install Ollama: curl -fsSL https://ollama.com/install.sh | sh
    2. Pull a model: ollama pull phi3:mini  (or mistral:7b-instruct-q4_0)
    3. Run this script: python agents/reasoning_agent_local.py
"""

import json
import os
import time
import logging
import requests
from pathlib import Path
from dotenv import load_dotenv

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
        logging.FileHandler('reasoning_agent_local.log', mode='a')
    ]
)
logger = logging.getLogger('reasoning_agent_local')

# ============================================================================
# Configuration
# ============================================================================
EVIDENCE_DIR = Path("evidence")
OUTPUT_DIR = Path("verdicts")

# Ollama configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3:mini")  # or "mistral:7b-instruct-q4_0"

# Rate limiting (local is fast, but let's not overload)
RATE_LIMIT_DELAY = 0.1  # seconds between calls

# System prompt for reasoning - strict JSON output
SYSTEM_PROMPT = """You are a strict, precise reasoning assistant. You will output EXACTLY one valid JSON object and nothing else. Do not add text, commentary, or markdown. Use double quotes for strings, no trailing commas, and valid JSON arrays even if empty."""


def build_user_prompt(claim_data: dict) -> str:
    """Build the user prompt with claim and evidence in structured format."""
    evidence = claim_data["evidence"]
    claim_id = claim_data["claim_id"]
    claim_text = claim_data["claim_text"]
    
    # Build evidence sections with full metadata
    evidence_sections = []
    for i, ev in enumerate(evidence, 1):
        text = ev['text'][:1500]  # Shorter for local models
        evidence_sections.append(
            f'Evidence {i}:\n'
            f'BOOK: "{ev["book"]}"\n'
            f'TEXT: "{text}"'
        )
    
    evidence_text = "\n\n".join(evidence_sections)
    num_evidence = len(evidence)
    
    return f'''CLAIM_ID: "{claim_id}"
CLAIM_TEXT: "{claim_text}"

EVIDENCE ({num_evidence} passages):
{evidence_text}

TASK: Decide if CLAIM_TEXT is "supported", "contradicted", or "undetermined" based on evidence.

Return JSON with this exact format:
{{
  "claim_id": "{claim_id}",
  "verdict": "supported" or "contradicted" or "undetermined",
  "confidence": 0.0 to 1.0,
  "supporting_spans": [],
  "contradicting_spans": [],
  "reasoning": "one sentence explanation"
}}

RULES:
1. "supported" = evidence confirms the claim
2. "contradicted" = evidence conflicts with the claim
3. "undetermined" = not enough evidence

Output ONLY the JSON, nothing else.'''


def call_ollama(claim_data: dict) -> dict:
    """Call Ollama API for local inference."""
    user_prompt = build_user_prompt(claim_data)
    claim_id = claim_data["claim_id"]
    
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": f"{SYSTEM_PROMPT}\n\n{user_prompt}",
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Low for consistent JSON
                    "num_predict": 512,  # Enough for our JSON
                    "top_p": 0.9
                }
            },
            timeout=120  # 2 minutes timeout
        )
        
        if response.status_code != 200:
            logger.error(f"Ollama API error: {response.status_code}")
            return create_error_verdict(claim_id, f"Ollama error: {response.status_code}")
        
        result = response.json()
        response_text = result.get("response", "").strip()
        
        # Try to extract JSON from response
        # Handle potential markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        # Parse JSON
        verdict = json.loads(response_text)
        
        # Ensure claim_id is correct
        verdict["claim_id"] = claim_id
        
        # Ensure required fields exist
        if "supporting_spans" not in verdict:
            verdict["supporting_spans"] = []
        if "contradicting_spans" not in verdict:
            verdict["contradicting_spans"] = []
        if "confidence" not in verdict:
            verdict["confidence"] = 0.5
        if "reasoning" not in verdict:
            verdict["reasoning"] = "Local model inference"
            
        return verdict
        
    except json.JSONDecodeError as e:
        logger.warning(f"Claim {claim_id}: Failed to parse JSON: {e}")
        logger.debug(f"Raw response: {response_text[:500] if 'response_text' in locals() else 'N/A'}")
        return create_error_verdict(claim_id, f"JSON parse error: {str(e)}")
        
    except requests.exceptions.ConnectionError:
        logger.error(f"Claim {claim_id}: Cannot connect to Ollama. Is it running?")
        return create_error_verdict(claim_id, "Ollama not running. Start with: ollama serve")
        
    except requests.exceptions.Timeout:
        logger.error(f"Claim {claim_id}: Ollama timeout")
        return create_error_verdict(claim_id, "Ollama timeout - model may be too slow")
        
    except Exception as e:
        logger.error(f"Claim {claim_id}: Unexpected error: {e}")
        return create_error_verdict(claim_id, f"Error: {str(e)}")


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


def check_ollama_status() -> bool:
    """Check if Ollama is running and model is available."""
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        if response.status_code != 200:
            return False
        
        models = response.json().get("models", [])
        model_names = [m.get("name", "") for m in models]
        
        if not any(OLLAMA_MODEL in name for name in model_names):
            logger.warning(f"Model {OLLAMA_MODEL} not found. Available: {model_names}")
            print(f"\n⚠️  Model '{OLLAMA_MODEL}' not found!")
            print(f"   Available models: {model_names}")
            print(f"\n   To install: ollama pull {OLLAMA_MODEL}")
            return False
        
        return True
        
    except requests.exceptions.ConnectionError:
        return False


def main():
    """Main entry point for local reasoning agent."""
    print("=" * 60)
    print("LOCAL REASONING AGENT - Ollama")
    print("=" * 60)
    
    logger.info("Starting local reasoning agent")
    
    # Check Ollama status
    print(f"\nChecking Ollama at {OLLAMA_HOST}...")
    if not check_ollama_status():
        print("\n❌ Ollama is not running or model not found!")
        print("\nSetup instructions:")
        print("  1. Install Ollama:")
        print("     curl -fsSL https://ollama.com/install.sh | sh")
        print(f"\n  2. Pull the model:")
        print(f"     ollama pull {OLLAMA_MODEL}")
        print("\n  3. Start Ollama (if not auto-started):")
        print("     ollama serve")
        print("\n  4. Re-run this script")
        return
    
    print(f"✅ Ollama running with model: {OLLAMA_MODEL}")
    
    # Check evidence directory
    evidence_files = list(EVIDENCE_DIR.glob("*.json"))
    if not evidence_files:
        logger.error(f"No evidence files found in {EVIDENCE_DIR}/")
        print(f"\n❌ No evidence files found in {EVIDENCE_DIR}/")
        print("   Run the retrieval stage first: python agents/retriever_agent.py")
        return
    
    print(f"Found {len(evidence_files)} evidence files")
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check for already processed files (resumable)
    processed = set(f.stem for f in OUTPUT_DIR.glob("*.json"))
    remaining = [f for f in evidence_files if f.stem not in processed]
    
    if processed:
        print(f"  {len(processed)} already processed, {len(remaining)} remaining")
    
    # Process claims
    print(f"\nProcessing {len(remaining)} claims with local LLM...")
    print("(This may take a while depending on your GPU)\n")
    
    stats = {"supported": 0, "contradicted": 0, "undetermined": 0}
    start_time = time.time()
    
    for i, evidence_file in enumerate(remaining):
        with open(evidence_file, "r", encoding="utf-8") as f:
            claim_data = json.load(f)
        
        # Call local LLM
        verdict = call_ollama(claim_data)
        
        # Update stats
        stats[verdict.get("verdict", "undetermined")] += 1
        
        # Save result
        output_file = OUTPUT_DIR / f"{claim_data['claim_id']}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(verdict, f, indent=2, ensure_ascii=False)
        
        # Progress update
        elapsed = time.time() - start_time
        avg_time = elapsed / (i + 1)
        remaining_time = avg_time * (len(remaining) - i - 1)
        
        if (i + 1) % 5 == 0 or i == len(remaining) - 1:
            print(f"  [{i + 1}/{len(remaining)}] {verdict['verdict']} ({verdict.get('confidence', 0):.2f}) "
                  f"- ETA: {remaining_time/60:.1f}min")
        
        time.sleep(RATE_LIMIT_DELAY)
    
    total_time = time.time() - start_time
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Completed in {total_time/60:.1f} minutes")
    print(f"Verdicts saved to {OUTPUT_DIR}/")
    print(f"\nResults:")
    print(f"  ✅ Supported: {stats['supported']}")
    print(f"  ❌ Contradicted: {stats['contradicted']}")
    print(f"  ⚠️  Undetermined: {stats['undetermined']}")
    
    logger.info(f"Completed: {stats}")


if __name__ == "__main__":
    main()
