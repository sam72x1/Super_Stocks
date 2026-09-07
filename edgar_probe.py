#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🔬📰 `T-PRE-EDGAR` — **المرحلة صفر: مِجَسُّ جدوى المصدر**.

العقد: `edgar_prereg.md` **مدفوعٌ قبل هذا الملفّ** (‏`a2cfe53`) — و§② يحدّد
الخمسةَ `F1`-`F5` وحدودَها ورموزَ خروجها، ولا يُخفَّض حدٌّ منها بعد رؤية رقمه.

🔒 **مِجَسُّ جدوى لا تجربةَ حكم** (سابقةُ `flatfiles_probe` · `nbbo_history_verdict`
   · `otc_uplist_verdict`) ⇒ **سقفُ نجاحه صفر**: لا يُنشَر منه رقمُ فرقٍ ولا نسبةُ
   إصابةٍ ولا حكمٌ على `EG1`/`EG2`. يُجيب سؤالًا واحدًا: **هل المصدرُ صالحٌ للقياس؟**
🔒 **قراءةٌ فقط:** صفرُ إرسالٍ · صفرُ كتابةِ حالة · صفرُ مسٍّ بعتبةٍ إنتاجية.
🔒 **`V-E7`:** `Super_stock.sec_recent_filings` **لا تُنادى إطلاقًا** — حلقتُها تكسر
   عند `fdate < pcut` حيث `pcut = today − PROXY_LOOKBACK_DAYS(75)`
   (‏`Super_stock.py:4788-4789` و`4793-4794`) ⇒ **عمياءُ عن 2025 بنيويًّا**.
🔒 **مقياسٌ واحدٌ لا اثنان:** الخريطةُ من `Super_stock.sec_cik_map` **بالاسم**
   والترويسةُ `Super_stock.SEC_UA` **بالاسم** — وجالبُ `submissions` محلّيٌّ لأنه
   **لا توجد دالّةُ جلبٍ عامّة في المستودع** (المشتركُ الوحيد هو الترويسة).

⚠️ **حدُّ صدقٍ على العقد نفسِه — يُعلَن قبل أيّ رقم:** اشتقاقُ `F4` في §②-ب-6 حسب
   **زمنَ `sleep` وحدَه** (‏0.15ث ⇒ ≈6.7/ث) **وأغفل زمنَ الشبكة**، والمعدّلُ الفعليُّ
   يشمل الاثنين. ⇒ يُقاس المعدّلُ كما نصّ العقد **والحدُّ 5/ث لا يُخفَّض**، ومعه
   **تفكيكٌ مطبوع** (شبكة/كبح) وإسقاطُ الكادنس المشحون — فإن سقط `F4` بصفرِ حجبٍ
   قُرئ سببُه من الأرقام لا من التخمين.
⚠️ **والكبحُ هنا `SEC_MIN_INTERVAL`=0.10ث = سقفُ SEC المُعلَن (10/ث)** لا الكادنس
   المشحون (0.15) — لأن `F4` **يقيس سقفَ المصدر** («سقفُ النداء») لا كادنسَنا،
   ويبقى داخلَ سياسة الوصول العادل. **يُعلَن ولا يُخمَّن.**
