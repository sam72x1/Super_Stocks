# -*- coding: utf-8 -*-
"""
🚧 FAISAL V4.1 — الاكتشاف · التحقّق · الاحتجاز (§4-6 · العقد `V41_prereg.md` §⑤): أعلامُ تلوّثٍ لكلّ حالة ⟵ بيانُ احتجازٍ **مختوم**
⟵ ثمّ وحدَها دالّةُ «الكشف» تضمّ كلماتِ فيصل وتحمل بصمةَ البيان الذي استعملته.

⚖️ **أعمى عن كلمة القرار بالبناء:** البنّاءُ يرى من الحالة `BLIND_FIELDS` وحدَها (`blind_view`) — لا `label` ولا `label4` ولا `plan_F` …
(قفل FV42 بالـAST على `blind_view` و`flags_for` و`build_manifest`). والنسخُ/الاشتقاق (عنقودُ `image_corpus.json`) يُحسب وحدةً واحدة (FV43).
🔴 **قاعدةُ العقد:** كلُّ وحدةٍ قُرئت في مرور V4 البصريّ **مكشوفة** (`EXPOSED`) ⟵ أثرُها غيرُ مؤكَّد ⟵ ملوَّثة · فالاحتجازُ التاريخيُّ النظيف 0
بالبناء — ولا يُصنَع احتجازٌ بإرخاء العَلَم. والطبقتان الوصفيّتان T1 (`CITED`) وT2 (`EXPOSED_UNCITED`) ليستا احتجازًا.
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
V4 = os.path.join(ROOT, "faisal_method_v4")
for _p in (V4, os.path.join(ROOT, "faisal_method_v3"), HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import v4_cases as VC        # noqa: E402 — مجمَّد
import provenance as PV      # noqa: E402

CASES = os.path.join(V4, "results", "cases_v4.json")
OUT = os.path.join(HERE, "docs", "V4_HOLDOUT_MANIFEST.json")
CONTRACT = "V41_prereg §⑤"
BLIND_FIELDS = ("case", "sids", "third_party_sids", "tickers", "dates", "statement_date", "date_precision", "set", "split",
                "golden", "tiers", "best_tier")
FORBIDDEN = ("label", "label4", "plan_F", "levels_F", "targets_F", "label_notes", "basis", "dec", "lean", "hold_status_rule")
FLAG_ORDER = ("CITED", "DISCOVERY", "GOLDEN", "EDU", "THIRD_PARTY", "EXCLUDED", "SHARED_UNIT", "EXPOSED")
PATTERNS = (("INV_HS", r"(?:رأس|راس)\s*و\s*كتف\w*\s*مقلوب|inverse\s*h&s|مقلوب"), ("HS", r"(?:رأس|راس)\s*و\s*كتف|h&s|head"),
            ("W", r"\bW\b|دبل\s*بوتوم|قاع\s*مزدوج|double\s*bottom"), ("M", r"\bM\b|قم\w*\s*مزدوج|double\s*top"),
            ("BREAKOUT", r"اختراق|تحرر|تحرّر|breakout"), ("RETEST", r"اختبار|يختبر|retest"),
            ("STRUCTURE", r"موج|دور[ةه]|ABC|اليوت|elliott"), ("SUPPORT_SETUP", r"دعم|قاع|support"))


def canon(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)


def sha(obj):
    return hashlib.sha256(canon(obj).encode("utf-8")).hexdigest()


def blind_view(case):
    """ما يراه البنّاء من الحالة — `BLIND_FIELDS` وحدَها."""
    return {k: case.get(k) for k in BLIND_FIELDS}


def base_id(s):
    """«TG_2207#1» = العبارةُ 1 داخل الصورة TG_2207 ⟵ الوحدةُ وحدةُ الصورة (17 معرّفًا بلاحقةٍ في cases_v4)."""
    return str(s).split("#", 1)[0]


def unit_set(bc, unit_of):
    return {unit_of.get(base_id(s), base_id(s)) for s in (bc.get("sids") or []) + (bc.get("third_party_sids") or [])}


def flags_for(bc, cited, unit_of, exposed, golden_tickers):
    """أعلامُ التلوّث لحالةٍ عمياء (بلا SHARED_UNIT — يُضاف عبر الحالات)."""
    units = unit_set(bc, unit_of)
    f = []
    if units & cited:
        f.append("CITED")
    if bc.get("split") == "discovery":
        f.append("DISCOVERY")
    if bc.get("set") == "S3" or bc.get("golden") or (set(bc.get("tickers") or []) & golden_tickers):
        f.append("GOLDEN")
    if bc.get("set") == "S4" or bc.get("best_tier") == "2b":
        f.append("EDU")
    if bc.get("best_tier") == "X":
        f.append("THIRD_PARTY")
    if bc.get("set") == "EXCL":
        f.append("EXCLUDED")
    if units & exposed:
        f.append("EXPOSED")
    return f


def pattern_of(units, recs):
    """نموذجُ فيصل المسمّى من عبارات `PATTERN` وحدَها (لا عبارةَ قرار) — للتغطية (§⑮)."""
    txt = " ".join(x.get("txt", "") for u in sorted(units) for x in (recs.get(u, {}).get("rules") or []) if x.get("eff") == "PATTERN")
    for name, rx in PATTERNS:
        if re.search(rx, txt, re.I):
            return name
    return "NONE"


def timeframes_of(units, recs):
    return sorted({t for u in units for t in (recs.get(u, {}).get("tf") or [])})


