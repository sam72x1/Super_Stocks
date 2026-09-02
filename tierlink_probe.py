#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🔗🔬 `T-TIERLINK` — «الرابطُ المشترك» للمنفجرين منذ أداة المتابعة والتصنيف.

**العقد:** `tierlink_prereg.md` (مدفوعٌ قبل هذا الملفّ). أمرُ المالك 2026-09-02.

المجتمع **ثلاثُ طبقاتٍ لا انتقاء**: (A) كلُّ مِرساةِ سيولةٍ حيّة من تاريخ git
لـ`op_entry_state.json` · (B) كروتُ `M5` في `tier_fwd_ledger.jsonl` (الميزاتُ
الكاملة) · (C) سجلُّ الانفجارات للتغطية فقط.

🔒 **مقياسٌ واحدٌ لا اثنان:** `tier_fwd_report.fetch_day`/`load_ledger`/`tier_of`
· `sym_day_probe.full_day_max`/`exit_point` · `tier_days_report.true_e5` ·
`kasih_scan.wilson` — **بالاسم**؛ صفرُ منطقِ حسمٍ مكرّر.

🔒 **قراءةٌ فقط:** صفرُ إرسالٍ · صفرُ كتابةِ حالة · والإنتاجُ لا يستورده.

**رموزُ الخروج:** 0 صدر · 2 لا مفتاح · 3 تغطيةُ الجلب دون 80% (لا يُفسَّر رقم)
· 4 صفرُ مِرساة (بصمةُ no-op).
"""
import collections
import datetime as dt
import json
import os
import subprocess
import sys

from tier_fwd_report import fetch_day, load_ledger, tier_of      # بالاسم
from tier_days_report import true_e5                              # بالاسم
from sym_day_probe import full_day_max, exit_point                # بالاسم
from kasih_scan import NY, wilson                                 # بالاسم
import requests

SINCE = os.environ.get("TIERLINK_SINCE", "2026-08-18")
H2_FROM = "2026-08-26"                     # نصفا الفترة (العقد §④-4)
EXPL = 50.0                                # «انفجرت» = ‏+50% (العقد §③)
MIN_N = 20                                 # §④-3
MIN_HALF = 10                              # §④-4
MIN_COVER = 0.80                           # بوّابةُ الجلب


# ───────────────────────── الطبقة A: المراسي من تاريخ git ─────────────────────
def anchor_history(since=SINCE):
    """آخرُ لقطةٍ لكلّ يومٍ من تاريخ `op_entry_state.json` ⇒ كلُّ `LIQ:*` بمِرساة."""
    log = subprocess.run(["git", "log", "--format=%h %ad", "--date=iso-strict",
                          "--", "op_entry_state.json"],
                         capture_output=True, text=True).stdout.splitlines()
    last = {}
    for line in log:
        if not line.strip():
            continue
        h, ts = line.split(" ", 1)
        last.setdefault(ts[:10], h)          # الأحدثُ أوّلًا ⇒ أوّلُ ظهورٍ = آخرُ اليوم
    rows = {}
    for day, h in sorted(last.items()):
        try:
            s = json.loads(subprocess.run(["git", "show", f"{h}:op_entry_state.json"],
                                          capture_output=True, text=True).stdout)
        except (ValueError, OSError):
            continue
        for k, v in s.items():
            if not k.startswith("LIQ:") or not isinstance(v, dict) or not v.get("anchor_ms"):
                continue
            d = v.get("date") or day
            if d < since:
                continue
            key = (d, k[4:])
            if key not in rows or len(json.dumps(v)) > len(json.dumps(rows[key])):
                rows[key] = dict(v, symbol=k[4:], date=d)
    return rows


# ───────────────────────── الميزات (العقد §⑤ — مُغلَقة) ───────────────────────
def _bucket(x, edges, labels):
    if x is None:
        return "؟"
    for e, lab in zip(edges, labels):
        if x < e:
            return lab
    return labels[-1]


def features(a, b):
    """`a` صفُّ المِرساة (A) · `b` صفُّ السجلّ (B) أو None. كلُّها معلومةٌ لحظةَ الكرت."""
    src = b or {}
    k2 = (a.get("k2") or {}) if not b else {k: src.get(k) for k in ("c3", "c4", "v2", "v3", "j1")}
    green = src.get("green")
    if green is None and k2:
        # 🔒 السلالُ العليا **بنصّ `liq_tier` حرفيًّا** (مساواةٌ تامّة لا مطابقةٌ جزئيّة)
        top = {"c3": "صادقت (إغلاقٌ فوق المرساة)", "c4": "خضراء 3-4",
               "v2": "المرساة دون 30% (سيولة تتوالى)",
               "v3": "سيولةٌ داخلة (نبضٌ صافٍ موجب)"}
        got = [c for c in top if k2.get(c)]
        green = sum(1 for c in got if k2.get(c) == top[c]) if got else None
    tier = tier_of({"green": green, "j1": k2.get("j1")}) if green is not None else "؟"
    ap, pc = a.get("anchor_price") or src.get("anchor_price"), src.get("prev_close")
    gap = (ap / pc - 1) * 100 if ap and pc else None
    wick = ((ap - a["anchor_low"]) / ap * 100) if ap and a.get("anchor_low") else None
    t = dt.datetime.fromtimestamp(a["anchor_ms"] / 1000, tz=NY)
    hh = t.hour + t.minute / 60
    return {
        "tier": tier,
        "green": str(green) if green is not None else "؟",
        "c3": (k2.get("c3") or "؟").split(" ")[0],
        "c4": k2.get("c4") or "؟",
        "v2": (k2.get("v2") or "؟")[:14],
        "v3": (k2.get("v3") or "؟").split(" (")[0],
        "j1": "J1" if k2.get("j1") else ("لا" if k2 else "؟"),
        "cls": (src.get("cls") or ["؟"])[0],
        "vol_x": _bucket(src.get("vol_x") if b else None, (10, 30), ("<10", "10-30", "≥30")),
        "usd": _bucket(src.get("usd"), (100_000, 300_000), ("<100k", "100-300k", "≥300k")),
        "gap": _bucket(gap, (10, 30), ("<10%", "10-30%", "≥30%")),
        "prev_px": _bucket(pc, (1, 3, 10), ("<1$", "1-3$", "3-10$", ">10$")),
        "tod": "pre" if hh < 9.5 else ("reg" if hh < 16 else "after"),
        "wick": _bucket(wick, (5, 15), ("<5%", "5-15%", "≥15%")),
        "V1": "نعم" if (green is not None and (green >= 3 or k2.get("j1"))) else ("لا" if green is not None else "؟"),
        "g3": "نعم" if (green is not None and green >= 3) else ("لا" if green is not None else "؟"),
    }


# ───────────────────────── النتيجة ─────────────────────────────────────────────
def daily_range(sym, day, key, get=None):
    """شموعٌ يوميّة `adjusted=false` من `day-10` إلى `day+10`: إغلاقُ الأمس + الخمس التالية."""
    g = requests.get if get is None else get
    d0 = (dt.date.fromisoformat(day) - dt.timedelta(days=10)).isoformat()
    d1 = (dt.date.fromisoformat(day) + dt.timedelta(days=10)).isoformat()
    try:
        r = g(f"https://api.polygon.io/v2/aggs/ticker/{sym}/range/1/day/{d0}/{d1}"
              "?adjusted=false&sort=asc&limit=50", headers={"Authorization": f"Bearer {key}"},
              timeout=30)
        if getattr(r, "status_code", 0) != 200:
            return None
        return [(dt.datetime.fromtimestamp(b["t"] / 1000, tz=NY).date().isoformat(),
                 float(b["h"]), float(b["c"])) for b in (r.json() or {}).get("results") or []]
    except Exception:                                                # noqa: BLE001
        return None


def measure(a, b, bars, dailies):
    """تُرجع قاموسَ النتيجة أو None عند تعذّر الأساس (يُعَدّ ولا يُنسَب)."""
    a_ms = int(a["anchor_ms"])
    ap = a.get("anchor_price") or (b or {}).get("anchor_price")
    if not ap:
        ab = next((x for x in bars if x[0] == a_ms), None)
        ap = ab[4] if ab else None
    e5 = (b or {}).get("e5")
    broke5 = False
    if not e5:
        e5, broke5 = true_e5(bars, a_ms, ap) if ap else (None, False)
    if not e5:
        return None
    card_ms = a_ms + 4 * 60_000
    mg_day, _ = full_day_max(bars, card_ms, e5)
    alow = a.get("anchor_low") or (b or {}).get("anchor_low")
    ex_px, ex_ms = exit_point(bars, card_ms, alow) if alow else (None, None)
    mg_cut = None
    if ex_ms:
        pre = [x for x in bars if card_ms < x[0] < ex_ms]
        mg_cut = max((x[2] / e5 - 1) * 100 for x in pre) if pre else 0.0
    else:
        mg_cut = mg_day
    reg = [x for x in bars if dt.datetime.fromtimestamp(x[0] / 1000, tz=NY).hour < 16]
    close = (reg or bars)[-1][4]
    nxt = [h for (d, h, _c) in (dailies or []) if d > a["date"]][:5]
    mg5d = (max(nxt) / e5 - 1) * 100 if nxt else None
    return {"e5": e5, "broke5": broke5, "mg_day": mg_day, "mg_cut": mg_cut,
            "close_ret": (close / e5 - 1) * 100, "mg_5d": mg5d,
            "exploded50": bool(mg_day is not None and mg_day >= EXPL),
            "exploded100": bool(mg_day is not None and mg_day >= 100),
            "kasih30_cut": bool(mg_cut is not None and mg_cut >= 30)}


# ───────────────────────── الحكم (العقد §④) ────────────────────────────────────
FEATS = ["tier", "green", "c3", "c4", "v2", "v3", "j1", "cls", "vol_x", "usd",
         "gap", "prev_px", "tod", "wick", "press", "V1", "g3"]


def judge(rows, feat, label="exploded50"):
    """لكلّ سلّةٍ: n · k · نسبة · Wilson — ثم الشروطُ الأربعة على السلّة الأعلى."""
    by = collections.defaultdict(list)
    for r in rows:
        v = r["f"][feat]
        if v != "؟":
            by[v].append(r)
    table = {}
    for v, rs in by.items():
        k = sum(1 for r in rs if r["o"][label])
        table[v] = (len(rs), k, wilson(k, len(rs)))
    elig = [(v, t) for v, t in table.items() if t[0] >= MIN_N]
    verdict = {"ok": False, "why": "لا حكم (كلُّ السلال دون 20)", "best": None}
    if not elig:
        return table, verdict
    best_v, (bn, bk, (blo, bhi)) = max(elig, key=lambda x: x[1][1] / x[1][0])
    rest = [r for r in rows if r["f"][feat] not in ("؟", best_v)]
    rn, rk = len(rest), sum(1 for r in rest if r["o"][label])
    if rn < MIN_N:
        verdict["why"] = f"لا حكم (المُكمِّل {rn} دون 20)"
        return table, verdict
    rlo, rhi = wilson(rk, rn)
    c1 = (bk / bn) >= 2 * (rk / rn) if rk else bk > 0
    c2 = blo > rhi
    h = {}
    for half, sel in (("H1", lambda r: r["date"] < H2_FROM), ("H2", lambda r: r["date"] >= H2_FROM)):
        hb = [r for r in rows if sel(r) and r["f"][feat] == best_v]
        hr = [r for r in rows if sel(r) and r["f"][feat] not in ("؟", best_v)]
        pb = sum(r["o"][label] for r in hb) / len(hb) if hb else None
        pr = sum(r["o"][label] for r in hr) / len(hr) if hr else None
        h[half] = (len(hb), pb, len(hr), pr)
    c4 = all(v[0] >= MIN_HALF and v[1] is not None and v[3] is not None and v[1] > v[3]
             for v in h.values())
    verdict = {"best": best_v, "best_rate": bk / bn * 100, "rest_rate": rk / rn * 100,
               "ci_best": (blo, bhi), "ci_rest": (rlo, rhi), "n": (bn, rn),
               "c1": c1, "c2": c2, "c3": True, "c4": c4, "halves": h,
               "ok": c1 and c2 and c4,
               "why": "رابط" if (c1 and c2 and c4) else
                      ("فصلٌ غيرُ متكرّر" if (c1 and c2) else "لا فصل")}
    return table, verdict


def main() -> int:
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key:
        print("⛔ لا POLYGON_API_KEY — خروج 2")
        return 2
    anchors = anchor_history()
    if not anchors:
        print("⛔ صفرُ مِرساةٍ في تاريخ git (بصمةُ no-op) — خروج 4")
        return 4
    ledger = {(r["date"], r["symbol"]): r for r in load_ledger()}
    press = collections.defaultdict(set)
    try:
        for line in open("press_radar_ledger.jsonl", encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                press[r["session"]].add(r["symbol"])
    except OSError:
        pass
    sess = sorted(press)
    print(f"🔗 T-TIERLINK · مراسٍ {len(anchors)} · سجلّ M5 {len(ledger)} · منذ {SINCE}")
    rows, fails, nobase = [], 0, 0
    cache = {}
    for (day, sym), a in sorted(anchors.items()):
        bars = cache.get((sym, day))
        if bars is None:
            bars = fetch_day(sym, day, key)
            cache[(sym, day)] = bars or []
        if not bars:
            fails += 1
            continue
        dailies = daily_range(sym, day, key)
        b = ledger.get((day, sym))
        if b is None:
            # إغلاقُ الأمس من الشموع اليوميّة لمن ليس في السجلّ
            pcs = [c for (d, _h, c) in (dailies or []) if d < day]
            b_like = {"prev_close": pcs[-1] if pcs else None}
        else:
            b_like = b
        o = measure(a, b if b else None, bars, dailies)
        if o is None:
            nobase += 1
            continue
        f = features(a, b if b else None)
        if b is None and b_like.get("prev_close") and a.get("anchor_price"):
            f["gap"] = _bucket((a["anchor_price"] / b_like["prev_close"] - 1) * 100, (10, 30),
                               ("<10%", "10-30%", "≥30%"))
            f["prev_px"] = _bucket(b_like["prev_close"], (1, 3, 10), ("<1$", "1-3$", "3-10$", ">10$"))
        prev = [s for s in sess if s < day]
        f["press"] = "مضغوطٌ سابقًا" if (prev and sym in press[prev[-1]]) else "لا"
        rows.append({"date": day, "symbol": sym, "in_ledger": b is not None, "f": f, "o": o})
    total = len(anchors)
    cover = len(rows) / total
    print(f"🩺 التغطية: قِيس {len(rows)} · تعذّر الجلب {fails} · بلا أساس {nobase} من {total} "
          f"= {cover*100:.1f}%")
    if cover < MIN_COVER:
        print("⛔ التغطية دون 80% ⇒ لا يُفسَّر رقم — خروج 3")
        return 3
    # ── الأساس
    n = len(rows)
    for lab in ("exploded50", "exploded100", "kasih30_cut"):
        k = sum(r["o"][lab] for r in rows)
        lo, hi = wilson(k, n)
        print(f"📊 الأساس {lab}: {k}/{n} = {k/n*100:.1f}% [{lo:.0f}·{hi:.0f}]")
    import statistics as st
    print(f"📊 وسيط mg_day {st.median([r['o']['mg_day'] for r in rows]):.1f}% · "
          f"وسيط close_ret {st.median([r['o']['close_ret'] for r in rows]):.1f}% · "
          f"وسيط mg_5d {st.median([r['o']['mg_5d'] for r in rows if r['o']['mg_5d'] is not None]):.1f}%")
    # ── جدول الميزات
    print("\n" + "=" * 78 + "\n🔗 الميزاتُ على exploded50 (العقد §④)\n" + "=" * 78)
    links = []
    for feat in FEATS:
        table, v = judge(rows, feat)
        print(f"\n▶ {feat}")
        for val, (tn, tk, (lo, hi)) in sorted(table.items(), key=lambda x: -x[1][1] / x[1][0]):
            mc = st.median([r["o"]["close_ret"] for r in rows if r["f"][feat] == val])
            e100 = sum(r["o"]["exploded100"] for r in rows if r["f"][feat] == val)
            print(f"   {val:<16} n={tn:<4} +50%: {tk:<3} {tk/tn*100:5.1f}% [{lo:.0f}·{hi:.0f}] · "
                  f"+100%: {e100:<3} · وسيط الإغلاق {mc:+.1f}%")
        if v.get("best") is not None:
            h = v["halves"]
            print(f"   ⇒ الأعلى «{v['best']}» {v['best_rate']:.1f}% مقابل {v['rest_rate']:.1f}% · "
                  f"①{'✅' if v['c1'] else '🔴'} ②{'✅' if v['c2'] else '🔴'} ③✅ "
                  f"④{'✅' if v['c4'] else '🔴'} "
                  f"(H1 n={h['H1'][0]} {(h['H1'][1] or 0)*100:.0f}% مقابل {(h['H1'][3] or 0)*100:.0f}% · "
                  f"H2 n={h['H2'][0]} {(h['H2'][1] or 0)*100:.0f}% مقابل {(h['H2'][3] or 0)*100:.0f}%) "
                  f"⇒ **{v['why']}**")
        else:
            print(f"   ⇒ {v['why']}")
        if v.get("ok"):
            links.append((feat, v["best"]))
    print("\n" + "=" * 78)
    print("🏁 الحكم: " + (("رابطٌ مستوفٍ للمعيار: " + " · ".join(f"{f}={b}" for f, b in links))
                          if links else "**لا ميزةَ تستوفي المعيارَ الرباعيّ** — «لا رابط بهذا المعيار»"))
    # ── التغطية (C)
    try:
        wl = json.load(open("weekly_watchlist.json", encoding="utf-8"))
        ex = [e for e in wl.get("explosions", []) if str(e.get("expl_date", "")) >= SINCE]
        clean = [e for e in ex if not e.get("suspect_split")]
        hit = [e for e in clean if (e["expl_date"], e["symbol"]) in anchors]
        print(f"\n🔭 التغطية: انفجاراتُ السجلّ منذ {SINCE}: {len(ex)} · نظيفة {len(clean)} · "
              f"لها مِرساةٌ في يومها {len(hit)} ({len(hit)/max(1,len(clean))*100:.0f}%)")
        miss = [e for e in clean if (e["expl_date"], e["symbol"]) not in anchors]
        print("   بلا مِرساة: " + " · ".join(f"{e['symbol']}({e['expl_date'][5:]} +{e['gain']:.0f}%)" for e in miss))
    except (OSError, ValueError):
        print("🔭 التغطية: تعذّر قراءة سجلّ الانفجارات")
    # ── الصفوف كاملةً (لا قصّ)
    print("\n📋 الصفوف (تاريخ · رمز · فئة · خضراء · J1 · cls · وقت · فجوة · mg_day · mg_cut · إغلاق · 5ج):")
    for r in sorted(rows, key=lambda r: -(r["o"]["mg_day"] or 0)):
        f, o = r["f"], r["o"]
        print(f"   {r['date'][5:]} {r['symbol']:<6} {f['tier']:<6} g={f['green']} {f['j1']:<3} "
              f"{f['cls']:<8} {f['tod']:<5} {f['gap']:<7} {o['mg_day']:+7.1f} "
              f"{(o['mg_cut'] if o['mg_cut'] is not None else 0):+7.1f} {o['close_ret']:+7.1f} "
              f"{(o['mg_5d'] if o['mg_5d'] is not None else 0):+7.1f}")
    print("\n⚠️ حدودُ صدق: لمسٌ لا تنفيذ · فترةٌ قصيرة · لا ربحيّة · ميزاتُ A من آخر لقطةٍ لليوم.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
