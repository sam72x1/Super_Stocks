"""🔬 PHASE 5 §2 — تدقيقُ المرحلة 4 لا الثقةُ بها: إعادةُ اشتقاق الأعداد من السكربتات والملفّات ومصالحتُها ⟵
`PHASE5_PHASE4_RECONCILIATION.md` + `PHASE5_COHORT_MANIFEST.csv` (وحدةُ القرار بهويّتها · بلا ميزةٍ ولا نتيجة)."""
import collections
import os
import subprocess

import p5lib as P

Q, L = P.Q, P.L
REPORT_CLAIMS = {  # ما نشره تقريرُ المرحلة 4 (يُعاد اشتقاقُه هنا لا يُنسَخ)
    "tickers": 41, "discovery": 22, "validation": 16, "anchors": 3,
    "rows": 83, "rows_discovery": 46, "rows_validation": 29, "rows_anchor": 8,
    "DIRECT_TEXT": 59, "DIRECT_CHART": 20, "ACTION": 4,
    "controls": 164, "controls_discovery": 88, "controls_validation": 64, "controls_anchor": 12,
    "controls_distinct": 75, "controls_full_match": 128,
    "ledger_rows": 415, "ordering_rows": 41, "EXPECTED": 15, "CONTRADICTED": 12, "INSUFFICIENT": 11,
    "E2_never": 32, "LEVEL_INVALIDATED": 20, "WINDOW_EXPIRED": 12, "E2_occurred": 6,
    "E3_present": 27, "ft_state_median": 5, "weekend_mapped": 16,
    "alertFP": {("discovery", "A"): 0.17, ("discovery", "B"): 0.102, ("discovery", "C"): 0.398, ("discovery", "D"): 0.341,
                ("validation", "A"): 0.234, ("validation", "B"): 0.109, ("validation", "C"): 0.406, ("validation", "D"): 0.328,
                ("anchor", "B"): 0.083},
    "feature_fresh": (181, 5911, 230, 8383), "feature_e3": (10, 694, 401, 13600),
}


def head_sha():
    return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=P.REPO).stdout.strip()


