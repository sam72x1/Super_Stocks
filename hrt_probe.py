# -*- coding: utf-8 -*-
"""🏦 مِجَسّ توفّر بيانات «صندوق hrt» المؤقّت (P-02 · U-15 · أمرُ المالك «سجّل HRT» 2026-09-23).

**قراءةٌ فقط · يُحذف قبل الدمج · لا تلغرام · لا كتابةُ حالة · SEC وحدها** (بهويّة `SEC_UA` نفسِها).
يُجيب قبل أيّ عقد: هل إيداعاتُ Hudson River Trading متاحةٌ ومؤرَّخةٌ بما يكفي لقياس «خروجه»؟
  A) الهويّة: من يطابق «Hudson River Trading» في EDGAR (الاسم · CIK).
  B) إيداعاتُه في submissions: الأنواعُ وأعدادُها ومداها الزمنيّ · وعيّنةُ 13G بتاريخ التقرير.
  C) البحثُ النصّيّ الكامل: إيداعاتُ 13G/13G-A التي تذكره · الشركاتُ المعنيّة · المدى.
  D) WHLR (مثالُ المنشور «باع نص كمياته يوم 10/9»): هل له 13G/A من HRT قرب 2026-09-10؟
  E) عيّنةُ مستندات: تاريخُ الحدث مقابل تاريخ الإيداع (التأخّر) · ونسبةُ الملكيّة المعلنة.
"""
import re
import time
from collections import Counter

import requests

import Super_stock as S

UA = S.SEC_UA
HITS = []


def get(url, **kw):
    time.sleep(0.25)                       # سياسةُ SEC: ‏≤10 طلبات/ثانية — نبقى تحتها بكثير
    try:
        r = requests.get(url, headers=UA, timeout=40, **kw)
        return r
    except Exception as e:                                       # noqa: BLE001
        print(f"   ⛔ {type(e).__name__}: {url[:90]}")
        return None


def section(t):
    print("\n" + "═" * 8 + f" {t} " + "═" * 8)


def identity():
    section("A) الهويّة")
    ciks = {}
    r = get("https://www.sec.gov/cgi-bin/browse-edgar", params={
        "company": "hudson river trading", "owner": "include", "count": "40",
        "action": "getcompany", "output": "atom"})
    print(f"   browse-edgar: {getattr(r, 'status_code', None)}")
    if r is not None and r.ok:
        for m in re.finditer(r"<cik>(\d+)</cik>.*?<name>([^<]+)</name>", r.text, re.S):
            ciks[int(m.group(1))] = m.group(2).strip()
        if not ciks:
            for m in re.finditer(r"CIK=(\d{10})[^>]*>[^<]*</a>\s*</td>\s*<td[^>]*>([^<]+)", r.text):
                ciks[int(m.group(1))] = m.group(2).strip()
        print("   مطابقاتٌ:", ciks or "— (لا شيء بالاسم)", "·", r.text[:160].replace("\n", " ") if not ciks else "")
    return ciks


def submissions(ciks):
    section("B) submissions لكلّ CIK")
    for cik, name in list(ciks.items())[:6]:
        r = get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json")
        if r is None or not r.ok:
            print(f"   {cik} {name}: ⛔ {getattr(r, 'status_code', None)}")
            continue
        d = r.json()
        rec = d.get("filings", {}).get("recent", {})
        forms = rec.get("form", [])
        dates = rec.get("filingDate", [])
        rds = rec.get("reportDate", [])
        acc = rec.get("accessionNumber", [])
        extra = d.get("filings", {}).get("files", [])
        c = Counter(forms)
        print(f"   {cik} «{d.get('name')}» · حديثة {len(forms)} صفًّا ({min(dates) if dates else '—'} ⟶ {max(dates) if dates else '—'}) · "
              f"صفحاتٌ أقدم {len(extra)} · الأنواع: {dict(c.most_common(12))}")
        g = [(dates[i], forms[i], rds[i] if i < len(rds) else "", acc[i]) for i in range(len(forms)) if "13G" in forms[i]]
        by_year = Counter(x[0][:4] for x in g)
        print(f"   13G بالسنة (حديثة): {dict(sorted(by_year.items()))}")
        for row in g[:8]:
            print(f"      {row}")
        HITS.extend((cik, *row) for row in g)


