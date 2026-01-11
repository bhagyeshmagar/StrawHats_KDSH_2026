import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'

function DossierPanel({ claimId, onClose }) {
    const [content, setContent] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        fetchDossier()
    }, [claimId])

    const fetchDossier = async () => {
        try {
            setLoading(true)
            setError(null)
            const response = await fetch(`/api/dossier/${claimId}`)
            if (!response.ok) throw new Error('Failed to fetch dossier')
            const data = await response.json()
            setContent(data.content)
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="glass rounded-xl overflow-hidden h-[calc(100vh-200px)] flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-white/10 bg-white/5">
                <div className="flex items-center gap-2">
                    <svg className="w-5 h-5 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <h3 className="font-semibold text-white">Dossier: {claimId}</h3>
                </div>
                <button
                    onClick={onClose}
                    className="p-1 rounded-lg hover:bg-white/10 transition-colors"
                >
                    <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4">
                {loading ? (
                    <div className="flex items-center justify-center h-32">
                        <div className="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full"></div>
                    </div>
                ) : error ? (
                    <div className="text-center py-8">
                        <p className="text-danger-500 mb-2">Failed to load dossier</p>
                        <p className="text-gray-400 text-sm">{error}</p>
                        <button
                            onClick={fetchDossier}
                            className="mt-4 px-4 py-2 rounded-lg bg-primary-600 hover:bg-primary-500 text-white text-sm"
                        >
                            Retry
                        </button>
                    </div>
                ) : content ? (
                    <div className="markdown-content">
                        <ReactMarkdown>{content}</ReactMarkdown>
                    </div>
                ) : (
                    <p className="text-gray-400 text-center py-8">No dossier content available.</p>
                )}
            </div>
        </div>
    )
}

export default DossierPanel
