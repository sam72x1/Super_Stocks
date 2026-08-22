#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""⛏️🕐 **`T-RECLAIM-INTRADAY`** — أذرعُ «الاستعادة داخل اليوم».

> **العقد:** `intraday_reclaim_prereg.md` — مدفوعٌ **قبل سطرِ كودٍ واحدٍ من
> هذا الملفّ وقبل أيّ رقم**. ولا يُقرأ رقمٌ من هنا إلّا معه.

**السؤال:** هل قاعدةُ الخروج البنيويّ تُكلّفنا **داخلَ اليوم**، وهل ثمّة
قاعدةُ خروجٍ بديلةٌ تُحسّن التوقّعَ **بوحدة المخاطرة**؟

**خمسُ أذرعٍ ولا سادسة** (‏§②): `X0` الأساس · **`X1` الحاكمة** (إعادةُ الدخول
عند الاستعادة) · `X2`/`X3` وقفٌ واعٍ بالمسح 13%/10% · `X4` بلا وقف.

🔒 **ووحدةُ مخاطرةٍ واحدةٌ لكلّ الأذرع** `R₀ = entry − anchor_low` (‏§③) —
والفخُّ المُعلَن أن `T-SWEEP-RECLAIM` قاست إعادةَ الدخول **بوحدتها هي**.
⚖️ **ومحقَّقٌ لا لمسُ قمّة** — لا `MFE` في الحكم إطلاقًا (وهو عينُ الخلط الذي
أخرجه بلاغُ `HUIZ`)؛ و`MFE` يُطبَع **وصفيًّا** فقط.

🔒 **مقياسٌ واحدٌ لا اثنان:** `kasih_scan` يُستورَد **بالاسم** (`parse_day` ·
`prescreen` · `first_anchor` · **`resolve`** · `weekdays` · `PRICE_LO/HI` ·
`GAP_CAP`) — صفرُ منطقٍ مكرّر.
⛔ **قراءةٌ فقط · بلا كرون · والإنتاجُ لا يستوردها · ولا `LOGIC_VERSION`.**

