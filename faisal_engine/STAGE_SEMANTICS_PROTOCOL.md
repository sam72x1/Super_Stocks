# STAGE_SEMANTICS_PROTOCOL — evaluation contract (committed BEFORE any source-vs-engine comparison)

> Task: «FAISAL BOT — STAGE SEMANTICS RECONSTRUCTION» (2026-10-09). Research only. Production, V4, H6, Telegram,
> scheduled workflows and candidate generation are NOT touched. Every result produced under this contract is
> **EXPLORATORY** (the historical cases already shaped the method).

## §0 What is fixed by this contract, and what was already seen

- **Source ledger (built and viewed before this contract):** `faisal_engine/stage_ledger.py` regenerates, byte for byte
  (`--check`), these pinned files — the comparison runs on exactly them:
  - `faisal_engine/out/stage_events.csv` — SHA-256 `ac74a23e400c759411f941c092883da2ac6114458963b65fc777ffea03d14cda`
  - `faisal_engine/out/stage_episodes.csv` — SHA-256 `78662cc3b8048c3bed501644ee537a1ecf3dc571f4865d2e29b5a724d913cbd7`
  - `faisal_engine/data/stage/eye_reads.json` — SHA-256 `f4ce4e04f3d88dc286c70810a8aadfa7aea3b07dfc4dc46cbb92dd217835ba9d`
  Any later change to them requires a dated addendum stating why, before the changed numbers are shown.
- **Already known (source side only):** admissible H1 episodes — strict 1 (CDIO), broad 6 (AMIX · BTOG · CDIO · HCWB · KWM ·
  RAYA); H2 list snapshot — 8 symbols (2026-09-13 «قائمتي») + 1 stated add (BRTX); H3 state carry-forward — 6 symbols
  (AMIX · CUPR · ELPW · HCWB · YMT · ZCMD); comparison C events — AMIX · GCTK · LABT · PIII · SXTC; comparison E — 46
  episodes (2 strict).
- **Contamination disclosure:** earlier tasks computed and showed engine replays for the 88 Phase-3 units
  (`out/replay_units.csv`, `RANKING_REPORT.md`, Phase 2/3/6 traces of DKI/SXTC/HUBC). Those include some of the symbols
  below. **No engine stage has been computed for any ledger event in this task before this contract.**

## §1 Engine reading (fixed)

- `faisal_engine/replay.read(sym, day)` on the frozen bars `fm_forensics/data/bars_2026-10-08.json.gz` (bars strictly
  before `day`; SEC context dated ≤ `day`). Stages: INSUFFICIENT_DATA · REJECTED · FOCUS · WATCH · READY · TRIGGER · HOLD.
  **No change to engine definitions.**
- **In-process** = FOCUS · WATCH · READY · TRIGGER · HOLD (= engine candidate inclusion). **Out-of-process** = REJECTED ·
  INSUFFICIENT_DATA.
- An event's as-of window `[asof_lo, asof_hi]` comes from the ledger. The engine is read at **every session in the
  window**. All equal ⟹ that stage. Otherwise ⟹ `VARIES` (the comparison is AMBIGUOUS, reported, never counted).
  A window longer than **10 sessions** ⟹ `WINDOW_TOO_WIDE` (not evaluated).
- Symbol absent from the frozen bars, or no bar before `asof_lo` ⟹ `UNAVAILABLE` (not a negative, not an error).
- TRIGGER needs `operator_press`, which is UNKNOWN historically ⟹ TRIGGER is **not observable** in any historical replay.
- Context columns (descriptive only): engine `first_failed`, V4 `tech_state`, blocks, missing data. For sessions
  2026-07-09…2026-10-08, the frozen bot decision and rank from `data/rank/rows.csv.gz` / `out/rank_top108_C.csv.gz`
  may be shown for §9 diagnosis. **No new ranking variant, no threshold change, no new universe fetch.**

## §2 Subsets (fixed)

| | STRICT | BROAD (exploratory) |
|---|---|---|
| author | `is_faisal=1` | `is_faisal=1` |
| confidence | `HIGH` (read by eye in this task · author visible · speaker Faisal) | `HIGH` or `MEDIUM` |
| timestamp | `EXACT_PRINTED` · `EXACT_DATE_PRINTED` · `EXACT_DERIVED` | strict ∪ `DERIVED_INFERRED` · `RECORDED_UNVERIFIED` · `BOUNDED` |
| identity | named in the image, or `identity_basis` STRONGLY_SUPPORTED | any resolved ticker |
| engine | not VARIES / WINDOW_TOO_WIDE / UNAVAILABLE | same |

