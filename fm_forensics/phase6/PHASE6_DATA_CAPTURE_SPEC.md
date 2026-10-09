# PHASE 6 — DATA CAPTURE SPEC (Workstream A · `fm_forensics/phase6/collector.py`)

Status: built and validated offline with injected providers (locks `P6C1`–`P6C12` in `test_bot.py`). Live runs happen only on
GitHub Actions (`.github/workflows/fm_phase6_collect.yml`); this session cannot reach any provider (proxy 403).

## 1. What is captured, from which existing integration, and what it can and cannot prove
| Field | Source (existing integration reused) | Units | As-of basis | Category at capture | Limitation (documented, not papered over) |
|---|---|---|---|---|---|
| `public_float` | Yahoo `Ticker.info.floatShares` via `_fetch_info` | shares | COLLECTION | 1 | Yahoo publishes no as-of; the value is a snapshot at collection time only. |
| `public_float` | TradingView screener `float_shares_outstanding` (`tv_data.scan`) | shares | COLLECTION | 1 | Same; unofficial API, may change/block. One scan per run serves all tickers. |
| `public_float` | SEC XBRL `dei/EntityPublicFloat` | **USD** | PROVIDER (`end`) | 2 | A dollar value at the fiscal period end, not a share count — never mixed with share counts (`units` differ). Foreign 6-K/20-F filers mostly lack it. |
| `shares_outstanding` | Yahoo `sharesOutstanding` · SEC `dei/EntityCommonStockSharesOutstanding` | shares | COLLECTION · PROVIDER | 1 · 2 | SEC value is per filing cover page (dated); Yahoo is a snapshot. |
| `short_interest` | Yahoo `sharesShort` + `dateShortInterest` | shares | PROVIDER when `dateShortInterest` present, else COLLECTION | 2 · 1 | FINRA settlement-date as-of; flagged `STALE_ASOF` when older than 45 days at collection; `NO_PROVIDER_ASOF` when Yahoo omits the date. |
| `borrow_available` · `borrow_fee` | ChartExchange borrow page via `ce_borrow_info(sym, diag)` (IBKR feed) | shares · % annual | COLLECTION | 1 | Current only; page shows no as-of. Soft quota ≈50 pages per runner ⇒ `CE_QUOTA=48`, the rest written `NOT_ATTEMPTED quota:48`; the ticker order rotates by last attempt (`borrow_order`) so every ticker is reached within two runs. Zero available is recorded as `units=shares_zero_reported` (explicit provider zero, distinct from missing). |
| `sec_filing` | SEC submissions JSON (`form`, `filingDate`, `accessionNumber`, `acceptanceDateTime`) | json | PROVIDER (`acceptanceDateTime`) | 2 | One row per accession (idempotent across runs). Only the `recent` block is read (≤1000 filings); for tickers not yet in the ledger only filings dated ≥ `SEC_FILINGS_SINCE` (2025-01-01) are added (first live run backfilled 30,457 rows = 31 MB). |
| `reverse_split` | Yahoo `Ticker.splits` (ratio < 1) · Nasdaq split calendar (`data_quality.nasdaq_calendar`; announcement + ex-date) | ratio | PROVIDER (effective date) | 2 | Yahoo history may contain duplicate rows (same date/ratio) — collapsed; Nasdaq calendar window is 45 days back only. |
| `identity` | SEC CIK map + submissions (`name`, `tickers`, `exchanges`, `formerNames`) | json | COLLECTION | 1 | Ticker→CIK resolved at collection; `security_id` = `CIK##########` when resolved, else `UNKNOWN`. Historical ticker changes are only visible through `formerNames` (names, not tickers). |

Short interest ≠ public float ≠ borrow availability: three different fields, three different sources, never substituted (`P6C7`).

## 2. Record schema (one JSONL row per observation)
`obs_key` (sha256 of `[ticker, field, source, event_id]`) · `seq` · `prev_sha256` · `sha256` · `run_id` · `collected_utc` (tz-aware, `Z`) ·
`ticker` (canonical) · `original_ticker` · `security_id` · `field` · `value` (numeric, json, or the literal `UNKNOWN`) · `units` ·
`source` · `source_url` · `source_asof` · `asof_basis` (`PROVIDER` | `COLLECTION` | `UNKNOWN`) · `category` (1 | 2 | 4 at capture) ·
`status` (`OK` | `UNKNOWN` | `FAILED` | `NOT_ATTEMPTED`) · `failure_reason` · `raw_sha256` (content-addressed raw response) ·
`split_frame` (`post:<last reverse split ≤ as-of>` or `pre:none`) · `extra` (quality flags, provider extras).

