#!/usr/bin/env python3
"""H6 — gated prospective test (contract `fm_forensics/perf/H6_PREREG.md`, frozen 2026-10-09).

  python3 fm_forensics/perf/h6_test.py status    ⟵ eligibility · coverage · lag · panel health (no prevalence, no effect) → out/H6_STATUS.json
  python3 fm_forensics/perf/h6_test.py analyze   ⟵ ONE run after the floor (15 eligible units) or after the window closes (INSUFFICIENT_SAMPLE)
                                                     refuses (exit 8) before the floor, and refuses forever once out/H6_RESULT.json exists

Research only: reads PROTOCOL_STATUS.json / intake annotations / Phase 6 ledger + control panel; writes under fm_forensics/perf/out only.
No production module is imported (market_calendar is a pure table). Refuses to run if the contract file changed (exit 9).
"""
import csv
import datetime as dt
import hashlib
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
import market_calendar as MC                                        # noqa: E402  (pure holiday table)

PREREG = os.path.join(HERE, "H6_PREREG.md")
PREREG_SHA256 = "a6f68f745cba189223b1f8258e733dc5e1e538382dfe6533307092d8e942c7ed"
OUT = os.environ.get("H6_OUT") or os.path.join(HERE, "out")
CUTOFF_DATE = "2026-10-09"
WINDOW_END = "2027-04-09"
FLOOR = 15
LAG_MAX_SESSIONS = 5
REPEAT_SESSIONS = 30
CONTROLS_MAX, CONTROLS_MIN = 4, 2
COVERAGE_MIN = 0.80
BOOT_B, BOOT_SEED, CI_LEVEL = 2000, 20261009, 0.9875
POSITIVE_LABELS = ("WATCH", "FOCUS", "READY", "ENTRY", "WAIT")
ANCHORS = ("DKI", "SXTC", "HUBC")
FAMILIES = ("A_float", "B_offering", "C_borrow", "D_split")
DIRECTION = {"A_float": +1, "B_offering": -1, "C_borrow": +1, "D_split": +1}
FINAL_PROSPECTUS = ("424B1", "424B4", "424B5")


# ---------------------------------------------------------------- calendar
def is_session(d: str) -> bool:
    try:
        return bool(MC.is_trading_day(d))
    except Exception:                                                # noqa: BLE001 (beyond table ⟶ weekday rule)
        return dt.date.fromisoformat(d).weekday() < 5


def add_sessions(d: str, n: int) -> str:
    x = dt.date.fromisoformat(d)
    k = 0
    while k < n:
        x += dt.timedelta(days=1)
        if is_session(x.isoformat()):
            k += 1
    return x.isoformat()


def sessions_between(a: str, b: str) -> int:
    """Number of sessions in (a, b] (b ≥ a) · negative when b < a."""
    if b < a:
        return -sessions_between(b, a)
    x, n = dt.date.fromisoformat(a), 0
    end = dt.date.fromisoformat(b)
    while x < end:
        x += dt.timedelta(days=1)
        n += int(is_session(x.isoformat()))
    return n


# ---------------------------------------------------------------- inputs
def prereg_ok() -> bool:
    return hashlib.sha256(open(PREREG, "rb").read()).hexdigest() == PREREG_SHA256


def load_cases(root=None) -> list:
    root = root or ROOT
    p = os.path.join(root, "faisal_method_v41", "final_protocol", "PROTOCOL_STATUS.json")
    if not os.path.exists(p):
        return []
    return list(json.load(open(p, encoding="utf-8")).get("cases") or [])


