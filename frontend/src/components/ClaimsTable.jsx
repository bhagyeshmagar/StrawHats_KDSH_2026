import { useState } from 'react'

const VERDICT_CONFIG = {
    supported: { badge: 'badge-success', label: '✅ Supported' },
    contradicted: { badge: 'badge-danger', label: '❌ Contradicted' },
    undetermined: { badge: 'badge-warning', label: '⚠️ Undetermined' }
}

function ClaimsTable({ results, selectedId, onSelect }) {
    const [sortField, setSortField] = useState('id')
    const [sortDir, setSortDir] = useState('asc')

    // Sort results
    const sortedResults = [...results].sort((a, b) => {
        let aVal = a[sortField]
        let bVal = b[sortField]

        // Handle numeric fields
        if (sortField === 'id' || sortField === 'confidence' || sortField === 'prediction') {
            aVal = Number(aVal) || 0
            bVal = Number(bVal) || 0
        } else {
            aVal = String(aVal || '').toLowerCase()
            bVal = String(bVal || '').toLowerCase()
        }

        if (aVal < bVal) return sortDir === 'asc' ? -1 : 1
        if (aVal > bVal) return sortDir === 'asc' ? 1 : -1
        return 0
    })

    const handleSort = (field) => {
        if (sortField === field) {
            setSortDir(sortDir === 'asc' ? 'desc' : 'asc')
        } else {
            setSortField(field)
            setSortDir('asc')
        }
    }

    const SortIcon = ({ field }) => {
        if (sortField !== field) return null
        return (
            <span className="ml-1">
                {sortDir === 'asc' ? '↑' : '↓'}
            </span>
        )
    }

    if (results.length === 0) {
        return (
            <div className="glass rounded-xl p-8 text-center">
                <p className="text-gray-400">No results found matching your filters.</p>
            </div>
        )
    }

    return (
        <div className="glass rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
                <table className="w-full">
                    <thead>
                        <tr className="border-b border-white/10">
                            <th
                                className="text-left p-4 font-medium text-gray-400 cursor-pointer hover:text-white transition-colors"
                                onClick={() => handleSort('id')}
                            >
                                ID <SortIcon field="id" />
                            </th>
                            <th
                                className="text-left p-4 font-medium text-gray-400 cursor-pointer hover:text-white transition-colors"
                                onClick={() => handleSort('character')}
                            >
                                Character <SortIcon field="character" />
                            </th>
                            <th
                                className="text-left p-4 font-medium text-gray-400 cursor-pointer hover:text-white transition-colors"
                                onClick={() => handleSort('book_name')}
                            >
                                Book <SortIcon field="book_name" />
                            </th>
                            <th
                                className="text-left p-4 font-medium text-gray-400 cursor-pointer hover:text-white transition-colors"
                                onClick={() => handleSort('verdict')}
                            >
                                Verdict <SortIcon field="verdict" />
                            </th>
                            <th
                                className="text-left p-4 font-medium text-gray-400 cursor-pointer hover:text-white transition-colors"
                                onClick={() => handleSort('confidence')}
                            >
                                Confidence <SortIcon field="confidence" />
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        {sortedResults.map((result) => {
                            const config = VERDICT_CONFIG[result.verdict] || VERDICT_CONFIG.undetermined
                            const isSelected = selectedId === result.id

                            return (
                                <tr
                                    key={result.id}
                                    className={`table-row-hover ${isSelected ? 'bg-primary-500/20' : ''}`}
                                    onClick={() => onSelect(result)}
                                >
                                    <td className="p-4 font-mono text-sm">{result.id}</td>
                                    <td className="p-4 font-medium">{result.character}</td>
                                    <td className="p-4 text-gray-400 text-sm truncate max-w-[200px]">
                                        {result.book_name}
                                    </td>
                                    <td className="p-4">
                                        <span className={`badge ${config.badge}`}>
                                            {config.label}
                                        </span>
                                    </td>
                                    <td className="p-4">
                                        <div className="flex items-center gap-2">
                                            <div className="w-16 h-2 bg-gray-700 rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-primary-500 transition-all"
                                                    style={{ width: `${(result.confidence || 0) * 100}%` }}
                                                />
                                            </div>
                                            <span className="text-xs text-gray-400">
                                                {((result.confidence || 0) * 100).toFixed(0)}%
                                            </span>
                                        </div>
                                    </td>
                                </tr>
                            )
                        })}
                    </tbody>
                </table>
            </div>

            {/* Results count */}
            <div className="border-t border-white/10 px-4 py-3 text-sm text-gray-400">
                Showing {results.length} result{results.length !== 1 ? 's' : ''}
            </div>
        </div>
    )
}

export default ClaimsTable
