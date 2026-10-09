# PHASE 6 — VALIDATION REPORT

## 1. Production decisions unchanged (before vs after, same fixtures)
| Check | Result |
|---|---|
| `Super_stock.py` vs `origin/main` (`e85f12af`) | byte-identical (`git diff` empty; also `data_quality.py`, `tv_data.py`, `pullback_live.py`) |
| Roots AST fingerprint (12 functions: `rank_key select_top classify_tier analyze_ticker apply_short_gate apply_float_gate scan_market backtest_symbol scan_ignition scan_split_hunter entry_status build_interpretation`) | no difference vs `origin/main` (e.g. `analyze_ticker d36af8284ef9`, `entry_status a9f12435b523`) |
| `analyze_ticker` on the frozen fixtures (6 anchor rows) before/after | identical: same reasons as Phase 3's `bot_states.csv.gz` and `logo_rows.csv` (lock `P6T2`) |
| `LOGIC_VERSION` | unchanged (`…+pivotstoplow`) |
| Production state files touched by Phase 6 code | none (`P6C11`: no `send_telegram`/`git_save`/`save_*` calls; `trace.py` never assigns `CONFIG`; `Super_stock.py` does not reference `phase6`) |
| V4 / final protocol / Telegram | untouched (no file under `faisal_method_v4*` or `faisal_validation` changed) |

## 2. Tests added (all before the `LEAK0` separator; each a lock that can fail)
`P6C1` idempotence · `P6C2` timestamp/tz integrity (naive refused) · `P6C3` duplicate events/posts · `P6C4` missing provider → UNKNOWN never zero · `P6C5` invalid/stale observations · `P6C6` historical/current separation + schema refusals · `P6C7` float ≠ SI ≠ borrow · `P6C8` ticker/identity change · `P6C9` reverse-split frames · `P6C10` audit-log tamper evidence + raw refs · `P6C11` no production change (static) · `P6C12` runner workflow · `P6T1` deterministic, cwd-independent trace (subprocess from a temp cwd, byte-identical to committed) · `P6T2` reproducible rejection attribution (6/6 vs Phase 3) · `P6T3` document table = CSV · `P6T4` no writes outside its output dir, suite config untouched, production thresholds applied.

Mutation round (each mutation applied to a copy, suite lock expected to fail, file restored): see §5.

## 3. Isolated suite / CI
- Isolated suite (copy of the working tree, `python3 test_bot.py`): __SUITE__
- PR CI: tests __CI_T__ · lint __CI_L__ · PR #__PR__ merged `__SHA__`
- CI on `main` after merge: __MAIN__
- First live collector run on Actions: __RUN__

## 4. Collector offline validation (injected providers, lock fixtures)
Run with two tickers: 22 rows (OK 11 · UNKNOWN 10 · NOT_ATTEMPTED 1; categories 1:6 · 2:5 · 4:11); re-run same day with and
without resume adds 0 rows; chain verifies from disk; audit gaps 0. Provider outage fixture: every row FAILED/UNKNOWN/NOT_ATTEMPTED
with value UNKNOWN; no zero. No live provider was reachable from this session (proxy 403) — live behaviour is validated only by the
first Actions run (§3).

## 5. Mutation evidence
| # | Mutation (applied to a copy, then restored) | Expected lock | Outcome |
|---|---|---|---|
| 1 | `Ledger.append` accepts duplicate keys | P6C1 | caught (P6C1, P6C10) |
| 2 | `prev_sha256` always genesis (chain not linked) | P6C10 | caught (P6C1, P6C10 — after strengthening P6C10 to assert the links on the real ledger) |
| 3 | naive datetime accepted as UTC | P6C2 | caught |
| 4 | missing Yahoo float written as `0.0 OK` | P6C4 | caught (P6C4 after adding the SXTC fixture, P6C5, P6C7) |
| 5 | short interest without provider as-of labelled CAT 2 | P6C6 | caught (P6C5, P6C6) |
| 6 | STALE_ASOF flag removed | P6C5 | caught |
| 7 | Yahoo duplicate split rows not collapsed in-run | P6C3 | **survived with no observable effect**: the ledger key (`effective:ratio`) already dedups the event — the in-run `seen` set is redundant defence, not a behaviour (lock-and-mutate §④, "no behavioural effect") |
| 8 | split frame ignores ratio direction (forward splits counted) | P6C9 | caught |
| 9 | `sharesShort` used as float fallback | P6C7 | caught |
| 10 | `ticker_listed_by_sec` forced True | P6C8 | caught |
| 11 | schema allows an unmarked zero share count | P6C7 | caught |
| 12 | trace does not force `FAISAL_ONLY=1` | P6T1 | caught (P6T1, P6T2, P6T3, P6T4 — thresholds silently fall to 97/… and DKI/HUBC are re-attributed to M2) |
| 13 | trace assigns `CONFIG` | P6C11 | caught |
| 14 | workflow cron changed | P6C12 | caught |
| 15 | document summary row edited | P6T3 | caught |

