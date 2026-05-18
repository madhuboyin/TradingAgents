# Engineering Implementation Plan: Top 3 New Analysts

## Document Info

- Status: Draft
- Date: 2026-05-18
- Scope: Phased engineering plan for implementing:
  - Industry / Peer Comparison Analyst
  - Earnings / Catalyst Analyst
  - Macro Sensitivity Analyst
- Inputs:
  - [docs/prd_new_analysts.md](/Users/madhuboyina/Desktop/madhu/TradingAgents/docs/prd_new_analysts.md)
  - [docs/spec_industry_peer_comparison_analyst.md](/Users/madhuboyina/Desktop/madhu/TradingAgents/docs/spec_industry_peer_comparison_analyst.md)
  - [docs/spec_earnings_catalyst_analyst.md](/Users/madhuboyina/Desktop/madhu/TradingAgents/docs/spec_earnings_catalyst_analyst.md)
  - [docs/spec_macro_sensitivity_analyst.md](/Users/madhuboyina/Desktop/madhu/TradingAgents/docs/spec_macro_sensitivity_analyst.md)

---

## 1. Goal

Implement the top 3 new analysts as first-layer parallel analysts in the existing TradingAgents graph, using the current architecture and preserving the recent LLM cost optimizations.

Target analysts:

1. Industry / Peer Comparison Analyst
2. Earnings / Catalyst Analyst
3. Macro Sensitivity Analyst

Guiding constraints:

- keep the current graph structure
- prefer pre-fetch + single synthesis call
- avoid new multi-turn tool loops
- keep analyst outputs compact but high-signal
- integrate with `analyst_brief`
- make activation configurable and horizon-aware

---

## 2. Rollout Strategy

The recommended build order is:

1. Shared infrastructure for new analysts
2. Industry / Peer Comparison Analyst
3. Earnings / Catalyst Analyst
4. Macro Sensitivity Analyst
5. Analyst-brief tuning and horizon defaults
6. Integration testing and quality validation

This order is intentional:

- Industry adds the highest-value new dimension
- Catalyst complements short-term and medium-term recommendations
- Macro becomes most useful after peer and catalyst context exist

---

## 3. Cross-Cutting Work

These tasks should be completed once before implementing all three analysts.

### Phase 0: Shared Plumbing

#### 0.1 Extend agent state

Files:

- [tradingagents/agents/utils/agent_states.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/agents/utils/agent_states.py)

Tasks:

- add `industry_report`
- add `catalyst_report`
- add `macro_report`
- add `industry_messages`
- add `catalyst_messages`
- add `macro_messages`

Deliverable:

- state can represent all 3 new analyst outputs and message streams

#### 0.2 Extend initial state propagation

Files:

- [tradingagents/graph/propagation.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/graph/propagation.py)

Tasks:

- initialize empty `industry_report`
- initialize empty `catalyst_report`
- initialize empty `macro_report`
- initialize `industry_messages`
- initialize `catalyst_messages`
- initialize `macro_messages`

Deliverable:

- graph can start runs with the new analyst branches without missing state keys

#### 0.3 Add config flags and limits

Files:

- [tradingagents/default_config.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/default_config.py)

Tasks:

- add base enablement flags:
  - `industry_analyst_enabled`
  - `catalyst_analyst_enabled`
  - `macro_analyst_enabled`
- add activation defaults by horizon where applicable
- add context and data limits for each analyst
- add lookahead settings for catalyst analyst
- add peer set settings for industry analyst

Deliverable:

- new analysts are config-driven rather than hard-coded

#### 0.4 Export constructors in agents package

Files:

- `tradingagents/agents/__init__.py`

Tasks:

- export:
  - `create_industry_analyst`
  - `create_catalyst_analyst`
  - `create_macro_analyst`

Deliverable:

- graph setup can instantiate the new analysts cleanly

#### 0.5 Graph setup extensibility

Files:

- [tradingagents/graph/setup.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/graph/setup.py)

Tasks:

- add new analyst keys:
  - `industry`
  - `catalyst`
  - `macro`
- add create/delete/tool node registration pattern for each
- extend `selected_analysts` handling
- extend `sync_analysts()` to include the new report sections

Deliverable:

