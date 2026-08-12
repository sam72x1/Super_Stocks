#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🌙 `T-AH` — قياسُ «عمى الافتر» من شموع الدقيقة المجمَّعة (‏Flat Files · S3).

**العقد:** `ah_prereg.md` (مدفوعٌ **قبل أيّ رقم** · حرّاسُ الصلاحية `V1`-`V6`).

**السؤال:** الفرزُ يقرأ الشمعةَ اليومية **ولا تشمل الجلسةَ الممتدّة** — فانفجر `NUWE`
‏+100% في الافتر وأعاد الصيّادُ ترشيحَه صباحَ الغد. وحارسُنا `ah_guard` بعتبة 20%
**لم تُقَس قطّ**. والملفّاتُ تعطي ما لا يعطيه أيُّ مصدرٍ آخر: **تاريخَ الجلسة الممتدّة**.

🔒 **بحث/قياس فقط:** لا يُستورَد في أيّ مسار إنتاج · لا يكتب حالة · لا تلغرام · ولا
يمسّ عتبةً. **وإعادةُ استعمالٍ لا بناء:** الوصولُ إلى S3 من `flatfiles_probe`
بأسمائه · وحدُّ الجلسة من `market_calendar.session_info` (فيومُ الإغلاق المبكّر
‏13:00 يجعل ما بعده **ممتدًّا**) · والاتّفاقُ مع `event_exec.ny_session_key`
الإنتاجية **مُثبَتٌ بحارس** فلا يصير عندنا تعريفان للجلسة.
"""
from __future__ import annotations

import csv
import datetime as dt
import gzip
import os
import sys
import time
from zoneinfo import ZoneInfo

import flatfiles_probe as FP
import market_calendar as MC

NY = ZoneInfo("America/New_York")

DAYS = [d.strip() for d in os.environ.get("AH_DAYS", "2026-08-07").split(",")
        if d.strip()]
WITNESS = os.environ.get("AH_WITNESS", "AAPL")
PRICE_MAX = float(os.environ.get("AH_PRICE_MAX", "10"))
CAP_MB = float(os.environ.get("AH_CAP_MB", "2048"))
# 🎯 عتباتُ `Q1` **مثبَّتةٌ قبل الأرقام** — و20% هي عتبةُ `ah_guard` الحيّة.
THRESH = (10.0, 20.0, 50.0, 100.0)
GUARD_T = 20.0
# 🕯️ نافذةُ ما قبل السوق عند المزوّد تبدأ 04:00 نيويورك.
PRE_OPEN_NY_MIN = 4 * 60
MIN_PATH = "us_stocks_sip/minute_aggs_v1"
# ‏V1: شاهدُ الضبط — حجمٌ ممتدٌّ **موجبٌ وصغير**. الصفرُ عطبٌ حتى يُنفى، والنصفُ عطبٌ أيضًا.
CTRL_MIN_PCT, CTRL_MAX_PCT = 0.0, 20.0


def log(m: str = "") -> None:
    print(m, flush=True)                       # ⚡ حيًّا: عمليةٌ طويلة بلا طباعةٍ حيّة عمياءُ عند أوّل قتل


# ── دوالُّ نقيّة (بلا شبكة · قابلة للاختبار) ──────────────────────────────────
def ny_minute(ts_ns) -> tuple:
    """‏(تاريخُ نيويورك ISO، دقيقةُ اليوم) لطابعٍ زمنيّ **بالنانو**. تعذّرٌ ⇒ `(None, None)`."""
    try:
        d = dt.datetime.fromtimestamp(int(ts_ns) / 1e9, tz=NY)
    except (TypeError, ValueError, OSError, OverflowError):
        return (None, None)
    return (d.date().isoformat(), d.hour * 60 + d.minute)


def session_bucket(day: str, mod) -> str:
    """‏`regular` / `pre` / `post` / `off` — **بحدود اليوم الفعلية** من التقويم (`V3`).

    فيومُ الإغلاق المبكّر (‏13:00) ما بعده **ممتدٌّ لا نظاميّ**، وتثبيتُ 16:00 يَسِمه
    «نظاميًّا» فيخلط مقياسين. والعطلةُ ⇒ لا جلسةَ نظامية ⇒ كلُّ شيءٍ `off`."""
    if mod is None:
        return "off"
    info = MC.session_info(day)
    op, cl = info.get("open_ny_min"), info.get("close_ny_min")
    if op is None or cl is None:
        return "off"
    if op <= mod < cl:
        return "regular"
    if PRE_OPEN_NY_MIN <= mod < op:
        return "pre"
    if cl <= mod < 20 * 60:
        return "post"
    return "off"


def _pick(header: list, *names) -> int:
    """فهرسُ عمودٍ **من الترويسة** (`V2`) — لا افتراضَ ترتيبٍ ولا اسم. غيابٌ ⇒ `-1`."""
    low = [str(h).strip().lower() for h in (header or [])]
    for n in names:
        if n in low:
            return low.index(n)
    return -1


def reduce_minutes(fh) -> dict:
    """يختزل ملفَّ شموع الدقيقة إلى سماتِ جلسةٍ لكل **(رمز، يوم)**.

    المُرجَع: `{(sym, day): {...}}` بحقول `reg_high/reg_low/reg_close/reg_vol ·
    pre_high/pre_vol · post_high/post_vol · reg_close_mod`.
    🔴 **و`reg_close` = إغلاقُ آخرِ دقيقةٍ نظامية** (بالدقيقة الأكبر) لا آخرِ صفٍّ في
    الملفّ — فترتيبُ الملفّ ليس عقدًا."""
    rd = csv.reader(fh)
    try:
        header = next(rd)
    except StopIteration:
        return {}
    i_t = _pick(header, "ticker", "symbol")
    i_h = _pick(header, "high")
    i_l = _pick(header, "low")
    i_c = _pick(header, "close")
    i_v = _pick(header, "volume")
    i_w = _pick(header, "window_start", "t", "timestamp")
    if min(i_t, i_h, i_l, i_c, i_v, i_w) < 0:
        raise KeyError(f"ترويسةٌ ناقصة: {header}")
    out: dict = {}
    for row in rd:
        try:
            sym = row[i_t].strip().upper()
            hi, lo = float(row[i_h]), float(row[i_l])
            cl, vol = float(row[i_c]), float(row[i_v])
            day, mod = ny_minute(row[i_w])
        except (IndexError, ValueError, TypeError):
            continue
        if not sym or day is None:
            continue
        b = session_bucket(day, mod)
        if b == "off":
            continue
        k = (sym, day)
        r = out.get(k)
        if r is None:
            r = out[k] = {"reg_high": None, "reg_low": None, "reg_close": None,
                          "reg_close_mod": -1, "reg_vol": 0.0,
                          "pre_high": None, "pre_vol": 0.0,
                          "post_high": None, "post_vol": 0.0}
        if b == "regular":
            r["reg_high"] = hi if r["reg_high"] is None else max(r["reg_high"], hi)
            r["reg_low"] = lo if r["reg_low"] is None else min(r["reg_low"], lo)
            r["reg_vol"] += vol
            if mod > r["reg_close_mod"]:
                r["reg_close_mod"], r["reg_close"] = mod, cl
        elif b == "pre":
            r["pre_high"] = hi if r["pre_high"] is None else max(r["pre_high"], hi)
            r["pre_vol"] += vol
        else:
            r["post_high"] = hi if r["post_high"] is None else max(r["post_high"], hi)
            r["post_vol"] += vol
    return out


def post_move_pct(r: dict):
    """حركةُ الافتر = `post_high / reg_close − 1` بالمئة. **`None` إن تعذّر** —
    ولا يُستبدَل بصفرٍ (‏«تعذّرٌ ≠ صفر»)."""
    try:
        rc, ph = float(r.get("reg_close")), float(r.get("post_high"))
    except (TypeError, ValueError):
        return None
    if rc <= 0 or ph <= 0:
        return None
    return (ph / rc - 1.0) * 100.0


def pre_move_pct(r: dict, prev_close):
    """حركةُ ما قبل السوق **مقابل إغلاق اليوم السابق** — و`None` إن لم يكن السابقُ
    في العيّنة (`V5`: مقياسٌ مفبركٌ أسوأُ من غيابِ مقياس)."""
    try:
        pc, ph = float(prev_close), float(r.get("pre_high"))
    except (TypeError, ValueError):
        return None
    if pc <= 0 or ph <= 0:
        return None
    return (ph / pc - 1.0) * 100.0


def ext_vol_share(r: dict):
    """نصيبُ الحجم الممتدّ من **حجم اليوم كلِّه** بالمئة. `None` إن لا حجمَ نظاميّ."""
    reg = float(r.get("reg_vol") or 0.0)
    ext = float(r.get("pre_vol") or 0.0) + float(r.get("post_vol") or 0.0)
    tot = reg + ext
    return None if tot <= 0 else ext / tot * 100.0


def control_verdict(r) -> tuple:
    """`V1` — شاهدُ الضبط: حجمٌ ممتدٌّ **موجبٌ ودون 20%**. غيابُ الرمز ⇒ سقوط."""
    if not isinstance(r, dict):
        return False, "الشاهدُ غائبٌ عن المُخرَج — عطبُ اختزالٍ حتى يُنفى"
    sh = ext_vol_share(r)
    if sh is None:
        return False, "لا حجمَ للشاهد (صفرٌ = عطبٌ حتى يُنفى)"
    if not (CTRL_MIN_PCT < sh < CTRL_MAX_PCT):
        return False, f"نصيبُ الممتدّ {sh:.2f}% خارج [{CTRL_MIN_PCT}, {CTRL_MAX_PCT}]"
    return True, f"نصيبُ الممتدّ {sh:.2f}%"


def bucket_counts(rows: list, threshes=THRESH) -> dict:
    """عددُ الرموز-الأيام التي تتجاوز حركةُ افترها كلَّ عتبة + المقام **الصريح**."""
    vals = [post_move_pct(r) for r in rows]
    ok = [v for v in vals if v is not None]
    out = {"n": len(rows), "measurable": len(ok),
           "unmeasurable": len(vals) - len(ok)}
    for t in threshes:
        out[f"ge_{t:g}"] = sum(1 for v in ok if v >= t)
    return out


# ── الشبكة (فاشلٌ-آمن · يُعلن ولا يصمت) ───────────────────────────────────────
def day_key(day: str) -> str:
    y, m, _ = day.split("-")
    return f"{MIN_PATH}/{y}/{m}/{day}.csv.gz"


def head_size_mb(key: str):
    for ep in FP.ENDPOINTS:
        rc, out, _ = FP.aws_api("head-object", "--bucket", FP.BUCKET,
                                "--key", key, endpoint=ep)
        if rc == 0:
            try:
                import json as _j
                return float(_j.loads(out)["ContentLength"]) / (1024 * 1024), ep
            except (ValueError, KeyError, TypeError):
                continue
    return None, None


def download(key: str, dest: str, endpoint: str) -> bool:
    rc, _, err = FP.aws("cp", f"s3://{FP.BUCKET}/{key}", dest,
                        endpoint=endpoint, timeout=3600)
    if rc != 0:
        log(f"   ⛔ تعذّر التنزيل (rc={rc}): {(err or '')[:180]}")
    return rc == 0


def main() -> int:
    log("=" * 78)
    log("🌙 T-AH — عمى الافتر من شموع الدقيقة المجمَّعة · **قياسُ أساسٍ لا حكم**")
    log("=" * 78)
    log(f"🔗 البكت: {FP.BUCKET} · المسار: {MIN_PATH} · الأيام: {', '.join(DAYS)}")
    log(f"   شاهدُ الضبط: {WITNESS} · فئتُنا: سعرٌ دون ${PRICE_MAX:g} · "
        f"عتبةُ الحارس: {GUARD_T:g}%")
    log("")

    sh = FP.creds_shape()
    log("⓪ شكلُ المفتاحين (لا تُطبَع قيمة): "
        f"معرِّف طول={sh['id_len']} · UUID={'✅' if sh['id_uuid_shaped'] else '❌'} · "
        f"سرّ طول={sh['sec_len']}")
    if FP.resolve_swapped_creds():
        log("   🔁 **صُحّح انقلابُ المعرِّف/السرّ لهذي التشغيلة فقط** — وما في "
            "GitHub لم يتغيّر.")
    if not FP.creds_present():
        log("⛔ المفتاحان غائبان ⇒ خروج 2 (تهيئة) — لا رقمَ يُنشَر.")
        return 2
    log("")

    frames: dict = {}
    t_red = 0.0
    mb_tot = 0.0
    for day in DAYS:
        info = MC.session_info(day)
        key = day_key(day)
        mb, ep = head_size_mb(key)
        if mb is None:
            log(f"⛔ {day}: لا ملفَّ على أيّ منفذ ({key}) ⇒ خروج 4.")
            return 4
        log(f"① {day} ({info['session_type']} · إغلاق "
            f"{info['close_ny_min']}د) ≈ {mb:,.1f}MB · المنفذ {ep}")
        if mb_tot + mb > CAP_MB:
            log(f"   ⛔ يتجاوز السقفَ المُعلَن {CAP_MB:g}MB ⇒ يُوقَف بإعلانٍ لا صمتًا.")
            return 4
        dest = f"/tmp/ah-{day}.csv.gz"
        if not download(key, dest, ep):
            return 4
        mb_tot += mb
        t0 = time.time()
        try:
            with gzip.open(dest, "rt", newline="") as fh:
                red = reduce_minutes(fh)
        except KeyError as e:
            log(f"⛔ {e} ⇒ خروج 5.")
            return 5
        except (OSError, EOFError, gzip.BadGzipFile) as e:
            log(f"⛔ تعذّر فكُّ الضغط: {e} ⇒ خروج 4.")
            return 4
        finally:
            try:
                os.remove(dest)                  # 🧹 المساحةُ لا تتراكم
            except OSError:
                pass
        t_red += time.time() - t0
        frames.update(red)
        log(f"   ✅ اختُزل إلى {len(red):,} (رمز، يوم) في {time.time() - t0:,.1f}ث"
            f" · أُسقط الخام")
    log("")

    # ── V1 شاهدُ الضبط (إلزاميّ · قبل أيّ رقم) ────────────────────────────────
    wrow = None
    for (sym, day), r in frames.items():
        if sym == WITNESS.upper():
            wrow = r
            break
    ok, why = control_verdict(wrow)
    log(f"② شاهدُ الضبط `{WITNESS}` (‏V1): {'✅' if ok else '❌'} {why}")
    if not ok:
        log("⛔ الشاهدُ سقط ⇒ **لا رقمَ يُنشَر** (الصفرُ عطبٌ حتى يُنفى) · خروج 3.")
        return 3
    if wrow:
        log(f"   نظاميّ حجم={wrow['reg_vol']:,.0f} · قبل={wrow['pre_vol']:,.0f} · "
            f"بعد={wrow['post_vol']:,.0f} · إغلاق={wrow['reg_close']}")
    log("")

    # ── Q1 نصيبُ الحركة خارج النظاميّ ────────────────────────────────────────
    allr = list(frames.values())
    ours = [r for r in allr
            if isinstance(r.get("reg_close"), float) and 0 < r["reg_close"] < PRICE_MAX]
    log("③ `Q1` حركةُ الافتر فوق إغلاق النظاميّ — العتباتُ مثبَّتةٌ قبل الأرقام:")
    for name, rows in (("الكونُ كلُّه", allr), (f"فئتُنا (<${PRICE_MAX:g})", ours)):
        c = bucket_counts(rows)
        m = c["measurable"] or 1
        log(f"   • {name}: ن={c['n']:,} · قابلٌ للقياس={c['measurable']:,} "
            f"· غيرُ قابل={c['unmeasurable']:,}")
        log("     " + " · ".join(
            f"‏≥{t:g}%: {c[f'ge_{t:g}']:,} ({c[f'ge_{t:g}'] / m * 100:.2f}%)"
            for t in THRESH))
    log("")

    # ── Q1-ب حركةُ ما قبل السوق — **تُقاس فقط إن كان السابقُ في العيّنة** (V5) ──
    pre_ok, pre_ge = 0, 0
    for (sym, day), r in frames.items():
        try:
            prev = (dt.date.fromisoformat(day) - dt.timedelta(days=1)).isoformat()
        except ValueError:
            continue
        pm = pre_move_pct(r, (frames.get((sym, prev)) or {}).get("reg_close"))
        if pm is None:
            continue
        pre_ok += 1
        if pm >= GUARD_T:
            pre_ge += 1
    log(f"③-ب `Q1-ب` ما قبل السوق مقابل إغلاق **اليوم السابق**: قابلٌ للقياس="
        f"{pre_ok:,}" + (f" · ‏≥{GUARD_T:g}%: {pre_ge:,}" if pre_ok else
                         " ⇒ **لا يُقاس** (اليومُ السابق خارج العيّنة — `V5`)"))
    log("")

    # ── Q2 معدَّلُ الأساس عند عتبة الحارس ────────────────────────────────────
    co = bucket_counts(ours, (GUARD_T,))
    mo = co["measurable"] or 1
    log(f"④ `Q2` معايرةُ `ah_guard` عند {GUARD_T:g}% على فئتنا: "
        f"{co[f'ge_{GUARD_T:g}']:,} من {co['measurable']:,} = "
        f"**{co[f'ge_{GUARD_T:g}'] / mo * 100:.2f}%**")
    log("   ⚠️ **يقيس معدَّلَ الظاهرة لا دقّةَ الحارس** — مرشّحو الصيّاد التاريخيون "
        "غيرُ محفوظين (مسجَّلٌ قبل الرقم).")
    log("")

    # ── Q3 نصيبُ الحجم الممتدّ (وصفيّ) ───────────────────────────────────────
    shares = [s for s in (ext_vol_share(r) for r in ours) if s is not None]
    if shares:
        shares.sort()
        med = shares[len(shares) // 2]
        log(f"⑤ `Q3` نصيبُ الحجم الممتدّ في فئتنا: وسيط {med:.2f}% · "
            f"ن={len(shares):,}")
    else:
        log("⑤ `Q3` لا حجمَ قابلًا للقياس (يُعلَن ولا يُخمَّن).")

    # ── Q4 الجدوى (معامِلُ التوسيع مطبوعٌ — V6) ──────────────────────────────
    if mb_tot > 0 and DAYS:
        per_day = t_red / len(DAYS)
        log("")
        log(f"⑥ `Q4` الجدوى: {mb_tot:,.1f}MB لـ{len(DAYS)} يوم · اختزال "
            f"{t_red:,.1f}ث ⇒ **{per_day:,.1f}ث/يوم**")
        log(f"   • معامِلُ التوسيع لسنةٍ = **×252 يومًا** (مطبوعٌ لا مضمَر) ⇒ "
            f"اختزال ‏≈{per_day * 252 / 3600:,.1f} ساعة · "
            f"وبالتوازي 8 ‏≈{per_day * 252 / 3600 / 8:,.1f} ساعة")
        log("   ⚠️ ورقمُ التنزيل غيرُ مقيسٍ هنا منفصلًا (مدموجٌ في `s3 cp`) ⇒ "
            "**أرضيّةٌ لا سقف**.")
    log("")
    log("🔒 **قياسُ أساسٍ لا حكم:** لا عتبةَ تتغيّر · ولا `ah_guard` يُمَسّ · وأيُّ "
        "معايرةٍ تلزمها سنةٌ كاملة **بتسجيلٍ جديد وإذن المالك**.")
    log(f"📌 وعيّنةُ {len(DAYS)} يومٍ **لا تحكم** — الأرقامُ وصفيّةٌ لجدوى (‏§④-4).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
