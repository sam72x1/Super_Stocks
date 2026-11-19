#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🔬🔢 عدٌّ وصفيّ لمستوى «مخفّف» في صيّاد «النهج العلمي» (أمرُ المالك 2026-11-19 · البند ② «قبل البناء اطبع عدًّا فقط»).

لكلّ جلسةٍ من آخر `SESSIONS`: مَن استوفى الشروطَ الستّة **عدا** أن سعره تجاوز مستوى الدخول بهامشٍ صغير (0.5 · 1 · 2 · 3%).
يعيد استعمالَ دوالّ الصيّاد **بالاسم** (`method_founding` · `method_sequence` · `falling_gap_candle` · `group_pump_scar` · `_offering_event`)
على الشموع مقصوصةً عند كلّ جلسة (بلا نظرٍ للمستقبل) · **عدٌّ وأسماء فقط — لا عائدَ ولا نتيجةَ بعد الجلسة** · لا تلغرام · لا حالة ·
لا يمسّ الصيّاد ولا عتبة.
⚠️ حدودُ صدقٍ تُطبَع: المتاحُ للاقتراض لا تاريخَ له ⟵ يُقرأ من ملفّات البوت خلال 7 أيّام قبل الجلسة وإلّا «مجهول يمرّ» (كما في الأداة) ·
وشموعُ 4س المتاحة ‏≈60 يومًا · والطرحُ بفحص SEC بتاريخ الجلسة.
"""
import sys

MARGINS = (0.5, 1.0, 2.0, 3.0)
SESSIONS = 20
H4_CAP = 900                    # سقفُ جلبات 4س في التشغيلة كلِّها (رمزٌ يُجلَب مرّةً) — والمقصوصُ يُعلَن


def bucket(over_pct, margins=MARGINS):
    """🔒 **نقيّة**: الهوامشُ التي يدخلها تجاوزٌ `over_pct` (موجبٌ حصرًا — صفرٌ أو أقلّ = داخل منطقة الدخول أصلًا فليس «مخفّفًا»)."""
    try:
        v = float(over_pct)
    except (TypeError, ValueError):
        return []
    if not (v == v) or v <= 0:
        return []
    return [m for m in margins if v <= m]


def cut(df, day):
    """الإطارُ حتى إغلاق `day` شاملًا (بلا نظرٍ للمستقبل)."""
    keep = [getattr(ts, "date", lambda: ts)() <= day for ts in df.index]
    return df[keep]


def classify(S, sym, df, day, h4_of=None, borrow_known=None, offering=None, pump=None):
    """⟵ None (ليس مرشَّحًا للمخفّف) أو {"over": %, "frame", "fail": None|سبب} — ترتيبُ الشروط ترتيبُ `scan_method_hunter`."""
    if df is None or len(df) < 60:
        return None
    price = float(df["Close"].values[-1])
    if price < S.CONFIG["METHOD_MIN_PRICE"]:
        return None
    fnd = S.method_founding(df)
    if not fnd:
        return None
    ts, frame = S.method_sequence(df, win=int(fnd["bars_since_peak"]) + 2), "يوميّ"
    if not (ts and ts.get("ok")) and h4_of is not None:
        d4 = h4_of(sym)
        if d4 is not None and len(d4) >= 8:
            d4 = cut(d4, day)
            if len(d4) >= 8:
                w4 = max(8, int(fnd["bars_since_peak"]) * int(S.CONFIG["METHOD_4H_BARS_PER_SESSION"]) + 2)
                t4 = S.method_sequence(d4, win=w4)
                if t4 and t4.get("ok"):
                    ts, frame = t4, "4 ساعات"
    if not (ts and ts.get("ok")):
        return None
    bot = float(ts.get("bottom") or 0)
    if bot <= 0:
        return None
    entry = bot * (1.0 + S.CONFIG["METHOD_ENTRY_PCT"] / 100.0)
    over = (price / entry - 1.0) * 100.0
    if not bucket(over):
        return None                                   # داخل المنطقة (شأنُ المطابق الكامل) أو أبعدُ من أوسع هامش
    out = {"over": over, "frame": frame, "price": price, "entry": entry, "fail": None}
    gap = S.falling_gap_candle(df, price=entry)
    t1 = float((gap or {}).get("head") or 0)
    if not t1 or t1 <= entry:
        out["fail"] = "لا فجوة هابطة"
        return out
    if (pump or S.group_pump_scar)(df):
        out["fail"] = "قروب"
        return out
    try:
        if (offering or S._offering_event)(sym, today=day):
            out["fail"] = "طرح"
            return out
    except Exception:                                            # noqa: BLE001
        pass
    av = ((borrow_known or {}).get(sym) or {}).get("shares_available")
    out["avail"] = av
    if av is not None and float(av) > float(S.CONFIG["METHOD_SHORT_MAX"]):
        out["fail"] = "متاح فوق الحدّ"
    return out


def main():
    import Super_stock as S
    uni = S.get_universe()
    hist = S.download_history(uni)
    S.log(f"🔢 عدُّ المخفّف: شموعٌ صالحة {len(hist)} من {len(uni)}")
    ref = max(hist.values(), key=len)
    days = [ts.date() for ts in ref.index][-SESSIONS:]
    h4_cache, h4_left = {}, [H4_CAP]

    def h4_of(sym):
        if sym not in h4_cache:
            if h4_left[0] <= 0:
                return None
            h4_left[0] -= 1
            try:
                h4_cache[sym] = S.fetch_4h(sym)
            except Exception:                                    # noqa: BLE001
                h4_cache[sym] = None
        return h4_cache[sym]

    rows = []
    for day in days:
        known = S._known_borrow(day.isoformat(), days=7)
        n = 0
        for sym, df in hist.items():
            try:
                r = classify(S, sym, cut(df, day), day, h4_of=h4_of, borrow_known=known)
            except Exception as e:                               # noqa: BLE001
                S.log(f"⚠️ {sym} {day}: {type(e).__name__}")
                continue
            if r:
                r.update(sym=sym, day=day.isoformat())
                rows.append(r)
                n += 1
        S.log(f"   {day}: تجاوزوا الدخول بـ3% أو أقلّ بعد التسلسل {n}")
    S.log(f"🔢 الجلسات {days[0]} … {days[-1]} ({len(days)}) · جلباتُ 4س {H4_CAP - h4_left[0]}"
          + (" · ⚠️ بلغ السقف" if h4_left[0] <= 0 else ""))
    fails = {}
    for r in rows:
        if r["fail"]:
            fails[r["fail"]] = fails.get(r["fail"], 0) + 1
    S.log(f"🔢 ضمن 3% بعد التسلسل: {len(rows)} سهم-جلسة · سقط منهم على شرطٍ آخر: "
          + (" · ".join(f"{k} {v}" for k, v in sorted(fails.items(), key=lambda x: -x[1])) or "لا أحد"))
    ok = [r for r in rows if not r["fail"]]
    for m in MARGINS:
        sel = [r for r in ok if m in bucket(r["over"])]
        names = sorted({r["sym"] for r in sel})
        S.log(f"🔢 هامش {m:g}%: {len(sel)} سهم-جلسة · {len(names)} سهمًا · في {len({r['day'] for r in sel})} جلسة من {len(days)}")
        S.log("   الأسماء: " + (" · ".join(names) or "—"))
    S.log("🔢 التفصيل (كلُّ مَن يدخل أوسعَ هامش):")
    for r in sorted(ok, key=lambda x: (x["day"], x["over"])):
        S.log(f"   {r['day']} {r['sym']} ${r['price']:.2f} تجاوز {r['over']:.2f}% (الدخول ${r['entry']:.2f} · {r['frame']} · "
              f"المتاح {'مجهول' if r.get('avail') is None else int(r['avail'])})")
    S.log("⚠️ حدودُ الصدق: المتاحُ من ملفّات البوت خلال 7 أيّام قبل الجلسة وإلّا مجهولٌ يمرّ · 4س ‏≈60 يومًا · عدٌّ بلا أيّ نتيجةٍ بعد الجلسة.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
