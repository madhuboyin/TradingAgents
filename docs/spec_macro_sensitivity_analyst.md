# Technical Spec: Macro Sensitivity Analyst

## Document Info

- Status: Draft
- Date: 2026-05-18
- Owner: TradingAgents
- Depends on: [docs/prd_new_analysts.md](/Users/madhuboyina/Desktop/madhu/TradingAgents/docs/prd_new_analysts.md)

---

## 1. Purpose

Add a new analyst that explains how macro conditions flow through the specific stock.

This analyst should answer:

- Which macro variables matter most for this company?
- How does the stock transmit rates, FX, commodities, consumer demand, or credit conditions?
- Does the current macro regime amplify or offset the company-specific thesis?

---

## 2. Product Goals

### Primary goals

- improve stock-specific macro reasoning
- strengthen cyclical and rate-sensitive recommendations
- reduce generic “macro is bad/good” commentary

### Secondary goals

- improve medium-term recommendation quality
- improve short-term recommendations in rate-sensitive sectors
- improve long-term resilience framing where macro regime matters

### Non-goals

- replacing the News Analyst’s macro headline role
- building a full macro forecasting system
- providing exact economic predictions

---

## 3. Current Gap

The current News Analyst sees macro headlines, but does not explicitly model:

- rate sensitivity
- FX sensitivity
- commodity/input-cost sensitivity
- demand-cycle sensitivity
- credit-cycle transmission

As a result, the system can miss:

- stock is effectively a rates trade
- stock is vulnerable to a demand slowdown despite good company fundamentals
- macro headwind is temporary and already understood by the market

---

## 4. Recommended Placement in the Graph

Add as a new first-layer parallel analyst:

- analyst key: `macro`
- node label: `Macro Analyst`
- state keys:
  - `macro_messages`
  - `macro_report`

### Activation recommendation

- default-on for `medium_term`
- enabled for `short_term` on macro-sensitive names
- summary-only for `long_term`

### Future enhancement

Enable conditionally by sector:

- banks
- industrials
- consumer discretionary
- real estate
- transports
- energy
- small caps

---

## 5. Operating Model

Use:

- pre-fetch compact macro context and company exposure hints
- one synthesis LLM call

Avoid:

- broad global-macro essay generation
- duplicating the News Analyst’s macro-news function

The Macro Sensitivity Analyst should answer “what macro means for this stock,” not “what macro news happened.”

---

## 6. Inputs

## 6.1 Required inputs

- target ticker
- trade date
- investment horizon
- instrument context

## 6.2 Required data blocks

### A. Macro context

Compact current regime snapshot:

- rates backdrop
- inflation backdrop
- growth backdrop
- risk-on / risk-off regime
- major commodity backdrop if relevant

### B. Company / industry exposure hints

Needed:

- geographic revenue exposure if available
- input-cost sensitivity hints
- financing/capital intensity sensitivity
- consumer/corporate demand sensitivity
- credit sensitivity

### C. Sector templates

Use sector-aware heuristics to frame:

- banks
- industrials
- semis
- software
- discretionary
- energy
- healthcare
- real estate

---

## 7. Data Sourcing Requirements

## 7.1 MVP

MVP can use a hybrid approach:

- macro regime from compact macro news/context
- sector template heuristics
- basic company exposure hints from fundamentals/profile

Recommended utility module:

- `tradingagents/agents/utils/macro_data_tools.py`

Recommended functions:

- `_cached_macro_regime(curr_date)`
- `_cached_company_macro_exposure(ticker, curr_date)`
- `_cached_sector_macro_template(ticker, curr_date)`

## 7.2 Later improvements

- explicit geographic revenue mix
- cost-structure-based sensitivity
- deeper macro factor datasets

---

## 8. New Config Keys

Add to [tradingagents/default_config.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/default_config.py):

- `macro_analyst_enabled: True`
- `macro_analyst_default_for_short_term: True`
- `macro_analyst_default_for_medium_term: True`
- `macro_analyst_default_for_long_term: False`
- `macro_analyst_max_chars: 1600`

Optional later:

- `macro_analyst_enabled_sectors`
- `macro_analyst_use_sector_templates`

