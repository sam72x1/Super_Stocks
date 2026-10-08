# CANDIDATE_GATE_FORENSICS — Phase 3 (2026-10-08) · research only

## §1 Actual production trace (code read, not documentation) — `Super_stock.py` at `4ac8a642f`

| Stage | Where | What actually happens | Lookahead | Temporal position vs Faisal |
|---|---|---|---|---|
| ticker universe | `get_universe()` ← `nasdaqlisted.txt` (NASDAQ only) | symbol strings; no identity object | safe | — |
| eligibility | `MIN_BARS=120` daily bars (`download_history`/`tv_download`, adjustment=splits) | fewer bars ⇒ silently dropped (never in `reject_log`) | safe | Faisal's post-split regime (TG_1807/1811: MA30 *from the split date*) needs 20-40 bars; a history re-based at the split would be dropped here |
| normalization | TradingView adjusted bars (`BARS_SOURCE=tradingview`), Yahoo fallback; `repair_split_mismatch` dead (Polygon ended 09-29) | one price regime: cumulative split-adjusted | safe | the regime Faisal uses (post-split prices) is reconstructable but not represented |
| M1 | `analyze_ticker` L4045: `price < MIN_PRICE` (0.40 live) | reject `M1_سعر` | safe | identity |
| M2 | L4053-4073: `hi52 = High.tail(252).max()`; drop ∉ [71.72, 99.95] ⇒ `M2_هبوط_فوق_97` / `M2_هبوط_تحت_40` | the 252-bar high is the cumulative-adjusted high; `BT_SPLIT_REF_M2` branch is backtest-only (`_BT_SPLITS_CTX is None` in production) | safe | identity — evaluated on day 1 of a post-split regime using pre-split highs |
| M3 | L4081-4085: `spike_info(close[:-15])` best gain over 1..20-session windows ≥ 78.27% | reject `M3_انفجار_تحت_60` | safe | identity (requires a *prior* explosion inside the adjusted series) |
| M4 range | L4088-4117: 15-session High/Low range ≤ 120% | reject `M4_base_واسعة` (pullback mode has a `held_at_tested_level` escape — not used by the scanner) | safe | structure — measured on the last 15 bars regardless of where the low is |
| M4 rise | L4136-4139: 5-session gain ≤ 214.7% (envelope) | reject `M4_انفجر_فعلاً` | safe | structure |
| M5 | L4142-4144: mean(close×vol, 20) ≥ $14.3K | reject `M5_سيولة` | safe | identity |
| M6-M9 | soft fails (frames, candle pattern, gap-above) | counted | safe | — |
| M10 | L4185-4205: RSI min25 > 69 ⇒ `M10_RSI_ما_تشبّع`; RSI now > 71.1 ⇒ `M10_RSI_فات_القطار`; soft otherwise | hard thresholds are envelope P100 | safe | timing |
| M11-M12 | MACD / EMA30-50 soft | counted | safe | — |
| SOFT cap | L4243: `len(soft_fails) > WATCH_MAX_FAILS (8)` ⇒ `نواقص_فوق_8` | | safe | — |
| stability | L4319-4338: `pivot_stability` display only (`BT_STABILITY_GATE` off) | **no gate** | safe | Faisal's «3-5 sessions» is displayed, never required |
| NEAR | L4349-4355: `readiness < NEAR_PCT (0)` ⇒ inactive | | safe | — |
| SCORE | L4498-4499: `score < SCORE_MIN (5)` ⇒ `نقاط_تحت_5` | | safe | — |
| ANCHOR | L4533-4541: `ANCHOR_MODE=tested_strict` ⇒ `tested_level(df, 30, 0.015, 2)` must find ≥2 *independent* clusters of lows within 1.5% of the 30-bar minimum, else `M_لا_مستوى_مختبر` | the rule is Faisal's ENTRY anchor (IMG_0451) applied as a CANDIDATE gate | safe | **temporal mismatch**: Faisal's Watch begins at touch #1 (SMX TG_1908, KWM, DKI TG_57894); the second touch, when it comes, is usually a *higher* second support (YMT 1.84 vs 1.81 = +1.7% > tol 1.5%) |
| RR | L4750-4758 | soft/reject | safe | — |
| reject_log | `_reject()` → `_REJECT_STATS`/`_REJECT_REASONS`; `reject_log.json` keeps walls per day (sampled) | first wall only | safe | — |
| select_top / fill_picks | 15 slots, rank_key, M13/M14/borrow gates on the enriched picks, 4 fill rounds | membership | safe | — |
| watchlist | `weekly_watchlist.json` — active until stop; daily `update_watchlist_status` | the only persistent object | safe | persistence exists only AFTER candidacy |
| near_watch | `near_watch_measure/founded` on rejected names within ≤2 envelope criteria (`NEAR_WATCH_MAX_OUT`) | a second persistent object (from 2026-08-16), display cut 20 per bucket | safe | — |
| READY NOW | `entry_status()` L14914 on watchlist members: `near_support`/`sweep_confirmed` ∧ price ≤ top tranche | a price-location flag | safe | downstream |

