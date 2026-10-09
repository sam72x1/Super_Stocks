"""🔬 PHASE 5 — حساسيّةٌ لاحقة (POST-HOC · غيرُ تأكيديّة · `PHASE5_PREREG_AMENDMENT.md` A1): H4 على المُودِعين المحلّيّين وحدَهم (8-K/10-Q)
حيث تأكيدُ SEC للتقسيم ممكن — لأن معيارَ §N «≥ 80% مُتحقَّق» يسقط بالبناء على المُودِعين الأجانب (6-K) لا على البيانات."""
import collections
import glob
import gzip
import json
import os

import analysis as A
import p5lib as P


def filer_type(sec, s):
    r = sec.get(s)
    if not r or r["status"] != "ok":
        return "no_cik"
    forms = collections.Counter(f["form"] for f in r["filings"])
    return "foreign" if (forms["6-K"] + forms["20-F"]) > (forms["8-K"] + forms["10-Q"]) else "domestic"


def main():
    sec = json.load(gzip.open(sorted(glob.glob(os.path.join(P.FM, "data", "sec_*.json.gz")))[-1], "rt"))["symbols"]
    man, prim, disc, val = A.sets()
    pdate = {r["SECURITY_ID"]: r["DECISION_DATE"] for r in man if r["PHASE5_PRIMARY_UNIT"] == "1"}
    cm = P.read_csv(os.path.join(P.HERE, "PHASE5_MATCHED_CONTROL_MANIFEST.csv"))
    fa = P.read_csv(os.path.join(P.HERE, "PHASE5_FEATURE_AVAILABILITY.csv"))
    rows_by_unit = collections.defaultdict(list)
    for r in fa:
        rows_by_unit[f"{r['SECURITY_ID']}|{r['DECISION_DATE']}"].append(r)
    out = []
    for mode, sel in (("discovery", disc), ("validation", val), ("all", prim)):
        ctrl_by_pos = collections.defaultdict(list)
        for r in cm:
            if filer_type(sec, r["CONTROL"]) == "domestic":
                ctrl_by_pos[f"{r['MATCHED_POSITIVE']}|{r['MATCHING_DATE']}"].append(f"{r['CONTROL']}|{r['MATCHING_DATE']}")
        units = [f"{t}|{pdate[t]}" for t in sel if filer_type(sec, t) == "domestic"]
        A.analyse(mode, "H4_SPLIT", units, ctrl_by_pos, rows_by_unit, out, tag="POST-HOC domestic filers only (A1)")
    P.write_csv(os.path.join(P.OUT, "results_posthoc_h4_domestic.csv"), out)
    for r in out:
        print({k: r.get(k) for k in ("MODE", "N_POSITIVES", "N_POS_WITH_VALUE", "N_CTRL_WITH_VALUE", "N_MATCHED_STRATA", "POS_RATE", "CTRL_RATE", "MATCHED_DIFF", "MATCHED_CI_98_75", "MATCHED_CI_EXCLUDES_0", "POINT_IN_TIME_VERIFIED_SHARE", "STATUS")})


if __name__ == "__main__":
    main()
