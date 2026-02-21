from typing import Any, Dict


def require_keys(obj: Dict[str, Any], keys: list[str]) -> None:
    missing = [k for k in keys if not obj.get(k)]
    if missing:
        raise ValueError(f"Missing mandatory field(s): {', '.join(missing)}")