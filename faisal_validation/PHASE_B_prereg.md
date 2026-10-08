# PHASE B — PROSPECTIVE VALIDATION · PRE-REGISTRATION (merged before any Phase B number)

> **العربيّة باختصار:** هذا عقدُ المرحلة ب من أمر المالك «FAISAL BOT — MASTER FORENSIC RECOVERY → FROZEN VALIDATION PROTOCOL»، يُدمَج
> **قبل أيّ رقمٍ من المرحلة ب**. السؤال: هل يُعيد V4 المجمَّد قراراتِ فيصل الحقيقيّة على حالاتٍ أماميّةٍ لم تُرَ أفضلَ من خطوطِ أساسٍ مسجَّلةٍ
> مسبقًا؟ الساعةُ الأماميّة تبدأ بعد حدّ أدلّة المرحلة أ **2026-10-08T01:29:04Z** (الختم `PHA-ea12cb86a3f39a5b`). كلُّ ما قبله تاريخيّ.
> لا تعديلَ على V4 ولا على حقبة البروتوكول ولا على الجامع ولا على الإنتاج. وكلُّ تحسينٍ محتمل ⟵ طابورُ V5 بلا تنفيذ.

## ⓪ Anchors (fixed before any number)
- **Phase A seal:** `faisal_recovery/HISTORICAL_PHASE_A_SEAL.json` · `PHA-ea12cb86a3f39a5b` · status `CLOSED` · evidence cutoff
  **`2026-10-08T01:29:04Z`** = `prospective_clock_starts_after`. **Hard gate:** the Phase B tool refuses to run (exit 9, `VALIDATION_BLOCKED`)
  unless that file is present, `phase_a.validate` reports no problem, its status is `CLOSED` and its id equals the id above.
- **Frozen model:** V4 commit `7c8826c25e745668d33facabb2efbc488e997fb7` · config hash `bd548f11…` · rule registry `5a2a8626…` (protocol epoch 1,
  `faisal_method_v41/final_protocol/EPOCH_FREEZE.json`). Phase B reads them; it never writes them.
- **Machinery reused unchanged:** the FINAL PROTOCOL chain (`faisal_method_v41/final_protocol.py`: intake-scan → seal → run frozen V4 →
  reveal → classify; ledger `faisal_method_v41/ledger.py`; checks I1-I12, LA1-LA6). Phase B adds a stricter eligibility layer, an
  append-only Phase B ledger, the B5-B21 reports and the Phase B status block. Where this contract and the protocol differ, **the stricter
  rule applies** and the difference is listed in ⑱.

## ① Question (B1)
"Does frozen V4 reproduce Faisal's real decisions on genuinely unseen prospective cases better than meaningful pre-registered baselines?"

## ② Eligibility (B2) — a case is PRIMARY only if all nine hold, checked in this order; the first failure is the exclusion reason
| # | Condition | Concrete check |
|---|---|---|
| E1 | Captured after the Phase A seal | protocol `CAPTURE_TIMESTAMP` **and** Faisal's decision timestamp (`ORIGINAL_POST_TIMESTAMP`, else the decision date from the post) are both later than the cutoff; either unknown ⟶ fail |
| E2 | Not in the historical corpus | image SHA256 ∉ every SHA256 sealed by Phase A (`HISTORICAL_IMAGE_INVENTORY.csv` + corpus manifest) |
| E3 | Not a duplicate | protocol intake class ≠ `DUPLICATE` and SHA256 not already used by an earlier Phase B case |
| E4 | Not an informative derivative | protocol intake class ≠ `DERIVATIVE` / `CONTAMINATED` |
| E5 | Not previously exposed to V4 | no V4 record for the case before its seal; not a legacy case (CASE_0001 is pre-seal ⟶ historical) |
| E6 | Faisal decision recoverable | a reveal record exists with label ∈ READY/WAIT/REJECT and evidence class `DIRECT` or `STRONG_INFERENCE`; a revealed `UNKNOWN` is counted in `UNKNOWN_CASES`, not in PRIMARY |
| E7 | Provenance adequate | protocol provenance confidence ∈ {HIGH, MEDIUM} (protocol PRIMARY rule) |
| E8 | Input sufficient | protocol data-quality wall passes (no `INSUFFICIENT_CONTEXT`, no LA5 invalidation) |
| E9 | No decision leakage | LA1-LA4 and LA6 pass, and the reveal sequence is later than the V4 record (LA3) |