def load_annotations(root=None) -> list:
    """Flat list of intake images: {batch, image_id, symbol, decision_date, decision_date_max, faisal_author}."""
    root = root or ROOT
    out = []
    base = os.path.join(root, "faisal_method_v41", "final_protocol", "intake")
    if not os.path.isdir(base):
        return out
    for b in sorted(os.listdir(base)):
        ap = os.path.join(base, b, "annotations.json")
        if not os.path.exists(ap):
            continue
        imgs = (json.load(open(ap, encoding="utf-8")).get("images") or {})
        items = imgs.items() if isinstance(imgs, dict) else enumerate(imgs)
        for k, a in items:
            if isinstance(a, dict):
                out.append(dict(batch=b, image_id=str(k), symbol=str(a.get("symbol") or "").upper(), decision_date=a.get("decision_date"),
                                decision_date_max=a.get("decision_date_max"), faisal_author=bool(a.get("faisal_author"))))
    return out


def prior_dates(root=None, cases=None) -> dict:
    """ticker ⟶ sorted dated Faisal decisions before H6 (timeline IS_FAISAL=1 · Phase 5 cohort · protocol cases)."""
    root = root or ROOT
    d = {}

    def put(t, day):
        t = (t or "").strip().upper()
        if t and day and len(str(day)) >= 10:
            d.setdefault(t, set()).add(str(day)[:10])
    p = os.path.join(root, "fm_forensics", "phase3", "FAISAL_TIMELINE.csv")
    if os.path.exists(p):
        for r in csv.DictReader(open(p, encoding="utf-8")):
            if r.get("IS_FAISAL") in ("1", "True") and r.get("OBSERVATION_CLASS") != "MENTION":
                put(r.get("TICKER"), r.get("DATE"))
    p = os.path.join(root, "fm_forensics", "phase5", "PHASE5_COHORT_MANIFEST.csv")
    if os.path.exists(p):
        for r in csv.DictReader(open(p, encoding="utf-8")):
            put(r.get("TICKER_AT_DECISION"), r.get("DECISION_DATE"))
    for c in cases or []:
        put(c.get("SYMBOL"), c.get("DECISION_DATE"))
    return {k: sorted(v) for k, v in d.items()}


def load_ledger(path=None) -> list:
    path = path or os.path.join(ROOT, "fm_forensics", "phase6", "data", "PHASE6_LEDGER.jsonl")
    if not os.path.exists(path):
        return []
    return [json.loads(x) for x in open(path, encoding="utf-8") if x.strip()]


def load_panel(path=None) -> dict:
    """obs_date ⟶ {tickers, status, pool_date, pool_n} (first line per day wins — append-only file)."""
    path = path or os.path.join(ROOT, "fm_forensics", "phase6", "data", "PHASE6_CONTROL_PANEL.jsonl")
    out = {}
    if not os.path.exists(path):
        return out
    for x in open(path, encoding="utf-8"):
        if x.strip():
            e = json.loads(x)
            out.setdefault(e["obs_date"], e)
    return out


def index_ledger(rows) -> dict:
    """ticker ⟶ {days: sorted collected dates, rows: [...]}"""
    ix = {}
    for r in rows:
        t = ix.setdefault(r["ticker"].upper(), {"days": set(), "rows": []})
        t["days"].add(r["collected_utc"][:10])
        t["rows"].append(r)
    for t in ix.values():
        t["days"] = sorted(t["days"])
    return ix


