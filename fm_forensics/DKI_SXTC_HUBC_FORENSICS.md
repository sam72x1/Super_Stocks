# DKI_SXTC_HUBC_FORENSICS — full case reconstructions with LOOKAHEAD FIREWALL (2026-10-08)

> Anchors are forensic cases, NOT optimization targets. No ticker name is used in any production logic.
> Every block separates DECISION_TIMESTAMP / INFORMATION_CUTOFF / AVAILABLE_DATA / FAISAL_ACTION / LATER_OUTCOME.
> Prices in `near_watch.json` are the bot's own (split-adjusted by its source at the time); where sources changed (Polygon → TradingView 2026-09-29/30) a level may differ by the split factor — stated where it matters.
> Daily/hourly bars were NOT available in this sandbox (TradingView blocked); the Actions probe `fm_bars_probe.yml` is pending. Every candle-level claim below is therefore marked from the bot's own files, from Faisal's images, or UNKNOWN.

---
## CASE 1 — SXTC (China SXT Pharmaceuticals)

### Corporate context (bot files)
- Reverse split 1:80 effective 2026-08-10 (bot `_fetch_splits` / three_cond log «SXTC ×8.1» source repair 09-26). The split inflates the raw 52-week high → M2 drop reads > 99.95%.
- Float ≈ 401,683 (three_cond 09-25) · available-to-borrow 2,000 (ChartExchange, 09-25).

### Faisal timeline (images; dates inferred where the post header is cropped)
| # | IMAGE | DECISION_TIMESTAMP | INFORMATION_CUTOFF | AVAILABLE_DATA (as seen by Faisal) | FAISAL_ACTION | IMPLIED_STATE |
|---|---|---|---|---|---|---|
| 1 | WA_20260918_31_SXTC | ≈2026-09-10 (WhatsApp, day of pressure) | 09-10 session | base ≈1.78–1.90 after split; pressure/sweep day; RSI ≈23 | **READY**: entry 1.80–1.90 «بعد الضغط» | READY→TRIGGERED (same session) |
| 2 | X_20260918_24_SXTC | 2026-09-11 | 09-11 | spike to 2.98 (+65%) | exit at 3; «حقق المقاومة الأولى ثم يرجع يختبر الدعم» → WAIT | TRIGGERED→ENTERED→EXITED→WATCH |
| 3 | X_20260918_22_pipeline / 23_watchlist | 2026-09-13 | 09-13 | app tabs «قائمتي · الأسهم المملوكة · تحت الجاهزية · جاهز 100%», SXTC 2.56 in list | explicit pipeline text (فرز 1 → فرز 2 → جاهزية) | FOCUS list membership |
| 4 | TG_57862 | ≈2026-09-20 | 09-20 | retest pending | WAIT («دخول جديد بعد الاختراق وتأكيد الدعوم») | WATCH |
| 5 | TG_58527 | ≈2026-09-24 17:02Z (attachment «24/09-13:00:03 EDT») | 09-24 | price ≈2.5; author inferred (no name visible) | «الليلة يدبل 6.31 هدف» | TARGET claim (not an entry) |
| 6 | TG_58418 | after 10-07 (post shows «الآن فوق 3») | post-move | re-entry 2.15–2.25 | READY (second wave) | READY→ENTERED |
| 7 | TG_58417 | after 10-07 | post-move | outcome statement | «بعد الضغط وسحب السيولة تم الدخول والخروج عند 3 · والدخول مرة أخرى 2.15>2.25 · فوق 100% بموجتين» | OUTCOME |

LATER_OUTCOME (bot files + probe bars, UTC): 09-11 high 3.00 (+65% day, presession AH rank 7, sent); high 3.27 on 10-01; close 1.25 on 10-06 (low 1.18); **10-07 regular high 9.59 (+667% from the 10-06 close), close 2.83**; AH 10-07 2.26 (presession rank 1, sent); **10-08: pre-market 2.36 → collapse to 0.32 at ≈14:00 UTC (−97% from the 10-07 peak), regular close 0.331** — below every level in the thread. The 6.31 target (TG_58527) was reached intraday on 10-07 (high 9.59) but the move reversed within one session; Faisal's TG_58417 («الخروج عند 3») describes an exit at ≈3. The forecast's timing («الليلة يدبل», 09-24) failed; the level was later exceeded for hours. Both are kept.

