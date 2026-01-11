"""Tests for the claim parser agent."""

import sys
import csv
from pathlib import Path
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.claim_parser import parse_csv


class TestParseCSV:
    """Tests for the parse_csv function."""
    
    @pytest.mark.unit
    def test_parse_train_csv_with_labels(self, temp_csv_files):
        """Parsing train CSV should include labels."""
        train_file, _ = temp_csv_files
        
        claims = parse_csv(train_file, has_label=True)
        
        assert len(claims) == 2
        assert all("label" in c for c in claims)
        assert all("claim_id" in c for c in claims)
        assert all("book_name" in c for c in claims)
        assert all("character" in c for c in claims)
        assert all("claim_text" in c for c in claims)
    
    @pytest.mark.unit
    def test_parse_test_csv_without_labels(self, temp_csv_files):
        """Parsing test CSV should not include labels."""
        _, test_file = temp_csv_files
        
        claims = parse_csv(test_file, has_label=False)
        
        assert len(claims) == 1
        assert "label" not in claims[0]
    
    @pytest.mark.unit
    def test_source_field_set_correctly(self, temp_csv_files):
        """Source field should match the file stem."""
        train_file, test_file = temp_csv_files
        
        train_claims = parse_csv(train_file, has_label=True)
        test_claims = parse_csv(test_file, has_label=False)
        
        assert all(c["source"] == "train" for c in train_claims)
        assert all(c["source"] == "test" for c in test_claims)
    
    @pytest.mark.unit
    def test_claim_id_preserved(self, temp_csv_files):
        """Claim IDs should be preserved from CSV."""
        train_file, _ = temp_csv_files
        
        claims = parse_csv(train_file, has_label=True)
        
        claim_ids = [c["claim_id"] for c in claims]
        assert "test_001" in claim_ids
        assert "test_002" in claim_ids


class TestClaimParserIntegration:
    """Integration tests for claim parser."""
    
    @pytest.mark.integration
    def test_empty_csv_returns_empty_list(self, tmp_path):
        """Empty CSV (headers only) should return empty list."""
        csv_file = tmp_path / "empty.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "book_name", "char", "caption", "content", "label"])
            writer.writeheader()
        
        claims = parse_csv(csv_file, has_label=True)
        assert claims == []
