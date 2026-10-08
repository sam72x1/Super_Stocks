"""🔬 PHASE 5 §6/§9/§21 — الجردُ الأعمى عن المخرَج: لكلّ حلقةِ قرارٍ في المانيفست (وللضوابط حين تُعرَّف) ما المتاحُ من المعلومات
غير الشمعيّة **بعتادٍ مؤرَّخ** قبل يوم القرار T، ومن أيّ مصدر، وبأيّ ثقةٍ في التوافر التاريخيّ ⟵ `PHASE5_FEATURE_AVAILABILITY.csv`
و`PHASE5_SOURCE_LEDGER.csv`. لا يُحسب أيُّ ارتباطٍ بين ميزةٍ ومخرَج هنا، ولا تُطبَع توزيعاتُ القيم.
العوائلُ الأربع: A الفلوت · B حالةُ SEC (طرح/تسجيل) · C المتاحُ للاقتراض · D العمرُ منذ التقسيم العكسيّ."""
import collections
import datetime as dt
import gzip
import json
import os
import subprocess

import p5lib as P

L = P.L
SCR = os.environ.get("P5_SCRATCH") or os.path.join(P.HERE, "out")

# ---------------------------------------------------------------- sources (ledger §21)
SOURCES = {
    "S01": dict(SOURCE_NAME="weekly_watchlist.json (git history)", SOURCE_TYPE="bot state file · Yahoo floatShares / ChartExchange borrow at selection time",
                RECORD_TIMESTAMP="git commit time (UTC) of the first commit carrying the value", PUBLICATION_TIMESTAMP="unknown (vendor page retrieved by the bot ≤ commit)",
                EFFECTIVE_TIMESTAMP="retrieval day = commit day (lag added→commit median 0 days)", DATA_VINTAGE="point-in-time (value as the bot saw it)",
                HISTORICAL_COVERAGE="bot-selected / pullback symbols only · 2026-06-20 → present · 408 symbols",
                VERIFICATION_METHOD="git log -- weekly_watchlist.json · 527 commits parsed", KNOWN_LIMITATIONS="only symbols the bot selected; float_src/float_asof absent; borrow_hist stores (date, available) pairs without time of day",
                INDEPENDENTLY_REPRODUCIBLE="yes (git)", CONFIDENCE="HIGH for vintage · MEDIUM for value (Yahoo floatShares)"),
    "S02": dict(SOURCE_NAME="company_cache.json (git history)", SOURCE_TYPE="bot enrichment cache · Yahoo info (float, shares_out, short_pct)",
                RECORD_TIMESTAMP="git commit time (UTC) of first appearance of the value", PUBLICATION_TIMESTAMP="unknown", EFFECTIVE_TIMESTAMP="≤ first-appearance commit (value may persist unchanged afterwards)",
                DATA_VINTAGE="point-in-time upper bound (first appearance)", HISTORICAL_COVERAGE="2026-06-21 → present · 590 symbols",
                VERIFICATION_METHOD="git log -- company_cache.json · 124 commits parsed", KNOWN_LIMITATIONS="float_asof present in 1.3% of rows; a stale value can persist for months (we date it by first appearance, so VALUE_DATE is an upper bound of retrieval)",
                INDEPENDENTLY_REPRODUCIBLE="yes (git)", CONFIDENCE="MEDIUM"),
    "S03": dict(SOURCE_NAME="near_watch_float.json (git history)", SOURCE_TYPE="bot float store · Yahoo floatShares with `date` (retrieval day)",
                RECORD_TIMESTAMP="git commit time (UTC)", PUBLICATION_TIMESTAMP="unknown", EFFECTIVE_TIMESTAMP="`date` field = retrieval day",
                DATA_VINTAGE="point-in-time", HISTORICAL_COVERAGE="2026-09-29 → present · 794 symbols", VERIFICATION_METHOD="git log -- near_watch_float.json · 8 commits parsed",
                KNOWN_LIMITATIONS="starts 2026-09-29 (after most decisions)", INDEPENDENTLY_REPRODUCIBLE="yes (git)", CONFIDENCE="HIGH for vintage"),
    "S04": dict(SOURCE_NAME="ctb_log.jsonl", SOURCE_TYPE="daily borrow harvest · ChartExchange (IBKR) shares available + fee",
                RECORD_TIMESTAMP="`date` = harvest day (job cron 01:20 UTC Tue–Sat = after the previous US session; no intraday time)", PUBLICATION_TIMESTAMP="IBKR snapshot ≤ harvest time (vendor refresh ~15 min)",
                EFFECTIVE_TIMESTAMP="harvest day", DATA_VINTAGE="point-in-time snapshot", HISTORICAL_COVERAGE="2026-07-30 → present · 214 symbols · cohorts bot/faisal/control",
                VERIFICATION_METHOD="file parsed · 1,543 rows", KNOWN_LIMITATIONS="only symbols in the harvest cohorts; no snapshot before 2026-07-30; ~50-page quota per runner until 2026-09-26 (gaps)",
                INDEPENDENTLY_REPRODUCIBLE="yes (file in git)", CONFIDENCE="HIGH for vintage · MEDIUM for coverage"),
    "S05": dict(SOURCE_NAME="weekly_watchlist.json borrow_hist (git history)", SOURCE_TYPE="bot daily borrow refresh · (date, shares available) pairs",
                RECORD_TIMESTAMP="date field (refresh day)", PUBLICATION_TIMESTAMP="ChartExchange ≤ refresh", EFFECTIVE_TIMESTAMP="refresh day", DATA_VINTAGE="point-in-time",
                HISTORICAL_COVERAGE="bot-selected symbols while active", VERIFICATION_METHOD="parsed from S01 snapshots", KNOWN_LIMITATIONS="only while the symbol is on the watchlist",
                INDEPENDENTLY_REPRODUCIBLE="yes (git)", CONFIDENCE="HIGH for vintage"),
    "S06": dict(SOURCE_NAME="Yahoo splits (fm_forensics/data/bars_2026-10-08.json.gz)", SOURCE_TYPE="corporate-action list · current vintage",
                RECORD_TIMESTAMP="snapshot 2026-10-08", PUBLICATION_TIMESTAMP="unknown (vendor)", EFFECTIVE_TIMESTAMP="split effective date (historical fact)",
                DATA_VINTAGE="CURRENT (retrieved 2026-10-08); dates are historical", HISTORICAL_COVERAGE="238 symbols of the probe universe", VERIFICATION_METHOD="cross-checked against SEC filings (S07) when available",
                KNOWN_LIMITATIONS="vendor may miss or duplicate splits (documented: 39/3,390 inconsistencies 2026-09-26; dedupe rule SPLIT_DUP_DAYS=7); symbol continuity not guaranteed", INDEPENDENTLY_REPRODUCIBLE="yes (file in git)", CONFIDENCE="MEDIUM"),
    "S07": dict(SOURCE_NAME="SEC EDGAR submissions + dei XBRL (fm_forensics/data/sec_*.json.gz via fm_sec_probe.yml)", SOURCE_TYPE="primary regulatory filings · form, filingDate, acceptanceDateTime; dei:EntityCommonStockSharesOutstanding (filed/end); formerNames",
                RECORD_TIMESTAMP="acceptanceDateTime (EDGAR, ET)", PUBLICATION_TIMESTAMP="acceptanceDateTime (public on EDGAR at acceptance; after 17:30 ET ⇒ next business day dissemination)",
                EFFECTIVE_TIMESTAMP="filingDate", DATA_VINTAGE="point-in-time by construction (filings are immutable)", HISTORICAL_COVERAGE="US domestic + foreign private issuers with a CIK; sec.gov blocked from the session (proxy 403) ⇒ collected on a GitHub runner",
                VERIFICATION_METHOD="accession numbers are verifiable at sec.gov", KNOWN_LIMITATIONS="ticker→CIK map is current (company_tickers.json); delisted/renamed tickers may not resolve; foreign issuers file 6-K/20-F/F-1/F-3 (different offering forms)",
                INDEPENDENTLY_REPRODUCIBLE="yes", CONFIDENCE="HIGH"),
    "S08": dict(SOURCE_NAME="Yahoo current float / ChartExchange current borrow (NOT USED)", SOURCE_TYPE="current vendor pages",
                RECORD_TIMESTAMP="now", PUBLICATION_TIMESTAMP="now", EFFECTIVE_TIMESTAMP="now", DATA_VINTAGE="CURRENT ONLY", HISTORICAL_COVERAGE="none",
                VERIFICATION_METHOD="n/a", KNOWN_LIMITATIONS="a current value is not a historical value (§6) ⇒ NON_CONFIRMATORY; iBorrowDesk unreachable from runners (2026-09-25)", INDEPENDENTLY_REPRODUCIBLE="n/a", CONFIDENCE="n/a"),
}

