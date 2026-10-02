# -*- coding: utf-8 -*-
"""
🧭 FAISAL V4 — بانيّ حالات القرار (حتميّ · بلا بيانات سوق · بلا شبكة).

المدخل: `data/visual_pass_v4.jsonl` (المرورُ البصريّ على 609 وحدة · منقّحٌ من الأسماء الخاصّة) و`data/case_labels_v4.json`
(فئةُ الخطّة والمستوياتُ المكتوبة نصًّا لكلّ حالة — وُسمت قبل أيّ رقم سوق).
المخرج: `results/cases_v4.json` — العبارات ⟵ الحالات ⟵ المجموعات S1/S2/S3/S4 ⟵ تاريخُ القراءة (as-of) لكلّ حالة.

القواعد (مكتوبةٌ في `V4_prereg.md` §③ قبل أيّ رقم):
  • العبارةُ = سجلٌّ بقرارٍ غير NONE (أو حالةٌ داخل MULTI) · والكاتبُ يحدّد الطبقة (1 · 2 · 2b · X).
  • الحالة = الرمز ‏+ التاريخ (±جلسة) أو مفتاحُ `case` الصريح · ووسمُها من عبارات فيصل وحدَها (الطبقة X لا تصنع وسمًا —
    إصلاحُ عيبٍ في نسخة المسودّة: عبارةُ مساعدٍ READY جعلت FTFT «MIXED»).
  • الصريحُ يعلو الاصطلاحَ (TRIG-ABOVE · ZONE-BELOW · NOT-READY-BARE) ويعلو الميل · والمُستعاد (DECISION_RECALLED) لا يُعدّ قرارًا آنيًّا.
  • WATCH ⟵ WAIT في الوسم الرباعيّ.
  • تاريخُ القراءة = آخرُ جلسةٍ قبل تاريخ العبارة **حصرًا** (لا نظرَ للأمام مهما كان وقتُ النشر).
"""
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
VP = os.path.join(DATA, "visual_pass_v4.jsonl")
LABELS = os.path.join(DATA, "case_labels_v4.json")
OUT = os.path.join(HERE, "results", "cases_v4.json")

# الحالاتُ الذهبيّة: المسجَّلة في v31/golden_fixtures.json ‏+ ما سمّته المهمّة (SPRC · CUPR) — للتحقّق وحدَه لا للاكتشاف.
GOLDEN_REGISTERED = ["RAYA", "LABT", "ZNB", "RUBI", "AMIX", "HCWB", "DXST", "VEEE", "ATMV"]
GOLDEN_MISSION_NAMED = ["SPRC", "CUPR"]
GOLDEN = set(GOLDEN_REGISTERED) | set(GOLDEN_MISSION_NAMED)
HOLDOUT_FROM = "2026-08-01"          # الاكتشاف قبل هذا التاريخ · والاحتجاز منه فصاعدًا (§③)

TIER1 = {"VISIBLE", "VISIBLE_TAG", "VISIBLE_LINKED", "OWNER_ATTESTED", "VISIBLE_AVATAR", "VISIBLE_PROFILE",
         "VISIBLE_EMBEDDED", "VISIBLE_OCR"}
TIER1_FLAG = {"VISIBLE_AVATAR", "VISIBLE_PROFILE", "VISIBLE_EMBEDDED", "VISIBLE_OCR"}
TIER2 = {"INFERRED_PHONE_OWNER", "INFERRED_DEVICE_LINKED", "INFERRED_CROPPED", "INFERRED_CHART",
         "CATALOG_ATTRIBUTION", "CONTEXT_LINKED", "CHANNEL_REPOST_OF_VISIBLE"}
TIER2B = {"EDU_CHANNEL_UNMATCHED", "EDU_ATTRIBUTED_FAISAL", "VISIBLE_CHANNEL", "CHANNEL_NAMED_IN_SET"}
CONV = re.compile(r"اصطلاح|TRIG-ABOVE|ZONE-BELOW|NOT-READY-BARE")
L4 = {"READY": "READY", "WAIT": "WAIT", "WATCH": "WAIT", "REJECT": "REJECT"}


