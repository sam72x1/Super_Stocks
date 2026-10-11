# READY NOW — historical discovery of the missing technical conditions

Mission «HISTORICAL READY NOW DISCOVERY: FIND THE MISSING TECHNICAL CONDITIONS» (2026-10-11). Historical repository data
only; no forward collection, no download, no network, no agent or workflow, no production change. Files: this folder
(`rn_disc_build.py` dataset · `rn_disc_dev.py` development map · `rn_disc_seeds.py` seed matrix · `rn_disc_model.py`
ceiling test · `rn_disc_cand.py` candidates · `DISC_PROTOCOL.md` the sealed 2026 check · `test_disc.py` guards ·
`disc_mutate.py` mutations · `data/`).

**Answer.** **No pivot-specific technical condition was found.** The best daily-bar separator of pivots that start a +70% leg 7–10 sessions later is a generic «fresh volatile capitulation» — a wide 20-session range and a sharp 5-session decline at the 60-session low. Ranked at the existing tool's burden, it beats the tool's technical part in 2026 by +1.88 pp precision, pooled [0.26, 3.49] (5.6% vs 3.5–4.0%), and captures about 1.5× its events (46 vs 31, 28 vs 19) with fewer false positives. **It adds nothing over ranking by the 5-session decline alone** (+0.18 pp) or by volatility (+0.03). The seeds' volume-burst pattern failed on the population. Combining all daily features, with interactions, adds nothing beyond volatility. The missed winners look like the inactive pivots on every daily feature. Exploratory (the 2026 windows were read by earlier studies); sealed before the run (`DISC_PROTOCOL.md`); no production change.

Artifact counts, verified against `data/inventory.json` (rebuilt from READYNOW's rows, the READY70 detector and the
local bars): **174,796 pivot-days on 1,108 symbols, 3,727 clean episodes (3,842 with split-near ones), bars for 3,584
symbols**, decision rows 2025-05-01 → 2026-10-07. The figures quoted in the task match.

## 1. PRIOR_RESEARCH_COVERAGE

What was already tested on this question, and therefore not repeated (every entry points to its artifact).

| family | tested as | population · lead | verdict | artifact |
|---|---|---|---|---|
| RSI oversold + bounce 10–40% (RN_A) | sealed rule | pivot-days · onset t+7..t+10 (trough anchor) | NO_INCREMENTAL_EDGE_FOUND: lift 1.37 · 1.76, matched 1.25 [0.90, 1.71] pooled, no better than volume/volatility at equal burden | `readynow/RN_REPORT.md §8–12` |
| the three-condition tool's technical part (RSI < 33 ∧ hold 5 ∧ no boom) | reference | same | lift 1.07 · 1.64, CI includes 1 | `RN_REPORT.md §9` |
| app chips: within 15% · bounce 10–40% · hold 2 · EMA/MACD turn · cycle ≥ 3 · order «oversold then hold» | conditions, pairs, order test | same | nothing added (0.68–1.27); order 0.96 vs simultaneous 1.49 | `RN_REPORT.md §6–7`, `audit/RN_AUDIT.md §1–3` |
| parity of stability, EMA, retest, momentum chips with the app | chip parity on app snapshots | — | approximations, listed | `audit/RN_AUDIT.md §4` |
| volume while the 5-session path is still down (H-S70) vs the volume ranking | sealed hypothesis | pivot-days · +70% within 10 | PROMISING_UNVALIDATED; ≈ VOL-k at equal burden | `seq70/S70_RESULT.md` |
| cycle stage 1, DROP-k, VOL-k, PRICE-k | sealed comparison | pivot-days · f10 | generic DROP-k 12.06% and VOL-k 12.50% beat STAGE1 7.81% | `ready70/R70_RESULT.md §3–5` |
| room to overhead resistance · unfilled gaps above | development discovery | pivot-days · detection anchor | neither separated | `recon/RN_RECON.md §4–5` |
| candle shapes (hammer etc.) | arms | candidates | failed 0/6 | `DECISIONS_ARCHIVE.md` T-CANDLE |
| MA ladder 20/30/50 | arms | candidates | collapsed to MA50, not recommended | `ma_ladder_result.md` |
| pressure / squeeze (range compression) | radar, back-tests | candidates | T-PRESS-Q failed; T-PRESS-BT break-even | archive T-PRESS* |
| liquidity sweep then reclaim | arms | candidates | negative expectancy (−0.041R) | `sweep_reclaim_prereg.md` |
| quiet / dormant bottom · wake-ups | arms | candidates · radar cards | T-DORMANT 2/5 · T-WAKE 0/3 | archive lines 6303 · 6393 |
| support stability 3–8 sessions | gate | candidates | T-STABILITY failed | archive T-STABILITY |
| volume spike ≥ 10× on the alert day · prior pumps | link study | operator-alert anchors · explosion within days | 1.5–1.8×, «momentum by construction»; prior pumps return more often | `prelink_result.md` |
| volume ≥ 3× and 5-session gain > 20% the day before | link study | whole market · d−1 | both cross; «hot already», not a selection gate | `link100_result.md` |
| «operator is preparing it» (volume spike, range expansion, close position, critical level) | ranker arms | candidates | T-RANKER3 failed (5th failure of the family) | `ranker3_result.md` |

