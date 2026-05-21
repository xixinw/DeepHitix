from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional

from hermes_constants import get_hermes_home

_SECRET_FIELD_FRAGMENTS = (
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "cookie",
    "password",
    "secret",
    "token",
)
_CONTENT_FIELD_NAMES = {
    "prompt",
    "messages",
    "conversation_history",
    "request_messages",
    "assistant_message",
    "assistant_content",
    "content",
    "response",
    "raw_response",
    "tool_result",
    "tool_results",
}
_ALLOWED_EVENT_FIELDS = {
    "schema_version",
    "event_type",
    "timestamp",
    "session_id",
    "turn_id",
    "provider",
    "api_mode",
    "model",
    "call_type",
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "cache_read_tokens",
    "cache_write_tokens",
    "cache_miss_tokens",
    "reasoning_tokens",
    "cache_hit_ratio",
    "estimated_cost_usd",
    "pricing_source",
    "pricing_status",
    "latency_ms",
    "routing_decision",
    "escalation_reason",
    "tool_schema_hash",
    "immutable_prefix_hash",
    "prefix_drift_reason",
}


def _stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def compute_tool_schema_hash(tools: Any) -> str | None:
    """Return a stable digest for the active tool schema surface.

    The digest is safe for telemetry: only the hash is emitted.  Tools are
    sorted by function name so equivalent schema sets produce the same hash even
    if registration order changes.
    """
    if not tools:
        return None
    if not isinstance(tools, list):
        return _stable_hash(tools)

    def _tool_sort_key(tool: Any) -> str:
        if isinstance(tool, Mapping):
            function = tool.get("function")
            if isinstance(function, Mapping):
                return str(function.get("name") or "")
            return str(tool.get("name") or "")
        return str(tool)

    return _stable_hash(sorted(tools, key=_tool_sort_key))


def compute_immutable_prefix_hash(messages: Any) -> str | None:
    """Return a digest for the stable request prefix.

    For DeepSeek cache observability we only hash leading system/developer
    messages.  User, assistant, and tool turns are intentionally excluded so
    changing prompt text cannot leak into telemetry and does not perturb the
    immutable-prefix signal.
    """
    if not isinstance(messages, list) or not messages:
        return None
    prefix = []
    for message in messages:
        if not isinstance(message, Mapping):
            break
        if message.get("role") not in {"system", "developer"}:
            break
        prefix.append(message)
    if not prefix:
        return None
    return _stable_hash(prefix)


def default_telemetry_path() -> Path:
    return get_hermes_home() / "telemetry" / "usage.jsonl"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _is_forbidden_key(key: str) -> bool:
    k = key.lower()
    return k in _CONTENT_FIELD_NAMES or any(fragment in k for fragment in _SECRET_FIELD_FRAGMENTS)


def sanitize_event(event: Mapping[str, Any]) -> dict[str, Any]:
    """Return a secret/content-safe telemetry event.

    This is intentionally allow-list based: unexpected fields are dropped rather
    than recursively redacted. Telemetry v1 must never log prompts, responses,
    headers, tool outputs, or secrets by accident.
    """
    safe: dict[str, Any] = {}
    for key, value in event.items():
        if key not in _ALLOWED_EVENT_FIELDS:
            continue
        safe[key] = value
    return safe


def append_telemetry_event(event: Mapping[str, Any], *, path: Optional[str | Path] = None) -> bool:
    """Append one event as JSONL. Best effort: returns False on write failure."""
    target = Path(path) if path is not None else default_telemetry_path()
    safe = sanitize_event(event)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(safe, ensure_ascii=False, separators=(",", ":")) + "\n")
        return True
    except Exception:
        return False


def _format_cost_usd(amount: float | None, status: str = "unknown") -> str:
    if status == "included":
        return "included"
    if amount is None:
        return "n/a"
    prefix = "~" if status == "estimated" else ""
    if amount < 0.0001:
        return f"{prefix}${amount:.6f}"
    return f"{prefix}${amount:.4f}"


def format_llm_call_summary(event: Mapping[str, Any]) -> str:
    """Return a compact, content-safe per-call cost/cache summary.

    The summary is derived only from allow-listed telemetry fields, so it is
    safe for CLI/Gateway display and cannot include prompt or response text.
    """
    safe = sanitize_event(event)
    cost = _format_cost_usd(
        safe.get("estimated_cost_usd"),
        str(safe.get("pricing_status") or "unknown"),
    )
    total_tokens = int(safe.get("total_tokens") or 0)
    prompt_tokens = int(safe.get("prompt_tokens") or 0)
    cache_read_tokens = int(safe.get("cache_read_tokens") or 0)
    cache_write_tokens = int(safe.get("cache_write_tokens") or 0)
    latency_ms = int(safe.get("latency_ms") or 0)
    model = safe.get("model") or "unknown"
    status = safe.get("pricing_status") or "unknown"

    parts = [f"💰 Turn cost: {cost}", f"tokens {total_tokens:,}"]
    if prompt_tokens and (cache_read_tokens or cache_write_tokens):
        hit_pct = (cache_read_tokens / prompt_tokens * 100) if prompt_tokens else 0
        parts.append(
            f"cache {cache_read_tokens:,}/{prompt_tokens:,} ({hit_pct:.0f}% hit, {cache_write_tokens:,} written)"
        )
    if latency_ms:
        parts.append(f"latency {latency_ms / 1000:.1f}s")
    if status == "unknown":
        parts.append(f"pricing unknown for {model}")
    return " · ".join(parts)


def build_llm_call_event(
    *,
    provider: str,
    api_mode: str,
    model: str,
    call_type: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: int = 0,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
    cache_miss_tokens: int = 0,
    reasoning_tokens: int = 0,
    session_id: str | None = None,
    turn_id: str | None = None,
    estimated_cost_usd: float | None = None,
    pricing_source: str = "none",
    pricing_status: str = "unknown",
    latency_ms: int = 0,
    routing_decision: str = "unknown",
    escalation_reason: str | None = None,
    tool_schema_hash: str | None = None,
    immutable_prefix_hash: str | None = None,
    prefix_drift_reason: str | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    denom = cache_read_tokens + cache_miss_tokens
    cache_hit_ratio = (cache_read_tokens / denom) if denom > 0 else None
    if not total_tokens:
        total_tokens = prompt_tokens + completion_tokens
    return {
        "schema_version": 1,
        "event_type": "llm_call",
        "timestamp": timestamp or _utc_now_iso(),
        "session_id": session_id,
        "turn_id": turn_id,
        "provider": provider,
        "api_mode": api_mode,
        "model": model,
        "call_type": call_type,
        "prompt_tokens": int(prompt_tokens or 0),
        "completion_tokens": int(completion_tokens or 0),
        "total_tokens": int(total_tokens or 0),
        "cache_read_tokens": int(cache_read_tokens or 0),
        "cache_write_tokens": int(cache_write_tokens or 0),
        "cache_miss_tokens": int(cache_miss_tokens or 0),
        "reasoning_tokens": int(reasoning_tokens or 0),
        "cache_hit_ratio": cache_hit_ratio,
        "estimated_cost_usd": estimated_cost_usd,
        "pricing_source": pricing_source,
        "pricing_status": pricing_status,
        "latency_ms": int(latency_ms or 0),
        "routing_decision": routing_decision,
        "escalation_reason": escalation_reason,
        "tool_schema_hash": tool_schema_hash,
        "immutable_prefix_hash": immutable_prefix_hash,
        "prefix_drift_reason": prefix_drift_reason,
    }
