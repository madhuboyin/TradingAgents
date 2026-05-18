"""Pydantic schemas used by agents that produce structured output.

The framework's primary artifact is still prose: each agent's natural-language
reasoning is what users read in the saved markdown reports and what the
downstream agents read as context.  Structured output is layered onto the
three decision-making agents (Research Manager, Trader, Portfolio Manager)
so that:

- Their outputs follow consistent section headers across runs and providers
- Each provider's native structured-output mode is used (json_schema for
  OpenAI/xAI, response_schema for Gemini, tool-use for Anthropic)
- Schema field descriptions become the model's output instructions, freeing
  the prompt body to focus on context and the rating-scale guidance
- A render helper turns the parsed Pydantic instance back into the same
  markdown shape the rest of the system already consumes, so display,
  memory log, and saved reports keep working unchanged
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared rating types
# ---------------------------------------------------------------------------


class PortfolioRating(str, Enum):
    """5-tier rating used by the Research Manager and Portfolio Manager."""

    BUY = "Buy"
    OVERWEIGHT = "Overweight"
    HOLD = "Hold"
    UNDERWEIGHT = "Underweight"
    SELL = "Sell"


class TraderAction(str, Enum):
    """3-tier transaction direction used by the Trader.

    The Trader's job is to translate the Research Manager's investment plan
    into a concrete transaction proposal: should the desk execute a Buy, a
    Sell, or sit on Hold this round.  Position sizing and the nuanced
    Overweight / Underweight calls happen later at the Portfolio Manager.
    """

    BUY = "Buy"
    HOLD = "Hold"
    SELL = "Sell"


# ---------------------------------------------------------------------------
# Research Manager
# ---------------------------------------------------------------------------


class ResearchPlan(BaseModel):
    """Structured investment plan produced by the Research Manager.

    Hand-off to the Trader: the recommendation pins the directional view,
    the rationale captures which side of the bull/bear debate carried the
    argument, and the strategic actions translate that into concrete
    instructions the trader can execute against.
    """

    recommendation: PortfolioRating = Field(
        description=(
            "The investment recommendation. Exactly one of Buy / Overweight / "
            "Hold / Underweight / Sell. Reserve Hold for situations where the "
            "evidence on both sides is genuinely balanced; otherwise commit to "
            "the side with the stronger arguments."
        ),
    )
    bull_case_summary: str = Field(
        description=(
            "Specific summary of the strongest bullish arguments, citing the "
            "data points, catalysts, and metrics that support a more positive stance. "
            "Keep it concise but substantive."
        ),
    )
    bear_case_summary: str = Field(
        description=(
            "Specific summary of the strongest bearish arguments, citing the "
            "data points, risks, and metrics that support a more cautious stance. "
            "Keep it concise but substantive."
        ),
    )
    why_this_rating: str = Field(
        description=(
            "Balanced explanation of why the final rating lands where it does. "
            "Explain why the stock is not rated more bullish and not rated more "
            "bearish, and identify which evidence ultimately carried the decision. "
            "Be concise but specific."
        ),
    )
    strategic_actions: str = Field(
        description=(
            "Concrete steps for the trader to implement the recommendation, "
            "including position sizing guidance consistent with the rating. "
            "Keep this practical and specific, with clear actions, conditions, "
            "or thresholds where useful."
        ),
    )
    monitoring_triggers: str = Field(
        description=(
            "Key metrics, catalysts, price levels, or business developments to "
            "monitor after the decision. Include what would strengthen the thesis "
            "and what would invalidate it. Keep it concise but actionable."
        ),
    )


def render_research_plan(plan: ResearchPlan) -> str:
    """Render a ResearchPlan to markdown for storage and the trader's prompt context."""
    return "\n".join([
        f"**Recommendation**: {plan.recommendation.value}",
        "",
        f"**Bull Case Summary**: {plan.bull_case_summary}",
        "",
        f"**Bear Case Summary**: {plan.bear_case_summary}",
        "",
        f"**Why This Rating**: {plan.why_this_rating}",
        "",
        f"**Strategic Actions**: {plan.strategic_actions}",
        "",
        f"**Monitoring Triggers**: {plan.monitoring_triggers}",
    ])


# ---------------------------------------------------------------------------
# Trader
# ---------------------------------------------------------------------------


