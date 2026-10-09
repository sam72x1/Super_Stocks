"""🚪🧭 Gate provenance inventory — research only (no Telegram, no state writes, no production change).

What it builds (owner mission «GATE PROVENANCE, CANDIDATE GENERATION, AND EVIDENCE-BASED REPAIR», 2026-10-09):
  · one row per gate of the candidate chain (universe → data → `analyze_ticker` → post-scan → quality → capacity →
    post-enrich → readiness → manual display), from the curated provenance file `data/gate_provenance.json`;
  · derived columns read from the code itself: the line of each gate's anchor inside its function (AST), the live
    threshold values under the production configuration (`FAISAL_ONLY=1`), production reject counts from a frozen
    snapshot of `reject_log.json`, and completeness checks (every `_reject(...)` code and every post-scan gate
    function must be inventoried — an uninventoried gate fails the build);
  · the first exclusion of each Faisal episode at its as-of date, recomputed with the production `analyze_ticker`
    on the frozen ranking bars (`data/rank/bars.json.gz`, bars dated < T), checked against the frozen ranking rows
    (`data/rank/rows.csv.gz`), with the peel chain (the next wall when the previous one is neutralised — research
    only, the cause is always the FIRST wall) and the metrics needed to tell an adjustment artefact from a rule;
  · `GATE_PROVENANCE_REPORT.md` — the decision table, generated from the data (no hand-typed numbers).

`python3 faisal_engine/gate_inventory.py` builds · `--check` rebuilds in memory and compares (line numbers are
normalised: they move with any edit above the gate; the anchor must still be found inside its function).
`--snapshot` refreshes the frozen reject-count snapshot from the working `reject_log.json` (explicit only).
"""
import ast
import contextlib
import csv
import gzip
import hashlib
import io
import json
import os
import re
import sys

os.environ["FAISAL_ONLY"] = "1"                 # the subject is the production configuration
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gate_audit as GA                          # noqa: E402 — pure derivation (no I/O, no env)
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "out")
DATA = os.path.join(HERE, "data")
PROV = os.environ.get("GATE_PROV_FILE") or os.path.join(DATA, "gate_provenance.json")
SNAP = os.path.join(DATA, "gate_reject_snapshot.json")
F_JSON = os.path.join(OUT, "GATE_INVENTORY.json")
F_CSV = os.path.join(OUT, "GATE_INVENTORY.csv")
F_FX = os.path.join(OUT, "gate_first_exclusion.csv")
F_MD = os.path.join(HERE, "GATE_PROVENANCE_REPORT.md")
CATS = ["DIRECT_FAISAL_EVIDENCE", "INFERRED_FROM_FAISAL_EVIDENCE", "OWNER_POLICY", "ENGINEERING_GUARD",
        "DATA_OR_ADJUSTMENT_ARTIFACT", "UNKNOWN_OR_UNSUPPORTED"]
# post-scan gate functions that must each be inventoried (completeness)
REQUIRED_FUNCS = ["get_universe", "_extract_into", "analyze_ticker", "apply_short_gate", "apply_float_gate", "classify_tier",
                  "rank_key", "dq_filter", "fill_picks", "refloat_gate_recheck", "borrow_second_chance",
                  "borrow_gate_recheck", "entry_status", "append_short_float_gates", "post_enrich_verdict"]
# production reject code → peel-chain gate name (p3lib.reason_gate names) → inventory id
GATE_ID = {"M1": "M1_PRICE", "M2_CEIL": "M2_CEIL", "M2_FLOOR": "M2_FLOOR", "M3": "M3_FLOOR", "M4_RANGE": "M4_RANGE",
           "M4_RISE": "M4_RISE", "M5": "M5_DOLLAR_VOL", "RSI_OS": "M10_RSI_OS", "RSI_NOW": "M10_RSI_NOW",
           "SOFT": "SOFT_COUNT", "SCORE": "SCORE_MIN", "NEAR": "NEAR_READINESS", "ANCHOR": "ANCHOR_TWO_TOUCH",
           "DEPTH": "D_DEPTH", "UNIVERSE": "U_NASDAQ"}
NEUTRAL = {"M1": {"MIN_PRICE": 0.0}, "M2_CEIL": {"MAX_DROP_PCT": 1e9}, "M2_FLOOR": {"MIN_DROP_FLOOR": -1e9},
           "M3": {"PRIOR_SPIKE_FLOOR": -1e9}, "M4_RANGE": {"BASE_RANGE_MAX_PCT": 1e9},
           "M4_RISE": {"RECENT_RISE_BLOCK_PCT": 1e9}, "M5": {"MIN_DOLLAR_VOL": 0.0}, "RSI_OS": {"RSI_OS_HARD": 1e9},
           "RSI_NOW": {"RSI_NOW_HARD": 1e9}, "SOFT": {"WATCH_MAX_FAILS": 10 ** 6}, "SCORE": {"SCORE_MIN": -1e9},
           "NEAR": {"NEAR_PCT": -1e9}, "DEPTH": {"MIN_BARS": 0}, "ANCHOR": {}}
EXTRA_CASES = [("HUBC", "2026-04-24", "TG_2098", "anchor case (Faisal state UNKNOWN)")]


def _S():
    sys.path.insert(0, ROOT)
    os.chdir(ROOT)
    with contextlib.redirect_stdout(io.StringIO()):
        import Super_stock as S                          # noqa: E402
    return S


def _rel(p):
    return os.path.relpath(p, ROOT)


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ---------------------------------------------------------------- code locations (AST)
def _functions(path):
    src = open(os.path.join(ROOT, path), encoding="utf-8").read()
    lines = src.splitlines()
    out = {}
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name not in out:
            out[n.name] = (n.lineno, n.end_lineno, n)
    return src, lines, out


def locate(gates):
    """(file, function, anchor) ⟶ line of the anchor inside the function; missing ⟶ build error."""
    cache, errors = {}, []
    for g in gates:
        f = g["file"]
        if f not in cache:
            cache[f] = _functions(f)
        src, lines, fn = cache[f]
        if g["function"] not in fn:
            errors.append(f"{g['id']}: function {g['function']} not in {f}")
            g["line"] = None
            continue
        a, b, _ = fn[g["function"]]
        hit = [i for i in range(a - 1, b) if g["anchor"] in lines[i]]
        if not hit:
            errors.append(f"{g['id']}: anchor not found in {f}::{g['function']}")
            g["line"] = None
            continue
        g["line"] = hit[0] + 1
        g["function_lines"] = [a, b]
    return errors, cache


def completeness(gates, cache):
    """Every reject code / bare `return None` of `analyze_ticker` and every required function must be inventoried."""
    errors = []
    _, _, fn = cache["Super_stock.py"]
    node = fn["analyze_ticker"][2]
    codes, bare = [], 0
    for n in ast.walk(node):
        if isinstance(n, ast.Return):
            v = n.value
            if isinstance(v, ast.Call) and getattr(v.func, "id", "") == "_reject":
                a = v.args[0]
                if isinstance(a, ast.Constant):
                    codes.append(str(a.value))
                elif isinstance(a, ast.JoinedStr):
                    codes.append("".join(str(x.value) for x in a.values if isinstance(x, ast.Constant)))
            elif v is None or (isinstance(v, ast.Constant) and v.value is None):
                bare += 1
    inv = [c for g in gates for c in g.get("reject_codes") or []]
    for c in codes:
        if not any(c == x or c.startswith(x) for x in inv):
            errors.append(f"reject code not inventoried: {c}")
    silent = [g["id"] for g in gates if g["function"] == "analyze_ticker" and "return None" in g.get("on_fail", "")]
    if bare != len(silent):
        errors.append(f"bare `return None` paths in analyze_ticker: {bare} vs inventoried {len(silent)} ({silent})")
    funcs = {g["function"] for g in gates}
    for f in REQUIRED_FUNCS:
        if f not in funcs:
            errors.append(f"required gate function not inventoried: {f}")
    return errors, codes, bare


