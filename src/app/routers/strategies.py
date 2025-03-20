"""
Strategy router for the Multi-Agent Trading System.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..auth import get_current_user
from ...models.user import User
from ...models.strategy import StrategyBase, StrategyCreate, StrategyInDB

router = APIRouter()

# Temporary in-memory storage for strategies (will be replaced with DB)
strategies_db = {}
strategy_id_counter = 0

class StrategyResponse(BaseModel):
    """
    Strategy response model.
    """
    id: str
    name: str
    description: str
    parameters: Dict[str, Any]
    owner_id: str
    created_at: str
    updated_at: str

@router.post("", response_model=StrategyResponse)
async def create_strategy(
    strategy: StrategyCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create a new strategy.
    """
    global strategy_id_counter
    
    strategy_id_counter += 1
    strategy_id = f"strategy_{strategy_id_counter}"
    
    import datetime
    now = datetime.datetime.utcnow().isoformat()
    
    new_strategy = {
        "id": strategy_id,
        "name": strategy.name,
        "description": strategy.description,
        "parameters": strategy.parameters,
        "owner_id": current_user.id,
        "created_at": now,
        "updated_at": now
    }
    
    strategies_db[strategy_id] = new_strategy
    
    return new_strategy

@router.get("", response_model=List[StrategyResponse])
async def list_strategies(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    List all strategies for the current user.
    """
    return [
        strategy for strategy in strategies_db.values()
        if strategy["owner_id"] == current_user.id
    ]

@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get a specific strategy.
    """
    if strategy_id not in strategies_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    strategy = strategies_db[strategy_id]
    
    # Check ownership
    if strategy["owner_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this strategy"
        )
    
    return strategy

@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: str,
    strategy_update: StrategyCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update a strategy.
    """
    if strategy_id not in strategies_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    strategy = strategies_db[strategy_id]
    
    # Check ownership
    if strategy["owner_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this strategy"
        )
    
    import datetime
    now = datetime.datetime.utcnow().isoformat()
    
    # Update strategy with fields from strategy_update
    update_data = {k: v for k, v in strategy_update.dict().items() if v is not None}
    strategy.update(update_data)
    
    strategy["updated_at"] = now
    strategies_db[strategy_id] = strategy
    
    return strategy

@router.delete("/{strategy_id}")
async def delete_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Delete a strategy.
    """
    if strategy_id not in strategies_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    strategy = strategies_db[strategy_id]
    
    # Check ownership
    if strategy["owner_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this strategy"
        )
    
    # Delete strategy
    del strategies_db[strategy_id]
    
    return {"status": "success", "message": "Strategy deleted"}