OFFERING_FORMS = ("424B1", "424B2", "424B3", "424B4", "424B5", "424B7", "424B8", "S-1", "S-1/A", "S-3", "S-3/A", "F-1", "F-1/A", "F-3", "F-3/A", "EFFECT", "424H", "S-8", "F-10")
FINAL_PROSPECTUS = ("424B1", "424B4", "424B5")
REG_STATEMENT = ("S-1", "S-1/A", "S-3", "S-3/A", "F-1", "F-1/A", "F-3", "F-3/A", "F-10")


def git_hist(name):
    p = os.path.join(SCR, name)
    return json.load(open(p)) if os.path.exists(p) else None


def build_hist():
    """تُعاد بناءُ تواريخ git عند الغياب (نفس الاستخراج الذي حُفظ في الـscratch)."""
    out = {}
    for fn, key in (("weekly_watchlist.json", "wl_history.json"), ("company_cache.json", "cc_history.json"), ("near_watch_float.json", "nwf_history.json")):
        h = git_hist(key)
        if h is None:
            h = []
            log = subprocess.run(["git", "log", "--format=%H %cI", "--", fn], capture_output=True, text=True, cwd=P.REPO).stdout.split("\n")
            for ln in log:
                if not ln:
                    continue
                hsh, ci = ln.split()
                r = subprocess.run(["git", "show", f"{hsh}:{fn}"], capture_output=True, text=True, cwd=P.REPO)
                if r.returncode:
                    continue
                try:
                    d = json.loads(r.stdout)
                except Exception:
                    continue
                if fn == "weekly_watchlist.json":
                    for ln2, lst in (("stocks", d.get("stocks") or []), ("pullback", d.get("pullback") or [])):
                        for s in lst:
                            if isinstance(s, dict) and s.get("symbol"):
                                h.append(dict(commit=hsh[:10], cdate=ci[:19], lst=ln2, sym=s["symbol"], added=s.get("added"), float=s.get("float"),
                                              sa=s.get("shares_available"), fee=s.get("borrow_fee"), bh=s.get("borrow_hist") or [], sec=s.get("sec_filings"),
                                              off=s.get("offering_event"), rs=s.get("recent_split")))
                elif fn == "company_cache.json":
                    for k, v in d.items():
                        if isinstance(v, dict) and v:
                            h.append(dict(commit=hsh[:10], cdate=ci[:19], sym=k, float=v.get("float"), float_asof=v.get("float_asof"), shares_out=v.get("shares_out")))
                else:
                    for k, v in d.items():
                        if isinstance(v, dict):
                            h.append(dict(commit=hsh[:10], cdate=ci[:19], sym=k, float=v.get("float"), date=v.get("date"), src=v.get("src")))
            json.dump(h, open(os.path.join(SCR, key), "w"))
        out[key] = h
    return out


