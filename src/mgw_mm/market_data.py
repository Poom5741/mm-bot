"""L2 order book, mid price, and volatility data provider.

Fetches and maintains real-time market data from Hyperliquid:
L2 snapshots, best bid/ask, mid price calculation, and volatility estimates.
"""

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class MarketData:
    """Provides current market state: L2 book, mid price, volatility.

    Used by the QuotingEngine to compute two-sided quotes and by the
    RiskManager to evaluate kill-switch conditions.
    """

    def __init__(self, config: Any = None) -> None:
        self.config = config
        # TODO: implement in Phase 3
