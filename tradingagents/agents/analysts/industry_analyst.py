"""Industry / peer comparison analyst.

This analyst follows the same low-cost pattern as the fundamentals analyst:
deterministic data is pre-fetched first, then one synthesis call produces the
final report. The initial rollout uses a curated peer map to avoid unstable
auto-resolution that could degrade current recommendation quality.
"""

import asyncio

from langchain_core.messages import HumanMessage, RemoveMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda

from tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_language_instruction,
)
from tradingagents.agents.utils.industry_data_tools import build_industry_inputs
from tradingagents.agents.utils.prompt_context import get_horizon_prompt
from tradingagents.dataflows.config import get_config


def create_industry_analyst(llm):
    """Create the Industry / Peer Comparison analyst node."""

    async def _collect_inputs(state):
        ticker = state["company_of_interest"]
        curr_date = state["trade_date"]
        investment_horizon = state.get("investment_horizon", "short_term")
        config = get_config()
        max_peers = config.get("industry_analyst_max_peers", 5)
        metric_limit = config.get("industry_analyst_peer_metric_limit", 8)

        industry_inputs = await asyncio.to_thread(
            build_industry_inputs,
            ticker,
            curr_date,
            max_peers=max_peers,
            metric_limit=metric_limit,
        )

        return {
            "ticker": ticker,
            "curr_date": curr_date,
            "investment_horizon": investment_horizon,
            "instrument_context": build_instrument_context(ticker),
            "max_peers": max_peers,
            "metric_limit": metric_limit,
            **industry_inputs,
        }

    def _collect_inputs_sync(state):
        return asyncio.run(_collect_inputs(state))

    def _build_chain(inputs):
        horizon_prompt = get_horizon_prompt(inputs["investment_horizon"], role="industry")

        system_message = f"""You are an industry and peer comparison analyst. Your job is to evaluate the target company relative to credible alternatives in its peer set, using the pre-fetched fundamentals below. Add orthogonal signal relative to the standard fundamentals/news/market/sentiment stack.

{horizon_prompt}

Your report must answer:
- Is the stock attractive relative to its peers?
- Is the thesis company-specific, peer-relative, or mostly industry-cycle driven?
- Is the company best-in-class, merely average in a strong group, or weak but optically cheap?

Focus on:
- relative growth and scale
- relative margin quality and profitability
- balance-sheet quality and financial resilience
- valuation context versus peers
- whether the opportunity looks like quality leadership, cyclical beta, or a value trap

Hard constraints:
- Only use peers explicitly listed in the curated peer set and peer snapshots below.
- Do not infer, invent, simulate, or substitute peers when coverage is missing.
- Do not fabricate financial values, comparison rows, placeholder datasets, or unsupported claims.
- Do not output Python, pseudo-code, data-fetch simulations, or implementation notes.
- If peer coverage is incomplete or unavailable, say that plainly and keep the peer-relative confidence low.

Avoid repeating generic company-overview prose unless it directly helps the peer comparison. Be explicit when peer coverage is incomplete. End with a compact Markdown table summarizing the target against peers only when peer coverage is available.

## Industry Context
<start_of_industry_context>
{inputs["industry_context"]}
<end_of_industry_context>

## Peer Coverage
<start_of_peer_coverage>
Status: {inputs["peer_coverage_status"]}
{inputs["peer_selection_note"]}
<end_of_peer_coverage>

## Target Snapshot
<start_of_target_snapshot>
{inputs["target_snapshot"]}
<end_of_target_snapshot>

## Target Fundamentals (full block)
<start_of_target_fundamentals>
{inputs["target_fundamentals"]}
<end_of_target_fundamentals>

## Peer Snapshots
<start_of_peer_snapshots>
{inputs["peer_snapshots"]}
<end_of_peer_snapshots>

## Comparison Table
<start_of_comparison_table>
{inputs["comparison_table"]}
<end_of_comparison_table>

For your reference, the current date is {inputs["curr_date"]}. {inputs["instrument_context"]}{get_language_instruction()}"""

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_message),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        return prompt | llm

    def _format_result(state, result):
        messages = state["industry_messages"]
        removal_operations = [RemoveMessage(id=m.id) for m in messages]
        return {
            "industry_messages": removal_operations + [HumanMessage(content="Complete")],
            "industry_report": result.content,
            "analyst_count": 1,
        }

    def industry_analyst_node(state):
        inputs = _collect_inputs_sync(state)
        chain = _build_chain(inputs)
        result = chain.invoke(state["industry_messages"])
        return _format_result(state, result)

    async def industry_analyst_node_async(state):
        inputs = await _collect_inputs(state)
        chain = _build_chain(inputs)
        result = await chain.ainvoke(state["industry_messages"])
        return _format_result(state, result)

    return RunnableLambda(industry_analyst_node, afunc=industry_analyst_node_async)
