function StatsBar({ stats }) {
    if (!stats) return null

    const cards = [
        {
            label: 'Total Claims',
            value: stats.total,
            icon: '📊',
            color: 'from-primary-500 to-primary-700'
        },
        {
            label: 'Supported',
            value: stats.supported,
            icon: '✅',
            color: 'from-success-500 to-success-600',
            percent: stats.total > 0 ? (stats.supported / stats.total * 100).toFixed(0) : 0
        },
        {
            label: 'Contradicted',
            value: stats.contradicted,
            icon: '❌',
            color: 'from-danger-500 to-danger-600',
            percent: stats.total > 0 ? (stats.contradicted / stats.total * 100).toFixed(0) : 0
        },
        {
            label: 'Avg Confidence',
            value: `${(stats.avg_confidence * 100).toFixed(0)}%`,
            icon: '🎯',
            color: 'from-warning-500 to-warning-600'
        }
    ]

    return (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            {cards.map((card) => (
                <div
                    key={card.label}
                    className="glass rounded-xl p-4 glass-hover"
                >
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-2xl">{card.icon}</span>
                        {card.percent !== undefined && (
                            <span className="text-xs text-gray-400">{card.percent}%</span>
                        )}
                    </div>
                    <div className="text-2xl font-bold text-white">{card.value}</div>
                    <div className="text-sm text-gray-400">{card.label}</div>
                </div>
            ))}
        </div>
    )
}

export default StatsBar
