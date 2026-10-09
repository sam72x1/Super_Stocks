# -*- coding: utf-8 -*-
"""🧭🔀 stage_crosswalk — مقارنةُ حالات فيصل المصدريّة بحالات المحرّك البحثيّ حرفًا بعقد STAGE_SEMANTICS_PROTOCOL.md (مدموجٌ قبل أيّ رقم).
بحثٌ فقط · EXPLORATORY · لا إنتاج · لا V4 · لا H6 · لا تلغرام · لا شبكة.

خطوتان:
  `python3 faisal_engine/stage_crosswalk.py engine` — قراءةُ المحرّك (`replay.read` نفسُه: engine.evaluate على الشموع المجمَّدة · شموعٌ قبل
      اليوم حصرًا) لكلّ (رمز · جلسة) يحتاجها العقد ⟵ out/stage_engine_reads.csv (عمليّةٌ مستقلّة بـFAISAL_ONLY=1 كما replay.py).
  `python3 faisal_engine/stage_crosswalk.py` — التحليل من السجلّ ‏+ قراءات المحرّك المخزَّنة ⟵ out/stage_crosswalk.csv ·
      out/stage_overlay.csv · out/stage_case_timelines.csv · out/stage_crosswalk_summary.json — حتميٌّ (`--check`).

`overlay_asof(symbol, day)` = الطبقةُ البحثيّة المنفصلة عن المحرّك المجمَّد: حقولُ المصدر لا تُستنتَج من المحرّك ولا تُمَدّ عبر الفجوات."""
import csv
import gzip
import hashlib
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import stage_ledger as SL          # noqa: E402

OUT = os.environ.get("FE_STAGE_OUT") or os.path.join(HERE, "out")
READS = os.path.join(HERE, "out", "stage_engine_reads.csv")
RANK_C = os.path.join(HERE, "out", "rank_top108_C.csv.gz")
IN_PROCESS = ("FOCUS", "WATCH", "READY", "TRIGGER", "HOLD")
OUT_PROCESS = ("REJECTED", "INSUFFICIENT_DATA")
STRICT_TS = ("EXACT_PRINTED", "EXACT_DATE_PRINTED", "EXACT_DERIVED")
BROAD_TS = STRICT_TS + ("DERIVED_INFERRED", "RECORDED_UNVERIFIED", "BOUNDED")
MAX_WINDOW = 10          # §1 — نافذةٌ أطول ⟵ WINDOW_TOO_WIDE
D_SPAN = 60              # §3b — مدى المثابرة في المقارنة D
H1_MIN_READY = 3         # §4
H2_MIN_MEMBERS = 5       # §5
H3_MIN_SYMBOLS = 3       # §6
WAITISH = ("WAIT", "MONITOR", "WAIT_FOR_PRESS")
TRIGGERS = ("PRESS_OBSERVED", "OPERATOR_MONEY_OBSERVED", "ENTRY_EXECUTED")


# ------------------------------------------------------------------ الجلسات
def sessions_in(lo, hi):
    cal = SL.calendar()
    return [d for d in cal if lo <= d <= hi] if lo and hi else []


def sessions_back(day, n):
    cal = SL.calendar()
    i = cal.index(day) if day in cal else None
    return cal[max(0, i - n)] if i is not None else None


# ------------------------------------------------------------------ قراءةُ المحرّك (خطوةٌ مستقلّة)
def engine_read(sym, day):
    """= faisal_engine/replay.read حرفًا: engine.evaluate(sym, data.bars(sym), day, data.context(sym, day), label="HISTORICAL")."""
    import engine as E          # noqa: PLC0415 — كسولٌ: التحليلُ لا يستورد المحرّك
    import data as D            # noqa: PLC0415
    return E.evaluate(sym, D.bars(sym), day, D.context(sym, day), label="HISTORICAL")


def needed_reads(events):
    """(رمز · جلسة) المطلوبة: نوافذُ أحداث فيصل المؤهّلة (≤ 10 جلسات · شموعٌ متاحة) ‏+ مدى D لرموز المثابرة."""
    need = set()
    for e in events:
        if e["is_faisal"] != "1" or not e["identity"] or not e["asof_lo"] or e["md_available"] != "YES" or e["ts_quality"] not in BROAD_TS:
            continue
        ss = sessions_in(e["asof_lo"], e["asof_hi"] or e["asof_lo"])
        if 0 < len(ss) <= MAX_WINDOW:
            need |= {(e["identity"], d) for d in ss}
    for sym, eps in d_candidates(events).items():
        lo, hi = eps[0]["lo"], eps[-1]["hi"]
        ss = sessions_in(lo, hi)
        if len(ss) <= D_SPAN:
            need |= {(sym, d) for d in ss}
    return sorted(need)


