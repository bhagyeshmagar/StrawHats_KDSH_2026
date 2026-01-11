import { useState } from 'react'

/**
 * VisualizationPanel Component
 * 
 * Displays charts and statistics for claim verification results.
 * Shows: Verdict pie chart, Claims by book, Confidence distribution, Stats overview
 */
export default function VisualizationPanel({ stats, results }) {
    const [activeChart, setActiveChart] = useState('pie')

    // Calculate verdict distribution
    const verdictCounts = {
        supported: results?.filter(r => r.verdict?.toLowerCase() === 'supported').length || 0,
        contradicted: results?.filter(r => r.verdict?.toLowerCase() === 'contradicted').length || 0,
        undetermined: results?.filter(r => r.verdict?.toLowerCase() === 'undetermined').length || 0
    }
    const total = verdictCounts.supported + verdictCounts.contradicted + verdictCounts.undetermined

    // Calculate book distribution
    const bookCounts = results?.reduce((acc, r) => {
        const book = r.book_name || 'Unknown'
        acc[book] = (acc[book] || 0) + 1
        return acc
    }, {}) || {}

    // Calculate confidence distribution
    const confidenceBuckets = { 'Low (0-40%)': 0, 'Medium (40-70%)': 0, 'High (70-100%)': 0 }
    results?.forEach(r => {
        const conf = parseFloat(r.confidence) || 0
        if (conf < 0.4) confidenceBuckets['Low (0-40%)']++
        else if (conf < 0.7) confidenceBuckets['Medium (40-70%)']++
        else confidenceBuckets['High (70-100%)']++
    })

    // Calculate average confidence
    const avgConfidence = results?.length > 0
        ? (results.reduce((sum, r) => sum + (parseFloat(r.confidence) || 0), 0) / results.length * 100).toFixed(1)
        : 0

    return (
        <div className="glass rounded-xl p-6 mb-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                    <svg className="w-5 h-5 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    Verification Results
                </h2>

                {/* Chart Toggle */}
                <div className="flex gap-1 bg-gray-800 rounded-lg p-1">
                    {[
                        { id: 'pie', label: 'Verdicts' },
                        { id: 'bar', label: 'By Book' },
                        { id: 'confidence', label: 'Confidence' },
                        { id: 'stats', label: 'Stats' }
                    ].map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveChart(tab.id)}
                            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${activeChart === tab.id
                                ? 'bg-primary-600 text-white'
                                : 'text-gray-400 hover:text-white'
                                }`}
                        >
                            {tab.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Charts Container */}
            <div className="min-h-[220px]">
                {activeChart === 'pie' && (
                    <PieChart
                        data={verdictCounts}
                        total={total}
                    />
                )}

                {activeChart === 'bar' && (
                    <BarChart
                        data={bookCounts}
                    />
                )}

                {activeChart === 'confidence' && (
                    <ConfidenceChart
                        buckets={confidenceBuckets}
                        average={avgConfidence}
                    />
                )}

                {activeChart === 'stats' && (
                    <StatsView
                        stats={stats}
                        verdictCounts={verdictCounts}
                        avgConfidence={avgConfidence}
                        total={total}
                    />
                )}
            </div>
        </div>
    )
}

/**
 * Pie Chart - Verdict Distribution
 */
function PieChart({ data, total }) {
    const colors = {
        supported: '#22c55e',
        contradicted: '#ef4444',
        undetermined: '#f59e0b'
    }

    const labels = {
        supported: 'Supported',
        contradicted: 'Contradicted',
        undetermined: 'Undetermined'
    }

    const icons = {
        supported: '✓',
        contradicted: '✗',
        undetermined: '?'
    }

    let currentAngle = 0
    const segments = Object.entries(data).map(([key, value]) => {
        const percentage = total > 0 ? value / total : 0
        const angle = percentage * 360
        const startAngle = currentAngle
        currentAngle += angle
        return { key, value, percentage, startAngle, endAngle: currentAngle, color: colors[key] }
    }).filter(s => s.value > 0)

    const getArcPath = (startAngle, endAngle, radius, cx, cy) => {
        const start = polarToCartesian(cx, cy, radius, endAngle)
        const end = polarToCartesian(cx, cy, radius, startAngle)
        const largeArcFlag = endAngle - startAngle <= 180 ? 0 : 1
        return ['M', cx, cy, 'L', start.x, start.y, 'A', radius, radius, 0, largeArcFlag, 0, end.x, end.y, 'Z'].join(' ')
    }

    const polarToCartesian = (cx, cy, radius, angle) => {
        const radian = (angle - 90) * Math.PI / 180
        return { x: cx + radius * Math.cos(radian), y: cy + radius * Math.sin(radian) }
    }

    return (
        <div className="flex flex-col sm:flex-row items-center justify-center gap-8">
            <div className="relative">
                <svg width="180" height="180" viewBox="0 0 180 180">
                    {segments.map((segment) => (
                        <path
                            key={segment.key}
                            d={getArcPath(segment.startAngle, segment.endAngle, 80, 90, 90)}
                            fill={segment.color}
                            className="hover:opacity-80 transition-opacity cursor-pointer"
                        />
                    ))}
                    <circle cx="90" cy="90" r="45" fill="#1f2937" />
                    <text x="90" y="85" textAnchor="middle" className="fill-white text-2xl font-bold">{total}</text>
                    <text x="90" y="105" textAnchor="middle" className="fill-gray-400 text-xs">Claims</text>
                </svg>
            </div>

            <div className="space-y-3">
                {Object.entries(data).map(([key, value]) => (
                    <div key={key} className="flex items-center gap-3">
                        <div
                            className="w-10 h-10 rounded-lg flex items-center justify-center text-lg"
                            style={{ backgroundColor: colors[key] + '30' }}
                        >
                            <span style={{ color: colors[key] }}>{icons[key]}</span>
                        </div>
                        <div>
                            <p className="text-white font-medium">{labels[key]}</p>
                            <p className="text-gray-400 text-sm">
                                {value} ({total > 0 ? ((value / total) * 100).toFixed(1) : 0}%)
                            </p>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}

/**
 * Bar Chart - Claims by Book
 */
function BarChart({ data }) {
    const entries = Object.entries(data)
    const maxValue = Math.max(...Object.values(data), 1)
    const colors = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4']

    return (
        <div className="space-y-3">
            <h3 className="text-sm font-medium text-gray-400 mb-4">Claims by Book</h3>

            {entries.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No data available</p>
            ) : (
                entries.map(([book, count], index) => (
                    <div key={book} className="flex items-center gap-3">
                        <div className="w-36 text-right">
                            <p className="text-gray-300 text-sm truncate" title={book}>
                                {book.length > 20 ? book.substring(0, 20) + '...' : book}
                            </p>
                        </div>
                        <div className="flex-1 bg-gray-800 rounded-full h-6 overflow-hidden">
                            <div
                                className="h-full rounded-full transition-all duration-500 flex items-center justify-end pr-2"
                                style={{
                                    width: `${(count / maxValue) * 100}%`,
                                    backgroundColor: colors[index % colors.length],
                                    minWidth: '30px'
                                }}
                            >
                                <span className="text-white text-xs font-medium">{count}</span>
                            </div>
                        </div>
                    </div>
                ))
            )}
        </div>
    )
}

/**
 * Confidence Distribution Chart
 */
function ConfidenceChart({ buckets, average }) {
    const colors = {
        'Low (0-40%)': '#ef4444',
        'Medium (40-70%)': '#f59e0b',
        'High (70-100%)': '#22c55e'
    }

    const total = Object.values(buckets).reduce((a, b) => a + b, 0) || 1
    const maxValue = Math.max(...Object.values(buckets), 1)

    return (
        <div>
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-gray-400">Confidence Distribution</h3>
                <div className="flex items-center gap-2 bg-gray-800 px-3 py-1.5 rounded-lg">
                    <span className="text-gray-400 text-xs">Average:</span>
                    <span className="text-white font-bold">{average}%</span>
                </div>
            </div>

            <div className="space-y-4">
                {Object.entries(buckets).map(([label, count]) => (
                    <div key={label}>
                        <div className="flex justify-between text-sm mb-1">
                            <span className="text-gray-300">{label}</span>
                            <span className="text-gray-400">{count} ({((count / total) * 100).toFixed(0)}%)</span>
                        </div>
                        <div className="bg-gray-800 rounded-full h-4 overflow-hidden">
                            <div
                                className="h-full rounded-full transition-all duration-700"
                                style={{
                                    width: `${(count / maxValue) * 100}%`,
                                    backgroundColor: colors[label],
                                    minWidth: count > 0 ? '8px' : '0'
                                }}
                            />
                        </div>
                    </div>
                ))}
            </div>

            <div className="mt-6 p-4 bg-gray-800/50 rounded-lg">
                <p className="text-gray-400 text-sm">
                    <span className="text-white font-medium">Confidence</span> indicates how certain the LLM is about its verdict.
                    High confidence (70%+) means strong evidence was found in the text.
                </p>
            </div>
        </div>
    )
}

/**
 * Stats Overview
 */
function StatsView({ stats, verdictCounts, avgConfidence, total }) {
    // Get accuracy from stats if available
    const modelAccuracy = stats?.accuracy
    const evaluatedClaims = stats?.evaluated_claims || 0
    const correctPredictions = stats?.correct_predictions || 0

    const statCards = [
        {
            label: 'Model Accuracy',
            value: modelAccuracy !== null ? `${modelAccuracy}%` : 'N/A',
            icon: '🎯',
            color: modelAccuracy >= 80 ? 'from-green-500 to-emerald-600' : modelAccuracy >= 60 ? 'from-amber-500 to-orange-600' : 'from-red-500 to-red-600',
            description: `${correctPredictions}/${evaluatedClaims} correct`
        },
        {
            label: 'Total Claims',
            value: total,
            icon: '📊',
            color: 'from-blue-500 to-blue-600',
            description: 'Verified claims'
        },
        {
            label: 'Supported',
            value: verdictCounts.supported,
            icon: '✓',
            color: 'from-green-500 to-green-600',
            description: 'Consistent with text'
        },
        {
            label: 'Contradicted',
            value: verdictCounts.contradicted,
            icon: '✗',
            color: 'from-red-500 to-red-600',
            description: 'Conflicts with text'
        },
        {
            label: 'Undetermined',
            value: verdictCounts.undetermined,
            icon: '?',
            color: 'from-amber-500 to-amber-600',
            description: 'Insufficient evidence'
        },
        {
            label: 'Avg Confidence',
            value: `${avgConfidence}%`,
            icon: '💪',
            color: 'from-cyan-500 to-cyan-600',
            description: 'LLM certainty level'
        }
    ]

    return (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {statCards.map((stat, i) => (
                <div
                    key={i}
                    className={`p-4 rounded-xl bg-gradient-to-br ${stat.color} relative overflow-hidden group hover:scale-105 transition-transform`}
                >
                    <div className="absolute right-2 top-2 text-2xl opacity-30 group-hover:opacity-50 transition-opacity">
                        {stat.icon}
                    </div>
                    <p className="text-white/80 text-xs font-medium">{stat.label}</p>
                    <p className="text-white text-2xl font-bold mt-1">{stat.value}</p>
                    <p className="text-white/60 text-xs mt-1">{stat.description}</p>
                </div>
            ))}
        </div>
    )
}
