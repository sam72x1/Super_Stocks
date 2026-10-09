# 🧭🏁 RANKING_PROTOCOL — evaluation contract for the research-engine ranker (frozen before any ranking output)

> **Status:** committed and merged **before** any ranked list, capture number, or case rank exists. Task: «FAISAL BOT — METHOD
> RECONSTRUCTION & RANKING OPTIMIZATION — MASTER EXECUTION TASK» (2026-10-09). Research only: production V4, production candidate
> generation, Telegram, scheduled production workflows, alerts and the H6 contract are frozen and not touched.
> Label for every result produced under this contract: **EXPLORATORY** (§12 of the task) — the 41 documented units in the window
> already shaped Phases 3–6 and the engine design (two-touch wall removal FE-SCREEN-01, post-split frame FE-FRAME-01, stage map
> FE-STAGE-01). No held-out symbol is untouched by prior development.

## ⓪ Verified starting point (§1–§2 of the task)

- main = `7a5dc0f94` (PR #590 protocol merged `c28ce579e`, PR #591 result merged `7a5dc0f94`; Tests CI on main `37929100824` success).
- Every figure of the previous universe test reproduces from committed files (`out/universe_units.csv`, `out/universe_daily.csv`,
  `out/universe_summary.json`): 34 dates · 41 units / 38 evaluable (3 `NO_BARS`) · bot 3/38 = 7.9 % · engine screen 23/38 = 60.5 % ·
  engine READY/HOLD 4/38 = 10.5 % · bot PASS median 108 (range 65–129) · engine screen median 482.5 · valid median 3,396.5 ·
  LR bot 2.45 vs engine 4.58–6.06 · wall-vs-replay consistency 37/38.
- What that test proved and did **not** prove (from code): bot capture came from the frozen bot replayed on frozen bars
  (`replay_units.base_result`); daily bot counts came from stored `reject_stats` (valid − Σ walls) — **bot PASS identities were never
  stored**; engine stages were computed only for anchor-wall symbols, and SCREEN = PASS ∪ wall ignored the post-split frame route
  for symbols failing other gates. Nothing in the engine ranks: `stage_rank` is an ordinal of the stage list, not a ranking.
- Bot pipeline (code): `scan_market` → `analyze_ticker` truthy = PASS (this is what `reject_stats` counts) → M13 (soft) → M14 float
  (hard, not counted in `reject_stats`) → `classify_tier` → sort by `rank_key` = (in entry band first, −readiness, −h4_confirm,
  −score, −rr) → `select_top`. ⇒ the frozen bot **has a reconstructable ordering** (`rank_key` uses analyze_ticker fields only;
  `h4_confirm` is 0 at scan time).
- Engine pipeline (code): rows strictly < asof → FE-DATA-01 (≥ 40 bars) → SCREEN = frozen `analyze_ticker` with the two-touch anchor
  neutralised, on the FULL frame, else on the frame after the last reverse split (≥ 40 bars) → V4 `analyze_rows` → `TECH_TO_STAGE` →
  validity (offering = SEC 424B1/4/5 ≤ 90 days; float/short/groups/operator = UNKNOWN historically) → READY+blocker ⇒ HOLD,
  READY+operator press ⇒ TRIGGER (never historically: press is not observable in daily candles).

## ① Target behaviour

Which eligible symbols the method puts first on a given morning, measured against Faisal's **documented attention** (units of class
FOCUS / WATCH / READY / ENTRY in `fm_forensics/phase3/FAISAL_TIMELINE.csv`). The ranker orders candidates; it does **not** change
stages. Detection ≠ READY ≠ TRIGGER.

## ② Historical data and eligibility (identical rules for engine and bot)

- **Sessions computed:** every trading session T from 2026-07-09 to 2026-10-08 (calendar = dates on which ≥ 1,000 reconstructed
  symbols have a bar). Ranking sessions used for evaluation: 2026-08-07 … 2026-10-08 (5 sessions before the first case session);
  earlier sessions feed variant C's stage history only.
