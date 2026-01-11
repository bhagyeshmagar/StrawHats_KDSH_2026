"""
Evaluation Script - Compare predictions against training labels.

Usage:
    python scripts/evaluate.py
"""

import csv
import json
from pathlib import Path

# Paths
RESULTS_FILE = Path("output/results.csv")
CLAIMS_FILE = Path("claims/claims.jsonl")


def load_claims_with_labels() -> dict:
    """Load claims that have labels (train set only)."""
    claims = {}
    if CLAIMS_FILE.exists():
        with open(CLAIMS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                claim = json.loads(line.strip())
                if "label" in claim:
                    # Convert label to binary
                    label = 1 if claim["label"] == "consistent" else 0
                    claims[claim["claim_id"]] = label
    return claims


def main():
    print("=" * 60)
    print("EVALUATION - Comparing predictions to labels")
    print("=" * 60)
    
    # Load ground truth
    labels = load_claims_with_labels()
    if not labels:
        print("ERROR: No labeled claims found. Run claim_parser.py first.")
        return
    
    print(f"Found {len(labels)} labeled claims (train set)")
    
    # Load predictions
    if not RESULTS_FILE.exists():
        print(f"ERROR: {RESULTS_FILE} not found. Run the pipeline first.")
        return
    
    predictions = {}
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            predictions[row["id"]] = int(row["prediction"])
    
    print(f"Found {len(predictions)} predictions")
    
    # Calculate metrics
    tp = fp = tn = fn = 0
    correct = 0
    errors = []
    
    for claim_id, label in labels.items():
        if claim_id not in predictions:
            continue
        
        pred = predictions[claim_id]
        
        if pred == label:
            correct += 1
            if label == 1:
                tp += 1
            else:
                tn += 1
        else:
            errors.append((claim_id, label, pred))
            if label == 1:
                fn += 1  # Missed a consistent claim
            else:
                fp += 1  # False positive (predicted consistent but was contradicted)
    
    total = tp + fp + tn + fn
    
    if total == 0:
        print("No overlapping claims between labels and predictions!")
        return
    
    accuracy = correct / total
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    print("\n" + "=" * 40)
    print("RESULTS")
    print("=" * 40)
    print(f"Accuracy:  {accuracy:.2%} ({correct}/{total})")
    print(f"Precision: {precision:.2%}")
    print(f"Recall:    {recall:.2%}")
    print(f"F1 Score:  {f1:.2%}")
    
    print("\nConfusion Matrix:")
    print(f"  True Positives:  {tp}")
    print(f"  True Negatives:  {tn}")
    print(f"  False Positives: {fp}")
    print(f"  False Negatives: {fn}")
    
    if errors:
        print(f"\nErrors ({len(errors)} total):")
        for claim_id, label, pred in errors[:10]:  # Show first 10
            label_str = "consistent" if label == 1 else "contradict"
            pred_str = "consistent" if pred == 1 else "contradict"
            print(f"  {claim_id}: expected {label_str}, got {pred_str}")
        
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")


if __name__ == "__main__":
    main()