# ---------------------------------------------------------------- eligibility (§3)
def eligibility(case, anns, priors, ledger_ix, panel, units_so_far, mention_tickers=()):
    sym = str(case.get("SYMBOL") or "").upper()
    T = str(case.get("DECISION_DATE") or "")
    out = dict(case_id=case.get("CASE_ID"), ticker=sym, T=T, sample=case.get("SAMPLE"), status="ELIGIBLE", code="", C=None, lag=None, controls=[])
    if sym in ANCHORS:
        out.update(status="ANCHOR", code="anchor")
        return out
    if len(T) != 10 or T < CUTOFF_DATE:
        out.update(status="HISTORICAL", code="before_cutoff")
        return out
    if T > WINDOW_END:
        out.update(status="OUT_OF_WINDOW", code="after_window")
        return out
    a = [x for x in anns if x["symbol"] == sym and x["decision_date"] == T and x["faisal_author"]]
    if not a:
        out.update(status="INELIGIBLE", code="E1:no_intake_annotation")
        return out
    if any(x["decision_date_max"] not in (None, "", T) for x in a):
        out.update(status="INELIGIBLE", code="E1:date_ambiguous")
        return out
    if case.get("INTAKE_CLASS") != "NEW_PROSPECTIVE":
        out.update(status="INELIGIBLE", code=f"E3:{case.get('INTAKE_CLASS')}")
        return out
    fa = case.get("FAISAL") or {}
    label = str(fa.get("label") or fa.get("effective_label") or "").upper()
    if not label:
        out.update(status="PENDING_REVEAL", code="E2:not_revealed")
        return out
    if label == "REJECT":
        out.update(status="NEGATIVE", code="E2:reject")
        return out
    if label not in POSITIVE_LABELS:
        out.update(status="INELIGIBLE", code=f"E2:label_{label}")
        return out
    for d in priors.get(sym, []):
        if d < T and sessions_between(d, T) <= REPEAT_SESSIONS:
            out.update(status="REPEAT", code=f"E4:repeat_of_{d}")
            return out
    days = ledger_ix.get(sym, {}).get("days", [])
    cand = [d for d in days if T <= d <= add_sessions(T, LAG_MAX_SESSIONS)]
    if not cand:
        out.update(status="NOT_COVERED", code="E5:no_collection_within_5_sessions")
        return out
    C = cand[0]
    out.update(C=C, lag=sessions_between(T, C))
    pick = None
    for d in [C, prev_session(C), add_sessions(C, 1)]:
        e = panel.get(d)
        if e and e.get("status") == "OK" and e.get("tickers"):
            pick = e
            break
    if not pick:
        out.update(status="NO_CONTROLS", code="E6:no_panel_day")
        return out
    excl = set(mention_tickers) | {u["ticker"] for u in units_so_far} | {sym} | set(ANCHORS)
    ctl = [t for t in pick["tickers"] if t not in excl and pick["obs_date"] in ledger_ix.get(t, {}).get("days", [])][:CONTROLS_MAX]
    if len(ctl) < CONTROLS_MIN:
        out.update(status="NO_CONTROLS", code=f"E6:controls_{len(ctl)}")
        return out
    out.update(controls=ctl, panel_day=pick["obs_date"])
    fr = {r["split_frame"] for r in ledger_ix[sym]["rows"] if r["collected_utc"][:10] == C and r["status"] == "OK" and r["field"] == "public_float"}
    if any(r["field"] == "reverse_split" and r["status"] == "OK" and T < str(r.get("source_asof"))[:10] <= C for r in ledger_ix[sym]["rows"]):
        out.update(status="FRAME_CHANGED", code="E7:reverse_split_between_T_and_C")
        return out
    out["frame"] = sorted(fr)
    return out


def prev_session(d: str) -> str:
    x = dt.date.fromisoformat(d)
    while True:
        x -= dt.timedelta(days=1)
        if is_session(x.isoformat()):
            return x.isoformat()


