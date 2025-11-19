import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# --- CONFIGURATION ---
WEBHOOK_URL = "https://discord.com/api/webhooks/1440621223846613074/eDyk7fXWLHk-aumUz3dQYUG9cmX_AwqMdF1PK6WyxfH3PjK4n0fjaqoZlJvs815GRKQS"

# PASTE YOUR COPIED SCAN_CLAUSE INSIDE THE QUOTES BELOW
SCAN_CLAUSE = '( {cash} ( ( {cash} ( latest close > latest sma( close,200 ) and latest rsi( 14 ) > 50 and latest volume > latest sma( volume,20 ) * 1.5 ) ) ) )'

def get_stocks():
    with requests.Session() as s:
        # 1. Get the security token (CSRF) so Chartink thinks we are a real browser
        r = s.get("https://chartink.com/screener/short-term-breakouts")
        soup = BeautifulSoup(r.content, "lxml")
        csrf = soup.find('meta', {'name': 'csrf-token'})['content']

        # 2. Ask Chartink for the data
        r = s.post("https://chartink.com/screener/process", 
                   headers={"x-csrf-token": csrf}, 
                   data={"scan_clause": SCAN_CLAUSE})
        
        return pd.DataFrame(r.json()['data'])

def send_alert(df):
    if df.empty: return
    
    # Just take top 5 stocks to avoid spamming
    top_stocks = df.sort_values(by='per_chg', ascending=False).head(10)
    
    msg = "**🔔 Market Open Alerts**\n"
    for _, row in top_stocks.iterrows():
        link = f"https://in.tradingview.com/chart/?symbol=NSE:{row['nsecode']}"
        msg += f"**{row['nsecode']}** (+{row['per_chg']}%) -> [Chart](<{link}>)\n"
        
    requests.post(WEBHOOK_URL, json={"content": msg})

if __name__ == "__main__":
    try:
        df = get_stocks()
        send_alert(df)
    except Exception as e:
        print(f"Failed: {e}")