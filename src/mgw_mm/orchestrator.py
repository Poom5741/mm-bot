"""Asyncio orchestrator — ties all components together.

The main event loop for the MGW/USDC market-maker bot. In Phase 1 this is a
skeleton that proves the async entry point works and emits structured logs.
Subsequent phases will initialize and wire up each component.
"""

import structlog

from mgw_mm.config import Settings


async def run(settings: Settings) -> None:
    """Main asyncio event loop. Ties all components together.

    Args:
        settings: Fully validated Settings object from load_settings().
    """
    logger = structlog.get_logger(__name__)

    logger.info(
        "orchestrator_starting",
        network=settings.network_config.network,
        pair=settings.trading.target_pair,
        api_url=settings.network_config.api_url,
    )

    # TODO Phase 2: Initialize HyperliquidClient and authenticate agent wallet
    # TODO Phase 3: Initialize MarketData (L2 book, mid price, volatility)
    # TODO Phase 4: Initialize QuotingEngine (two-sided maker quotes)
    # TODO Phase 6: Initialize PnLTracker (inventory and PnL accounting)
    # TODO Phase 7: Initialize RiskManager (order veto, kill-switch)
    # TODO Phase 8: Initialize TelegramBot (operator commands and alerts)
    # TODO Phase 9: Initialize AIGuardrail (advisory spread/pause suggestions)

    logger.info(
        "orchestrator_ready",
        status="skeleton_mode",
        note="No trading components initialized — Phase 1 skeleton only",
    )
