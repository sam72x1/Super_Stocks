# READY_NOW_TARGET_REASSESSMENT — what READY NOW is, conceptually, and whether its target variable is Faisal's (2026-10-08)

## What it is, by code (`entry_status`, `Super_stock.py:14914`)
`ready_now` ⇔ the stock is already a watchlist member (15 slots, borrow ≤ 20k, tested two-touch anchor) **and** `interp.entry_mode.mode ∈ {near_support, sweep_confirmed}` **and** `last_price ≤ max(tranches)·(1 + 0)`.

| Candidate concept | Fits? | Why |
|---|---|---|
| a state | partly | it persists only while the price stays inside the band; no memory of how it got there (no hold count, no test bounce, no prior readiness) |
| a signal | no | it is recomputed daily from a static condition; it does not fire on an event |
| a ranking label | no | ranking (`rank_key`) is upstream; `ready_now` does not reorder |
| an entry trigger | no | no operator/pressure/volume event is required; `sweep_confirmed` is optional |
| a daily snapshot | yes | evaluated once per scan on the previous close |
| a price-location classifier | **yes** | the whole test is "price ≤ top tranche of the anchor" plus "not stopped / not far" |
| a bot-created abstraction | **yes** | nothing in the corpus names a state defined by "price within 6% above a twice-touched 30-bar low" |

## Faisal's target variable (from the corpus, Phase 1 + Phase 2 re-verification)
"جاهز" = a *technically ready* stock (base held 3–5 sessions above a split-anchored low, RSI oversold, averages 20/30/50 in a known configuration, short < 20k, no groups) that *still waits* for the operator event (hold-with-loading or sweep-and-reclaim). It is one node in a persistent per-stock lifecycle, reached weeks after focus began.

## Verdict
**The two concepts are fundamentally different.** READY NOW answers "is the current price near a tested level inside my selected set today?"; Faisal's READY answers "has this focus name matured to the point where only the operator is missing?". The former has no lifecycle, no split-anchored regime, no validity filters at the state level, and no trigger. Repairing the classifier's thresholds cannot change its target variable; a different target would be a different object (a per-stock state with persistence), which Phase 1's shadow test did not validate either (branch 2) — and whose identity layer removed Faisal's names before any state could be evaluated (see `M2_FORENSICS.md`).

This file makes no recommendation to change production.
