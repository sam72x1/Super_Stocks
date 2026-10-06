# -*- coding: utf-8 -*-
"""
🧭 FAISAL V4 — إعادةُ التقييم محلّيًّا من الشموع المحفوظة (§⑭ · §36) ‏+ الحالاتُ الذهبيّة ‏+ DXST ‏+ VEEE — حتميّ · بلا شبكة.

المدخلات (كلُّها في المستودع):
  data/v4_bars_fixture.json        — حمولةُ وضع fetch كما طُبعت في سجلّ Actions حرفًا (مُعادةُ التجميع من أجزاء V4OUT)
  data/v4_bars_fixture.sha256      — بصمتُها
  results/v4_metrics_actions.json  — المقاييسُ كما حسبها Actions (من الأجزاء نفسِها)
  ../faisal_method_v3/v31/golden_fixtures.json — شموعُ V3.1 المجمَّدة (DXST 30 دقيقة · VEEE يوميّ · الحالاتُ الذهبيّة)
المخرج: results/v4_eval_results.json — المصفوفة · المقاييس · «يطابق Actions؟» · الذهبيّة V3.1 مقابل V4 · DXST · VEEE.

⚖️ التشغيلةُ الأولى هي النتيجة (§⑭) · ولا تسامحَ يُوسَّع (§19) · وVEEE `POST-HOC-INSPECTED` (§①).
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "faisal_method_v3"))
import decision_engine as E      # noqa: E402
import v4_eval as EV             # noqa: E402
import v4_run as RUN             # noqa: E402

FIXTURE = os.path.join(HERE, "data", "v4_bars_fixture.json")
FIXTURE_SHA = os.path.join(HERE, "data", "v4_bars_fixture.sha256")
ACTIONS_METRICS = os.path.join(HERE, "results", "v4_metrics_actions.json")
GOLDEN = os.path.join(ROOT, "faisal_method_v3", "v31", "golden_fixtures.json")
GOLDEN_V31 = os.path.join(ROOT, "faisal_method_v3", "v31", "golden_cases_v31.json")
OUT = os.path.join(HERE, "results", "v4_eval_results.json")
TECH_TO_WORD = {"WAIT": "WAIT", "TECH_READY": "READY", "UNKNOWN": "UNKNOWN", None: None}


def reassemble(text, prefix="V4OUT"):
    """أجزاءُ «prefix|الاسم|i|n|جزء» في نصّ سجلٍّ ⟵ {الاسم: النصّ الكامل} للمكتمل وحدَه · و{الاسم: (وصل، من)} للناقص."""
    chunks = {}
    for line in text.split("\n"):
        m = re.search(prefix + r"\|([^|]+)\|(\d+)\|(\d+)\|(.*)$", line.rstrip("\r"))
        if m:
            chunks.setdefault(m.group(1), {})[int(m.group(2))] = (int(m.group(3)), m.group(4))
    full, partial = {}, {}
    for name, ch in chunks.items():
        n = next(iter(ch.values()))[0]
        if len(ch) == n and all(i in ch for i in range(1, n + 1)):
            full[name] = "".join(ch[i][1] for i in range(1, n + 1))
        else:
            partial[name] = (len(ch), n)
    return full, partial


def sha256_text(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def canon(obj):
    """شكلٌ قانونيّ للمقارنة: رحلةُ JSON ذهابًا وإيابًا ثمّ ترتيبُ المفاتيح (ما يطبعه Actions نصًّا هو ما يُقارَن)."""
    return json.dumps(json.loads(json.dumps(obj, ensure_ascii=False, default=str)), ensure_ascii=False, sort_keys=True)


def load_fixture():
    raw = open(FIXTURE, encoding="utf-8").read()
    want = open(FIXTURE_SHA, encoding="utf-8").read().split()[0]
    got = sha256_text(raw)
    payload = json.loads(raw)
    return payload, RUN.unpack(payload["b64gz_bars"]), got, (got == want)


def _next_session(rows, asof):
    return next((r[0] for r in rows if str(r[0])[:10] > asof), "9999-12-31")


def golden_v31_vs_v4(golden, v31):
    """الحالاتُ الذهبيّة السبع بتواريخ V3.1 نفسِها (قراءةٌ عند جلسة V3.1 شاملةً) ⟵ V3.1 مقابل V4 مقابل كلمة فيصل · تحقّقٌ لا اكتشاف."""
    out = []
    for r in v31.get("rows") or []:
        sym = r["case"]
        rows = golden["daily"].get(sym) or []
        asof = r.get("asof")
        rec = {"case": sym, "faisal": r.get("faisal"), "asof_v31": asof, "v31_state": (r.get("tool_v31") or {}).get("state"),
               "v31_label": (r.get("tool_v31") or {}).get("label")}
        if not rows or not asof:
            rec.update(v4_state="UNKNOWN", v4_tech=None, v4_word=None, note="لا شموع أو لا تاريخ")
            out.append(rec)
            continue
        d = E.analyze_rows(rows, asof_date=_next_session(rows, asof), symbol=sym)
        word = TECH_TO_WORD.get(E.STATE_DECISION.get(d.get("tech_state")))
        rec.update(v4_levels=(d.get("support_resistance") or {}).get("levels") or {},
                   v4_asof=d.get("asof"), v4_close=(d.get("price_location") or {}).get("close"), v4_state=d.get("state"),
                   v4_tech=d.get("tech_state"), v4_word=word, v4_decisive=d.get("decisive_level"), v4_class=d.get("decisive_class"),
                   v4_missing=d.get("missing_information"), v4_rules=d.get("rule_ids"),
                   v31_match=(rec["v31_label"] == r.get("faisal")), v4_match=(word == r.get("faisal")))
        out.append(rec)
    ok = [x for x in out if x.get("v4_word") is not None]
    return {"rows": out, "v31_matched": sum(1 for x in out if x.get("v31_match")), "v4_matched": sum(1 for x in ok if x.get("v4_match")),
            "of": len(out), "dated": len(ok), "always_wait_baseline": sum(1 for x in ok if x.get("faisal") == "WAIT"),
            "note": "تحقّقٌ لا اكتشاف (§16) · كلمةُ V4 = القرارُ الفنيّ (TECH_READY ≙ READY) لأنّ الصلاحيّة مجهولة · "
                    "و«دائمًا WAIT» خطُّ أساسٍ على المؤرَّخة نفسِها (وصفيّ · بعد الرقم)"}


def veee(golden, bars):
    """§⑨: A8 (الأساسيّ) وA9 (V3.1) على شموع V3.1 المجمَّدة وعلى شموع fetch — واختلافُ المصدرين يُعلَن ولا يُختار."""
    res = {}
    for src, rows in (("v31_fixture", golden["daily"].get("VEEE") or []), ("v4_fetch", bars.get("VEEE") or [])):
        res[src] = {k: EV.veee_date(rows, EV.VEEE_ANCHORS[k]) for k in ("A8", "A9")}
        res[src]["bars"] = len(rows)
        res[src]["first"] = rows[0][0] if rows else None
        res[src]["last"] = rows[-1][0] if rows else None
    a = res["v31_fixture"]["A8"]
    b = res["v4_fetch"]["A8"]
    res["agree_sources_A8"] = (a["candidates"] == b["candidates"])
    res["verdict"] = a["verdict"] if res["agree_sources_A8"] else "UNRESOLVED"
    res["tag"] = "POST-HOC-INSPECTED"
    res["posthoc"] = veee_posthoc(golden["daily"].get("VEEE") or [])
    return res


VEEE_APP = {"close": 6.76, "change": 0.200, "src": "APP_20260918_59_VEEE «$6.760 +0.200 (+3.049%) At close» (شارتُ فيصل · VISIBLE_LINKED)"}


def veee_posthoc(rows, close_tol=0.005, chg_tol=0.005):
    """⚠️ POST-HOC (لم يُسجَّل في §⑨): الجلساتُ التي إغلاقُها 6.76 ±0.5% **وتغيّرُها عن السابقة +0.200 ±0.005** كما في شارت فيصل —
    وتشخيصُ سقوط A8: قمّةُ الستّين الفعليّة عند كلّ مرشَّح (8.80 قمّةٌ محلّيّةٌ لا قمّةُ النافذة)."""
    hits, diag = [], []
    for i in range(1, len(rows)):
        c, pc = float(rows[i][4]), float(rows[i - 1][4])
        if abs(c / VEEE_APP["close"] - 1) <= 0.01:
            seg = rows[max(0, i - 59):i + 1]
            diag.append({"date": str(rows[i][0])[:10], "close": c, "change": round(c - pc, 4),
                         "low60": min(float(r[3]) for r in seg), "high60": max(float(r[2]) for r in seg)})
        if abs(c / VEEE_APP["close"] - 1) <= close_tol and abs((c - pc) - VEEE_APP["change"]) <= chg_tol:
            hits.append(str(rows[i][0])[:10])
    return {"tag": "POST-HOC", "anchor": VEEE_APP, "candidates": hits,
            "verdict": "DATED_POSTHOC" if len(hits) == 1 else ("AMBIGUOUS_POSTHOC" if hits else "UNKNOWN_POSTHOC"),
            "a8_failure_diagnosis": diag}


OVERLAYS = os.path.join(HERE, "overlays")
OVERLAY_BARS = 60


def render_overlays(cases, bars, rows_by_case, golden, golden_rows, outdir=OVERLAYS):
    """§33 طبقةُ تحقّقٍ بصريّ (لا دليل): S1 السليمة ‏+ الذهبيّة المؤرَّخة بتواريخ V3.1 — شموعٌ حتى جلسة القراءة وحدَها (بلا نظرٍ للأمام) ·
    مستوياتُ فيصل النصّيّة «F:…» ومستوياتُ المحرّك بأسمائها · والعنوانُ كلمةُ فيصل وحالةُ المحرّك. ⟵ قائمةُ الملفّات."""
    import hs_forensic as FX                       # دالّةُ رسمٍ نقيّةٌ وحدَها (المحورُ مُغلَقٌ لأوضاعه لا لدوالّه — سابقةُ V3.1)
    os.makedirs(outdir, exist_ok=True)
    made = []
    byc = {c["case"]: c for c in cases}
    jobs = []
    for cs in cases:
        r = rows_by_case.get(cs["case"])
        if cs.get("set") == "S1" and r and r.get("status") == "OK":
            jobs.append((cs["case"], (cs.get("tickers") or [None])[0], r["asof"], bars, r, cs.get("levels_F") or [], cs.get("label4")))
    for g in golden_rows:
        if g.get("v4_asof"):
            jobs.append((f"GOLDEN_{g['case']}", g["case"], g["v4_asof"], {g["case"]: golden["daily"].get(g["case"]) or []},
                         {"levels": g.get("v4_levels") or {}, "state": g.get("v4_state"), "tech_state": g.get("v4_tech")}, [], g.get("faisal")))
    for name, tk, asof, src, r, lvF, lab in jobs:
        rr = [x for x in (src.get(tk) or []) if str(x[0])[:10] <= str(asof)[:10]][-OVERLAY_BARS:]
        if len(rr) < 10:
            continue
        close = float(rr[-1][4])
        lines = {}                                  # نطاقُ H-LEVEL نفسُه (0.60-1.40 × إغلاق القراءة) — ما قِيس هو ما يُرسم
        for k, v in sorted((r.get("levels") or {}).items()):
            if v and EV.in_band(float(v), close):
                lines["E:" + k] = (float(v), 0)
        for j, lv in enumerate(lvF):
            if lv.get("price") and EV.in_band(float(lv["price"]), close):
                lines[f"F:{lv.get('kind')}{'*' if lv.get('derived') else ''}#{j}"] = (float(lv["price"]), 0)
        title = f"{tk} daily to {asof} · Faisal {lab} · V4 {r.get('state')} ({r.get('tech_state')}) · E=engine F=Faisal text (*=derived)"
        pth = os.path.join(outdir, f"{name}.png")
        FX.render_bars([[x[1], x[2], x[3], x[4]] for x in rr], pth, lines=lines, title=title)
        made.append(os.path.relpath(pth, HERE))
    return made


def _in_group(r, g):
    return {"S1_discovery": r["set"] == "S1" and r["split"] == "discovery", "S1_holdout": r["set"] == "S1" and r["split"] == "holdout",
            "S1_all": r["set"] == "S1", "S2": r["set"] == "S2", "S3_golden": r["set"] == "S3", "S4_edu": r["set"] == "S4"}.get(g, False)


def main():
    cases = json.load(open(os.path.join(HERE, "results", "cases_v4.json"), encoding="utf-8"))["cases"]
    payload, bars, sha, sha_ok = load_fixture()
    res = EV.evaluate(cases, bars)
    act = json.load(open(ACTIONS_METRICS, encoding="utf-8"))
    same = canon(res["metrics"]) == canon(act)
    golden = json.load(open(GOLDEN, encoding="utf-8"))
    v31 = json.load(open(GOLDEN_V31, encoding="utf-8"))
    dx = EV.dxst_classify({"regular": golden["m30"].get("DXST") or [], "extended": golden["m30x"].get("DXST") or []})
    desc = {}
    for g in res["metrics"]:
        sel = [r for r in res["rows"] if r["status"] == "OK" and _in_group(r, g)]
        n = len(sel)
        desc[g] = {"n": n, "state_exact": sum(1 for r in sel if r["state"] == r["faisal"]),
                   "always_wait": sum(1 for r in sel if r["faisal"] == "WAIT"),
                   "faisal_ready": sum(1 for r in sel if r["faisal"] == "READY"),
                   "engine_ready": sum(1 for r in sel if r["state"] == "READY"),
                   "engine_unknown": sum(1 for r in sel if r["state"] == "UNKNOWN")}
    doc = {"generated_by": "faisal_method_v4/v4_offline.py", "engine": E.ENGINE_VERSION, "fixture_sha256": sha, "fixture_sha_ok": sha_ok,
           "h_state_descriptive": desc,
           "fixture_coverage": payload.get("coverage"), "tv_calls": payload.get("tv_calls"), "keep_from": payload.get("keep_from"),
           "reproduces_actions_metrics": same, "metrics": res["metrics"], "rows": res["rows"], "level_rows": res["level_rows"],
           "golden_v31_vs_v4": golden_v31_vs_v4(golden, v31), "dxst": dx, "veee": veee(golden, bars)}
    if os.environ.get("V4_OVERLAYS") == "1":
        doc["overlays"] = render_overlays(cases, bars, {r["case"]: r for r in res["rows"]}, golden, doc["golden_v31_vs_v4"]["rows"])
    elif os.path.exists(OUT):
        doc["overlays"] = (json.load(open(OUT, encoding="utf-8")).get("overlays") or [])
    json.dump(doc, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True, default=str)
    print(f"🧾 البصمة {sha[:16]} · مطابقةُ الملفّ {sha_ok} · مطابقةُ Actions {same}")
    for g, m in res["metrics"].items():
        print(f"📏 {g}: حالات {m['cases']} · سليمة {m['ok']} · H-LEVEL {m['h_level_verdict']} {m['h_level']} · "
              f"H-CLASS {m['h_class'].get('verdict')} {m['h_class'].get('rate')}")
    print(f"🧩 DXST ⟵ {dx['verdict']} · VEEE ⟵ {doc['veee']['verdict']} · الذهبيّة: V3.1 {doc['golden_v31_vs_v4']['v31_matched']} · "
          f"V4 {doc['golden_v31_vs_v4']['v4_matched']} من {doc['golden_v31_vs_v4']['of']}")
    return 0 if (sha_ok and same) else 4


if __name__ == "__main__":
    raise SystemExit(main())
