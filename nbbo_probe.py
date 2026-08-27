#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📡🩺 مِجَسُّ جدوى NBBO لقياس تعبئة الوقف — **تشخيصٌ لا تجربةَ حكم**.

سابقةُ `nbbo_history_verdict` و`flatfiles_probe` و`wall_stack`: مِجَسُّ جدوى
**بلا تسجيلٍ مسبق وبسقفِ نجاحٍ صفر** — يجيب «هل يمكن القياسُ أصلًا وبأيّ
كلفة؟» ولا يطبع **ولا رقمَ نتيجةٍ واحدًا** (لا `R` ولا سعرَ تعبئةٍ ولا فارقًا).

**أربعةُ أسئلةٍ تصميميّةٍ لا تُخمَّن:**
① كثافةُ الاقتباسات في **دقيقةِ الزناد** ⇒ أيُّ `limit` يمنع القصَّ الصامت؟
② هل `/v3/trades` يحمل **طابعًا زمنيًّا** (‏`hist_trades` يُسقطه) ⇒ هل يمكن
   تحديدُ لحظة الزناد بالمِلّي بدل تخمينِ موضعٍ داخل الدقيقة؟
③ **مقياسُ الخام مقابل المعدَّل:** الشموعُ `adjusted=true` والاقتباسات/الصفقات
   **خام** ⇒ كم يبلغ الفرق؟ (حارسُ `scale_ok` القائم يقارن معدَّلًا بمعدَّل
   فلا يلتقط هذا).
④ زمنُ النداء ⇒ هل تُنجَز سنةٌ داخل سقف الجوب؟

قراءةٌ فقط · خارج الفرز · الإنتاجُ لا يستوردها · لا `LOGIC_VERSION`.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request

KEY = os.environ.get("POLYGON_API_KEY") or ""
N_SYMS = int(os.environ.get("NBP_SYMS") or 400)
N_EV = int(os.environ.get("NBP_EVENTS") or 30)
QLIMIT = int(os.environ.get("NBP_QLIMIT") or 25000)


def _log(m):
    print(m, flush=True)


