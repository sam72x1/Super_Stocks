#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🧱🕵️ مِجَسّ «جدار الطلبات الملغى» — تحقيقٌ من NBBO التاريخيّ (‏/v3/quotes).

**مِجَسّ تشخيصيّ لا تجربة حكم** (سابقة `nbbo_history_verdict`/`wall_stack`) ⇒ بلا
تسجيلٍ مسبق، وقراءةٌ فقط: لا كتابةَ حالة، لا تلغرام، لا مسَّ فرز.

**الحالة المؤسِّسة (‏2026-08-19، لقطة المالك):** شهادة الغامدي على `$ZCMD`:
«المضارب **ثبّته على طلب 270 ألف سهم** يوم الجمعة **وفجأة ألغاه** وباعوا العالم
وهبط سنتات» — ثم مُسح ستوبُنا ($0.93) الاثنين واستعاد السعرُ فوق القاع.
**السؤال:** هل يظهر الجدارُ وإلغاؤه في قمّة الدفتر (NBBO) التاريخيّة؟

**ما يجيبه:** أكبرُ عرضِ طلبٍ (bid) مثبَّتٍ عند سعرٍ واحد: حجمُه · مدّتُه ·
لحظةُ اختفائه · وكم سهمًا **طُبع فعلًا** عند سعره وقتَ حياته (طبعاتٌ قليلة +
اختفاءٌ فجائيّ = **أُلغي لا أُكل**) · ومسارُ السعر بعده (شموع الدقيقة).

⚠️ **حدود صدق مطبوعة مع النتيجة:**
- NBBO = **قمّة الدفتر فقط** — جدارٌ تحت أفضل طلبٍ لا يُرى حتى يصير هو الأفضل.
- «أُلغي/أُكل» **استنتاجٌ** من فرق (الحجم المعروض − المطبوع) لا شهادةُ دفتر أوامر.
- **وحدة الحجم تُطبَع خامًا وبكلا التفسيرين** (أسهم / لوتات×100) — لا تُفترَض.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request

SYM = os.environ.get("PROBE_SYMBOL", "ZCMD").strip().upper()
DAY = os.environ.get("PROBE_DATE", "2026-08-14").strip()
KEY = os.environ.get("POLYGON_API_KEY", "").strip()
PAGE_CAP = int(os.environ.get("PROBE_PAGE_CAP", "40"))     # 40×50k = 2م اقتباس كحدّ
TOP_N = 12


def _get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "wall-probe/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def _paged(path: str, params: dict, key_results="results"):
    out = []
    base = "https://api.polygon.io"
    params = dict(params)
    params["apiKey"] = KEY
    url = base + path + "?" + urllib.parse.urlencode(params)
    pages = 0
    while url and pages < PAGE_CAP:
        d = _get(url)
        out.extend(d.get(key_results) or [])
        nxt = d.get("next_url")
        url = (nxt + "&apiKey=" + KEY) if nxt else None
        pages += 1
    return out, pages


def _ny_ts(ms):
    """طابع نيويورك المقروء من ملّي ثانية UTC (فرق الصيف −4)."""
    t = dt.datetime.utcfromtimestamp(ms / 1000.0) - dt.timedelta(hours=4)
    return t.strftime("%H:%M:%S")


