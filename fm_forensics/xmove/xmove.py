#!/usr/bin/env python3
"""📣 `T-XMOVE` «تحرّك X% — إشعارٌ واحدٌ يوميًّا» (العقد `fm_forensics/xmove/XMOVE_prereg.md` · مدموجٌ قبل أيّ رقم) — قراءةٌ فقط.

`--mode chunk --part p --parts P --out f` (الرنر · Polygon · تاريخُ git كامل): جلساتٌ متناوبة من الستّين ⟵ لكلّ (سهم، يوم) في الكون `L ∪ N`:
دقائقُ اليوم وإغلاقُ الأمس ⟵ إطلاقُ كلّ عتبة X (`x_fire`) ⟵ «الحاليّ» (المِرساةُ المصحَّحة) ⟵ 🥇 بقاعدة اليوم (`gold_map`) ⟵ JSON.
`--mode pool f1 f2 …`: النطاقاتُ الثلاثة ⟵ البوّابتان G1/G2 ⟵ الجدولُ الواحد ⟵ التنبّؤات ⟵ markdown و`XMOVE_JSON`.
🔒 لا تلغرام · لا كتابة في المستودع · لا تغيير في أيّ أداة · وتخرج 9 إن تغيّرت بصمةُ العقد و7 إن سقطت G1.
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

CONTRACT = os.path.join(HERE, "XMOVE_prereg.md")
CONTRACT_SHA = "cb878a348254cbceacb2ed0afab271b18f4e7fa10bbb2d930eaa4dc0885e8d5e"
CONTRACT_RC, G1_RC = 9, 7
UNIVERSE = os.path.join(ROOT, "fm_forensics", "ema_cross", "data", "gcross_runner_universe.json")
RUNNERS = os.path.join(ROOT, "fm_forensics", "rrgate", "data", "runners_60.json")
LEDGER_REF, TIER_FILE = "b7d812971", "tier_fwd_ledger.jsonl"     # K2 (main وقتَ العقد)
NY = ZoneInfo("America/New_York")
XS = (0.10, 0.15, 0.20, 0.30)                                   # الأمر
USD_MIN = 50_000                                                # الأمر: حجمٌ دولاريٌّ تراكميّ لحظتَها
X_FROM, X_END = 4 * 60, 16 * 60                                 # §② بري ‏+ نظامي [04:00، 16:00)
GOLD_MIN = 3                                                    # K2 = `LIQ_TIER_STRONG_MIN` (مقفولٌ بالهُويّة في السويّة)
GOLD_FROM = "2026-08-24"                                        # K2 أوّلُ صفوف السجلّ
RUN50, RUN100 = 0.5, 1.0
G1_N, G1_K, G1_FIRES, G1_TOL = 209, 155, 1561, 0.01             # §③ = LVS_RESULT.md §⑨ المصحَّح
R_TOL, AGREE_MIN, FAIL_MAX, FLOOR_RUN = 0.02, 0.90, 0.10, 30    # §③
WORKERS = 16
ROWS = ("X10", "X15", "X20", "X30", "cur", "gold")
ROW_AR = {"X10": "تحرّك 10%", "X15": "تحرّك 15%", "X20": "تحرّك 20%", "X30": "تحرّك 30%", "cur": "الحاليّ («هنا الدخول»)", "gold": "🥇 وحدَه"}


def log(m=""):
    print(m, flush=True)


def _load(name, rel):
    sp = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    mod = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(mod)
    return mod


def contract_ok(path=None, sha=None):
    try:
        return hashlib.sha256(open(path or CONTRACT, "rb").read()).hexdigest() == (sha or CONTRACT_SHA)
    except OSError:
        return False


def ny_parts(t_ms):
    t = dt.datetime.fromtimestamp(int(t_ms) / 1000, dt.timezone.utc).astimezone(NY)
    return t.date().isoformat(), t.hour * 60 + t.minute


def median(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def wilson(k, n, z=1.96):
    if not n:
        return (None, None)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / den
    return (max(0.0, c - h), min(1.0, c + h))


# ── دوالُّ نقيّة (مقفولةٌ في السويّة) ──────────────────────────────────────────────────────────
def x_fire(bars, day, p0, x, usd_min=USD_MIN, start=X_FROM, end=X_END):
    """§② أوّلُ دقيقةٍ في [start، end) نيويورك يومَ `day` فيها `high ≥ p0·(1+x)` **و**مجموعُ `v·c` من `start` حتى الدقيقة **شاملةً** ‏≥ usd_min
    ⟵ (الدقيقة، ms، السعر = `c` تلك الدقيقة) أو None · `bars` = [(t، o، h، l، c، v)] كما يُرجعها `fetch_day`."""
    if not bars or not p0:
        return None
    lvl, cum = float(p0) * (1.0 + x), 0.0
    for b in sorted(bars, key=lambda r: int(r[0])):
        d, m = ny_parts(b[0])
        if d != day or m < start or m >= end:
            continue
        cum += float(b[5] or 0.0) * float(b[4])
        if float(b[2]) >= lvl and cum >= usd_min:
            return (m, int(b[0]), float(b[4]))
    return None


def gold_map(lines, gmin=GOLD_MIN):
    """K2 ⟵ {(يوم، رمز): (ms، السعر)} = أبكرُ صفٍّ قويٍّ بقاعدة اليوم (`green ≥ gmin` أو `j1` = true) بـ`price_ms` و`e5`."""
    out = {}
    for ln in lines:
        try:
            r = json.loads(ln)
        except (ValueError, TypeError):
            continue
        if not isinstance(r, dict) or not r.get("price_ms") or r.get("e5") is None:
            continue
        g = r.get("green")
        if not ((isinstance(g, (int, float)) and g >= gmin) or r.get("j1") is True):
            continue
        k = (str(r.get("date") or ""), str(r.get("symbol") or "").upper())
        if k not in out or int(r["price_ms"]) < out[k][0]:
            out[k] = (int(r["price_ms"]), float(r["e5"]))
    return out


def day_stats(counts):
    """① ⟵ (الوسيط، الأقصى، المجموع) من عددٍ لكلّ يوم (الأيّامُ بصفرٍ تُعَدّ)."""
    vals = list(counts)
    return (median(vals), max(vals) if vals else None, sum(vals))


def g1_ok(n, k, fires, n0=G1_N, k0=G1_K, f0=G1_FIRES, tol=G1_TOL):
    """§③ G1: المقيسون والمُطلَق لهم بالضبط · والإطلاقاتُ بفارقٍ لا يتجاوز `tol`."""
    return n == n0 and k == k0 and abs(fires - f0) <= tol * f0


# ── الرنر ─────────────────────────────────────────────────────────────────────────────────────
def _git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout


def _dailies(sym, d0, d1, key):
    import requests
    try:
        r = requests.get(f"https://api.polygon.io/v2/aggs/ticker/{sym}/range/1/day/{d0}/{d1}",
                         params={"adjusted": "false", "sort": "asc", "limit": 400}, headers={"Authorization": f"Bearer {key}"}, timeout=30)
        if r.status_code != 200:
            return None
        return [(dt.datetime.fromtimestamp(b["t"] / 1000, tz=NY).date().isoformat(), float(b["h"]), float(b["c"]))
                for b in (r.json() or {}).get("results") or []]
    except Exception:                                                # noqa: BLE001
        return None


def mode_chunk(part, parts, out_path):
    from concurrent.futures import ThreadPoolExecutor
    from tier_fwd_report import fetch_day
    from shadow_ready import split_ratio
    LVS = _load("lvs_xm", "fm_forensics/live_vs_shadow/live_vs_shadow.py")
    key = (os.environ.get("POLYGON_API_KEY") or "").strip()
    if not key:
        log("⛔ بلا مفتاح Polygon — لا قياس")
        return 3
    U0 = json.load(open(UNIVERSE, encoding="utf-8"))
    RN = json.load(open(RUNNERS, encoding="utf-8"))
    sessions = sorted(U0["sessions"])
    assert len(sessions) == RN["sessions"][2] and sessions[0] == RN["sessions"][0] and sessions[-1] == RN["sessions"][1]
    days = sessions[part::parts]
    alerts = LVS.rebuild_alerts(U0, True)                        # K1 (المصحَّحة)
    src = set(LVS.source_days(dict(U0, alerts=alerts)))
    _led = _git("show", f"{LEDGER_REF}:{TIER_FILE}").splitlines()
    gold = gold_map(_led)
    m5_by = {}
    for _ln in _led:
        try:
            _d = str(json.loads(_ln).get("date") or "")
        except (ValueError, TypeError, AttributeError):
            continue
        m5_by[_d] = m5_by.get(_d, 0) + 1
    run_by = {(r["sym"], r["day"]): r["R"] for r in RN["rows"]}
    d_min = (dt.date.fromisoformat(sessions[0]) - dt.timedelta(days=12)).isoformat()
    d_max = (dt.date.fromisoformat(sessions[-1]) + dt.timedelta(days=2)).isoformat()
    log(f"📣 الجزء {part + 1}/{parts}: {len(days)} جلسة · أيّامُ مصدرٍ منه {sum(1 for d in days if d in src)} · صفوفُ 🥇 (الكلّ) {len(gold)}")
    dly_c = {}
    out = {"part": part, "parts": parts, "days": {}, "recs": []}
    for d in days:
        uni = LVS.universe_of(U0, d)
        syms = sorted(uni)
        with ThreadPoolExecutor(WORKERS) as pool:
            raw = dict(zip(syms, pool.map(lambda s: fetch_day(s, d, key), syms)))
        need = [s for s in syms if s not in dly_c]
        with ThreadPoolExecutor(WORKERS) as pool:
            for s, v in zip(need, pool.map(lambda s: _dailies(s, d_min, d_max, key), need)):
                dly_c[s] = v
        n_fail = 0
        cands = []
        for sym in syms:
            bars = raw.get(sym)
            pd_, p0 = LVS.prev_close(dly_c.get(sym), d)
            if not bars or not p0:
                n_fail += 1
            seq = LVS.day_seq(bars, d) if bars else []
            R = LVS.day_R(seq, p0)[0] if (seq and p0) else None
            fires = {}
            for x in XS:
                f = x_fire(bars, d, p0, x) if bars and p0 else None
                if f:
                    fires[f"X{int(round(x * 100))}"] = [f[0], f[2]]
            al = (alerts.get(d) or {}).get(sym)
            if al and d in src:
                px = al.get("px")
                if px is None and bars:
                    px = next((float(b[4]) for b in bars if int(b[0]) == int(al["ms"])), None)
                fires["cur"] = [ny_parts(al["ms"])[1], px]
            g = gold.get((d, sym))
            if g and d >= GOLD_FROM:
                fires["gold"] = [ny_parts(g[0])[1], g[1]]
            Rf = run_by.get((sym, d))
            if not fires and Rf is None:
                continue
            rec = {"sym": sym, "d": d, "R": R, "Rf": Rf, "ok": bool(seq and p0), "fires": fires, "split": False, "stats": {}}
            if Rf is not None and seq and p0:
                for k, (m, px) in fires.items():
                    st = LVS.after_stats(seq, m, px, p0) if px else None
                    rec["stats"][k] = st
            cands.append((rec, pd_))
        fired = [(rec, pd_) for rec, pd_ in cands if rec["fires"] and pd_]
        with ThreadPoolExecutor(WORKERS) as pool:
            srs = list(pool.map(lambda t: split_ratio(t[0]["sym"], t[1], d, key), fired))
        for (rec, _pd), sr in zip(fired, srs):
            rec["split"] = bool(sr is not None and sr != 1.0)
        out["recs"].extend(rec for rec, _pd in cands)
        out["days"][d] = {"src": d in src, "uni": len(syms), "fail": n_fail, "m5": m5_by.get(d, 0)}
        log(f"   {d}: كون {len(syms)} · بلا شموع/إغلاق {n_fail} · سجلّات {len(cands)} · مصدر {'نعم' if d in src else 'لا'}")
    json.dump(out, open(out_path, "w", encoding="utf-8"), ensure_ascii=False)
    log(f"✅ كُتب {out_path}")
    return 0


def scope_rows(recs, days, rows):
    """⟵ {صفّ: مقاييسُه} على أيّام `days` (نقيّ على السجلّات)."""
    days = set(days)
    rr = [r for r in recs if r["d"] in days]
    run100 = [r for r in rr if r.get("Rf") is not None and r["Rf"] >= RUN100 and r["ok"]]
    run50 = [r for r in rr if r.get("Rf") is not None and r["Rf"] >= RUN50 and r["ok"]]
    out = {"_run100": len(run100), "_run50": len(run50)}
    for k in rows:
        fires = [r for r in rr if k in r["fires"] and not r["split"] and r["R"] is not None]
        per = {d: 0 for d in days}
        for r in fires:
            per[r["d"]] += 1
        med, mx, tot = day_stats(per.values())
        p50 = sum(1 for r in fires if r["R"] >= RUN50)
        p100 = sum(1 for r in fires if r["R"] >= RUN100)
        nf = sum(1 for r in fires if r["R"] < RUN50)
        c100 = [r for r in run100 if k in r["fires"]]
        c50 = [r for r in run50 if k in r["fires"]]
        st = [r["stats"].get(k) or {} for r in c100]
        out[k] = {"day_med": med, "day_max": mx, "fires": tot, "split": sum(1 for r in rr if k in r["fires"] and r["split"]),
                  "prec50": [p50, len(fires)], "prec50_ci": wilson(p50, len(fires)), "prec100": [p100, len(fires)],
                  "cap100": [len(c100), len(run100)], "cap50": [len(c50), len(run50)],
                  "false_per_run": (nf / len(c100)) if c100 else None,
                  "min_med": median([r["fires"][k][0] for r in c100]), "pct_med": median([s.get("pct") for s in st]),
                  "left_med": median([s.get("left") for s in st]), "gain_med": median([s.get("gain") for s in st]),
                  "left50_med": median([(r["stats"].get(k) or {}).get("left") for r in c50])}
    return out


def _pc(x, sign=False):
    return "—" if x is None else (f"{x * 100:+.1f}%" if sign else f"{x * 100:.1f}%")


def _hm(m):
    return "—" if m is None else f"{int(m) // 60:02d}:{int(m) % 60:02d}"


def _num(x):
    return "—" if x is None else (f"{x:g}" if isinstance(x, int) or float(x).is_integer() else f"{x:.1f}")


def table_lines(res, rows, floor_ok=True):
    L = ["| الصفّ | إشعاراتٌ/يوم (الوسيط · الأقصى) | المجموع | التقاط ‏+100% | ما بقي من الحركة (+100%) | الدقيقة · من إغلاق الأمس (وسيط) | التقاط ‏+50% | "
         "الدقّة (صار ‏+50%) | ‏+100% منها | كاذبٌ لكلّ راكض ‏+100% |", "|---|---|---|---|---|---|---|---|---|---|"]
    for k in rows:
        v = res[k]
        c1, c5 = v["cap100"], v["cap50"]
        cap = f"{c1[0]} من {c1[1]} = {_pc(c1[0] / c1[1]) if c1[1] else '—'}" if floor_ok else f"{c1[0]} من {c1[1]} (لا قياس)"
        ci = v["prec50_ci"]
        L.append(f"| **{ROW_AR[k]}** | {_num(v['day_med'])} · {_num(v['day_max'])} | {v['fires']} | {cap} | {_pc(v['left_med'])} | "
                 f"{_hm(v['min_med'])} · {_pc(v['pct_med'], True)} | {c5[0]} من {c5[1]} = {_pc(c5[0] / c5[1]) if c5[1] else '—'} | "
                 f"{v['prec50'][0]} من {v['prec50'][1]} = {_pc(v['prec50'][0] / v['prec50'][1]) if v['prec50'][1] else '—'} "
                 f"[{_pc(ci[0])}، {_pc(ci[1])}] | {_pc(v['prec100'][0] / v['prec100'][1]) if v['prec100'][1] else '—'} | "
                 f"{'—' if v['false_per_run'] is None else format(v['false_per_run'], '.1f')} |")
    return L


def predictions(A):
    def _in(v, lo, hi):
        return v is not None and lo <= v <= hi

    def cap(k):
        c = A[k]["cap100"]
        return c[0] / c[1] if c[1] else None

    def prec(k):
        p = A[k]["prec50"]
        return p[0] / p[1] if p[1] else None
    return {
        "XP1": all(_in(A[k]["day_med"], lo, hi) for k, lo, hi in (("X10", 40, 90), ("X15", 25, 60), ("X20", 15, 45), ("X30", 8, 25))),
        "XP2": all((cap(k) or 0) >= 0.90 for k in ("X10", "X15", "X20", "X30")),
        "XP3": (A["X10"]["left_med"] or 0) >= 0.75 and _in(A["X30"]["left_med"], 0.55, 0.80),
        "XP4": _in(prec("X10"), 0.10, 0.25) and _in(prec("X30"), 0.35, 0.65)
               and all((prec(a) or 0) <= (prec(b) or 0) for a, b in (("X10", "X15"), ("X15", "X20"), ("X20", "X30")))
               and (prec("X10") or 0) < (prec("X30") or 0),
        "XP5": (A["X30"]["day_med"] or 0) < (A["cur"]["day_med"] or 0) and (prec("X30") or 0) > (prec("cur") or 0)
               and (cap("X30") or 0) > (cap("cur") or 0),
        "XP6": _in(A["gold"]["day_med"], 3, 12) and _in(cap("gold"), 0.35, 0.65),
    }


def mode_pool(paths):
    recs, days = [], {}
    for p in paths:
        o = json.load(open(p, encoding="utf-8"))
        recs.extend(o["recs"])
        days.update(o["days"])
    alld = sorted(days)
    src = [d for d in alld if days[d]["src"]]
    scA = [d for d in src if d >= GOLD_FROM]
    log("# 📣 `T-XMOVE` — النتيجة (مولَّدةٌ بـ`xmove.py --mode pool` · لا رقمَ باليد)")
    log("")
    log(f"**التشغيلة:** {os.environ.get('GITHUB_RUN_ID')} · main `{_git('rev-parse', 'HEAD').strip()[:9]}` · الجلسات {len(alld)} · أيّامُ مصدر «الحاليّ» {len(src)} · "
        f"النطاق أ {len(scA)} ({scA[0] if scA else '—'} ⟵ {scA[-1] if scA else '—'})")
    # G1
    B = scope_rows(recs, src, ("cur",))
    n100 = B["_run100"]
    g1 = g1_ok(n100, B["cur"]["cap100"][0], B["cur"]["fires"])
    log(f"**G1 (الحاليّ = المنشور §⑨):** راكضو ‏+100% المقيسون {n100} (المنشور {G1_N}) · المُطلَق لهم {B['cur']['cap100'][0]} ({G1_K}) · إطلاقاتُ الكون "
        f"{B['cur']['fires']} ({G1_FIRES} ±1%) ⟵ {'✅' if g1 else '⛔'}")
    if not g1:
        log(f"⛔ G1 ساقطة — لا تقرير (خروج {G1_RC})")
        return G1_RC
    meas = [r for r in recs if r.get("Rf") is not None and r["ok"] and r["R"] is not None]
    agree = sum(1 for r in meas if abs(r["R"] - r["Rf"]) <= R_TOL)
    g2 = bool(meas) and agree / len(meas) >= AGREE_MIN
    log(f"**G2 (صدقُ الشموع):** R المُعاد يطابق المجمَّد (±2 نقطة) في {agree} من {len(meas)} ⟵ {'✅' if g2 else '⛔ لا قياس'}")
    fail = {}
    for nm, sc in (("أ", scA), ("ب", src), ("ج", alld)):
        u = sum(days[d]["uni"] for d in sc)
        f = sum(days[d]["fail"] for d in sc)
        fail[nm] = (f / u) if u else 1.0
        log(f"- النطاق {nm}: سهم-أيّامُ الكون {u} · بلا شموع/إغلاق {f} ({_pc(fail[nm])})")
    if not g2:
        return 0
    log("")
    log(f"## ① الجدولُ الواحد — النطاق أ ({len(scA)} جلسة من {GOLD_FROM} · الكونُ `L ∪ N` · الصفوفُ الستّة على الأيّام نفسِها)")
    log("")
    A = scope_rows(recs, scA, ROWS)
    ok = fail["أ"] <= FAIL_MAX
    for ln in table_lines(A, ROWS, A["_run100"] >= FLOOR_RUN):
        log(ln if ok else ln + " (لا قياس: شموع)")
    log("")
    _m5 = [days[d].get("m5", 0) for d in scA]
    log(f"وصفًا (K1): كروتُ `M5` المُرسَلة يوميًّا من السجلّ — الوسيط {_num(median(_m5))} · الأقصى {_num(max(_m5) if _m5 else None)} (فوق إشعار «الحاليّ» الأوّل)")
    log(f"راكضو ‏+100% في النطاق {A['_run100']} · ‏+50% فأكثر {A['_run50']} · أيّامُ تقسيمٍ مستبعَدة (الإطلاقات): "
        + " · ".join(f"{ROW_AR[k]} {A[k]['split']}" for k in ROWS))
    log("")
    log(f"## ② النطاق ب — أيّامُ المصدر كلُّها ({len(src)} جلسة · بلا 🥇) — وصفًا")
    log("")
    Bf = scope_rows(recs, src, ROWS[:5])
    for ln in table_lines(Bf, ROWS[:5], Bf["_run100"] >= FLOOR_RUN):
        log(ln)
    log("")
    log(f"## ③ النطاق ج — الستّون كلُّها ({len(alld)} جلسة · صفوفُ X وحدَها) — وصفًا")
    log("")
    C = scope_rows(recs, alld, ROWS[:4])
    for ln in table_lines(C, ROWS[:4], C["_run100"] >= FLOOR_RUN):
        log(ln)
    log("")
    log(f"راكضو ‏+100% في الستّين المقيسون {C['_run100']} · ‏+50% فأكثر {C['_run50']}")
    preds = predictions(A)
    log("")
    log("## ④ التنبّؤات (النطاق أ · منشورةٌ قبل الرقم)")
    log("")
    for k, v in preds.items():
        log(f"- `{k}` {'✅' if v else '❌'}")
    log("")
    log("🔒 لا تغييرَ في أيّ أداة · والقرارُ للمالك (العقد §⑥).")
    log("XMOVE_JSON " + json.dumps({"A": A, "B": Bf, "C": C, "preds": preds, "g1": g1, "g2": [agree, len(meas)], "fail": fail,
                                     "days": {"A": scA, "B": src, "C": alld}}, ensure_ascii=False, default=str))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("chunk", "pool", "check"), default="check")
    ap.add_argument("--part", type=int, default=0)
    ap.add_argument("--parts", type=int, default=1)
    ap.add_argument("--out", default="xmove_part.json")
    ap.add_argument("files", nargs="*")
    a = ap.parse_args(argv)
    if not contract_ok():
        log(f"⛔ بصمةُ العقد `{CONTRACT}` تغيّرت أو غاب — المدموجُ لا يُعدَّل (خروج {CONTRACT_RC})")
        return CONTRACT_RC
    if a.mode == "check":
        log("✅ العقدُ مطابقٌ لبصمته")
        return 0
    if a.mode == "chunk":
        return mode_chunk(a.part, a.parts, a.out)
    return mode_pool(a.files)


if __name__ == "__main__":
    sys.exit(main())
