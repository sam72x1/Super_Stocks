# B4_20261008 — CLASSIFICATION AUDIT (2026-10-08)

> أمرُ المالك: «STOP — AUDIT THE CLASSIFICATION OF B4 BEFORE ACCEPTING ANY EXCLUSION» — تدقيقٌ خصوميٌّ للصور الأربع وحدَها، قراءةٌ فقط
> (لا V4 · لا سجلّ · لا دمج · لا دفعة). كُتب بعد ختم الدفعة وكشف CASE_0002، **وقبل أيّ تصحيح**. **لا قرارَ لفيصل على NCT في هذا الملفّ**
> (العمى محفوظٌ لتصحيحٍ لاحق). النتيجةُ وحدَها: ثلاثةُ أصنافٍ صحيحة وواحدٌ خاطئ (TG_58526) · وPRIMARY يبقى 0.
> وما تقرّر بعده: `faisal_method_v41/FINAL_PROTOCOL_AMENDMENT_1_prereg.md` (أمرُ المالك «الاثنين»).

## Temporal model (six separate timestamps)

| | A Telegram | B Faisal post | C Phase A cutoff | D V4 dev-data cutoff | E V4's last candle for the case | F V4's prior exposure to the case |
|---|---|---|---|---|---|---|
| TG_58524 CDT | 2026-10-08T08:54:40Z | ≈01:23–01:25Z 10-08 (inferred) | 2026-10-08T01:29:04Z | bars ≤ 2026-10-02 · engine 2026-10-02T21:36:57Z | 2026-10-06 (actual run 37758334365) | none |
| TG_58525 CDT | 08:54:40Z | 01:35:00Z 10-08 (visible) | ″ | ″ | 2026-10-06 (via CASE_0002) | none |
| TG_58526 NCT | 08:54:40Z | 00:45–00:51Z 10-08 (inferred) | ″ | ″ | 2026-10-06 (if run) | computed case at the default as-of; no Faisal label; no outcome bars |
| TG_58527 SXTC | 08:54:40Z | ≈17:02Z 09-24 (inferred) | ″ | ″ | 2026-09-23 (if run) | same base with Faisal labels; outcome inside the dev bars |

