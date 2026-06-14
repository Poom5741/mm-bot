"""Inventory tracker and realized/unrealized PnL calculator.

Records fills, tracks net inventory position (base and quote),
computes realized PnL from round-trips, and estimates unrealized PnL
against current mid price.
"""

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class PnLTracker:
    """Tracks inventory, realized and unrealized PnL, and fee accumulation.

    Provides inventory position to the QuotingEngine (for skew) and
    to the RiskManager (for cap enforcement).
    """

    def __init__(self, config: Any = None) -> None:
        self.config = config
        # TODO: implement in Phase 6
