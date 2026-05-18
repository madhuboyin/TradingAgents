from langchain_core.messages import HumanMessage, RemoveMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda
from tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_global_news,
    get_language_instruction,
    get_news,
)
from tradingagents.agents.utils.prompt_context import get_horizon_prompt
from tradingagents.dataflows.config import get_config


def create_news_analyst(llm):
    def _build_chain(state):
        current_date = state["trade_date"]
        investment_horizon = state.get("investment_horizon", "short_term")
        instrument_context = build_instrument_context(state["company_of_interest"])

        tools = [
            get_news,
            get_global_news,
        ]

        system_message = (
            "You are a news researcher tasked with analyzing recent news and trends over the past week. Please write a comprehensive report of the current state of the world that is relevant for trading and macroeconomics. Prioritize macro, sector, regulatory, and company-catalyst developments rather than social sentiment commentary. Start with get_global_news(curr_date, look_back_days, limit) for broader macroeconomic news, then use get_news(query, start_date, end_date) only for material company-specific or targeted catalysts that add incremental value beyond the separate sentiment branch. Keep tool use lean: call get_global_news at most once and call get_news at most once unless a prior result is clearly empty or irrelevant. Avoid repeating retail-sentiment framing unless it is directly newsworthy. Provide specific, actionable insights with supporting evidence to help traders make informed decisions."
            + f" {get_horizon_prompt(investment_horizon, role='news')}"
            + """ Make sure to append a Markdown table at the end of the report to organize key points in the report, organized and easy to read."""
            + get_language_instruction()
        )

        system_content = (
            system_message
            + f" For your reference, the current date is {current_date}. {instrument_context}"
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_content),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        return prompt | llm.bind_tools(tools)

    def _format_result(state, result):
        if len(result.tool_calls) == 0:
            messages = state["news_messages"]
            removal_operations = [RemoveMessage(id=m.id) for m in messages]
            return {
                "news_messages": removal_operations + [HumanMessage(content="Complete")],
                "news_report": result.content,
                "analyst_count": 1,
            }
        return {"news_messages": [result]}

    def news_analyst_node(state):
        chain = _build_chain(state)
        result = chain.invoke(state["news_messages"])
        return _format_result(state, result)

    async def news_analyst_node_async(state):
        chain = _build_chain(state)
        result = await chain.ainvoke(state["news_messages"])
        return _format_result(state, result)

    return RunnableLambda(news_analyst_node, afunc=news_analyst_node_async)
