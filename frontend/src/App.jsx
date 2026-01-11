import { useState, useEffect } from 'react'
import ClaimsTable from './components/ClaimsTable'
import DossierPanel from './components/DossierPanel'
import StatsBar from './components/StatsBar'
import FilterBar from './components/FilterBar'
import FileUpload from './components/FileUpload'
import VisualizationPanel from './components/VisualizationPanel'
import HistoryPanel from './components/HistoryPanel'

function App() {
    const [results, setResults] = useState([])
    const [stats, setStats] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [selectedClaim, setSelectedClaim] = useState(null)
    const [showUpload, setShowUpload] = useState(false)
    const [showHistory, setShowHistory] = useState(false)
    const [showVisualizations, setShowVisualizations] = useState(true)
    const [filters, setFilters] = useState({
        search: '',
        book: '',
        verdict: '',
        character: ''
    })

    // Fetch results on mount
    useEffect(() => {
        fetchResults()
        fetchStats()
    }, [])

    const fetchResults = async () => {
        try {
            setLoading(true)
            const response = await fetch('/api/results')
            if (!response.ok) throw new Error('Failed to fetch results')
            const data = await response.json()
            setResults(data.results || [])
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    const fetchStats = async () => {
        try {
            const response = await fetch('/api/stats')
            if (!response.ok) return
            const data = await response.json()
            setStats(data)
        } catch (err) {
            console.error('Failed to fetch stats:', err)
        }
    }

    // Filter results
    const filteredResults = results.filter(result => {
        const matchesSearch = filters.search === '' ||
            result.id?.toString().includes(filters.search) ||
            result.character?.toLowerCase().includes(filters.search.toLowerCase()) ||
            result.rationale?.toLowerCase().includes(filters.search.toLowerCase())

        const matchesBook = filters.book === '' || result.book_name === filters.book
        const matchesVerdict = filters.verdict === '' || result.verdict === filters.verdict
        const matchesCharacter = filters.character === '' || result.character === filters.character

        return matchesSearch && matchesBook && matchesVerdict && matchesCharacter
    })

    // Get unique values for filters
    const books = [...new Set(results.map(r => r.book_name).filter(Boolean))]
    const characters = [...new Set(results.map(r => r.character).filter(Boolean))]
    const verdicts = [...new Set(results.map(r => r.verdict).filter(Boolean))]

    const handleDownload = () => {
        window.location.href = '/download/results.csv'
    }

    const handleUploadSuccess = (data) => {
        console.log('Upload successful:', data)
        // Optionally refresh results after upload
        fetchResults()
        fetchStats()
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
            {/* Header */}
            <header className="glass border-b border-white/10 sticky top-0 z-40">
                <div className="max-w-7xl mx-auto px-4 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
                                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                            </div>
                            <div>
                                <h1 className="text-xl font-bold text-white">NovelVerified.AI</h1>
                                <p className="text-xs text-gray-400">Claim Verification Dashboard</p>
                            </div>
                        </div>

                        <div className="flex items-center gap-2">
                            {/* Upload Button */}
                            <button
                                onClick={() => setShowUpload(true)}
                                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-green-600 hover:bg-green-500 text-white font-medium transition-colors"
                            >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                                </svg>
                                <span className="hidden sm:inline">Upload Novel</span>
                            </button>

                            {/* Toggle Charts */}
                            <button
                                onClick={() => setShowVisualizations(!showVisualizations)}
                                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${showVisualizations
                                    ? 'bg-purple-600 hover:bg-purple-500 text-white'
                                    : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                                    }`}
                            >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                                </svg>
                                <span className="hidden sm:inline">Charts</span>
                            </button>

                            {/* History Button */}
                            <button
                                onClick={() => setShowHistory(true)}
                                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-medium transition-colors"
                            >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                <span className="hidden sm:inline">History</span>
                            </button>

                            {/* Download Button */}
                            <button
                                onClick={handleDownload}
                                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary-600 hover:bg-primary-500 text-white font-medium transition-colors"
                            >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                </svg>
                                <span className="hidden sm:inline">CSV</span>
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-4 py-6">
                {/* Stats Bar */}
                {stats && <StatsBar stats={stats} />}

                {/* Visualization Panel */}
                {showVisualizations && results.length > 0 && (
                    <VisualizationPanel stats={stats} results={results} />
                )}

                {/* Filter Bar */}
                <FilterBar
                    filters={filters}
                    setFilters={setFilters}
                    books={books}
                    characters={characters}
                    verdicts={verdicts}
                />

                {/* Content Grid */}
                <div className="flex flex-col lg:flex-row gap-6">
                    {/* Claims Table */}
                    <div className={`transition-all duration-300 ${selectedClaim ? 'lg:w-1/2' : 'w-full'}`}>
                        {loading ? (
                            <div className="glass rounded-xl p-8 text-center">
                                <div className="animate-spin w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full mx-auto mb-4"></div>
                                <p className="text-gray-400">Loading results...</p>
                            </div>
                        ) : error ? (
                            <div className="glass rounded-xl p-8 text-center">
                                <div className="w-12 h-12 rounded-full bg-danger-500/20 flex items-center justify-center mx-auto mb-4">
                                    <svg className="w-6 h-6 text-danger-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                </div>
                                <p className="text-danger-500 font-medium mb-2">Error Loading Results</p>
                                <p className="text-gray-400 text-sm">{error}</p>
                                <button
                                    onClick={fetchResults}
                                    className="mt-4 px-4 py-2 rounded-lg bg-primary-600 hover:bg-primary-500 text-white"
                                >
                                    Retry
                                </button>
                            </div>
                        ) : (
                            <ClaimsTable
                                results={filteredResults}
                                selectedId={selectedClaim?.id}
                                onSelect={setSelectedClaim}
                            />
                        )}
                    </div>

                    {/* Dossier Panel */}
                    {selectedClaim && (
                        <div className="lg:w-1/2 animate-slide-in">
                            <DossierPanel
                                claimId={selectedClaim.id}
                                onClose={() => setSelectedClaim(null)}
                            />
                        </div>
                    )}
                </div>
            </main>

            {/* Footer */}
            <footer className="border-t border-white/10 mt-12 py-6">
                <div className="max-w-7xl mx-auto px-4 text-center text-gray-500 text-sm">
                    <p>NovelVerified.AI — AI-Powered Novel Claim Verification</p>
                </div>
            </footer>

            {/* Upload Modal */}
            {showUpload && (
                <FileUpload
                    onUploadSuccess={handleUploadSuccess}
                    onClose={() => setShowUpload(false)}
                />
            )}

            {/* History Modal */}
            {showHistory && (
                <HistoryPanel
                    onClose={() => setShowHistory(false)}
                    onSelectRun={(run) => {
                        console.log('Selected run:', run)
                        setShowHistory(false)
                    }}
                />
            )}
        </div>
    )
}

export default App
