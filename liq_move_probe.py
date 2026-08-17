#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📈🧮 **مِجَسُّ LIQ-MOVE** — الأرضيةُ التراكميّة ‏× ثمانيةُ بدائلَ للتجاوب.

عقدُه `liq_move_prereg.md` **مدفوعٌ قبل أيّ رقم**. يجيب سؤالَين:
**① هل التراكميّةُ تستعيد الـ59 دقيقةَ المفقودة؟ ② وهل هناك تجاوبٌ أفضلُ من ‏+5%؟**

🔑 **مقياسٌ واحدٌ لا اثنان:** الخليّةُ `A0/B1` **هي الإنتاجُ حرفيًّا** ويُقفَل عليها
**بت-بت** (`LOCK-PROD`) بمقارنةِ مُخرَجها بـ`Super_stock.liq_stage_events` على أربع
عيّناتٍ مفرِّقة. فإن تفرّقا **يُوقَف بخروج 3** ولا يُنشَر رقم.

🥇 **والمقياسُ الحاكمُ «الإثمار»** (‏§④-ب): نسبةُ إشعاراتِ `M1` التي بلغ سعرُها ‏+3%
خلال ‏15 دقيقةً **بعدها** — وهو جوابُ شكوى المالك «داخلها سيولة ومع ذلك ما تتحرك».
⚖️ و3% لا 5% عمدًا: `B1` تشترط 5% **قبل** الإشعار فقياسُ 5% بعده **دائريّة**.

