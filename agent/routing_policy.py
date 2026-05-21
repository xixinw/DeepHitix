from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


_PRO_PREFIX_RE = re.compile(r"^\s*/pro(?:\s+|$)", re.IGNORECASE)


@dataclass(frozen=True)
class RoutingPolicyConfig:
    enabled: bool = False
    flash_model: str = ""
    pro_model: str = ""
    current_model: str = ""


@dataclass(frozen=True)
class RoutingDecision:
    model: str
    routing_decision: str
    escalation_reason: Optional[str]
    sanitized_message: str = field(repr=False)
    consume_one_shot_pro: bool = False


def resolve_turn_routing(
    user_message: str,
    config: RoutingPolicyConfig,
    *,
    one_shot_pro_pending: bool = False,
) -> RoutingDecision:
    """Resolve the model/routing metadata for one user turn.

    The first M2 policy is intentionally dumb and explicit:
    - disabled -> keep current model, no routing metadata
    - `/pro ...` -> one turn on pro, sanitized reason only
    - pending one-shot flag -> one turn on pro, then caller consumes it
    - otherwise -> flash

    Never put user text into escalation_reason; telemetry must only receive a
    bounded enum-like reason string.
    """
    message = user_message or ""
    if not config.enabled:
        return RoutingDecision(
            model=config.current_model or config.flash_model or config.pro_model,
            routing_decision="unknown",
            escalation_reason=None,
            sanitized_message=message,
            consume_one_shot_pro=False,
        )

    match = _PRO_PREFIX_RE.match(message)
    if match:
        sanitized = message[match.end():].lstrip()
        return RoutingDecision(
            model=config.pro_model or config.current_model or config.flash_model,
            routing_decision="pro",
            escalation_reason="explicit_pro_command",
            sanitized_message=sanitized,
            consume_one_shot_pro=True,
        )

    if one_shot_pro_pending:
        return RoutingDecision(
            model=config.pro_model or config.current_model or config.flash_model,
            routing_decision="pro",
            escalation_reason="one_shot_pro_pending",
            sanitized_message=message,
            consume_one_shot_pro=True,
        )

    return RoutingDecision(
        model=config.flash_model or config.current_model or config.pro_model,
        routing_decision="flash",
        escalation_reason=None,
        sanitized_message=message,
        consume_one_shot_pro=False,
    )