The protocol contract (#563) was merged 2026-10-07T20:49:41Z — before every B4 decision except SXTC.

```
B4_CLASSIFICATION_AUDIT
=======================
TG_58524 = CORRECT — NEW_PROSPECTIVE → CASE_0002 · SECONDARY (LOW) · Phase B HISTORICAL
TG_58525 = CORRECT IN SUBSTANCE — DUPLICATE (SAME_DECISION) = informative continuation
           of the same decision point
TG_58526 = INCORRECT (TOO_STRICT) — CONTAMINATED → should be NEW_PROSPECTIVE · SECONDARY (LOW)
           · Phase B HISTORICAL
TG_58527 = CORRECT — CONTAMINATED (independently PRE_EXISTING as well)
```

```
TG_58524
TELEGRAM_TIME = 2026-10-08T08:54:40Z (msg 58524 · collected 08:58:17Z · run 37753340291)
FAISAL_POST_TIME = ≈2026-10-08T01:23–01:25Z (INFERRED: relative «12 د» on a 4:36 Riyadh capture;
                   Faisal's embedded chart clock 4:20 = 01:20Z) = ≈21:24 NY on 10-07
PHASE_A_CUTOFF_RELATION = BEFORE, by ≈4–6 min
V4_PRIOR_EXPOSURE = NONE — CDT is absent from the bar fixture, the 157 V4 cases, the EX inventory
                    and B48; its name appears only in the V3 pressure-radar pool lists
                    (a symbol name: no chart, no decision)
SPECIFIC_CASE_PRIOR_EXPOSURE = NO
SAME_INFORMATIONAL_STATE = NO (nothing prior to compare against)
CLASSIFICATION = NEW_PROSPECTIVE → CASE_0002 — correct
PRIMARY_ELIGIBLE = NO — LOW (no absolute timestamp on this post, contract §⑤)
                   and the decision predates the cutoff (E1)
EVIDENCE = INTAKE.json C1–C8 all empty · 4H chart: AH 0.8399, low 0.8041,
           bid 0.8042 / ask 0.8935
```

```
TG_58525
TELEGRAM_TIME = 2026-10-08T08:54:40Z (msg 58525)
FAISAL_POST_TIME = 2026-10-08T01:35:00Z (DIRECTLY OBSERVED «4:35 ص · 2026/10/8», read as Riyadh
                   per §⑤) = 21:35 NY on 10-07
PHASE_A_CUTOFF_RELATION = AFTER by ≈6 min — but it is a reply in a thread whose head (TG_58524)
                          was published ≈5 min before the cutoff
V4_PRIOR_EXPOSURE = NONE
SPECIFIC_CASE_PRIOR_EXPOSURE = NO
SAME_INFORMATIONAL_STATE = YES with TG_58524: same quotes (AH 0.8399 · bid 0.8042 · ask 0.8935),
    same low (0.8040 vs 0.8041), no new candle, 11–15 min apart, joined by the thread line.
    It adds the daily view and conditional levels 0.6426/0.5411 that expand the head post's 0.64.
CLASSIFICATION = DUPLICATE (SAME_DECISION:CASE_0002) — correct in substance:
    an informative continuation of the same decision point. Not an exact duplicate,
    not a later update, not a different decision point.
PRIMARY_ELIGIBLE = NO — the decision was already expressed before the cutoff; counting the reply
    on its own timestamp would be a rescue.
    Sensitivity: sent alone or before TG_58524, the current rule would have made it PRIMARY.
EVIDENCE = INTAKE.json (MEDIUM, reason SAME_DECISION) · both images · reveal/CASE_0002.json
```

```
TG_58526
TELEGRAM_TIME = 2026-10-08T08:54:40Z (msg 58526)
FAISAL_POST_TIME = 2026-10-08T00:45–00:51Z (INFERRED: attachment «07/10-20:45:28 EDT» lower bound,
                   capture 3:51 Riyadh upper bound) = 20:45–20:51 NY on 10-07
PHASE_A_CUTOFF_RELATION = BEFORE, by ≈38–44 min
V4_PRIOR_EXPOSURE = YES at ticker level: bars to 2026-10-02 · one computed case NCT_None
    (S4 educational channel · label UNKNOWN · golden false · from the undated TG_2179/TG_2180)
    · 3 undated Faisal level charts in the V3 corpus (TG_1906 · TG_2100 · TG_2101 · v4_use NOT_USED) at old
    pre-split prices ≈3–6 · and 3 undated educational-channel units (TG_2175 with NAMM · TG_2179 · TG_2180)
    (the chat version of this audit listed only TG_2179/TG_2180 — the verdict does not change)
SPECIFIC_CASE_PRIOR_EXPOSURE = NO for the decision, the label and the outcome.
    PARTIAL for the chart window: 118 of the 120 bars V4 would read as of 10-06.
    - NCT_None's 10-02 as-of is the evaluator's default for undated cases,
      not a decision moment (every undated row with bars got asof 2026-10-02)
    - no Faisal label, so nothing was scored and nothing could be tuned against;
      no V4 rule or document mentions NCT
    - the fixture ends 10-02, so it contains no post-decision bars
    - Faisal's own 09-30/10-02 NCT posts arrived in B48 after the freeze
      and are outside the dev set by contract
SAME_INFORMATIONAL_STATE = NO — V4 on 10-02: close 1.68, bottom 1.29 (09-30), 10% sweep 1.161.
    Faisal's chart on 10-07: low 1.140 (below the V4 bottom and below its sweep),
    close ≈1.52, at least two new sessions.
CLASSIFICATION = CONTAMINATED — INCORRECT. Correct = NEW_PROSPECTIVE: the frozen tool's C1–C8 are
    all empty, decision 10-07 ≥ 10-03, @kisar_ visible, ticker + decision statement + date present.
    Cause: I misapplied the eye-level SEEN_EXAMPLE flag. The contract's "an example V3/V4 saw"
    means this example; I applied it to "V4 computed this ticker", which is ticker-level exposure.
PRIMARY_ELIGIBLE = NO, even after correction — LOW (post header cropped, no absolute timestamp)
                   and before the cutoff
EVIDENCE = INTAKE.json (C1–C8 empty; reason SEEN_EXAMPLE) · v4_eval_results.json NCT_None ·
    cases_v4.json (S4, label UNKNOWN) · fixture (lows 10-01 1.3702, 10-02 1.41) · image
```

```
TG_58527
TELEGRAM_TIME = 2026-10-08T08:54:40Z (msg 58527)
FAISAL_POST_TIME = ≈2026-09-24T17:02Z (INFERRED: WhatsApp «8:02 م» with attachment
    «24/09-13:00:03 EDT») = ≈13:02 NY · author F_inferred (no name visible)
PHASE_A_CUTOFF_RELATION = BEFORE by 13+ days — also before WINDOW_START (10-03), D and the V4 freeze
V4_PRIOR_EXPOSURE = YES — bars to 10-02 · 3 V4 cases with Faisal labels
    (09-10 READY/WAIT · 09-20 WAIT from TG_57862) · 8 dev units inside the window (C5)
SPECIFIC_CASE_PRIOR_EXPOSURE = YES — the same base (bottom 1.78 on 09-10, test 3.00 on 09-11)
    was evaluated four days earlier with Faisal's label, and the post-decision outcome is in
    V4's development bars (high 3.27 on 10-01, low 1.941 on 10-02)
SAME_INFORMATIONAL_STATE = LARGELY YES — same setup at a later chart state
    (3 extra bars to 09-23); not a new decision point in the sense that matters
CLASSIFICATION = CONTAMINATED — correct on three independent grounds:
    C5/C8 · PRE_EXISTING · outcome exposure
PRIMARY_ELIGIBLE = NO
EVIDENCE = INTAKE.json (C5: 8 · C8: 3) · v4_eval_results.json · fixture 09-08…10-02
```

```
CUTOFF_RULE = AMBIGUOUS
  - E1 does not conflate Telegram arrival with the decision's existence: it requires both capture
    time and decision time to be after 01:29:04Z, and the Telegram time (08:54Z) rescued none of
    the three pre-cutoff decisions. On that question it is CORRECT.
  - The ambiguity is which timestamp a multi-post thread gets. The duplicate rule keeps the case on
    the earliest Telegram message number, not the earliest post time. In B4 the message order
    matched the posting order, so nothing changed. Sent in reverse, TG_58525 (MEDIUM, 01:35Z) would
    have made a decision published ≈5 min before the cutoff PRIMARY → TOO_LOOSE in that scenario.
  - Phase B's cutoff (01:29Z) being stricter than the protocol window (10-03) is deliberate and
    pre-registered, not an error.
CONTAMINATION_RULE = TOO_STRICT (as applied in B4)
  - The frozen C5/C8 tool was right on both: no hit for NCT, hits for SXTC.
  - The error was my eye-level extension applied to an undated computed case with no label and
    no outcome bars. That is ticker-level exposure, which the owner's rule says is not enough.
  - The real guard against outcome leakage, PRE_EXISTING (≥10-03, after the last dev bar 10-02),
    is correct.
  - The same stretch does not appear anywhere else: a grep across intake/ and batches/ finds it
    only on TG_58526.
PROTOCOL_CHANGE_REQUIRED = NO for the B4 result · YES, minimal and prospective only
                           (B5 onward, pre-registered before the batch)
IF_YES: thread anchor by earliest post · C8 "date" = dated V4 decision (undated = disclosure) ·
        SEEN_EXAMPLE limited to the same example · plus an append-only correction for TG_58526
        → FINAL_PROTOCOL_AMENDMENT_1_prereg.md
```
