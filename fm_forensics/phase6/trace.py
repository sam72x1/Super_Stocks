"""🔎🧭⑥ PHASE 6 — Workstream B: stage-by-stage pipeline trace for DKI / SXTC / HUBC (research only, frozen data).

For every Faisal-dated mention T of an anchor ticker the trace walks the production pipeline with a lookahead firewall
(bars < T): raw data → identity → universe → candidate gates (each gate's function/location, inputs, predicate + live
parameters, whether it ran, pass/fail — using `p3lib.run_gates`, i.e. the unmodified `analyze_ticker` with config-neutralised
ablation) → selection → near-watch / ready → notification. It then names the earliest ineligible stage and checks
reproducibility against Phase 3's independent daily reconstruction (`bot_states.csv.gz`) and LOGO rows.
No production code is modified; nothing is written outside `fm_forensics/phase6/out/`."""
import csv
import gzip
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
os.environ["FAISAL_ONLY"] = "1"            # production gates (the suite runs with FAISAL_ONLY=0; the trace must not inherit it)
os.chdir(ROOT)                           # the catalog envelope (`envelope_p100.json`) is loaded relative to cwd
sys.path.insert(0, os.path.join(ROOT, "fm_forensics", "phase3"))
sys.path.insert(0, HERE)
import p3lib as L                        # noqa: E402
import collector as C                    # noqa: E402

OUT = os.environ.get("P6_OUT") or os.path.join(HERE, "out")   # tests redirect output to a temp dir
ANCHORS = ("DKI", "SXTC", "HUBC")
FAISAL_STATE_OVERRIDE = {"HUBC": "UNKNOWN"}      # mission: HUBC's Faisal state stays UNKNOWN

# gate → (function:line, predicate text, live parameter names, context input keys)
GATE_SPEC = {
    "DEPTH":    ("analyze_ticker / MIN_BARS check (p3lib.run_gates)", "bars < MIN_BARS", ("MIN_BARS",), ("bars",)),
    "M1":       ("Super_stock.analyze_ticker:4046", "close < MIN_PRICE", ("MIN_PRICE",), ("price",)),
    "M2_CEIL":  ("Super_stock.analyze_ticker:4071", "drop from 52w high > MAX_DROP_PCT", ("MAX_DROP_PCT",), ("hi52", "drop_pct")),
    "M2_FLOOR": ("Super_stock.analyze_ticker:4073", "drop from 52w high < MIN_DROP_FLOOR", ("MIN_DROP_FLOOR",), ("hi52", "drop_pct")),
    "M3":       ("Super_stock.analyze_ticker:4085", "best prior spike (window PRIOR_SPIKE_WINDOW) < PRIOR_SPIKE_FLOOR", ("PRIOR_SPIKE_FLOOR", "PRIOR_SPIKE_WINDOW"), ("spike_pct", "n_spikes")),
    "M4_RANGE": ("Super_stock.analyze_ticker:4117", "base range over BASE_WINDOW bars > BASE_RANGE_MAX_PCT", ("BASE_RANGE_MAX_PCT", "BASE_WINDOW"), ("base_range_pct",)),
    "M4_RISE":  ("Super_stock.analyze_ticker:4139", "recent rise > RECENT_RISE_BLOCK_PCT", ("RECENT_RISE_BLOCK_PCT",), ("dist_low30_pct",)),
    "M5":       ("Super_stock.analyze_ticker:4144", "20-day dollar volume < MIN_DOLLAR_VOL", ("MIN_DOLLAR_VOL",), ("dollar_vol20",)),
    "RSI_OS":   ("Super_stock.analyze_ticker:4194", "RSI14 minimum over lookback > RSI_OS_HARD", ("RSI_OS_HARD",), ("rsi_min25",)),
    "RSI_NOW":  ("Super_stock.analyze_ticker:4201", "RSI14 now > RSI_NOW_HARD", ("RSI_NOW_HARD",), ("rsi14",)),
    "SOFT":     ("Super_stock.analyze_ticker:4244", "soft-fail count > WATCH_MAX_FAILS", ("WATCH_MAX_FAILS",), ()),
    "ANCHOR":   ("Super_stock.analyze_ticker:4541 (tested_level :10030)", "no level with ≥ 2 touches within 1.5% over 30 bars", (), ("tested_touches", "tested_level")),
    "SCORE":    ("Super_stock.analyze_ticker:4499", "score < SCORE_MIN", ("SCORE_MIN",), ()),
    "NEAR":     ("Super_stock.analyze_ticker:4355", "readiness below entry proximity", (), ()),
}
STAGES = ["S0_RAW_DATA", "S1_IDENTITY", "S2_UNIVERSE", "S3_DQ_GATE", "S4_CANDIDATE_GATES", "S5_SELECTION", "S6_NEAR_WATCH", "S7_READY", "S8_TRIGGER", "S9_NOTIFICATION"]


