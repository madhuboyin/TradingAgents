"""Fundamentals analyst — pre-fetches all financial data before LLM invocation.

Redesigned from a tool-calling agentic loop (4–5 LLM turns) to a
single-call design: all four data sources are fetched concurrently before
the LLM is invoked and injected into the prompt as structured blocks.

Mirrors the sentiment analyst pattern and eliminates ~4× redundant
context re-transmission that the tool-calling loop caused.
"""

import asyncio

from langchain_core.messages import HumanMessage, RemoveMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda

from tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_language_instruction,
)
from tradingagents.agents.utils.fundamental_data_tools import (
    _cached_balance_sheet,
    _cached_cashflow,
    _cached_fundamentals,
    _cached_income_statement,
)
from tradingagents.agents.utils.prompt_context import get_horizon_prompt, normalize_investment_horizon


def create_fundamentals_analyst(llm):
    """Create a fundamentals analyst node.

    Pre-fetches all four financial data sources concurrently, injects them
    into the prompt, and produces a fundamentals report in a single LLM call.
    """

    async def _collect_inputs(state):
        ticker = state["company_of_interest"]
        curr_date = state["trade_date"]
        investment_horizon = state.get("investment_horizon", "short_term")
        freq = "annual" if normalize_investment_horizon(investment_horizon) == "long_term" else "quarterly"

        async def _run(fn, *args):
            try:
                return await asyncio.to_thread(fn, *args)
            except Exception as exc:
                return f"<unavailable: {type(exc).__name__}: {exc}>"

        fundamentals, balance_sheet, cashflow, income_statement = await asyncio.gather(
            _run(_cached_fundamentals, ticker, curr_date),
            _run(_cached_balance_sheet, ticker, freq, curr_date),
            _run(_cached_cashflow, ticker, freq, curr_date),
            _run(_cached_income_statement, ticker, freq, curr_date),
        )

        return {
            "ticker": ticker,
            "curr_date": curr_date,
            "investment_horizon": investment_horizon,
            "freq": freq,
            "instrument_context": build_instrument_context(ticker),
            "fundamentals": fundamentals,
            "balance_sheet": balance_sheet,
            "cashflow": cashflow,
            "income_statement": income_statement,
        }

    def _collect_inputs_sync(state):
        return asyncio.run(_collect_inputs(state))

    def _build_chain(inputs):
        horizon_prompt = get_horizon_prompt(inputs["investment_horizon"], role="fundamentals")
        freq_label = inputs["freq"].capitalize()

        system_message = f"""You are a researcher tasked with analyzing fundamental information about a company. All financial data has been pre-fetched and is provided in the sections below. Write a comprehensive report covering the company's financial health, historical performance, and key fundamental drivers to inform traders. Include as much detail as possible and provide specific, actionable insights with supporting evidence.

{horizon_prompt}

Make sure to append a Markdown table at the end of the report to organize key points, making it easy to read.

## Company Fundamentals
<start_of_fundamentals>
{inputs["fundamentals"]}
<end_of_fundamentals>

## Balance Sheet ({freq_label})
<start_of_balance_sheet>
{inputs["balance_sheet"]}
<end_of_balance_sheet>

## Cash Flow Statement ({freq_label})
<start_of_cashflow>
{inputs["cashflow"]}
<end_of_cashflow>

## Income Statement ({freq_label})
<start_of_income_statement>
{inputs["income_statement"]}
<end_of_income_statement>

For your reference, the current date is {inputs["curr_date"]}. {inputs["instrument_context"]}{get_language_instruction()}"""

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_message),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        return prompt | llm

    def _format_result(state, result):
        messages = state["fundamentals_messages"]
        removal_operations = [RemoveMessage(id=m.id) for m in messages]
        return {
            "fundamentals_messages": removal_operations + [HumanMessage(content="Complete")],
            "fundamentals_report": result.content,
            "analyst_count": 1,
        }

    def fundamentals_analyst_node(state):
        inputs = _collect_inputs_sync(state)
        chain = _build_chain(inputs)
        result = chain.invoke(state["fundamentals_messages"])
        return _format_result(state, result)

    async def fundamentals_analyst_node_async(state):
        inputs = await _collect_inputs(state)
        chain = _build_chain(inputs)
        result = await chain.ainvoke(state["fundamentals_messages"])
        return _format_result(state, result)

    return RunnableLambda(fundamentals_analyst_node, afunc=fundamentals_analyst_node_async)