**Not tested before this study** (and tested here, §4–7): the corrected target (start of the final +70% leg, §2);
temporal order on daily bars — RSI divergence at a retest of the low, higher closing lows since the low, a quiet climb
off the low, «volume at the low then price recovering», first close above EMA20 after a long spell below; the seed
pattern «extreme volume burst with a flat-to-rising close 7–10 sessions before the leg» on pivot-days; the
«volatile and falling» profile of the captured group as one ranking, alone and as a second path beside the tool; and
the combined information of all point-in-time daily features (a ceiling model with pairwise interactions).

## 2. CORRECTED_EVENT_TIMELINES

**Three dates kept apart** (`rn_disc_build.py`; detector unchanged):
- **ONSET** — start of the final +70% leg: 1 + the latest close k in [L−1, Q−1] that is the lowest close of [k, Q−1]
  and from which the qualifying close was reached (close[Q] ≥ G × close[k]). Q = x70 (first close ≥ 1.70 × the
  trough close, G = 1.70); for a jump that never closes +70% above the trough, Q = D1 and G = 1.50.
- **Q** — the date the +70% close is reached (x70), or D1 for those jumps.
- **D1** — the detector's first detection (observable that day). Recorded real-time alerts are listed separately.

Labels: IN_EVENT for ONSET ≤ t ≤ max(P, D1, Q) (never a prediction), CENSORED when t + 29 is beyond the last bar,
UNKNOWN_SPLIT for a split-near onset in [t+1, t+10], **POS710 when a clean ONSET falls in [t+7, t+10]**, NEG otherwise.

**Why the correction matters.** Of 3,727 clean episodes the onset equals the old launch L in 1,839 and moves later in
1,888 (51%); in 1,079 it is the qualifying day itself (one-day jumps). 240 jumps never close +70% above the trough.
236 episodes sit on the detector's 20-session lookback edge (`edge_clipped`): their true trough may be earlier.
Under the old anchor a slow drift followed by a jump started at the bottom of the drift; under the corrected one it
starts at the jump.

**Limitations of the onset.** It is retrospective: known only once the +70% close prints (Q), and the trough it starts
from can be revised by a later, lower close inside the 20-session window. A rule is judged on the decision day t with
bars ≤ t; the onset is used only to label t afterwards.

**Seed timelines (onset · Q · D1 · recorded alerts).**

| episode | L | ONSET | Q | D1 | kind | recorded alerts |
|---|---|---|---|---|---|---|
| DLXY | 2025-12-29 | 12-29 | 12-30 | 12-30 | jump +67.9% | — |
| DLXY | 2026-03-04 | 03-04 | 03-04 | 03-04 | jump +75.3% | — |
| DLXY | 2026-04-02 | **04-13** | 04-21 | 04-21 | run +79.3% | — |
| DLXY | 2026-08-31 | **09-16** | 09-16 | 09-16 | jump +451.8% | liquidity anchors 09-16 08:01 and 08:07 (قوي), 09-18, 09-28 |
| RETO | 2026-02-24 | 02-25 | 03-03 | 03-03 | run +94.9% | — |
| RETO | 2026-04-14 | 04-14 | 04-16 | 04-16 | run +70.6% | — |
| RETO | 2026-09-15 | 09-15 | 09-15 | 09-15 | jump +676.3% | 09-08 15:13, 09-15 10:35 (قوي), later |
| DKI | 2026-02-02 | 02-02 | 02-02 | 02-02 | jump +185.3% | — |
| DKI | 2026-04-01 | **04-09** | 04-09 | 04-09 | jump +142.7% | — |
| SXTC | 2025-05-19 | 05-19 | 06-06 | 06-06 | jump +56.0% | — |
| SXTC | 2026-03-30 | 03-30 | 04-08 | 04-08 | run +73.1% | — |
| SXTC | 2026-06-08 | 06-08 | 06-12 | 06-12 | run +78.5% | — |
| SXTC | 2026-07-30 | **08-03** | 08-04 | 08-04 | jump +60.1% | 08-21, 09-11, 09-29 (later moves) |
| SXTC | 2026-10-07 | 10-07 | 10-07 | 10-07 | jump +126.4% | — |

