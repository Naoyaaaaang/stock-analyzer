"""
S&P500全銘柄をスクリーニングして上位100銘柄を選定する
選定基準: 週次騰落率の絶対値 + 出来高急増 + RSI
"""
import json
import sys
import time
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd

def get_sp500_tickers():
    table = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
    return table['Symbol'].str.replace('.', '-').tolist()

def calc_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def screen_stocks(tickers, top_n=100):
    end = datetime.now()
    start = end - timedelta(days=60)

    print(f"Fetching data for {len(tickers)} tickers...", flush=True)
    raw = yf.download(
        tickers,
        start=start.strftime('%Y-%m-%d'),
        end=end.strftime('%Y-%m-%d'),
        group_by='ticker',
        auto_adjust=True,
        threads=True,
        progress=False
    )

    scores = []
    week_ago = end - timedelta(days=7)

    for ticker in tickers:
        try:
            if len(tickers) == 1:
                df = raw
            else:
                df = raw[ticker]

            df = df.dropna()
            if len(df) < 20:
                continue

            close = df['Close']
            volume = df['Volume']

            # 週次騰落率
            week_prices = close[close.index >= pd.Timestamp(week_ago)]
            if len(week_prices) < 2:
                continue
            weekly_return = (week_prices.iloc[-1] - week_prices.iloc[0]) / week_prices.iloc[0]

            # 出来高スコア（直近5日 vs 前20日平均）
            avg_vol = volume.iloc[-25:-5].mean()
            recent_vol = volume.iloc[-5:].mean()
            vol_ratio = recent_vol / avg_vol if avg_vol > 0 else 1

            # RSI
            rsi = calc_rsi(close).iloc[-1]
            rsi_score = abs(rsi - 50) / 50  # 0〜1、50から離れるほど高い

            # 総合スコア（騰落率絶対値 + 出来高急増 + RSI偏差）
            score = abs(weekly_return) * 100 + (vol_ratio - 1) * 10 + rsi_score * 20

            scores.append({
                'ticker': ticker,
                'weeklyReturn': round(float(weekly_return) * 100, 2),
                'currentPrice': round(float(close.iloc[-1]), 2),
                'prevWeekPrice': round(float(week_prices.iloc[0]), 2),
                'volumeRatio': round(float(vol_ratio), 2),
                'rsi': round(float(rsi), 1),
                'score': round(float(score), 4)
            })
        except Exception as e:
            continue

    scores.sort(key=lambda x: x['score'], reverse=True)
    return scores[:top_n]

if __name__ == '__main__':
    tickers = get_sp500_tickers()
    top100 = screen_stocks(tickers, top_n=100)

    output = {
        'screenedAt': datetime.now().isoformat(),
        'total': len(top100),
        'stocks': top100
    }

    out_path = sys.argv[1] if len(sys.argv) > 1 else 'data/screened.json'
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Screened {len(top100)} stocks -> {out_path}", flush=True)
