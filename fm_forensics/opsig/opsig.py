#!/usr/bin/env python3
"""🕵️📈 `T-OPSIG` «إشعار المضارب يدفع» (العقد `fm_forensics/opsig/T_OPSIG_prereg.md` · مدموجٌ قبل أيّ رقم) — قراءةٌ فقط · ومعه مُخرَجُ العرض ④.

`--mode check` بصمةُ العقد بلا شبكة · `--mode run` (رنر · Polygon · تاريخُ git كامل): المراسي المصحَّحة (`live_vs_shadow.rebuild_alerts`) على أيّام المصدر وكون
`L ∪ N` (بوّابةُ 1,561) ⟵ شموعُ الدقيقة (`tier_fwd_report.fetch_day`) وصفقاتُ وأسعارُ Polygon في النافذة ⟵ السماتُ الأربع (قبل الدخول) ⟵ النتيجةُ من
`t_a + 2 د` (نجاح ‏+20% قبل −10% · كارثيّ −20% خلال 30 د) ⟵ جداولُ الكلّ و🥇 J1 وأكتوبر · وحكمُ «تفرّق» بفاصل عناقيد الأيّام · وسطرُ الكرت المقترح ④.
🔒 لا تلغرام · لا كتابة في المستودع · لا تغيير في أيّ أداة · وتخرج 9 إن تغيّرت بصمةُ العقد.
"""
import argparse
import bisect
import hashlib
import itertools
import json
import math
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

CONTRACT = os.path.join(HERE, "T_OPSIG_prereg.md")
CONTRACT_SHA = "61a9160ac6faabbd4fc67d78e5ad4ba0ef09d3dbe56c6536e89f41d522128e60"
CONTRACT_RC = 9
N_GATE = 1561                                    # §① بوّابةُ الصدق (LVS §④ المصحَّح)
MIN_MS = 60_000
T_UP, T_DN, T_CAT, CAT_MIN = 0.20, 0.10, 0.20, 30
A_MIN, B_MIN, C_MIN = 0.60, 0.50, 0.50           # §③ حدودُ السمات
A_TRADES_MIN = 20
FLOOR = 30
A_UNKNOWN_MAX, MISS_MAX = 0.25, 0.10
BOOT_N, BOOT_SEED = 2000, 20261107
DAYS_SRC = 47
GOLD = "قوي"
ATTRS = ("a", "b", "c", "d")


def log(m=""):
    print(m, flush=True)


def contract_ok(path=CONTRACT):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest() == CONTRACT_SHA
    except OSError:
        return False


# ── دوالُّ نقيّة (مقفولةٌ في السويّة) ─────────────────────────────────────────────────────────────────────
def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


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
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def entry_px(bars, t):
    """إغلاقُ آخر شمعةٍ بدايتُها قبل `t`."""
    prev = [b for b in bars if b[0] < t]
    return float(prev[-1][4]) if prev else None


def outcome(bars, t0, E, up=T_UP, dn=T_DN, cat=T_CAT, cat_min=CAT_MIN):
    """§② ⟵ {res: win/loss/open · cat · maxg (أعلى ربح %) · stop10 (النتيجة بوقف −10% %)} من الشموع التي تبدأ عند `t0` فصاعدًا."""
    gu, gd, gc = E * (1 + up), E * (1 - dn), E * (1 - cat)
    res, hit_cat, mx, last, stop_px = "open", False, None, None, None
    for b in bars:
        t, _o, h, lo, c, _v = b
        if t < t0:
            continue
        last = float(c)
        mx = h if mx is None else max(mx, h)
        if t < t0 + cat_min * MIN_MS and lo <= gc:
            hit_cat = True
        if stop_px is None and lo <= gd:
            stop_px = gd
        if res == "open":
            if lo <= gd:
                res = "loss"
            elif h >= gu:
                res = "win"
    maxg = ((mx / E - 1) * 100.0) if mx is not None else None
    s10 = ((stop_px if stop_px is not None else (last if last is not None else E)) / E - 1) * 100.0
    return {"res": res, "cat": hit_cat, "maxg": maxg, "stop10": s10}