DKI 2026-09-24 has a recorded liquidity anchor; **DKI's 2026-10-07 move was intraday only** (high +167.6%, close
+22.8%): no daily-close detection, so it is neither a success nor a failure here. HUBC (separate, active, never a
success) has seven episodes since 2025-07; none enters a statistic.

## 3. SEED_CASE_TECHNICAL_MATRIX (`data/seed_matrix.json`; descriptive — seeds never enter a statistic)

«App position» = within 15% of the 25-session low ∧ bounce 10–40% (`APP_POS`); H-S70 = r5 < 0 ∧ volume in the session's
top quintile; LOC = the current READY location rule.

State at T−10 … T−7 before each corrected onset, from bars ≤ that day (values for days that were not pivot-days are
computed the same way and marked).

| episode | pivot-days in window | profile at T−10..T−7 | existing rules that flag it |
|---|---|---|---|
| DLXY 09 | 4 of 4 | **volume burst v1x 59.8 at T−10** (then 7.2), r5 +12…+17%, RSI 49–57, hold 17–20 | none |
| RETO 02 | 4 of 4 | dry volume (v1x 0.23–0.39) then **burst v1x 114 at T−7**, RSI 31–36, range20 105% | TC_TECH T−9, T−8 · app position T−10..T−8 · nothing on the burst day |
| DLXY 04 | 4 of 4 | burst v1x 15.7 at T−10 with r5 −13%, range20 222%, RSI 35–41 | H-S70 T−10, T−9, T−7 · app position · LOC T−9 |
| RETO 09 | 4 of 4 | repeated bursts (v1x 31, 23, 45) while falling (r5 −12…−24%), range20 293% | H-S70 all four · TC_TECH T−7 |
| SXTC 2025-05 | 4 of 4 | bursts v1x 15–644 while falling (r5 −7…−42%), range20 239% | H-S70 all four |
| SXTC 07 | 3 of 4 | burst v1x 7.8 with r5 +11% (T−9), then 1,115 with r5 −22% (T−8) | H-S70 T−8 |
| DKI 04 | 4 of 4 | quiet (v1x 0.2), r5 −6…−19%, RSI 31–38, at the low | app position T−8, T−7 |
| SXTC 03 | 4 of 4 | quiet, RSI ≈ 24, r5 −13…−30% | RN_A and app position all four · STAGE1 T−8, T−7 |
| SXTC 06 | 4 of 4 | RSI 32–35, v1x 0.3–2.5, flat | app position all four · TC_TECH and LOC T−8 |
| DLXY 03 | 4 of 4 | RSI 47–54, hold 22–24, bounce 40% | app position T−10, T−8 |
| RETO 04 | 4 of 4 | stage 4, 47–58% above the low, volume very dry (v1x 0.07–0.14) | none |
| DKI 02 · DLXY 12 · SXTC 10 | 0 | not pivot-days in the window (outside the population) | on those days: none · app position · TC_TECH all four |

**Commonalities:** none shared by all. Two recurring shapes — (i) **an extreme single-day volume burst** in 6 of the 11
pivot windows (3 with a rising close: DLXY 09, RETO 02, SXTC 07 at T−9), and (ii) **a quiet, oversold base at the low**
(DKI 04, SXTC 03, SXTC 06). **Differences:** DLXY 03 and RETO 04 were neither — high RSI, long hold, dry volume well above
the low. **The existing tool** (TC_TECH) flags 3 of the 11 windows; the rising-close bursts are flagged by nothing.
**Exact vs proxy:** RSI, hold, boom, bounce and distance are the tool's own definitions on daily bars; hourly lows,
after-hours highs, float and available-to-borrow are not reconstructable, so the tool's full state is a proxy.

## 4. MISSED_WINNER_ANALYSIS (development 2025-05-01 → 12-31; `data/dev_map.json`)

69,794 pivot-day rows (65,306 evaluable; base rate 3.12%), 540 eligible events (a POS710 pivot-day in
[onset−10, onset−7]). Reference union = TC_TECH ∨ RN_A ∨ H-S70 ∨ STAGE1 ∨ LOC (105 flags per session).
- **A** events captured by the union: 267 · **B** missed: 273 · **C** flagged rows without an event: 16,657 · **D**
  unflagged rows without an event: 46,609. TC_TECH alone captures 44 and misses 496.