# ---------------------------------------------------------------- features (§5)
def feature(rows, fam, T, C):
    """True/False, or None when MISSING. `rows` = ledger rows of one ticker."""
    def ok(field, src):
        return [r for r in rows if r["field"] == field and r["source"].startswith(src) and r["status"] == "OK"]
    if fam == "A_float":
        for src in ("yahoo_info", "tv_scan"):
            x = [r for r in ok("public_float", src) if r["collected_utc"][:10] == C and int(r["category"]) == 1]
            if x:
                return float(x[0]["value"]) <= 5_000_000
        return None
    if fam == "C_borrow":
        x = [r for r in ok("borrow_available", "chartexchange") if r["collected_utc"][:10] == C]
        return (float(x[0]["value"]) < 20_000) if x else None
    if fam == "B_offering":
        if not ok("identity", "sec_submissions"):
            return None
        lo = (dt.date.fromisoformat(T) - dt.timedelta(days=90)).isoformat()
        for r in ok("sec_filing", "sec_submissions"):
            v = json.loads(r["value"]) if isinstance(r["value"], str) else r["value"]
            if v.get("form") in FINAL_PROSPECTUS and lo < str(v.get("filingDate")) <= T:
                return True
        return False
    if fam == "D_split":
        ys, ns = ok("reverse_split", "yahoo_splits"), ok("reverse_split", "nasdaq_calendar")
        if not ys and not ns:
            return None
        lo = (dt.date.fromisoformat(T) - dt.timedelta(days=120)).isoformat()
        return any(lo < str(r.get("source_asof"))[:10] <= T for r in ys + ns)
    raise ValueError(fam)


def short_interest(rows, T):
    lo = (dt.date.fromisoformat(T) - dt.timedelta(days=30)).isoformat()
    x = [r for r in rows if r["field"] == "short_interest" and r["status"] == "OK" and lo <= str(r.get("source_asof"))[:10] <= T]
    return float(x[0]["value"]) if x else None


