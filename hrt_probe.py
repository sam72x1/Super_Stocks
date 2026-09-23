# -*- coding: utf-8 -*-
"""🏦 مِجَسّ توفّر بيانات «صندوق hrt» المؤقّت — الجولة الثالثة (P-02 · U-15 · أمرُ المالك «سجّل HRT»).

**قراءةٌ فقط · يُحذف قبل الدمج · لا تلغرام · لا كتابةُ حالة · SEC وحدها · ولا سعرَ واحدًا**
(المجتمعُ يُعَدّ قبل العقد، **والنتيجةُ لا تُقاس قبله** — لا شمعةَ ولا عائدَ في هذا الملفّ).
الثانيةُ أعطت: على WHLR ‏Form 3 من `HRT FINANCIAL LP` (‏09-10) · Form 4 شراءٌ 09-08/09-09 · **Form 4 بيعٌ 09-10**
· ومُودِعُ 13G/A على WHLR هو Magnetar لا HRT · والبحثُ النصّيّ يعمل (شاهدُ الضبط غيرُ صفر).
الثالثةُ تُجيب:
  G) WHLR: الكمّيات — هل «باع نص كمياته»؟ (قبل البيع/بعده) · هُويّةُ المالك (CIK · العنوان) · الحواشي.
  H) سجلُّ HRT مالكًا: كم إيداعًا وأيَّ نموذجٍ وأيَّ سنة (‏3 سنواتٍ حدٌّ أدنى للقياس).
  I) كلُّ Form 4 لـ HRT: المُصدِر · رمزُ العملية · «خروجٌ كامل» أم جزئيّ · تأخّرُ الإيداع عن العملية
     (**وقتُ الإشارة = قبولُ الإيداع لا تاريخُ العملية**) — عدٌّ بالسنة وعيّنةٌ صغيرة فقط.
"""
import collections
import re
import time

import requests

import Super_stock as S

UA = S.SEC_UA
WHLR = 1527541
CAP_XML = 450          # سقفُ جلب الإيداعات — والمقصوصُ يُطبَع لا يُصمَت


def get(url, **kw):
    time.sleep(0.2)
    try:
        return requests.get(url, headers=UA, timeout=40, **kw)
    except Exception as e:                                       # noqa: BLE001
        print(f"   ⛔ {type(e).__name__}: {url[:90]}")
        return None


def section(t):
    print("\n" + "═" * 8 + f" {t} " + "═" * 8, flush=True)


def _v(block, tag):
    m = re.search(rf"<{tag}>\s*(?:<value>\s*)?([^<]*)", block, re.S)
    return m.group(1).strip() if m else None


def own_doc(cik, acc):
    """نصُّ الإيداع الكامل (.txt) ⟵ حقولُ نموذج الملكيّة."""
    nod = acc.replace("-", "")
    r = get(f"https://www.sec.gov/Archives/edgar/data/{cik}/{nod}/{acc}.txt")
    if r is None or not r.ok:
        return {"err": getattr(r, "status_code", None)}
    t = r.text
    acc_dt = re.search(r"<ACCEPTANCE-DATETIME>(\d{14})", t)
    rows = []
    for tb in ("nonDerivativeTransaction", "nonDerivativeHolding",
               "derivativeTransaction", "derivativeHolding"):
        for b in re.findall(rf"<{tb}>(.*?)</{tb}>", t, re.S):
            rows.append({"t": tb[:5] + ("T" if "Transaction" in tb else "H"),
                         "title": _v(b, "securityTitle"),
                         "date": _v(b, "transactionDate"),
                         "code": _v(b, "transactionCode"),
                         "sh": _v(b, "transactionShares"),
                         "px": _v(b, "transactionPricePerShare"),
                         "ad": _v(b, "transactionAcquiredDisposedCode"),
                         "after": _v(b, "sharesOwnedFollowingTransaction"),
                         "di": _v(b, "directOrIndirectOwnership")})
    fn = [re.sub(r"\s+", " ", x).strip()[:260]
          for x in re.findall(r"<footnote id=\"[^\"]+\">(.*?)</footnote>", t, re.S)][:4]
    return {"acc_dt": acc_dt.group(1) if acc_dt else None,
            "doc": _v(t, "documentType"),
            "period": _v(t, "periodOfReport"),
            "issuer": _v(t, "issuerTradingSymbol"),
            "issuer_cik": _v(t, "issuerCik"),
            "owner": _v(t, "rptOwnerName"),
            "owner_cik": _v(t, "rptOwnerCik"),
            "street": _v(t, "rptOwnerStreet1"),
            "city": _v(t, "rptOwnerCity"),
            "ten": _v(t, "isTenPercentOwner"),
            "other": _v(t, "otherText"),
            "rows": rows, "fn": fn}


def _num(x):
    try:
        return float(str(x).replace(",", ""))
    except Exception:                                            # noqa: BLE001
        return None


