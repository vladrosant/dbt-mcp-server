"""unit tests for the five implemented tools, against a minimal v12 manifest."""

from pathlib import Path

import pytest

from dbt_mcp_server.tools.docs import find_undocumented_models
from dbt_mcp_server.tools.failures import summarize_test_failures
from dbt_mcp_server.tools.lineage import get_model_lineage, trace_column_lineage
from dbt_mcp_server.tools.sources import find_orphan_sources

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def manifest_env(monkeypatch):
    monkeypatch.setenv("DBT_MANIFEST_PATH", str(FIXTURES / "manifest_v12.json"))


class TestGetModelLineage:
    def test_upstream_and_downstream(self):
        result = get_model_lineage("fct_orders")
        assert result["model"] == "model.demo.fct_orders"
        assert result["upstream"]["direct"] == ["model.demo.stg_orders"]
        assert result["upstream"]["all"] == [
            "model.demo.stg_orders",
            "source.demo.raw.orders",
        ]
        assert result["downstream"]["direct"] == [
            "test.demo.not_null_fct_orders_order_id"
        ]

    def test_unknown_model_lists_available(self):
        with pytest.raises(ValueError, match="fct_orders"):
            get_model_lineage("does_not_exist")


class TestFindOrphanSources:
    def test_finds_only_the_orphan(self):
        result = find_orphan_sources()
        assert result["total_sources"] == 2
        assert result["orphan_count"] == 1
        assert result["orphans"][0]["unique_id"] == "source.demo.raw.legacy_events"


class TestFindUndocumentedModels:
    def test_flags_missing_model_and_column_docs(self):
        result = find_undocumented_models()
        assert result["total_models"] == 2
        flagged = {m["unique_id"]: m for m in result["models"]}

        # fct_orders: no model description and an undocumented column
        fct = flagged["model.demo.fct_orders"]
        assert fct["model_description_missing"] is True
        assert fct["undocumented_columns"] == ["order_id"]

        # stg_orders: model documented, but 'amount' column is not
        stg = flagged["model.demo.stg_orders"]
        assert stg["model_description_missing"] is False
        assert stg["undocumented_columns"] == ["amount"]


class TestSummarizeTestFailures:
    def test_groups_failures_by_model(self):
        result = summarize_test_failures("2026-07-01")
        assert result["in_window"] is True
        assert result["failure_count"] == 1
        (model_id,) = result["by_model"].keys()
        assert model_id == "model.demo.fct_orders"
        failure = result["by_model"][model_id][0]
        assert failure["status"] == "fail"
        assert failure["failures"] == 3

    def test_window_after_run_returns_empty(self):
        result = summarize_test_failures("2026-07-06")
        assert result["in_window"] is False
        assert result["failure_count"] == 0

    def test_invalid_date_raises(self):
        with pytest.raises(ValueError, match="ISO date"):
            summarize_test_failures("last tuesday")


class TestTraceColumnLineage:
    def test_traces_to_source(self):
        result = trace_column_lineage("order_id", "fct_orders")
        assert result["declared_in_model"] is True
        nodes = [m["node"] for m in result["upstream_declarations"]]
        assert nodes == ["model.demo.stg_orders", "source.demo.raw.orders"]
        assert result["likely_origins"][0]["node"] == "source.demo.raw.orders"

    def test_case_insensitive(self):
        result = trace_column_lineage("ORDER_ID", "fct_orders")
        assert len(result["upstream_declarations"]) == 2

    def test_column_not_upstream(self):
        result = trace_column_lineage("amount", "fct_orders")
        nodes = [m["node"] for m in result["upstream_declarations"]]
        assert nodes == ["model.demo.stg_orders"]
        # source declares no 'amount' column, so origin falls back to last match
        assert result["likely_origins"][0]["node"] == "model.demo.stg_orders"