**رموزُ الخروج:** 0 طُبع · 2 مدخلاتٌ ناقصة · **3 بوّابةُ صلاحيةٍ ساقطة** ·
**4 `X1` لم تُطلق (‏`no-op`)**.
"""
import datetime as dt
import gzip
import json
import math
import os
import statistics as st_
import sys

os.environ.setdefault("SCREENER_MODE", "BACKTEST")

import ah_scan as AH                                             # noqa: E402
import kasih_scan as KS                                          # noqa: E402
import Super_stock as S                                          # noqa: E402

# 🔒 أرقامُ العقد §② — **من `CONFIG` لا مغروسة** (صفرُ رقمٍ مخترَع)
SWEEP_MAX = float(S.CONFIG["SPLIT_SWEEP_MAX_PCT"])      # 13 · faisal_verbatim
SWEEP_MID = float(S.CONFIG["SPLIT_SWEEP_MID_PCT"])      # 10 · faisal_verbatim
ARMS = ("X0", "X1", "X2", "X3", "X4")
MIN_COVERAGE = 95.0        # ‏§⑤-V3
FLOOR_TOTAL, FLOOR_YEAR = 150, 30                       # ‏§④-④


def log(m):
    print(m, flush=True)


def wilson_mean(xs):
    """فاصلُ ثقةٍ 95% لمتوسّطٍ (‏t≈z على عيّناتٍ كبيرة) — للفرق في §④-③."""
    n = len(xs)
    if n < 2:
        return (None, None)
    m = st_.fmean(xs)
    sd = st_.pstdev(xs) * math.sqrt(n / (n - 1)) if n > 1 else 0.0
    h = 1.96 * sd / math.sqrt(n)
    return (m - h, m + h)


def _exit_below(rows, a_ms, level, start_ms=None):
    """أوّلُ إغلاقِ دقيقةٍ **دون** `level` بعد `start_ms` (أو المِرساة) —
    يُرجع `(السعر، الطابع، وقع؟)`؛ وإلّا إغلاقُ آخر شمعة (‏`eod`)."""
    ref = a_ms if start_ms is None else start_ms
    last = None
    for t, _o, _h, _l, c, _v in rows:
        if t <= ref:
            continue
        last = (float(c), int(t))
        if c < level:
            return (float(c), int(t), True)
    return ((last[0], last[1], False) if last else (None, None, False))


def _mfe(rows, a_ms, ref_px, until_ms=None):
    """أقصى ارتفاعٍ (وصفيٌّ فقط — خارج الحكم بنصّ §③)."""
    best = None
    for t, _o, h, _l, _c, _v in rows:
        if t <= a_ms or (until_ms is not None and t > until_ms):
            continue
        p = (h / ref_px - 1.0) * 100.0 if ref_px > 0 else None
        if p is not None and (best is None or p > best):
            best = p
    return best


def reclaim_point(rows, exit_ms, alow):
    """**§②-`X1`:** أوّلُ إغلاقِ دقيقةٍ **فوق** `anchor_low` بعد الخروج ·
    ومعه **أدنى قاعٍ بين الخروج والاستعادة** (قاعُ المسح = وقفُ الدخول
    الثاني). يُرجع `(سعرُ الاستعادة، طابعُها، قاعُ المسح)` أو `(None,)*3`.

    ⚖️ **متناظرٌ مع قاعدة الخروج عمدًا** (إغلاقٌ دون القاع ⟵⟶ إغلاقٌ فوقه)
    فلا يكون التعريفُ مُعايَرًا على حالةٍ بعينها."""
    if exit_ms is None:
        return (None, None, None)
    lo = None
    for t, _o, _h, l, c, _v in rows:
        if t <= exit_ms:
            continue
        lo = float(l) if lo is None else min(lo, float(l))
        if c > alow:
            return (float(c), int(t), lo)
    return (None, None, None)


def arms_for(rows, a_ms, entry, alow):
    """محصّلةُ الأذرع الخمس **بوحدة `R₀` واحدة** — §②/§③ حرفيًّا."""
    r0 = entry - alow
    if r0 <= 0:
        return None
    out = {}
    # ── X0: الأساس (قاعدةُ `resolve` نفسُها) ──
    x0_px, x0_ms, x0_broke = _exit_below(rows, a_ms, alow)
    if x0_px is None:
        return None
    out["X0"] = {"r": (x0_px - entry) / r0, "exit_ms": x0_ms,
                 "broke": x0_broke}
    # ── X1: الحاكمة — إعادةُ دخولٍ **واحدةٌ** عند الاستعادة (لا تهرام) ──
    rc_px, rc_ms, sweep_lo = (None, None, None)
    if x0_broke:
        rc_px, rc_ms, sweep_lo = reclaim_point(rows, x0_ms, alow)
    if rc_px is not None and sweep_lo is not None and sweep_lo < rc_px:
        e2_px, _e2_ms, _b2 = _exit_below(rows, a_ms, sweep_lo, start_ms=rc_ms)
        second = ((e2_px - rc_px) / r0) if e2_px is not None else 0.0
        out["X1"] = {"r": out["X0"]["r"] + second, "fired": True,
                     "entry2": rc_px, "stop2": sweep_lo}
    else:
        out["X1"] = {"r": out["X0"]["r"], "fired": False}
    # ── X2/X3: وقفٌ واعٍ بالمسح (أرقامُ CONFIG) ──
    for arm, pct in (("X2", SWEEP_MAX), ("X3", SWEEP_MID)):
        lvl = alow * (1.0 - pct / 100.0)
        px, ms, broke = _exit_below(rows, a_ms, lvl)
        out[arm] = {"r": ((px - entry) / r0 if px is not None else None),
                    "exit_ms": ms, "broke": broke}
    # ── X4: بلا وقفٍ إطلاقًا ──
    last = rows[-1][4] if rows else None
    out["X4"] = {"r": ((float(last) - entry) / r0 if last else None),
                 "broke": False}
    out["_r0"] = r0
    out["_mfe"] = _mfe(rows, a_ms, entry)          # وصفيّ خارج الحكم
    return out


# ── 🔒 §⑤-V2: الأذرعُ الخمسُ تتفرّق على عيّنةٍ مصطنعة (لا ذراعَ مكرّرة) ──
def _v2_sample():
    """مِرساةٌ عند 1.00 قاعُها 0.90 ⇒ كسرٌ ثم استعادةٌ ثم ركضة.
    القيمُ مختارةٌ لتُفرِّق **الخمسَ كلَّها** — وإلّا صارت البوّابةُ عمياء."""
    m = 60_000
    b = [(0, 1.00, 1.02, 0.90, 1.00, 100)]           # المِرساة · alow=0.90
    b += [(1 * m, 1.00, 1.00, 0.86, 0.880, 90)]      # كسرٌ ⇒ **X0** يخرج
    b += [(2 * m, 0.88, 0.90, 0.79, 0.805, 90)]      # دون 0.81 ⇒ **X3** يخرج
    b += [(3 * m, 0.80, 0.82, 0.75, 0.780, 90)]      # دون 0.783 ⇒ **X2** يخرج
    b += [(4 * m, 0.78, 0.96, 0.77, 0.950, 90)]      # **استعادة** فوق 0.90
    b += [(5 * m, 0.95, 1.60, 0.94, 1.550, 90)]      # ركضة
    b += [(6 * m, 1.55, 1.60, 1.50, 1.520, 90)]      # إغلاقُ اليوم ⇒ **X4**
    return b


def v2_gate():
    b = _v2_sample()
    a = arms_for(b, 0, 1.00, 0.90)
    if a is None:
        return False, "تعذّر الحساب"
    vals = {k: (None if a[k]["r"] is None else round(a[k]["r"], 4))
            for k in ARMS}
    if not a["X1"]["fired"]:
        return False, f"X1 لم تُطلق على العيّنة · {vals}"
    if len(set(v for v in vals.values() if v is not None)) < len(ARMS):
        return False, f"ذراعان متطابقتان ⇒ بوّابةٌ عمياء · {vals}"
    return True, str(vals)


def v0_gate(rows, a_ms, entry, alow, res):
    """**§⑤-V0:** `X0` يُعيد `resolve` بت-بت (نوعُ الخروج)."""
    _px, _ms, broke = _exit_below(rows, a_ms, alow)
    mine = "break" if broke else "eod"
    return mine == res.get("exit")


def main() -> int:                                              # noqa: C901
    if not (os.environ.get("AWS_ACCESS_KEY_ID") or "").strip():
        print("⛔ لا مفاتيح S3 — لا قياس (ولا يُخمَّن رقم).")
        return 2
    year = (os.environ.get("RC_YEAR") or "").strip()
    if not year:
        print("⛔ لا `RC_YEAR`.")
        return 2

    ok2, why2 = v2_gate()
    log(f"🔒 V2 الأذرعُ الخمسُ تتفرّق: {'✅' if ok2 else '🔴'} {why2}")
    if not ok2:
        return 3

    days = KS.weekdays(f"{year}-01-01", f"{year}-12-31")
    seed = KS.weekdays(f"{int(year)-1}-12-20", f"{int(year)-1}-12-31")[-3:]
    log(f"⛏️🕐 T-RECLAIM-INTRADAY — سنة {year} · أيام {len(days)} · "
        f"كون [{KS.PRICE_LO}, {KS.PRICE_HI}]$ · وقفا المسح "
        f"{SWEEP_MAX:.0f}%/{SWEEP_MID:.0f}% (من CONFIG)")
    log("⚖️ العقد `intraday_reclaim_prereg.md` — محقَّقٌ لا لمسُ قمّة · "
        f"وحدةُ مخاطرةٍ واحدة R0 = entry − anchor_low")

    prev_close: dict = {}
    rows_out: list = []
    n_files = n_missing = n_anchored = n_v0bad = 0
    missing_days: list = []
    for day in seed + days:
        seeding = day in seed
        key = AH.day_key(day)
        mb, ep = AH.head_size_mb(key)
        if mb is None:
            if not seeding:
                n_missing += 1
                missing_days.append(day)
            continue
        dest = f"/tmp/rc-{day}.csv.gz"
        if not AH.download(key, dest, ep):
            if not seeding:
                n_missing += 1
                missing_days.append(day)
            continue
        universe = ({s for s, c in prev_close.items()
                     if KS.PRICE_LO <= c <= KS.PRICE_HI} if not seeding
                    else set())
        try:
            with gzip.open(dest, "rt") as fh:
                bars, closes = KS.parse_day(fh, universe)
        except (OSError, KeyError, ValueError) as e:
            log(f"   ⛔ {day}: تعذّرت القراءة ({type(e).__name__}: {e})")
            if not seeding:
                n_missing += 1
                missing_days.append(day)
            continue
        finally:
            try:
                os.remove(dest)
            except OSError:
                pass
        if seeding:
            prev_close.update(closes)
            continue
        n_files += 1
        for sym, b in bars.items():
            if not KS.prescreen(b):
                continue
            e = KS.first_anchor(b)
            if e is None:
                continue
            a_ms, entry = int(e["anchor_ms"]), float(e["price"])
            pc = prev_close.get(sym)
            gap = (entry / pc - 1.0) * 100.0 if pc else None
            if gap is not None and abs(gap) > KS.GAP_CAP:
                continue
            res = KS.resolve(b, a_ms, entry)
            if res is None:
                continue
            alow = float(res["anchor_low"])
            if not v0_gate(b, a_ms, entry, alow, res):
                n_v0bad += 1
                continue
            a = arms_for(b, a_ms, entry, alow)
            if a is None:
                continue
            n_anchored += 1
            rows_out.append({
                "sym": sym, "day": day, "anchor_ms": a_ms, "entry": entry,
                "alow": alow, "r0": round(a["_r0"], 4),
                "mfe": (None if a["_mfe"] is None else round(a["_mfe"], 1)),
                "fired": a["X1"]["fired"],
                **{k: (None if a[k]["r"] is None else round(a[k]["r"], 4))
                   for k in ARMS}})
        prev_close.update(closes)

    cov = 100.0 * n_files / max(1, len(days))
    log(f"\n🩺 التغطية: {n_files}/{len(days)} يومًا = {cov:.1f}% · "
        f"مفقودٌ {n_missing}")
    if missing_days:
        log("   ⛔ الأيامُ المفقودةُ بتواريخها (تُسمّى ولا تُطوى): "
            + " · ".join(missing_days[:40])
            + (f" … و{len(missing_days)-40}" if len(missing_days) > 40 else ""))
    if cov < MIN_COVERAGE:
        log(f"🔴 V3 التغطيةُ دون {MIN_COVERAGE}% ⇒ **عطبُ أنبوبةٍ لا نتيجة**.")
        return 3
    log(f"🔒 V0 تفرّقُ `X0` عن `resolve`: {n_v0bad} "
        f"{'✅' if n_v0bad == 0 else '🔴'}")
    if n_v0bad:
        return 3
    log(f"⚓ مراسٍ مقيسة: {n_anchored:,}")

    fired = [r for r in rows_out if r["fired"]]
    log(f"🔒 V1 `X1` أطلقت في {len(fired):,} مِرساة "
        f"{'✅' if fired else '🔴 no-op'}")
    if not fired:
        return 4

    out = f"reclaim_rows_{year}.jsonl"
    with open(out, "w", encoding="utf-8") as fh:
        for r in rows_out:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    log(f"💾 {out} · {len(rows_out):,} صفًّا")

    # ── الحصيلةُ بالمقياس الحاكم (‏§③) ──
    log("\n" + "=" * 72)
    log(f"📐 التوقّعُ `E` بوحدة R0 — سنة {year}")
    log("=" * 72)
    log(f"{'الذراع':<7}|{'ن':>7}|{'E (R)':>10}|{'وسيط R':>9}|"
        f"{'موجبة%':>9}|{'فاصلُ 95% لـE':>22}")
    base = [r["X0"] for r in rows_out if r["X0"] is not None]
    for arm in ARMS:
        v = [r[arm] for r in rows_out if r[arm] is not None]
        if not v:
            log(f"{arm:<7}|{0:>7}| — تعذّر")
            continue
        lo, hi = wilson_mean(v)
        pos = 100.0 * sum(1 for x in v if x > 0) / len(v)
        ci = f"[{lo:+.3f}·{hi:+.3f}]" if lo is not None else "—"
        log(f"{arm:<7}|{len(v):>7}|{st_.fmean(v):>+10.4f}|"
            f"{st_.median(v):>+9.3f}|{pos:>8.1f}%|{ci:>22}")

    # ── الفرقُ المقترن (‏§④-①③) — على المراسي التي تُطلق `X1` وحدها ──
    log("\n📊 الفرقُ المقترن عن `X0` (نفسُ المراسي · §④):")
    for arm in ("X1", "X2", "X3", "X4"):
        d = [r[arm] - r["X0"] for r in rows_out
             if r[arm] is not None and r["X0"] is not None]
        if not d:
            continue
        lo, hi = wilson_mean(d)
        touch = "🔴 يلمس الصفر" if (lo is None or lo <= 0 <= hi) else "✅ لا يلمسه"
        log(f"   {arm}−X0 = {st_.fmean(d):+.4f}R · ن={len(d):,} · "
            f"[{lo:+.4f}·{hi:+.4f}] {touch}")
    dF = [r["X1"] - r["X0"] for r in fired]
    loF, hiF = wilson_mean(dF)
    log(f"   🥇 **X1−X0 على المُطلِقات وحدها** = {st_.fmean(dF):+.4f}R · "
        f"ن={len(dF):,} · [{loF:+.4f}·{hiF:+.4f}]")
    log(f"\n📏 الأرضية (‏§④-④): مُطلِقاتُ `X1` {len(fired):,} — "
        f"السنةُ تحتاج {FLOOR_YEAR} "
        f"{'✅' if len(fired) >= FLOOR_YEAR else '🔴'} · "
        f"والمجمَّعُ يحتاج {FLOOR_TOTAL} (يُقرأ عبر السنوات الثلاث)")
    broke = sum(1 for r in rows_out if r["X0"] is not None
                and r["X0"] < 0 and not r["fired"])
    nb = sum(1 for r in rows_out if r["fired"]) + broke
    if nb:
        log(f"🎯 `RC-P4`: أطلقت `X1` في {100.0*len(fired)/nb:.1f}% من "
            f"المراسي ذاتِ الخروج البنيويّ (التنبّؤ 25-45%)")
    log("\n⚠️ حدودُ الصدق السبعةُ في العقد §⑧ — تُقرأ **مع** هذي الأرقام.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
