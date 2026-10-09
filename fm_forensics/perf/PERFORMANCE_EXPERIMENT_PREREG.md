# PERFORMANCE EXPERIMENT — PRE-REGISTRATION (frozen before any new number)

Date: 2026-10-09 · Repository: `main` = `b8b1242e91c9fce079a95e6b32e0c76b0e4ba697` (after PR #585) · Research branch only · No production change.

## 0. Scope freeze (what exists, verified from the repository at this commit)
| Item | Value (source) |
|---|---|
| Frozen bot | `Super_stock.py` at `b8b1242e` (`LOGIC_VERSION …+pivotstoplow`, `FAISAL_ONLY=1` envelope `envelope_p100.json`); roots fingerprint unchanged since Phase 5 |
| Frozen V4 | `faisal_method_v4/` freeze `5f291a3b…` — untouched, not used here |
| Bars (lookahead-firewalled) | `fm_forensics/data/bars_2026-10-08.json.gz`: 232 symbols, daily 2025-01-02 → 2026-10-08, split-adjusted TradingView |
| Dated Faisal decisions (Target A positives) | `fm_forensics/phase3/FAISAL_TIMELINE.csv`, `IS_FAISAL=1`, classes FOCUS/WATCH/READY/ENTRY, with bars: **83 rows / 41 securities** — discovery 46 rows / 22 securities · validation 29 / 16 · anchors 8 / 3 (DKI, SXTC, HUBC). Phase 5 episodes: 46 (38 primary units with bars). |
| Label classes available | POSITIVE_DIRECT 88 (Phase 5 manifest; FOCUS 10 · WATCH 68 · READY 6 · ENTRY 4); NEGATIVE_DIRECT 2 (BTOG 2026-09-04, LABT 2026-07-05: explicit REJECT); EXIT 2 (BNAI, CDIO); UNKNOWN 15 Faisal rows with no classifiable state; MENTION 128 (not decisions) |
| Matched controls (Baseline 3) | Phase 4 frozen procedure: identity-eligible-without-anchor names on an untested 30-bar low, matched by date to each positive (never using future outcomes): **88 control-days (discovery) · 64 (validation) · 12 (anchor)** — `fm_forensics/phase4/out/arch_controls_*.csv` |
| Current bot performance (reproducible) | Phase 3/4: candidate at the decision date 2/46 rows (discovery), 3/29 (validation), 0/8 (anchors); A flags 15/88 = 17.0% and 15/64 = 23.4% of matched control-days |
| Universe-level volume (production logs) | `reject_log.json` 20 days (2026-09-11 → 10-08): anchor-rule rejections 373–400 symbols/day (cap 400); `weekly_watchlist.reject_stats`: valid universe ≈ 3,388, passes ≈ 109/day (2026-08-14 example, derived as valid − Σ rejections) |
| Known limitations | 16/38 first dates weekend-mapped to the next session (Phase 4); HUBC Faisal state UNKNOWN (kept); non-candle inputs have no point-in-time history before 2026-10-09 (Phase 5/6); thresholds replayed are today's envelope; no Faisal decision after 2026-10-08 is available |

## 1. Research question (one)
Does separating **early candidate discovery** from **later technical readiness** — architecture **B** of Phase 4, i.e. the frozen gates with the two-touch anchor rule moved from admission to the alert stage, holding the name from its first touch of the 30-bar low — identify Faisal-selected securities before his documented decision and before their major move, better than the frozen bot, without an unacceptable increase in false alerts?

Why B and not another alternative: Phases 2–6 located the first reproducible divergence at candidate generation, and specifically at the anchor rule at admission (first wall on 20/53 dated rows; fails independently on all 6 anchor rows in Phase 6). B is the *existing, frozen* Phase 4 definition (`phase4/arch.py`): no new parameter, no new model, no tuning. Phase 4 reported B's row-level recall and alert-noise; it did **not** report precision/likelihood ratio at a common alert stage, security-level recall with uncertainty, lead time to Faisal's date and to the move, candidate volume, or Target C outcomes with matched controls. That is the specific, documented reason for re-using the frozen split here.

## 2. Targets (never combined)
- **TARGET A — Faisal selection:** contemporaneous dated evidence of FOCUS/WATCH/READY/ENTRY (classes from Phase 3, provenance in `FAISAL_TIMELINE.csv`). Categories: POSITIVE_DIRECT (dated text/action), POSITIVE_STRONG (dated chart/app screenshot with state), NEGATIVE_DIRECT (explicit REJECT), NEGATIVE_OBSERVED (not available — no contemporaneous "did not select" evidence exists; matched controls are **UNKNOWN**, not negatives), UNKNOWN (no classifiable Faisal state, e.g. HUBC), RIGHT_CENSORED (decision within 20 sessions of 2026-10-08 — outcomes incomplete), CONTAMINATED (rows used to design B in Phase 4: the whole discovery set; the validation set was viewed once in Phase 4 for recall/noise).
- **TARGET B — early identification:** the method's state on day T uses bars < T and events dated ≤ T only.
- **TARGET C — subsequent price outcome:** from the T−1 close: +50% high within 20 sessions (primary), +100% within 60 (secondary), adverse = max drawdown from T−1 close before the first +50% (or within the window if never).

## 3. Cohort, inclusion/exclusion
Included: every Target-A positive row with bars (83 rows / 41 securities) and every Phase 4 control-day (164). Excluded: MENTION rows, UNKNOWN-state rows, rows without bars (ATPC, LABT, MI, UNK — named in Phase 5). Anchors (DKI/SXTC/HUBC) are reported separately and excluded from all acceptance counts. HUBC's Faisal state stays UNKNOWN; its row is diagnostic only.

Development data = discovery set (22 securities, used to design B in Phase 4). Validation data = Phase 4 validation set (16 securities): **contaminated by one prior view** (Phase 4 reported its recall/noise); no untouched Faisal decision exists after 2026-10-08. Consequence declared now: the best attainable verdict is **B. PROMISING BUT UNVALIDATED**; "A. VALIDATED IMPROVEMENT" is unreachable with this data and will not be claimed.

## 4. Methods compared (all with bars < T, identical windows)
- **BASELINE 1 (A, frozen bot):** `analyze_ticker` candidate on day T (`bot_states.csv.gz` / `p3lib.run_gates`); identification = candidate.
- **BASELINE 2 (simple screen):** RSI14(T−1) < 33 and drop from 52-week high ≥ 70% (the two numeric conditions of Faisal's "three conditions" as the bot encodes them; no anchor, no gates). Identification = screen true at T.
- **BASELINE 3 (matched controls):** Phase 4 control-days; each method's rate on control-days is its false-flag rate.
- **ALTERNATIVE (B):** observation = first touch of the 30-bar low while identity-eligible without the anchor (`REMOVE_candidate`); alert = production `tested_level(30, 1.5%, 2)` satisfied later on the same level (E2). Identification for the primary metric = **alert (B_watch_ready)**; observation reported separately.

## 5. Metrics (denominators always stated)
Independent unit = security (cluster). Row-level numbers reported with security-level numbers.
- Recall (security-level): share of securities with ≥ 1 positive row identified **on or before** its earliest dated decision.
- Control false-flag rate: identified control-days / control-days (and per matched security).
- **Primary metric:** likelihood ratio **LR = security-level recall (alert stage) ÷ control-day flag rate (alert stage)**, per set.
- Lead time: sessions from first identification to (i) Faisal's earliest dated decision, (ii) first +50% session; negative = after.
- Volume: identified securities per observation day on the frozen 232-symbol panel (bot_states dates), and universe-level proxy from `reject_log`/`reject_stats` (anchor-rule rejections per day = B's observation pool additions; passes per day = A's candidates).
- Uncertainty: cluster bootstrap by security (B = 2000, seed 20261009) for recall differences and LR ratios; Wilson 95% for single rates.
- Target C: % making the move, time to move, adverse move, vs the same statistics on matched control-days flagged by each method; sensitivity: horizons 10/20/40 sessions and +30%/+50%/+100% (secondary).

## 6. Acceptance rule (declared before computing; based on the baseline A values above)
B is "promising" only if **all** hold on **both** sets (discovery and validation), anchors excluded:
1. LR_B ≥ 2 × LR_A, and the cluster-bootstrap 95% interval of LR_B / LR_A excludes 1.
2. Security-level alert-stage recall_B − recall_A ≥ +0.10 absolute with bootstrap 95% lower bound > 0.
3. B's control-day alert rate ≤ A's control-day candidate rate (0.170 discovery / 0.234 validation).
4. Lead time: among securities B identifies, the median first identification is ≥ 1 session **before** Faisal's earliest dated decision.
5. Robustness: 1–3 keep their direction with weekend-mapped (ambiguous-date) rows excluded, and with the two POSITIVE_STRONG-only securities excluded.
6. B beats Baseline 2 on LR on both sets (otherwise the simple screen explains the result).
Failing any of 1–6 ⇒ **C. NO DEMONSTRATED IMPROVEMENT**. If fewer than 10 securities per set remain evaluable ⇒ **D. INSUFFICIENT EVIDENCE TO TEST**. Target C never enters the acceptance rule.

## 7. Stopping rule
One run of the frozen comparison; no variant search; no threshold change after viewing. The task ends with the verdict file.

## 8. Lookahead / contamination controls
Bars < T for every state; Faisal states from units dated ≤ T; controls chosen without future outcomes (Phase 4 procedure); Target C computed after states are frozen (`p3lib.outcomes`); every row carries `DATA_CUTOFF`; anchors excluded from counts; no parameter is set from DKI/SXTC/HUBC.

## 9. Boundaries
No production, V4, Telegram, threshold or three-condition change; research files under `fm_forensics/perf/` only; isolated suite + CI before any push; production roots fingerprint compared before/after.