def wl_full():
    """borrow_hist pairs need the full snapshots — re-read if the scratch rows lack them."""
    h = git_hist("wl_history.json")
    if h and "bh" in h[0] and isinstance(h[0]["bh"], list):
        return h
    return None


def sec_data():
    files = sorted(f for f in os.listdir(os.path.join(P.FM, "data")) if f.startswith("sec_") and f.endswith(".json.gz"))
    if not files:
        return None
    return json.load(gzip.open(os.path.join(P.FM, "data", files[-1]), "rt", encoding="utf-8"))


def ny_cutoff(T):
    return f"{T}T00:00:00-04:00/-05:00 (America/New_York)"


def sessions_between(a, b):
    ia, ib = L.cal_index(a), L.cal_index(b)
    if ia is None or ib is None:
        cal = L.calendar()
        ia = sum(1 for d in cal if d < a)
        ib = sum(1 for d in cal if d < b)
    return ib - ia


def row(base, **kw):
    r = dict(base)
    r.update(kw)
    return r


class Sources:
    """كلُّ المصادر محمَّلةً مرّةً (git · الحصاد · التقسيمات · SEC)."""

    def __init__(self):
        hist = build_hist()
        self.wl, self.cc, self.nwf = hist["wl_history.json"], hist["cc_history.json"], hist["nwf_history.json"]
        self.wlf = wl_full() or []
        self.ctb = P.ctb_log()
        self.splits = P.splits_yahoo()
        self.sec = sec_data()
        self.by_wl, self.by_cc, self.by_nwf, self.by_ctb, self.by_bh = (collections.defaultdict(list) for _ in range(5))
        for r in self.wl:
            self.by_wl[r["sym"]].append(r)
        for r in self.cc:
            self.by_cc[r["sym"]].append(r)
        for r in self.nwf:
            self.by_nwf[r["sym"]].append(r)
        for r in self.ctb:
            self.by_ctb[r["symbol"]].append(r)
        for r in self.wlf:
            for d, v in (r.get("bh") or []):
                self.by_bh[r["sym"]].append((d, v, r["cdate"]))