def main():
    t0 = time.time()
    print(f"🏦 مِجَسّ HRT (3) · SEC_UA مضبوط={'contact@example.com' not in UA['User-Agent']}")

    section("G) WHLR: الكمّيات والهُويّة")
    rs = get(f"https://data.sec.gov/submissions/CIK{WHLR:010d}.json")
    rec = rs.json().get("filings", {}).get("recent", {}) if rs is not None and rs.ok else {}
    forms, dates, accs = rec.get("form", []), rec.get("filingDate", []), rec.get("accessionNumber", [])
    owner_cik = None
    for i in range(len(forms)):
        if forms[i] in ("3", "4", "5", "3/A", "4/A") and "2026-09-01" <= dates[i] <= "2026-09-23":
            d = own_doc(WHLR, accs[i])
            if "HRT" not in str(d.get("owner", "")).upper():
                continue
            owner_cik = owner_cik or d.get("owner_cik")
            print(f"   {dates[i]} Form {forms[i]} {accs[i]} قبول={d.get('acc_dt')} · مالك={d.get('owner')}"
                  f" CIK={d.get('owner_cik')} · {d.get('street')}، {d.get('city')} · 10%={d.get('ten')}")
            for rw in d.get("rows", []):
                print(f"      {rw}")
            for f in d.get("fn", []):
                print(f"      📝 {f}")
    if not owner_cik:
        print("   ⛔ لم يُقرأ CIK المالك — تتوقّف H/I")
        return

    section(f"H) سجلُّ HRT مالكًا (CIK {owner_cik})")
    ro = get(f"https://data.sec.gov/submissions/CIK{int(owner_cik):010d}.json")
    if ro is None or not ro.ok:
        print(f"   ⛔ {getattr(ro, 'status_code', None)}")
        return
    j = ro.json()
    print(f"   الاسم={j.get('name')} · الأسماءُ السابقة={[x.get('name') for x in j.get('formerNames', [])][:4]}"
          f" · النوع={j.get('entityType')} · SIC={j.get('sic')}")
    parts = [j.get("filings", {}).get("recent", {})]
    for fobj in j.get("filings", {}).get("files", [])[:12]:
        rf = get("https://data.sec.gov/submissions/" + fobj.get("name", ""))
        if rf is not None and rf.ok:
            parts.append(rf.json())
    F, D, A = [], [], []
    for p in parts:
        F += p.get("form", [])
        D += p.get("filingDate", [])
        A += p.get("accessionNumber", [])
    print(f"   مجموعُ الإيداعات={len(F)} · أقدمُها={min(D) if D else None} · أحدثُها={max(D) if D else None}"
          f" · ملفّاتٌ إضافيّة={len(j.get('filings', {}).get('files', []))}")
    byf = collections.Counter(F)
    print(f"   بالنموذج: {byf.most_common(14)}")
    byy = collections.defaultdict(collections.Counter)
    for f, d in zip(F, D):
        byy[d[:4]][f] += 1
    for y in sorted(byy):
        print(f"   {y}: {dict(byy[y].most_common(8))}")

    section("I) كلُّ Form 4/5 لـ HRT: المُصدِر · الرمز · الخروج · التأخّر")
    idx = [i for i in range(len(F)) if F[i] in ("4", "4/A", "5", "5/A")]
    idx.sort(key=lambda i: D[i])
    if len(idx) > CAP_XML:
        print(f"   ✂️ مقصوص: {len(idx)} ⟶ أحدثُ {CAP_XML} (المُسقَط {len(idx) - CAP_XML} أقدم)")
        idx = idx[-CAP_XML:]
    per_year = collections.defaultdict(collections.Counter)
    issuers = collections.defaultdict(set)
    lags, samples, errs = [], [], 0
    for i in idx:
        d = own_doc(int(owner_cik), A[i])
        if d.get("err") or not d.get("rows"):
            errs += 1
            continue
        y = D[i][:4]
        codes = [r.get("code") for r in d["rows"] if r["t"].endswith("T")]
        sells = [r for r in d["rows"] if r["t"].endswith("T") and r.get("code") == "S"]
        per_year[y]["إيداع"] += 1
        if sells:
            per_year[y]["فيه بيع S"] += 1
            issuers[y].add(d.get("issuer"))
            last = sells[-1]
            if _num(last.get("after")) == 0:
                per_year[y]["خروجٌ كامل"] += 1
            try:
                tx = max(r.get("date") for r in sells if r.get("date"))
                lags.append((dt_(D[i]) - dt_(tx)).days)
            except Exception:                                    # noqa: BLE001
                pass
            if len(samples) < 6:
                samples.append((D[i], d.get("issuer"), codes[:6], last.get("after"), d.get("ten")))
        if any(c == "P" for c in codes):
            per_year[y]["فيه شراء P"] += 1
    print(f"   مقروء={len(idx) - errs} · تعذّر={errs}")
    for y in sorted(per_year):
        print(f"   {y}: {dict(per_year[y])} · مُصدِرون ببيع={len(issuers[y])}")
    if lags:
        lags.sort()
        print(f"   تأخّرُ الإيداع عن آخر بيع (يوم): وسيط={lags[len(lags) // 2]} · أقصى={lags[-1]}"
              f" · توزيع={collections.Counter(min(x, 5) for x in lags)}")
    print(f"   عيّنة (تاريخ · رمز · الرموز · بعد آخر بيع · 10%): {samples}")
    print(f"\n⏱️ {time.time() - t0:.0f}ث")


def dt_(s):
    import datetime as _dt
    return _dt.date.fromisoformat(str(s)[:10])


if __name__ == "__main__":
    main()