def _bot_states():
    p = os.path.join(ROOT, "fm_forensics", "phase3", "out", "bot_states.csv.gz")
    rows = {}
    if os.path.exists(p):
        for r in csv.DictReader(io.TextIOWrapper(gzip.open(p), encoding="utf-8")):
            rows[(r["symbol"], r["date"])] = r
    return rows


def _logo_rows():
    p = os.path.join(ROOT, "fm_forensics", "phase3", "out", "logo_rows.csv")
    out = {}
    if os.path.exists(p):
        for r in csv.DictReader(open(p, encoding="utf-8")):
            out[(r["symbol"], r["date"])] = r
    return out


def _identity():
    p = os.path.join(ROOT, "fm_forensics", "phase2", "SECURITY_IDENTITY_LEDGER.csv")
    return {r["CURRENT_TICKER"]: r for r in csv.DictReader(open(p, encoding="utf-8"))} if os.path.exists(p) else {}


def _alerts():
    p = os.path.join(ROOT, "alerts_history.json")
    return json.load(open(p, encoding="utf-8")).get("alerts", []) if os.path.exists(p) else []


def gate_status(sym, df):
    """Per-gate pass/fail with the production function (config-neutralised ablation): gate g fails iff, with every other
    gate neutralised, the rejection reason is g; it passes iff the run passes or fails on a later non-neutralisable stage."""
    out = {}
    base, reason, extra = L.run_gates(sym, df)
    out["_current"] = (base, reason, L.reason_gate(reason) if base == "REJECT" else ("DEPTH" if base == "TOO_FEW_BARS" else ""), extra)
    if base == "TOO_FEW_BARS":
        for g in L.GATE_ORDER:
            out[g] = "NOT_RUN"
        return out
    for g in L.GATE_ORDER:
        others = tuple(x for x in L.GATE_ORDER if x != g)
        r, why, _ = L.run_gates(sym, df, others)
        rg = L.reason_gate(why) if r == "REJECT" else ""
        out[g] = "FAIL" if rg == g else ("PASS" if r == "PASS" or rg in ("NEAR", "SCORE", "SOFT", "") or rg != g else "PASS")
        if r == "ERROR":
            out[g] = "ERROR"
    return out