**Never inflate N.** A case that fails stays excluded (the exclusion is an append-only ledger event and cannot be reversed by a later
event). Items captured or dated on/before the cutoff are **HISTORICAL** and are not Phase B candidates at all (they are reported as a count).

## ③ Blind-first (B3)
Exactly the protocol chain, with the Phase B ledger recording one event per step (`CAPTURED` · `SEALED_INPUT` · `V4_SEALED` · `REVEALED` ·
`CLASSIFIED` · `EXCLUDED`), each carrying the hashes of what it seals. Faisal's decision is read only after the `V4_SEALED` event exists.

## ④ Labels (B4)
READY · WAIT · REJECT · UNKNOWN — and nothing else. Insufficient evidence ⟶ UNKNOWN; UNKNOWN is never mapped to WAIT or to a match.
Structural fact recorded before any number: while the validity inputs (groups · offering · operator) have no source, V4's forward output is
{WAIT, UNKNOWN} by construction (FVO1) ⟶ V4 cannot score READY or REJECT recall above zero in this epoch.

## ⑤ Baselines (B5) — fixed now
- **ALWAYS_WAIT** — predicts WAIT for every case (protocol `BASELINE_A`).
- **EXISTING_BASELINE** — the baseline the frozen protocol already registered as `BASELINE_B` = **NONE** (no technical baseline was
  pre-registered; none is invented now). Reported as `NONE`; `V4_VS_BASELINE` therefore compares V4 with ALWAYS_WAIT.
- **HISTORICAL_PRIOR** (other pre-registered baseline) — a deterministic draw with the frequencies of Faisal's definite historical labels in
  the sealed A10 table (READY 13 · WAIT 93 · REJECT 4 of 110): `u = int(sha256(case_id)[:8], 16) / 2**32`; READY if `u < 13/110`, REJECT if
  `u ≥ 106/110`, else WAIT. A fixed function of the case id — no randomness, no tuning.

## ⑥ Metrics (B5 · B13) — every percentage with its numerator / denominator
Denominator = PRIMARY cases (E1-E9 pass, Faisal ∈ READY/WAIT/REJECT), minus `VALIDATION_BLOCKED_EXTERNAL_CONTEXT` cases (⑩), which are
reported separately and also in a sensitivity line that includes them.
- exact agreement · READY/WAIT/REJECT precision and recall (`UNDEFINED` at a zero denominator) · UNKNOWN rate (V4 UNKNOWN ÷ PRIMARY).
- `FALSE_READY` = V4 READY ∧ Faisal ≠ READY · `FALSE_WAIT` = V4 WAIT ∧ Faisal ≠ WAIT · `FALSE_REJECT` = V4 REJECT ∧ Faisal ≠ REJECT ·
  `FALSE_UNKNOWN` = V4 UNKNOWN ∧ Faisal ∈ READY/WAIT/REJECT — per-class false positives. The protocol's own `MATCH_CLASS` (asymmetric
  FALSE_WAIT/FALSE_REJECT and the MISMATCH_* classes) is kept per case in the results CSV, unchanged.
- Wilson 95% interval when the denominator is 10 or more; below 10 the value carries **LOW_POWER**.
- **Effect size / `V4_VS_BASELINE`:** the protocol's own `V4_BEATS_BASELINE`, computed by `final_protocol.metrics` on the same set —
  paired discordance against ALWAYS_WAIT, b = V4 right & baseline wrong, c = the reverse; in this order: n = 0 ⟶ `UNKNOWN` · b = 0 ⟶ `NO` ·
  b + c below 10 ⟶ `UNKNOWN` · else `YES` only when the Wilson lower bound of b ÷ (b + c) is above 0.5, otherwise `NO` (the protocol rule
  and order, unchanged — called, not re-implemented). No p-value is the sole basis of a judgement.

