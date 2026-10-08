# STATE_MODEL_PHASE3_REASSESSMENT — Phase 3 (2026-10-08) · research only

Inputs: `FAISAL_TIMELINE.csv` (306 observations · 235 by Faisal · 101 tickers · 72 with bars), `TEMPORAL_PERSISTENCE_ANALYSIS.csv` (41 tickers with bars and a dated FOCUS/WATCH/READY/ENTRY row), `CORPUS_MATERIALITY_P3.csv` (11 eye re-reads), the Phase 2 state model (`../phase2/FAISAL_STATE_MODEL_REASSESSMENT.md`). Every answer below cites dated evidence read at or before the stated date; no state was inferred from later price.

## The five questions of §22

### 1. Does Focus precede Watch?
**Not as separate dated events — they usually coincide, and Watch can precede the structural low.**
- Dated corpus: 29 of 41 first observations are WATCH, 5 FOCUS, 5 READY, 2 ENTRY (`FIRST_DIVERGENCE_TEMPORAL_MATRIX.csv`). The 5 dated FOCUS rows are the owner-forwarded app list of 2026-09-13 (`X_20260918_23 «قائمتي»`: SXTC, MSGY, DKI, CUPR, YMT, CETX, ATPC, SVRE) — a list, i.e. Focus is the *container*, not a stage that is announced before Watch.
- Where the two are visible on one ticker: YMT WATCH 2026-09-04 (`X_20260905_10`) → on the list 2026-09-13; SXTC READY 09-10 → ENTRY 09-11 → list 09-14 → ENTRY again 09-24. So the list *collects* names already watched/entered; the first public act is WATCH.
- Watch can start before the low exists: ELPW «متبقي شمعتين فوليوم للهبوط · تحت المتابعه فقط» (`X_20260918_04`), and on the day the low forms: SMX `TG_1908` (same-day low 1.65, «تحت المراقبه الان»), KWM («1.50 قاع امس … مراقبه 3 جلسات»).
- Split-day Focus (IMG_0150 WORX; TG_1807/1811/1824/2200) is a *trigger to start watching* (the split is the founding event), not a stage after Watch.
**Verdict: CONFIRMED-MODIFIED.** Focus = the persistent list; Watch = the first dated act; the order "Focus → Watch" is a modelling convenience, not an observed sequence.

### 2. Does Watch persist?
**Directly supported by text, not provable from the dated corpus.**
- Text: explicit forward windows («مراقبه 3 جلسات», «نحتاج 5 جلسات», HTCR/LIMN/CETX staged checklists with ticks that span weeks — `IMG_8242`, `TG_50585`, `TG_50828`); SMX watched from 04-25 to 05-24 (`TG_1908` → `TG_2034`, 21 sessions); DXST 06-16 → 08-04 (34 sessions); NUWE 07-28 → 09-04 (29 sessions); CANF 07-20 → 08-01.
- Numbers: only 9 of 41 tickers have ≥2 dated days; max consecutive observations median 1 (IQR 1–1, max 3); span for multi-dated tickers median 11 sessions (max 34). 5 of the 9 multi-dated tickers show ≥2 consecutive observations (P4 first half: 56% ≥ 50% — holds on n = 9, which is too small to carry weight).
- H5 bites here: 58% of corpus units are undated; dated units cluster 2026-07 → 10 and Telegram forwards. Persistence cannot be *measured* from the corpus; it can only be *read* from his own forward-looking statements.
**Verdict: CONFIRMED (textual), UNMEASURED (numeric).**

