# READYNOW — research specification (sealed before the validation and holdout windows are read)

Mission: «RECONSTRUCT READY NOW — DISCOVER EARLY TECHNICAL CONDITIONS AND VALIDATE AGAINST THE HISTORICAL EXPLOSION
UNIVERSE». Research only: no production, Telegram, schedule, threshold, membership, frozen-axis or closed-axis change;
no network request; no agents or workflows. READY70 and SEQ70 are imported read-only. This file is pinned by SHA-256
in `rn_eval.py`; the evaluator refuses to read a row (exit 9) if it differs. The seal commit is pushed before the run.

## 1. Seeds and move dates (hypothesis generation only; excluded from every statistic)
Onset rule for every stock (one rule, never adjusted per ticker): **L = the session after the trough close of a clean
episode of the bot's explosion detector** (`Super_stock.scan_explosions` semantics recomputed by READY70: a one-day
close-to-close jump ≥ 50% or a ≥ 70% run within 20 sessions; «clean» = no split within [L − 5 d, D1 + 1 d]).
Also reported: L10 (first close ≥ 10% above the trough), IGN (largest one-day close gain in [L, D1]), x70 (first close
≥ 70% above the trough), D1 (first detection).

| seed | onset L | L10 | IGN | +70% close | D1 | Faisal timestamp in the local corpus |
|---|---|---|---|---|---|---|
| DLXY | 2026-08-31 | 09-01 | 09-16 | 09-16 | 09-16 | none (phase-5 control pool «without any Faisal unit»); raised by the owner 2026-09-26 |
| RETO | 2026-09-15 | 09-15 | 09-15 | 09-15 | 09-15 | none (same); raised by the owner 2026-09-26 |
| SXTC | 2026-06-08 · 07-30 · 10-07 | 06-10 · 07-30 · 10-07 | 06-11 · 08-04 · 10-07 | 06-12 · 08-04 · 10-07 | 06-12 · 08-04 · 10-07 | READY 09-10 · ENTRY 09-11 · FOCUS 09-13 · ENTRY inferred 09-24 |
| DKI | **no qualifying onset** (2026-10-07 closed +22.8% after an intraday high +168%) | | | | | FOCUS 2026-09-13 · WAIT for a sweep |

Seed matrix at T−10 … T−7 (`data/seeds_matrix.json`): the only conditions present in all five seed events are «held ≥ 5
sessions above the 25-session low» and «no 50% boom in a week»; RSI < 33 appears in SXTC-10/07 (4 of 4 days), RETO (1)
and SXTC-06/08 (2); the app's «within 15%» only in SXTC-06/08; the momentum turn (EMA 9/26) in none. **The candidate
of §6 holds on none of the five seed events at T−10 … T−7** (DLXY, RETO, SXTC-06/08 and -07/30: RSI 31–61; SXTC-10/07:
bounce 68.5% above the 40% band); the tool's technical part holds on SXTC-10/07 (4 of 4), RETO (1) and SXTC-06/08 (1);
DKI at T−10 … T−7 of its 10-07 intraday move: RSI 34–38. HUBC is the active
case: descriptive only, after this seal (its daily values were printed in the seed step; no threshold below came from it).

## 2. Condition sources (only verifiable definitions; exact gaps)
| condition | formula (bars ≤ t) | source · type |
|---|---|---|
| RSI33 | RSI14 (Wilder, `S.rsi`) < 33 | three-condition tool `rsi_max` = `RSI_OVERSOLD` · inferred (catalog median trough) |
| RSI30 | RSI14 < 30 | Faisal «rsi اقل من 30» (DRCT) · verbatim |
| OS_AT_LOW | RSI14 on the day of the 25-session low < 33 | IMG_6814 «oversold reached at the bottom» · verbatim concept, tool threshold |
| HOLD2 / HOLD3 / HOLD5 | sessions since the first day reaching the 25-session daily low ≥ 2 / 3 / 5 and close above it | app chip (2, partly unknown) · IMG_0151 (3) · tool `STABILITY_REQ` (5) |
| NEAR15 | close ≤ 15% above the 25-session low | app chip · base window unknown (25 used) |
| BOUNCE10_40 | max high since the low day ÷ low − 1 within 10–40% | app chip (confirmed definition) |
| BELOW3 | close below EMA20, EMA30 and EMA50 | app chip (definition UNKNOWN — parity failed) · IMG_6814 «bearish averages» |
| EMA_UP / EMA_X5 | EMA9 > EMA26 / crossed up within 5 sessions | Faisal panel TG_57927 |
| MACD_POS | MACD(12,26,9) line > signal | app chip (confirmed definition) |
| NO_BOOM | max high of the last 5 sessions over the running lowest close since the session before them < +50% | tool `recent_explosion` (after-hours highs not archived) |
| SPLIT120 | a reverse split within 120 calendar days | `SPLIT_LOOKBACK_DAYS` · Faisal's preference for fresh splits |
| CYCLE3 | `pivot_cycle_state` stage ≥ 3 (returned to test the bottom) | TG_50584 cycle · READY70 feature |

