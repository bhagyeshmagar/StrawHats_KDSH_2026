"""
Retriever Agent - Retrieves relevant novel passages for each claim.

For each claim in claims/claims.jsonl, queries the FAISS index
and saves top evidence to evidence/{claim_id}.json.
"""

import json
import pickle
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

# Configuration
CLAIMS_FILE = Path("claims/claims.jsonl")
FAISS_INDEX_FILE = Path("index/faiss.index")
META_FILE = Path("index/meta.pkl")
OUTPUT_DIR = Path("evidence")
MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K = 6  # Retrieve top 6, filter to top 3
FINAL_K = 3


def load_claims() -> list[dict]:
    """Load claims from JSONL file."""
    claims = []
    with open(CLAIMS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            claims.append(json.loads(line.strip()))
    return claims


def load_index_and_metadata():
    """Load FAISS index and metadata."""
    index = faiss.read_index(str(FAISS_INDEX_FILE))
    with open(META_FILE, "rb") as f:
        metadata = pickle.load(f)
    return index, metadata


def retrieve_evidence(claim: dict, model: SentenceTransformer, 
                      index: faiss.Index, metadata: list[dict]) -> list[dict]:
    """
    Retrieve relevant passages for a claim.
    
    Strategy:
    1. Embed the claim text
    2. Query FAISS for top-K chunks
    3. Prefer chunks from the same book
    4. Return top FINAL_K results
    """
    # Create query embedding
    query_text = f"{claim['character']}: {claim['claim_text']}"
    query_embedding = model.encode([query_text]).astype(np.float32)
    faiss.normalize_L2(query_embedding)
    
    # Search
    scores, indices = index.search(query_embedding, TOP_K * 2)  # Get more for filtering
    
    # Build results
    results = []
    book_name = claim["book_name"]
    
    # Normalize book name for matching
    book_name_lower = book_name.lower().replace(" ", "").replace("_", "")
    
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
            
        meta = metadata[idx]
        
        # Prioritize matching book (boost score)
        meta_book_lower = meta["book"].lower().replace(" ", "").replace("_", "")
        is_same_book = book_name_lower in meta_book_lower or meta_book_lower in book_name_lower
        
        adjusted_score = float(score) + (0.2 if is_same_book else 0)
        
        results.append({
            "chunk_idx": meta["chunk_idx"],
            "book": meta["book"],
            "char_start": meta["char_start"],
            "char_end": meta["char_end"],
            "text": meta["text"],
            "score": adjusted_score,
            "is_same_book": is_same_book
        })
    
    # Sort by adjusted score and take top FINAL_K
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:FINAL_K]


def main():
    """Main entry point for retriever agent."""
    print("=" * 60)
    print("RETRIEVER AGENT - Evidence Retrieval")
    print("=" * 60)
    
    # Check prerequisites
    if not CLAIMS_FILE.exists():
        print(f"ERROR: {CLAIMS_FILE} not found. Run claim_parser.py first.")
        return
    if not FAISS_INDEX_FILE.exists():
        print(f"ERROR: {FAISS_INDEX_FILE} not found. Run embedding_agent.py first.")
        return
    
    # Load everything
    claims = load_claims()
    print(f"Loaded {len(claims)} claims")
    
    print("Loading FAISS index...")
    index, metadata = load_index_and_metadata()
    print(f"Index contains {index.ntotal} vectors")
    
    print(f"Loading model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    
    # Process claims
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"\nRetrieving evidence for {len(claims)} claims...")
    
    for i, claim in enumerate(claims):
        evidence = retrieve_evidence(claim, model, index, metadata)
        
        output = {
            "claim_id": claim["claim_id"],
            "book_name": claim["book_name"],
            "character": claim["character"],
            "claim_text": claim["claim_text"],
            "evidence": evidence
        }
        
        output_file = OUTPUT_DIR / f"{claim['claim_id']}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        if (i + 1) % 20 == 0 or i == len(claims) - 1:
            print(f"  Processed {i + 1}/{len(claims)} claims")
    
    print("=" * 60)
    print(f"Evidence saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