Medians (A · B · D): RSI 33.9 · 46.3 · 45.1 · r5 −11.3% · 0.0% · −1.0% · range20 87% · 52% · 51% · v1x 1.75 · 0.91 ·
0.86 · close in the 60-session band 0.04 · 0.23 · 0.19 · distance from the 25-session low 8.5% · 20.4% · 17.2% ·
hold 2 · 13 · 12 · sessions since the 60-session low 5 · 28 · 24 · price $1.68 · $1.56 · $1.86.

**B versus A:** the captured group is a capitulation — oversold, falling, volatile, at the low on rising volume. **The
missed winners look like the inactive pivots, not like A.** Inside the 47,985 unflagged rows (base 2.87%), no quartile
of any of 25 point-in-time features moves the rate outside 0.79–1.27× (largest: price in the lowest quartile 1.27 ·
RSI-divergence gap Q3 1.14 · range20 Q4 1.13 · r5 Q1 1.13). The new temporal features: RSI divergence 0.56 (248 rows) ·
quiet climb off the low 1.04 · «volume at the low then up» 1.02 · first close above EMA20 after a long spell 0.81 (ema_x5).
The only large separator is `in_drift` (7.54×) — the stock is already in the slow part of an episode — which is defined
by the outcome and is not a feature.

**Ceiling of daily information (`data/model_dev.json`; train 2025-05 → 09, test 2025-10 → 12).** A ridge logistic model
on every point-in-time feature (M_MAIN) and with all pairwise products (M_INT) scored **below** a single volatility
ranking out of time:

| test 2025-10 → 12 | all rows (28,150 · 677 pos.) | rows the union ignores (21,060 · 433 pos.) |
|---|---|---|
| M_MAIN AUC (minus volatility) | 0.553 (−0.054 [−0.101, −0.004]) | 0.514 (−0.082 [−0.150, −0.013]) |
| M_INT AUC (minus volatility) | 0.533 (−0.075 [−0.127, −0.018]) | 0.490 (−0.105 [−0.185, −0.028]) |
| volatility (range20) · 5-session drop · low RSI | 0.608 · 0.608 · 0.590 | 0.595 · 0.575 · 0.538 |
| volume ratio · low price · TC_TECH | 0.502 · 0.520 · 0.513 | 0.506 · 0.493 · — |

Training AUCs were 0.59 and 0.71: the extra structure the models found in May–September did not hold in
October–December. Among the missed winners there is no stable daily-bar signature to find.

## 5. NEW_CONDITION_CANDIDATES (declared in `rn_disc_cand.py` before their rates were computed)

| name | exact formula (bars ≤ T) | tied to |
|---|---|---|
| BURST_UP | v1x(T) ≥ 5 ∧ r5(T) ≥ 0 | seed bursts with a rising close (DLXY 09-01, RETO 02-13) — flagged by no existing rule |
| BURST_UP_3 | max v1x(T−2..T) ≥ 5 ∧ r5(T) ≥ 0 | same, 3-session lookback (decisions at T−9, T−8 after a T−10 burst) |
| BURST_ANY_3 | max v1x(T−2..T) ≥ 5 | the burst alone, to separate «burst» from «burst with a rising close» |
| PATH2 | REF_UNION ∨ BURST_UP_3 | two paths: the existing capitulation rules + the burst path |
| CAPIT_TC | per session, the k pivot-days with the highest p_range20 + (1 − p_r5), k = TC_TECH's flags that session | the profile of group A (§4) as one explainable ranking at the tool's own burden |
| TC_OR_CAPIT | TC_TECH ∨ CAPIT_TC | added after development showed the two catch almost disjoint events (59 and 44, 3 shared) |
| the five temporal features | `rn_disc_build.temporal` | untested order structures (§1) — mapped in §4, none promoted |

v1x = volume / median volume of sessions j−60..j−11 (SEQ70's definition; equal to the stored value to 5e−05 on all
69,794 development rows). 5 = `VOL_SPIKE_MULT`, the production constant («شمعة الفوليوم الضخمة ≥ 5x») — no threshold
was fitted. p_ = mid-rank percentile among the session's pivot-days. Everything is computable from daily OHLCV at the
close of T.

## 6. INDIVIDUAL_CONDITION_VALUE

