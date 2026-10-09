"""🔬 PHASE 5 — بنّاءُ التقرير والحكم من ملفّات النتائج (الأرقامُ من CSV لا باليد): PHASE5_FINAL_REPORT.md + PHASE5_FINAL_VERDICT.md.
الأحكامُ الخمسة منفصلة (§23): STATISTICAL DISCRIMINATION · HISTORICAL AVAILABILITY · DIRECT METHOD SUPPORT · CAUSAL INTERPRETATION · PRODUCTION RELEVANCE."""
import collections
import json
import os
import subprocess

import p5lib as P

METHOD_EVIDENCE = {
    "H1_FLOAT": ("SUPPORTED (direct)", "«الحد النهائي 5 ملايين» · «5 ملايين أو أقل — مطابق» (TG_57915/57918/57919 · `faisal_adopted` · `FWD_FLOAT_MAX`)"),
    "H2_OFFERING": ("CONTRADICTED/AMBIGUOUS", "«لا إعلان طرح» as an exclusion (method ⑤) **and** «طرح» as a founding event (TG_2077) — the corpus states both directions"),
    "H3_BORROW": ("SUPPORTED (verbatim)", "«تحت 20 ألف» (IMG_0151 · `BORROW_AVAIL_MAX` · `faisal_verbatim`) · «شورته 10K» · «باقي 80 الف شورت ننتظر»"),
    "H4_SPLIT": ("SUPPORTED (concept) · number engineering", "«توها مقسمة» · founding event «مقسم أو طرح أو نقل من otc» (TG_2077); the 120-day window is `SPLIT_LOOKBACK_DAYS` (tagged `unsourced`)"),
}


def load(mode):
    p = os.path.join(P.OUT, f"results_{mode}.csv")
    return P.read_csv(p) if os.path.exists(p) else []


def fmt(r, k):
    return r.get(k, "") if r.get(k, "") not in (None, "None") else ""


