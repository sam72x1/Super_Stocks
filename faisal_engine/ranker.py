# -*- coding: utf-8 -*-
"""🧭🏁 FAISAL RESEARCH RANKER — يرتّب مجتمعَ المحرّك (P(T)) ولا يغيّر مرحلةً واحدة (RANKING_PROTOCOL.md §④).

ثلاثةُ متغيّراتٍ مسجَّلةٍ مسبقًا، كلُّها مفتاحٌ معجميٌّ حتميّ بلا أوزانٍ مُعايَرة:
  A — المرحلةُ وحدَها + كسرُ تعادلٍ لا يعرف التسميات (sha256).
  B — المرحلة + قوّةُ القاعدة المحدِّدة للحالة من سجلّ القواعد + المناقَض + الصلاحيّة (الطرحُ المتحقَّق غيابُه) + إطارُ الهُويّة.
  C — المرحلة + الصنفُ الزمنيّ (تقدّم · جديد · ثابتٌ قديم · تراجع) + أيّامُ المرحلة + مفاتيحُ B.
المدخلُ صفوفُ `data/rank/rows.csv.gz` (مخرَجُ `rank_universe.py`) — والمرحلةُ تُقرأ من المحرّك كما هي. قراءةٌ فقط · لا إنتاج."""
import csv
import gzip
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RANKER_VERSION = "FE-RANK 1.0 (2026-10-09)"
VARIANTS = ("A", "B", "C")
STAGE_PRIORITY = {"TRIGGER": 0, "READY": 1, "WATCH": 2, "FOCUS": 3, "HOLD": 4}
POOL = tuple(STAGE_PRIORITY)
TIE_TAG = "FE-RANK-1"
FRESH_SESSIONS = 5               # §④: «دخل المرحلةَ خلال آخر 5 جلسات» = طازج (= نافذةُ الالتقاط المبكر · HOLD_MIN 5)
AGE_CAP = 20                     # §④: أيّامُ المرحلة تُعَدّ حتى 20 جلسة
TEMPORAL = {"PROGRESSED": 0, "NEW": 1, "PERSISTENT": 2, "REGRESSED": 3}
STRENGTH = {"CONFIRMED": 3, "SUPPORTED": 2, "PROBABLE": 1, "CONTRADICTED": 0}
ROWS = os.path.join(HERE, "data", "rank", "rows.csv.gz")

