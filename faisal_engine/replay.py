# -*- coding: utf-8 -*-
"""إعادةٌ تاريخيّةٌ آمنةٌ من النظر للأمام لمحرّك البحث على وحدات فيصل المؤرَّخة وضوابط المرحلة 4 — وفق `REPLAY_PROTOCOL.md`.
يكتب في `faisal_engine/out/` وحدَه: replay_units.csv · replay_controls.csv · lead_time.csv · summary.json · run.log
قراءةٌ فقط · لا يكتب `phase4/out/extra_states.csv` · لا تلغرام."""
import csv
import json
import math
import os
import sys
import time

os.environ["FAISAL_ONLY"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(ROOT)
for p in (HERE, os.path.join(ROOT, "fm_forensics", "phase3"), os.path.join(ROOT, "fm_forensics", "phase4")):
    sys.path.insert(0, p)
import p3lib as L           # noqa: E402
import p4lib as P           # noqa: E402
import engine as E          # noqa: E402
import data as D            # noqa: E402

OUT = os.environ.get("FE_OUT") or os.path.join(HERE, "out")
BACK = 60
IN_PROCESS = ("FOCUS", "WATCH", "READY", "TRIGGER", "HOLD")
SETS = ("discovery", "validation", "anchor", "other")
MOVE_KEYS = ("MOVE_25_10", "MOVE_50_20", "MOVE_100_20")


def sessions_between(a, b):
    """عددُ الجلسات من a إلى b (b − a بالجلسات · موجبٌ إن كان a أبكر)."""
    return L.cal_index(b) - L.cal_index(a)


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None, None)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (round(p, 4), round(c - h, 4), round(c + h, 4))


def read(sym, day):
    """المحرّكُ عند يومٍ (شموعٌ قبله حصرًا)."""
    return E.evaluate(sym, D.bars(sym), day, D.context(sym, day), label="HISTORICAL")


def baseline(sym, day):
    g = P.gate_row(sym, day)
    return g["result"], g["gate"], g["reason"]


def unit_rows():
    rows = []
    for r in P.faisal_timeline():
        rows.append(dict(ticker=r["ticker"], session=r["session"], state=r["state"], evidence_class=r["evidence_class"],
                         evidence_id=r["evidence_id"], set=r["set"], has_bars=r["has_bars"], date_ambiguous=r["date_ambiguous"]))
    return rows


def control_rows():
    out = []
    for s in ("discovery", "validation", "anchor"):
        p = os.path.join(ROOT, "fm_forensics", "phase4", "out", f"arch_controls_{s}.csv")
        for r in csv.DictReader(open(p, encoding="utf-8")):
            out.append(dict(ticker=r["CONTROL"], session=r["DECISION_DATE"], matched=r["MATCHED_POSITIVE"], set=s))
    return out


def agreement(faisal_state, stage):
    if stage not in IN_PROCESS:
        return "MISS"
    if faisal_state == "ENTRY":
        return "EXACT" if stage in ("READY", "TRIGGER") else "COMPATIBLE"
    return "EXACT" if stage == faisal_state else "COMPATIBLE"


def flat(rec, prefix=""):
    v4 = rec.get("v4") or {}
    scr = rec.get("screen") or {}
    ff = rec.get("first_failed") or {}
    return {prefix + "stage": rec["stage"], prefix + "frame": scr.get("frame") or "", prefix + "tech_state": v4.get("tech_state") or "",
            prefix + "v4_state": v4.get("state") or "", prefix + "first_failed": ff.get("rule") or "", prefix + "first_failed_why": ff.get("why") or "",
            prefix + "offering": str((rec.get("validity") or {}).get("offering_pending")), prefix + "bars": rec["provenance"]["bars"],
            prefix + "last_rsplit": (rec.get("corporate_actions") or {}).get("last_reverse_split") or "",
            prefix + "missing_n": len(rec.get("missing_data") or [])}


def first_in_process(sym, anchor_day, log):
    """أوّلُ يومٍ «في المسار» وأوّلُ PASS لخطّ الأساس ضمن [anchor − BACK, anchor] (جلسات)."""
    days = [L.shift(anchor_day, -k) for k in range(BACK, -1, -1)]
    seen, first_e, first_b, stages = set(), None, None, {}
    for d in days:
        if d in seen or d > anchor_day:
            continue
        seen.add(d)
        if first_e is None:
            rec = read(sym, d)
            stages[d] = rec["stage"]
            if rec["stage"] in IN_PROCESS:
                first_e = d
        if first_b is None and baseline(sym, d)[0] == "PASS":
            first_b = d
        if first_e and first_b:
            break
    return first_e, first_b, len(seen)