READ_COLS = ["symbol", "session", "stage", "first_failed", "tech_state", "v4_state", "frame", "blocks", "missing", "bars_last"]


def write_engine_reads(events, path=READS):
    rows = []
    for sym, day in needed_reads(events):
        r = engine_read(sym, day)
        rows.append(dict(symbol=sym, session=day, stage=r["stage"],
                         first_failed=(r.get("first_failed") or {}).get("rule", ""),
                         tech_state=(r.get("v4") or {}).get("tech_state") or "",
                         v4_state=(r.get("v4") or {}).get("state") or "",
                         frame=(r.get("screen") or {}).get("frame") or "",
                         blocks=" | ".join(b["rule"] for b in r.get("blocks") or []),
                         missing=len(r.get("missing_data") or []),
                         bars_last=(r.get("provenance") or {}).get("bars_last") or ""))
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=READ_COLS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    return len(rows)


# ------------------------------------------------------------------ التحليل
def load_events():
    return list(csv.DictReader(open(os.path.join(HERE, "out", "stage_events.csv"), encoding="utf-8")))


def load_reads(path=READS):
    return {(r["symbol"], r["session"]): r for r in csv.DictReader(open(path, encoding="utf-8"))}


def subset_of(e):
    """§2 ⟵ STRICT · BROAD · أو سببُ الاستبعاد."""
    if e["is_faisal"] != "1":
        return "EXCLUDED:NOT_FAISAL"
    if not e["identity"]:
        return "EXCLUDED:NO_IDENTITY"
    if e["ts_quality"] == "AMBIGUOUS" or not e["asof_lo"]:
        return "EXCLUDED:AMBIGUOUS_TIMESTAMP"
    if e["confidence"] not in ("HIGH", "MEDIUM"):
        return "EXCLUDED:LOW_CONFIDENCE"
    strict = (e["confidence"] == "HIGH" and e["ts_quality"] in STRICT_TS
              and (e["identity_basis"] == "VISIBLE" or e["identity_basis"].startswith("STRONGLY_SUPPORTED")))
    return "STRICT" if strict else ("BROAD" if e["ts_quality"] in BROAD_TS else "EXCLUDED:TIMESTAMP")


def engine_at(e, reads):
    """§1 ⟵ (stage, detail): نفسُ المرحلة في كلّ جلسات النافذة ⟵ تلك المرحلة · وإلّا VARIES · أطولُ من 10 ⟵ WINDOW_TOO_WIDE."""
    if e["md_available"] != "YES":
        return "UNAVAILABLE", {}
    ss = sessions_in(e["asof_lo"], e["asof_hi"] or e["asof_lo"])
    if not ss:
        return "UNAVAILABLE", {}
    if len(ss) > MAX_WINDOW:
        return "WINDOW_TOO_WIDE", {}
    rr = [reads.get((e["identity"], d)) for d in ss]
    if any(r is None for r in rr):
        return "UNAVAILABLE", {}
    st = {r["stage"] for r in rr}
    if len(st) > 1:
        return "VARIES", {"stages": " → ".join(r["stage"] for r in rr)}
    return st.pop(), rr[0]


def eclass(stage):
    if stage in OUT_PROCESS:
        return "OUT"
    if stage in ("TRIGGER", "HOLD"):
        return "TRIGGER/HOLD"
    return stage


def _split(x):
    return [t for t in (x or "").split("+") if t]


def rank_context():
    if not os.path.exists(RANK_C):
        return {}
    out = {}
    for r in csv.DictReader(gzip.open(RANK_C, "rt", encoding="utf-8")):
        out[(r["symbol"], r["date"])] = int(r["rank"])
    return out


def d_candidates(events):
    """§7-D: رموزٌ لها حلقتان فأكثر من فيصل تحمل WAIT/MONITOR أو إحالةً سابقة (طابعٌ غيرُ ملتبس · ثقةٌ HIGH/MEDIUM)."""
    by = {}
    for e in events:
        if e["is_faisal"] != "1" or not e["identity"] or not e["asof_lo"] or e["ts_quality"] == "AMBIGUOUS":
            continue
        if e["confidence"] not in ("HIGH", "MEDIUM"):
            continue
        if not (set(_split(e["C_action"])) & set(WAITISH) or e["carry_forward_state"]):
            continue
        by.setdefault(e["identity"], {}).setdefault(e["episode_id"], []).append(e)
    out = {}
    for sym, eps in by.items():
        if len(eps) >= 2:
            lst = [dict(id=k, lo=min(x["asof_lo"] for x in v), hi=max(x["asof_hi"] or x["asof_lo"] for x in v), events=v) for k, v in eps.items()]
            out[sym] = sorted(lst, key=lambda d: (d["lo"], d["hi"], d["id"]))
    return out


