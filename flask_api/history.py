"""
History Management API for NovelVerified.AI

Manages pipeline run history - saves each run with metadata for comparison.
Supports comparing Claude API vs Local Ollama model results.
"""

import json
import shutil
import os
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)

history_bp = Blueprint('history', __name__)

PROJECT_ROOT = Path(__file__).parent.parent
HISTORY_DIR = PROJECT_ROOT / "history"
RUNS_FILE = HISTORY_DIR / "runs.json"

# Ensure history directory exists
HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def load_runs():
    """Load runs metadata from JSON file."""
    if not RUNS_FILE.exists():
        return []
    try:
        with open(RUNS_FILE, 'r') as f:
            return json.load(f)
    except:
        return []


def save_runs(runs):
    """Save runs metadata to JSON file."""
    with open(RUNS_FILE, 'w') as f:
        json.dump(runs, f, indent=2, default=str)


def get_current_stats():
    """Get stats from current results.csv."""
    results_file = PROJECT_ROOT / "output" / "results.csv"
    if not results_file.exists():
        return None
    
    import csv
    stats = {
        'total': 0,
        'supported': 0,
        'contradicted': 0,
        'undetermined': 0,
        'avg_confidence': 0
    }
    
    confidences = []
    with open(results_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stats['total'] += 1
            verdict = row.get('verdict', '').lower()
            if verdict == 'supported':
                stats['supported'] += 1
            elif verdict == 'contradicted':
                stats['contradicted'] += 1
            else:
                stats['undetermined'] += 1
            
            conf = float(row.get('confidence', 0))
            confidences.append(conf)
    
    if confidences:
        stats['avg_confidence'] = round(sum(confidences) / len(confidences) * 100, 1)
    
    return stats


@history_bp.route('/api/runs', methods=['GET'])
def list_runs():
    """List all saved runs."""
    runs = load_runs()
    return jsonify({
        'runs': runs,
        'total': len(runs)
    })


@history_bp.route('/api/runs/save', methods=['POST'])
def save_current_run():
    """
    Save current pipeline results as a new history entry.
    
    Body:
        - model: 'ollama' or 'claude'
        - model_name: specific model name (e.g., 'mistral:7b-instruct-q4_0')
        - novel_name: name of the processed novel
        - notes: optional notes
    """
    data = request.json or {}
    
    # Generate run ID
    timestamp = datetime.now()
    run_id = timestamp.strftime("%Y%m%d_%H%M%S")
    run_dir = HISTORY_DIR / f"run_{run_id}"
    
    # Check if results exist
    results_file = PROJECT_ROOT / "output" / "results.csv"
    if not results_file.exists():
        return jsonify({'error': 'No results to save. Run the pipeline first.'}), 400
    
    try:
        # Create run directory
        run_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy results
        shutil.copy(results_file, run_dir / "results.csv")
        
        # Copy verdicts
        verdicts_src = PROJECT_ROOT / "verdicts"
        if verdicts_src.exists():
            verdicts_dst = run_dir / "verdicts"
            verdicts_dst.mkdir(exist_ok=True)
            for f in verdicts_src.glob("*.json"):
                shutil.copy(f, verdicts_dst / f.name)
        
        # Copy dossiers
        dossiers_src = PROJECT_ROOT / "dossiers"
        if dossiers_src.exists():
            dossiers_dst = run_dir / "dossiers"
            dossiers_dst.mkdir(exist_ok=True)
            for f in dossiers_src.glob("*.md"):
                shutil.copy(f, dossiers_dst / f.name)
        
        # Get stats
        stats = get_current_stats()
        
        # Create run metadata
        run_meta = {
            'id': run_id,
            'timestamp': timestamp.isoformat(),
            'display_time': timestamp.strftime("%b %d, %Y %I:%M %p"),
            'model_type': data.get('model', 'ollama'),
            'model_name': data.get('model_name', 'unknown'),
            'novel_name': data.get('novel_name', 'Unknown Novel'),
            'notes': data.get('notes', ''),
            'stats': stats,
            'path': str(run_dir.relative_to(PROJECT_ROOT))
        }
        
        # Save metadata in run directory
        with open(run_dir / "meta.json", 'w') as f:
            json.dump(run_meta, f, indent=2)
        
        # Update runs list
        runs = load_runs()
        runs.insert(0, run_meta)  # Most recent first
        save_runs(runs)
        
        logger.info(f"Saved run: {run_id}")
        
        return jsonify({
            'success': True,
            'run': run_meta
        })
        
    except Exception as e:
        logger.error(f"Failed to save run: {e}")
        return jsonify({'error': str(e)}), 500


@history_bp.route('/api/runs/<run_id>', methods=['GET'])
def get_run(run_id):
    """Get details for a specific run."""
    runs = load_runs()
    
    run = next((r for r in runs if r['id'] == run_id), None)
    if not run:
        return jsonify({'error': 'Run not found'}), 404
    
    return jsonify(run)


@history_bp.route('/api/runs/<run_id>/results', methods=['GET'])
def get_run_results(run_id):
    """Get results.csv data for a specific run."""
    run_dir = HISTORY_DIR / f"run_{run_id}"
    results_file = run_dir / "results.csv"
    
    if not results_file.exists():
        return jsonify({'error': 'Results not found for this run'}), 404
    
    import csv
    results = []
    with open(results_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['prediction'] = int(row.get('prediction', 0))
            row['confidence'] = float(row.get('confidence', 0))
            results.append(row)
    
    return jsonify({
        'run_id': run_id,
        'total': len(results),
        'results': results
    })


@history_bp.route('/api/runs/<run_id>/dossier/<claim_id>', methods=['GET'])
def get_run_dossier(run_id, claim_id):
    """Get dossier for a claim from a specific run."""
    run_dir = HISTORY_DIR / f"run_{run_id}"
    dossier_file = run_dir / "dossiers" / f"{claim_id}.md"
    
    if not dossier_file.exists():
        return jsonify({'error': 'Dossier not found'}), 404
    
    with open(dossier_file, 'r') as f:
        content = f.read()
    
    return jsonify({
        'run_id': run_id,
        'claim_id': claim_id,
        'content': content
    })


@history_bp.route('/api/runs/<run_id>', methods=['DELETE'])
def delete_run(run_id):
    """Delete a specific run from history."""
    run_dir = HISTORY_DIR / f"run_{run_id}"
    
    if run_dir.exists():
        try:
            shutil.rmtree(run_dir)
        except Exception as e:
            return jsonify({'error': f'Failed to delete: {e}'}), 500
    
    # Update runs list
    runs = load_runs()
    runs = [r for r in runs if r['id'] != run_id]
    save_runs(runs)
    
    return jsonify({'success': True, 'message': f'Deleted run {run_id}'})


@history_bp.route('/api/runs/compare', methods=['POST'])
def compare_runs():
    """
    Compare two runs side by side.
    
    Body:
        - run1_id: First run ID
        - run2_id: Second run ID
    """
    data = request.json or {}
    run1_id = data.get('run1_id')
    run2_id = data.get('run2_id')
    
    if not run1_id or not run2_id:
        return jsonify({'error': 'Both run1_id and run2_id required'}), 400
    
    runs = load_runs()
    run1 = next((r for r in runs if r['id'] == run1_id), None)
    run2 = next((r for r in runs if r['id'] == run2_id), None)
    
    if not run1 or not run2:
        return jsonify({'error': 'One or both runs not found'}), 404
    
    return jsonify({
        'run1': run1,
        'run2': run2,
        'comparison': {
            'supported_diff': (run1['stats']['supported'] - run2['stats']['supported']),
            'contradicted_diff': (run1['stats']['contradicted'] - run2['stats']['contradicted']),
            'confidence_diff': round(run1['stats']['avg_confidence'] - run2['stats']['avg_confidence'], 1)
        }
    })
