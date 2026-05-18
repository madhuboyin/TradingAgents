"""Earnings / catalyst analyst.

This analyst pre-fetches earnings timing, expectation context, and a compact
event inventory before making a single synthesis call. The rollout is kept
deterministic and opt-in so current recommendation quality is preserved unless
the caller explicitly selects the catalyst branch.
"""

import asyncio

from langchain_core.messages import HumanMessage, RemoveMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda

from tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_language_instruction,
)
from tradingagents.agents.utils.catalyst_data_tools import build_catalyst_inputs
from tradingagents.agents.utils.prompt_context import get_horizon_prompt
from tradingagents.dataflows.config import get_config


def create_catalyst_analyst(llm):
    """Create the Earnings / Catalyst analyst node."""

    async def _collect_inputs(state):
        ticker = state["company_of_interest"]
        curr_date = state["trade_date"]
        investment_horizon = state.get("investment_horizon", "short_term")
        config = get_config()

        lookahead_key = {
            "short_term": "catalyst_lookahead_days_short_term",
            "medium_term": "catalyst_lookahead_days_medium_term",
            "long_term": "catalyst_lookahead_days_long_term",
        }.get(investment_horizon, "catalyst_lookahead_days_short_term")

        lookahead_days = config.get(lookahead_key, 120)
        max_events = config.get("catalyst_analyst_max_events", 8)

        catalyst_inputs = await asyncio.to_thread(
            build_catalyst_inputs,
            ticker,
            curr_date,
            lookahead_days=lookahead_days,
            max_events=max_events,
        )

        return {
            "ticker": ticker,
            "curr_date": curr_date,
            "investment_horizon": investment_horizon,
            "instrument_context": build_instrument_context(ticker),
            **catalyst_inputs,
        }

    def _collect_inputs_sync(state):
        return asyncio.run(_collect_inputs(state))

    def _build_chain(inputs):
        horizon_prompt = get_horizon_prompt(inputs["investment_horizon"], role="catalyst")

        system_message = f"""You are an earnings and catalyst analyst. Your job is to map the future events most likely to move the stock over the selected horizon, using the pre-fetched blocks below.

{horizon_prompt}

Your report must:
- focus on future events and expectation-sensitive setups, not broad current-news recap
- identify the 3-8 most material catalysts
- distinguish scheduled events from likely but unscheduled catalyst clusters
- explain whether the bar is high, normal, or low where possible
- explicitly state what must go right for upside and what must go wrong for downside
- say when timing is known versus uncertain
- say when the catalyst map is sparse and confidence should be lower

Required section order:
1. Catalyst Calendar
2. Expectation Context
3. Top Bullish Catalysts
4. Top Bearish Catalysts
5. What Must Go Right
6. What Must Go Wrong
7. Catalyst Verdict
8. Markdown Table

Guardrails:
- Do not just repeat recent headlines.
- Do not speculate without an identifiable catalyst path.
- Be explicit when event timing is inferred from news rather than confirmed in a schedule.

## Earnings Calendar
<start_of_earnings_calendar>
{inputs["earnings_calendar"]}
<end_of_earnings_calendar>

## Expectation Context
<start_of_expectation_context>
{inputs["expectation_context"]}
<end_of_expectation_context>

## Event Inventory
<start_of_event_calendar>
{inputs["event_calendar"]}
<end_of_event_calendar>

For your reference, the current date is {inputs["curr_date"]}. The structured event lookahead window is {inputs["lookahead_days"]} days. {inputs["instrument_context"]}{get_language_instruction()}"""

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_message),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        return prompt | llm

    def _format_result(state, result):
        messages = state["catalyst_messages"]
        removal_operations = [RemoveMessage(id=m.id) for m in messages]
        return {
            "catalyst_messages": removal_operations + [HumanMessage(content="Complete")],
            "catalyst_report": result.content,
            "analyst_count": 1,
        }

    def catalyst_analyst_node(state):
        inputs = _collect_inputs_sync(state)
        chain = _build_chain(inputs)
        result = chain.invoke(state["catalyst_messages"])
        return _format_result(state, result)

    async def catalyst_analyst_node_async(state):
        inputs = await _collect_inputs(state)
        chain = _build_chain(inputs)
        result = await chain.ainvoke(state["catalyst_messages"])
        return _format_result(state, result)

    return RunnableLambda(catalyst_analyst_node, afunc=catalyst_analyst_node_async)