def feature_rows(S, base, sym, T):
    """صفوفُ الجرد للورقة sym عند يوم القرار T (القيمُ بعتادٍ قبل T حصرًا)."""
    out = []
    by_wl, by_cc, by_nwf, by_ctb, by_bh, splits, sec = S.by_wl, S.by_cc, S.by_nwf, S.by_ctb, S.by_bh, S.splits, S.sec
    # ---- A float
    cands = []
    for r in by_wl[sym]:
        if r["float"] and r["cdate"][:10] < T:
            cands.append(("S01", r["float"], r["cdate"][:10], r["cdate"], f"wl:{r['commit']}"))
    firsts = {}
    for r in sorted(by_cc[sym], key=lambda x: x["cdate"]):
        if r["float"] and r["float"] not in firsts:
            firsts[r["float"]] = r
    for v, r in firsts.items():
        if r["cdate"][:10] < T:
            cands.append(("S02", v, (r["float_asof"] or r["cdate"][:10]), r["cdate"], f"cc:{r['commit']}"))
    for r in by_nwf[sym]:
        if r["float"] and r["date"] and r["date"] < T:
            cands.append(("S03", r["float"], r["date"], r["cdate"], f"nwf:{r['commit']}"))
    if cands:
        s, v, vd, rec, rid = max(cands, key=lambda c: c[2])
        out.append(row(base, FEATURE_FAMILY="A_FLOAT", FEATURE_NAME="FLOAT_SHARES", VALUE=v, VALUE_DATE=vd, SOURCE=s, SOURCE_RECORD_ID=rid, SOURCE_RECORD_DATE=rec,
                       SOURCE_PUBLICATION_TIMESTAMP="unknown (vendor)", SOURCE_RETRIEVAL_TIMESTAMP=rec, HISTORICAL_VALUE_DATE=vd, DATA_VINTAGE="point-in-time (git)",
                       POINT_IN_TIME_VERIFIED=1, LOOKAHEAD_SAFE=1, AVAILABILITY_CONFIDENCE=("HIGH" if s in ("S01", "S03") else "MEDIUM"), MISSING_REASON="", DATA_QUALITY="vendor floatShares; shares_outstanding fallback not used",
                       N_CANDIDATE_RECORDS=len(cands), DAYS_VALUE_TO_DECISION=(dt.date.fromisoformat(T) - dt.date.fromisoformat(vd)).days))
    else:
        any_later = any(r["float"] for r in by_wl[sym] + by_cc[sym] + by_nwf[sym])
        out.append(row(base, FEATURE_FAMILY="A_FLOAT", FEATURE_NAME="FLOAT_SHARES", VALUE="", VALUE_DATE="", SOURCE="S01/S02/S03", SOURCE_RECORD_ID="", SOURCE_RECORD_DATE="",
                       SOURCE_PUBLICATION_TIMESTAMP="", SOURCE_RETRIEVAL_TIMESTAMP="", HISTORICAL_VALUE_DATE="", DATA_VINTAGE="", POINT_IN_TIME_VERIFIED=0, LOOKAHEAD_SAFE="",
                       AVAILABILITY_CONFIDENCE="NONE", MISSING_REASON=("NO_HISTORICAL_SOURCE" if not any_later else "NO_RECORD_FOUND"),
                       DATA_QUALITY=("value exists only after T (not usable)" if any_later else "no bot record"), N_CANDIDATE_RECORDS=0, DAYS_VALUE_TO_DECISION=""))
    # A' shares outstanding from SEC dei (vintage by `filed`)
    if sec and sym in sec["symbols"] and sec["symbols"][sym]["status"] == "ok":
        so = [x for x in sec["symbols"][sym]["shares_outstanding"] if x.get("filed") and x["filed"] < T and x.get("val")]
        if so:
            x = max(so, key=lambda z: (z["filed"], z.get("end") or ""))
            out.append(row(base, FEATURE_FAMILY="A_FLOAT", FEATURE_NAME="SHARES_OUTSTANDING_DEI", VALUE=x["val"], VALUE_DATE=x.get("end"), SOURCE="S07", SOURCE_RECORD_ID=x.get("accn"), SOURCE_RECORD_DATE=x["filed"],
                           SOURCE_PUBLICATION_TIMESTAMP=x["filed"], SOURCE_RETRIEVAL_TIMESTAMP=sec["meta"]["retrieved_utc"], HISTORICAL_VALUE_DATE=x.get("end"), DATA_VINTAGE="point-in-time (filed)",
                           POINT_IN_TIME_VERIFIED=1, LOOKAHEAD_SAFE=1, AVAILABILITY_CONFIDENCE="HIGH", MISSING_REASON="", DATA_QUALITY=f"{x.get('form')} cover page; shares outstanding ≠ float (upper bound)",
                           N_CANDIDATE_RECORDS=len(so), DAYS_VALUE_TO_DECISION=(dt.date.fromisoformat(T) - dt.date.fromisoformat(x["filed"])).days))
        else:
            out.append(row(base, FEATURE_FAMILY="A_FLOAT", FEATURE_NAME="SHARES_OUTSTANDING_DEI", VALUE="", VALUE_DATE="", SOURCE="S07", SOURCE_RECORD_ID="", SOURCE_RECORD_DATE="", SOURCE_PUBLICATION_TIMESTAMP="",
                           SOURCE_RETRIEVAL_TIMESTAMP=sec["meta"]["retrieved_utc"], HISTORICAL_VALUE_DATE="", DATA_VINTAGE="", POINT_IN_TIME_VERIFIED=0, LOOKAHEAD_SAFE="", AVAILABILITY_CONFIDENCE="NONE",
                           MISSING_REASON="NO_RECORD_FOUND", DATA_QUALITY="no dei:EntityCommonStockSharesOutstanding filed before T (foreign filers lack it)", N_CANDIDATE_RECORDS=0, DAYS_VALUE_TO_DECISION=""))
    # ---- B SEC offering status
    if sec is None:
        out.append(row(base, FEATURE_FAMILY="B_SEC_OFFERING", FEATURE_NAME="OFFERING_STATUS_AS_OF_DECISION", VALUE="", VALUE_DATE="", SOURCE="S07", SOURCE_RECORD_ID="", SOURCE_RECORD_DATE="",
                       SOURCE_PUBLICATION_TIMESTAMP="", SOURCE_RETRIEVAL_TIMESTAMP="", HISTORICAL_VALUE_DATE="", DATA_VINTAGE="", POINT_IN_TIME_VERIFIED=0, LOOKAHEAD_SAFE="",
                       AVAILABILITY_CONFIDENCE="NONE", MISSING_REASON="NOT_COLLECTED", DATA_QUALITY="SEC probe not yet run", N_CANDIDATE_RECORDS=0, DAYS_VALUE_TO_DECISION=""))
    else:
        rec = sec["symbols"].get(sym)
        if not rec or rec["status"] != "ok":
            out.append(row(base, FEATURE_FAMILY="B_SEC_OFFERING", FEATURE_NAME="OFFERING_STATUS_AS_OF_DECISION", VALUE="", VALUE_DATE="", SOURCE="S07", SOURCE_RECORD_ID="", SOURCE_RECORD_DATE="",
                           SOURCE_PUBLICATION_TIMESTAMP="", SOURCE_RETRIEVAL_TIMESTAMP=sec["meta"]["retrieved_utc"], HISTORICAL_VALUE_DATE="", DATA_VINTAGE="", POINT_IN_TIME_VERIFIED=0, LOOKAHEAD_SAFE="",
                           AVAILABILITY_CONFIDENCE="NONE", MISSING_REASON=("IDENTIFIER_UNRESOLVED" if (not rec or rec["status"] == "no_cik") else "SOURCE_CONFLICT"), DATA_QUALITY=(rec or {}).get("status", "no record"),
                           N_CANDIDATE_RECORDS=0, DAYS_VALUE_TO_DECISION=""))
        else:
            fil = [f for f in rec["filings"] if f.get("filingDate") and f["filingDate"] < T]
            offs = [f for f in fil if (f.get("form") or "").upper() in OFFERING_FORMS]
            last = max(offs, key=lambda f: f["filingDate"]) if offs else None
            fin = [f for f in offs if (f.get("form") or "").upper() in FINAL_PROSPECTUS]
            lastfin = max(fin, key=lambda f: f["filingDate"]) if fin else None
            days_last = (dt.date.fromisoformat(T) - dt.date.fromisoformat(last["filingDate"])).days if last else ""
            days_fin = (dt.date.fromisoformat(T) - dt.date.fromisoformat(lastfin["filingDate"])).days if lastfin else ""
            out.append(row(base, FEATURE_FAMILY="B_SEC_OFFERING", FEATURE_NAME="DAYS_SINCE_LAST_OFFERING_FORM", VALUE=days_last, VALUE_DATE=(last or {}).get("filingDate", ""), SOURCE="S07",
                           SOURCE_RECORD_ID=(last or {}).get("accessionNumber", ""), SOURCE_RECORD_DATE=(last or {}).get("filingDate", ""), SOURCE_PUBLICATION_TIMESTAMP=(last or {}).get("acceptanceDateTime", ""),
                           SOURCE_RETRIEVAL_TIMESTAMP=sec["meta"]["retrieved_utc"], HISTORICAL_VALUE_DATE=(last or {}).get("filingDate", ""), DATA_VINTAGE="point-in-time (filing)", POINT_IN_TIME_VERIFIED=1, LOOKAHEAD_SAFE=1,
                           AVAILABILITY_CONFIDENCE="HIGH", MISSING_REASON=("" if fil else "NO_RECORD_FOUND"), DATA_QUALITY=f"filings before T: {len(fil)} · offering-class forms: {len(offs)} · last form {(last or {}).get('form', '')}",
                           N_CANDIDATE_RECORDS=len(offs), DAYS_VALUE_TO_DECISION=days_last))
            out.append(row(base, FEATURE_FAMILY="B_SEC_OFFERING", FEATURE_NAME="DAYS_SINCE_LAST_FINAL_PROSPECTUS", VALUE=days_fin, VALUE_DATE=(lastfin or {}).get("filingDate", ""), SOURCE="S07",
                           SOURCE_RECORD_ID=(lastfin or {}).get("accessionNumber", ""), SOURCE_RECORD_DATE=(lastfin or {}).get("filingDate", ""), SOURCE_PUBLICATION_TIMESTAMP=(lastfin or {}).get("acceptanceDateTime", ""),
                           SOURCE_RETRIEVAL_TIMESTAMP=sec["meta"]["retrieved_utc"], HISTORICAL_VALUE_DATE=(lastfin or {}).get("filingDate", ""), DATA_VINTAGE="point-in-time (filing)", POINT_IN_TIME_VERIFIED=1, LOOKAHEAD_SAFE=1,
                           AVAILABILITY_CONFIDENCE="HIGH", MISSING_REASON=("" if fil else "NO_RECORD_FOUND"), DATA_QUALITY=f"final prospectuses (424B1/B4/B5) before T: {len(fin)}", N_CANDIDATE_RECORDS=len(fin), DAYS_VALUE_TO_DECISION=days_fin))
    # ---- C borrow availability
    bc = []
    for r in by_ctb[sym]:
        if r["date"] < T and r.get("shares_available") is not None:
            bc.append(("S04", r["shares_available"], r["date"], r.get("borrow_fee"), f"ctb:{r['date']}"))
    for d, v, cd in by_bh[sym]:
        if d and d < T and v is not None:
            bc.append(("S05", v, d, None, f"bh:{d}@{cd[:10]}"))
    for r in by_wl[sym]:
        if r.get("sa") is not None and r["cdate"][:10] < T:
            bc.append(("S01", r["sa"], r["cdate"][:10], r.get("fee"), f"wl:{r['commit']}"))
    if bc:
        s, v, vd, fee, rid = max(bc, key=lambda c: c[2])
        out.append(row(base, FEATURE_FAMILY="C_BORROW", FEATURE_NAME="AVAILABLE_SHARES", VALUE=v, VALUE_DATE=vd, SOURCE=s, SOURCE_RECORD_ID=rid, SOURCE_RECORD_DATE=vd, SOURCE_PUBLICATION_TIMESTAMP="IBKR snapshot ≤ harvest",
                       SOURCE_RETRIEVAL_TIMESTAMP=vd, HISTORICAL_VALUE_DATE=vd, DATA_VINTAGE="point-in-time snapshot", POINT_IN_TIME_VERIFIED=1, LOOKAHEAD_SAFE=1, AVAILABILITY_CONFIDENCE="HIGH",
                       MISSING_REASON="", DATA_QUALITY=f"fee={fee}; snapshots before T: {len(bc)}", N_CANDIDATE_RECORDS=len(bc), DAYS_VALUE_TO_DECISION=(dt.date.fromisoformat(T) - dt.date.fromisoformat(vd)).days))
    else:
        later = bool(by_ctb[sym] or by_bh[sym])
        out.append(row(base, FEATURE_FAMILY="C_BORROW", FEATURE_NAME="AVAILABLE_SHARES", VALUE="", VALUE_DATE="", SOURCE="S04/S05/S01", SOURCE_RECORD_ID="", SOURCE_RECORD_DATE="", SOURCE_PUBLICATION_TIMESTAMP="",
                       SOURCE_RETRIEVAL_TIMESTAMP="", HISTORICAL_VALUE_DATE="", DATA_VINTAGE="", POINT_IN_TIME_VERIFIED=0, LOOKAHEAD_SAFE="", AVAILABILITY_CONFIDENCE="NONE",
                       MISSING_REASON=("NO_HISTORICAL_SOURCE" if T <= "2026-07-30" or not later else "NO_RECORD_FOUND"), DATA_QUALITY=("snapshots exist only after T" if later else "no snapshot source before T"),
                       N_CANDIDATE_RECORDS=0, DAYS_VALUE_TO_DECISION=""))
    # ---- D reverse-split age
    sp = splits.get(sym)
    if sp is None:
        out.append(row(base, FEATURE_FAMILY="D_SPLIT_AGE", FEATURE_NAME="SESSIONS_SINCE_LAST_REVERSE_SPLIT", VALUE="", VALUE_DATE="", SOURCE="S06", SOURCE_RECORD_ID="", SOURCE_RECORD_DATE="2026-10-08", SOURCE_PUBLICATION_TIMESTAMP="",
                       SOURCE_RETRIEVAL_TIMESTAMP="2026-10-08", HISTORICAL_VALUE_DATE="", DATA_VINTAGE="CURRENT", POINT_IN_TIME_VERIFIED=0, LOOKAHEAD_SAFE="", AVAILABILITY_CONFIDENCE="NONE", MISSING_REASON="NOT_COLLECTED",
                       DATA_QUALITY="symbol not in the splits snapshot", N_CANDIDATE_RECORDS=0, DAYS_VALUE_TO_DECISION=""))
    else:
        rs = sorted([s for s in sp if s[0] < T and s[1] < 1], key=lambda s: s[0])
        # dedupe same ratio within 7 days (production rule SPLIT_DUP_DAYS)
        dd = []
        for d, r in rs:
            if dd and dd[-1][1] == r and (dt.date.fromisoformat(d) - dt.date.fromisoformat(dd[-1][0])).days <= 7:
                continue
            dd.append((d, r))
        conf = "MEDIUM"
        sec_conf = ""
        if sec and sym in sec["symbols"] and sec["symbols"][sym]["status"] == "ok" and dd:
            d0 = dt.date.fromisoformat(dd[-1][0])
            near = [f for f in sec["symbols"][sym]["filings"] if f.get("form", "").upper().startswith("8-K") and f.get("filingDate") and abs((dt.date.fromisoformat(f["filingDate"]) - d0).days) <= 21 and ("5.03" in (f.get("items") or "") or "3.03" in (f.get("items") or ""))]
            sec_conf = f"8-K item 5.03/3.03 within 21d: {len(near)}"
            if near:
                conf = "HIGH"
        if dd:
            d, r = dd[-1]
            out.append(row(base, FEATURE_FAMILY="D_SPLIT_AGE", FEATURE_NAME="SESSIONS_SINCE_LAST_REVERSE_SPLIT", VALUE=sessions_between(d, T), VALUE_DATE=d, SOURCE="S06", SOURCE_RECORD_ID=f"yahoo:{d}:{r}", SOURCE_RECORD_DATE="2026-10-08",
                           SOURCE_PUBLICATION_TIMESTAMP="unknown (vendor); SEC confirmation: " + (sec_conf or "not checked"), SOURCE_RETRIEVAL_TIMESTAMP="2026-10-08", HISTORICAL_VALUE_DATE=d,
                           DATA_VINTAGE="CURRENT snapshot of historical dates", POINT_IN_TIME_VERIFIED=int(conf == "HIGH"), LOOKAHEAD_SAFE=1, AVAILABILITY_CONFIDENCE=conf, MISSING_REASON="",
                           DATA_QUALITY=f"ratio={r}; reverse splits before T: {len(dd)} (raw {len(rs)}); calendar days {(dt.date.fromisoformat(T) - dt.date.fromisoformat(d)).days}", N_CANDIDATE_RECORDS=len(dd),
                           DAYS_VALUE_TO_DECISION=(dt.date.fromisoformat(T) - dt.date.fromisoformat(d)).days))
        else:
            out.append(row(base, FEATURE_FAMILY="D_SPLIT_AGE", FEATURE_NAME="SESSIONS_SINCE_LAST_REVERSE_SPLIT", VALUE="NO_CONFIRMED_PRIOR_REVERSE_SPLIT", VALUE_DATE="", SOURCE="S06", SOURCE_RECORD_ID="", SOURCE_RECORD_DATE="2026-10-08",
                           SOURCE_PUBLICATION_TIMESTAMP="", SOURCE_RETRIEVAL_TIMESTAMP="2026-10-08", HISTORICAL_VALUE_DATE="", DATA_VINTAGE="CURRENT snapshot", POINT_IN_TIME_VERIFIED=0, LOOKAHEAD_SAFE=1,
                           AVAILABILITY_CONFIDENCE="MEDIUM", MISSING_REASON="RECORD_NOT_APPLICABLE", DATA_QUALITY=f"splits listed (any): {len(sp)}; none reverse before T", N_CANDIDATE_RECORDS=0, DAYS_VALUE_TO_DECISION=""))
    return out