def analyze(events, reads):
    ranks = rank_context()
    rows = []
    for e in events:
        if e["is_faisal"] != "1" or not e["identity"]:
            continue
        sub = subset_of(e)
        stage, det = engine_at(e, reads) if not sub.startswith("EXCLUDED") else ("NOT_COMPARED", {})
        rk = ranks.get((e["identity"], e["asof_lo"])) if stage not in ("NOT_COMPARED",) else None
        rows.append(dict(event_id=e["event_id"], identity=e["identity"], episode_id=e["episode_id"], source_ref=e["source_ref"],
                         statement=e["statement"], subset=sub, ts_quality=e["ts_quality"], asof_lo=e["asof_lo"], asof_hi=e["asof_hi"],
                         raw_label=e["raw_label"], raw_action=e["raw_action"], A_list=e["A_list"], B_stage=e["B_stage"],
                         readiness_recalled=e["readiness_recalled"], C_action=e["C_action"], E_trigger=e["E_trigger"],
                         carry_forward_state=e["carry_forward_state"], engine_stage=stage, engine_class=eclass(stage) if stage in IN_PROCESS + OUT_PROCESS else "",
                         first_failed=det.get("first_failed", ""), tech_state=det.get("tech_state", ""), v4_state=det.get("v4_state", ""),
                         frame=det.get("frame", ""), blocks=det.get("blocks", ""), varies=det.get("stages", ""),
                         rank_C=rk if rk is not None else "", diagnosis=""))
    for r in rows:
        r["diagnosis"] = diagnose(r)
    return rows


def determinable(r):
    return r["engine_stage"] in IN_PROCESS + OUT_PROCESS


def diagnose(r):
    """§8 — أوّلُ صفٍّ يطابق بالترتيب."""
    if r["subset"] == "EXCLUDED:AMBIGUOUS_TIMESTAMP" or r["engine_stage"] in ("VARIES", "WINDOW_TOO_WIDE"):
        return "Ambiguous source timestamp"
    if r["subset"].startswith("EXCLUDED") or r["engine_stage"] == "UNAVAILABLE":
        return "Missing source evidence"
    b = set(_split(r["B_stage"]))
    if not (r["A_list"] or b or r["C_action"] or r["E_trigger"] or r["carry_forward_state"]):
        return "Missing source evidence"
    if r["E_trigger"] and set(_split(r["E_trigger"])) & set(TRIGGERS):
        return "Unobservable decision or trigger"
    ready = "READY" in b and r["readiness_recalled"] != "1"
    if ready and r["engine_class"] == "OUT":
        return "Wrong candidate-generation logic"
    if ready and r["engine_stage"] in IN_PROCESS and r["engine_stage"] != "READY":
        return "Wrong technical pattern classification"
    if r["A_list"] == "LIST_SNAPSHOT_VISIBLE":
        return "Wrong mapping from technical state to Faisal's attention state"
    if (r["carry_forward_state"] or set(_split(r["C_action"])) & set(WAITISH)) and r["engine_class"] == "OUT":
        return "Wrong temporal persistence representation"
    if r["engine_stage"] in IN_PROCESS and r["rank_C"] == "" and r["asof_lo"] >= "2026-08-07":
        return "Wrong ranking among candidates with comparable states"
    return "No demonstrable failure"


def _episodes(rows, pick, subset):
    """حلقاتُ فيصل ⟵ [ (episode, label_set, engine_stage) ] للمقبول في الفئة (STRICT ⊂ BROAD)."""
    ok = ("STRICT",) if subset == "STRICT" else ("STRICT", "BROAD")
    by = {}
    for r in rows:
        if r["subset"] in ok and pick(r):
            by.setdefault(r["episode_id"], []).append(r)
    out = []
    for ep, rr in sorted(by.items()):
        st = {r["engine_stage"] for r in rr}
        out.append(dict(episode=ep, identity=rr[0]["identity"], rows=rr, engine=(st.pop() if len(st) == 1 else "VARIES")))
    return out


