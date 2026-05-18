import asyncio
import importlib.util
import sys
import types
from pathlib import Path


class _HumanMessage:
    def __init__(self, content=None, id="msg-1"):
        self.content = content
        self.id = id


class _RemoveMessage:
    def __init__(self, id):
        self.id = id


class _MessagesPlaceholder:
    def __init__(self, variable_name):
        self.variable_name = variable_name


class _Result:
    def __init__(self, content, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls or []


class _FakeChain:
    def __init__(self):
        self.ainvoke_calls = 0
        self.invoke_calls = 0
        self.prompt_partials = {}

    async def ainvoke(self, messages):
        self.ainvoke_calls += 1
        return _Result("async report", [])

    def invoke(self, messages):
        self.invoke_calls += 1
        return _Result("sync report", [])


class _FakePrompt:
    def __init__(self, chain):
        self.chain = chain
        self.partials = {}

    def partial(self, **kwargs):
        self.partials.update(kwargs)
        return self

    def __or__(self, other):
        merged = dict(self.chain.prompt_partials)
        merged.update(self.partials)
        self.chain.prompt_partials = merged
        return self.chain


class _FakeChatPromptTemplate:
    chain = None

    @classmethod
    def from_messages(cls, messages):
        for entry in messages:
            if isinstance(entry, tuple) and len(entry) == 2:
                message_type, content = entry
                if message_type == "system":
                    cls.chain.prompt_partials["system_message"] = content
                    break
        return _FakePrompt(cls.chain)


class _FakeTool:
    def __init__(self, name):
        self.name = name


class _FakeLLM:
    def bind_tools(self, tools):
        return self


class _FakeRunnableLambda:
    def __init__(self, func, afunc=None):
        self.func = func
        self.afunc = afunc

    def invoke(self, state):
        return self.func(state)

    async def ainvoke(self, state):
        if self.afunc is not None:
            return await self.afunc(state)
        return self.func(state)


def _install_namespace_packages():
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


def _load_market_module(chain):
    _install_namespace_packages()

    fake_messages = types.ModuleType("langchain_core.messages")
    fake_messages.HumanMessage = _HumanMessage
    fake_messages.RemoveMessage = _RemoveMessage
    sys.modules["langchain_core.messages"] = fake_messages

    fake_prompts = types.ModuleType("langchain_core.prompts")
    _FakeChatPromptTemplate.chain = chain
    fake_prompts.ChatPromptTemplate = _FakeChatPromptTemplate
    fake_prompts.MessagesPlaceholder = _MessagesPlaceholder
    sys.modules["langchain_core.prompts"] = fake_prompts

    fake_runnables = types.ModuleType("langchain_core.runnables")
    fake_runnables.RunnableLambda = _FakeRunnableLambda
    sys.modules["langchain_core.runnables"] = fake_runnables

    fake_agent_utils = types.ModuleType("tradingagents.agents.utils.agent_utils")
    fake_agent_utils.build_instrument_context = lambda ticker: f"context for {ticker}"
    fake_agent_utils.create_msg_delete = lambda *args, **kwargs: None
    fake_agent_utils.get_language_instruction = lambda: ""
    fake_agent_utils.get_stock_data = _FakeTool("get_stock_data")
    fake_agent_utils.get_indicators = _FakeTool("get_indicators")
    sys.modules["tradingagents.agents.utils.agent_utils"] = fake_agent_utils

    fake_config = types.ModuleType("tradingagents.dataflows.config")
    fake_config.get_config = lambda: {}
    sys.modules["tradingagents.dataflows.config"] = fake_config

    module_path = (
        Path(__file__).resolve().parents[1]
        / "tradingagents"
        / "agents"
        / "analysts"
        / "market_analyst.py"
    )
    spec = importlib.util.spec_from_file_location("market_analyst_test_module", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_market_analyst_uses_ainvoke():
    chain = _FakeChain()
    module = _load_market_module(chain)
    analyst = module.create_market_analyst(_FakeLLM())

    state = {
        "trade_date": "2026-05-15",
        "investment_horizon": "medium_term",
        "company_of_interest": "SHOP",
        "market_messages": [_HumanMessage("SHOP")],
    }

    result = asyncio.run(analyst.ainvoke(state))

    assert chain.ainvoke_calls == 1
    assert chain.invoke_calls == 0
    assert result["market_report"] == "async report"


def test_market_analyst_prompt_requests_batched_indicator_call():
    chain = _FakeChain()
    module = _load_market_module(chain)
    analyst = module.create_market_analyst(_FakeLLM())

    state = {
        "trade_date": "2026-05-15",
        "investment_horizon": "long_term",
        "company_of_interest": "SHOP",
        "market_messages": [_HumanMessage("SHOP")],
    }

    analyst.invoke(state)

    system_message = chain.prompt_partials["system_message"]
    assert "call get_indicators **once** with a comma-separated list" in system_message
    assert "Do not make multiple indicator-tool calls for the same report" in system_message
    assert "Do not call get_stock_data again unless the prior call clearly failed" in system_message
    assert "Investment horizon: Long term (3-5 years)." in system_message


def _load_news_module(chain):
    _install_namespace_packages()

    fake_messages = types.ModuleType("langchain_core.messages")
    fake_messages.HumanMessage = _HumanMessage
    fake_messages.RemoveMessage = _RemoveMessage
    sys.modules["langchain_core.messages"] = fake_messages

    fake_prompts = types.ModuleType("langchain_core.prompts")
    _FakeChatPromptTemplate.chain = chain
    fake_prompts.ChatPromptTemplate = _FakeChatPromptTemplate
    fake_prompts.MessagesPlaceholder = _MessagesPlaceholder
    sys.modules["langchain_core.prompts"] = fake_prompts

    fake_runnables = types.ModuleType("langchain_core.runnables")
    fake_runnables.RunnableLambda = _FakeRunnableLambda
    sys.modules["langchain_core.runnables"] = fake_runnables

    fake_agent_utils = types.ModuleType("tradingagents.agents.utils.agent_utils")
    fake_agent_utils.build_instrument_context = lambda ticker: f"context for {ticker}"
    fake_agent_utils.create_msg_delete = lambda *args, **kwargs: None
    fake_agent_utils.get_language_instruction = lambda: ""
    fake_agent_utils.get_news = _FakeTool("get_news")
    fake_agent_utils.get_global_news = _FakeTool("get_global_news")
    sys.modules["tradingagents.agents.utils.agent_utils"] = fake_agent_utils

    fake_config = types.ModuleType("tradingagents.dataflows.config")
    fake_config.get_config = lambda: {}
    sys.modules["tradingagents.dataflows.config"] = fake_config

    module_path = (
        Path(__file__).resolve().parents[1]
        / "tradingagents"
        / "agents"
        / "analysts"
        / "news_analyst.py"
    )
    spec = importlib.util.spec_from_file_location("news_analyst_test_module", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_news_analyst_prompt_prioritizes_macro_and_incremental_company_news():
    chain = _FakeChain()
    module = _load_news_module(chain)
    analyst = module.create_news_analyst(_FakeLLM())

    state = {
        "trade_date": "2026-05-15",
        "investment_horizon": "medium_term",
        "company_of_interest": "SHOP",
        "news_messages": [_HumanMessage("SHOP")],
    }

    analyst.invoke(state)

    system_message = chain.prompt_partials["system_message"]
    assert "Start with get_global_news" in system_message
    assert "only for material company-specific or targeted catalysts" in system_message
    assert "call get_global_news at most once" in system_message
    assert "call get_news at most once" in system_message
    assert "Avoid repeating retail-sentiment framing" in system_message
    assert "Investment horizon: Medium term (1-2 years)." in system_message


def _load_industry_module(chain):
    _install_namespace_packages()

    fake_messages = types.ModuleType("langchain_core.messages")
    fake_messages.HumanMessage = _HumanMessage
    fake_messages.RemoveMessage = _RemoveMessage
    sys.modules["langchain_core.messages"] = fake_messages

    fake_prompts = types.ModuleType("langchain_core.prompts")
    _FakeChatPromptTemplate.chain = chain
    fake_prompts.ChatPromptTemplate = _FakeChatPromptTemplate
    fake_prompts.MessagesPlaceholder = _MessagesPlaceholder
    sys.modules["langchain_core.prompts"] = fake_prompts

    fake_runnables = types.ModuleType("langchain_core.runnables")
    fake_runnables.RunnableLambda = _FakeRunnableLambda
    sys.modules["langchain_core.runnables"] = fake_runnables

    fake_agent_utils = types.ModuleType("tradingagents.agents.utils.agent_utils")
    fake_agent_utils.build_instrument_context = lambda ticker: f"context for {ticker}"
    fake_agent_utils.create_msg_delete = lambda *args, **kwargs: None
    fake_agent_utils.get_language_instruction = lambda: ""
    sys.modules["tradingagents.agents.utils.agent_utils"] = fake_agent_utils

    fake_industry_tools = types.ModuleType("tradingagents.agents.utils.industry_data_tools")
    fake_industry_tools.build_industry_inputs = lambda ticker, curr_date, max_peers, metric_limit: {
        "target_fundamentals": "Revenue (TTM): 100\nOperating Margin: 0.2",
        "target_snapshot": "### SHOP\n- Revenue (TTM): 100\n- Operating Margin: 0.2",
        "peer_tickers": ["AMZN", "WMT"],
        "peer_snapshots": "### AMZN\n- Revenue (TTM): 200\n\n### WMT\n- Revenue (TTM): 300",
        "industry_context": "Sector: Consumer Defensive\nIndustry: Internet Retail",
    }
    sys.modules["tradingagents.agents.utils.industry_data_tools"] = fake_industry_tools

    fake_config = types.ModuleType("tradingagents.dataflows.config")
    fake_config.get_config = lambda: {
        "industry_analyst_max_peers": 5,
        "industry_analyst_peer_metric_limit": 8,
    }
    sys.modules["tradingagents.dataflows.config"] = fake_config

    module_path = (
        Path(__file__).resolve().parents[1]
        / "tradingagents"
        / "agents"
        / "analysts"
        / "industry_analyst.py"
    )
    spec = importlib.util.spec_from_file_location("industry_analyst_test_module", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_industry_analyst_uses_ainvoke_and_includes_peer_prompting():
    chain = _FakeChain()
    module = _load_industry_module(chain)
    analyst = module.create_industry_analyst(_FakeLLM())

    state = {
        "trade_date": "2026-05-15",
        "investment_horizon": "long_term",
        "company_of_interest": "SHOP",
        "industry_messages": [_HumanMessage("SHOP")],
    }

    result = asyncio.run(analyst.ainvoke(state))

    assert chain.ainvoke_calls == 1
    assert chain.invoke_calls == 0
    assert result["industry_report"] == "async report"

    system_message = chain.prompt_partials["system_message"]
    assert "industry and peer comparison analyst" in system_message
    assert "Is the stock attractive relative to its peers?" in system_message
    assert "Investment horizon: Long term (3-5 years)." in system_message


def _load_catalyst_module(chain):
    _install_namespace_packages()

    fake_messages = types.ModuleType("langchain_core.messages")
    fake_messages.HumanMessage = _HumanMessage
    fake_messages.RemoveMessage = _RemoveMessage
    sys.modules["langchain_core.messages"] = fake_messages

    fake_prompts = types.ModuleType("langchain_core.prompts")
    _FakeChatPromptTemplate.chain = chain
    fake_prompts.ChatPromptTemplate = _FakeChatPromptTemplate
    fake_prompts.MessagesPlaceholder = _MessagesPlaceholder
    sys.modules["langchain_core.prompts"] = fake_prompts

    fake_runnables = types.ModuleType("langchain_core.runnables")
    fake_runnables.RunnableLambda = _FakeRunnableLambda
    sys.modules["langchain_core.runnables"] = fake_runnables

    fake_agent_utils = types.ModuleType("tradingagents.agents.utils.agent_utils")
    fake_agent_utils.build_instrument_context = lambda ticker: f"context for {ticker}"
    fake_agent_utils.create_msg_delete = lambda *args, **kwargs: None
    fake_agent_utils.get_language_instruction = lambda: ""
    sys.modules["tradingagents.agents.utils.agent_utils"] = fake_agent_utils

    fake_catalyst_tools = types.ModuleType("tradingagents.agents.utils.catalyst_data_tools")
    fake_catalyst_tools.build_catalyst_inputs = lambda ticker, curr_date, lookahead_days, max_events: {
        "earnings_calendar": "### SHOP Earnings Calendar\n- Earnings Date: 2026-06-01",
        "expectation_context": "### SHOP Expectation Context\n- Revenue Growth: 0.22",
        "event_calendar": "### SHOP Event Inventory\n- [Earnings] Q2 earnings setup",
        "lookahead_days": lookahead_days,
        "max_events": max_events,
    }
    sys.modules["tradingagents.agents.utils.catalyst_data_tools"] = fake_catalyst_tools

    fake_config = types.ModuleType("tradingagents.dataflows.config")
    fake_config.get_config = lambda: {
        "catalyst_lookahead_days_short_term": 120,
        "catalyst_lookahead_days_medium_term": 365,
        "catalyst_lookahead_days_long_term": 540,
        "catalyst_analyst_max_events": 8,
    }
    sys.modules["tradingagents.dataflows.config"] = fake_config

    module_path = (
        Path(__file__).resolve().parents[1]
        / "tradingagents"
        / "agents"
        / "analysts"
        / "catalyst_analyst.py"
    )
    spec = importlib.util.spec_from_file_location("catalyst_analyst_test_module", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_catalyst_analyst_uses_ainvoke_and_includes_event_blocks():
    chain = _FakeChain()
    module = _load_catalyst_module(chain)
    analyst = module.create_catalyst_analyst(_FakeLLM())

    state = {
        "trade_date": "2026-05-15",
        "investment_horizon": "short_term",
        "company_of_interest": "SHOP",
        "catalyst_messages": [_HumanMessage("SHOP")],
    }

    result = asyncio.run(analyst.ainvoke(state))

    assert chain.ainvoke_calls == 1
    assert chain.invoke_calls == 0
    assert result["catalyst_report"] == "async report"

    system_message = chain.prompt_partials["system_message"]
    assert "earnings and catalyst analyst" in system_message
    assert "Catalyst Calendar" in system_message
    assert "What Must Go Right" in system_message
    assert "lookahead window is 120 days" in system_message