def attr_b(bars, ms):
    """(ب) أكبرُ (رأس ÷ إغلاق الشمعة السابقة − 1) على الشموع التي تبدأ في [ms − 5د، ms] · ⟵ نسبة %."""
    best, prev = None, None
    for b in bars:
        t = b[0]
        if prev is not None and ms - 5 * MIN_MS <= t <= ms and prev[4]:
            j = (b[2] / prev[4] - 1) * 100.0
            best = j if best is None else max(best, j)
        prev = b
    return best


def attr_c(bars, ms):
    """(ج) حجمُ شمعة المِرساة ÷ حجمِ الشموع العشر المنتهية بها."""
    win = [b for b in bars if ms - 9 * MIN_MS <= b[0] <= ms]
    tot = sum(float(b[5] or 0) for b in win)
    a = next((float(b[5] or 0) for b in win if b[0] == ms), None)
    return (a / tot) if (a is not None and tot > 0) else None


def attr_d(bars, ms):
    """(د) ⟵ (ثابت؟، منتصفُ الشمعة الكبيرة): الأوسعُ مدًى في [ms − 5د، ms] · وإغلاقاتُ الشموع عند ms+1/+2/+3 (الموجودةُ منها) كلُّها فوق المنتصف."""
    big = [b for b in bars if ms - 5 * MIN_MS <= b[0] <= ms]
    if not big:
        return None, None
    g = max(big, key=lambda b: (b[2] - b[3]))
    m = (g[2] + g[3]) / 2.0
    nxt = [b for b in bars if b[0] in (ms + MIN_MS, ms + 2 * MIN_MS, ms + 3 * MIN_MS)]
    if not nxt:
        return None, m
    return all(b[4] > m for b in nxt), m


def lee_ready(trades, quotes):
    """(أ) حصّةُ حجم الشراء من الحجم المصنَّف · `trades` [(ts، سعر، حجم)] و`quotes` [(ts، bid، ask)] مرتَّبة · ⟵ (حصّة، عددُ الصفقات) أو (None، n)."""
    if not trades:
        return None, 0
    qts = [q[0] for q in quotes]
    buy = tot = 0.0
    last_px, last_side = None, 0
    for ts, px, sz in trades:
        i = bisect.bisect_right(qts, ts) - 1
        side = 0
        if i >= 0:
            bid, ask = quotes[i][1], quotes[i][2]
            if bid and ask and ask >= bid > 0:
                mid = (bid + ask) / 2.0
                side = 1 if px > mid else (-1 if px < mid else 0)
        if side == 0 and last_px is not None:
            side = 1 if px > last_px else (-1 if px < last_px else last_side)
        if px != last_px:
            last_px = px
        if side:
            tot += sz
            buy += sz if side > 0 else 0
            last_side = side
    n = len(trades)
    if n < A_TRADES_MIN or tot <= 0:
        return None, n
    return buy / tot, n


def flags(row):
    """السماتُ الأربع منطقيّةً (المجهولُ لا يمرّ)."""
    return {"a": row.get("a") is not None and row["a"] >= A_MIN,
            "b": row.get("b") is not None and row["b"] >= B_MIN * 100.0,
            "c": row.get("c") is not None and row["c"] >= C_MIN,
            "d": bool(row.get("d"))}


def res_of(row, use_d):
    """النتيجةُ المستعملة: من `E_d` إن كان الفلترُ يحوي (د) · وإلّا من `E`."""
    return (row.get("out_d") if use_d else row.get("out")) or {}


