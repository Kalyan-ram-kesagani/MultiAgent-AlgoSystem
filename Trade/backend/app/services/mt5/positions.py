"""
MT5 Positions Service

Retrieves open positions from MetaTrader 5.
Placeholder for Phase 2.
"""

from typing import List
import logging

logger = logging.getLogger(__name__)


class MT5PositionsService:
    """Retrieves open positions from MT5."""

    async def get_positions(self) -> List[dict]:
        """
        Get all open positions from MT5.

        Returns list of position dicts with symbol, direction, volume,
        entry price, current price, SL, TP, floating P&L.
        """
        logger.info("MT5 positions requested (not connected)")
        return []

    async def get_position(self, ticket: int) -> dict:
        """Get a specific position by ticket number."""
        return {}