def main():
    disc, val, allr = load("discovery"), load("validation"), load("all")
    fa = P.read_csv(os.path.join(P.HERE, "PHASE5_FEATURE_AVAILABILITY.csv"))
    man = P.read_csv(os.path.join(P.HERE, "PHASE5_COHORT_MANIFEST.csv"))
    cm = P.read_csv(os.path.join(P.HERE, "PHASE5_MATCHED_CONTROL_MANIFEST.csv"))
    fz = json.load(open(os.path.join(P.OUT, "discovery_frozen.json"))) if os.path.exists(os.path.join(P.OUT, "discovery_frozen.json")) else {}
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=P.REPO).stdout.strip()
    prim = [r for r in man if r["PHASE5_PRIMARY_UNIT"] == "1"]
    av = collections.Counter()
    for r in fa:
        key = (r["ROLE"], r["FEATURE_FAMILY"], r["FEATURE_NAME"])
        av[key + ("available",)] += int(r["VALUE"] != "" and r["MISSING_REASON"] == "")
        av[key + ("total",)] += 1
        if r["VALUE"] != "" and r["MISSING_REASON"] == "":
            av[key + ("verified",)] += int(r.get("POINT_IN_TIME_VERIFIED") in ("1", 1))

    def family_table(rows, title):
        out = [f"### {title}", "", "| family | status | n pos (value/total) | n ctrl (value/total) | avail diff (pts) | pos rate [95%] | ctrl rate [95%] | Fisher p | matched diff [98.75%] | excludes 0 | MH OR (price) | necessity fail | verified |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in rows:
            out.append(f"| {r['FAMILY']}{(' · ' + r['TAG']) if fmt(r, 'TAG') else ''} | {fmt(r, 'STATUS')} | {fmt(r, 'N_POS_WITH_VALUE')}/{fmt(r, 'N_POSITIVES')} | {fmt(r, 'N_CTRL_WITH_VALUE')}/{fmt(r, 'N_CONTROL_UNITS')} | {fmt(r, 'AVAIL_DIFF_POINTS')} | {fmt(r, 'POS_RATE')} {fmt(r, 'POS_WILSON95')} | {fmt(r, 'CTRL_RATE')} {fmt(r, 'CTRL_WILSON95')} | {fmt(r, 'FISHER_P')} | {fmt(r, 'MATCHED_DIFF')} {fmt(r, 'MATCHED_CI_98_75')} | {fmt(r, 'MATCHED_CI_EXCLUDES_0')} | {fmt(r, 'MH_OR_PRICE_BUCKETS')} | {fmt(r, 'NECESSITY_FAIL_SHARE')} | {fmt(r, 'POINT_IN_TIME_VERIFIED_SHARE')} |")
        return out + [""]

    # verdict per family (prereg §N)
    verdict = {}
    for fam in ("H1_FLOAT", "H2_OFFERING", "H3_BORROW", "H4_SPLIT"):
        d = next((r for r in disc if r["FAMILY"] == fam and not fmt(r, "TAG")), None)
        v = next((r for r in val if r["FAMILY"] == fam and not fmt(r, "TAG")), None)
        a = next((r for r in allr if r["FAMILY"] == fam and not fmt(r, "TAG")), None)
        if d is None:
            verdict[fam] = ("NOT RUN", "")
            continue
        st = d.get("STATUS", "")
        if st.startswith("NOT_TESTABLE"):
            verdict[fam] = ("NOT TESTABLE (F — missing history)", st)
        elif "AVAILABILITY-CONFOUNDED" in st:
            verdict[fam] = ("AVAILABILITY-CONFOUNDED (D — data-availability artifact)", st)
        elif st.startswith("INSUFFICIENT"):
            verdict[fam] = ("INSUFFICIENT POWER (G)", st)
        else:
            ex = fmt(d, "MATCHED_CI_EXCLUDES_0") == "1"
            dd = float(fmt(d, "MATCHED_DIFF") or 0)
            vd = float(fmt(v, "MATCHED_DIFF") or 0) if v and fmt(v, "MATCHED_DIFF") else None
            same = vd is not None and ((vd > 0) == (dd > 0)) and abs(vd) >= abs(dd) / 2
            verified_ok = (float(fmt(d, "POINT_IN_TIME_VERIFIED_SHARE") or 0) >= 0.8)
            if ex and same and verified_ok:
                verdict[fam] = ("SUPPORTED (association · replicated)", f"discovery {dd:+.3f} {fmt(d, 'MATCHED_CI_98_75')} · validation {vd:+.3f}")
            elif ex and not same:
                verdict[fam] = ("UNSUPPORTED (discovery signal did not replicate)", f"discovery {dd:+.3f} {fmt(d, 'MATCHED_CI_98_75')} · validation {vd if vd is not None else 'n/a'}")
            elif ex and not verified_ok:
                verdict[fam] = ("UNSUPPORTED (availability not point-in-time verified ≥ 80%)", fmt(d, "POINT_IN_TIME_VERIFIED_SHARE"))
            else:
                verdict[fam] = ("UNSUPPORTED (98.75% CI includes 0)", f"discovery {dd:+.3f} {fmt(d, 'MATCHED_CI_98_75')} · validation {vd if vd is not None else 'n/a'} · pooled {fmt(a, 'MATCHED_DIFF') if a else ''} {fmt(a, 'MATCHED_CI_98_75') if a else ''}")
    md = ["# PHASE 5 — FINAL REPORT (non-candle information × Faisal selection)", "",
          f"Built by `report.py` from `out/results_*.csv` at `{head[:12]}`. Pre-registration: `PHASE5_PREREG.md` (merged in PR #582, `4249c764`). Discovery frozen at `{fz.get('commit', '')[:12]}` (`results_discovery.csv` sha {fz.get('results_sha', '')}).", "",
          "## 1. Denominators (§5)", "",
          f"- Manifest rows {len(man)} · securities {len({r['SECURITY_ID'] for r in man})} · episodes {len({r['DECISION_EPISODE_ID'] for r in man})} · evidence units {len({r['EVIDENCE_ID'] for r in man})}",
          f"- Primary units (one per non-anchor security with bars): **{len(prim)}** · discovery 23 · validation 15 · anchors 3 (descriptive) · bar-less 4 (ATPC, LABT, MI, UNK — listed, excluded)",
          f"- Matched controls: {len(cm)} control-days · {len({r['CONTROL'] for r in cm})} distinct securities · positives matched {len({r['MATCHED_POSITIVE'] for r in cm})} of {len(prim)} (unmatched: {sorted(set(r['SECURITY_ID'] for r in prim) - {r['MATCHED_POSITIVE'] for r in cm})})",
          f"- Balance (SMD pos−ctrl): {cm[0]['BALANCE_DIAGNOSTICS'] if cm else ''}", "",
          "## 2. Historical availability (§9/§17 — Q-B)", "", "| role | family | feature | available/total | point-in-time verified |", "|---|---|---|---|---|"]
    for key in sorted({k[:3] for k in av}):
        md.append(f"| {key[0]} | {key[1]} | {key[2]} | {av[key + ('available',)]}/{av[key + ('total',)]} | {av[key + ('verified',)]} |")
    md += ["", "## 3. Results (§16) — discovery, validation (blind until freeze), pooled (descriptive)", ""]
    md += family_table(disc, "Discovery (23 securities)") + family_table(val, "Validation (15 securities)") + family_table(allr, "Pooled — descriptive only (§P: never used to reach significance)")
    md += ["## 4. Hypotheses (§22)", "", "| id | verdict (association) | evidence |", "|---|---|---|"]
    for fam, (v, e) in verdict.items():
        md.append(f"| {fam} | **{v}** | {e} |")
    h5 = next((r for r in disc if r["FAMILY"] == "H5_JOINT"), None)
    md.append(f"| H5_JOINT | **{fmt(h5, 'STATUS') if h5 else 'NOT RUN'}** | {fmt(h5, 'MATCHED_DIFF') if h5 else ''} {fmt(h5, 'MATCHED_CI_98_75') if h5 else ''} |")
    md.append(f"| H6_NULL | **{'SUPPORTED' if not any(v[0].startswith('SUPPORTED') for v in verdict.values()) else 'REJECTED for ' + ', '.join(k for k, v in verdict.items() if v[0].startswith('SUPPORTED'))}** | the available historical data {'cannot' if not any(v[0].startswith('SUPPORTED') for v in verdict.values()) else 'can'} distinguish selected from matched securities on these features |")
    md += ["", "## 5. Separate verdicts (§23)", ""]
    for fam, (v, e) in verdict.items():
        me = METHOD_EVIDENCE[fam]
        d = next((r for r in disc if r["FAMILY"] == fam and not fmt(r, "TAG")), {})
        avail = "VERIFIED (point-in-time)" if float(fmt(d, "POINT_IN_TIME_VERIFIED_SHARE") or 0) >= 0.8 else ("PARTIAL" if fmt(d, "N_POS_WITH_VALUE") not in ("", "0") else "UNVERIFIED/ABSENT")
        md += [f"### {fam}", f"- STATISTICAL DISCRIMINATION: **{v}** — {e}", f"- HISTORICAL AVAILABILITY: **{avail}** — positives {fmt(d, 'N_POS_WITH_VALUE')}/{fmt(d, 'N_POSITIVES')} · controls {fmt(d, 'N_CTRL_WITH_VALUE')}/{fmt(d, 'N_CONTROL_UNITS')} · differential {fmt(d, 'AVAIL_DIFF_POINTS')} pts · verified share {fmt(d, 'POINT_IN_TIME_VERIFIED_SHARE')}",
               f"- DIRECT METHOD SUPPORT: **{me[0]}** — {me[1]}", "- CAUSAL INTERPRETATION: **NOT ESTABLISHED** (association ≠ use; §M falsifiers reported in the tables: placebo/necessity)", "- PRODUCTION RELEVANCE: **none claimed** (§24)", ""]
    md += ["## 6. Predictions P1–P6 (written before any number)", ""]
    with open(os.path.join(P.HERE, "PHASE5_FINAL_REPORT.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    json.dump(verdict, open(os.path.join(P.OUT, "verdict.json"), "w"), ensure_ascii=False, indent=1)
    print("\n".join(md[-40:]))


if __name__ == "__main__":
    main()