def h1(rows, subset):
    eps = _episodes(rows, lambda r: (set(_split(r["B_stage"])) & {"READY", "NOT_READY"}) and r["readiness_recalled"] != "1", subset)
    tab = []
    for ep in eps:
        lab = set()
        for r in ep["rows"]:
            lab |= set(_split(r["B_stage"])) & {"READY", "NOT_READY"}
        src = "CONTRADICTED_SOURCE" if len(lab) == 2 else lab.pop()
        tab.append(dict(episode=ep["episode"], identity=ep["identity"], source=src, engine=ep["engine"],
                        asof=ep["rows"][0]["asof_lo"] + ".." + ep["rows"][0]["asof_hi"],
                        first_failed=ep["rows"][0]["first_failed"], refs=" ".join(sorted({r["source_ref"] + ":" + r["statement"] for r in ep["rows"]}))))
    det = [t for t in tab if t["engine"] in IN_PROCESS + OUT_PROCESS and t["source"] != "CONTRADICTED_SOURCE"]
    eng_ready = [t for t in det if t["engine"] == "READY"]
    bad = [t for t in eng_ready if t["source"] == "NOT_READY"]
    if len(bad) >= 2 or (len(eng_ready) >= 2 and len(bad) * 2 >= len(eng_ready) and bad):
        verdict = "CONTRADICTED"
    elif len(eng_ready) >= H1_MIN_READY and not bad:
        verdict = "SUPPORTED"
    else:
        verdict = "INSUFFICIENT EVIDENCE"
    dist = {}
    for t in det:
        dist.setdefault(t["source"], {}).setdefault(t["engine"], 0)
        dist[t["source"]][t["engine"]] += 1
    return dict(subset=subset, verdict=verdict, episodes=len(tab), determinable=len(det), engine_ready=len(eng_ready),
                engine_ready_with_faisal_not_ready=len(bad), source_by_engine=dist, table=tab)


def h2(rows, events, subset):
    snaps = [r for r in rows if r["A_list"] == "LIST_SNAPSHOT_VISIBLE" and r["subset"] in (("STRICT",) if subset == "STRICT" else ("STRICT", "BROAD"))]
    members = {}
    for r in snaps:
        members.setdefault((r["identity"], r["asof_lo"]), r)
    a = any(e["source_ref"] == "X_20260918_22_pipeline" and e["statement"] == "s1" and "SORT" in e["B_stage"] and e["confidence"] == "HIGH"
            for e in events)
    tab, classes = [], set()
    trig = [e for e in events if e["is_faisal"] == "1" and e["identity"] and e["asof_lo"] and e["ts_quality"] != "AMBIGUOUS"
            and set(_split(e["E_trigger"])) & set(TRIGGERS + ("ENTRY_STATED",))]
    c_hits = []
    for (sym, asof), r in sorted(members.items()):
        tab.append(dict(identity=sym, asof=asof, engine=r["engine_stage"], included=("YES" if r["engine_stage"] in IN_PROCESS else
                        ("NO" if r["engine_stage"] in OUT_PROCESS else "UNKNOWN")), first_failed=r["first_failed"], rank_C=r["rank_C"]))
        if determinable(r):
            classes.add(eclass(r["engine_stage"]))
        lo10 = sessions_back(asof, 10)
        for e in trig:
            if e["identity"] == sym and lo10 and lo10 <= e["asof_lo"] and (e["asof_hi"] or e["asof_lo"]) <= asof:
                c_hits.append(f"{sym}:{e['source_ref']}:{e['statement']}:{e['E_trigger']}")
    det = [t for t in tab if t["engine"] in IN_PROCESS + OUT_PROCESS]
    if len(det) >= H2_MIN_MEMBERS and a and (len(classes) >= 2 or c_hits):
        verdict = "SUPPORTED"
    elif len(det) >= H2_MIN_MEMBERS and len(classes) == 1 and next(iter(classes)) != "OUT":
        verdict = "CONTRADICTED"
    else:
        verdict = "INSUFFICIENT EVIDENCE"
    return dict(subset=subset, verdict=verdict, members=len(tab), determinable=len(det), classes=sorted(classes),
                pipeline_statement=a, entry_within_10_sessions=c_hits, table=tab)


def h3(rows, subset):
    ok = ("STRICT",) if subset == "STRICT" else ("STRICT", "BROAD")
    by = {}
    for r in rows:
        if r["subset"] in ok and r["carry_forward_state"]:
            by.setdefault(r["identity"], []).append(r)
    tab = []
    for sym, rr in sorted(by.items()):
        cls = {eclass(r["engine_stage"]) for r in rr if determinable(r)}
        st = "OUT" if cls == {"OUT"} else ("IN" if cls and "OUT" not in cls else ("MIXED" if cls else "UNDETERMINED"))
        tab.append(dict(identity=sym, status=st, events=" ".join(f"{r['source_ref']}:{r['statement']}@{r['asof_lo']}={r['engine_stage']}" for r in rr),
                        markers=" ".join(sorted({r["carry_forward_state"] for r in rr}))))
    det = [t for t in tab if t["status"] in ("OUT", "IN", "MIXED")]
    n_out = sum(1 for t in det if t["status"] == "OUT")
    if len(det) >= H3_MIN_SYMBOLS and n_out >= 2:
        verdict = "SUPPORTED"
    elif len(det) >= H3_MIN_SYMBOLS and all(t["status"] == "IN" for t in det):
        verdict = "CONTRADICTED"
    else:
        verdict = "INSUFFICIENT EVIDENCE"
    return dict(subset=subset, verdict=verdict, symbols=len(tab), determinable=len(det), out_of_process=n_out, table=tab)


