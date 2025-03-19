from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime


class Parameter(BaseModel):
    """Model for indicator or backtesting parameter."""
    name: str
    default_value: Any
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    type: str = "float"
    description: Optional[str] = None


class Indicator(BaseModel):
    """Model for a technical indicator."""
    name: str
    description: Optional[str] = None
    parameters: Dict[str, Any] = {}


class Condition(BaseModel):
    """Model for an entry or exit condition."""
    type: str  # entry, exit
    logic: str
    description: Optional[str] = None


class PositionSizing(BaseModel):
    """Model for position sizing settings."""
    method: str = "percent"  # percent, fixed, risk_based
    value: float = 1.0


class RiskManagement(BaseModel):
    """Model for risk management settings."""
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    max_positions: int = 1


class StrategyBase(BaseModel):
    """Base strategy model with common attributes."""
    name: str = Field(..., min_length=3, max_length=100)
    strategy_type: str
    instrument: str
    frequency: str
    indicators: List[Indicator] = []
    conditions: List[Condition] = []
    position_sizing: PositionSizing = PositionSizing()
    risk_management: RiskManagement = RiskManagement()


class StrategyCreate(StrategyBase):
    """Strategy creation model."""
    pass


class StrategyInDB(StrategyBase):
    """Strategy model as stored in the database."""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    version: int = 1
    
    class Config:
        orm_mode = True


class Strategy(StrategyBase):
    """Strategy model returned to clients."""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


class BacktestRequest(BaseModel):
    """Model for backtest request."""
    strategy_id: str
    start_date: datetime
    end_date: datetime
    parameters: Optional[Dict[str, Any]] = None


class TradeRecord(BaseModel):
    """Model for individual trade in backtest results."""
    entry_time: datetime
    exit_time: Optional[datetime] = None
    instrument: str
    direction: str  # long, short
    entry_price: float
    exit_price: Optional[float] = None
    quantity: float
    profit_loss: Optional[float] = None
    profit_loss_percent: Optional[float] = None
    exit_reason: Optional[str] = None


class BacktestPerformance(BaseModel):
    """Model for backtest performance metrics."""
    total_return: float
    max_drawdown: float
    sharpe_ratio: Optional[float] = None
    trade_count: int
    win_rate: Optional[float] = None
    average_win: Optional[float] = None
    average_loss: Optional[float] = None
    profit_factor: Optional[float] = None


class BacktestResult(BaseModel):
    """Model for complete backtest results."""
    id: str
    strategy_id: str
    user_id: str
    name: str
    start_date: datetime
    end_date: datetime
    created_at: datetime
    parameters: Dict[str, Any]
    performance: BacktestPerformance
    trades: List[TradeRecord] = []