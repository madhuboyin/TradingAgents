"""Tests for structured-output agents (Trader and Research Manager).

The Portfolio Manager has its own coverage in tests/test_memory_log.py
(which exercises the full memory-log → PM injection cycle).  This file
covers the parallel schemas, render functions, and graceful-fallback
behavior we added for the Trader and Research Manager so all three
decision-making agents share the same shape.
"""

from unittest.mock import MagicMock

import pytest

from tradingagents.agents.managers.research_manager import create_research_manager
from tradingagents.agents.schemas import (
    PortfolioRating,
    ResearchPlan,
    TraderAction,
    TraderProposal,
    render_research_plan,
    render_trader_proposal,
)
from tradingagents.agents.trader.trader import create_trader


# ---------------------------------------------------------------------------
# Render functions
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestRenderTraderProposal:
    def test_minimal_required_fields(self):
        p = TraderProposal(action=TraderAction.HOLD, reasoning="Balanced setup; no edge.")
        md = render_trader_proposal(p)
        assert "**Action**: Hold" in md
        assert "**Reasoning**: Balanced setup; no edge." in md
        # The trailing FINAL TRANSACTION PROPOSAL line is preserved for the
        # analyst stop-signal text and any external code that greps for it.
        assert "FINAL TRANSACTION PROPOSAL: **HOLD**" in md

    def test_optional_fields_included_when_present(self):
        p = TraderProposal(
            action=TraderAction.BUY,
            reasoning="Strong technicals + fundamentals.",
            entry_price=189.5,
            stop_loss=178.0,
            position_sizing="6% of portfolio",
        )
        md = render_trader_proposal(p)
        assert "**Action**: Buy" in md
        assert "**Entry Price**: 189.5" in md
        assert "**Stop Loss**: 178.0" in md
        assert "**Position Sizing**: 6% of portfolio" in md
        assert "FINAL TRANSACTION PROPOSAL: **BUY**" in md

    def test_optional_fields_omitted_when_absent(self):
        p = TraderProposal(action=TraderAction.SELL, reasoning="Guidance cut.")
        md = render_trader_proposal(p)
        assert "Entry Price" not in md
        assert "Stop Loss" not in md
        assert "Position Sizing" not in md
        assert "FINAL TRANSACTION PROPOSAL: **SELL**" in md


@pytest.mark.unit
class TestRenderResearchPlan:
    def test_required_fields(self):
        p = ResearchPlan(
            recommendation=PortfolioRating.OVERWEIGHT,
            bull_case_summary="Bull case carried on durable demand and improving margins.",
            bear_case_summary="Bear case remains focused on valuation and cyclical slowdown risk.",
            why_this_rating="The bull case is stronger, but not enough for a full Buy because valuation leaves less room for error.",
            strategic_actions="Build position over two weeks; cap at 5%.",
            monitoring_triggers="Watch next earnings for backlog conversion and any margin slippage.",
        )
        md = render_research_plan(p)
        assert "**Recommendation**: Overweight" in md
        assert "**Bull Case Summary**: Bull case carried" in md
        assert "**Bear Case Summary**: Bear case remains" in md
        assert "**Why This Rating**: The bull case is stronger" in md
        assert "**Strategic Actions**: Build position" in md
        assert "**Monitoring Triggers**: Watch next earnings" in md

    def test_all_5_tier_ratings_render(self):
        for rating in PortfolioRating:
            p = ResearchPlan(
                recommendation=rating,
                bull_case_summary="b",
                bear_case_summary="b2",
                why_this_rating="w",
                strategic_actions="s",
                monitoring_triggers="m",
            )
            md = render_research_plan(p)
            assert f"**Recommendation**: {rating.value}" in md


# ---------------------------------------------------------------------------
# Trader agent: structured happy path + fallback
# ---------------------------------------------------------------------------