### Bot timeline (lookahead-safe: each row uses only that day's snapshot)
| Date | Layer reached | Reason | Visible to owner? |
|---|---|---|---|
| 08-16 → 09-07 | L2 reject | `M2_هبوط_فوق_97` every day (post-split 52w high) | no (near_watch n_out=1–2, not shown) |
| 09-08, 09-09 | near_watch OVERSOLD bucket | RSI 23.3, price 2.23/2.24 | **yes** — shown at rank 20 / 19 of the oversold list (bottom of a 20-row list) |
| 09-10 (Faisal READY day) | L2 reject | M2 ceiling; RSI 23.3; price 2.14; near_watch n_out=1 | no (not in top 20 shown) |
| 09-11 | presession AH | +11% day, rank 7, **sent** (after the move) | yes (post-hoc) |
| 09-25 → 10-02 | three_cond_daily | matched 6 consecutive sessions (RSI 26–29, float 401k, avail 2k, stable 11–16 sessions above 1.78) | **yes** (three-conditions message) |
| 10-07 AH | presession | +81%, rank 1, **sent** | yes (after the move) |
| any day | READY NOW | **never** (never entered `weekly_watchlist.json`) | — |

### Layer attribution
- L2 M2 ceiling (99.95%) is the single blocking layer every day. Cause: the reverse split makes the pre-split high astronomically higher than the post-split base. `MAX_DROP_PCT` 99.95 is an envelope number; Faisal's catalog itself contains splits, but the envelope was measured on bot-adjusted histories where a 1:80 split in the window pushes the drop above the P100 edge.
- Had M2 passed: M4 base ≤ 120% — UNKNOWN without bars; L5 tested_level: the 09-10 base (1.78) had ≥ 2 touches only after 09-22 (stable 11 sessions by 09-25) → on 09-10 it would have been rejected `M_لا_مستوى_مختبر` (single-touch fresh low) — strong inference from the three_cond stability counter, not a replay.
- READY NOW could not have fired on 09-10 even with every gate open: `near_support` requires the price to be at/below the top tranche of an anchor that exists only after the low has been touched twice.

### Classification
FOCUS_WITHOUT_READY (bot) · MISSED_READY for the 09-10 entry and the 10-07 re-entry · the three-condition tool did surface it 09-25→10-02 (a WATCH-stage signal, 2 weeks before the second wave).

---
## CASE 2 — DKI

### Corporate context
- Reverse split (Faisal: «شمعة التقسيم 5.70», TG_57894 annotations: split_candle 5.7, group_candle 2.97, res_test 2.74, low 2.18, sweep_to 2.0). Split date not in bot files → UNKNOWN (bars probe).
- near_watch prices: 08-16 4.10 · 09-02 3.13 · 09-11 2.47 · 09-18 2.82 · 09-25 2.90 · 10-01 1.57 · 10-02 1.29 · 10-07 1.36 · 10-08 1.67.

### Faisal timeline
| # | IMAGE | DECISION_TIMESTAMP | INFORMATION_CUTOFF | AVAILABLE_DATA | FAISAL_ACTION | IMPLIED_STATE |
|---|---|---|---|---|---|---|
| 1 | EDU_20260827_dki_group_candle | 2026-08-26 (educational channel, DKI chart) | 08-26 | group candle ≈2.97 after split | REJECT-style reading («شمعة قروب») | SCREENED / INVALIDATED |
| 2 | X_20260918_22_pipeline | 2026-09-13 | 09-13 | DKI 2.66 in the app list | FOCUS list member | FOCUS |
| 3 | TG_57893 / TG_57894 | ≈2026-09-2x (batch 09-30; price ≈2.18 low) | that day | low 2.18, resistance test 2.74, expected sweep to ≈2.0 | **WAIT**: «انتظر مسح سيولة إلى 2 تقريبًا · الشراء بعد المسح لا قبله · نهج ثابت بكل الأسهم» | WATCH (pre-trigger) |
| 4 | TG_58386 (owner chart) | UNKNOWN (after the collapse to 1.10) | — | 4h chart: 4.20 → 1.10 → 1.48; levels 1.333/1.529/1.897 | none (owner chart) | — |

