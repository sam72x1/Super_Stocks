# 🧭🔀 STAGE_SEMANTICS_REPORT — Faisal's documented selection stages vs the engine's technical states (final report · 2026-10-09)

> **Verdict: 3 — INSUFFICIENT EVIDENCE TO ESTABLISH THE MAPPING.** Label **EXPLORATORY** (the historical cases already shaped
> the method). Research only. Production V4, H6, Telegram, scheduled workflows, alerts and candidate generation are unchanged.
> Contract: `STAGE_SEMANTICS_PROTOCOL.md`, merged (#595) **before** any engine stage was computed for a ledger event.
> Generated numbers: `STAGE_SEMANTICS_RESULT.md` and `out/stage_*`. Every figure below is copied from those files.

---

## A — VERIFIED STATE

| Item | Value |
|---|---|
| Starting main | `0b4e5af63` (#594 · Tests `37954788406` · Lint `37954788483` success) · `rank_eval.py --check` ⟶ exit 0 (the ranking artifacts reproduce byte for byte) |
| Contract PR | **#595** (ledger + contract + STG1–STG14) · isolated suite on `533a08c7b`: exit 0, 5335 passed · 0 failed · PR CI: Tests `37962641619` + `37962599916`, Lint `37962641667`, all success · merged as `6ea9406b8` |
| Engine readings | `python3 faisal_engine/stage_crosswalk.py engine` was run on `6ea9406b8`, after the merge: 744 (symbol, session) reads ⟶ `out/stage_engine_reads.csv` |
| Result PR | #596 (crosswalk + overlay + STX1–STX12 + this report). Its checks, merge and main CI are reported in the session's final reply and in `HANDOFF.md`, because a file cannot verify itself. |
| Production / H6 | The diff touches only `faisal_engine/`, `test_bot.py` (new locks before LEAK0) and memory files. `engine.py` and the ranking outputs are byte-identical to main (STG14). |

## B — EVIDENCE COUNTS (reproduced, not copied)

- **The Phase-3 decision timeline, re-counted:** **88 rows · 45 symbols** (`FAISAL_TIMELINE.csv` · FOCUS/WATCH/READY/ENTRY, all F/F_inferred). Reconciled against the verbatim sources (`out/stage_phase3_reconciliation.csv`):
  - **FOCUS 10/10** = list membership only (the «قائمتي» tab). No stage is shown.
  - **READY 0/6** carry an explicit «جاهز»: 4 have no readiness word, and 2 are a pressure/entry statement (GCTK · SXTC).
  - **WATCH 68:** 30 carry a wait/monitor word in the verbatim text; 29 do not (their WATCH came from V4's decision label); 9 have no ledger event.
  - **ENTRY 4:** 1 is operator money, not Faisal's entry (AMIX «3 مليون دولار دخلت»), 1 is a plan only (CRE), 1 has no entry word, and 1 has no ledger event.
- **Source ledger** (`out/stage_ledger_summary.json`):
  - Events: 631 total · 507 Faisal · 390 dated Faisal events, from **350 source units** on **122 symbols**.
  - Episodes: 207 (179 contain a Faisal event).
  - Eye reads in this task: 28 images · 38 statements.
- **Timestamp quality** (Faisal events):

  | Quality | Events |
  |---|---|
  | EXACT_PRINTED | 48 |
  | EXACT_DATE_PRINTED | 32 |
  | EXACT_DERIVED | 4 |
  | DERIVED_INFERRED | 7 |
  | RECORDED_UNVERIFIED (V4 date, no printed date found) | 138 |
  | BOUNDED | 191 |
  | AMBIGUOUS | 87 |

  - **Sufficiently reliable (strict: eye-read here, author visible, printed or derived timestamp):** 25 events.
- **Concept counts:**

  | Evidence category | Count |
  |---|---|
  | Direct list-state evidence | 16 events (13 visible rows in a list snapshot = 8 symbols on 2026-09-13; 1 stated «يضاف للمفضله» for BRTX; 2 general rules with no ticker) |
  | Direct readiness-state evidence | 13 «جاهز…»/«غير جاهز» events on dated Faisal statements, of which 10 are not recalled · H1-admissible episodes: **1 strict** (CDIO), **6 broad** |
  | Only a technical/chart state | 112 chart-only events; 1 technical-only statement |
  | UNKNOWN (no list/stage/action/trigger word) | 248 dated events |
  | Ambiguous timestamp | 87 Faisal events |

- **Units vs episodes vs evaluable cases:**
  - Of the 390 dated Faisal events, 209 are comparable: 25 strict and 184 broad.
  - 253 are excluded: 72 ambiguous timestamp, 181 low confidence.
  - Among the compared events, the engine was not determinable for 60: VARIES 32 · UNAVAILABLE 26 · WINDOW_TOO_WIDE 2.

## C — STAGE SEMANTICS (what each source term establishes)

| Term (verbatim) | What the source establishes | What it does NOT establish | Evidence |
|---|---|---|---|
| «قائمتي» (app tab) | Visible membership of 8 rows at 2026-09-13 1:41 (screenshot) / 1:44 م (post): SXTC · MSGY · DKI · CUPR · YMT · CETX · ATPC · SVRE | Any stage, readiness or status per row (rows show only bid/ask/price/change); membership at any other time; the contents of the other tabs | X_20260918_22/23, eye-read · author Faisal @kisar_ visible · tab «قائمتي» selected |
| «متابعة قائمه فرز اول فرز ثاني جاهزيه» | A **general** order: list → first sort → second sort → readiness. «تحقيق متوسطات شورت الخ تنقل السهم الى فرز 2» · «ضغط السهم بعد جميع ماذكر نقل الى جاهزيه» | Which symbol is in which sort; any date of a transition for any symbol | Same post (DIRECT, general rule) |
| «تحت الجاهزيه» · «جاهز 100%» | Tab titles exist in Faisal's app | Their contents (never shown in any committed image); their exact meaning | Searched: V4 pass (609 units), B48/B4 annotations, corpus-audit eye pass and catalogs — the only tab-title occurrences are X_22/X_23. The only other «تحت الجاهزيه» is a chart annotation on NEXR (TG_58400): «تحت الجاهزيه انتظار ضغط مضارب». Its author is not visible, so it is **not** a Faisal label. |
| «جاهز» (adjective in posts) | Faisal calls a named stock ready, usually **technically** («جاهز ع جميع المؤشرات والشموع», «جاهز فنيا»), and in the same breath **waits for the operator** («بانتظار فقط دخول المضارب», «ننتظر ضغط المضارب») | That the stock is ready to trade; membership of a «جاهز 100%» tab | CDIO 2026/1/28 (TG_2218/TG_2090) · AMIX/HCWB chat 1:29–1:50 ص (inferred 2026-08-24) · TG_1810 general «اسهم جاهزه فنيا اطرحها انتظر المضارب يشيلها فوق» |
| «غير جاهز» | Explicit technical NOT-ready, with a waiting condition | — | KWM (offering) · RAYA («انتظار الهبوط») · BTOG |
| Two senses of "ready" (INFERRED) | Pre-pressure technical readiness («جاهز … بانتظار … المضارب») vs the pipeline's post-pressure «جاهزيه» («ضغط السهم … نقل الى جاهزيه»). An earlier file (`fm_forensics/FAISAL_STATE_MACHINE.md`) mapped «جاهز 100%» to "technically ready, operator not yet"; the pipeline's word order points the other way. | Which of the two the «جاهز 100%» tab means (tab contents unseen) | Inference from verbatim order; no direct statement |
| «انتظار» · «مراقبه» · «تحت المجهر» · «تحت المتابعه» | Waiting for a named condition / continued attention at the post time | Continuous attention between posts (gaps are unknown) | 45 / 43 source units |
| «الضغط حصل» · «تم الضغط اليوم» · «دخولنا … مع شمعة الضغط» | Operator pressure observed and/or an entry with the pressure candle | That a daily candle state before it could predict it | AMIX 2026/8/24 11:10 م · SXTC 2026/9/11 «اضافة كميات مع الضغط» · GCTK after-hours 2026-09-23 |
| «يضاف للمفضله + تنبيهات للهبوط» | A stated add-to-list with drop alerts, together with «مراقبه مبكره» | — | BRTX (CASE_0001) |
| «كان جاهز» · «ذكرنا سابقا» · «مازال تحت المجهر» | A state carried forward from an earlier, undated time | The date of the earlier state | HCWB · ELPW · AMIX · CUPR · YMT · ZCMD |

## D — STATE CROSSWALK (EXPLORATORY · strict and broad shown separately · no merged score)

- **A. Explicit readiness label vs engine stage (H1).**
  - Strict: CDIO READY 2026-01-28 ⟶ engine **REJECTED** (FE-SCREEN-01/M3: the prior explosion is below the identity floor). Engine READY: 0 episodes ⟹ **H1 strict: INSUFFICIENT EVIDENCE**.
  - Broad:
    - Faisal READY: AMIX ⟶ REJECTED (M3) · HCWB ⟶ FOCUS · CDIO ⟶ REJECTED.
    - Faisal NOT_READY: RAYA ⟶ WATCH.
    - BTOG and KWM ⟶ VARIES across their windows.
    - Engine READY in 0 of 4 determinable episodes; no case of engine READY with Faisal NOT_READY ⟹ H1 broad: INSUFFICIENT EVIDENCE.
- **B. List membership vs candidate inclusion (H2).**
  - The 8 «قائمتي» members at as-of 2026-09-14:

    | Engine stage | Members |
    |---|---|
    | READY | CETX · MSGY |
    | WATCH | CUPR · SVRE |
    | FOCUS | DKI |
    | REJECTED | SXTC (M2_CEIL) · YMT (M3) |
    | UNAVAILABLE (no frozen bars) | ATPC |

  - 7 are determinable, spanning **4 engine classes**.
  - SXTC carries a dated Faisal entry with pressure (2026/9/11) three sessions before the snapshot ⟹ the list holds a stock already entered.
  - ⟹ **H2 SUPPORTED** (strict = broad). Non-members are not negatives (other tabs unseen) ⟹ no confusion matrix.
- **C. Entry/pressure vs TRIGGER.**
  - TRIGGER needs `operator_press`, which is UNKNOWN historically ⟹ every trigger is `NOT_REPRESENTABLE`.
  - Engine stage just before: REJECTED for AMIX (×2), SXTC (×2) and PIII · FOCUS for GCTK.
- **D. Continued watch vs persistence.**

  | Symbol | Episodes | In-process share |
  |---|---|---|
  | CDIO | 3 | 0.0 over 23 sessions |
  | ELPW | 3 | all REJECTED (M2_CEIL) · span 102 sessions, share not computed |
  | CUPR | 2 | 0.486 |
  | DXST | 2 | 0.571 |

  - Source continuity between observations is **not** claimed.
- **E. Waiting vs WATCH** (episodes with a wait/monitor word and no trigger):
  - Broad, 38 episodes: engine WATCH 4 · other in-process 6 · **out-of-process 19** · not determinable 9.
  - Strict, 2 episodes: out-of-process 1 · not determinable 1.
- **H3** (state carry-forward; contract §6 admits strict and broad timestamps):
  - AMIX OUT · ELPW OUT · HCWB IN · CUPR UNDETERMINED ⟹ **H3 SUPPORTED** on its admissible set.
  - Strict-only: 2 symbols ⟹ INSUFFICIENT.
- **Predictions (§10):** P1–P5 all came true (published as written).

## E — CASE-LEVEL RESULTS (dated source events only · engine stage at the matching as-of · `out/stage_case_timelines.csv`)

- **DKI**
  - 2026-09-14 (strict): visible in «قائمتي» ⟶ engine FOCUS.
  - 2026-09-20…30 (broad; cropped text attributed by V4): «بنتظر وين يضغطه المضارب … لابد يتم ضغطه» ⟶ engine WATCH. Not in C's top-108.
  - No readiness label exists for DKI.
- **SXTC**
  - 2026/9/11 (strict): «اضافة كميات مع الضغط» ⟶ engine REJECTED (M2_CEIL).
  - 09-10…18 (broad, WhatsApp): «تم الضغط اليوم ✅ دخول 1.80 > 1.90» ⟶ REJECTED.
  - 2026-09-14: in «قائمتي» ⟶ REJECTED.
  - The technical rejection, the available evidence (pressure + entry + list) and Faisal's behaviour are kept apart. The cause of the selection is not stated ⟹ **UNKNOWN**.
- **HUBC**
  - The only statement («1 فشل دخول وقف 7٪ واعطى دخول اخر ربح 40٪», listed above a 2026/4/24 post) is undated and refers to «الاسبوع الماضي» ⟹ AMBIGUOUS, not compared.
  - Phase-3 had dated it 2026-04-24 from the neighbouring ELPW post's date.
- **NUWE**
  - 09-04 (broad): levels only («اخر دعم … تحرر … الاهداف») ⟶ engine FOCUS.
  - 09-1x: «بالنسبه لي مادخل السهم بالمناطق الضبابيه الاولى» ⟶ VARIES.
  - IMG_0413/0414 are low confidence (device-linked).
- **AMIX**
  - Inferred 2026-08-24: «جاهز جدا … لو بس يضرب 4.70 ويرتد ممتاز نركب» and «عندنا سهمين حاهزه» ⟶ REJECTED (M3).
  - Printed 2026/8/24 11:10 م: «الضغط حصل 4.97» ⟶ as-of 08-25, REJECTED.
- **HCWB:** «عندنا سهمين حاهزه» ⟶ FOCUS · «السهم فنيا كان جاهز» (recalled, 08-24 pre-market) ⟶ FOCUS.
- **CDIO:** «جاهز ع جميع المؤشرات والشموع … بانتظار فقط دخول المضارب» ⟶ REJECTED (M3), and REJECTED in all 3 episodes through 03-02.
- **ELPW**
  - «ذكرنا سابقا بشهر 1 جاهز … مازال تحت المجهر» and «تحت المتابعه فقط» ⟶ REJECTED (M2_CEIL) in every observed episode.
  - The two September posts cannot be ordered by any source timestamp.
- **GCTK:** entry with the pressure candle in after-hours 2026-09-23 ⟶ engine FOCUS before it, with an offering block. Not in C's top-108.
- **NCT:** 2026/9/30 mention · 2026/10/2 conditional targets · 10-07 «1.24 دعم لابد يختبره» ⟶ REJECTED (M4_RANGE) at all three. No stage word.
- **BRTX / CDT:**
  - BRTX: «مراقبه مبكره · يضاف للمفضله» ⟶ FOCUS.
  - CDT: «هل يضغط 64 … تحت المجهر» ⟶ UNAVAILABLE (no frozen bars).

Transitions (`out/stage_transitions.csv`): INFERRED 41 · NO_CHANGE_OBSERVED 15 · UNKNOWN 12. **None is DIRECTLY OBSERVED or STRONGLY SUPPORTED**: no symbol has two strict observations with different explicit stage labels.

## F — FAILURE DIAGNOSIS (largest verified gap)

1. **Semantic mismatch in the target, not in the ranking:** the Phase-3 labels that the ranking work optimised against are mostly mappings, not source states.
   - FOCUS = tab membership (10/10).
   - READY rows with an explicit readiness word: 0/6.
   - WATCH rows from V4's label without a wait/monitor word: 29/68.
2. **Faisal's attention and readiness fall on symbols the engine rejects at candidate generation (the identity screen).**
   - Readiness: AMIX and CDIO ⟶ M3.
   - List members: SXTC ⟶ M2_CEIL · YMT ⟶ M3.
   - Waiting/monitoring: 19 of 29 determinable broad episodes are out-of-process.
   - Continued watch: ELPW ⟶ M2_CEIL in every episode.
   - This is the "wrong candidate-generation logic" row of §8 (5 events), together with "wrong temporal persistence" (22 events). It agrees with the Phase 2/3 findings and is **not** fixed here: the task forbids changing gates to fit labels.
3. **List membership is a separate state** (H2): one list spans REJECTED · FOCUS · WATCH · READY. Mapping it to FOCUS (Phase 3) is "wrong mapping from technical state to Faisal's attention state" (12 events).
4. **Triggers are unobservable historically** (6 events). The engine cannot represent the pressure candle at all.
- **§8 rule gaps (reported, not patched after the result):**
  - An ENTRY_PLAN on an engine-REJECTED symbol falls through to "No demonstrable failure" (e.g. AMIX s4).
  - "Wrong ranking" is assigned whenever an in-process symbol is absent from C's top-108, even when the source carries no selection statement (e.g. GCTK's validity rule).
  - The event-level diagnosis counts also include the 253 excluded events ("Missing source evidence" 272), so read them per case.

## G — IMPLEMENTATION (minimum useful, research-only)

| File | Purpose |
|---|---|
| `faisal_engine/stage_ledger.py` | Source event ledger (verbatim RAW_LABEL/RAW_ACTION · timestamp quality · concepts A/B/C/E · recalled flags · carry-forward · episodes · transitions · Phase-3 reconciliation) — no engine import |
| `faisal_engine/data/stage/eye_reads.json` | 28 images / 38 statements read by eye in this task (no private names) |
| `faisal_engine/STAGE_SEMANTICS_PROTOCOL.md` | Contract (#595, before any comparison) |
| `faisal_engine/stage_crosswalk.py` | Step 1 `engine`: `replay.read`-identical engine readings ⟶ `out/stage_engine_reads.csv`. Step 2: H1–H3, comparisons A–E, diagnosis, case timelines, generated `STAGE_SEMANTICS_RESULT.md`. Also the **research overlay**: `out/stage_overlay.csv` + `overlay_asof(symbol, day)`, with separate fields `SOURCE_LIST_STATE` · `SOURCE_SELECTION_STAGE` · `TECHNICAL_ENGINE_STAGE` · `OBSERVED_ACTION` · `TRIGGER_STATE` · `EVIDENCE_STATUS`. Source fields are never derived from the engine and never extended across gaps. |
| `test_bot.py` | STG1–STG14 (#595) + STX1–STX12 · mutations 14/14 + 12/12 killed (`out/stage_mutations_pr1.json`, `pr2.json`; STX12 was strengthened after its first mutation survived) |

The engine's stage definitions are **not** changed: no evidence justifies a change. The only change is the separate overlay, which stops future work from reading a list tab as FOCUS or the word «جاهز» as engine READY.

```bash
python3 faisal_engine/stage_ledger.py            # ledger ⟶ out/stage_events.csv · episodes · transitions · reconciliation · summary
python3 faisal_engine/stage_ledger.py --check    # byte-identical regeneration (exit 0)
python3 faisal_engine/stage_crosswalk.py engine  # engine readings (standalone, FAISAL_ONLY=1 like replay.py) ⟶ out/stage_engine_reads.csv
python3 faisal_engine/stage_crosswalk.py         # crosswalk + overlay + STAGE_SEMANTICS_RESULT.md
python3 faisal_engine/stage_crosswalk.py --check # byte-identical regeneration (exit 0)
python3 test_bot.py                              # STG1-STG14 · STX1-STX12 (before LEAK0)
```

## H — FINAL VERDICT

**3 — INSUFFICIENT EVIDENCE TO ESTABLISH THE MAPPING.**

- H1 strict has one admissible episode (CDIO), and the engine is never READY on any admissible Faisal readiness episode.
  - Strict: 0/1. Broad: 0/4 determinable.
  - So "engine READY ⊂ Faisal readiness" can be neither supported nor contradicted.
- What the evidence does establish:
  - **H2:** list membership is an independent state (one dated list spans four engine classes and includes an already-entered stock).
  - **H3:** carried-forward attention is not readable from candles (2 of 3 determinable symbols are out-of-process) — on the contract's admissible set, which includes broad timestamps; strict-only it is INSUFFICIENT.
  - **The Phase-3 READY/FOCUS labels are not the source's own states.**

## I — NEXT HIGHEST-VALUE ACTION

Use the **prospective channel that already exists** (the scheduled Telegram collector + the sealed-case protocol) to capture **one dated snapshot of each readiness tab** («تحت الجاهزيه» · «جاهز 100%») from Faisal's own app. It needs the same post format as X_23: selected tab, visible rows, a printed post time.

- Two such snapshots on different dates would let H1 be tested directly. Membership of «جاهز 100%» on date T would be compared with the engine stage at T, under the merged contract, with no new code.
- Every currently accessible artifact has been searched. No committed image shows those tabs' contents.
- Until then, the overlay keeps `SOURCE_SELECTION_STAGE = UNKNOWN` rather than mapping.
- No ranking, gate or engine change is justified by this result.

## J — INTEGRITY CHECK

1. **No fabricated source labels:** every RAW label is a substring of its own excerpt (STG12). Eye reads quote images verbatim; private names are omitted.
2. **No fabricated timestamps:**
   - Printed times are as seen; derived times state their basis.
   - The Riyadh-time assumption is declared.
   - V4 dates without a printed date are labelled RECORDED_UNVERIFIED; file order is never used (STG9).
3. **No look-ahead:** engine reads use bars strictly before the as-of session. As-of = the first session whose bars are all complete at the post time. The overlay never reads a later event (STX8).
4. **No unknowns treated as negatives:** excluded/UNAVAILABLE/VARIES never count (STX3); non-list members are not negatives (STX5).
5. **No post-hoc success criteria:** the contract (with the aggregation rules §3b) was merged before any engine reading of a ledger event. The §8 rule gaps are reported, not patched.
6. **No production or H6 modification:** STG14 pins `engine.py` and the ranking summary. The diff is research files plus locks plus memory.
7. **Tests and CI actually completed:** #595 suite exit 0 (5335/0) and PR CI success. #596 checks are verified in the final reply.
8. **Regenerable:** both `--check` commands exit 0 (STG11 · STX11).
9. **Contamination disclosed:** earlier replays of the 88 units had been seen (§0 of the contract).
10. **Not checked / unavailable:**
    - Faisal's Telegram channel history, X live and WhatsApp text.
    - 10 Phase-3 rows have no ledger event (8 are B48/B4 images not eye-read here).
    - 605 V4 units keep their V4 transcription (not re-read).
