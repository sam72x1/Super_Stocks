#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🌊 `T-KASIH` — أيُّ مِرساةِ سيولةٍ يتبعها «التحرّكُ الكاسح»؟ (أداةُ قياسٍ تاريخيّ).

العقد: `kasih_prereg.md` — **مدفوعٌ قبل أيّ رقم**، ولا معيارَ يُحرَّك بعده.
أمرُ المالك (2026-08-19): «عصف ذهني وتجارب الين توصل لافضل طريقة من ناحية
الدخول … نحتاج نوصل للتحرك الكاسح».

⚖️ **مقياسٌ واحدٌ لا اثنان:**
- كشفُ المِرساة بدالّة الإنتاج `Super_stock.liq_stage_events` **نفسها**، بإعادة
  تشغيلٍ تدريجيةٍ هي النمطُ القانونيّ في `alert_filter_check.replay_symbol`
  (شريحة `bars[max(0, k-LIQ_WINDOW_MIN):k]`).
- تصنيفُ السيولة الدولاريّ بـ`_ignition_candle_class` الإنتاجية (أرقامُ فيصل).
- المصدر: ملفات Polygon المجمّعة `minute_aggs` (تشمل المشطوبين = PIT بالبناء) —
  عبر عُدّة `flatfiles_probe`/`ah_scan` القائمة (إعادةُ استعمالٍ لا بناء).

🔒 **قراءة/قياسٌ فقط**: لا كتابةَ حالةٍ ولا تلغرام ولا مساسَ بأيّ عتبة. أرقامُ
المالك (‏5% · $30,000 · 3×) تُقرأ من الإنتاج ولا تُمَسّ.

🧮 **المرشِّح المسبق سوبرست مُبرهَن** (‏§③ من العقد): كلُّ دقيقةٍ يقبلها الإنتاج
تستوفي — بالبناء — رفعةً ‏≥`LIQ_MIN_MOVE_PCT` **و**مجموعَ آخرِ `LIQ_CUM_MINUTES`
شموعٍ **باليوم كاملًا** ‏≥`LIQ_MIN_USD` (مجموعُ النافذة ‏≤ مجموعِ اليوم لنفس
الفهارس) ⇒ إسقاطُ يومٍ لا يحوي دقيقةً كهذي **لا يُفقد مِرساةً** — ويُثبَت
بعيّنة `V2` (تشغيلُ الدالّة على مستبعَدين ⇒ صفرُ مِرساة وإلا خروج 3).