## ⑦ FALSE READY forensics (B6)
For every false READY one cause from: data · external-context · implementation · pattern · structure · location · validity · decision-order ·
entry · stop · target · methodology gap · unresolved — each with the quoted evidence that supports it. V4 is never patched.

## ⑧ Separate dimensions (B7) — never collapsed
PATTERN · STRUCTURE · ENTRY · STOP · TARGET · DECISION · FULL_FAISAL_AGREEMENT (decision and every stated component agree) ·
TRADING_EXPECTANCY. ENTRY/STOP/TARGET use the protocol component rule (±2%). PATTERN/STRUCTURE are compared only where Faisal states them;
otherwise `NOT_STATED`. TRADING_EXPECTANCY is **NOT_MEASURED in this epoch** (no outcome window was pre-registered; none is added later).

## ⑨ Sample (B9) · diversity (B10) · checkpoints (B14)
- Minimum **43** PRIMARY valid cases — a floor, not a stop: below 5 Faisal READY or 5 REJECT, or one setup above half of PRIMARY, the state
  stays `INSUFFICIENT_SAMPLE` even past 43.
- Diversity: pattern · timeframe · market regime · sector · volatility · liquidity · price range · catalyst · external-context class
  (protocol dimensions; unknown values are `UNKNOWN`, never guessed). `LOW_DIVERSITY` is a flag, never an exclusion.
- Checkpoints at N = 10 · 20 · 30 · 43: the status records an immutable checkpoint row (N, agreement, baselines, FALSE_*). Nothing changes at a
  checkpoint — no stopping rule, denominator, model, baseline or eligibility rule.

## ⑩ External context (B11)
Each case gets one class from Faisal's **own stated reasons** as recorded at reveal (the protocol's `external_codes`, mapped by
`final_protocol.ext_categories`) — never from the chart's silence:
- `DATA_INSUFFICIENT` — E8 failed, or Faisal's revealed label is UNKNOWN/MIXED.
- `EXTERNAL_REQUIRED` — Faisal states at least one non-chart fact (`external_codes` non-empty).
- `CHART_SUFFICIENT` — no external fact stated, and a chart reason is stated (plan, pattern or a component level).
- `EXTERNAL_UNKNOWN` — neither.
An `EXTERNAL_REQUIRED` case is `VALIDATION_BLOCKED_EXTERNAL_CONTEXT` when any stated category has no V4 input at decision time. V4's only
non-chart inputs are the four validity keys, so every category blocks except `short_borrow` when the case's `short_available` was
available to V4. Blocked cases are out of the main denominator, counted separately, and included in a sensitivity line. **VALIDATED and
PARTIALLY_VALIDATED require their criteria in both the main and the sensitivity analysis**, so the exclusion can neither rescue nor sink
V4 silently.

## ⑪ No post-hoc learning (B12) · production firewall (B17)
No threshold, rule, weight, feature, order, target, entry, stop or baseline change; no relabelling; no case removed after results. Every idea
⟶ `FAISAL_V5_CANDIDATES.md` (B18 fields). The Phase B tool imports no production module, sends nothing, schedules nothing and writes only
under `faisal_validation/`.

## ⑫ Append-only ledger (B15)
`faisal_validation/PROSPECTIVE_LEDGER.jsonl` — one JSON line per event with the B15 fields (`case_id` · `capture_timestamp` · `source` ·
`provenance` · `image_hash` · `perceptual_hash` · `ticker` · `timeframe` · `faisal_timestamp` · `v4_commit` · `v4_config_hash` · `v4_decision` ·
`v4_reason` · `faisal_decision` · `decision_match` · `baseline_decisions` · `classification` · `external_context_status` · `data_quality` ·
`contamination_status` · `notes`) plus `seq` · `event` · `utc` · `prev_sha256` · `sha256` (hash chain). The committed file must remain a
byte prefix of every later version: the tool opens it in append mode only (AST-locked) · `PHASE_B_STATUS.json` records its record count
and head hash and `check` fails when they differ · `audit-history` walks the git history and fails when any committed version is not a
byte prefix of the next (run before every Phase B PR; CI checkouts are shallow). A candidate's later events must extend its earlier ones —
a regression in the protocol state is a ledger problem (⟶ `VALIDATION_BLOCKED`), never a deletion.

