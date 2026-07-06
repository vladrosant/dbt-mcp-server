"""loading and querying helpers for dbt's manifest.json.

the server is stateless: every tool call re-reads the manifest from disk, so
answers always reflect the latest `dbt parse` with no cache invalidation.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

DEFAULT_MANIFEST_PATH = "./target/manifest.json"


def manifest_path() -> Path:
    return Path(os.environ.get("DBT_MANIFEST_PATH", DEFAULT_MANIFEST_PATH))


def run_results_path() -> Path:
    """run_results.json lives next to manifest.json in the dbt target dir."""
    return manifest_path().parent / "run_results.json"


def load_manifest() -> dict:
    path = manifest_path()
    if not path.exists():
        raise FileNotFoundError(
            f"manifest.json not found at '{path}'. run any dbt command (e.g. `dbt parse`) "
            "to generate it, or set DBT_MANIFEST_PATH to its location."
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_run_results() -> dict:
    path = run_results_path()
    if not path.exists():
        raise FileNotFoundError(
            f"run_results.json not found at '{path}'. run `dbt test` or `dbt build` "
            "to generate it. it is expected in the same directory as manifest.json."
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def find_model(manifest: dict, model_name: str) -> tuple[str, dict]:
    """return (unique_id, node) for a model by its short name.

    raises ValueError with the available model names if not found.
    """
    for unique_id, node in manifest.get("nodes", {}).items():
        if node.get("resource_type") == "model" and node.get("name") == model_name:
            return unique_id, node
    available = sorted(
        node.get("name", "")
        for node in manifest.get("nodes", {}).values()
        if node.get("resource_type") == "model"
    )
    raise ValueError(
        f"no model named '{model_name}' in the manifest. available models: {available}"
    )


def walk_graph(graph: dict[str, list[str]], start: str) -> list[str]:
    """breadth-first traversal of parent_map/child_map. excludes `start` itself."""
    seen = {start}
    queue = [start]
    order: list[str] = []
    while queue:
        current = queue.pop(0)
        for neighbor in graph.get(current) or []:
            if neighbor not in seen:
                seen.add(neighbor)
                order.append(neighbor)
                queue.append(neighbor)
    return order
