#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📐🔕 **صيّاد ظرف الكاتالوج — أداةٌ خامسة صامتة.**

العقد: `catalog_envelope_design.md` · النتيجة: `catalog_envelope_result.md`
(‏`P90`: التقاطٌ خارج العيّنة **66.7%** · تمييز **7.2%** ⇒ **إثراء ×9.20** ·
‏≈105 مطابق/يوم) · الخطة: `PIVOT_V2_PLAN.md` §④ م-د.

🔕 **صامتٌ بقرار — صفر `send_telegram`.** والسبب مقيسٌ لا تحفّظ: قاعدة المالك
«ما ابي يجيني اشعار نهائيًّا إلا بالأسهم الجاهزة فقط» **مقفولةٌ باختبارٍ باسم
القرار**، واستثناءاها **محصوران** (قسم اليد · متابعة المركز). وسابقةُ رادار
التقسيم قُصَّت من اثني عشر سهمًا إلى المطابق وحده لأنها «ضجيجٌ يدفن الجاهز» —
وهذا الظرف يعطي **‏~105/يوم**، أي أثقلُ بعشرات المرّات. ⇒ يكتب ملفًّا ويُرفَع
artifact، **ولا يُرسِل**. وأيُّ رسالةٍ لاحقةً **قرارُ المالك وحده**.

🔒 **القرار كلُّه من `envelope_scan.decide`** — نفس الدالّة التي سيستعملها
الباكتيست ⇒ يستحيل أن يقيس أحدُهما مجتمعًا غير الذي يبنيه الآخر.
🔒 **خارج الفرز والحالة** · لا `LOGIC_VERSION` · **ولا يمسّ الفارز بحرف.**

