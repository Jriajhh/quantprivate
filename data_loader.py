import pandas as pd
import yfinance as yf

def fetch_market_data(symbol: str = "BTC-USD", period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    clean_symbol = symbol.strip().upper()
    if clean_symbol.endswith("USDT"):
        clean_symbol = clean_symbol.replace("USDT", "-USD")
    
    ticker = yf.Ticker(clean_symbol)
    df = ticker.history(period=period, interval=interval)
    
    if df.empty:
        raise ValueError(f"Data tidak ditemukan untuk simbol '{symbol}'.")
        
    df = df.reset_index()
    
    rename_map = {}
    for col in df.columns:
        c_lower = str(col).lower()
        if "date" in c_lower or "datetime" in c_lower:
            rename_map[col] = "time"
        elif "open" in c_lower:
            rename_map[col] = "open"
        elif "high" in c_lower:
            rename_map[col] = "high"
        elif "low" in c_lower:
            rename_map[col] = "low"
        elif "close" in c_lower and "adj" not in c_lower:
            rename_map[col] = "close"
        elif "volume" in c_lower:
            rename_map[col] = "volume"
            
    df.rename(columns=rename_map, inplace=True)
    df['time'] = pd.to_datetime(df['time']).dt.strftime('%Y-%m-%d')
    
    return df[['time', 'open', 'high', 'low', 'close', 'volume']].sort_values('time').dropna().copy()