Not reconstructible (exact gaps): the tool's float < 4,000,000 and available-to-borrow < 20,000 (no point-in-time
series; borrow harvest only from 2026-08) · the tool's exact low uses hourly extended bars (not archived; daily lows
used) · the app's two unnamed conditions (no source: «هذي جميع الصور اللي عندي في التطبيق فقط») · the app's 4-hour
momentum and «successful daily retest» (definitions UNKNOWN; no 4-hour archive) · the app's base-low window (UNKNOWN).

## 3. Event, label and horizon
Pivot-day population = READY70 `pi_obs` (pivot identity M1–M3, FAISAL_ONLY, 2025-05-01 → 2026-10-07; frozen M2/M3 and
ANCHOR_TWO_TOUCH untouched — SXTC and HUBC fall outside it by the M2 ceiling, reported, not changed).
Label at the close of t: **POS710** = a clean onset L in [t+7, t+10] · NEG = no clean onset in [t+7, t+10] (onsets in
[t+1, t+6] are NEG for the primary label; `pos110` reports them) · IN_EVENT (an episode under way: L ≤ t ≤ max(peak,
D1)) · UNKNOWN_SPLIT (a split-near episode starts in [t+1, t+10]) · CENSORED (t + 10 + 19 beyond the last bar;
19 = the longest launch-to-detection gap measured over all clean episodes). Missing future is never negative.
Last label-known decision: 2026-08-27. Sensitivity labels (reported, never decisive): strict +70% close, onset L10,
onset IGN. Each event counts once at event level (eligible = at least one POS710 pivot-day in [L−10, L−7]).

## 4. Sampling, controls, splits
Windows (decision dates): **development 2025-05-01 → 2025-12-31 (read)** · **validation 2026-01-16 → 2026-05-15
(unread)** · **holdout 2026-06-02 → 2026-08-27 (unread)**; each start more than 10 sessions after the previous end.
Seeds (DLXY, RETO, DKI, SXTC) and HUBC are removed from every window. Matched controls (Layer B): evaluable pivot-days
of the same session and traded-price bucket (< $1, < $3, < $10, ≥ $10), each within-session percentile of volume ratio
(`v1x`), 20-session range (`range20`, volatility) and median dollar volume (`dv20`, liquidity) within 0.10, nearest,
no reuse within a session, not flagged by the rule; «beyond the tool» additionally requires the same status of the
tool's technical part. Equal-burden rankings: on every session the same number of pivot-days as the rule flags, chosen
by highest `v1x` (VOL_k), highest `range20` (VOLAT_k) or lowest price (LOWPX_k). Ticker-cluster bootstrap.

## 5. Development results (read before this seal; `data/dev.json`, `data/dev_round2.json`)
Development: 69,794 pivot-days (798 symbols, 169 sessions); evaluable 63,708; POS710 base rate 3.06%; 1,581 clean
events in the window, 513 eligible, 1,020 with no pivot-day at all in [L−10, L−7] (outside the population).

Round 1 (declared before any number): individually only **RSI now** is informative — RSI30 lift 1.55 [1.33, 1.80],
matched 1.62 [1.17, 2.20]; RSI33 1.41 / 1.47. Hold 2/3/5 ≤ 1 (0.95–0.96); NEAR15 1.02 (matched 1.23 [1.01, 1.49]);
BOUNCE10_40 1.07 (matched 1.34 [1.11, 1.63]); BELOW3 1.05; momentum turn negative (EMA_X5 0.75 [0.55, 0.97], matched
0.49); MACD_POS 0.95; CYCLE3 1.00; SPLIT120 1.16 [0.99, 1.34]. Combinations: APP3 0.98 · SEQ_BASE 1.15 · SEQ_TURN 1.27
[0.98, 1.59] · CYCLE_NEAR 1.03 · TC_SPLIT 1.32 (n small). **Order test:** «oversold at the low, then hold»
(ORDERED) 0.96 vs «oversold now and hold» (SIMULTANEOUS) 1.49 [1.16, 1.86] — the order adds nothing; RSI now does.
Existing: the tool's technical part TC_TECH (RSI33 ∧ HOLD5 ∧ NO_BOOM) lift 1.65 [1.18, 2.15] at 13.7 flags/session,
recall 8.0%, matched 1.68 [1.06, 2.81]; the current READY location rule LOC 0.87.

