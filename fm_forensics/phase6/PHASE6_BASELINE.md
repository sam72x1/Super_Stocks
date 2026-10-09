# PHASE 6 — BASELINE MANIFEST (written before any Phase 6 change)

Date: 2026-10-09 · Branch for this phase: `claude/conversation-compaction-failure-088pki` (= `main` at start).

## 0. Repository state at baseline
| Item | Value |
|---|---|
| `main` head | `e85f12af59c70e1586e139d911d56b2c118c04eb` (merge of PR #583, Phase 5) |
| Phases shipped | #578 (Phase 3 prereg) … #582 (Phase 5 prereg `4249c764`) · #583 (Phase 5 results `e85f12af`) |
| CI on main (read from Actions log) | tests `113656086448` / `113656131062` ✅ · lint `113656086262` ✅ |
| Isolated suite at baseline | 5268 pass / 0 fail (Phase 5 ship) |
| `LOGIC_VERSION` | `2026.08.14-…+pivotstoplow` (unchanged by Phase 6 — asserted in validation) |
| `FAISAL_ONLY` | `1` (envelope `envelope_p100.json`) |
| CLAUDE.md size | 239,568 chars (< 250,000 `MEM1`) |

## 1. Existing data-provider integrations (inspected before writing any collector)
All in `Super_stock.py` unless stated. None of them stores a point-in-time history of float / short interest / borrow for Faisal tickers; that is the gap Workstream A fills **without** adding providers.

| Field | Function (line) | Provider | Returns | Timestamp semantics today |
|---|---|---|---|---|
| Public float (shares) | `_yahoo_float_status(sym)` :13289 · `_yahoo_float(sym, strict)` :7562 | Yahoo `Ticker.info.floatShares` | `("ok",v)/("miss",None)/("fail",None)` | **current only** (Yahoo gives no as-of) |
| Public float (shares) | `tv_data.scan(columns=["float_shares_outstanding",…])` `tv_data.py:275` | TradingView screener | `{"EXCH:SYM": {...}}` or `None` for the whole scan | **current only** |
| Public float ($) · shares outstanding | SEC XBRL `dei/EntityPublicFloat`, `dei/EntityCommonStockSharesOutstanding` (used by `fm_forensics/phase5/sec_probe.py`, frozen in `fm_forensics/data/sec_2026-10-08.json.gz`) | data.sec.gov | per-filing values with `end`/`filed` | **historical, timestamped** (units: USD for public float; shares for outstanding) |
| Short interest | `_fetch_info(t)` :6526 (`sharesShort`, `dateShortInterest`, `shortRatio`) | Yahoo | dict | provider as-of date present (`dateShortInterest`) ⇒ historical-as-of |
| Shares available to borrow + fee | `ce_borrow_info(sym, diag)` :4968 (`_parse_ce_borrow` :4935, Next.js `bf-summary` since 2026-10-06) | ChartExchange (IBKR feed) | `{"shares_available", "borrow_fee"}` or `{}` + `diag["reason"]` | **current only**; ~50 pages/runner quota (`ctb_harvest.py`) |
| Daily short volume | FINRA/Fintel chain (M13) | — | — | not a Phase 6 field (≠ short interest ≠ borrow) |
| SEC filings | `sec_cik_map()` :6013 · `sec_recent_filings(sym)` :6130 (`SEC_UA` :1106, `SEC_CONTACT` env) | data.sec.gov submissions | rendered lines | historical, with `acceptanceDateTime` in raw JSON |
| Reverse splits | `_fetch_splits(sym)` :14278 (Yahoo) · `data_quality.nasdaq_calendar(days, today, get, workers)` `data_quality.py:544` (announcement + ex-date) · `_fetch_splits_dq(sym, upto)` :14303 (union) | Yahoo · Nasdaq calendar | Series / `{sym:[(day,ratio)]}` | historical, effective-dated |
| Identity | `sec_cik_map()` (CIK ↔ ticker) · SEC submissions `formerNames`, `tickers` | SEC | — | historical (former names dated) |
| Bars | `download_history` :2524 (TradingView `BARS_SOURCE` → Yahoo fallback) | — | — | adjusted bars; not re-fetched by Phase 6 (frozen `fm_forensics/data/bars_2026-10-08.json.gz`) |

Blocked from this session (proxy 403): sec.gov, Yahoo, ChartExchange, TradingView. ⇒ live collection runs only on GitHub Actions runners; everything built here is validated with injected fetchers.

## 2. Existing Faisal-mention sources (inputs of the collector)
| Source | Rows | Fields used |
|---|---|---|
| `fm_forensics/phase5/PHASE5_COHORT_MANIFEST.csv` | 88 rows · 45 securities | `SECURITY_ID`, `TICKER_AT_DECISION`, `DECISION_DATE`, `FAISAL_DATE_RAW`, `EVIDENCE_ID`, `HAS_BARS` |
| `fm_forensics/phase3/FAISAL_TIMELINE.csv` | 306 observations | `TICKER`, `DATE`, `EVIDENCE_ID`, `EVIDENCE_TYPE`, `AUTHOR`, `IS_FAISAL`, `FAISAL_STATE` |
| `faisal_method_v41/final_protocol/intake/*/annotations.json` | B4: 4 images | `symbol`, `decision_date`, `post_timestamp_visible`, `date_evidence_level`, `faisal_author` |
| `faisal_validation/PROSPECTIVE_LEDGER.jsonl` | 2 rows (hash-chained) | `ticker`, `faisal_timestamp` (UTC), `provenance.message_id` |
| `telegram_collect_meta.jsonl` | 54 rows | `message_id`, `date` (UTC), `sha256` |

## 3. Existing pipeline entry points (Workstream B trace targets)
| Stage | Function (line) | Evidence available offline |
|---|---|---|
| Universe | `get_universe()` :1729 (`nasdaqlisted.txt`) | `fm_forensics/phase3/out/bot_states.csv.gz` (30,698 rows; `nw_known`, `wl_snap`) |
| Bars | `download_history` :2524 | frozen bars (232 symbols) |
| Data-quality gate | `dq_filter` :2429 (called :22156 daily, :21739 renewal) | — |
| Candidate gates | `analyze_ticker` :4029 → `_reject` :3920 sites: M1 :4046 · M2 :4068/4071/4073 · M3 :4085 · M4 :4095/4117/4128/4139 · M5 :4144 · RSI :4194/4201 · soft :4244 · stability :4335/4338 · near :4355 · score :4499 · anchor :4541 | `S._REJECT_REASONS` + `p3lib.run_gates` (unchanged production code, config-neutralised ablation) |
| Selection | `select_top` :14133 · `rank_key` :12958 · `fill_picks` :12860 · `borrow_gate_recheck` :12764 · `refloat_gate_recheck` :12720 | `weekly_watchlist.json` (33 stocks), `alerts_history.json` (271 alerts) |
| Near-watch | `near_watch_entry` :13532 (called :13991 in `scan_market` :13932) | `near_watch.json` (671 symbols) |
| Ready | `entry_status` :14914 | `bot_states.csv.gz` `ready` column |
| Notification | `build_daily_message` :20454 (`ready_only=True` :22324) → `send_telegram` :11532 (:22416, :22419) | `alerts_history.json` |

Prior results reused rather than repeated (per mission): Phase 2 identity ledger (`phase2/SECURITY_IDENTITY_LEDGER.csv`), Phase 3 LOGO rows (`phase3/out/logo_rows.csv`), Phase 3 daily bot states.

## 4. Verified baseline behaviour (to be re-asserted after Phase 6)
- Roots fingerprint (`rank_key select_top classify_tier analyze_ticker apply_short_gate apply_float_gate scan_market backtest_symbol scan_ignition scan_split_hunter entry_status build_interpretation`) vs `origin/main`: **no difference** (recorded in `PHASE6_VALIDATION_REPORT.md`).
- `analyze_ticker` on frozen bars for DKI/SXTC/HUBC at their Faisal dates (from `phase3/out/logo_rows.csv`): DKI 2026-09-13 → `M_لا_مستوى_مختبر`; SXTC 2026-09-10/11/13/24 → `M2_هبوط_فوق_97`; HUBC 2026-04-24 → `M4_base_واسعة`. Phase 6 trace must reproduce these bit-for-bit (lock `P6T2`).
- No Telegram, no production state file, no threshold, no V4 artefact is written by Phase 6 code (locks `P6C9`, `P6T4`).