LATER_OUTCOME (bot files + probe bars `bars_2026-10-08.json.gz`, TradingView daily + hourly extended, UTC): close 1.36 on 10-06 → regular high 3.64 on 10-07 (close 1.67) → **pre-market 10-08 high 7.43 at ≈10:00 UTC (+446% from the 10-06 close)** → regular-session collapse to **0.80 at ≈14:00 UTC (−89% from the peak, below the 2.18 base and below the 1.10 sweep low)**; 10-08 regular close 0.807. So DKI's "major move" is VERIFIED as a two-session spike that fully reversed inside the same session it peaked. Faisal's WAIT («الشراء بعد المسح إلى ≈2») was never followed by a reclaim of 2 before the spike (closes 1.29–1.67) — whether he entered is UNKNOWN (no post in corpus).

### Bot timeline
| Date | Layer | Reason | Visible? |
|---|---|---|---|
| 08-16 | near_watch n_out=2 (M2 52w-drop, RR) | — | no |
| 09-02 → 10-02 | **near_watch INSIDE (n_out = 0)** — fully inside the Faisal envelope, RSI 21.5–45 | L5 reject `M_لا_مستوى_مختبر` every day 09-11→10-01 (reject_log walls) | shown ONLY on 09-18 (rank 3 and 5 of the inside list) |
| 10-02 → | L2 reject `M4_base_واسعة` | the collapse widened the 15-bar base range beyond 120% | no |
| 09-25 PM / 09-30 PM / 10-02 AH | presession rows | ranks 3 / 48 / 47, not sent | no |
| any day | READY NOW | never | — |

### Layer attribution
- Sept 11 → Oct 1: identity passed (M1–M5), soft fails ≤ 8, score ≥ 5 — the ONLY wall was the tested-level anchor (fresh low 2.18 touched once). This is exactly the state Faisal calls WATCH/pre-sweep. The bot's design says "no anchor until two touches", Faisal says "wait for the sweep, buy after". Both are WAIT on the same day, but the bot's WAIT is invisible (not in the shown 20 of 297 inside symbols on most days) while Faisal's is an explicit, tracked focus item.
- Oct 2 →: the sweep came (−41%) and the bot moved DKI further away (M4), while Faisal's method would restart from the new low (R4-INV-01: broken base → new base).

### Classification
FOCUS_WITHOUT_READY · WATCH_INVISIBLE (inside bucket cut to 20) · LATER_OUTCOME UNKNOWN pending bars.

---
## CASE 3 — HUBC (Hub Cyber Security)

### Corporate context
- Reverse split 1:25 effective 2026-09-14 (three_cond source-repair log 09-26 lists HUBC; press_radar ledger 09-23: high 4.125 / low 3.17 / close 3.21; 09-28: 1.88/1.47/1.49).
- near_watch prices: 08-16→09-11 0.74→0.42 (pre-split) · 09-15 0.34 · 09-23 4.24 · 09-24 3.21 · 09-25 2.33 · 09-26 1.90 · 09-29 1.49 · 09-30→10-08 0.95–1.05.
- Owner's memory 2026-09-26: «HUBC +139%» among the week's explosions excluded by the three-conditions tool (it had exploded before stabilizing).

### Faisal timeline
| # | IMAGE | DECISION_TIMESTAMP | INFORMATION_CUTOFF | AVAILABLE_DATA | FAISAL_ACTION | IMPLIED_STATE |
|---|---|---|---|---|---|---|
| 1 | TG_2098 | 2026-04-24 | 04-24 | plan with stop 7% (pre-split era) | plan / counter-example in inventory | old FOCUS |
| 2 | owner chart card 2026-10-07 (`chart_cards/blind/2026-10-07/`) | 2026-10-07 | 10-07 | 4h chart 09-23→09-29: peak 4.125, 21 red candles to ≈1.12, «الهدف من 3-4», «موجات السهم المتوقعه» | current FOCUS: expected waves back to 3–4 | FOCUS / DEVELOPING |