def table_row(rows, keys, runners_by=None, n_unfired=(0, 0)):
    """صفُّ جدول لفلتر `keys` (فارغ = الكلّ)."""
    use_d = "d" in keys
    sel = [r for r in rows if all(flags(r)[k] for k in keys)]
    outs = [res_of(r, use_d) for r in sel]
    outs = [o for o in outs if o.get("res")]
    n = len(outs)
    w = sum(1 for o in outs if o["res"] == "win")
    lo = sum(1 for o in outs if o["res"] == "loss")
    ca = sum(1 for o in outs if o.get("cat"))
    ci = wilson(w, n)
    days = len({r["day"] for r in sel})
    up = [((r.get("E_d") or 0) / r["E"] - 1) * 100.0 for r in sel if use_d and r.get("E") and r.get("E_d")]
    cap50 = cap100 = lost50 = lost100 = 0
    sel_ids = {id(r) for r in sel}
    for r in rows:
        R = (runners_by or {}).get((r["day"], r["sym"]))
        if R is None:
            continue
        inside = id(r) in sel_ids
        cap50 += int(inside and R >= 0.5)
        cap100 += int(inside and R >= 1.0)
        lost50 += int((not inside) and R >= 0.5)
        lost100 += int((not inside) and R >= 1.0)
    return {"keys": "+".join(keys) or "الكلّ", "n": n, "per_day": n / DAYS_SRC, "days": days,
            "win": (100.0 * w / n) if n else None, "win_ci": tuple(100.0 * x for x in ci) if ci[0] is not None else None,
            "loss": (100.0 * lo / n) if n else None, "open": (100.0 * (n - w - lo) / n) if n else None,
            "cat": (100.0 * ca / n) if n else None, "cap50": cap50, "cap100": cap100, "lost50": lost50, "lost100": lost100,
            "unfired50": n_unfired[0], "unfired100": n_unfired[1], "higher": median(up)}


def boot_diff(rows, key, n=BOOT_N, seed=BOOT_SEED):
    """§⑤ فرقُ النجاح (مع − بدون) بفاصل 95% على عناقيد الأيّام."""
    per = {}
    for r in rows:
        f = flags(r)[key]
        o = res_of(r, key == "d" and f)
        if not o.get("res"):
            continue
        c = per.setdefault(r["day"], [0, 0, 0, 0])
        if f:
            c[0] += int(o["res"] == "win")
            c[1] += 1
        else:
            c[2] += int(o["res"] == "win")
            c[3] += 1
    keys = sorted(per)

    def _d(cells):
        a, b, c_, d_ = (sum(x[i] for x in cells) for i in range(4))
        return (a / b - c_ / d_) if (b and d_) else None
    pt = _d([per[k] for k in keys])
    if pt is None or len(keys) < 2:
        return pt, None
    rng = random.Random(seed)
    ds = []
    for _ in range(int(n)):
        v = _d([per[keys[rng.randrange(len(keys))]] for _k in keys])
        if v is not None:
            ds.append(v)
    ds.sort()
    return pt, ((ds[int(0.025 * len(ds))], ds[int(0.975 * len(ds)) - 1]) if ds else None)


def verdict_attr(rows, key):
    """§⑤ ⟵ (الحكم، فرق، فاصل)."""
    if key == "a":
        unk = sum(1 for r in rows if r.get("a") is None)
        if rows and unk / len(rows) > A_UNKNOWN_MAX:
            return "لا قياس", None, None
    w_ = [r for r in rows if flags(r)[key] and res_of(r, key == "d").get("res")]
    wo = [r for r in rows if not flags(r)[key] and res_of(r, False).get("res")]
    if len(w_) < FLOOR or len(wo) < FLOOR:
        return "لا قياس", None, None
    pt, ci = boot_diff(rows, key)
    cat_w = mean([1.0 if res_of(r, key == "d").get("cat") else 0.0 for r in w_])
    cat_o = mean([1.0 if res_of(r, False).get("cat") else 0.0 for r in wo])
    ok = pt is not None and pt > 0 and ci is not None and ci[0] > 0 and (cat_w or 0) <= (cat_o or 0)
    return ("تفرّق" if ok else "لا تفرّق"), pt, ci


def best_pair(rows, runners_by=None, unfired=(0, 0)):
    """أفضلُ زوجٍ = أعلى حدٍّ أدنى لـWilson بأرضيّة 30 (داخل العيّنة · موسوم)."""
    best = None
    for ks in itertools.combinations(ATTRS, 2):
        t = table_row(rows, ks, runners_by, unfired)
        if t["n"] >= FLOOR and t["win_ci"] and (best is None or t["win_ci"][0] > best["win_ci"][0]):
            best = t
    return best


