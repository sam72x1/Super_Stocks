"""🔬 PHASE 5 §7-B/§6 — مِجَسُّ SEC (قراءةٌ فقط · يعمل على رنر GitHub لأن الجلسة محجوبةٌ عن sec.gov): لكلّ رمزٍ في كون المِجَسّ
يجلب سجلَّ الإيداعات الكامل (النموذج · تاريخُ الإيداع · طابعُ القبول = طابعُ النشر الأوّليّ · رقمُ الوصول · البنود · الأسماءُ السابقة)
وحقائقَ XBRL للأسهم القائمة (`dei:EntityCommonStockSharesOutstanding` · `dei:EntityPublicFloat` بتواريخ `filed`/`end` = عتادٌ مؤرَّخ).
بلا تلغرام · بلا حالةِ إنتاج · بلا ربطٍ بأيّ نتيجة — جمعٌ أعمى عن المخرَج. المخرَج: fm_forensics/data/sec_<date>.json.gz"""
import datetime as dt
import gzip
import json
import os
import sys
import time

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
FM = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(FM, "phase3"))
import p3lib as L  # noqa: E402

UA = {"User-Agent": (os.environ.get("SEC_CONTACT") or "SuperStocks research bot research@example.com"),
      "Accept-Encoding": "gzip, deflate"}
SLEEP = 0.12          # ≤ 10 طلبات/ث (حدّ SEC المعلَن)
KEYS = ("form", "filingDate", "acceptanceDateTime", "accessionNumber", "primaryDocument", "items", "reportDate", "act", "size")


def get(url, tries=3):
    err = "non-200"
    for i in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=40)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 404:
                return {"_status": 404}
            err = f"http {r.status_code}"
        except Exception as e:  # noqa: BLE001
            err = repr(e)
        time.sleep(1.5 * (i + 1))
    return {"_status": "error", "_err": err}


def rows(block):
    cols = {k: block.get(k) or [] for k in KEYS}
    n = len(cols["form"])
    return [{k: (cols[k][j] if j < len(cols[k]) else None) for k in KEYS} for j in range(n)]


def main():
    data = L.load()
    universe = sorted(set(data["daily"]) | set(data.get("splits") or {}))
    extra = [s for s in (os.environ.get("SEC_EXTRA") or "").replace(",", " ").split() if s]
    universe = sorted(set(universe) | set(extra))
    retrieved = dt.datetime.now(dt.timezone.utc).isoformat()
    tick = get("https://www.sec.gov/files/company_tickers.json")
    cmap = {}
    for v in (tick or {}).values():
        if isinstance(v, dict) and v.get("ticker"):
            cmap[v["ticker"].upper()] = (int(v["cik_str"]), v.get("title"))
    out = {"meta": {"retrieved_utc": retrieved, "universe": len(universe), "cik_map_size": len(cmap),
                    "sources": ["https://www.sec.gov/files/company_tickers.json", "https://data.sec.gov/submissions/CIK##########.json",
                                "https://data.sec.gov/api/xbrl/companyconcept/CIK##########/dei/EntityCommonStockSharesOutstanding.json",
                                "https://data.sec.gov/api/xbrl/companyconcept/CIK##########/dei/EntityPublicFloat.json"]},
           "symbols": {}}
    n_ok = 0
    for i, sym in enumerate(universe):
        rec = {"cik": None, "title": None, "status": "no_cik", "filings": [], "former_names": [], "tickers": [], "exchanges": [],
               "shares_outstanding": [], "public_float": []}
        if sym in cmap:
            cik, title = cmap[sym]
            rec["cik"], rec["title"] = cik, title
            sub = get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json")
            time.sleep(SLEEP)
            if sub and "filings" in sub:
                rec["status"] = "ok"
                rec["former_names"] = sub.get("formerNames") or []
                rec["tickers"] = sub.get("tickers") or []
                rec["exchanges"] = sub.get("exchanges") or []
                rec["sic"] = sub.get("sic")
                rec["state_of_inc"] = sub.get("stateOfIncorporation")
                rec["fiscal_year_end"] = sub.get("fiscalYearEnd")
                rec["filings"] = rows(sub["filings"].get("recent") or {})
                for f in sub["filings"].get("files") or []:
                    nm = f.get("name")
                    if nm:
                        more = get(f"https://data.sec.gov/submissions/{nm}")
                        time.sleep(SLEEP)
                        if more and "form" in more:
                            rec["filings"] += rows(more)
                for concept, key in (("EntityCommonStockSharesOutstanding", "shares_outstanding"), ("EntityPublicFloat", "public_float")):
                    cc = get(f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik:010d}/dei/{concept}.json")
                    time.sleep(SLEEP)
                    if cc and "units" in cc:
                        for unit, vals in cc["units"].items():
                            for v in vals:
                                rec[key].append({"unit": unit, "val": v.get("val"), "end": v.get("end"), "filed": v.get("filed"),
                                                 "form": v.get("form"), "fy": v.get("fy"), "fp": v.get("fp"), "frame": v.get("frame"), "accn": v.get("accn")})
                n_ok += 1
            else:
                rec["status"] = f"submissions:{(sub or {}).get('_status')}"
        out["symbols"][sym] = rec
        if i % 25 == 0:
            print(f"… {i + 1}/{len(universe)} ok={n_ok}", flush=True)
    out["meta"]["ok"] = n_ok
    os.makedirs(os.path.join(FM, "data"), exist_ok=True)
    path = os.path.join(FM, "data", f"sec_{retrieved[:10]}.json.gz")
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    print(f"✅ SEC probe: {n_ok}/{len(universe)} with submissions · {path} · {os.path.getsize(path)} bytes")
    print("SECPROBE_JSON " + json.dumps({"ok": n_ok, "universe": len(universe), "no_cik": sum(1 for r in out['symbols'].values() if r['status'] == 'no_cik'),
                                         "statuses": sorted({r['status'] for r in out['symbols'].values()})}))


if __name__ == "__main__":
    main()
