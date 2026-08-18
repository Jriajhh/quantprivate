import pandas as pd
import numpy as np
from typing import List, Dict, Any

def calculate_metrics(trades: List[Dict[str, Any]], equity_curve: List[Dict[str, Any]], initial_capital: float) -> Dict[str, Any]:
    """
    Menghitung metrik performa statistik portofolio.
    """
    if not trades or len(equity_curve) < 2:
        return {
            "net_profit_pct": 0.0,
            "net_profit_dollar": 0.0,
            "win_rate": 0.0,
            "total_trades": 0,
            "profit_factor": 0.0,
            "max_drawdown": 0.0,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0
        }
        
    final_equity = equity_curve[-1]['value']
    net_profit_dollar = final_equity - initial_capital
    net_profit_pct = (net_profit_dollar / initial_capital) * 100.0
    
    wins = [t for t in trades if t['pnl_dollar'] > 0]
    losses = [t for t in trades if t['pnl_dollar'] <= 0]
    total_trades = len(trades)
    win_rate = (len(wins) / total_trades) * 100.0 if total_trades > 0 else 0.0
    
    gross_profit = sum(t['pnl_dollar'] for t in wins)
    gross_loss = abs(sum(t['pnl_dollar'] for t in losses))
    
    if gross_loss > 0:
        profit_factor = round(gross_profit / gross_loss, 2)
    else:
        profit_factor = 99.0 if gross_profit > 0 else 0.0
        
    # Kalkulasi Maximum Drawdown (MDD) bar-by-bar
    values = [p['value'] for p in equity_curve]
    peak = values[0]
    max_dd = 0.0
    for v in values:
        if v > peak:
            peak = v
        dd = ((v - peak) / peak) * 100.0
        if dd < max_dd:
            max_dd = dd
            
    # Kalkulasi Sharpe & Sortino Ratio Harian (Annualized 252 trading days)
    equity_series = pd.Series(values)
    returns = equity_series.pct_change().dropna()
    
    if len(returns) > 1 and returns.std() > 0:
        sharpe = float((returns.mean() / returns.std()) * np.sqrt(252))
        
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std()
        if downside_std > 0:
            sortino = float((returns.mean() / downside_std) * np.sqrt(252))
        else:
            sortino = sharpe
    else:
        sharpe = 0.0
        sortino = 0.0
        
    return {
        "net_profit_pct": round(net_profit_pct, 2),
        "net_profit_dollar": round(net_profit_dollar, 2),
        "win_rate": round(win_rate, 2),
        "total_trades": total_trades,
        "profit_factor": profit_factor,
        "max_drawdown": round(max_dd, 2),
        "sharpe_ratio": round(sharpe, 2),
        "sortino_ratio": round(sortino, 2)
    }