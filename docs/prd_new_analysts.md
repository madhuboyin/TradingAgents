# PRD: Expand TradingAgents with New Orthogonal Analysts

## Document Info

- Status: Draft
- Date: 2026-05-18
- Scope: Product + architecture requirements for adding new analysts/agents to improve recommendation quality
- Primary goal: Improve recommendation quality by adding orthogonal signal, not duplicate narrative

---

## 1. Executive Summary

TradingAgents already has a strong multi-stage decision pipeline:

1. Parallel analyst layer
2. Bull vs bear synthesis layer
3. Trader translation layer
4. Risk debate layer
5. Final portfolio decision layer

Today, the system is strongest at combining:

- technical context
- current/recent news
- current/recent sentiment
- company fundamentals

The biggest remaining quality gaps are not “more of the same,” but missing dimensions of analysis that materially change investment conclusions:

- relative attractiveness vs peers
- timing around earnings and catalysts
- stock-specific macro transmission
- management execution quality
- durability of business quality
- valuation context across regimes
- positioning and flow pressure
- regulation and policy exposure

This PRD proposes a staged expansion of the analyst layer, starting with the highest-value additions:

1. Industry / Peer Comparison Analyst
2. Earnings / Catalyst Analyst
3. Macro Sensitivity Analyst

These three additions give the largest expected quality lift because together they cover:

- relative attractiveness
- event timing and conviction
- macro/regime context

The recommendation is to add new analysts as compact, evidence-rich, low-overlap modules that plug into the existing analyst synchronization stage, rather than adding more debate personas or generic prose agents.

---

## 2. Current System Overview

### 2.1 Existing Graph

The current workflow is defined in [tradingagents/graph/setup.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/graph/setup.py).

Current default path:

1. Parallel analyst branches
   - Market Analyst
   - Sentiment Analyst
   - News Analyst
   - Fundamentals Analyst
2. Analyst Synchronizer
3. Bull Researcher
4. Bear Researcher
5. Research Manager
6. Trader
7. Aggressive Risk Analyst
8. Conservative Risk Analyst
9. Neutral Risk Analyst
10. Portfolio Manager

The graph already supports:

- parallel analyst execution
- compact downstream analyst brief synthesis
- investment horizon support:
  - `short_term`
  - `medium_term`
  - `long_term`

### 2.2 Existing Shared State

The current shared state is defined in [tradingagents/agents/utils/agent_states.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/agents/utils/agent_states.py).

Current first-layer analyst outputs:

- `market_report`
- `sentiment_report`
- `news_report`
- `fundamentals_report`

Current downstream shared compaction:

- `analyst_brief`

### 2.3 Existing Analyst Responsibilities

#### Market Analyst

File: [tradingagents/agents/analysts/market_analyst.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/agents/analysts/market_analyst.py)

Current role:

- retrieves stock data and technical indicators
- selects a focused set of indicators
- produces a detailed technical/trend report

Strengths:

- trend and momentum interpretation
- technical timing context
- volatility context

Limitations:

- no peer-relative technical context
- no explicit catalyst timing model
- no macro transmission model

#### Sentiment Analyst

File: [tradingagents/agents/analysts/sentiment_analyst.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/agents/analysts/sentiment_analyst.py)

Current role:

- pre-fetches:
  - Yahoo Finance ticker news
  - StockTwits
  - Reddit
- synthesizes cross-source sentiment into one report

Strengths:

- retail vs institutional narrative divergence
- short-term sentiment context
- crowd attention and narrative tracking

Limitations:

- does not cover broader positioning structure
- not designed for institutional flow analysis
- useful mostly for short-term and parts of medium-term analysis

#### News Analyst

File: [tradingagents/agents/analysts/news_analyst.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/agents/analysts/news_analyst.py)

Current role:

- covers macro, sector, regulatory, and company-specific news
- starts with macro/global news
- optionally adds targeted company news

Strengths:

- current macro and sector context
- company and regulatory developments
- event-driven narrative support

Limitations:

- not a dedicated catalyst calendar
- not a structured event-timing agent
- not a stock-specific macro sensitivity model

#### Fundamentals Analyst

File: [tradingagents/agents/analysts/fundamentals_analyst.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/agents/analysts/fundamentals_analyst.py)

Current role:

- pre-fetches:
  - fundamentals overview
  - balance sheet
  - cash flow
  - income statement
- produces a single-pass fundamentals report

Strengths:

- financial health
- balance sheet, cash flow, income statement context
- current valuation/fundamental summary

Limitations:

