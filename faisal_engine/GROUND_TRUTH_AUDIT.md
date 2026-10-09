# HISTORICAL GROUND-TRUTH AUDIT — the 22 ranking episodes (2026-10-09)

> **EXPLORATORY.** This audit re-reads the sources behind an evaluation that was already built and scored on the same episodes. It is
> not a confirmatory, independent or out-of-sample validation, and no result here is confirmatory.
> Numbers come from `faisal_engine/out/gt_summary.json`, `gt_episodes.csv` and `gt_units.csv` (generator: `faisal_engine/gt_audit.py`,
> `--check` regenerates them byte for byte). Human-readable tables: `faisal_engine/GROUND_TRUTH_RESULT.md`.

## 1 · Verdict

**OUTCOME C — INSUFFICIENT HISTORICAL GROUND TRUTH.**

- The existing material supports **4 independent** decision units in which Faisal himself selected a stock, at a verified or strongly
  supported time, before a qualifying move: AMIX_E1, DCOY_E1, MI_E1 and MSGY_E1. Three of them (AMIX, DCOY, MSGY) are among the 22
  ranking-evaluable episodes. MI is not in the reconstructed ranking universe.
- One more unit could be added if a named original item turned up: the date of the SXTC WhatsApp message.
- 4 + 1 = 5, below the floor of 15 independent units in the existing contracts (RANKING_PROTOCOL verdict 3, H6_PREREG).
- **The outcome does not depend on the unknowns.** Suppose every censored episode, the ambiguous one, every undetermined episode that has
  a selection statement, and every episode with a named missing item resolved as an own pre-move success. The count would then be
  **13** (12 among the ranking-evaluable), still below 15.
- So outcome B (owner input) cannot reach the floor either. The available history is too thin to serve as ground truth for "selected
  before the move".

## 2 · Commit and files inspected

