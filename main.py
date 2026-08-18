from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any

from data_loader import fetch_market_data
from engine import run_backtest_engine
from analytics import calculate_metrics

# Inisialisasi Aplikasi FastAPI di level modul utama
app = FastAPI(
    title="Quantitative Backtesting API",
    description="Engine backend untuk analisis dan simulasi strategi trading kuantitatif.",
    version="1.0.0"
)

# Konfigurasi CORS agar frontend (React / Next.js) dapat mengakses API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------- DATA CONTRACT SCHEMAS -------------------

class BacktestRequest(BaseModel):
    symbol: str = Field(default="BTC-USD", description="Ticker simbol pasar (misal: BTC-USD, ETH-USD, AAPL)")
    period: str = Field(default="1y", description="Rentang data historis (1mo, 3mo, 6mo, 1y, 2y, 5y)")
    fast_period: int = Field(default=20, ge=2, le=200, description="Periode Fast Moving Average")
    slow_period: int = Field(default=50, ge=3, le=500, description="Periode Slow Moving Average")
    stop_loss_pct: float = Field(default=2.0, ge=0.1, le=50.0, description="Batas Stop Loss (%)")
    fee_pct: float = Field(default=0.05, ge=0.0, le=5.0, description="Fee komisi per trade (%)")
    slippage_pct: float = Field(default=0.02, ge=0.0, le=5.0, description="Estimasi slippage (%)")
    initial_capital: float = Field(default=10000.0, ge=100.0, description="Modal awal backtesting ($)")

class MetricSummary(BaseModel):
    net_profit_pct: float
    net_profit_dollar: float
    win_rate: float
    total_trades: int
    profit_factor: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float

class EquityPoint(BaseModel):
    time: str
    value: float

class CandlePoint(BaseModel):
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: float

class TradeLog(BaseModel):
    id: int
    type: str
    entry_time: str
    exit_time: str
    entry_price: float
    exit_price: float
    pnl_dollar: float
    pnl_pct: float
    status: str

class BacktestResponse(BaseModel):
    symbol: str
    summary: MetricSummary
    equity_curve: List[EquityPoint]
    candlesticks: List[CandlePoint]
    trades: List[TradeLog]

# ------------------- API ENDPOINTS -------------------

@app.get("/")
def health_check():
    return {
        "status": "online",
        "message": "Quantitative Backtester Engine API siap digunakan."
    }

@app.post("/api/run-backtest", response_model=BacktestResponse)
def handle_backtest(req: BacktestRequest):
    try:
        # 1. Unduh data pasar riil
        df = fetch_market_data(symbol=req.symbol, period=req.period)
        
        # 2. Jalankan engine simulasi
        data, trades, equity_curve = run_backtest_engine(
            df=df,
            fast_period=req.fast_period,
            slow_period=req.slow_period,
            stop_loss_pct=req.stop_loss_pct,
            fee_pct=req.fee_pct,
            slippage_pct=req.slippage_pct,
            initial_capital=req.initial_capital
        )
        
        # 3. Hitung ringkasan performa kuantitatif
        summary_dict = calculate_metrics(trades, equity_curve, req.initial_capital)
        
        # 4. Siapkan output candlestick
        candlesticks = data[['time', 'open', 'high', 'low', 'close', 'volume']].to_dict(orient="records")
        
        return BacktestResponse(
            symbol=req.symbol,
            summary=MetricSummary(**summary_dict),
            equity_curve=[EquityPoint(**p) for p in equity_curve],
            candlesticks=[CandlePoint(**c) for c in candlesticks], # type: ignore
            trades=[TradeLog(**t) for t in trades]
        )
        
    except ValueError as val_err:
        raise HTTPException(status_code=404, detail=str(val_err))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan internal: {str(e)}")

# Jalankan langsung jika dipanggil via `python main.py`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)