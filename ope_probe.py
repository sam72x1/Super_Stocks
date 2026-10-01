#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🧪🎯 مِجَسُّ «رجع هنا الدخول» على TradingView — مؤقّتٌ يُحذف قبل الدمج · قراءةٌ فقط (بلا تلغرام ولا كتابةِ حالةٍ ولا git).

**أمرُ المالك (2026-10-01):** «رجع هنا الدخول». العاملُ (`operator_entry_live.py`) صامتٌ منذ انتهاء Polygon (2026-09-29):
مسحُ الدخول ومسحُ السيولة يأخذان **شموعَ الدقيقة** من `polygon_minute_bars` وإغلاقَ الأمس من `polygon_prev_close`.
البديلُ الوحيد المتاح: مِقبسُ TradingView (زائرٌ بلا دخول) — و**حدُّ صدقٍ مكتوبٌ لم يُقَس**: «بيانُ الزائر متأخّرٌ ‏≈15 دقيقة
داخل الجلسة» (`tv_bars_result.md §④`) · وحجمُ دقائقه **جزئيّ** (‏≈5-15% من الموحَّد · مِجَسّ `36653615576`).
⇒ **لا يُشعَل شيءٌ قبل أن يُقاس هذا في جلسةٍ حيّة.** المرجعُ: ياهو (دقائق 1m ممتدّة · ويوميّ) — مرجعٌ لا حقيقة.
🔌 **والقياسُ من نقطة النداء الإنتاجيّة نفسِها:** `Super_stock.TVLiveFeed` (الجلبُ · التسويةُ بحارسَيها · `bars` · `prev_close`)
— لا نسخةٌ موازية — فما يعبر هنا هو ما سيعمل في العامل حرفًا.

══ المعيارُ — مكتوبٌ قبل أيّ رقم (الحاكمةُ = أوّلُ تشغيلةٍ بين 14:00 و19:30 UTC في يوم جلسة) ══
- **O1 الطزاجة (يحكم الإشعال):** بين الرموز **النشطة** (لها شمعةُ ياهو في آخر 10 دقائق) — ‏≥10 رموز — الفرقُ `ياهو − TV`
  بين آخر شمعتَي الدقيقة: **الوسيط ‏≤ 2 دقيقة والـ90٪ ‏≤ 5 دقائق**. (تأخّرُ 15 دقيقة يُسقطها بالبناء.)
- **O2 التغطية:** شموعُ TV (غيرُ None) لـ‏≥ **95%** من كون السيولة.
- **O3 السعر:** إغلاقاتُ الدقائق المشتركة (الطابعُ نفسُه) ضمن **1%** في ‏≥ **90%** منها (‏≥200 دقيقة مشتركة).
- **O4 السرعة:** الدورةُ المستقرّة (‏`refresh(force=True)` الثاني: دقائقُ الكون كلِّه بثمانية مقابس) في ‏≤ **45 ثانية** (الدورةُ 60ث).
- **O5 الحجم بعد التسوية:** على الرموز التي سوّاها الجالبُ (`f` من الماسح بحارسَي التغطية والمدى) ولها ‏≥5 دقائق مشتركة —
  ‏≥10 رموز — الوسيطُ لنسبة `مجموع حجم TV المسوّى ÷ مجموع حجم ياهو` على الدقائق المشتركة بين **0.67 و1.5**
  (حدُّ مِجَسّ VOL ‏[0.5، 2] مُضيَّقًا لأن العتباتِ دولاريّة).
- **O6 إغلاقُ الأمس** (‏`prev_close` يختم J1 وسطرَ الكرت): ضمن **1%** من إغلاق ياهو للجلسة السابقة في ‏≥ **95%** من الرموز
  التي لها الاثنان (‏≥20 رمزًا).