# ---------------------------------------------------------------- status / coverage (§7)
def build_status(today=None, root=None, ledger_rows=None, panel=None):
    root = root or ROOT
    cases = load_cases(root)
    anns = load_annotations(root)
    priors = prior_dates(root, cases)
    rows = load_ledger() if ledger_rows is None else ledger_rows
    ix = index_ledger(rows)
    panel = load_panel() if panel is None else panel
    today = today or dt.datetime.now(dt.timezone.utc).date().isoformat()
    units, items = [], []
    for c in sorted(cases, key=lambda c: (str(c.get("DECISION_DATE")), str(c.get("CASE_ID")))):
        e = eligibility(c, anns, priors, ix, panel, units)
        items.append(e)
        if e["status"] == "ELIGIBLE":
            units.append(e)
    by = {}
    for e in items:
        by[e["status"]] = by.get(e["status"], 0) + 1
    cov = {}
    for fam in FAMILIES:
        pu = [feature(ix[u["ticker"]]["rows"], fam, u["T"], u["C"]) for u in units]
        pc = [feature(ix[t]["rows"], fam, u["T"], u["panel_day"]) for u in units for t in u["controls"]]
        cu = sum(v is not None for v in pu) / len(pu) if pu else 0.0
        cc = sum(v is not None for v in pc) / len(pc) if pc else 0.0
        cov[fam] = dict(units_with_value=sum(v is not None for v in pu), units=len(pu), controls_with_value=sum(v is not None for v in pc),
                        controls=len(pc), coverage_units=round(cu, 4), coverage_controls=round(cc, 4),
                        testable=bool(len(pu) >= FLOOR and cu >= COVERAGE_MIN and cc >= COVERAGE_MIN))
    cov_fail = [e for e in items if e["status"] in ("NOT_COVERED", "NO_CONTROLS", "FRAME_CHANGED")]
    denom = len(units) + len(cov_fail)
    lags = sorted(u["lag"] for u in units)
    pdays = sorted(panel)
    st = dict(contract_sha256=PREREG_SHA256, today=today, cutoff=CUTOFF_DATE, window_end=WINDOW_END, floor=FLOOR,
              candidates=len(items), by_status=by, eligible=len(units), units=[{k: u[k] for k in ("case_id", "ticker", "T", "C", "lag", "sample", "controls", "panel_day")} for u in units],
              items=[{k: e[k] for k in ("case_id", "ticker", "T", "status", "code", "sample")} for e in items],
              coverage_failures=len(cov_fail), coverage_failure_share=(round(len(cov_fail) / denom, 4) if denom else 0.0),
              lag_sessions=dict(n=len(lags), median=(lags[len(lags) // 2] if lags else None), max=(lags[-1] if lags else None)),
              families=cov, any_testable=any(v["testable"] for v in cov.values()),
              panel=dict(days=len(pdays), first=(pdays[0] if pdays else None), last=(pdays[-1] if pdays else None),
                         no_pool_days=sum(1 for d in pdays if panel[d].get("status") != "OK"), k=(panel[pdays[-1]].get("k") if pdays else None)),
              ledger_rows=len(rows), floor_reached=bool(len(units) >= FLOOR and any(v["testable"] for v in cov.values())),
              window_closed=bool(today > WINDOW_END))
    return st, units, ix


# ---------------------------------------------------------------- analysis (§6 · §8) — runs once
def effect_rows(units, ix, fam):
    out = []
    for u in units:
        pu = feature(ix[u["ticker"]]["rows"], fam, u["T"], u["C"])
        pc = [feature(ix[t]["rows"], fam, u["T"], u["panel_day"]) for t in u["controls"]]
        out.append((u["ticker"], pu, [v for v in pc if v is not None]))
    return out


def summarise(rows, direction):
    pos = [r[1] for r in rows if r[1] is not None]
    ctl = [v for r in rows for v in r[2]]
    if not pos or not ctl:
        return None
    p1, p0 = sum(pos) / len(pos), sum(ctl) / len(ctl)
    return dict(n_units=len(pos), n_controls=len(ctl), p_pos=round(p1, 4), p_ctl=round(p0, 4), effect=round(direction * (p1 - p0), 4),
                p_ctl_directional=round(p0 if direction > 0 else 1 - p0, 4))


def bootstrap(rows, direction, B=BOOT_B, seed=BOOT_SEED, level=CI_LEVEL):
    clusters = {}
    for r in rows:
        clusters.setdefault(r[0], []).append(r)
    keys = sorted(clusters)
    rng = random.Random(seed)
    eff = []
    for _ in range(B):
        draw = [x for k in (rng.choice(keys) for _ in keys) for x in clusters[k]]
        s = summarise(draw, direction)
        if s:
            eff.append(s["effect"])
    if not eff:
        return None
    eff.sort()
    a = (1 - level) / 2
    return dict(lo=eff[int(a * len(eff))], hi=eff[min(len(eff) - 1, int((1 - a) * len(eff)))], B=len(eff))


def verdict_family(s, ci):
    if s is None or ci is None:
        return "NOT TESTABLE"
    if ci["lo"] > 0 and s["p_ctl_directional"] <= 0.5:       # §8: control prevalence of the feature in its expected direction
        return "SUPPORTED"
    if ci["hi"] < 0:
        return "REVERSED"
    return "UNSUPPORTED"


def overall(fams: dict, testable_any: bool, insufficient: bool) -> str:
    if insufficient:
        return "INSUFFICIENT_SAMPLE"
    if not testable_any:
        return "NOT TESTABLE"
    vs = [v["verdict"] for v in fams.values() if v["verdict"] != "NOT TESTABLE"]
    if not vs:
        return "NOT TESTABLE"
    if "REVERSED" not in vs and "SUPPORTED" in vs:
        return "SUPPORTED"
    return "UNSUPPORTED"


def analyze(st, units, ix):
    insufficient = (not st["floor_reached"]) and st["window_closed"]
    fams = {}
    for fam in FAMILIES:
        if insufficient or not st["families"][fam]["testable"]:
            fams[fam] = dict(verdict="NOT TESTABLE", coverage=st["families"][fam])
            continue
        rows = effect_rows(units, ix, fam)
        s, ci = summarise(rows, DIRECTION[fam]), bootstrap(rows, DIRECTION[fam])
        fams[fam] = dict(summary=s, ci=ci, verdict=verdict_family(s, ci), direction=DIRECTION[fam], coverage=st["families"][fam])
    si = dict(pos=[short_interest(ix[u["ticker"]]["rows"], u["T"]) for u in units],
              ctl=[short_interest(ix[t]["rows"], u["T"]) for u in units for t in u["controls"]])
    return dict(contract_sha256=PREREG_SHA256, analyzed_at=dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
                status=st, families=fams, short_interest_descriptive=si,
                H6=overall(fams, st["any_testable"], insufficient), coverage_block=(st["coverage_failure_share"] > 0.20))


def verdict_md(res) -> str:
    L = ["# H6 — VERDICT (single pre-registered analysis · `fm_forensics/perf/H6_PREREG.md`)", "",
         f"Analyzed {res['analyzed_at']} · contract `{res['contract_sha256'][:16]}` · eligible units {res['status']['eligible']} (floor {FLOOR}) · "
         f"coverage failures {res['status']['coverage_failures']} ({res['status']['coverage_failure_share']:.0%})", "",
         f"## H6 = {('NOT TESTABLE (coverage)' if res['coverage_block'] and res['H6'] not in ('INSUFFICIENT_SAMPLE',) else res['H6'])}", "",
         "| family | n units | n controls | p_pos | p_ctl | effect (direction) | 98.75% CI | verdict |", "|---|---|---|---|---|---|---|---|"]
    for fam, v in res["families"].items():
        s, ci = v.get("summary"), v.get("ci")
        L.append(f"| {fam} | {s['n_units'] if s else '—'} | {s['n_controls'] if s else '—'} | {s['p_pos'] if s else '—'} | {s['p_ctl'] if s else '—'} | "
                 f"{s['effect'] if s else '—'} ({v.get('direction', '—')}) | {('[' + str(ci['lo']) + ', ' + str(ci['hi']) + ']') if ci else '—'} | {v['verdict']} |")
    L += ["", "Short interest (descriptive, no test): " + json.dumps(res["short_interest_descriptive"]), "",
          "No production change follows from this file (contract §0, §11). No further phase follows automatically (§9).", ""]
    return "\n".join(L)


# ---------------------------------------------------------------- CLI
def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    mode = argv[0] if argv else "status"
    if not prereg_ok():
        print("H6 REFUSED: contract file changed (SHA-256 mismatch) — amendments go in H6_PREREG_AMENDMENT_<n>.md")
        return 9
    today = os.environ.get("H6_TODAY")
    st, units, ix = build_status(today)
    os.makedirs(OUT, exist_ok=True)
    json.dump(st, open(os.path.join(OUT, "H6_STATUS.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    print(f"H6 STATUS today={st['today']} candidates={st['candidates']} eligible={st['eligible']}/{FLOOR} by_status={json.dumps(st['by_status'])} "
          f"coverage_failures={st['coverage_failures']} lag_median={st['lag_sessions']['median']} panel_days={st['panel']['days']} "
          f"testable={[f for f, v in st['families'].items() if v['testable']]} floor_reached={st['floor_reached']} window_closed={st['window_closed']}")
    if mode == "status":
        return 0
    if mode != "analyze":
        print("usage: h6_test.py status|analyze")
        return 2
    res_path = os.path.join(OUT, "H6_RESULT.json")
    if os.path.exists(res_path):
        print("H6 REFUSED: analysis already ran once (out/H6_RESULT.json exists) — the contract allows a single analysis")
        return 8
    if not st["floor_reached"] and not st["window_closed"]:
        print(f"H6 REFUSED: floor not reached ({st['eligible']}/{FLOOR} eligible · testable={st['any_testable']}) and window open until {WINDOW_END}")
        return 8
    res = analyze(st, units, ix)
    json.dump(res, open(res_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    open(os.path.join(HERE, "H6_VERDICT.md"), "w", encoding="utf-8").write(verdict_md(res))
    print(f"H6 = {res['H6']} · families={ {k: v['verdict'] for k, v in res['families'].items()} } → {res_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
