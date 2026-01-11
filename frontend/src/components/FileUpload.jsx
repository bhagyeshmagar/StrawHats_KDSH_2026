import { useState, useRef } from 'react'

/**
 * FileUpload Component
 * 
 * Multi-step upload flow:
 * 1. Select file + model
 * 2. Upload (auto-saves previous to history)
 * 3. Add claims for the new novel
 * 4. Run pipeline
 */
export default function FileUpload({ onUploadSuccess, onClose }) {
    const [isDragging, setIsDragging] = useState(false)
    const [file, setFile] = useState(null)
    const [uploading, setUploading] = useState(false)
    const [error, setError] = useState(null)
    const [progress, setProgress] = useState(0)
    const [step, setStep] = useState('upload') // 'upload' | 'processing' | 'claims' | 'done'
    const [uploadResult, setUploadResult] = useState(null)
    const [selectedModel, setSelectedModel] = useState('ollama')
    const [claims, setClaims] = useState([])
    const [newClaim, setNewClaim] = useState({ char: '', content: '', label: 'consistent' })
    const fileInputRef = useRef(null)

    const models = {
        ollama: { id: 'ollama', name: 'Local Ollama', icon: '🖥️' },
        claude: { id: 'claude', name: 'Claude AI', icon: '🤖' }
    }

    const allowedExtensions = ['.pdf', '.docx', '.doc', '.txt']

    const validateFile = (file) => {
        const ext = '.' + file.name.split('.').pop().toLowerCase()
        if (!allowedExtensions.includes(ext)) return `Invalid file type`
        if (file.size > 50 * 1024 * 1024) return 'File too large (max 50MB)'
        return null
    }

    const handleDragOver = (e) => { e.preventDefault(); setIsDragging(true) }
    const handleDragLeave = (e) => { e.preventDefault(); setIsDragging(false) }

    const handleDrop = (e) => {
        e.preventDefault()
        setIsDragging(false)
        const droppedFile = e.dataTransfer.files[0]
        if (droppedFile) {
            const err = validateFile(droppedFile)
            if (err) { setError(err); return }
            setFile(droppedFile)
        }
    }

    const handleFileSelect = (e) => {
        const selectedFile = e.target.files[0]
        if (selectedFile) {
            const err = validateFile(selectedFile)
            if (err) { setError(err); return }
            setFile(selectedFile)
            setError(null)
        }
    }

    const handleUpload = async () => {
        if (!file) return
        setUploading(true)
        setError(null)
        setProgress(20)
        setStep('processing')

        try {
            const formData = new FormData()
            formData.append('file', file)

            setProgress(50)
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            })

            const data = await response.json()
            if (!response.ok) throw new Error(data.error || 'Upload failed')

            setProgress(100)
            setUploadResult(data)
            setStep('claims')  // Move to claims step

        } catch (err) {
            setError(err.message)
            setStep('upload')
            setProgress(0)
        } finally {
            setUploading(false)
        }
    }

    const handleAddClaim = async () => {
        if (!newClaim.char.trim() || !newClaim.content.trim()) {
            setError('Character and claim text are required')
            return
        }

        try {
            const response = await fetch('/api/claims', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    book_name: uploadResult?.book_name,
                    char: newClaim.char,
                    content: newClaim.content,
                    label: newClaim.label
                })
            })

            const data = await response.json()
            if (!response.ok) throw new Error(data.error)

            setClaims([...claims, data.claim])
            setNewClaim({ char: '', content: '', label: 'consistent' })
            setError(null)
        } catch (err) {
            setError(err.message)
        }
    }

    const handleDeleteClaim = async (claimId) => {
        try {
            await fetch(`/api/claims/${claimId}`, { method: 'DELETE' })
            setClaims(claims.filter(c => c.id !== claimId))
        } catch (err) {
            console.error(err)
        }
    }

    const formatFileSize = (bytes) => {
        if (bytes < 1024) return bytes + ' B'
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
    }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="bg-gray-800 rounded-2xl w-full max-w-xl mx-4 shadow-2xl border border-gray-700 max-h-[90vh] flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-gray-700">
                    <h2 className="text-lg font-semibold text-white">
                        {step === 'upload' && '1️⃣ Select Novel'}
                        {step === 'processing' && '⏳ Processing...'}
                        {step === 'claims' && '2️⃣ Add Claims to Verify'}
                        {step === 'done' && '✅ Ready to Run'}
                    </h2>
                    <button onClick={onClose} className="p-2 hover:bg-gray-700 rounded-lg">
                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6">
                    {/* Step 1: Upload */}
                    {step === 'upload' && (
                        <div className="space-y-4">
                            {/* Dropzone */}
                            <div
                                onDragOver={handleDragOver}
                                onDragLeave={handleDragLeave}
                                onDrop={handleDrop}
                                onClick={() => fileInputRef.current?.click()}
                                className={`border-2 border-dashed rounded-xl p-6 cursor-pointer transition-all text-center
                                    ${isDragging ? 'border-primary-500 bg-primary-500/10' : 'border-gray-600 hover:border-gray-500'}
                                    ${file ? 'border-green-500 bg-green-500/10' : ''}`}
                            >
                                <input ref={fileInputRef} type="file" accept=".pdf,.docx,.doc,.txt" onChange={handleFileSelect} className="hidden" />
                                {file ? (
                                    <div className="flex items-center justify-center gap-3">
                                        <span className="text-2xl">📄</span>
                                        <div className="text-left">
                                            <p className="text-white font-medium">{file.name}</p>
                                            <p className="text-gray-400 text-sm">{formatFileSize(file.size)}</p>
                                        </div>
                                    </div>
                                ) : (
                                    <div>
                                        <span className="text-4xl">📚</span>
                                        <p className="text-gray-300 mt-2">Drop novel or click to browse</p>
                                        <p className="text-gray-500 text-sm">PDF, Word, or TXT</p>
                                    </div>
                                )}
                            </div>

                            {/* Model Selection */}
                            <div className="flex gap-2">
                                {Object.values(models).map(m => (
                                    <button
                                        key={m.id}
                                        onClick={() => setSelectedModel(m.id)}
                                        className={`flex-1 p-3 rounded-lg border-2 transition-all ${selectedModel === m.id
                                                ? 'border-primary-500 bg-primary-500/10'
                                                : 'border-gray-600 hover:border-gray-500'
                                            }`}
                                    >
                                        <span className="text-xl">{m.icon}</span>
                                        <p className="text-white text-sm mt-1">{m.name}</p>
                                    </button>
                                ))}
                            </div>

                            {/* Info */}
                            <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3 text-sm text-blue-300">
                                ℹ️ Previous results will be auto-saved to history
                            </div>
                        </div>
                    )}

                    {/* Processing */}
                    {step === 'processing' && (
                        <div className="text-center py-8">
                            <div className="w-12 h-12 mx-auto mb-4 border-4 border-primary-500 border-t-transparent rounded-full animate-spin"></div>
                            <p className="text-white">Uploading and processing...</p>
                            <div className="h-2 bg-gray-700 rounded-full mt-4 max-w-xs mx-auto">
                                <div className="h-full bg-primary-500 rounded-full transition-all" style={{ width: `${progress}%` }} />
                            </div>
                        </div>
                    )}

                    {/* Step 2: Add Claims */}
                    {step === 'claims' && uploadResult && (
                        <div className="space-y-4">
                            <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-3">
                                <p className="text-green-400 font-medium">✓ Novel uploaded: {uploadResult.book_name}</p>
                                <p className="text-gray-400 text-sm">{uploadResult.words?.toLocaleString()} words</p>
                            </div>

                            {/* Add Claim Form */}
                            <div className="bg-gray-700/50 rounded-lg p-4 space-y-3">
                                <h3 className="text-white font-medium text-sm">Add a claim to verify:</h3>

                                <input
                                    type="text"
                                    placeholder="Character name"
                                    value={newClaim.char}
                                    onChange={(e) => setNewClaim({ ...newClaim, char: e.target.value })}
                                    className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm"
                                />

                                <textarea
                                    placeholder="Claim to verify (e.g., 'Captain Nemo was born in India')"
                                    value={newClaim.content}
                                    onChange={(e) => setNewClaim({ ...newClaim, content: e.target.value })}
                                    className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm h-20 resize-none"
                                />

                                <div className="flex gap-2">
                                    <button
                                        onClick={() => setNewClaim({ ...newClaim, label: 'consistent' })}
                                        className={`flex-1 py-2 rounded-lg text-sm font-medium ${newClaim.label === 'consistent'
                                                ? 'bg-green-600 text-white'
                                                : 'bg-gray-700 text-gray-300'
                                            }`}
                                    >
                                        ✓ Consistent
                                    </button>
                                    <button
                                        onClick={() => setNewClaim({ ...newClaim, label: 'contradict' })}
                                        className={`flex-1 py-2 rounded-lg text-sm font-medium ${newClaim.label === 'contradict'
                                                ? 'bg-red-600 text-white'
                                                : 'bg-gray-700 text-gray-300'
                                            }`}
                                    >
                                        ✗ Contradicts
                                    </button>
                                </div>

                                <button
                                    onClick={handleAddClaim}
                                    className="w-full py-2 rounded-lg bg-primary-600 hover:bg-primary-500 text-white font-medium text-sm"
                                >
                                    + Add Claim
                                </button>
                            </div>

                            {/* Claims List */}
                            {claims.length > 0 && (
                                <div className="space-y-2">
                                    <p className="text-gray-400 text-sm">{claims.length} claim(s) added:</p>
                                    {claims.map((c, i) => (
                                        <div key={c.id || i} className="flex items-start gap-2 bg-gray-700/30 rounded-lg p-2">
                                            <span className={c.label === 'consistent' ? 'text-green-400' : 'text-red-400'}>
                                                {c.label === 'consistent' ? '✓' : '✗'}
                                            </span>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-white text-sm truncate"><b>{c.char}</b>: {c.content}</p>
                                            </div>
                                            <button onClick={() => handleDeleteClaim(c.id)} className="text-gray-500 hover:text-red-400">×</button>
                                        </div>
                                    ))}
                                </div>
                            )}

                            {claims.length === 0 && (
                                <p className="text-amber-400 text-sm text-center py-4">
                                    ⚠️ Add at least one claim to verify
                                </p>
                            )}
                        </div>
                    )}

                    {/* Done */}
                    {step === 'done' && (
                        <div className="text-center py-4">
                            <div className="w-16 h-16 mx-auto mb-4 bg-green-500/20 rounded-full flex items-center justify-center">
                                <span className="text-3xl">🎉</span>
                            </div>
                            <p className="text-white font-medium">Ready to verify {claims.length} claims!</p>
                            <div className="bg-gray-700/50 rounded-lg p-4 mt-4 text-left">
                                <p className="text-gray-400 text-sm mb-2">Run the pipeline:</p>
                                <code className="block bg-gray-900 text-green-400 p-2 rounded text-sm">
                                    python3 run_all.py {selectedModel === 'ollama' ? '--local' : ''}
                                </code>
                            </div>
                        </div>
                    )}

                    {/* Error */}
                    {error && (
                        <div className="mt-4 p-3 bg-red-500/20 border border-red-500/50 rounded-lg">
                            <p className="text-red-400 text-sm">{error}</p>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="flex gap-3 p-4 border-t border-gray-700">
                    {step === 'upload' && (
                        <>
                            <button onClick={onClose} className="flex-1 px-4 py-2 rounded-lg border border-gray-600 text-gray-300 hover:bg-gray-700">
                                Cancel
                            </button>
                            <button
                                onClick={handleUpload}
                                disabled={!file}
                                className="flex-1 px-4 py-2 rounded-lg bg-green-600 hover:bg-green-500 text-white font-medium disabled:opacity-50"
                            >
                                Upload Novel
                            </button>
                        </>
                    )}

                    {step === 'claims' && (
                        <>
                            <button onClick={onClose} className="flex-1 px-4 py-2 rounded-lg border border-gray-600 text-gray-300 hover:bg-gray-700">
                                Cancel
                            </button>
                            <button
                                onClick={() => {
                                    setStep('done')
                                    onUploadSuccess?.({ ...uploadResult, claims, model: selectedModel })
                                }}
                                disabled={claims.length === 0}
                                className="flex-1 px-4 py-2 rounded-lg bg-primary-600 hover:bg-primary-500 text-white font-medium disabled:opacity-50"
                            >
                                Continue ({claims.length} claims)
                            </button>
                        </>
                    )}

                    {step === 'done' && (
                        <button onClick={onClose} className="w-full px-4 py-2 rounded-lg bg-primary-600 hover:bg-primary-500 text-white font-medium">
                            Close
                        </button>
                    )}
                </div>
            </div>
        </div>
    )
}
