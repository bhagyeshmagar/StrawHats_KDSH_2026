"""Tests for the results aggregator agent."""

import sys
import json
from pathlib import Path
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.results_aggregator import load_claims, VERDICT_MAP


class TestVerdictMapping:
    """Tests for verdict to prediction mapping."""
    
    @pytest.mark.unit
    def test_supported_maps_to_one(self):
        """Supported verdict should map to 1."""
        assert VERDICT_MAP["supported"] == 1
    
    @pytest.mark.unit
    def test_contradicted_maps_to_zero(self):
        """Contradicted verdict should map to 0."""
        assert VERDICT_MAP["contradicted"] == 0
    
    @pytest.mark.unit
    def test_undetermined_maps_to_zero(self):
        """Undetermined verdict should map to 0 (conservative)."""
        assert VERDICT_MAP["undetermined"] == 0


class TestLoadClaims:
    """Tests for the load_claims function."""
    
    @pytest.mark.integration
    def test_load_claims_from_file(self, temp_claims_file):
        """Should load claims from JSONL file."""
        # Patch the claims file path
        import agents.results_aggregator as module
        original_path = module.CLAIMS_FILE
        module.CLAIMS_FILE = temp_claims_file
        
        try:
            claims = load_claims()
            assert len(claims) > 0
            assert all("claim_id" in c for c in claims.values())
        finally:
            module.CLAIMS_FILE = original_path
    
    @pytest.mark.unit
    def test_load_claims_returns_dict(self, tmp_path):
        """Should return empty dict if file doesn't exist."""
        import agents.results_aggregator as module
        original_path = module.CLAIMS_FILE
        module.CLAIMS_FILE = tmp_path / "nonexistent.jsonl"
        
        try:
            claims = load_claims()
            assert claims == {}
        finally:
            module.CLAIMS_FILE = original_path
