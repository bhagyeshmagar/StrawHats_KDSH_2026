"""
Claims Management API for NovelVerified.AI

Manages claims for the current novel - add, list, delete claims.
Claims are stored in data/train.csv for pipeline processing.
"""

import csv
import os
from pathlib import Path
from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)

claims_bp = Blueprint('claims', __name__)

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
TRAIN_CSV = DATA_DIR / "train.csv"
CURRENT_NOVEL_FILE = DATA_DIR / ".current_novel"

CSV_HEADER = ["id", "book_name", "char", "caption", "content", "label"]


def get_current_novel():
    """Get the name of the currently active novel."""
    if CURRENT_NOVEL_FILE.exists():
        return CURRENT_NOVEL_FILE.read_text().strip()
    return None


def set_current_novel(novel_name):
    """Set the currently active novel."""
    CURRENT_NOVEL_FILE.write_text(novel_name)


def get_next_id():
    """Get the next available claim ID."""
    if not TRAIN_CSV.exists():
        return 1
    
    max_id = 0
    with open(TRAIN_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                claim_id = int(row.get('id', 0))
                max_id = max(max_id, claim_id)
            except ValueError:
                pass
    return max_id + 1


def load_claims(novel_filter=None):
    """Load claims, optionally filtered by novel name."""
    if not TRAIN_CSV.exists():
        return []
    
    claims = []
    with open(TRAIN_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if novel_filter is None or row.get('book_name') == novel_filter:
                claims.append(row)
    return claims


def save_claims(claims):
    """Save claims to train.csv."""
    with open(TRAIN_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
        writer.writeheader()
        writer.writerows(claims)


def init_empty_csv():
    """Initialize an empty train.csv with just the header."""
    with open(TRAIN_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
        writer.writeheader()


@claims_bp.route('/api/claims', methods=['GET'])
def list_claims():
    """Get all claims for the current novel."""
    novel = request.args.get('novel') or get_current_novel()
    claims = load_claims(novel)
    
    return jsonify({
        'novel': novel,
        'claims': claims,
        'total': len(claims)
    })


@claims_bp.route('/api/claims', methods=['POST'])
def add_claim():
    """
    Add a new claim.
    
    Body:
        - book_name: Novel name (optional, defaults to current novel)
        - char: Character name
        - caption: Category/topic (optional)
        - content: The claim text
        - label: 'consistent' or 'contradict'
    """
    data = request.json or {}
    
    # Validate required fields
    if not data.get('content'):
        return jsonify({'error': 'content is required'}), 400
    if not data.get('char'):
        return jsonify({'error': 'char (character name) is required'}), 400
    if data.get('label') not in ['consistent', 'contradict']:
        return jsonify({'error': 'label must be consistent or contradict'}), 400
    
    book_name = data.get('book_name') or get_current_novel()
    if not book_name:
        return jsonify({'error': 'No novel specified or set as current'}), 400
    
    # Create new claim
    claim = {
        'id': get_next_id(),
        'book_name': book_name,
        'char': data['char'],
        'caption': data.get('caption', ''),
        'content': data['content'],
        'label': data['label']
    }
    
    # Append to file
    file_exists = TRAIN_CSV.exists()
    with open(TRAIN_CSV, 'a', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
        if not file_exists:
            writer.writeheader()
        writer.writerow(claim)
    
    logger.info(f"Added claim {claim['id']} for {book_name}")
    
    return jsonify({
        'success': True,
        'claim': claim
    }), 201


@claims_bp.route('/api/claims/<int:claim_id>', methods=['DELETE'])
def delete_claim(claim_id):
    """Delete a specific claim by ID."""
    claims = load_claims()
    original_count = len(claims)
    
    claims = [c for c in claims if int(c.get('id', 0)) != claim_id]
    
    if len(claims) == original_count:
        return jsonify({'error': f'Claim {claim_id} not found'}), 404
    
    save_claims(claims)
    
    return jsonify({
        'success': True,
        'message': f'Deleted claim {claim_id}'
    })


@claims_bp.route('/api/claims/clear', methods=['POST'])
def clear_claims():
    """Clear all claims and initialize empty train.csv."""
    init_empty_csv()
    
    return jsonify({
        'success': True,
        'message': 'All claims cleared'
    })


@claims_bp.route('/api/claims/current-novel', methods=['GET'])
def get_current():
    """Get the currently active novel name."""
    novel = get_current_novel()
    return jsonify({'novel': novel})


@claims_bp.route('/api/claims/current-novel', methods=['POST'])
def set_current():
    """Set the currently active novel name."""
    data = request.json or {}
    novel = data.get('novel')
    
    if not novel:
        return jsonify({'error': 'novel name required'}), 400
    
    set_current_novel(novel)
    
    return jsonify({
        'success': True,
        'novel': novel
    })