def _make_trader_state():
    return {
        "company_of_interest": "NVDA",
        "investment_plan": (
            "**Recommendation**: Buy\n"
            "**Bull Case Summary**: Demand remains durable.\n"
            "**Bear Case Summary**: Valuation is elevated.\n"
            "**Why This Rating**: Bull case wins, but not enough for maximum aggression.\n"
            "**Strategic Actions**: Scale in.\n"
            "**Monitoring Triggers**: Watch earnings."
        ),
    }


def _structured_trader_llm(captured: dict, proposal: TraderProposal | None = None):
    """Build a MagicMock LLM whose with_structured_output binding captures the
    prompt and returns a real TraderProposal so render_trader_proposal works.
    """
    if proposal is None:
        proposal = TraderProposal(
            action=TraderAction.BUY,
            reasoning="Strong setup.",
        )
    structured = MagicMock()
    structured.invoke.side_effect = lambda prompt: (
        captured.__setitem__("prompt", prompt) or proposal
    )
    llm = MagicMock()
    llm.with_structured_output.return_value = structured
    return llm


@pytest.mark.unit
class TestTraderAgent:
    def test_structured_path_produces_rendered_markdown(self):
        captured = {}
        proposal = TraderProposal(
            action=TraderAction.BUY,
            reasoning="AI capex cycle intact; institutional flows constructive.",
            entry_price=189.5,
            stop_loss=178.0,
            position_sizing="6% of portfolio",
        )
        llm = _structured_trader_llm(captured, proposal)
        trader = create_trader(llm)
        result = trader(_make_trader_state())
        plan = result["trader_investment_plan"]
        assert "**Action**: Buy" in plan
        assert "**Entry Price**: 189.5" in plan
        assert "FINAL TRANSACTION PROPOSAL: **BUY**" in plan
        # The same rendered markdown is also added to messages for downstream agents.
        assert plan in result["messages"][0].content

    def test_prompt_includes_investment_plan(self):
        captured = {}
        llm = _structured_trader_llm(captured)
        trader = create_trader(llm)
        trader(_make_trader_state())
        # The investment plan is in the user message of the captured prompt.
        prompt = captured["prompt"]
        assert any("Proposed Investment Plan" in m["content"] for m in prompt)

    def test_prompt_requests_balanced_non_monotone_reasoning(self):
        captured = {}
        llm = _structured_trader_llm(captured)
        trader = create_trader(llm)
        trader(_make_trader_state())

        prompt = captured["prompt"]
        system_prompt = prompt[0]["content"]
        assert "Reflect both the evidence supporting the action and the strongest counterarguments." in system_prompt
        assert "avoid generic or one-note reasoning" in system_prompt

    def test_falls_back_to_freetext_when_structured_unavailable(self):
        plain_response = (
            "**Action**: Sell\n\nGuidance cut hits margins.\n\n"
            "FINAL TRANSACTION PROPOSAL: **SELL**"
        )
        llm = MagicMock()
        llm.with_structured_output.side_effect = NotImplementedError("provider unsupported")
        llm.invoke.return_value = MagicMock(content=plain_response)
        trader = create_trader(llm)
        result = trader(_make_trader_state())
        assert result["trader_investment_plan"] == plain_response

    def test_does_not_retry_plain_invoke_for_schema_failure(self):
        llm = MagicMock()
        structured = MagicMock()
        structured.invoke.side_effect = ValueError("schema validation failed")
        llm.with_structured_output.return_value = structured
        trader = create_trader(llm)

        with pytest.raises(ValueError):
            trader(_make_trader_state())

        llm.invoke.assert_not_called()

    def test_does_not_retry_plain_invoke_for_rate_limit_failure(self):
        llm = MagicMock()
        structured = MagicMock()
        structured.invoke.side_effect = RuntimeError("429 rate limit exceeded")
        llm.with_structured_output.return_value = structured
        trader = create_trader(llm)

        with pytest.raises(RuntimeError):
            trader(_make_trader_state())

        llm.invoke.assert_not_called()


# ---------------------------------------------------------------------------
# Research Manager agent: structured happy path + fallback
# ---------------------------------------------------------------------------


