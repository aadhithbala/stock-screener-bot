import requests
import os
from bs4 import BeautifulSoup
import pandas as pd
import datetime

# --- CONFIGURATION ---
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK") 

if not WEBHOOK_URL:
    raise SystemExit("DISCORD_WEBHOOK environment variable not set")


SCAN_CLAUSE = '( {cash} ( ( {cash} ( latest close > latest sma( close,200 ) and latest rsi( 14 ) > 50 and latest volume > latest sma( volume,20 ) * 1.5 ) ) ) )'

def format_volume(num):
    """Helper to make volume readable (e.g., 1.2M, 500K)"""
    num = float(num)
    if num >= 1_000_000:
        return f"{num/1_000_000:.2f}M"
    elif num >= 1_000:
        return f"{num/1_000:.2f}K"
    return str(int(num))

def get_stocks():
    try:
        with requests.Session() as s:
            # 1. Get CSRF Token
            r = s.get("https://chartink.com/screener/short-term-breakouts")
            soup = BeautifulSoup(r.content, "lxml")
            csrf = soup.find('meta', {'name': 'csrf-token'})['content']

            # 2. Fetch Data
            r = s.post("https://chartink.com/screener/process", 
                       headers={"x-csrf-token": csrf}, 
                       data={"scan_clause": SCAN_CLAUSE})
            
            data = r.json().get('data', [])
            return pd.DataFrame(data)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()

def send_discord_embed(df):
    if df.empty:
        print("No stocks found.")
        return
    
    # Sort by Change % and take top 10
    top_stocks = df.sort_values(by='per_chg', ascending=False).head(10)
    
    # --- CONSTRUCT THE EMBED ---
    
    # 1. Create the Fields List
    fields = []
    for _, row in top_stocks.iterrows():
        symbol = row['nsecode']
        price = float(row['close'])
        change = float(row['per_chg'])
        volume = format_volume(row['volume'])
        
        # Direct link to TradingView
        link = f"https://in.tradingview.com/chart/?symbol=NSE:{symbol}"
        
        
        
        # Field Value (The details)
        # We use specific formatting to make it look clean
   
        fields.append({
            "name": f"{symbol} (+{change}%)", 
            "value": f"[View Chart]({link})",
            # "inline": True  # This makes them stack side-by-side (2 per row usually)
        })

    # 2. Build the Main Embed Object
    embed = {
        "title": "Short Term Breakouts",
        "url": "https://chartink.com/screener",
        "color": 5763719,  # Decimal color code for Green (Hex #57F287)
        "fields": fields,
        "footer": {
            "text": f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }
    }

    # 3. Send Payload
    payload = {
        "username": "Anand Srinivas",
        "embeds": [embed]
    }
    
    response = requests.post(WEBHOOK_URL, json=payload)
    
    if response.status_code == 204:
        print("✅ Discord Embed sent successfully!")
    else:
        print(f"❌ Failed to send: {response.status_code} - {response.text}")

if __name__ == "__main__":
    print("Analyzing Market...")
    df = get_stocks()
    send_discord_embed(df)