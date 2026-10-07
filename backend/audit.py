from datetime import datetime, timezone
import json
from pathlib import Path

AUDIT_PATH = Path(__file__).resolve().parents[1] / "output" / "audit_trail.json"

def audit_event(tool_name: str, short_args: str = "", short_result: str = "", stop_reason: str = "") -> None:
    """Append one compact JSON object; the file is intentionally never truncated."""
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "time": datetime.now(timezone.utc).isoformat(),
        "tool_name": tool_name,
        "short_args": short_args[:300],
        "short_result": short_result[:500],
        "stop_reason": stop_reason,
    }
    with AUDIT_PATH.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, ensure_ascii=False) + "\n")
