#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🩺📦 مِجَسُّ جدوى «الملفّات المجمَّعة» (Flat Files · S3) — أمرُ المالك 2026-08-11.

**السؤال الوحيد:** هل نستطيع فعلًا — باشتراك المالك — أن نسرد البكت، وننزّل **يومًا
واحدًا**، ونختزله إلى **سمات المضارب بدوالّ الإنتاج نفسِها**، داخل حدود الرنر؟
**وهو مِجَسُّ جدوى لا تجربةَ حكم** ⇒ بلا تسجيلٍ مسبق (سابقةُ `nbbo_history_verdict`
و`otc_uplist_verdict` ومِجَسّات PIT) — **وأيُّ تجربةٍ تُبنى عليه تُسجَّل قبل أرقامها**.

**لماذا يستحقّ:** جملةٌ واحدة مكرّرة في توثيقنا أغلقت محورَ المضارب/اليد — «لحظيّ فقط
(لا تاريخ = لا باكتيست)» — وعليها بُني إغلاقُ السؤال وستّةَ عشرَ تأكيدًا لـ«الحافة =
التوقيت». والدوالُّ كلُّها مبنيّةٌ ومقفولةٌ وتنتظر تاريخًا: `_operator_blocks` ·
`acc_components` · `_tick_classify` · `_flow_prints` · `operator_sustain` ·
`operator_tape_profile`. **الملفّاتُ تُزيل القيدَ — لا تُصدر حكمًا.**

🔒 **قراءةٌ محضة:** لا يكتب حالةً ولا يمسّ فرزًا ولا يُستورَد في الإنتاج. و**بلا
اعتماديةٍ جديدة**: يستعمل `aws` CLI المتوفّر على رنرات GitHub (وهو الطريقُ الموثَّق
للمزوّد) عبر `subprocess` — فلا `boto3` ولا سؤالُ تثبيتِ نسخة.

🐞 **وحرّاسٌ من دروسٍ مقيسة في هذا المستودع:**
 ① **شاهدُ ضبطٍ إلزاميّ**: رمزٌ سائلٌ معروف يجب أن يُخرج أرقامًا غيرَ تافهة — وإلّا
    فالصفرُ **عطبُ أداةٍ حتى يُنفى** (درسُ PIT: `pip` سحب numpy غيرَ متوافقة فقرأ
    المِجَسُّ 0/40 وكاد يُدفَن المشروعُ بخطأ بيئة).
 ② **أسماءُ الأعمدة تُقرأ من الترويسة** لا تُفترَض (درسُ «قرأتُ `available` والحقلُ
    `shares_available` فخرجت 0 من 170 وكِدتُ أُبلغ أن الحصادَ ميّت»).
 ③ **كلُّ فشلٍ يُعلَن بسببه** ولا يُبتلَع، والخروجُ غيرُ صفريّ.
