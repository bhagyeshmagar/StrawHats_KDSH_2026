function FilterBar({ filters, setFilters, books, characters, verdicts }) {
    const handleChange = (field, value) => {
        setFilters(prev => ({ ...prev, [field]: value }))
    }

    const clearFilters = () => {
        setFilters({
            search: '',
            book: '',
            verdict: '',
            character: ''
        })
    }

    const hasFilters = filters.search || filters.book || filters.verdict || filters.character

    return (
        <div className="glass rounded-xl p-4 mb-6">
            <div className="flex flex-wrap gap-4">
                {/* Search */}
                <div className="flex-1 min-w-[200px]">
                    <div className="relative">
                        <svg
                            className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                        <input
                            type="text"
                            placeholder="Search claims..."
                            value={filters.search}
                            onChange={(e) => handleChange('search', e.target.value)}
                            className="w-full pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-white placeholder-gray-400"
                        />
                    </div>
                </div>

                {/* Book Filter */}
                <select
                    value={filters.book}
                    onChange={(e) => handleChange('book', e.target.value)}
                    className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 text-white"
                >
                    <option value="">All Books</option>
                    {books.map((book) => (
                        <option key={book} value={book} className="bg-gray-800">{book}</option>
                    ))}
                </select>

                {/* Character Filter */}
                <select
                    value={filters.character}
                    onChange={(e) => handleChange('character', e.target.value)}
                    className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 text-white"
                >
                    <option value="">All Characters</option>
                    {characters.map((char) => (
                        <option key={char} value={char} className="bg-gray-800">{char}</option>
                    ))}
                </select>

                {/* Verdict Filter */}
                <select
                    value={filters.verdict}
                    onChange={(e) => handleChange('verdict', e.target.value)}
                    className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 text-white"
                >
                    <option value="">All Verdicts</option>
                    {verdicts.map((verdict) => (
                        <option key={verdict} value={verdict} className="bg-gray-800">
                            {verdict.charAt(0).toUpperCase() + verdict.slice(1)}
                        </option>
                    ))}
                </select>

                {/* Clear Filters */}
                {hasFilters && (
                    <button
                        onClick={clearFilters}
                        className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                    >
                        Clear Filters
                    </button>
                )}
            </div>
        </div>
    )
}

export default FilterBar