- the graph can run each new analyst in parallel and include it in `analyst_brief`

#### 0.6 Analyst brief section strategy

Files:

- [tradingagents/graph/setup.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/graph/setup.py)
- [tradingagents/agents/utils/prompt_context.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/agents/utils/prompt_context.py)

Tasks:

- add new section titles in `build_analyst_brief(...)` call sites
- decide whether all sections use the same char cap or analyst-specific caps
- preserve ordering that makes downstream reasoning coherent

Recommended order:

1. Market Analysis
2. Sentiment Analysis
3. News Analysis
4. Fundamentals Analysis
5. Industry / Peer Comparison
6. Earnings / Catalyst Analysis
7. Macro Sensitivity Analysis

Deliverable:

- downstream decision layers can consume the new signals in a consistent order

---

## 4. Phase 1: Industry / Peer Comparison Analyst

### 4.1 New data utilities

Create:

- `tradingagents/agents/utils/industry_data_tools.py`
- optionally `tradingagents/dataflows/peer_mapping.py`

Tasks:

- implement peer set resolver
- implement peer mapping fallback logic
- implement cached retrieval helpers
- normalize peer metric output into compact prompt-ready blocks

Suggested functions:

- `_cached_peer_set(ticker, curr_date)`
- `_cached_peer_fundamentals(peer_ticker, curr_date)`
- `_cached_peer_valuation(peer_ticker, curr_date)`
- `_cached_industry_context(ticker, curr_date)`

Deliverable:

- deterministic data layer for peer comparison

### 4.2 Peer mapping strategy

Tasks:

- create MVP peer map source
- define fallback behavior when no peer set exists
- define bounded peer count logic
- define exclusion rules for invalid peers

Recommended MVP:

- curated peer map first
- fallback to sector/industry heuristic if missing

Deliverable:

- reliable peer set selection for initial rollout

### 4.3 Analyst implementation

Create:

- `tradingagents/agents/analysts/industry_analyst.py`

Tasks:

- implement `_collect_inputs(state)`
- pre-fetch target + peer metrics
- build prompt with structured peer blocks
- generate single-pass report
- clear `industry_messages`
- write `industry_report`
- increment `analyst_count`

Deliverable:

- functioning first-layer industry analyst

### 4.4 Horizon behavior

Tasks:

- apply `get_horizon_prompt(..., role=...)`
- add industry-specific horizon emphasis in prompt body
- ensure:
  - `medium_term` and `long_term` are strongest modes
  - `short_term` stays narrower and less dominant

Deliverable:

- horizon-aware peer comparison

### 4.5 Synchronizer integration

Tasks:

- add `industry_report` to `sync_analysts()`
- tune section placement
- set initial section size policy

Deliverable:

- peer context reaches bull/bear and downstream managers

### 4.6 Tests

Add or update tests:

- state initialization tests
- prompt includes peer sections
- peer fallback works with missing data
- `industry_report` appears in `analyst_brief`
- report includes peer verdict structure

Likely files:

- `tests/test_async_analyst_execution.py`
- new analyst-focused test file if clearer

Deliverable:

- confidence that peer analyst integrates correctly

### 4.7 Validation set

Run qualitative checks on:

- `NVDA`
- `AMD`
- `CRWD`
- `SHOP`
- `JPM`

Validate:

- report is peer-relative, not generic
- report distinguishes company quality vs stock attractiveness
- final recommendations change meaningfully when peer context is material

---

## 5. Phase 2: Earnings / Catalyst Analyst

### 5.1 New data utilities

Create:

- `tradingagents/agents/utils/catalyst_data_tools.py`

Tasks:

- implement earnings calendar fetch helper
- implement expectation context helper
- implement event calendar helper
- normalize event blocks into prompt-friendly structure

Suggested functions:

- `_cached_earnings_calendar(ticker, curr_date)`
- `_cached_expectation_context(ticker, curr_date)`
- `_cached_event_calendar(ticker, curr_date, lookahead_days)`

Deliverable:

- deterministic event/catalyst data layer

### 5.2 Lookahead window logic

Tasks:

- implement horizon-specific lookahead window selection
- define short/medium/long defaults from config
- define max event count behavior
- define event sorting and prioritization rules

