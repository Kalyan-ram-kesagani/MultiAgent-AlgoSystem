"""
MT5 Account Service

Retrieves account information from MetaTrader 5.
Placeholder for Phase 2.
"""

from typing import Optional
import logging

logger = logging.getLogger(__name__)


class MT5AccountService:
    """Retrieves account data from MT5."""

    async def get_account_info(self) -> Optional[dict]:
        """
        Get current account information from MT5.

        Returns balance, equity, margin, free margin, etc.
        """
        logger.info("MT5 account info requested (not connected)")
        return None

    async def get_balance(self) -> float:
        """Get current account balance."""
        return 0.0

    async def get_equity(self) -> float:
        """Get current account equity."""
        return 0.0
