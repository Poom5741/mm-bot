"""AI advisory guardrail layer for adaptive spread, sizing, and pausing.

An optional advisory layer (not required for core operation) that analyzes
market regime and provides spread/size adjustment suggestions and auto-pause
recommendations. Deterministic core is unaffected if AI is unavailable.
"""

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class AIGuardrail:
    """Provides advisory spread/size/pause suggestions via LLM or rules.

    Runs asynchronously — its output is advisory only. If the AI call
    fails or times out, the quoting engine continues with its defaults.
    """

    def __init__(self, config: Any = None) -> None:
        self.config = config
        # TODO: implement in Phase 9