## ⑬ Integrity tests (B16) — each with a mutation that makes it fail
V4 commit and config hash fixed for the epoch · historical images, duplicates and derivatives cannot enter · no decision leakage · Faisal's
decision unreadable before the V4 event · the denominator equals a recount from the ledger · an excluded case stays excluded · append-only
(prefix) · timestamps and provenance immutable (hash chain) · hashes deterministic.

## ⑭ Final states (B20)
In order: **VALIDATION_BLOCKED** (Phase A gate, Phase B ledger, epoch integrity, lookahead, provenance or a live-collector `FAIL`) ⟶
**INSUFFICIENT_SAMPLE** (PRIMARY below 43, Faisal READY below 5, or the ⑨ floor) ⟶ **VALIDATED** ⟶ **PARTIALLY_VALIDATED** ⟶ **NOT_VALIDATED**.
**Computation — the frozen protocol decides, Phase B only adds:** the state is `final_protocol.final_state` fed by `final_protocol.metrics`
and `final_protocol.unexplained_failure` on the protocol case records of the Phase B set, with the protocol's own integrity, lookahead,
provenance and live-collector inputs unchanged (its §⑱ conditions, not re-implemented). Phase B adds, in this order: the Phase A gate or a
Phase B ledger problem ⟶ VALIDATION_BLOCKED · the ⑨ floor ⟶ INSUFFICIENT_SAMPLE · and ⑩ — the state is computed on the main set and on the
sensitivity set and **the lower of the two is reported** (VALIDATED above PARTIALLY_VALIDATED above NOT_VALIDATED). A real improvement (B19)
is only: better prospective agreement · fewer false READY · superiority over the baselines · generalisation to unseen setups · better UNKNOWN
calibration · a defensible trading improvement.

## ⑮ Artifacts (B21)
`faisal_validation/`: `FAISAL_VALIDATION_STATUS.md` · `FAISAL_PROSPECTIVE_RESULTS.csv` · `FAISAL_PROSPECTIVE_ERRORS.md` ·
`FAISAL_V5_CANDIDATES.md` · `FAISAL_VALIDATION_TIMELINE.md` · `PROSPECTIVE_LEDGER.jsonl` · `PHASE_B_STATUS.json`. The historical development
audit is not overwritten; the development percentages are not recalculated (ENGINEERING 92.9% · METHODOLOGY 90.0% · VALIDATION 0.0% ·
PRODUCTION 0.0%).

## ⑯ Collector
The only live intake is the Telegram collector (`telegram_collect.yml`, `17 */4 * * *` + manual). `COLLECTOR_STATUS` joins the protocol's
live acceptance (`final_protocol.collector_status`: LIVE_PENDING · PASS · FAIL — only FAIL blocks, as in the protocol) with a recorded
observation of the Actions record (`faisal_validation/data/collector_observation.json`: runs by event, the last run, whether a **scheduled**
run has ever fired, pending updates — CI has no network, so the observation is recorded with its time). A collector that has stopped makes
no case eligible and is reported, not hidden.

## ⑰ Predictions (published before the first build; kept if wrong)
- **P1** first build: Phase A gate PASS · PRIMARY 0 · VALID 0 · EXCLUDED 0 · UNKNOWN 0 · `VALIDATION_STATE = INSUFFICIENT_SAMPLE` ·
  `V4_VS_BASELINE = UNKNOWN` · every pre-seal protocol candidate (48 + CASE_0001) reported as HISTORICAL.
- **P2** as long as FVO1 holds: V4_READY = 0 and V4_REJECT = 0 for every Phase B case.
- **P3** epoch 1 can at most reach `PARTIALLY_VALIDATED`; `VALIDATED` is structurally unreachable while P2 holds.

## ⑱ Stricter than the frozen protocol (listed, not hidden)
E1 (cutoff instead of the protocol window start 2026-10-03) · E2 (Phase A sealed hashes) · the external-context split (⑩) with both
analyses required · the coverage floor (⑨: REJECT 5 as well as READY 5, and no setup above half of PRIMARY) · per-class FALSE_* (⑥) · the
HISTORICAL_PRIOR baseline · the Phase B ledger. Nothing in the protocol is loosened.
