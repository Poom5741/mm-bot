"""Risk Manager: order veto, inventory caps, and kill-switch logic.

Guards all outgoing orders against configured risk limits. Enforces
MAX_INVENTORY_USDC, MAX_CAPITAL_USDC, spread bounds, and kill-switch
on volatility or drift exceeding thresholds.
"""

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class RiskManager:
    """Vetoes orders that would breach risk limits; triggers kill-switch.

    Sits between the QuotingEngine and HyperliquidClient — every proposed
    order is checked here before submission to the exchange.
    """

    def __init__(self, config: Any = None) -> None:
        self.config = config
        # TODO: implement in Phase 7