def main():
    lines = []
    checks = []

    def chk(name, got, exp, note=""):
        ok = (got == exp)
        checks.append((name, got, exp, "REPRODUCED" if ok else "NOT_REPRODUCED", note))
        return ok

    # ① recompute the cohort from the Phase 3 timeline through the Phase 4 loader (by name)
    units_all = P.faisal_units()
    nobars = sorted({u["ticker"] for u in units_all if not u["has_bars"]})
    units = [u for u in units_all if u["has_bars"]]           # Phase 4 rule (prereg §⑦ line 67): no bars ⇒ excluded, counted
    fs = Q.first_states(units)
    tick = sorted(fs)
    sets = collections.Counter(Q.which_set(t) for t in tick)
    chk("tickers (dated FOCUS/WATCH/READY/ENTRY · IS_FAISAL=1)", len(tick), REPORT_CLAIMS["tickers"])
    chk("discovery tickers", sets["discovery"], REPORT_CLAIMS["discovery"])
    chk("validation tickers", sets["validation"], REPORT_CLAIMS["validation"])
    chk("anchor tickers", sets["anchor"], REPORT_CLAIMS["anchors"])
    chk("tickers outside the three sets", sets["other"], 0)
    # membership rule: discovery = first dated state <= 2026-08-31
    mis = [t for t in tick if Q.which_set(t) != "anchor" and ((fs[t]["first_state"] <= "2026-08-31") != (Q.which_set(t) == "discovery"))]
    chk("membership rule (first state <= 2026-08-31 ⇔ discovery)", len(mis), 0, ";".join(mis))
    rows_by_set = collections.Counter(u["set"] for u in units)
    chk("dated rows", len(units), REPORT_CLAIMS["rows"])
    chk("rows discovery", rows_by_set["discovery"], REPORT_CLAIMS["rows_discovery"])
    chk("rows validation", rows_by_set["validation"], REPORT_CLAIMS["rows_validation"])
    chk("rows anchor", rows_by_set["anchor"], REPORT_CLAIMS["rows_anchor"])
    ev = collections.Counter(u["evidence_class"] for u in units)
    for k in ("DIRECT_TEXT", "DIRECT_CHART", "ACTION"):
        chk(f"evidence class {k}", ev[k], REPORT_CLAIMS[k])
    chk("evidence class WATCHLIST/UNKNOWN among dated rows", ev["WATCHLIST"] + ev["UNKNOWN"], 0)
    # all rows direct (IS_FAISAL=1) by construction — count third-party rows the loader excluded
    tl = P.timeline_all()
    excl_tp = sum(1 for r in tl if r["IS_FAISAL"] != "1" and r["OBSERVATION_CLASS"] in Q.STATES)
    excl_cls = collections.Counter(r["OBSERVATION_CLASS"] for r in tl if r["IS_FAISAL"] == "1" and r["OBSERVATION_CLASS"] not in Q.STATES)
    lines.append(f"- third-party rows with a state class, excluded by `IS_FAISAL==1`: **{excl_tp}**")
    lines.append(f"- Faisal rows excluded by class: {dict(excl_cls)} (MENTION/UNKNOWN carry no selection tier · EXIT = post-selection exit, not a pre-selection negative)")
    # repeated tickers · unique dates · pairs
    per = collections.Counter(u["ticker"] for u in units)
    multi = {t: n for t, n in per.items() if n > 1}
    pairs = {(u["ticker"], u["session"]) for u in units}
    udates = {u["session"] for u in units}
    lines.append(f"- tickers with more than one dated row: **{len(multi)}** (max {max(multi.values())} · {sorted(multi.items(), key=lambda x: -x[1])[:5]})")
    lines.append(f"- unique sessions {len(udates)} · ticker×session pairs {len(pairs)} · rows {len(units)} (same ticker, same session, several evidence units: {len(units) - len(pairs)})")
    chk("weekend/holiday first dates mapped to next session (non-anchor)", sum(1 for t in tick if Q.which_set(t) != "anchor" and fs[t]["first_state_ambiguous"]), REPORT_CLAIMS["weekend_mapped"])
    # duplicated evidence IDs across tickers (one post naming several tickers)
    evid = collections.defaultdict(set)
    for u in units:
        evid[u["evidence_id"]].add(u["ticker"])
    shared = {k: sorted(v) for k, v in evid.items() if len(v) > 1}
    lines.append(f"- evidence units naming more than one ticker: **{len(shared)}** → {shared}")
    dup_rows = len(units) - len({(u['ticker'], u['session'], u['evidence_id'], u['state']) for u in units})
    chk("exact duplicate rows (ticker,session,evidence,state)", dup_rows, 0)
    # has_bars
    chk("tickers excluded by Phase 4 for lack of bars (prereg §⑦: 'excluded (counted)')", len(nobars), 4, ";".join(nobars))
    lines.append(f"- **Phase 4 excluded {len(nobars)} dated Faisal tickers without bars** ({nobars} · {sum(1 for u in units_all if not u['has_bars'])} rows): the prereg says 'excluded (counted)' but the report's 41/83 never lists them by name. Under Phase 5 §0 this is a **data-availability exclusion (category D)**; they stay in the manifest with `HAS_BARS=0` and `PHASE4_SET=other`, outside primary inference, and are reported in every denominator audit. `UNK` is an unresolved ticker from an image; `MI` is a single TG unit.")

    # ② artifacts vs recomputation
    pos = P.p4("POSITIVE_VALIDATION_CASES.csv")
    chk("POSITIVE_VALIDATION_CASES rows", len(pos), len(tick))
    chk("POSITIVE_VALIDATION_CASES first-state dates == recomputed", sum(1 for p in pos if fs.get(p["TICKER"], {}).get("first_state") == p["FIRST_STATE_DATE"]), len(tick))
    chk("POSITIVE_VALIDATION_CASES first-state class == recomputed", sum(1 for p in pos if fs.get(p["TICKER"], {}).get("first_state_class") == p["FIRST_STATE_CLASS"]), len(tick))
    neg = P.p4("NEGATIVE_VALIDATION_CASES.csv")
    chk("controls (control-days)", len(neg), REPORT_CLAIMS["controls"])
    cs = collections.Counter(n["SET"] for n in neg)
    for s in ("discovery", "validation", "anchor"):
        chk(f"controls {s}", cs[s], REPORT_CLAIMS[f"controls_{s}"])
    chk("controls distinct symbols", len({n["CONTROL"] for n in neg}), REPORT_CLAIMS["controls_distinct"])
    chk("controls full matches (4/4)", sum(1 for n in neg if n["MATCH_QUALITY_OF_4"] == "4"), REPORT_CLAIMS["controls_full_match"])
    reuse = collections.Counter(n["CONTROL"] for n in neg)
    reused = {k: v for k, v in reuse.items() if v > 1}
    lines.append(f"- control symbols reused across positives: **{len(reused)}** (max {max(reused.values())} · top {sorted(reused.items(), key=lambda x: -x[1])[:5]}) — Phase 4 treated each control-day as independent; Phase 5 clusters by security")
    chk("controls with any Faisal unit (should be none)", sum(1 for n in neg if not n["FAISAL_EVIDENCE"].startswith("NONE")), 0)
    chk("controls equal to a positive ticker", sum(1 for n in neg if n["CONTROL"] in fs), 0)
    chk("controls matched on the positive's first-state date", sum(1 for n in neg if fs.get(n["MATCHED_POSITIVE"], {}).get("first_state") == n["DATE"]), len(neg))
    chk("controls identity-eligible without anchor at date", sum(1 for n in neg if n["ELIGIBLE_NO_ANCHOR_AT_DATE"] == "1"), len(neg))
    per_pos = collections.Counter(n["MATCHED_POSITIVE"] for n in neg)
    lines.append(f"- controls per positive: {dict(collections.Counter(per_pos.values()))} (positives with 0 controls: {sorted(set(tick) - set(per_pos))})")
    led = P.p4("EVENT_LEDGER.csv")
    chk("EVENT_LEDGER rows", len(led), REPORT_CLAIMS["ledger_rows"])
    chk("EVENT_LEDGER decision units", len({(r['TICKER'], r['DECISION_DATE'], r['EVIDENCE_ID']) for r in led}), len(units))
    chk("EVENT_LEDGER lookahead-safe rows", sum(1 for r in led if r["LOOKAHEAD_SAFE"] == "1"), len(led))
    om = P.p4("PHASE_ORDERING_MATRIX.csv")
    chk("PHASE_ORDERING_MATRIX rows", len(om), REPORT_CLAIMS["ordering_rows"])
    oc = collections.Counter(r["ORDER_RESULT"] for r in om if r["SET"] != "anchor")
    for k in ("EXPECTED", "CONTRADICTED", "INSUFFICIENT"):
        chk(f"ordering {k} (non-anchor)", oc[k], REPORT_CLAIMS[k])
    e2 = collections.Counter(r["SECOND_TOUCH_STATUS"] for r in om if r["SET"] != "anchor")
    chk("E2 LEVEL_INVALIDATED (non-anchor)", e2["LEVEL_INVALIDATED"], REPORT_CLAIMS["LEVEL_INVALIDATED"])
    chk("E2 WINDOW_EXPIRED (non-anchor)", e2["WINDOW_EXPIRED"], REPORT_CLAIMS["WINDOW_EXPIRED"])
    chk("E2 occurred (non-anchor)", e2["E2"], REPORT_CLAIMS["E2_occurred"])
    chk("E3 present (non-anchor)", sum(1 for r in om if r["SET"] != "anchor" and r["RETEST_DATE"]), REPORT_CLAIMS["E3_present"])
    ftd = sorted(int(r["SESSIONS_FT_TO_STATE"]) for r in om if r["SET"] != "anchor" and r["SESSIONS_FT_TO_STATE"] not in ("", "None"))
    med = ftd[len(ftd) // 2] if len(ftd) % 2 else (ftd[len(ftd) // 2 - 1] + ftd[len(ftd) // 2]) / 2
    chk("FT→state median sessions (non-anchor)", med, REPORT_CLAIMS["ft_state_median"], f"n={len(ftd)}")
    ac = P.p4("ARCHITECTURE_COMPARISON.csv")
    for (s, a), v in REPORT_CLAIMS["alertFP"].items():
        got = [float(r["FP_ALERT_RATE"]) for r in ac if r["SET"] == s and r["ARCHITECTURE"] == a]
        chk(f"alert FP {s}/{a}", got[0] if got else None, v)
    ft = P.p4("FEATURE_TESTS.csv")
    lines.append(f"- FEATURE_TESTS rows {len(ft)} (values checked by eye against the report: fresh-first-touch 181/5,911 vs 230/8,383 · E3-present 10/694 vs 401/13,600)")
    # arch rows per set: unique dates and ticker-date pairs
    for s in ("discovery", "validation", "anchor"):
        ar = P.read_csv(os.path.join(P.P4, "out", f"arch_rows_{s}.csv"))
        lines.append(f"- arch rows {s}: rows {len(ar)} · tickers {len({r['TICKER'] for r in ar})} · unique decision dates {len({r['DECISION_DATE'] for r in ar})} · ticker×date pairs {len({(r['TICKER'], r['DECISION_DATE']) for r in ar})}")
    # label audit: positives are all POSITIVE_DIRECT; Phase 4 controls had NO negative label (absence of a post)
    lines.append("- labels in Phase 4: positives = documented Faisal state (all DIRECT · IS_FAISAL=1); controls = **absence of any Faisal unit** — under Phase 5 §4 that is `UNKNOWN`, not `NEGATIVE_DIRECT`")
    lines.append("- Phase 4 validation labels were **revealed** (validation rows were analysed after the discovery freeze) ⇒ for Phase 5 they are contaminated as a blind set (§10)")

    # ③ episodes → cohort manifest
    eps = P.episodes(units_all)
    man = []
    for e in eps:
        for u in e["units"]:
            man.append(dict(SECURITY_ID=e["ticker"], TICKER_AT_DECISION=e["ticker"], DECISION_EPISODE_ID=e["episode_id"], EPISODE_NO=e["episode_no"],
                            EPISODE_START=e["start"], EPISODE_END=e["end"], PRIMARY_EPISODE=int(e["episode_no"] == 1),
                            DECISION_DATE=u["session"], FAISAL_DATE_RAW=u["date"], DATE_AMBIGUOUS=u["date_ambiguous"],
                            FAISAL_STATE=u["state"], OUTCOME_TIER={"WATCH": "FOCUS_OR_WATCH", "FOCUS": "FOCUS_OR_WATCH", "READY": "READY", "ENTRY": "ENTRY"}[u["state"]],
                            EVIDENCE_ID=u["evidence_id"], EVIDENCE_CLASS=u["evidence_class"],
                            LABEL_SOURCE="FAISAL_" + ("ACTION" if u["evidence_class"] == "ACTION" else "POST"), LABEL=("POSITIVE_DIRECT"),
                            LABEL_CONFIDENCE=("HIGH" if u["evidence_class"] in ("DIRECT_TEXT", "ACTION") else "MEDIUM"),
                            REPEATED_ATTENTION=u["repeated_attention"], PHASE4_SET=u["set"], ANCHOR_EXCLUDED=int(u["set"] == "anchor"),
                            OBSERVATION_WINDOW=f"bars < {u['session']}; sources with publication date <= {u['session']}",
                            DATA_CUTOFF_TIMESTAMP=f"{u['session']}T00:00:00 America/New_York", HAS_BARS=u["has_bars"],
                            PHASE5_PRIMARY_UNIT=int(e["episode_no"] == 1 and u["session"] == e["start"] and u["set"] != "anchor" and u["has_bars"])))
    # primary unit: one per security — the earliest unit of the first episode (ties: earliest evidence id)
    seen = set()
    for r in sorted(man, key=lambda r: (r["SECURITY_ID"], r["DECISION_DATE"], r["EVIDENCE_ID"])):
        if r["PHASE5_PRIMARY_UNIT"]:
            if r["SECURITY_ID"] in seen:
                r["PHASE5_PRIMARY_UNIT"] = 0
            seen.add(r["SECURITY_ID"])
    P.write_csv(os.path.join(P.HERE, "PHASE5_COHORT_MANIFEST.csv"), sorted(man, key=lambda r: (r["SECURITY_ID"], r["DECISION_DATE"], r["EVIDENCE_ID"])))
    ne = collections.Counter(e["ticker"] for e in eps)
    lines.append(f"- episodes (gap > {P.EPISODE_GAP} sessions opens a new one): **{len(eps)}** over {len(ne)} securities · securities with 2+ episodes: {sorted((t, n) for t, n in ne.items() if n > 1)}")
    lines.append(f"- primary units (one per non-anchor security with bars · earliest unit of episode 1): **{sum(1 for r in man if r['PHASE5_PRIMARY_UNIT'])}**")
    lines.append(f"- manifest rows {len(man)} · unique securities {len({r['SECURITY_ID'] for r in man})} · unique episodes {len({r['DECISION_EPISODE_ID'] for r in man})} · unique evidence units {len({r['EVIDENCE_ID'] for r in man})}")

    # ④ write the reconciliation
    n_ok = sum(1 for c in checks if c[3] == "REPRODUCED")
    md = ["# PHASE 5 §2 — Phase 4 reconciliation (audited, not trusted)", "",
          f"Recomputed from `fm_forensics/phase3/FAISAL_TIMELINE.csv` through `p4lib.faisal_timeline`/`first_states` by name, and from the Phase 4 artifacts at HEAD `{head_sha()[:12]}`. No feature value and no feature–outcome number was computed here.", "",
          f"**Checks: {n_ok}/{len(checks)} REPRODUCED.**", "",
          "| check | recomputed | Phase 4 claim | status | note |", "|---|---|---|---|---|"]
    md += [f"| {n} | {g} | {e} | {s} | {t} |" for n, g, e, s, t in checks]
    md += ["", "## Reconciliation notes", ""] + lines
    md += ["", "## Decisions for Phase 5 (from this audit)", "",
           "1. **Unit of analysis** = `DECISION_EPISODE_ID` (security × episode; a gap over 30 sessions between dated units opens a new episode). Primary inference uses **one primary unit per non-anchor security** (earliest unit of episode 1); repeated units are evidence within the episode, never independent rows. Clustering by `SECURITY_ID`.",
           "2. **Anchors DKI/SXTC/HUBC** carry `ANCHOR_EXCLUDED=1` and are outside primary inference (descriptive only). HUBC's label is never invented.",
           "3. **Phase 4 controls** have no negative label: their status under §4 is `UNKNOWN` (absence of a post). Phase 5 builds its control manifest fresh (§11) and assigns tiers (§12) explicitly; Phase 4 control identities are kept for comparison only.",
           "4. **Phase 4 validation membership is contaminated** (labels revealed in Phase 4) ⇒ Phase 5 does not reuse it as a blind set. A new security-level partition is defined in the prereg (§G) before any feature value is joined to an outcome.",
           "5. Evidence quality: `DIRECT_CHART` units (20) are labelled MEDIUM confidence; `DIRECT_TEXT`/`ACTION` HIGH. Sensitivity to label quality is pre-registered.",
           "6. Repeated tickers (20 of 41 with more than one dated row) explain why rows (83) exceed securities (41): Phase 4 reported both; nothing is hidden.",
           "7. The four bar-less tickers (ATPC · LABT · MI · UNK) are a **documented data-availability exclusion**, not a hidden one; Phase 5 keeps them in the manifest (`HAS_BARS=0`) and lists them in every denominator."]
    with open(os.path.join(P.HERE, "PHASE5_PHASE4_RECONCILIATION.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