# ---------------------------------------------------------------- four-dimension audit (origin · justification · role · fidelity)
REJECT_ROLES = ("HARD_REJECTION", "OWNER_TRADING_ELIGIBILITY", "DATA_QUALITY", "OPS_SAFETY")
T_FIELDS = ("key", "concept", "window", "basis", "data_at_decision", "pipeline_point", "hard_why", "number_origin")


def _refs(a):
    r = list(a.get("origin_refs") or []) + list(a.get("concept_refs") or []) + list(a.get("hardness_refs") or [])
    for t in a.get("thresholds") or []:
        r += list(t.get("refs") or [])
    return r


def audit_errors(prov):
    """Every evidence item is verified against its file; every gate's justification must be the one its evidence derives
    (`gate_audit.derive_justification`) — absence, comments and inherited records never count; origin and fidelity may not claim
    more than their references; every active rejecting gate states the provenance of each of its numbers."""
    reg = prov.get("evidence_registry") or {}
    errs, texts, cited = [], {}, set()
    for k, e in sorted(reg.items()):
        if e.get("kind") not in GA.KINDS or e.get("stance") not in GA.STANCES:
            errs.append(f"evidence {k}: kind/stance {e.get('kind')}/{e.get('stance')} not in vocabulary")
        v = e.get("verify") or {}
        f, q = v.get("file"), v.get("contains")
        if not f or not q:
            errs.append(f"evidence {k}: no verify spec")
            continue
        if f not in texts:
            p = os.path.join(ROOT, f)
            texts[f] = open(p, encoding="utf-8").read() if os.path.exists(p) else None
        if texts[f] is None:
            errs.append(f"evidence {k}: file missing {f}")
        elif q not in texts[f]:
            errs.append(f"evidence {k}: quote not found in {f}")
    for g in prov["gates"]:
        a = g.get("audit")
        if not isinstance(a, dict):
            errs.append(f"{g['id']}: no audit dimensions")
            continue
        for r in _refs(a):
            cited.add(r)
            if r not in reg:
                errs.append(f"{g['id']}: evidence {r} not in registry")
        if a.get("impl_role") not in GA.IMPL_ROLE:
            errs.append(f"{g['id']}: impl_role {a.get('impl_role')} not in vocabulary")
        e = GA.check_origin(a, reg)
        if e:
            errs.append(f"{g['id']}: {e}")
        j, _ = GA.derive_justification(a, reg)
        if a.get("justification") != j:
            errs.append(f"{g['id']}: justification {a.get('justification')} but evidence derives {j}")
        e = GA.check_fidelity(a, reg, j)
        if e:
            errs.append(f"{g['id']}: {e}")
        keys = set()
        for t in a.get("thresholds") or []:
            keys.add(t.get("key"))
            if t.get("number_origin") not in GA.NUMBER_ORIGIN:
                errs.append(f"{g['id']}: threshold {t.get('key')} number_origin {t.get('number_origin')} not in vocabulary")
            if any(not str(t.get(x) or "").strip() for x in T_FIELDS):
                errs.append(f"{g['id']}: threshold {t.get('key')} lacks a provenance field")
        if g.get("status") != "INACTIVE" and a.get("impl_role") in REJECT_ROLES:
            for k in g.get("config_keys") or []:
                if k not in keys:
                    errs.append(f"{g['id']}: active rejecting gate has no threshold record for {k}")
    for k in sorted(set(reg) - cited):
        errs.append(f"evidence {k}: never cited")
    return errs


# ---------------------------------------------------------------- live values and production counts
def _fmt(v):
    if isinstance(v, bool) or v is None or isinstance(v, str):
        return v
    try:
        fv = float(v)
    except (TypeError, ValueError):
        return str(v)
    return int(fv) if fv == int(fv) and abs(fv) < 1e15 else round(fv, 4)