**Candidate memory:** none. Every scan re-evaluates every symbol from scratch; a symbol that passed yesterday and fails today is gone (unless already a watchlist member).

## §2 Gate concept audit
See `GATE_CONCEPT_MATRIX.csv` (16 gates) — concept, source image, direct support, contradictions, temporal position, necessity, sufficiency, status.

## §3 Leave-one-gate-out (LOGO) — pre-registered in `PHASE3_prereg.md §⑥`
Research harness `p3lib.run_gates` runs the **unmodified** production `analyze_ticker` with one threshold relaxed per run (values restored in `finally`; the anchor gate is relaxed by wrapping `tested_level`, restored likewise). Targets: all Faisal-dated FOCUS/WATCH/READY/ENTRY rows with bars (independent set), the three anchors ±20 sessions around 2026-09-11, and the negative/matched controls on the 20 `reject_log` dates.

Results: `LOGO_SUMMARY.csv` · rows in `out/logo_rows.csv`.

### §3.1 Results (`LOGO_SUMMARY.csv` · `out/logo_rows.csv` · lookahead-safe: bars < DATE; weekend Faisal dates evaluated on the following session)

**Denominators.** Faisal-dated rows with ≥1 bar: **53** (ticker,date) pairs over **41** tickers (FOCUS 7 · WATCH 37 · READY 5 · ENTRY 4). Negative + matched controls: **1,320** rows (Phase 2 `groups.json` neg ∪ m2hi on the 20 `reject_log` dates). Anchor days: **160** (DKI/SXTC/HUBC/CRE × 41 sessions around 2026-09-11, minus days without bars).

| Gate | First wall on Faisal rows | Faisal PASS without it | Negative/matched PASS without it | Restore ratio | Negative inflation |
|---|---|---|---|---|---|
| CURRENT (no change) | — | 3 / 53 | 299 / 1,320 | — | — |
| ANCHOR (two-touch) | **20** | **23 / 53** | **914 / 1,320** | **0.40** | **×3.06** |
| M3 (prior spike) | 13 | 4 / 53 | 299 / 1,320 | 0.02 | ×1.00 |
| M2_CEIL | 7 | 3 / 53 | 318 / 1,320 | 0.00 | ×1.06 |
| M4_RANGE | 6 | 3 / 53 | 312 / 1,320 | 0.00 | ×1.04 |
| DEPTH (MIN_BARS 120) | 2 | n/a (not a threshold) | — | — | — |
| M2_FLOOR | 1 | 3 / 53 | 300 / 1,320 | 0.00 | ×1.00 |
| RSI_NOW | 1 | 3 / 53 | 299 / 1,320 | 0.00 | ×1.00 |
| M1 · M4_RISE · M5 · RSI_OS · SOFT · SCORE | 0 | 3 / 53 | 299 / 1,320 | 0.00 | ×1.00 |
| ALL identity gates off | — | **51 / 53** (2 = TOO_FEW_BARS: BETA, CRE 2025-08) | — | — | — |