- no structured peer comparison
- no dedicated management quality interpretation
- no moat/durability layer
- no valuation regime framing

### 2.4 Existing Synthesis Layers

#### Bull Researcher / Bear Researcher

Files:

- [tradingagents/agents/researchers/bull_researcher.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/agents/researchers/bull_researcher.py)
- [tradingagents/agents/researchers/bear_researcher.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/agents/researchers/bear_researcher.py)

Role:

- turn `analyst_brief` into adversarial bull/bear arguments

#### Research Manager

File: [tradingagents/agents/managers/research_manager.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/agents/managers/research_manager.py)

Role:

- synthesizes bull/bear debate into a structured investment plan

#### Trader

File: [tradingagents/agents/trader/trader.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/agents/trader/trader.py)

Role:

- converts the investment plan into a buy/hold/sell execution proposal

#### Risk Debate

Files:

- [tradingagents/agents/risk_mgmt/aggressive_debator.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/agents/risk_mgmt/aggressive_debator.py)
- [tradingagents/agents/risk_mgmt/conservative_debator.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/agents/risk_mgmt/conservative_debator.py)
- [tradingagents/agents/risk_mgmt/neutral_debator.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/agents/risk_mgmt/neutral_debator.py)

Role:

- debate risk posture after the trader’s plan

#### Portfolio Manager

File: [tradingagents/agents/managers/portfolio_manager.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/agents/managers/portfolio_manager.py)

Role:

- synthesizes risk debate into final structured recommendation

---

## 3. Current Quality Gaps

The system’s strongest current signals are:

- what the stock is doing
- what people are saying
- what the company’s current financials look like
- what recent news says

The biggest missing signals are:

### 3.1 Relative attractiveness

The current system is weak at answering:

- Is this the best stock in the industry?
- Is this company good, but not attractive relative to peers?
- Is the entire group expensive or cheap?

### 3.2 Event-driven timing

The current system mentions catalysts, but does not deeply structure:

- what events matter
- when they occur
- what the market expects
- what must go right or wrong

### 3.3 Stock-specific macro transmission

The current system sees macro headlines, but does not explicitly model:

- how rates, FX, input costs, demand cycles, or credit conditions flow through this stock

### 3.4 Management and durability quality

The system does not yet explicitly model:

- management credibility
- capital allocation quality
- durability of business advantage

### 3.5 Valuation and positioning context

The system lacks dedicated modules for:

- valuation under current market regime
- crowdedness / flow / short squeeze / institutional positioning

### 3.6 Regulation-heavy sectors

The system does not have a conditional specialist for:

- healthcare
- fintech
- energy
- defense
- telecom
- China-sensitive names

---

## 4. Product Goal

Add new analysts that improve recommendation quality by contributing orthogonal signal that changes the conclusion, the conviction, or the timing of the recommendation.

### 4.1 Primary Goal

Improve final recommendation quality, especially for:

- medium-term and long-term recommendations
- sector-sensitive names
- catalyst-sensitive names
- valuation-sensitive names

### 4.2 Secondary Goals

- improve explanation depth
- improve cross-factor consistency
- improve confidence calibration
- reduce false “good company therefore good stock” conclusions
- reduce false “bad chart therefore bad long-term stock” conclusions

### 4.3 Non-Goals

- reducing LLM cost
- adding more debate personas
- adding more generic news or sentiment redundancy
- replacing the current graph architecture

---

## 5. Design Principles

1. Add orthogonal signal, not duplicated prose.
2. Prefer structured evidence blocks over unconstrained narrative.
3. Avoid adding analysts whose output overlaps heavily with existing analysts.
4. Make analyst activation horizon-aware and, where appropriate, sector-aware.
5. Prefer pre-fetch + single synthesis over multi-turn tool loops when feasible.
6. Preserve the current graph and extend it incrementally.
7. Do not dilute the current short-term baseline by globally changing all analysts at once.

---

## 6. Proposed New Analysts: Ranked Portfolio

## 6.1 Industry / Peer Comparison Analyst

### Priority

Highest

### Why it matters

- answers whether the stock is attractive relative to alternatives
- catches “good company, expensive stock”
- catches “weak headline, still best-in-class operator”
- materially improves sector-sensitive recommendations

### Core questions

- Who are the right peers?
- Is the company gaining or losing relative ground?
- Is valuation premium/discount justified?
- Are margins, growth, and leverage better or worse than peers?
- Is the industry in expansion, contraction, or disruption?

### Best contribution

- peer set
- relative revenue growth
- relative margins
- relative valuation
- balance-sheet quality vs peers
- industry cycle position