def comp_c(rows):
    out = []
    for r in rows:
        if r["subset"].startswith("EXCLUDED") or not (set(_split(r["E_trigger"])) & set(TRIGGERS)):
            continue
        out.append(dict(identity=r["identity"], ref=f"{r['source_ref']}:{r['statement']}", subset=r["subset"], E=r["E_trigger"],
                        asof=r["asof_lo"], engine_before_trigger=r["engine_stage"], trigger="NOT_REPRESENTABLE (operator_press UNKNOWN historically)"))
    return out


def comp_d(events, reads):
    out = []
    for sym, eps in sorted(d_candidates(events).items()):
        ss = sessions_in(eps[0]["lo"], eps[-1]["hi"])
        per = []
        for ep in eps:
            st = {reads.get((sym, d), {}).get("stage", "UNAVAILABLE") for d in sessions_in(ep["lo"], ep["hi"])}
            per.append(f"{ep['id']}[{ep['lo']}..{ep['hi']}]={'/'.join(sorted(st))}")
        share = ""
        if len(ss) <= D_SPAN:
            got = [reads.get((sym, d), {}).get("stage") for d in ss]
            if all(g is not None for g in got) and got:
                share = round(sum(1 for g in got if g in IN_PROCESS) / len(got), 4)
        out.append(dict(identity=sym, episodes=len(eps), span_sessions=len(ss), per_episode=" ; ".join(per), in_process_share=share))
    return out


def comp_e(rows, subset):
    eps = _episodes(rows, lambda r: bool(set(_split(r["C_action"])) & set(WAITISH)) and not (set(_split(r["E_trigger"])) & set(TRIGGERS)), subset)
    cat = {"engine WATCH": 0, "engine other in-process": 0, "engine out-of-process": 0, "not determinable": 0}
    for ep in eps:
        g = ep["engine"]
        cat["engine WATCH" if g == "WATCH" else ("engine other in-process" if g in IN_PROCESS else
            ("engine out-of-process" if g in OUT_PROCESS else "not determinable"))] += 1
    return dict(subset=subset, episodes=len(eps), categories=cat)


def overlay_rows(rows):
    """§10 من المهمّة — طبقةُ مصدرٍ منفصلة: لكلّ (رمز · يوم قرار) ما رصده المصدرُ بجانب ما يقوله المحرّك — لا يُشتقّ حقلٌ من الآخر."""
    by = {}
    for r in rows:
        if r["subset"].startswith("EXCLUDED"):
            continue
        by.setdefault((r["identity"], r["asof_lo"], r["asof_hi"]), []).append(r)
    out = []
    for (sym, lo, hi), rr in sorted(by.items()):
        lst = sorted({r["A_list"] for r in rr if r["A_list"]})
        b = sorted({x + ("(RECALLED)" if r["readiness_recalled"] == "1" else "") for r in rr for x in _split(r["B_stage"])})
        out.append(dict(
            identity=sym, asof_lo=lo, asof_hi=hi,
            SOURCE_LIST_STATE=("VISIBLE_IN_TAB «قائمتي»" if "LIST_SNAPSHOT_VISIBLE" in lst else ("STATED_ADD" if lst else "UNKNOWN")),
            SOURCE_SELECTION_STAGE=("+".join(b) if b else "UNKNOWN"),
            TECHNICAL_ENGINE_STAGE="/".join(sorted({r["engine_stage"] for r in rr})),
            OBSERVED_ACTION="+".join(sorted({x for r in rr for x in _split(r["C_action"])})) or "UNKNOWN",
            TRIGGER_STATE="+".join(sorted({x for r in rr for x in _split(r["E_trigger"])})) or "UNKNOWN",
            EVIDENCE_STATUS=("STRICT" if any(r["subset"] == "STRICT" for r in rr) else "BROAD") + " · " + " ".join(sorted(r["event_id"] for r in rr))))
    return out


