import pandas as pd
from typing import Tuple, List, Dict, Any

def run_backtest_engine(
    df: pd.DataFrame, 
    fast_period: int = 20, 
    slow_period: int = 50, 
    stop_loss_pct: float = 2.0, 
    fee_pct: float = 0.05, 
    slippage_pct: float = 0.02,
    initial_capital: float = 10000.0
) -> Tuple[pd.DataFrame, List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Menjalankan simulasi transaksi bar-demi-bar.
    """
    data = df.copy()
    
    # 1. Hitung Indikator Teknis
    data['fast_ma'] = data['close'].rolling(window=max(2, fast_period)).mean()
    data['slow_ma'] = data['close'].rolling(window=max(3, slow_period)).mean()
    
    # 2. Hasilkan Sinyal & Terapkan Shift(1) untuk Mencegah Lookahead Bias
    data['raw_signal'] = 0
    data.loc[data['fast_ma'] > data['slow_ma'], 'raw_signal'] = 1
    data['exec_signal'] = data['raw_signal'].shift(1).fillna(0)
    
    trades = []
    equity = float(initial_capital)
    equity_curve = [{"time": str(data['time'].iloc[0]), "value": round(equity, 2)}]
    
    in_position = False
    entry_price = 0.0
    entry_time = ""
    trade_id = 1
    total_friction_rate = (fee_pct + slippage_pct) / 100.0

    for i in range(1, len(data)):
        current_bar = data.iloc[i]
        prev_signal = data['exec_signal'].iloc[i-1]
        curr_signal = data['exec_signal'].iloc[i]
        
        # Logika Masuk Posisi (BUY / ENTRY)
        if not in_position and curr_signal == 1 and prev_signal == 0:
            in_position = True
            entry_price = float(current_bar['open']) * (1.0 + total_friction_rate) # Penalti harga beli
            entry_time = str(current_bar['time'])
            
        # Logika Keluar Posisi (EXIT / STOP LOSS)
        elif in_position:
            # Evaluasi apakah Stop Loss tersentuh pada bar berjalan
            lowest_price = float(current_bar['low'])
            drawdown_from_entry = ((lowest_price - entry_price) / entry_price) * 100.0
            is_stop_loss = drawdown_from_entry <= -abs(stop_loss_pct)
            is_signal_exit = (curr_signal == 0 and prev_signal == 1)
            is_last_bar = (i == len(data) - 1)
            
            if is_stop_loss or is_signal_exit or is_last_bar:
                if is_stop_loss:
                    raw_exit = entry_price * (1.0 - (abs(stop_loss_pct) / 100.0))
                else:
                    raw_exit = float(current_bar['open'])
                    
                exit_price = raw_exit * (1.0 - total_friction_rate) # Penalti harga jual
                
                # Hitung PnL Transaksi
                pnl_pct = ((exit_price - entry_price) / entry_price) * 100.0
                pnl_dollar = equity * (pnl_pct / 100.0)
                equity += pnl_dollar
                
                trades.append({
                    "id": trade_id,
                    "type": "LONG",
                    "entry_time": entry_time,
                    "exit_time": str(current_bar['time']),
                    "entry_price": round(entry_price, 2),
                    "exit_price": round(exit_price, 2),
                    "pnl_dollar": round(pnl_dollar, 2),
                    "pnl_pct": round(pnl_pct, 2),
                    "status": "WIN" if pnl_dollar > 0 else "LOSS"
                })
                trade_id += 1
                in_position = False
                
        equity_curve.append({
            "time": str(current_bar['time']), 
            "value": round(equity, 2)
        })
        
    return data, trades, equity_curve