المخرَج: صفوف JSONL (سطر/مِرساة) + جداولُ سلالٍ بفواصل Wilson لكل خاصيةٍ من
`F1`-`F6` + مقياسُ الدائرية المرافق («الكاسحُ من إغلاق الدقيقة 5»).
"""
import csv
import gzip
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SCREENER_MODE", "BACKTEST")

import datetime as dt                                            # noqa: E402
from zoneinfo import ZoneInfo                                    # noqa: E402

import ah_scan as AH                                             # noqa: E402
import flatfiles_probe as FP                                     # noqa: E402
import Super_stock as S                                          # noqa: E402

NY = ZoneInfo("America/New_York")


def weekdays(a: str, b: str) -> list:
    """أيامُ الأسبوع في [a, b] — **بلا تقويم عطلات عمدًا**: `trading_days`
    القائمة ترفض ما قبل 2026 (عقد `VY-CAL` لأداة الافتر ولا يلزمنا هنا)؛
    والعطلةُ ملفُّها غائبٌ في S3 فتسقط ذاتيًّا **وتُعَدّ ضمن «مفقودة»**
    (‏≈9-10/سنة متوقَّعة). وأيامُ الإغلاق المبكّر (~3/سنة) تُحسب عاديةً —
    حدُّ صدقٍ مُعلَنٌ في §⑧ يمسّ خاصية F5 وحدها بتشويهٍ طفيف."""
    d0, d1 = dt.date.fromisoformat(a), dt.date.fromisoformat(b)
    out, d = [], d0
    while d <= d1:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out

# ── ثوابتُ العقد (مصادرُها في `kasih_prereg.md` §②/§④) ─────────────────────
PRICE_LO = float(S.CONFIG.get("MIN_PRICE", 0.40))       # ظرفُ الكاتالوج النافذ
PRICE_HI = float(S.CONFIG.get("SPLIT_RADAR_PRICE_MAX", 10.0))   # engineering مُعاد
KASIH_PCT = 30.0          # faisal_verbatim — «صعود أقلها 30-50%» (الحاكمة)
KASIH_DESC = (50.0, 100.0)  # وصفيّتان تُنشران ولا تحكمان
SUSTAIN_MIN = 15          # قاعدةُ فيصل «ربع الساعة»
ENTRY5_MIN = 5            # مقياسُ M5 القائم (الدائريةُ المرافقة §⑦-K5)
GAP_CAP = 500.0           # استبعادُ تشويه التقسيم (سابقة T-GATE §⑨-4)
V2_EVERY = 25             # كلَّ N يومًا تُفحص عيّنةُ مستبعَدين
V2_SAMPLE = 40


def log(msg: str):
    print(f"[{dt.datetime.utcnow().strftime('%H:%M:%S')}] {msg}", flush=True)


def wilson(k: int, n: int, z: float = 1.96):
    if n <= 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, (c - h) / d) * 100, min(1.0, (c + h) / d) * 100)


# ── قراءةُ ملفّ اليوم: شموعُ كوننا + إغلاقاتُ الجميع (لخريطة الغد) ───────────
def parse_day(fh, universe: set):
    rd = csv.reader(fh)
    header = next(rd)
    i_t = AH._pick(header, "ticker", "symbol")
    i_o = AH._pick(header, "open")
    i_h = AH._pick(header, "high")
    i_l = AH._pick(header, "low")
    i_c = AH._pick(header, "close")
    i_v = AH._pick(header, "volume")
    i_w = AH._pick(header, "window_start", "t", "timestamp")
    if min(i_t, i_o, i_h, i_l, i_c, i_v, i_w) < 0:
        raise KeyError(f"ترويسةٌ ناقصة: {header}")
    bars: dict = {}
    closes: dict = {}
    for row in rd:
        try:
            sym = row[i_t].strip().upper()
            ns = int(row[i_w])
            o, h = float(row[i_o]), float(row[i_h])
            lo, c = float(row[i_l]), float(row[i_c])
            v = float(row[i_v])
        except (IndexError, ValueError, TypeError):
            continue
        if not sym:
            continue
        day, mod = AH.ny_minute(ns)
        if day is None:
            continue
        # إغلاقُ الجلسة النظامية (‏≤16:00) — لخريطة «إغلاق الأمس» للجميع
        if mod <= 16 * 60:
            pc = closes.get(sym)
            if pc is None or mod > pc[0]:
                closes[sym] = (mod, c)
        if sym not in universe:
            continue
        if mod < 4 * 60 or mod >= 20 * 60:   # 04:00-20:00 نيويورك (عقد §②)
            continue
        bars.setdefault(sym, []).append(
            (int(ns / 1e6), o, h, lo, c, v))
    for b in bars.values():
        b.sort(key=lambda x: x[0])
    return bars, {k: v[1] for k, v in closes.items()}


# ── المرشِّح المسبق (سوبرست مُبرهَن — انظر docstring) ────────────────────────
def prescreen(rows) -> bool:
    mv, floor_ = float(S.LIQ_MIN_MOVE_PCT), float(S.LIQ_MIN_USD)
    n = max(1, int(S.LIQ_CUM_MINUTES))
    for i, b in enumerate(rows):
        o, c, v = b[1], b[4], b[5]
        if o <= 0 or (c - o) / o * 100.0 < mv:
            continue
        if sum(x[4] * x[5] for x in rows[max(0, i - n + 1):i + 1]) < floor_:
            continue
        return True
    return False


def _dicts(rows):
    return [{"t": t, "o": o, "h": h, "l": lo, "c": c, "v": v}
            for (t, o, h, lo, c, v) in rows]


# ── كشفُ المِرساة بدالّة الإنتاج (النمطُ القانونيّ حرفيًّا) ──────────────────
def first_anchor(rows):
    st: dict = {}
    win = int(S.LIQ_WINDOW_MIN)
    bd = _dicts(rows)
    for k in range(3, len(bd) + 1):
        evs, st = S.liq_stage_events(bd[max(0, k - win):k], st)
        for e in (evs or []):
            if e.get("stage") == "M1":
                return e
    return None


# ── الحسم (تعريفاتُ §④ حرفيًّا) ─────────────────────────────────────────────
def resolve(rows, anchor_ms: int, entry: float):
    ab = next((b for b in rows if b[0] == anchor_ms), None)
    if ab is None or entry <= 0:
        return None
    anchor_low = ab[3]
    mx = entry
    e5 = entry            # إغلاقُ الدقيقة 5 = آخرُ إغلاقٍ قبل anchor+5د (مقياس M5)
    e5_frozen = False
    mx5 = None
    sustain = True
    exit_reason = "eod"
    for b in rows:
        t, _o, h, _l, c, _v = b
        if t <= anchor_ms:
            continue
        if not e5_frozen and t < anchor_ms + ENTRY5_MIN * 60_000:
            e5 = c
        elif not e5_frozen:
            e5_frozen = True
            mx5 = e5
        mx = max(mx, h)
        if mx5 is not None:
            mx5 = max(mx5, h)
        if t <= anchor_ms + SUSTAIN_MIN * 60_000 and c < entry:
            sustain = False
        if c < anchor_low:      # الخروجُ البنيويّ: إغلاقٌ دون قاع شمعة المِرساة
            exit_reason = "break"
            break
    mg = (mx / entry - 1.0) * 100.0
    out = {"anchor_low": round(anchor_low, 4), "exit": exit_reason,
           "mg_after": round(mg, 1), "sustain15": sustain,
           "kasih30": mg >= KASIH_PCT,
           "kasih50": mg >= KASIH_DESC[0], "kasih100": mg >= KASIH_DESC[1]}
    if mx5 is not None and e5 and e5 > 0:
        out["kasih30_from5"] = (mx5 / e5 - 1.0) * 100.0 >= KASIH_PCT
    return out


def f2_usd5(rows, anchor_ms: int) -> float:
    return sum(b[4] * b[5] for b in rows
               if anchor_ms <= b[0] < anchor_ms + ENTRY5_MIN * 60_000)


def f3_bucket(anchor_ms: int) -> str:
    m = dt.datetime.fromtimestamp(anchor_ms / 1000, tz=NY)
    mod = m.hour * 60 + m.minute
    if mod < 6 * 60:
        return "بريماركت مبكر 04-06"
    if mod < 9 * 60 + 30:
        return "بريماركت متأخر"
    if mod < 12 * 60:
        return "جلسة صباحية"
    return "بعد الظهر"


def f4_bucket(vx) -> str:
    try:
        v = float(vx)
    except (TypeError, ValueError):
        return "؟"
    if v < 10:
        return "قفزة 3-10×"
    if v < 30:
        return "قفزة 10-30×"
    return "قفزة فوق 30×"


def f5_bucket(gap_pct: float) -> str:
    if gap_pct < 10:
        return "دون 10%"
    if gap_pct < 30:
        return "10-30%"
    if gap_pct < 75:
        return "30-75%"
    return "فوق 75%"


def bucket_table(rows: list, feat: str, title: str):
    agg: dict = {}
    for r in rows:
        b = r.get(feat)
        if b is None:
            continue
        a = agg.setdefault(b, {"n": 0, "k": 0, "k5": 0, "n5": 0, "mg": []})
        a["n"] += 1
        a["k"] += 1 if r["kasih30"] else 0
        a["mg"].append(r["mg_after"])
        if "kasih30_from5" in r:
            a["n5"] += 1
            a["k5"] += 1 if r["kasih30_from5"] else 0
    print(f"\n  ── {title} ──")
    print(f"  {'السلة':24} {'ن':>5} {'كاسح30%':>9} {'ويلسون':>13} "
          f"{'وسيط mg':>9} {'كاسح من د5':>11}")
    order = sorted(agg.items(), key=lambda kv: -(kv[1]["k"] / kv[1]["n"])
                   if kv[1]["n"] else 0)
    for name, a in order:
        p = a["k"] / a["n"] * 100 if a["n"] else 0.0
        lo, hi = wilson(a["k"], a["n"])
        med = sorted(a["mg"])[len(a["mg"]) // 2] if a["mg"] else 0.0
        p5 = (f"{a['k5'] / a['n5'] * 100:.0f}%" if a["n5"] else "—")
        print(f"  {name:24} {a['n']:>5} {p:>8.1f}% [{lo:>4.0f}·{hi:>3.0f}] "
              f"{med:>8.1f}% {p5:>11}")
    # المعيار ①/②/④ لهذي السنة (③ الثبات يُقرأ عبر السنوات في ملف النتيجة)
    ok = [(n, a) for n, a in agg.items() if a["n"] >= 40]
    if len(ok) >= 2:
        ok.sort(key=lambda kv: kv[1]["k"] / kv[1]["n"])
        loN, hiN = ok[0], ok[-1]
        p_lo = loN[1]["k"] / loN[1]["n"] * 100
        p_hi = hiN[1]["k"] / hiN[1]["n"] * 100
        w_lo = wilson(loN[1]["k"], loN[1]["n"])
        w_hi = wilson(hiN[1]["k"], hiN[1]["n"])
        sep = w_hi[0] > w_lo[1]
        print(f"  ⚖️ الفرق (أعلى−أدنى): {p_hi - p_lo:+.1f} نقطة · "
              f"فاصلان {'منفصلان ✅' if sep else 'متداخلان 🔴'} "
              f"(أرضية 40: مستوفاة في {len(ok)} سلال)")
    else:
        print("  ⚖️ الأرضية (40/سلة) غير مستوفاة لسلّتين ⇒ لا حكم لهذي الخاصية")


def main() -> int:
    if not (os.environ.get("AWS_ACCESS_KEY_ID") or "").strip():
        print("⛔ لا مفاتيح S3 — لا قياس (ولا يُخمَّن رقم).")
        return 2
    year = (os.environ.get("KASIH_YEAR") or "").strip()
    one_day = (os.environ.get("KASIH_DAY") or "").strip()
    if one_day:
        days = [one_day]
        seed_from, seed_to = None, None
        seed_days = weekdays(
            (dt.date.fromisoformat(one_day) - dt.timedelta(days=7)).isoformat(),
            (dt.date.fromisoformat(one_day) - dt.timedelta(days=1)).isoformat())[-3:]
    elif year:
        days = weekdays(f"{year}-01-01", f"{year}-12-31")
        seed_days = weekdays(f"{int(year)-1}-12-20",
                             f"{int(year)-1}-12-31")[-3:]
    else:
        print("⛔ لا KASIH_YEAR ولا KASIH_DAY.")
        return 2
    log(f"🌊 T-KASIH — {'يوم ' + one_day if one_day else 'سنة ' + year} · "
        f"أيام {len(days)} · كون [{PRICE_LO}, {PRICE_HI}]$ · "
        f"بوابات الإنتاج: رفعة {S.LIQ_MIN_MOVE_PCT}% · أرضية ${S.LIQ_MIN_USD:,} "
        f"× {S.LIQ_CUM_MINUTES}د · قفزة {S.CONFIG['IGNITION_VOL_MULT']}×")

    prev_close: dict = {}
    rows_out: list = []
    n_files = n_missing = n_syms = n_screened = n_anchored = 0
    n_gapcap = 0
    v2_checked = v2_anchors = 0
    out_path = (f"kasih_rows_{year or one_day}.jsonl")
    fout = open(out_path, "w", encoding="utf-8")

    for di, day in enumerate(seed_days + days):
        seeding = di < len(seed_days)
        key = AH.day_key(day)
        mb, ep = AH.head_size_mb(key)
        if mb is None:
            if not seeding:
                n_missing += 1        # عطلةٌ أو ملفٌّ غائب — يُعَدّ لا يُخفى
            continue
        dest = f"/tmp/kasih-{day}.csv.gz"
        if not AH.download(key, dest, ep):
            n_missing += 0 if seeding else 1
            continue
        universe = {s for s, c in prev_close.items()
                    if PRICE_LO <= c <= PRICE_HI} if not seeding else set()
        try:
            with gzip.open(dest, "rt") as fh:
                bars, closes = parse_day(fh, universe)
        except (OSError, KeyError, ValueError) as e:
            log(f"   ⛔ {day}: تعذّرت القراءة ({type(e).__name__}: {e})")
            try:
                os.remove(dest)
            except OSError:
                pass
            n_missing += 0 if seeding else 1
            continue
        try:
            os.remove(dest)
        except OSError:
            pass
        if seeding:
            prev_close.update(closes)
            log(f"🌱 بذرة إغلاق الأمس من {day}: {len(closes):,} رمزًا")
            continue
        n_files += 1
        n_syms += len(bars)
        screened = {s: b for s, b in bars.items() if prescreen(b)}
        n_screened += len(screened)
        # ‏V2: عيّنةُ مستبعَدين تمرّ على دالّة الإنتاج — سوبرست أو خروج 3
        if n_files % V2_EVERY == 1:
            import random
            excl = [s for s in bars if s not in screened]
            random.Random(day).shuffle(excl)
            for s in excl[:V2_SAMPLE]:
                v2_checked += 1
                if first_anchor(bars[s]) is not None:
                    v2_anchors += 1
                    log(f"   🔴 V2: مِرساةٌ في مستبعَد {s} يوم {day}!")
        for sym, b in screened.items():
            e = first_anchor(b)
            if e is None:
                continue
            a_ms = int(e["anchor_ms"])
            entry = float(e["price"])
            pc = prev_close.get(sym)
            gap = (entry / pc - 1.0) * 100.0 if pc else None
            if gap is not None and abs(gap) > GAP_CAP:
                n_gapcap += 1
                continue
            res = resolve(b, a_ms, entry)
            if res is None:
                continue
            n_anchored += 1
            usd5 = f2_usd5(b, a_ms)
            row = {"sym": sym, "day": day, "anchor_ms": a_ms,
                   "anchor_ny": dt.datetime.fromtimestamp(
                       a_ms / 1000, tz=NY).strftime("%H:%M"),
                   "entry": entry, "usd1": float(e.get("usd") or 0),
                   "usd5": round(usd5),
                   "vol_x": e.get("vol_x"), "gap_pct":
                       round(gap, 1) if gap is not None else None,
                   "f1": S._ignition_candle_class(
                       float(e.get("usd") or 0))[0],
                   "f2": S._ignition_candle_class(usd5)[0],
                   "f3": f3_bucket(a_ms), "f4": f4_bucket(e.get("vol_x")),
                   "f5": (f5_bucket(gap) if gap is not None else None),
                   "f6": None}
            row.update(res)
            row["f6"] = "صمد 15د" if res["sustain15"] else "سُحق"
            fout.write(json.dumps(row, ensure_ascii=False) + "\n")
            rows_out.append(row)
        prev_close.update(closes)
        if n_files % 20 == 0:
            log(f"   📦 {n_files}/{len(days)} يومًا · كون اليوم "
                f"{len(universe):,} · مرشَّح {n_screened:,} · "
                f"مراسٍ {n_anchored:,}")
    fout.close()

    print("\n" + "=" * 74)
    print(f"🌊 T-KASIH — {'يوم ' + one_day if one_day else 'سنة ' + year} · "
          f"العقد kasih_prereg.md (مدفوع قبل أي رقم)")
    print("=" * 74)
    print(f"📥 أيامٌ قِيست {n_files} · مفقودة {n_missing} · رمز-يوم بالكون "
          f"{n_syms:,} · عبر المرشِّح {n_screened:,} · "
          f"**مراسٍ {n_anchored:,}** · استُبعد بتشويه تقسيم {n_gapcap}")
    print(f"🔒 V2 (سوبرست): فُحص {v2_checked} مستبعَدًا ⇒ مراسٍ فيهم "
          f"{v2_anchors} {'✅' if v2_anchors == 0 else '⛔'}")
    if rows_out:
        k = sum(1 for r in rows_out if r["kasih30"])
        k5 = sum(1 for r in rows_out if r.get("kasih50"))
        k100 = sum(1 for r in rows_out if r.get("kasih100"))
        lo, hi = wilson(k, len(rows_out))
        print(f"\n📊 الأساس: كاسح30 = {k}/{len(rows_out)} "
              f"({k / len(rows_out) * 100:.1f}% [{lo:.0f}·{hi:.0f}]) · "
              f"بلغ +50%: {k5} · بلغ +100%: {k100}")
        bucket_table(rows_out, "f2", "F2 — صنفُ فيصل على مجموع 5 دقائق من المِرساة (الحاكمة المرجَّحة K1)")
        bucket_table(rows_out, "f1", "F1 — صنفُ فيصل لدقيقة المِرساة")
        bucket_table(rows_out, "f3", "F3 — وقتُ المِرساة (نيويورك)")
        bucket_table(rows_out, "f4", "F4 — قفزةُ الحجم")
        bucket_table(rows_out, "f5", "F5 — المسافة من إغلاق الأمس")
        bucket_table(rows_out, "f6", "F6 — صمودُ ربع الساعة (فيصل)")
        if one_day:
            # ⚠️ وضعُ اليوم يطبع **كلَّ** المراسي بلا قصّ — V1 تشترط المطابقةَ
            #   بالاسم والزمن والسعر، والـartifact محجوبٌ شبكيًّا من بيئة التطوير.
            print(f"\n⑤ مراسي اليوم كلُّها ({len(rows_out)} — بلا قصّ) "
                  f"لمطابقة V1 مع gate_result:")
            for r in sorted(rows_out, key=lambda x: -x["mg_after"]):
                print(f"   ${r['sym']:6} مرساة {r['anchor_ny']} · دخول "
                      f"${r['entry']:.4g} · mg بعدها {r['mg_after']:+.1f}% · "
                      f"خروج {r['exit']} · F2 {r['f2']} (${r['usd5']:,})")
    print("\n⚠️ حدودُ الصدق (§⑧): لمسٌ لا تنفيذ · يومٌ واحد · مِرساةٌ/رمز/يوم ·"
          " إغلاقُ الأمس من الشموع · الحكمُ عبر السنوات الثلاث لا سنةً واحدة.")
    if v2_anchors:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
