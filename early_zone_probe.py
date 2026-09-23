"""🧪 مِجَسٌّ مؤقّت — **يُحذف بعد القراءة** (نمطُ «مِجَسّ Actions مؤقّت»).

`V-E2` بنصّ العقد (`early_close_prereg.md §③`): **صفرُ صفٍّ متغيّرٍ في أيّ يومٍ خارج
منطقة الأثر** — ومنطقةُ الأثر = من كلّ يومِ إغلاقٍ مبكّر D حتى الجلسة الستّين بعده
(‏`ROLL_N`) · وأوّلُ يومٍ بعدها.

⚖️ لماذا: أداةُ التدقيق طبّقت `V-E2` **نافذتَي ضبطٍ** فقط (‏2023-H1 · 2024-01-01..07-02)
= ثلثُ الأيّام — والعقدُ يطلب كلَّ يومٍ خارج المنطقة. هذا المِجَسّ يسدّ الفرق على صفوف
التشغيلة `35907136622` مقابل المسوح المنشورة، **بدوالّ الأداة نفسِها** (`diff_streams`).
🔒 قراءةٌ فقط: لا كتابةَ في المستودع · لا إرسال · لا سرّ.
"""
from __future__ import annotations

import datetime as dt
import os
import sys

import early_close_audit as EA
import market_calendar as MC

ROLL_N = 60                       # = presession_feats.ROLL_N (العقد §③)
SPAN = ROLL_N + 1                 # «حتى الجلسة الستّين بعده · وأوّلُ يومٍ بعدها»


def trading_days(d0: str, d1: str) -> list:
    out, d, e = [], dt.date.fromisoformat(d0), dt.date.fromisoformat(d1)
    while d <= e:
        s = d.isoformat()
        if d.weekday() < 5 and MC.session_info(s).get("open_ny_min") is not None:
            out.append(s)
        d += dt.timedelta(days=1)
    return out


def zone_of(days: list, early) -> dict:
    """{يوم: (D الأقرب قبله · بُعدُه بالجلسات)} لكلّ يومٍ داخل منطقة أثر يومٍ مبكّر."""
    idx = {d: i for i, d in enumerate(days)}
    z = {}
    for D in early:
        i = idx.get(D)
        if i is None:
            continue
        for j in range(i, min(i + SPAN + 1, len(days))):
            k = days[j]
            if k not in z or (j - i) < z[k][1]:
                z[k] = (D, j - i)
    return z


def main() -> int:
    old_dir = (os.environ.get("EARLY_OLD_DIR") or "").strip()
    new_dir = (os.environ.get("EARLY_NEW_DIR") or "").strip()
    days = trading_days("2022-11-01", "2025-12-31")
    zone = zone_of(days, EA.PINNED_EARLY)
    print(f"🧪 V-E2 الكامل · منطقةُ الأثر = D ⟶ +{ROLL_N} جلسة · وأوّلُ يومٍ بعدها "
          f"(‏{SPAN + 1} جلسة لكلّ D) · أيّامُ المنطقة داخل 2023-2025: "
          f"{sum(1 for d in zone if d >= '2023-01-01')}")
    tot_in = tot_out = 0
    outside, far = [], {}
    for y in EA.YEARS:
        po, pn = EA.year_file(old_dir, y), EA.year_file(new_dir, y)
        if not po or not pn:
            print(f"⛔ ملفّ {y} غائب (قديم={po} · جديد={pn}) ⇒ خروج 4")
            return 4
        per = EA.diff_streams(EA.read_rows(po), EA.read_rows(pn))
        hit = sorted(d for d, v in per.items() if v["added"] or v["removed"] or v["changed"])
        y_in = [d for d in hit if d in zone]
        y_out = [d for d in hit if d not in zone]
        tot_in += len(y_in)
        tot_out += len(y_out)
        outside += [(d, per[d]["added"], per[d]["removed"], per[d]["changed"]) for d in y_out]
        for d in y_in:
            D, k = zone[d]
            far[D] = max(far.get(D, 0), k)
        rows_out = sum(per[d]["changed"] + per[d]["added"] + per[d]["removed"] for d in y_out)
        print(f"   {y}: أيّامٌ مقروءة {len(per)} · تفرّقت {len(hit)} · داخل المنطقة {len(y_in)} · "
              f"خارجها {len(y_out)} (صفوف {rows_out})")
    print("   أبعدُ يومٍ متفرّقٍ لكلّ D (بالجلسات بعده):",
          " · ".join(f"{D}=+{far[D]}" for D in sorted(far)) or "—")
    for d, a, r, c in outside[:40]:
        print(f"   ⚠️ خارج المنطقة: {d} · مضاف {a} · محذوف {r} · متغيّر {c}")
    ok = tot_out == 0
    print(f"JUDGE_VE2_FULL days_in_zone={tot_in} days_outside={tot_out} ⇒ "
          f"{'✅ الفرقُ كلُّه داخل منطقة الأثر' if ok else '🔴 فرقٌ خارج المنطقة — الإسنادُ مقيَّد'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
