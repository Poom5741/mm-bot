"""Hyperliquid Info+Exchange client wrapper.

Provides a unified interface to the Hyperliquid SDK's Info and Exchange objects,
handling connection setup, API agent authentication, and order lifecycle.
"""

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class HyperliquidClient:
    """Wraps Hyperliquid Info and Exchange SDK objects for spot trading.

    Handles connection to testnet or mainnet, API agent authentication,
    order placement (post-only maker), cancellation, and L2 book queries.
    """

    def __init__(self, config: Any = None) -> None:
        self.config = config
        # TODO: implement in Phase 2
