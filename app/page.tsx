'use client'
import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

type Stock = {
  ticker: string
  weeklyReturn: number
  currentPrice: number
  volumeRatio: number
  rsi: number
  direction: string
  confidence: number
  reason: string
  keyFactors: string[]
  actualReturn?: number
  actualDirection?: string
  hit?: boolean
}

type Predictions = {
  week: string
  generatedAt: string
  total: number
  stocks: Stock[]
}

type Result = {
  week: string
  evaluatedAt: string
  total: number
  hits: number
  accuracy: number
  stocks: Stock[]
}

const DIRECTION_COLOR: Record<string, string> = {
  UP: 'text-green-400',
  DOWN: 'text-red-400',
  NEUTRAL: 'text-yellow-400',
}
const DIRECTION_BG: Record<string, string> = {
  UP: 'bg-green-900/40 border-green-700',
  DOWN: 'bg-red-900/40 border-red-700',
  NEUTRAL: 'bg-yellow-900/40 border-yellow-700',
}

export default function Home() {
  const [tab, setTab] = useState<'predictions' | 'results'>('predictions')
  const [predictions, setPredictions] = useState<Predictions | null>(null)
  const [results, setResults] = useState<Result[]>([])
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<'ALL' | 'UP' | 'DOWN' | 'NEUTRAL'>('ALL')
  const [selected, setSelected] = useState<Stock | null>(null)

  useEffect(() => {
    fetch('/api/predictions').then(r => r.json()).then(setPredictions)
    fetch('/api/results').then(r => r.json()).then(setResults)
  }, [])

  const filtered = (predictions?.stocks || []).filter(s => {
    if (filter !== 'ALL' && s.direction !== filter) return false
    if (search && !s.ticker.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  const accuracyData = results.map(r => ({ week: r.week, accuracy: r.accuracy }))
  const latestResult = results[results.length - 1]

  return (
    <div className="max-w-6xl mx-auto p-4">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-blue-400">Stock Analyzer</h1>
        <p className="text-gray-400 text-sm">S&P500 週次予測システム</p>
      </div>

      {/* サマリーカード */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <div className="bg-gray-900 rounded-lg p-3 border border-gray-800">
          <div className="text-gray-400 text-xs">今週対象銘柄</div>
          <div className="text-2xl font-bold text-white">{predictions?.total ?? '-'}</div>
        </div>
        <div className="bg-gray-900 rounded-lg p-3 border border-gray-800">
          <div className="text-gray-400 text-xs">UP予測</div>
          <div className="text-2xl font-bold text-green-400">
            {predictions?.stocks.filter(s => s.direction === 'UP').length ?? '-'}
          </div>
        </div>
        <div className="bg-gray-900 rounded-lg p-3 border border-gray-800">
          <div className="text-gray-400 text-xs">DOWN予測</div>
          <div className="text-2xl font-bold text-red-400">
            {predictions?.stocks.filter(s => s.direction === 'DOWN').length ?? '-'}
          </div>
        </div>
        <div className="bg-gray-900 rounded-lg p-3 border border-gray-800">
          <div className="text-gray-400 text-xs">直近的中率</div>
          <div className="text-2xl font-bold text-yellow-400">
            {latestResult ? `${latestResult.accuracy}%` : '-'}
          </div>
        </div>
      </div>

      {/* タブ */}
      <div className="flex gap-2 mb-4">
        {(['predictions', 'results'] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              tab === t ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            {t === 'predictions' ? '今週の予測' : '過去の結果'}
          </button>
        ))}
      </div>

      {tab === 'predictions' && (
        <>
          <div className="flex gap-2 mb-4 flex-wrap">
            <input
              type="text"
              placeholder="ティッカー検索..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm text-white w-40"
            />
            {(['ALL', 'UP', 'DOWN', 'NEUTRAL'] as const).map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                  filter === f ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                }`}
              >
                {f}
              </button>
            ))}
            <span className="text-gray-500 text-xs self-center ml-auto">
              {predictions?.week} / {filtered.length}銘柄
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {filtered.map(stock => (
              <div
                key={stock.ticker}
                onClick={() => setSelected(stock)}
                className={`rounded-lg border p-3 cursor-pointer hover:brightness-110 transition ${DIRECTION_BG[stock.direction] || 'bg-gray-900 border-gray-700'}`}
              >
                <div className="flex justify-between items-start mb-1">
                  <span className="font-bold text-white">{stock.ticker}</span>
                  <span className={`text-sm font-bold ${DIRECTION_COLOR[stock.direction]}`}>
                    {stock.direction}
                  </span>
                </div>
                <div className="text-gray-300 text-sm">${stock.currentPrice}</div>
                <div className={`text-xs ${stock.weeklyReturn >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  先週: {stock.weeklyReturn >= 0 ? '+' : ''}{stock.weeklyReturn}%
                </div>
                <div className="text-gray-400 text-xs mt-1">
                  RSI {stock.rsi} / 出来高 {stock.volumeRatio}x / 確信度 {'★'.repeat(stock.confidence)}
                </div>
                <div className="text-gray-300 text-xs mt-2 line-clamp-2">{stock.reason}</div>
              </div>
            ))}
          </div>
        </>
      )}

      {tab === 'results' && (
        <>
          {accuracyData.length > 0 && (
            <div className="bg-gray-900 rounded-lg p-4 border border-gray-800 mb-4">
              <div className="text-sm text-gray-400 mb-3">週次的中率推移</div>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={accuracyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="week" stroke="#9CA3AF" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#9CA3AF" tick={{ fontSize: 11 }} domain={[0, 100]} unit="%" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: 8 }}
                    labelStyle={{ color: '#9CA3AF' }}
                  />
                  <Line type="monotone" dataKey="accuracy" stroke="#60A5FA" strokeWidth={2} dot={{ fill: '#60A5FA' }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          <div className="space-y-4">
            {[...results].reverse().map((result, i) => (
              <div key={i} className="bg-gray-900 rounded-lg border border-gray-800 p-4">
                <div className="flex justify-between items-center mb-3">
                  <span className="font-bold text-white">{result.week}</span>
                  <span className="text-yellow-400 font-bold">{result.accuracy}% 的中</span>
                  <span className="text-gray-400 text-sm">{result.hits}/{result.total}</span>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {result.stocks.map(s => (
                    <div
                      key={s.ticker}
                      className={`rounded p-2 text-xs border ${s.hit ? 'border-green-700 bg-green-900/20' : 'border-red-800 bg-red-900/10'}`}
                    >
                      <span className="font-bold text-white">{s.ticker}</span>
                      <span className={`ml-2 ${DIRECTION_COLOR[s.direction]}`}>{s.direction}</span>
                      <span className="text-gray-500"> → </span>
                      <span className={`${(s.actualReturn ?? 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {(s.actualReturn ?? 0) >= 0 ? '+' : ''}{s.actualReturn}%
                      </span>
                      <span className="ml-1">{s.hit ? '✓' : '✗'}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
            {results.length === 0 && (
              <div className="text-gray-500 text-center py-8">まだ評価データがありません。金曜日に初回評価が実行されます。</div>
            )}
          </div>
        </>
      )}

      {/* 詳細モーダル */}
      {selected && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4" onClick={() => setSelected(null)}>
          <div className="bg-gray-900 rounded-xl border border-gray-700 p-5 max-w-md w-full" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-start mb-3">
              <h2 className="text-xl font-bold text-white">{selected.ticker}</h2>
              <span className={`text-lg font-bold ${DIRECTION_COLOR[selected.direction]}`}>{selected.direction}</span>
            </div>
            <div className="grid grid-cols-3 gap-3 mb-4 text-center">
              <div className="bg-gray-800 rounded p-2">
                <div className="text-xs text-gray-400">現在価格</div>
                <div className="font-bold text-white">${selected.currentPrice}</div>
              </div>
              <div className="bg-gray-800 rounded p-2">
                <div className="text-xs text-gray-400">先週騰落</div>
                <div className={`font-bold ${selected.weeklyReturn >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {selected.weeklyReturn >= 0 ? '+' : ''}{selected.weeklyReturn}%
                </div>
              </div>
              <div className="bg-gray-800 rounded p-2">
                <div className="text-xs text-gray-400">確信度</div>
                <div className="font-bold text-yellow-400">{'★'.repeat(selected.confidence)}{'☆'.repeat(5 - selected.confidence)}</div>
              </div>
            </div>
            <div className="mb-3">
              <div className="text-xs text-gray-400 mb-1">分析理由</div>
              <div className="text-sm text-gray-200">{selected.reason}</div>
            </div>
            {selected.keyFactors?.length > 0 && (
              <div className="mb-3">
                <div className="text-xs text-gray-400 mb-1">キーファクター</div>
                <div className="flex flex-wrap gap-1">
                  {selected.keyFactors.map((f, i) => (
                    <span key={i} className="bg-blue-900/40 text-blue-300 text-xs px-2 py-0.5 rounded">{f}</span>
                  ))}
                </div>
              </div>
            )}
            <div className="text-xs text-gray-500">RSI: {selected.rsi} / 出来高比: {selected.volumeRatio}x</div>
            <button onClick={() => setSelected(null)} className="mt-4 w-full bg-gray-700 hover:bg-gray-600 text-white rounded py-2 text-sm">閉じる</button>
          </div>
        </div>
      )}
    </div>
  )
}
