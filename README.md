# dbt-mcp-server

mcp server that lets claude answer questions about your dbt project. model lineage, missing docs, test failures straight from `manifest.json`

stateless by design: every tool call re-reads `target/manifest.json`, so answers always reflect your latest `dbt parse`. core logic is stdlib only, with a single dependency on the official [mcp](https://pypi.org/project/mcp/) SDK. talks over stdio.

## requirements
- python 3.10+
- a dbt project with a generated `target/manifest.json` (any dbt command creates it)

## installing

```bash
pip install dbt-mcp-server
```

## configuration

| env var | required | description |
|---|---|---|
| `DBT_MANIFEST_PATH` | no | path to `manifest.json` (default: `./target/manifest.json`). `run_results.json` is expected next to it |
| `ANTHROPIC_API_KEY` | no | reserved for the planned `suggest_doc_blocks` tool, not needed yet |

## hooking it up

claude desktop: add to `claude_desktop_config.json` (settings → developer → edit config):

```json
{
  "mcpServers": {
    "dbt": {
      "command": "dbt-mcp-server",
      "env": {
        "DBT_MANIFEST_PATH": "/path/to/your/dbt_project/target/manifest.json"
      }
    }
  }
}
```

claude code:

```bash
claude mcp add dbt --env DBT_MANIFEST_PATH=/path/to/your/dbt_project/target/manifest.json -- dbt-mcp-server
```

## tools

| tool | what you get |
|---|---|
| `get_model_lineage(model_name)` | upstream and downstream dependency graph, direct and transitive |
| `find_orphan_sources()` | sources that no model references |
| `find_undocumented_models()` | models missing model-level or column-level descriptions |
| `summarize_test_failures(since)` | test failures from `run_results.json` at or after an ISO date, grouped by model |
| `trace_column_lineage(column, model)` | where a column likely originates, walking the graph upstream and matching declared column names |
| `suggest_doc_blocks(model_name)` | (planned) YAML doc block drafts from compiled SQL via the claude API |

then just ask things like:

> "what feeds into fct_orders, and what breaks downstream if i change it?"
>
> "which models are missing docs? list the undocumented columns."
>
> "summarize test failures since 2026-07-01."

note: the manifest has no true column-level lineage, so `trace_column_lineage` won't match renamed or derived columns; it flags upstream nodes without declared columns so you know where the trail could continue.

## development

```bash
git clone https://github.com/vladrosant/dbt-mcp-server
cd dbt-mcp-server
pip install -e ".[dev]"
pytest
```

## license

MIT
