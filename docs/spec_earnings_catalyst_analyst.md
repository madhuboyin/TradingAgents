# Technical Spec: Earnings / Catalyst Analyst

## Document Info

- Status: Draft
- Date: 2026-05-18
- Owner: TradingAgents
- Depends on: [docs/prd_new_analysts.md](/Users/madhuboyina/Desktop/madhu/TradingAgents/docs/prd_new_analysts.md)

---

## 1. Purpose

Add a new analyst focused on discrete future events that can drive the stock over the selected horizon, especially in the short term and medium term.

This analyst should answer:

- What upcoming events matter most?
- When do they happen?
- What does the market likely expect?
- What must go right for upside?
- What must go wrong for downside?

---

## 2. Product Goals

### Primary goals

- improve timing and conviction
- improve recommendations around earnings and binary events
- reduce overly static recommendations based only on current fundamentals

### Secondary goals

- better explain event-driven risk
- improve short-term recommendations
- improve tactical invalidation and monitoring triggers

### Non-goals

- replacing the News Analyst
- being a full event-driven trading engine
- forecasting exact earnings outcomes with false precision

---

## 3. Current Gap

Today:

- News Analyst sees current developments
- Sentiment Analyst sees narrative shifts
- Fundamentals Analyst sees current financial condition

What is missing:

- a structured event calendar
- explicit market-expectation framing
- what-must-go-right / what-must-go-wrong logic

This causes the system to under-model:

- earnings setup
- near-term product launches
- regulatory decisions
- binary milestone timing

---

## 4. Recommended Placement in the Graph

Add as a new first-layer parallel analyst:

- analyst key: `catalyst`
- node label: `Catalyst Analyst`
- state keys:
  - `catalyst_messages`
  - `catalyst_report`

### Activation recommendation

- default-on for `short_term`
- default-on for `medium_term`
- optional/summary-only for `long_term`

---

## 5. Operating Model

Use:

- pre-fetch event data
- inject into prompt
- one synthesis call

Avoid:

- iterative tool loops
- news-analyst overlap

The Catalyst Analyst should not broadly summarize current news. It should structure upcoming events and expectation-sensitive developments.

---

## 6. Inputs

## 6.1 Required inputs

- target ticker
- trade date
- investment horizon
- instrument context

## 6.2 Required data blocks

### A. Earnings calendar

- next earnings date
- optionally prior earnings dates for rhythm/context

### B. Expectation context

- expected revenue growth if available
- expected EPS growth if available
- whether expectations are high / normal / depressed
- recent guidance trend if available

### C. Event inventory

- product launches
- regulatory dates
- conference / investor-day / milestone events
- major partnership / contract milestones

### D. Scenario hooks

- what upside would likely require
- what downside would likely require

---

## 7. Data Sourcing Requirements

## 7.1 MVP

Allow a blended input approach:

- earnings date source
- light expectation context source
- compact event feed from existing news infrastructure if a dedicated feed is not available yet

Recommended new utility module:

- `tradingagents/agents/utils/catalyst_data_tools.py`

Recommended functions:

- `_cached_earnings_calendar(ticker, curr_date)`
- `_cached_expectation_context(ticker, curr_date)`
- `_cached_event_calendar(ticker, curr_date, lookahead_days)`

## 7.2 Practical note

The MVP can derive some events from targeted news if necessary, but the resulting analyst must still output a structured event view rather than generic news commentary.

---

## 8. New Config Keys

Add to [tradingagents/default_config.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/default_config.py):

- `catalyst_analyst_enabled: True`
- `catalyst_lookahead_days_short_term: 120`
- `catalyst_lookahead_days_medium_term: 365`
- `catalyst_lookahead_days_long_term: 540`
- `catalyst_analyst_max_events: 8`
- `catalyst_analyst_max_chars: 1800`

---

## 9. State Changes

Extend [tradingagents/agents/utils/agent_states.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/agents/utils/agent_states.py):

