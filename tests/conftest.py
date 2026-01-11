"""
Pytest fixtures and configuration for NovelVerified.AI tests.
"""

import json
import tempfile
import pytest
from pathlib import Path


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_novel_text():
    """Sample novel text for testing chunking and embedding."""
    return """
    Chapter One: The Beginning

    It was the best of times, it was the worst of times. The count stood at the 
    window, gazing out at the Mediterranean sea. His name was Edmond Dantes, and 
    he had been wrongfully imprisoned for fourteen years in the Chateau d'If.
    
    During his imprisonment, he had learned many things from the Abbe Faria, a 
    fellow prisoner who became his mentor. Faria taught him languages, sciences, 
    and the location of a great treasure on the island of Monte Cristo.
    
    Now free, Edmond had transformed himself into the wealthy Count of Monte Cristo.
    His mission was to reward those who had been kind to him and to punish those 
    who had betrayed him. Fernand Mondego, Danglars, and Villefort would all face
    his carefully planned revenge.
    
    Chapter Two: The Return

    The count arrived in Paris with great fanfare. His mysterious origins and 
    immense wealth made him the subject of much speculation among the Parisian
    aristocracy. Mercedes, his former beloved who had married Fernand, recognized
    something familiar in his eyes but could not place it.
    """


@pytest.fixture
def sample_claims():
    """Sample claims data for testing parsing and retrieval."""
    return [
        {
            "claim_id": "test_001",
            "book_name": "The Count of Monte Cristo",
            "character": "Edmond Dantes",
            "claim_text": "Edmond Dantes was imprisoned for fourteen years.",
            "source": "test",
            "label": "consistent"
        },
        {
            "claim_id": "test_002",
            "book_name": "The Count of Monte Cristo",
            "character": "Abbe Faria",
            "claim_text": "Faria was Dantes' mentor in prison.",
            "source": "test",
            "label": "consistent"
        },
        {
            "claim_id": "test_003",
            "book_name": "The Count of Monte Cristo",
            "character": "Mercedes",
            "claim_text": "Mercedes married Edmond Dantes.",
            "source": "test",
            "label": "contradict"
        }
    ]


@pytest.fixture
def sample_chunks():
    """Sample chunked text data."""
    return [
        {
            "chunk_idx": 0,
            "book": "test_novel",
            "char_start": 0,
            "char_end": 500,
            "text": "It was the best of times, it was the worst of times. The count stood at the window.",
            "token_count": 100
        },
        {
            "chunk_idx": 1,
            "book": "test_novel",
            "char_start": 400,
            "char_end": 900,
            "text": "During his imprisonment, he learned many things from the Abbe Faria.",
            "token_count": 100
        }
    ]


@pytest.fixture
def sample_evidence():
    """Sample evidence data for reasoning tests."""
    return {
        "claim_id": "test_001",
        "book_name": "The Count of Monte Cristo",
        "character": "Edmond Dantes",
        "claim_text": "Edmond Dantes was imprisoned for fourteen years.",
        "evidence": [
            {
                "chunk_idx": 0,
                "book": "The Count of Monte Cristo",
                "char_start": 0,
                "char_end": 500,
                "text": "He had been wrongfully imprisoned for fourteen years in the Chateau d'If.",
                "score": 0.92,
                "is_same_book": True
            }
        ]
    }


@pytest.fixture
def sample_verdict():
    """Sample verdict data for dossier and aggregator tests."""
    return {
        "claim_id": "test_001",
        "verdict": "supported",
        "confidence": 0.95,
        "supporting_spans": ["imprisoned for fourteen years"],
        "contradicting_spans": [],
        "reasoning": "The evidence clearly states the protagonist was imprisoned for fourteen years."
    }


# ============================================================================
# Temporary Directory Fixtures
# ============================================================================

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create temporary data directory structure."""
    # Create directories
    (tmp_path / "data" / "novels").mkdir(parents=True)
    (tmp_path / "chunks").mkdir()
    (tmp_path / "index").mkdir()
    (tmp_path / "claims").mkdir()
    (tmp_path / "evidence").mkdir()
    (tmp_path / "verdicts").mkdir()
    (tmp_path / "dossiers").mkdir()
    (tmp_path / "output").mkdir()
    
    return tmp_path


@pytest.fixture
def temp_novel_file(temp_data_dir, sample_novel_text):
    """Create a temporary novel file."""
    novel_file = temp_data_dir / "data" / "novels" / "test_novel.txt"
    novel_file.write_text(sample_novel_text)
    return novel_file


@pytest.fixture
def temp_chunks_file(temp_data_dir, sample_chunks):
    """Create a temporary chunks file."""
    chunks_file = temp_data_dir / "chunks" / "chunks.jsonl"
    with open(chunks_file, "w") as f:
        for chunk in sample_chunks:
            f.write(json.dumps(chunk) + "\n")
    return chunks_file


@pytest.fixture  
def temp_claims_file(temp_data_dir, sample_claims):
    """Create a temporary claims file."""
    claims_file = temp_data_dir / "claims" / "claims.jsonl"
    with open(claims_file, "w") as f:
        for claim in sample_claims:
            f.write(json.dumps(claim) + "\n")
    return claims_file


@pytest.fixture
def temp_csv_files(temp_data_dir, sample_claims):
    """Create temporary train/test CSV files."""
    import csv
    
    train_file = temp_data_dir / "data" / "train.csv"
    test_file = temp_data_dir / "data" / "test.csv"
    
    fieldnames = ["id", "book_name", "char", "caption", "content", "label"]
    
    with open(train_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for claim in sample_claims[:2]:
            writer.writerow({
                "id": claim["claim_id"],
                "book_name": claim["book_name"],
                "char": claim["character"],
                "caption": "",
                "content": claim["claim_text"],
                "label": claim.get("label", "")
            })
    
    with open(test_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "book_name", "char", "caption", "content"])
        writer.writeheader()
        claim = sample_claims[2]
        writer.writerow({
            "id": claim["claim_id"],
            "book_name": claim["book_name"],
            "char": claim["character"],
            "caption": "",
            "content": claim["claim_text"]
        })
    
    return train_file, test_file


# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_claude_response():
    """Mock Claude API response for reasoning tests."""
    return {
        "claim_id": "test_001",
        "verdict": "supported",
        "confidence": 0.95,
        "supporting_spans": ["imprisoned for fourteen years"],
        "contradicting_spans": [],
        "reasoning": "The text confirms the fourteen-year imprisonment."
    }


@pytest.fixture
def mock_anthropic_client(mock_claude_response, mocker):
    """Mock Anthropic client for API tests."""
    mock_response = mocker.MagicMock()
    mock_response.content = [mocker.MagicMock(text=json.dumps(mock_claude_response))]
    
    mock_client = mocker.MagicMock()
    mock_client.messages.create.return_value = mock_response
    
    return mock_client