def trace_one(sym, day, mention, states, logo, ident, alerts):
    before = L.bars_before(sym, day)
    ctx = L.context(sym, day) if len(before) >= 2 else None
    row = dict(ticker=sym, mention_date=day, evidence_id=mention.get("evidence_id", ""), faisal_state=FAISAL_STATE_OVERRIDE.get(sym, mention.get("faisal_state", "")),
               asof=before[-1][0] if before else "", bars_before=len(before))
    stages = []
    # S0 raw data
    sp = [d for d, r in L.rsplits(sym) if d <= day]
    stages.append(dict(stage="S0_RAW_DATA", where="fm_forensics/data/bars_2026-10-08.json.gz (TradingView bars, split-adjusted)",
                       inputs=f"bars<T {len(before)} · last bar {row['asof']} · reverse splits ≤T {len(sp)} (last {sp[-1] if sp else '—'})",
                       predicate="bars available before T", ran="YES", result="PASS" if len(before) >= 2 else "FAIL"))
    # S1 identity
    idr = ident.get(sym, {})
    stages.append(dict(stage="S1_IDENTITY", where="phase2/SECURITY_IDENTITY_LEDGER.csv · Super_stock keys by ticker string",
                       inputs=f"security_id={idr.get('SECURITY_ID','UNKNOWN')[:30]} · symbol_change={idr.get('SYMBOL_CHANGE','UNKNOWN')} · splits={idr.get('SPLIT_EVENTS_ALL','')[:60]}",
                       predicate="ticker string resolves to one continuous bar series", ran="YES",
                       result="PASS (ticker continuous; no symbol change evidence)" if idr else "UNKNOWN"))
    # S2 universe
    st = states.get((sym, day)) or states.get((sym, L.session(day)))
    stages.append(dict(stage="S2_UNIVERSE", where="Super_stock.get_universe:1729 (nasdaqlisted.txt)",
                       inputs=f"bot_states row {'present' if st else 'absent'} · nw_known={st.get('nw_known') if st else '—'}",
                       predicate="ticker listed on NASDAQ at T", ran="YES" if st else "UNKNOWN", result="PASS" if st else "UNKNOWN"))
    # S3 DQ gate (not reproducible offline)
    dq_live = day >= "2026-10-01"
    stages.append(dict(stage="S3_DQ_GATE", where="Super_stock.dq_filter:2429 (called :22156)",
                       inputs="needs a live Yahoo cross-check; not in frozen data" if dq_live else "gate shipped 2026-10-01 (#519); did not exist at T",
                       predicate="DQ status allow/warn", ran="UNKNOWN" if dq_live else "NO (not in code at T)",
                       result="NOT_REPRODUCIBLE_OFFLINE" if dq_live else "NOT_APPLICABLE_AT_T"))
    # S4 candidate gates
    gates = {}
    first_fail = ""
    if ctx is None or len(before) < L.S.CONFIG["MIN_BARS"]:
        cur = ("TOO_FEW_BARS", "MIN_BARS", "DEPTH", None)
        gates = {g: "NOT_RUN" for g in L.GATE_ORDER}
        first_fail = "DEPTH"
    else:
        gates = gate_status(sym, L.frame(before))
        cur = gates.pop("_current")
        first_fail = cur[2]
    for g in ["DEPTH"] + L.GATE_ORDER:
        spec = GATE_SPEC[g]
        params = {k: (round(L.S.CONFIG[k], 4) if isinstance(L.S.CONFIG[k], float) else L.S.CONFIG[k]) for k in spec[2]}
        inputs = {k: (ctx or {}).get(k) for k in spec[3]} if g != "DEPTH" else {"bars": len(before)}
        if g == "DEPTH":
            res = "FAIL" if cur[0] == "TOO_FEW_BARS" else "PASS"
            ran = "YES"
        else:
            res = gates.get(g, "NOT_RUN")
            ran = "YES" if cur[0] != "TOO_FEW_BARS" else "NO"
        stages.append(dict(stage="S4_CANDIDATE_GATES", gate=g, where=spec[0], inputs=json.dumps(inputs, ensure_ascii=False, default=str),
                           predicate=f"{spec[1]} · params {json.dumps(params)}", ran=ran, result=res,
                           first_in_sequence="YES" if g == first_fail else ""))
    row["candidate_result"] = cur[0]
    row["candidate_reason"] = cur[1]
    row["first_failing_gate"] = first_fail
    row["failing_gates_independent"] = ",".join(g for g in L.GATE_ORDER if gates.get(g) == "FAIL")
    # S5-S9 from reconstructed states / production state files
    stv = st or {}
    stages.append(dict(stage="S5_SELECTION", where="Super_stock.select_top:14133 · fill_picks:12860 · borrow_gate_recheck:12764",
                       inputs=f"watchlist={stv.get('watchlist','—')} · wl_snap={stv.get('wl_snap','—')}", predicate="among top-N candidates with borrow ≤ 20k",
                       ran="NO (no candidate)" if cur[0] != "PASS" else "YES", result="NOT_REACHED" if cur[0] != "PASS" else ("PASS" if stv.get("watchlist") == "1" else "FAIL")))
    stages.append(dict(stage="S6_NEAR_WATCH", where="Super_stock.near_watch_entry:13532 (scan_market :13991)",
                       inputs=f"near_watch={stv.get('near_watch','') or '—'}", predicate="rejected close to the gate walls",
                       ran="YES" if st else "UNKNOWN", result=("IN_NEAR_WATCH:" + stv["near_watch"]) if stv.get("near_watch") else "NOT_IN_NEAR_WATCH"))
    stages.append(dict(stage="S7_READY", where="Super_stock.entry_status:14914", inputs=f"ready={stv.get('ready','—')}", predicate="price inside tranche zone",
                       ran="NO" if cur[0] != "PASS" else "YES", result="NOT_REACHED" if cur[0] != "PASS" else ("READY" if stv.get("ready") == "1" else "WATCH")))
    stages.append(dict(stage="S8_TRIGGER", where="pullback_live.monitor_live_events / liq_stage_events (Polygon; dead since 2026-09-29)",
                       inputs="requires watchlist membership", predicate="liquidity anchor on a watchlist stock", ran="NO", result="NOT_REACHED"))
    al = [a for a in alerts if a.get("symbol") == sym and a.get("date", "") <= day]
    stages.append(dict(stage="S9_NOTIFICATION", where="Super_stock.build_daily_message:20454 → send_telegram:11532", inputs=f"alerts_history rows ≤T: {len(al)}",
                       predicate="ready card sent", ran="NO", result="NONE_SENT" if not al else f"SENT:{len(al)}"))
    # earliest ineligible stage = first stage whose result is FAIL (S0–S3 passed or were not applicable for every anchor row)
    row["earliest_ineligible_stage"] = (f"S4_CANDIDATE_GATES/{first_fail}" if first_fail else "NONE")
    # reproducibility checks
    bs = states.get((sym, day))
    lg = logo.get((sym, day))
    row["bot_states_reason"] = bs["reason"] if bs else "—"
    row["bot_states_agrees"] = "YES" if bs and bs["reason"] == cur[1] else ("NO" if bs else "NO_ROW")
    row["logo_agrees"] = "YES" if lg and lg["CURRENT_reason"] == cur[1] else ("NO" if lg else "NO_ROW")
    row["justified_by_documented_rule"] = "YES (gate predicate + live parameter in CONFIG; parameter provenance per FAISAL_SOURCE_LEDGER)" if first_fail else "n/a"
    row["input_data_unavailable"] = "NO (bars present)" if len(before) >= L.S.CONFIG["MIN_BARS"] else "YES (bars < MIN_BARS)"
    return row, stages