**No dated Faisal HUBC decision text exists in the corpus between 2026-04-24 and 2026-10-07.** The claim «Faisal is currently centered on HUBC» rests on the owner's statement and the 10-07 chart (identified as HUBC by `chart_id_tv.py`, key confirmed by the owner). Confidence: owner-reported, chart-verified; Faisal's own words for the current thesis: UNKNOWN.

LATER_OUTCOME: none yet (as of 10-08: 0.95–1.05; three_cond 10-08 flagged HUBC as avail-unknown and DQ-quarantined for the recent reverse split, ÷2 of the post-split open hit 10-07, held 0/3).

### Bot timeline
| Date | Layer | Reason | Visible? |
|---|---|---|---|
| 08-16 → 09-12 | near_watch n_out=1 (M2 52w-drop) | pre-split price 0.42–0.77 | no |
| 09-15 | L2 reject M1 (price 0.34 raw / split transition) | | no |
| 09-21 AH / 09-22 PM | presession rank 43 (not sent) / **rank 2, sent** (6.01 → +29% day) | post-move alert | yes (during/after the +139% week) |
| 09-23 → 10-08 | L2 reject `M2_هبوط_فوق_97` (post-split 52w high) · n_out = 2 | | 09-30, 10-01, 10-02 shown in the OVERSOLD list (rank 19/17/18; RSI 21) |
| 10-08 | three_cond | avail unknown + DQ quarantine (recent split) | no (quarantined, counted in footer) |
| any day | READY NOW | never | — |

### Layer attribution
Same mechanism as SXTC: the reverse split makes M2 a permanent wall; the DQ gate additionally quarantines the symbol for the split. The bot has no "post-split restart" notion for the READY path (the split hunter has one — but it is a separate tool with its own recipe, and HUBC did not match it).

### Classification
FOCUS_WITHOUT_READY · the only bot output that reached the owner was a post-move presession alert (09-22) and three oversold-list appearances at the bottom of a 20-row list.

---
## CASE 4 (control) — CRE

- Faisal: open position since at least 2025-08-02 (TG_2103 «$CRE -10 مفتوحه»); 2026-09-2x TG_57869 «الفجوة لازم تُغطّى» → WAIT.
- Bot: near_watch INSIDE (n_out=0) from 08-16, shown 08-16/17/18 (rank 10–20); added to the watchlist 2026-10-06 (sweep_confirmed), READY NOW 10-06, 10-07, 10-08 (alerts_history 10-06: price 2.67, stop 2.54, t1 3.00).
- Gap-down thesis: Faisal waits for the gap below to fill; the bot's M9 only models gaps ABOVE (targets). The bot became READY on the sweep (consistent with R4-SWEEP-01), Faisal still WAIT on the unfilled gap — a genuine rule difference (see `GAP_DOWN_FORENSICS.md`).
- Classification: READY_WITHOUT_FOCUS-TRIGGER (bot ready while Faisal waits) → candidate EARLY_READY; outcome UNKNOWN (open).

---
## Cross-case findings (what the three cases share)
1. All three anchors are post-reverse-split stocks; for two of them (SXTC, HUBC) the split alone makes M2 a permanent wall in the READY path, and for the third (DKI) the only wall during its 3-week base was the two-touch anchor rule.
2. Faisal's visible process is staged and the *entry* is a trigger event (pressure + sweep + reclaim), never a price location alone: WA_31 («بعد الضغط»), TG_57894 («الشراء بعد المسح»), TG_58417 («بعد الضغط وسحب السيولة … مرة أخرى»).
3. The bot's near-watch section did hold DKI (inside) and SXTC/HUBC (oversold) but showed them to the owner on 1, 2 and 3 days respectively, each time near the bottom of a 20-row cut of 120–300 symbols. The information existed in state and was lost at the display cut (L11), not at computation.
4. The three-conditions tool (a WATCH-stage filter, not READY) was the only channel that named SXTC for six consecutive sessions before its second wave.
5. **The "major moves" of DKI and SXTC were pre-market/intraday spikes that reversed within the same session** (SXTC +667% then −97%; DKI +446% then −89%), ending below their bases. Any evaluation of "catching" them must state the exit assumption; a daily-close evaluator sees SXTC's 10-07 as +126% close-to-close and DKI's as +23%.