حرّاسُه نفسُ حرّاس الصيّادين: بوّابة توقيت بعد إغلاق الافتر · حارس تغطية ·
دِدوب بطبقتين · إبلاغٌ صريح لا صمت · وختمٌ **بعد** الكتابة.
"""
from __future__ import annotations

MIN_COVERAGE_PCT = 60.0
STAMP_FILE = "envelope_hunter_stamp.json"
OUT_FILE = "envelope_candidates.jsonl"
FLOAT_BUDGET = 200          # سقفُ نداءات الفلوت — لا يُستهلَك إلا على المطابقين
MAX_ROWS = 400              # سقفُ صفوف المُخرَج · **والقصّ يُعلَن بعدّاده**


def session_gate(now_utc=None, close_hour=20):
    """⏰ نفسُ بوّابة الصيّادين الثلاثة: لا مسحَ قبل إغلاق الافتر (20:00 نيويورك)
    — تُصيب الفصلين ذاتيًّا. يرجّع `(مفتوحة، تاريخ الجلسة النيويوركيّ)`. نقيّة."""
    import datetime as _dt
    from zoneinfo import ZoneInfo as _Z
    now = now_utc or _dt.datetime.now(_dt.timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=_dt.timezone.utc)
    et = now.astimezone(_Z("America/New_York"))
    if et.hour < int(close_hour):
        return (False, None)
    return (True, et.date())


def _read_stamp():
    try:
        import json
        with open(STAMP_FILE, encoding="utf-8") as fh:
            return str(json.load(fh).get("session") or "")
    except Exception:                                            # noqa: BLE001
        return ""


def _write_stamp(S, sess):
    """🔏 الختمُ **بعد** الكتابة — فلو سقطت الكتابة لم يُختم ⇒ يُعاد غدًا.
    ⚠️ و`git_save` **بوسيطٍ واحد**: توقيعها `(filenames, runner, sender)` —
    ووسيطٌ ثانٍ نصّيّ يُفسَّر `runner` فيُنادى ⇒ `'str' object is not callable`
    (عيبٌ كشفه التشغيل الحيّ في الأداة الرابعة، ولا يُعاد)."""
    try:
        import json
        with open(STAMP_FILE, "w", encoding="utf-8") as fh:
            json.dump({"session": (sess.isoformat() if sess else None)}, fh)
        S.git_save([STAMP_FILE, OUT_FILE])
    except Exception as e:                                       # noqa: BLE001
        S.log(f"⚠️ صيّاد الظرف: تعذّر ختمُ الجلسة ({e}).")


def _fail(S, msg):
    """⛔ إبلاغٌ صريح **باللوق** — والصمت لا يُخلَط بالعطل. وبلا تلغرام (صامت)."""
    S.log(f"⛔ صيّاد الظرف: {msg}")
    return 1


def _float_of(S, sym, budget):
    """🏢 فلوت ياهو **بـ`strict=True` إلزامًا**.

    ⚠️ السبب مقفولٌ بدرسٍ موثّق: الوضع المتساهل يسقط لـ`sharesOutstanding` وهو
    **‏≥ الفلوت دائمًا** (يشمل المقيَّد) ⇒ قيمةٌ منفوخة تصل M14 فتُوسَم «فلوت
    كبير» = **تشديدٌ صامت للبوّابة**. وهنا M14 **تحذف** ⇒ الخطأ يُخرِج سهمًا سليمًا."""
    if budget[0] <= 0:
        return None
    budget[0] -= 1
    try:
        return S._yahoo_float(sym, strict=True)
    except Exception:                                            # noqa: BLE001
        return None


def run(now_utc=None, decide_fn=None) -> int:
    """`decide_fn` حاقنٌ للاختبار **فقط** (نمط `fetch_hist`/`fetch_bars` في
    الصيّادين) — الافتراض `envelope_scan.decide` **الإنتاجيّة نفسها**.

    🐞 وسببُ وجوده عيبٌ في اختباري أنا: عيّنةٌ مصطنعةٌ مسطّحة **تسقط على شرط
    الظرف** فلا تبلغ فرعَ M14 قطّ ⇒ قفلٌ يبدو أخضرَ ولا يختبر ما يدّعيه. وهو
    **فخّ «الحارس الأسبق» الموثّق** — والحقنُ يجعل القفل تفريقيًّا فعلًا."""
    import json
    import os
    import Super_stock as S
    import envelope_scan as ES

    manual = os.environ.get("ENVELOPE_FORCE", "") == "1"
    ok, sess_et = session_gate(now_utc)
    if not manual and not ok:
        S.log("⏳ صيّاد الظرف: قبل إغلاق الافتر — لا مسح.")
        return 0
    prev = _read_stamp()
    if not manual and sess_et is not None and prev == sess_et.isoformat():
        S.log(f"🔁 صيّاد الظرف: جلسة {sess_et} فُحِصت سلفًا — لا تكرار.")
        return 0

    # ① الحواف — وغيابُها **رفضٌ صريح** لا تساهل (ظرفٌ بلا حوافّ يقبل السوق كلَّه)
    edges = ES.load_edges()
    if not edges:
        return _fail(S, f"حوافُّ الظرف غائبة ({ES.EDGES_FILE}) — لا قرار.")
    if not ES.selftest(S):
        return _fail(S, "فحصُ سلامة `relaxed` سقط — لا نمسح بـCONFIG مشكوكة.")
    meta = edges.get("_meta") or {}
    S.log(f"📐 صيّاد الظرف — حوافّ {ES.edges_fingerprint(edges)} · "
          f"لقطة {meta.get('snapshot')} · {meta.get('n_symbols')} رمزًا · "
          f"مُستبعَدون: {list((meta.get('excluded') or {}).keys()) or '—'}")

    if S.yf is None:
        return _fail(S, "yfinance غير متاح.")
    try:
        uni = S.get_universe()
    except Exception as e:                                       # noqa: BLE001
        return _fail(S, f"تعذّر جلب كون ناسداك ({e}).")
    if not uni:
        return _fail(S, "كون ناسداك فارغ.")
    try:
        hist = S.download_history(uni)
    except Exception as e:                                       # noqa: BLE001
        return _fail(S, f"انهار التحميل ({e}).")
    cov = 100.0 * len(hist) / max(1, len(uni))
    if cov < MIN_COVERAGE_PCT:
        return _fail(S, f"تغطية ناقصة: {len(hist)} من {len(uni)} ({cov:.0f}%) "
                        "— لم يُفحَص السوق.")
    try:
        sess = max(df.index[-1] for df in hist.values() if len(df)).date()
    except Exception:                                            # noqa: BLE001
        sess = None
    # دِدوبٌ حاسمٌ مرجعُه **جلسة البيانات** — يُصيب يومَ العطلة حيث يخطئ السريع
    if sess is not None and not manual and prev == sess.isoformat():
        S.log(f"🔁 صيّاد الظرف: جلسة {sess} فُحِصت سلفًا — لا تكرار.")
        return 0

    # ② تمريرةُ الظرف على الكون كلِّه — بلا فلوت/شورت (كالفارز: الإثراء بعد الاختيار)
    stage = {"scanned": 0, "no_vals": 0, "outside": 0, "inside": 0}
    hits = []
    for sym, df in hist.items():
        if df is None or len(df) < 60:
            continue
        stage["scanned"] += 1
        _dec = decide_fn or ES.decide
        try:
            good, why, vals = _dec(S, sym, df, edges)
        except Exception:                                        # noqa: BLE001
            stage["no_vals"] += 1
            continue
        if vals is None:
            stage["no_vals"] += 1
            continue
        if not good:
            stage["outside"] += 1
            continue
        stage["inside"] += 1
        hits.append({"symbol": sym, "vals": vals})

    S.log(f"🔎 فُحِص {stage['scanned']} · تعذّر القياس {stage['no_vals']} · "
          f"خارج الظرف {stage['outside']} · **داخل الظرف {stage['inside']}**")

    # ③ M13/M14 فلترٌ نهائيّ — بميزانيةٍ وعلى المطابقين وحدهم
    budget = [FLOAT_BUDGET]
    rows, removed, unknown_float = [], [], 0
    for h in sorted(hits, key=lambda r: r["symbol"]):
        fl = _float_of(S, h["symbol"], budget)
        if fl is None:
            unknown_float += 1
        if S._float_too_big(fl):
            removed.append((h["symbol"], f"M14 فلوت {fl:,.0f}"))
            continue
        rows.append({**h, "float": fl})
    if removed:
        S.log(f"⛔ أخرجتهم M14 ({len(removed)}): "
              + " · ".join(f"{a} [{b}]" for a, b in removed[:12])
              + (" …" if len(removed) > 12 else ""))
    S.log(f"🏢 فلوتٌ مجهول: {unknown_float} — **يمرّ بفائدة الشك** "
          f"(ميزانية {FLOAT_BUDGET}، بقي {budget[0]})")
    # ⚠️ M13 (الشورت) **غير مقيسٍ هنا ويُصرَّح به**: يلزمه نداءٌ شبكيّ لكل رمز،
    #    ومصدرُ الفارز (FINRA) يُجلب في مرحلةٍ ثانية. ⇒ يمرّ الكلُّ بفائدة الشك،
    #    **ويُعلَن** بدل أن يُوهم المُخرَجُ أنه مُطبَّق.
    S.log("ℹ️ M13 (الشورت) غير مقيسة في هذي التمريرة — تُعلَن ولا تُوهَم.")

    cut = max(0, len(rows) - MAX_ROWS)
    if cut:
        S.log(f"✂️ قُصَّ {cut} صفًّا (سقف {MAX_ROWS}) — **مُعلَنٌ لا صامت**.")
        rows = rows[:MAX_ROWS]

    # ④ الكتابة — سطرٌ لكل مرشّح، وسطرُ ترويسةٍ يحمل التغطية والبصمة
    try:
        with open(OUT_FILE, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "_meta": True, "session": (sess.isoformat() if sess else None),
                "edges": ES.edges_fingerprint(edges), "edges_meta": meta,
                "universe": len(uni), "covered": len(hist),
                "coverage_pct": round(cov, 1), "stage": stage,
                "m14_removed": [a for a, _ in removed],
                "unknown_float": unknown_float, "m13_measured": False,
                "cut": cut, "n": len(rows),
            }, ensure_ascii=False) + "\n")
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    except Exception as e:                                       # noqa: BLE001
        return _fail(S, f"تعذّرت كتابة المُخرَج ({e}).")

    S.log(f"✅ صيّاد الظرف: {len(rows)} مرشّحًا في {OUT_FILE} "
          f"(صامت — لا تلغرام بقرار المالك).")
    _write_stamp(S, sess)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
