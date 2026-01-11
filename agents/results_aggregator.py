"""
Results Aggregator Agent - Compiles all verdicts into final results.csv.

Reads all verdicts from verdicts/*.json and generates output/results.csv.
"""

import json
import csv
from pathlib import Path

# Configuration
VERDICTS_DIR = Path("verdicts")
CLAIMS_FILE = Path("claims/claims.jsonl")
OUTPUT_DIR = Path("output")
OUTPUT_FILE = OUTPUT_DIR / "results.csv"

# Verdict to prediction mapping
VERDICT_MAP = {
    "supported": 1,
    "contradicted": 0,
    "undetermined": 0  # Treat as contradicted for binary classification
}


def load_claims() -> dict:
    """Load claims into a dict by claim_id."""
    claims = {}
    if CLAIMS_FILE.exists():
        with open(CLAIMS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                claim = json.loads(line.strip())
                claims[claim["claim_id"]] = claim
    return claims


def main():
    """Main entry point for results aggregator agent."""
    print("=" * 60)
    print("RESULTS AGGREGATOR AGENT - CSV Generation")
    print("=" * 60)
    
    # Check verdicts directory
    verdict_files = list(VERDICTS_DIR.glob("*.json"))
    if not verdict_files:
        print(f"ERROR: No verdict files found in {VERDICTS_DIR}/")
        print("  Run reasoning_agent.py first.")
        return
    
    print(f"Found {len(verdict_files)} verdict files")
    
    # Load claims for additional metadata
    claims = load_claims()
    
    # Collect results
    results = []
    
    for verdict_file in verdict_files:
        with open(verdict_file, "r", encoding="utf-8") as f:
            verdict = json.load(f)
        
        claim_id = verdict["claim_id"]
        claim_data = claims.get(claim_id, {})
        
        # Map verdict to binary prediction
        prediction = VERDICT_MAP.get(verdict["verdict"], 0)
        
        # Create concise rationale
        reasoning = verdict.get("reasoning", "")
        if len(reasoning) > 200:
            reasoning = reasoning[:197] + "..."
        
        results.append({
            "id": claim_id,
            "book_name": claim_data.get("book_name", ""),
            "character": claim_data.get("character", ""),
            "prediction": prediction,
            "verdict": verdict["verdict"],
            "confidence": verdict.get("confidence", 0),
            "rationale": reasoning
        })
    
    # Sort by claim ID (numeric if possible)
    try:
        results.sort(key=lambda x: int(x["id"]))
    except ValueError:
        results.sort(key=lambda x: x["id"])
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Write CSV
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["id", "book_name", "character", "prediction", "verdict", "confidence", "rationale"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\nSaved {len(results)} results to {OUTPUT_FILE}")
    
    # Summary statistics
    print("=" * 60)
    supported = sum(1 for r in results if r["prediction"] == 1)
    contradicted = sum(1 for r in results if r["prediction"] == 0)
    
    print("Summary:")
    print(f"  Total claims: {len(results)}")
    print(f"  Predicted consistent (1): {supported}")
    print(f"  Predicted contradicted (0): {contradicted}")
    
    # Breakdown by verdict type
    verdicts = {}
    for r in results:
        v = r["verdict"]
        verdicts[v] = verdicts.get(v, 0) + 1
    
    print("\nVerdict breakdown:")
    for v, count in sorted(verdicts.items()):
        print(f"  {v}: {count}")
    
    # Average confidence
    avg_conf = sum(r["confidence"] for r in results) / len(results) if results else 0
    print(f"\nAverage confidence: {avg_conf:.2%}")


if __name__ == "__main__":
    main()
