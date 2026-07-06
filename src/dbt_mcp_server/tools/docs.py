"""documentation coverage tools."""

from __future__ import annotations

from dbt_mcp_server.manifest import load_manifest


def find_undocumented_models() -> dict:
    """models missing a description at the model level or at any column level."""
    manifest = load_manifest()

    undocumented = []
    total = 0
    for unique_id, node in manifest.get("nodes", {}).items():
        if node.get("resource_type") != "model":
            continue
        total += 1

        model_description_missing = not (node.get("description") or "").strip()
        columns = node.get("columns", {})
        undocumented_columns = [
            name
            for name, meta in columns.items()
            if not (meta.get("description") or "").strip()
        ]

        if model_description_missing or undocumented_columns:
            undocumented.append(
                {
                    "unique_id": unique_id,
                    "name": node.get("name"),
                    "path": node.get("original_file_path"),
                    "model_description_missing": model_description_missing,
                    "undocumented_columns": undocumented_columns,
                    "has_declared_columns": bool(columns),
                }
            )

    return {
        "total_models": total,
        "undocumented_count": len(undocumented),
        "models": undocumented,
    }