Round 2 (post hoc on development, disclosed): adding the app chips to the tool adds nothing within the tool (TC∧BOUNCE
vs TC∧¬BOUNCE 1.09 [0.60, 2.17]; NEAR 0.68; both 0.70). Faisal's RSI text with the app's bounce band, **RN_A = RSI30 ∧
BOUNCE10_40**: lift 1.65 [1.36, 1.94] at 27.1 flags/session, recall 18.9% (97 of 513 events vs 41 for the tool; 81
caught only by RN_A, 25 only by the tool), matched 1.64 [1.16, 2.35]; rows the tool does not flag vs matched non-tool
controls 1.65 [1.12, 2.49]; vs VOL_k +2.08 pp [1.07, 3.23]; **vs VOLAT_k +0.53 pp [−0.52, 1.78] (not better than
ranking by volatility)**; bounce band within RSI30 1.18 [0.89, 1.64] (its contribution: −40% signals, −22% events).
RSI30 alone: lift 1.55, 45.1 flags/session, beyond the tool 1.57 [1.13, 2.14]. One third of RN_A's rows (1,480 of
4,454) are SEQ70 flag rows (top-quintile volume and negative 5-session return): RN_A is not that signal, and C1 below
matches on volume. Sensitivity: RN_A lift 1.57 (strict +70%), 1.61 (onset L10), 1.56 (onset IGN).

## 6. The candidate and the choice rule
Choice (development, stated before the seal): the candidate with the largest development «beyond the tool» lower bound,
burden as tie-break → RSI30 (1.126) and RN_A (1.118) tie within 0.01 → **RN_A (27 vs 45 flags/session)**.
**Candidate RN_A: RSI14 below 30 at the close, and the close's bounce from the 25-session low (max high since the low
day) between 10% and 40%.** Ablation (reported, not decisive): RSI30 alone. Comparators: TC_TECH, LOC, VOL_k, VOLAT_k,
LOWPX_k. No other rule is tested in the windows below.

## 7. Decision rules (each window; 97.5% two-sided ticker-cluster CIs, 2,000 resamples, seed 20261011)
- **C1** beyond price, volatility, liquidity and volume: matched ratio (RN_A rows vs controls) lower bound > 1.
- **C2** a better alarm at equal burden: RN_A precision minus VOL_k **and** minus VOLAT_k, both lower bounds > 0.
- **C3** beyond the existing tool: rows RN_A flags and TC_TECH does not, vs matched controls also not flagged by
  TC_TECH — matched ratio lower bound > 1.
- Floors per window: ≥ 20 eligible events, ≥ 300 C1 pairs, ≥ 200 C3 pairs; below a floor ⇒ the window is INSUFFICIENT.

Status: **VALIDATED_READY_SIGNAL** — C1, C2 and C3 pass in both windows (both sufficient) · **PROMISING_UNVALIDATED** —
not validated, but on the pooled windows (95%) the C1 and C3 lower bounds both exceed 1 · **NO_INCREMENTAL_EDGE_FOUND**
— otherwise · **BLOCKED_BY_SPECIFIC_DATA_GAP** — both windows insufficient. Reported in every window (never decisive):
precision with Wilson CI, lift, recall (events), FPR, groups A–D, flags and triggers per session, flagged sessions per
ticker, lead first flag → onset and → +70%, events caught only by RN_A or only by the tool, missed winners by
archetype, TC_TECH, LOC and RSI30 under the same metrics, the sensitivity labels, overlap with SEQ70's flag, events
outside the pivot population and whether RN_A held there.

## 8. Predictions (written before the run)
P1 C1 passes in the holdout · P2 C2 fails in at least one window (VOLAT_k ties in development) · P3 C3 passes in at most
one window · P4 status PROMISING_UNVALIDATED · P5 RN_A's median lead first flag → onset ≥ 10 sessions (it fires
earlier than the 7–10 ideal) · P6 RN_A captures more eligible events than TC_TECH in both windows.

## 9. Protection and reuse
One command computes validation and holdout together (`python3 faisal_engine/readynow/rn_eval.py final`) after this
file's hash check; no rule, threshold, window or control changes after the seal; the result is written once
(`data/result.json`). Reused read-only: READY70 bars, splits, detector, pivot population and features; SEQ70 path
descriptors and L10; `three_cond_daily.py` rules (read, not imported); `Super_stock.rsi` and `pivot_cycle_state`.
Not rerun: the 58-feature search, the alert comparison, the sequence experiment, any `CLOSED_RC` axis (RSI is used as
the tool's own READY condition, not as the screener gate of T-RSI40 nor the ranking key of T-RSI-RANK).
