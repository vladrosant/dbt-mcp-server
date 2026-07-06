"""source hygiene tools."""

from __future__ import annotations

from dbt_mcp_server.manifest import load_manifest


def find_orphan_sources() -> dict:
    """sources defined in the project with no downstream models referencing them."""
    manifest = load_manifest()
    child_map = manifest.get("child_map", {})

    orphans = []
    total = 0
    for unique_id, source in manifest.get("sources", {}).items():
        total += 1
        if not child_map.get(unique_id):
            orphans.append(
                {
                    "unique_id": unique_id,
                    "source_name": source.get("source_name"),
                    "table_name": source.get("name"),
                    "path": source.get("original_file_path"),
                }
            )

    return {
        "total_sources": total,
        "orphan_count": len(orphans),
        "orphans": orphans,
    }
