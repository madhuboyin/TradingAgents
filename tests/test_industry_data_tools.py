import importlib.util
import sys
import types
from pathlib import Path


def _load_peer_mapping_module():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "tradingagents"
        / "dataflows"
        / "peer_mapping.py"
    )
    spec = importlib.util.spec_from_file_location("peer_mapping_test_module", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_industry_data_tools_module():
    repo_root = Path(__file__).resolve().parents[1]

    tradingagents_pkg = types.ModuleType("tradingagents")
    tradingagents_pkg.__path__ = [str(repo_root / "tradingagents")]
    sys.modules["tradingagents"] = tradingagents_pkg

    agents_pkg = types.ModuleType("tradingagents.agents")
    agents_pkg.__path__ = [str(repo_root / "tradingagents" / "agents")]
    sys.modules["tradingagents.agents"] = agents_pkg

    agents_utils_pkg = types.ModuleType("tradingagents.agents.utils")
    agents_utils_pkg.__path__ = [str(repo_root / "tradingagents" / "agents" / "utils")]
    sys.modules["tradingagents.agents.utils"] = agents_utils_pkg

    dataflows_pkg = types.ModuleType("tradingagents.dataflows")
    dataflows_pkg.__path__ = [str(repo_root / "tradingagents" / "dataflows")]
    sys.modules["tradingagents.dataflows"] = dataflows_pkg

    fake_fundamental_tools = types.ModuleType("tradingagents.agents.utils.fundamental_data_tools")
    fake_fundamental_tools._cached_fundamentals = lambda ticker, curr_date: ""
    sys.modules["tradingagents.agents.utils.fundamental_data_tools"] = fake_fundamental_tools

    module_path = (
        repo_root
        / "tradingagents"
        / "agents"
        / "utils"
        / "industry_data_tools.py"
    )
    spec = importlib.util.spec_from_file_location("industry_data_tools_test_module", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_resolve_peer_candidates_supports_goog_alias():
    module = _load_peer_mapping_module()
    assert module.resolve_peer_candidates("GOOG", max_peers=4) == ["META", "AMZN", "MSFT", "BIDU"]


def test_build_industry_inputs_returns_strict_no_peer_fallback(monkeypatch):
    module = _load_industry_data_tools_module()

    def fake_cached_fundamentals(ticker, curr_date):
        del curr_date
        return "\n".join(
            [
                f"Name: {ticker}",
                "Sector: Technology",
                "Industry: Software",
                "Revenue (TTM): 100",
                "Operating Margin: 0.2",
            ]
        )

    monkeypatch.setattr(module, "_cached_fundamentals", fake_cached_fundamentals)
    module._cached_peer_set.cache_clear()
    module._cached_peer_fundamentals.cache_clear()
    module._cached_industry_context.cache_clear()

    inputs = module.build_industry_inputs(
        "UNKNOWN",
        "2026-05-18",
        max_peers=4,
        metric_limit=5,
    )

    assert inputs["peer_coverage_status"] == "unavailable"
    assert "Do not infer, invent, or simulate peers." in inputs["peer_selection_note"]
    assert inputs["peer_snapshots"] == "Peer snapshots unavailable."
    assert inputs["comparison_table"] == "Comparison table unavailable because no curated peer set is available."
