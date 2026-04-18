"""
先週の予測と実際の株価を照合し的中率を記録する
"""
import json
import os
import sys
from datetime import datetime, timedelta
import yfinance as yf

def evaluate():
    predictions_path = sys.argv[1] if len(sys.argv) > 1 else 'data/predictions.json'
    results_path = sys.argv[2] if len(sys.argv) > 2 else 'data/results.json'
    history_path = sys.argv[3] if len(sys.argv) > 3 else 'data/history.json'

    with open(predictions_path, encoding='utf-8') as f:
        predictions = json.load(f)

    if not predictions.get('stocks'):
        print("No predictions to evaluate.")
        return

    stocks = predictions['stocks']
    tickers = [s['ticker'] for s in stocks]

    print(f"Evaluating {len(tickers)} stocks...", flush=True)

    end = datetime.now()
    start = end - timedelta(days=3)
    raw = yf.download(tickers, start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'),
                      group_by='ticker', auto_adjust=True, threads=True, progress=False)

    evaluated = []
    for stock in stocks:
        ticker = stock['ticker']
        try:
            df = raw[ticker] if len(tickers) > 1 else raw
            df = df.dropna()
            if len(df) < 1:
                continue

            actual_price = float(df['Close'].iloc[-1])
            predicted_price = stock['currentPrice']
            actual_return = (actual_price - predicted_price) / predicted_price * 100

            if actual_return > 1.0:
                actual_direction = 'UP'
            elif actual_return < -1.0:
                actual_direction = 'DOWN'
            else:
                actual_direction = 'NEUTRAL'

            hit = stock['direction'] == actual_direction

            evaluated.append({
                **stock,
                'actualPrice': round(actual_price, 2),
                'actualReturn': round(actual_return, 2),
                'actualDirection': actual_direction,
                'hit': hit,
                'evaluatedAt': datetime.now().isoformat()
            })
        except Exception as e:
            print(f"  Error {ticker}: {e}", flush=True)
            continue

    if not evaluated:
        print("No stocks evaluated.")
        return

    hits = sum(1 for e in evaluated if e['hit'])
    accuracy = hits / len(evaluated) * 100

    result_entry = {
        'week': predictions['week'],
        'evaluatedAt': datetime.now().isoformat(),
        'total': len(evaluated),
        'hits': hits,
        'accuracy': round(accuracy, 1),
        'stocks': evaluated
    }

    # results.json に追記
    with open(results_path, encoding='utf-8') as f:
        results = json.load(f)
    results.append(result_entry)
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # history.json にも追記
    with open(history_path, encoding='utf-8') as f:
        history = json.load(f)
    history.append(result_entry)
    with open(history_path, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    print(f"Week {predictions['week']}: {hits}/{len(evaluated)} correct ({accuracy:.1f}%)", flush=True)

if __name__ == '__main__':
    evaluate()
