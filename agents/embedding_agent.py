"""
Embedding Agent - Creates FAISS index from chunked novel text.

Loads chunks from chunks/chunks.jsonl, embeds using SentenceTransformers,
and saves FAISS index to index/faiss.index with metadata in index/meta.pkl.
"""

import json
import pickle
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from tqdm import tqdm

# Configuration
INPUT_FILE = Path("chunks/chunks.jsonl")
INDEX_DIR = Path("index")
FAISS_INDEX_FILE = INDEX_DIR / "faiss.index"
META_FILE = INDEX_DIR / "meta.pkl"
MODEL_NAME = "all-MiniLM-L6-v2"
BATCH_SIZE = 64


def load_chunks() -> list[dict]:
    """Load chunks from JSONL file."""
    chunks = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line.strip()))
    return chunks


def create_embeddings(chunks: list[dict], model: SentenceTransformer) -> np.ndarray:
    """Create embeddings for all chunks."""
    texts = [c["text"] for c in chunks]
    
    print(f"Creating embeddings for {len(texts)} chunks...")
    
    # Process in batches with progress bar
    embeddings = []
    for i in tqdm(range(0, len(texts), BATCH_SIZE), desc="Embedding"):
        batch = texts[i:i + BATCH_SIZE]
        batch_embeddings = model.encode(batch, show_progress_bar=False)
        embeddings.append(batch_embeddings)
    
    return np.vstack(embeddings).astype(np.float32)


def build_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatIP:
    """Build FAISS index for cosine similarity search."""
    # Normalize embeddings for cosine similarity
    faiss.normalize_L2(embeddings)
    
    # Create index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # Inner product = cosine sim after normalization
    index.add(embeddings)
    
    return index


def create_metadata(chunks: list[dict]) -> list[dict]:
    """Create metadata list for chunks."""
    return [
        {
            "book": c["book"],
            "chunk_idx": c["chunk_idx"],
            "char_start": c["char_start"],
            "char_end": c["char_end"],
            "text": c["text"]  # Store text for easy retrieval
        }
        for c in chunks
    ]


def main():
    """Main entry point for embedding agent."""
    print("=" * 60)
    print("EMBEDDING AGENT - FAISS Index Creation")
    print("=" * 60)
    
    # Check input file exists
    if not INPUT_FILE.exists():
        print(f"ERROR: {INPUT_FILE} not found. Run ingestion_agent.py first.")
        return
    
    # Load chunks
    chunks = load_chunks()
    print(f"Loaded {len(chunks)} chunks")
    
    # Load model
    print(f"Loading model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    
    # Create embeddings
    embeddings = create_embeddings(chunks, model)
    print(f"Embeddings shape: {embeddings.shape}")
    
    # Build FAISS index
    print("Building FAISS index...")
    index = build_faiss_index(embeddings)
    
    # Create metadata
    metadata = create_metadata(chunks)
    
    # Save everything
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    
    faiss.write_index(index, str(FAISS_INDEX_FILE))
    print(f"Saved FAISS index to {FAISS_INDEX_FILE}")
    
    with open(META_FILE, "wb") as f:
        pickle.dump(metadata, f)
    print(f"Saved metadata to {META_FILE}")
    
    print("=" * 60)
    print(f"Index ready! {index.ntotal} vectors indexed.")


if __name__ == "__main__":
    main()