# سجلُّ الميزات (§6 من المهمّة): ما يدخل المفاتيحَ فعلًا — وما سواه لا يمسّ الترتيب.
FEATURES = [
    {"name": "stage_priority", "variants": "A B C", "definition": "TRIGGER 0 · READY 1 · WATCH 2 · FOCUS 3 · HOLD 4 (أصغرُ أولى)",
     "source": "engine.evaluate → rec['stage'] (rows.eng_stage)", "evidence_class": "INFERRED (FE-STAGE-01 PROBABLE: خريطةُ V4 ⟵ مراحل فيصل)",
     "availability": "شموعٌ < T وسياقٌ ≤ T", "direction": "المرحلةُ الأقربُ إلى الفعل أوّلًا · HOLD آخرًا (مانعٌ مؤرَّخ)",
     "reason": "سلسلةُ NEXT_CONDITION في engine.py: FOCUS ⟵ WATCH ⟵ READY ⟵ TRIGGER", "failure_modes": "اهتمامُ فيصل الموثَّق أغلبُه WATCH/FOCUS — قد يُعاكس الالتقاط",
     "faisal_support": "المراحلُ مستنبطةٌ من آلة حالة فيصل (مرحلة 3/4) · الترتيبُ بينها ليس منصوصًا"},
    {"name": "tie_break", "variants": "A B C", "definition": "sha256('FE-RANK-1|T|symbol') تصاعديًّا",
     "source": "ranker.tiebreak", "evidence_class": "N/A (حياديّ)", "availability": "دائمًا", "direction": "لا اتّجاه — كسرُ تعادلٍ ثابت",
     "reason": "حتميٌّ ولا يعرف التسميات ولا الأسعار", "failure_modes": "اعتباطيٌّ بالتصميم داخل التعادل", "faisal_support": "لا"},
    {"name": "state_rule_strength", "variants": "B C", "definition": "حالةُ القاعدة V4.STATE_RULE[tech_state] في FAISAL_RULE_LEDGER: CONFIRMED 3 · SUPPORTED 2 · PROBABLE 1",
     "source": "rows.state_rule + FAISAL_RULE_LEDGER.json", "evidence_class": "تصنيفُ السجلّ نفسُه (DIRECTLY_OBSERVED/REPEATEDLY_SUPPORTED/INFERRED)",
     "availability": "ثابتٌ (سجلٌّ مجمَّد)", "direction": "الأقوى دليلًا أوّلًا", "reason": "§7 B: لا يُعامَل المنصوصُ والمستنبَط سواءً",
     "failure_modes": "يقيس قوّةَ دليل القاعدة لا قوّةَ الإعداد · مرتبطٌ بالحالة الفنيّة", "faisal_support": "التصنيفُ نفسُه من أدلّة فيصل"},
    {"name": "contradicted", "variants": "B C", "definition": "أيُّ قاعدةٍ مطبَّقة حالتُها CONTRADICTED ⟵ بعد", "source": "rows.rules_passed|v4_rule_ids + ledger",
     "evidence_class": "CONTRADICTED", "availability": "ثابت", "direction": "المناقَضُ آخرًا", "reason": "§6 B: الدليلُ المعاكس",
     "failure_modes": "نادرٌ (H-D2 وحدَها)", "faisal_support": "مناقَضةٌ بسلوكه الموثَّق"},
    {"name": "validity_offering", "variants": "B C", "definition": "الطرحُ متحقَّقٌ غيابُه (False) قبل المجهول (UNKNOWN) · المعلَّقُ (True) ⟵ HOLD بالمرحلة",
     "source": "rows.offering (SEC 424B1/4/5 ≤ 90 يومًا ≤ T)", "evidence_class": "REPEATEDLY_SUPPORTED (R4-VAL-OFF-01)",
     "availability": "إيداعاتٌ مؤرَّخة ≤ T", "direction": "المتحقَّقُ أوّلًا — المجهولُ ليس «لا»", "reason": "§6 B: الموانعُ الصريحة · UNKNOWN ≠ false",
     "failure_modes": "غيابُ CIK ⟵ مجهولٌ لا سلبيّ · نماذجُ أخرى للطرح خارج التغطية", "faisal_support": "R4-VAL-OFF-01"},
    {"name": "identity_frame", "variants": "B C", "definition": "FULL (FE-SCREEN-01 SUPPORTED) قبل POST_SPLIT (FE-FRAME-01 PROBABLE)",
     "source": "rows.frame", "evidence_class": "REPEATEDLY_SUPPORTED vs INFERRED", "availability": "تقسيماتٌ ≤ T",
     "direction": "الإطارُ الأقوى دليلًا أوّلًا", "reason": "§7 B: درجةُ الدليل", "failure_modes": "أسهمُ فيصل كثيرًا ما تكون بعد تقسيم — قد يؤخّرها",
     "faisal_support": "إطارُ ما بعد التقسيم مستنبَط (المرحلة 2)"},
    {"name": "temporal_class", "variants": "C", "definition": "PROGRESSED 0 · NEW 1 · PERSISTENT 2 (≥5 جلسات في المرحلة) · REGRESSED 3",
     "source": "مراحلُ المحرّك في الجلسات السابقة (rows.eng_stage)", "evidence_class": "فرضيّةٌ مسجَّلة H-C (اتّجاهُها من نصّ المهمّة §7 وسلسلة المراحل)",
     "availability": "جلساتٌ < T فقط", "direction": "الطازجُ قبل القديم داخل المرحلة · التراجعُ آخرًا",
     "reason": "§7 C: لا يعلو الثابتُ القديم على الإعداد الجديد", "failure_modes": "حدودُ التاريخ المحسوب (20 جلسة) · الدخولُ/الخروجُ المتكرّر عند الحدّ",
     "faisal_support": "استنتاج: المرحلتان 3/4 (انتباهُه عند اللمسة الأولى) من المدوّنة نفسِها — تلوّثٌ مُعلَن"},
    {"name": "age_in_stage", "variants": "C", "definition": "جلساتٌ متتاليةٌ سابقة في المرحلة نفسِها (سقف 20)", "source": "rows.eng_stage",
     "evidence_class": "فرضيّةٌ مسجَّلة H-C", "availability": "جلساتٌ < T", "direction": "الأحدثُ أوّلًا", "reason": "§7 C",
     "failure_modes": "مرتبطٌ بالصنف الزمنيّ (لا يُعَدّ دليلًا مستقلًّا — كسرُ تعادلٍ داخله)", "faisal_support": "كما فوق"},
]