**The gates stack.** Removing a single non-anchor gate almost never restores a Faisal row because the next wall takes over: M3-walled rows (13) → without M3: ANCHOR 7 · M4_RANGE 5 · PASS 1; M2_CEIL-walled rows (7) → M4_RANGE 5 · ANCHOR 2; M4_RANGE-walled rows (6) → ANCHOR 6. Counting the anchor rule at *any* depth, it blocks **35 / 53** Faisal rows (66%); it is also the first wall on **615 / 1,320** control rows (47%) — i.e. the rule rejects almost everything that is sitting on a fresh low, Faisal's names included.

**Pre-registered prediction P3** («no single gate restores ≥50% of Faisal rows without raising negative-control PASS ≥2×») **holds**: the only gate with a material restore ratio (ANCHOR, 0.40) triples the control pass rate. H1's falsifier (one gate restores ≥50% at <2× inflation) **fired** — H1 (mis-tuned thresholds) is rejected as a *single-threshold* explanation; what remains of it is absorbed into the stage-order finding below.

**Anchor days (160).** Removing ANCHOR alone: 3 → **57** candidate-days. DKI is rejected by the anchor rule alone on every session 2026-09-08 → 2026-09-16 (touches 0 after each new low; `DKI_TIMELINE.csv`); SXTC and HUBC are walled by M2_CEIL and no *single* gate restores them (all identity gates off → PASS); CRE is walled by M4_RANGE (15-bar range ≈250%).

### §3.2 Temporal reading of the anchor rule
`tested_level(df, 30, 0.015, 2)` needs two independent clusters of lows within 1.5% of the 30-bar minimum. On Faisal's dated rows the context at T−1 shows **tested_touches = 0** in all 7 positive controls (`POSITIVE_TEMPORAL_CONTROLS.csv`) and in **20 of the 20** anchor-walled rows; in 11 of the 20 the 30-bar low is 0–2 sessions old and in 8 the price sits within 10% of it (the rest are 3–29 sessions after a low the rule still finds untested, e.g. UPC +34% / 23 sessions, CUPR +26% / 29 sessions). Faisal's own text on the same dates is a WATCH/FOCUS declaration at touch #1 (SMX TG_1908 «تحت المراقبه الان» on the day the low formed; KWM «1.50 قاع امس … مراقبه 3 جلسات»; ELPW «متبقي شمعتين … تحت المتابعه فقط» before the low exists; DKI TG_57894 «الشراء بعد المسح»). The second touch, when it comes, is frequently a *higher* second support (YMT 1.84 vs 1.81 = +1.7% > tol 1.5%) or a sweep *below* the first low (7–13%, `PIVOT_SWEEP_PCT`), neither of which the 1.5% cluster test counts as a touch of the same level. So the rule is Faisal's **entry** anchor (IMG_0451 «ضربها مرتين ولا كسرها») applied at **candidate** time: it asks for the retest before the watch begins.

### §3.3 Gate-definition variants (§9 of the brief · research only)
See `ANCHOR_VARIANTS.csv` (tol 3% · tol 5% · lookback 60 · min_touches 1 · tol 3% + lookback 60) — filled by `variants.py`; numbers quoted in `PHASE3_FINAL_REPORT.md §C`.

### §3.4 What this does and does not show
- It shows **where** Faisal's dated decisions sit relative to the production gates on the same bars (necessity of each gate on his rows; sufficiency of removing one).
- It does **not** show that any relaxation is *good*: every relaxation that admits Faisal's rows admits ≥3× more control rows; the bot has no object to hold them (no candidate memory) and no later stage to discriminate them (the anchor rule *is* its retest).
- Replay thresholds are today's live envelope (`envelope_p100.json` as of 2026-10-08), not the envelope of each historical day (changed 08-06 / 08-10) — stated limitation, `LOOKAHEAD_AUDIT.csv`.
- No production code, threshold, or state file was modified; `p3lib.run_gates` restores CONFIG and `tested_level` in `finally`.

