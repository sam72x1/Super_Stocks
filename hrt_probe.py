# -*- coding: utf-8 -*-
"""🏦 مِجَسّ توفّر بيانات «صندوق hrt» المؤقّت — الجولة الثانية (P-02 · U-15 · أمرُ المالك «سجّل HRT»).

**قراءةٌ فقط · يُحذف قبل الدمج · لا تلغرام · لا كتابةُ حالة · SEC وحدها** (بهويّة `SEC_UA` نفسِها).
الجولةُ الأولى أعطت: 6 إيداعات `SCHEDULE 13G/A` على WHLR منذ 2025-06 ببادئة وكيلٍ واحد (‏0000905148)
· وصفرَ نتائجَ في البحث النصّيّ (قد يكون صفرًا حقيقيًّا أو نداءً خاطئًا) · وتعذّرَ تحليلُ هويّة الشركة.
الثانية تُجيب:
  C0) شاهدُ ضبطٍ للبحث النصّيّ: استعلامٌ جوابُه معروفٌ غيرُ صفر (يفرّق «صفرٌ حقيقيّ» عن «نداءٌ خاطئ»).
  A) الهويّة: خلاصةُ موجز EDGAR خامًا (العناوين · CIK) لـ«hudson river».
  D) WHLR: **مَن المُودِع** في كلّ 13G/A (رأسُ الإيداع) · ونسبتُه · وتاريخُ الحدث.
  F) WHLR: نماذجُ 3/4/5 قرب 2026-09-10 ومُودِعوها (مالكُ ‏10% يودع Form 4 خلال يومين — هل هذا مصدرُ «10/9»؟).
"""
import re
import time

import requests

import Super_stock as S

UA = S.SEC_UA
WHLR = 1527541


def get(url, **kw):
    time.sleep(0.25)
    try:
        return requests.get(url, headers=UA, timeout=40, **kw)
    except Exception as e:                                       # noqa: BLE001
        print(f"   ⛔ {type(e).__name__}: {url[:90]}")
        return None


def section(t):
    print("\n" + "═" * 8 + f" {t} " + "═" * 8)


def efts(q, forms=None, start="2023-01-01"):
    p = {"q": q, "dateRange": "custom", "startdt": start, "enddt": "2026-09-23"}
    if forms:
        p["forms"] = forms
    r = get("https://efts.sec.gov/LATEST/search-index", params=p)
    if r is None or not r.ok:
        return None, f"⛔ {getattr(r, 'status_code', None)}"
    try:
        j = r.json()
    except Exception:                                            # noqa: BLE001
        return None, f"⛔ ليس JSON: {r.text[:100]}"
    tot = (j.get("hits", {}).get("total", {}) or {}).get("value")
    rows = [(h.get("_source", {}).get("file_date"), h.get("_source", {}).get("form"),
             h.get("_source", {}).get("display_names")) for h in j.get("hits", {}).get("hits", [])]
    return rows, tot


def header(cik, acc):
    """رأسُ الإيداع: المُودِع (FILED BY) · الشركةُ المعنيّة · تاريخُ الإيداع · وأسطرُ النسبة وتاريخ الحدث."""
    nod = acc.replace("-", "")
    r = get(f"https://www.sec.gov/Archives/edgar/data/{cik}/{nod}/{acc}.txt")
    if r is None or not r.ok:
        return {"err": getattr(r, "status_code", None)}
    t = r.text
    fb = re.search(r"FILED BY:.*?COMPANY CONFORMED NAME:\s*([^\n]+)", t, re.S)
    rp = re.findall(r"REPORTING-OWNER:.*?COMPANY CONFORMED NAME:\s*([^\n]+)", t, re.S)[:3] or \
        re.findall(r"<rptOwnerName>([^<]+)<", t)[:3]
    ev = (re.search(r"<eventDateRequiresFilingThisStatement>([^<]+)<", t)
          or re.search(r"(?is)date of event[^0-9A-Z]{0,200}([0-9]{1,2}/[0-9]{1,2}/[0-9]{4}|[0-9]{4}-[0-9]{2}-[0-9]{2})", t))
    pct = re.findall(r"<classPercent>([^<]+)<", t)[:3] or \
        re.findall(r"(?is)percent of class[^0-9]{0,300}?([0-9]{1,3}(?:\.[0-9]+)?)\s?%", t)[:3]
    shares = re.findall(r"<aggregateAmountOwned>([^<]+)<", t)[:3]
    tx = re.findall(r"<transactionDate>\s*<value>([^<]+)<", t)[:4]
    code = re.findall(r"<transactionCode>([^<]+)<", t)[:4]
    return {"filed_by": fb.group(1).strip() if fb else None, "owners": [x.strip() for x in rp],
            "event": ev.group(1) if ev else None, "pct": pct, "shares": shares, "tx": list(zip(tx, code))}


def main():
    t0 = time.time()
    print(f"🏦 مِجَسّ HRT (2) · SEC_UA مضبوط={'contact@example.com' not in UA['User-Agent']}")
    section("C0) شاهدُ ضبطٍ للبحث النصّيّ")
    for q, frm in (('"Wheeler Real Estate"', None), ('"Wheeler Real Estate"', "SCHEDULE 13G/A"),
                   ('"Hudson River Trading"', None), ('"Hudson River Trading"', "13F-HR")):
        rows, tot = efts(q, frm)
        print(f"   q={q} forms={frm}: المجموع {tot} · {(rows or [])[:2]}")
    section("A) الهويّة (موجز EDGAR خامًا)")
    r = get("https://www.sec.gov/cgi-bin/browse-edgar", params={
        "company": "hudson river", "owner": "include", "count": "40",
        "action": "getcompany", "output": "atom"})
    if r is not None and r.ok:
        titles = re.findall(r"<title>([^<]+)</title>", r.text)[:12]
        ciks = re.findall(r"CIK=(\d+)", r.text)[:12] or re.findall(r"<cik>(\d+)</cik>", r.text)[:12]
        print(f"   {getattr(r, 'status_code', None)} · عناوين {titles} · CIK {sorted(set(ciks))}")
    section("D) WHLR: مَن المُودِع في كلّ 13G/A")
    rs = get(f"https://data.sec.gov/submissions/CIK{WHLR:010d}.json")
    rec = rs.json().get("filings", {}).get("recent", {}) if rs is not None and rs.ok else {}
    forms, dates, accs = rec.get("form", []), rec.get("filingDate", []), rec.get("accessionNumber", [])
    g = [(dates[i], forms[i], accs[i]) for i in range(len(forms)) if "13G" in forms[i] and dates[i] >= "2024-01-01"]
    print(f"   13G منذ 2024: {len(g)}")
    for fd, fm, acc in g[:10]:
        print(f"      {fd} {fm} {acc} ⟵ {header(WHLR, acc)}")
    section("F) WHLR: نماذجُ 3/4/5 منذ 2026-08-15")
    f4 = [(dates[i], forms[i], accs[i]) for i in range(len(forms))
          if forms[i] in ("3", "4", "5", "3/A", "4/A") and dates[i] >= "2026-08-15"]
    print(f"   العدد: {len(f4)}")
    for fd, fm, acc in f4[:12]:
        print(f"      {fd} Form {fm} {acc} ⟵ {header(WHLR, acc)}")
    print(f"\n⏱️ {time.time() - t0:.0f}ث")


if __name__ == "__main__":
    main()