`AMBIGUOUS` timestamps and `LOW` confidence are never compared. The broad result can never upgrade a verdict.

## §3 Episodes and duplicates (fixed)

- The counting unit is the **episode** (`stage_episodes.csv`): one symbol, overlapping as-of windows. Events are never
  deleted; `duplicate_of` events never add to a count.
- An episode's source label for a comparison = the admissible labels of its events. An episode with both READY and
  NOT_READY (both not recalled) ⟹ `CONTRADICTED_SOURCE` (reported, not counted).
- A **recalled** label (`readiness_recalled=1`, `RECALLED_*` actions) describes an earlier, undated time. It is **never**
  assigned to the post's as-of session.

## §3b Aggregation (fixed)

- **Episode engine stage** (H1, E): the engine stage of the episode's admissible events if they all agree; otherwise
  `VARIES` (not counted).
- **Symbol engine status** (H3): `OUT` if every determinable admissible carry-forward event of the symbol is
  out-of-process, `IN` if every one is in-process, otherwise `MIXED` (reported, counts as neither).
- **H2 (c) entry window:** a Faisal `E_trigger` event of the member with a non-AMBIGUOUS timestamp whose `asof_lo` is at
  most 10 sessions before the snapshot's as-of and whose `asof_hi` is not after it.
- **Comparison D window:** in-process share is computed only when the first `asof_lo` → last `asof_hi` span is at most
  60 sessions; otherwise only the per-episode stages are shown.

## §4 H1 — technical-state equivalence (engine READY ⊂ Faisal's explicit readiness)

- **Admissible source labels:** `B_stage` = READY or NOT_READY (raw «جاهز…» / «غير جاهز…») on a named symbol, by Faisal,
  not recalled. **Not admissible:** tab titles («تحت الجاهزيه» · «جاهز 100%») without visible rows; the general noun
  «جاهزيه» in a rule; APP panels; V4 `dec`; Phase-3 `FAISAL_STATE`.
- **Minimum evidence:** at least **3 STRICT episodes with engine READY** (any admissible Faisal label).
- **Supports:** minimum met AND every STRICT engine-READY episode carries Faisal READY.
- **Contradicts:** at least **2** STRICT episodes with engine READY ∧ Faisal NOT_READY, or (when engine-READY episodes are
  2 or more) at least half of them.
- **Otherwise:** `INSUFFICIENT EVIDENCE`.
- Descriptive only (no verdict): the engine-stage distribution of Faisal READY episodes and of Faisal NOT_READY episodes.

## §5 H2 — list membership is an independent state

- **Admissible:** `A_list = LIST_SNAPSHOT_VISIBLE` (a visible row in a tab of Faisal's own app inside a Faisal-authored
  post); `ADD_TO_LIST_STATED` on a named symbol is reported but does not count toward the minimum. A row not shown is
  **UNKNOWN**, never "not a member". A tab title never establishes membership.
- **Minimum evidence:** at least **5 list-member symbols** with a determinable engine stage at the snapshot's as-of
  session, and (a) a dated Faisal statement about the list's role (the 2026-09-13 pipeline post).
- **Supports:** (a) AND either (b) the determinable members span **2 or more engine classes** among {out-of-process,
  FOCUS, WATCH, READY, TRIGGER/HOLD}, or (c) a member has a Faisal entry/pressure event (`E_trigger`) with an as-of within
  the 10 sessions before the snapshot.
- **Contradicts:** all determinable members (at least 5) are in **one** in-process class, or a dated Faisal statement
  equates the list with a single stage.
- **Otherwise:** `INSUFFICIENT EVIDENCE`.
- Comparison B reports member-by-member inclusion. **No confusion matrix**: non-members are unknown (other tabs unseen).

## §6 H3 — stage progression requires source history

- **Admissible:** Faisal events (STRICT or BROAD timestamp) whose verbatim text carries a **state carry-forward** marker
  (`carry_forward_state`: «ذكرنا متابعة/سابقا» · «كان سهم متابعه» · «كان جاهز» · «مازال/لازال تحت» · «تحليل سابق» ·
  «ذاكره قبل» · «تم التحليل قبل» · «نعطيك سهم جاهز»). The generic «سابقا»/«كان» alone does not count.
