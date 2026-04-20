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

SP500_TICKERS = [
    "MMM","AOS","ABT","ABBV","ACN","ADBE","AMD","AES","AFL","A","APD","ABNB","AKAM","ALB","ARE","ALGN","ALLE","LNT","ALL","GOOGL","GOOG","MO","AMZN","AMCR","AEE","AAL","AEP","AXP","AIG","AMT","AWK","AMP","AME","AMGN","APH","ADI","ANSS","AON","APA","AAPL","AMAT","APTV","ACGL","ADM","ANET","AJG","AIZ","T","ATO","ADSK","ADP","AZO","AVB","AVY","AXON","BKR","BALL","BAC","BAX","BDX","BBY","BIO","TECH","BIIB","BLK","BX","BA","BKNG","BWA","BSX","BMY","AVGO","BR","BRO","BF-B","BLDR","BG","CDNS","CZR","CPT","CPB","COF","CAH","KMX","CCL","CARR","CTLT","CAT","CBOE","CBRE","CDW","CE","COR","CNC","CNX","CDAY","CF","CRL","SCHW","CHTR","CVX","CMG","CB","CHD","CI","CINF","CTAS","CSCO","C","CFG","CLX","CME","CMS","KO","CTSH","CL","CMCSA","CAG","COP","ED","STZ","CEG","COO","CPRT","GLW","CPAY","CTVA","CSGP","COST","CTRA","CRWD","CCI","CSX","CMI","CVS","DHR","DRI","DVA","DAY","DECK","DE","DELL","DAL","DVN","DXCM","FANG","DLR","DFS","DG","DLTR","D","DPZ","DOV","DOW","DHI","DTE","DUK","DD","EMN","ETN","EBAY","ECL","EIX","EW","EA","ELV","EMR","ENPH","ETR","EOG","EPAM","EQT","EFX","EQIX","EQR","ESS","EL","ETSY","EG","EVRG","ES","EXC","EXPE","EXPD","EXR","XOM","FFIV","FDS","FICO","FAST","FRT","FDX","FIS","FITB","FSLR","FE","FI","F","FTNT","FTV","FOXA","FOX","BEN","FCX","GRMN","IT","GE","GEHC","GEV","GEN","GNRC","GD","GIS","GM","GPC","GILD","GPN","GL","GDDY","GS","HAL","HIG","HAS","HCA","DOC","HSIC","HSY","HES","HPE","HLT","HOLX","HD","HON","HRL","HST","HWM","HPQ","HUBB","HUM","HBAN","HII","IBM","IEX","IDXX","ITW","INCY","IR","PODD","INTC","ICE","IFF","IP","IPG","INTU","ISRG","IVZ","INVH","IQV","IRM","JBAL","JKHY","J","JBL","JNPR","JPM","JNPR","K","KVUE","KDP","KEY","KEYS","KMB","KIM","KMI","KLAC","KHC","KR","LHX","LH","LRCX","LW","LVS","LDOS","LEN","LLY","LIN","LYV","LKQ","LMT","L","LOW","LULU","LYB","MTB","MRO","MPC","MKTX","MAR","MMC","MLM","MAS","MA","MTCH","MKC","MCD","MCK","MDT","MRK","META","MET","MTD","MGM","MCHP","MU","MSFT","MAA","MRNA","MHK","MOH","TAP","MDLZ","MPWR","MNST","MCO","MS","MOS","MSI","MSCI","NDAQ","NTAP","NFLX","NEM","NWSA","NWS","NEE","NKE","NI","NDSN","NSC","NTRS","NOC","NCLH","NRG","NUE","NVDA","NVR","NXPI","ORLY","OXY","ODFL","OMC","ON","OKE","ORCL","OTIS","PCAR","PKG","PLTR","PANW","PARA","PH","PAYX","PAYC","PYPL","PNR","PEP","PFE","PCG","PM","PSX","PNW","PNC","POOL","PPG","PPL","PFG","PG","PGR","PLD","PRU","PEG","PTC","PSA","PHM","QRVO","PWR","QCOM","DGX","RL","RJF","RTX","O","REG","REGN","RF","RSG","RMD","RVTY","ROK","ROL","ROP","ROST","RCL","SPGI","CRM","SBAC","SLB","STX","SRE","NOW","SHW","SPG","SWKS","SJM","SW","SNA","SOLV","SO","LUV","SWK","SBUX","STT","STLD","STE","SYK","SMCI","SYF","SNPS","SYY","TMUS","TROW","TTWO","TPR","TRGP","TGT","TEL","TDY","TFX","TER","TSLA","TXN","TPL","TXT","TMO","TJX","TSCO","TT","TDG","TRV","TRMB","TFC","TYL","TSN","USB","UBER","UDR","ULTA","UNP","UAL","UPS","URI","UNH","UHS","VLO","VTR","VLTO","VRSN","VRSK","VZ","VRTX","VIAV","VST","V","VST","WRB","GWW","WAB","WBA","WMT","DIS","WBD","WM","WAT","WEC","WFC","WELL","WST","WDC","WY","WMB","WTW","WYNN","XEL","XYL","YUM","ZBRA","ZBH","ZTS"
]

def get_sp500_tickers():
    return SP500_TICKERS

def calc_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def fetch_batch(tickers, start, end, retries=3):
    for attempt in range(retries):
        try:
            raw = yf.download(
                tickers,
                start=start,
                end=end,
                auto_adjust=True,
                threads=False,
                progress=False
            )
            return raw
        except Exception as e:
            print(f"  Batch error (attempt {attempt+1}): {e}", flush=True)
            time.sleep(10 * (attempt + 1))
    return None

def screen_stocks(tickers, top_n=100):
    end = datetime.now()
    start = end - timedelta(days=60)
    start_str = start.strftime('%Y-%m-%d')
    end_str = end.strftime('%Y-%m-%d')
    week_ago = end - timedelta(days=7)

    BATCH_SIZE = 50
    all_data = {}

    for i in range(0, len(tickers), BATCH_SIZE):
        batch = tickers[i:i+BATCH_SIZE]
        print(f"Fetching batch {i//BATCH_SIZE+1}/{(len(tickers)-1)//BATCH_SIZE+1} ({len(batch)} tickers)...", flush=True)
        raw = fetch_batch(batch, start_str, end_str)
        if raw is None:
            continue
        for ticker in batch:
            try:
                if len(batch) > 1:
                    if isinstance(raw.columns, pd.MultiIndex):
                        df = raw.xs(ticker, level=1, axis=1)
                    else:
                        df = raw[ticker]
                else:
                    df = raw
                all_data[ticker] = df.dropna()
            except:
                continue
        time.sleep(3)

    scores = []

    for ticker in tickers:
        try:
            df = all_data.get(ticker)
            if df is None or len(df) < 20:
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