class TraderProposal(BaseModel):
    """Structured transaction proposal produced by the Trader.

    The trader reads the Research Manager's investment plan and the analyst
    reports, then turns them into a concrete transaction: what action to
    take, the reasoning that justifies it, and the practical levels for
    entry, stop-loss, and sizing.
    """

    action: TraderAction = Field(
        description="The transaction direction. Exactly one of Buy / Hold / Sell.",
    )
    reasoning: str = Field(
        description=(
            "The case for this action, anchored in the analysts' reports and "
            "the research plan. Be concise but specific, and cite the evidence "
            "that most directly justifies the action."
        ),
    )
    entry_price: Optional[float] = Field(
        default=None,
        description="Optional entry price target in the instrument's quote currency.",
    )
    stop_loss: Optional[float] = Field(
        default=None,
        description="Optional stop-loss price in the instrument's quote currency.",
    )
    position_sizing: Optional[str] = Field(
        default=None,
        description="Optional sizing guidance, ideally a short phrase such as '5% of portfolio'.",
    )


def render_trader_proposal(proposal: TraderProposal) -> str:
    """Render a TraderProposal to markdown.

    The trailing ``FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**`` line is
    preserved for backward compatibility with the analyst stop-signal text
    and any external code that greps for it.
    """
    parts = [
        f"**Action**: {proposal.action.value}",
        "",
        f"**Reasoning**: {proposal.reasoning}",
    ]
    if proposal.entry_price is not None:
        parts.extend(["", f"**Entry Price**: {proposal.entry_price}"])
    if proposal.stop_loss is not None:
        parts.extend(["", f"**Stop Loss**: {proposal.stop_loss}"])
    if proposal.position_sizing:
        parts.extend(["", f"**Position Sizing**: {proposal.position_sizing}"])
    parts.extend([
        "",
        f"FINAL TRANSACTION PROPOSAL: **{proposal.action.value.upper()}**",
    ])
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Portfolio Manager
# ---------------------------------------------------------------------------


class PortfolioDecision(BaseModel):
    """Structured output produced by the Portfolio Manager.

    The model fills every field as part of its primary LLM call; no separate
    extraction pass is required. Field descriptions double as the model's
    output instructions, so the prompt body only needs to convey context and
    the rating-scale guidance.
    """

    rating: PortfolioRating = Field(
        description=(
            "The final position rating. Exactly one of Buy / Overweight / Hold / "
            "Underweight / Sell, picked based on the analysts' debate."
        ),
    )
    executive_summary: str = Field(
        description=(
            "A concise but substantive action plan covering the current stance, "
            "how to manage exposure, and the practical next step for the stated horizon."
        ),
    )
    investment_thesis: str = Field(
        description=(
            "Core thesis anchored in specific evidence from the analysts' debate. "
            "Explain the business, financial, valuation, technical, and sentiment "
            "factors that matter most for this rating. If prior lessons are referenced "
            "in the prompt context, incorporate them; otherwise rely solely on the current analysis."
        ),
    )
    recommendation_rationale: str = Field(
        description=(
            "Balanced explanation of why the final rating is appropriate. "
            "Explicitly address the strongest opposing arguments and explain why "
            "the recommendation is not more bullish and not more bearish."
        ),
    )
    strategic_actions: str = Field(
        description=(
            "Concrete next steps for managing the position, including exposure, "
            "risk management, entries or exits, and the key conditions that would "
            "justify changing the stance."
        ),
    )
    key_risks: str = Field(
        description=(
            "Most important downside risks or failure modes that could hurt the thesis. "
            "Be specific and grounded in the current analysis."
        ),
    )
    key_catalysts: str = Field(
        description=(
            "Most important catalysts, milestones, or confirmations that could strengthen "
            "or weaken the thesis over the selected horizon."
        ),
    )
    price_target: Optional[float] = Field(
        default=None,
        description="Optional target price in the instrument's quote currency.",
    )
    time_horizon: Optional[str] = Field(
        default=None,
        description="Optional recommended holding period, ideally a short phrase such as '3-6 months'.",
    )


def render_pm_decision(decision: PortfolioDecision) -> str:
    """Render a PortfolioDecision back to the markdown shape the rest of the system expects.

    Memory log, CLI display, and saved report files all read this markdown,
    so the rendered output preserves the exact section headers (``**Rating**``,
    ``**Executive Summary**``, ``**Investment Thesis**``) that downstream
    parsers and the report writers already handle.
    """
    parts = [
        f"**Rating**: {decision.rating.value}",
        "",
        f"**Executive Summary**: {decision.executive_summary}",
        "",
        f"**Investment Thesis**: {decision.investment_thesis}",
        "",
        f"**Recommendation Rationale**: {decision.recommendation_rationale}",
        "",
        f"**Strategic Actions**: {decision.strategic_actions}",
        "",
        f"**Key Risks**: {decision.key_risks}",
        "",
        f"**Key Catalysts**: {decision.key_catalysts}",
    ]
    if decision.price_target is not None:
        parts.extend(["", f"**Price Target**: {decision.price_target}"])
    if decision.time_horizon:
        parts.extend(["", f"**Time Horizon**: {decision.time_horizon}"])
    return "\n".join(parts)