Invariants enforced by `schema_problems` and `Ledger.verify` (both run by the suite and by `collector.py verify`):
- non-OK rows carry `value=UNKNOWN`, `category=4` (missing is never zero);
- CAT 2 requires a provider as-of; CAT 1 requires collection as-of; CAT 3 is never written — it is computed by `evidence_class(record, T)` at use time;
- a zero share count must be an explicit provider zero (`units=shares_zero_reported`);
- `collected_utc` must be tz-aware ISO; naive timestamps are refused (`parse_ts` → None, `utc_now_iso` raises);
- hash chain: `prev_sha256` of row *n* equals `sha256` of row *n−1*; genesis is 64 zeros.

## 3. Event identity (idempotence)
| Field | `event_id` | Effect |
|---|---|---|
| snapshot fields (float, SO, borrow, identity) | collection date (UTC) | one row per source per day; same-day re-run adds nothing |
| short interest | `asof:<dateShortInterest>` | one row per FINRA as-of date; a new as-of date adds a new row |
| SEC filing | accession number | one row per filing, ever |
| SEC dei points | `<accession>:<period end>` | one row per cover-page value |
| reverse split | `<effective>:<ratio>` per source | one row per event per source; `yahoo_splits` duplicates collapsed in-run |

`Collector.run(resume=True)` skips a ticker whose daily Yahoo float row and SEC identity row already exist (resumable after a
killed job); forced re-runs are still idempotent because `Ledger.append` refuses existing keys.

## 4. Mentions registry (`data/PHASE6_MENTIONS.csv`, rebuilt deterministically every run)
Sources: Phase 5 cohort manifest · Phase 3 Faisal timeline · V4.1 intake annotations · prospective ledger. Fields: `mention_id`,
`evidence_id`, `original_ticker`, `canonical_ticker`, `post_date`, `post_timestamp` (UTC when visible, else `UNKNOWN`), `post_tz`,
`ts_precision` (`TIMESTAMP` | `DATE` | `DATE_AMBIGUOUS` | `INFERRED`), `author`, `is_faisal`, `source`. Duplicate posts collapse on
(`evidence_id`, `original_ticker`). Collection set = Faisal-authored mentions only (`mention_tickers(faisal_only=True)`); placeholders
(`UNK`) excluded. Today: 303 mentions · 89 tickers. Controls are **not** collected (none pre-registered).

## 5. Historical vs current — the rule that makes the ledger honest
A record is historical evidence about mention date T only if `evidence_class(record, T) ∈ {1, 2}`, i.e. status OK **and** as-of ≤ T.
Every CAT 1 snapshot captured after T is class 3 for that T (current-only) and must not be used to describe T. Consequently, for all
mentions dated before the first live run, float/borrow/TV values are class 3 — this is expected and is exactly what Phase 5 found
(`H1`/`H3` NOT TESTABLE); the ledger only becomes historical evidence for mentions made **after** collection starts.

## 6. Operations
- Runner: `fm_phase6_collect.yml` — daily `41 2 * * 2-6` (after the ChartExchange borrow harvest, before the screener) + manual;
  commits only `fm_forensics/phase6/data/*` and `out/*`; raw responses are uploaded as a 90-day artifact (`phase6-raw-<run>`), not committed.
- Rate limits: `P6_PACE_S` (0.4 s between provider calls) · `CE_QUOTA` 48 · SEC ≤ 10 req/s by construction · single TV scan.
- Outage safety: any provider exception becomes a `FAILED` row with the exception name; a dead provider never aborts the run.
- Auditability: `audit(ledger, run_id)` lists every expected (ticker, field, source) without a status row (must be empty) and verifies the chain.
- Reverse splits / identity changes: share-count rows carry `split_frame`; `comparable(a, b)` refuses cross-frame comparisons;
  `original_ticker` is kept beside `ticker`; SEC `tickers`/`formerNames` are stored verbatim.
- Growth: ≈ 9 snapshot rows per ticker per day (≈ 800 rows ≈ 300 KB/day for 89 tickers). Retention/rotation is an owner decision.

## 7. Boundaries
No production module is modified; nothing here is imported by `Super_stock.py`; no Telegram; no threshold; no V4 artefact; no claim
that collection improves selection or performance (it cannot — it only makes Phase 5's untestable hypotheses testable going forward).
