# -*- coding: utf-8 -*-
"""
🩺 مِجَسّ SEC مؤقت — يتحقّق **حيًّا** من ميزتَي بطاقة فيصل قبل الاعتماد عليهما:
  ① Form 4: هل حقل `primaryDocument` يأتي بسابقة XSL فعلًا؟ وهل الرابط المُجرَّد
     يعيد XML يقرأه `_parse_form4`؟ (البيئة المحلية تحجب SEC — الرنر لا يحجبه.)
  ② الطرح الجديد: هل `_offering_event` يلتقط نشرة نهائية حديثة لأسهم القائمة؟
     وهل التسجيل الرفّي الروتيني يُستبعَد كما صُمِّم؟

**قراءة/تشخيص فقط** — لا يحفظ حالة ولا يمسّ الفرز ولا يطبع أي سرّ.
يُحذَف بعد قراءة النتيجة (نمط مِجَسّ ChartExchange 2026-07-10).
التشغيل: workflow يدوي `sec_probe.yml`.
"""
import os
import time
import requests

import Super_stock as bot

SYMS = [s.strip().upper() for s in
        (os.environ.get("PROBE_SYMS") or "PSTV,TYGO,CMTL,PONY,APVO,AAPL").split(",")
        if s.strip()]


def _get(url):
    try:
        r = requests.get(url, headers=bot.SEC_UA, timeout=30)
        return r.status_code, r.text
    except Exception as e:                       # noqa: BLE001
        return -1, f"EXC {type(e).__name__}: {e}"


def probe_form4(sym, cik):
    """يفحص أحدث Form 4 للرمز: شكل primaryDocument · الرابطان · نتيجة المحلّل."""
    st, txt = _get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json")
    print(f"  submissions HTTP {st} · {len(txt)} حرف")
    if st != 200:
        return
    try:
        rec = ((requests.models.complexjson.loads(txt).get("filings") or {})
               .get("recent")) or {}
    except Exception:
        import json as _j
        rec = ((_j.loads(txt).get("filings") or {}).get("recent")) or {}
    forms = rec.get("form", []) or []
    dates = rec.get("filingDate", []) or []
    accs = rec.get("accessionNumber", []) or []
    docs = rec.get("primaryDocument", []) or []
    idx = [i for i, f in enumerate(forms) if (f or "").strip() == "4"]
    print(f"  عدد Form 4 في آخر الإيداعات: {len(idx)}")
    if not idx:
        return
    xsl = sum(1 for i in idx if "/" in str(docs[i] if i < len(docs) else ""))
    print(f"  ➜ منها بسابقة مسار (xsl…/): {xsl}/{len(idx)}")
    i = idx[0]
    acc = str(accs[i]).replace("-", "")
    doc = str(docs[i])
    print(f"  أحدث: {dates[i]} · primaryDocument = {doc}")
    base = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/"
    for label, u in (("خام (مجرَّد)", base + doc.split("/")[-1]),
                     ("كما يأتي (بالسابقة)", base + doc)):
        s2, t2 = _get(u)
        has = "<transactionCode>" in t2
        p = bot._parse_form4(t2) if s2 == 200 else None
        print(f"  [{label}] HTTP {s2} · فيه transactionCode: {has} · "
              f"المحلّل: {('شراء ' + str(p['shares']) + ' سهم') if p else 'لا شراء/None'}")
        time.sleep(0.2)


def main():
    print("🩺 مِجَسّ SEC — بدء")
    cmap = bot.sec_cik_map() or {}
    print(f"خريطة CIK: {len(cmap)} رمزًا")
    for sym in SYMS:
        cik = cmap.get(sym)
        print(f"\n=== {sym} (CIK {cik}) ===")
        if not cik:
            print("  لا CIK — تخطٍّ")
            continue
        probe_form4(sym, cik)
        # ② الطرح الجديد (يستعمل نفس نداء SEC داخليًّا)
        bot._SEC_FOUNDING.pop(sym, None)
        ev = bot._offering_event(sym)
        print(f"  🆕 الحدث المؤسِّس (نشرة نهائية حديثة): {ev or '— لا شيء'}")
        # ملاحظة تشخيصية: ماذا كانت القناة الواسعة ستقول (لبيان الحجب المُصلَح)
        _, _ = bot.sec_recent_filings(sym)
        print(f"  (القناة الواسعة للسياق: {bot._SEC_OFFERING.get(sym) or '—'})")
        # 🔎 يفرّق «لا إيداع أصلًا» عن «إيداع موجود ورُفِض»: نطبع كل نماذج الطرح
        # الموجودة فعلًا في آخر الإيداعات بتواريخها (تشخيص فقط).
        st, txt = _get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json")
        if st == 200:
            import json as _j
            rec = ((_j.loads(txt).get("filings") or {}).get("recent")) or {}
            fs = rec.get("form", []) or []
            ds = rec.get("filingDate", []) or []
            found = [(f, ds[i] if i < len(ds) else "")
                     for i, f in enumerate(fs)
                     if (f or "").strip() in bot._OFFERING_FORMS][:6]
            fnd = [x for x in found if x[0] in bot._FOUNDING_OFFERING_FORMS]
            print(f"  🔎 نماذج طرح موجودة فعلًا (أحدث 6): {found or 'لا شيء'}")
            print(f"     منها نشرة نهائية: {fnd or 'لا شيء'}")
        time.sleep(0.3)
    print("\n🩺 انتهى المِجَسّ")


if __name__ == "__main__":
    main()
