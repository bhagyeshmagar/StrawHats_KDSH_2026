import { useState, useEffect } from 'react'

/**
 * HistoryPanel Component
 * 
 * Displays run history with model comparison capabilities.
 * Users can view, compare, and delete previous runs.
 */
export default function HistoryPanel({ onClose, onSelectRun }) {
    const [runs, setRuns] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [selectedRuns, setSelectedRuns] = useState([])
    const [comparing, setComparing] = useState(false)
    const [comparison, setComparison] = useState(null)

    useEffect(() => {
        fetchRuns()
    }, [])

    const fetchRuns = async () => {
        try {
            setLoading(true)
            const response = await fetch('/api/runs')
            if (!response.ok) throw new Error('Failed to fetch history')
            const data = await response.json()
            setRuns(data.runs || [])
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    const saveCurrentRun = async () => {
        try {
            const response = await fetch('/api/runs/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    model: 'ollama',
                    model_name: 'mistral:7b-instruct-q4_0',
                    novel_name: 'Current Run'
                })
            })
            if (!response.ok) throw new Error('Failed to save run')
            fetchRuns()
        } catch (err) {
            alert(err.message)
        }
    }

    const handleDeleteRun = async (runId) => {
        if (!confirm('Delete this run from history?')) return

        try {
            const response = await fetch(`/api/runs/${runId}`, { method: 'DELETE' })
            if (!response.ok) throw new Error('Failed to delete')
            setRuns(runs.filter(r => r.id !== runId))
        } catch (err) {
            alert(err.message)
        }
    }

    const toggleRunSelection = (runId) => {
        if (selectedRuns.includes(runId)) {
            setSelectedRuns(selectedRuns.filter(id => id !== runId))
        } else if (selectedRuns.length < 2) {
            setSelectedRuns([...selectedRuns, runId])
        }
    }

    const handleCompare = async () => {
        if (selectedRuns.length !== 2) return

        setComparing(true)
        try {
            const response = await fetch('/api/runs/compare', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    run1_id: selectedRuns[0],
                    run2_id: selectedRuns[1]
                })
            })
            if (!response.ok) throw new Error('Comparison failed')
            const data = await response.json()
            setComparison(data)
        } catch (err) {
            alert(err.message)
        } finally {
            setComparing(false)
        }
    }

    const getModelBadge = (run) => {
        const isLocal = run.model_type === 'ollama'
        return (
            <span className={`
                px-2 py-0.5 rounded-full text-xs font-medium
                ${isLocal ? 'bg-green-500/20 text-green-400' : 'bg-purple-500/20 text-purple-400'}
            `}>
                {isLocal ? '🖥️ Local' : '🤖 Claude'}
            </span>
        )
    }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="bg-gray-800 rounded-2xl w-full max-w-2xl mx-4 shadow-2xl border border-gray-700 max-h-[85vh] flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-gray-700">
                    <div>
                        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                            <svg className="w-5 h-5 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            Run History
                        </h2>
                        <p className="text-xs text-gray-400 mt-1">Compare model accuracy across runs</p>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-gray-700 rounded-lg transition-colors">
                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                {/* Actions Bar */}
                <div className="flex items-center gap-3 p-4 border-b border-gray-700">
                    <button
                        onClick={saveCurrentRun}
                        className="px-3 py-1.5 rounded-lg bg-green-600 hover:bg-green-500 text-white text-sm font-medium flex items-center gap-2"
                    >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
                        </svg>
                        Save Current
                    </button>

                    {selectedRuns.length === 2 && (
                        <button
                            onClick={handleCompare}
                            disabled={comparing}
                            className="px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-sm font-medium flex items-center gap-2"
                        >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                            </svg>
                            Compare Selected
                        </button>
                    )}

                    {selectedRuns.length > 0 && (
                        <button
                            onClick={() => setSelectedRuns([])}
                            className="px-3 py-1.5 rounded-lg text-gray-400 hover:text-white text-sm"
                        >
                            Clear Selection
                        </button>
                    )}

                    <span className="text-gray-500 text-sm ml-auto">
                        {selectedRuns.length}/2 selected for comparison
                    </span>
                </div>

                {/* Comparison View */}
                {comparison && (
                    <div className="p-4 bg-purple-500/10 border-b border-purple-500/30">
                        <div className="flex items-center justify-between mb-3">
                            <h3 className="text-purple-400 font-medium">Comparison Results</h3>
                            <button onClick={() => setComparison(null)} className="text-gray-400 hover:text-white text-sm">
                                Close
                            </button>
                        </div>
                        <div className="grid grid-cols-3 gap-4 text-center">
                            <div>
                                <div className="bg-gray-800 rounded-lg p-3">
                                    <p className="text-xs text-gray-400 mb-1">{comparison.run1.model_type}</p>
                                    <p className="text-2xl font-bold text-white">{comparison.run1.stats?.supported}</p>
                                    <p className="text-xs text-green-400">Supported</p>
                                </div>
                            </div>
                            <div>
                                <div className="bg-gray-800 rounded-lg p-3 border border-purple-500/50">
                                    <p className="text-xs text-gray-400 mb-1">Difference</p>
                                    <p className={`text-2xl font-bold ${comparison.comparison.supported_diff >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                        {comparison.comparison.supported_diff >= 0 ? '+' : ''}{comparison.comparison.supported_diff}
                                    </p>
                                    <p className="text-xs text-gray-400">Supported</p>
                                </div>
                            </div>
                            <div>
                                <div className="bg-gray-800 rounded-lg p-3">
                                    <p className="text-xs text-gray-400 mb-1">{comparison.run2.model_type}</p>
                                    <p className="text-2xl font-bold text-white">{comparison.run2.stats?.supported}</p>
                                    <p className="text-xs text-green-400">Supported</p>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Runs List */}
                <div className="flex-1 overflow-y-auto p-4">
                    {loading ? (
                        <div className="text-center py-8">
                            <div className="animate-spin w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full mx-auto"></div>
                            <p className="text-gray-400 mt-2">Loading history...</p>
                        </div>
                    ) : error ? (
                        <div className="text-center py-8">
                            <p className="text-red-400">{error}</p>
                            <button onClick={fetchRuns} className="mt-2 text-primary-400 hover:underline">Retry</button>
                        </div>
                    ) : runs.length === 0 ? (
                        <div className="text-center py-12">
                            <svg className="w-16 h-16 mx-auto text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <p className="text-gray-400 font-medium">No runs saved yet</p>
                            <p className="text-gray-500 text-sm mt-1">Run the pipeline and save results to history</p>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {runs.map((run) => (
                                <div
                                    key={run.id}
                                    onClick={() => toggleRunSelection(run.id)}
                                    className={`
                                        p-4 rounded-xl border-2 cursor-pointer transition-all
                                        ${selectedRuns.includes(run.id)
                                            ? 'border-purple-500 bg-purple-500/10'
                                            : 'border-gray-700 hover:border-gray-600 bg-gray-700/30'
                                        }
                                    `}
                                >
                                    <div className="flex items-start justify-between">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2 mb-1">
                                                {getModelBadge(run)}
                                                <span className="text-gray-400 text-xs">{run.display_time}</span>
                                            </div>
                                            <p className="text-white font-medium">{run.novel_name || 'Unknown Novel'}</p>
                                            <p className="text-gray-500 text-xs mt-1">{run.model_name}</p>
                                        </div>

                                        <div className="text-right">
                                            <div className="flex items-center gap-4 text-sm">
                                                <div>
                                                    <span className="text-green-400 font-bold">{run.stats?.supported || 0}</span>
                                                    <span className="text-gray-500 text-xs ml-1">✓</span>
                                                </div>
                                                <div>
                                                    <span className="text-red-400 font-bold">{run.stats?.contradicted || 0}</span>
                                                    <span className="text-gray-500 text-xs ml-1">✗</span>
                                                </div>
                                            </div>
                                            <p className="text-gray-500 text-xs mt-1">
                                                {run.stats?.avg_confidence}% conf
                                            </p>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-2 mt-3 pt-3 border-t border-gray-600">
                                        <button
                                            onClick={(e) => { e.stopPropagation(); onSelectRun?.(run) }}
                                            className="px-3 py-1 rounded-lg bg-primary-600 hover:bg-primary-500 text-white text-xs font-medium"
                                        >
                                            View Results
                                        </button>
                                        <button
                                            onClick={(e) => { e.stopPropagation(); handleDeleteRun(run.id) }}
                                            className="px-3 py-1 rounded-lg text-gray-400 hover:text-red-400 hover:bg-red-500/20 text-xs"
                                        >
                                            Delete
                                        </button>

                                        {selectedRuns.includes(run.id) && (
                                            <span className="ml-auto text-purple-400 text-xs flex items-center gap-1">
                                                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                                </svg>
                                                Selected
                                            </span>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-gray-700">
                    <button
                        onClick={onClose}
                        className="w-full px-4 py-2 rounded-lg border border-gray-600 text-gray-300 hover:bg-gray-700 transition-colors"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    )
}
