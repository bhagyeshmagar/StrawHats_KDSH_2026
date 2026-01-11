"""Tests for the reasoning agent."""

import sys
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.reasoning_agent import build_user_prompt, call_claude_with_retry


class TestBuildUserPrompt:
    """Tests for the build_user_prompt function."""
    
    @pytest.mark.unit
    def test_includes_claim_id(self, sample_evidence):
        """Prompt should include claim ID."""
        result = build_user_prompt(sample_evidence)
        assert sample_evidence["claim_id"] in result
    
    @pytest.mark.unit
    def test_includes_character(self, sample_evidence):
        """Prompt should include character name."""
        result = build_user_prompt(sample_evidence)
        assert sample_evidence["character"] in result
    
    @pytest.mark.unit
    def test_includes_book_name(self, sample_evidence):
        """Prompt should include book name."""
        result = build_user_prompt(sample_evidence)
        assert sample_evidence["book_name"] in result
    
    @pytest.mark.unit
    def test_includes_claim_text(self, sample_evidence):
        """Prompt should include claim text."""
        result = build_user_prompt(sample_evidence)
        assert sample_evidence["claim_text"] in result
    
    @pytest.mark.unit
    def test_includes_evidence_text(self, sample_evidence):
        """Prompt should include evidence passages."""
        result = build_user_prompt(sample_evidence)
        for ev in sample_evidence["evidence"]:
            # Check partial match since text may be truncated
            assert ev["text"][:50] in result


class TestCallClaude:
    """Tests for the call_claude function."""
    
    @pytest.mark.unit
    def test_returns_valid_verdict_structure(self, sample_evidence):
        """Should return a verdict with all required fields."""
        # Mock the Anthropic client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "claim_id": "test_001",
            "verdict": "supported",
            "confidence": 0.9,
            "supporting_spans": ["test span"],
            "contradicting_spans": [],
            "reasoning": "Test reasoning"
        }))]
        mock_client.messages.create.return_value = mock_response
        
        result = call_claude_with_retry(mock_client, sample_evidence)
        
        assert "claim_id" in result
        assert "verdict" in result
        assert "confidence" in result
        assert "reasoning" in result
    
    @pytest.mark.unit
    def test_handles_json_in_code_block(self, sample_evidence):
        """Should handle JSON wrapped in markdown code blocks."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        # Response with markdown code blocks
        mock_response.content = [MagicMock(text='''```json
{
    "claim_id": "test_001",
    "verdict": "supported",
    "confidence": 0.9,
    "supporting_spans": [],
    "contradicting_spans": [],
    "reasoning": "Test"
}
```''')]
        mock_client.messages.create.return_value = mock_response
        
        result = call_claude_with_retry(mock_client, sample_evidence)
        
        assert result["verdict"] == "supported"
    
    @pytest.mark.unit
    def test_handles_json_parse_error(self, sample_evidence):
        """Should handle JSON parse errors gracefully."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="This is not valid JSON")]
        mock_client.messages.create.return_value = mock_response
        
        result = call_claude_with_retry(mock_client, sample_evidence)
        
        assert result["verdict"] == "undetermined"
        assert result["confidence"] == 0.0
        assert "Failed to parse" in result["reasoning"]
    
    @pytest.mark.unit
    def test_handles_api_error(self, sample_evidence):
        """Should handle API errors gracefully."""
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API Error")
        
        result = call_claude_with_retry(mock_client, sample_evidence)
        
        assert result["verdict"] == "undetermined"
        assert result["confidence"] == 0.0
        assert "error" in result["reasoning"].lower()
    
    @pytest.mark.unit
    def test_preserves_claim_id(self, sample_evidence):
        """Should always set correct claim_id even if Claude returns wrong one."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "claim_id": "wrong_id",
            "verdict": "supported",
            "confidence": 0.9,
            "supporting_spans": [],
            "contradicting_spans": [],
            "reasoning": "Test"
        }))]
        mock_client.messages.create.return_value = mock_response
        
        result = call_claude_with_retry(mock_client, sample_evidence)
        
        # Should use the actual claim_id, not the one from response
        assert result["claim_id"] == sample_evidence["claim_id"]
