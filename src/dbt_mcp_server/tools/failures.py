"""test failure summarization from dbt's run_results.json."""

from __future__ import annotations

from datetime import datetime, timezone

from dbt_mcp_server.manifest import load_manifest, load_run_results

_FAILING_STATUSES = {"fail", "error", "warn"}


def _parse_iso(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def summarize_test_failures(since: str) -> dict:
    """test failures from run_results.json at or after `since` (ISO date string),
    grouped by the model each test attaches to."""
    try:
        cutoff = _parse_iso(since)
    except ValueError as exc:
        raise ValueError(
            f"'{since}' is not a valid ISO date string (e.g. '2026-07-01' "
            "or '2026-07-01T00:00:00Z')."
        ) from exc

    run_results = load_run_results()
    manifest = load_manifest()
    nodes = manifest.get("nodes", {})

    generated_at = run_results.get("metadata", {}).get("generated_at")
    run_time = _parse_iso(generated_at) if generated_at else None
    if run_time is not None and run_time < cutoff:
        return {
            "since": since,
            "run_generated_at": generated_at,
            "in_window": False,
            "failure_count": 0,
            "by_model": {},
            "note": "the latest run_results.json predates the requested window. "
            "dbt only keeps the most recent run's results.",
        }

    by_model: dict[str, list[dict]] = {}
    failure_count = 0
    for result in run_results.get("results", []):
        unique_id = result.get("unique_id", "")
        if not unique_id.startswith("test."):
            continue
        status = result.get("status")
        if status not in _FAILING_STATUSES:
            continue

        # result-level completed_at, when present, refines the window check.
        completed_at = None
        for timing in result.get("timing", []):
            if timing.get("name") == "execute" and timing.get("completed_at"):
                completed_at = timing["completed_at"]
        if completed_at and _parse_iso(completed_at) < cutoff:
            continue

        failure_count += 1
        test_node = nodes.get(unique_id, {})
        depends_on = test_node.get("depends_on", {}).get("nodes", [])
        models = [n for n in depends_on if n.startswith("model.")] or ["(no model)"]

        entry = {
            "test": unique_id,
            "test_name": test_node.get("name", unique_id),
            "status": status,
            "message": result.get("message"),
            "failures": result.get("failures"),
            "completed_at": completed_at,
        }
        for model_id in models:
            by_model.setdefault(model_id, []).append(entry)

    return {
        "since": since,
        "run_generated_at": generated_at,
        "in_window": True,
        "failure_count": failure_count,
        "by_model": by_model,
    }
