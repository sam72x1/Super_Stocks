# -*- coding: utf-8 -*-
"""🧹 مِجَسّ «احذف المكرّر في عدّ التقسيم» المؤقّت (2026-09-23) — **قراءةٌ فقط · يُحذف قبل الدمج**.

على المجتمع الحقيقيّ نفسِه الذي قاسه مِجَسُّ R-02 (قائمةُ الصيّاد ‏+ سجلُّ حصاده) بسلسلة ياهو:
  ① كم رمزًا فيه سجلٌّ مكرّر (النسبةُ نفسها خلال `SPLIT_DUP_DAYS`) · بأسمائها وتواريخها.
  ② العدُّ الخام (منطقُ ما قبل الأمر، منسوخٌ هنا حرفيًّا) مقابل المدموج: على التاريخ كلِّه (R-02)
     وفي السنة (§P4) — ومَن **عبر الحدّ** (سطرُ R-02 · وسطرُ «تقسيمات متكررة»).
لا تلغرام · لا كتابة حالة · لا أسرار · لا كرون.
"""
import datetime as dt
import json
import os
import time

import Super_stock as S

T0 = time.time()
BUDGET_S = float(os.environ.get("PROBE_BUDGET_S", "540"))
TODAY = dt.date.today()


def _syms_of(obj):
    out = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("symbol", "sym", "ticker") and isinstance(v, str):
                out.add(v.upper())
            else:
                out |= _syms_of(v)
    elif isinstance(obj, list):
        for x in obj:
            out |= _syms_of(x)
    return out


def _load():
    hw, led = set(), set()
    try:
        hw = _syms_of(json.load(open("hunter_watchlist.json", encoding="utf-8")))
    except Exception as e:                                       # noqa: BLE001
        print(f"⛔ hunter_watchlist.json: {type(e).__name__}")
    try:
        for ln in open("hunter_ledger.jsonl", encoding="utf-8"):
            try:
                led |= _syms_of(json.loads(ln))
            except Exception:                                    # noqa: BLE001
                continue
    except Exception as e:                                       # noqa: BLE001
        print(f"⛔ hunter_ledger.jsonl: {type(e).__name__}")
    return sorted(hw) + sorted(led - hw)


def _raw_pairs(sp):
    """منطقُ ما قبل الأمر حرفيًّا: كلُّ صفٍّ عكسيّ (بلا دمج)."""
    out = []
    for ts, ratio in zip(sp.index, sp.values):
        try:
            d = ts.date() if hasattr(ts, "date") else ts
            r = float(ratio)
            if 0.0 < r < 1.0:
                out.append((d, r))
        except Exception:                                        # noqa: BLE001
            continue
    return out


def main():
    syms = _load()
    k = S.CONFIG["SPLIT_MANY_COUNT"]
    print(f"🧹 مِجَسّ المكرّر · اليوم {TODAY} · المجتمع {len(syms)} · SPLIT_DUP_DAYS={S.CONFIG['SPLIT_DUP_DAYS']} "
          f"· SPLIT_MANY_COUNT={k} · ميزانيّة {BUDGET_S:.0f}ث")
    n_ok, n_fail, skipped = 0, 0, 0
    dup_rows, cross_all, cross_yr = [], [], []
    tot_raw = tot_new = 0
    for sym in syms:
        if time.time() - T0 > BUDGET_S:
            skipped += 1
            continue
        sp = S._fetch_splits(sym)
        if sp is None:
            n_fail += 1
            continue
        n_ok += 1
        raw = _raw_pairs(sp)
        new = S._dedupe_reverse_splits(sp)
        a_raw = sum(1 for d, _ in raw if d <= TODAY)
        a_new = S.split_count_all(sp, TODAY)
        cut = TODAY - dt.timedelta(days=365)
        y_raw = sum(1 for d, _ in raw if cut <= d <= TODAY)
        y_new = S._split_frequency(sp, TODAY)
        tot_raw += a_raw
        tot_new += a_new
        if len(new) != len(raw):
            kept = {(str(d), round(r, 6)) for d, r in new}
            dropped = [(str(d), round(r, 6)) for d, r in raw if (str(d), round(r, 6)) not in kept]
            dup_rows.append((sym, a_raw, a_new, y_raw, y_new, dropped))
        if (a_raw > k) != (a_new > k):
            cross_all.append((sym, a_raw, a_new))
        if (y_raw >= 2) != (y_new >= 2):
            cross_yr.append((sym, y_raw, y_new))
    print(f"📊 قيس {n_ok} · تعذّر {n_fail} · **لم يُقَس لانتهاء الميزانيّة {skipped}**")
    print(f"📊 رموزٌ فيها سجلٌّ مكرّر: {len(dup_rows)} من {n_ok} · التقسيماتُ العكسيّة كلُّها: خام {tot_raw} ⟶ مدموج {tot_new}")
    for sym, a0, a1, y0, y1, dr in dup_rows:
        print(f"   🧹 {sym}: كلّ {a0}⟶{a1} · سنة {y0}⟶{y1} · المحذوف {dr}")
    print(f"📊 عبر حدّ سطر R-02 (فوق {k}): {len(cross_all)} — {cross_all}")
    print(f"📊 عبر حدّ سطر السنة (2 فأكثر): {len(cross_yr)} — {cross_yr}")
    print(f"⏱️ {time.time() - T0:.0f}ث")


if __name__ == "__main__":
    main()