### Recommended output schema

- `peer_set`
- `industry_summary`
- `relative_growth_position`
- `relative_margin_position`
- `relative_valuation_position`
- `balance_sheet_position`
- `industry_cycle_position`
- `why_this_stock_vs_peers`
- `peer_comparison_verdict`

### Recommended activation

- always-on for medium-term and long-term
- optional for short-term

### Data requirements

- peer mapping source
- peer financial metrics
- peer multiples
- sector/industry classification
- optionally price performance vs peers

### Product risk

- peer set quality is critical
- bad peer selection creates misleading output

### Recommendation

Phase 1

---

## 6.2 Earnings / Catalyst Analyst

### Priority

Very high

### Why it matters

- many stock moves are driven by upcoming events
- current system mentions catalysts, but does not deeply structure them
- improves timing and conviction

### Core questions

- What upcoming events matter?
- When do they happen?
- What does the market expect?
- What must go right for upside?
- What must go wrong for downside?

### Best contribution

- next earnings date
- expected revenue/EPS growth
- guidance trend
- major launches
- regulatory milestones
- catalyst calendar
- upside/downside scenario triggers

### Recommended output schema

- `near_term_catalysts`
- `event_calendar`
- `market_expectations`
- `bull_case_event_path`
- `bear_case_event_path`
- `must_go_right`
- `must_go_wrong`
- `catalyst_verdict`

### Recommended activation

- always-on for short-term
- high priority for medium-term
- optional summary-only for long-term

### Data requirements

- earnings calendar
- consensus estimates
- guidance history
- launch/calendar signals
- regulatory milestone feeds where relevant

### Product risk

- event-date freshness matters
- expectation data quality matters

### Recommendation

Phase 1

---

## 6.3 Macro Sensitivity Analyst

### Priority

Very high

### Why it matters

- some stocks are mostly expressions of macro conditions
- current system sees macro headlines but not stock-specific transmission
- improves cyclical and rate-sensitive names

### Core questions

- What macro variables matter most for this stock?
- Is this company rate-sensitive, FX-sensitive, commodity-sensitive, or credit-sensitive?
- Does macro context amplify or offset the company thesis?

### Best contribution

- rate sensitivity
- FX sensitivity
- energy/input cost exposure
- consumer demand sensitivity
- credit cycle exposure
- recession / soft-landing sensitivity

### Recommended output schema

- `macro_exposure_map`
- `top_macro_drivers`
- `positive_macro_scenarios`
- `negative_macro_scenarios`
- `stock_macro_transmission`
- `macro_verdict`

### Recommended activation

- always-on for medium-term
- high priority for short-term on cyclical/rate-sensitive names
- summary-only for long-term

### Data requirements

- sector mappings
- macro series context
- company/industry exposure heuristics
- optionally geography/revenue mix and cost structure inputs

### Product risk

- macro narratives can become generic unless tied tightly to company economics

### Recommendation

Phase 1

---

## 6.4 Management Quality / Execution Analyst

### Priority

High

### Why it matters

- many outcomes depend on execution quality
- often underweighted in numeric models

### Best contribution

- capital allocation quality
- guidance credibility
- dilution / buyback behavior
- acquisition track record
- margin execution
- consistency vs promises

### Recommended activation

- medium-term and long-term

### Key risk

- harder to source and score robustly

### Recommendation

Phase 2

---

## 6.5 Business Model Durability / Moat Analyst

### Priority

High

### Why it matters

- separates durable quality from temporary performance
- helps avoid overweighting short-term winners with weak long-run economics

### Best contribution

- switching costs
- network effects
- brand strength
- cost advantage
- distribution advantage
- regulatory moat
- reinvestment runway

### Recommended activation

- long-term primary
- medium-term optional

### Recommendation

Phase 3

---

## 6.6 Valuation Regime Analyst

### Priority

Moderate to high

### Why it matters

- helps avoid bullish calls on names already priced for perfection
- gives explicit regime-aware multiple context

### Best contribution

- historical multiple context
- peer-relative multiple context
- rate-regime sensitivity
- justified vs unjustified premium

### Recommended activation

- medium-term and long-term

### Recommendation

Phase 2

---

## 6.7 Positioning / Flow Analyst

### Priority

Moderate

### Why it matters

- price can move because of positioning, not fundamentals
- especially relevant for tactical trades

### Best contribution

- crowdedness
- short interest
- options skew / implied positioning
- institutional flow proxies
- squeeze / unwind risk

### Recommended activation