Per window: flags per session · precision · lift vs the window's base [95%] · events captured of eligible · matched ratio
(same session, price bucket, volume / volatility / dollar-volume percentiles within 0.10) · events added beyond
REF_UNION and the precision of the added flags vs the base of the rows REF_UNION ignores · precision minus the
volatility (VOLAT_k) and drop (DROP_k) rankings at the same burden (pp). Development 2025-05 → 12 (540 events, base
3.12%) · validation 2026-01-16 → 05-15 (334, 3.16%) · holdout 2026-06-02 → 08-27 (219, 2.59%).

| rule | window | flags/s | precision | lift | events | matched | + beyond union (added prec · base) | − VOLAT_k | − DROP_k |
|---|---|---|---|---|---|---|---|---|---|
| TC_TECH (tool) | dev | 13.7 | 5.14% | 1.65 [1.20, 2.13] | 44 | 1.45 [0.91, 2.36] | — | +0.21 | −0.61 |
| | val | 21.6 | 3.52% | 1.11 [0.74, 1.53] | 31 | 0.90 [0.53, 1.54] | — | −1.04 | −1.88 [−3.92, 0.04] |
| | hold | 20.2 | 3.97% | 1.53 [0.92, 2.21] | 19 | 1.64 [0.84, 3.21] | — | −3.11 [−6.85, 0.20] | −1.44 |
| BURST_UP | dev | 28.8 | 2.66% | **0.85 [0.63, 1.09]** | 59 | **0.55 [0.33, 0.85]** | +33 (2.75% · 2.87%) | −1.67 [−2.84, −0.53] | −2.12 [−3.39, −0.86] |
| | val | 30.8 | 3.76% | 1.19 [0.82, 1.59] | 36 | 1.06 [0.56, 1.88] | +16 (3.90% · 2.84%) | −1.09 | −1.29 |
| | hold | 38.8 | 4.16% | 1.61 [1.07, 2.18] | 37 | 0.98 [0.54, 1.66] | +17 (4.15% · 2.25%) | −1.79 [−3.59, −0.23] | −0.52 |
| BURST_UP_3 | dev | 44.9 | 2.70% | 0.86 [0.67, 1.07] | 83 | 0.57 [0.38, 0.81] | +47 (2.74% · 2.87%) | −1.49 | −1.59 [−2.62, −0.58] |
| | val | 47.0 | 3.61% | 1.14 [0.85, 1.46] | 54 | 1.14 [0.72, 1.78] | +26 (3.69% · 2.84%) | −1.35 | −1.34 |
| | hold | 61.8 | 3.44% | 1.33 [0.96, 1.70] | 49 | 1.00 [0.60, 1.58] | +25 (3.49% · 2.25%) | −2.04 [−3.42, −0.75] | −0.49 |
| BURST_ANY_3 | dev | 99.4 | 3.49% | 1.12 [0.96, 1.26] | 182 | 0.80 [0.57, 1.11] | +56 (3.04% · 2.87%) | −0.33 | −0.39 |
| | val | 110.6 | 4.18% | 1.32 [1.11, 1.54] | 121 | 1.31 [0.86, 1.97] | +30 (3.64% · 2.84%) | −0.86 [−1.53, −0.19] | −0.11 |
| | hold | 147.0 | 3.66% | 1.41 [1.18, 1.67] | 100 | 1.02 [0.66, 1.53] | +26 (3.28% · 2.25%) | −0.43 | +0.54 |
| **CAPIT_TC** | dev | 13.7 | 5.97% | 1.91 [1.43, 2.44] | 59 | 2.15 [1.32, 3.50] | +6 (7.64% · 2.87%) | +1.04 [−0.36, 2.40] | +0.22 |
| | val | 21.6 | **5.57%** | **1.76 [1.30, 2.28]** | **46** | 1.26 [0.72, 2.22] | +6 (4.82% · 2.84%) | +1.01 | +0.17 |
| | hold | 20.2 | **5.60%** | **2.16 [1.47, 2.89]** | **28** | 1.39 [0.79, 2.45] | +3 (4.58% · 2.25%) | −1.48 | +0.19 |

**Burst path (the seed observation).** Development contradicts it: a rising-close burst is followed by the final leg
*less* often than the average pivot-day (0.85) and than same-volume controls (0.55). In 2026 it is around 1 against
matched controls (1.06 · 0.98) and below the volatility ranking at its own burden in every window. What the burst
carries is the volume level itself, not readiness; the seeds' bursts were the visible part of a common event (a
burst of 5× or more in the last 3 sessions flags 99–147 pivot-days per session).