14/15 caught by a named lock; the one survivor is a non-behavioural redundancy, documented rather than "fixed" by weakening the ledger.

## 6. Adversarial review — ten perspectives
1. **Collector storing current values as historical** — prevented structurally: CAT 2 requires a provider as-of (`schema_problems`), CAT 1 carries `asof_basis=COLLECTION`, and `evidence_class(rec, T)` returns 3 for any as-of after T; `P6C6` includes the mislabel mutation. Residual: the SEC `dei` "end" date is a fiscal period end — it is historical, but it describes the period, not the mention day (documented in the spec).
2. **Ticker referring to different securities over time** — the bot keys by ticker string; the collector adds `security_id=CIK` and SEC's own `tickers`/`formerNames` daily and keeps `original_ticker`; `P6C8` covers the mismatch case. Residual: no historical ticker-change source exists for mentions before today; the identity ledger's `SYMBOL_CHANGE` stays UNKNOWN for them.
3. **Reverse-split distortion** — share counts carry `split_frame`; `comparable()` refuses cross-frame use; the trace shows SXTC's M2 and HUBC's M4 failures *are* split-window artefacts (H2), which is reported, not corrected.
4. **Missing mistaken for negative** — status/UNKNOWN enforced (`P6C4`, `P6C5`); a provider zero must be labelled (`shares_zero_reported`, `P6C7`); the trace labels the DQ gate "not in code at T" rather than "passed".
5. **Future price leakage** — the trace uses bars strictly < T (`p3lib.bars_before`); Faisal states come from the dated registry; no outcome column is produced by `trace.py` at all.
6. **Confirmation bias toward DKI/SXTC/HUBC** — the trace machinery is generic (any ticker/date); the anchors were fixed by the mission; the result (S4 first wall) was checked against two independent reconstructions rather than asserted; HUBC's Faisal state is kept UNKNOWN.
7. **Same examples in discovery and validation** — Phase 6 ran no statistical test; the six rows are *traced*, not used to fit anything. The collector's future use must follow Phase 5's §N floor and a new pre-registration (not done here).
8. **Was a rejected ticker correctly rejected?** — Mechanically yes (predicate + live parameter reproduce 6/6). Methodologically unresolved: Phase 2–4 showed single-gate changes do not reproduce Faisal's picks without large false-positive growth; this report does not claim the rejections were "wrong".
9. **Apparent first failure a downstream symptom?** — Checked explicitly: S0–S2 pass, S3 did not exist at T, S4 is the first FAIL, S5–S9 never ran; the first-divergence principle is applied per row (SXTC M2 vs HUBC M4 vs DKI anchor differ; the anchor rule fails on all six independently).
10. **Instrumentation changing production** — Phase 6 adds no import to production modules; roots fingerprint unchanged; the only runtime effect is a new scheduled workflow that commits research files under `fm_forensics/phase6/`; the trace restores every `CONFIG` value it neutralises (`p3lib.run_gates` `finally`), verified by `P6T4`.

## 7. Known limitations (documented, not fabricated)
- Live provider behaviour (ChartExchange shell quota, Yahoo throttling, TradingView blocking, SEC rate limits) is observable only on Actions; the first run's coverage report is the evidence.
- Historical mentions (before 2026-10-09) get class-3 (current-only) values for float/borrow/TV float — by design; only mentions after collection start can be analysed with class 1/2 evidence.
- Short interest as-of is FINRA's settlement date; Yahoo may omit it (`NO_PROVIDER_ASOF`).
- SEC public float is in USD and only for domestic 10-K/10-Q filers.
- Ledger growth ≈ 300 KB/day; retention is an owner decision.