def overlay_asof(symbol, day, overlay=None):
    """الحالةُ المصدريّة يومَ `day`: ما رُصد في نافذةٍ تحوي اليوم وحدَه · خارجها UNKNOWN مع آخر رصدٍ سابق (لا امتدادَ عبر الفجوات ·
    ولا يُقرأ أيُّ حدثٍ لاحقٍ لليوم)."""
    ov = overlay if overlay is not None else list(csv.DictReader(open(os.path.join(HERE, "out", "stage_overlay.csv"), encoding="utf-8")))
    own = [o for o in ov if o["identity"] == symbol and o["asof_lo"] <= day]
    cur = [o for o in own if day <= (o["asof_hi"] or o["asof_lo"])]
    if cur:
        return dict(cur[-1], observed="IN_WINDOW")
    prev = sorted(own, key=lambda o: (o["asof_hi"] or o["asof_lo"]))
    return dict(identity=symbol, SOURCE_LIST_STATE="UNKNOWN", SOURCE_SELECTION_STAGE="UNKNOWN", OBSERVED_ACTION="UNKNOWN",
                TRIGGER_STATE="UNKNOWN", TECHNICAL_ENGINE_STAGE="(read the engine separately)",
                EVIDENCE_STATUS="NO OBSERVATION ON THIS DAY", observed="GAP",
                last_observed=(f"{prev[-1]['asof_lo']}..{prev[-1]['asof_hi']}" if prev else ""))


def case_timelines(rows, events):
    out = []
    for r in sorted(rows, key=lambda r: (r["identity"], r["asof_lo"] or "9999", r["source_ref"], r["statement"])):
        out.append(dict(identity=r["identity"], asof_lo=r["asof_lo"], asof_hi=r["asof_hi"], ts_quality=r["ts_quality"], subset=r["subset"],
                        source_ref=f"{r['source_ref']}:{r['statement']}", raw=(r["raw_label"] + " " + r["raw_action"]).strip(),
                        A=r["A_list"], B=r["B_stage"] + ("(RECALLED)" if r["readiness_recalled"] == "1" and r["B_stage"] else ""),
                        C=r["C_action"], E=r["E_trigger"], engine=r["engine_stage"], first_failed=r["first_failed"], rank_C=r["rank_C"],
                        diagnosis=r["diagnosis"]))
    return out


def predictions(res):
    h1b = res["H1"]["BROAD"]
    ready_eps = [t for t in h1b["table"] if t["source"] == "READY" and t["engine"] in IN_PROCESS + OUT_PROCESS]
    p2 = (sum(1 for t in ready_eps if t["engine"] in OUT_PROCESS) * 2 >= len(ready_eps)) if ready_eps else None
    c = res["C"]
    cdet = [x for x in c if x["engine_before_trigger"] in IN_PROCESS + OUT_PROCESS]
    p4 = (sum(1 for x in cdet if x["engine_before_trigger"] == "READY") * 2 < len(cdet)) if cdet else None
    eb = res["E"]["BROAD"]["categories"]
    tot = eb["engine WATCH"] + eb["engine other in-process"] + eb["engine out-of-process"]
    p5 = (eb["engine WATCH"] * 2 < tot) if tot else None
    return {"P1 H1 strict INSUFFICIENT ⟹ verdict 3": res["H1"]["STRICT"]["verdict"] == "INSUFFICIENT EVIDENCE",
            "P2 broad Faisal-READY mostly out-of-process": p2,
            "P3 «قائمتي» members span 2+ engine classes": len(res["H2"]["STRICT"]["classes"]) >= 2,
            "P4 under half of C episodes engine READY": p4,
            "P5 engine WATCH under half of broad E": p5}


def verdict(res):
    h1s, h2s, h3b = res["H1"]["STRICT"]["verdict"], res["H2"]["STRICT"]["verdict"], res["H3"]["BROAD"]["verdict"]
    if h1s == "CONTRADICTED":
        return 4, "CURRENT ENGINE STATES CONTRADICT DOCUMENTED FAISAL STATES"
    if h1s == "SUPPORTED":
        return (2, "STAGE MAPPING PARTIALLY SUPPORTED") if "CONTRADICTED" in (h2s, h3b) else (1, "STAGE MAPPING SUPPORTED BY DIRECT EVIDENCE")
    return 3, "INSUFFICIENT EVIDENCE TO ESTABLISH THE MAPPING"