def main():
    os.makedirs(OUT, exist_ok=True)
    log = open(os.path.join(OUT, "run.log"), "w", encoding="utf-8")
    t0 = time.time()
    units = unit_rows(); ctls = control_rows()
    print(f"units {len(units)} · controls {len(ctls)}", file=log, flush=True)
    # --- A: at Faisal's date
    urows = []
    for u in units:
        row = dict(u)
        if not u["has_bars"]:
            row.update(stage="NO_BARS", agreement="NO_BARS", base_result="NO_BARS")
        else:
            rec = read(u["ticker"], u["session"])
            row.update(flat(rec)); row["agreement"] = agreement(u["state"], rec["stage"])
            b = baseline(u["ticker"], u["session"]); row.update(base_result=b[0], base_gate=b[1])
            oc = L.outcomes(u["ticker"], u["session"]) or {}
            for k in MOVE_KEYS:
                row[k] = oc.get(k)
        urows.append(row)
        print(f"U {u['ticker']} {u['session']} {u['state']} ⟵ {row.get('stage')} / base {row.get('base_result')}", file=log, flush=True)
    crows = []
    for c in ctls:
        rec = read(c["ticker"], c["session"]); row = dict(c); row.update(flat(rec))
        b = baseline(c["ticker"], c["session"]); row.update(base_result=b[0], base_gate=b[1])
        oc = L.outcomes(c["ticker"], c["session"]) or {}
        for k in MOVE_KEYS:
            row[k] = oc.get(k)
        crows.append(row)
        print(f"C {c['ticker']} {c['session']} ⟵ {row['stage']} / base {row['base_result']}", file=log, flush=True)
    # --- B: lead time per ticker
    fs = P.first_states([r for r in P.faisal_timeline()])
    lrows = []
    for sym, d in sorted(fs.items()):
        if not D.bars(sym):
            lrows.append(dict(ticker=sym, set=P.which_set(sym), first_faisal=d["first_state"], first_class=d["first_state_class"], engine_first="", base_first="", engine_lead="", base_lead="", scanned=0, note="NO_BARS"))
            continue
        fe, fb, n = first_in_process(sym, d["first_state"], log)
        lead_e = sessions_between(fe, d["first_state"]) if fe else ""
        lead_b = sessions_between(fb, d["first_state"]) if fb else ""
        lrows.append(dict(ticker=sym, set=P.which_set(sym), first_faisal=d["first_state"], first_class=d["first_state_class"], engine_first=fe or "",
                          base_first=fb or "", engine_lead=lead_e, base_lead=lead_b, scanned=n, note=""))
        print(f"L {sym} faisal {d['first_state']} engine {fe} (+{lead_e}) base {fb} (+{lead_b}) scanned {n}", file=log, flush=True)
    # controls lead: first in-process within window before the control day
    clrows = []
    for c in ctls:
        fe, fb, n = first_in_process(c["ticker"], c["session"], log)
        clrows.append(dict(ticker=c["ticker"], set=c["set"], day=c["session"], engine_first=fe or "", base_first=fb or "",
                           engine_lead=(sessions_between(fe, c["session"]) if fe else ""), base_lead=(sessions_between(fb, c["session"]) if fb else ""), scanned=n))
        print(f"CL {c['ticker']} {c['session']} engine {fe} base {fb}", file=log, flush=True)
    L.write_csv(os.path.join(OUT, "replay_units.csv"), urows)
    L.write_csv(os.path.join(OUT, "replay_controls.csv"), crows)
    L.write_csv(os.path.join(OUT, "lead_time.csv"), lrows)
    L.write_csv(os.path.join(OUT, "lead_time_controls.csv"), clrows)
    summ = summarise(urows, crows, lrows, clrows)
    summ["runtime_s"] = round(time.time() - t0, 1)
    json.dump(summ, open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(summ["headline"], ensure_ascii=False, indent=1), file=log, flush=True)
    print(json.dumps(summ["headline"], ensure_ascii=False, indent=1))


def _median(xs):
    xs = sorted(xs)
    if not xs:
        return None
    m = len(xs) // 2
    return xs[m] if len(xs) % 2 else (xs[m - 1] + xs[m]) / 2


def _q(xs, q):
    xs = sorted(xs)
    if not xs:
        return None
    i = max(0, min(len(xs) - 1, int(round(q * (len(xs) - 1)))))
    return xs[i]