def card_stats(rows):
    """④ ⟵ {وسيط/متوسّط أعلى ربح · وسيط/متوسّط النتيجة بوقف −10% · ‏+20% · ‏+50% · كارثيّ · n}."""
    outs = [r["out"] for r in rows if (r.get("out") or {}).get("res")]
    n = len(outs)
    if not n:
        return {"n": 0}
    mg = [o["maxg"] for o in outs if o.get("maxg") is not None]
    return {"n": n, "maxg_med": median(mg), "maxg_mean": mean(mg),
            "s10_med": median([o["stop10"] for o in outs]), "s10_mean": mean([o["stop10"] for o in outs]),
            "p20": 100.0 * sum(1 for x in mg if x >= 20.0) / n, "p50": 100.0 * sum(1 for x in mg if x >= 50.0) / n,
            "cat": 100.0 * sum(1 for o in outs if o.get("cat")) / n}


def card_line(st):
    """④ النصُّ المقترح: «📊 مثل هذا الإشعار: وسيط الربح X% · 1 من Z بلغ +20% · كارثي Y%»."""
    if not st.get("n") or not st.get("p20"):
        return "📊 مثل هذا الإشعار: لا عيّنة كافية"
    z = max(1, round(100.0 / st["p20"]))
    return f"📊 مثل هذا الإشعار: وسيط الربح {st['maxg_med']:.0f}% · 1 من {z} بلغ +20% · كارثي {st['cat']:.0f}%"


def pop_gate(n_fires, n_split):
    """§① بوّابةُ الصدق على العدد **بعد** استبعاد يوم التقسيم — كما نشره LVS §④ («الإطلاقات 1561 … يومُ تقسيمٍ مستبعَد 35»).
    🔧 عطلٌ مُثبَت في التشغيلة الأولى (`42396386956`): قارنتُ العددَ قبل الاستبعاد (1596 = 1561 ‏+ 35) ⟵ «سقطت» زورًا."""
    n = int(n_fires) - int(n_split)
    return n, n == N_GATE


def predictions(n_pop, all_row, verd, j1_row, cs_norm):
    sep = [k for k in ATTRS if verd[k][0] == "تفرّق"]     # 🔧 السماتُ الأربع وحدَها (`verd` يحمل `b_share` و`d_row` أيضًا ⟵ كان يرمي TypeError)
    d_row = verd.get("d_row") or {}
    return {
        "OPS1": n_pop == N_GATE,
        "OPS2": all_row["win"] is not None and 20.0 <= all_row["win"] <= 35.0,
        "OPS3": all_row["cat"] is not None and 10.0 <= all_row["cat"] <= 25.0,
        "OPS4": verd["a"][0] == "لا تفرّق",
        "OPS5": verd.get("b_share") is not None and verd["b_share"] <= 15.0 and verd["b"][0] != "تفرّق",
        "OPS6": verd["c"][0] == "لا تفرّق",
        "OPS7": verd["d"][0] == "تفرّق" and d_row.get("higher") is not None and 2.0 <= d_row["higher"] <= 8.0,
        "OPS8": (j1_row.get("win") is not None and all_row["win"] is not None and j1_row["win"] >= all_row["win"] + 10.0),
        "OPS9": len(sep) <= 1,
        "OPS10": cs_norm.get("maxg_med") is not None and 5.0 <= cs_norm["maxg_med"] <= 15.0,
    }


def _f(v, s=".1f"):
    return format(v, s) if v is not None else "—"


def _trow(t):
    ci = t.get("win_ci")
    return (f"| {t['keys']} | {t['n']} | {_f(t['per_day'])} | {_f(t['win'])} [{_f(ci[0]) if ci else '—'}، {_f(ci[1]) if ci else '—'}] | {_f(t['loss'])} | "
            f"{_f(t['open'])} | {_f(t['cat'])} | {t['cap50']}/{t['cap100']} | {t['lost50']}/{t['lost100']} | {t['unfired50']}/{t['unfired100']} | "
            f"{_f(t['higher'], '+.1f') if t.get('higher') is not None else '—'} |")


HDR = ["| الفلتر | n | يوميًّا | نجاح % [Wilson] | فشل % | لا حسم % | كارثيّ % | راكضو +50/+100 ملتقَطون | مفقودون بالفلتر | لم يُطلَق لهم | الدخولُ أعلى % (وسيط) |",
       "|---|---|---|---|---|---|---|---|---|---|---|"]