def run(events=None, reads=None):
    events = events if events is not None else load_events()
    reads = reads if reads is not None else load_reads()
    rows = analyze(events, reads)
    res = {"H1": {s: h1(rows, s) for s in ("STRICT", "BROAD")},
           "H2": {s: h2(rows, events, s) for s in ("STRICT", "BROAD")},
           "H3": {s: h3(rows, s) for s in ("STRICT", "BROAD")},
           "C": comp_c(rows), "D": comp_d(events, reads), "E": {s: comp_e(rows, s) for s in ("STRICT", "BROAD")}}
    res["predictions"] = predictions(res)
    res["verdict"] = verdict(res)
    res["counts"] = dict(compared_events=sum(1 for r in rows if not r["subset"].startswith("EXCLUDED")),
                         strict_events=sum(1 for r in rows if r["subset"] == "STRICT"),
                         broad_events=sum(1 for r in rows if r["subset"] == "BROAD"),
                         excluded=dict(sorted({k: sum(1 for r in rows if r["subset"] == k) for k in {r["subset"] for r in rows if r["subset"].startswith("EXCLUDED")}}.items())),
                         engine_stage=dict(sorted({k: sum(1 for r in rows if r["engine_stage"] == k) for k in {r["engine_stage"] for r in rows}}.items())),
                         diagnosis=dict(sorted({k: sum(1 for r in rows if r["diagnosis"] == k) for k in {r["diagnosis"] for r in rows}}.items())))
    res["label"] = "EXPLORATORY — historical cases already shaped the method (STAGE_SEMANTICS_PROTOCOL.md §0)"
    return rows, res


