#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🔇 **مِجَسُّ الضجيج LIQ-NOISE** — إعادةٌ مضبوطةٌ لثمانية أذرعٍ على جلسةٍ حيّة.

عقدُه `liq_noise_prereg.md` **مدفوعٌ قبل أيّ رقم**. يجيب سؤالًا واحدًا: **كم إشعارًا
يقصّ كلُّ طبقةٍ من بوّابة الضجيج؟ وهل تُفقِد متحرّكًا؟**

🔑 **مقياسٌ واحدٌ لا اثنان:** الذراعُ `V4` **هي الإنتاجُ حرفيًّا** — والمِجَسُّ يقفلها
بمقارنةٍ **بت-بت** مع `Super_stock.liq_stage_events` على المدخل نفسِه (‏`LOCK-V4`).
فإن تفرّق المُخرَجان **يُوقَف بخروجٍ غيرِ صفريّ** ولا يُنشَر رقم — لأن أرقامَ الأذرع
الأخرى ستكون على آلةٍ غير آلةِ الإنتاج.

⚖️ **والإعادةُ ما يفعله الحيُّ فعلًا:** المُشغِّلُ يلفّ كلَّ ‏≈60 ثانية ويقرأ نافذةَ
`LIQ_WINDOW_MIN`، والدالّةُ **تُسقط الشمعةَ المتكوّنة** ⇒ فإطعامُ `bars[:k]` خطوةً
خطوةً يعطي **دقيقةً مكتملةً جديدةً في كلّ خطوة** = نفسُ ما يراه الحيّ. وسقوطُ نداءٍ
حيًّا أو تأخّرُ دورةٍ يجعله **أقلَّ** إشعارًا لا أكثر ⇒ أرقامُنا **سقفٌ** للضجيج.

🔒 **عرض/قياس فقط:** لا يكتب ملفَّ حالةٍ ولا يرسل تلغرامًا ولا يمسّ فرزًا ولا جذرًا.