---

## 9. State Changes

Extend [tradingagents/agents/utils/agent_states.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/agents/utils/agent_states.py):

- `macro_report`
- `macro_messages`

Extend [tradingagents/graph/propagation.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/graph/propagation.py):

- initialize empty `macro_report`
- initialize `macro_messages`

---

## 10. Analyst Interface

## 10.1 Suggested file

- `tradingagents/agents/analysts/macro_analyst.py`

## 10.2 Public constructor

```python
def create_macro_analyst(llm):
    ...
```

## 10.3 Suggested structure

- `_collect_inputs(state)`
- `_collect_inputs_sync(state)`
- `_build_chain(inputs)`
- `_format_result(state, result)`
- `macro_analyst_node(state)`
- `macro_analyst_node_async(state)`

Follow the one-call pre-fetch analyst pattern.

---

## 11. Prompt Requirements

The prompt must instruct the model to:

- identify the most important macro drivers for the stock
- map macro variables to business impact
- distinguish direct vs indirect macro sensitivity
- explain whether macro is:
  - tailwind
  - neutral
  - headwind
  - mixed

### Required dimensions

- rates
- inflation
- growth
- FX
- input costs / commodities when relevant
- credit / funding when relevant
- consumer or enterprise demand sensitivity

### Must-have guardrails

- do not write generic macro commentary detached from the stock
- do not repeat the News Analyst’s macro-news summary
- explicitly say when macro sensitivity is low
- explicitly separate macro-driven risk from company-specific risk

### Horizon behavior

#### Short term

- focus on current regime and near-term transmission

#### Medium term

- strongest mode
- focus on 1-2 year sensitivity and earnings-path implications

#### Long term

- summarize only persistent macro sensitivities that matter to long-run thesis durability

---

## 12. Output Contract

Required sections:

1. `Macro Exposure Map`
2. `Top Macro Drivers`
3. `Bullish Macro Scenarios`
4. `Bearish Macro Scenarios`
5. `Transmission to This Stock`
6. `Macro Verdict`
7. `Markdown Table`

The report must answer:

- which macro variable matters most
- whether current macro regime helps or hurts
- whether macro sensitivity is high, medium, or low

---

## 13. Analyst Brief Integration

Section title in synchronizer:

- `("Macro Sensitivity Analysis", state.get("macro_report", ""))`

Recommended brief budget:

- 1400 to 1700 chars

This analyst should be concise, because the value is stock-specific transmission clarity, not long narrative.

---

## 14. Acceptance Criteria

The MVP is complete when:

1. the graph runs with `macro` as a first-layer analyst
2. the report identifies the stock’s main macro drivers
3. the report explains direct stock transmission rather than just macro news
4. the report clearly states whether macro is tailwind/headwind/mixed
5. the report improves recommendations for cyclical and rate-sensitive names

---

## 15. Test Plan

## 15.1 Unit tests

- sector template selection works
- low-sensitivity names degrade gracefully
- prompt includes macro regime and exposure blocks
- report path increments `analyst_count`

## 15.2 Integration tests

Suggested names:

- `JPM`
- `TSLA`
- `HD`
- `UAL`
- `O`

Validation:

- rates sensitivity appears where relevant
- demand-cycle sensitivity appears where relevant
- low-sensitivity names are not overfit into macro narratives

## 15.3 Golden checks

The analyst should catch:

- rate-sensitive financials
- cyclical consumer names exposed to slowdown risk
- capital-intensive names exposed to funding conditions

---

## 16. Risks and Mitigations

### Risk: generic macro prose

Mitigation:

- prompt requires stock-specific transmission explanation

### Risk: overfitting macro to low-sensitivity names

Mitigation:

- require explicit low/medium/high sensitivity classification

### Risk: duplicate macro-news commentary

Mitigation:

- separate role sharply from News Analyst

---

## 17. Rollout Recommendation

Build third, after:

1. Industry / Peer Comparison Analyst
2. Earnings / Catalyst Analyst

Reason:

- very high value for cyclical/rate-sensitive names
- excellent complement to news and fundamentals
- strongest payoff once the system already has better peer and catalyst context