def _raw(path, params):
    """نداءٌ خامّ ليُطبَع **شكلُ الحقول الحقيقيّ** لا المفترَض (wire-check §①)."""
    p = dict(params)
    p["apiKey"] = KEY
    url = "https://api.polygon.io" + path + "?" + urllib.parse.urlencode(p)
    req = urllib.request.Request(url, headers={"User-Agent": "nbbo-probe"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def main() -> int:                                               # noqa: C901
    if not KEY:
        _log("⛔ لا POLYGON_API_KEY ⇒ خروج 4.")
        return 4
    import Super_stock as S                                      # noqa: PLC0415
    import rebound_arms as RB                                    # noqa: PLC0415
    import gold_entry_arms as GE                                 # noqa: PLC0415
    import slip_arms as SL                                       # noqa: PLC0415
    from datetime import datetime, timezone                      # noqa: PLC0415
    import event_exec as EX                                      # noqa: PLC0415

    year = (os.environ.get("BACKTEST_YEAR") or "?").strip()
    path = os.environ.get("BT_FROZEN_PATH") or "frozen_backtest.pkl.gz"
    _log(f"\n{'=' * 78}\n📡🩺 مِجَسُّ جدوى NBBO — سنة {year} "
         f"(‏تشخيصٌ فقط · صفرُ رقمِ نتيجة)\n{'=' * 78}")
    if not os.path.exists(path):
        _log(f"⛔ اللقطةُ مفقودة ({path!r}) ⇒ خروج 2.")
        return 2
    hist, _sp, asof = S.load_frozen_dataset(path)
    _log(f"📦 لقطة as-of {asof} · رموز {len(hist)} · نمشي {N_SYMS} رمزًا")

    # ① أحداثُ وقفٍ حقيقيّة (نفسُ محرّك T-SLIP بالاسم — لا منطقَ منسوخ)
    yr = year if year and year != "?" else None
    evs, n = [], 0
    for sym, df in hist.items():
        if df is None or len(df) < RB.MIN_BARS + 5:
            continue
        n += 1
        for e in GE.walk_symbol_gold(sym, df, year=yr, with_plan=True):
            for a in SL.PARMS:
                p = (e.get("plan") or {}).get(a) or {}
                if e[a][0] and e[a][1] == "loss" and p.get("date"):
                    evs.append((sym, p["date"], float(p["stop"]), a))
        if n >= N_SYMS or len(evs) >= N_EV * 4:
            break
    _log(f"🩸 أحداثُ وقفٍ مرشَّحة: {len(evs)} (من {n} رمزًا)")
    if not evs:
        _log("⛔ صفرُ حدث ⇒ خروج 4 (بصمةُ الـ`no-op`).")
        return 4

    dens, lat_q, lat_t, ratios, trunc, no_q, no_t = [], [], [], [], 0, 0, 0
    ts_field, sizes_seen, tick, shown = None, 0, 0, 0
    seen = set()
    for sym, day, stop, arm in evs:
        key = (sym, day)
        if key in seen:
            continue
        bars = SL.fetch_day(sym, day)
        if not bars:
            continue
        sess = SL.session_slice(bars)
        if not sess:
            continue
        k = SL.trigger_index(sess, stop)
        if k is None:
            continue
        seen.add(key)
        b = sess[k]
        t0 = int(b["t"])
        t1 = t0 + 60_000
        # ② الاقتباسات — نداءٌ خامّ لطباعة الحقول الحقيقيّة
        s = time.time()
        try:
            jq = _raw(f"/v3/quotes/{sym}", {
                "timestamp.gte": t0 * 1_000_000, "timestamp.lt": t1 * 1_000_000,
                "order": "asc", "sort": "timestamp", "limit": QLIMIT})
        except Exception as _e:                                  # noqa: BLE001
            _log(f"   ⚠️ {sym} {day}: اقتباساتٌ رمت {type(_e).__name__}")
            continue
        lat_q.append(time.time() - s)
        qs = jq.get("results") or []
        if not qs:
            no_q += 1
            continue
        dens.append(len(qs))
        if len(qs) >= QLIMIT:
            trunc += 1
        if ts_field is None:
            ts_field = sorted(qs[0].keys())
        sizes_seen += sum(1 for q in qs if q.get("bid_size") is not None)
        # ③ الصفقات — هل فيها طابعٌ زمنيّ؟ وما مقياسُها مقابل الشمعة المعدَّلة؟
        s = time.time()
        try:
            jt = _raw(f"/v3/trades/{sym}", {
                "timestamp.gte": t0 * 1_000_000, "timestamp.lt": t1 * 1_000_000,
                "order": "asc", "sort": "timestamp", "limit": 5000})
        except Exception:                                        # noqa: BLE001
            jt = {}
        lat_t.append(time.time() - s)
        tr = jt.get("results") or []
        if not tr:
            no_t += 1
        else:
            if tick == 0:
                _log(f"   🔑 حقولُ الصفقة الحقيقيّة: {sorted(tr[0].keys())}")
                tick = 1
            ps = [float(t["price"]) for t in tr if t.get("price")]
            if ps and b["l"] > 0:
                ratios.append(min(ps) / float(b["l"]))
        if shown < 3:
            shown += 1
            _log(f"   • {sym} {day} د{k}: اقتباسات={len(qs)} صفقات={len(tr)}")
        if len(dens) >= N_EV:
            break

    _log(f"\n🔑 حقولُ الاقتباس الحقيقيّة: {ts_field}")
    if dens:
        v = sorted(dens)
        m = v[len(v) // 2]
        _log(f"\n① كثافةُ الاقتباسات في دقيقة الزناد (ن={len(v)}): "
             f"أدنى={v[0]} · وسيط={m} · p90={v[min(len(v)-1, int(0.9*(len(v)-1)))]}"
             f" · أقصى={v[-1]} · بلغ سقفَ {QLIMIT}: {trunc}")
        _log(f"   ↳ وحجمُ الطلب حاضرٌ في {sizes_seen} اقتباسًا من "
             f"{sum(dens)} = {100.0*sizes_seen/max(sum(dens),1):.1f}%")
    _log(f"② صفرُ اقتباس: {no_q} · صفرُ صفقة: {no_t}")
    if ratios:
        r = sorted(ratios)
        near = sum(1 for x in r if abs(x - 1.0) <= 0.02)
        _log(f"③ مقياسُ الخام مقابل المعدَّل (أدنى صفقةٍ ÷ قاع الشمعة · ن={len(r)}):"
             f" أدنى={r[0]:.4f} · وسيط={r[len(r)//2]:.4f} · أقصى={r[-1]:.4f}"
             f" ⇒ داخلَ ‏2%: {near} من {len(r)} = {100.0*near/len(r):.1f}%")
    if lat_q:
        _log(f"④ زمنُ النداء: اقتباسات وسيطًا {sorted(lat_q)[len(lat_q)//2]:.2f}ث"
             f" · صفقات {sorted(lat_t)[len(lat_t)//2]:.2f}ث"
             f" ⇒ نافذةٌ واحدةٌ ‏≈{sorted(lat_q)[len(lat_q)//2] + (sorted(lat_t)[len(lat_t)//2] if lat_t else 0):.2f}ث")
    _log("\n⚠️ مِجَسُّ جدوى: صفرُ رقمِ نتيجةٍ هنا — لا تعبئةَ ولا `R` ولا فارق."
         " الحكمُ يلزمه تسجيلٌ مسبقٌ مدفوعٌ قبل أيّ رقم.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