def tier(author, basis):
    """طبقةُ الدليل: 1 (فيصل ظاهر) · 2 (فيصل مستنتَج) · 2b (القناة التعليميّة) · X (طرفٌ ثالث/تطبيق/مساعد)."""
    if author not in ("F", "EDU", "U"):
        return "X"
    if author == "EDU" or basis in TIER2B:
        return "2b"
    if basis in TIER1:
        return "1"
    if basis in TIER2:
        return "2"
    return "X"


def date_prec(d):
    if not d:
        return "unknown"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
        return "day"
    if re.fullmatch(r"\d{4}-\d{2}-[0-3]x", d):
        return "decade"
    if re.fullmatch(r"\d{4}-\d{2}", d):
        return "month"
    return "range"


def load_records(path=VP):
    return [json.loads(x) for x in open(path, encoding="utf-8") if x.strip()]


def statements(recs):
    out = []
    for r in recs:
        base = dict(rid=r["id"], a=r["a"], ab=r.get("ab"), tier=tier(r["a"], r.get("ab")), d=r.get("d"), tickers=r.get("t") or [],
                    case=r.get("case"), chain=r.get("chain"), golden_flag=bool(r.get("golden_ticker")),
                    hindsight=bool(r.get("hindsight")), res=r.get("res"), why=r.get("why") or [],
                    label_note=r.get("label_note") or "", px=r.get("px"))
        if r["dec"] == "MULTI":
            for i, c in enumerate(r.get("cases") or []):
                if c.get("dec") in (None, "NONE"):
                    continue
                who = c.get("who", r["a"])
                out.append(dict(base, sid=f'{r["id"]}#{i}', dec=c["dec"], lean=c.get("lean"),
                                tickers=[c["t"]] if c.get("t") else base["tickers"],
                                recalled=(c.get("res") == "DECISION_RECALLED" or bool(c.get("recalled"))),
                                a=who, tier=tier(who, r.get("ab")), convention=False,
                                case=c.get("case", r.get("case"))))
            continue
        if r["dec"] == "NONE":
            continue
        out.append(dict(base, sid=r["id"], dec=r["dec"], lean=r.get("lean"), recalled=(r.get("res") == "DECISION_RECALLED"),
                        convention=bool(CONV.search(base["label_note"]))))
    return out


def case_key(s):
    tks = [t for t in s["tickers"] if t and t != "UNK"]
    if s.get("case"):
        b = s["case"]
        return b if len(tks) <= 1 or tks[0] in b else f"{b}|{tks[0]}"
    if not tks:
        return f'UNK_{s["rid"]}'
    return f'{tks[0]}_{s["d"]}'


def _first_day(dates):
    days = sorted(d for d in dates if date_prec(d) == "day")
    return days[0] if days else None


def statement_date(dates):
    """تاريخُ العبارة للقراءة: أقدمُ تاريخٍ بدقّة اليوم · وإلّا بدايةُ العقد/الشهر · وإلّا «≤تاريخ» · وإلّا None."""
    d = _first_day(dates)
    if d:
        return d, "day"
    for x in sorted(dates):
        m = re.fullmatch(r"(\d{4}-\d{2})-([0-3])x", x)
        if m:
            day = max(1, int(m.group(2)) * 10)
            return f"{m.group(1)}-{day:02d}", "decade"
    for x in sorted(dates):
        if re.fullmatch(r"\d{4}-\d{2}", x):
            return f"{x}-01", "month"
    for x in sorted(dates):
        m = re.fullmatch(r"≤(\d{4}-\d{2}-\d{2})", x)
        if m:
            return m.group(1), "range"
    return None, "unknown"


