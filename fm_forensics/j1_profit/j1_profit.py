#!/usr/bin/env python3
"""💵🥇 `T-J1-PROFIT` — «عقد ربح J1» (العقد `fm_forensics/j1_profit/J1P_prereg.md` · مدموجٌ قبل أيّ رقم) — قراءةٌ فقط.

`--mode year` يقرأ صفوفَ `target10_arms.py` (بلا تعديل) لسنةٍ وسجلَّها ⟵ بوّابةُ التكامل ⟵ جدولُ J1 · ¬J1 · M (ضبطُ الزخم) ⟵ `j1p_<سنة>.json` ·
`--mode pool` يجمع السنوات الثلاث ⟵ `D1`/`D2` بفاصل bootstrap على عناقيد الأيّام ⟵ الحكم ⟵ markdown و`J1P_JSON` ·
`--mode live` القراءةُ الوصفيّة على إطلاقات كون البوت (§④) · `--mode check` البصمة.
🔒 لا تلغرام · لا كتابة في المستودع · لا تغيير في أيّ أداة · وتخرج 9 إن تغيّرت بصمةُ العقد.
"""
import argparse
import json
import os
import random
import re
import subprocess
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

CONTRACT = os.path.join(HERE, "J1P_prereg.md")
CONTRACT_SHA = "620d1e9f86af441f46f9cdac5e51725dea6fd89459e6126209ea1c19a92fe601"
CONTRACT_RC = 9
YEARS = ("2023", "2024", "2025")
ANCHORS = {"2023": 10851, "2024": 14312, "2025": 19037}       # §① المنشور في target10_result.md
QUALIFIED = {"2023": 8834, "2024": 11367, "2025": 15150}
WINSOR = 10.0
FLOOR, FLOOR_M, D1_MIN = 150, 100, 0.10
BOOT_N, BOOT_SEED = 2000, 20261107
GAP_MIN = 30.0
STRONG = ("strong", "operator")
UNIVERSE = os.path.join(ROOT, "fm_forensics", "ema_cross", "data", "gcross_runner_universe.json")
LEDGER_REF = "86bc3838b5c0ee692a919ca346e667fdce475d92"
GAP = ("2026-09-29", "2026-10-12")


def log(m=""):
    print(m, flush=True)


def contract_ok(path=CONTRACT):
    import hashlib
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest() == CONTRACT_SHA
    except OSError:
        return False


