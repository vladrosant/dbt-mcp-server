"""dbt-mcp-server — MCP server entrypoint (stdio transport).

stateless by design: every tool call re-reads target/manifest.json (and
run_results.json where relevant), so answers always reflect the latest
dbt parse with no cache invalidation.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from dbt_mcp_server.tools import docs, failures, lineage, sources

mcp = FastMCP("dbt-mcp-server")


@mcp.tool()
def get_model_lineage(model_name: str) -> dict:
    """return the upstream and downstream dependency graph for a dbt model.

    args:
        model_name: the model's short name (e.g. 'fct_orders'), not its unique_id.
    """
    return lineage.get_model_lineage(model_name)


@mcp.tool()
def find_orphan_sources() -> dict:
    """return all sources defined in the dbt project that have no downstream
    models referencing them."""
    return sources.find_orphan_sources()


@mcp.tool()
def find_undocumented_models() -> dict:
    """return models missing a description at the model level or at any
    declared column level."""
    return docs.find_undocumented_models()


@mcp.tool()
def summarize_test_failures(since: str) -> dict:
    """summarize dbt test failures from run_results.json within a time window,
    grouped by model.

    args:
        since: ISO date string marking the start of the window,
            e.g. '2026-07-01' or '2026-07-01T00:00:00Z'.
    """
    return failures.summarize_test_failures(since)


@mcp.tool()
def trace_column_lineage(column: str, model: str) -> dict:
    """trace where a column in a model likely originates upstream by walking
    the manifest dependency graph and matching declared column names.

    args:
        column: the column name to trace (case-insensitive).
        model: the model's short name containing the column.
    """
    return lineage.trace_column_lineage(column, model)


def main() -> None:
    mcp.run()  # stdio transport


if __name__ == "__main__":
    main()