def tiebreak(date, symbol):
    return hashlib.sha256(f"{TIE_TAG}|{date}|{symbol}".encode()).hexdigest()


_LEDGER = None


def ledger():
    global _LEDGER
    if _LEDGER is None:
        L = json.load(open(os.path.join(HERE, "FAISAL_RULE_LEDGER.json"), encoding="utf-8"))
        _LEDGER = {r["rule_id"]: r["status"] for r in L["rules"]}
    return _LEDGER


def _rules(row):
    out = []
    for k in ("rules_passed", "v4_rule_ids"):
        for x in (row.get(k) or "").split("|"):
            if x:
                out.append(x.split(":")[0])
    return out


def evidence(row):
    led = ledger()
    st = led.get(row.get("state_rule") or "", "")
    return {"state_rule": row.get("state_rule") or "", "status": st or "UNKNOWN", "strength": STRENGTH.get(st, 0),
            "contradicted": int(any(led.get(r) == "CONTRADICTED" for r in _rules(row))),
            "validity": (0 if str(row.get("offering")) == "False" else 1),
            "frame": (1 if row.get("frame") == "POST_SPLIT" else 0)}


def stage_history(rows):
    """{date: {symbol: stage}} لأعضاء المجتمع وحدَهم."""
    h = {}
    for r in rows:
        if r.get("eng_stage") in POOL:
            h.setdefault(r["date"], {})[r["symbol"]] = r["eng_stage"]
    return h


def temporal(symbol, date, stage, hist, sessions):
    """الصنفُ الزمنيّ من جلساتٍ < date فقط (§④ C)."""
    if date not in sessions:
        return {"cls": "NEW", "age": 0, "prev": None, "truncated": True}
    i = sessions.index(date)
    age = 0
    while age < AGE_CAP and i - age - 1 >= 0 and hist.get(sessions[i - age - 1], {}).get(symbol) == stage:
        age += 1
    j = i - age - 1
    prev = hist.get(sessions[j], {}).get(symbol) if j >= 0 else None
    truncated = j < 0
    if age >= FRESH_SESSIONS:
        cls = "PERSISTENT"
    elif prev is None:
        cls = "NEW"
    elif STAGE_PRIORITY[prev] > STAGE_PRIORITY[stage]:
        cls = "PROGRESSED"
    else:
        cls = "REGRESSED"
    return {"cls": cls, "age": age, "prev": prev, "truncated": truncated}


def key(variant, row, ev=None, tm=None):
    pri = STAGE_PRIORITY[row["eng_stage"]]
    tb = tiebreak(row["date"], row["symbol"])
    if variant == "A":
        return (pri, tb)
    ev = ev or evidence(row)
    eb = (-ev["strength"], ev["contradicted"], ev["validity"], ev["frame"])
    if variant == "B":
        return (pri,) + eb + (tb,)
    if variant == "C":
        return (pri, TEMPORAL[tm["cls"]], tm["age"]) + eb + (tb,)
    raise ValueError(variant)


