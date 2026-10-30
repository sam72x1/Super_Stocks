# -*- coding: utf-8 -*-
"""🕯️🔬 `T-WICK` «عمى الذيل» — قياسُ الذيل العلويّ فوق الإغلاق في الجلسات الخمس قبل القرار (العقد `T_WICK_prereg.md` · مدموجٌ قبل أيّ رقم).

قراءةٌ وقياسٌ فقط: لا يُستورَد في الإنتاج · لا يكتب حالةً · لا تلغرام · لا بوّابة ولا عرض · ولا يُشحَن منه شيء.
المجتمعُ ودوالُّه من الجزء ب **بالاسم** (`rebuild.base2_fire` · `new_entries` · `exploded` · `row_guards` · `gaps` · `p3_days` · `pair_flags` ·
`sessions_between` · `_first_sessions`) · والإحصاءُ من `split_gates.py` بالاسم · والجديدُ وحدَه تعريفُ الذيل (`wick_max`).

الأوضاع (`WK_MODE`):
    units         بناءُ الوحدات من ملفّات المستودع وتاريخ git (محلّيًّا) ⟵ data/units.json
    units_eval    ① الذيلُ لكلّ وحدة (Polygon) ⟵ RESULT_JSON
    pop_prep      ②③ اللقطاتُ والتقسيماتُ والجلسات ⟵ out/prep.json.gz
    pop_shard     ②③ شريحةُ رموز (SHARD · NSHARDS) ⟵ out/shard_NN.json.gz
    pop_assemble  ②③ الهويّةُ والحصصُ والفواصلُ والتقاطعُ والحكم ⟵ RESULT_JSON
    guards        حرّاسٌ اصطناعيّة بلا شبكة (WG…)
"""
import csv
import datetime as dt
import gzip
import hashlib
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
CONTRACT = os.path.join(HERE, "T_WICK_prereg.md")
UNITS = os.path.join(HERE, "data", "units.json")
OUT = os.path.join(HERE, "out")
CONTRACT_SHA = "be3a6af8d424651b1c6f558a7f66893d7851b9738f3d63ad4d00932961981fa0"           # بصمةُ العقد (TWK1)
UNITS_SHA = "241c06fd50fdf9810d81879a75954510170379b4b1314afa99588605073ad5df"              # بصمةُ قائمة الوحدات (TWK2)
SEED = 20261030
WIN5 = 5                           # «آخر 5 جلسات»
RUNGS = (0.30, 0.50, 0.80)         # §① الدرجات
GOV = 0.50                         # §① الحاكمة (نصُّ الأمر)
BINS = (0.30, 0.50, 0.80)          # §④ الجرعة: دون 30 · 30-50 · 50-80 · 80 فأكثر
ADDS_FROM, ADDS_TO = "2026-08-01", "2026-10-30"
UNIT_BARS_FROM = "2026-01-02"     # أبكرُ `first_ready` 2026-06-21 ⟵ أكثرُ من خمس جلساتٍ قبله
EXP_PCT = 50.0                     # «≥50% خلال 20 جلسة» (نصُّ الأمر) = `EXPLOSION_PCT` في الجزء ب
PUB_ENTRIES = {"TRAIN": 3267, "VAL": 1925, "TEST": 2682}   # §③ بوّابةُ الهويّة (الجزء ب: bases ‏+ test)
IDENT_TOL = 0.02
MIN_GROUP, MIN_TICKERS = 30, 15
COVERAGE_FLOOR = 0.85
NSHARDS = 8                        # الشرائح (wick.yml)


def log(*a):
    print(*a, flush=True)