- **O7 الفيواب** (زنادُ «هنا الدخول» نفسُه: «عبرَ الفيواب صاعدًا»): فيوابُ الجلسة النظاميّة (إغلاقٌ × حجم) على الدقائق المشتركة
  — لكلّ رمزٍ له ‏≥30 دقيقةً مشتركة — ضمن **1%** من فيواب ياهو في ‏≥ **90%** من الرموز (‏≥10 رموز). (التسويةُ لا تغيّره بالبناء ·
  والخطرُ أن دقائق الزائر **جزءٌ من المنصّات** فيختلف توزيعُ الحجم.)
- **الحكم:** السبعةُ معًا ⟵ يُشعَل مسارُ TradingView في «هنا الدخول» (خلف مفتاحٍ يرجع بت-بت) · أيُّ ساقطٍ ⟵ لا إشعال ويُعلَن
  الرقمُ للمالك (ولا يُرخى معيارٌ بعد رؤية رقم). **وتشغيلةٌ خارج النافذة وصفٌ لا حكم** (خروج 4).
══ تنبّؤات (تُنشر كما تقع) ══ (أ) O1 تسقط (التأخّرُ ‏≈15 دقيقة كما كُتب) · (ب) O2 تعبر · (ج) O3 تعبر · (د) O4 تعبر ·
(هـ) O5 مجهولة · (و) O6 تعبر · (ز) O7 مجهولة.
"""
from __future__ import annotations

import datetime as dt
import os
import statistics as st
import sys
import time

os.environ.setdefault("SCREENER_MODE", "PROBE")

import Super_stock as bot                                         # noqa: E402

UTC = dt.timezone.utc
O1_MED_MIN, O1_P90_MIN, O1_MIN_SYMS = 2.0, 5.0, 10
O2_MIN = 0.95
O3_TOL, O3_MIN, O3_MIN_N = 0.01, 0.90, 200
O4_MAX_S = 45.0
O5_LO, O5_HI, O5_MIN_SYMS, O5_MIN_PAIRS = 0.67, 1.5, 10, 5
O6_TOL, O6_MIN, O6_MIN_SYMS = 0.01, 0.95, 20
O7_TOL, O7_MIN, O7_MIN_SYMS, O7_MIN_PAIRS = 0.01, 0.90, 10, 30
ACTIVE_MIN = 10
WIN_LO_UTC, WIN_HI_UTC = 14 * 60, 19 * 60 + 30
YH_CAP = 150                       # ياهو مرجعٌ لعيّنةٍ مسقوفةٍ معلنة (الكونُ كلُّه لـO2/O4)


def _log(m):
    print(m, flush=True)


def _ny():
    from zoneinfo import ZoneInfo
    return ZoneInfo("America/New_York")


def load_universe():
    wl = bot.load_watchlist()
    near = bot.load_near_watch()
    try:
        import json
        press = json.load(open("press_radar_state.json", encoding="utf-8"))
    except Exception:                                             # noqa: BLE001
        press = {}
    hunter = bot.load_hunter_watch()
    uni_all, _ = bot.live_watch_universe(wl, near, press, hunter, cap=10 ** 9)
    return [r["symbol"] for r in uni_all]


def yahoo_minutes(syms):
    """{رمز: {طابعُ البداية (ث): (close, volume)}} لدقائق اليوم الممتدّة من ياهو — مرجع."""
    import yfinance as yf
    out = {}
    if not syms:
        return out
    try:
        df = yf.download(" ".join(syms), period="1d", interval="1m", prepost=True, group_by="ticker",
                         threads=True, progress=False, auto_adjust=False)
    except Exception as e:                                        # noqa: BLE001
        _log(f"⚠️ ياهو دقائق: {e}")
        return out
    for s in syms:
        try:
            sub = df[s] if len(syms) > 1 else df
            sub = sub.dropna(subset=["Close"])
            m = {}
            for ts, row in sub.iterrows():
                t = int(ts.tz_convert("UTC").timestamp()) if ts.tzinfo else int(ts.timestamp())
                m[t] = (float(row["Close"]), float(row.get("Volume") or 0.0))
            if m:
                out[s] = m
        except Exception:                                         # noqa: BLE001
            continue
    return out


def yahoo_prev_close(syms, today_ny):
    """{رمز: إغلاقُ آخر جلسةٍ قبل `today_ny`} من يوميّ ياهو (غيرِ المسوّى) — مرجع."""
    import yfinance as yf
    out = {}
    if not syms:
        return out
    try:
        df = yf.download(" ".join(syms), period="7d", interval="1d", group_by="ticker",
                         threads=True, progress=False, auto_adjust=False)
    except Exception as e:                                        # noqa: BLE001
        _log(f"⚠️ ياهو يوميّ: {e}")
        return out
    for s in syms:
        try:
            sub = df[s] if len(syms) > 1 else df
            sub = sub.dropna(subset=["Close"])
            rows = [(ix.date(), float(r["Close"])) for ix, r in sub.iterrows() if ix.date() < today_ny]
            if rows:
                out[s] = rows[-1][1]
        except Exception:                                         # noqa: BLE001
            continue
    return out


def main() -> int:
    now = dt.datetime.now(UTC)
    mins_utc = now.hour * 60 + now.minute
    day_ny = now.astimezone(_ny()).date()
    session_day = day_ny.weekday() < 5
    governing = session_day and WIN_LO_UTC <= mins_utc <= WIN_HI_UTC
    _log(f"🕒 الآن {now:%Y-%m-%d %H:%M} UTC · يومُ نيويورك {day_ny} · حاكمة={governing}")
    syms = load_universe()
    _log(f"👁️ كونُ السيولة: {len(syms)} رمزًا")
    feed = bot.TVLiveFeed()
    t0 = time.time()
    r1 = feed.refresh(syms)                      # أوّلُ جلب: دقائقُ الكون ‏+ يوميّ إغلاق الأمس
    s1 = time.time() - t0
    t0 = time.time()
    r2 = feed.refresh(syms, force=True)          # دورةٌ مستقرّة: الدقائقُ وحدَها (اليوميُّ مرّةً في اليوم)
    secs = time.time() - t0
    got = [s for s in syms if feed.raw.get(s)]
    _log(f"📺 TV (‏`TVLiveFeed`): الأوّل {r1} في {s1:.1f}ث · المستقرّ {r2} في {secs:.1f}ث")

    sample = got[:YH_CAP]
    yh = yahoo_minutes(sample)
    ypc = yahoo_prev_close(sample, day_ny)
    _log(f"🟣 ياهو (مرجع): دقائق {len(yh)} · إغلاقُ الأمس {len(ypc)} من {len(sample)}")
    now_s = int(time.time())
    deltas, pairs_ok, pairs_n, ratios, pc_ok, pc_n, pc_bad = [], 0, 0, [], 0, 0, []
    vw_ok, vw_n, vw_bad = 0, 0, []
    reg_open = int(dt.datetime(day_ny.year, day_ny.month, day_ny.day, 9, 30, tzinfo=_ny()).timestamp())
    for s in sample:
        b = feed.bars(s, minutes=24 * 60) or []
        y = yh.get(s) or {}
        if b and y:
            y_last = max(y)
            tv_last = int(b[-1]["t"]) // 1000
            if now_s - y_last <= ACTIVE_MIN * 60:
                deltas.append((y_last - tv_last) / 60.0)
            tvm = {int(x["t"]) // 1000: (float(x["c"]), float(x["v"] or 0.0)) for x in b}
            common = sorted(set(tvm) & set(y))
            for t in common:
                pairs_n += 1
                if y[t][0] > 0 and abs(tvm[t][0] / y[t][0] - 1.0) <= O3_TOL:
                    pairs_ok += 1
            if s in feed.scale and len(common) >= O5_MIN_PAIRS:     # O5 على ما سوّاه الجالبُ وحدَه
                sv_tv = sum(tvm[t][1] for t in common)
                sv_yh = sum(y[t][1] for t in common)
                if sv_yh > 0:
                    ratios.append(sv_tv / sv_yh)
            reg = [t for t in common if t >= reg_open]                 # O7 فيوابُ الجلسة على الدقائق المشتركة
            if len(reg) >= O7_MIN_PAIRS:
                d_tv = sum(tvm[t][1] for t in reg)
                d_yh = sum(y[t][1] for t in reg)
                if d_tv > 0 and d_yh > 0:
                    v_tv = sum(tvm[t][0] * tvm[t][1] for t in reg) / d_tv
                    v_yh = sum(y[t][0] * y[t][1] for t in reg) / d_yh
                    vw_n += 1
                    if abs(v_tv / v_yh - 1.0) <= O7_TOL:
                        vw_ok += 1
                    else:
                        vw_bad.append(f"{s} {v_tv:.4g}/{v_yh:.4g}")
        pv, yv = feed.prev_close(s), ypc.get(s)
        if pv and yv:
            pc_n += 1
            if abs(pv / yv - 1.0) <= O6_TOL:
                pc_ok += 1
            else:
                pc_bad.append(f"{s} {pv:g}/{yv:g}")
    med = st.median(deltas) if deltas else None
    p90 = sorted(deltas)[max(0, int(round(0.9 * len(deltas))) - 1)] if deltas else None
    o1 = len(deltas) >= O1_MIN_SYMS and med <= O1_MED_MIN and p90 <= O1_P90_MIN
    o2 = len(syms) > 0 and len(got) / len(syms) >= O2_MIN
    o3 = pairs_n >= O3_MIN_N and pairs_ok / pairs_n >= O3_MIN
    o4 = secs <= O4_MAX_S
    rmed = st.median(ratios) if ratios else None
    o5 = len(ratios) >= O5_MIN_SYMS and O5_LO <= rmed <= O5_HI
    o6 = pc_n >= O6_MIN_SYMS and pc_ok / pc_n >= O6_MIN
    o7 = vw_n >= O7_MIN_SYMS and vw_ok / vw_n >= O7_MIN
    _log("\n══════ النتيجة")
    _log(f"O1 الطزاجة: نشطة {len(deltas)} · الوسيط {med} د · الـ90٪ {p90} د ⟵ {'✅' if o1 else '❌'}")
    _log(f"O2 التغطية: {len(got)}/{len(syms)} ⟵ {'✅' if o2 else '❌'}")
    _log(f"O3 السعر ضمن 1%: {pairs_ok}/{pairs_n} ⟵ {'✅' if o3 else '❌'}")
    _log(f"O4 الدورةُ المستقرّة: {secs:.1f}ث (الأوّلُ بيوميّه {s1:.1f}ث) ⟵ {'✅' if o4 else '❌'}")
    _log(f"O5 الحجم المسوّى÷ياهو: رموز {len(ratios)} (مسوّى {len(feed.scale)} من {len(got)}) · الوسيط {rmed} ⟵ "
         f"{'✅' if o5 else '❌'}")
    _log(f"O6 إغلاقُ الأمس ضمن 1%: {pc_ok}/{pc_n} ⟵ {'✅' if o6 else '❌'}"
         + (f" · المخالفون: {', '.join(pc_bad[:15])}" if pc_bad else ""))
    _log(f"O7 الفيواب ضمن 1%: {vw_ok}/{vw_n} ⟵ {'✅' if o7 else '❌'}"
         + (f" · المخالفون: {', '.join(vw_bad[:15])}" if vw_bad else ""))
    if deltas:
        _log("   توزيعُ فرق الطزاجة (د): " + " · ".join(f"{x:.0f}" for x in sorted(deltas)))
    if ratios:
        _log("   توزيعُ نسبة الحجم: " + " · ".join(f"{x:.2f}" for x in sorted(ratios)))
    ok = o1 and o2 and o3 and o4 and o5 and o6 and o7
    if not governing:
        _log(f"⟵ ⚪ وصفٌ لا حكم (خارج نافذة 14:00-19:30 UTC ليوم جلسة) — والمعيارُ كان {'سيعبر' if ok else 'سيسقط'}")
        return 4
    _log(f"⟵ {'✅ الحاكمة عبرت — يُشعَل المسار' if ok else '❌ الحاكمة سقطت — لا إشعال'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