def build_cases(recs, labels=None):
    labels = labels or {}
    st = statements(recs)
    groups = collections.OrderedDict()
    for s in st:
        groups.setdefault(case_key(s), []).append(s)
    out = []
    for k, ss in groups.items():
        usable = [s for s in ss if not s["hindsight"] and s["res"] != "DECISION_DUP"]
        faisal = [s for s in usable if s["tier"] != "X"]            # الطبقة X لا تصنع وسمًا (تبقى للتناقض)
        expl = [s for s in faisal if s["dec"] in L4 and not s["convention"] and not s["recalled"]]
        conv = [s for s in faisal if s["dec"] in L4 and s["convention"]]
        rec = [s for s in faisal if s["recalled"]]
        lean = [s for s in faisal if s["dec"] == "UNKNOWN" and s.get("lean")]
        labs = sorted({s["dec"] for s in expl})
        hold = "READY" in labs and bool(conv) and all(c["dec"] == "WAIT" for c in conv)
        if len(labs) == 1:
            label, basis = labs[0], "explicit"
        elif labs:
            label, basis = "MIXED:" + "/".join(labs), "explicit_conflict"
        elif conv:
            lc = sorted({c["dec"] for c in conv})
            label, basis = (lc[0], "convention") if len(lc) == 1 else ("MIXED:" + "/".join(lc), "convention_conflict")
        elif lean:
            ll = sorted({x["lean"] for x in lean})
            label, basis = ("UNKNOWN~" + ll[0], "lean") if len(ll) == 1 else ("UNKNOWN", "lean_conflict")
        elif rec:
            label, basis = "READY", "recalled_only"
        else:
            label, basis = "UNKNOWN", "none"
        if label.startswith("MIXED:"):
            parts = {L4.get(x, x) for x in label[6:].split("/")}
            label4 = parts.pop() if len(parts) == 1 else "MIXED"
        elif label.startswith("UNKNOWN"):
            label4 = "UNKNOWN"
        else:
            label4 = L4.get(label, label)
        tiers = sorted({s["tier"] for s in faisal})
        best = "1" if "1" in tiers else ("2" if "2" in tiers else ("2b" if "2b" in tiers else "X"))
        tickers = sorted({t for s in ss for t in s["tickers"] if t and t != "UNK"})
        dates = sorted({s["d"] for s in ss if s["d"]})
        sd, sprec = statement_date(dates)
        lab = labels.get(k) or {}
        golden = any(t in GOLDEN for t in tickers)
        if not tickers:
            cset, why = "EXCL", "no_ticker"
        elif best == "X":
            cset, why = "EXCL", "third_party_only"
        elif not usable:
            cset, why = "EXCL", "hindsight_or_dup_only"
        elif golden:
            cset, why = "S3", "golden_ticker"
        elif best == "2b":
            cset, why = "S4", "edu_channel"
        elif sd is None:
            cset, why = "EXCL", "no_date"
        elif (best == "1" and basis in ("explicit", "explicit_conflict") and label4 in ("READY", "WAIT", "REJECT")
              and sprec == "day" and not lab.get("time_uncertain")):
            cset, why = "S1", "primary"
        else:
            cset, why = "S2", "secondary"
        split = None
        if cset == "S1":
            split = "holdout" if sd >= HOLDOUT_FROM else "discovery"
        out.append(dict(case=k, tickers=tickers, label4=label4, label=label, basis=basis, hold_status_rule=hold,
                        best_tier=best, tiers=tiers, dates=dates, statement_date=sd, date_precision=sprec,
                        set=cset, set_reason=why, split=split, golden=golden, recalled=bool(rec),
                        n_stmts=len(ss), sids=[s["sid"] for s in ss],
                        third_party_sids=[s["sid"] for s in usable if s["tier"] == "X"],
                        chain=sorted({s["chain"] for s in ss if s.get("chain")}),
                        plan_F=lab.get("plan"), levels_F=lab.get("levels") or [], targets_F=lab.get("targets") or [],
                        px_F=lab.get("px"), label_notes=lab.get("note")))
    return st, out


def main(argv=None):
    recs = load_records()
    labels = json.load(open(LABELS, encoding="utf-8"))["cases"] if os.path.exists(LABELS) else {}
    st, cases = build_cases(recs, labels)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    summary = {"statements": len(st), "cases": len(cases),
               "by_set": dict(sorted(collections.Counter(c["set"] for c in cases).items())),
               "S1_by_label": dict(sorted(collections.Counter(c["label4"] for c in cases if c["set"] == "S1").items())),
               "S1_by_split": dict(sorted(collections.Counter(c["split"] for c in cases if c["set"] == "S1").items())),
               "unlabelled_in_sets": sorted(c["case"] for c in cases if c["set"] in ("S1", "S2", "S3", "S4")
                                            and c["plan_F"] is None)}
    doc = {"generated_by": "faisal_method_v4/v4_cases.py", "inputs": [os.path.relpath(VP, os.path.dirname(HERE)),
                                                                       os.path.relpath(LABELS, os.path.dirname(HERE))],
           "summary": summary, "statements": st, "cases": cases}
    json.dump(doc, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
