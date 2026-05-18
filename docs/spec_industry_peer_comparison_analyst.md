# Technical Spec: Industry / Peer Comparison Analyst

## Document Info

- Status: Draft
- Date: 2026-05-18
- Owner: TradingAgents
- Depends on: [docs/prd_new_analysts.md](/Users/madhuboyina/Desktop/madhu/TradingAgents/docs/prd_new_analysts.md)

---

## 1. Purpose

Add a new first-layer analyst that evaluates the target stock relative to direct peers and the broader industry context.

This analyst should answer:

- Is this stock attractive relative to alternatives in its peer group?
- Is the company genuinely best-in-class or merely a good company in an expensive industry?
- Is the current thesis company-specific, peer-relative, or mostly industry-cycle driven?

The analyst must add orthogonal signal relative to the current fundamentals/news/market/sentiment stack.

---

## 2. Product Goals

### Primary goals

- improve recommendation quality by adding peer-relative context
- reduce false “good company, automatically good stock” conclusions
- strengthen medium-term and long-term recommendations

### Secondary goals

- give the final recommendation explicit relative-valuation context
- improve sector-sensitive names
- increase differentiation across stocks in the same industry

### Non-goals

- replacing the existing Fundamentals Analyst
- building a full market-neutral quant ranker
- adding a broad generic sector-news agent

---

## 3. Current Gap

Today, the system has:

- standalone fundamentals analysis
- standalone news analysis
- standalone technical and sentiment analysis

What is missing is structured relative context:

- peer set definition
- relative growth
- relative margin quality
- relative valuation
- relative balance-sheet quality
- industry cycle context

Without this, the system can misclassify:

- good company, bad stock
- weak company, cheap turnaround
- noisy company headline, still best operator in industry

---

## 4. Recommended Placement in the Graph

This should be a new first-layer parallel analyst in the graph defined in [tradingagents/graph/setup.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/graph/setup.py).

### Required additions

- new analyst key: `industry`
- new graph node label: `Industry Analyst`
- new message state: `industry_messages`
- new report state: `industry_report`
- new delete node via `create_msg_delete("industry_messages")`
- new brief section in `sync_analysts()`:
  - `("Industry / Peer Comparison", state.get("industry_report", ""))`

### Initial activation recommendation

- enabled by default for:
  - `medium_term`
  - `long_term`
- optional for:
  - `short_term`

### Conditional activation recommendation

Prefer an initial simple config-driven toggle over dynamic auto-selection in MVP.

Possible later enhancement:

- always-on for sectors where peer comparison matters most:
  - semiconductors
  - software
  - consumer brands
  - banks
  - industrials
  - retail

---

## 5. Operating Model

Use the same successful pattern as the current Fundamentals Analyst:

- pre-fetch deterministic data
- inject it into the prompt
- run one synthesis LLM call

Avoid:

- multi-turn tool loops
- open-ended tool selection by the LLM

### Why

- peer comparison is deterministic enough to precompute
- this minimizes cost growth
- this minimizes prompt drift
- this keeps the analyst structured and reproducible

---

## 6. Inputs

## 6.1 Required inputs

- target ticker
- trade date
- investment horizon
- instrument context

## 6.2 Required data blocks

### A. Target company fundamentals snapshot

Needed fields:

- revenue growth
- gross margin
- operating margin
- EBITDA margin if available
- net margin
- free cash flow / FCF margin if available
- leverage and liquidity indicators
- valuation multiples if available

### B. Peer set

Required:

- 3 to 5 peers
- peer tickers
- peer names if available

### C. Peer-relative metrics

For target + peers:

- revenue growth
- gross margin
- operating margin
- net margin
- FCF or cash flow quality proxy
- leverage / net cash / balance-sheet strength
- valuation multiple set

### D. Industry context

Needed:

- sector
- industry
- basic industry-cycle context
- optionally 1-2 industry news headlines or a compact industry summary

---

## 7. Data Sourcing Requirements

## 7.1 MVP requirement

The MVP can use a config-driven or static peer mapping source before building a more dynamic peer resolver.

Recommended initial implementation:

- add a peer mapping utility:
  - `tradingagents/dataflows/peer_mapping.py`
- allow:
  - hand-maintained peer map
  - fallback to sector/industry-based peer heuristics

## 7.2 Future improvement

Later, replace or augment with:

- provider-based peer lists
- market-cap filtered peers
- geography-aware peers

## 7.3 New utility functions

Recommended utilities:

- `_cached_peer_set(ticker, curr_date)`
- `_cached_peer_fundamentals(peer_ticker, curr_date)`
- `_cached_peer_valuation(peer_ticker, curr_date)`
- `_cached_industry_context(ticker, curr_date)`

Suggested location:

- `tradingagents/agents/utils/industry_data_tools.py`

---

## 8. New Config Keys