def snapshot():
    log = json.load(open(os.path.join(ROOT, "reject_log.json"), encoding="utf-8"))
    days = []
    for e in log:
        walls = e.get("walls") or {}
        full = e.get("walls_n") or {}            # the stored name lists are sampled (400); walls_n holds the full counts
        days.append({"date": e.get("date"),
                     "walls": {k: int(full.get(k, len(v) if isinstance(v, list) else v)) for k, v in walls.items()},
                     "sampled": list(e.get("sampled") or [])})
    snap = {"source": "reject_log.json (working tree)", "source_sha256": _sha(os.path.join(ROOT, "reject_log.json")),
            "days": days}
    json.dump(snap, open(SNAP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"snapshot: {len(days)} days")


def counts_for(g, snap):
    codes = g.get("reject_codes") or []
    if not codes or not snap:
        return None
    per = []
    for d in snap["days"]:
        n = sum(v for k, v in d["walls"].items() if any(k == c or k.startswith(c) for c in codes))
        per.append((d["date"], n))
    vals = sorted(n for _, n in per)
    med = vals[len(vals) // 2] if vals else 0
    return {"days": len(per), "median_per_day": med, "max_per_day": max(vals) if vals else 0,
            "last_day": per[-1][0] if per else "", "last_day_count": per[-1][1] if per else 0}


# ---------------------------------------------------------------- first exclusion (frozen bars, production code)
def _load_rank():
    bars = json.load(gzip.open(os.path.join(DATA, "rank", "bars.json.gz"), "rt", encoding="utf-8"))["daily"]
    rows = {}
    with gzip.open(os.path.join(DATA, "rank", "rows.csv.gz"), "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows[(r["date"], r["symbol"])] = r
    splits = json.load(open(os.path.join(DATA, "rank", "splits.json"), encoding="utf-8"))["splits"]
    ub = json.load(gzip.open(os.path.join(DATA, "universe_bars.json.gz"), "rt", encoding="utf-8"))
    ubars = ub.get("daily") or ub.get("bars") or {}
    uni = json.load(open(os.path.join(DATA, "rank", "universe.json"), encoding="utf-8"))
    return bars, rows, splits, ubars, uni


def _frame(rows):
    import pandas as pd
    df = pd.DataFrame(rows, columns=["Date", "Open", "High", "Low", "Close", "Volume"])
    df["Date"] = pd.to_datetime(df["Date"])
    return df.set_index("Date")


def _reason_gate(why):
    m = {"M1_سعر": "M1", "M2_هبوط_فوق_97": "M2_CEIL", "M2_هبوط_تحت_40": "M2_FLOOR", "M2_hi52": "M2_FLOOR",
         "M3_انفجار_تحت_60": "M3", "M4_base_واسعة": "M4_RANGE", "M4_base_lo": "M4_RANGE", "M4_انفجر_فعلاً": "M4_RISE",
         "M5_سيولة": "M5", "M10_RSI_ما_تشبّع": "RSI_OS", "M10_RSI_فات_القطار": "RSI_NOW", "M_لا_مستوى_مختبر": "ANCHOR",
         "MIN_BARS": "DEPTH"}
    if why in m:
        return m[why]
    for p, n in (("نواقص_فوق", "SOFT"), ("RR+نواقص", "SOFT"), ("نقاط_تحت", "SCORE"), ("بعيد_عن_الدخول", "NEAR")):
        if str(why).startswith(p):
            return n
    return str(why)


def run_once(S, sym, df, neutral):
    """production `analyze_ticker`; neutralised gates use relaxed CONFIG values restored in `finally`."""
    saved, tl = {}, S.tested_level
    for gname in neutral:
        for k, v in NEUTRAL[gname].items():
            saved[k] = S.CONFIG[k]
            S.CONFIG[k] = v
    if "ANCHOR" in neutral:
        def _tl(d, lookback=30, tol=0.015, min_touches=2):
            r = tl(d, lookback, tol, min_touches)
            if r:
                return r
            return {"level": round(float(d.tail(int(lookback))["Low"].min()), 4), "touches": 1}
        S.tested_level = _tl
    for k in ("BT_SPLIT_REF_M2", "BT_SPLIT_AWARE_M4", "BT_M4_POST_SPLIT", "BT_STABILITY_GATE"):
        saved.setdefault(k, S.CONFIG.get(k))
        S.CONFIG[k] = 0 if k != "BT_STABILITY_GATE" else ""
    S._BT_SPLITS_CTX = None
    S._REJECT_REASONS.pop(sym, None)
    try:
        if len(df) < S.CONFIG["MIN_BARS"]:
            return "REJECT", "MIN_BARS"
        with contextlib.redirect_stdout(io.StringIO()):
            try:
                r = S.analyze_ticker(sym, df)
            except Exception as e:                                # noqa: BLE001
                return "ERROR", type(e).__name__
        return ("PASS", "") if r else ("REJECT", S._REJECT_REASONS.get(sym, "?"))
    finally:
        for k, v in saved.items():
            S.CONFIG[k] = v
        S.tested_level = tl


def metrics(S, df, rsplits, T):
    """the quantities each gate reads, with the production formulas; plus the post-split reference (artefact test)."""
    import math
    c = df["Close"].values
    high, low, vol, close = df["High"], df["Low"], df["Volume"], df["Close"]
    price = float(c[-1])
    hi52 = float(high.tail(252).max())
    drop = (1.0 - price / hi52) * 100.0 if hi52 > 0 else None
    sp = [(d, r) for d, r in rsplits if d < T]
    psh = None
    if sp:
        import pandas as pd
        try:
            psh = S._post_split_high(high.tail(252), pd.Series([r for _, r in sp], index=pd.to_datetime([d for d, _ in sp])),
                                     df.index[-1])
        except Exception:                                         # noqa: BLE001
            psh = None
    drop_ps = ((1.0 - price / psh) * 100.0) if psh else None
    bw = int(S.CONFIG["BASE_WINDOW"])
    base_hi, base_lo = float(high.tail(bw).max()), float(low.tail(bw).min())
    base_range = (base_hi / base_lo - 1.0) * 100.0 if base_lo > 0 else None
    first_base = str(df.index[-bw].date()) if len(df) >= bw else ""
    split_in_base = bool([d for d, _ in sp if d >= first_base])
    best_spike, n_spikes = S.spike_info(c, exclude_last=bw)
    gain5 = (c[-1] / c[-6] - 1.0) * 100.0 if len(c) > 6 else None
    dvol = float((close * vol).tail(20).mean())
    rs = S.rsi(close)
    tl = S.tested_level(df)
    last_split = sp[-1][0] if sp else ""
    # a reverse split left UNADJUSTED in the series shows as a jump ≈ 1/ratio between the close before and the open on the
    # split date; an adjusted series is continuous. Only an unadjusted split is a data artefact (frame choice is not).
    unadj = []
    idx = [str(x.date()) for x in df.index]
    for d, r in sp:
        k = next((i for i, x in enumerate(idx) if x >= d), None)
        if k is None or k == 0 or not (r > 0):
            continue
        c0, o1 = float(df["Close"].iloc[k - 1]), float(df["Open"].iloc[k])
        if c0 > 0 and o1 / c0 > 0.65 / r:
            unadj.append(d)
    return {"nbars": len(df), "last_bar": str(df.index[-1].date()), "price": round(price, 4), "drop_adj_pct": _fmt(drop),
            "drop_post_split_pct": _fmt(drop_ps), "base_range_pct": _fmt(base_range), "reverse_split_in_base": split_in_base,
            "best_spike_pct": _fmt(best_spike), "gain5_pct": _fmt(gain5), "dollar_vol_20": _fmt(dvol if math.isfinite(dvol) else None),
            "rsi_min_25": _fmt(float(rs.tail(int(S.CONFIG["RSI_OS_LOOKBACK"])).min())), "rsi_now": _fmt(float(rs.iloc[-1])),
            "tested_touches": (int(tl["touches"]) if tl else 1), "last_reverse_split": last_split,
            "unadjusted_splits": " ".join(unadj)}


def _value_of(gname, m, S):
    C = S.CONFIG
    v = {"M1": (m["price"], f"MIN_PRICE {_fmt(C['MIN_PRICE'])}"),
         "M2_CEIL": (m["drop_adj_pct"], f"MAX_DROP_PCT {_fmt(C['MAX_DROP_PCT'])}"),
         "M2_FLOOR": (m["drop_adj_pct"], f"MIN_DROP_FLOOR {_fmt(C['MIN_DROP_FLOOR'])}"),
         "M3": (m["best_spike_pct"], f"PRIOR_SPIKE_FLOOR {_fmt(C['PRIOR_SPIKE_FLOOR'])}"),
         "M4_RANGE": (m["base_range_pct"], f"BASE_RANGE_MAX_PCT {_fmt(C['BASE_RANGE_MAX_PCT'])}"),
         "M4_RISE": (m["gain5_pct"], f"RECENT_RISE_BLOCK_PCT {_fmt(C['RECENT_RISE_BLOCK_PCT'])}"),
         "M5": (m["dollar_vol_20"], f"MIN_DOLLAR_VOL {_fmt(C['MIN_DOLLAR_VOL'])}"),
         "RSI_OS": (m["rsi_min_25"], f"RSI_OS_HARD {_fmt(C['RSI_OS_HARD'])}"),
         "RSI_NOW": (m["rsi_now"], f"RSI_NOW_HARD {_fmt(C['RSI_NOW_HARD'])}"),
         "ANCHOR": (m["tested_touches"], "≥2 independent touches of the 30-bar low (±1.5%)"),
         "DEPTH": (m["nbars"], f"MIN_BARS {_fmt(C['MIN_BARS'])}")}
    return v.get(gname, ("", ""))


def classify(first, m, S):
    """provenance class of the first wall for THIS case (an adjustment artefact overrides the gate's own class)."""
    C = S.CONFIG
    if first == "M2_CEIL" and m["drop_post_split_pct"] is not None and \
            C["MIN_DROP_FLOOR"] <= m["drop_post_split_pct"] <= C["MAX_DROP_PCT"]:
        return "DATA_OR_ADJUSTMENT_ARTIFACT", "post-split drop is inside the M2 band; the adjusted drop exceeds the ceiling only because of reverse-split adjustment"
    if first == "M2_CEIL" and m["drop_post_split_pct"] is not None and m["drop_post_split_pct"] < C["MIN_DROP_FLOOR"]:
        return None, (f"post-split drop {m['drop_post_split_pct']}% is below the floor {_fmt(C['MIN_DROP_FLOOR'])}: excluded in "
                      "either frame — the ceiling name is an adjustment misnomer, not the decisive reason")
    if m.get("unadjusted_splits") and first in ("M2_CEIL", "M2_FLOOR", "M3", "M4_RANGE", "M4_RISE", "ANCHOR"):
        return "DATA_OR_ADJUSTMENT_ARTIFACT", f"reverse split(s) {m['unadjusted_splits']} left unadjusted in the series"
    if first == "M4_RANGE" and m["reverse_split_in_base"]:
        return None, ("a reverse split falls inside the 15-bar window but the series is adjusted at that date (no jump): "
                      "the range is genuine price action, not an adjustment artefact")
    return None, ""


EVIDENCE_NEEDED = {
    "UNIVERSE": "listing venue of the symbol at T and an owner decision on the universe scope",
    "DEPTH": "Faisal's frame for short post-split histories (TG_1807/TG_1811 describe it); a prereg for a post-split depth rule",
    "M2_CEIL": "closed axis (owner «خلّ السقف»); only the owner can reopen — evidence would be Faisal's own drop reference at T",
    "M4_RANGE": "a Faisal statement of a base-width limit (none found); for artefacts, a split-aware window already exists as a research arm",
    "M3": "a Faisal statement on the size/window of the prior explosion (the «100٪» text is about the target)",
    "RSI_NOW": "his RSI reading at T (closed RSI axis)",
    "ANCHOR": "frozen by the H6 control-pool dependency and the perf verdict; prospective H6 evidence is the admissible route",
    "PASS": "point-in-time float / borrow / short at T (not archived for history) to replay the post-scan gates",
}


def first_exclusion(S):
    bars, rows, splits, ubars, uni = _load_rank()
    eps = list(csv.DictReader(open(os.path.join(OUT, "gt_episodes.csv"), encoding="utf-8")))
    cases = [(e["episode_id"], e["ticker"], e["rank_T_e"], e["defensible_ref"], e["eligibility"], e["rank_evaluable"])
             for e in eps]
    cases += [(f"{t}_{d}", t, d, ref, "ANCHOR_CASE", "1") for t, d, ref, _ in EXTRA_CASES]
    rc = {}
    p = os.path.join(OUT, "rank_cases.csv")
    if os.path.exists(p):
        for r in csv.DictReader(open(p, encoding="utf-8")):
            rc[r["episode_id"]] = r
    out = []
    nas = set(uni.get("symbols") or [])
    for eid, sym, T, ref, elig, rkev in cases:
        src_rows = bars.get(sym)
        in_uni = sym in nas
        src = "rank" if src_rows is not None else ("universe_test" if sym in ubars else "")
        rr = src_rows if src_rows is not None else ubars.get(sym)
        hist = [r for r in (rr or []) if r[0] < T]
        rsp = sorted((d, float(x)) for d, x in (splits.get(sym) or []) if float(x) < 1.0)
        rec = {"case": eid, "ticker": sym, "T": T, "source_ref": ref, "eligibility": elig, "in_universe": int(in_uni),
               "bars_source": src}
        if not hist:
            rec.update(first_gate="NO_BARS", chain="", classification="UNKNOWN_OR_UNSUPPORTED")
            out.append(rec)
            continue
        df = _frame(hist)
        m = metrics(S, df, rsp, T)
        chain, neutral = [], []
        if not in_uni:
            chain.append(("UNIVERSE", "not in nasdaqlisted snapshot"))
        res, why = run_once(S, sym, df, ())
        first_g = _reason_gate(why) if res == "REJECT" else res
        chain_g = first_g
        steps = 0
        while res == "REJECT" and steps < 10:
            gname = _reason_gate(why)
            chain.append((gname, why))
            if gname not in NEUTRAL or gname in neutral:
                break
            neutral.append(gname)
            res, why = run_once(S, sym, df, tuple(neutral))
            steps += 1
        tail = "PASS" if res == "PASS" else (res if res != "REJECT" else "")
        fr = rows.get((T, sym)) or {}
        g0 = chain[0][0] if chain else "PASS"
        val, thr = _value_of(g0, m, S) if g0 not in ("PASS", "UNIVERSE") else ("", "")
        cls, why_cls = classify(g0, m, S)
        rec.update(first_gate=g0, first_gate_id=GATE_ID.get(g0, g0), first_reason=(chain[0][1] if chain else ""),
                   value=val, threshold=thr, frozen_bot_gate=fr.get("bot_gate", ""), frozen_bot_res=fr.get("bot_res", ""),
                   replay_matches_frozen=(("" if not fr else int((fr.get("bot_res") == "PASS" and chain_g == "PASS")
                                                               or (fr.get("bot_gate") == chain_g)))),
                   chain=" → ".join(gname for gname, _ in chain) + (f" → {tail}" if tail else ""),
                   never_ran=_never_ran(g0), case_artifact=cls or "", case_artifact_reason=why_cls,
                   bot_operational_list=(rc.get(eid, {}).get("bot_op_exact", "") if eid in rc else ""),
                   post_scan_gates=("M13/M14/borrow/DQ/capacity: point-in-time UNKNOWN (inputs not archived)" if g0 == "PASS" else ""),
                   evidence_needed=EVIDENCE_NEEDED.get(g0, ""))
        rec.update({k: m[k] for k in ("nbars", "last_bar", "price", "drop_adj_pct", "drop_post_split_pct", "base_range_pct",
                                      "reverse_split_in_base", "best_spike_pct", "rsi_now", "tested_touches", "last_reverse_split",
                                      "unadjusted_splits")})
        out.append(rec)
    return out


ORDER = ["UNIVERSE", "DEPTH", "M1", "M2_CEIL", "M2_FLOOR", "M3", "M4_RANGE", "M4_RISE", "M5", "RSI_OS", "RSI_NOW", "SOFT",
         "NEAR", "SCORE", "ANCHOR", "RR", "M13/M14/TIER", "DQ", "CAPACITY/FILL", "BORROW", "ENTRY_STATUS"]


def _never_ran(g0):
    if g0 == "PASS":
        return ""
    i = ORDER.index(g0) if g0 in ORDER else -1
    return " · ".join(ORDER[i + 1:]) if i >= 0 else ""


# ---------------------------------------------------------------- build
FX_COLS = ["case", "ticker", "T", "source_ref", "eligibility", "in_universe", "bars_source", "first_gate", "first_gate_id",
           "first_reason", "value", "threshold", "frozen_bot_res", "frozen_bot_gate", "replay_matches_frozen", "chain",
           "never_ran", "case_artifact", "case_artifact_reason", "bot_operational_list", "post_scan_gates", "evidence_needed",
           "nbars", "last_bar", "price", "drop_adj_pct", "drop_post_split_pct", "base_range_pct", "reverse_split_in_base",
           "best_spike_pct", "rsi_now", "tested_touches", "last_reverse_split", "unadjusted_splits", "classification"]
INV_COLS = ["order", "id", "system", "stage", "file", "function", "line", "role", "kind", "blocks_downstream", "origin",
            "justification", "impl_role", "fidelity", "contradicted", "legacy_label_pr598", "confidence", "artifact_risk", "status", "status_ref", "condition", "config", "on_pass", "on_fail",
            "on_unavailable", "on_malformed", "inputs", "provider", "timestamp_rule", "prod_median_per_day",
            "prod_last_day_count", "affected_cases", "chain_cases", "evidence_units", "next_action", "repro"]


def build():
    S = _S()
    prov = json.load(open(PROV, encoding="utf-8"))
    gates = prov["gates"]
    errors = []
    ids = [g["id"] for g in gates]
    if len(ids) != len(set(ids)):
        errors.append("duplicate gate ids")
    for g in gates:
        if g["provenance"] not in CATS:
            errors.append(f"{g['id']}: provenance {g['provenance']} not one of the six categories")
    e1, cache = locate(gates)
    e2, codes, bare = completeness(gates, cache)
    errors += e1 + e2 + audit_errors(prov)
    reg = prov.get("evidence_registry") or {}
    for g in gates:
        a = g.get("audit") or {}
        j, det = GA.derive_justification(a, reg)
        a["derived_justification"], a["contradicted"], a["support"] = j, det["contradicted"], det["components"]
        for t in a.get("thresholds") or []:
            if "value" not in t:
                if t.get("key") not in S.CONFIG:
                    errors.append(f"{g['id']}: threshold {t.get('key')} has no value and is not a CONFIG key")
                t["value"] = _fmt(S.CONFIG.get(t.get("key")))
    snap = json.load(open(SNAP, encoding="utf-8")) if os.path.exists(SNAP) else None
    fx = first_exclusion(S)
    for g in gates:
        g["config"] = {k: _fmt(S.CONFIG.get(k)) for k in g.get("config_keys") or []}
        g["production_counts"] = counts_for(g, snap)
        g["affected_cases"] = [r["case"] for r in fx if r.get("first_gate_id") == g["id"]]
        g["chain_cases"] = [r["case"] for r in fx if g["id"] in {GATE_ID.get(x.strip(), x.strip()) for x in (r.get("chain") or "").split("→")}
                            and r.get("first_gate_id") != g["id"]]
    for r in fx:
        gid = r.get("first_gate_id")
        gg = next((g for g in gates if g["id"] == gid), None)
        r["classification"] = r.get("case_artifact") or (gg["audit"]["justification"] if gg else ("PASS" if r.get("first_gate") == "PASS" else "UNKNOWN"))
    def by(field, vocab):
        return {c: sum(1 for g in gates if (g.get("audit") or {}).get(field) == c) for c in vocab}
    summary = {"gates": len(gates), "by_origin": by("origin", GA.ORIGIN), "by_justification": by("justification", GA.JUSTIFICATION),
               "by_impl_role": by("impl_role", GA.IMPL_ROLE), "by_fidelity": by("fidelity", GA.FIDELITY),
               "contradicted": [g["id"] for g in gates if (g.get("audit") or {}).get("contradicted")],
               "legacy_by_label": {c: sum(1 for g in gates if g["provenance"] == c) for c in CATS},
               "reject_codes_in_analyze_ticker": len(codes), "bare_none_returns": bare,
               "cases": len(fx), "first_gate_counts": _count(r["first_gate"] for r in fx),
               "replay_mismatches": [r["case"] for r in fx if r.get("replay_matches_frozen") == 0],
               "chain_presence": _count(x.strip() for r in fx for x in (r.get("chain") or "").split("→")
                                        if x.strip() and x.strip() != "PASS"),
               "errors": errors,
               "inputs": {"provenance_sha256": _sha(PROV), "snapshot_sha256": (_sha(SNAP) if snap else ""),
                          "rank_bars_sha256": _sha(os.path.join(DATA, "rank", "bars.json.gz")),
                          "rank_rows_sha256": _sha(os.path.join(DATA, "rank", "rows.csv.gz"))}}
    summary["pool_question"] = pool_question(S)
    if summary["pool_question"] and not summary["pool_question"]["rows_sha_ok"]:
        errors.append("gate_pool_evidence.json: rows_sha256 does not match its rows")
    inv = {"schema": 2, "summary": summary, "categories": CATS, "legacy_label": prov.get("legacy_label", ""),
           "audit_vocab": {"origin": GA.ORIGIN, "justification": GA.JUSTIFICATION, "impl_role": GA.IMPL_ROLE, "fidelity": GA.FIDELITY,
                           "number_origin": GA.NUMBER_ORIGIN, "evidence_kinds": GA.KINDS},
           "evidence_registry": reg, "gates": gates}
    return inv, fx


def _wilson(k, n, z=1.96):
    if not n:
        return None, None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return round(100 * (c - h), 1), round(100 * (c + h), 1)


def pool_question(S):
    """§7 of the owner follow-up: would the next-ranked names beyond the fill rounds pass the owner gates? Read-only, from the
    frozen point-in-time evidence (`data/gate_pool_evidence.json` · `data/gate_fill_observations.json`). Unknown availability is
    never counted as passing; the answer is NOT DETERMINABLE unless the ranked names and their availability exist."""
    pe = os.path.join(DATA, "gate_pool_evidence.json")
    fo = os.path.join(DATA, "gate_fill_observations.json")
    if not (os.path.exists(pe) and os.path.exists(fo)):
        return None
    ev = json.load(open(pe, encoding="utf-8"))
    obs = json.load(open(fo, encoding="utf-8"))
    thr = float(S.CONFIG.get(ev["threshold_key"]))
    rows = ev["harvest"]["rows"]
    sha = hashlib.sha256(json.dumps(rows, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    coh = {}
    for c in ("control_market", "bot_selected", "bot_pullback"):
        k, n, unk = GA.pass_rate(rows, c, thr)
        coh[c] = {"k": k, "n": n, "ci": _wilson(k, n), "unknown": unk}
    ex = sum(o["filled"] + o["borrow_ejected"] + o["fl_ejected"] for o in obs["runs"])
    fill = sum(o["filled"] for o in obs["runs"])
    r9 = ev["run_2026_10_09"]
    ex9 = len(r9["added"]) + len(r9["borrow_ejected"])
    return {"threshold": thr, "rows_sha_ok": sha == ev["harvest"]["rows_sha256"], "cohorts": coh,
            "examined": {"k": fill, "n": ex, "ci": _wilson(fill, ex)},
            "run_1009": {"after_dq": r9["after_dq"], "examined": ex9, "unexamined_le": r9["after_dq"] - ex9,
                         "ejected_n": len(r9["borrow_ejected"]),
                         "ejected_all_above": all(float(x["shares_available"]) > thr for x in r9["borrow_ejected"])},
            "determinable": bool(ev.get("pool_names_logged")), "why_not_logged": ev["why_not_logged"]}


def _count(it):
    d = {}
    for x in it:
        d[x] = d.get(x, 0) + 1
    return dict(sorted(d.items(), key=lambda kv: (-kv[1], kv[0])))


def render(inv, fx):
    j = json.dumps(inv, ensure_ascii=False, indent=1, default=str) + "\n"
    s = io.StringIO()
    w = csv.writer(s, lineterminator="\n")
    w.writerow(INV_COLS)
    for g in sorted(inv["gates"], key=lambda g: (g["order"], g["id"])):
        pc = g.get("production_counts") or {}
        a = g.get("audit") or {}
        w.writerow([g["order"], g["id"], g["system"], g["stage"], g["file"], g["function"], g.get("line"), g["role"], g["kind"],
                    int(bool(g["blocks_downstream"])), a.get("origin"), a.get("justification"), a.get("impl_role"), a.get("fidelity"),
                    int(bool(a.get("contradicted"))), g["provenance"], g["confidence"], g["artifact_risk"], g["status"],
                    g["status_ref"], g["condition"], json.dumps(g["config"], ensure_ascii=False), g["on_pass"], g["on_fail"],
                    g["on_unavailable"], g["on_malformed"], g["inputs"], g["provider"], g["timestamp_rule"],
                    pc.get("median_per_day", ""), pc.get("last_day_count", ""), " ".join(g["affected_cases"]),
                    " ".join(g["chain_cases"]), " | ".join(e["source_unit"] for e in g["evidence"]), g["next_action"], g["repro"]])
    c = s.getvalue()
    s2 = io.StringIO()
    w2 = csv.writer(s2, lineterminator="\n")
    w2.writerow(FX_COLS)
    for r in fx:
        w2.writerow([r.get(k, "") for k in FX_COLS])
    return j, c, s2.getvalue(), report(inv, fx)


# the owner's «13 gates» shown by hand_check/analyze_one (main f6afbb81) — display kind before and after 2026-10-09;
# the current kinds are enforced by the suite locks GPV4/GPV5 (behavioural), not by this table.
HC13 = [("السعر", "M1_PRICE", "hard", "hard"), ("الهبوط ضمن الأرضية–السقف", "M2_FLOOR / M2_CEIL", "hard", "hard"),
        ("انفجار سابق", "M3_FLOOR", "hard", "hard"), ("قاعدة ضيقة ولم ينفجر", "M4_RANGE / M4_RISE", "hard", "hard"),
        ("سيولة", "M5_DOLLAR_VOL", "hard", "hard"), ("توافق الفريمات", "SOFT_M6_TF", "info", "info"),
        ("نمط شمعة انعكاسي", "SOFT_M7_PATTERN", "soft", "soft"), ("فجوة-هدف فوق السعر", "SOFT_M9_GAP_ABOVE", "soft", "soft"),
        ("RSI تشبّع والآن", "M10_RSI_OS / M10_RSI_NOW", "hard", "hard"), ("تقاطع MACD", "SOFT_M11_MACD", "soft", "soft"),
        ("السعر قرب متوسطه 30/50", "SOFT_M12_EMA", "soft", "soft"), ("الشورت تحت 40K", "M13_SHORT", "hard", "soft"),
        ("الفلوت تحت 50M", "M14_FLOAT", "hard", "hard"), ("مِرساة: قاعٌ مُختبَر", "ANCHOR_TWO_TOUCH", "absent", "hard"),
        ("المتاح للاقتراض 20K أو أقل", "BORROW_AVAIL", "absent", "hard")]


def _why(a):
    sup = a.get("support") or {}
    miss = [k for k, v in sup.items() if not v]
    return ("unsupported: " + ", ".join(miss)) if miss else "—"


def _q(gates, pred):
    return [g["id"] for g in gates if pred(g)]


def report(inv, fx):
    G = sorted(inv["gates"], key=lambda g: (g["order"], g["id"]))
    sm = inv["summary"]
    hard = [g for g in G if g["role"] == "reject" and g["status"] not in ("INACTIVE",) and g["blocks_downstream"]
            and g["kind"] in ("hard", "owner_policy", "coverage_guard", "ops_safety")]
    L = ["# 🚪🧭 Gate provenance report — generated (`python3 faisal_engine/gate_inventory.py`)", "",
         "Research only. Generated from `faisal_engine/data/gate_provenance.json` (curated evidence), the code (AST anchors, live",
         "production configuration `FAISAL_ONLY=1`), a frozen snapshot of `reject_log.json`, and the frozen ranking bars. "
         "Every number below is produced by the builder; `--check` regenerates and compares. Line numbers are as of the build "
         "and move with edits (the check verifies each anchor still sits inside its function).", "",
         f"**{sm['gates']} gates inventoried** · reject codes in `analyze_ticker`: {sm['reject_codes_in_analyze_ticker']} (all inventoried) · "
         f"silent `return None` paths: {sm['bare_none_returns']} (all inventoried) · build errors: {len(sm['errors'])}", "",
         "## 1. The decision questions", ""]
    def ids(pred):
        x = _q(G, pred)
        return ", ".join(f"`{i}`" for i in x) or "none"
    hard_ids = {g["id"] for g in hard}
    A = {g["id"]: g.get("audit") or {} for g in G}
    rej = [g["id"] for g in G if g["status"] != "INACTIVE" and A[g["id"]].get("impl_role") in ("HARD_REJECTION", "OWNER_TRADING_ELIGIBILITY")]

    def jl(ids_, just):
        x = [f"`{i}`" for i in ids_ if A[i].get("justification") in just]
        return ", ".join(x) or "none"
    allid = [g["id"] for g in G]
    L += [f"1. **Active rejecting gates with direct Faisal-source support (concept, every number and the hard role):** "
          f"{jl(rej, ('DIRECT_SOURCE_SUPPORT',))}.",
          f"2. **Active rejecting gates with partial support only** (some part — the concept, a number or the hard role — is "
          f"supported, but not every part by one kind of evidence; a supported concept does not support the exact threshold): "
          f"{jl(rej, ('PARTIAL_OR_CONCEPT_ONLY_SUPPORT',))}.",
          f"3. **Justified as engineering guards** (documented operational invariant or tested reliability requirement): "
          f"{jl(allid, ('DOCUMENTED_OPERATIONAL_INVARIANT', 'TESTED_RELIABILITY_REQUIREMENT'))} · **guards whose concept is supported "
          f"but whose number is not:** {jl([i for i in allid if A[i].get('impl_role') in ('DATA_QUALITY', 'OPS_SAFETY')], ('PARTIAL_OR_CONCEPT_ONLY_SUPPORT',))} · "
          f"**explicit owner requirement** (owner policy — not Faisal's method): {jl(allid, ('EXPLICIT_OWNER_REQUIREMENT',))}.",
          f"4. **Possible data/adjustment/order artefacts or frame differences:** {ids(lambda g: str(g['artifact_risk']).startswith(('HIGH', 'MEDIUM', 'FRAME')))}; "
          f"cases whose first wall is an artefact: {', '.join(r['case'] for r in fx if r.get('case_artifact')) or 'none'}.",
          f"5. **Without supporting evidence (UNJUSTIFIED_BY_CURRENT_EVIDENCE or UNKNOWN):** "
          f"{jl(allid, ('UNJUSTIFIED_BY_CURRENT_EVIDENCE', 'UNKNOWN'))} — the absence of a Faisal source, a code comment or an "
          "inherited record is never read as support (`gate_audit.derive_justification`).",
          f"6. **Change the candidate set** (hard, active): {', '.join(f'`{g}`' for g in sorted(hard_ids, key=lambda i: next(x['order'] for x in G if x['id'] == i)))} · "
          f"**ranking only:** {ids(lambda g: g['role'] == 'rank')} · **display/readiness only:** {ids(lambda g: g['role'] == 'display')} · "
          f"**soft (count toward `SOFT_COUNT`):** {ids(lambda g: g['kind'] == 'soft')}.",
          f"7. **Contradicted by a Faisal source** (concept or number): {', '.join(f'`{i}`' for i in sm['contradicted']) or 'none'}.",
          "8. **Highest-value permitted next action:** see §5.", "",
          "## 2. Gate table (pipeline order) — four independent dimensions", "",
          "Origin = where the rule came from · justification = what currently supports the rule **as implemented** (derived from the "
          "evidence attached to its concept, to every number and, for rejecting roles, to the hard role) · role = what it does · "
          "fidelity = how it maps to Faisal's method. None of the four stands in for another.", "",
          "| # | gate | where (as of build) | role | origin | justification | fidelity | contradicted | status | live value | prod/day (median · 10-09) |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for g in G:
        pc = g.get("production_counts") or {}
        a = A[g["id"]]
        cfg = " · ".join(f"{k}={v}" for k, v in g["config"].items()) or "—"
        L.append(f"| {g['order']} | `{g['id']}` | `{g['file']}::{g['function']}` L{g.get('line')} | {a.get('impl_role')} | "
                 f"{a.get('origin')} | {a.get('justification')} | {a.get('fidelity')} | {'yes' if a.get('contradicted') else ''} | "
                 f"{g['status']} | {cfg} | {(str(pc.get('median_per_day')) + ' · ' + str(pc.get('last_day_count'))) if pc else '—'} |")
    labs = list(sm["legacy_by_label"])
    L += ["", "## 2b. What changed against the single label of PR #598", "",
          "PR #598 gave each gate one label and read «no Faisal source» as an engineering guard. Rows = that label; columns = the "
          "justification derived now from the evidence (counts of gates).", "",
          "| PR #598 label | " + " | ".join(j.replace("_", " ").title() for j in GA.JUSTIFICATION) + " |",
          "|---|" + "---|" * len(GA.JUSTIFICATION)]
    for lab in labs:
        row = [sum(1 for g in G if g["provenance"] == lab and A[g["id"]].get("justification") == j) for j in GA.JUSTIFICATION]
        if sum(row):
            L.append(f"| {lab} | " + " | ".join(str(x) for x in row) + " |")
    moved = [g for g in G if (g["provenance"] == "OWNER_POLICY" and A[g["id"]].get("justification") != "EXPLICIT_OWNER_REQUIREMENT")
             or (g["provenance"] == "ENGINEERING_GUARD" and A[g["id"]].get("justification") not in
                 ("DOCUMENTED_OPERATIONAL_INVARIANT", "TESTED_RELIABILITY_REQUIREMENT"))
             or (g["provenance"].startswith(("DIRECT", "INFERRED")) and A[g["id"]].get("justification") == "DIRECT_SOURCE_SUPPORT")]
    L += ["", f"Gates whose old label does not hold ({len(moved)}): an owner label without a full owner requirement, or an "
          "engineering label without a documented invariant or a tested requirement.", "",
          "| gate | PR #598 label | origin now | justification now | change | why |", "|---|---|---|---|---|---|"]
    for g in moved:
        a = A[g["id"]]
        chg = ("support was overstated" if a.get("justification") in ("PARTIAL_OR_CONCEPT_ONLY_SUPPORT", "UNJUSTIFIED_BY_CURRENT_EVIDENCE", "UNKNOWN")
               else "re-attributed to the owner (not an engineering guard)")
        L.append(f"| `{g['id']}` | {g['provenance']} | {a.get('origin')} | {a.get('justification')} | {chg} | {a.get('note') or _why(a)} |")
    L += ["", "## 3. First exclusion per Faisal episode (frozen bars < T, production `analyze_ticker`)", "",
          "The cause is the **first** wall; the chain lists what would block next if each wall were neutralised (research only).",
          "", "| case | T | first wall | value · threshold | case class | chain | frozen replay | operational list |", "|---|---|---|---|---|---|---|---|"]
    for r in fx:
        L.append(f"| {r['case']} | {r['T']} | {r.get('first_gate', '')} | {r.get('value', '')} · {r.get('threshold', '')} | "
                 f"{r.get('classification', '')} | {r.get('chain', '')} | "
                 f"{({1: 'match', 0: 'MISMATCH'}.get(r.get('replay_matches_frozen'), '—'))} | {r.get('bot_operational_list', '') or '—'} |")
    L += ["", f"First-wall counts: {', '.join(f'{k} {v}' for k, v in sm['first_gate_counts'].items())} · replay mismatches against the frozen "
          f"ranking rows: {len(sm['replay_mismatches'])} · walls present anywhere in a chain: "
          f"{', '.join(f'{k} {v}' for k, v in sm['chain_presence'].items())} (of {sm['cases']} cases).", ""]
    notes = [r for r in fx if r.get("case_artifact_reason")]
    if notes:
        L += ["Case notes:"] + [f"- **{r['case']}** ({r['first_gate']}): {r['case_artifact_reason']}." for r in notes] + [""]
    L += ["## 3b. Exact thresholds of the active gates that reject, guard data or bound the list", "",
          "One row per number. **number origin** is where the exact value came from (Faisal source · owner · catalogue percentile · "
          "inferred · engineering default · inherited · experiment · unexplained) — independent of where the concept came from. "
          "A catalogue percentile is a number fitted to his chosen stocks under the owner's 2026-08-06 order, not a number he stated.", "",
          "| gate | key | live value | concept | window | measurement basis | data at decision | pipeline point | why hard (not soft) | number origin | evidence |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for g in G:
        a = A[g["id"]]
        if g["status"] == "INACTIVE" or not (a.get("thresholds") or a.get("impl_role") in REJECT_ROLES):
            continue
        for t in a.get("thresholds") or [{"key": "—", "value": "—", "concept": a.get("note") or "no numeric threshold", "window": "—",
                                          "basis": "—", "data_at_decision": "—", "pipeline_point": g["function"], "hard_why": "—",
                                          "number_origin": "—", "refs": a.get("concept_refs")}]:
            L.append(f"| `{g['id']}` | `{t['key']}` | {t.get('value')} | {t['concept']} | {t['window']} | {t['basis']} | "
                     f"{t['data_at_decision']} | {t['pipeline_point']} | {t['hard_why']} | {t['number_origin']} | "
                     f"{' · '.join(t.get('refs') or [])} |")
    L += [""]
    L += ["## 4. The manual tools (`hand_check.py` · `analyze_one.py`) — the owner's «13 gates»", "",
          "| displayed gate | inventory id | shown before | shown now | origin · justification |", "|---|---|---|---|---|"]
    for lab, gid, k0, k1 in HC13:
        L.append(f"| {lab} | `{gid}` | {k0} | {k1} | "
                 f"{' / '.join((A.get(x.strip()) or {}).get('origin', '?') + ' · ' + (A.get(x.strip()) or {}).get('justification', '?') for x in gid.split('/'))} |")
    L += ["",
          "Displayed gates now mirror the scanner: M1–M5 + RSI hard (catalog numbers), M6 info at 0, M7/M9/M11/M12 soft, "
          "**M13 soft** (was shown hard), **M14 hard**, **borrow hard** (was absent), **anchor hard** (was absent). "
          "The verdict line now equals the scanner's post-enrich decision (`post_enrich_verdict`): a stock removed by M14 or the "
          "borrow gate is no longer called «مؤهّل — كان سيدخل قائمة المراقبة». Below that verdict both tools now print five separate "
          "layers (`analyze_one.verdict_layers`, display only): ① Faisal's observed action and ② the source stage — UNKNOWN unless a "
          "source establishes them, never inferred from candles · ③ the technical assessment (the screener's technical gates, not a "
          "certificate of Faisal's method) · ④ owner-policy eligibility (float, borrow — unknown stays unknown) · ⑤ actionability "
          "(a technical «ready» is a price location, not an entry: without a confirmed trigger it is «not determined»). A name that "
          "passes technically and is removed by the float or borrow gate is no longer called «ليس سهم ارتكاز مؤهّلًا» in `hand_check`.", "",
          ]
    fo = os.path.join(DATA, "gate_fill_observations.json")
    if os.path.exists(fo):
        obs = json.load(open(fo, encoding="utf-8"))
        L += ["## 4b. Slot filling after the borrow gate (production logs, recorded in `data/gate_fill_observations.json`)", "",
              "| date | run | free slots | filled | rounds | ejected by borrow | examined | pool after DQ | unexamined (≤) |",
              "|---|---|---|---|---|---|---|---|---|"]
        tot_free = tot_fill = 0
        for o in obs["runs"]:
            ex = o["filled"] + o["borrow_ejected"] + o["fl_ejected"]
            un = (o["pool_after_dq"] - ex) if o.get("pool_after_dq") else None
            tot_free += o["space"]
            tot_fill += o["filled"]
            L.append(f"| {o['date']} | {o['run_id']} | {o['space']} | {o['filled']} | {o['rounds']} | {o['borrow_ejected']} | {ex} | "
                     f"{o.get('pool_after_dq') or '—'} | {un if un is not None else '—'} |")
        ej = sum(o["borrow_ejected"] for o in obs["runs"])
        exs = sum(o["filled"] + o["borrow_ejected"] + o["fl_ejected"] for o in obs["runs"])
        L += ["", f"Over these runs {tot_fill} of {tot_free} free slots were filled; the borrow gate ejected {ej} of {exs} examined "
              f"({100.0 * ej / exs:.0f}%). The «unexamined» column is an upper bound (names already held or stopped are excluded too); "
              "with the held ∪ stopped bound from the committed watchlist, the rounds cap is the verified cause on 2026-10-08 and "
              "2026-10-09 and the cause is not determinable on 2026-10-07 (pool size not logged) — `POOL_FUNNEL_REPORT.md` §3. "
              "Why these days: " + obs["why_these_days"] + ".", ""]
    pq = sm.get("pool_question")
    if pq:
        c, e, r9 = pq["cohorts"], pq["examined"], pq["run_1009"]

        def kn(x):
            return f"{x['k']} of {x['n']} ({100.0 * x['k'] / x['n']:.1f}% [{x['ci'][0]}, {x['ci'][1]}])"
        lo9, hi9 = r9["unexamined_le"] * e["k"] / e["n"], r9["unexamined_le"] * c["control_market"]["k"] / c["control_market"]["n"]
        L += ["## 4c. Would the next-ranked names pass the owner gates beyond the fill rounds? (read-only · existing point-in-time data)", "",
              ("**Answer: NOT DETERMINABLE from existing point-in-time data.** " if not pq["determinable"] else "**Answer: determinable.** ")
              + "Missing fields: ① the ranked post-DQ pool **by name** beyond the examined names — " + pq["why_not_logged"]
              + f" (2026-10-09: after DQ {r9['after_dq']} · examined {r9['examined']} · at most {r9['unexamined_le']} never examined); "
              "② `shares_available` **at decision time** for those names — never looked up (the rounds cap ends the lookups and "
              "ChartExchange serves ≈50 pages per runner) and not collected for them elsewhere: the harvest cohorts are the list, "
              "the pullback list, Faisal tickers and 20 random universe controls a day, and the Phase 6 ledger holds Faisal tickers "
              "and anchor-wall controls — a pool name could appear there only by chance, and without ① no match can be made. An "
              "unknown availability is not counted as passing.", "",
              f"Context, not an answer (borrow threshold {pq['threshold']:,.0f}): examined fill candidates passed {kn(e)} over the three "
              f"post-fix runs · the universe control cohort {kn(c['control_market'])} · names already on the list {kn(c['bot_selected'])} · "
              f"the pullback list {kn(c['bot_pullback'])}. Every one of the {r9['ejected_n']} names ejected on 2026-10-09 was above the "
              f"threshold: {'yes' if r9['ejected_all_above'] else 'NO'}.", "",
              f"Hypothesis (unmeasured): if the ≤{r9['unexamined_le']} unexamined names of 2026-10-09 passed like the examined names or "
              f"like the universe controls, ≈{lo9:.0f}–{hi9:.0f} would pass — which would need ≈{r9['unexamined_le']} more lookups, "
              "above the per-runner quota. What would answer it: logging the ranked post-DQ names (no extra request) and harvesting "
              "their availability at decision time (extra requests ⇒ owner decision). The first part ships with the pool log "
              "(`fill_pool_log.jsonl`, one record per screening run, evaluated by `pool_funnel.py`); names below the cutoff keep their "
              "availability NOT_COLLECTED, so for them the question stays open unless availability is harvested.", ""]
    L += ["## 5. Next permitted action", "",
          "- Two active gates have no supporting evidence at all — `M13_SHORT` (FINRA short volume, 40,000: no Faisal source, no owner "
          "order; Faisal's «شورت» is availability) and `STOPPED_EXCLUSION` (inherited switch). Removing or changing either changes live "
          "candidate generation ⇒ owner decision; any removal needs a preregistered measurement (the M13 tightening experiments were null).",
          "- Guards with a supported concept and an unsupported number (`COVERAGE_GUARD` 85% · `FILL_ROUNDS` 4 · `D_DEPTH` 120 · the "
          "`DQ_GATE` mapping and 5% tolerance): the concept stays; the number is a disclosed engineering default, not evidence.",
          "- The dominant first wall on Faisal's episodes is `ANCHOR_TWO_TOUCH` (owner policy, FROZEN by the H6 control-pool "
          "dependency and the perf verdict): no production change is permitted; the admissible evidence is the prospective H6 "
          "collection already running.",
          "- `FILL_ROUNDS` × `BORROW_AVAIL` (§4b): the rounds cap, not the pool, ended slot filling in the two post-fix runs whose "
          "pool size was logged (2026-10-08 · 2026-10-09; not determinable for 2026-10-07 — `POOL_FUNNEL_REPORT.md` §3). More "
          "rounds would push ChartExchange lookups past its ~50-page runner quota, and an unknown availability passes the gate, so "
          "raising the cap alone would weaken the borrow gate; harvesting availability for the ranked pool before the screen would "
          "not. Either is a change to live candidate generation ⇒ owner decision (and a prereg for a threshold). The new log line "
          "(`fill_shortfall_note`) now records the binding cause daily.",
          "- `M2_CEIL` / `M4_RANGE` artefacts on reverse-split names: closed / owner-decided axes; reopening needs the owner.", ""]
    return "\n".join(L) + "\n"


def _norm(text):
    text = re.sub(r'"line": (\d+|null)', '"line": #', text)
    text = re.sub(r'"function_lines": \[\s*\d+,\s*\d+\s*\]', '"function_lines": #', text)
    return re.sub(r"\bL(\d+|None)\b", "L#", text)


def _norm_csv(text):
    rows = list(csv.reader(io.StringIO(text)))
    if rows and "line" in rows[0]:
        i = rows[0].index("line")
        for r in rows[1:]:
            if len(r) > i:
                r[i] = "#"
    return rows


def main(argv):
    if "--snapshot" in argv:
        snapshot()
        return 0
    if "--completeness" in argv:                     # fast: anchors + coverage of reject codes / silent returns / functions
        gates = json.load(open(PROV, encoding="utf-8"))["gates"]
        e1, cache = locate(gates)
        e2, codes, bare = completeness(gates, cache)
        bad = [f"{g['id']}: provenance {g['provenance']}" for g in gates if g["provenance"] not in CATS]
        errs = e1 + e2 + bad + audit_errors(json.load(open(PROV, encoding="utf-8")))
        print(f"🚪 completeness: codes {len(codes)} · silent returns {bare} · errors {len(errs)}")
        for e in errs:
            print("  ⛔", e)
        return 0 if not errs else 1
    inv, fx = build()
    j, c, x, md = render(inv, fx)
    errs = inv["summary"]["errors"]
    if "--check" in argv:
        bad = []
        for path, new, norm in ((F_JSON, j, _norm), (F_MD, md, _norm)):
            old = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
            if norm(old) != norm(new):
                bad.append(_rel(path))
        for path, new in ((F_CSV, c), (F_FX, x)):
            old = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
            if _norm_csv(old) != _norm_csv(new):
                bad.append(_rel(path))
        if errs:
            bad.append("build errors: " + "; ".join(errs))
        print("🚪 gate inventory --check:", "OK" if not bad else "⛔ " + " · ".join(bad))
        return 0 if not bad else 1
    os.makedirs(OUT, exist_ok=True)
    for path, text in ((F_JSON, j), (F_CSV, c), (F_FX, x), (F_MD, md)):
        open(path, "w", encoding="utf-8").write(text)
    print(f"🚪 gates {inv['summary']['gates']} · cases {inv['summary']['cases']} · first walls {inv['summary']['first_gate_counts']} · "
          f"errors {len(errs)}")
    for e in errs:
        print("  ⛔", e)
    return 0 if not errs else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