- **Minimum evidence:** at least **3 symbols** with an admissible carry-forward event and a determinable engine stage.
- **Supports:** minimum met AND for **2 or more** of those symbols the engine at the event's as-of is out-of-process,
  i.e. the attention/readiness that the source carries forward is not readable from the daily candles at that time.
- **Contradicts:** minimum met AND for **every** such symbol the engine is in-process at the event's as-of.
- **Otherwise:** `INSUFFICIENT EVIDENCE`.
- Timelines: transitions are labelled by the ledger (`stage_transitions.csv`). A gap is never a transition, and no
  change date is invented.

## §7 Comparisons A–E (separate · no merged score · unknown ≠ error)

- **A** explicit stage label vs engine stage = the H1 table (+ descriptive rows).
- **B** list membership vs engine candidate inclusion = the H2 table.
- **C** `E_trigger` (PRESS_OBSERVED · OPERATOR_MONEY_OBSERVED · ENTRY_EXECUTED · ENTRY_STATED with PRESS_OBSERVED) vs
  engine: TRIGGER is unobservable (§1), so the comparison reports the engine stage at the as-of **before** the trigger
  and labels it `NOT_REPRESENTABLE` for the trigger itself.
- **D** continued watch vs persistence: symbols with 2 or more Faisal episodes carrying WAIT/MONITOR or a carry-forward
  marker ⟹ engine stage at each observed episode, plus the share of in-process sessions between the first `asof_lo`
  and the last `asof_hi` (at most 60 sessions). Source continuity between observations is **not** claimed.
- **E** waiting vs WATCH: episodes with WAIT · MONITOR · WAIT_FOR_PRESS (and no `E_trigger`) ⟹ engine stage distribution;
  the categories are "engine WATCH", "engine other in-process" and "engine out-of-process". No error rate.

## §8 Diagnosis rules (§9 of the task · fixed)

| condition (per case) | failure type |
|---|---|
| timestamp AMBIGUOUS / window too wide / VARIES | Ambiguous source timestamp |
| no admissible Faisal label on the symbol | Missing source evidence |
| source E_trigger (pressure/entry) | Unobservable decision or trigger |
| source READY (not recalled) ∧ engine out-of-process | Wrong candidate-generation logic (gate = engine `first_failed`) |
| source READY ∧ engine in-process but not READY | Wrong technical pattern classification |
| source list membership treated as a stage (Phase-3 FOCUS) | Wrong mapping from technical state to Faisal's attention state |
| source carry-forward / continued watch ∧ engine out-of-process | Wrong temporal persistence representation |
| engine in-process and same-stage peers outrank it (rank rows) | Wrong ranking among candidates with comparable states |
| source and engine agree | No demonstrable failure |

The cause of a selection that is not stated in the source is **UNKNOWN**; later price performance is never used.

## §9 Final verdict mapping (fixed)

1. **STAGE MAPPING SUPPORTED BY DIRECT EVIDENCE** — H1 SUPPORTED (strict) and neither H2 nor H3 CONTRADICTED.
2. **STAGE MAPPING PARTIALLY SUPPORTED** — H1 SUPPORTED (strict) but H2 or H3 CONTRADICTED.
3. **INSUFFICIENT EVIDENCE TO ESTABLISH THE MAPPING** — H1 INSUFFICIENT EVIDENCE (strict), whatever H2/H3 show; H2/H3
   then decide only whether a separate source-state representation is justified (§10 of the task).
4. **CURRENT ENGINE STATES CONTRADICT DOCUMENTED FAISAL STATES** — H1 CONTRADICTED (strict).

## §10 Predictions (published whatever the outcome)

- **P1** H1 STRICT ⟹ INSUFFICIENT EVIDENCE (only one strict admissible episode exists) ⟹ verdict 3.
- **P2** In the broad H1 set, at least half of the Faisal READY episodes have an out-of-process engine stage.
- **P3** The 8 «قائمتي» members at as-of 2026-09-14 span 2 or more engine classes (H2 SUPPORTED).
- **P4** Fewer than half of comparison-C episodes are engine READY at their as-of.
- **P5** In comparison E, engine WATCH is under half of the broad episodes.

## §11 What this contract does not do

No new hypothesis after results; no proxy labels; no weights trained on these cases; no change to the engine, V4, H6,
production, Telegram or workflows; no ranking variant; no threshold tuning; no full-universe fetch.
