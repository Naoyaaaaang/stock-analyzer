"""
スクリーニング済み100銘柄をClaude APIで分析し予測を生成する
"""
import json
import os
import sys
import time
from datetime import datetime, timedelta
import yfinance as yf
import anthropic

SYSTEM_PROMPT = """You are an expert stock analyst. Analyze the provided stock data and recent news, then predict whether the stock will go UP, DOWN, or NEUTRAL for the coming week.

Respond in this exact JSON format:
{
  "direction": "UP" | "DOWN" | "NEUTRAL",
  "confidence": 1-5,
  "reason": "2-3 sentence explanation in Japanese",
  "keyFactors": ["factor1", "factor2", "factor3"]
}"""

def get_news(ticker):
    try:
        stock = yf.Ticker(ticker)
        news = stock.news or []
        summaries = []
        for item in news[:5]:
            title = item.get('title', '')
            summary = item.get('summary', '') or item.get('description', '')
            if title:
                summaries.append(f"- {title}: {summary[:200]}" if summary else f"- {title}")
        return '\n'.join(summaries) if summaries else 'No recent news available.'
    except:
        return 'No recent news available.'

def analyze_stock(client, stock_data, news_text):
    prompt = f"""Stock: {stock_data['ticker']}
Current Price: ${stock_data['currentPrice']}
Weekly Return: {stock_data['weeklyReturn']}%
Volume Ratio (vs avg): {stock_data['volumeRatio']}x
RSI: {stock_data['rsi']}

Recent News:
{news_text}

Predict next week's direction."""

    response = client.messages.create(
        model='claude-sonnet-4-6',
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=[{'role': 'user', 'content': prompt}]
    )

    text = response.content[0].text.strip()
    # JSONブロック抽出
    if '```' in text:
        text = text.split('```')[1]
        if text.startswith('json'):
            text = text[4:]
    return json.loads(text)

def main():
    screened_path = sys.argv[1] if len(sys.argv) > 1 else 'data/screened.json'
    predictions_path = sys.argv[2] if len(sys.argv) > 2 else 'data/predictions.json'

    with open(screened_path) as f:
        screened = json.load(f)

    client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])

    week_str = datetime.now().strftime('%Y-W%V')
    predictions = []
    stocks = screened['stocks']

    print(f"Analyzing {len(stocks)} stocks...", flush=True)

    for i, stock in enumerate(stocks):
        ticker = stock['ticker']
        print(f"[{i+1}/{len(stocks)}] {ticker}", flush=True)

        try:
            news = get_news(ticker)
            analysis = analyze_stock(client, stock, news)

            predictions.append({
                **stock,
                'direction': analysis.get('direction', 'NEUTRAL'),
                'confidence': analysis.get('confidence', 1),
                'reason': analysis.get('reason', ''),
                'keyFactors': analysis.get('keyFactors', []),
                'news': news[:500]
            })
        except Exception as e:
            print(f"  Error: {e}", flush=True)
            predictions.append({
                **stock,
                'direction': 'NEUTRAL',
                'confidence': 1,
                'reason': 'Analysis failed.',
                'keyFactors': [],
                'news': ''
            })

        # レートリミット対策
        if (i + 1) % 10 == 0:
            time.sleep(2)

    output = {
        'week': week_str,
        'generatedAt': datetime.now().isoformat(),
        'total': len(predictions),
        'stocks': predictions
    }

    with open(predictions_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    up = sum(1 for p in predictions if p['direction'] == 'UP')
    down = sum(1 for p in predictions if p['direction'] == 'DOWN')
    print(f"Done. UP:{up} DOWN:{down} NEUTRAL:{len(predictions)-up-down}", flush=True)

if __name__ == '__main__':
    main()