Add to [tradingagents/default_config.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/default_config.py):

- `industry_analyst_enabled: True`
- `industry_analyst_default_for_short_term: False`
- `industry_analyst_max_peers: 5`
- `industry_analyst_peer_metric_limit: 8`
- `industry_analyst_max_chars: 1800`

Optional later:

- `industry_analyst_allowed_sectors`
- `industry_analyst_peer_source`

---

## 9. State Changes

Extend [tradingagents/agents/utils/agent_states.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/agents/utils/agent_states.py):

- `industry_report: Annotated[str, "Report from the Industry / Peer Comparison Analyst"]`
- `industry_messages: Annotated[list, add_messages]`

Extend [tradingagents/graph/propagation.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/graph/propagation.py):

- initialize `industry_messages`
- initialize `industry_report`

---

## 10. Analyst Interface

## 10.1 Suggested file

- `tradingagents/agents/analysts/industry_analyst.py`

## 10.2 Public constructor

```python
def create_industry_analyst(llm):
    ...
```

## 10.3 Suggested internal structure

- `_collect_inputs(state)`
- `_collect_inputs_sync(state)`
- `_build_chain(inputs)`
- `_format_result(state, result)`
- `industry_analyst_node(state)`
- `industry_analyst_node_async(state)`

Follow the current single-call analyst pattern used by:

- [fundamentals_analyst.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/agents/analysts/fundamentals_analyst.py)
- [sentiment_analyst.py](/Users/madhuboyina/Desktop/madhu/TradingAgents/tradingagents/agents/analysts/sentiment_analyst.py)

---

## 11. Prompt Requirements

The prompt must instruct the model to:

- identify the target’s place within the peer group
- explicitly compare relative growth, margins, balance-sheet quality, and valuation
- decide whether the stock is attractive relative to peers
- separate company quality from stock attractiveness
- explain whether the thesis is:
  - company-specific
  - peer-relative
  - industry-cycle driven

### Must-have guardrails

- do not write generic sector prose
- do not only repeat the company’s own fundamentals
- do not treat “higher multiple” as automatically bullish
- explicitly note when peer data is weak or incomplete

### Horizon guidance

Reuse `get_horizon_prompt(...)`, but add analyst-specific emphasis:

- `short_term`:
  - relative setup and valuation support near-term decision
- `medium_term`:
  - strongest mode
- `long_term`:
  - emphasize industry structure and sustained peer advantage

---

## 12. Output Contract

The analyst output should remain prose, but strongly structured in sections.

### Required sections

1. `Peer Set`
2. `Industry Context`
3. `Relative Growth`
4. `Relative Profitability`
5. `Relative Valuation`
6. `Balance Sheet vs Peers`
7. `Industry Cycle Position`
8. `Peer Comparison Verdict`
9. `Markdown Table`

### Required final verdict

The report must clearly answer:

- best-in-class / above average / average / below average
- attractive / fair / unattractive relative to peers

---

## 13. Analyst Brief Integration

The `industry_report` should be included in the compact downstream `analyst_brief`.

### Recommendation

Give this analyst a slightly larger downstream budget than sentiment because it will matter more for medium-term and long-term synthesis.

Recommended starting brief cap:

- 1600 to 2000 chars

---

## 14. Acceptance Criteria

The MVP is complete when:

1. the graph can run with `industry` as a selected analyst
2. the analyst executes in one LLM call after pre-fetch
3. `industry_report` is stored in state
4. `industry_report` is included in `analyst_brief`
5. the report includes a peer set and a clear peer-relative verdict
6. the report distinguishes company quality from stock attractiveness
7. the report changes recommendations meaningfully on peer-sensitive names

---

## 15. Test Plan

## 15.1 Unit tests

- peer set resolver returns bounded peer list
- missing peer data degrades gracefully
- render path completes and increments `analyst_count`
- prompt includes horizon and peer data blocks

## 15.2 Integration tests

Use representative names such as:

- `NVDA`
- `AMD`
- `CRWD`
- `SHOP`
- `JPM`

Validate:

- peer section appears
- report is not generic
- peer-relative language affects final synthesis

## 15.3 Qualitative golden checks

The analyst should catch:

- strong company but too expensive vs peers
- noisy negative headline but still strongest operator
- sector downturn affecting the whole group, not just the target

---

## 16. Risks and Mitigations

### Risk: poor peer selection

Mitigation:

- fixed curated peer map in MVP
- later upgrade to dynamic resolver

### Risk: duplicated fundamentals prose

Mitigation:

- prompt explicitly requires relative framing

### Risk: weak peer data quality

Mitigation:

- degrade gracefully and say when peer comparison confidence is low

---

## 17. Rollout Recommendation

Build this first among all proposed new analysts.

Reason:

- highest recommendation-quality upside
- strong fit with current graph
- medium implementation difficulty
- strong benefit for medium-term and long-term runs