# ── دوالُّ نقيّة (مقفولةٌ في السويّة) ─────────────────────────────────────────────────────────────────────
def wins(x, w=WINSOR):
    return max(-w, min(w, x))


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def median(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def group_of(r):
    """§② ⟵ «J1» · «M» (فجوة 30%+ بلا صنف قويّ/مضارب) · «R» (الباقي من ¬J1)."""
    if r.get("j1"):
        return "J1"
    g = r.get("gap_pct")
    if g is not None and g >= GAP_MIN and r.get("f2") not in STRONG:
        return "M"
    return "R"


def slim(r):
    """صفُّ التحليل من صفّ `target10_arms` ⟵ {day · g · top · r10 · r0 · p10}."""
    return {"day": r["day"], "g": group_of(r), "top": bool(r.get("j1_top")),
            "r10": (r.get("t10") or {}).get("r"), "r0": (r.get("t0") or {}).get("r"),
            "p10": (r.get("t10") or {}).get("pct")}


def stats(rows, arm="r10"):
    """{n · nR · raw · w · med · pos%} على R الذراع (الموجبُ من نسبة الخروج %)."""
    rs = [r[arm] for r in rows if r.get(arm) is not None]
    pk = "p10" if arm == "r10" else None
    pos = (100.0 * sum(1 for r in rows if (r.get(pk) or 0) > 0) / len(rows)) if (rows and pk) else None
    return {"n": len(rows), "nR": len(rs), "raw": mean(rs), "w": mean([wins(x) for x in rs]),
            "med": median(rs), "pos": pos}


def groups(rows):
    J = [r for r in rows if r["g"] == "J1"]
    N = [r for r in rows if r["g"] != "J1"]
    M = [r for r in rows if r["g"] == "M"]
    return J, N, M


def year_block(rows, arm="r10"):
    """جدولُ سنة: إحصاءاتُ J1 · ¬J1 · M · والفرقان مشذَّبًا وخامًّا."""
    J, N, M = groups(rows)
    sJ, sN, sM = stats(J, arm), stats(N, arm), stats(M, arm)

    def _d(a, b, k):
        return (a[k] - b[k]) if (a[k] is not None and b[k] is not None) else None
    return {"J1": sJ, "notJ1": sN, "M": sM, "top": stats([r for r in rows if r["top"]], arm),
            "D1w": _d(sJ, sN, "w"), "D1raw": _d(sJ, sN, "raw"), "D2w": _d(sJ, sM, "w"), "D2raw": _d(sJ, sM, "raw")}


def boot_ci(rows, a="J1", b="notJ1", arm="r10", n=BOOT_N, seed=BOOT_SEED):
    """§② فاصلُ 95% لفرق المتوسّط المشذَّب (a − b) بإعادة عناقيد الأيّام (مفتاحُها (سنة، يوم))."""
    per = {}
    for r in rows:
        x = r.get(arm)
        if x is None:
            continue
        x = wins(x)
        g = r["g"]
        side = "J1" if g == "J1" else None
        k = (r.get("year", ""), r["day"])
        cell = per.setdefault(k, {"J1": [0.0, 0], "notJ1": [0.0, 0], "M": [0.0, 0]})
        if side == "J1":
            cell["J1"][0] += x
            cell["J1"][1] += 1
        else:
            cell["notJ1"][0] += x
            cell["notJ1"][1] += 1
            if g == "M":
                cell["M"][0] += x
                cell["M"][1] += 1
    keys = sorted(per)
    if not keys:
        return None
    rng = random.Random(seed)
    ds = []
    for _ in range(n):
        sa = na = sb = nb = 0
        for _k in range(len(keys)):
            c = per[keys[rng.randrange(len(keys))]]
            sa += c[a][0]
            na += c[a][1]
            sb += c[b][0]
            nb += c[b][1]
        if na and nb:
            ds.append(sa / na - sb / nb)
    if not ds:
        return None
    ds.sort()
    return (ds[int(0.025 * len(ds))], ds[int(0.975 * len(ds)) - 1])


def integrity(year, anchors, qualified, v0, rc):
    """§① بوّابةُ التكامل بت-بت."""
    return (anchors == ANCHORS.get(year) and qualified == QUALIFIED.get(year) and v0 == 0 and rc == 0)


def parse_t10_log(text):
    """من سجلّ `target10_arms.py` ⟵ (المراسي، تفرّقاتُ V0) أو (None، None)."""
    m = re.search(r"مراسٍ ([\d,]+)\*\*", text or "")
    v = re.search(r"تفرّقات (\d+)", text or "")
    return (int(m.group(1).replace(",", "")) if m else None, int(v.group(1)) if v else None)


def verdict(years, pool):
    """§③ الحكمُ بالأضعف ⟵ (الفرع، نصّ)."""
    if not all(y.get("integrity") for y in years.values()):
        return 4, "④ «لا قياس» — بوّابةُ التكامل سقطت"
    if any(y["arm"]["J1"]["nR"] < FLOOR or y["arm"]["notJ1"]["nR"] < FLOOR for y in years.values()):
        return 4, "④ «لا قياس» — J1 أو ¬J1 دون 150 صفًّا بـR في سنة"

    def _pos(d, r):
        return d is not None and r is not None and d > 0 and r > 0
    d1_years = all(_pos(y["arm"]["D1w"], y["arm"]["D1raw"]) for y in years.values())
    ci1 = pool.get("D1ci")
    d1_ok = d1_years and (pool.get("D1w") or 0) >= D1_MIN and ci1 is not None and ci1[0] > 0
    if not d1_ok:
        return 3, "③ «لا ميزةَ ربحٍ لـJ1»"
    if any(y["arm"]["M"]["nR"] < FLOOR_M for y in years.values()):
        return 0, "J1 أربح (`D1` عبر) · **الزخم: لا قياس** (M دون 100 في سنة) ⟵ لا يُحكم بالفرع ①"
    d2_years = all((y["arm"]["D2w"] or 0) > 0 for y in years.values())
    ci2 = pool.get("D2ci")
    if d2_years and ci2 is not None and ci2[0] > 0:
        return 1, "① «J1 أربح ويضيف على الزخم»"
    return 2, "② «J1 أربح والزخمُ يفسّره»"


def predictions(years, pool, branch, live=None):
    yv = list(years.values())
    return {
        "J1P1": all(y.get("integrity") for y in yv),
        "J1P2": all(600 <= y["arm"]["J1"]["nR"] <= 2500 for y in yv),
        "J1P3": all((y["arm"]["D1w"] or 0) > 0 for y in yv) and 0.05 <= (pool.get("D1w") or 0) <= 0.40,
        "J1P4": branch == 2,
        "J1P5": pool.get("J1w") is not None and -0.25 <= pool["J1w"] <= 0.15,
        "J1P6": all((y["arm"]["J1"]["pos"] or 0) - (y["arm"]["notJ1"]["pos"] or 0) >= 5.0 for y in yv),
        "J1P7": (None if not live else bool(live.get("J1w") is not None and live.get("notJ1w") is not None
                                            and live["J1w"] > live["notJ1w"])),
    }


def _f(v, s="+.3f"):
    return format(v, s) if v is not None else "—"


def report_lines(years, pool, branch_txt, preds, live, meta):
    L = ["# 💵🥇 `T-J1-PROFIT` — النتيجة (مولَّدةٌ بـ`j1_profit.py --mode pool` · لا رقمَ باليد)", "",
         f"**التشغيلة:** {meta.get('run')} · main `{(meta.get('sha') or '')[:9]}` · `target10_arms.py` بلا تعديل", "",
         "## ① بوّابةُ التكامل (§①)", "", "| السنة | المراسي | المؤهَّلون | V0 | خروج | |", "|---|---|---|---|---|---|"]
    for yr, y in years.items():
        L.append(f"| {yr} | {y.get('anchors')} (المنشور {ANCHORS[yr]}) | {y.get('qualified')} (المنشور {QUALIFIED[yr]}) | {y.get('v0')} | "
                 f"{y.get('rc')} | {'✅' if y.get('integrity') else '⛔'} |")
    L += ["", "## ② الحاكم — `T10` · متوسّطُ R المشذَّب ±10R (الخامّ بين قوسين)", "",
          "| السنة | J1 (n) | ¬J1 (n) | M ضبطُ الزخم (n) | `D1` J1−¬J1 | `D2` J1−M |", "|---|---|---|---|---|---|"]
    for yr, y in years.items():
        a = y["arm"]
        L.append(f"| {yr} | {_f(a['J1']['w'])} ({_f(a['J1']['raw'])}) · {a['J1']['nR']} | {_f(a['notJ1']['w'])} ({_f(a['notJ1']['raw'])}) · "
                 f"{a['notJ1']['nR']} | {_f(a['M']['w'])} ({_f(a['M']['raw'])}) · {a['M']['nR']} | {_f(a['D1w'])} ({_f(a['D1raw'])}) | "
                 f"{_f(a['D2w'])} ({_f(a['D2raw'])}) |")
    c1, c2 = pool.get("D1ci"), pool.get("D2ci")
    L += [f"| **مجمَّعًا** | {_f(pool.get('J1w'))} · {pool.get('J1n')} | {_f(pool.get('notJ1w'))} · {pool.get('notJ1n')} | "
          f"{_f(pool.get('Mw'))} · {pool.get('Mn')} | **{_f(pool.get('D1w'))}** [{_f(c1[0] if c1 else None)}، {_f(c1[1] if c1 else None)}] | "
          f"**{_f(pool.get('D2w'))}** [{_f(c2[0] if c2 else None)}، {_f(c2[1] if c2 else None)}] |", "",
          f"## ③ الحكم: **{branch_txt}**", "",
          "## ④ وصفًا بلا حكم", ""]
    for yr, y in years.items():
        a, b = y["arm"], y["t0"]
        L.append(f"- {yr} · نسبةُ الموجب تحت `T10`: J1 {_f(a['J1']['pos'], '.1f')}% · ¬J1 {_f(a['notJ1']['pos'], '.1f')}% · M {_f(a['M']['pos'], '.1f')}%"
                 f" · الوسيط J1 {_f(a['J1']['med'])} · ¬J1 {_f(a['notJ1']['med'])} · «أقوى خليّة» {_f(a['top']['w'])} ({a['top']['nR']})"
                 f" · `T0` مشذَّبًا: J1 {_f(b['J1']['w'])} · ¬J1 {_f(b['notJ1']['w'])} · M {_f(b['M']['w'])}")
        L.append(f"  الكتم: مجموعُ R المشذَّب للكلّ {_f(y['mute']['all'], '+.1f')} مقابل J1 وحدَه {_f(y['mute']['j1'], '+.1f')} · "
                 f"صفوفٌ موجبةٌ تضيع بكتم ¬J1 {y['mute']['lost_pos']} من {y['mute']['pos_all']}")
    L += ["", "## ⑤ قراءةٌ وصفيّة على كون البوت (§④ · بلا حكم)", ""]
    if live:
        L.append(f"- الإطلاقاتُ المقيسة {live.get('n')} (J1 {live.get('nJ1')} · ¬J1 {live.get('nNot')}) · يومُ تقسيمٍ مستبعَد {live.get('split')} · "
                 f"بلا شموع {live.get('nobars')} · كُسر قبل الخمس {live.get('broke5')}")
        L.append(f"- `T10` مشذَّبًا: J1 {_f(live.get('J1w'))} · ¬J1 {_f(live.get('notJ1w'))} · نسبةُ الموجب J1 {_f(live.get('J1pos'), '.1f')}% · "
                 f"¬J1 {_f(live.get('notJ1pos'), '.1f')}%")
    else:
        L.append("- لم تُقرأ (القراءةُ الحيّة لم تُشغَّل أو تعذّرت)")
    L += ["", "## ⑥ التنبّؤات (منشورةٌ قبل الرقم)", ""]
    for k, v in preds.items():
        L.append(f"- `{k}` {'✅' if v else ('—' if v is None else '❌')}")
    L += ["", "🔒 لا شيء يُشحَن · الكونُ التاريخيّ كلُّ السوق في نطاق السعر لا قوائمُ البوت · والهدفُ بلا انزلاقٍ ولا تكلفة ⟵ الرقمُ سقفٌ والفرقُ هو الحكم."]
    return L


# ── الأوضاع ─────────────────────────────────────────────────────────────────────────────────────────────
def mode_year(year, rows_path, log_path, rc, out=None):
    rows = []
    with open(rows_path, encoding="utf-8") as f:
        for ln in f:
            if ln.strip():
                rows.append(json.loads(ln))
    anchors, v0 = parse_t10_log(open(log_path, encoding="utf-8").read() if os.path.exists(log_path) else "")
    sl = [dict(slim(r), year=year) for r in rows]
    y = {"year": year, "anchors": anchors, "qualified": len(rows), "v0": v0, "rc": int(rc),
         "integrity": integrity(year, anchors, len(rows), v0, int(rc)),
         "arm": year_block(sl, "r10"), "t0": year_block(sl, "r0")}
    allw = [wins(r["r10"]) for r in sl if r["r10"] is not None]
    j1w = [wins(r["r10"]) for r in sl if r["r10"] is not None and r["g"] == "J1"]
    y["mute"] = {"all": sum(allw), "j1": sum(j1w), "pos_all": sum(1 for r in sl if (r["p10"] or 0) > 0),
                 "lost_pos": sum(1 for r in sl if (r["p10"] or 0) > 0 and r["g"] != "J1")}
    out = out or f"j1p_{year}.json"
    json.dump({"y": y, "rows": sl}, open(out, "w", encoding="utf-8"), ensure_ascii=False)
    a = y["arm"]
    log(f"📅 {year}: تكامل {'✅' if y['integrity'] else '⛔'} (مراسٍ {anchors} · مؤهَّل {len(rows)} · V0 {v0} · خروج {rc}) · "
        f"J1 {a['J1']['nR']} مشذَّبًا {_f(a['J1']['w'])} · ¬J1 {a['notJ1']['nR']} {_f(a['notJ1']['w'])} · M {a['M']['nR']} {_f(a['M']['w'])}")
    return 0


def pool_stats(allrows):
    J, N, M = groups(allrows)

    def _w(rs):
        return mean([wins(r["r10"]) for r in rs if r["r10"] is not None])
    p = {"J1w": _w(J), "notJ1w": _w(N), "Mw": _w(M),
         "J1n": sum(1 for r in J if r["r10"] is not None), "notJ1n": sum(1 for r in N if r["r10"] is not None),
         "Mn": sum(1 for r in M if r["r10"] is not None)}
    p["D1w"] = (p["J1w"] - p["notJ1w"]) if (p["J1w"] is not None and p["notJ1w"] is not None) else None
    p["D2w"] = (p["J1w"] - p["Mw"]) if (p["J1w"] is not None and p["Mw"] is not None) else None
    p["D1ci"] = boot_ci(allrows, "J1", "notJ1")
    p["D2ci"] = boot_ci(allrows, "J1", "M")
    return p


def mode_pool(paths, live_path=None):
    years, allrows = {}, []
    for p in paths:
        d = json.load(open(p, encoding="utf-8"))
        years[d["y"]["year"]] = d["y"]
        allrows += d["rows"]
    years = {k: years[k] for k in sorted(years)}
    if sorted(years) != list(YEARS):
        log(f"⛔ سنواتٌ ناقصة: {sorted(years)} ⟵ لا قياس")
    pool = pool_stats(allrows)
    br, txt = verdict(years, pool) if sorted(years) == list(YEARS) else (4, "④ «لا قياس» — سنةٌ ناقصة")
    live = json.load(open(live_path, encoding="utf-8")) if (live_path and os.path.exists(live_path)) else None
    preds = predictions(years, pool, br, live)
    meta = {"run": os.environ.get("GITHUB_RUN_ID"),
            "sha": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()}
    for ln in report_lines(years, pool, txt, preds, live, meta):
        print(ln)
    print("J1P_JSON " + json.dumps({"years": years, "pool": pool, "branch": br, "preds": preds, "live": live, "meta": meta},
                                   ensure_ascii=False, default=str))
    return 0


def mode_live(out=None):
    """§④ القراءةُ الوصفيّة على إطلاقات كون البوت."""
    from concurrent.futures import ThreadPoolExecutor
    import target10_arms as T10
    import tier_days_report as TD
    from tier_fwd_report import fetch_day
    from tierlink_probe import daily_range
    from shadow_ready import split_ratio
    sys.path.insert(0, os.path.join(ROOT, "fm_forensics", "live_vs_shadow"))
    import live_vs_shadow as LVS
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key:
        log("⛔ بلا مفتاح Polygon — لا قراءة حيّة")
        return 3
    U = json.load(open(UNIVERSE, encoding="utf-8"))
    src = LVS.source_days(U, GAP)
    led = subprocess.run(["git", "show", f"{LEDGER_REF}:tier_fwd_ledger.jsonl"], capture_output=True, text=True).stdout
    j1m, _has = LVS.j1_map(led.splitlines())
    fires = [(d, sym, v) for d in src for sym, v in sorted((U["alerts"].get(d) or {}).items()) if sym in LVS.universe_of(U, d)]

    def _one(f):
        d, sym, v = f
        bars = fetch_day(sym, d, key)
        if not bars:
            return {"why": "nobars"}
        pd_, _p0 = LVS.prev_close(daily_range(sym, d, key), d)
        sr = split_ratio(sym, pd_, d, key) if pd_ else None
        if sr is not None and sr != 1.0:
            return {"why": "split"}
        a_ms, px = int(v["ms"]), float(v["px"])
        ab = next((b for b in bars if b[0] == a_ms), None)
        if ab is None:
            return {"why": "nobars"}
        e5, broke5 = TD.true_e5(bars, a_ms, px)
        if broke5 or not e5:
            return {"why": "broke5"}
        alow = float(ab[3])
        risk = e5 - alow
        if risk <= 0:
            return {"why": "rundef"}
        px10, _k = T10.arm_exit(bars, a_ms, alow, e5, 10.0)
        if px10 is None:
            return {"why": "nobars"}
        return {"g": "J1" if (d, sym) in j1m else "R", "r10": (px10 - e5) / risk, "p10": (px10 / e5 - 1) * 100}
    with ThreadPoolExecutor(8) as pool:
        got = list(pool.map(_one, fires))
    ok = [g for g in got if "g" in g]
    J = [g for g in ok if g["g"] == "J1"]
    N = [g for g in ok if g["g"] != "J1"]
    live = {"n": len(ok), "nJ1": len(J), "nNot": len(N),
            "split": sum(1 for g in got if g.get("why") == "split"), "nobars": sum(1 for g in got if g.get("why") == "nobars"),
            "broke5": sum(1 for g in got if g.get("why") in ("broke5", "rundef")),
            "J1w": mean([wins(g["r10"]) for g in J]), "notJ1w": mean([wins(g["r10"]) for g in N]),
            "J1pos": (100.0 * sum(1 for g in J if g["p10"] > 0) / len(J)) if J else None,
            "notJ1pos": (100.0 * sum(1 for g in N if g["p10"] > 0) / len(N)) if N else None}
    json.dump(live, open(out or "j1p_live.json", "w", encoding="utf-8"), ensure_ascii=False)
    log(f"📡 الحيّ: {json.dumps(live, ensure_ascii=False)}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("check", "year", "pool", "live"), default="check")
    ap.add_argument("--year")
    ap.add_argument("--rows")
    ap.add_argument("--log")
    ap.add_argument("--rc", default="0")
    ap.add_argument("--live")
    ap.add_argument("--out")
    ap.add_argument("paths", nargs="*")
    a = ap.parse_args(argv)
    if not contract_ok():
        log("⛔ بصمةُ العقد تغيّرت — خروج 9 (لا قياس).")
        return CONTRACT_RC
    if a.mode == "check":
        log("🔒 بصمةُ العقد ✅")
        return 0
    if a.mode == "year":
        return mode_year(a.year, a.rows, a.log, a.rc, a.out)
    if a.mode == "pool":
        return mode_pool(a.paths, a.live)
    return mode_live(a.out)


if __name__ == "__main__":
    sys.exit(main())