def explain(variant, rank, row, ev, tm):
    off = {"False": "verified absent", "True": "PENDING (HOLD)"}.get(str(row.get("offering")), "UNKNOWN")
    parts = [f"#{rank} {row['symbol']} @ {row['date']} [{variant}]",
             f"stage {row['eng_stage']} (priority {STAGE_PRIORITY[row['eng_stage']]}) · tech {row.get('tech_state') or '—'}"]
    if variant in ("B", "C"):
        parts.append(f"stage rule {ev['state_rule'] or '—'} {ev['status']}" + (" · CONTRADICTED rule present" if ev["contradicted"] else ""))
        parts.append(f"offering {off} · frame {row.get('frame') or '—'}")
    if variant == "C":
        parts.append(f"temporal {tm['cls']} (age {tm['age']}, prev {tm['prev'] or 'out-of-pool'}{', history truncated' if tm['truncated'] else ''})")
    if row.get("missing_rules"):
        parts.append("UNKNOWN: " + row["missing_rules"].replace("|", ", "))
    if row.get("blocks"):
        parts.append("validity block: " + row["blocks"])
    parts.append(f"tie-break {tiebreak(row['date'], row['symbol'])[:8]}")
    return " · ".join(parts)


def rank_session(date, rows_t, variant, hist=None, sessions=None):
    """صفوفُ جلسةٍ واحدة ⟵ قائمةٌ مرتّبة (كلُّ أعضاء المجتمع) بمفتاحها وتفسيرها. الأعضاءُ = eng_stage ∈ POOL."""
    pool = [r for r in rows_t if r.get("eng_stage") in POOL and r.get("date") == date]
    items = []
    for r in pool:
        ev = evidence(r)
        tm = temporal(r["symbol"], date, r["eng_stage"], hist or {}, sessions or []) if variant == "C" else None
        items.append((key(variant, r, ev, tm), r, ev, tm))
    items.sort(key=lambda x: x[0])
    out = []
    for k, (kk, r, ev, tm) in enumerate(items, 1):
        out.append({"rank": k, "symbol": r["symbol"], "date": date, "stage": r["eng_stage"], "tech_state": r.get("tech_state"),
                    "frame": r.get("frame"), "offering": r.get("offering"), "state_rule": ev["state_rule"], "rule_status": ev["status"],
                    "temporal": (tm or {}).get("cls", ""), "age": (tm or {}).get("age", ""), "key": json.dumps(list(kk)),
                    "explain": explain(variant, k, r, ev, tm)})
    return out


def load_rows(path=ROWS):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sessions_of(rows):
    return sorted({r["date"] for r in rows})


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="FAISAL RESEARCH RANKER — قائمةُ جلسةٍ مرتّبة أو رتبةُ رمز")
    ap.add_argument("--date", required=True)
    ap.add_argument("--variant", default="C", choices=VARIANTS)
    ap.add_argument("--k", type=int, default=108)
    ap.add_argument("--symbol")
    ap.add_argument("--rows", default=ROWS)
    a = ap.parse_args()
    rows = load_rows(a.rows)
    ss = sessions_of(rows)
    hist = stage_history(rows) if a.variant == "C" else None
    rk = rank_session(a.date, [r for r in rows if r["date"] == a.date], a.variant, hist, ss)
    if a.symbol:
        hit = [x for x in rk if x["symbol"] == a.symbol.upper()]
        row = next((r for r in rows if r["date"] == a.date and r["symbol"] == a.symbol.upper()), None)
        print(json.dumps(hit[0] if hit else {"symbol": a.symbol.upper(), "date": a.date, "rank": None, "in_pool": False,
                                             "eng_stage": (row or {}).get("eng_stage"), "first_failed": (row or {}).get("eng_first_failed"),
                                             "in_universe": bool(row)}, ensure_ascii=False, indent=1))
    else:
        print(f"{a.date} · variant {a.variant} · pool {len(rk)} · shortlist {min(a.k, len(rk))}", file=sys.stderr)
        for x in rk[:a.k]:
            print(x["explain"])
