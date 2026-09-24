"""AI/ML Regime Detection and Signal Filter API endpoints."""
import pandas as pd
from fastapi import APIRouter
from backend.app.agents.data.data_agent import DataAgent
from backend.app.agents.ml.ml_agent import ml_agent

router = APIRouter(prefix="/ml", tags=["AI & Machine Learning"])


@router.post("/train-regime")
def train_regime_model(symbol: str = "EURUSD", count: int = 500):
    """Train ML regime classifier using walk-forward cross-validation."""
    bars = DataAgent.generate_synthetic_data(symbol=symbol, num_bars=count)
    df = pd.DataFrame([b.model_dump() for b in bars])
    results = ml_agent.train_regime_classifier(df)
    return results


@router.get("/predict-regime/{symbol}")
def predict_current_regime(symbol: str = "EURUSD"):
    """Predict the current market regime for symbol."""
    bars = DataAgent.generate_synthetic_data(symbol=symbol, num_bars=50)
    df = pd.DataFrame([b.model_dump() for b in bars])
    regime = ml_agent.predict_regime(df)
    return {"symbol": symbol, "market_regime": regime}