**CAPIT_TC (the captured group's profile).** At the tool's own burden it is the strongest condition in every window
(lift 1.91 · 1.76 · 2.16, CI above 1 each time) and its 2026 halves stay above 1.6 (validation 1.64 · 1.89, holdout
2.37 · 2.00 lift). **But it is not independent of volatility:** every flag lies in the top quartile of the 20-session
range by construction; inside that quartile its precision is 5.99% · 5.57% · 5.60% against the quartile's own base
3.87% · 4.64% · 4.13% (1.55 · 1.20 · 1.36×), and against matched controls (which hold volatility, volume and dollar
volume fixed) it is 2.15 in development but 1.26 and 1.39 with intervals including 1 in 2026. In each 2026 window its precision
is above the cell's own base in all four price buckets and all four dollar-volume quartiles (small cells).

**The temporal-order features** (§4) — RSI divergence at the low, higher closing lows, quiet climb, volume-at-the-low
then up, first close above EMA20 — moved the unflagged rate by 0.56–1.04× in development and were not carried forward.

## 7. COMBINATION_AND_SEQUENCE_RESULTS

| rule | window | flags/s · triggers/s | precision · FPR | lift | recall (events) | matched | lead to onset · to +70% (q25/med/q75) |
|---|---|---|---|---|---|---|---|
| TC_OR_CAPIT (two paths) | dev | 26.9 · 6.4 | 5.58% · 6.6% | 1.79 [1.48, 2.12] | 100/540 (18.5%) | 1.71 [1.18, 2.44] | 10/12.5/18 · 11.8/18.5/22.3 |
| | val | 42.4 · 9.4 | 4.47% · 8.6% | 1.41 [1.10, 1.73] | 73/334 (21.9%) | 1.09 [0.72, 1.57] | 9/13/18 · 12/15/20 |
| | hold | 39.8 · 9.7 | 4.80% · 6.9% | 1.86 [1.41, 2.34] | 45/219 (20.5%) | 1.39 [0.90, 2.13] | 9/12/20 · 11/15/20 |
| PATH2 (union + burst) | dev | 147.6 · 18.9 | 3.57% · 34.6% | 1.14 [1.05, 1.24] | 314/540 | 1.08 [0.86, 1.35] | 12/16/20 · 15/20/24 |
| | val | 184.2 · 24.1 | 3.91% · 35.3% | 1.24 [1.11, 1.36] | 218/334 | 1.23 [0.95, 1.61] | 13/18/20 · 16/20/25 |
| | hold | 210.7 · 28.8 | 3.48% · 35.9% | 1.35 [1.20, 1.49] | 149/219 | 1.38 [0.99, 1.90] | 11/17/20 · 14/19/21 |
| REF_UNION (reference) | val · hold | 140.3 · 151.5 | 3.95% · 3.48% | 1.25 · 1.34 | 192 · 124 | 1.23 · 1.24 | 12/16/20 · 10/16/20 |

- **Two paths.** TC_TECH and CAPIT_TC catch almost disjoint events (both: 3 of 100 in development, 4 of 73 in
  validation, 2 of 45 in the holdout). Their union doubles the tool's recall (31 → 73, 19 → 45) at twice its burden, with
  lift above 1 in each window — but it fails the matched criterion in validation (1.09) and is no better than the
  volatility, drop or low-RSI rankings at its burden (−0.80 … +1.24 pp, all intervals include 0). Sealed verdict:
  TWO_PATHS_NOT_SUPPORTED.
- **Burst as a second path** (PATH2): +47 · +26 · +25 events over REF_UNION for +43 · +44 · +59 flags per session;
  the added flags' precision is 2.7% · 3.7% · 3.5%. Verdict: BURST_NOT_SUPPORTED.
- **Interactions and sequences.** The interaction ceiling (M_INT, every pairwise product) scored below the single
  volatility ranking in every test (AUC minus volatility −0.075 dev · −0.055 [−0.093, −0.015] val · −0.070 [−0.115,
  −0.022] hold); the main-effects model equalled it (−0.006 [−0.033, 0.021] · +0.012 [−0.016, 0.043]). Sealed verdict:
  NO_INFORMATION_BEYOND_VOLATILITY. The order «oversold first, then hold» was already tested (READYNOW, 0.96) and is not
  repeated.
- **Chronology** (lift per half-window): CAPIT_TC 1.62 · 2.29 (dev) · 1.64 · 1.89 (val) · 2.37 · 2.00 (hold);
  TC_OR_CAPIT 1.68 · 2.00 · 1.21 · 1.58 · 1.65 · 1.96; BURST_UP 0.86 · 0.75 · 1.47 · 1.03 · 1.98 · 1.28 (unstable,
  sign of the edge changes between development and 2026).

## 8. COMPARISON_WITH_EXISTING_TOOL

Paired at the same per-session burden (precision difference in percentage points, ticker-cluster 95%):

| CAPIT_TC minus | dev | val | hold | pooled 2026 |
|---|---|---|---|---|
| **TC_TECH (the tool's technical part)** | +0.83 [−1.43, 3.00] | +2.05 [0.13, 4.00] | +1.63 [−0.93, 4.22] | **+1.88 [0.26, 3.49]** |
| DROP_k (largest 5-session decline) | +0.22 [−0.76, 1.20] | +0.17 [−0.96, 1.27] | +0.19 [−1.15, 1.45] | +0.18 [−0.67, 1.06] |
| VOLAT_k (widest 20-session range) | +1.04 [−0.36, 2.40] | +1.01 [−0.63, 2.71] | −1.48 [−4.30, 0.95] | +0.03 [−1.50, 1.51] |
| LOWRSI_k (lowest RSI) | +1.41 [−0.18, 3.18] | +0.67 [−1.29, 2.55] | +1.99 [−0.27, 4.42] | +1.20 [−0.26, 2.67] |

- **Against the tool:** at the same number of flags (21.6 · 20.2 per session; 5.6 new triggers per session) CAPIT_TC
  has precision 5.57% vs 3.52% and 5.60% vs 3.97%, captures **46 vs 31 and 28 vs 19 events** (42 and 26 of them not
  captured by the tool; the tool's 27 and 17 not captured by CAPIT_TC), and raises **73 and 42 fewer false positives**
  (1,626 vs 1,699 · 1,096 vs 1,138). Lead from the first flag: median 10 and 11 sessions to the onset, 14 and 14.5 to
  the +70% close (the tool: 11 and 12 · 13 and 18).
- **Against generic rankings:** CAPIT_TC is indistinguishable from simply ranking pivot-days by their 5-session decline
  (+0.18 pp pooled; events 46 vs 50, 28 vs 30) or by their 20-session range (+0.03). The tool's technical part itself
  sits *below* the drop ranking at its burden (−1.88 · −1.44 pp). **The value CAPIT_TC adds over the tool is the value
  of the generic capitulation ranking, not of a pivot-specific pattern.**
- **Against the union of all reference rules** (TC_TECH ∨ RN_A ∨ H-S70 ∨ STAGE1 ∨ LOC, 140–152 flags per session):
  CAPIT_TC's events are almost all already flagged there (+6 and +3 events) — the union reaches them only at seven
  times the burden.
- **Sealed verdict for CAPIT_TC: IMPROVES_ON_TOOL_EQUAL_TO_GENERIC** (A1 ✓ · A2 ✓ · A3 ✗).

## 9. HISTORICAL_VALIDATION_LIMITATIONS
- **No pristine holdout.** The 2026 windows were read by READYNOW (RN_A, trough anchor), READY70 and SEQ70 (other rules
  and targets). This study's development never read them, the candidates and decision rules were sealed and pushed
  before the single run (`DISC_PROTOCOL.md`), and every 2026 number here is labelled exploratory.
- **Development informed two candidates.** CAPIT_TC encodes the captured group's profile read in development, and
  TC_OR_CAPIT was added after the development overlap table; their development numbers are in-sample.
- **Untestable with local data** (marked, not approximated): float and available-to-borrow point in time (the forward
  borrow harvest starts 2026-08), hourly lows and after-hours highs (the tool's exact stability and boom), pre-market and
  intraday timing (DKI 2026-10-07), the app's own chip states, and operator tape. Any rule that needs them cannot be
  judged here.
- **Population.** Only pivot-days are scored; they cover about a third to a half of the events 7–10 sessions ahead
  (`recon/RN_RECON.md`). Missed events outside the population are a population question, not a readiness one.
- **Target.** Daily-close detector only; split-near episodes are excluded from positives (UNKNOWN_SPLIT); 236 episodes
  sit on the 20-session lookback edge, so their onset may be later than the true start of the decline-to-leg
  sequence; survivorship (today's listings) and split-adjusted volume as in the earlier studies.
- **Seeds and HUBC** generated hypotheses and enter no statistic. One seed pattern (rising-close volume bursts) was
  turned into a candidate precisely so that the population, not the seeds, could judge it.
- **Matched controls** describe the matched part only (rows with an extreme profile find no control); ticker-cluster
  bootstrap intervals; multiple candidates were examined, so a single interval that excludes 1 is weak evidence.
- **A counting defect found after the sealed run, corrected and disclosed.** Ten of 3,727 clean episodes share their
  corrected onset with the next episode of the same symbol (the first one's +70% close is the day the second starts),
  so the event index listed them twice: eligible events 542 → 540 (development), 335 → 334 (validation), 222 → 219
  (holdout). `rn_disc_dev.unique_events` now keeps one per (symbol, onset). The sealed run's output is kept as
  `data/cand_final_asrun.json`; the corrected rerun differs from it **only in event counts and lead times — zero
  row-level differences** (precision, lift, matched ratios, equal-burden and paired differences, which carry every
  decision rule of `DISC_PROTOCOL.md §③`). The protocol file was not edited; `final` was run twice, the second time with
  only this change.

## 10. PROPOSED_READY_NOW_CANDIDATE

**Sealed verdicts (`data/verdict.json`, from `rn_disc_verdict.py`):** burst path BURST_NOT_SUPPORTED (all four) ·
**CAPIT_TC IMPROVES_ON_TOOL_EQUAL_TO_GENERIC** · TC_OR_CAPIT TWO_PATHS_NOT_SUPPORTED · ceiling
NO_INFORMATION_BEYOND_VOLATILITY. Predictions: Q1 ✓ · Q2 ✓ · **Q3 ✗** (I expected CAPIT_TC not to beat the tool; it
did, pooled +1.88 pp) · Q4 ✓ · Q5 ✓ · Q6 ✓.

**The one candidate that survives — exploratory, not validated:**

> **READY_CAPIT** — on each session, among the pivot-days (M1–M3 identity), rank by
> `p_range20 + (1 − p_r5)` and take the top K, where
> `range20 = max(high, last 20 sessions) / min(low, last 20 sessions) − 1`,
> `r5 = close / close 5 sessions earlier − 1`, `p_` = mid-rank percentile among that session's pivot-days, and
> K = the number of pivot-days the three-condition tool's technical part flags that session (≈ 14–22).

- **Extra winners vs the tool at equal burden:** +15 events (46 vs 31) in validation and +9 (28 vs 19) in the holdout;
  42 and 26 of its events are ones the tool never flags.
- **Missed:** 288 of 334 and 191 of 219 eligible events (recall 13.8% · 12.8%) — most qualifying moves give no
  daily-bar sign 7–10 sessions ahead.
- **False-positive burden:** 94.4% of its flags are not followed by a qualifying onset 7–10 sessions later (precision
  5.6%, about 1 in 18), 73 and 42 fewer false positives than the tool at the same number of flags; ≈ 5.6 new names per
  session.
- **Lead:** median 10–11 sessions from the first flag to the start of the final leg, 14–14.5 to the +70% close.
- **What it is:** a «fresh volatile capitulation» ranking — the profile of the events the existing rules do catch
  (RSI ≈ 34, 5-session decline ≈ 11%, close at the 60-session low, hold ≈ 2 sessions). **It equals ranking by the
  5-session decline alone** (+0.18 pp [−0.67, 1.06]); the decline alone is the simpler equivalent. It is not a
  pivot-specific readiness pattern, and against matched controls of the same volatility and volume it is not
  significant in 2026.
- **Not proposed:** the burst path, the two-path union, any temporal-order condition, and any combined model.

**Why no stronger rule is justified.** The missed winners (group B) carry the same daily-bar profile as inactive pivots
on every feature; a model using all of them, with interactions, does not beat volatility out of time; the one
seed-derived structure (volume burst with a rising close) failed on the population. What still separates winners is
outside daily bars — float and borrow point in time, intraday and pre-market timing — and is untestable here (§9).

Production, live rules, frozen axes, Telegram behaviour and candidate membership are unchanged. Using READY_CAPIT (or
the 5-session-decline ranking) in the tool would be a production decision for the owner, and it would still have only
exploratory support.

## Files
`rn_disc_build.py` (`--check`) · `rn_disc_dev.py` · `rn_disc_seeds.py` · `rn_disc_model.py dev|final` ·
`rn_disc_cand.py dev|final` · `rn_disc_verdict.py` · `DISC_PROTOCOL.md` (SHA-256 `a75d21b9…20a0`, pinned in the two
`final` modes) · `test_disc.py` (DG1–DG8; `DISC_FAST=1` skips the slow regenerations) · `disc_mutate.py`
(`data/mutations.json`: nine of nine fell on their own guard) · `data/` (rows · events · alerts · inventory ·
dev_map · seed_matrix · model_dev · model_final · cand_dev · cand_final · cand_final_asrun · verdict · mutations).
