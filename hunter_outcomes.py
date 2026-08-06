#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📏 `hunter_outcomes` — يحسم مرشّحي السجلّ بعد انقضاء نافذتهم، ويقيس **الشاهد**.

**العقد:** `harvest_prereg.md` (مدفوعٌ قبل جمع صفٍّ واحد).

**الطريقة:** يقرأ `hunter_ledger.jsonl` ⟶ يأخذ مَن لم يُحسم ⟶ يجلب شموعَه ⟶ يقصّ
**ما بعد جلسة الرصد حصرًا** ⟶ `LEDGER.score` ⟶ يكتب الحكم. ثم يبني **الشاهد**
(`ctb_harvest.control_panel` الحتميّة) **للجلسات نفسها** ويقيسه **بالقاعدة نفسها**.

🔒 **قياسٌ فقط:** لا يمسّ صيّادًا ولا فرزًا ولا جذرًا · بلا تلغرام · ولا يقترح رقمًا —
يطبع الملخّصَ بفواصل Wilson **والحكمُ بقاعدة التسجيل لا برأيه**.

⚠️ **ولا حكمَ قبل بلوغ العتبات المسجَّلة** — يُطبَع «لا حكم» صراحةً مع الأرقام.
"""
from __future__ import annotations

import datetime as dt
import math
import os
import sys

import hunter_ledger as LEDGER

CONTROL_PER_SESSION = 25      # حجمُ لوحة الشاهد لكل جلسة
MIN_RESOLVED = 30             # عتبةُ الحكم لكل صيّاد (‏§③)
MIN_AGGREGATE = 150           # عتبةُ الحكم المجمَّع


def wilson(k: int, n: int, z: float = 1.96):
    """فاصلُ Wilson 95% — نفسُ الآلة المستعملة في كل تجارب المستودع."""
    if n <= 0:
        return (0.0, 1.0)
    p = k / n
    d = 1.0 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def after_session(df, session):
    """✂️ قممُ الجلسات **التالية** لجلسة الرصد حصرًا — لا الجلسةَ نفسها.

    🔒 هذا هو الموضعُ الوحيد الذي يمنع تسريبًا: لو ضُمّت جلسةُ الرصد لصار جزءٌ من
    الحركة معلومًا وقتَ الرصد. مقفولٌ باختبار."""
    try:
        d0 = dt.date.fromisoformat(str(session)[:10])
    except Exception:                                            # noqa: BLE001
        return []
    out = []
    try:
        for ts, hi in zip(df.index, df["High"].values):
            if ts.date() > d0:
                out.append(float(hi))
    except Exception:                                            # noqa: BLE001
        return []
    return out


def resolve(rows, fetch_hist, log=None) -> dict:
    """يحسم ما انقضت نافذتُه. يُرجع `{key: outcome}`."""
    todo = LEDGER.pending(rows)
    if not todo:
        return {}
    syms = sorted({r["symbol"] for r in todo})
    if log:
        log(f"📏 بانتظار الحسم: {len(todo)} صفًّا · {len(syms)} رمزًا")
    hist = {}
    try:
        hist = fetch_hist(syms) or {}
    except Exception as e:                                       # noqa: BLE001
        if log:
            log(f"⚠️ تعذّر جلبُ الشموع ({e}) — لا حسمَ هذي المرّة.")
        return {}
    out, not_yet, missing = {}, 0, 0
    for r in todo:
        df = hist.get(r["symbol"])
        if df is None or not len(df):
            missing += 1
            continue
        oc = LEDGER.score(r.get("ref_close"), after_session(df, r.get("session")))
        if oc.get("resolved"):
            out[r["key"]] = oc
        else:
            not_yet += 1
    if log:
        log(f"   ⇒ حُسم {len(out)} · لم تنقضِ نافذتُه {not_yet} · بلا شموع {missing}")
    return out


def report(rows, log):
    """📊 الملخّصُ بفواصل Wilson — **والحكمُ بقاعدة التسجيل لا برأي الأداة**."""
    summ = LEDGER.summary(rows)
    if not summ:
        log("🌱 السجلُّ فارغ — لم يُرصد مرشّحٌ بعد.")
        return
    ctrl = summ.get("control") or {}
    c_n, c_k = ctrl.get("resolved", 0), ctrl.get("hit100", 0)
    c_lo, c_hi = wilson(c_k, c_n)
    log("")
    log("═══ 🌱 حصادُ الصيّادين (‏`harvest_prereg.md`) ═══")
    log(f"   {'الصيّاد':<14}{'مرصود':>8}{'محسوم':>8}{'hit100':>9}"
        f"{'المعدّل':>9}   فاصل Wilson 95%")
    total_res = 0
    for name in sorted(summ):
        d = summ[name]
        n, k = d["resolved"], d["hit100"]
        total_res += n if name != "control" else 0
        lo, hi = wilson(k, n)
        rate = (k / n * 100.0) if n else 0.0
        log(f"   {name:<14}{d['n']:>8}{n:>8}{k:>9}{rate:>8.1f}%   "
            f"[{lo*100:5.1f}% · {hi*100:5.1f}%]")
    log("")
    if c_n:
        log(f"   🎯 الشاهد: {c_k}/{c_n} = {c_k/c_n*100:.1f}% "
            f"[{c_lo*100:.1f}% · {c_hi*100:.1f}%]")
    else:
        log("   ⚠️ الشاهدُ لم يُحسم بعد — **فلا مقارنة** (والحكمُ يشترطها).")
    log("")
    log("═══ ⚖️ الحكم (قاعدةُ التسجيل §③ — مثبَّتةٌ قبل البيانات) ═══")
    any_verdict = False
    for name in sorted(summ):
        if name == "control":
            continue
        d = summ[name]
        n, k = d["resolved"], d["hit100"]
        if n < MIN_RESOLVED:
            log(f"   ⏳ {name}: {n}/{MIN_RESOLVED} محسومًا ⇒ **لا حكم** (عيّنة).")
            continue
        if not c_n:
            log(f"   ⏳ {name}: لا شاهدَ محسوم ⇒ **لا حكم**.")
            continue
        lo, hi = wilson(k, n)
        sep = lo > c_hi
        pos = (k / n) > (c_k / c_n)
        any_verdict = True
        if sep and pos:
            log(f"   ✅ {name}: فاصلُه [{lo*100:.1f}%…] **فوق** فاصل الشاهد "
                f"[…{c_hi*100:.1f}%] ⇒ **حافّةٌ مُعلَنة**.")
        else:
            log(f"   ⚖️ {name}: الفاصلان يتقاطعان أو الاتّجاه غير موجب ⇒ **لا حكم**.")
    if not any_verdict:
        log("   ⇒ **لا حكمَ بعد لأيّ صيّاد** — وهذا **متوقَّعٌ ومسجَّلٌ سلفًا** "
            "(‏`H-P3`)، ولا يُقرأ حكمًا سالبًا.")
    log(f"   📦 المجمَّع: {total_res}/{MIN_AGGREGATE} محسومًا.")


def run() -> int:
    import Super_stock as S
    try:
        import ctb_harvest as CT
    except Exception:                                            # noqa: BLE001
        CT = None

    rows = LEDGER.load()
    S.log(f"🌱 السجلّ: {len(rows)} صفًّا")

    # ── الشاهد: يُبنى **للجلسات المرصودة نفسها** بلوحةٍ حتميّة (‏H4) ──────────
    if CT is not None:
        try:
            sessions = sorted({str(r.get("session"))[:10] for r in rows
                               if r.get("session") and r.get("hunter") != "control"})
            have = {(r.get("session"), r.get("symbol")) for r in rows
                    if r.get("hunter") == "control"}
            uni = S.get_universe() or []
            for sess in sessions[-60:]:          # آخرُ 60 جلسةً مرصودة
                panel = CT.control_panel(uni, sess[:7], size=CONTROL_PER_SESSION)
                fresh = [{"symbol": s} for s in panel if (sess, s) not in have]
                if fresh:
                    LEDGER.record("control", sess, fresh, kind="control", log=None)
            rows = LEDGER.load()
        except Exception as e:                                   # noqa: BLE001
            S.log(f"⚠️ تعذّر بناءُ الشاهد ({e}) — يُعلَن ولا يُصمت.")

    # الشاهدُ يحتاج `ref_close` من شموعه (لا سعرَ عنده وقت البناء)
    need_ref = [r for r in rows if r.get("ref_close") is None]
    if need_ref:
        try:
            h = S.download_history(sorted({r["symbol"] for r in need_ref})) or {}
            for r in need_ref:
                df = h.get(r["symbol"])
                try:
                    d0 = dt.date.fromisoformat(str(r["session"])[:10])
                    px = [float(c) for ts, c in zip(df.index, df["Close"].values)
                          if ts.date() <= d0]
                    if px:
                        r["ref_close"] = px[-1]
                except Exception:                                # noqa: BLE001
                    pass
            LEDGER.apply_outcomes(rows, {}, log=None)
        except Exception as e:                                   # noqa: BLE001
            S.log(f"⚠️ تعذّر ملءُ مرجع الشاهد ({e}).")
        rows = LEDGER.load()

    got = resolve(rows, S.download_history, log=S.log)
    if got:
        LEDGER.apply_outcomes(rows, got, log=S.log)
        rows = LEDGER.load()
    report(rows, S.log)
    try:
        S.git_save([LEDGER.LEDGER_FILE])
    except Exception as e:                                       # noqa: BLE001
        S.log(f"⚠️ تعذّر حفظُ السجلّ ({e}).")
    return 0


if __name__ == "__main__":                                       # pragma: no cover
    os.environ.setdefault("SCREENER_MODE", "DIGEST")
    sys.exit(run())