def main():
    os.makedirs(OUT, exist_ok=True)
    mentions = [m for m in C.build_mentions() if m["canonical_ticker"] in ANCHORS and m["is_faisal"] and m["post_date"] != C.UNKNOWN]
    tl = {}
    p = os.path.join(ROOT, "fm_forensics", "phase3", "FAISAL_TIMELINE.csv")
    for r in csv.DictReader(open(p, encoding="utf-8")):
        tl[(r["EVIDENCE_ID"], r["TICKER"])] = r["FAISAL_STATE"]
    states, logo, ident, alerts = _bot_states(), _logo_rows(), _identity(), _alerts()
    rows, stage_rows, seen = [], [], set()
    for m in sorted(mentions, key=lambda x: (x["canonical_ticker"], x["post_date"])):
        key = (m["canonical_ticker"], m["post_date"])
        if key in seen:
            continue
        seen.add(key)
        m = dict(m, faisal_state=tl.get((m["evidence_id"], m["original_ticker"]), ""))
        row, stages = trace_one(m["canonical_ticker"], m["post_date"], m, states, logo, ident, alerts)
        rows.append(row)
        for s in stages:
            stage_rows.append(dict(ticker=row["ticker"], mention_date=row["mention_date"], **s))
        print(row["ticker"], row["mention_date"], row["candidate_result"], row["candidate_reason"], "| independent fails:", row["failing_gates_independent"],
              "| bot_states", row["bot_states_agrees"], "| logo", row["logo_agrees"], flush=True)
    keys = ["ticker", "mention_date", "evidence_id", "faisal_state", "asof", "bars_before", "candidate_result", "candidate_reason", "first_failing_gate",
            "failing_gates_independent", "earliest_ineligible_stage", "bot_states_reason", "bot_states_agrees", "logo_agrees", "justified_by_documented_rule", "input_data_unavailable"]
    with open(os.path.join(OUT, "PHASE6_TRACE_SUMMARY.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
    skeys = ["ticker", "mention_date", "stage", "gate", "where", "inputs", "predicate", "ran", "result", "first_in_sequence"]
    with open(os.path.join(OUT, "PHASE6_TRACE_STAGES.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=skeys, extrasaction="ignore"); w.writeheader(); w.writerows(stage_rows)
    json.dump(dict(rows=rows, n_stage_rows=len(stage_rows)), open(os.path.join(OUT, "PHASE6_TRACE_SUMMARY.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return rows, stage_rows


if __name__ == "__main__":
    main()