def main():
    man = P.read_csv(os.path.join(P.HERE, "PHASE5_COHORT_MANIFEST.csv"))
    cm = os.path.join(P.HERE, "PHASE5_MATCHED_CONTROL_MANIFEST.csv")
    extra = P.read_csv(cm) if os.path.exists(cm) else []
    units = []
    seen = set()
    for r in man:
        key = (r["SECURITY_ID"], r["DECISION_EPISODE_ID"])
        if key in seen:
            continue
        seen.add(key)
        units.append(dict(SECURITY_ID=r["SECURITY_ID"], DECISION_EPISODE_ID=r["DECISION_EPISODE_ID"], DECISION_DATE=r["EPISODE_START"], ROLE="POSITIVE", PHASE4_SET=r["PHASE4_SET"]))
    for c in extra:
        if (c["CONTROL"], c["CONTROL_EPISODE_ID"]) in seen:
            continue
        seen.add((c["CONTROL"], c["CONTROL_EPISODE_ID"]))
        units.append(dict(SECURITY_ID=c["CONTROL"], DECISION_EPISODE_ID=c["CONTROL_EPISODE_ID"], DECISION_DATE=c["MATCHING_DATE"], ROLE="CONTROL", PHASE4_SET=""))
    S = Sources()
    out = []
    for u in units:
        sym, T = u["SECURITY_ID"], u["DECISION_DATE"]
        base = dict(SECURITY_ID=sym, DECISION_EPISODE_ID=u["DECISION_EPISODE_ID"], DECISION_DATE=T, ROLE=u["ROLE"], DECISION_TIMESTAMP=f"{T} (session date; post time unknown)",
                    DECISION_TIMEZONE="America/New_York", DATA_CUTOFF_TIMESTAMP=f"{T} 00:00 America/New_York (bars < T; sources with record date <= T-1 or publication <= T)")
        out += feature_rows(S, base, sym, T)
    P.write_csv(os.path.join(P.HERE, "PHASE5_FEATURE_AVAILABILITY.csv"), out)
    led = [dict(SOURCE_ID=k, **v) for k, v in SOURCES.items()]
    P.write_csv(os.path.join(P.HERE, "PHASE5_SOURCE_LEDGER.csv"), led)
    summ = collections.Counter()
    for r in out:
        summ[(r["ROLE"], r["FEATURE_FAMILY"], r["FEATURE_NAME"], "AVAILABLE" if r["VALUE"] != "" and r["MISSING_REASON"] == "" else (r["MISSING_REASON"] or "AVAILABLE"))] += 1
    print(f"units {len(units)} (positives {sum(1 for u in units if u['ROLE'] == 'POSITIVE')} · controls {sum(1 for u in units if u['ROLE'] == 'CONTROL')}) · rows {len(out)}")
    for k in sorted(summ):
        print(f"  {k[0]:8} {k[1]:15} {k[2]:36} {k[3]:28} {summ[k]}")
    print("SEC probe:", "present" if S.sec else "absent")


if __name__ == "__main__":
    main()
