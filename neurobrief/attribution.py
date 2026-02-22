from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple


DATE_FMT = "%Y-%m-%d"
WINDOW_DAYS_DEFAULT = 28


def _parse_date(date_str: str) -> Optional[datetime.date]:
    try:
        return datetime.strptime(date_str, DATE_FMT).date()
    except Exception:
        return None


def _intervention_key(event: Dict[str, Any]) -> Tuple[str, str]:
    """
    Dedup key for interventions.
    Example: ("medication", "Sertraline 50mg") or ("therapy", "CBT")
    """
    return (event.get("type", "").strip().lower(), event.get("label", "").strip().lower())


def detect_attribution_uncertainty(
    events: List[Dict[str, Any]],
    assessments: List[Dict[str, Any]],
    window_days: int = WINDOW_DAYS_DEFAULT,
    min_delta: int = 1,
) -> List[Dict[str, Any]]:
    """
    Flags periods where multiple interventions (medication/therapy) occur within
    a time window before a documented assessment score change.

    - Deterministic, rule-based (no ML).
    - Does NOT infer causality.
    - Designed for explainability in the UI/video.

    Args:
        events: list of extracted events (must include date, type, label, source_id, excerpt)
        assessments: list of extracted assessments (must include date, scale, score, source_id, excerpt)
        window_days: lookback window length (default 28 days)
        min_delta: ignore small score changes below this absolute delta (default 1)

    Returns:
        flags: list of uncertainty flag dicts
    """
    flags: List[Dict[str, Any]] = []

    # Parse + keep only well-formed assessment entries
    parsed_assessments = []
    for a in assessments:
        d = _parse_date(a.get("date", ""))
        score = a.get("score", None)
        if d is None or score is None:
            continue
        parsed_assessments.append({**a, "_date": d})

    # Sort by date
    parsed_assessments.sort(key=lambda a: a["_date"])

    # Pre-parse events once; keep only interventions with valid dates
    parsed_events = []
    for e in events:
        if e.get("type") not in {"medication", "therapy"}:
            continue
        d = _parse_date(e.get("date", ""))
        if d is None:
            continue
        parsed_events.append({**e, "_date": d})

    parsed_events.sort(key=lambda e: e["_date"])

    last_by_scale: Dict[str, Dict[str, Any]] = {}

    for current in parsed_assessments:
        scale = current.get("scale", "UNKNOWN")
        prev = last_by_scale.get(scale)
        last_by_scale[scale] = current

        if not prev:
            continue

        delta = int(current["score"]) - int(prev["score"])
        if abs(delta) < min_delta:
            continue

        assessment_date = current["_date"]
        window_start = assessment_date - timedelta(days=window_days)

        # Collect interventions within window
        in_window = [
            e for e in parsed_events
            if window_start <= e["_date"] <= assessment_date
        ]

        # Deduplicate by (type,label) so repeated mentions don't inflate counts
        seen = set()
        unique_interventions = []
        for e in in_window:
            k = _intervention_key(e)
            if k in seen:
                continue
            seen.add(k)
            unique_interventions.append(e)

        if len(unique_interventions) > 1:
            direction = "increase" if delta > 0 else "decrease"

            flags.append(
                {
                    "date": current.get("date"),
                    "scale": scale,
                    "previous_score": prev.get("score"),
                    "current_score": current.get("score"),
                    "delta": delta,
                    "direction": direction,
                    "window_days": window_days,
                    "window_start": window_start.strftime(DATE_FMT),
                    "window_end": assessment_date.strftime(DATE_FMT),
                    "issue": "Multiple concurrent interventions",
                    "explanation": (
                        f"{scale} changed from {prev.get('score')} to {current.get('score')} "
                        f"within a period containing {len(unique_interventions)} interventions. "
                        "Attribution of change to a single intervention is uncertain."
                    ),
                    "interventions": [
                        {
                            "date": e.get("date"),
                            "type": e.get("type"),
                            "label": e.get("label"),
                            "source_id": e.get("source_id"),
                            "excerpt": e.get("excerpt"),
                        }
                        for e in unique_interventions
                    ],
                    "assessment_source": {
                        "source_id": current.get("source_id"),
                        "excerpt": current.get("excerpt"),
                    },
                }
            )

    return flags