🔒 **قراءةٌ/قياسٌ فقط:** لا يكتب حالةً ولا يرسل تلغرامًا ولا يمسّ فرزًا ولا جذرًا.
"""
import json
import os
import sys
import time

os.environ.setdefault("SCREENER_MODE", "PROBE")
import Super_stock as bot                                          # noqa: E402
import liq_noise_probe as NZ                                       # noqa: E402

WINDOW_MIN = 480
MOVER_PCT = 30.0            # 🔒 نفسُ تعريف `liq_noise_prereg` حرفيًّا — لا يُحرَّك
MOVER_MIN_N = 5
FRUIT_PCT = 3.0             # عتبةُ «أثمر» (‏§④-ب)
FRUIT_MIN = 15              # دقائقُ المهلة بعد الإشعار
JITTER_PP = 3.6             # تقلّبُ القياس المقيس (‏`liq_noise_result.md §④`)
WORKERS = 8

# ⚙️ **الشبكةُ مثبَّتةٌ في `liq_move_prereg.md §②/§③`** — ولا تُزاد خليّةٌ بعد الأرقام.
A_ARMS = {"A0": {"cum_floor": 0}, "A1": {"cum_floor": 3}}
B_ARMS = {
    "B0": {},
    "B1": {"move_min": 5.0},                       # 🥇 قاعدةُ المالك (الإنتاج)
    "B2": {"move_prev_min": 5.0},
    "B3": {"move_cum_min": 5.0},
    "B4": {"hi30": True},
    "B5": {"above_vwap": True},
    "B6": {"above_open": True},
    "B7": {"move_min": 5.0, "or_struct": True},    # `B1` أو (`B4` و`B5`)
}
B_DESC = {
    "B0": "بلا تجاوب (ما قبل أمره — للمقارنة)",
    "B1": "🥇 رفعةُ الدقيقة ‏≥5% فتحًا⟶إغلاقًا (**المُعتمَدُ بأمره**)",
    "B2": "رفعةٌ ‏≥5% عن إغلاق الدقيقة السابقة",
    "B3": "رفعةٌ تراكميّةٌ ‏≥5% من المِرساة",
    "B4": "قمّةُ ثلاثين دقيقة (بنيويّ — بلا رقمٍ مخترَع)",
    "B5": "فوق فيواب الجلسة (بنيويّ)",
    "B6": "فوق افتتاح اليوم (حالةُ `BZAI` ‏−28%)",
    "B7": "مركَّب: `B1` أو (`B4` و`B5`)",
}


def cell_events(bars, state, a_cfg, b_cfg, anchor_px=None):
    """♻️ منطقُ `liq_stage_events` بأعلامِ الخليّة — و`A0/B1` مقفولةٌ بت-بت عليه.

    ترجّع `(events, new_state)`. فاشلةٌ-آمنة ⇒ `([], state)`."""
    st = dict(state or {})
    try:
        vm = float(bot.CONFIG["IGNITION_VOL_MULT"])
        cap = int(bot.LIQ_UPDATE_CAP)
        stg = tuple(bot.LIQ_STAGE_MINUTES)
        floor = float(bot.LIQ_MIN_USD)
        cum_n = int(a_cfg.get("cum_floor") or 0)
        rows = [b for b in (bars or []) if b.get("t") is not None
                and b.get("c") is not None and b.get("v") is not None]
        if len(rows) < 3:
            return ([], st)
        rows.sort(key=lambda b: int(b["t"]))
        closed = rows[:-1]                      # 🔒 المتكوّنةُ تُسقَط دائمًا
        if len(closed) < 2:
            return ([], st)
        last = closed[-1]
        last_ms = int(last["t"])

        def _usd(b):
            return float(b["c"]) * float(b["v"])

        def _liq_ok():
            """الأرضية: الدقيقةُ الواحدة · أو **مجموعُ `cum_n` دقائقَ متتالية**.

            🔒 وشرطُ الحياة باقٍ في الحالين: القفزةُ والاتجاهُ والرفعةُ كلُّها على
            **الدقيقة الأخيرة** ⇒ مجموعٌ قديمٌ بدقيقةٍ ميّتةٍ الآن لا يُطلِق."""
            if cum_n <= 1:
                return _usd(last) >= floor
            return sum(_usd(b) for b in closed[-cum_n:]) >= floor

        def _rise(b):
            try:
                o_, c_ = float(b.get("o") or b["c"]), float(b["c"])
                return ((c_ - o_) / o_ * 100.0) if o_ > 0 else 0.0
            except Exception:                                    # noqa: BLE001
                return 0.0

        def _rise_prev(b):
            try:
                i = closed.index(b)
            except ValueError:                                   # noqa: BLE001
                return 0.0
            if i < 1:
                return _rise(b)
            p = float(closed[i - 1]["c"])
            return ((float(b["c"]) - p) / p * 100.0) if p > 0 else 0.0

        def _hi30(b):
            """قمّةُ ثلاثين دقيقة: إغلاقُها أعلى من **كلّ** إغلاقٍ في الثلاثين قبلها."""
            try:
                i = closed.index(b)
            except ValueError:                                   # noqa: BLE001
                return False
            prev = closed[max(0, i - 30):i]
            return bool(prev) and float(b["c"]) > max(float(x["c"]) for x in prev)

        def _vwap():
            num = sum(float(x.get("vw") or x["c"]) * float(x["v"]) for x in closed)
            den = sum(float(x["v"]) for x in closed)
            return (num / den) if den > 0 else None

        def _above_open(b):
            b0 = closed[0]
            op = float(b0.get("o") or b0["c"])
            return op <= 0 or float(b["c"]) >= op

        def _struct(b):
            v = _vwap()
            return _hi30(b) and (v is None or float(b["c"]) >= v)

        def _resp(b, apx):
            """بوّابةُ التجاوب بأعلام الخليّة (‏`B0`-`B7`)."""
            if b_cfg.get("or_struct"):
                mm = float(b_cfg.get("move_min") or 0)
                return (_rise(b) >= mm) or _struct(b)
            if b_cfg.get("move_min") and _rise(b) < float(b_cfg["move_min"]):
                return False
            if (b_cfg.get("move_prev_min")
                    and _rise_prev(b) < float(b_cfg["move_prev_min"])):
                return False
            if b_cfg.get("move_cum_min"):
                ref = apx if apx else float(b.get("o") or b["c"])
                need = float(b_cfg["move_cum_min"])
                if ref > 0 and (float(b["c"]) - ref) / ref * 100.0 < need:
                    return False
            if b_cfg.get("hi30") and not _hi30(b):
                return False
            if b_cfg.get("above_vwap"):
                v = _vwap()
                if v is not None and float(b["c"]) < v:
                    return False
            if b_cfg.get("above_open") and not _above_open(b):
                return False
            return True

        def _inflow(b):
            try:
                o_, c_ = float(b.get("o") or b["c"]), float(b["c"])
                h_, l_ = float(b.get("h") or c_), float(b.get("l") or c_)
                if c_ < o_:
                    return False
                rng = h_ - l_
                return rng <= 0 or (c_ - l_) >= bot.LIQ_CLOSE_POS_MIN * rng
            except Exception:                                    # noqa: BLE001
                return False

        ev = []
        anchor = st.get("anchor_ms")
        apx = st.get("anchor_px") or anchor_px
        if not anchor:
            prior = [float(b["v"]) for b in closed[:-1]]
            avg = sum(prior) / len(prior) if prior else 0.0
            vx = (float(last["v"]) / avg) if avg > 0 else 0.0
            if (vx < vm or not _liq_ok() or not _inflow(last)
                    or not _resp(last, float(last.get("o") or last["c"]))):
                return ([], st)
            st = {"anchor_ms": last_ms, "last_ms": last_ms, "sent": ["M1"],
                  "updates": 0, "vol_x": round(vx, 1),
                  "peak_usd": round(_usd(last)),
                  "anchor_px": float(last.get("o") or last["c"])}
            ev.append({"stage": "M1", "usd": round(_usd(last)), "minutes": 1,
                       "anchor_ms": last_ms, "last_ms": last_ms,
                       "vol_x": round(vx, 1),
                       "price": round(float(last["c"]), 4),
                       "move": round(_rise(last), 2),
                       "class": bot._ignition_candle_class(_usd(last))})
            return (ev, st)
        anchor = int(anchor)
        if last_ms > int(st.get("last_ms") or 0):
            st["last_ms"] = last_ms
            _u = _usd(last)
            _pk = float(st.get("peak_usd") or 0)
            if (_u > _pk and _liq_ok() and _inflow(last)
                    and _resp(last, apx)):
                st["peak_usd"] = round(_u)
                if int(st.get("updates") or 0) < cap:
                    st["updates"] = int(st.get("updates") or 0) + 1
                    ev.append({"stage": "Mu", "usd": round(_u), "minutes": 1,
                               "anchor_ms": anchor, "last_ms": last_ms,
                               "vol_x": st.get("vol_x"),
                               "price": round(float(last["c"]), 4),
                               "move": round(_rise(last), 2),
                               "class": bot._ignition_candle_class(_u)})
        sent = list(st.get("sent") or [])
        span = (last_ms - anchor) // 60_000 + 1
        for n in stg:
            tag = f"M{int(n)}"
            if tag in sent or span < int(n):
                continue
            win = [b for b in closed
                   if anchor <= int(b["t"]) < anchor + int(n) * 60_000]
            if not win:
                continue
            tot = sum(_usd(b) for b in win)
            sent.append(tag)
            ev.append({"stage": tag, "usd": round(tot), "minutes": len(win),
                       "anchor_ms": anchor, "last_ms": last_ms,
                       "vol_x": st.get("vol_x"),
                       "price": round(float(win[-1]["c"]), 4),
                       "class": bot._ignition_candle_class(tot)})
        st["sent"] = sent
        return (ev, st)
    except Exception:                                            # noqa: BLE001
        return ([], st)


def replay(bars, a_cfg, b_cfg, window=None):
    """▶️ دقيقةٌ مكتملةٌ في كلّ خطوة — نفسُ ما يراه المُشغِّلُ الحيّ."""
    win = int(window or bot.LIQ_WINDOW_MIN)
    st, out = {}, []
    for k in range(3, len(bars) + 1):
        evs, st = cell_events(bars[max(0, k - win):k], st, a_cfg, b_cfg)
        for e in (evs or []):
            out.append((k - 2, e))
    return out


def fruit(bars, idx, price):
    """🍎 **الإثمار**: أعلى إغلاقٍ في `FRUIT_MIN` دقيقةً **بعد** الإشعار ÷ سعرِه ‏−1.

    يرجّع `None` إن لم تتوفّر المهلةُ كاملةً ⇒ **يُستبعَد ويُعَدّ** (‏§⑨-4) ولا يُحسَب
    صفرًا — فالإشعارُ في آخر ربع ساعةٍ من الجلسة لا يُقاس إثمارُه."""
    nxt = bars[idx + 1: idx + 1 + FRUIT_MIN]
    if len(nxt) < FRUIT_MIN or not price:
        return None
    try:
        hi = max(float(b["c"]) for b in nxt)
        return (hi / float(price) - 1.0) * 100.0
    except Exception:                                            # noqa: BLE001
        return None


def _lock_prod():
    """🔒 `LOCK-PROD` — الخليّةُ `A1/B1` **بت-بت** مع الإنتاج على عيّناتِ `LOCK-V4`
    الأربعِ **المفرِّقة** (تُعاد استعمالًا لا نسخًا) ‏+ شاهدُ تفريقٍ للتجاوب."""
    def _b(t, o, h, l, c, v):
        return {"t": t, "o": o, "h": h, "l": l, "c": c, "v": v}
    base = [_b(i * 60_000, 1.0, 1.01, 0.99, 1.0, 500) for i in range(8)]
    big = base + [_b(8 * 60_000, 1.0, 1.30, 1.0, 1.29, 35_000),
                  _b(9 * 60_000, 1.29, 1.30, 1.28, 1.29, 100)]
    small = base + [_b(8 * 60_000, 1.0, 1.02, 1.0, 1.01, 1_600),
                    _b(9 * 60_000, 1.01, 1.02, 1.0, 1.01, 100)]
    fade = big + [_b(10 * 60_000, 1.29, 1.30, 1.20, 1.21, 31_000),
                  _b(11 * 60_000, 1.21, 1.22, 1.10, 1.11, 30_000),
                  _b(12 * 60_000, 1.11, 1.12, 1.10, 1.11, 100)]
    dim = base + [_b(8 * 60_000, 1.00, 1.29, 1.00, 1.29, 35_000),
                  _b(9 * 60_000, 1.29, 1.44, 1.29, 1.44, 28_000),
                  _b(10 * 60_000, 1.44, 1.54, 1.44, 1.54, 23_000),
                  _b(11 * 60_000, 1.54, 1.55, 1.53, 1.54, 100)]
    # 🕵️ حالةُ `TENX`: سيولةٌ ضخمةٌ بلا تجاوب ⇒ يجب أن تفرّق `B0` عن `B1`
    tenx = base + [_b(8 * 60_000, 1.82, 1.83, 1.815, 1.8227, 100_000),
                   _b(9 * 60_000, 1.82, 1.83, 1.82, 1.82, 100)]
    # 🐞 **عيّنةٌ سادسةٌ أضافتها طفرةٌ نجت** (‏`N5`: توسيعُ نافذة التراكميّة إلى
    #    **بلا حدّ** مرَّ أخضر): الخمسةُ أعلاه مجموعُها فوق الأرضية **بالحدّ وبلاه**
    #    فلا تفرّقان. ⇒ هذي **ستّون دقيقةً هادئةً مجموعُها ‏$30 ألفًا بالضبط** ثم
    #    ثلاثُ دقائقَ صاعدةٍ صغيرةٍ مجموعُها ‏$6.7 ألفًا: **بحدّ الثلاثِ ⇒ صمتٌ**
    #    (‏6.7 دون الأرضية) · **وبلا حدٍّ ⇒ تُطلق** (‏36.7 فوقها). ولو صار المجموعُ
    #    بلا حدٍّ لصارت الأرضيةُ بلا معنى (أيُّ سهمٍ له تاريخُ حجمٍ يعبرها).
    wide = [_b(i * 60_000, 1.0, 1.0, 1.0, 1.0, 500) for i in range(60)]
    for _i in range(3):
        _o, _c = 1.06 ** _i, 1.06 ** (_i + 1)
        wide.append(_b((60 + _i) * 60_000, _o, _c, _o, _c, 2_000))
    wide.append(_b(63 * 60_000, 1.19, 1.19, 1.19, 1.19, 50))
    ok, notes = True, []
    for name, bars in (("ضخمةٌ داخلة", big), ("صغيرةٌ نسبيّة", small),
                       ("سلسلةٌ خابية", fade), ("خضراءُ متناقصة", dim),
                       ("TENX بلا تجاوب", tenx),
                       ("هادئٌ طويلٌ ثم ثلاثٌ صغيرة", wide)):
        # 🔓 **إقرارٌ مؤرَّخ 2026-08-17: الإنتاجُ صار `A1/B1`** باعتماد التراكميّة
        #    بعقد `liq_move_prereg.md §⑥` ⇒ القفلُ ينتقل إليها. و`A0/B1` تبقى
        #    ذراعًا مقيسةً في الشبكة فأرقامُ `liq_move_result.md` تُعاد بت-بت.
        mine = replay(bars, A_ARMS["A1"], B_ARMS["B1"])
        prod, st = [], {}
        for k in range(3, len(bars) + 1):
            evs, st = bot.liq_stage_events(
                bars[max(0, k - bot.LIQ_WINDOW_MIN):k], st)
            for e in (evs or []):
                prod.append((k - 2, e))
        same = json.dumps(mine, sort_keys=True, default=str) == \
            json.dumps(prod, sort_keys=True, default=str)
        notes.append(f"{name}: مِجَسّ={len(mine)} إنتاج={len(prod)} "
                     f"{'✅' if same else '❌'}")
        ok = ok and same
    n0 = len(replay(tenx, A_ARMS["A0"], B_ARMS["B0"]))
    n1 = len(replay(tenx, A_ARMS["A0"], B_ARMS["B1"]))
    notes.append(f"التجاوبُ يفرّق (TENX): B0={n0} · B1={n1} "
                 f"{'✅' if n0 > n1 else '❌'}")
    ok = ok and n0 > n1
    # 🔒 والتراكميّةُ تفرّق: ثلاثُ دقائقَ × ‏$12 ألفًا (المجموعُ 36 ألفًا) بمنحدرٍ ‏+6%
    cum = base + [_b((8 + i) * 60_000, 1.0 * 1.06 ** i, 1.0 * 1.06 ** (i + 1),
                     1.0 * 1.06 ** i, 1.0 * 1.06 ** (i + 1), 11_500)
                  for i in range(3)] + [_b(11 * 60_000, 1.19, 1.19, 1.19, 1.19, 50)]
    c0 = len(replay(cum, A_ARMS["A0"], B_ARMS["B1"]))
    c1 = len(replay(cum, A_ARMS["A1"], B_ARMS["B1"]))
    notes.append(f"التراكميّةُ تفرّق: A0={c0} · A1={c1} "
                 f"{'✅' if c1 > c0 else '❌'}")
    ok = ok and c1 > c0
    # 🔒 وشاهدٌ يُثبت أن العيّنةَ السادسةَ تفرّق **حدَّ النافذة بعينه**
    w3 = len(replay(wide, {"cum_floor": 3}, B_ARMS["B1"]))
    w99 = len(replay(wide, {"cum_floor": 999}, B_ARMS["B1"]))
    notes.append(f"حدُّ النافذة يفرّق: بثلاثٍ={w3} · بلا حدٍّ={w99} "
                 f"{'✅' if w99 > w3 else '❌'}")
    ok = ok and w99 > w3
    return ok, notes


def main():
    if not os.environ.get("POLYGON_API_KEY", "").strip():
        print("⛔ لا مفتاح Polygon — لا قياس (ولا يُخمَّن رقم).")
        return 2
    print("📈🧮 مِجَسُّ LIQ-MOVE — عقدُه `liq_move_prereg.md`\n")
    ok, notes = _lock_prod()
    for n in notes:
        print("   🔒 " + n)
    if not ok:
        print("\n⛔ `LOCK-PROD` سقط: المِجَسُّ تفرّق عن الإنتاج ⇒ **لا يُنشَر رقم**.")
        return 3
    print("   ✅ `LOCK-PROD` عبر — المِجَسُّ يقيس بآلة الإنتاج نفسِها.\n")

    import operator_entry_live as oel
    try:
        _u, _c, _s, uni_all = oel._load_universe()
    except Exception as e:                                       # noqa: BLE001
        print(f"⛔ تعذّر بناءُ الكون: {type(e).__name__}: {e}")
        return 2
    syms = [r["symbol"] for r in uni_all]
    print(f"👁️ الكون: {len(syms)} سهمًا (نفسُ كونِ المُشغِّل · بلا استثناء)")

    import concurrent.futures as cf
    t0, data, fails = time.time(), {}, 0

    def _one(s):
        try:
            return (s, bot.polygon_minute_bars(s, minutes=WINDOW_MIN))
        except Exception:                                        # noqa: BLE001
            return (s, None)

    with cf.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for s, bars in pool.map(_one, syms):
            if bars and len(bars) >= 5:
                data[s] = bars
            else:
                fails += 1
    print(f"📥 شموعٌ مجلوبة: {len(data)} من {len(syms)} · تعذّر {fails} · "
          f"{round(time.time() - t0, 1)}ث\n")
    if not data:
        print("⛔ صفرُ شموع — لا قياس.")
        return 2

    refs, movers, no_ref = {}, [], 0
    for s, bars in data.items():
        r = NZ.session_ref(bars)          # 🔒 نفسُ تعريف المتحرّك حرفيًّا
        if r is None:
            no_ref += 1
            continue
        refs[s] = r
        if r["rise_pct"] >= MOVER_PCT:
            movers.append(s)
    print(f"🏃 متحرّكون (‏+{MOVER_PCT:.0f}%): {len(movers)} — "
          f"{', '.join(sorted(movers)) if movers else 'لا أحد'}"
          + (f"\n   ⚠️ **دون حدّ {MOVER_MIN_N} ⇒ لا حكمَ على الاسترجاع** (‏§⑨-3)"
             if len(movers) < MOVER_MIN_N else "") + "\n")

    res = {}
    for an, a in A_ARMS.items():
        for bn, b in B_ARMS.items():
            tot, syms_n, m1, fr, unres = 0, set(), {}, [], 0
            for s, bars in data.items():
                evs = replay(bars, a, b)
                if not evs:
                    continue
                tot += len(evs)
                syms_n.add(s)
                for k, e in evs:
                    if e["stage"] == "M1" and s not in m1:
                        m1[s] = k
                        f = fruit(bars, k, e.get("price"))
                        if f is None:
                            unres += 1
                        else:
                            fr.append(f)
            hit = sum(1 for f in fr if f >= FRUIT_PCT)
            res[(an, bn)] = {
                "total": tot, "syms": len(syms_n), "m1": m1,
                "fruit_n": len(fr), "fruit_hit": hit, "unres": unres,
                "fruit_pct": (100.0 * hit / len(fr)) if fr else None}

    def _lead(cell):
        ls = sorted(refs[s]["high_i"] - cell["m1"][s] for s in movers
                    if cell["m1"].get(s) is not None)
        return ls[len(ls) // 2] if ls else None

    print("=" * 70)
    print("① الشبكةُ كاملةً — الضجيجُ والإثمارُ والأسبقيّة")
    print("=" * 70)
    print("  خليّة | إشعارات | أسهم | أثمر٪ (مقام) | غيرُ مقيس | متحرّكون | أسبقيّة")
    for an in A_ARMS:
        for bn in B_ARMS:
            c = res[(an, bn)]
            fp = ("—" if c["fruit_pct"] is None
                  else f"{c['fruit_pct']:.1f}% ({c['fruit_n']})")
            hits = sum(1 for s in movers if c["m1"].get(s) is not None)
            ld = _lead(c)
            print(f"  {an}/{bn} | {c['total']:>7,} | {c['syms']:>4} | {fp:>14} |"
                  f" {c['unres']:>9} | {hits:>8} |"
                  f" {('—' if ld is None else str(ld) + 'د'):>7}")
    print("\n  " + " · ".join(f"{k}: {v}" for k, v in B_DESC.items()))

    prod = res[("A0", "B1")]
    b0 = res[("A0", "B0")]
    print("\n" + "=" * 70)
    print("② المقارنةُ الأساسيّة المسجَّلة — `A1` مقابل `A0` (كلتاهما `B1`)")
    print("=" * 70)
    a1 = res[("A1", "B1")]
    l0, l1 = _lead(prod), _lead(a1)
    rec = (l1 - l0) if (l0 is not None and l1 is not None) else None
    dn = (100.0 * (a1["total"] - prod["total"]) / prod["total"]
          if prod["total"] else 0.0)
    df = ((a1["fruit_pct"] - prod["fruit_pct"])
          if (a1["fruit_pct"] is not None and prod["fruit_pct"] is not None)
          else None)
    c1 = rec is not None and rec >= 5
    c2 = df is not None and df >= -JITTER_PP
    c3 = dn <= 20.0
    print(f"  الأسبقيّةُ المستعادة: {rec} دقيقة (الحدّ 5) "
          f"{'✅' if c1 else '❌'}")
    print(f"  فرقُ الإثمار: {('—' if df is None else f'{df:+.1f}ن')} "
          f"(الحدّ ‏−{JITTER_PP}) {'✅' if c2 else '❌'}")
    print(f"  زيادةُ الإشعارات: {dn:+.1f}% (الحدّ 20%) {'✅' if c3 else '❌'}")
    print(f"  ⇒ **{'✅ تُعتمَد التراكميّة' if (c1 and c2 and c3) else '🔴 لا تُعتمَد'}**")

    print("\n" + "=" * 70)
    print("③ بدائلُ التجاوب — من يستبدل قاعدةَ المالك؟ (ثانويٌّ · حدُّ 3.6 نقطة)")
    print("=" * 70)
    pm = {s for s in movers if prod["m1"].get(s) is not None}
    for bn in B_ARMS:
        if bn == "B1":
            continue
        c = res[("A0", bn)]
        hm = {s for s in movers if c["m1"].get(s) is not None}
        d = ((c["fruit_pct"] - prod["fruit_pct"])
             if (c["fruit_pct"] is not None and prod["fruit_pct"] is not None)
             else None)
        k1 = d is not None and d > JITTER_PP
        k2 = pm <= hm
        k3 = c["total"] <= prod["total"]
        lc, lp = _lead(c), _lead(prod)
        k4 = (lc is None or lp is None) or (lp - lc) <= 1
        good = k1 and k2 and k3 and k4
        print(f"  {bn}: إثمارٌ {('—' if d is None else f'{d:+.1f}ن')} "
              f"{'✅' if k1 else '❌'} · متحرّكون {len(hm)}/{len(pm)} "
              f"{'✅' if k2 else '❌'} · إشعارات {c['total']:,} "
              f"{'✅' if k3 else '❌'} · أسبقيّة {'✅' if k4 else '❌'} ⇒ "
              f"{'✅ يستبدل' if good else '🔴 لا يستبدل'}")

    print("\n" + "=" * 70)
    print("④ الحالةُ التي تُوجب الرجوعَ للمالك (‏§⑥)")
    print("=" * 70)
    if (prod["fruit_pct"] is not None and b0["fruit_pct"] is not None
            and prod["fruit_pct"] < b0["fruit_pct"]):
        print(f"  🔴🔴 **إثمارُ قاعدته {prod['fruit_pct']:.1f}% دون `B0` "
              f"{b0['fruit_pct']:.1f}% ⇒ يُبلَّغ فورًا**: الرفعةُ تكتم المُثمِر.")
    else:
        _p = prod["fruit_pct"]
        _z = b0["fruit_pct"]
        _ps = "—" if _p is None else "{:.1f}%".format(_p)
        _zs = "—" if _z is None else "{:.1f}%".format(_z)
        print("  ✅ إثمارُ قاعدته {} مقابل `B0` {} ⇒ **لا تقع الحالة**."
              .format(_ps, _zs))

    print("\n" + "=" * 70)
    print("⑤ حدودُ صدقٍ (‏§⑨ — تُقرأ مع الأرقام لا بعدها)")
    print("=" * 70)
    print("  1. جلسةٌ واحدة ⇒ مِجَسُّ كلفةٍ وإثمارٍ لا حكمٌ على العائد · ولا صفقةَ تُقاس.")
    print(f"  2. «الإثمار» أعلى إغلاقٍ في {FRUIT_MIN} دقيقة — **سعرٌ مطبوعٌ لا "
          "تنفيذ** ⇒ سقفٌ متفائل.")
    print(f"  3. المتحرّكون {len(movers)} (الحدّ {MOVER_MIN_N}) ⇒ متحرّكٌ واحدٌ يقلب "
          "ذراعًا · وبلا مرجعِ جلسة "
          f"{no_ref} · وتعذّرَ الجلبُ لـ{fails}.")
    print("  4. وإشعاراتُ آخر ربع ساعةٍ **غيرُ مقيسةِ الإثمار** — تُستبعَد وتُعَدّ "
          "(العمودُ «غيرُ مقيس»).")
    print("  5. والإعادةُ **سقفٌ** للضجيج: المُشغِّلُ الحيُّ يفقد دوراتٍ فيُنبِّه أقلّ.")
    print("  6. وكونُ اليوم رقيقٌ ⇒ لا تُعمَّم على كونٍ سائل.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