- short-term primary
- medium-term optional

### Recommendation

Phase 3

---

## 6.8 Regulatory / Policy Analyst

### Priority

Sector-conditional high

### Why it matters

- in certain sectors, regulation dominates fundamentals

### Best contribution

- policy risk map
- pending approvals / restrictions
- antitrust risk
- subsidy / tariff / trade exposure

### Recommended activation

- only for:
  - healthcare
  - fintech
  - energy
  - defense
  - telecom
  - China-sensitive names

### Recommendation

Phase 3 as conditional specialist

---

## 7. Prioritization

## 7.1 Best additions if only adding three

1. Industry / Peer Comparison Analyst
2. Earnings / Catalyst Analyst
3. Macro Sensitivity Analyst

Why:

- covers relative attractiveness
- covers timing and event risk
- covers broader regime/context

## 7.2 Recommended build order

1. Industry / Peer Comparison
2. Earnings / Catalyst
3. Macro Sensitivity
4. Management Quality / Execution
5. Valuation Regime
6. Business Model Durability / Moat
7. Positioning / Flow
8. Regulatory / Policy

---

## 8. Horizon Strategy

The new analysts should not all be always-on with equal weight.

### Short term (<1 year)

Highest weight:

- Market Analyst
- Sentiment Analyst
- News Analyst
- Earnings / Catalyst Analyst
- Macro Sensitivity Analyst

Supporting:

- Fundamentals Analyst
- Industry / Peer Comparison Analyst

Usually de-emphasized:

- Management Quality
- Moat / Durability

### Medium term (1-2 years)

Highest weight:

- Fundamentals Analyst
- Industry / Peer Comparison Analyst
- Earnings / Catalyst Analyst
- Macro Sensitivity Analyst
- Valuation Regime Analyst

Supporting:

- Market Analyst
- News Analyst

Lower weight:

- Sentiment Analyst

### Long term (3-5 years)

Highest weight:

- Fundamentals Analyst
- Industry / Peer Comparison Analyst
- Management Quality / Execution Analyst
- Business Model Durability / Moat Analyst
- Valuation Regime Analyst

Supporting:

- Macro Sensitivity Analyst
- News Analyst

Lowest weight:

- Sentiment Analyst
- Tactical Market Analyst

---

## 9. Architecture Requirements

## 9.1 Graph Integration

New analysts should plug into the existing parallel analyst stage in [tradingagents/graph/setup.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/graph/setup.py).

Required graph-level changes:

- add new analyst node constructors
- add tool/pre-fetch support for new analyst data sources
- add message/delete node support where needed
- extend `sync_analysts()` to merge the new reports into `analyst_brief`

### Target pattern

Prefer:

- pre-fetch deterministic data
- one LLM synthesis call

Avoid by default:

- multi-turn tool loops
- generic free-form agents with large repeated context

## 9.2 State Changes

Extend [AgentState](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/agents/utils/agent_states.py) with new first-layer outputs such as:

- `industry_report`
- `catalyst_report`
- `macro_sensitivity_report`
- `management_quality_report`
- `moat_report`
- `valuation_regime_report`
- `positioning_report`
- `regulatory_report`

Also add message histories as needed:

- `industry_messages`
- `catalyst_messages`
- `macro_messages`
- etc.

## 9.3 Analyst Brief Integration

`analyst_brief` should remain the compact downstream handoff.

Requirements:

- per-analyst section titles must be explicit
- per-analyst budgets must be configurable
- low-value sections should be de-emphasized by horizon rather than always removed

## 9.4 Configuration

Add configuration for:

- selected analysts by horizon
- conditional sector activation
- per-analyst context limits
- per-analyst data-source limits
- peer set size
- catalyst calendar lookahead windows

Example config additions:

- `peer_analyst_enabled`
- `peer_analyst_max_peers`
- `catalyst_analyst_enabled`
- `catalyst_lookahead_days`
- `macro_analyst_enabled`
- `regulatory_analyst_enabled_sectors`

---

## 10. Data Requirements

## 10.1 Industry / Peer Comparison

Needed:

- industry classification
- peer set mapping
- peer revenue growth
- peer margins
- peer leverage / balance sheet
- peer valuation multiples

## 10.2 Earnings / Catalyst

Needed:

- earnings calendar
- consensus EPS / revenue expectations
- guidance history
- catalyst/event feed
- product / regulatory event tracking

## 10.3 Macro Sensitivity

Needed:

- company geographic exposure
- input-cost sensitivity
- rate sensitivity heuristics
- sector sensitivity templates
- macro series context

