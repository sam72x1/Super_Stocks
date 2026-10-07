# -*- coding: utf-8 -*-
"""
📊 FAISAL V4.1 — المقاييس والتدقيقات (العقد `V41_prereg.md` §⑧-⑮) — **بعد الختم وحدَه**.

نطاقان لا يُخلطان أبدًا:
  • **الأماميّ (الحكمُ الرسميّ):** من السجلّ الإلحاقيّ (`ledger.complete_cases`) — صفرٌ عند التجميد ⟵ «NOT STARTED».
  • **التاريخيُّ الملوَّث (وصفيٌّ فقط):** قراراتُ V4 المجمَّدة المنشورة (`faisal_method_v4/results/v4_eval_results.json` · لا إعادةَ تشغيل)
    مقابل كلمات فيصل بعد الكشف من البيان المختوم (`holdout.reveal`) — كلُّ حالةٍ فيه مكشوفة (§⑤) فلا يُدّعى منه تعميم.
المخرَج: `results/analysis_v41.json` — والوثائقُ تُبنى منه (`docs_v41.py`).
"""
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
V4 = os.path.join(ROOT, "faisal_method_v4")
for _p in (V4, os.path.join(ROOT, "faisal_method_v3"), HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import decision_engine as E      # noqa: E402 — مجمَّد
import holdout as HO             # noqa: E402
import ledger as LG              # noqa: E402
import provenance as PV          # noqa: E402

OUT = os.path.join(HERE, "results", "analysis_v41.json")
EVAL = os.path.join(V4, "results", "v4_eval_results.json")
STATES = ("READY", "WAIT", "REJECT", "UNKNOWN")
TECH_READY = {s for s, d in E.STATE_DECISION.items() if d == "TECH_READY"}
N_MIN = 43                         # العقد §⑨
Z = 1.96
WILSON_MIN = 10                    # العقد §⑧
# §⑪ — رموزٌ وكلماتٌ مسجَّلة قبل الرقم
UNAVAILABLE_CODES = ("WAIT_OPERATOR", "PRESSURE_AT_LEVEL", "GROUPS_PRESENT", "NO_GROUPS")
EXTERNAL_PREFIX = ("FLOAT", "SHORT", "FEE", "SPLIT_RECENT", "JUST_SPLIT", "SPLIT_DATE", "NEWS", "NASDAQ", "COUNTRY", "AH_", "PM_")
DISCRETIONARY_CODES = ("WATCHLIST_CALL", "WATCH_ONLY", "FOLLOWER_DONT_BUY")
UNAVAILABLE_WORDS = re.compile(r"مضارب|ضغط|قروب")
EXTERNAL_WORDS = re.compile(r"شورت|فلوت|طرح|تخفيف|تقسيم|خبر|اقتراض")
CHART_EFFECTS = ("ENTRY", "INVALIDATION", "CONFIRMATION", "PATTERN")
ORDERS_WORDS = re.compile(r"طلب|طلبات|\border|\bbid", re.I)
SUPPORT_KINDS = ("support", "bottom", "zone_lo")
SUPPORT_CODE = re.compile(r"SUPPORT|AT_SUPPORT|MAIN_SUPPORT")
TECH_READY_CODES = ("TECH_READY",)
DEP_ORDER = ("UNAVAILABLE", "EXTERNAL-DATA-DERIVABLE", "MANUAL/DISCRETIONARY", "CHART-DERIVABLE")


def wilson(k, n):
    if n < WILSON_MIN:
        return None
    p = k / n
    den = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / den
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / den
    return [round(c - h, 4), round(c + h, 4)]


def matrix(pairs):
    """أزواجُ (فيصل · V4) ⟵ المصفوفة 4×4 والمقاييسُ المسجَّلة (§⑧) — والفاصلُ حين المقامُ 10 فأكثر."""
    m = {f: {v: 0 for v in STATES} for f in STATES}
    for f, v in pairs:
        if f in STATES and v in STATES:
            m[f][v] += 1
    n = sum(m[f][v] for f in STATES for v in STATES)
    diag = sum(m[s][s] for s in STATES)
    col = {v: sum(m[f][v] for f in STATES) for v in STATES}
    row = {f: sum(m[f].values()) for f in STATES}
    out = {"n": n, "matrix": m, "exact": diag, "exact_rate": round(diag / n, 4) if n else None, "exact_wilson": wilson(diag, n),
           "ready_precision": (round(m["READY"]["READY"] / col["READY"], 4) if col["READY"] else "UNDEFINED (V4 READY = 0)"),
           "ready_recall": (f"{m['READY']['READY']}/{row['READY']}" if row["READY"] else "UNDEFINED (Faisal READY = 0)"),
           "agreement": {s: (f"{m[s][s]}/{row[s]}" if row[s] else "N=0") for s in STATES},
           "false": {s: sum(m[f][s] for f in STATES if f != s) for s in STATES},
           "false_rate": {s: (round(sum(m[f][s] for f in STATES if f != s) / n, 4) if n else None) for s in STATES},
           "always_wait": col_always(m, n)}
    out["insufficient"] = n < WILSON_MIN
    out["v4_not_run"] = sum(1 for f, v in pairs if f in STATES and v not in STATES)   # لا قرارَ V4 (NO_BARS) — يُعَدّ ولا يُسقَط صامتًا
    return out


def col_always(m, n):
    k = sum(m["WAIT"].values())
    return {"agree": k, "n": n, "rate": round(k / n, 4) if n else None}


def case_units(row_ids, unit_of):
    return sorted({unit_of.get(HO.base_id(s), HO.base_id(s)) for s in row_ids})


def dependency(units, recs):
    """§⑪: أقصى اعتمادٍ في عبارات الحالة (بالترتيب) ⟵ (الفئة · الأدلّة)."""
    codes = [c for u in units for c in (recs.get(u, {}).get("why") or [])]
    rules = [x for u in units for x in (recs.get(u, {}).get("rules") or [])]
    vtxt = " ".join(x.get("txt", "") for x in rules if x.get("eff") in ("VALIDITY", "CONFIRMATION"))
    v_only = " ".join(x.get("txt", "") for x in rules if x.get("eff") == "VALIDITY")
    ev = []
    if any(c in UNAVAILABLE_CODES or c.startswith("NO_GROUPS") for c in codes) or UNAVAILABLE_WORDS.search(vtxt):
        ev = [c for c in codes if c in UNAVAILABLE_CODES or c.startswith("NO_GROUPS")] or ["نصّ: " + UNAVAILABLE_WORDS.search(vtxt).group(0)]
        return "UNAVAILABLE", ev
    if any(c.startswith(EXTERNAL_PREFIX) for c in codes) or EXTERNAL_WORDS.search(v_only):
        ev = [c for c in codes if c.startswith(EXTERNAL_PREFIX)] or ["نصّ: " + EXTERNAL_WORDS.search(v_only).group(0)]
        return "EXTERNAL-DATA-DERIVABLE", ev
    if any(c in DISCRETIONARY_CODES for c in codes) and not any(x.get("eff") in CHART_EFFECTS for x in rules):
        return "MANUAL/DISCRETIONARY", [c for c in codes if c in DISCRETIONARY_CODES]
    return "CHART-DERIVABLE", []


def orders_support(units, recs, levels_f):
    txt = " ".join(recs.get(u, {}).get("g", "") + " " + " ".join(x.get("txt", "") for x in (recs.get(u, {}).get("rules") or []))
                   for u in units)
    codes = [c for u in units for c in (recs.get(u, {}).get("why") or [])]
    support = any((lv or {}).get("kind") in SUPPORT_KINDS for lv in (levels_f or [])) or any(SUPPORT_CODE.search(c) for c in codes)
    return support, bool(ORDERS_WORDS.search(txt))


def plan_agrees(plan, cls):
    if plan == "NONE" or not plan or not cls:
        return False
    return plan == cls or (plan == "BOTH" and cls in ("BELOW", "ABOVE"))


def consistent(row):
    """A: مخرجُ V4 يوافق مواصفتَه؟ (الحالةُ الفنيّة ⟵ القرار عبر STATE_DECISION والصلاحيّة)."""
    ts, st = row.get("tech_state"), row.get("state")
    base = E.STATE_DECISION.get(ts)
    if base is None:
        return False
    if base == "UNKNOWN":
        return st == "UNKNOWN"
    if base == "WAIT":
        return st in ("WAIT", "REJECT")
    return st in ("READY", "UNKNOWN", "WAIT", "REJECT") and (st != "UNKNOWN" or bool(row.get("missing")))


def classify(r, contra_units_by_rule, dep):
    """§⑫ — A ثمّ F (شرطاهما مستقلّان) ثمّ ①..⑧ بالترتيب ⟵ (الفئة · التفسير)."""
    if not consistent(r["v4"]):
        return "A", "مخرجُ V4 يناقض مواصفتَه (STATE_DECISION/الصلاحيّة)"
    if r.get("basis") == "explicit_conflict":
        return "F", "عباراتُ الحالة نفسُها متعارضة"
    v = r["v4"]
    if v.get("tech_state") == "DATA_INSUFFICIENT":
        return "E", "شموعٌ ناقصة قبل تاريخ القراءة"
    sc = v.get("scale")
    if isinstance(sc, (int, float)) and abs(sc - 1) > 0.15:
        return "G", f"سعرُ الصورة يخالف إغلاقَ القراءة ×{sc:.3g} (توقيت/أفتر)"
    if v.get("state") == "UNKNOWN" and v.get("tech_state") in TECH_READY:
        return "D", "V4 جاهزٌ فنيًّا وينقصه بنفسه: " + " · ".join(v.get("missing") or [])
    if r["timeframes"] and "D" not in r["timeframes"]:
        return "B", f"فريمُ فيصل {r['timeframes']} لا يضمّ اليوميّ (المحرّكُ يوميٌّ وحدَه · R4-TF-01)"
    if not plan_agrees(r.get("plan_f"), v.get("decisive_class")):
        return "B", f"فئةُ خطّة فيصل {r.get('plan_f')} ≠ فئةُ مستوى V4 {v.get('decisive_class')}"
    blocking = [b.get("rule") for b in (v.get("blocking") or [])]
    if any(set(r["units"]) & contra_units_by_rule.get(b, set()) for b in blocking):
        return "C", f"عبارةُ الحالة مذكورةٌ مناقِضةً في {blocking}"
    if dep in ("UNAVAILABLE", "EXTERNAL-DATA-DERIVABLE"):
        return "D", f"قرارُ فيصل يعتمد معلومةً {dep}"
    return "H", "لم يفسّره بديلٌ مسجَّل"


RULE_TOKEN = re.compile(r"R4?-[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*")


def difference(f, v):
    """§11 DIFFERENCE — اتّجاهُ الخلاف لا مجرّدُ وقوعه."""
    if v == "UNKNOWN":
        return "V4 يمتنع (UNKNOWN) وفيصل يقرّر " + str(f)
    if v == "READY":
        return "V4 أرخى: READY وفيصل " + str(f) + " (FALSE READY)"
    if f == "READY":
        return "V4 أشدّ: " + str(v) + " وفيصل READY"
    return f"V4 {v} وفيصل {f}"


def explain_disagreement(r, e, prov_status):
    """§11 — الحقولُ الأحد عشر لخلافٍ واحد (من سجلّ V4 المنشور ومصدريّة القواعد · لا تخمين)."""
    blocked = [b.get("rule") for b in (e.get("blocking") or [])]
    named = sorted({t for t in RULE_TOKEN.findall(r.get("why") or "") if t in prov_status} | {b for b in blocked if b in prov_status})
    return {"CASE_ID": r["case"], "FAISAL_DECISION": r["faisal"], "V4_DECISION": f'{r["v4"]["state"]} ({r["v4"]["tech_state"]})',
            "DIFFERENCE": difference(r["faisal"], r["v4"]["state"]), "RULES_TRIGGERED": e.get("rule_ids") or [],
            "RULES_BLOCKED": blocked,
            "DATA_AVAILABLE": {"bars_asof": e.get("asof"), "v4_status": e.get("status"), "close_asof": e.get("close"),
                               "image_price_F": e.get("px_F"), "validity_context": "لا شيء — تشغيلُ V4 التاريخيّ بلا سياق (v4_eval.run_case)"},
            "DATA_MISSING": e.get("missing") or [], "POSSIBLE_REASON": r.get("why"),
            "EVIDENCE_STATUS": {"case": "HISTORICAL-CONTAMINATED · " + r["tier"], "rules": {x: prov_status[x] for x in named}},
            "CLASSIFICATION": r.get("class"), "set": r["set"], "dependency": r["dependency"]}


def verdict(classes):
    k = sum(1 for c in classes if c == "D")
    n = sum(1 for c in classes if c not in ("E", "G"))
    if n == 0:
        return "UNKNOWN", k, n
    if n < 10:
        return ("PARTIAL" if k >= 1 else "UNKNOWN"), k, n
    q = k / n
    return ("SUPPORTED" if q >= 0.5 else "PARTIAL" if q >= 0.2 else "REJECTED"), k, n


def load_eval():
    with open(EVAL, encoding="utf-8") as f:
        return json.load(f)


def historical(man, ev, prov):
    """التاريخيُّ الملوَّث (وصفيّ): صفوفُ V4 المنشورة × كلماتُ فيصل بعد الكشف."""
    unit_of, recs = PV.corpus_units()
    revealed = {r["CASE_ID"]: r for r in HO.reveal(man)}
    cases = {c["case"]: c for c in json.load(open(HO.CASES, encoding="utf-8"))["cases"]}
    contra = {x["RULE_ID"]: {unit_of.get(i, i) for i in x["CONTRADICTORY_SOURCE_IDS"]} for x in prov["rules"]}
    rows = []
    for v in ev["rows"]:
        h = revealed.get(v["case"])
        if not h:
            continue
        units = h["UNITS"]
        dep, dev = dependency(units, recs)
        sup, ords = orders_support(units, recs, h.get("LEVELS_F"))
        r = {"case": v["case"], "set": v.get("set"), "split": v.get("split"), "tier": h["TIER"], "flags": h["DISCOVERY_CONTAMINATION"],
             "faisal": h["FAISAL"], "plan_f": h["PLAN_F"], "basis": cases.get(v["case"], {}).get("basis"),
             "timeframes": h["TIMEFRAME"], "pattern": h["PATTERN"], "units": units, "dependency": dep, "dependency_evidence": dev,
             "support_f": sup, "orders_f": ords,
             "tech_ready_f": any(c in TECH_READY_CODES for u in units for c in (recs.get(u, {}).get("why") or [])),
             "v4": {k: v.get(k) for k in ("state", "tech_state", "decisive_class", "scale", "missing", "blocking", "status")}}
        r["agree"] = r["faisal"] == r["v4"]["state"]
        if r["faisal"] in ("READY", "WAIT", "REJECT") and r["v4"]["state"] in STATES and not r["agree"]:
            r["class"], r["why"] = classify(r, contra, dep)
        rows.append(r)

    def pairs(sel):
        return [(r["faisal"], r["v4"]["state"]) for r in rows if sel(r) and r["faisal"] in STATES]
    groups = {
        "S1_all": lambda r: r["set"] == "S1", "S1_discovery": lambda r: r["set"] == "S1" and r["split"] == "discovery",
        "S1_holdout_v4": lambda r: r["set"] == "S1" and r["split"] == "holdout", "S2": lambda r: r["set"] == "S2",
        "S3_golden": lambda r: r["set"] == "S3", "S4_edu": lambda r: r["set"] == "S4",
        "T1_cited_S1S2": lambda r: r["set"] in ("S1", "S2") and r["tier"] == "T1_CITED",
        "T2_exposed_uncited_S1S2": lambda r: r["set"] in ("S1", "S2") and r["tier"] == "T2_EXPOSED_UNCITED"}
    mats = {g: matrix(pairs(f)) for g, f in groups.items()}
    # إعادةُ إنتاج رقم V4 المنشور (‏`h_state_descriptive` على status = OK وحدَه) — جسرٌ بين الرقمين لا رقمٌ بديل
    v4g = {"S1_all": "S1_all", "S1_discovery": "S1_discovery", "S1_holdout_v4": "S1_holdout", "S2": "S2", "S3_golden": "S3_golden",
           "S4_edu": "S4_edu"}
    st = {r["case"]: r.get("status") for r in ev["rows"]}
    repro = {}
    for g, vg in v4g.items():
        okp = [(r["faisal"], r["v4"]["state"]) for r in rows if groups[g](r) and st.get(r["case"]) == "OK"]
        pub = (ev.get("h_state_descriptive") or {}).get(vg) or {}
        mine = {"n": len(okp), "state_exact": sum(1 for f, v in okp if f == v)}
        repro[g] = {"v4_published": {k: pub.get(k) for k in ("n", "state_exact")}, "recomputed_ok_only": mine,
                    "match": mine == {k: pub.get(k) for k in ("n", "state_exact")},
                    "scale_mismatch_included_v41": sum(1 for r in rows if groups[g](r) and st.get(r["case"]) == "SCALE_MISMATCH")}
    mixed = sum(1 for r in rows if r["set"] in ("S1", "S2") and r["faisal"] not in STATES)

    def two_by_two(sel, a, b):
        t = {"both": 0, "v4_only": 0, "faisal_only": 0, "neither": 0}
        for r in rows:
            if not sel(r):
                continue
            x, y = a(r), b(r)
            t["both" if x and y else "v4_only" if x else "faisal_only" if y else "neither"] += 1
        return t
    s12 = lambda r: r["set"] in ("S1", "S2") and r["faisal"] in STATES and r["v4"]["state"] in STATES      # noqa: E731
    not_run = [{"case": r["case"], "set": r["set"], "faisal": r["faisal"], "status": r["v4"]["status"]}
               for r in rows if r["v4"]["state"] not in STATES]
    stages = {
        "structure_exists": two_by_two(s12, lambda r: r["v4"]["tech_state"] != "DATA_INSUFFICIENT",
                                       lambda r: r["support_f"] or bool(revealed[r["case"]]["LEVELS_F"])),
        "setup_valid": two_by_two(s12, lambda r: r["v4"]["tech_state"] in TECH_READY,
                                  lambda r: r["tech_ready_f"] or r["faisal"] == "READY")}
    dep_tab = {}
    for r in rows:
        if s12(r):
            d = dep_tab.setdefault(r["dependency"], {"n": 0, "faisal": {}, "v4": {}})          # s12 يُقصي ما لم يُشغَّل
            d["n"] += 1
            d["faisal"][r["faisal"]] = d["faisal"].get(r["faisal"], 0) + 1
            d["v4"][r["v4"]["state"]] = d["v4"].get(r["v4"]["state"], 0) + 1
    tr = [r for r in rows if r["v4"]["tech_state"] in TECH_READY]
    unknown_ok = {"tech_ready_outputs": len(tr), "of_which_unknown": sum(r["v4"]["state"] == "UNKNOWN" for r in tr),
                  "of_which_ready": sum(r["v4"]["state"] == "READY" for r in tr),
                  "note": "بنيويّ: operator_press = None دائمًا ⟵ الجاهزيّةُ الفنيّة بلا WAIT/REJECT صريحٍ تصير UNKNOWN"}
    ords = {}
    for r in rows:
        if s12(r):
            key = ("support+orders" if r["support_f"] and r["orders_f"] else "support+no_orders" if r["support_f"]
                   else "no_support+orders" if r["orders_f"] else "no_support+no_orders")
            ords.setdefault(key, {s: 0 for s in STATES})[r["faisal"]] += 1
    ready_sup = [r for r in rows if s12(r) and r["faisal"] == "READY" and r["support_f"]]
    if not ready_sup:
        h_ord = "UNKNOWN"
    elif any(not r["orders_f"] for r in ready_sup):
        h_ord = "CONTRADICTED"
    else:
        h_ord = "SUPPORTED" if len(ready_sup) >= 3 else "POSSIBLE"
    dis = [r for r in rows if r["set"] in ("S1", "S2") and r.get("class")]
    evr = {x["case"]: x for x in ev["rows"]}
    prov_status = {x["RULE_ID"]: x["EVIDENCE_STATUS"] for x in prov["rules"]}
    inv_v, inv_k, inv_n = verdict([r["class"] for r in dis])
    cover = {"pattern": {}, "timeframe": {}}
    for r in rows:
        if s12(r):
            cover["pattern"][r["pattern"]] = cover["pattern"].get(r["pattern"], 0) + 1
            for t in (r["timeframes"] or ["?"]):
                cover["timeframe"][t] = cover["timeframe"].get(t, 0) + 1
    return {"rows": rows, "matrices": mats, "v4_published_reproduction": repro, "mixed_excluded_S1S2": mixed, "not_run": not_run,
            "stages": stages, "dependency": dep_tab,
            "unknown_behaviour": unknown_ok, "orders": ords, "h_ord": h_ord, "h_ord_ready_with_support": len(ready_sup),
            "disagreements": [explain_disagreement(r, evr.get(r["case"], {}), prov_status) for r in dis],
            "invisible": {"verdict": inv_v, "k_D": inv_k, "n": inv_n,
                          "by_class": {c: sum(1 for r in dis if r["class"] == c) for c in "ABCDEFGH"}},
            "coverage": cover}


def golden_generalization(ev, prov):
    g = ev["golden_v31_vs_v4"]["rows"]
    used = {}
    for r in g:
        if r.get("v4_match"):
            for rid in r.get("v4_rules") or []:
                used.setdefault(rid, []).append(r["case"])
    out = []
    for x in prov["rules"]:
        rid = x["RULE_ID"]
        gs = sorted(set(used.get(rid, []) + [w for w in x["GOLDEN_WITNESS_IDS"]]))
        if not (used.get(rid) or x["GOLDEN_WITNESS_IDS"]):
            continue
        ind = x["COUNTS"]["n1"]
        con = x["COUNTS"]["c1"] + x["COUNTS"]["c2"]
        out.append({"RULE": rid, "GOLDEN_CASE_SUPPORT": gs, "INDEPENDENT_SUPPORT": ind, "CONTRADICTIONS": con,
                    "HOLDOUT_SUPPORT": 0, "PROSPECTIVE_SUPPORT": 0,
                    "OVERFIT_RISK": ind == 0 or (ind == 1 and con >= 1)})
    return out


def sample_size(cases):
    s1 = [c for c in cases if c.get("set") == "S1"]
    ds = sorted(c["statement_date"] for c in s1 if c.get("statement_date"))
    import datetime as dt
    months = None
    if len(ds) >= 2:
        a, b = dt.date.fromisoformat(ds[0][:10]), dt.date.fromisoformat(ds[-1][:10])
        months = round(((b - a).days + 1) / 30.4375, 2)
    rate = round(len(s1) / months, 3) if months else None
    ready = sum(c.get("label4") == "READY" for c in s1)
    n_req = math.ceil(Z * Z * 0.25 / 0.15 ** 2)
    return {"n_min": N_MIN, "formula": "1.96²·0.25/0.15² = 42.7 ⟵ 43", "n_min_check": n_req,
            "s1_cases": len(s1), "s1_first": ds[0] if ds else None, "s1_last": ds[-1] if ds else None, "months": months,
            "s1_per_month": rate, "months_to_n_min": (round(N_MIN / rate, 1) if rate else None),
            "s1_ready": ready, "ready_rate": round(ready / len(s1), 4) if s1 else None,
            "cases_for_43_ready": (math.ceil(N_MIN / (ready / len(s1))) if ready else "UNDEFINED (READY = 0)"),
            "years_for_43_ready": (round(N_MIN / (ready / len(s1)) / rate / 12, 1) if ready and rate else None)}


def prospective(lg=None):
    lg = lg or LG.Ledger()
    done, invalid = lg.complete_cases()
    pairs = [(c["faisal"]["label4"], c["v4"]["decision"].get("state")) for c in done]
    mat = matrix(pairs)
    n = mat["n"]
    sealed = len({e["case_id"] for e in lg.entries("case")})
    # «SEALED_PENDING» (2026-10-07 · دفعة B48): حالةٌ مختومةٌ تنتظر قرارَ V4 أو كلمةَ فيصل — «NOT STARTED» بعدها تكذب («لا عبارةَ وصلت»)
    status = ("NOT STARTED" if n == 0 and not invalid and not sealed else "SEALED_PENDING" if n == 0 and not invalid
              else ("SUFFICIENT" if n >= N_MIN else "INSUFFICIENT"))
    return {"complete": n, "invalid": len(invalid), "matrix": mat, "status": status,
            "pending_images": LG.pending_new_images(lg), "candidates": len(lg.entries("candidate")),
            "sealed_cases": sealed}


def first_run_reconstruction(ev, prov, posthoc):
    """§⑲: التشغيلةُ الأولى لبيان الاحتجاز (قبل تطبيع «#k» · 2026-10-07) تُعاد حتميًّا وتُنشر بجوار الإعادة POST-HOC — لا تُدهَس."""
    orig = HO.base_id
    try:
        HO.base_id = lambda s: str(s)                       # سلوكُ التشغيلة الأولى بعينه — للإفصاح وحدَه
        first = HO.build()
        h1 = historical(first, ev, prov)
    finally:
        HO.base_id = orig
    fr = {r["CASE_ID"]: r for r in first["rows"]}
    changed = [{"case": r["CASE_ID"], "first_tier": fr[r["CASE_ID"]]["TIER"], "posthoc_tier": r["TIER"],
                "first_flags": fr[r["CASE_ID"]]["DISCOVERY_CONTAMINATION"], "posthoc_flags": r["DISCOVERY_CONTAMINATION"]}
               for r in posthoc["rows"] if fr[r["CASE_ID"]]["DISCOVERY_CONTAMINATION"] != r["DISCOVERY_CONTAMINATION"]
               or fr[r["CASE_ID"]]["UNITS"] != r["UNITS"]]
    keep = ("S1_all", "S2", "T1_cited_S1S2", "T2_exposed_uncited_S1S2")
    cases = json.load(open(HO.CASES, encoding="utf-8"))["cases"]
    occ = [x for c in cases for x in (c.get("sids") or []) + (c.get("third_party_sids") or []) if "#" in str(x)]
    return {"bug": f"معرّفُ العبارة «#k» ({len(set(occ))} معرّفًا · {len(occ)} ظهورًا في {len(cases)} حالة) لم يُطبَّع إلى وحدة صورته "
                   "⟵ لا يطابق المرورَ البصريّ ولا الاستشهاد",
            "fix": "holdout.base_id ‏+ حالةُ «panel» في FV43 ‏+ الطفرة M43e", "first_seal": first["seal"]["sha256"],
            "first_summary": first["summary"], "posthoc_seal": posthoc["seal"]["sha256"], "posthoc_summary": posthoc["summary"],
            "changed_cases": changed,
            "first_matrices": {g: {k: h1["matrices"][g][k] for k in ("n", "exact", "exact_rate")} for g in keep},
            "first_invisible": h1["invisible"], "first_disagreements": len(h1["disagreements"])}


def build():
    man = HO.load()
    ev = load_eval()
    prov = json.load(open(PV.OUT, encoding="utf-8"))
    cases = json.load(open(HO.CASES, encoding="utf-8"))["cases"]
    hist = historical(man, ev, prov)
    pro = prospective()
    overall = ("VALIDATION IN PROGRESS" if pro["status"] in ("NOT STARTED", "SEALED_PENDING") else
               "INSUFFICIENT PROSPECTIVE EVIDENCE" if pro["status"] == "INSUFFICIENT" else "SUFFICIENT — CHECK §35 BOXES")
    return {"generated_by": "faisal_method_v41/analysis.py", "contract": "V41_prereg §⑧-⑮",
            "holdout_seal": man["seal"]["sha256"], "holdout_summary": man["summary"], "provenance_summary": prov["summary"],
            "historical_contaminated": hist, "golden_generalization": golden_generalization(ev, prov),
            "golden": {k: ev["golden_v31_vs_v4"][k] for k in ("v31_matched", "v4_matched", "always_wait_baseline", "dated", "of")},
            "sample_size": sample_size(cases), "prospective": pro, "status": overall,
            "posthoc_disclosure": first_run_reconstruction(ev, prov, man)}


def write(obj=None):
    obj = obj or build()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, sort_keys=True, default=str)
        f.write("\n")
    return obj


if __name__ == "__main__":
    o = write()
    print(o["status"], json.dumps(o["prospective"]["matrix"]["n"]))
