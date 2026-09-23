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


ROLLING = {"hist_n", "dist_low20", "dist_high20", "down_streak", "spike60",
           "days_since_spike", "usd_rel20"}


def outside_details(po, pn, zone, days_idx, limit=80):
    """الجولةُ الثانية (تشخيص): لكلّ صفٍّ متغيّرٍ خارج المنطقة — الرمز · الجلسة · الحقولُ المتغيّرة
    بقيمها · وعددُ أيّامِ ظهور الرمز في صفوف `AH` بين أقرب D قبله واليوم (مقابل الجلسات)."""
    out = []
    it_o, it_n = EA.iter_days(EA.read_rows(po)), EA.iter_days(EA.read_rows(pn))
    o, n = next(it_o, None), next(it_n, None)
    while o is not None and n is not None:
        if o[0] != n[0]:
            if str(o[0]) < str(n[0]):
                o = next(it_o, None)
            else:
                n = next(it_n, None)
            continue
        d = o[0]
        if d not in zone:
            for k in o[1].keys() & n[1].keys():
                a, b = o[1][k], n[1][k]
                if a != b:
                    ks = sorted(f for f in set(a) | set(b) if a.get(f) != b.get(f))
                    out.append((d, k, ks, {f: (a.get(f), b.get(f)) for f in ks}))
        o, n = next(it_o, None), next(it_n, None)
    return out[:limit]


def presence(pn, syms, d0, d1):
    """{رمز: عددُ الأيّام التي له فيها صفُّ AH بين d0 وd1 شاملًا}."""
    cnt = {s: set() for s in syms}
    for r in EA.read_rows(pn):
        d = str(r.get("day"))
        if d0 <= d <= d1 and r.get("sess") == "AH" and r.get("sym") in cnt:
            cnt[r["sym"]].add(d)
    return {s: len(v) for s, v in cnt.items()}


def main() -> int:
    old_dir = (os.environ.get("EARLY_OLD_DIR") or "").strip()
    new_dir = (os.environ.get("EARLY_NEW_DIR") or "").strip()
    days = trading_days("2022-11-01", "2025-12-31")
    idx = {d: i for i, d in enumerate(days)}
    zone = zone_of(days, EA.PINNED_EARLY)
    only_rolling = True
    for y in ("2023", "2024"):
        po, pn = EA.year_file(old_dir, y), EA.year_file(new_dir, y)
        det = outside_details(po, pn, zone, idx)
        print(f"🔎 {y}: صفوفٌ متغيّرةٌ خارج المنطقة (أوّلُ 80): {len(det)}")
        fset = {}
        for d, k, ks, vals in det:
            for f in ks:
                fset[f] = fset.get(f, 0) + 1
            if not set(ks) <= ROLLING:
                only_rolling = False
        print(f"   الحقولُ المتغيّرة فيها: {fset}")
        syms = sorted({k[2] for _d, k, _ks, _v in det})
        for sym in syms:
            ds = sorted(d for d, k, _ks, _v in det if k[2] == sym)
            D = max((e for e in EA.PINNED_EARLY if e <= ds[0]), default=None)
            pres = presence(pn, [sym], D, ds[-1]).get(sym) if D else None
            print(f"   {sym}: أيّامٌ متغيّرة {len(ds)} ({ds[0]} … {ds[-1]}) · أقربُ D قبلها {D} · "
                  f"جلساتُ السوق من D حتى آخرها {idx[ds[-1]] - idx[D] + 1 if D else '—'} · "
                  f"أيّامُ صفوف AH للرمز فيها {pres}")
        for d, k, ks, vals in det[:12]:
            print(f"   · {d} {k[1]} {k[2]}: " + " · ".join(f"{f} {v[0]}→{v[1]}" for f, v in vals.items()))
    print(f"JUDGE_OUTSIDE only_rolling_fields={only_rolling}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
