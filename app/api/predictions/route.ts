import { NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

export async function GET() {
  const filePath = path.join(process.cwd(), 'data', 'predictions.json')
  const data = JSON.parse(fs.readFileSync(filePath, 'utf-8'))
  return NextResponse.json(data)
}