def build_manifest(blind_cases, cited, unit_of, recs, exposed, golden_tickers, inputs=None):
    rows = []
    for bc in blind_cases:
        units = unit_set(bc, unit_of)
        rows.append({"CASE_ID": bc["case"], "IMAGE_ID": sorted(bc.get("sids") or []), "UNITS": sorted(units),
                     "TICKER": bc.get("tickers") or [], "TIMEFRAME": timeframes_of(units, recs), "PATTERN": pattern_of(units, recs),
                     "SOURCE": {"best_tier": bc.get("best_tier"), "tiers": bc.get("tiers") or [], "set_v4": bc.get("set"),
                                "split_v4": bc.get("split")},
                     "PROVENANCE": {"statement_date": bc.get("statement_date"), "date_precision": bc.get("date_precision"),
                                    "origin": "V4 visual pass (609 units read before the rules were written)"},
                     "DISCOVERY_CONTAMINATION": flags_for(bc, cited, unit_of, exposed, golden_tickers)})
    owners = {}
    for r in rows:
        for u in r["UNITS"]:
            owners.setdefault(u, []).append(r)
    for r in rows:
        mates = {m["CASE_ID"] for u in r["UNITS"] for m in owners[u] if m["CASE_ID"] != r["CASE_ID"]
                 and set(m["DISCOVERY_CONTAMINATION"]) & {"CITED", "DISCOVERY", "GOLDEN"}}
        if mates and "SHARED_UNIT" not in r["DISCOVERY_CONTAMINATION"]:
            r["DISCOVERY_CONTAMINATION"].append("SHARED_UNIT")
            r["SHARED_WITH"] = sorted(mates)
        r["DISCOVERY_CONTAMINATION"] = [f for f in FLAG_ORDER if f in r["DISCOVERY_CONTAMINATION"]]
        r["HOLDOUT_ELIGIBLE"] = not r["DISCOVERY_CONTAMINATION"]
        fl = set(r["DISCOVERY_CONTAMINATION"])
        r["TIER"] = ("CLEAN" if not fl else "T1_CITED" if "CITED" in fl
                     else "T2_EXPOSED_UNCITED" if fl == {"EXPOSED"} else "OTHER_CONTAMINATED")
        r["REASON"] = ("نظيفة" if not fl else " · ".join(f for f in r["DISCOVERY_CONTAMINATION"]))
    summary = {"cases": len(rows), "eligible": sum(r["HOLDOUT_ELIGIBLE"] for r in rows),
               "by_flag": {f: sum(f in r["DISCOVERY_CONTAMINATION"] for r in rows) for f in FLAG_ORDER},
               "by_tier": {t: sum(r["TIER"] == t for r in rows) for t in ("CLEAN", "T1_CITED", "T2_EXPOSED_UNCITED", "OTHER_CONTAMINATED")},
               "v4_holdout_cited": sorted(r["CASE_ID"] for r in rows if r["SOURCE"]["split_v4"] == "holdout" and "CITED" in r["DISCOVERY_CONTAMINATION"]),
               "v4_holdout_total": sum(r["SOURCE"]["split_v4"] == "holdout" for r in rows)}
    man = {"generated_by": "faisal_method_v41/holdout.py", "contract": CONTRACT, "blind_fields": list(BLIND_FIELDS),
           "inputs": inputs or {}, "rows": rows, "summary": summary}
    man["seal"] = {"sha256": sha(man), "note": "بصمةُ البيان قبل الكشف — الكشفُ يتحقّق منها ويحملها"}
    return man


def seal_ok(man):
    body = {k: v for k, v in man.items() if k != "seal"}
    return (man.get("seal") or {}).get("sha256") == sha(body)


def _file_sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def build():
    cases = json.load(open(CASES, encoding="utf-8"))["cases"]
    blind = [blind_view(c) for c in cases]
    unit_of, recs = PV.corpus_units()
    cited = PV.cited_units()
    exposed = set(recs)                       # كلُّ وحدةٍ في المرور البصريّ (609)
    golden = set(VC.GOLDEN)
    inputs = {"cases_v4_sha256": _file_sha(CASES), "corpus_sha256": _file_sha(PV.CORPUS),
              "visual_pass_sha256": _file_sha(VC.VP), "cited_units": len(cited), "exposed_units": len(exposed)}
    return build_manifest(blind, cited, unit_of, recs, exposed, golden, inputs)


class SealError(Exception):
    pass


def reveal(man, cases=None):
    """الكشفُ بعد الختم: كلماتُ فيصل تُضمّ إلى الصفوف · ويُرفض بيانٌ تغيّر بعد ختمه."""
    if not seal_ok(man):
        raise SealError("بيانُ الاحتجاز تغيّر بعد ختمه")
    cases = cases if cases is not None else json.load(open(CASES, encoding="utf-8"))["cases"]
    by = {c["case"]: c for c in cases}
    out = []
    for r in man["rows"]:
        c = by.get(r["CASE_ID"], {})
        out.append(dict(r, FAISAL=c.get("label4"), FAISAL_LABEL=c.get("label"), PLAN_F=c.get("plan_F"),
                        LEVELS_F=c.get("levels_F") or [], REVEALED_WITH=man["seal"]["sha256"]))
    return out


def write(man=None):
    man = man or build()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(man, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    return man


def load(path=OUT):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    m = write()
    print(json.dumps(m["summary"], ensure_ascii=False))
