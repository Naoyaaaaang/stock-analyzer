import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Stock Analyzer',
  description: 'S&P500 週次株価分析・予測システム',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body className="bg-gray-950 text-gray-100 min-h-screen">{children}</body>
    </html>
  )
}