"""
from __future__ import annotations

import csv
import gzip
import json
import os
import shutil
import subprocess
import sys
import time

ENDPOINT = os.environ.get("POLYGON_S3_ENDPOINT", "https://files.massive.com")
BUCKET = os.environ.get("POLYGON_S3_BUCKET", "flatfiles")
# 🎛️ يومٌ واحد فقط — المِجَسُّ يقيس الجدوى لا يبني بيانات.
DAY = os.environ.get("PROBE_DAY", "2026-08-07")
WITNESS = os.environ.get("PROBE_WITNESS", "AAPL")        # شاهدُ الضبط (سائلٌ معروف)
CAP_MB = float(os.environ.get("PROBE_CAP_MB", "4096"))   # سقفُ تنزيلٍ معلَن
OPERATOR_MIN = int(os.environ.get("OPERATOR_MIN_SHARES", "1000"))
# مساراتٌ مرشَّحة — تُجرَّب بالترتيب ويُعلَن ما نجح (لا افتراضَ مسارٍ واحد).
TRADE_PREFIXES = ("us_stocks_sip/trades_v1", "us_stocks_sip/trades")
# 🔗 منفذان يُجرَّبان: منفذُ صفحة المفتاح **أوّلًا** (هو الموثَّق لاشتراك المالك) ثم
#    منفذُ Polygon التاريخيّ — تشخيصًا لا تخمينًا: نفسُ المفتاحين على منفذين، فإن نجح
#    أحدُهما فالعلّةُ عنوانٌ لا استحقاق، وإن فشل الاثنان فالعلّةُ **الاستحقاق**.
ENDPOINTS = tuple(dict.fromkeys(
    [ENDPOINT] + [e for e in ("https://files.polygon.io",) if e != ENDPOINT]))


def _run(args: list, timeout=900) -> tuple[int, str, str]:
    """ينادي الأمرَ ويرجّع (rc, out, err) — **ولا يبتلع شيئًا**."""
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except FileNotFoundError as e:
        return 127, "", f"الأمرُ غير موجود: {e}"
    except subprocess.TimeoutExpired:
        return 124, "", f"تجاوزَ المهلة ({timeout}ث)"


def aws(*args: str, timeout=900, endpoint=None) -> tuple[int, str, str]:
    return _run(["aws", "s3", *args, "--endpoint-url", endpoint or ENDPOINT],
                timeout=timeout)


def aws_api(*args: str, timeout=300, endpoint=None) -> tuple[int, str, str]:
    """‏`s3api` لا `s3` — يُستعمل لـ`head-object` الذي **لا يلزمه إذنُ سرد**.

    🔴 **ولماذا:** تشغيلةُ 2026-08-11 رجعت `403 Forbidden` على `ListObjectsV2` عند
    جذر البكت. والسردُ إذنٌ **منفصل** عن القراءة، فمنعُه لا يعني منعَ البيانات ⇒
    نقيسُ الحجمَ بـ`head-object` (‏HeadObject) فلا يحجبنا إذنُ السرد."""
    return _run(["aws", "s3api", *args, "--endpoint-url", endpoint or ENDPOINT],
                timeout=timeout)


def creds_present() -> bool:
    """🔐 المفتاحان يُقرآن من البيئة فقط — **ويُرجَع حكمٌ لا القيمة**، ولا يُطبَعان."""
    return bool(os.environ.get("AWS_ACCESS_KEY_ID")
                and os.environ.get("AWS_SECRET_ACCESS_KEY"))


# ── الاختزال: من CSV صفقاتٍ خام إلى سمات المضارب (نقيّ · بلا شبكة) ──────────────
REQ_COLS = ("ticker", "price", "size")


def _pick_cols(header: list) -> dict:
    """② أسماءُ الأعمدة **من الترويسة** لا مفترَضة. المفقودُ يُعلَن ويُسقط المِجَسّ."""
    idx = {c: i for i, c in enumerate(h.strip() for h in header)}
    missing = [c for c in REQ_COLS if c not in idx]
    if missing:
        raise KeyError("أعمدةٌ ناقصة: " + ", ".join(missing)
                       + " | الترويسةُ الفعلية: " + ", ".join(header[:14]))
    return idx


def reduce_trades(fh, symbols=None, min_shares=OPERATOR_MIN, cap_rows=None) -> dict:
    """يختزل صفقاتِ يومٍ إلى **سمات لكلّ رمز** بدوالّ الإنتاج نفسِها (لا نسخةٍ منها).

    `fh` ملفٌّ نصّيّ (‏CSV مفكوكُ الضغط). `symbols` مجموعةُ رموزٍ أو `None` = الكلّ.
    يرجّع `{sym: {...}}` ومعه `_rows_read`. **الاختزالُ فوريّ**: نحتفظ بـ(سعر، حجم،
    بورصة) لكلّ رمز ثم نحسب — فلا يُخزَّن خامٌ ولا تُبنى بياناتٌ (قيدُ المساحة)."""
    import Super_stock as S                                  # noqa: PLC0415
    rd = csv.reader(fh)
    idx = _pick_cols(next(rd))
    ti, pi, si = idx["ticker"], idx["price"], idx["size"]
    xi = idx.get("exchange")
    buf: dict = {}
    n_rows = 0
    for row in rd:
        n_rows += 1
        if cap_rows and n_rows > cap_rows:
            break
        try:
            sym = row[ti]
            if symbols is not None and sym not in symbols:
                continue
            buf.setdefault(sym, []).append(
                (float(row[pi]), float(row[si]),
                 int(row[xi]) if xi is not None and row[xi] else 0))
        except (IndexError, ValueError):
            continue
    out = {}
    for sym, rows in buf.items():
        ob = S._operator_blocks([(p, s) for p, s, _x in rows], min_shares)
        ac = S.acc_components([{"price": p, "size": s, "exchange": x}
                               for p, s, x in rows])
        out[sym] = {"n_trades": len(rows), "operator": ob, "acc": ac}
    out["_rows_read"] = n_rows
    return out


def min_shares_str() -> str:
    return f"{OPERATOR_MIN:,}"


def control_ok(feat: dict, witness: str = WITNESS) -> tuple[bool, str]:
    """① **شاهدُ الضبط**: الرمزُ السائل يجب أن يُخرج أرقامًا غيرَ تافهة.

    وإلّا فالنتيجةُ **عطبُ أداةٍ حتى يُنفى** — لا «لا إشارة». (‏درسُ PIT المدوَّن.)"""
    w = (feat or {}).get(witness)
    if not w:
        return False, f"شاهدُ الضبط `{witness}` **غائبٌ** عن المُخرَج"
    if not w.get("n_trades") or w["n_trades"] < 1000:
        return False, f"`{witness}` صفقاتُه {w.get('n_trades')} — أقلُّ من المعقول"
    if not w.get("operator") or not w.get("acc"):
        return False, f"`{witness}` بلا سماتٍ محسوبة (‏operator/acc = None)"
    return True, (f"`{witness}`: صفقات={w['n_trades']:,} · "
                  f"طبعات≥{min_shares_str()}={w['operator']['n_blocks']:,} · "
                  f"شراءٌ عدوانيّ={w['acc']['aggressive_buy_pct']:.1f}% · "
                  f"دارك={w['acc']['dark_share_pct']:.1f}%")


def find_trades_key(day: str) -> tuple[str, float, str, list]:
    """يجرّب المساراتَ المرشَّحة ويرجّع (المفتاح، الميغا، المنفذ، محاولاتٌ مُعلَنة).

    🔑 **`head-object` أوّلًا** (لا يلزمه إذنُ سرد — والسردُ رجع 403) ثم `ls` احتياطًا،
    فالطريقان مستقلّان في الإذن ونجاحُ أحدهما يكفي.
    🔴 **وعيبٌ ثانٍ في مِجَسّي أُصلح (2026-08-11):** كانت ترجّع «لم يُوجَد» **وتبتلع
    السبب** ⇒ يستوي عندها **«ممنوعٌ» (‏AccessDenied)** و**«لا مفتاحَ بهذا الاسم»
    (‏404)** و**«يومٌ لم يتداول»** — ثلاثةُ أحكامٍ مختلفةٍ تمامًا تُطبَع حكمًا واحدًا.
    الآن تُرجَع **كلُّ محاولةٍ بسببها الحرفيّ** فيُقرأ الفرق. 🧭 والدرس: **حكمٌ سالبٌ
    بلا سببٍ مُسمًّى يخفي تشخيصَه.**"""
    y, m, _d = day.split("-")
    tries = []
    for ep in ENDPOINTS:
        for pre in TRADE_PREFIXES:
            key = f"{pre}/{y}/{m}/{day}.csv.gz"
            rc, out, err = aws_api("head-object", "--bucket", BUCKET,
                                   "--key", key, timeout=180, endpoint=ep)
            if rc == 0 and out.strip():
                try:
                    return (key, int(json.loads(out)["ContentLength"])
                            / 1024 / 1024, ep, tries)
                except (ValueError, KeyError, TypeError):
                    return key, float("nan"), ep, tries
            tries.append((ep, key, "head", rc, (err or out).strip()[:200]))
            rc, out, err = aws("ls", f"s3://{BUCKET}/{key}", timeout=180,
                               endpoint=ep)
            if rc == 0 and out.strip():
                try:
                    return key, int(out.split()[2]) / 1024 / 1024, ep, tries
                except (IndexError, ValueError):
                    return key, float("nan"), ep, tries
            tries.append((ep, key, "ls", rc, (err or out).strip()[:200]))
    return "", float("nan"), "", tries


def main() -> int:
    print("=" * 78)
    print("🩺📦 مِجَسُّ جدوى الملفّات المجمَّعة (Flat Files · S3) — **جدوى لا حكم**")
    print("=" * 78)
    if not creds_present():
        print("⛔ المفتاحان غائبان — أضِف `POLYGON_S3_KEY`/`POLYGON_S3_SECRET` في "
              "GitHub Secrets. **لا حصادَ ولا حكم.**")
        return 2
    if not shutil.which("aws"):
        print("⛔ `aws` CLI غير متوفّر على هذا الرنر — يُعلَن ولا يُخمَّن.")
        return 2
    print(f"🔗 المنفذ: {ENDPOINT} · البكت: {BUCKET} · اليوم: {DAY} · "
          f"شاهدُ الضبط: {WITNESS}")

    # ── ① الاستحقاق: ماذا يشمله الاشتراك فعلًا؟ (سردٌ لا افتراض) ──────────────
    # 🔴 **تصحيحُ عيبٍ في مِجَسِّي نفسِه (2026-08-11):** كانت هذي الخطوةُ **تُسقط
    #    المِجَسَّ كلَّه** عند فشل السرد — فرجعَ `403 Forbidden` على `ListObjectsV2`
    #    عند الجذر فمات القياسُ قبل أن يجرّب البياناتَ أصلًا. **والسردُ إذنٌ منفصلٌ
    #    عن القراءة**: منعُه لا يعني منعَ الملفّات. ⇒ صارت **تشخيصًا لا بوّابة**:
    #    تجرّب سلّمَ بادئاتٍ وتطبع نتيجةَ كلٍّ **وتمضي مهما كان**.
    # 🧭 **الدرس المُعمَّم: خطوةُ تشخيصٍ لا يجوز أن تُسقط القياسَ الذي تسبقه.**
    print("\n① الاستحقاق — سلّمُ سردٍ **تشخيصيّ** (لا يُسقط القياس):")
    for pre in ("", "us_stocks_sip/", TRADE_PREFIXES[0] + "/"):
        rc, out, err = aws("ls", f"s3://{BUCKET}/{pre}", timeout=180)
        tag = pre or "(الجذر)"
        if rc == 0:
            names = [ln.split()[-1] for ln in out.splitlines() if ln.strip()]
            print(f"  ✅ {tag}: " + (" · ".join(names[:12]) or "(فارغ)"))
        else:
            print(f"  ⚠️ {tag}: rc={rc} · {(err or out).strip()[:160]}")
    print("  ↳ ‏403 على السرد **لا يمنع القراءة** — الحكمُ في ② و③ لا هنا. "
          "و`NoSuchBucket` وحده يعني أن اسمَ البكت غلط.")

    # ── ② حجمُ يومٍ واحد قبل تنزيله (قرارُ كلفةٍ لا مفاجأة) ───────────────────
    print("\n② حجمُ يومٍ واحد من الصفقات (يُجرَّب أكثرُ من مسار):")
    key, size_mb, used_ep, tries = find_trades_key(DAY)
    for ep, k, how, rc, err in tries:
        print(f"  ⚠️ [{how}] {ep} · {k} · rc={rc} · {err}")
    if not key:
        print(f"  ⛔ لم يُوجَد ملفُّ صفقاتٍ لـ{DAY} — **والسببُ مطبوعٌ أعلاه لكلّ محاولة**.")
        print("  ↳ اقرأ **نوعَ** الخطأ لا وجودَه: `AccessDenied`/‏403 على **كلّ** منفذٍ "
              "وكلّ مسار ⇒ **الاشتراكُ لا يشمل الملفّاتَ المجمَّعة** (استحقاقٌ لا عنوان) · "
              "و‏404/`NoSuchKey` ⇒ المسارُ أو اليومُ غلط (يومَ عطلةٍ لا ملفّ) · "
              "و`NoSuchBucket` ⇒ اسمُ البكت غلط · ونجاحُ منفذٍ وفشلُ آخرَ ⇒ العلّةُ العنوان.")
        return 3
    print(f"  ✅ {key} ≈ {size_mb:,.1f} ميغابايت (مضغوط) · المنفذُ النافع: {used_ep}")
    if size_mb == size_mb and size_mb > CAP_MB:      # (‏nan != nan)
        print(f"  ⛔ فوق السقف المُعلَن {CAP_MB:,.0f}MB — **يُعلَن ولا يُنزَّل صامتًا**.")
        return 3

    # ── ③ التنزيل والاختزال: هل يمرّ داخل حدود الرنر؟ ────────────────────────
    dst = f"/tmp/{DAY}.trades.csv.gz"
    print(f"\n③ تنزيلٌ واحدٌ ثم اختزالٌ فوريّ (لا تخزينَ خام) → {dst}")
    t0 = time.time()
    # 🔗 **من المنفذ الذي نجح في ②** لا من الافتراض (وإلّا قِسنا منفذًا وحمّلنا آخر).
    rc, out, err = aws("cp", f"s3://{BUCKET}/{key}", dst, timeout=1800,
                       endpoint=used_ep or None)
    dl = time.time() - t0
    if rc != 0:
        print(f"  ⛔ فشل التنزيل (rc={rc}): {(err or out).strip()[:300]}")
        return 3
    real_mb = os.path.getsize(dst) / 1024 / 1024
    print(f"  ✅ نُزّل {real_mb:,.1f}MB في {dl:,.1f}ث "
          f"({real_mb / max(dl, 1e-9):,.1f}MB/ث)")
    t1 = time.time()
    try:
        with gzip.open(dst, "rt", newline="", encoding="utf-8") as gz:
            feat = reduce_trades(gz)
    except Exception as e:                                    # noqa: BLE001
        print(f"  ⛔ الاختزالُ فشل: {type(e).__name__}: {e}")
        os.remove(dst)
        return 3
    red = time.time() - t1
    rows = feat.pop("_rows_read", 0)
    print(f"  ✅ اختُزل {rows:,} صفقةً ⟶ {len(feat):,} رمزًا في {red:,.1f}ث")
    os.remove(dst)
    print("  🧹 أُسقط الخام (قيدُ المساحة) — الباقي سماتٌ فقط.")

    # ── ④ شاهدُ الضبط: صفرٌ بلا شاهدٍ = عطبٌ حتى يُنفى ───────────────────────
    print("\n④ شاهدُ الضبط (إلزاميّ — الصفرُ عطبٌ حتى يُنفى):")
    ok, why = control_ok(feat)
    print(("  ✅ " if ok else "  ⛔ ") + why)
    if not ok:
        print("  ⛔ **لا يُقرأ أيُّ رقمٍ من هذي التشغيلة** — عطبُ قراءةٍ محتمل.")
        return 3

    # ── ⑤ الحكمُ على الجدوى وحدها (لا على أيّ فرضيةِ سوق) ────────────────────
    print("\n⑤ الجدوى — بالأرقام المقيسة:")
    per_day = dl + red
    print(f"  • يومٌ واحد: {real_mb:,.0f}MB · {per_day:,.0f}ث "
          f"(تنزيل {dl:,.0f} + اختزال {red:,.0f})")
    for label, days in (("شهر", 21), ("سنة", 252), ("ثلاث سنوات", 756)):
        print(f"  • {label} ({days} جلسة): ≈ {per_day * days / 3600:,.1f} ساعة · "
              f"وبالتوازي 8 ⇒ ≈ {per_day * days / 3600 / 8:,.1f} ساعة")
    print("  ⚠️ والمساحةُ لا تتراكم: يومٌ يُنزَّل ⟶ يُختزَل ⟶ يُسقَط.")
    print("\n🔒 **مِجَسُّ جدوى فقط:** لا يُدَّعى منه أيُّ حافّةٍ ولا نتيجةِ سوق · "
          "وأيُّ تجربةٍ تُبنى عليه **تُسجَّل قبل أرقامها**.")
    print("📌 وما **لا** تحلّه الملفّات: المتاحُ للاقتراض والرسوم (‏ChartExchange) · "
          "الفلوت · شورت FINRA · القروبات · إيداعات SEC.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