def report_lines(meta, n_pop, n_split, n_nobars, tabs, verd, j1tabs, octo, cards, preds, literal, n_gate=None):
    L = ["# 🕵️📈 `T-OPSIG` — النتيجة (مولَّدةٌ بـ`opsig.py --mode run` · لا رقمَ باليد)", "",
         f"**التشغيلة:** {meta.get('run')} · main `{(meta.get('sha') or '')[:9]}`", "",
         f"- الإشعاراتُ المصحَّحة على الكون: {n_pop} · يومُ تقسيمٍ خارجَ النتيجة {n_split} ⟵ **{n_pop - n_split if n_gate is None else n_gate}** (البوّابة {N_GATE} = LVS §④ بعد الاستبعاد) · بلا شموع {n_nobars}", "",
         "## ① الجدول الحاكم — كلُّ «هنا الدخول» (السماتُ قبل الدخول)", ""] + HDR
    L += [_trow(t) for t in tabs]
    L += ["", "**الحكمُ لكلّ سمة (فرقُ النجاح مع − بدون · فاصلُ عناقيد الأيّام 95%):**", ""]
    for k in ATTRS:
        v, pt, ci = verd[k]
        L.append(f"- ({k}) **{v}** · الفرق {_f(100 * pt if pt is not None else None, '+.1f')} نقطة "
                 f"[{_f(100 * ci[0] if ci else None, '+.1f')}، {_f(100 * ci[1] if ci else None, '+.1f')}]")
    L += ["", "## ② 🥇 J1 وحدَها", ""] + HDR + [_trow(t) for t in j1tabs]
    L += ["", "## ③ وصفًا — حرفُ المالك [−5، +5] (موسومٌ «بعد الدخول» · لا يحكم)", ""]
    L += [f"- {k}" for k in literal]
    L += ["", "## ④ سطرُ الكرت المقترح (لا يُنفَّذ قبل قرار المالك)", "",
          "| الفئة | n | وسيطُ/متوسّطُ أعلى ربح % | وسيطُ/متوسّطُ النتيجة بوقف −10% % | ‏+20% | ‏+50% | كارثيّ % | السطر |", "|---|---|---|---|---|---|---|---|"]
    for nm, st in cards.items():
        L.append(f"| {nm} | {st.get('n')} | {_f(st.get('maxg_med'))} / {_f(st.get('maxg_mean'))} | {_f(st.get('s10_med'), '+.1f')} / "
                 f"{_f(st.get('s10_mean'), '+.1f')} | {_f(st.get('p20'))} | {_f(st.get('p50'))} | {_f(st.get('cat'))} | {card_line(st)} |")
    L += ["", f"## ⑤ أكتوبر بالأسماء ({len(octo)})", "", "| اليوم | الرمز | الدقيقة | أ | ب % | ج | د | النتيجة | أعلى ربح % |", "|---|---|---|---|---|---|---|---|---|"]
    for r in octo:
        o = r.get("out") or {}
        L.append(f"| {r['day']} | {r['sym']} | {r.get('hhmm')} | {_f(r.get('a'), '.2f')} | {_f(r.get('b'), '.0f')} | {_f(r.get('c'), '.2f')} | "
                 f"{'✓' if r.get('d') else ('✗' if r.get('d') is False else '—')} | {o.get('res', '—')}{' · كارثيّ' if o.get('cat') else ''} | "
                 f"{_f(o.get('maxg'), '+.0f')} |")
    L += ["", "## ⑥ التنبّؤات (منشورةٌ قبل الرقم)", ""]
    for k, v in preds.items():
        L.append(f"- `{k}` {'✅' if v else '❌'}")
    L += ["", "🔒 لا شيء يُشحَن · الشارةُ وسطرُ الكرت اقتراحان بلا تنفيذ قبل قرار المالك."]
    return L


# ── الجلب (رنر) ─────────────────────────────────────────────────────────────────────────────────────────
def _poly_pages(url, key, cap_pages=8):
    import requests
    out, h = [], {"Authorization": f"Bearer {key}"}
    for _ in range(cap_pages):
        r = requests.get(url, headers=h, timeout=30)
        if getattr(r, "status_code", 0) != 200:
            return None
        j = r.json() or {}
        out.extend(j.get("results") or [])
        url = j.get("next_url")
        if not url:
            return out
    return out


