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

📺 **كلُّ صفٍّ يُحسم بشموع مصدره (‏2026-09-30 · ملحق §⑦):** الصيّادون صاروا على TradingView ⇒ الصفُّ يحمل `src`
(‏`hunter_ledger.row_src` · غيابُه ياهو) ⟵ `src_fetchers`: ياهو بـ`download_history` (بلا `BARS_SOURCE`) وTradingView
بـ`tv_download` وحدَه (**بلا احتياط ياهو** — الرمزُ الذي تعذّر إطارُه يبقى معلّقًا ويُعلَن) · والشاهدُ يأخذ مصدرَ أغلبيّة
صفوف الصيّادين في جلسته (‏`session_srcs`) ⇒ المرجعُ والقممُ من المصدر نفسِه دائمًا.
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


def session_srcs(rows) -> dict:
    """📺 {جلسة: مصدرُ أغلبيّة صفوف الصيّادين فيها} — «tradingview» بأغلبيّةٍ صارمة وإلّا «yahoo» (التعادلُ ياهو ·
    والشاهدُ لا يُعدّ). نقيّة — يأخذها الشاهدُ عند بنائه فيُقاس **بالمصدر نفسِه** الذي قيس به صيّادو جلسته (‏H4)."""
    cnt = {}
    for r in (rows or []):
        try:
            if r.get("hunter") == "control" or not r.get("session"):
                continue
            d = cnt.setdefault(str(r["session"])[:10], [0, 0])
            d[0 if LEDGER.row_src(r) == LEDGER.SRC_TV else 1] += 1
        except Exception:                                        # noqa: BLE001
            continue
    return {k: (LEDGER.SRC_TV if tv > yh else LEDGER.SRC_YAHOO) for k, (tv, yh) in cnt.items()}


def src_fetchers(S, log=None) -> dict:
    """📺 {المصدر: جالب(رموز) ⟵ {رمز: إطار}} — ياهو: `S.download_history` **وبيئةُ `BARS_SOURCE` منزوعةٌ مدّةَ النداء**
    (فيبقى ياهو ولو ضُبطت) · TradingView: `S.tv_download` وحدَه على نافذة `HISTORY_DAYS` (**لا احتياطَ ياهو** — والإطارُ
    الذي لا يحمل وسمَ TradingView يُسقَط) والتعذّرُ يُعلَن بعدّه."""
    def _yahoo(syms):
        old = os.environ.pop("BARS_SOURCE", None)
        try:
            return S.download_history(list(syms)) or {}
        finally:
            if old is not None:
                os.environ["BARS_SOURCE"] = old

    def _tv(syms):
        start = (dt.date.today() - dt.timedelta(days=int(S.CONFIG["HISTORY_DAYS"]))).isoformat()
        got, rep = S.tv_download(list(syms), start)
        out = {k: d for k, d in (got or {}).items() if LEDGER.frame_src(d) == LEDGER.SRC_TV}
        if log:
            rep = rep or {}
            log(f"   📺 TradingView: {len(out)} من {rep.get('asked', len(syms))} في {rep.get('secs', 0)}ث · "
                f"تعذّر {len(rep.get('none') or [])} · بلا شموع {len(rep.get('empty') or [])} · "
                f"دون {S.CONFIG['MIN_BARS']} شمعة {len(rep.get('short') or [])} ⟵ صفوفُها معلّقة (لا ياهو)")
        return out

    return {LEDGER.SRC_YAHOO: _yahoo, LEDGER.SRC_TV: _tv}


