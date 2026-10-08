# PIPELINE_FAILURE_FORENSICS — where the bot loses Faisal's stocks, layer by layer (2026-10-08)

## 1. Broad sample: 279 explosions ≥ 100% (2026-07-17 → 2026-10-07), blocking layer at the base (`base_reason`, computed by the bot at the pre-move base; `READY_NOW_MISSED_SIGNALS.csv`)
| Layer | Reason | n | share | Comment |
|---|---|---|---|---|
| L2 M2 (drop < 71.7%) | `M2_هبوط_تحت_40` | 79 | 28.3% | not a "pivot" by the catalog envelope — most are momentum/news names, by design excluded |
| L5 anchor | `M_لا_مستوى_مختبر` | 73 | 26.2% | **identity passed; only the two-touch anchor failed** — the DKI mechanism |
| L2 M1 | price < 0.40 | 66 | 23.7% | sub-40-cent names (Faisal trades some; owner's price category 🪙 exists in three-cond) |
| L2 M4 | base range > 120% | 40 | 14.3% | the base widened by a collapse/sweep (DKI after 10-02) |
| L8/L10 | «مرشّح» (was a candidate) | 10 | 3.6% | selected or selectable but not READY before the move (2 were READY ≤ 14 d before: PSIG, QTEX) |
| L2 M3 | prior spike < 78% | 6 | 2.2% | |
| L2 M2 ceiling | drop > 99.95% (split) | 4 | 1.4% | the SXTC/HUBC mechanism — small in this register because the register itself is built from bot-adjusted bars where many split names never appear |
| L2 M5 | liquidity | 1 | 0.4% | |

Near-watch coverage of the same movers (snapshots from 08-16; 231 with a snapshot): INSIDE bucket 81 (35%), OVERSOLD 26 (11%), not in near-watch 124 (54%). So roughly **46% of the ≥100% movers were already inside the bot's own "under watch" state** in the 14 days before the move and were shown to the owner only if they fell in the top-20 cut of their bucket.

READY NOW recall on this register: 2 / 279 = 0.7% (14-day window). This is the bot's own register (gain ≥ 100% from the explosion detector), not Faisal's picks; it is the only outcome-labelled population available without bars.

## 2. Anchor cases (full trace in `DKI_SXTC_HUBC_FORENSICS.md`)
| Ticker | L0 | L1 | L2 | L3 | L4 | L5 | L6 | L7 | L8 | L9 | L10 | L11 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SXTC | ok (TV; split ×8.1 repaired 09-26) | in | **M2 ceiling every day** | — | — | (would fail: fresh low 09-10) | — | — | — | never | never | oversold list 09-08/09 (rank 20/19); presession 09-11 & 10-07 after the move; three-cond 6 sessions |
| DKI | ok | in | pass 09-11→10-01 | pass | pass | **anchor fail 09-11→10-01** | — | — | — | never | never | inside list shown 09-18 only; presession 10-07 after |
| HUBC | ok (split ×25 09-14) | in | M1 (09-15) then **M2 ceiling** | — | — | — | — | — | — | never | never | oversold list 09-30/10-01/10-02 (rank 19/17/18); presession 09-22 (sent, during the +139% week) |
| CRE (control) | ok | in | pass | pass | pass | pass (10-05) | plan | pass | selected 10-06 | active | **READY 10-06/07/08** | card sent |

## 3. Root-cause map
| Cause | Layer | Mechanism | Anchors affected | Fix class |
|---|---|---|---|---|
| Reverse split inflates the 52-week drop | L2 (M2 ceiling 99.95) | pre-split high vs post-split base | SXTC, HUBC | DATA/RULE: a post-split restart of the M2 reference (the split hunter already has `_post_split_high`); must be measured, not assumed |
| Fresh low needs two touches | L5 (`tested_level`) | Faisal's WATCH stage is exactly "one touch, waiting for the sweep" | DKI (3 weeks), 73/279 movers | STATE: WATCH state before anchor; not a gate change |
| READY = location, not stage/trigger | L10 | `near_support` fires on first contact | CRE (early), 70/117 stop-outs | STATE/TRIGGER |
| Stop inside the sweep zone | L6 | stop 5–7% below anchor vs expected sweep 7–13% | 70 FALSE_READY (partly) | measured elsewhere (T-SWEEP-RECLAIM, T-PIVOT-BOTTOM: closed axes) — not reopened |
| Display cut | L11 | top-20 of 120–300 per bucket, 240 s budget | DKI, SXTC, HUBC visible 1–3 days | OUTPUT decision (owner) |
| Membership recomputed daily, 15 slots, borrow gate | L8 | 10-07: 2 of 8 slots filled; 28 excluded by avail > 20k | — | DESIGN (owner's 20k rule is Faisal's) |
| No re-entry after exit | L9 | removed on stop; second waves missed | SXTC wave 2 | STATE |

## 4. Verdict on the pipeline
The failure is **not** a data failure (bars arrive; splits are known to the DQ gate) and **not** a single wrong threshold. It is a **state-model mismatch**: the bot evaluates membership from scratch each day and reports a location flag, while Faisal maintains a persistent focus set that moves through stages and enters on a trigger. Secondary: the split reference in M2 and the two-touch anchor convert Faisal's WATCH stage into a hard reject.