## 10.4 Management Quality / Moat / Valuation / Positioning / Regulation

Needed over time:

- capital allocation history
- buybacks/dilution/acquisition history
- historical valuation bands
- short interest / options context
- policy and regulatory milestone feeds

---

## 11. UX and Output Requirements

The user-facing recommendation should surface the new signal areas clearly, not bury them.

### Final report requirements

When new analysts are enabled, the final recommendation should visibly incorporate:

- peer-relative attractiveness
- event/catalyst timing
- macro exposure
- management quality or moat where applicable

### Report presentation

Add optional “Key Supporting Modules” metadata in report logs or UI:

- Industry / Peer
- Earnings / Catalyst
- Macro Sensitivity
- etc.

This helps users understand why the recommendation changed.

---

## 12. Evaluation Plan

## 12.1 Product-level success criteria

Success means:

- recommendations become more differentiated
- recommendations explain relative attractiveness better
- recommendations improve timing around event-driven names
- fewer generic “good company / bad chart” conclusions
- better horizon separation

## 12.2 Evaluation dimensions

### Qualitative

- recommendation depth
- orthogonality of reasoning
- reduced monotony
- clearer why-not-more-bullish / why-not-more-bearish explanations

### Quantitative

- benchmark recommendation stability across repeated runs
- outcome quality by horizon
- quality score from curated human review set
- sector-specific win-rate improvement

## 12.3 Golden evaluation set

Build a curated ticker set covering:

- semiconductors
- biotech
- banks
- software
- consumer discretionary
- energy
- industrials
- telecom/regulatory-heavy names

Include names where:

- peer context matters
- catalysts matter
- macro sensitivity matters
- management quality matters

---

## 13. Rollout Plan

## Phase 1

Build:

1. Industry / Peer Comparison Analyst
2. Earnings / Catalyst Analyst
3. Macro Sensitivity Analyst

Requirements:

- horizon-aware activation
- compact structured outputs
- analyst brief integration
- no graph redesign

## Phase 2

Build:

4. Management Quality / Execution Analyst
5. Valuation Regime Analyst

## Phase 3

Build:

6. Business Model Durability / Moat Analyst
7. Positioning / Flow Analyst
8. Regulatory / Policy Analyst

---

## 14. Detailed Phase 1 Product Specs

## 14.1 Industry / Peer Comparison Analyst

### User value

Improves recommendation quality by answering:

- attractive stock or just attractive company?
- best idea in the industry or not?

### MVP scope

- fixed peer set size: 3-5
- structured comparison of growth, margins, leverage, valuation
- one final verdict on relative attractiveness

### Recommended operating mode

- pre-fetch data
- one synthesis call

### MVP output

- short structured report
- markdown table comparing peers
- final peer-relative verdict

## 14.2 Earnings / Catalyst Analyst

### User value

Improves timing, especially for short-term and medium-term runs.

### MVP scope

- next earnings date
- expectations context
- top 3-5 near-term catalysts
- what must go right / wrong

### Recommended operating mode

- pre-fetch event data
- one synthesis call

## 14.3 Macro Sensitivity Analyst

### User value

Improves recommendations for cyclical, rate-sensitive, and globally exposed names.

### MVP scope

- rate sensitivity
- FX sensitivity
- consumer demand / credit / commodity sensitivity
- scenario map:
  - bullish macro path
  - bearish macro path

### Recommended operating mode

- pre-fetch macro context + stock exposure hints
- one synthesis call

---

## 15. Risks

### Product risks

- too many analysts can make recommendations slower and noisier
- poor peer selection can reduce trust
- low-quality event or macro data can create false precision
- too much overlap can recreate the same monotony problem in a different form

### Technical risks

- state and prompt growth
- analyst brief compaction quality
- increased evaluation complexity
- vendor/data freshness issues

### Mitigations

- stage rollout
- keep analysts structured
- use horizon/sector gating
- evaluate on a curated golden set before default enablement

---

## 16. Final Recommendation

If we want maximum recommendation-quality improvement per unit of complexity, the right first move is:

1. Industry / Peer Comparison Analyst
2. Earnings / Catalyst Analyst
3. Macro Sensitivity Analyst

Do not add first:

- another generic news-style agent
- another sentiment variant
- another debate persona

Those are more likely to add overlap than orthogonal signal.

The strategic recommendation is:

- keep the current graph
- extend the parallel analyst layer
- prefer structured specialist analysts
- activate them by horizon and sector
- start with the top three orthogonal additions before building deeper specialists