def resolve(rows, fetch_hist, log=None) -> dict:
    """يحسم ما انقضت نافذتُه. يُرجع `{key: outcome}`.

    📺 `fetch_hist` جالبٌ واحد ⟵ المسارُ السابق **بت-بت** (نداءٌ واحد لكلّ المعلّق) · أو قاموسُ {المصدر: جالب}
    (‏`src_fetchers` · ملحق §⑦) ⟵ كلُّ صفٍّ بشموع مصدره (‏`LEDGER.row_src`) · ومصدرٌ بلا جالب أو تعذّر جلبُه ⟵ صفوفُه
    معلّقةٌ وتُعلَن (لا تُحسم بمصدرٍ آخر)."""
    todo = LEDGER.pending(rows)
    if not todo:
        return {}
    if callable(fetch_hist):
        plan = [(None, fetch_hist, todo)]
    else:
        by = {}
        for r in todo:
            by.setdefault(LEDGER.row_src(r), []).append(r)
        plan = [(k, (fetch_hist or {}).get(k), v) for k, v in sorted(by.items())]
    out, not_yet, missing, nofetch = {}, 0, 0, 0
    for src, fetch, part in plan:
        syms = sorted({r["symbol"] for r in part})
        if log:
            log(f"📏 بانتظار الحسم{'' if src is None else f' ({src})'}: {len(part)} صفًّا · {len(syms)} رمزًا")
        if fetch is None:
            nofetch += len(part)
            if log:
                log(f"⚠️ لا جالبَ لمصدر «{src}» — {len(part)} صفًّا معلّقة (لا تُحسم بمصدرٍ آخر).")
            continue
        hist = {}
        try:
            hist = fetch(syms) or {}
        except Exception as e:                                   # noqa: BLE001
            if log:
                log(f"⚠️ تعذّر جلبُ الشموع ({e}) — لا حسمَ هذي المرّة.")
            if src is None:
                return {}
            nofetch += len(part)
            continue
        for r in part:
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
        log(f"   ⇒ حُسم {len(out)} · لم تنقضِ نافذتُه {not_yet} · بلا شموع {missing}"
            + (f" · تعذّر مصدرُه {nofetch}" if nofetch else ""))
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
    _src = {}
    for r in (rows or []):
        _d = _src.setdefault(str(r.get("hunter") or "?"), [0, 0])
        _d[0 if LEDGER.row_src(r) == LEDGER.SRC_TV else 1] += 1
    if any(v[0] for v in _src.values()):
        log("   📺 مصدرُ الصفوف (ملحق §⑦ — كلُّ صفٍّ يُحسم بشموع مصدره): "
            + " · ".join(f"{k} TradingView {v[0]} / ياهو {v[1]}" for k, v in sorted(_src.items())))
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
            ssrc = session_srcs(rows)            # 📺 مصدرُ أغلبيّة صيّادي الجلسة (ملحق §⑦)
            for sess in sessions[-60:]:          # آخرُ 60 جلسةً مرصودة
                panel = CT.control_panel(uni, sess[:7], size=CONTROL_PER_SESSION)
                fresh = [{"symbol": s} for s in panel if (sess, s) not in have]
                if fresh:
                    _v = ssrc.get(sess, LEDGER.SRC_YAHOO)
                    LEDGER.record("control", sess, fresh, kind="control", log=None,
                                  src_of=(None if _v == LEDGER.SRC_YAHOO else (lambda _s, _v=_v: _v)))
            rows = LEDGER.load()
        except Exception as e:                                   # noqa: BLE001
            S.log(f"⚠️ تعذّر بناءُ الشاهد ({e}) — يُعلَن ولا يُصمت.")

    # الشاهدُ يحتاج `ref_close` من شموعه (لا سعرَ عنده وقت البناء) — 📺 ومن **مصدره** (ملحق §⑦)
    fx = src_fetchers(S, log=S.log)
    need_ref = [r for r in rows if r.get("ref_close") is None]
    if need_ref:
        by = {}
        for r in need_ref:
            by.setdefault(LEDGER.row_src(r), []).append(r)
        for _k, part in sorted(by.items()):
            try:
                h = fx[_k](sorted({r["symbol"] for r in part})) or {}
                for r in part:
                    df = h.get(r["symbol"])
                    try:
                        d0 = dt.date.fromisoformat(str(r["session"])[:10])
                        px = [float(c) for ts, c in zip(df.index, df["Close"].values)
                              if ts.date() <= d0]
                        if px:
                            r["ref_close"] = px[-1]
                    except Exception:                            # noqa: BLE001
                        pass
            except Exception as e:                               # noqa: BLE001
                S.log(f"⚠️ تعذّر ملءُ مرجع الشاهد ({_k}: {e}).")
        try:
            LEDGER.apply_outcomes(rows, {}, log=None)
        except Exception as e:                                   # noqa: BLE001
            S.log(f"⚠️ تعذّر ملءُ مرجع الشاهد ({e}).")
        rows = LEDGER.load()

    got = resolve(rows, fx, log=S.log)
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