def _make_rm_state():
    return {
        "company_of_interest": "NVDA",
        "investment_debate_state": {
            "history": "Bull and bear arguments here.",
            "bull_history": "Bull says...",
            "bear_history": "Bear says...",
            "current_response": "",
            "judge_decision": "",
            "count": 1,
        },
    }


def _structured_rm_llm(captured: dict, plan: ResearchPlan | None = None):
    if plan is None:
        plan = ResearchPlan(
            recommendation=PortfolioRating.HOLD,
            bull_case_summary="Bull case highlights demand durability.",
            bear_case_summary="Bear case highlights valuation risk.",
            why_this_rating="Balanced evidence keeps the stock at Hold.",
            strategic_actions="Hold current position; reassess after earnings.",
            monitoring_triggers="Watch earnings and guide revisions.",
        )
    structured = MagicMock()
    structured.invoke.side_effect = lambda prompt: (
        captured.__setitem__("prompt", prompt) or plan
    )
    llm = MagicMock()
    llm.with_structured_output.return_value = structured
    return llm


@pytest.mark.unit
class TestResearchManagerAgent:
    def test_structured_path_produces_rendered_markdown(self):
        captured = {}
        plan = ResearchPlan(
            recommendation=PortfolioRating.OVERWEIGHT,
            bull_case_summary="Bull case is stronger; AI tailwind intact.",
            bear_case_summary="Bear case centers on elevated expectations and valuation.",
            why_this_rating="The bull case wins, but elevated expectations keep the rating at Overweight instead of Buy.",
            strategic_actions="Build position gradually over two weeks.",
            monitoring_triggers="Watch margins and bookings in the next print.",
        )
        llm = _structured_rm_llm(captured, plan)
        rm = create_research_manager(llm)
        result = rm(_make_rm_state())
        ip = result["investment_plan"]
        assert "**Recommendation**: Overweight" in ip
        assert "**Bull Case Summary**: Bull case" in ip
        assert "**Bear Case Summary**: Bear case" in ip
        assert "**Why This Rating**: The bull case wins" in ip
        assert "**Strategic Actions**: Build position" in ip
        assert "**Monitoring Triggers**: Watch margins" in ip

    def test_prompt_uses_5_tier_rating_scale(self):
        """The RM prompt must list all five tiers so the schema enum matches user expectations."""
        captured = {}
        llm = _structured_rm_llm(captured)
        rm = create_research_manager(llm)
        rm(_make_rm_state())
        prompt = captured["prompt"]
        for tier in ("Buy", "Overweight", "Hold", "Underweight", "Sell"):
            assert f"**{tier}**" in prompt, f"missing {tier} in prompt"

    def test_prompt_requests_balanced_specific_synthesis(self):
        captured = {}
        llm = _structured_rm_llm(captured)
        rm = create_research_manager(llm)
        rm(_make_rm_state())

        prompt = captured["prompt"]
        assert "capture the best bullish evidence separately" in prompt
        assert "why the recommendation is not more bullish and not more bearish" in prompt
        assert "avoid collapsing the debate into a single talking point" in prompt

    def test_prompt_includes_horizon_guidance(self):
        captured = {}
        llm = _structured_rm_llm(captured)
        rm = create_research_manager(llm)
        state = _make_rm_state()
        state["investment_horizon"] = "long_term"
        rm(state)

        prompt = captured["prompt"]
        assert "Investment horizon: Long term (3-5 years)." in prompt

    def test_falls_back_to_freetext_when_structured_unavailable(self):
        plain_response = "**Recommendation**: Sell\n\n**Rationale**: ...\n\n**Strategic Actions**: ..."
        llm = MagicMock()
        llm.with_structured_output.side_effect = NotImplementedError("provider unsupported")
        llm.invoke.return_value = MagicMock(content=plain_response)
        rm = create_research_manager(llm)
        result = rm(_make_rm_state())
        assert result["investment_plan"] == plain_response