- `catalyst_report`
- `catalyst_messages`

Extend [tradingagents/graph/propagation.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/graph/propagation.py):

- initialize empty `catalyst_report`
- initialize `catalyst_messages`

---

## 10. Analyst Interface

## 10.1 Suggested file

- `tradingagents/agents/analysts/catalyst_analyst.py`

## 10.2 Public constructor

```python
def create_catalyst_analyst(llm):
    ...
```

## 10.3 Suggested structure

- `_collect_inputs(state)`
- `_collect_inputs_sync(state)`
- `_build_chain(inputs)`
- `_format_result(state, result)`
- `catalyst_analyst_node(state)`
- `catalyst_analyst_node_async(state)`

Reuse the pre-fetch + one-call analyst pattern.

---

## 11. Prompt Requirements

The prompt must instruct the model to:

- focus on future events, not recap broad current news
- identify the 3-8 most material catalysts
- distinguish:
  - scheduled events
  - likely unscheduled catalyst clusters
- describe expectation risk:
  - easy compare
  - high bar
  - low bar
- describe:
  - what must go right
  - what must go wrong

### Must-have guardrails

- do not just repeat recent headlines
- do not speculate without an identifiable catalyst path
- explicitly say when the event calendar is sparse
- explicitly say when timing is known vs uncertain

### Horizon behavior

#### Short term

- strongest mode
- emphasize next earnings, launches, rulings, tactical triggers

#### Medium term

- emphasize multi-quarter milestones and execution checkpoints

#### Long term

- summarize only catalysts that can affect long-horizon thesis durability

---

## 12. Output Contract

Required sections:

1. `Catalyst Calendar`
2. `Expectation Context`
3. `Top Bullish Catalysts`
4. `Top Bearish Catalysts`
5. `What Must Go Right`
6. `What Must Go Wrong`
7. `Catalyst Verdict`
8. `Markdown Table`

The analyst must explicitly communicate:

- time-bounded event relevance
- confidence in the event map
- whether the setup is catalyst-rich or catalyst-poor

---

## 13. Analyst Brief Integration

Section title in synchronizer:

- `("Earnings / Catalyst Analysis", state.get("catalyst_report", ""))`

Recommended brief budget:

- 1400 to 1800 chars

This analyst is especially important for short-term and medium-term final synthesis.

---

## 14. Acceptance Criteria

The MVP is complete when:

1. the graph runs with `catalyst` as a first-layer analyst
2. the report includes an explicit event calendar
3. the report identifies what must go right and wrong
4. the report changes short-term recommendation quality in event-driven names
5. the report remains distinct from the News Analyst

---

## 15. Test Plan

## 15.1 Unit tests

- lookahead window respects investment horizon
- empty event calendar degrades gracefully
- prompt includes structured event blocks
- analyst increments `analyst_count`

## 15.2 Integration tests

Suggested names:

- `AAPL`
- `TSLA`
- `INSM`
- `NVDA`
- `CRWD`

Validation:

- near-term catalysts appear clearly
- report contains event timing language
- report includes expectation framing, not just facts

## 15.3 Golden checks

The analyst should detect:

- high-expectation earnings setup
- binary biotech/regulatory event risk
- product launch as meaningful near-term re-rating driver

---

## 16. Risks and Mitigations

### Risk: stale event data

Mitigation:

- keep event windows explicit
- show confidence/caveat when events are sparse or uncertain

### Risk: overlap with News Analyst

Mitigation:

- prompt hard-separates event framing from general news summarization

### Risk: false precision around market expectations

Mitigation:

- allow qualitative framing like “high bar” / “easy compare” when hard consensus is unavailable

---

## 17. Rollout Recommendation

Build second, after the Industry / Peer Comparison Analyst.

Reason:

- strongest impact for short-term quality
- excellent complement to existing news/sentiment/market branches
- major value in event-driven names