التشغيل: `LIQ_NOISE=1 python3 liq_noise_probe.py` (يلزمه `POLYGON_API_KEY`).
"""
import json
import os
import sys
import time

os.environ.setdefault("SCREENER_MODE", "PROBE")
import Super_stock as bot                                          # noqa: E402

WINDOW_MIN = 480          # ‏8 ساعاتٍ رجعيًّا: تغطّي البريماركت والجلسة كاملةً
MOVER_PCT = 30.0          # تعريفُ «المتحرّك» — مثبَّتٌ في التسجيل §③
MOVER_MIN_N = 5           # دون هذا: «لا حكم» على الاسترجاع (‏§⑦-3)
WORKERS = 8

# ⚙️ **الأذرعُ الثمانية — مثبَّتةٌ في `liq_noise_prereg.md §②`.** ولا تُضاف ذراعٌ
#    بعد الأرقام (`LOCK-ARMS` في السويّة يقفل الأسماءَ والعدد).
ARMS = {
    "V0": {},
    "V1": {"floor_anchor": True},
    "V2": {"floor_anchor": True, "floor_update": True},
    "V3": {"floor_anchor": True, "floor_update": True, "inflow": True},
    "V4": {"floor_anchor": True, "floor_update": True, "inflow": True,
           "highwater": True},
    "V5": {"floor_anchor": True, "floor_update": True, "inflow": True,
           "highwater": True, "consecutive": 2},
    "V6": {"floor_anchor": True, "floor_update": True, "inflow": True,
           "highwater": True, "rel_floor_mult": 5.0},
    "V7": {"floor_anchor": True, "floor_update": True, "inflow": True,
           "highwater": True, "above_open": True},
}
ARM_DESC = {
    "V0": "الأساسُ الذي أغرق (قفزةٌ نسبيّةٌ وحدها)",
    "V1": "‏+ أرضيةُ $30 ألفٍ على المِرساة وحدها",
    "V2": "‏+ الأرضيةُ على التحديثات أيضًا",
    "V3": "‏+ اتجاهٌ داخل (خضراءُ وإغلاقٌ في النصف الأعلى)",
    "V4": "‏+ تحديثٌ عند تجاوز القمّة ⇐ **المُعتمَدُ بأمر المالك**",
    "V5": "‏V4 + دقيقتان متتاليتان قبل أوّل إشعار",
    "V6": "‏V4 بأرضيةٍ نسبيّةٍ max($30k, 5× وسيطَ السهم)",
    "V7": "‏V4 + إغلاقٌ فوق افتتاح اليوم",
}


def arm_events(bars, state, cfg):
    """♻️ **إعادةُ منطقِ `liq_stage_events` بأعلامِ الذراع** — و`V4` تُقفَل بت-بت
    عليه (‏`LOCK-V4`) فيبقى **مقياسٌ واحد** لا نسختان تتفرّقان بصمت.

    ترجّع `(events, new_state)` بنفس شكل الإنتاج. فاشلةٌ-آمنة ⇒ `([], state)`."""
    st = dict(state or {})
    try:
        vm = float(bot.CONFIG["IGNITION_VOL_MULT"])
        cap = int(bot.LIQ_UPDATE_CAP)
        stg = tuple(bot.LIQ_STAGE_MINUTES)
        base_floor = float(bot.LIQ_MIN_USD)
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

        def _floor():
            """الأرضيةُ النافذة: مطلقةٌ · أو `max(المطلقة، mult× وسيطَ السهم)`."""
            f = base_floor if cfg.get("floor_anchor") else 0.0
            mult = cfg.get("rel_floor_mult")
            if mult and len(closed) >= 5:
                vals = sorted(_usd(b) for b in closed[:-1])
                med = vals[len(vals) // 2]
                f = max(f, float(mult) * med)
            return f

        def _day_open():
            try:
                b0 = closed[0]
                return float(b0.get("o") or b0["c"])
            except Exception:                                    # noqa: BLE001
                return None

        def _ok(b, floor_on):
            """بوّابةُ الدقيقة الواحدة: أرضيةٌ ‏+ اتجاهٌ ‏+ «اليومُ صاعد»."""
            if floor_on and _usd(b) < _floor():
                return False
            if cfg.get("inflow") and not _inflow(b):
                return False
            if cfg.get("above_open"):
                op = _day_open()
                if op is not None and float(b["c"]) < op:
                    return False
            return True

        ev = []
        anchor = st.get("anchor_ms")
        if not anchor:
            prior = [float(b["v"]) for b in closed[:-1]]
            avg = sum(prior) / len(prior) if prior else 0.0
            vx = (float(last["v"]) / avg) if avg > 0 else 0.0
            if vx < vm or not _ok(last, cfg.get("floor_anchor")):
                st["streak"] = 0
                return ([], st)
            need = int(cfg.get("consecutive") or 1)
            if need > 1:
                # ⏳ **دقيقتان متتاليتان:** تُحتسب المتتاليةُ ولا يُرسَل حتى تكتمل.
                run = int(st.get("streak") or 0) + 1
                if run < need:
                    st["streak"] = run
                    st["streak_ms"] = last_ms
                    return ([], st)
            st = {"anchor_ms": last_ms, "last_ms": last_ms, "sent": ["M1"],
                  "updates": 0, "vol_x": round(vx, 1),
                  "peak_usd": round(_usd(last))}
            ev.append({"stage": "M1", "usd": round(_usd(last)), "minutes": 1,
                       "anchor_ms": last_ms, "last_ms": last_ms,
                       "vol_x": round(vx, 1),
                       "price": round(float(last["c"]), 4),
                       "class": bot._ignition_candle_class(_usd(last))})
            return (ev, st)
        anchor = int(anchor)
        if last_ms > int(st.get("last_ms") or 0):
            st["last_ms"] = last_ms
            _u = _usd(last)
            _pk = float(st.get("peak_usd") or 0)
            _pass = _ok(last, cfg.get("floor_update"))
            if cfg.get("highwater") and _u <= _pk:
                _pass = False
            if _pass:
                if _u > _pk:
                    st["peak_usd"] = round(_u)
                if int(st.get("updates") or 0) < cap:
                    st["updates"] = int(st.get("updates") or 0) + 1
                    ev.append({"stage": "Mu", "usd": round(_u), "minutes": 1,
                               "anchor_ms": anchor, "last_ms": last_ms,
                               "vol_x": st.get("vol_x"),
                               "price": round(float(last["c"]), 4),
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


def replay(bars, cfg, window=None):
    """▶️ يُطعِم الشموعَ **دقيقةً مكتملةً في كلّ خطوة** ويجمع الأحداث.

    يرجّع قائمةَ `(k, event)` حيث `k` = فهرسُ آخرِ شمعةٍ مكتملةٍ رآها (‏= `k-2`
    في `bars`) — تُستعمل لقياس الأسبقيّة بالدقائق."""
    win = int(window or bot.LIQ_WINDOW_MIN)
    st, out = {}, []
    for k in range(3, len(bars) + 1):
        chunk = bars[max(0, k - win):k]
        evs, st = arm_events(chunk, st, cfg)
        for e in (evs or []):
            out.append((k - 2, e))
    return out


def session_ref(bars):
    """🕘 مرجعُ «المتحرّك» = **الجلسةُ النظاميّة** (‏09:30-16:00 نيويورك).

    الإعادةُ تُطعِم **كلَّ** الشموع (بريماركتَ وجلسةً) كما يفعل الحيُّ حرفيًّا،
    أمّا تعريفُ المتحرّك فيُقاس على الجلسة النظاميّة **ويُعلَن**. تعذّرُ المنطقة
    الزمنيّة ⇒ `None` ⇒ السهمُ **يُستبعَد من الاسترجاع ويُعَدّ** لا يُخمَّن."""
    try:
        from zoneinfo import ZoneInfo
        import datetime as _dt
        ny = ZoneInfo("America/New_York")
        reg = []
        for i, b in enumerate(bars or []):
            t = b.get("t")
            if t is None:
                continue
            d = _dt.datetime.fromtimestamp(int(t) / 1000, tz=ny)
            mn = d.hour * 60 + d.minute
            if 9 * 60 + 30 <= mn < 16 * 60:
                reg.append((i, b))
        if len(reg) < 5:
            return None
        i0, b0 = reg[0]
        op = float(b0.get("o") or b0["c"])
        if op <= 0:
            return None
        hi_i, hi = i0, float(b0.get("h") or b0["c"])
        for i, b in reg:
            h = float(b.get("h") or b["c"])
            if h > hi:
                hi, hi_i = h, i
        return {"open": op, "high": hi, "high_i": hi_i,
                "rise_pct": round((hi / op - 1.0) * 100.0, 2),
                "n_reg": len(reg)}
    except Exception:                                            # noqa: BLE001
        return None


def _lock_v4(fetch=None):
    """🔒 `LOCK-V4` — الذراعُ `V4` **بت-بت** مع الإنتاج على عيّناتٍ **مفرِّقة**.

    ثلاثُ حالاتٍ يجب أن تفرّق بين الأذرع (وإلّا كان القفلُ أعمى): دقيقةٌ ضخمةٌ
    داخلة · دقيقةٌ صغيرةٌ بقفزةٍ نسبيّة · وسلسلةٌ خابية. **وقفلٌ سالبٌ رابع**:
    لو ساوى `V0` مُخرَجَ `V4` على العيّنة الأولى فالعيّنةُ غيرُ مفرِّقة ⇒ يُوقَف."""
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
    ok, notes = True, []
    for name, bars in (("ضخمةٌ داخلة", big), ("صغيرةٌ نسبيّة", small),
                       ("سلسلةٌ خابية", fade)):
        mine = replay(bars, ARMS["V4"])
        prod, st = [], {}
        for k in range(3, len(bars) + 1):
            evs, st = bot.liq_stage_events(bars[max(0, k - bot.LIQ_WINDOW_MIN):k],
                                           st)
            for e in (evs or []):
                prod.append((k - 2, e))
        same = json.dumps(mine, sort_keys=True, default=str) == \
            json.dumps(prod, sort_keys=True, default=str)
        notes.append(f"{name}: مِجَسّ={len(mine)} إنتاج={len(prod)} "
                     f"{'✅' if same else '❌'}")
        ok = ok and same
    n0 = len(replay(small, ARMS["V0"]))
    n4 = len(replay(small, ARMS["V4"]))
    notes.append(f"عيّنةٌ مفرِّقة: V0={n0} · V4={n4} "
                 f"{'✅' if n0 > n4 else '❌'}")
    ok = ok and n0 > n4
    return ok, notes


def main():
    if not os.environ.get("POLYGON_API_KEY", "").strip():
        print("⛔ لا مفتاح Polygon — لا قياس (ولا يُخمَّن رقم).")
        return 2
    print("🔇 مِجَسُّ الضجيج LIQ-NOISE — عقدُه `liq_noise_prereg.md`\n")
    ok, notes = _lock_v4()
    for n in notes:
        print("   🔒 " + n)
    if not ok:
        print("\n⛔ `LOCK-V4` سقط: مقياسُ المِجَسّ تفرّق عن الإنتاج ⇒ **لا يُنشَر رقم**.")
        return 3
    print("   ✅ `LOCK-V4` عبر — المِجَسُّ يقيس بآلة الإنتاج نفسِها.\n")

    import operator_entry_live as oel
    try:
        _uni, _cut, _seen, uni_all = oel._load_universe()
    except Exception as e:                                       # noqa: BLE001
        print(f"⛔ تعذّر بناءُ الكون: {type(e).__name__}: {e}")
        return 2
    syms = [r["symbol"] for r in uni_all]
    print(f"👁️ الكون: {len(syms)} سهمًا (**بلا استثناء** — نفسُ كونِ المُشغِّل)\n")

    import concurrent.futures as cf
    t0 = time.time()
    data, fails = {}, 0

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

    # 🏃 المتحرّكون **من الشموع نفسِها** لا من قائمةٍ مختارةٍ بعد الحدث
    refs, movers, no_ref = {}, [], 0
    for s, bars in data.items():
        r = session_ref(bars)
        if r is None:
            no_ref += 1
            continue
        refs[s] = r
        if r["rise_pct"] >= MOVER_PCT:
            movers.append(s)
    print(f"🏃 متحرّكون (‏+{MOVER_PCT:.0f}% من الافتتاح): {len(movers)} — "
          f"{', '.join(sorted(movers)) if movers else 'لا أحد'}")
    print(f"   (بلا مرجعِ جلسةٍ نظاميّة: {no_ref} — مُستبعَدون من الاسترجاع "
          f"ويُعَدّون)\n")

    res = {}
    for arm, cfg in ARMS.items():
        per_sym, first_m1 = {}, {}
        total, stages = 0, {}
        for s, bars in data.items():
            evs = replay(bars, cfg)
            if not evs:
                continue
            per_sym[s] = len(evs)
            total += len(evs)
            for k, e in evs:
                stages[e["stage"]] = stages.get(e["stage"], 0) + 1
                if e["stage"] == "M1" and s not in first_m1:
                    first_m1[s] = k
        counts = sorted(per_sym.values())
        med = counts[len(counts) // 2] if counts else 0
        res[arm] = {"total": total, "syms": len(per_sym), "median": med,
                    "max": max(counts) if counts else 0, "stages": stages,
                    "m1": first_m1, "per_sym": per_sym}

    print("=" * 62)
    print("① الضجيج — إشعاراتٌ في الجلسة على الكون كلِّه")
    print("=" * 62)
    b = res["V0"]["total"] or 1
    for arm in ARMS:
        r = res[arm]
        cut = 100.0 * (1 - r["total"] / b)
        st = " · ".join(f"{k} {v}" for k, v in sorted(r["stages"].items()))
        print(f"  {arm} {ARM_DESC[arm]}")
        print(f"      إشعارات {r['total']:,} (قصٌّ {cut:.1f}% عن V0) · "
              f"أسهم {r['syms']} · وسيطٌ للسهم {r['median']} · أقصى {r['max']}")
        print(f"      المراحل: {st or '—'}")

    print("\n" + "=" * 62)
    print("② الاسترجاعُ والأسبقيّة على المتحرّكين")
    print("=" * 62)
    if len(movers) < MOVER_MIN_N:
        print(f"  ⚠️ **لا حكم على الاسترجاع**: {len(movers)} متحرّكًا دون "
              f"حدّ {MOVER_MIN_N} المسجَّل (‏§⑦-3) — الأرقامُ وصفيّةٌ لا حاكمة.")
    for arm in ARMS:
        r, hit, leads = res[arm], 0, []
        for s in movers:
            k = r["m1"].get(s)
            if k is None:
                continue
            hit += 1
            leads.append(refs[s]["high_i"] - k)
        leads.sort()
        lead_med = leads[len(leads) // 2] if leads else None
        print(f"  {arm}: أمسك {hit} من {len(movers)} · وسيطُ الأسبقيّة "
              + (f"{lead_med} دقيقة" if lead_med is not None else "—"))
    lost = [s for s in movers if res["V0"]["m1"].get(s) is not None
            and res["V4"]["m1"].get(s) is None]
    print(f"\n  🔴 متحرّكون أمسكتهم V0 وفقدتهم V4: {len(lost)}"
          + (f" — {', '.join(sorted(lost))}" if lost else " (لا أحد)"))
    if lost:
        print("  ⇒ **بنصّ التسجيل §④: يُبلَّغ المالكُ فورًا بالرقم** — أرضيتُه "
              "تكتم ما جاءت لتُمسكه.")

    print("\n" + "=" * 62)
    print("③ قاعدةُ القرار المسجَّلة — من يستبدل V4؟")
    print("=" * 62)
    v4 = res["V4"]
    v4_hit = {s for s in movers if v4["m1"].get(s) is not None}
    v4_leads = sorted(refs[s]["high_i"] - v4["m1"][s] for s in v4_hit)
    v4_med = v4_leads[len(v4_leads) // 2] if v4_leads else None
    for arm in ("V5", "V6", "V7"):
        r = res[arm]
        hit = {s for s in movers if r["m1"].get(s) is not None}
        c1 = r["total"] <= v4["total"]
        c2 = v4_hit <= hit
        both = sorted(v4_hit & hit)
        dl = sorted((refs[s]["high_i"] - v4["m1"][s])
                    - (refs[s]["high_i"] - r["m1"][s]) for s in both)
        dmed = dl[len(dl) // 2] if dl else 0
        c3 = dmed <= 1
        verd = "✅ يستبدل V4" if (c1 and c2 and c3) else "🔴 لا يستبدل"
        print(f"  {arm}: ضجيجٌ ليس أكثر {'✅' if c1 else '❌'} "
              f"({r['total']:,} مقابل {v4['total']:,}) · "
              f"لا يُفقِد متحرّكًا {'✅' if c2 else '❌'} "
              f"({len(hit)} مقابل {len(v4_hit)}) · "
              f"فقدُ الأسبقيّة {dmed} {'✅' if c3 else '❌'} ⇒ {verd}")
    print(f"\n  وسيطُ أسبقيّة V4 على المتحرّكين: "
          + (f"{v4_med} دقيقة" if v4_med is not None else "—"))

    print("\n" + "=" * 62)
    print("④ صنفُ فيصل الدولاريّ على إشعارات V4 (تنبّؤ `H5`)")
    print("=" * 62)
    cls = {}
    for s, bars in data.items():
        for _k, e in replay(bars, ARMS["V4"]):
            k, _d = (e.get("class") or ("—", ""))
            cls[k] = cls.get(k, 0) + 1
    tot4 = sum(cls.values()) or 1
    for k, v in sorted(cls.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v} ({100.0 * v / tot4:.1f}%)")
    print("\n  ⚠️ «دخلت سيولة» ليست «دخل المضارب» — والأولى قفزةُ حجمٍ بأرضيةٍ "
          "دولاريّة، والثانيةُ عتبةُ فيصل، وكلٌّ مطبوعٌ باسمه.")

    print("\n" + "=" * 62)
    print("⑤ كلفةُ الطبقة الخامسة (تأكيدُ المضارب) — تُقرأ ولا تُشغَّل")
    print("=" * 62)
    print(f"  نداءاتُ `operator_flow` = إشعاراتُ V4 = **{v4['total']:,}** في "
          f"الجلسة (‏{v4['syms']} سهمًا) — مقابل {res['V0']['total']:,} لو بلا "
          "بوّابةٍ ⇒ البوّابةُ هي ما جعل التأكيدَ رخيصًا.")

    print("\n" + "=" * 62)
    print("⑥ حدودُ صدقٍ (‏§⑦ — تُقرأ مع الأرقام لا بعدها)")
    print("=" * 62)
    print("  1. جلسةٌ واحدة ⇒ مِجَسُّ كلفةٍ لا تجربةَ حكم · لا عائدَ ولا دقّةَ "
          "مقيسة.")
    print("  2. «إشعارٌ على غير متحرّك» **بديلُ دقّةٍ لا دقّة** — قد تدخل سيولةٌ "
          "حقيقيّةٌ ولا يبلغ السهمُ +30%.")
    print(f"  3. المتحرّكون {len(movers)} (الحدُّ {MOVER_MIN_N}) · "
          f"وبلا مرجعِ جلسة {no_ref} · وتعذّرَ الجلبُ لـ{fails}.")
    print("  4. الجلسةُ قد تكون جاريةً ⇒ «القمّة» هي القمّةُ **حتى الآن**.")
    print("  5. والإعادةُ **سقفٌ** للضجيج: سقوطُ نداءٍ حيًّا يُنقص الإشعارَ لا "
          "يزيده.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