def fetch_tq(sym, t0_ms, t1_ms, key):
    """صفقاتٌ [(ts، سعر، حجم)] وأسعارٌ [(ts، bid، ask)] بالنانوثانية في [t0، t1) (والأسعارُ من دقيقةٍ قبلها) · أو (None، None)."""
    s = str(sym).upper()
    a, b, q0 = t0_ms * 1_000_000, t1_ms * 1_000_000, (t0_ms - MIN_MS) * 1_000_000
    tr = _poly_pages(f"https://api.polygon.io/v3/trades/{s}?timestamp.gte={a}&timestamp.lt={b}&limit=50000&order=asc", key)
    qu = _poly_pages(f"https://api.polygon.io/v3/quotes/{s}?timestamp.gte={q0}&timestamp.lt={b}&limit=50000&order=asc", key)
    if tr is None or qu is None:
        return None, None
    trades = [(int(x.get("sip_timestamp") or x.get("participant_timestamp") or 0), float(x.get("price") or 0), float(x.get("size") or 0))
              for x in tr if x.get("price")]
    quotes = [(int(x.get("sip_timestamp") or x.get("participant_timestamp") or 0), float(x.get("bid_price") or 0), float(x.get("ask_price") or 0))
              for x in qu]
    trades.sort()
    quotes.sort()
    return trades, quotes


def measure(day, sym, ms, bars, tq_fn):
    """صفُّ إشعار ⟵ قاموس."""
    out = {"day": day, "sym": sym, "ms": ms}
    if not bars:
        return out
    t_a = ms + MIN_MS
    E = entry_px(bars, t_a + 2 * MIN_MS)
    if not E or E <= 0:
        return out
    out["E"] = E
    out["out"] = outcome(bars, t_a + 2 * MIN_MS, E)
    out["b"] = attr_b(bars, ms)
    out["c"] = attr_c(bars, ms)
    d, m = attr_d(bars, ms)
    out["d"], out["d_mid"] = d, m
    if d:
        Ed = entry_px(bars, t_a + 3 * MIN_MS)
        if Ed and Ed > 0:
            out["E_d"] = Ed
            out["out_d"] = outcome(bars, t_a + 3 * MIN_MS, Ed)
    trades, quotes = tq_fn(sym, ms - 5 * MIN_MS, ms + 6 * MIN_MS)
    if trades is not None:
        gov = [x for x in trades if x[0] < (ms + 3 * MIN_MS) * 1_000_000]
        out["a"], out["a_n"] = lee_ready(gov, quotes)
        out["a_lit"], _n = lee_ready(trades, quotes)
    return out


