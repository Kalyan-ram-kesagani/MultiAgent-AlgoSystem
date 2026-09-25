"""
MT5 Trades Service

Retrieves trade history from MetaTrader 5.
Placeholder for Phase 2.
"""

from typing import List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MT5TradesService:
    """Retrieves and synchronizes trade history from MT5."""

    async def get_history(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> List[dict]:
        """
        Get trade history from MT5.

        Returns list of closed trades within the specified date range.
        """
        logger.info("MT5 trade history requested (not connected)")
        return []

    async def sync_trades(self, account_id: str) -> int:
        """
        Synchronize trades from MT5 to database.

        Returns the number of new trades synced.
        """
        logger.info(f"MT5 trade sync requested for account {account_id}")
        return 0