def main() -> int:
    if not KEY:
        print("⛔ لا POLYGON_API_KEY — المِجَسّ يلزمه المفتاح. خروج 4.")
        return 4
    day0 = dt.datetime.fromisoformat(DAY)
    lo_ns = int(day0.replace(hour=0).timestamp() * 1e9)
    hi_ns = int((day0 + dt.timedelta(days=1)).timestamp() * 1e9)
    print(f"🧱🕵️ مِجَسّ الجدار الملغى · {SYM} · {DAY} (اليوم كاملًا بريماركت→أفتر)")

    # ① الاقتباسات
    quotes, qp = _paged(f"/v3/quotes/{SYM}", {
        "timestamp.gte": lo_ns, "timestamp.lt": hi_ns,
        "order": "asc", "limit": 50000, "sort": "timestamp"})
    print(f"   📡 اقتباسات NBBO: {len(quotes)} (صفحات {qp}"
          + (" — ⚠️ بلغ سقف الصفحات، الذيل مقصوص مُعلَنًا" if qp >= PAGE_CAP else "") + ")")
    if not quotes:
        print("⛔ صفر اقتباس — إمّا رمز/يوم خطأ وإمّا المنفذ مرفوض. خروج 3.")
        return 3

    # ② تجميع «جلسات الجدار»: فتراتٌ متّصلة يكون فيها أفضلُ طلبٍ نفسَ (سعر، حجم كبير)
    #    نلتقط لكلّ (سعر طلب) أقصى حجمٍ شوهد + آخر لحظة كان فيها الأفضل.
    walls = {}      # bid_price -> dict
    prev_bid = None
    for q in quotes:
        bp, bs, ts = q.get("bid_price"), q.get("bid_size"), q.get("sip_timestamp")
        if bp is None or bs is None or ts is None:
            continue
        ms = ts / 1e6
        w = walls.setdefault(round(float(bp), 4), {
            "max_size": 0, "first_ms": ms, "last_ms": ms, "n_quotes": 0})
        w["n_quotes"] += 1
        w["last_ms"] = ms
        if bs > w["max_size"]:
            w["max_size"] = bs
        prev_bid = (bp, bs, ms)

    top = sorted(walls.items(), key=lambda kv: -kv[1]["max_size"])[:TOP_N]
    print(f"\n   🧱 أكبر أحجام طلبٍ شوهدت على قمّة الدفتر (أعلى {TOP_N}):")
    print("      سعر الطلب | أقصى حجم (خام) | لو لوتات×100 | أوّل ظهور | آخر ظهور | عدد اللقطات")
    for bp, w in top:
        print(f"      ${bp:<8} | {w['max_size']:>10,} | {w['max_size']*100:>12,} | "
              f"{_ny_ts(w['first_ms'])} | {_ny_ts(w['last_ms'])} | {w['n_quotes']:,}")

    # ③ الجدار الأكبر: ماذا طُبع عند سعره خلال حياته؟ (أُكل أم أُلغي؟)
    if top:
        wp, w = top[0]
        t_lo = int(w["first_ms"] * 1e6)
        t_hi = int((w["last_ms"] + 60_000) * 1e6)   # +دقيقة بعد آخر ظهور
        trades, tp = _paged(f"/v3/trades/{SYM}", {
            "timestamp.gte": t_lo, "timestamp.lt": t_hi,
            "order": "asc", "limit": 50000, "sort": "timestamp"})
        at_wall = [t for t in trades
                   if t.get("price") is not None
                   and abs(float(t["price"]) - wp) < 0.0005]
        sh_at_wall = sum(int(t.get("size") or 0) for t in at_wall)
        sh_all = sum(int(t.get("size") or 0) for t in trades)
        print(f"\n   🔍 الجدار الأكبر ${wp} (أقصى حجم خام {w['max_size']:,}):")
        print(f"      خلال حياته (+60ث): صفقات كلّية {len(trades)} بمجموع {sh_all:,} سهم · "
              f"منها **عند سعر الجدار** {len(at_wall)} صفقة بمجموع {sh_at_wall:,} سهم")
        for unit, factor in (("أسهم", 1), ("لوتات×100", 100)):
            wall_sh = w["max_size"] * factor
            eaten = (100.0 * sh_at_wall / wall_sh) if wall_sh else 0.0
            verdict = "أُكل غالبًا" if eaten >= 60 else ("جزئيّ" if eaten >= 20 else "أُلغي غالبًا (طبعاتٌ قليلة ثم اختفى)")
            print(f"      بوحدة {unit}: الجدار {wall_sh:,} سهم ⇒ طُبع {eaten:.1f}% منه ⇒ {verdict}")

    # ④ مسار السعر: شموع الدقيقة لليوم + اليومان التاليان (المسح والاستعادة)
    d_end = (day0 + dt.timedelta(days=4)).date().isoformat()
    aggs, _ = _paged(f"/v2/aggs/ticker/{SYM}/range/1/minute/{DAY}/{d_end}",
                     {"limit": 50000, "sort": "asc"})
    if aggs:
        by_day = {}
        for a in aggs:
            d = dt.datetime.utcfromtimestamp(a["t"] / 1000.0).date().isoformat()
            r = by_day.setdefault(d, {"o": a["o"], "h": a["h"], "l": a["l"],
                                      "c": a["c"], "v": 0})
            r["h"] = max(r["h"], a["h"])
            r["l"] = min(r["l"], a["l"])
            r["c"] = a["c"]
            r["v"] += a.get("v") or 0
        print("\n   📉 مسار الأيام (من دقائق Polygon، UTC-يوم تقريبًا):")
        for d in sorted(by_day):
            r = by_day[d]
            print(f"      {d}: فتح {r['o']} · أعلى {r['h']} · أدنى {r['l']} · "
                  f"إغلاق {r['c']} · حجم {r['v']:,.0f}")

    print("\n⚠️ حدود الصدق: NBBO قمّةُ الدفتر فقط · «أُلغي/أُكل» استنتاجٌ من فرق "
          "المعروض والمطبوع · ووحدة الحجم مطبوعة بالتفسيرين ولا تُفترَض.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