### 3. Can Ready exist without a trigger?
**Yes — READY is declared before the trigger, and the trigger decides ENTRY, not READY.**
- 5 dated READY rows (PIII 05-16, SPRC 07-17, UPC 07-31, SXTC 09-10, GCTK 09-24): each is a checklist with the last box open («باقي سحب السيولة», «باقي تكه», two-branch «سحب أو ثبات» — `TG_57872` OMH «اعادة الاختبار شرط اساسي»).
- SPRC READY 07-17 → WATCH 07-20 (`READY→WATCH`): readiness is reversible without an entry.
- So Faisal's READY ≈ «all validity boxes ticked, waiting for the retest/sweep». The bot's READY NOW is a price-location flag on an already-admitted name (`entry_status`); it has no "waiting for trigger" state — it is either near support (READY) or not.
**Verdict: CONFIRMED (Phase 2 reading stands).**

### 4. Is the trigger a state transition or an event?
**An event that completes a transition, with two branches, and it is defined relative to the *watched* level, not to a candidate rule.**
- Branches: sweep below the low (7–13%, `PIVOT_SWEEP_PCT`, DKI `TG_57894` «الشراء بعد المسح لا قبله») **or** stability on the level with MA10 > MA20 (`TG_57872`); scientific-method sequence low → +17% → retest of the rise candle (`IMG_0488`); YMT: «لم يكسر القاع 5 جلسات · +20% · يرجع يختبر الدعم الثاني 1.84».
- The retest level can be a *higher* second support (YMT 1.84 vs 1.81) — the bot's 1.5% two-touch cluster does not recognise this as the same level.
- ENTRY rows (AMIX 08-24, CRE 2025-08, SXTC 09-11 / 09-24) sit 0–1 sessions after READY where both exist (SXTC 09-10 → 09-11).
**Verdict: CONFIRMED-MODIFIED.** Trigger = event; the transition it completes is WATCH/READY → ENTRY; the bot has no object on which such an event could fire (no watched level before candidacy).

### 5. Is Entry separate from Ready?
**Yes.** SXTC: READY 09-10 (`WA_20260918_31`), ENTRY 09-11 (`X_20260918_24`), still on the Focus list 09-14, second ENTRY 09-24 (`TG_58527`, second wave `TG_58417`). SPRC READY without ENTRY. EXIT rows (4) are separate acts («طلعت»). The bot's READY NOW ↔ ENTRY distinction does not exist (there is no bot ENTRY state at all — `FIRST_ENTRY_MISMATCH` = "bot has no entry state" on all 3 dated ENTRY tickers).
**Verdict: CONFIRMED.**

## What changes versus the Phase 2 model
| Element | Phase 2 | Phase 3 |
|---|---|---|
| FOCUS | «first screen → second screen → readiness» funnel | the **persistent list**; the first *dated act* is WATCH, and the list collects names already watched/entered |
| WATCH start | at/after the low | **at touch #1 or before the low** (ELPW, SMX, KWM, DKI) — the retest is awaited, not required to start watching |
| Persistence | assumed from text | **textual only**; numerically unmeasurable from the dated corpus (9/41 multi-dated) |
| READY | checklist complete minus trigger | unchanged; shown reversible (SPRC READY→WATCH) |
| Trigger | sweep-and-reclaim or hold-with-loading | unchanged; the retest level may be **higher** than the first low (second support) |
| ENTRY/EXIT | separate acts | unchanged |

## What this means for the bot's state model (description, no fix)
The bot has three persistent objects (watchlist, near_watch, pullback list) and all three sit **after** candidacy. Faisal's only persistent object (the list) sits **before** his trigger and admits names on one touch. The temporal order is therefore inverted at exactly one point: the bot evaluates the retest rule (two-touch anchor) as an admission test; Faisal evaluates it as the exit from Watch. Every other state (READY, ENTRY, EXIT) is downstream of that inversion. This is a description of the observed process, not a design.

## Remaining unknowns
- HUBC: Faisal state UNKNOWN on every day 2026-04-24 → 10-07 (no dated text).
- The owner's 10 current-chat screenshots: not recoverable in this session (`CORPUS_MATERIALITY_P3.csv`).
- Whether Faisal's Watch is ever *dropped* silently (no dated «خرج من المتابعة» rows exist; 4 EXIT rows are post-entry exits).