def fts():
    section("C) البحث النصّيّ الكامل (efts)")
    out = []
    for frm in ("SC 13G/A", "SC 13G", "SCHEDULE 13G/A", "SCHEDULE 13G"):
        r = get("https://efts.sec.gov/LATEST/search-index", params={
            "q": '"Hudson River Trading"', "forms": frm,
            "dateRange": "custom", "startdt": "2023-01-01", "enddt": "2026-09-23"})
        st = getattr(r, "status_code", None)
        if r is None or not r.ok:
            print(f"   {frm}: ⛔ {st}")
            continue
        try:
            j = r.json()
        except Exception:                                        # noqa: BLE001
            print(f"   {frm}: ⛔ ليس JSON · {r.text[:120]}")
            continue
        tot = (j.get("hits", {}).get("total", {}) or {}).get("value")
        hs = j.get("hits", {}).get("hits", [])
        print(f"   {frm}: المجموع {tot} · الصفحة الأولى {len(hs)}")
        for h in hs:
            s = h.get("_source", {})
            out.append((s.get("file_date"), s.get("form"), s.get("display_names"), s.get("adsh")))
    out.sort(key=lambda x: x[0] or "", reverse=True)
    subj = Counter()
    for fd, fm, dn, adsh in out:
        for n in (dn or []):
            if "HUDSON RIVER" not in n.upper():
                subj[n] += 1
    print(f"   شركاتٌ معنيّة مختلفة في الصفحات الأولى: {len(subj)}")
    for row in out[:15]:
        print(f"      {row[0]} {row[1]} {[n[:60] for n in (row[2] or [])]}")
    return out


def whlr(ciks, fts_rows):
    section("D) WHLR (Wheeler) قرب 2026-09-10")
    cmap = S.sec_cik_map() or {}
    wc = cmap.get("WHLR")
    print(f"   CIK WHLR: {wc}")
    hrt_prefix = {f"{c:010d}" for c in ciks}
    if wc:
        r = get(f"https://data.sec.gov/submissions/CIK{wc:010d}.json")
        if r is not None and r.ok:
            rec = r.json().get("filings", {}).get("recent", {})
            rows = [(rec["filingDate"][i], rec["form"][i], rec["accessionNumber"][i])
                    for i in range(len(rec.get("form", []))) if "13G" in rec["form"][i]
                    and rec["filingDate"][i] >= "2025-06-01"]
            print(f"   13G على WHLR منذ 2025-06: {len(rows)}")
            for fd, fm, acc in rows[:15]:
                pre = acc.split("-")[0]
                print(f"      {fd} {fm} {acc} {'⟵ بادئةُ HRT' if pre in hrt_prefix else ''}")
    hit = [x for x in fts_rows if any("WHEELER" in (n or "").upper() for n in (x[2] or []))]
    print(f"   في البحث النصّيّ: {len(hit)} — {hit[:5]}")


def sample_docs():
    section("E) عيّنةُ مستندات: تاريخُ الحدث · النسبة · التأخّر")
    seen = 0
    for cik, fd, fm, rd, acc in HITS[:40]:
        if seen >= 4:
            break
        nod = acc.replace("-", "")
        r = get(f"https://www.sec.gov/Archives/edgar/data/{cik}/{nod}/{acc}.txt")
        if r is None or not r.ok:
            continue
        t = r.text
        subj = re.search(r"SUBJECT COMPANY:.*?COMPANY CONFORMED NAME:\s*([^\n]+)", t, re.S)
        ev = (re.search(r"(?i)date of event[^\n]{0,120}\n?[^\n]{0,120}?(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2}|[A-Z][a-z]+ \d{1,2}, \d{4})", t)
              or re.search(r"<eventDateRequiresFilingThisStatement>([^<]+)<", t))
        pct = re.findall(r"(?i)percent of class[^\d]{0,200}?(\d{1,3}(?:\.\d+)?)\s?%", t)[:3] or \
            re.findall(r"<classPercent>([^<]+)<", t)[:3]
        print(f"   {fd} {fm} · الشركة {subj.group(1).strip() if subj else '—'} · الحدث {ev.group(1) if ev else '—'} "
              f"· النسبة {pct or '—'} · reportDate {rd or '—'}")
        seen += 1


def main():
    t0 = time.time()
    print(f"🏦 مِجَسّ HRT · SEC_UA مضبوط={'contact@example.com' not in UA['User-Agent']}")
    ciks = identity()
    if ciks:
        submissions(ciks)
    rows = fts()
    whlr(ciks, rows)
    sample_docs()
    print(f"\n⏱️ {time.time() - t0:.0f}ث")


if __name__ == "__main__":
    main()
