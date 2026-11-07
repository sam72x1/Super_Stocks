#!/usr/bin/env python3
"""🥇↩️ `T-J1-PULLBACK` — «الدخول على العودة لا على الإشعار» (العقد `fm_forensics/j1_pullback/J1PB_prereg.md` · مدموجٌ قبل أيّ رقم) — قراءةٌ فقط.

`--mode check` بصمةُ العقد بلا شبكة · `--mode run` (رنر بمفتاح Polygon): إشعاراتُ 🥇 J1 في الجلسات الستّين من `tier_fwd_ledger.jsonl` عند المرجع المجمَّد ⟵
شموعُ الدقيقة (`tier_fwd_report.fetch_day` بالاسم) ⟵ المستوى `L` PIT (`Super_stock.tested_level` بالاسم على يوميّةٍ مسوّاة مُعادةٍ لمقياس يوم الإشعار) ⟵
الذراعُ أ (لحظةُ الإشعار) · الذراعُ ب (العودةُ إلى ±5% من `L` ثمّ أوّلُ إغلاق 5د فوقه) · الضابطُ `C` (شمعةُ 5د عشوائيّة بوقفٍ مطابق) ⟵ R المشذَّب ±10R ·
`D_A` · `D_C` · التفكيك · الحكمُ بالأضعف ⟵ تقريرٌ و`J1PB_JSON` و`j1pb_rows.json`.
🔒 لا تلغرام · لا كتابة في المستودع · لا تغيير في أيّ أداة · وتخرج 9 إن تغيّرت بصمةُ العقد.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

CONTRACT = os.path.join(HERE, "J1PB_prereg.md")
CONTRACT_SHA = "4611a085a8005aebfa404df0814559f42632c3ea353aeb0424fe3303cdf9820c"
CONTRACT_RC = 9
LEDGER_REF = "2525be4b50d87dadfcffa2ca544c5b21f644725e"             # §① المرجعُ المجمَّد (main وقتَ العقد)
UNIVERSE = os.path.join(ROOT, "fm_forensics", "ema_cross", "data", "gcross_runner_universe.json")
GOLD = "قوي"                                                          # §① 🥇 منذ «اعتمد v1» 2026-08-26
BAND, T1, T2 = 0.05, 0.20, 0.50                                      # §③ ±5% · ‏+20% نصف · ‏+50% نصف (نصُّ المالك)
WINSOR = 10.0
K_DRAWS = 20
BOOT_N, BOOT_SEED = 2000, 20261107
MISS_MAX, A_MIN, B_MIN = 0.10, 100, 20                               # §⑥ بوّاباتُ «لا قياس»
MIN_MS = 60_000
B5 = 5 * MIN_MS                                                      # إزاحةُ نيويورك عن UTC مضاعفُ ساعة ⟵ محاذاةُ 5د واحدةٌ في الساعتين
OUT_ROWS = "j1pb_rows.json"
ADD_D = os.path.join(HERE, "J1PB_ADDENDUM_D.md")                     # الملحق D (أمرُ المالك 2026-11-07 · قبل أيّ رقم)
ADD_D_SHA = "c1d5691f4f2349327c0b8124a924a3fac3a3ff1262e628c309062ac07ec8e59c"
D_DELAY = 2 * MIN_MS                                                 # «الدخول بعد دقيقتين من الإشعار»
D_T1, D_T2, D_CAT = 0.20, 0.50, 0.30                                 # نصفٌ ‏+20% · نصفٌ ‏+50% · كارثيٌّ −30%
OUT_ROWS_D = "j1pd_rows.json"
D_BUCKETS = ((-1e9, -30.0), (-30.0, -20.0), (-20.0, -10.0), (-10.0, 0.0), (0.0, 10.0), (10.0, 20.0), (20.0, 1e9))


def log(m=""):
    print(m, flush=True)


def contract_ok(path=CONTRACT):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest() == CONTRACT_SHA
    except OSError:
        return False


def addendum_ok(path=ADD_D):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest() == ADD_D_SHA
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


def population(lines, sessions, gold=GOLD):
    """§① ⟵ (إشعاراتُ 🥇 J1: أوّلُ صفٍّ لكلّ (تاريخ، رمز) بترتيب السجلّ · وعددُ صفوف J1 بلا 🥇 في الإطار)."""
    first, not_gold = {}, 0
    for ln in lines:
        try:
            r = json.loads(ln)
        except (ValueError, TypeError):
            continue
        if r.get("j1") is not True or r.get("date") not in sessions:
            continue
        if r.get("tier") != gold:
            not_gold += 1
            continue
        k = (r["date"], str(r.get("symbol") or "").upper())
        if k[1] and k not in first:
            first[k] = r
    rows = sorted(first.values(), key=lambda r: (r["date"], int(r.get("price_ms") or 0), str(r["symbol"]).upper()))
    return rows, not_gold


def t_ev_of(row):
    """§① بدءُ التقييم = الأكبرُ من (المِرساة + 5د) و(شمعةُ سعر الكرت + 1د)."""
    return max(int(row["anchor_ms"]) + B5, int(row.get("price_ms") or 0) + MIN_MS)


def level_of(adj_rows, raw_close_d, day, tl=None):
    """§② ⟵ (L أو None، المصدر). `adj_rows` = [(تاريخ، o، h، l، c)] مسوّاة · `raw_close_d` إغلاقُ D الخامّ.
    `tested` المستوى × (الخامّ ÷ المسوّى ليوم D) · `alert` القاعدةُ لم تجد مستوًى · `alert-fetch` تعذّر الجلب."""
    if not adj_rows or raw_close_d is None:
        return None, "alert-fetch"
    dbar = next((r for r in adj_rows if r[0] == day), None)
    if dbar is None or not dbar[4] or dbar[4] <= 0 or raw_close_d <= 0:
        return None, "alert-fetch"
    k = float(raw_close_d) / float(dbar[4])
    prior = [r for r in adj_rows if r[0] < day]
    if tl is None:
        from Super_stock import tested_level as tl
    import pandas as pd
    lv = tl(pd.DataFrame({"Low": [float(r[3]) for r in prior]})) if prior else None
    if not lv:
        return None, "alert"
    return float(lv["level"]) * k, "tested"


def exit_plan(bars, t0, e, s, t1=T1, t2=T2):
    """§③ الخطّةُ المشتركة — الوقفُ أوّلًا بإغلاق الدقيقة · نصفٌ عند ‏+20% ونصفٌ عند ‏+50% بأمر حدّ · الباقي بإغلاق آخر شمعة."""
    g1, g2 = e * (1.0 + t1), e * (1.0 + t2)
    x1 = x2 = None
    h1 = h2 = stopped = False
    last = None
    for b in bars:
        t, _o, h, _l, c, _v = b
        if t < t0:
            continue
        last = float(c)
        if c < s:
            x1 = c if x1 is None else x1
            x2 = c if x2 is None else x2
            stopped = True
            break
        if x1 is None and h >= g1:
            x1, h1 = g1, True
        if x2 is None and h >= g2:
            x2, h2 = g2, True
        if x1 is not None and x2 is not None:
            break
    end = last if last is not None else e
    x1 = end if x1 is None else x1
    x2 = end if x2 is None else x2
    risk = e - s
    R = (0.5 * (x1 - e) + 0.5 * (x2 - e)) / risk if risk > 0 else None
    return {"R": R, "pct": ((0.5 * x1 + 0.5 * x2) / e - 1.0) * 100.0, "hit20": h1, "hit50": h2,
            "stop": stopped, "eod": (not stopped and not (h1 and h2))}


def arm_b(bars, t_ev, P, L, band=BAND):
    """§③ب ⟵ {ret · entry · e · s · t0 · t_ret · dep}: مغادرةٌ فوق `1.05·L` ثمّ عودةٌ (قاعٌ `≤ 1.05·L`) في شمعةٍ لاحقة ⟵
    أوّلُ شمعة 5د من شمعة العودة فصاعدًا إغلاقُها فوق `L` · والوقفُ أدنى Low من العودة حتى نهاية شمعة الدخول."""
    hi = L * (1.0 + band)
    departed = P > hi
    out = {"ret": False, "entry": False, "dep": departed}
    t_ret = None
    for b in bars:
        t, _o, h, lo, _c, _v = b
        if t < t_ev:
            continue
        if not departed:
            if h > hi:
                departed = True
            continue
        if lo <= hi:
            t_ret = t
            break
    if t_ret is None:
        return out
    out.update(ret=True, t_ret=t_ret)
    b0 = t_ret - t_ret % B5
    groups = {}
    for b in bars:
        if b[0] >= b0:
            groups.setdefault(b[0] - b[0] % B5, []).append(b)
    dip = None
    for st in sorted(groups):
        grp = groups[st]
        for b in grp:
            if b[0] >= t_ret:
                dip = b[3] if dip is None else min(dip, b[3])
        if grp[-1][4] > L:
            out.update(entry=True, e=float(grp[-1][4]), s=float(dip), t0=st + B5)
            return out
    return out


def control_R(bars, t_ev, risk_frac, key, k=K_DRAWS):
    """§④ الضابط ⟵ (متوسّطُ R المشذَّب للسحوب، عددُها): شمعةُ 5د عشوائيّة تبدأ بعد `t_ev` · الدخولُ إغلاقُها · الوقفُ بنسبة وقف `ب`."""
    groups = {}
    for b in bars:
        st = b[0] - b[0] % B5
        if st >= t_ev:
            groups.setdefault(st, []).append(b)
    starts = sorted(groups)
    if not starts or not (0 < risk_frac < 1):
        return None, 0
    rng = random.Random(key)
    vals = []
    for _ in range(int(k)):
        st = starts[rng.randrange(len(starts))]
        e = float(groups[st][-1][4])
        r = exit_plan(bars, st + B5, e, e * (1.0 - risk_frac))["R"]
        if r is not None:
            vals.append(wins(r))
    return (mean(vals), len(vals))


def boot_ci(pairs, n=BOOT_N, seed=BOOT_SEED):
    """§④ فاصلُ 95% لمتوسّط القيم بإعادة عناقيد الأيّام · `pairs` = [(يوم، قيمة)]."""
    per = {}
    for d, v in pairs:
        if v is None:
            continue
        c = per.setdefault(d, [0.0, 0])
        c[0] += v
        c[1] += 1
    keys = sorted(per)
    if len(keys) < 2:
        return None
    rng = random.Random(seed)
    ds = []
    for _ in range(int(n)):
        s = m = 0
        for _k in range(len(keys)):
            c = per[keys[rng.randrange(len(keys))]]
            s += c[0]
            m += c[1]
        if m:
            ds.append(s / m)
    ds.sort()
    return (ds[int(0.025 * len(ds))], ds[int(0.975 * len(ds)) - 1]) if ds else None


def arm_stats(trades, n_alerts):
    """{n · nR · w · raw · med · pos · hit20 · hit50 · stop · eod} ونسبُ الأهداف من الصفقات ومن الإشعارات."""
    rs = [t["R"] for t in trades if t.get("R") is not None]
    n = len(trades)

    def _sh(key, den):
        return (100.0 * sum(1 for t in trades if t.get(key)) / den) if den else None
    return {"n": n, "nR": len(rs), "w": mean([wins(x) for x in rs]), "raw": mean(rs), "med": median(rs),
            "pos": _sh("pos", n), "hit20": _sh("hit20", n), "hit50": _sh("hit50", n), "stop": _sh("stop", n), "eod": _sh("eod", n),
            "hit20_all": _sh("hit20", n_alerts), "hit50_all": _sh("hit50", n_alerts)}


def summarize(rows):
    """§④ من صفوف الإشعارات ⟵ الإحصاءاتُ والفرقان والتفكيك."""
    ev = [r for r in rows if r.get("bars")]
    nev = len(ev)
    A = [r["A"] for r in ev if r.get("A")]
    B = [r["B"] for r in ev if r.get("B") and r["B"].get("entry")]
    res = {"n_pop": len(rows), "n_ev": nev, "n_nobars": len(rows) - nev,
           "src": {s: sum(1 for r in ev if r.get("src") == s) for s in ("tested", "alert", "alert-fetch")},
           "ret": sum(1 for r in ev if (r.get("B") or {}).get("ret")), "entry": len(B),
           "A": arm_stats(A, nev), "B": arm_stats(B, nev),
           "AT10": {"nR": sum(1 for r in ev if r.get("at10") is not None), "w": mean([wins(r["at10"]) for r in ev if r.get("at10") is not None])}}
    pa, b1b, b1a, b2a = [], [], [], []
    for r in ev:
        ra = (r.get("A") or {}).get("R")
        b = r.get("B") or {}
        if ra is None:
            continue
        if b.get("entry"):
            rb = b.get("R")
            if rb is None:
                continue
            pa.append((r["date"], wins(rb) - wins(ra)))
            b1b.append(wins(rb))
            b1a.append(wins(ra))
        else:
            pa.append((r["date"], 0.0 - wins(ra)))
            b2a.append(wins(ra))
    f = (len(b1b) / len(pa)) if pa else None
    res["DA"] = mean([v for _d, v in pa])
    res["DA_n"] = len(pa)
    res["DA_ci"] = boot_ci(pa)
    res["B1"] = {"n": len(b1b), "B": mean(b1b), "A": mean(b1a)}
    res["B2"] = {"n": len(b2a), "A": mean(b2a)}
    res["f"] = f
    res["DA_check"] = ((f * ((res["B1"]["B"] or 0) - (res["B1"]["A"] or 0)) - (1 - f) * (res["B2"]["A"] or 0))
                       if f is not None else None)
    pc = [(r["date"], wins(r["B"]["R"]) - r["C"]) for r in ev
          if (r.get("B") or {}).get("entry") and r["B"].get("R") is not None and r.get("C") is not None]
    res["C"] = {"n": len(pc), "w": mean([r["C"] for r in ev if (r.get("B") or {}).get("entry") and r.get("C") is not None])}
    res["DC"] = mean([v for _d, v in pc])
    res["DC_n"] = len(pc)
    res["DC_ci"] = boot_ci(pc)
    return res


def verdict(res):
    """§⑥ ⟵ (الفرع، نصّ). 0 = «لا قياس»."""
    n_pop, n_ev = res["n_pop"], res["n_ev"]
    if not n_pop or res["n_nobars"] / n_pop > MISS_MAX:
        return 0, "«لا قياس» — شموعُ الدقيقة تعذّرت لأكثر من 10% من الإشعارات"
    if res["src"].get("alert-fetch", 0) / n_ev > MISS_MAX:
        return 0, "«لا قياس» — تعذّر جلبُ اليوميّة لأكثر من 10% من الإشعارات"
    if res["DA_n"] < A_MIN:
        return 0, "«لا قياس» — الإشعاراتُ بـR معرَّفٍ للذراع أ دون 100"
    if res["B1"]["n"] < B_MIN:
        return 0, "«لا قياس» — صفقاتُ الذراع ب بـR معرَّفٍ دون 20"

    def _pass(x, ci):
        return x is not None and x > 0 and ci is not None and ci[0] > 0
    da, dc = _pass(res["DA"], res["DA_ci"]), _pass(res["DC"], res["DC_ci"])
    if da and dc:
        return 1, "① «يعبر بالأضعف» ⟵ تُفتح المرحلة 2 (ثلاثُ سنوات PIT بملحقٍ قبل أيّ رقم)"
    if da:
        return 2, "② «لا يعبر — التجنّبُ لا التوقيت»"
    return 3, "③ «لا يعبر»"


def predictions(res, branch):
    ne = res["n_ev"] or 0
    ci = res.get("DC_ci")
    a, b = res["A"], res["B"]
    return {
        "J1PB1": bool(ne) and 0.20 <= res["ret"] / ne <= 0.50,
        "J1PB2": 20 <= res["entry"] <= 60,
        "J1PB3": bool(ne) and 0.25 <= res["src"].get("tested", 0) / ne <= 0.60,
        "J1PB4": a["w"] is not None and a["w"] < 0,
        "J1PB5": b["w"] is not None and b["w"] < 0,
        "J1PB6": res["DA"] is not None and res["DA"] > 0,
        "J1PB7": ci is not None and ci[0] <= 0 <= ci[1],
        "J1PB8": a["hit20"] is not None and b["hit20"] is not None and a["hit20"] > b["hit20"],
        "J1PB9": a["hit50"] is not None and b["hit50"] is not None and a["hit50"] <= 10.0 and b["hit50"] <= 10.0,
        "J1PB10": branch != 1,
    }


def _f(v, s="+.3f"):
    return format(v, s) if v is not None else "—"


def _ci(c):
    return f"[{_f(c[0])}، {_f(c[1])}]" if c else "[—]"


def report_lines(res, branch_txt, preds, meta, not_gold=0):
    a, b = res["A"], res["B"]
    L = ["# 🥇↩️ `T-J1-PULLBACK` — النتيجة (مولَّدةٌ بـ`j1_pullback.py --mode run` · لا رقمَ باليد)", "",
         f"**التشغيلة:** {meta.get('run')} · main `{(meta.get('sha') or '')[:9]}` · السجلّ عند `{LEDGER_REF[:9]}`", "",
         "## ① المجتمع", "",
         f"- إشعاراتُ 🥇 J1 في الإطار: **{res['n_pop']}** · بشموع دقيقة **{res['n_ev']}** · تعذّرت شموعُها {res['n_nobars']} · "
         f"وصفوفُ J1 بلا 🥇 خارجَ المجتمع {not_gold}",
         f"- مصدرُ `L`: tested {res['src'].get('tested', 0)} · alert {res['src'].get('alert', 0)} · alert-fetch {res['src'].get('alert-fetch', 0)}",
         f"- **أعطى عودةً: {res['ret']} من {res['n_ev']}** ({_f(100.0 * res['ret'] / res['n_ev'] if res['n_ev'] else None, '.1f')}%) · "
         f"ومنها **دخولٌ (إغلاق 5د فوق L): {res['entry']}**", "",
         "## ② R لكلّ ذراع (مشذَّبٌ ±10R · الخامّ بين قوسين)", "",
         "| الذراع | الصفقات (بـR) | متوسّطُ R | الوسيط | الموجب % | ‏+20% من الصفقات | ‏+50% من الصفقات | ‏+20% من الإشعارات | ‏+50% من الإشعارات | وقف % | نهايةُ اليوم % |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for nm, s in (("أ — لحظةُ الإشعار", a), ("ب — العودة (فيصل)", b)):
        L.append(f"| {nm} | {s['n']} ({s['nR']}) | {_f(s['w'])} ({_f(s['raw'])}) | {_f(s['med'])} | {_f(s['pos'], '.1f')} | {_f(s['hit20'], '.1f')} | "
                 f"{_f(s['hit50'], '.1f')} | {_f(s['hit20_all'], '.1f')} | {_f(s['hit50_all'], '.1f')} | {_f(s['stop'], '.1f')} | {_f(s['eod'], '.1f')} |")
    L += [f"| C — الضابطُ العشوائيّ (على صفقات ب · 20 سحبًا · وقفٌ مطابق) | {res['C']['n']} | {_f(res['C']['w'])} | | | | | | | | |", "",
          f"- وصفًا: `A-T10` (الهدفُ ‏+10% الحاكمُ في `T-J1-PROFIT`) مشذَّبًا {_f(res['AT10']['w'])} على {res['AT10']['nR']}", "",
          "## ③ الفرقان (فاصلُ 95% · عناقيدُ الأيّام · 2,000 · بذرة 20261107)", "",
          f"- **`D_A`** (لكلّ إشعار · ب أو 0 − أ) = **{_f(res['DA'])}** {_ci(res['DA_ci'])} على {res['DA_n']}",
          f"- **`D_C`** (لكلّ صفقة ب · ب − الضابط) = **{_f(res['DC'])}** {_ci(res['DC_ci'])} على {res['DC_n']}",
          f"- التفكيك: `B1` (ما دخلته ب · {res['B1']['n']}) ب {_f(res['B1']['B'])} مقابل أ {_f(res['B1']['A'])} · "
          f"`B2` (ما تركته ب · {res['B2']['n']}) أ {_f(res['B2']['A'])} · f = {_f(res['f'], '.3f')} ⟵ "
          f"f·(B1ب − B1أ) − (1 − f)·B2أ = {_f(res['DA_check'])}", "",
          f"## ④ الحكم: **{branch_txt}**", "",
          "## ⑤ التنبّؤات (منشورةٌ قبل الرقم)", ""]
    for k, v in preds.items():
        L.append(f"- `{k}` {'✅' if v else '❌'}")
    L += ["", "🔒 لا شيء يُشحَن · الهدفُ بأمر حدٍّ بلا انزلاقٍ ولا تكلفة ⟵ الرقمُ سقفٌ والفرقُ هو الحكم · والقراءةُ داخل يوم الإشعار وحدَه."]
    return L


# ── الملحق D (نقيّة) ──────────────────────────────────────────────────────────────────────────────────────
def ny_close_cut(t_ms):
    """16:00 نيويورك ليوم `t_ms` (ميلّي ثانية UTC)."""
    from zoneinfo import ZoneInfo
    d = dt.datetime.fromtimestamp(int(t_ms) / 1000, tz=ZoneInfo("America/New_York"))
    return int(d.replace(hour=16, minute=0, second=0, microsecond=0).timestamp() * 1000)


def d_cut(t_d):
    """§② حدُّ «الإغلاق»: 16:00 إن كان الدخولُ قبلها · وإلّا None (آخرُ شمعةٍ في اليوم)."""
    c = ny_close_cut(t_d)
    return c if t_d < c else None


def d_entry(bars, t_d):
    """§② سعرُ الدخول = إغلاقُ آخر شمعةٍ بدايتُها قبل `t_d`."""
    prev = [b for b in bars if b[0] < t_d]
    return float(prev[-1][4]) if prev else None


def plan_d(bars, t0, E, cut=None, t1=D_T1, t2=D_T2, cat=D_CAT):
    """§② الخطّة D: أمرا حدٍّ على الذيل (نصفٌ ‏+20% · نصفٌ ‏+50%) · وقفٌ كارثيٌّ −30% بالأدنى من (الافتتاح · سعرِه) والوقفُ أوّلًا ·
    والباقي بإغلاق آخر شمعةٍ قبل `cut` (أو آخر شمعةٍ في اليوم)."""
    g1, g2, gs = E * (1.0 + t1), E * (1.0 + t2), E * (1.0 - cat)
    x1 = x2 = None
    h1 = h2 = hit_cat = False
    last = None
    for b in bars:
        t, o, h, lo, c, _v = b
        if t < t0:
            continue
        if cut is not None and t >= cut:
            break
        last = float(c)
        if lo <= gs:
            px = min(float(o), gs)
            x1 = px if x1 is None else x1
            x2 = px if x2 is None else x2
            hit_cat = True
            break
        if x1 is None and h >= g1:
            x1, h1 = g1, True
        if x2 is None and h >= g2:
            x2, h2 = g2, True
        if x1 is not None and x2 is not None:
            break
    end = last if last is not None else E
    x1 = end if x1 is None else x1
    x2 = end if x2 is None else x2
    pct = ((0.5 * x1 + 0.5 * x2) / E - 1.0) * 100.0
    kind = "cat" if hit_cat else ("t50" if (h1 and h2) else "close")
    return {"pct": pct, "R": pct / (cat * 100.0), "hit20": h1, "hit50": h2, "cat": hit_cat, "kind": kind}


def control_d(bars, t_d, cut, key, k=K_DRAWS):
    """§③ `C_D`: شمعةُ دقيقةٍ عشوائيّة من `t_d` حتى قبل الحدّ · الدخولُ إغلاقُها · والخطّةُ D من الشمعة التالية ⟵ متوسّطُ العائد %."""
    cand = [b for b in bars if b[0] >= t_d and (cut is None or b[0] < cut)]
    if not cand:
        return None
    rng = random.Random(key)
    vals = []
    for _ in range(int(k)):
        b = cand[rng.randrange(len(cand))]
        vals.append(plan_d(bars, b[0] + MIN_MS, float(b[4]), cut)["pct"])
    return mean(vals)


def summarize_d(rows):
    """§④ من صفوف الملحق D."""
    ev = [r for r in rows if r.get("bars")]
    ok = [r for r in ev if r.get("D")]
    ds = [r["D"] for r in ok]
    n = len(ds)

    def _sh(key):
        return (100.0 * sum(1 for d in ds if d.get(key)) / n) if n else None
    buckets = []
    for lo, hi in D_BUCKETS:
        buckets.append(sum(1 for d in ds if lo < d["pct"] <= hi) if lo > -1e9 else sum(1 for d in ds if d["pct"] <= hi))
    tail = sorted(({"date": r["date"], "symbol": r["symbol"], "pct": r["D"]["pct"], "kind": r["D"]["kind"]}
                   for r in ok if r["D"]["pct"] <= -10.0), key=lambda x: x["pct"])
    worst = sorted(({"date": r["date"], "symbol": r["symbol"], "pct": r["D"]["pct"], "kind": r["D"]["kind"]} for r in ok),
                   key=lambda x: x["pct"])[:10]
    pa = [(r["date"], r["D"]["pct"] - r["A_pct"]) for r in ok if r.get("A_pct") is not None]
    pc = [(r["date"], r["D"]["pct"] - r["C"]) for r in ok if r.get("C") is not None]
    pr = [(r["date"], r["D"]["R"]) for r in ok]
    return {"n_pop": len(rows), "n_ev": len(ev), "n_nobars": len(rows) - len(ev), "n_ok": n,
            "R": mean([d["R"] for d in ds]), "R_ci": boot_ci(pr), "R_med": median([d["R"] for d in ds]),
            "pct": mean([d["pct"] for d in ds]), "pct_med": median([d["pct"] for d in ds]),
            "pos": (100.0 * sum(1 for d in ds if d["pct"] > 0) / n) if n else None,
            "hit20": _sh("hit20"), "hit50": _sh("hit50"), "cat": _sh("cat"),
            "close": (100.0 * sum(1 for d in ds if d["kind"] == "close") / n) if n else None,
            "buckets": buckets, "tail": tail, "worst": worst,
            "A_pct": mean([r["A_pct"] for r in ok if r.get("A_pct") is not None]),
            "C_pct": mean([r["C"] for r in ok if r.get("C") is not None]),
            "DA": mean([v for _d, v in pa]), "DA_ci": boot_ci(pa), "DA_n": len(pa),
            "DC": mean([v for _d, v in pc]), "DC_ci": boot_ci(pc), "DC_n": len(pc)}


def verdict_d(res):
    """§⑤ ⟵ (رمز، نصّ): 0 «لا قياس» · 1 المرحلة 2 تُفتح (متوسّطُ R_D فوق الصفر) · 2 لا تُفتح."""
    if not res["n_pop"] or res["n_nobars"] / res["n_pop"] > MISS_MAX or res["n_ok"] < A_MIN:
        return 0, "«لا قياس» — شموعٌ تعذّرت لأكثر من 10% أو أقلُّ من 100 إشعارٍ بعائدٍ معرَّف"
    if res["R"] is not None and res["R"] > 0:
        return 1, "R_D موجب ⟵ **تُفتح المرحلة 2** (ثلاثُ سنوات PIT بملحقٍ قبل أيّ رقم)"
    return 2, "R_D غيرُ موجب ⟵ المرحلة 2 لا تُفتح · لا شيء يُشحَن"


def predictions_d(res, code):
    ci = res.get("DC_ci")
    return {
        "J1PD1": res["R"] is not None and res["R"] < 0,
        "J1PD2": res["pct"] is not None and -15.0 <= res["pct"] <= 0.0,
        "J1PD3": res["cat"] is not None and 15.0 <= res["cat"] <= 35.0,
        "J1PD4": (res["hit20"] is not None and 20.0 <= res["hit20"] <= 30.0 and res["hit50"] is not None and 8.0 <= res["hit50"] <= 18.0),
        "J1PD5": res["DA"] is not None and res["DA"] < 0,
        "J1PD6": ci is not None and ci[0] <= 0 <= ci[1],
        "J1PD7": bool(res["worst"]) and all(w["kind"] == "cat" for w in res["worst"]),
    }


def report_lines_d(res, txt, preds, meta):
    names = ("−30% فأدنى", "−30…−20", "−20…−10", "−10…0", "0…10", "10…20", "20…35")
    kinds = {"cat": "كارثيّ −30%", "close": "الإغلاق", "t50": "‏+50%"}
    L = ["## ⑦ الملحق D — أوامرُ بيعٍ استباقيّة بلا وقفٍ ضيّق (مولَّدٌ بـ`j1_pullback.py --mode armd` · لا رقمَ باليد)", "",
         f"**التشغيلة:** {meta.get('run')} · main `{(meta.get('sha') or '')[:9]}`", "",
         f"- الإشعارات {res['n_pop']} · بشموع {res['n_ev']} · بعائدٍ معرَّف **{res['n_ok']}**",
         f"- **`R_D` لكلّ إشعار (العائد ÷ 30%): المتوسّط {_f(res['R'])} {_ci(res['R_ci'])} · الوسيط {_f(res['R_med'])}** · "
         f"العائدُ % المتوسّط {_f(res['pct'], '+.2f')} والوسيط {_f(res['pct_med'], '+.2f')} · الموجب {_f(res['pos'], '.1f')}%",
         f"- ‏+20% {_f(res['hit20'], '.1f')}% · ‏+50% {_f(res['hit50'], '.1f')}% · الوقفُ الكارثيّ {_f(res['cat'], '.1f')}% · خرج الباقي بالإغلاق "
         f"{_f(res['close'], '.1f')}%", "",
         "| السلّة (العائد %) | " + " | ".join(names) + " |", "|---|" + "---|" * len(names),
         "| الإشعارات | " + " | ".join(str(x) for x in res["buckets"]) + " |", "",
         f"- **مقابل A** (العائد % لكلّ إشعار): A {_f(res['A_pct'], '+.2f')} · `D − A` = **{_f(res['DA'], '+.2f')}** {_ci(res['DA_ci'])} على {res['DA_n']}",
         f"- **مقابل العشوائيّ** `C_D` {_f(res['C_pct'], '+.2f')} · `D − C_D` = **{_f(res['DC'], '+.2f')}** {_ci(res['DC_ci'])} على {res['DC_n']}", "",
         f"**الحكم: {txt}**", "", "**أسوأ 10 صفقات:**", ""]
    for w in res["worst"]:
        L.append(f"- {w['date']} {w['symbol']} {_f(w['pct'], '+.2f')}% ({kinds.get(w['kind'], w['kind'])})")
    L += ["", f"**الذيلُ الأيسر بالأسماء (العائد −10% فأدنى · {len(res['tail'])}):**", ""]
    L.append(" · ".join(f"{w['date'][5:]} {w['symbol']} {_f(w['pct'], '+.1f')}%" for w in res["tail"]) or "—")
    L += ["", "**التنبّؤات (الملحق §⑥ · منشورةٌ قبل الرقم):**", ""]
    for k, v in preds.items():
        L.append(f"- `{k}` {'✅' if v else '❌'}")
    return L


# ── الجلب (رنر) ─────────────────────────────────────────────────────────────────────────────────────────
def fetch_daily(sym, d0, d1, key, adjusted, get=None):
    """يوميّةُ Polygon ⟵ [(تاريخ نيويورك، o، h، l، c)] أو None."""
    import requests
    from zoneinfo import ZoneInfo
    g = requests.get if get is None else get
    ny = ZoneInfo("America/New_York")
    try:
        r = g(f"https://api.polygon.io/v2/aggs/ticker/{str(sym).upper()}/range/1/day/{d0}/{d1}"
              f"?adjusted={'true' if adjusted else 'false'}&sort=asc&limit=200",
              headers={"Authorization": f"Bearer {key}"}, timeout=30)
        if getattr(r, "status_code", 0) != 200:
            return None
        return [(dt.datetime.fromtimestamp(b["t"] / 1000, tz=ny).date().isoformat(), float(b["o"]), float(b["h"]),
                 float(b["l"]), float(b["c"])) for b in (r.json() or {}).get("results") or []]
    except Exception:                                                # noqa: BLE001
        return None


def measure(row, bars, adj, raw):
    """صفُّ إشعارٍ واحد ⟵ قاموس (يُكتب في `j1pb_rows.json`)."""
    import target10_arms as T10
    day, sym = row["date"], str(row["symbol"]).upper()
    out = {"date": day, "symbol": sym, "bars": bool(bars)}
    if not bars:
        return out
    P, alow, t_ev = float(row["e5"]), float(row["anchor_low"]), t_ev_of(row)
    raw_c = next((r[4] for r in (raw or []) if r[0] == day), None)
    L, src = level_of(adj, raw_c, day)
    out["src"] = src
    out["L"] = L if L is not None else P
    L = out["L"]
    a = exit_plan(bars, t_ev, P, alow)
    a["pos"] = a["pct"] > 0
    out["A"] = a
    px10, _k = T10.arm_exit(bars, int(row["anchor_ms"]), alow, P, 10.0)
    out["at10"] = ((px10 - P) / (P - alow)) if (px10 is not None and P > alow) else None
    b = arm_b(bars, t_ev, P, L)
    if b.get("entry"):
        x = exit_plan(bars, b["t0"], b["e"], b["s"])
        x["pos"] = x["pct"] > 0
        b.update(x)
        if b.get("R") is not None and b["e"] > 0:
            out["C"], out["C_n"] = control_R(bars, t_ev, (b["e"] - b["s"]) / b["e"], f"20261107:{day}:{sym}")
    out["B"] = b
    return out


def mode_run():
    from concurrent.futures import ThreadPoolExecutor
    from tier_fwd_report import fetch_day
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key:
        log("⛔ بلا مفتاح Polygon — لا قياس")
        return 3
    U = json.load(open(UNIVERSE, encoding="utf-8"))
    led = subprocess.run(["git", "show", f"{LEDGER_REF}:tier_fwd_ledger.jsonl"], capture_output=True, text=True).stdout
    if not led.strip():
        log("⛔ تعذّر قراءةُ السجلّ عند المرجع — لا قياس")
        return 3
    rows, not_gold = population(led.splitlines(), set(U["sessions"]))
    log(f"📥 إشعاراتُ 🥇 J1: {len(rows)} على {len({r['date'] for r in rows})} جلسة · J1 بلا 🥇 {not_gold}")

    def _one(row):
        day = row["date"]
        d0 = (dt.date.fromisoformat(day) - dt.timedelta(days=60)).isoformat()
        bars = fetch_day(row["symbol"], day, key)
        adj = fetch_daily(row["symbol"], d0, day, key, True) if bars else None
        raw = fetch_daily(row["symbol"], day, day, key, False) if bars else None
        try:
            return measure(row, bars, adj, raw)
        except Exception as e:                                       # noqa: BLE001
            log(f"⛔ {day} {row['symbol']}: {type(e).__name__}")
            return {"date": day, "symbol": str(row["symbol"]).upper(), "bars": False, "err": type(e).__name__}
    with ThreadPoolExecutor(8) as pool:
        got = list(pool.map(_one, rows))
    json.dump(got, open(OUT_ROWS, "w", encoding="utf-8"), ensure_ascii=False, default=str)
    res = summarize(got)
    br, txt = verdict(res)
    preds = predictions(res, br)
    meta = {"run": os.environ.get("GITHUB_RUN_ID"),
            "sha": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()}
    for ln in report_lines(res, txt, preds, meta, not_gold):
        print(ln)
    print("J1PB_JSON " + json.dumps({"res": res, "branch": br, "preds": preds, "meta": meta, "not_gold": not_gold},
                                    ensure_ascii=False, default=str))
    return 0


def measure_d(row, bars):
    """صفُّ إشعارٍ واحد للملحق D."""
    day, sym = row["date"], str(row["symbol"]).upper()
    out = {"date": day, "symbol": sym, "bars": bool(bars)}
    if not bars:
        return out
    t_ev = t_ev_of(row)
    t_d = t_ev + D_DELAY
    E = d_entry(bars, t_d)
    if not E or E <= 0:
        return out
    cut = d_cut(t_d)
    out["E"] = E
    out["D"] = plan_d(bars, t_d, E, cut)
    out["A_pct"] = exit_plan(bars, t_ev, float(row["e5"]), float(row["anchor_low"]))["pct"]
    out["C"] = control_d(bars, t_d, cut, f"20261107:D:{day}:{sym}")
    return out


def mode_armd():
    from concurrent.futures import ThreadPoolExecutor
    from tier_fwd_report import fetch_day
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key:
        log("⛔ بلا مفتاح Polygon — لا قياس")
        return 3
    U = json.load(open(UNIVERSE, encoding="utf-8"))
    led = subprocess.run(["git", "show", f"{LEDGER_REF}:tier_fwd_ledger.jsonl"], capture_output=True, text=True).stdout
    if not led.strip():
        log("⛔ تعذّر قراءةُ السجلّ عند المرجع — لا قياس")
        return 3
    rows, _ng = population(led.splitlines(), set(U["sessions"]))
    log(f"📥 الملحق D: {len(rows)} إشعارًا")

    def _one(row):
        try:
            return measure_d(row, fetch_day(row["symbol"], row["date"], key))
        except Exception as e:                                       # noqa: BLE001
            log(f"⛔ {row['date']} {row['symbol']}: {type(e).__name__}")
            return {"date": row["date"], "symbol": str(row["symbol"]).upper(), "bars": False, "err": type(e).__name__}
    with ThreadPoolExecutor(8) as pool:
        got = list(pool.map(_one, rows))
    json.dump(got, open(OUT_ROWS_D, "w", encoding="utf-8"), ensure_ascii=False, default=str)
    res = summarize_d(got)
    code, txt = verdict_d(res)
    preds = predictions_d(res, code)
    meta = {"run": os.environ.get("GITHUB_RUN_ID"),
            "sha": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()}
    for ln in report_lines_d(res, txt, preds, meta):
        print(ln)
    print("J1PD_JSON " + json.dumps({"res": res, "code": code, "preds": preds, "meta": meta}, ensure_ascii=False, default=str))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("check", "run", "armd"), default="check")
    a = ap.parse_args(argv)
    if not contract_ok():
        log("⛔ بصمةُ العقد تغيّرت — خروج 9 (لا قياس).")
        return CONTRACT_RC
    if a.mode in ("check", "armd") and not addendum_ok():
        log("⛔ بصمةُ الملحق D تغيّرت — خروج 9 (لا قياس).")
        return CONTRACT_RC
    if a.mode == "check":
        log("🔒 بصمةُ العقد والملحق D ✅")
        return 0
    if a.mode == "armd":
        return mode_armd()
    return mode_run()


if __name__ == "__main__":
    sys.exit(main())