def _csv(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        if not rows:
            fh.write("\n")
            return
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


FILES = ("stage_crosswalk.csv", "stage_overlay.csv", "stage_case_timelines.csv", "stage_crosswalk_summary.json", "STAGE_SEMANTICS_RESULT.md")
CASES = ("DKI", "SXTC", "HUBC", "NUWE", "AMIX", "HCWB", "CDIO", "KWM", "RAYA", "BTOG", "ELPW", "GCTK", "CUPR", "YMT", "NCT", "BRTX", "CDT")


def _md_table(rows, cols):
    if not rows:
        return ["(none)"]
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        out.append("| " + " | ".join(str(r.get(c, "")).replace("|", "/") for c in cols) + " |")
    return out


def render_result(res, rows, ledger, overlay):
    """STAGE_SEMANTICS_RESULT.md — كلُّ رقمٍ من المخرَج (السجلّ · القراءات · التحليل) لا باليد."""
    L = ["# 🧭🔀 STAGE_SEMANTICS_RESULT — generated by `stage_crosswalk.py` (every figure from committed outputs)", "",
         f"> Contract `STAGE_SEMANTICS_PROTOCOL.md` (merged before any comparison) · label **{res['label']}**", "",
         "## ① Evidence counts (source ledger `out/stage_ledger_summary.json`)", ""]
    for k in ("events_total", "events_faisal", "events_faisal_with_identity", "events_faisal_dated", "source_units_faisal_dated",
              "symbols_faisal_dated", "episodes_total", "episodes_with_faisal", "strict_timestamp_events", "direct_list_snapshot_events",
              "direct_list_state_events", "explicit_readiness_events", "explicit_readiness_not_recalled", "technical_only_events",
              "chart_only_events", "unknown_events", "ambiguous_ts_faisal", "carry_forward_state_events", "eye_reads", "eye_statements",
              "phase3_rows", "phase3_symbols"):
        L.append(f"- `{k}`: {ledger.get(k)}")
    L += ["", f"- timestamp quality (Faisal events): {ledger['ts_quality_faisal']}",
          f"- Phase-3 reconciliation (88 decision units): {ledger['phase3_findings']}",
          f"- comparison subsets: {res['counts']['strict_events']} strict · {res['counts']['broad_events']} broad · excluded {res['counts']['excluded']}",
          f"- engine stage at compared events: {res['counts']['engine_stage']}", ""]
    for h, cols in (("H1", ["identity", "asof", "source", "engine", "first_failed", "refs"]),):
        for sub in ("STRICT", "BROAD"):
            x = res[h][sub]
            L += [f"## ② {h} {sub} — **{x['verdict']}** (episodes {x['episodes']} · determinable {x['determinable']} · engine READY {x['engine_ready']} · "
                  f"engine READY ∧ Faisal NOT_READY {x['engine_ready_with_faisal_not_ready']})", ""] + _md_table(x["table"], cols) + [""]
    for sub in ("STRICT", "BROAD"):
        x = res["H2"][sub]
        L += [f"## ③ H2 {sub} — **{x['verdict']}** (members {x['members']} · determinable {x['determinable']} · engine classes {x['classes']} · "
              f"pipeline statement {x['pipeline_statement']} · entry within 10 sessions {x['entry_within_10_sessions']})", ""]
        L += _md_table(x["table"], ["identity", "asof", "engine", "included", "first_failed", "rank_C"]) + [""]
    for sub in ("STRICT", "BROAD"):
        x = res["H3"][sub]
        L += [f"## ④ H3 {sub} — **{x['verdict']}** (symbols {x['symbols']} · determinable {x['determinable']} · out-of-process {x['out_of_process']})", ""]
        L += _md_table(x["table"], ["identity", "status", "markers", "events"]) + [""]
    L += ["## ⑤ Comparison C — entry / pressure vs engine (TRIGGER not observable historically)", ""]
    L += _md_table(res["C"], ["identity", "ref", "subset", "E", "asof", "engine_before_trigger", "trigger"]) + [""]
    L += ["## ⑥ Comparison D — continued watch vs engine persistence (source continuity between observations NOT claimed)", ""]
    L += _md_table(res["D"], ["identity", "episodes", "span_sessions", "in_process_share", "per_episode"]) + [""]
    L += ["## ⑦ Comparison E — waiting / monitoring vs engine stage (episodes)", ""]
    for sub in ("STRICT", "BROAD"):
        L.append(f"- {sub}: episodes {res['E'][sub]['episodes']} · {res['E'][sub]['categories']}")
    L += ["", "## ⑧ Diagnosis (per compared or excluded Faisal event · §8 rules)", "", f"- {res['counts']['diagnosis']}", ""]
    case_rows = []
    for c in CASES:
        rr = [r for r in rows if r["identity"] == c]
        if rr:
            case_rows.append(dict(case=c, events=len(rr), compared=sum(1 for r in rr if not r["subset"].startswith("EXCLUDED")),
                                  engine=" ".join(sorted({r["engine_stage"] for r in rr})),
                                  diagnoses=" · ".join(sorted({r["diagnosis"] for r in rr}))))
    L += _md_table(case_rows, ["case", "events", "compared", "engine", "diagnoses"]) + [""]
    L += ["## ⑨ Research overlay excerpt (`out/stage_overlay.csv` · source fields never derived from the engine)", ""]
    L += _md_table([o for o in overlay if o["identity"] in CASES], ["identity", "asof_lo", "asof_hi", "SOURCE_LIST_STATE", "SOURCE_SELECTION_STAGE",
                                                                    "TECHNICAL_ENGINE_STAGE", "OBSERVED_ACTION", "TRIGGER_STATE", "EVIDENCE_STATUS"]) + [""]
    L += ["## ⑩ Predictions (contract §10) and verdict (§9)", ""]
    L += [f"- {k}: {'TRUE' if v else ('FALSE' if v is False else 'UNDEFINED')}" for k, v in res["predictions"].items()]
    L += ["", f"**Verdict {res['verdict'][0]} — {res['verdict'][1]}**", ""]
    return "\n".join(L)


def _doc_dir(out):
    return HERE if os.path.abspath(out) == os.path.abspath(OUT) else out


def write(out=OUT):
    os.makedirs(out, exist_ok=True)
    events = load_events()
    rows, res = run(events)
    ov = overlay_rows(rows)
    _csv(os.path.join(out, "stage_crosswalk.csv"), rows)
    _csv(os.path.join(out, "stage_overlay.csv"), ov)
    _csv(os.path.join(out, "stage_case_timelines.csv"), case_timelines(rows, events))
    with open(os.path.join(out, "stage_crosswalk_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1, sort_keys=True, default=str)
        fh.write("\n")
    ledger = json.load(open(os.path.join(HERE, "out", "stage_ledger_summary.json"), encoding="utf-8"))
    with open(os.path.join(_doc_dir(out), "STAGE_SEMANTICS_RESULT.md"), "w", encoding="utf-8") as fh:
        fh.write(render_result(res, rows, ledger, ov) + "\n")
    return res


def check(out=None):
    bad = []
    with tempfile.TemporaryDirectory(prefix="stage_xw_") as tmp:
        write(tmp)
        for f in FILES:
            a = hashlib.sha256(open(os.path.join(tmp, f), "rb").read()).hexdigest()
            p = os.path.join(_doc_dir(out or OUT) if f.endswith(".md") else (out or OUT), f)
            b = hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None
            if a != b:
                bad.append(f)
    return bad


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "engine":
        os.environ["FAISAL_ONLY"] = "1"             # كما replay.py (يُضبط قبل أيّ استيرادٍ للبوت)
        os.chdir(ROOT)
        print("engine reads:", write_engine_reads(load_events()))
        sys.exit(0)
    if "--check" in sys.argv:
        bad = check()
        print("✅ regenerated identically" if not bad else f"❌ differs: {bad}")
        sys.exit(1 if bad else 0)
    r = write()
    print(json.dumps({k: r[k] for k in ("verdict", "predictions", "counts")}, ensure_ascii=False, indent=1, default=str))