- **As-of rule:** a reading at T uses bars with date < T only (the bot's morning run before the open), and context dated ≤ T.
- **Bar window:** production `HISTORY_DAYS` = 800 calendar days before T, for both bot and engine (production availability rule).
  This differs from the previous test (bars from 2025-01-01); the difference is reported (wall-stage agreement with
  `out/universe_stages.csv`).
- **Universe U(T):** today's Nasdaq list by the production `get_universe()` ∪ every symbol in the 34 stored anchor-wall lists
  (label-free; the bot's own historical universe). **No Faisal-cohort symbol is added.** A symbol is eligible at T if it has ≥ 1 bar
  < T and its last bar < T is within 10 sessions of T. Bars: TradingView daily, regular session, split-adjusted, from 2024-05-01,
  fetched once on a GitHub runner and committed with SHA-256 (`data/rank/`).
- **Splits:** production `_fetch_splits_dq` (Yahoo ∪ Nasdaq calendar) per symbol; failure ⇒ `None` (post-split frame UNKNOWN).
- **SEC:** submissions per CIK (forms + filing dates); missing CIK/record ⇒ `None` (offering UNKNOWN).
- **Float / short availability / groups / operator press:** UNKNOWN historically — never used to rank, never imputed.
- **Engine pool P(T):** eligible symbols whose engine stage ∈ {TRIGGER, READY, WATCH, FOCUS, HOLD}.
- **Bot set B(T):** eligible symbols where the frozen `analyze_ticker` passes (`TOO_FEW_BARS` if fewer than production `MIN_BARS`).

### Reconstruction fidelity (descriptive, reported before any ranking number)
- F1 — reconstructed |B(T)| vs stored PASS count for the 41 stored run dates (run date d ↦ T = first session ≥ d).
- F2 — recall and Jaccard of the reconstructed anchor wall vs the 34 stored full wall lists.
- F3 — |U(T)| / stored `valid`.
- **Gate:** F3 median < 0.90, or any computed session missing, ⇒ verdict 3. F1/F2 do not block (the frozen *current* bot on
  identical data is the fair baseline; stored outputs came from older code); they label the operational baseline "reproduced" only
  if F1 median |relative error| ≤ 0.25 **and** F2 median recall ≥ 0.80, else "reconstructed (not reproduced from historical outputs)".

## ③ Ground truth

- **Units:** `FAISAL_TIMELINE.csv` rows with `IS_FAISAL=1`, class ∈ {FOCUS, WATCH, READY, ENTRY}, full `DATE` (YYYY-MM-DD) — the
  existing Phase 3/4 rule. Session(u) = first session ≥ `DATE` (existing rule). Window: session ∈ [2026-08-14, 2026-10-08] ⇒ the
  same 41 units as the previous test (asserted).
- **Episodes (primary unit of analysis):** existing rule `p5lib.EPISODE_GAP` = 30 sessions per ticker; the episode decision date
  T_e = session of its first unit. Repeated mentions inside an episode are not independent successes.
- **Timestamp quality:** `AMBIGUOUS_WEEKEND` = `DATE` is not a session (existing `date_ambiguous`); `AMBIGUOUS_ID` = the evidence id
  embeds a YYYYMMDD different from `DATE` (date read from content, not post time). Primary metrics use the dates as recorded; a
  sensitivity table excludes ambiguous episodes. No date is invented or moved.
- **Unmentioned symbols are UNKNOWN** — never false positives, never negatives; no precision/specificity is computed.
- **Evaluable:** ticker ∈ U(T_e). Otherwise UNEVALUABLE with its reason (not in reconstructed universe / stale bars) — counted and
  listed, excluded from denominators. Evaluability may differ from the previous test (bars source changed); differences are listed.

## ④ The three preregistered variants (code: `faisal_engine/ranker.py`, committed with this contract)

Stage priority (all variants; the engine's own progression `FOCUS → WATCH → READY → TRIGGER` from `NEXT_CONDITION`; HOLD last
because a dated blocker stops action): **TRIGGER 0 · READY 1 · WATCH 2 · FOCUS 3 · HOLD 4**. Stages are taken from the engine as is.

Label-free tie-break (all variants): `sha256("FE-RANK-1|<T>|<symbol>")` ascending — deterministic, unrelated to labels or prices.

- **A — stage only:** key = (stage priority, tie-break).
- **B — stage + evidence strength/validity:** key = (stage priority, −strength of the stage-defining rule
  `V4.STATE_RULE[tech_state]` from `FAISAL_RULE_LEDGER.json` [CONFIRMED 3 · SUPPORTED 2 · PROBABLE 1], contradicted flag [any fired
  rule with status CONTRADICTED ⇒ after], validity [offering verified absent before offering UNKNOWN], identity frame [FULL
  (FE-SCREEN-01 SUPPORTED) before POST_SPLIT (FE-FRAME-01 PROBABLE)], tie-break). No weights; lexicographic.
- **C — stage + evidence + temporal progression:** key = (stage priority, temporal class, sessions in current stage, then B's
  evidence keys, tie-break). Temporal class from the engine stages of the previous sessions (as-of only):
  PROGRESSED 0 (current stage entered within the last 5 sessions from a lower in-pool stage) · NEW 1 (entered the pool within the
  last 5 sessions directly at this stage) · PERSISTENT 2 (same stage ≥ 5 consecutive sessions = stale) · REGRESSED 3 (entered within
  5 sessions from a higher stage). Sessions in stage capped at 20. **Within a stage a stale signal never outranks a fresh one.**
  Hypothesis H-C (testable, reported): fresh/progressed candidates are more Faisal-like than persistent ones. Source of direction:
  the task's rule (§7) and the engine's progression chain; prior Phase 3/4 findings (Faisal attends at first touch) came from the
  same corpus — disclosed contamination.

Every ranked row carries an explanation (stage, tech state, stage rule + ledger status, frame, validity, temporal class, missing
data, tie-break) — `ranker.explain`.

## ⑤ Budgets

K = 108 (primary) · 25 · 50 (diagnostic). Shortlist L_v(T, K) = first K of P(T) under variant v (whole pool if smaller; size recorded).
Exports per session and variant: ranks 1–108 with explanation and features (`out/rank_top108_<v>.csv.gz`); the full pool ranking is
regenerable by command.

## ⑥ Metrics (exact and early never merged)

- **Exact-date capture** (episode, primary): ticker ∈ L_v(T_e, K).
- **Early capture** (episode, primary-early): ticker ∈ L_v(T, K) for some T among the 5 sessions strictly before T_e.
- Unit-level versions (secondary, each unit with its own session).
- Rank distribution of cases at T_e: 1–25 · 26–50 · 51–108 · > 108 in pool · not in pool · unevaluable.
- First inclusion: earliest T in [T_e − 20 sessions, T_e] with rank ≤ 108; rank and stage then; sessions before T_e.
- Daily burden: shortlist size, % of U(T), pool size, bot |B(T)|.
- Concentration lift = capture / (K / |U|) — reported as lift over random, not as precision.

## ⑦ Baselines

- **Operational:** the frozen current bot's set B(T) as reconstructed on the same data (its actual daily size, not 108), with the
  stored historical counts beside it. Capture = ticker ∈ B(T_e) (exact) / ∈ B(T) for one of the 5 prior sessions (early).
- **Standardized budget:** B(T) ordered by production `rank_key` (ties by symbol), top-K for K = 25/50/108 (if |B(T)| < K the bot
  lists all; size recorded).

## ⑧ Random reference

- R-U (primary, §11): uniform random K of U(T). Exact: P = K/|U(T_e)|; early: 1 − Π(1 − K/|U(T)|) over the 5 prior sessions.
  Distribution of the captured count by Monte Carlo, seed **20261009**, **100,000** draws, independent per session, cases on the
  same session drawn jointly without replacement.
- R-P (secondary): uniform random K of P(T) (only pool members can be drawn).

## ⑨ Uncertainty and validation

- Wilson 95 % per proportion; paired differences variant − baseline with a **cluster bootstrap over tickers** (B = 10,000, seed
  20261009), Bonferroni 98.33 % intervals (three variants).
- Leave-one-ticker-out and leave-one-decision-date-out influence on each difference.
- Forward fold (symbol + time grouping): DISCOVERY = episodes with T_e < 2026-09-15; VALIDATION = T_e ≥ 2026-09-15; a ticker with
  episodes on both sides is assigned to the fold of its first episode (asserted: no ticker in both).
- No learned weights. Nothing is fitted; the only choices are §④, frozen here.

## ⑩ Selection, iterations, stopping

- **Preferred variant (Iteration 1):** highest exact-date episode capture at K = 108; ties → early capture at 108 → capture at 50 →
  capture at 25 → A before B before C. Model-selection uncertainty disclosed (Bonferroni).
- **Iteration 2:** dominant failure diagnosed **from DISCOVERY-fold episodes only** (case table + rank/stage distributions).
- **Iterations 3 and 5:** at most **two** post-hoc corrections, each: tied to one diagnosed failure category, label-free (no symbol
  exception, no weight fitted to cases), with targeted tests, re-evaluated on the complete set with the same dates, universes,
  budgets and labels. Labelled POST-HOC; reported whatever the result. Stop after the second correction or earlier if no
  evidence-supported correction exists.
- This contract is not edited after any ranking output exists; defects found later are added as dated addenda that name the
  outputs to regenerate.

## ⑪ Verdict rule

- **3 INSUFFICIENT EVIDENCE TO DECIDE** — evaluable episodes < 15, or F3 gate fails, or a computed session is missing.
- **1 DEFENSIBLE IMPROVEMENT UNDER THE FIXED BUDGET** — the preferred preregistered variant (or a post-hoc correction, see below)
  satisfies all of: (A) shortlist ≤ 108 on every session; (B) exact-date episode capture at K = 108 above the operational baseline
  with the 98.33 % cluster-bootstrap lower bound of the difference > 0, and above the standardized top-108 baseline (point);
  (E) difference > 0 after removing any single ticker and any single decision date, and > 0 (point) in both forward folds;
  (F) the as-of / UNKNOWN locks pass; (G) a fresh regeneration reproduces the principal tables byte-identically. Early detection (C)
  and rank distribution (D) are reported; if early capture is not above the baseline the verdict text says "exact-date only".
  A post-hoc correction can carry verdict 1 only if its diagnosis used the DISCOVERY fold alone and its VALIDATION-fold difference
  is > 0; it stays labelled POST-HOC/EXPLORATORY.
- **2 IMPROVEMENT NOT DEMONSTRATED** — otherwise.
- (H) Every verdict is EXPLORATORY; none is independent validation.

## ⑫ Predictions (published whatever happens)

- P1 — reconstructed bot |B(T)| median within ±25 % of the stored median 108.
- P2 — reconstructed anchor-wall recall vs stored lists, median ≥ 0.80.
- P3 — no FOCUS-stage case is captured at K = 108 on its exact date under any variant (READY + WATCH exceed 108 on most days).
- P4 — the best variant's exact-date episode capture at K = 108 is ≤ 6.
- P5 — no preregistered variant meets verdict 1.
- P6 — on the median day, PERSISTENT is the largest temporal class of the pool.

## ⑬ Commands

```bash
python3 faisal_engine/rank_universe.py universe|bars|sec|splits|compute|assemble   # runner (TradingView/Yahoo/SEC)
python3 faisal_engine/ranker.py --date 2026-09-22 [--variant B] [--k 108]           # one session's shortlist + explanations
python3 faisal_engine/ranker.py --date 2026-09-22 --symbol DKI                       # one symbol's rank on a date
python3 faisal_engine/rank_eval.py                                                   # full evaluation → out/rank_* + RANKING_RESULT.md
```
