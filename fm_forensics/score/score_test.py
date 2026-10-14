"""T-SCORE — a continuous closeness score to Faisal's conditions, weighted from his words, tested on tracked movers.

Owner's prompt 2026-10-13/14 («T-SCORE: درجةُ قربٍ موزونةٌ من كلام فيصل» — permission for this axis only). Research only:
no production, V4, H6, Telegram, threshold or root change. The contract `T_SCORE_prereg.md` is pinned below and must be on
origin/main before any number (run() exits 9 otherwise).

Components (production functions by name, never modified): `Super_stock.rsi` · `pivot_cycle_state` · `_cycle_sweep_reclaimed`
· `unfilled_gaps_above`. Each component is a closeness in [0, 1] to Faisal's own threshold; the level S_L is their weighted mean
over the known components (unknown stays unknown — never 0); the governing score adds the direction:
    S(t) = S_L(t) + (S_L(t) − S_L(t − 5))     (the closeness projected one trading week ahead)
Weights w = L1 (decisionality) × L2 (evidence class) × L3 (1 + times named in Faisal's WAIT statements ÷ the most named).

    python3 fm_forensics/score/score_test.py --guards   # synthetic guards (no population read)
    python3 fm_forensics/score/score_test.py            # the sealed run (once, after the contract is on main)
    python3 fm_forensics/score/score_test.py --today    # stage D: today's near-watch list ranked (needs data/today_bars.json.gz)
"""
import csv
import gzip
import hashlib
import inspect
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (os.path.join(ROOT, "fm_forensics", "gen5"), os.path.join(ROOT, "fm_forensics", "heat"), ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import gen5_features as G   # noqa: E402
import gen5_ext as X        # noqa: E402

PREREG = os.path.join(HERE, "T_SCORE_prereg.md")
PREREG_SHA256 = "b1f21d163c02f9894f945a9910f6255bd5e9091dd3efc909ed093d0d7e670946"
TAGS = os.path.join(HERE, "data", "wait_tags.json")
LEDGER = os.path.join(ROOT, "faisal_engine", "FAISAL_RULE_LEDGER.csv")
MATRIX = os.path.join(ROOT, "fm_forensics", "READY_NOW_RULE_EVIDENCE_MATRIX.csv")
HEAT_RESULT = os.path.join(ROOT, "fm_forensics", "heat", "data", "heat_result.json")
PINS = {TAGS: "0606fe4ae5e13dd4fc62d5b89aae8eca6f9f049e0dd45162e84ae15f35e1d75e",
        LEDGER: "88bd3244feab49d477b6b4e30039ae7c4418210830273ea42ec904b39e56fbb7",
        MATRIX: "ad9fb6e4ab9c59dd1c8d273fd4cbf514063125fae96b107f6274c9f23baa361e",
        HEAT_RESULT: "e3585b12b17c84607e40c22f1f04183183868b8513a274493cdc71ae8963606b"}
PROD_SRC_SHA256 = "431464ac2a675879c827f82b509efa93d8a2b14088c7bc7da9fbea42ef3a012d"            # rsi · pivot_cycle_state · _cycle_sweep_reclaimed · unfilled_gaps_above
OUT = os.path.join(HERE, "data", "score_result.json")
UNITS_CSV = os.path.join(HERE, "data", "score_units.csv")
TODAY_BARS = os.path.join(HERE, "data", "today_bars.json.gz")
TODAY_CSV = os.path.join(HERE, "data", "today_ranked.csv")

# ── frozen design (the contract quotes each one) ───────────────────────────────────────────────────────
K_GAP = 2                       # decision day t = A − 2 (A − 1 is never read) — same guard as T-HEAT
DIR_LAG = 5                     # direction over one trading week
RSI_FULL, RSI_ZERO = 27.0, 40.0  # TG_2043 verbatim: «RSI بين 23-27» · «مستحيل يصعد اذا RSI بمناطق 40»
HOLD_FULL = 5                   # R4-HOLD-01 / X_20260918_85_YMT «ما كسر القاع اكثر من 5 جلسات» (IMG_0151 «3» ⟶ 0.6)
TEST_FULL = 15.0                # R4-CYC-01 «صعودُ اختبارٍ 15% فأكثر · غالبًا 20%»
ZONE_TOP, ZONE_DECAY = 15.0, 15.0  # R4-ZONE-01 «من القاع حتى 15% فوقه» · decay over one more zone width (engineering)
HOLDZ_FULL = 3                  # R4-HOLDZ-01 «2-5 جلسات · الأساسيّ 3»
SCAN_RSI, SCAN_DROP = 33.0, 70.0  # BASE2 of PERFORMANCE_VERDICT.md (fm_forensics/perf/perf.py: rsi14 < 33 ∧ drop_pct ≥ 70)
HI52_BARS = 252
MIN_BARS = 80                   # history before t (gen5_test.HIST)
FLOORS = {"events": 30, "symbols": 20, "min_ctrl": 3}
MDE_MAX = 0.20                  # design MDE80 of the matched AUC above 0.20 ⟶ D (cannot detect AUC 0.70)
BOOT, SEED = 4000, 20261014
ORDER = {"D": 0, "C": 1, "B": 2, "A0": 3, "A": 4}

L1 = {"DECISIONAL": 1.0, "SUPPORTING": 2 / 3, "INFORMATIONAL": 1 / 3, "UNKNOWN": 1 / 3, "CONTRADICTED": 0.0}
L2 = {"DIRECTLY_OBSERVED": 1.0, "REPEATEDLY_SUPPORTED": 2 / 3, "INFERRED": 1 / 3, "CONTRADICTED": 0.0}
MATRIX_TO_L2 = {"DIRECTLY_SUPPORTED": "DIRECTLY_OBSERVED", "STRONGLY_SUPPORTED": "REPEATEDLY_SUPPORTED"}
# component ⟶ ledger rows (the strongest row's classes are used) · matrix row when the ledger has none · wait-tag category
COMPONENTS = {
    "RSI": {"ledger": [], "matrix": "R-RSI-LOW", "l1_from": "FE-SCREEN-01", "tag": "RSI"},
    "HOLD": {"ledger": ["R4-HOLD-01"], "tag": "HOLD"},
    "CYC": {"ledger": ["R4-CYC-01"], "tag": "TEST"},
    "ZONE": {"ledger": ["R4-ZONE-01", "R4-LOC-01"], "tag": "ZONE"},
    "HOLDZ": {"ledger": ["R4-HOLDZ-01"], "tag": "HOLD"},
    "SWEEP": {"ledger": ["R4-SWEEP-01"], "tag": "SWEEP"},
    "GAP": {"ledger": ["R4-TGT-01"], "tag": "GAP"},
}
COMP_ORDER = list(COMPONENTS)
WEIGHTS_FROZEN = {"RSI": 1.1852, "HOLD": 1.3333, "CYC": 1.7037, "ZONE": 1.4074, "HOLDZ": 0.6667, "SWEEP": 0.9877, "GAP": 0.3457}


def _sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest() if os.path.exists(path) else None


def prod_src_sha():
    S = G.S()
    src = "".join(inspect.getsource(f) for f in (S.rsi, S.pivot_cycle_state, S._cycle_sweep_reclaimed, S.unfilled_gaps_above))
    return hashlib.sha256(src.encode()).hexdigest()


def check_pins(prereg=PREREG, prereg_sha=None):
    """Contract, weight sources, the T-HEAT unit list and the production functions must match before any read; else exit 9."""
    want = PREREG_SHA256 if prereg_sha is None else prereg_sha
    if _sha(prereg) != want:
        print(f"⛔ contract changed or not pinned: {_sha(prereg)} ≠ {want}")
        sys.exit(9)
    for p, h in PINS.items():
        if _sha(p) != h:
            print(f"⛔ pinned input changed: {os.path.relpath(p, ROOT)} {_sha(p)} ≠ {h}")
            sys.exit(9)
    if prod_src_sha() != PROD_SRC_SHA256:
        print(f"⛔ production functions changed: {prod_src_sha()} ≠ {PROD_SRC_SHA256}")
        sys.exit(9)
    if weights() != WEIGHTS_FROZEN:
        print(f"⛔ recomputed weights differ from the frozen ones: {weights()} ≠ {WEIGHTS_FROZEN}")
        sys.exit(9)


def _main_contract():
    import subprocess
    rel = os.path.relpath(PREREG, ROOT).replace(os.sep, "/")
    p = subprocess.run(["git", "-C", ROOT, "show", f"origin/main:{rel}"], capture_output=True)
    return p.stdout if p.returncode == 0 else None


def check_merged(read=None):
    """«العقد مدموجًا في main قبل أيّ رقم»: origin/main must carry the pinned contract bytes, else exit 9."""
    blob = (read or _main_contract)()
    got = hashlib.sha256(blob).hexdigest() if blob is not None else None
    if got != PREREG_SHA256:
        print(f"⛔ the pinned contract is not on origin/main ({got}) — merge it first (git fetch --force)")
        sys.exit(9)


# ── weights (from Faisal's words only) ───────────────────────────────────────────────────────────────
def weights(ledger=LEDGER, matrix=MATRIX, tags=TAGS, layers=(1, 2, 3)):
    """{component: w} rounded to 4 places. L1/L2 from the ledger row(s) (the strongest row when two) · the matrix row (mapped)
    when the ledger has none · L3 = 1 + n/max over Faisal's deduplicated WAIT statements. `layers` drops layers (ablation)."""
    led = {r["rule_id"]: r for r in csv.DictReader(open(ledger, encoding="utf-8"))}
    mat = {r["RULE_ID"]: r for r in csv.DictReader(open(matrix, encoding="utf-8"))}
    counts = json.load(open(tags, encoding="utf-8"))["sets"]["faisal"]["counts"]
    nmax = max(counts.values())
    out = {}
    for c, spec in COMPONENTS.items():
        if spec["ledger"]:
            rows = [led[r] for r in spec["ledger"]]
            l1 = max(L1[r["decisionality"]] for r in rows)
            l2 = max(L2[r["evidence_class"]] for r in rows)
        else:
            l1 = L1[led[spec["l1_from"]]["decisionality"]]
            l2 = L2[MATRIX_TO_L2.get(mat[spec["matrix"]]["RULE_CLASS"], "INFERRED")]
        l3 = 1.0 + counts[spec["tag"]] / nmax
        w = (l1 if 1 in layers else 1.0) * (l2 if 2 in layers else 1.0) * (l3 if 3 in layers else 1.0)
        out[c] = round(w, 4)
    return out


def contradicted_rules(ledger=LEDGER, matrix=MATRIX):
    """Rules whose evidence class is CONTRADICTED — weight zero, listed (none is a component)."""
    a = [r["rule_id"] for r in csv.DictReader(open(ledger, encoding="utf-8")) if r["evidence_class"] == "CONTRADICTED"]
    b = [r["RULE_ID"] for r in csv.DictReader(open(matrix, encoding="utf-8")) if r["RULE_CLASS"] == "CONTRADICTED"]
    return sorted(a + b)


# ── components (pure) ────────────────────────────────────────────────────────────────────────────────
def _clip(x):
    return max(0.0, min(1.0, x))


def raw_at(df, i):
    """Raw readings at session index i from bars 0..i only. None ⟵ unknown."""
    S = G.S()
    d = df.iloc[: i + 1]
    out = {"t": d.index[-1].date().isoformat(), "rsi": None, "pc": None, "sweep_reclaimed": None, "gaps_above": None,
           "drop52": None}
    if len(d) < 15:
        return out
    try:
        r = S.rsi(d["Close"].astype(float))
        v = float(r.iloc[-1])
        out["rsi"] = v if math.isfinite(v) else None
    except Exception:                                            # noqa: BLE001
        pass
    pc = S.pivot_cycle_state(d)
    out["pc"] = pc
    out["sweep_reclaimed"] = bool(S._cycle_sweep_reclaimed(pc)) if pc else None
    try:
        out["gaps_above"] = int(S.unfilled_gaps_above(d, int(S.CONFIG["GAP_LOOKBACK"])).get("count") or 0)
    except Exception:                                            # noqa: BLE001
        pass
    hi = float(d["High"].tail(HI52_BARS).max())
    c = float(d["Close"].iloc[-1])
    out["drop52"] = (1.0 - c / hi) * 100.0 if hi > 0 else None
    return out


def closeness(raw):
    """{component: closeness in [0, 1] | None} — the distance to Faisal's threshold, not a pass/fail."""
    c = {k: None for k in COMP_ORDER}
    rsi, pc = raw.get("rsi"), raw.get("pc")
    if rsi is not None:
        c["RSI"] = _clip((RSI_ZERO - rsi) / (RSI_ZERO - RSI_FULL))
    if raw.get("gaps_above") is not None:
        c["GAP"] = 1.0 if raw["gaps_above"] > 0 else 0.0
    if pc:
        st, bounce, vs = int(pc["stage"]), float(pc["bounce_pct"]), float(pc["vs_bottom_pct"])
        c["HOLD"] = _clip(int(pc["bottom_ago"]) / HOLD_FULL)
        rise = _clip(bounce / TEST_FULL)
        if st >= 3:
            back = 1.0
        elif st == 2 and bounce > 0:
            back = _clip(1.0 - vs / bounce)          # share of the test rise already given back toward the bottom
        else:
            back = 0.0
        c["CYC"] = 0.5 * rise + 0.5 * back
        c["ZONE"] = 1.0 if vs <= ZONE_TOP else _clip(1.0 - (vs - ZONE_TOP) / ZONE_DECAY)
        c["HOLDZ"] = _clip(int(pc["held"]) / HOLDZ_FULL) if st >= 3 else 0.0
        if raw.get("sweep_reclaimed"):
            c["SWEEP"] = 1.0
        elif pc.get("branch") == "sweep":
            c["SWEEP"] = 0.5
        else:
            c["SWEEP"] = 0.0
    return c


def level(c, w):
    """Weighted mean over the KNOWN components (unknown is never 0) · None when nothing is known or all weights are 0."""
    num = sum(w[k] * v for k, v in c.items() if v is not None)
    den = sum(w[k] for k, v in c.items() if v is not None)
    return (num / den) if den > 0 else None


def score_from(raw_t, raw_lag, w):
    """{S, S_L, D}: S = S_L(t) + (S_L(t) − S_L(t−5)) · None when either level is unknown."""
    a, b = level(closeness(raw_t), w), level(closeness(raw_lag), w) if raw_lag is not None else None
    if a is None or b is None:
        return {"S": None, "S_L": a, "D": None}
    return {"S": a + (a - b), "S_L": a, "D": a - b}


def scan_flag(raw):
    """BASE2: RSI14 < 33 ∧ drop from the 252-session high ≥ 70% · None when unknown."""
    if raw.get("rsi") is None or raw.get("drop52") is None:
        return None
    return 1.0 if (raw["rsi"] < SCAN_RSI and raw["drop52"] >= SCAN_DROP) else 0.0


# ── statistics ───────────────────────────────────────────────────────────────────────────────────────
def unit_auc(e, cs):
    """Within one matched set: share of known controls the event outranks (ties ½). None if the event or all controls unknown."""
    cs = [x for x in cs if x is not None]
    if e is None or not cs:
        return None
    return sum(1.0 if e > x else (0.5 if e == x else 0.0) for x in cs) / len(cs)


def unit_diff(e, cs):
    cs = [x for x in cs if x is not None]
    if e is None or not cs:
        return None
    return e - sum(cs) / len(cs)


def matched(units, key, fn=unit_auc):
    vals = [fn(u["ev"][key], [c[key] for c in u["ctrl"]]) for u in units]
    vals = [v for v in vals if v is not None]
    return (sum(vals) / len(vals)) if vals else None


def cluster_boot(units, stat, reps=BOOT, seed=SEED):
    """Percentile 95% CI of stat(units) resampling event SYMBOLS with replacement (a symbol's units move together)."""
    by = {}
    for u in units:
        by.setdefault(u["sym"], []).append(u)
    syms = sorted(by)
    rng = random.Random(seed)
    vals = []
    for _ in range(reps):
        s = [u for t in (rng.choice(syms) for _ in syms) for u in by[t]]
        v = stat(s)
        if v is not None:
            vals.append(v)
    vals.sort()
    pt = stat(units)
    if not vals or pt is None:
        return {"point": None if pt is None else round(pt, 4), "ci95": None, "sd": None}
    m = sum(vals) / len(vals)
    sd = math.sqrt(sum((v - m) ** 2 for v in vals) / max(1, len(vals) - 1))
    return {"point": round(pt, 4), "ci95": [round(vals[int(0.025 * (len(vals) - 1))], 4),
                                            round(vals[int(0.975 * (len(vals) - 1))], 4)], "sd": round(sd, 4)}


def design_mde80(n_e, n_c):
    """Design MDE80 of an AUC (null SE ≈ √((n_E + n_C + 1) / (12 n_E n_C)) · ×2.8 for 80 % power at two-sided 5 %)."""
    if not n_e or not n_c:
        return None
    return round(2.8 * math.sqrt((n_e + n_c + 1) / (12.0 * n_e * n_c)), 4)


def branch(b, mde_rule=True):
    """D · C · B · A for one reading (governing score S vs 0.5, then vs the scan)."""
    if b["events"] < FLOORS["events"] or b["symbols"] < FLOORS["symbols"]:
        return "D"
    if mde_rule and (b["design_mde80"] is None or b["design_mde80"] > MDE_MAX):
        return "D"
    lo = (b["auc"]["S"]["ci95"] or [None])[0]
    if lo is None or lo <= 0.5:
        return "C"
    lo2 = (b["delta_auc"]["S_minus_scan"]["ci95"] or [None])[0]
    return "A" if (lo2 is not None and lo2 > 0) else "B"


def verdict(primary, identity):
    p = branch(primary, True)
    if p in ("D", "C"):
        return p
    s = branch(identity, False)
    if s == "D":
        return "A0" if p == "A" else p
    return min((p, s), key=lambda x: ORDER[x])


KEYS = ("S", "S_L", "U", "S1", "S12", "scan")


def block(units):
    n_sym = len({u["sym"] for u in units})
    n_c = sum(sum(1 for c in u["ctrl"] if c["S"] is not None) for u in units)
    res = {"events": len(units), "symbols": n_sym, "control_draws": n_c, "design_mde80": design_mde80(len(units), n_c),
           "floors_met": len(units) >= FLOORS["events"] and n_sym >= FLOORS["symbols"], "auc": {}, "mean_diff": {},
           "delta_auc": {}, "pooled_auc": {}}
    for k in KEYS:
        res["auc"][k] = cluster_boot(units, lambda us, k=k: matched(us, k))
        res["mean_diff"][k] = cluster_boot(units, lambda us, k=k: matched(us, k, unit_diff))
        res["pooled_auc"][k] = pooled_auc(units, k)
    for a, b in (("S", "scan"), ("S", "U"), ("S", "S_L"), ("S12", "S1"), ("S", "S12"), ("S1", "U")):
        res["delta_auc"][f"{a}_minus_{b}"] = cluster_boot(
            units, lambda us, a=a, b=b: (None if matched(us, a) is None or matched(us, b) is None
                                         else matched(us, a) - matched(us, b)))
    return res


def pooled_auc(units, key):
    """Descriptive Mann-Whitney AUC: every event against every known control draw (ignores the matching)."""
    e = [u["ev"][key] for u in units if u["ev"][key] is not None]
    c = [x[key] for u in units for x in u["ctrl"] if x[key] is not None]
    if not e or not c:
        return None
    return round(sum(1.0 if a > b else (0.5 if a == b else 0.0) for a in e for b in c) / (len(e) * len(c)), 4)


# ── data side ────────────────────────────────────────────────────────────────────────────────────────
def unit_scores(df, i, splits, wsets):
    """All readings of one symbol at decision index i (A − K_GAP) with the direction lag · unknown on an unadjusted split."""
    if i - DIR_LAG < MIN_BARS:
        return None, "short_history"
    rows = [[d.date().isoformat(), 0, 0, 0, float(c), 0] for d, c in zip(df.index, df["Close"])]
    lo = rows[max(0, i - DIR_LAG - 80)][0]
    bad = X.split_unadjusted(rows, splits, lo, rows[i][0])
    if bad:
        return None, "split_unadjusted"
    rt, rl = raw_at(df, i), raw_at(df, i - DIR_LAG)
    out = {"t": rt["t"], "raw": {"rsi": rt["rsi"], "drop52": rt["drop52"], "gaps_above": rt["gaps_above"],
                                 "pc": rt["pc"], "sweep_reclaimed": rt["sweep_reclaimed"]},
           "close": closeness(rt), "scan": scan_flag(rt)}
    for name, w in wsets.items():
        sc = score_from(rt, rl, w)
        out[name] = sc["S"]
        if name == "S":
            out["S_L"], out["D"] = sc["S_L"], sc["D"]
    return out, "ok"


def weight_sets():
    w = weights()
    return {"S": w, "U": {k: 1.0 for k in COMP_ORDER}, "S1": weights(layers=(1,)), "S12": weights(layers=(1, 2))}


def run():
    check_pins()
    check_merged()
    heat = json.load(open(HEAT_RESULT, encoding="utf-8"))["anchors"]["O"]["units"]
    need = sorted({u["sym"] for u in heat} | {c for u in heat for c in u["ctrl_syms"]})
    bars = G.load_bars(set(need))
    splits = G.load_splits()
    ws = weight_sets()
    acc = {"events_in": len(heat), "event_unknown": [], "ctrl_unknown": 0, "few_controls": []}
    units = []
    for u in heat:
        def at(sym, A=u["A"]):
            df = bars.get(sym)
            if df is None:
                return None, "no_bars"
            ix = list(df.index.strftime("%Y-%m-%d"))
            if A not in ix:
                return None, "anchor_not_in_archive"
            return unit_scores(df, ix.index(A) - K_GAP, splits.get(sym), ws)
        ev, why = at(u["sym"])
        if ev is None or ev["S"] is None:
            acc["event_unknown"].append((u["sym"], u["A"], why if ev is None else "score_unknown"))
            continue
        ctrl = []
        for c in u["ctrl_syms"]:
            cv, _ = at(c)
            if cv is None or cv["S"] is None:
                acc["ctrl_unknown"] += 1
                continue
            ctrl.append(dict(cv, sym=c))
        if len(ctrl) < FLOORS["min_ctrl"]:
            acc["few_controls"].append((u["sym"], u["A"], len(ctrl)))
            continue
        units.append({"sym": u["sym"], "A": u["A"], "E_reg": u["E_reg"], "identity": u["identity"],
                      "ev": dict(ev, sym=u["sym"]), "ctrl": ctrl})
    res = {"prereg_sha256": PREREG_SHA256, "weights": {k: v for k, v in ws.items()}, "accounting": acc,
           "primary": block(units), "sensitivity_identity": block([u for u in units if u["identity"]]),
           "units": units}
    res["verdict"] = verdict(res["primary"], res["sensitivity_identity"])
    res["weights_answer"] = weights_answer(res["primary"])
    res["component_profile"] = component_profile(units)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    write_units_csv(units)
    report(res)
    return res


def weights_answer(b):
    """Did the weights add anything over the unweighted score? Each layer, by the lower bound of its paired ΔAUC."""
    def lo(k):
        ci = b["delta_auc"][k]["ci95"]
        return None if not ci else ci[0]
    return {"weighted_vs_unweighted": lo("S_minus_U"), "layer2_over_layer1": lo("S12_minus_S1"),
            "layer3_over_layers12": lo("S_minus_S12"), "layer1_over_unweighted": lo("S1_minus_U"),
            "direction_over_level": lo("S_minus_S_L")}


def component_profile(units):
    """Descriptive: mean closeness of each component, events vs their controls (no CI, no verdict)."""
    out = {}
    for k in COMP_ORDER:
        e = [u["ev"]["close"][k] for u in units if u["ev"]["close"][k] is not None]
        c = [x["close"][k] for u in units for x in u["ctrl"] if x["close"][k] is not None]
        out[k] = {"events": round(sum(e) / len(e), 4) if e else None, "n_e": len(e),
                  "controls": round(sum(c) / len(c), 4) if c else None, "n_c": len(c)}
    return out


def write_units_csv(units, path=UNITS_CSV):
    cols = ["role", "sym", "event_sym", "A", "t", "S", "S_L", "D", "U", "scan", "rsi", "drop52"] + [f"c_{k}" for k in COMP_ORDER]
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for u in units:
            for role, x in [("event", u["ev"])] + [("control", c) for c in u["ctrl"]]:
                w.writerow([role, x["sym"], u["sym"], u["A"], x["t"]] + [None if x.get(k) is None else round(x[k], 4)
                                                                        for k in ("S", "S_L", "D", "U", "scan")]
                           + [None if x["raw"]["rsi"] is None else round(x["raw"]["rsi"], 2),
                              None if x["raw"]["drop52"] is None else round(x["raw"]["drop52"], 2)]
                           + [None if x["close"][k] is None else round(x["close"][k], 4) for k in COMP_ORDER])


def report(res):
    p = res["primary"]
    print("accounting", json.dumps({k: (v if isinstance(v, int) else len(v)) for k, v in res["accounting"].items()}))
    print(f"events {p['events']} · symbols {p['symbols']} · control draws {p['control_draws']} · design MDE80 {p['design_mde80']}")
    for k in KEYS:
        print(f"  {k:5s} matched AUC {p['auc'][k]} · mean diff {p['mean_diff'][k]['point']} {p['mean_diff'][k]['ci95']}"
              f" · pooled AUC {p['pooled_auc'][k]}")
    for k, v in p["delta_auc"].items():
        print(f"  Δ {k}: {v}")
    print("identity:", res["sensitivity_identity"]["events"], "events · AUC S", res["sensitivity_identity"]["auc"]["S"])
    print("weights answer", res["weights_answer"])
    print("component profile", json.dumps(res["component_profile"]))
    print("VERDICT", res["verdict"])


# ── stage D: today's near-watch list ─────────────────────────────────────────────────────────────────
def gaps_text(raw, c):
    """What is missing and how far, in Faisal's phrasing («باقي له …»). Empty list ⟵ nothing missing."""
    out = []
    rsi, pc = raw.get("rsi"), raw.get("pc")
    if rsi is not None and rsi > RSI_FULL:
        out.append(f"RSI {rsi:.1f} — باقي {rsi - RSI_FULL:.1f} نقطة ليبلغ {RSI_FULL:.0f}"
                   + (" (عند 40 أو فوقها: «مستحيل يصعد»)" if rsi >= RSI_ZERO else ""))
    if pc:
        st, ago, bounce, vs = int(pc["stage"]), int(pc["bottom_ago"]), float(pc["bounce_pct"]), float(pc["vs_bottom_pct"])
        if ago < HOLD_FULL:
            out.append(f"الثبات: مضى {ago} من {HOLD_FULL} جلسات على القاع — باقي {HOLD_FULL - ago}")
        if bounce < TEST_FULL:
            out.append(f"اختبار المقاومة: صعد {bounce:.1f}% من القاع — باقي {TEST_FULL - bounce:.1f}% ليبلغ {TEST_FULL:.0f}%")
        elif st == 2:
            out.append(f"صعد {bounce:.1f}% — باقي الرجوع لاختبار القاع (فوقه بـ{vs:.1f}%)")
        if vs > ZONE_TOP:
            out.append(f"فوق القاع بـ{vs:.1f}% — باقي نزول {vs - ZONE_TOP:.1f}% ليدخل منطقة {ZONE_TOP:.0f}%")
        if st >= 3 and int(pc["held"]) < HOLDZ_FULL:
            out.append(f"الثبات بعد الاختبار: مضى {int(pc['held'])} من {HOLDZ_FULL} — باقي {HOLDZ_FULL - int(pc['held'])}")
    elif rsi is not None:
        out.append("دورة الارتكاز: غير معروفة (لا قاعَ داخل آخر 60 جلسة)")
    if c.get("GAP") == 0.0:
        out.append("لا فجوة مفتوحة فوقه")
    return out


def today():
    """Ranks the near-watch members of the latest screen by S on the runner-fetched bars. Not governed by the test unless the
    sealed verdict is A or A0 — labelled «قراءةٌ أماميّة غيرُ محكومة» otherwise."""
    nw = json.load(open(os.path.join(ROOT, "near_watch.json"), encoding="utf-8"))
    last = max(v.get("last_seen") or "" for v in nw.values())
    members = sorted(s for s, v in nw.items() if v.get("last_seen") == last)
    raw = json.load(gzip.open(TODAY_BARS, "rt", encoding="utf-8"))
    import pandas as pd
    ctb = {}
    p = os.path.join(ROOT, "ctb_log.jsonl")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("shares_available") is not None and r.get("date"):
                if r["symbol"] not in ctb or r["date"] >= ctb[r["symbol"]][0]:
                    ctb[r["symbol"]] = (r["date"], r["shares_available"])
    ws = weight_sets()
    rows = []
    for s in members:
        b = raw["daily"].get(s)
        if not b or len(b) < MIN_BARS + DIR_LAG + 1:
            rows.append({"sym": s, "S": None, "why": "no_bars" if not b else "short_history"})
            continue
        df = pd.DataFrame(b, columns=["Date", "Open", "High", "Low", "Close", "Volume"])
        df.index = pd.to_datetime(df["Date"])
        df = df[["Open", "High", "Low", "Close", "Volume"]].astype(float)
        df = df[df.index <= pd.Timestamp(last)]            # the screen's session: never a partial bar of a later day
        if len(df) < MIN_BARS + DIR_LAG + 1:
            rows.append({"sym": s, "S": None, "why": "short_history"})
            continue
        if df.index[-1].date().isoformat() != last:         # no bar for the screen's session ⟶ unknown, not an old reading
            rows.append({"sym": s, "S": None, "why": f"stale_bars:{df.index[-1].date().isoformat()}"})
            continue
        i = len(df) - 1
        rt, rl = raw_at(df, i), raw_at(df, i - DIR_LAG)
        sc = score_from(rt, rl, ws["S"])
        c = closeness(rt)
        av = ctb.get(s)
        rows.append({"sym": s, "t": rt["t"], "S": sc["S"], "S_L": sc["S_L"], "D": sc["D"], "scan": scan_flag(rt),
                     "rsi": rt["rsi"], "met": [k for k in COMP_ORDER if c[k] is not None and c[k] >= 0.999],
                     "missing": gaps_text(rt, c), "float": nw[s].get("float"), "n_out": nw[s].get("n_out"),
                     "avail": av[1] if av else None, "avail_date": av[0] if av else None, "why": "ok"})
    rows.sort(key=lambda r: (r["S"] is None, -(r["S"] or 0), r["sym"]))
    with open(TODAY_CSV, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["rank", "sym", "asof", "S", "S_level", "direction", "scan", "rsi", "met", "missing", "float", "avail",
                    "avail_date", "n_out", "note"])
        for k, r in enumerate(rows, 1):
            w.writerow([k if r["S"] is not None else "", r["sym"], r.get("t"), _r(r.get("S")), _r(r.get("S_L")),
                        _r(r.get("D")), r.get("scan"), _r(r.get("rsi"), 1), " · ".join(r.get("met") or []),
                        " | ".join(r.get("missing") or []), r.get("float"), r.get("avail"), r.get("avail_date"),
                        r.get("n_out"), r["why"]])
    print("members", len(members), "screen", last, "scored", sum(1 for r in rows if r["S"] is not None))
    return rows, last


def _r(x, nd=4):
    return None if x is None else round(x, nd)


# ── guards (synthetic) ───────────────────────────────────────────────────────────────────────────────
def guards():
    fails = []

    def chk(name, ok, detail=""):
        print(("✅ " if ok else "❌ ") + name + ("" if ok else f"  [{detail}]"))
        if not ok:
            fails.append(name)
    import pandas as pd

    def pc(stage, ago, bounce, vs, held=0, branch=None):
        return {"stage": stage, "bottom_ago": ago, "bounce_pct": bounce, "vs_bottom_pct": vs, "held": held, "branch": branch}

    def cl(rsi=None, p=None, sr=None, gaps=None):
        return closeness({"rsi": rsi, "pc": p, "sweep_reclaimed": sr, "gaps_above": gaps})
    def near(a, b):
        return a is not None and abs(a - b) < 1e-9
    chk("SG1 RSI closeness: 27 ⟶ 1 · 40 ⟶ 0 · 33.5 ⟶ ½ · 20 ⟶ 1 · 45 ⟶ 0 (TG_2043)",
        near(cl(27)["RSI"], 1) and near(cl(40)["RSI"], 0) and near(cl(33.5)["RSI"], 0.5) and near(cl(20)["RSI"], 1)
        and near(cl(45)["RSI"], 0))
    chk("SG2 HOLD: 5 sessions ⟶ 1 · 3 ⟶ 0.6 · 0 ⟶ 0 · 9 ⟶ 1",
        near(cl(30, pc(1, 5, 0, 0))["HOLD"], 1) and near(cl(30, pc(1, 3, 0, 0))["HOLD"], 0.6)
        and near(cl(30, pc(1, 0, 0, 0))["HOLD"], 0) and near(cl(30, pc(1, 9, 0, 0))["HOLD"], 1))
    chk("SG3 CYC: retest after 15% ⟶ 1 · stage 1 at 7.5% ⟶ 0.25 · stage 2 at 20% giving back half ⟶ 0.75 · at the peak ⟶ 0.5",
        near(cl(30, pc(3, 9, 15, 2))["CYC"], 1) and near(cl(30, pc(1, 2, 7.5, 7.5))["CYC"], 0.25)
        and near(cl(30, pc(2, 6, 20, 10))["CYC"], 0.75) and near(cl(30, pc(2, 6, 20, 20))["CYC"], 0.5))
    chk("SG4 ZONE: 15% ⟶ 1 · 22.5% ⟶ ½ · 30% ⟶ 0 · 5% ⟶ 1",
        near(cl(30, pc(1, 2, 15, 15))["ZONE"], 1) and near(cl(30, pc(2, 2, 30, 22.5))["ZONE"], 0.5)
        and near(cl(30, pc(2, 2, 40, 30))["ZONE"], 0) and near(cl(30, pc(1, 2, 5, 5))["ZONE"], 1))
    chk("SG5 HOLDZ: retest held 3 ⟶ 1 · held 1 ⟶ ⅓ · before any retest ⟶ 0",
        near(cl(30, pc(4, 9, 20, 3, 3))["HOLDZ"], 1) and near(cl(30, pc(3, 9, 20, 3, 1))["HOLDZ"], 1 / 3)
        and near(cl(30, pc(2, 9, 20, 15, 5))["HOLDZ"], 0))
    chk("SG6 SWEEP: reclaimed ⟶ 1 · swept, not reclaimed ⟶ ½ · held ⟶ 0",
        near(cl(30, pc(3, 9, 20, 3, 1, "sweep"), True)["SWEEP"], 1)
        and near(cl(30, pc(3, 9, 20, 3, 1, "sweep"), False)["SWEEP"], 0.5)
        and near(cl(30, pc(3, 9, 20, 3, 1, "hold"), False)["SWEEP"], 0))
    chk("SG7 GAP above: some ⟶ 1 · none ⟶ 0 · unknown ⟶ None",
        near(cl(30, None, None, 2)["GAP"], 1) and near(cl(30, None, None, 0)["GAP"], 0) and cl(30)["GAP"] is None)
    w0 = {k: 1.0 for k in COMP_ORDER}
    c8 = cl(27, None, None, 0)
    chk("SG8 no cycle reading ⟶ its five components are None (not 0) and the level averages RSI and GAP only",
        all(c8[k] is None for k in ("HOLD", "CYC", "ZONE", "HOLDZ", "SWEEP")) and near(level(c8, w0), 0.5))
    chk("SG9 level = weighted mean of the known · all unknown ⟶ None · all-zero weights ⟶ None",
        near(level({"RSI": 1.0, "HOLD": 0.0, "CYC": None, "ZONE": None, "HOLDZ": None, "SWEEP": None, "GAP": None},
                   dict(w0, RSI=3.0)), 0.75)
        and level({k: None for k in COMP_ORDER}, w0) is None and level(c8, {k: 0.0 for k in COMP_ORDER}) is None)
    rt = {"rsi": 27.0, "pc": None, "sweep_reclaimed": None, "gaps_above": 1}
    rl = {"rsi": 40.0, "pc": None, "sweep_reclaimed": None, "gaps_above": 0}
    s10 = score_from(rt, rl, w0)
    chk("SG10 direction: S = S_L(t) + (S_L(t) − S_L(t−5)) — approaching the conditions adds · moving away subtracts",
        near(s10["S_L"], 1) and near(s10["D"], 1) and near(s10["S"], 2) and near(score_from(rl, rt, w0)["S"], -1)
        and score_from(rt, None, w0)["S"] is None)
    chk("SG11 scan BASE2 strict: RSI 32.99 ∧ drop 70 ⟶ 1 · RSI 33 ⟶ 0 · drop 69.99 ⟶ 0 · unknown ⟶ None",
        scan_flag({"rsi": 32.99, "drop52": 70.0}) == 1.0 and scan_flag({"rsi": 33.0, "drop52": 80.0}) == 0.0
        and scan_flag({"rsi": 20.0, "drop52": 69.99}) == 0.0 and scan_flag({"rsi": None, "drop52": 80.0}) is None)
    chk("SG12 matched AUC of one set: beats one, ties one, loses one (one unknown skipped) ⟶ ½",
        near(unit_auc(0.6, [0.5, 0.6, 0.7, None]), 0.5) and unit_auc(None, [0.1]) is None and unit_auc(0.5, [None]) is None)
    seen = set()

    def st13(us):
        v = sum(u["ev"]["S"] for u in us) / len(us)
        seen.add(round(v, 4))
        return v
    us13 = [{"sym": "A", "ev": {"S": 1.0}}, {"sym": "A", "ev": {"S": 1.0}}, {"sym": "B", "ev": {"S": 0.0}}]
    cluster_boot(us13, st13, reps=400, seed=1)
    chk("SG13 bootstrap resamples SYMBOLS (a symbol's two units move together: ⅔ appears · ⅓ never)",
        0.6667 in seen and 0.3333 not in seen and cluster_boot(us13, st13, reps=50, seed=3) == cluster_boot(us13, st13, reps=50, seed=3))
    chk("SG14 design MDE80 of the AUC: 31/155 ⟶ 0.1595 (≤ 0.20) · 12/60 ⟶ above 0.20",
        near(design_mde80(31, 155), 0.1595) and design_mde80(12, 60) > MDE_MAX and design_mde80(0, 5) is None)

    def blk(n, syms, mde, lo, lo2):
        return {"events": n, "symbols": syms, "design_mde80": mde, "auc": {"S": {"ci95": [lo, lo + 0.1]}},
                "delta_auc": {"S_minus_scan": {"ci95": [lo2, lo2 + 0.1]}}}
    ok_p, ok_i = blk(31, 31, 0.16, 0.55, 0.02), blk(25, 25, 0.17, 0.52, 0.01)
    chk("SG15 branches: floors ⟶ D · MDE above 0.20 ⟶ D · AUC low ≤ ½ ⟶ C · separates, not above the scan ⟶ B · both ⟶ A",
        branch(blk(29, 29, 0.1, 0.6, 0.1)) == "D" and branch(blk(31, 31, 0.21, 0.6, 0.1)) == "D"
        and branch(blk(31, 31, 0.16, 0.5, 0.1)) == "C" and branch(blk(31, 31, 0.16, 0.55, 0.0)) == "B"
        and branch(ok_p) == "A")
    chk("SG16 verdict by the weakest: identity below its floors caps A at A0 · identity C lowers A to C · primary C stays C",
        verdict(ok_p, ok_i) == "A0" and verdict(ok_p, blk(31, 31, 0.16, 0.45, 0.1)) == "C"
        and verdict(blk(31, 31, 0.16, 0.45, 0.1), ok_p) == "C"
        and verdict(ok_p, blk(31, 31, 0.16, 0.55, -0.05)) == "B")
    w = weights()
    chk("SG17 weights recomputed from the ledger, the matrix and the wait tags = the frozen ones · GAP (INFORMATIONAL) lowest",
        w == WEIGHTS_FROZEN and min(w, key=w.get) == "GAP"
        and contradicted_rules() == ["H-D2", "R-RSI-ABOVE-40-READY"]
        and all(k not in COMPONENTS for k in contradicted_rules()))
    rng = random.Random(7)
    px, rows = 10.0, []
    for k in range(140):
        px *= math.exp(rng.gauss(-0.004 if k < 90 else 0.003, 0.05))
        rows.append([px * 1.01, px * 1.05, px * 0.95, px])
    idx = pd.bdate_range("2026-01-01", periods=140)
    df = pd.DataFrame(rows, columns=["Open", "High", "Low", "Close"], index=idx)
    df["Volume"] = 1e5
    a = raw_at(df, 120)
    df2 = df.copy()
    df2.iloc[121:, :4] = df2.iloc[121:, :4] * 3.0
    b = raw_at(df2, 120)
    chk("SG18 no look-ahead: readings at t do not move when every bar after t changes",
        a["rsi"] == b["rsi"] and a["pc"] == b["pc"] and a["gaps_above"] == b["gaps_above"] and a["drop52"] == b["drop52"])
    sp = [[idx[110].date().isoformat(), 0.1]]
    df3 = df.copy()
    df3.iloc[110:, :4] = df3.iloc[110:, :4] * 10.0
    u_bad, why_bad = unit_scores(df3, 120, sp, {"S": w0})
    u_ok, why_ok = unit_scores(df, 120, sp, {"S": w0})
    u_sh, why_sh = unit_scores(df, 60, None, {"S": w0})
    chk("SG19 a reverse split not adjusted inside the window ⟶ unknown · the adjusted series reads · too little history ⟶ unknown",
        u_bad is None and why_bad == "split_unadjusted" and why_ok == "ok" and u_ok["S"] is not None
        and u_sh is None and why_sh == "short_history")
    g = gaps_text({"rsi": 31.0, "pc": pc(2, 2, 10, 22)}, {"GAP": 0.0})
    chk("SG20 «باقي له …»: RSI 31 ⟶ باقي 4.0 · ثبات 2 من 5 ⟶ باقي 3 · صعود 10% ⟶ باقي 5.0% · فوق 22% ⟶ نزول 7.0% · لا فجوة",
        any("باقي 4.0 نقطة" in x for x in g) and any("باقي 3" in x and "الثبات" in x for x in g)
        and any("باقي 5.0%" in x for x in g) and any("نزول 7.0%" in x for x in g) and any("لا فجوة" in x for x in g)
        and gaps_text({"rsi": 25.0, "pc": pc(4, 9, 20, 3, 3)}, {"GAP": 1.0}) == [])
    import tempfile

    def code(fn):
        try:
            fn()
            return 0
        except SystemExit as e:
            return e.code
    tmp = tempfile.NamedTemporaryFile("wb", delete=False, suffix=".md")
    tmp.write(b"x")
    tmp.close()
    pinned = open(PREREG, "rb").read() if os.path.exists(PREREG) else b""
    chk("SG21 contract pin ⟶ exit 9 · not on origin/main ⟶ 9 · altered on main ⟶ 9 · pinned bytes on main ⟶ passes",
        code(lambda: check_pins(tmp.name, "0" * 64)) == 9 and code(lambda: check_merged(lambda: None)) == 9
        and code(lambda: check_merged(lambda: pinned + b" ")) == 9
        and (code(lambda: check_merged(lambda: pinned)) == 0) == (hashlib.sha256(pinned).hexdigest() == PREREG_SHA256))
    os.unlink(tmp.name)
    chk("SG22 constants (k = 2 · lag 5 · RSI 27/40 · hold 5 · test 15% · zone 15% · hold-in-zone 3 · scan 33/70 · MDE 0.20)",
        (K_GAP, DIR_LAG, RSI_FULL, RSI_ZERO, HOLD_FULL, TEST_FULL, ZONE_TOP, ZONE_DECAY, HOLDZ_FULL, SCAN_RSI, SCAN_DROP,
         MDE_MAX, BOOT, SEED) == (2, 5, 27.0, 40.0, 5, 15.0, 15.0, 15.0, 3, 33.0, 70.0, 0.20, 4000, 20261014))

    print(f"\nguards failed: {len(fails)}")
    return fails


if __name__ == "__main__":
    if "--guards" in sys.argv:
        sys.exit(1 if guards() else 0)
    if "--today" in sys.argv:
        today()
        sys.exit(0)
    run()
