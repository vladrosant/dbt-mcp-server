"""model lineage and column lineage tools."""

from __future__ import annotations

from dbt_mcp_server.manifest import find_model, load_manifest, walk_graph


def get_model_lineage(model_name: str) -> dict:
    """upstream and downstream dependency graph for a model."""
    manifest = load_manifest()
    unique_id, _ = find_model(manifest, model_name)
    parent_map = manifest.get("parent_map", {})
    child_map = manifest.get("child_map", {})
    return {
        "model": unique_id,
        "upstream": {
            "direct": parent_map.get(unique_id, []),
            "all": walk_graph(parent_map, unique_id),
        },
        "downstream": {
            "direct": child_map.get(unique_id, []),
            "all": walk_graph(child_map, unique_id),
        },
    }


def trace_column_lineage(column: str, model: str) -> dict:
    """trace where a column in a model likely originates upstream.

    manifest.json does not contain true column-level lineage, so this walks
    the dependency graph upward and reports every upstream node (model, seed,
    snapshot, or source) that declares a column with the same name. nodes that
    declare no columns at all are listed separately, since the column may pass
    through them undeclared.
    """
    manifest = load_manifest()
    unique_id, node = find_model(manifest, model)
    parent_map = manifest.get("parent_map", {})
    column_lower = column.lower()

    declared_here = column_lower in {c.lower() for c in node.get("columns", {})}

    matches: list[dict] = []
    undeclared: list[str] = []
    for upstream_id in walk_graph(parent_map, unique_id):
        upstream = manifest.get("nodes", {}).get(upstream_id) or manifest.get(
            "sources", {}
        ).get(upstream_id)
        if upstream is None:
            continue
        columns = upstream.get("columns", {})
        if not columns:
            undeclared.append(upstream_id)
            continue
        for col_name, col_meta in columns.items():
            if col_name.lower() == column_lower:
                matches.append(
                    {
                        "node": upstream_id,
                        "resource_type": upstream.get("resource_type"),
                        "column": col_name,
                        "description": col_meta.get("description", ""),
                    }
                )

    origins = [m for m in matches if m["resource_type"] == "source"]
    return {
        "column": column,
        "model": unique_id,
        "declared_in_model": declared_here,
        "upstream_declarations": matches,
        "likely_origins": origins or matches[-1:],
        "upstream_nodes_without_declared_columns": undeclared,
        "note": (
            "traced by matching declared column names across the manifest graph. "
            "renamed or derived columns will not be matched; check the nodes "
            "listed without declared columns."
        ),
    }