def mode_run():
    from concurrent.futures import ThreadPoolExecutor
    from tier_fwd_report import fetch_day
    from tierlink_probe import daily_range
    from shadow_ready import split_ratio
    sys.path.insert(0, os.path.join(ROOT, "fm_forensics", "live_vs_shadow"))
    import live_vs_shadow as LVS
    key = (os.environ.get("POLYGON_API_KEY") or "").strip()
    if not key:
        log("⛔ بلا مفتاح Polygon — لا قياس")
        return 3
    U = json.load(open(LVS.UNIVERSE, encoding="utf-8"))
    RN = json.load(open(LVS.RUNNERS, encoding="utf-8"))
    full = LVS.rebuild_alerts(U, True)
    U = dict(U, alerts=full)
    src = LVS.source_days(U)
    fires = [(d, sym, int(a["ms"])) for d in src for sym, a in sorted((full.get(d) or {}).items()) if sym in LVS.universe_of(U, d)]
    log(f"📥 الإشعاراتُ المصحَّحة على الكون قبل استبعاد يوم التقسيم: {len(fires)} · أيّامُ المصدر {len(src)} (البوّابة {N_GATE} بعد الاستبعاد)")
    j1m, _has = LVS.j1_map(LVS._show(LVS.LEDGER_REF, LVS.TIER_FILE).splitlines())
    runners_by = {(r["day"], r["sym"]): float(r["R"]) for r in RN["rows"] if r["day"] in set(src)}
    fired = {(d, s) for d, s, _m in fires}
    unfired = (sum(1 for k, R in runners_by.items() if k not in fired and R >= 0.5), sum(1 for k, R in runners_by.items() if k not in fired and R >= 1.0))

    def _one(f):
        d, sym, ms = f
        try:
            dl = daily_range(sym, d, key)
            pd_, _p0 = LVS.prev_close(dl, d)
            sr = split_ratio(sym, pd_, d, key) if pd_ else None
            if sr is not None and sr != 1.0:
                return {"day": d, "sym": sym, "ms": ms, "split": True}
            r = measure(d, sym, ms, fetch_day(sym, d, key), lambda s, a, b: fetch_tq(s, a, b, key))
            j = j1m.get((d, sym))
            r["j1"] = bool(j)
            r["gold"] = bool(j) and j.get("tier") == GOLD
            r["hhmm"] = "%02d:%02d" % divmod(LVS.ny_parts(ms)[1], 60)
            return r
        except Exception as e:                                       # noqa: BLE001
            return {"day": d, "sym": sym, "ms": ms, "err": type(e).__name__}
    with ThreadPoolExecutor(8) as pool:
        rows = list(pool.map(_one, fires))
    json.dump(rows, open("opsig_rows.json", "w", encoding="utf-8"), ensure_ascii=False, default=str)
    n_split = sum(1 for r in rows if r.get("split"))
    n_gate, gate_ok = pop_gate(len(fires), n_split)
    log(f"📥 بعد استبعاد يوم التقسيم ({n_split}): {n_gate} · البوّابة {N_GATE} {'✅' if gate_ok else '⛔ سقطت — لا قياس'}")
    ok = [r for r in rows if r.get("out")]
    n_nobars = len(rows) - n_split - len(ok)
    tabs = [table_row(ok, (), runners_by, unfired)] + [table_row(ok, (k,), runners_by, unfired) for k in ATTRS]
    bp = best_pair(ok, runners_by, unfired)
    if bp:
        bp = dict(bp, keys=bp["keys"] + " (أفضلُ زوج · داخل العيّنة)")
        tabs.append(bp)
    verd = {k: verdict_attr(ok, k) for k in ATTRS}
    verd["b_share"] = 100.0 * sum(1 for r in ok if flags(r)["b"]) / len(ok) if ok else None
    verd["d_row"] = tabs[4]
    gold = [r for r in ok if r.get("gold")]
    j1tabs = [table_row(gold, (), runners_by)] + [table_row(gold, (k,), runners_by) for k in ATTRS]
    octo = sorted((r for r in ok if r["day"].startswith("2026-10")), key=lambda r: (r["day"], r["ms"]))
    literal = [f"(أ) بالنافذة [−5، +5]: حاملو 0.60 فأكثر {sum(1 for r in ok if (r.get('a_lit') or 0) >= A_MIN)} من {len(ok)} · "
               f"مجهولٌ {sum(1 for r in ok if r.get('a_lit') is None)}"]
    cards = {"عاديّ (ليس 🥇)": card_stats([r for r in ok if not r.get("gold")]), "🥇 J1": card_stats(gold)}
    for k in ATTRS:
        if verd[k][0] == "تفرّق":
            cards[f"السمة ({k})"] = card_stats([r for r in ok if flags(r)[k]])
    preds = predictions(n_gate, tabs[0], verd, j1tabs[0], cards["عاديّ (ليس 🥇)"])
    meta = {"run": os.environ.get("GITHUB_RUN_ID"),
            "sha": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()}
    if not gate_ok or (rows and n_nobars / len(rows) > MISS_MAX):
        log("⛔ «لا قياس» للكلّ (البوّابة أو الشموع)")
    for ln in report_lines(meta, len(fires), n_split, n_nobars, tabs, verd, j1tabs, octo, cards, preds, literal, n_gate):
        print(ln)
    print("OPSIG_JSON " + json.dumps({"n_pop": len(fires), "n_split": n_split, "n_gate": n_gate, "tabs": tabs, "verd": {k: verd[k] for k in ATTRS}, "j1": j1tabs, "cards": cards,
                                      "preds": preds, "unfired": unfired, "meta": meta}, ensure_ascii=False, default=str))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("check", "run"), default="check")
    a = ap.parse_args(argv)
    if not contract_ok():
        log("⛔ بصمةُ العقد تغيّرت — خروج 9 (لا قياس).")
        return CONTRACT_RC
    if a.mode == "check":
        log("🔒 بصمةُ العقد ✅")
        return 0
    return mode_run()


if __name__ == "__main__":
    sys.exit(main())