Deliverable:

- catalyst window behaves predictably by horizon

### 5.3 Analyst implementation

Create:

- `tradingagents/agents/analysts/catalyst_analyst.py`

Tasks:

- implement pre-fetch logic
- inject structured event blocks into prompt
- produce one-pass catalyst report
- clear `catalyst_messages`
- write `catalyst_report`
- increment `analyst_count`

Deliverable:

- functioning event/catalyst analyst

### 5.4 Role separation from News Analyst

Tasks:

- ensure prompt is about future events, not broad current-news recap
- ensure the report includes:
  - event calendar
  - expectation context
  - what must go right
  - what must go wrong
- avoid repeating existing news-analysis sections

Deliverable:

- catalyst analyst is orthogonal, not redundant

### 5.5 Synchronizer integration

Tasks:

- add `catalyst_report` to `sync_analysts()`
- place after industry report or near news depending on preferred downstream flow

Recommended order:

- after industry, before macro

Deliverable:

- event timing signal becomes available downstream

### 5.6 Tests

Add or update tests:

- lookahead respects horizon
- sparse event data degrades gracefully
- prompt includes event calendar block
- report includes “what must go right/wrong”
- `catalyst_report` appears in `analyst_brief`

Deliverable:

- reliable catalyst integration

### 5.7 Validation set

Run qualitative checks on:

- `AAPL`
- `TSLA`
- `INSM`
- `NVDA`
- `CRWD`

Validate:

- event calendar is explicit
- recommendation quality improves for catalyst-sensitive names
- the analyst adds timing detail absent from the News Analyst

---

## 6. Phase 3: Macro Sensitivity Analyst

### 6.1 New data utilities

Create:

- `tradingagents/agents/utils/macro_data_tools.py`

Tasks:

- implement macro regime helper
- implement company macro exposure helper
- implement sector template helper
- normalize macro blocks for prompt use

Suggested functions:

- `_cached_macro_regime(curr_date)`
- `_cached_company_macro_exposure(ticker, curr_date)`
- `_cached_sector_macro_template(ticker, curr_date)`

Deliverable:

- reusable macro-sensitivity data layer

### 6.2 Sector template logic

Tasks:

- define sector-aware sensitivity templates
- map core sectors to template behavior
- define fallback low-sensitivity behavior

Initial sectors to cover:

- banks
- industrials
- consumer discretionary
- semis
- software
- real estate
- energy

Deliverable:

- macro sensitivity has stock-specific structure instead of generic prose

### 6.3 Analyst implementation

Create:

- `tradingagents/agents/analysts/macro_analyst.py`

Tasks:

- implement pre-fetch logic
- inject macro regime + company exposure blocks
- generate one-pass macro sensitivity report
- clear `macro_messages`
- write `macro_report`
- increment `analyst_count`

Deliverable:

- functioning macro-sensitivity analyst

### 6.4 Distinguish from News Analyst

Tasks:

- prompt hard-separates macro transmission from macro headline recap
- require:
  - direct vs indirect sensitivity
  - macro tailwind/headwind/mixed verdict
  - stock-specific transmission explanation

Deliverable:

- macro analyst adds orthogonal value

### 6.5 Synchronizer integration

Tasks:

- add `macro_report` to `sync_analysts()`
- confirm downstream section order is still coherent

Deliverable:

- macro signal reaches debate and final recommendation layers

### 6.6 Tests

Add or update tests:

- prompt includes macro regime and exposure blocks
- low-sensitivity names do not overfit into macro narratives
- `macro_report` appears in `analyst_brief`
- stock-specific transmission language is present

Deliverable:

- stable macro analyst behavior

### 6.7 Validation set

Run qualitative checks on:

- `JPM`
- `TSLA`
- `HD`
- `UAL`
- `O`

Validate:

- rates sensitivity appears where relevant
- demand-cycle sensitivity appears where relevant
- low-sensitivity stocks are not forced into generic macro narratives

---

## 7. Phase 4: Horizon and Default Analyst Selection

After the three analysts exist, add horizon-aware analyst selection defaults.

### 7.1 Config and selection policy

Files:

- [tradingagents/default_config.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/default_config.py)
- [tradingagents/graph/setup.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/graph/setup.py)
- CLI entrypoints if analyst selection is user-configurable there