def summarise(urows, crows, lrows, clrows):
    out = {"protocol": "REPLAY_PROTOCOL.md", "label": "EXPLORATORY", "sets": {}}
    for s in SETS + ("all",):
        U = [r for r in urows if r["has_bars"] and (s == "all" or r["set"] == s)]
        C = [r for r in crows if (s == "all" or r["set"] == s)]
        if not U and not C:
            continue
        inp_u = sum(1 for r in U if r["agreement"] != "MISS"); inp_c = sum(1 for r in C if r["stage"] in IN_PROCESS)
        base_u = sum(1 for r in U if r["base_result"] == "PASS"); base_c = sum(1 for r in C if r["base_result"] == "PASS")
        pu, pc = wilson(inp_u, len(U)), wilson(inp_c, len(C))
        d = {"units": len(U), "controls": len(C),
             "A_exact": sum(1 for r in U if r["agreement"] == "EXACT"), "A_compatible": sum(1 for r in U if r["agreement"] == "COMPATIBLE"),
             "A_miss": sum(1 for r in U if r["agreement"] == "MISS"), "A_in_process_pos": pu, "A_in_process_ctl": pc,
             "A_LR": (round(pu[0] / pc[0], 3) if pu[0] and pc[0] else None),
             "A_ci_disjoint": (bool(pu[1] is not None and pc[2] is not None and pu[1] > pc[2]) if pu[0] is not None and pc[0] is not None else None),
             "baseline_pass_pos": wilson(base_u, len(U)), "baseline_pass_ctl": wilson(base_c, len(C)),
             "always_watch_compatible": len(U), "stages_pos": _count(r["stage"] for r in U), "stages_ctl": _count(r["stage"] for r in C),
             "first_failed_pos": _count(r.get("first_failed") for r in U if r["agreement"] == "MISS"),
             "frames_pos": _count(r.get("frame") for r in U if r["agreement"] != "MISS"),
             "validity_verified_pos": 0}
        # C — price behaviour, descriptive, controls-internal
        for k in MOVE_KEYS:
            ci = [r for r in C if r.get(k) in (0, 1, "0", "1")]
            inn = [r for r in ci if r["stage"] in IN_PROCESS]; outn = [r for r in ci if r["stage"] not in IN_PROCESS]
            d[f"C_{k}_ctl_in"] = wilson(sum(int(r[k]) for r in inn), len(inn)); d[f"C_{k}_ctl_out"] = wilson(sum(int(r[k]) for r in outn), len(outn))
            pi = [r for r in U if r.get(k) in (0, 1, "0", "1")]
            d[f"C_{k}_pos"] = wilson(sum(int(r[k]) for r in pi), len(pi))
        # B — lead time
        Lr = [r for r in lrows if r["note"] != "NO_BARS" and (s == "all" or r["set"] == s)]
        el = [int(r["engine_lead"]) for r in Lr if r["engine_lead"] != ""]; bl = [int(r["base_lead"]) for r in Lr if r["base_lead"] != ""]
        d["B_tickers"] = len(Lr); d["B_engine_captured"] = len(el); d["B_base_captured"] = len(bl)
        d["B_engine_lead_median"] = _median(el); d["B_engine_lead_q1_q3"] = [_q(el, .25), _q(el, .75)]
        d["B_base_lead_median"] = _median(bl); d["B_base_lead_q1_q3"] = [_q(bl, .25), _q(bl, .75)]
        Cl = [r for r in clrows if (s == "all" or r["set"] == s)]
        cel = [int(r["engine_lead"]) for r in Cl if r["engine_lead"] != ""]
        d["B_ctl_engine_captured"] = wilson(len(cel), len(Cl)); d["B_ctl_engine_lead_median"] = _median(cel)
        d["B_ctl_base_captured"] = wilson(sum(1 for r in Cl if r["base_lead"] != ""), len(Cl))
        out["sets"][s] = d
    a = out["sets"].get("all", {})
    out["headline"] = {k: a.get(k) for k in ("units", "controls", "A_exact", "A_compatible", "A_miss", "A_in_process_pos", "A_in_process_ctl", "A_LR",
                                               "A_ci_disjoint", "baseline_pass_pos", "baseline_pass_ctl", "B_engine_captured", "B_base_captured",
                                               "B_tickers", "B_engine_lead_median", "B_base_lead_median", "B_ctl_engine_captured")}
    out["falsification"] = {
        "P1_engine_ctl_in_process_gt_50pct": (a.get("A_in_process_ctl") or [None])[0],
        "P2_LR_disjoint_discovery_and_validation": bool(out["sets"].get("discovery", {}).get("A_ci_disjoint")) and bool(out["sets"].get("validation", {}).get("A_ci_disjoint")),
        "P3_ready_at_faisal_dates": sum(1 for r in urows if r.get("stage") in ("READY", "TRIGGER")),
        "validity_verified_any": False}
    out["no_bars_units"] = sorted({r["ticker"] for r in urows if r["has_bars"] == 0})
    return out


def _count(it):
    c = {}
    for x in it:
        c[x or ""] = c.get(x or "", 0) + 1
    return dict(sorted(c.items(), key=lambda kv: -kv[1]))


if __name__ == "__main__":
    main()