- **Base:** `main` at `f284a8f4d` (merge of PR #596).
- **Memory:** read `HANDOFF.md` and `CLAUDE.md`. Searched `DECISIONS_ARCHIVE.md` for: ranking, stage semantics, H6, Phase 3/4/5 and
  universe test. Ran `grep -ln CLOSED_RC *.py`. None of the closed axes is touched.
- **Contracts and results read:**
  - `faisal_engine/RANKING_PROTOCOL.md` (§③ ground truth, episodes, floor)
  - `RANKING_REPORT.md`
  - `RANKING_RESULT.md`
  - `STAGE_SEMANTICS_PROTOCOL.md`
  - `STAGE_SEMANTICS_REPORT.md`
  - `SOURCE_RECOVERY_AUDIT.md`
  - `fm_forensics/phase3/PHASE3_prereg.md` (move definition)
  - `fm_forensics/phase3/p3lib.py` (`outcomes`)
  - `fm_forensics/perf/H6_PREREG.md`
- **Ranking inputs:**
  - `faisal_engine/out/rank_cases.csv` (23 episodes)
  - `faisal_engine/out/rank_units.csv` (41 units)
  - `fm_forensics/phase3/FAISAL_TIMELINE.csv`
- **Frozen bars:**
  - `faisal_engine/data/rank/bars.json.gz` is the ranking universe. It is read up to and including 2026-10-08, because the 2026-10-09
    bar in that file is partial.
  - `faisal_engine/data/universe_bars.json.gz` is used for MI only.
- **Original artifacts:** 44 images in `faisal_images/` (SHA-256 in `gt_units.csv`), all opened and read by eye in this task. Their
  text is stored in two files:
  - 33 new reads in `faisal_engine/data/gt/gt_eye_reads.json`
  - 11 reads already recorded in `faisal_engine/data/stage/eye_reads.json`
- **Collection metadata:**
  - `telegram_collect_meta.jsonl`
  - git commit times of the image batches
  - `faisal_method_v41/final_protocol/intake/B4_20261008/` intake files
- **Contamination check (were the defensible statements quoted where the method was written?):**
  - `FAISAL_SOURCE_LEDGER.md`
  - `faisal_engine/FAISAL_RULE_LEDGER.csv`
  - `FAISAL_IMAGES_CATALOG.md`
  - and the other method documents listed in `gt_audit.METHOD_DOCS`

## 3 · Audit table (one row per episode; MOVE_50_20 = Phase 3 definition, frozen bars)

The A·B·C column gives the status of author · ticker identity · timestamp: V = VERIFIED, S = STRONGLY_SUPPORTED.

| Episode | Ranking T_e | Defensible statement (earliest) | A·B·C | As-of | Faisal's action (D) | Origin | Relation | Status |
|---|---|---|---|---|---|---|---|---|
| AMIX_E1 | 08-24 | `X_20260827_amix_hcwb_ready:s2` «جاهز جدا / لو بس يضرب 4.70 ويرتد ممتاز نركب» | S·V·S | 08-24 | TECH_READINESS + WAITING | OWN | **PRE_MOVE** (first +50% session 2; max +89.6%) | ELIGIBLE · reliable |
| ATPC_E1 | 09-14 | `X_20260918_23_watchlist:s1` (list tab) | V·V·V | 09-14 | LIST_MEMBERSHIP | OWN | CENSORED (19 sessions) | ELIGIBLE · list cluster |
| BRTX_E1 | 10-05 | `TG_58402:s1` | S·V·S | 10-05…10-07 | ATTENTION + LIST + WAITING | OWN | CENSORED (4) | ELIGIBLE |
| CETX_E1 | 09-14 | list tab | V·V·V | 09-14 | LIST_MEMBERSHIP | OWN | CENSORED (19) | ELIGIBLE · list cluster |
| CIIT_E1 | 09-25 ⟶ **08-24** | `X_20260827_ciit_targets:s2` (group target call) | S·V·S | 08-24 | ATTENTION | OWN | NO_QUALIFYING_MOVE (max +1.1%) | ELIGIBLE |
| CUPR_E1 | 09-14 | list tab | V·V·V | 09-14 | LIST_MEMBERSHIP | OWN | CENSORED (19) | ELIGIBLE · list cluster |
| DCOY_E1 | 09-22 ⟶ **09-21** | `TG_50578:s2` «Dcoy / باقي 80 الف شورت / ننتظر 2 ونقرر» | S·V·S | 09-21 | ATTENTION + WAITING | OWN | **PRE_MOVE** (session 2; max +173.7%) | ELIGIBLE · reliable |
| DKI_E1 | 09-14 | list tab | V·V·V | 09-14 | LIST_MEMBERSHIP | OWN | CENSORED (19) | ELIGIBLE · list cluster |
| EDBL_E1 | 09-22 | — (`TG_50579` chart analysis on request) | — | — | CHART_ANALYSIS_ONLY | — | UNDETERMINED | EXCLUDED · NO_SELECTION_STATEMENT |
| GCTK_E1 | 09-24 | `TG_57890:s1` «دخولنا بالملي مع شمعة الضغط اثناء التحليل» | V·V·S | 09-24 | ENTRY + PRESSURE | OWN | AFTER_MOVE_BEGAN (source-stated +130% after hours) | ELIGIBLE |
| IPDN_E1 | 09-23 | `TG_50833:s2` | V·V·V | 09-23 | ATTENTION + WAITING | PROMPTED | AFTER_MOVE_BEGAN | ELIGIBLE |
| LABT_E1 | 08-24 | `X_20260827_labt_supports_wait:s1` | V·V·V | 08-24 | ATTENTION + WAITING | OWN | NO_QUALIFYING_MOVE (max +27.7%) | ELIGIBLE |
| LIMN_E1 | 09-22 | `TG_50585:s1` | V·V·V | 09-22 | ATTENTION + WAITING | OWN | CENSORED (13) | ELIGIBLE |
| MI_E1 † | 09-28 | `TG_58387:s1` «سهم بطل انتظار الضغط 2.10» | S·V·V | 09-28 | ATTENTION + WAITING | OWN | **PRE_MOVE** (session 6; max +359.0%) | ELIGIBLE · reliable |
| MSGY_E1 | 09-14 ⟶ **09-02** | `X_20260905_12:s1` «$MSGY / يطبق ماذكر ادناه» | V·V·V | 09-02 | ATTENTION | OWN | **PRE_MOVE** (session 17; max +527.5%; prior move flag) | ELIGIBLE · reliable |
| NRSN_E1 | 09-28 | `TG_57867:s1` | V·V·V | 09-28 | ATTENTION + WAITING | OWN | CENSORED (9) | ELIGIBLE |
| NUWE_E1 | 09-04 | — (`WA_20260918_46_NUWE`: undated chat, no symbol visible) | — | — | CHART_ANALYSIS + WAITING | — | UNDETERMINED | EXCLUDED · TIMESTAMP_INFERRED |
| OMH_E1 | 09-28 | `TG_57870:s1` | V·V·S | 09-28 | ATTENTION + WAITING | OWN | CENSORED (9) | ELIGIBLE |
| PPBT_E1 | 09-04 ⟶ **09-03** | `X_20260905_02:s1` «مشروط الثبات الان فوق 1.70» | V·V·S | 09-03 | WAITING (+ retrospective) | OWN | AFTER_MOVE_BEGAN (comment on the previous day's pump) | ELIGIBLE |
| STKH_E1 | 09-04 | — (`TG_20260905_08/09`: sender not identifiable) | — | — | CHART_ANALYSIS + WAITING | — | UNDETERMINED | EXCLUDED · AUTHOR_UNKNOWN |
| SVRE_E1 | 09-14 | list tab | V·V·V | 09-14 | LIST_MEMBERSHIP | OWN | CENSORED (19) | ELIGIBLE · list cluster |
| SXTC_E1 | 09-10 | `WA_20260918_31_SXTC:s1` «تم الضغط اليوم✅ / دخول 1.80 > 1.90» | S·V·S | 09-10…09-11 | PRESSURE + ENTRY | OWN | AMBIGUOUS (09-10 PRE_MOVE · 09-11 NEAR_MOVE_START) | EXCLUDED · RELATION_AMBIGUOUS |
| YMT_E1 | 09-04 | `X_20260918_85_YMT:s1` | V·S·S | 09-04…09-08 | WAITING (+ «كان سهم متابعه», retrospective) | PROMPTED | NO_QUALIFYING_MOVE | ELIGIBLE |

† MI_E1 is not ranking-evaluable: the symbol is absent from the reconstructed universe. Its bars come from the universe-test file.

Further detail is in the generated files:

- Every unit, with its rank session, rank state, source as-of, label-word match, retrospective flag, duplicate link and image hash:
  `gt_units.csv`.
- Every statement, with its author, identity and timestamp basis written out: `data/gt/episode_evidence.json`.

## 4 · Counts

**Events, observations, episodes, decision units**

- **Ranking units (events):** 41.
  - Distinct observations: 33 (8 units duplicate another screenshot or chart of the same post).
  - 3 units are retrospective.
- **Episodes:** 23, of which 22 are ranking-evaluable. There are 23 symbols, one episode each.
- **Independent decision units:**
  - Among eligible episodes: 15 (14 among the 22). The five list members (ATPC, CETX, CUPR, DKI, SVRE) form one unit, because they come
    from one list snapshot.
  - **Reliable own pre-move: 4** (3 among the 22).
  - Resolvable by a named item: 1.
  - Favourable bound: 13 (12).

**Episode support**

- Fully source-supported (author, ticker and timestamp all VERIFIED or STRONGLY_SUPPORTED, on a non-retrospective selection statement):
  20 of 23 (19 of 22).
- Eligible: 19 (18 of 22).
- Excluded: 4.
- Inferred or ambiguous: 3 (NUWE, STKH, SXTC).
- Prompted by a follower: 2 (IPDN, YMT).

**Relation to the move** (MOVE_50_20, frozen bars, statement as-of)

| Relation | Episodes |
|---|---|
| PRE_MOVE | 4 |
| NEAR_MOVE_START | 0 |
| AFTER_MOVE_BEGAN | 3 |
| NO_QUALIFYING_MOVE | 3 |
| CENSORED (fewer than 20 sessions, no move yet) | 9 |
| AMBIGUOUS | 1 |
| UNDETERMINED | 3 |

**Agreement with the ranking labels**

- The ranking session lies inside the source as-of for 32 of 41 units. It does not for 6, and is unknown for 3.
- The ranking label's word (READY ⟶ readiness, WATCH ⟶ attention or waiting, ENTRY ⟶ entry) is present in the source for 22 of 41
  units.

## 5 · Exclusion reasons

- **EDBL_E1 — NO_SELECTION_STATEMENT.** The only source is a chart analysis given at a follower's request. It contains no selection word.
- **NUWE_E1 — TIMESTAMP_INFERRED.** The chat is undated and no symbol is visible on its charts. The date could be recovered, but the
  statement would still be levels only, with no selection word.
- **STKH_E1 — AUTHOR_UNKNOWN.** No sender can be identified in either chat image.
- **SXTC_E1 — RELATION_AMBIGUOUS.** The WhatsApp message at 1:00 م is undated, and the two possible days give different relations: 09-10
  is PRE_MOVE, 09-11 is NEAR_MOVE_START. This is the single resolvable unit.

## 6 · Corrections to prior interpretations (25 entries, all in `gt_summary.json`)

**Episode start dates (T_e)** — 4 episodes move (column `T_e_check`):

- CIIT: 09-25 ⟶ 08-24. A group target call exists; V4 had left it undated.
- MSGY: 09-14 ⟶ 09-02. A printed post from 8 sessions earlier, inside the 30-session episode gap.
- DCOY: 09-22 ⟶ 09-21. This follows from the episode-evidence entry below.
- PPBT: 09-04 ⟶ 09-03. This follows from the PPBT unit-date entry below.

These are 2 entries of their own (CIIT and MSGY); DCOY and PPBT are counted under their source entries.

**Unit and statement dates** — 5 entries:

- CIIT TG_57881/83: 09-25 was the chart's last-close stamp; the post is as-of 09-28.
- PPBT: 09-04 ⟶ 09-03, dated by the price identity of the attached pre-market quote plus «امس ع 2.40».
- STKH: 09-04 ⟶ 09-08. The quote is the 09-04 after-hours.
- NUWE: the chat is undated and shows no symbol.
- The stage ledger's as-of for AMIX `3m_inflow`: 08-24 ⟶ 08-25. The post was after the close.

**Labels and origin** — 9 entries:

- ATPC, CETX, CUPR, SVRE are list membership only. No stage is shown on the row; they were labelled FOCUS.
- EDBL is chart analysis only; it was labelled WATCH.
- GCTK is an entry executed after the move had begun; it was labelled READY.
- IPDN and YMT are prompted by a follower, not Faisal's own selection.
- SXTC: the READY unit shows pressure observed plus an entry zone (no readiness word), and the ENTRY unit is an undated retrospective
  outcome report.

**Unit counts** — 6 entries, because duplicates were counted as separate observations:

- DKI: 2 ⟶ 1
- BRTX: 2 ⟶ 1
- CIIT: 4 ⟶ 2
- LIMN: 2 ⟶ 1
- OMH: 4 ⟶ 2
- PPBT: 3 ⟶ 2

**Episode evidence and authorship** — 3 entries:

- AMIX: the ranking unit (`3m_inflow`) is a post-move retrospective. The defensible selection is the private group-chat readiness at
  01:29–01:50 ص, which Faisal published on X only after the move.
- DCOY: TG_50575 is an undated chat sent during the move; TG_50578 is the datable pre-move selection.
- STKH: the author is not Faisal as V4 assumed, but UNKNOWN.

## 7 · What is proven

**Confirmed (from the image text, the printed or in-image times, and the frozen bars):**

- The four reliable units are real, dated, own pre-move selections:
  - **AMIX**: «جاهز جدا … نركب» (as-of 08-24, +50% at session 2).
  - **DCOY**: «ننتظر 2 ونقرر» (as-of 09-21, session 2).
  - **MI**: «سهم بطل انتظار الضغط 2.10» (as-of 09-28, session 6).
  - **MSGY**: «$MSGY / يطبق ماذكر ادناه» (as-of 09-02, session 17).
- The episode start dates of 4 episodes, and 9 label or origin entries, in the ranking ground truth do not match their sources (section 6).
  The ranking scores were computed on those labels.
- All 41 ranking units trace to 44 images in the repository. Each image hash is recorded, no unit is unaccounted for, and no private name
  or follower handle is stored (locks GTA4 and GTA10).

**Strongly supported:**

- Authorship of the chat-bubble statements for AMIX, DCOY, MI and SXTC rests on the chat-wallpaper fingerprint: the same chat appears in
  posts Faisal published from his verified account.
- The AMIX and DCOY timestamps rest on price identity: «After Hours: X 0.00%» equals a specific close, using only prices up to the
  statement.

**Contamination:**

- The defensible statements of 9 episodes are quoted in the method documents that the rules were built from: AMIX, DCOY, GCTK, IPDN, LIMN,
  MSGY, NRSN, OMH and YMT.
- That includes 3 of the 4 reliable pre-move units (AMIX, DCOY, MSGY). Even those units are therefore not unseen by the method.

## 8 · Unknowns (named in `gt_summary.json` → `missing_items`)

- **When each list symbol entered «قائمتي»** (ATPC, CETX, CUPR, DKI, SVRE). The snapshot proves membership on 2026-09-13 only.
- **The send time of the DCOY chat in TG_50575.** The episode is already dated by TG_50578.
- **The date and symbol of the NUWE chat.** Even if recovered, the statement stays without a selection word.
- **The sender of the STKH chat.**
- **The date of the SXTC message.** It decides between PRE_MOVE (09-10) and NEAR_MOVE_START (09-11).
- **When YMT was first on Faisal's watch.**
- **The 9 censored episodes** stay censored under the frozen bars, because adding market data is outside this task.

None of these items, nor all of them together, lifts the count to 15 (favourable bound 13).

## 9 · One decision

**C — insufficient historical ground truth.** The 22-episode set cannot carry a claim that the engine finds Faisal's stocks before their
moves:

- only 3 of its episodes are reliable own pre-move units;
- 3 of the 4 reliable units overall are in the method documents;
- even the most favourable resolution of every unknown stays below the floor.

Earlier ranking results remain descriptive. Their ground-truth labels need the corrections in section 6 before any re-use. This audit
does not re-score them, which would be another variant.

## 10 · Single next action

**No new code.** The evidence that is missing — dated, first-time, own selection statements made before a move — can only come
prospectively.

The existing pipeline already captures it:

- `telegram_collect.yml` runs every 4 hours.
- Each post is sealed before V4 runs, under the FINAL_PROTOCOL epoch-1 seal (`final_protocol.py` intake-scan ⟶ seal ⟶ run ⟶ reveal).
- `faisal_validation/phase_b.py` keeps the append-only ledger.
- The Phase 6 collector records float, short volume and shares available for Faisal's names.

**The single action is to keep that loop fed:**

- Forward each new Faisal post when it appears.
- Keep the printed post time visible, not a cropped header.
- Do not pause the collector.

The 15-unit floor then accrues from independent future observations instead of being reconstructed from history.