Tasks:

- define recommended analyst sets by horizon
- define whether defaults are automatic or opt-in
- ensure short-term does not get overloaded

Suggested defaults:

- `short_term`
  - market
  - social
  - news
  - fundamentals
  - catalyst
  - optionally macro
- `medium_term`
  - market
  - news
  - fundamentals
  - industry
  - catalyst
  - macro
- `long_term`
  - news
  - fundamentals
  - industry
  - macro
  - optionally market in lighter role

Deliverable:

- analyst activation aligns to horizon instead of staying static

### 7.2 Analyst brief tuning

Tasks:

- review downstream compaction once the new sections are live
- adjust per-section caps if needed
- ensure new sections do not drown out existing core signals

Deliverable:

- balanced downstream synthesis quality

---

## 8. Phase 5: Integration and Quality Validation

### 8.1 Full-flow validation

Tasks:

- run end-to-end analyses on a representative ticker set
- inspect analyst reports, `analyst_brief`, research plan, trader output, and final recommendation
- verify the new analysts are materially influencing synthesis

Deliverable:

- confidence that the new analysts improve outputs instead of adding noise

### 8.2 Regression review

Tasks:

- compare recommendation quality before/after on selected names
- confirm short-term recommendation quality is not degraded
- confirm medium-term and long-term runs improve in depth and differentiation

Deliverable:

- evidence for enabling broader rollout

### 8.3 Documentation updates

Tasks:

- update README or architecture docs if analyst list is user-visible
- update any config docs
- update UI/report docs if new analyst sections are exposed

Deliverable:

- new functionality is documented for contributors and users

---

## 9. Suggested Repo Task Breakdown by File Area

## 9.1 New files likely required

- `tradingagents/agents/analysts/industry_analyst.py`
- `tradingagents/agents/analysts/catalyst_analyst.py`
- `tradingagents/agents/analysts/macro_analyst.py`
- `tradingagents/agents/utils/industry_data_tools.py`
- `tradingagents/agents/utils/catalyst_data_tools.py`
- `tradingagents/agents/utils/macro_data_tools.py`
- optionally `tradingagents/dataflows/peer_mapping.py`

## 9.2 Core files likely modified

- [tradingagents/agents/__init__.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/agents/__init__.py)
- [tradingagents/agents/utils/agent_states.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/agents/utils/agent_states.py)
- [tradingagents/graph/propagation.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/graph/propagation.py)
- [tradingagents/graph/setup.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/graph/setup.py)
- [tradingagents/default_config.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/default_config.py)
- [tradingagents/agents/utils/prompt_context.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/agents/utils/prompt_context.py)

## 9.3 Tests likely modified or added

- `tests/test_async_analyst_execution.py`
- `tests/test_structured_agents.py`
- new analyst-specific tests for:
  - industry
  - catalyst
  - macro

---

## 10. Recommended Implementation Sequence

### Sequence A

1. Shared state/config/graph plumbing
2. Industry data utilities
3. Industry analyst
4. Industry tests and validation
5. Catalyst data utilities
6. Catalyst analyst
7. Catalyst tests and validation
8. Macro data utilities
9. Macro analyst
10. Macro tests and validation
11. Horizon-aware analyst defaults
12. Final integration pass

This is the recommended sequence because each analyst can land incrementally and be evaluated before adding the next.

---

## 11. Recommended Git / PR Breakdown

### PR 1

Shared plumbing only:

- state
- config
- graph setup hooks
- test scaffolding

### PR 2

Industry / Peer Comparison Analyst

### PR 3

Earnings / Catalyst Analyst

### PR 4

Macro Sensitivity Analyst

### PR 5

Horizon-aware analyst defaults + brief tuning + docs cleanup

This breakdown keeps risk low and makes review manageable.

---

## 12. Final Recommendation

Start implementation with:

1. shared plumbing
2. Industry / Peer Comparison Analyst

That gives the highest quality return with the cleanest fit into the current architecture.

After that:

3. Earnings / Catalyst Analyst
4. Macro Sensitivity Analyst

This sequence produces the strongest quality lift while keeping the work incremental, reviewable, and compatible with the current system design.

