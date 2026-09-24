"""Real AI Trading & Research Agent Definition using the OpenAI Agents SDK."""
from typing import Optional
from agents import Agent

from backend.app.ai_agent.instructions import SYSTEM_INSTRUCTIONS
from backend.app.ai_agent.tools import ALL_AI_TOOLS
from backend.app.core.config import settings


def create_ai_trading_agent(model: Optional[str] = None) -> Agent:
    """
    Instantiate the unified institutional AI Trading & Research Agent.
    Equipped with complete market data, MT5 telemetry, backtesting, walk-forward,
    Monte Carlo, and non-bypassable Risk Gate tools.
    """
    selected_model = model or settings.OPENAI_MODEL or "gpt-4o-mini"
    
    agent = Agent(
        name="TradingResearchAgent",
        instructions=SYSTEM_INSTRUCTIONS,
        tools=ALL_AI_TOOLS,
        model=selected_model,
    )
    return agent


# Global agent instance
trading_research_agent = create_ai_trading_agent()