"""

from __future__ import annotations

import glob
import gzip
import hashlib
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests  # noqa: E402

import Super_stock as S  # noqa: E402

# ---- ثوابتُ العقد (‏§② — كلُّ رقمٍ مُسنَدٌ لسطره) ----
SAMPLE_N = 60                 # §②: «أدنى 60 رمزًا»
SAMPLE_SALT = "edgar-probe:"  # §②: sha256("edgar-probe:" + رمز)
YEAR = "2025"                 # §③-1: صفوفُ `E1` لسنة 2025
DEPTH_DAY = "2025-01-02"      # §②/F3: أوّلُ يومِ تداولٍ في مدى الدراسة
F1_MIN_PCT = 70.0             # §②/F1
F2_MIN_PCT = 100.0            # §②/F2
F3_MIN_PCT = 90.0             # §②/F3
F4_MIN_RATE = 5.0             # §②/F4 — لا يُخفَّض
SEC_MIN_INTERVAL = 0.10       # سقفُ SEC المُعلَن 10/ث (‏§②-ب-6)
SHIPPED_SLEEP = 0.15          # الكادنس المشحون (‏Super_stock.py:4942 · 5257 · 5743)
SUB_URL = "https://data.sec.gov/submissions/CIK{:010d}.json"
SUB_TIMEOUT = 40              # مطابقٌ لـ`Super_stock.py:4776`


def log(msg: str) -> None:
    print(msg, flush=True)


# ---- دوالٌّ نقيّة ----
def sample_symbols(syms, n: int = SAMPLE_N, salt: str = SAMPLE_SALT) -> list:
    """عيّنةٌ حتميّة: أدنى `n` رمزًا بـ`sha256(salt + رمز)` (نمطُ `control_panel`).

    حتميّةٌ بالبناء ⇒ إعادةُ التشغيل تُعيد العيّنةَ نفسَها بت-بت، وصفرُ انتقاءٍ بعديّ.
    """
    keyed = sorted(
        (hashlib.sha256((salt + s).encode("utf-8")).hexdigest(), s)
        for s in set(syms)
    )
    return [s for _, s in keyed[:n]]


def recent_depth(sub: dict) -> tuple:
    """‏(‏أقدمُ `acceptanceDateTime` في `recent`، هل يغطّي `files[]` يومَ العمق؟).

    🔒 يقرأ **`acceptanceDateTime` وحدَه** من `recent` — و`filingDate` **ممنوعٌ منعًا
       باتًّا** بنصّ §④ (يُسنَد ليوم العمل التالي فيُسرّب ويُخفي في الاتّجاهين).
    ⚠️ و`files[]` يُقرأ **للتغطية فقط** بحقل `filingFrom` وحدَه — اسمٌ مختلفٌ عن
       `filingDate` المحظور، ولا يدخل قرارَ نافذةٍ ولا وسمًا.
    🔒 **و`filingTo` لا يدخل القرار عمدًا** (افتراضٌ يُعلَن لا يُخمَّن): شرائحُ
       `files[]` مع `recent` **متلاصقةٌ** تغطّي تاريخَ الإيداعات كلَّه بلا فجوة ⇒
       شريحةٌ تبدأ عند يوم العمق أو قبله تُثبت أن التاريخَ يبلغه **ولو انتهت هي
       قبله**؛ فاشتراطُ `filingTo >= DEPTH_DAY` كان يقصّ تغطيةً حقيقية.
    """
    fil = (sub or {}).get("filings") or {}
    acc = ((fil.get("recent") or {}).get("acceptanceDateTime") or [])
    oldest = min((str(x)[:10] for x in acc if x), default=None)
    covered = False
    for f in (fil.get("files") or []):
        frm = str(f.get("filingFrom") or "")
        if frm and frm <= DEPTH_DAY:      # 🔒 شرطٌ واحد — انظر التلاصقَ أعلاه
            covered = True
            break
    return oldest, covered


def load_year_symbols(year: str = YEAR, paths=None) -> tuple:
    """رموزُ صفوف `E1` لسنةٍ بعينها من الـartifacts المُنزَّلة (‏`day` يبدأ بالسنة).

    يُعيد (‏مجموعةُ الرموز، عددُ الملفّات، عددُ الصفوف، عددُ صفوف السنة).
    `paths` **محقونٌ للاختبار** — الافتراضُ `None` يمسح مجلّدَ العمل (نمطُ الحقن
    القائم في المستودع: «وسيط `fetch_hist` محقون للاختبار»).
    """
    if paths is None:
        paths = sorted(glob.glob("presession_rows_*.jsonl.gz")) + \
            sorted(glob.glob("presession_rows_*.jsonl"))
    syms, n_rows, n_year = set(), 0, 0
    for p in paths:
        op = gzip.open if p.endswith(".gz") else open
        try:
            with op(p, "rt", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    n_rows += 1
                    try:
                        r = json.loads(line)
                    except ValueError:
                        continue
                    if str(r.get("day") or "").startswith(year):
                        n_year += 1
                        s = str(r.get("sym") or "").strip().upper()
                        if s:
                            syms.add(s)
        except OSError as e:
            log(f"   ⚠️ تعذّرت قراءةُ {p}: {type(e).__name__}: {e} — يُعلَن ولا يُصمت")
    return syms, len(paths), n_rows, n_year


def sec_get(url: str, timeout: int = SUB_TIMEOUT) -> tuple:
    """جلبُ SEC بترويسة الإنتاج — يُعيد (‏الحالة، الجسم أو None، زمنُ الشبكة).

    ‏`status` عددٌ صحيح، أو ‏−1 عند استثناءِ شبكةٍ (يُميَّز عن الحجب 403/429).
    """
    t0 = time.monotonic()
    try:
        r = requests.get(url, headers=S.SEC_UA, timeout=timeout)
        dt_ = time.monotonic() - t0
        if r.status_code != 200:
            return r.status_code, None, dt_
        try:
            return 200, r.json(), dt_
        except ValueError:
            return 200, None, dt_
    except Exception:
        return -1, None, time.monotonic() - t0


def main() -> int:
    log("=" * 78)
    log("🔬📰 T-PRE-EDGAR — المرحلة صفر: مِجَسُّ جدوى المصدر")
    log(f"   العقد: edgar_prereg.md §② · العيّنة: أدنى {SAMPLE_N} بـsha256"
        f"('{SAMPLE_SALT}' + رمز) · السنة: {YEAR}")
    log("   🔒 سقفُ النجاح **صفر** — مِجَسُّ جدوى لا تجربةَ حكم: "
        "لا رقمَ دراسةٍ ولا EG1/EG2.")
    log("=" * 78)

    # ── V-E8 (أشدُّ من العقد): بلا SEC_CONTACT تحجب SEC ⇒ عطبُ إعدادٍ يُقرأ
    #    «المصدرُ لا يعمل». يُوقَف **قبل** أيّ نداء (درسُ `BT_CANDLE`).
    contact = (os.environ.get("SEC_CONTACT") or "").strip()
    if not contact:
        log("⛔ SEC_CONTACT غيرُ مضبوط ⇒ SEC_UA بلا بريدٍ حقيقيّ فتحجب SEC.")
        log("   هذا **عطبُ إعدادٍ لا حكمٌ على المصدر** ⇒ لا قياس (خروج 2).")
        return 2
    log(f"✅ SEC_CONTACT مضبوط ({len(contact)} محرفًا — لا تُطبَع قيمتُه).")

    # ── ① الرموز: من صفوف E1 المرفوعة (ميزانيةٌ ثابتة — لا يُعاد مسحُ السوق)
    syms, n_files, n_rows, n_year = load_year_symbols()
    log(f"📦 صفوفُ E1: {n_files} ملفًّا · {n_rows} صفًّا · منها {n_year} من {YEAR}"
        f" ⇒ {len(syms)} رمزًا فريدًا")
    if not syms:
        log(f"⛔ صفرُ رمزٍ من {YEAR} — إمّا لم تُنزَّل الـartifacts أو المدى خاطئ.")
        log("   لا مدخلات ⇒ **لا قياس** (خروج 2) — يُعلَن ولا يُصمت.")
        return 2

    sample = sample_symbols(syms)
    log(f"🎲 العيّنةُ الحتميّة: {len(sample)} رمزًا "
        f"(أوّلُها {', '.join(sample[:5])} …)")

    # ── ② F1 + F5: خريطةُ CIK (‏`sec_cik_map` الإنتاجية بالاسم)
    cmap = S.sec_cik_map()
    if not cmap:
        log("⛔ خريطةُ SEC فارغة — **تعذّر الجلب** (وليست تغطيةً ناقصة).")
        log("   السببُ مُسمًّى: `company_tickers.json` لم يصل ⇒ F1 غيرُ قابلٍ "
            "للتقييم (خروج 5).")
        return 5
    log(f"🗺️ خريطةُ SEC: {len(cmap)} رمزًا")

    have = [s for s in sample if s in cmap]
    miss = [s for s in sample if s not in cmap]
    f1 = 100.0 * len(have) / len(sample)
    f5 = 100.0 * len(miss) / len(sample)
    log(f"🚪 F1 تغطيةُ CIK: {len(have)}/{len(sample)} = {f1:.1f}% "
        f"(الحدّ {F1_MIN_PCT:.0f}%)")
    log(f"📏 F5 رموزٌ غائبةٌ اليوم عن الخريطة: {len(miss)}/{len(sample)} = "
        f"{f5:.1f}% — **يُقاس ويُعلَن بلا حدّ** (حدُّ صدقٍ لا عطبُ أداة)")
    if miss:
        log(f"   الغائبون: {', '.join(miss[:20])}"
            + (" …" if len(miss) > 20 else ""))
    log("   ⚠️ الخريطةُ **لقطةُ اليوم بلا تاريخ** ⇒ رمزٌ تبدّل بين "
        f"{YEAR} واليوم يُنسَب لشركةٍ أخرى (سابقةُ BTOG⟶SGRX).")
    if f1 < F1_MIN_PCT:
        log(f"⛔ F1 سقط ({f1:.1f}% < {F1_MIN_PCT:.0f}%) ⇒ "
            "**غيرُ قابلةٍ للقياس — تغطيةٌ ناقصة** (خروج 5).")
        return 5
    log("✅ F1 عبر.")

    # ── ③ نداءاتُ submissions المتتالية ⇒ F2 · F3 · F4 من مرورٍ واحد
    log(f"🌐 {len(have)} نداءً متتاليًا لـ`submissions` بكبحِ "
        f"{SEC_MIN_INTERVAL:.2f}ث (سقفُ SEC 10/ث) …")
    if len(have) < SAMPLE_N:
        log(f"   ⚠️ المقيسُ على {len(have)} نداءً لا {SAMPLE_N} "
            "(الفارقُ رموزٌ بلا CIK) — يُعلَن.")
    ok, has_acc, deep_recent, deep_files = 0, 0, 0, 0
    blocks, net_errs, other = 0, 0, 0
    net_total = 0.0
    lat = []
    t_start = time.monotonic()
    for i, sym in enumerate(have):
        if i:
            time.sleep(SEC_MIN_INTERVAL)
        st, sub, dt_ = sec_get(SUB_URL.format(int(cmap[sym])))
        net_total += dt_
        lat.append(dt_)
        if st in (403, 429):
            blocks += 1
            continue
        if st == -1:
            net_errs += 1
            continue
        if st != 200 or not sub:
            other += 1
            continue
        ok += 1
        fil = (sub.get("filings") or {}).get("recent") or {}
        if "acceptanceDateTime" in fil:
            has_acc += 1
        oldest, covered = recent_depth(sub)
        if oldest and oldest <= DEPTH_DAY:
            deep_recent += 1
        elif covered:
            deep_files += 1
    elapsed = time.monotonic() - t_start

    n_calls = len(have)
    rate = (n_calls / elapsed) if elapsed > 0 else 0.0
    med = sorted(lat)[len(lat) // 2] if lat else 0.0
    log(f"   📨 نجح {ok} · حُجب {blocks} (403/429) · عطلُ شبكة {net_errs} "
        f"· أخرى {other}")

    # ── F4 (يُقيَّم أوّلًا: الحجبُ يُبطل قراءةَ F2/F3)
    log(f"🚪 F4 سقفُ النداء: {n_calls} نداءً في {elapsed:.2f}ث ⇒ "
        f"{rate:.2f}/ث (الحدّ {F4_MIN_RATE:.0f}/ث) · حجب {blocks}")
    log(f"   🔍 التفكيك: شبكة {net_total:.2f}ث (وسيطُ النداء {med * 1000:.0f}ms) "
        f"· كبحٌ {(n_calls - 1) * SEC_MIN_INTERVAL:.2f}ث")
    ship = (n_calls / (net_total + (n_calls - 1) * SHIPPED_SLEEP)) \
        if (net_total + (n_calls - 1) * SHIPPED_SLEEP) > 0 else 0.0
    log(f"   📐 وبالكادنس المشحون (0.15ث) كان المعدّلُ سيصير {ship:.2f}/ث "
        "— يُنشَر للقراءة لا للحكم.")
    if blocks:
        log(f"⛔ F4 سقط — **حجبٌ فعليّ** ({blocks} من 403/429) ⇒ غيرُ قابلةٍ "
            "للقياس (خروج 5).")
        return 5
    if rate < F4_MIN_RATE:
        log(f"⛔ F4 سقط — المعدّلُ {rate:.2f}/ث دون {F4_MIN_RATE:.0f}/ث "
            "**بصفرِ حجب** ⇒ القيدُ زمنُ الشبكة لا المصدر.")
        log("   ⚠️ وهذا عينُ الحدّ المُعلَن في رأس الملفّ: اشتقاقُ §②-ب-6 حسب "
            "الكبحَ وحدَه. **الحدُّ لا يُخفَّض بعد رؤية رقمه** ⇒ غيرُ قابلةٍ "
            "للقياس (خروج 5)، وأيُّ تعديلٍ للعقد قرارُ المالك.")
        return 5
    log("✅ F4 عبر.")

    if ok == 0:
        log("⛔ صفرُ ردٍّ ناجح ⇒ F2/F3 غيرُ قابلتين للتقييم (خروج 5).")
        return 5

    # ── F2
    f2 = 100.0 * has_acc / ok
    log(f"🚪 F2 حضورُ acceptanceDateTime: {has_acc}/{ok} = {f2:.1f}% "
        f"(الحدّ {F2_MIN_PCT:.0f}%)")
    if f2 < F2_MIN_PCT:
        log(f"⛔ F2 سقط — الحقلُ غائبٌ في {ok - has_acc} من {ok} ⇒ "
            "**غيرُ قابلةٍ للقياس** (خروج 5).")
        return 5
    log("✅ F2 عبر — والحقلُ لم يكن مقروءًا في المستودع كلِّه قبل اليوم.")

    # ── F3
    deep = deep_recent + deep_files
    f3 = 100.0 * deep / ok
    log(f"🚪 F3 العمقُ إلى {DEPTH_DAY}: {deep}/{ok} = {f3:.1f}% "
        f"(الحدّ {F3_MIN_PCT:.0f}%) — منها recent {deep_recent} · "
        f"files[] {deep_files}")
    if f3 < F3_MIN_PCT:
        log(f"⛔ F3 سقط ({f3:.1f}% < {F3_MIN_PCT:.0f}%) ⇒ **غيرُ قابلةٍ "
            "للقياس — عمقٌ ناقص** (خروج 5).")
        return 5
    log("✅ F3 عبر.")

    # ── الخلاصة
    log("=" * 78)
    log("⚖️ **المرحلةُ صفر عبَرت** — F1 · F2 · F3 · F4 كلُّها فوق حدودها.")
    log(f"   F1 {f1:.1f}% · F2 {f2:.1f}% · F3 {f3:.1f}% · F4 {rate:.2f}/ث "
        f"· F5 {f5:.1f}% (بلا حدّ)")
    log("⚠️ **حدودُ صدقٍ (مكتوبةٌ قبل الأرقام):**")
    log(f"   • عيّنةٌ {len(sample)} رمزًا من {len(syms)} — جدوًى لا تمثيلٌ إحصائيّ.")
    log("   • الخريطةُ لقطةُ اليوم بلا تاريخ ⇒ F5 يقيس حجمَ الخطر لا يزيله.")
    log("   • F4 مقيسٌ على هذي التشغيلة وشبكتِها — لا يُعمَّم على المجتمع كلِّه.")
    log("   • `filingDate` **لم يُقرأ** في أيّ قرار (‏§④) — والعمقُ من "
        "`acceptanceDateTime`، و`files[]` للتغطية وحدها.")
    log("🔒 **سقفُ النجاح صفر:** لا يُبنى `CASE`/`CTRL` ولا يُنشَر رقمُ دراسةٍ "
        "من هذا المِجَسّ — بناءُ §③ يلزمه أمرُ المالك.")
    log("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