def _sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def units_sha(blob):
    return hashlib.sha256(json.dumps(blob, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


_MODS = {}


def _load(name, rel):
    if name not in _MODS:
        import importlib.util as iu
        spec = iu.spec_from_file_location(name, os.path.join(ROOT, *rel))
        m = iu.module_from_spec(spec)
        spec.loader.exec_module(m)
        _MODS[name] = m
    return _MODS[name]


def _rb():
    """`fm_forensics/rebuild/rebuild.py` بالاسم (الجزء ب) — مرّةً واحدة."""
    return _load("rebuild_wk", ("fm_forensics", "rebuild", "rebuild.py"))


def _sg():
    """`fm_forensics/split_gates/split_gates.py` بالاسم (الإحصاء)."""
    return _load("split_gates_wk", ("fm_forensics", "split_gates", "split_gates.py"))


def _S():
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    os.environ.setdefault("FAISAL_ONLY", "0")
    import Super_stock as S
    return S


# ── نقيّة: الذيل ─────────────────────────────────────────────────────────────────────────────────────
def wick_max(h, c, lo, hi):
    """§① أكبرُ ذيلٍ علويّ High/Close − 1 على الشموع [lo، hi) ⟵ (النسبة، فهرسُ الشمعة) أو (None، None)."""
    best, at = None, None
    for j in range(max(0, lo), max(0, hi)):
        if c[j] and c[j] > 0 and h[j] == h[j] and c[j] == c[j]:
            w = h[j] / c[j] - 1.0
            if best is None or w > best:
                best, at = w, j
    return best, at


def unit_window(dates, D, ref_bar=None):
    """§② نهايةُ النافذة (حصريّة): `ref_bar` شاملًا إن وُجد · وإلّا الجلساتُ قبل D حصرًا."""
    import bisect
    if ref_bar:
        return bisect.bisect_right(dates, ref_bar), "ref_bar"
    return bisect.bisect_left(dates, D), "before_D"


# ── الوحدات (محلّيًّا · من الملفّات وتاريخ git) ────────────────────────────────────────────────────────
def build_units(root=ROOT, rev="origin/main"):
    rev = subprocess.run(["git", "-C", root, "rev-parse", rev], capture_output=True, text=True).stdout.strip()
    ready = [{"kind": "ready", "sym": r["symbol"], "D": r["first_ready"], "ref_bar": None}
             for r in csv.DictReader(open(os.path.join(root, "fm_forensics", "READY_NOW_OUTCOMES.csv"), encoding="utf-8"))]
    log_ = subprocess.run(["git", "-C", root, "log", "--reverse", "--format=%H %cI", "--since=2026-07-20", rev, "--",
                           "weekly_watchlist.json"], capture_output=True, text=True).stdout.split("\n")
    first = {}
    for ln in log_:
        if not ln.strip():
            continue
        h, ts = ln.split()
        try:
            wl = json.loads(subprocess.run(["git", "-C", root, "show", f"{h}:weekly_watchlist.json"], capture_output=True,
                                           text=True).stdout)
        except ValueError:
            continue
        for s in wl.get("stocks") or []:
            sym, add = s.get("symbol"), str(s.get("added") or "")
            if not sym or not (ADDS_FROM <= add <= ADDS_TO):
                continue
            first.setdefault((sym, add), {"kind": "add", "sym": sym, "D": add, "ref_bar": s.get("ref_bar"), "first_seen": ts})
    adds = [first[k] for k in sorted(first, key=lambda k: (k[1], k[0]))]
    frozen = json.load(open(os.path.join(root, "fm_forensics", "chase35", "data", "input.json"), encoding="utf-8"))["adds"]
    fk = {(a["sym"], a["added"]): a.get("ref_bar") for a in frozen}
    ek = {(a["sym"], a["D"]): a.get("ref_bar") for a in adds if a["D"] <= max(x[1] for x in fk)}
    ident = {"frozen": len(fk), "extracted_same_span": len(ek), "missing": sorted(set(fk) - set(ek)),
             "extra": sorted(set(ek) - set(fk)), "ref_bar_diff": sorted(k for k in set(fk) & set(ek) if fk[k] != ek[k])}
    return {"ready": ready, "adds": adds, "n_ready": len(ready), "n_adds": len(adds), "identity_vs_part_a": ident, "rev": rev,
            "adds_window": [ADDS_FROM, ADDS_TO]}


# ── ① الوحدات ─────────────────────────────────────────────────────────────────────────────────────────
def eval_unit(u, rows, pct=EXP_PCT):
    """§② ذيلُ الوحدة على شموعها ‏+ الانفجارُ الوصفيّ من أوّل جلسةٍ بعد النافذة (`rebuild.exploded` بالاسم)."""
    RB = _rb()
    dates = [x[0] for x in rows]
    h = [float(x[2]) for x in rows]
    c = [float(x[4]) for x in rows]
    end, how = unit_window(dates, u["D"], u.get("ref_bar"))
    w, j = wick_max(h, c, end - WIN5, end)
    rec = {"kind": u["kind"], "sym": u["sym"], "D": u["D"], "ref_bar": u.get("ref_bar"), "window": how,
           "bars_in_window": max(0, min(WIN5, end)), "last_bar": dates[end - 1] if end >= 1 else None}
    if w is None:
        rec["nodata"] = True
        return rec
    rec.update({"wick": round(w, 4), "wick_date": dates[j], "high": round(h[j], 4), "close": round(c[j], 4),
                "r30": w >= 0.30, "r50": w >= 0.50, "r80": w >= 0.80,
                "exploded": RB.exploded(rows, dates[end], pct) if end < len(dates) else None})
    return rec


def _bars(sym, a, b, key):
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    import pit_history as PH
    RB = _rb()
    df, why = PH.polygon_daily(sym, a, b, key)
    return (RB._rows(df) if df is not None else []), why


def mode_units_eval(key, units=None, fetch_bars=None):
    units = units or json.load(open(UNITS, encoding="utf-8"))
    allu = units["ready"] + units["adds"]
    syms = sorted({u["sym"] for u in allu})
    today = dt.date.today().isoformat()
    bars, diag = {}, {}
    for s in syms:
        rows, why = fetch_bars(s) if fetch_bars else _bars(s, UNIT_BARS_FROM, today, key)
        bars[s] = rows
        diag[why.split("(")[0]] = diag.get(why.split("(")[0], 0) + 1
    out = []
    for u in allu:
        rows = bars.get(u["sym"]) or []
        out.append(eval_unit(u, rows) if rows else {"kind": u["kind"], "sym": u["sym"], "D": u["D"], "ref_bar": u.get("ref_bar"),
                                                     "nodata": True})
    summ = {}
    for kind in ("ready", "add"):
        xs = [r for r in out if r["kind"] == kind]
        ok = [r for r in xs if not r.get("nodata")]
        summ[kind] = {"units": len(xs), "evaluated": len(ok), "nodata": len(xs) - len(ok),
                      **{f"r{int(g * 100)}": sum(1 for r in ok if r[f"r{int(g * 100)}"]) for g in RUNGS},
                      "exploded_r50": sum(1 for r in ok if r["r50"] and r.get("exploded")),
                      "labelled_r50": sum(1 for r in ok if r["r50"] and r.get("exploded") is not None)}
    return {"mode": "units_eval", "contract_sha": _sha(CONTRACT), "units_sha": units_sha(units), "symbols": len(syms),
            "bars_diag": diag, "summary": summ, "units": out}


# ── ②③ المجتمع ───────────────────────────────────────────────────────────────────────────────────────
def mode_pop_prep(key):
    RB = _rb()
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    import market_calendar as MC
    import pit_universe as PU
    import pit_snapshot as PS
    months = [(2022, 12)] + [(y, m) for y in (2023, 2024, 2025) for m in range(1, 13)]
    snaps, union = {}, set()
    for d in RB._first_sessions(months, MC):
        rows = PU.fetch_universe(d, key)
        keep = sorted(r["ticker"] for r in rows if r.get("type") in ("CS", "ADRC"))
        snaps[d[:7]] = keep
        union |= set(keep)
        log(f"prep snapshot {d}: CS/ADRC {len(keep)}")
    sp_by = {}
    for r in PS.fetch_all_splits(RB.BARS_FROM, RB.BARS_TO, key):
        try:
            if r["ticker"] in union:
                sp_by.setdefault(r["ticker"], []).append([r["execution_date"], float(r["split_to"]) / float(r["split_from"])])
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            continue
    sess = RB.sessions_between(RB.SESS_FROM, RB.TEST[1], MC)
    prep = {"snapshots": snaps, "union": sorted(union), "splits": sp_by, "sessions": sess}
    os.makedirs(OUT, exist_ok=True)
    with gzip.open(os.path.join(OUT, "prep.json.gz"), "wt", encoding="utf-8") as fh:
        json.dump(prep, fh)
    log(f"prep: union {len(union)} · splits for {len(sp_by)} · sessions {len(sess)}")
    return {"mode": "pop_prep", "union": len(union), "split_symbols": len(sp_by), "sessions": len(sess)}


def symbol_entries(rows, splits_sym, member_days, sess, S, G5, pct):
    """§③ إدخالاتُ BASE2 الجديدة لرمزٍ على [TRAIN[0]، TEST[1]] بدوالّ الجزء ب بالاسم ‏+ الذيلُ وP3 والزخم والنتيجة:
    [D، y، wick، يومُ الذيل، ret20، I_P3، الفترة]."""
    import bisect
    import pandas as pd
    RB = _rb()
    if not rows:
        return []
    dates = [x[0] for x in rows]
    c = [float(x[4]) for x in rows]
    h = [float(x[2]) for x in rows]
    v = [float(x[5]) for x in rows]
    rsi = [float(z) for z in S.rsi(pd.Series(c, dtype=float), 14).values]
    unadj = G5.split_unadjusted(rows, splits_sym, "0000-00-00", "9999-99-99")
    gp = RB.gaps(rows)
    p3 = RB.p3_days(c, h, v)
    fire, idx = [], {}
    for d in member_days:
        i = bisect.bisect_left(dates, d)
        if i < 1 or (dt.date.fromisoformat(d) - dt.date.fromisoformat(dates[i - 1])).days > RB.STALE_DAYS:
            continue
        sp, gq = RB.row_guards(dates, i, d, unadj, gp)
        if sp or gq:
            continue
        if RB.base2_fire(rsi, c, h, i):
            fire.append(d)
            idx[d] = i
    out = []
    for d in RB.new_entries(fire, sess):
        if not (RB.TRAIN[0] <= d <= RB.TEST[1]):
            continue
        i = idx[d]
        w, j = wick_max(h, c, i - WIN5, i)
        r20 = (c[i - 1] / c[i - 21] - 1.0) if i >= 21 and c[i - 21] > 0 else None
        per = "TRAIN" if d <= RB.TRAIN[1] else ("VAL" if d <= RB.VAL[1] else "TEST")
        out.append([d, RB.exploded(rows, d, pct), None if w is None else round(w, 6), None if j is None else dates[j],
                    None if r20 is None else round(r20, 6), RB.pair_flags((p3,), i)[0], per])
    return out


def mode_pop_shard(key, shard, nshards, fetch_bars=None, prep=None):
    RB = _rb()
    S = _S()
    G5 = RB._gen5_ext()
    pct = EXP_PCT
    if prep is None:
        with gzip.open(os.path.join(OUT, "prep.json.gz"), "rt", encoding="utf-8") as fh:
            prep = json.load(fh)
    member = {}
    for d in prep["sessions"]:
        for s in prep["snapshots"].get(d[:7], []):
            member.setdefault(s, []).append(d)
    syms = prep["union"][shard::nshards]
    res, diag = {}, {}
    t0 = time.time()
    for n, s in enumerate(syms):
        rows, why = fetch_bars(s) if fetch_bars else _bars(s, RB.BARS_FROM, RB.BARS_TO, key)
        diag[why.split("(")[0]] = diag.get(why.split("(")[0], 0) + 1
        try:
            e = symbol_entries(rows, prep["splits"].get(s), member.get(s, []), prep["sessions"], S, G5, pct)
        except Exception as ex:                                  # noqa: BLE001
            diag[f"err:{type(ex).__name__}"] = diag.get(f"err:{type(ex).__name__}", 0) + 1
            continue
        if e:
            res[s] = e
        if n % 50 == 0:
            log(f"shard {shard}: {n + 1}/{len(syms)} · {round(time.time() - t0)}s")
    out = {"shard": shard, "symbols": len(syms), "bars_diag": diag, "res": res}
    if fetch_bars is None:
        os.makedirs(OUT, exist_ok=True)
        with gzip.open(os.path.join(OUT, f"shard_{shard:02d}.json.gz"), "wt", encoding="utf-8") as fh:
            json.dump(out, fh)
    return out


def flag_items(ents, rung, cuts):
    """(له ذيل، انفجر، رمز، طبقةُ الزخم) — الدوالُّ الإحصائيّة من `split_gates` بالاسم تقرأ هذا الشكل."""
    SG = _sg()
    return [(e["wick"] is not None and e["wick"] >= rung, bool(e["y"]), e["sym"], SG.mom_bin(e["ret20"], cuts)) for e in ents]


def rung_stats(ents, rung, cuts, gates_ok):
    SG = _sg()
    items = flag_items(ents, rung, cuts)
    w = [e for e, it in zip(ents, items) if it[0]]
    n = [e for e, it in zip(ents, items) if not it[0]]

    def grp(xs):
        k = sum(1 for e in xs if e["y"])
        return {"n": len(xs), "tickers": len({e["sym"] for e in xs}), "exp": k,
                "share": round(k / len(xs), 4) if xs else None, "wilson": SG.wilson(k, len(xs))}

    raw, st = SG.delta_raw(items), SG.delta_strat(items)
    raw_ci, st_ci = SG.cluster_boot(items, SG.delta_raw), SG.cluster_boot(items, SG.delta_strat)
    years = {}
    for y in ("2023", "2024", "2025"):
        yi = [it for it, e in zip(items, ents) if e["D"][:4] == y]
        dy = SG.delta_raw(yi)
        years[y] = {"n_wick": sum(1 for it in yi if it[0]), "n_none": sum(1 for it in yi if not it[0]),
                    "delta": None if dy is None else round(dy, 4)}
    srt = sorted([e for e in ents if e["ret20"] is not None], key=lambda e: -e["ret20"])[:len(w)]
    floors = len(w) >= MIN_GROUP and len({e["sym"] for e in w}) >= MIN_TICKERS
    se = None if raw_ci[0] is None else (raw_ci[1] - raw_ci[0]) / (2 * 1.96)
    return {"rung": rung, "wick": grp(w), "none": grp(n), "delta_raw": None if raw is None else round(raw, 4), "delta_raw_ci": raw_ci,
            "delta_strat": None if st is None else round(st, 4), "delta_strat_ci": st_ci, "years": years,
            "cmom": grp(srt), "mde80": None if se is None else round(2.8 * se, 4), "floors_ok": floors,
            "verdict": wick_verdict(raw, raw_ci, st, st_ci, [v["delta"] for v in years.values()], floors and gates_ok)}


VERDICTS = {"تُسقط أفضل": "الذيلُ يرفع", "تحمي": "الذيلُ يخفض", "لا فرق قابل للكشف": "لا فرق قابل للكشف", "لا قياس": "لا قياس"}


def wick_verdict(raw, raw_ci, st, st_ci, years, ok):
    """§④ بالأضعف بقاعدة `split_gates.verdict` نفسِها (Δ = له ذيل − لا ذيل) ⟵ أسماءُ هذا العقد."""
    SG = _sg()
    return VERDICTS[SG.verdict(raw, raw_ci, st, st_ci, years, ok, True)]


def dose(ents):
    SG = _sg()
    out = {}
    lab = ("دون 30%", "30-50%", "50-80%", "80% فأكثر")
    for k, name in enumerate(lab):
        lo = 0.0 if k == 0 else BINS[k - 1]
        hi = BINS[k] if k < len(BINS) else None
        xs = [e for e in ents if e["wick"] is not None and (e["wick"] >= lo if k else True) and (hi is None or e["wick"] < hi)]
        kx = sum(1 for e in xs if e["y"])
        out[name] = {"n": len(xs), "exp": kx, "share": round(kx / len(xs), 4) if xs else None, "wilson": SG.wilson(kx, len(xs))}
    return out


def intersection(ents, cuts, rung=GOV):
    """§⑤ التقاطع مع P3 · وΔ كلٍّ مطبَّقًا على طبقتَي الآخر · والتصنيف."""
    SG = _sg()
    W = [e["wick"] is not None and e["wick"] >= rung for e in ents]
    P = [bool(e["p3"]) for e in ents]
    cells = {}
    for a in (1, 0):
        for b in (1, 0):
            xs = [e for e, w, p in zip(ents, W, P) if int(w) == a and int(p) == b]
            kx = sum(1 for e in xs if e["y"])
            cells[f"W{a}P{b}"] = {"n": len(xs), "exp": kx, "share": round(kx / len(xs), 4) if xs else None}
    n11, n10, n01, n00 = (cells[k]["n"] for k in ("W1P1", "W1P0", "W0P1", "W0P0"))
    den = ((n11 + n10) * (n01 + n00) * (n11 + n01) * (n10 + n00)) ** 0.5
    phi = round((n11 * n00 - n10 * n01) / den, 4) if den else None
    it_w = [(w, bool(e["y"]), e["sym"], int(p)) for e, w, p in zip(ents, W, P)]           # الذيلُ مطبَّقًا على طبقتَي P3
    it_p = [(p, bool(e["y"]), e["sym"], int(w)) for e, w, p in zip(ents, W, P)]           # P3 مطبَّقًا على طبقتَي الذيل
    it_w0 = [x for x in it_w if x[3] == 0]
    dw, dp = SG.delta_strat(it_w), SG.delta_strat(it_p)
    dw_ci, dp_ci = SG.cluster_boot(it_w, SG.delta_strat), SG.cluster_boot(it_p, SG.delta_strat)
    rw, rp = SG.delta_raw(it_w), SG.delta_raw(it_p)
    rw_ci, rp_ci = SG.cluster_boot(it_w, SG.delta_raw), SG.cluster_boot(it_p, SG.delta_raw)
    return {"cells": cells, "p_p3_given_w": round(n11 / (n11 + n10), 4) if (n11 + n10) else None,
            "p_w_given_p3": round(n11 / (n11 + n01), 4) if (n11 + n01) else None, "phi": phi,
            "dW_given_P3": None if dw is None else round(dw, 4), "dW_given_P3_ci": dw_ci,
            "dP3_given_W": None if dp is None else round(dp, 4), "dP3_given_W_ci": dp_ci,
            "dW_raw": None if rw is None else round(rw, 4), "dW_raw_ci": rw_ci, "dP3_raw": None if rp is None else round(rp, 4),
            "dP3_raw_ci": rp_ci, "dW_within_P3_0": None if SG.delta_raw(it_w0) is None else round(SG.delta_raw(it_w0), 4),
            "class": classify(dw_ci, dp_ci, rw_ci, rp_ci)}


def classify(dw_ci, dp_ci, rw_ci, rp_ci):
    """§⑤ التصنيفُ بالأضعف."""
    def above(ci):
        return bool(ci and ci[0] is not None and ci[0] > 0)
    if above(dw_ci) and above(dp_ci):
        return "مستقلّ"
    if above(dw_ci):
        return "الذيلُ يحمل ما في الزوج"
    if above(dp_ci):
        return "الزوجُ يحمل ما في الذيل"
    if above(rw_ci) or above(rp_ci):
        return "نفسُ الظاهرة"
    return "لا يُحكم"


def mode_pop_assemble(shards=None):
    SG = _sg()
    if shards is None:
        import glob
        shards = []
        for f in sorted(glob.glob(os.path.join(OUT, "**", "shard_*.json.gz"), recursive=True)):
            with gzip.open(f, "rt", encoding="utf-8") as fh:
                shards.append(json.load(fh))
    ents, diag, nsym = [], {}, 0
    for sh in shards:
        nsym += sh["symbols"]
        for k, v in sh["bars_diag"].items():
            diag[k] = diag.get(k, 0) + v
        for s, rows in sh["res"].items():
            for d, y, w, wd, r20, p3, per in rows:
                ents.append({"sym": s, "D": d, "y": y, "wick": w, "wick_date": wd, "ret20": r20, "p3": p3, "per": per})
    counts = {p: sum(1 for e in ents if e["per"] == p) for p in PUB_ENTRIES}
    ident = {p: {"n": counts[p], "pub": PUB_ENTRIES[p], "ok": abs(counts[p] - PUB_ENTRIES[p]) <= IDENT_TOL * PUB_ENTRIES[p]}
             for p in PUB_ENTRIES}
    ident_ok = all(v["ok"] for v in ident.values())
    cov = (diag.get("ok", 0) / nsym) if nsym else 0.0
    lab = [e for e in ents if e["y"] is not None and e["wick"] is not None]
    cuts = SG.mom_cuts([e["ret20"] for e in lab])
    gates_ok = ident_ok and cov >= COVERAGE_FLOOR
    out = {"mode": "pop_assemble", "contract_sha": _sha(CONTRACT), "symbols": nsym, "bars_diag": diag, "coverage": round(cov, 4),
           "coverage_ok": cov >= COVERAGE_FLOOR, "identity": ident, "identity_ok": ident_ok, "entries": len(ents),
           "labelled": len(lab), "unlabelled": len(ents) - len(lab), "mom_cuts": [round(x, 4) for x in cuts]}
    if not gates_ok:
        out["verdict"] = "لا قياس"
        return out
    out["rungs"] = {f"r{int(g * 100)}": rung_stats(lab, g, cuts, gates_ok) for g in RUNGS}
    out["verdict"] = out["rungs"]["r50"]["verdict"]
    out["dose"] = dose(lab)
    out["intersection"] = intersection(lab, cuts) if out["verdict"] != "لا قياس" else None
    out["intersection_class"] = out["intersection"]["class"] if out["intersection"] else "لا يُحكم"
    return out


# ── الحرّاس الاصطناعيّة (بلا شبكة) ──────────────────────────────────────────────────────────────────────
def guards():
    ok = []

    def chk(name, cond):
        ok.append((name, bool(cond)))
        log(("✅" if cond else "❌"), name)

    # WG1 الذيلُ = High/Close − 1 للشمعة نفسِها · والنافذةُ [lo، hi) لا تشمل hi
    h = [1.0, 1.1, 3.10, 1.2, 1.0, 5.0]
    c = [1.0, 1.0, 1.78, 1.1, 1.0, 1.0]
    w, j = wick_max(h, c, 0, 5)
    chk("WG1 wick_max: CETX 3.10/1.78 ⟵ 74.2% ويومُه · وشمعةُ hi خارجة", j == 2 and abs(w - (3.10 / 1.78 - 1)) < 1e-9)
    # WG2 نافذةُ الوحدة: ref_bar شاملًا · وبدونه قبل D حصرًا
    ds = ["2026-10-26", "2026-10-27", "2026-10-28", "2026-10-29", "2026-10-30"]
    chk("WG2 unit_window", unit_window(ds, "2026-10-30", "2026-10-29") == (4, "ref_bar")
        and unit_window(ds, "2026-10-30") == (4, "before_D") and unit_window(ds, "2026-10-29", None) == (3, "before_D"))
    # WG3 symbol_entries: إدخالٌ BASE2 على شموعٍ اصطناعيّة · والذيلُ من [D−5، D−1] لا من D
    import pandas as pd
    S = _S()
    G5 = _rb()._gen5_ext()
    days = pd.bdate_range("2022-01-03", "2023-06-30")
    rows = []
    for k, d in enumerate(days):
        cc = 10.0 if k < 200 else max(1.0, 10.0 - (k - 200) * 0.06)
        hh = cc * 1.01
        rows.append((d.date().isoformat(), cc, hh, cc * 0.99, cc, 1e5))
    dd = [r[0] for r in rows]
    ent0 = symbol_entries(rows, [], [d for d in dd if d >= "2023-01-03"], dd, S, G5, 50.0)
    if ent0:
        d0 = ent0[0][0]
        i0 = dd.index(d0)
        rows2 = list(rows)
        r = rows2[i0 - 2]
        rows2[i0 - 2] = (r[0], r[1], r[4] * 1.6, r[3], r[4], r[5])           # ذيلٌ 60% قبل D بجلستين
        r = rows2[i0]
        rows2[i0] = (r[0], r[1], r[4] * 3.0, r[3], r[4], r[5])                # ذيلٌ 200% يومَ D نفسَه (خارج النافذة)
        ent1 = symbol_entries(rows2, [], [d for d in dd if d >= "2023-01-03"], dd, S, G5, 50.0)
        e1 = next((e for e in ent1 if e[0] == d0), None)
    else:
        e1 = None
    i0 = dd.index(ent0[0][0]) if ent0 else 0
    chk("WG3 symbol_entries: إدخالٌ BASE2 والذيلُ 60% من D−2 لا 200% من D · وret20 = Close(D−1)÷Close(D−21)−1 · وصمتُ 20 جلسة بين الإدخالات",
        bool(ent0) and e1 is not None and abs(e1[2] - 0.6) < 1e-6 and e1[3] == dd[i0 - 2] and e1[6] == "TRAIN"
        and abs(e1[4] - round(rows[i0 - 1][4] / rows[i0 - 21][4] - 1, 6)) < 1e-9
        and all(dd.index(y[0]) - dd.index(x[0]) > 20 for x, y in zip(ent0, ent0[1:])))
    # WG8 حارسا الجزء ب: فجوةٌ أطولُ من 15 يومًا قبل D بأقلَّ من 60 يومًا ⟵ لا إدخال (`row_guards`) · والزوجُ P3 يُقرأ من [D−5، D−1]
    k = 327
    m0 = [d for d in dd if d >= dd[k + 9]]
    base = symbol_entries(rows, [], m0, dd, S, G5, 50.0)
    rows3 = list(rows)
    r = rows3[k]
    rows3[k] = (r[0], r[1], r[2], r[3], r[4], r[5] * 100.0)                 # سبايكُ حجمٍ يومَ k ⟵ زنادُ P3 بعد هبوط 20%
    sp3 = symbol_entries(rows3, [], m0, dd, S, G5, 50.0)
    gap = [x for j, x in enumerate(rows) if not (k - 15 <= j < k)]          # ثلاثة أسابيع بلا شموع قبل D بنحو شهر
    gp = symbol_entries(gap, [], m0, [x[0] for x in gap], S, G5, 50.0)
    chk("WG8 الزوجُ P3 بلا سبايك 0 ومعه 1 · والفجوةُ تُسقط الإدخال (`row_guards`)",
        bool(base) and bool(sp3) and base[0][0] == sp3[0][0] == dd[k + 9] and base[0][5] == 0 and sp3[0][5] == 1
        and not any(e[0] == dd[k + 9] for e in gp))
    # WG4 الحكمُ بالأضعف بأسماء العقد
    chk("WG4 wick_verdict", wick_verdict(0.2, (0.05, 0.3), 0.15, (0.01, 0.3), [0.1, 0.2, -0.1], True) == "الذيلُ يرفع"
        and wick_verdict(-0.2, (-0.3, -0.05), -0.15, (-0.3, -0.01), [-0.1, -0.2, 0.1], True) == "الذيلُ يخفض"
        and wick_verdict(0.2, (0.05, 0.3), 0.15, (-0.01, 0.3), [0.1, 0.2, 0.1], True) == "لا فرق قابل للكشف"
        and wick_verdict(0.2, (0.05, 0.3), 0.15, (0.01, 0.3), [0.1, 0.2, 0.1], False) == "لا قياس")
    # WG5 التصنيف
    chk("WG5 classify", classify((0.01, 0.2), (0.02, 0.3), (0.1, 0.3), (0.1, 0.3)) == "مستقلّ"
        and classify((0.01, 0.2), (-0.02, 0.3), None, None) == "الذيلُ يحمل ما في الزوج"
        and classify((-0.01, 0.2), (0.02, 0.3), None, None) == "الزوجُ يحمل ما في الذيل"
        and classify((-0.01, 0.2), (-0.02, 0.3), (0.05, 0.2), (-0.1, 0.2)) == "نفسُ الظاهرة"
        and classify((-0.01, 0.2), (-0.02, 0.3), (-0.05, 0.2), (-0.1, 0.2)) == "لا يُحكم")
    # WG6 التقاطع: الذيلُ = P3 تمامًا ⟵ phi = 1 وΔ الذيل داخل طبقات P3 لا تُعرَّف
    ents = []
    for k in range(200):
        f = k % 4 == 0
        ents.append({"sym": f"T{k}", "y": (k % 3 == 0) if f else (k % 7 == 0), "wick": 0.6 if f else 0.1, "ret20": 0.0, "p3": int(f)})
    it = intersection(ents, [])
    chk("WG6 intersection: تطابقُ الذيل وP3 ⟵ phi 1 وΔ مطبَّقٌ غيرُ معرَّف", it["phi"] == 1.0 and it["dW_given_P3"] is None
        and it["cells"]["W1P0"]["n"] == 0 and it["cells"]["W0P1"]["n"] == 0)
    # WG7 بوّابةُ الهويّة: عددٌ خارج 2% ⟵ «لا قياس»
    fake = {"shard": 0, "symbols": 10, "bars_diag": {"ok": 10}, "res": {"AAA": [["2023-02-01", True, 0.6, "2023-01-30", 0.0, 0, "TRAIN"]]}}
    r7 = mode_pop_assemble([fake])
    chk("WG7 الهويّةُ تسقط ⟵ لا قياس قبل أيّ حصّة", r7["verdict"] == "لا قياس" and r7["identity_ok"] is False and "rungs" not in r7)
    # WG9 الحصصُ والدرجاتُ والجرعة: «له ذيل» = الذيلُ عند الدرجة فأكثر (0.50 بالضبط داخلها) · وΔ = له ذيل − لا ذيل
    ents9 = []
    for k in range(240):
        w9 = (0.5, 0.65, 0.9, 0.1, 0.35, 0.2)[k % 6]
        ents9.append({"sym": f"S{k % 40}", "D": f"{2023 + k % 3}-03-01", "y": w9 >= 0.5, "wick": w9, "ret20": (k % 7) / 10.0,
                      "p3": 0})
    cuts9 = _sg().mom_cuts([e["ret20"] for e in ents9])
    r50, r80 = rung_stats(ents9, 0.50, cuts9, True), rung_stats(ents9, 0.80, cuts9, True)
    d9 = dose(ents9)
    chk("WG9 rung_stats/dose: 0.50 داخل «له ذيل» · Δ الخام 1 والحكمُ «الذيلُ يرفع» · والخاناتُ الأربع 80/40/80/40",
        r50["wick"]["n"] == 120 and r50["none"]["n"] == 120 and r50["delta_raw"] == 1.0 and r50["verdict"] == "الذيلُ يرفع"
        and r80["wick"]["n"] == 40 and [d9[x]["n"] for x in d9] == [80, 40, 80, 40] and d9["50-80%"]["exp"] == 80)
    bad = [n for n, cnd in ok if not cnd]
    log(f"guards: {len(ok) - len(bad)}/{len(ok)}")
    return 0 if not bad else 1


def _contract_ok():
    try:
        blob = json.load(open(UNITS, encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return _sha(CONTRACT) == CONTRACT_SHA and units_sha(blob) == UNITS_SHA


def main():
    mode = os.environ.get("WK_MODE", "guards")
    key = os.environ.get("POLYGON_API_KEY", "")
    if mode == "guards":
        return guards()
    if mode == "units":
        blob = build_units()
        os.makedirs(os.path.dirname(UNITS), exist_ok=True)
        with open(UNITS, "w", encoding="utf-8") as fh:
            json.dump(blob, fh, ensure_ascii=False, indent=1, sort_keys=True)
        log(f"units: ready {blob['n_ready']} · adds {blob['n_adds']} · {blob['identity_vs_part_a']} · sha {units_sha(blob)}")
        return 0
    if not _contract_ok():
        log("⛔ العقدُ أو قائمةُ الوحدات لا يطابقان بصمتَيهما — لا رقمَ قبل العقد")
        return 9
    if mode == "pop_assemble":
        log("RESULT_JSON " + json.dumps(mode_pop_assemble(), ensure_ascii=False, separators=(",", ":")))
        return 0
    if not key:
        log("⛔ لا مفتاح Polygon")
        return 2
    if mode == "units_eval":
        res = mode_units_eval(key)
        for r in res["units"]:
            if not r.get("nodata") and r["wick"] >= 0.30:
                log(f"WICK {r['kind']} {r['sym']} D {r['D']} · {round(r['wick'] * 100, 1)}% يومَ {r['wick_date']} "
                    f"(High {r['high']} · Close {r['close']}) · انفجر {r.get('exploded')}")
        log("RESULT_JSON " + json.dumps(res, ensure_ascii=False, separators=(",", ":")))
        return 0
    if mode == "pop_prep":
        log("PREP_JSON " + json.dumps(mode_pop_prep(key), ensure_ascii=False))
        return 0
    if mode == "pop_shard":
        r = mode_pop_shard(key, int(os.environ["SHARD"]), int(os.environ["NSHARDS"]))
        log(f"shard done: {r['symbols']} · {r['bars_diag']}")
        return 0
    log(f"⛔ وضعٌ مجهول: {mode}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
