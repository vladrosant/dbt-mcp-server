"""doc-block suggestion tool (planned, not yet implemented).

will read the compiled SQL for a model from target/compiled/ and draft YAML
doc blocks (name + description) for each column using the claude API.
requires ANTHROPIC_API_KEY. not registered on the server yet.
"""

from __future__ import annotations


def suggest_doc_blocks(model_name: str) -> dict:
    raise NotImplementedError(
        "suggest_doc_blocks is not implemented yet. it will draft YAML doc blocks "
        "from the model's compiled SQL using the claude API (ANTHROPIC_API_KEY required)."
    )
