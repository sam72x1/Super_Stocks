#!/usr/bin/env python3
"""🎯🔎 مصيرُ تنبيهات «هنا الدخول» منذ 2026-10-27 — قراءةٌ فقط (أمرُ المالك 2026-10-28: «كل تنبيهات هنا الدخول منذ عودتها 10-27 …
ومصير كل واحد حتى اليوم من سجل المراسي — قراءة فقط، لا تغيير ولا تنبيه جديد»).

المدخلُ `op_alert_fate_input.json` (المراسي التي حملت `M1` في تاريخ git لـ`op_entry_state.json` ‏+ وسمُ كرت `M5` من
`tier_fwd_ledger.jsonl`). لكلّ مِرساة: شموعُ الدقيقة **غيرُ المسوّاة** من Polygon (`tier_fwd_report.fetch_day` بالاسم — بُنيت لحسم
صفوف السجلّ نفسِه بسعرها الخامّ) من يومها حتى اليوم ⟵ القمّةُ بعد المِرساة ووقتُها · أوّلُ بلوغٍ لـ‏+70% و‏+100% من سعر المِرساة ·
أوّلُ إغلاقِ دقيقةٍ دون قاع شمعة المِرساة (الخروجُ البنيويّ — تعريفُ `kasih_scan.resolve`) · وآخرُ سعر.
🔒 صفرُ إرسالٍ وصفرُ كتابةِ حالة · بلا كرون · ورمزُ الخروج 0 دائمًا إن قُرئ المدخل (2 بلا مدخلٍ أو مفتاح)."""
import datetime as dt
import json
import os
import sys
from zoneinfo import ZoneInfo

from tier_fwd_report import fetch_day

NY = ZoneInfo("America/New_York")
IN = os.environ.get("OP_FATE_INPUT", "op_alert_fate_input.json")


def et(ms):
    return dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc).astimezone(NY)


def fate(a, bars):
    """نقيّة: `bars` = `(t, o, h, l, c, v)` مرتّبةٌ تصاعديًّا (أيّامٌ متتالية). ترجّع قاموسَ المصير أو `None` بلا شموعٍ بعد المِرساة."""
    p0, low = float(a["anchor_price"]), a.get("anchor_low")
    after = [b for b in bars or [] if b[0] >= int(a["anchor_ms"])]
    if not after or p0 <= 0:
        return None
    pk = max(after, key=lambda b: b[2])
    out = {"peak": pk[2], "peak_et": et(pk[0]).strftime("%m-%d %H:%M"), "peak_pct": round((pk[2] / p0 - 1) * 100, 1),
           "last": after[-1][4], "last_et": et(after[-1][0]).strftime("%m-%d %H:%M"),
           "last_pct": round((after[-1][4] / p0 - 1) * 100, 1), "hit70_et": None, "hit100_et": None, "exit_et": None,
           "hit70_before_exit": None}
    ex_t = None
    for b in after:
        if out["hit70_et"] is None and b[2] >= p0 * 1.7:
            out["hit70_et"] = et(b[0]).strftime("%m-%d %H:%M")
            h70 = b[0]
        if out["hit100_et"] is None and b[2] >= p0 * 2.0:
            out["hit100_et"] = et(b[0]).strftime("%m-%d %H:%M")
        if ex_t is None and low is not None and b[4] < float(low):
            ex_t = b[0]
            out["exit_et"] = et(b[0]).strftime("%m-%d %H:%M")
    if out["hit70_et"] is not None:
        out["hit70_before_exit"] = (ex_t is None) or (h70 < ex_t)
    return out


def main(get=None) -> int:
    try:
        rows = json.load(open(IN, encoding="utf-8"))["anchors"]
    except Exception as e:                                       # noqa: BLE001
        print(f"⛔ لا مدخل `{IN}`: {e}")
        return 2
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key and get is None:
        print("⛔ لا `POLYGON_API_KEY`")
        return 2
    today = dt.datetime.now(NY).date()
    cache, res = {}, []
    for a in rows:
        d0 = dt.date.fromisoformat(a["day"])
        bars = []
        d = d0
        while d <= today:
            if d.weekday() < 5:
                k = (a["sym"], d.isoformat())
                if k not in cache:
                    cache[k] = fetch_day(a["sym"], d.isoformat(), key, get=get)
                bars += cache[k] or []
            d += dt.timedelta(days=1)
        f = fate(a, sorted(bars))
        res.append(dict(a, fate=f))
    miss = sum(1 for r in res if r["fate"] is None)
    print(f"📦 مراسي: {len(res)} · بلا شموعٍ بعد المِرساة: {miss} · أيّامٌ مجلوبة: {len(cache)} (فشل {sum(1 for v in cache.values() if not v)})")
    print("الرمز | اليوم | وقتُ المِرساة ET | الجلسة | سعرُها | كرت M5 | التصنيف | J1 | القمّة % (وقتُها) | +70% | +100% | الخروج | آخر % (وقتُه)")
    for r in res:
        f = r["fate"] or {}
        print(" | ".join(str(x) for x in (
            r["sym"], r["day"], r["anchor_et"], r["session"], r["anchor_price"], "نعم" if r.get("m5_card") else "لا",
            r.get("tier") or "—", ("J1⭐" if r.get("j1_top") else "J1" if r.get("j1") else "—"),
            (f"{f.get('peak_pct')}% ({f.get('peak_et')})" if f else "—"), f.get("hit70_et") or "—", f.get("hit100_et") or "—",
            f.get("exit_et") or "—", (f"{f.get('last_pct')}% ({f.get('last_et')})" if f else "—"))))
    print("OPFATE_JSON " + json.dumps(res, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
