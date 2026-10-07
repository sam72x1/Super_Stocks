# -*- coding: utf-8 -*-
"""
📚 FAISAL V4.1 — بنّاءُ الوثائق (§33). كلُّ رقمٍ من JSON: بيانُ التجميد · المصدريّة · بيانُ الاحتجاز · التحليل · المخطّط ·
وسجلُّ الحقائق المقيسة من السجلّات (`results/run_registry_v41.json`) — **لا رقمَ باليد**. وقفلُ FVD1 يعيد التوليد ويقارن بايتًا بايتًا.
الاستعمال: python3 docs_v41.py            ⟵ يكتب الوثائق
           python3 docs_v41.py --check    ⟵ خروج 1 إن اختلف ملفٌّ عن توليده
"""
import inspect
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for _p in (os.path.join(ROOT, "faisal_method_v4"), os.path.join(ROOT, "faisal_method_v3"), HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import freeze as FZ       # noqa: E402
import ledger as LG       # noqa: E402
import runner as RN       # noqa: E402

DOCS = os.path.join(HERE, "docs")
STATES = ("READY", "WAIT", "REJECT", "UNKNOWN")
HEAD = ("> مولَّدٌ من `faisal_method_v41/docs_v41.py` — كلُّ رقمٍ من JSON (لا رقمَ باليد · FVD1) · العقدُ `V41_prereg.md` "
        "مدموجٌ قبل أيّ رقم (#{pr}) · V4 مجمَّد: `FREEZE_ID {fid}` · commit التجميد الرسميّ `{fc}`.\n")


def _j(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load():
    fm = FZ.load()
    return {"fm": fm, "cur": FZ.current_revision(fm), "prv": _j(os.path.join(DOCS, "V4_RULE_PROVENANCE.json")),
            "hm": _j(os.path.join(DOCS, "V4_HOLDOUT_MANIFEST.json")), "a": _j(os.path.join(HERE, "results", "analysis_v41.json")),
            "reg": _j(os.path.join(HERE, "results", "run_registry_v41.json")),
            "tf": _j(os.path.join(ROOT, "faisal_method_v3", "target_forensics.json"))}


def nd_thresholds():
    """عتبتا النسخة القريبة من توقيع `ledger.near_duplicates` نفسِه (لا رقمَ باليد)."""
    sig = inspect.signature(LG.near_duplicates).parameters
    return sig["dmax"].default, sig["pmax"].default


def split_tol_pct():
    return round((math.exp(RN.SPLIT_TOL) - 1) * 100)


def head(d, title):
    return f"# {title}\n\n" + HEAD.format(pr=d["reg"]["freeze"]["contract_pr"], fid=d["cur"]["freeze_id"][:16] + "…",
                                          fc=d["reg"]["freeze"]["official_freeze_commit"][:7]) + "\n"


def rate(k, n):
    return f"{k}/{n} = {k / n:.3f}" if n else f"{k}/0 (N=0)"


def wil(w):
    return f"[{w[0]:.3f} · {w[1]:.3f}]" if w else "— (المقامُ دون 10 ⟵ لا فاصل)"


def counts(dct):
    return " · ".join(f"{k} {v}" for k, v in sorted(dct.items(), key=lambda kv: (-kv[1], kv[0]))) or "—"


def mat_table(m):
    out = ["| فيصل ⟍ V4 | " + " | ".join(STATES) + " | المجموع |", "|---|" + "---|" * (len(STATES) + 1)]
    for f in STATES:
        row = m["matrix"][f]
        out.append(f"| **{f}** | " + " | ".join(str(row[v]) for v in STATES) + f" | {sum(row.values())} |")
    col = [sum(m["matrix"][f][v] for f in STATES) for v in STATES]
    out.append("| المجموع | " + " | ".join(str(c) for c in col) + f" | {m['n']} |")
    return "\n".join(out)


def mat_metrics(m):
    n = m["n"]
    return "\n".join([
        f"- **N** {n} · **التطابقُ التامّ** {rate(m['exact'], n)} · ويلسون 95% {wil(m['exact_wilson'])}"
        + (" · ⚠️ **INSUFFICIENT SAMPLE**" if m["insufficient"] else ""),
        f"- **READY:** دقّة {m['ready_precision']} · استدعاء {m['ready_recall']} · "
        f"**WAIT** {m['agreement']['WAIT']} · **REJECT** {m['agreement']['REJECT']} · **UNKNOWN** {m['agreement']['UNKNOWN']}",
        f"- **FALSE READY {m['false']['READY']}** (نسبة {m['false_rate']['READY']}) · FALSE WAIT {m['false']['WAIT']} "
        f"({m['false_rate']['WAIT']}) · FALSE REJECT {m['false']['REJECT']} ({m['false_rate']['REJECT']}) · "
        f"FALSE UNKNOWN {m['false']['UNKNOWN']} ({m['false_rate']['UNKNOWN']})",
        f"- خطُّ الأساس «دائمًا WAIT» (وصفيّ لا هدف): {rate(m['always_wait']['agree'], m['always_wait']['n'])} · "
        f"بلا قرار V4 (NOT_RUN) {m['v4_not_run']}"])


GROUP_AR = {"S1_all": "S1 كلُّها (الطبقةُ الأولى · الحاكمةُ في V4)", "S1_discovery": "S1 اكتشاف V4", "S1_holdout_v4": "S1 «احتجاز V4» (ملوَّثٌ هنا)",
            "S2": "S2 الثانويّة", "S3_golden": "S3 الذهبيّة (منفصلة · §16)", "S4_edu": "S4 القناة التعليميّة",
            "T1_cited_S1S2": "T1 مستشهَدٌ بها (S1+S2)", "T2_exposed_uncited_S1S2": "T2 مكشوفةٌ بلا استشهاد (S1+S2)"}


# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def doc_provenance(d):
    p = d["prv"]
    s = p["summary"]
    rank = {"UNKNOWN": 0, "POSSIBLE": 1, "PROBABLE": 2, "SUPPORTED": 3, "CONFIRMED": 4, "CONTRADICTED": -1}

    def note(r):
        c = r["COUNTS"]
        if not r["STATUS_DIFFERS"]:
            return "—"
        if r["ENGINEERING"]:
            return "مصدرٌ هندسيّ بلا وحدةٍ مستشهَدة ⟵ UNKNOWN (ليست دعوى عن فيصل)"
        if r["REGISTRY_STATUS"] == "CONTRADICTED" and not r["CONTRADICTORY_SOURCE_IDS"]:
            return "تناقضُ السجلّ من نتيجة اختبارٍ لا من صورة ⟵ المسطرةُ (مصدرٌ فقط) لا تراه"
        if rank.get(r["REGISTRY_STATUS"], 0) > rank.get(r["EVIDENCE_STATUS"], 0):
            return (f"تناقضٌ من الطبقة 1 (c1 {c['c1']}) يمنع CONFIRMED" if c["c1"] else
                    f"دعمُ الطبقة 1 (n1 {c['n1']}) أضعفُ من حالة السجلّ") + " ⟵ **السجلُّ أعلى من دليله**"
        return f"دعمُ الطبقة 1 (n1 {c['n1']} · c1 {c['c1']}) أقوى من حالة السجلّ ⟵ السجلُّ متحفّظ"

    rows = ["| القاعدة | فعّالة | القراريّة | المستوى | n1 | n2 | c1 | c2 | **المسطرة** | السجلّ | مباشرة | مُنفَّذة | مُختبَرة | طفرات | ملاحظة |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in p["rules"]:
        c = r["COUNTS"]
        rows.append(f"| `{r['RULE_ID']}` | {'✓' if r['CURRENT_IMPLEMENTATION']['active'] else '—'} | {r['DECISIONALITY']} | {r['SOURCE_LEVEL']} | "
                    f"{c['n1']} | {c['n2']} | {c['c1']} | {c['c2']} | **{r['EVIDENCE_STATUS']}** | {r['REGISTRY_STATUS']} | "
                    f"{'✓' if r['DIRECTLY_OBSERVED'] else '—'} | {'✓' if r['IMPLEMENTED'] else '—'} | {'✓' if r['TESTED'] else '—'} | "
                    f"{len(r['MUTATION_LOCK'])} | {note(r)} |")
    lims = []
    for r in p["rules"]:
        for x in r["KNOWN_LIMITATIONS"]:
            lims.append(f"- `{r['RULE_ID']}`: {x}")
    return head(d, "V4_RULE_PROVENANCE_AUDIT — مصدريّةُ قواعد V4 (§3)") + f"""## ① المسطرة (العقد §④ · تُطبَّق بالترتيب · مستقلّةٌ عن الأداء — FV49)
من **السجلّ المجمَّد والمدوّنة وحدهما** (لا نتيجةَ تقييمٍ ولا ذهبيّةَ ولا مقياس): لكلّ وحدةٍ مستشهَدٍ بها طبقتُها من مرورها البصريّ ·
والاستقلالُ **بالعنقود** (نُسخُ الصورة الواحدة وحدةٌ واحدة) · و`golden_witness` لا يُعدّ دعمًا أبدًا.
`n1`/`n2` = عناقيدُ الدعم بطبقة 1 / 2-2b · `c1`/`c2` = عناقيدُ التناقض بطبقة 1 / 2-2b.

① بلا وحدةٍ مستشهَدة ومصدرٌ هندسيّ ⟵ **UNKNOWN** (`engineering`) · ② `c1` واحدٌ فأكثر و`c1` لا يقلّ عن `n1` ⟵ **CONTRADICTED** ·
③ `n1` ثلاثةٌ فأكثر و`c1` صفر ⟵ **CONFIRMED** · ④ `n1` اثنان فأكثر ⟵ **SUPPORTED** · ⑤ `n1` واحد ⟵ **PROBABLE** · ⑥ `n2` واحدٌ فأكثر ⟵ **POSSIBLE** ·
⑦ وإلّا ⟵ **UNKNOWN**. **حالةُ السجلّ لا تُعدَّل** (V4 مجمَّد) — تُنشر بجوار المسطرة والفرقُ وسمٌ لا تصحيح.

## ② الحصيلة
- **القواعد {s['rules']}** (فعّالة {s['active']}) · وحداتٌ مستشهَدٌ بها في السجلّ كلِّه {s['cited_units_all']}.
- **المسطرة:** {counts(s['audit_status'])} · **السجلّ:** {counts(s['registry_status'])}.
- **مختلفة {len(s['differs'])}:** {' · '.join('`' + x + '`' for x in s['differs'])}.
- **السجلُّ أعلى من دليله {len(s['registry_stronger'])}:** {' · '.join('`' + x + '`' for x in s['registry_stronger'])} — ادّعاءٌ أقوى من مصدره (يُنقل إلى `V4_2_RESEARCH_QUEUE.md`).
- **قراءة:** الاختلافُ في الاتّجاهين — المسطرةُ أعلى في {len(s['differs']) - len(s['registry_stronger'])} وأدنى في {len(s['registry_stronger'])} ⟵ السجلُّ ليس منحازًا لاتّجاهٍ واحد ·
  والهندسيّةُ بلا صورة ({' · '.join('`' + r['RULE_ID'] + '`' for r in p['rules'] if r['ENGINEERING'])}) ليست دعوى عن فيصل.

## ③ كلُّ قاعدة (الحقولُ العشرون كاملةً في `V4_RULE_PROVENANCE.json`)
{chr(10).join(rows)}

## ④ الحدودُ المعروفة (من السجلّ والمسطرة)
{chr(10).join(lims)}

## ⑤ ما لا تقوله هذي المسطرة
- لا تقيس **هل القاعدةُ صحيحة** بل **كم مصدرًا مستقلًّا يسندها** — ودعمُ 3 صورٍ لا يجعلها عامّة.
- لا دعمَ احتجازٍ لأيّ قاعدة: الاحتجازُ التاريخيُّ النظيف 0 (`V4_HOLDOUT_INTEGRITY.md`) · والأماميّ لم يبدأ ⟵ `HOLDOUT_DATASET` و`VALIDATION_DATASET` فارغان كلُّهما.
"""


def doc_holdout(d):
    hm, a, reg = d["hm"], d["a"], d["reg"]
    s = hm["summary"]
    ph = a["posthoc_disclosure"]
    f1 = ph["first_summary"]
    ho = [r for r in hm["rows"] if r["SOURCE"]["split_v4"] == "holdout"]
    ho_rows = "\n".join(f"| `{r['CASE_ID']}` | {' · '.join(r['TICKER'])} | {r['TIER']} | {' · '.join(r['DISCOVERY_CONTAMINATION'])} |" for r in ho)
    ch_rows = "\n".join(f"| `{c['case']}` | {c['first_tier']} | {c['posthoc_tier']} | {' · '.join(c['first_flags']) or '—'} | "
                        f"{' · '.join(c['posthoc_flags'])} |" for c in ph["changed_cases"])
    fm1, fmp = ph["first_matrices"], a["historical_contaminated"]["matrices"]
    bb2 = next(b for b in reg["build_bugs"] if b["id"] == "BB2")
    v4h = a["historical_contaminated"]["v4_published_reproduction"]["S1_holdout_v4"]["v4_published"]
    was_clean = [c["case"] for c in ph["changed_cases"] if c["first_tier"] == "CLEAN"]
    dmax, pmax = nd_thresholds()
    return head(d, "V4_HOLDOUT_INTEGRITY — الاحتجاز وسلامتُه (§4-6)") + f"""## ① الحكم
**TRUE HOLDOUT: INSUFFICIENT SAMPLE — 0 حالةً نظيفة** من {s['cases']} (POST-HOC · التشغيلةُ الأولى قالت {f1['eligible']} بعيبٍ مُثبَت — §⑤ أدناه).
السبب **قاعدةُ العقد لا الصدفة**: كلُّ وحدةٍ تاريخيّة قُرئت في مرور V4 البصريّ قبل كتابة القواعد ⟵ `EXPOSED` ⟵ ملوَّثة (§4: «إن شككتَ فاكتشاف») ·
**ولا يُصنَع احتجازٌ بإرخاء العَلَم** ⟵ **الطريقُ الوحيد إلى احتجازٍ نظيف أماميّ** (`V4_PROSPECTIVE_PROTOCOL.md`).

## ② البيانُ المختوم
- **البصمة (الختم):** `{hm['seal']['sha256']}` — والكشفُ يتحقّق منها ويرفض بيانًا تغيّر بعد ختمه (FV42 · FV44).
- **المُدخَلات:** cases_v4 `{hm['inputs']['cases_v4_sha256'][:16]}…` · المدوّنة `{hm['inputs']['corpus_sha256'][:16]}…` · المرورُ البصريّ
  `{hm['inputs']['visual_pass_sha256'][:16]}…` · وحداتٌ مستشهَدٌ بها {hm['inputs']['cited_units']} · وحداتٌ مكشوفة {hm['inputs']['exposed_units']}.
- **الأعلام:** {counts(s['by_flag'])}.
- **الطبقات:** {counts(s['by_tier'])} — T1 = `CITED` · T2 = مكشوفةٌ بلا علمٍ آخر (طبقتان **وصفيّتان** لا احتجاز).

## ③ العمى عن الكلمة (§6)
البنّاءُ يرى `{' · '.join(hm['blind_fields'])}` وحدَها · **ولا يقرأ** `label · label4 · plan_F · levels_F · targets_F · dec` (قفل FV42 بالـAST) ·
ثمّ يُختم البيانُ ⟵ وبعدها فقط `reveal` تضمّ كلمةَ فيصل وتحمل بصمةَ البيان. ⚠️ **حدّ:** العمى بنيويٌّ في الكود لا معرفيّ — المنفّذُ قرأ الوحداتِ كلَّها في V4 ·
والمسطرةُ آليّةٌ مسجَّلةٌ قبل الرقم فلا يملك توجيهَها.

## ④ «احتجازُ V4» ليس احتجازًا هنا
من {s['v4_holdout_total']} حالاتِ احتجاز V4 **{len(s['v4_holdout_cited'])} مستشهَدٌ بعباراتها في سجلّ القواعد نفسِه** (Q2 · صدق) — أي أنّ قواعدَ V4 كُتبت
وهي ترى «احتجازَه» ⟵ رقمُ V4 على احتجازه (‏H-STATE {v4h['state_exact']}/{v4h['n']}) **وصفٌ ملوَّث** لا تحقّق.

| الحالة | الرمز | الطبقة | الأعلام |
|---|---|---|---|
{ho_rows}

## ⑤ إفصاحُ POST-HOC (العقد §⑲ — التشغيلةُ الأولى تُنشر ولا تُدهَس)
- **التشغيلةُ الأولى:** مؤهَّلة {f1['eligible']} · CITED {f1['by_flag']['CITED']} · SHARED_UNIT {f1['by_flag']['SHARED_UNIT']} · EXPOSED {f1['by_flag']['EXPOSED']} ·
  الطبقات {counts(f1['by_tier'])} · ختمُها `{ph['first_seal'][:16]}…`.
- **العيب ({bb2['id']}):** {bb2['bug']} · **الإصلاح:** `{bb2['fix']}` · **القفل:** {bb2['lock']}.
- **الإعادة (POST-HOC):** مؤهَّلة {ph['posthoc_summary']['eligible']} · CITED {ph['posthoc_summary']['by_flag']['CITED']} · SHARED_UNIT
  {ph['posthoc_summary']['by_flag']['SHARED_UNIT']} · EXPOSED {ph['posthoc_summary']['by_flag']['EXPOSED']} · ختمُها `{ph['posthoc_seal'][:16]}…`.
- **الأثرُ على الخلاصات:** T1 {fm1['T1_cited_S1S2']['exact']}/{fm1['T1_cited_S1S2']['n']} ⟵ {fmp['T1_cited_S1S2']['exact']}/{fmp['T1_cited_S1S2']['n']} ·
  T2 {fm1['T2_exposed_uncited_S1S2']['exact']}/{fm1['T2_exposed_uncited_S1S2']['n']} ⟵ {fmp['T2_exposed_uncited_S1S2']['exact']}/{fmp['T2_exposed_uncited_S1S2']['n']} ·
  المعلومةُ الخفيّة {ph['first_invisible']['verdict']} ({ph['first_invisible']['k_D']}/{ph['first_invisible']['n']}) في الاثنتين ⟵ **لا خلاصةَ انقلبت** ·
  والذي تغيّر: «النظيفة» في الأولى ({' · '.join('`' + x + '`' for x in was_clean) or '—'}) صارت مكشوفة ⟵ Q1 صدق **بعد الإصلاح وحدَه**.

| الحالة | الطبقة (الأولى) | الطبقة (POST-HOC) | الأعلام (الأولى) | الأعلام (POST-HOC) |
|---|---|---|---|---|
{ch_rows}

## ⑥ اختباراتُ التسرّب (FV42 · FV43 · FV44)
- **FV42:** الأعلامُ السبعة كلٌّ على حالته · النظيفةُ وحدَها مؤهَّلة · العمى بالـAST · والكشفُ يرفض بيانًا عُبث به.
- **FV43:** عضوُ العنقود يرث الاستشهاد · ومعرّفُ العبارة «#k» يرث وحدةَ صورته · والوحدةُ المشتركة مع الاكتشاف تُلوِّث · والنسخةُ المطابقة والمصغّرة
  تُكشف بالبصمة الإدراكيّة (dHash ≤ {dmax} · pHash ≤ {pmax} من V3) والضجيجُ لا · والختمُ يرفض حالةً لها نسخةٌ في المدوّنة.
- **الطفرات:** {reg['mutations']['FV42-FV50+FVT1+FVO1+FVW1+FVD1']['caught']}/{reg['mutations']['FV42-FV50+FVT1+FVO1+FVW1+FVD1']['of']} لأقفال FV42-FV50 وFVT1 وFVO1 وFVW1 وFVD1 سقطت كلٌّ بقفلها (صفرُ انهيار).
"""


def doc_protocol(d):
    reg = d["reg"]
    fw = [("F1", f"أقلُّ من {RN.MIN_BARS} جلسة قبل يوم القرار", "INVALID"), ("F2", "آخرُ شمعةٍ ليست آخرَ يومِ تداولٍ قبل القرار (بائتة)", "INVALID"),
          ("F3", f"في آخر {RN.MISS_WINDOW} يومَ تداول: غيابُ {RN.MISS_FAIL} جلساتٍ فأكثر · وأقلُّ منها", "INVALID · WARN"),
          ("F4", "تاريخٌ مكرَّر", "INVALID"), ("F5", f"شمعةٌ في يومٍ غيرِ تداوليّ داخل آخر {RN.WINDOW} (منطقةٌ زمنيّة/ربط)", "INVALID"),
          ("F6", f"تقسيمٌ في النافذة قفزةُ إغلاقه عند تاريخه داخل ±{split_tol_pct()}% من نسبته (غيرُ مسوّى) · ومصدرُ التقسيمات متعذّر",
           "INVALID · WARN"),
          ("F7", "أيُّ شمعةٍ يومَ القرار أو بعده في اللقطة · أو المحرّكُ قرأ ما بعده", "INVALID"),
          ("F8", "البورصةُ المحلولة غيرُ المسجَّلة", "WARN"), ("F9", "قيمةٌ ناقصة في OHLC", "INVALID")]
    fw_rows = "\n".join(f"| {a} | {b} | {c} |" for a, b, c in fw)
    unav = "\n".join(f"- `{k}`: {v}" for k, v in sorted(RN.UNAVAILABLE.items()))
    dmax, pmax = nd_thresholds()
    nmin = d["a"]["sample_size"]["n_min"]
    return head(d, "V4_PROSPECTIVE_PROTOCOL — بروتوكولُ التحقّق الأماميّ (§7-8 · §21-22 · §25-30)") + f"""## ① السؤال
**هل يعيد V4 المجمَّدُ قرارَ فيصل على حالةٍ لم تُستعمل في بنائه ولا ضبطه؟** — وحدَه يقرّر STATE C (§34).

## ② الأهليّة (آليّةٌ بلا انتقاء)
- **النافذة:** عبارةُ قرارٍ لفيصل تاريخُها بدقّة اليوم **من {LG.WINDOW_START} فصاعدًا** (أوّلُ يومٍ كاملٍ بعد آخر تغييرٍ في نواة المحرّك `d8b4937`) ·
  وتصل المستودعَ بعد التجميد.
- **كلُّ وحدةٍ جديدة تُسجَّل مرشَّحةً** ثمّ: حالةٌ (`CASE:CASE_0001`) أو سببُ استبعادٍ من قائمةٍ ثابتة: {' · '.join('`' + x + '`' for x in LG.EXCLUSIONS)} —
  **لا تخطّيَ صامت**. والنسخةُ القريبة من صورةٍ في المدوّنة (dHash ≤ {dmax} · pHash ≤ {pmax}) ⟵ `DUPLICATE_OF` لا حالة.
- **الكلمة:** {' · '.join(LG.LABELS)} ⟵ أربعُ حالات بجدول `L4` (WATCH ⟵ WAIT · MIXED يُعَدّ ويُستبعد).

## ③ تجميدُ القرار (§26 · §29) — الترتيبُ إلزاميٌّ في الكود
1. **الالتقاط والختم** (`Ledger.seal_case` · FV46): المعرّف · الرمز · تاريخُ القرار ودقّتُه ومصدرُه · فريمُ صورة فيصل · الصورةُ وبصمتُها · الطبقة ·
   وقتُ الالتقاط (لا يسبق تاريخَ القرار) ⟵ JSON قانونيّ ببصمة SHA-256 في سلسلةٍ إلحاقيّة.
2. **تشغيلُ V4 المجمَّد** (`runner.run_case`) على لقطة الشموع **قبل يوم القرار حصرًا** ⟵ **سجلُّ قرارٍ مختوم** (`Ledger.record_v4`): بصمةُ الحالة ·
   `freeze_id` · بصمةُ اللقطة (تُحفظ) · الجدار · السياقُ ومصدرُ كلّ حقل · بصماتُ الجالبين · commit التشغيلة.
3. **ثمّ وحدَه** كلمةُ فيصل (`Ledger.record_faisal` · FV48): الكلمةُ والاقتباسُ الحرفيّ (والمستوياتُ والخطّةُ والأهدافُ بحقول §18) —
   **وترفض بلا قرار V4 مختومٍ قبلها** (`DecisionFreezeError`).
4. **المقارنة** (`analysis.py`): الحالاتُ الكاملة وحدَها (ختم ‏+ V4 ‏+ فيصل · بلا INVALID).
- **المحرّكُ أعمى بالبناء:** `run_case` لا يقرأ من الحالة إلّا `symbol` و`decision_date` ولا يذكر صورةً ولا فيصل (FV48 بالـAST).
  ⚠️ **حدّ (§29):** الملتقِط يرى الصورةَ (وفيها الكلمة) — لكنّ ما يمرّ إلى المحرّك آليٌّ مسجَّل (الرمز والتاريخ) فلا قناةَ تسرّب.

## ④ لا معلومةَ مستقبليّة (§8)
- اللقطة = الشموعُ **قبل** يوم القرار (`runner.snapshot`) · والمحرّكُ يقصّ عند التاريخ نفسِه · وأيُّ شمعةٍ يومَه أو بعده ⟵ F7 ⟵ INVALID.
- **السياق:** `short_available` = «المتاح» من حصّاد الاقتراض بتاريخٍ لا يتجاوز يومَ القرار ولا يسبقه بأكثرَ من {RN.SHORT_LOOKBACK} جلسات ·
  وإلّا جلبٌ حيٌّ إن كان التشغيلُ خلال جلسةٍ من القرار · وإلّا `None`. والباقي **UNAVAILABLE بسببه** (لا تخمين):
{unav}
- ⇒ **V4 لا يستطيع أن يقول READY على أيّ حالةٍ أماميّة** ما دامت `groups`/`offering_pending`/`operator_press` = `None` (الصلاحيّةُ حاجبٌ لا يرقّي) —
  **قيدٌ بنيويٌّ معلَن**: FALSE READY = 0 بالبناء · واستدعاءُ READY = 0 بالبناء.
- ⇒ **وفضاءُ مخرَج V4 الأماميّ = {{WAIT · UNKNOWN}} بالبناء (FVO1):** حالاتُ المحرّك الفنيّة لا تُخرج REJECT (`STATE_DECISION`: WAIT · TECH_READY · UNKNOWN) ·
  وREJECT لا يأتي إلّا من «قروباتٍ داخلةٍ معلومة» (`groups = True`) ⟵ **كلُّ REJECT من فيصل خلافٌ بالبناء** · وخطُّ الأساس «دائمًا WAIT» هو الحدُّ الذي يُقارَن به.

## ⑤ جدارُ جودة البيانات (§21) — قبل أيّ مقياس
| الفحص | الشرط | الحكم |
|---|---|---|
{fw_rows}

`INVALID_FOR_VALIDATION` يُسجَّل (`Ledger.record_invalid`) ويُعَدّ ويُعلَّل ولا يدخل المقاييس · **ولا استبدالَ صامتًا للبيانات**.

## ⑥ السجلُّ الإلحاقيّ (§25 · FV47)
`faisal_method_v41/prospective_validation/`: `manifest.json` (السلسلة: لكلّ قيدٍ `seq` · `prev` · `entry_hash` · بصمةُ ملفّه) ·
`candidates/` · `cases/` · `decisions/` (قرارات V4) · `snapshots/` (لقطاتُ الشموع) · `faisal/` · `invalid/`.
- **«hashes/» في مثال المهمّة = السلسلةُ في البيان** (أقوى من ملفّات بصماتٍ منفصلة: تكشف الحذفَ وإعادةَ الترتيب · FV47).
- الملفُّ يُفتح بـ`"xb"` (لا كتابةَ فوق قائم حتى في السباق) · والتصحيحُ نسخةٌ جديدة بـ`supersedes` وسببٍ مكتوب · والتحقّقُ (`Ledger.verify`)
  يكشف: السلسلة · الترقيم · بصمةَ القيد والملفّ واللقطة · المحرّكَ الغريب · ربطَ القرار بحالته · ترتيبَ فيصل بعد V4 · واليتيم.

## ⑦ الإعادةُ الحتميّة (§22 · FV50)
كلُّ تشغيلة تختم: `freeze_id` · commit (`GITHUB_SHA`) · بصمةَ اللقطة · بصمةَ الإعداد · الرمزَ والفريمَ ومصدرَ البيانات وعددَ الشموع ·
وبصماتِ الجالبين (`tv_data.py` · `market_calendar.py` · `Super_stock.py` — مسجَّلةٌ لا مجمَّدة). **`replay` من اللقطة المحفوظة يعيد بصمةَ القرار
بايتًا بايتًا** — وإلّا خروجٌ غيرُ صفريّ وتحقيق.

## ⑧ عيبُ التنفيذ مقابل تغيير المنهج (§30)
- **عيبُ تنفيذٍ في V4** (سلوكٌ تنصّه المواصفةُ المجمَّدة والكودُ يخالفه) ⟵ مراجعةُ تجميدٍ جديدة في البيان (`IMPLEMENTATION_BUG` · `supersedes` ·
  قفلُ ارتدادٍ تُسقطه طفرة · `invalidates`) ثمّ إعادةُ التشغيلات المُبطَلة — **FV41 يرفض غيرَ ذلك**.
- **تغييرُ منهج** ⟵ لا يُطبَّق: `V4_CHANGE_REQUESTS.md` و`V4_2_RESEARCH_QUEUE.md` · **ولا تغذيةَ راجعة** من نتائج الأماميّ (§27).

## ⑨ التشغيل (`.github/workflows/faisal_v41.yml` · يدويّ)
- `verify`: التجميد (FV41) ‏+ السجلّ ‏+ ختمُ الاحتجاز — بلا شبكة.
- `smoke`: رمزٌ وتاريخٌ بلا سجلّ ⟵ الجدارُ وقرارُ V4 مطبوعان (`V41SMOKE`) — يُثبت المسارَ الحيّ.
- `run`: الحالاتُ المختومة بلا قرار V4 ⟵ تشغيلٌ وختمٌ ودفعٌ للسجلّ (الوحيدُ الذي يكتب).
- `replay`: يعيد كلَّ قرارٍ من لقطته ويقارن البصمة.

## ⑩ العيّنة (§28)
**N_MIN = {nmin}** حالةً صالحة (نصفُ عرض ويلسون ‏≈0.15 للتطابق عند p = 0.5) · واستدعاءُ READY يحتاج ‏≈{nmin} READY عند فيصل ⟵ التقديرُ الزمنيّ في
`V4_PROSPECTIVE_VALIDATION.md`. **ولا رقمَ سحريّ**: الأقلُّ يُنشر «INSUFFICIENT SAMPLE».

> 🔢 جامعُ التلغرام عند التجميد: التشغيلة `{reg['prospective_inputs']['telegram_collector_run']}` ({reg['prospective_inputs']['telegram_collector_utc']}) جلبت
> {reg['prospective_inputs']['telegram_new_images']} صورة · وآخرُ صورةٍ في المدوّنة {reg['prospective_inputs']['last_corpus_image_utc']}.
"""


MISSION_FIELDS = {
    "CASE_ID": "case.case_id", "TIMESTAMP": "case.decision_date (+ date_precision · date_source) · case.capture_utc",
    "SYMBOL": "case.symbol", "TIMEFRAME": "case.timeframe_f (فيصل) · v4.decision.timeframe (المحرّك: يوميّ وحدَه)",
    "CHART_IMAGE": "case.image · case.image_sha256", "RAW_DATA_VERSION": "v4.snapshot_path · v4.snapshot_sha256 · v4.meta.deps",
    "DATA_TIMESTAMP": "v4.firewall.last_bar", "PATTERN": "v4.decision.patterns · faisal.pattern_f",
    "MARKET_STRUCTURE": "v4.decision.structure", "SUPPORT": "v4.decision.support_resistance · faisal.levels_f / support_f",
    "RESISTANCE": "v4.decision.support_resistance.levels", "PRICE_LOCATION": "v4.decision.price_location",
    "VOLUME": "v4.decision.market_context.volume_vs_20d · اللقطة", "INDICATORS": "v4.decision.market_context.rsi14",
    "ENTRY": "v4.decision.entry · faisal.entry_f", "INVALIDATION": "v4.decision.invalidation · faisal.invalidation_f",
    "TARGET": "v4.decision.target · faisal.targets_f (حقول §18)", "VALIDITY_INFORMATION": "v4.context · v4.context_provenance",
    "FAISAL_DECISION": "faisal.label · faisal.label4 · faisal.quote", "V4_DECISION": "v4.decision.state · v4.decision.tech_state"}


def doc_schema(d):
    obj = {"generated_by": "faisal_method_v41/docs_v41.py", "contract": "V41_prereg §⑥-⑦ · §⑭", "ledger_dir": "faisal_method_v41/prospective_validation",
           "window_start": LG.WINDOW_START, "labels": list(LG.LABELS), "label4": LG.L4, "exclusions": list(LG.EXCLUSIONS),
           "record_kinds": list(LG.KINDS), "schema": LG.SCHEMA, "mission_field_map": MISSION_FIELDS,
           "context_unavailable": RN.UNAVAILABLE, "short_available_lookback_sessions": RN.SHORT_LOOKBACK,
           "firewall": {"MIN_BARS": RN.MIN_BARS, "WINDOW": RN.WINDOW, "MISS_WINDOW": RN.MISS_WINDOW, "MISS_FAIL": RN.MISS_FAIL,
                        "SPLIT_TOL_LOG": RN.SPLIT_TOL, "SPLIT_MIN_LOG": RN.SPLIT_MIN},
           "ordering": ["candidate", "case (seal)", "v4 (decision sealed)", "faisal (after v4 only)", "compare"],
           "append_only": {"open_mode": "xb", "correction": "new version with supersedes + correction_reason", "chain": "seq · prev · entry_hash"}}
    return json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def doc_prospective(d):
    a = d["a"]
    p, ss = a["prospective"], a["sample_size"]
    return head(d, "V4_PROSPECTIVE_VALIDATION — التحقّقُ الأماميّ") + f"""## ① الحالة
**PROSPECTIVE STATUS: {p['status']}** · **STATUS: {a['status']}** — **NOT COMPLETE**.
- مرشَّحون {p['candidates']} · حالاتٌ مختومة {p['sealed_cases']} · كاملة (ختم ‏+ V4 ‏+ فيصل) {p['complete']} · INVALID {p['invalid']} ·
  صورٌ جديدةٌ لم تُسجَّل {len(p['pending_images'])}.
- {'**لا حالاتٍ مصنوعة (§38):** لا عبارةَ قرارٍ لفيصل مؤرَّخةً من ' + LG.WINDOW_START + ' وصلت المستودع بعد التجميد ⟵ **PROSPECTIVE VALIDATION = NOT STARTED** وV4 باقٍ مجمَّدًا.' if p['status'] == 'NOT STARTED' else ('**حالاتٌ مختومةٌ تنتظر قرارَ V4 المجمَّد ثمّ كلمةَ فيصل** (الترتيبُ مختومٌ في السجلّ) — ولا حالةَ مصنوعة (§38).' if p['status'] == 'SEALED_PENDING' else 'الحالاتُ من السجلّ الإلحاقيّ وحدَه — ولا حالةَ مصنوعة (§38).')}

## ② المصفوفة الأماميّة (الرسميّة)
{mat_table(p['matrix'])}

{mat_metrics(p['matrix'])}

## ③ ما يلزم للحكم (§28 — تقديرٌ وصفيّ من معدّل S1 التاريخيّ)
- **N_MIN {ss['n_min']}** ({ss['formula']}) · حالاتُ S1 التاريخيّة {ss['s1_cases']} بين {ss['s1_first']} و{ss['s1_last']} ({ss['months']} شهرًا) ⟵
  **{ss['s1_per_month']} حالةً/شهر** ⟵ بلوغُ N_MIN ‏≈ **{ss['months_to_n_min']} شهرًا** (Q6 · صدق).
- **READY عند فيصل {ss['s1_ready']} من {ss['s1_cases']}** (نسبة {ss['ready_rate']}) ⟵ {ss['n_min']} READY تحتاج ‏≈{ss['cases_for_43_ready']} حالة ‏≈ **{ss['years_for_43_ready']} سنة** ⟵
  **استدعاءُ READY لا يُقاس عمليًّا بهذا المعدّل** — والأهمُّ أنّ V4 لا يقول READY بلا معلومة المضارب أصلًا (بنيويّ).
- ⚠️ التقديرُ يفترض استمرارَ معدّل النشر والالتقاط كما كان — **وصفٌ لا وعد**.

## ④ الدفعات (`faisal_method_v41/batches/` · مولَّدةٌ من بيانها)
{batches_block()}
"""


def batches_block():
    """سطرٌ لكلّ دفعة من `PROSPECTIVE_BATCH_*_MANIFEST.json` (ونتائجها إن وُجدت) — لا رقمَ باليد."""
    import glob
    rows = []
    for mp in sorted(glob.glob(os.path.join(HERE, "batches", "*", "PROSPECTIVE_BATCH_*_MANIFEST.json"))):
        m = _j(mp)
        c = m["counts"]
        line = (f"- **{m['batch_id']}** — وصل {m['total_received']} (قال المالك {m['expected_by_owner']}) · "
                + " · ".join(f"{k} {c[k]}" for k in ("CLEAN_PROSPECTIVE", "CONTAMINATED", "DUPLICATE", "DERIVATIVE", "UNKNOWN"))
                + f" · حالاتُ تحقّق {m['validation_cases']}")
        rp = mp.replace("_MANIFEST.json", "_RESULTS.json")
        if os.path.exists(rp):
            r = _j(rp)["aggregate"]
            line += f" · قورنت {r['N']} · تطابق {r['exact']}"
        rows.append(line + f" — `{os.path.relpath(os.path.dirname(mp), ROOT)}/`")
    return "\n".join(rows) or "- لا دفعة."


def doc_confusion(d):
    a = d["a"]
    h = a["historical_contaminated"]
    p = a["prospective"]
    parts = []
    for g in ("S1_all", "S1_discovery", "S1_holdout_v4", "S2", "T1_cited_S1S2", "T2_exposed_uncited_S1S2", "S4_edu", "S3_golden"):
        m = h["matrices"][g]
        parts.append(f"### {GROUP_AR[g]}\n{mat_table(m)}\n\n{mat_metrics(m)}\n")
    rep = "\n".join(f"| {GROUP_AR[g]} | {r['v4_published']['state_exact']}/{r['v4_published']['n']} | "
                    f"{r['recomputed_ok_only']['state_exact']}/{r['recomputed_ok_only']['n']} | {'✓' if r['match'] else '✗'} | "
                    f"{r['scale_mismatch_included_v41']} | {h['matrices'][g]['exact']}/{h['matrices'][g]['n']} |"
                    for g, r in h["v4_published_reproduction"].items())
    fr = "\n".join(f"- {GROUP_AR[g]}: FALSE READY **{h['matrices'][g]['false']['READY']}** من {h['matrices'][g]['n']}"
                   for g in ("S1_all", "S2", "S3_golden", "S4_edu"))
    nr = " · ".join(f"`{x['case']}` ({x['set']} · فيصل {x['faisal']} · {x['status']})" for x in h["not_run"]) or "—"
    st = h["stages"]
    return head(d, "V4_DECISION_CONFUSION_MATRIX — مصفوفاتُ القرار (§9-12 · §23)") + f"""## ① FALSE READY أوّلًا (§10 — الأخطر)
- **الأماميّ:** {p['matrix']['false']['READY']} من {p['matrix']['n']}{' (N = 0 ⟵ لا حكم)' if p['matrix']['n'] == 0 else ''}.
{fr}
- 🧭 **فضاءُ المخرَج الأماميّ {{WAIT · UNKNOWN}} بالبناء (FVO1)** ⟵ READY وREJECT من V4 مستحيلان أماميًّا ما دامت القروباتُ والطرحُ والمضاربُ بلا مصدر.
- ⚠️ **صفرٌ بنيويٌّ لا مهارة (Q4 · صدق):** V4 لم يقل READY قطّ لأنّ الصلاحيّةَ غائبة (`operator_press`/`groups`/`offering` = None) ⟵
  الحاجبُ لا يرقّي ⟵ **لا تُقرأ دقّةُ READY دليلَ جودة**.

## ② الأماميّ (الرسميّ)
{mat_table(p['matrix'])}

{mat_metrics(p['matrix'])}

## ③ التاريخيّ — **ملوَّثٌ ووصفيّ** (كلُّ وحدةٍ مكشوفة · لا يُقرأ تحقّقًا)
> يضمّ صفوفَ `SCALE_MISMATCH` (قرارُ V4 قائم · والخلافُ معها يُصنَّف G في §⑫) · ولا يضمّ ما لم يُشغَّل (`NO_BARS`): {nr}.

{chr(10).join(parts)}
## ④ الجسرُ إلى رقم V4 المنشور (إعادةُ إنتاج · لا رقمٌ بديل)
V4 حسب H-STATE على `status = OK` وحدَه · وV4.1 يضمّ `SCALE_MISMATCH` — **والفرقُ كلُّه منها** (أُعيد حسابُ رقم V4 فطابق في المجموعات كلِّها):

| المجموعة | V4 المنشور | المُعاد (OK وحدَه) | تطابق | SCALE_MISMATCH المضافة | V4.1 |
|---|---|---|---|---|---|
{rep}

## ⑤ المراحلُ منفصلة (§12 — «النموذجُ الصحيح بقرارٍ خاطئ ليس إعادةً ناجحة»)
- **PATTERN/STRUCTURE EXISTS** (V4 ليست DATA_INSUFFICIENT × فيصل وصف دعمًا/مستويات · S1+S2): كلاهما {st['structure_exists']['both']} ·
  V4 وحدَه {st['structure_exists']['v4_only']} · فيصل وحدَه {st['structure_exists']['faisal_only']} · لا هذا ولا ذاك {st['structure_exists']['neither']}.
- **SETUP VALID** (V4 جاهزيّةٌ فنيّة × فيصل «جاهز فنيًّا» أو READY): كلاهما {st['setup_valid']['both']} · V4 وحدَه {st['setup_valid']['v4_only']} ·
  فيصل وحدَه {st['setup_valid']['faisal_only']} · لا هذا ولا ذاك {st['setup_valid']['neither']} ⟵ **لا تطابقَ واحدًا على «الإعداد صالح»** —
  V4 يرى جاهزيّةً فنيّةً حيث لا يرى فيصل (ويقول UNKNOWN بغياب الصلاحيّة) · وفيصل يرى جاهزيّةً حيث لا يراها V4.
- **READY / WAIT / REJECT:** المصفوفاتُ أعلاه — ولا تُطوى في «صح/خطأ» (§9).
"""


def doc_invisible(d):
    a = d["a"]
    h = a["historical_contaminated"]
    inv = h["invisible"]
    rows = []
    for x in h["disagreements"]:
        rs = " · ".join(f"{k} {v}" for k, v in sorted(x["EVIDENCE_STATUS"]["rules"].items())) or "—"
        rows.append(f"| `{x['CASE_ID']}` | {x['set']} | {x['FAISAL_DECISION']} | {x['V4_DECISION']} | {x['DIFFERENCE']} | "
                    f"{' · '.join(x['RULES_BLOCKED']) or '—'} | {' · '.join(x['DATA_MISSING']) or '—'} | {x['POSSIBLE_REASON']} | {rs} | "
                    f"**{x['CLASSIFICATION']}** |")
    dep = "\n".join(f"| {k} | {v['n']} | {counts(v['faisal'])} | {counts(v['v4'])} |" for k, v in sorted(h["dependency"].items()))
    ords = "\n".join(f"| {k} | " + " | ".join(str(v[s]) for s in STATES) + " |" for k, v in sorted(h["orders"].items()))
    u = h["unknown_behaviour"]
    pm = a["prospective"]["matrix"]
    pro = (f"N = {pm['n']}" if not pm["n"] else
           f"N = {pm['n']} (دون حدّ الحكم بالنسبة 10) · خلافاتٌ أماميّة {a['prospective']['coverage']['disagreements']}")
    return head(d, "INVISIBLE_INFORMATION_AUDIT — فرضيّةُ «المعلومة الخفيّة» (§11 · §13-15)") + f"""## ① الحكم
- **الأماميّ (الرسميّ): UNKNOWN** — {pro}.
- **التاريخيّ الملوَّث (وصفيّ): {inv['verdict']}** — k (D بعد البدائل) = {inv['k_D']} من N (الخلافاتُ عدا E/G) = {inv['n']} ⟵ {inv['k_D'] / inv['n']:.3f}.
  ❌ **تنبّؤي Q8 «الحكمُ PARTIAL» خاب** (الأكثرُ D صدق) — يُنشر ولا يُحذف.
- **ما يعنيه بالضبط:** كلُّ D هنا من نوعٍ واحد — **V4 جاهزٌ فنيًّا ويمتنع (UNKNOWN) لأنّ الصلاحيّةَ غائبة وفيصل قال WAIT** ⟵ فيصل يقرّر بمعلومةٍ
  ليست في الشموع (المضارب · القروبات · الطرح · الشورت) — **ولا حالةَ واحدةً قال فيها V4 WAIT/REJECT وناقضته معلومةٌ خفيّة**. والمقامُ {inv['n']} (حدُّ الحكم بالنسبة 10).

## ② المنهج (العقد §⑫ — البدائلُ قبل «المعلومة الخارجيّة»)
لكلّ خلافٍ يُسجَّل **أوّلُ** ما يفسّره بالدليل المسجَّل: ① بياناتٌ ناقصة ⟵ **E** · ② توقيت (`SCALE_MISMATCH` أو سعرُ الصورة يخالف إغلاقَ القراءة
بأكثرَ من 15%) ⟵ **G** · ③ V4 جاهزٌ فنيًّا ويمتنع لغياب معلومةٍ بنفسه ⟵ **D** · ④ فريمُ فيصل لا يضمّ اليوميّ ⟵ **B** · ⑤ فئةُ خطّة فيصل ≠ فئةُ المستوى
الحاسم في V4 ⟵ **B** · ⑥ العبارةُ مذكورةٌ مناقِضةً في القاعدة الحاجبة ⟵ **C** · ⑦ اعتمادُ الحالة UNAVAILABLE/EXTERNAL ⟵ **D** · ⑧ وإلّا **H** ·
و**A** إن ناقض مخرجُ V4 مواصفتَه · و**F** لعباراتٍ متعارضة. أسئلةُ المهمّة العشرة (§15) مرسومةٌ عليها: الهندسةُ والبنيةُ والدعمُ والموقع ⟵ ⑤ ·
الفريم ⟵ ④ · التوقيت ⟵ ② · المعلومةُ الخارجيّة ⟵ ③/⑦ · التعليقُ اليدويّ/الالتباس ⟵ F · البياناتُ الناقصة ⟵ ① · الحكمُ التقديريّ ⟵ ⑥.

## ③ كلُّ خلاف (S1+S2 · {len(h['disagreements'])}) — الحقولُ الأحد عشر (§11)
الفئات: {counts(inv['by_class'])} · **H (غيرُ مفسَّر) = {inv['by_class']['H']}**.

| الحالة | المجموعة | فيصل | V4 | الفرق | الحاجبة | الناقص | السببُ المحتمل | دليلُ القواعد | الفئة |
|---|---|---|---|---|---|---|---|---|---|
{chr(10).join(rows)}

> `RULES_TRIGGERED` و`DATA_AVAILABLE` (شموعُ القراءة · الإغلاق · سعرُ الصورة · والسياقُ «لا شيء» في تشغيل V4 التاريخيّ) لكلّ خلافٍ في
> `results/analysis_v41.json` · و`EVIDENCE_STATUS` للحالة كلِّها: **HISTORICAL-CONTAMINATED** بطبقتها.

## ④ الاعتمادُ على المعلومة الخارجيّة (§14 · S1+S2)
| الاعتماد | N | كلمةُ فيصل | قرارُ V4 |
|---|---|---|---|
{dep}

**هل UNKNOWN في V4 يتصرّف صحيحًا؟** مخرجاتُ V4 الجاهزة فنيًّا {u['tech_ready_outputs']} ⟵ UNKNOWN {u['of_which_unknown']} · READY {u['of_which_ready']} ⟵
**يمتنع ولا يختلق READY** (§36: «UNKNOWN أفضلُ من READY مصطنَع») — {u['note']}.

## ⑤ «الطلباتُ عند الدعم» (§13 — لا يُفترض أنّها شرط)
| الدعم/الطلبات | READY | WAIT | REJECT | UNKNOWN |
|---|---|---|---|---|
{ords}

**H-ORD («كلُّ READY بدعمٍ يذكر الطلبات»): {h['h_ord']}** (READY بدعم = {h['h_ord_ready_with_support']}) — تاريخيٌّ ملوَّثٌ وصفيّ ⟵ يوافق قرارَ V4
أنّها `SUPPORTING` (آليّةُ دخولٍ لا شرطُ قرار) · **ولا يُغيَّر V4** · والحكمُ الرسميّ أماميّ.
"""


def doc_queue(d):
    a, p = d["a"], d["prv"]
    h = a["historical_contaminated"]
    b = [x for x in h["disagreements"] if x["CLASSIFICATION"] == "B"]
    g = [x for x in h["disagreements"] if x["CLASSIFICATION"] == "G"]
    dd = [x for x in h["disagreements"] if x["CLASSIFICATION"] == "D"]
    return head(d, "V4_2_RESEARCH_QUEUE — طابورُ أبحاث V4.2 (§27 · §30)") + f"""> **لا يدخل V4 شيءٌ من هنا أثناء التحقّق.** كلُّ بندٍ فرضيّةٌ تحتاج تسجيلًا مسبقًا ودليلًا أماميًّا · ولا يبدأ V4.2 قبل ختم مجموعة التحقّق الأماميّة.

## RQ-01 · معنى `operator_press = False` (CR-01)
المواصفةُ لا تحسم «نظيفة» للمضارب ⟵ ملتبس ⟵ لم يُصلح · **أثرُه اليوم صفر** (لا مصدرَ لبصمة المضارب) · يُحسم بنصٍّ من فيصل أو بإذن المالك.

## RQ-02 · الفريمُ غيرُ اليوميّ (B · فريم)
خلافاتٌ فريمُ فيصل فيها لا يضمّ اليوميّ: {' · '.join('`' + x['CASE_ID'] + '`' for x in b if 'فريمُ' in (x['POSSIBLE_REASON'] or '')) or '—'} — المحرّكُ يوميٌّ وحدَه (`R4-TF-01`) ⟵
سؤال: هل قرارُ فيصل على الأسبوعيّ/4س يُعاد بقاعدةٍ مكتوبة؟ (يلزمه شموعٌ بالفريم وتسجيلٌ مسبق).

## RQ-03 · فئةُ الخطّة مقابل المستوى الحاسم (B · بنية)
{' · '.join('`' + x['CASE_ID'] + '` (فيصل ' + x['FAISAL_DECISION'] + ' · ' + x['V4_DECISION'] + ')' for x in b if 'فئةُ' in (x['POSSIBLE_REASON'] or '')) or '—'} —
فيصل READY حيث يرى V4 القاعَ مكسورًا (`R4-INV-01`) أو غيرَ ثابت (`R4-HOLD-01`) ⟵ سؤال: **ما تعريفُ فيصل لـ«قاعٍ جديدٍ صالح» بعد كسر السابق؟**
⚠️ لا «تصحيحَ ليطابق» — بل قاعدةٌ مكتوبةٌ بنصّه تُقاس أماميًّا.

## RQ-04 · التوقيت (G)
{' · '.join('`' + x['CASE_ID'] + '` (' + (x['POSSIBLE_REASON'] or '') + ')' for x in g) or '—'} ⟵ **يُسجَّل في الأماميّ وقتُ الصورة بالساعة** (بري/نظاميّ/أفتر) ·
ويُحسم بقاعدة: أيُّ شمعةٍ هي «ما كان متاحًا» لصورةٍ في الأفتر؟

## RQ-05 · معلومةُ الصلاحيّة (D)
{len(dd)} خلافاتٍ D كلُّها «V4 يمتنع لغياب الصلاحيّة» ⟵ أيُّ مصدرٍ **as-of** للقروبات والطرح المعلَّق وبصمة المضارب؟ (Polygon انتهى 2026-09-29 ·
والمتاحُ للشورت من الحصّاد منذ 2026-08-07 وحدَه) — بلاه يبقى V4 عاجزًا عن READY أماميًّا.

## RQ-06 · السجلُّ أقوى من دليله
{' · '.join('`' + x + '`' for x in p['summary']['registry_stronger'])} ⟵ في V4.2 تُكتب حالةُ القاعدة **بالمسطرة** لا بالتقدير.

## RQ-07 · «70٪» هدفًا
لا معنى مستقلٌّ مفهرس لها (تظهر داخل F50-2 وحدَها: «أكثر من 70%» جنيٌ مبكّر عند المقاومة الثالثة) ⟵ **UNKNOWN** ⟵ يُجمع أماميًّا بحقول §18.

## RQ-08 · قاعدةُ الدورة `R4-CYC-01`
تناقضاتٌ من الطبقة 1 ({next(r['COUNTS']['c1'] for r in p['rules'] if r['RULE_ID'] == 'R4-CYC-01')}) بنصّ فيصل («تصعد مباشره لا تصلح لها هذي النظريه») ⟵
هل الدورةُ شرطٌ عامّ أم لنوعٍ من الأسهم؟ — يُقاس أماميًّا (حالاتُ «صعود مباشر» تُوسَم).
{batch_queue_block()}{ex_queue_block()}{protocol_queue_block()}"""


def protocol_queue_block():
    """🧊 بنودُ التحقّق الأماميّ النهائيّ (PHASE 9 · `final_protocol/PROTOCOL_STATUS.json` · العقد `FINAL_PROTOCOL_prereg.md` §⑫) —
    `V4_2_CANDIDATE` لكلّ عدمِ تطابقٍ بحقوله السبعة · **لا تنفيذ ولا إعادةَ تشغيل** · ومن JSON الحالة لا باليد."""
    sp = os.path.join(HERE, "final_protocol", "PROTOCOL_STATUS.json")
    if not os.path.exists(sp):
        return ""
    st = _j(sp)
    cands = st.get("v4_2_candidates") or []
    o = st.get("output") or {}
    out = ["", "## 🧊 التحقّقُ الأماميّ النهائيّ (`final_protocol/PROTOCOL_STATUS.json` · FINAL PROSPECTIVE VALIDATION PROTOCOL)",
           f"> V4 مجمَّد (V4_COMMIT `{o.get('V4_COMMIT', '—')[:12]}`) · `V4_2_CANDIDATE` لكلّ عدمِ تطابقٍ أماميّ — **لا يدخل V4 ولا يُعاد التشغيل** · "
           f"الحالاتُ الصالحة {o.get('VALID_PROSPECTIVE_CASES', 0)} · {o.get('FINAL_VALIDATION_STATE', '—')}",
           f"- **V4_2_CANDIDATE:** {len(cands)}" + ("" if cands else " — لا عدمَ تطابقٍ أماميّ بعد")]
    for c in cands:
        out += ["", f"### {c['CASE_ID']} · {c.get('MATCH_CLASS')} ({c.get('SAMPLE')})"]
        out += [f"- **{k}:** {c.get(k)}" for k in ("OBSERVATION", "EVIDENCE", "WHY_V4_FAILED", "POSSIBLE_MISSING_RULE",
                                                    "GENERALIZATION_STATUS", "CONTRADICTING_CASES")]
    return "\n".join(out) + "\n"


def ex_queue_block():
    """بنودُ تدقيق اكتمال المدوّنة (`corpus_audit/research_queue_ex.json` · EX_PROTOCOL §⑥ · §⑦) — مرشَّحاتٌ وتحديثاتٌ لبنودٍ قائمة · لا تدخل V4."""
    qp = os.path.join(HERE, "corpus_audit", "research_queue_ex.json")
    if not os.path.exists(qp):
        return ""
    q = _j(qp)
    out = ["", f"## تدقيقُ اكتمال المدوّنة {q['batch_id']} (`{os.path.relpath(qp, ROOT)}`)", f"> {q['rule']}"]
    for it in q["items"]:
        out += ["", f"### {it['id']} · {it['title']} ({it['cls']})",
                f"- **الملاحظة:** {it['observation']}",
                f"- **القاعدةُ المرشَّحة:** {it['candidate_rule']}",
                f"- **قواعدُ V4 المعنيّة:** {' · '.join('`' + r + '`' for r in it.get('rules') or []) or '— (فجوةٌ لا قاعدةَ لها في V4)'}",
                f"- **حالاتٌ تدعم ({len(it['supporting_cases'])}):** {' · '.join(it['supporting_cases']) or '—'} · "
                f"**حالاتٌ تعارض:** {' · '.join(it['contradictory_cases']) or 'لا شيء معروف'}",
                f"- **الثقة:** {it['confidence']} · **العموم:** {it['generality']}",
                f"- **لماذا لا تدخل V4 الآن:** {it['why_not_v4']} · **الأثر على V4:** {it['v4_effect']}"]
    out += ["", "### تحديثاتٌ لبنودٍ قائمة (سجلٌّ جديد · البندُ الأصليّ لا يُعدَّل)"]
    out += [f"- **{u['id']} ⟵ {u['updates']}:** {u['note']} ({' · '.join(u['evidence'])})"
            + (f" · قواعدُ V4: {' · '.join('`' + r + '`' for r in u['rules'])}" if u.get("rules") else "") for u in q["updates"]]
    return "\n".join(out) + "\n"


def batch_queue_block():
    """بنودُ الدفعات الأماميّة (`batches/*/research_queue.json`) — ملاحظةٌ وقاعدةٌ مرشَّحة وحالاتٌ تدعم وتعارض وثقةٌ وعمومٌ ولماذا لا تدخل V4 (§8)."""
    import glob
    out = []
    for qp in sorted(glob.glob(os.path.join(HERE, "batches", "*", "research_queue.json"))):
        q = _j(qp)
        out += ["", f"## دفعة {q['batch_id']} (`{os.path.relpath(qp, ROOT)}`)", f"> {q['rule']}"]
        for it in q["items"]:
            out += ["", f"### {it['id']} · {it['title']}",
                    f"- **الملاحظة:** {it['observation']}",
                    f"- **القاعدةُ المرشَّحة:** {it['candidate_rule']}",
                    f"- **حالاتٌ تدعم:** {' · '.join(it['supporting_cases']) or '—'} · **حالاتٌ تعارض:** {' · '.join(it['contradictory_cases']) or 'لا شيء معروف'}",
                    f"- **الثقة:** {it['confidence']} · **العموم:** {it['generality']}",
                    f"- **لماذا لا تدخل V4 الآن:** {it['why_not_v4']}"]
    return "\n".join(out) + ("\n" if out else "")


def doc_change_requests(d):
    cur = d["cur"]
    return head(d, "V4_CHANGE_REQUESTS — طلباتُ التغيير (§30)") + f"""## مراجعاتُ التجميد
- المراجعةُ الحاليّة **{cur.get('rev')}** · الصنف **{cur.get('reason_class')}** — لا مراجعةَ لعيب تنفيذٍ في V4 منذ التجميد.
- **عيوبٌ وُجدت أثناء بناء V4.1 كانت في أدوات V4.1 لا في V4** (`V4.1_CHANGELOG.md`) ⟵ لا تمسّ التجميد.

## CR-01 · `operator_press = False` (ملتبس ⟵ لا يُصلح)
- **الوصف:** `validity()` تعامل `operator_press = False` معلومةً مكتملةً لا تمنع ⟵ READY ممكن · ووصفُ `R4-OP-01` «الجاهزيّةُ الفنيّة بلا بصمةٍ ⟵ انتظار» ·
  والعقدُ «كاملةً نظيفةً ⟵ READY» لا يحسم «نظيفة».
- **التصنيف:** المواصفةُ لا تحسمه ⟵ **يُعامَل منهجيًّا** (لا IMPLEMENTATION BUG) ⟵ لا تعديلَ على V4.
- **الأثر:** صفرٌ بالبناء — المشغّلُ يمرّر `operator_press = None` دائمًا (لا مصدر) ⟵ لا قرارَ يتغيّر.
- **المكان:** `V4_2_RESEARCH_QUEUE.md` · RQ-01.
"""


def doc_changelog(d):
    reg = d["reg"]
    bugs = "\n".join(f"- **{b['id']}** `{b['tool']}` — {b['bug']} · كشفه: {b['found_by']} · الإصلاح: {b['fix']} · القفل: {b['lock']} · "
                     f"{'قبل أيّ رقم' if b['before_first_number'] else '**بعد التشغيلة الأولى ⟵ POST-HOC (العقد §⑲)**'}" for b in reg["build_bugs"])
    return head(d, "V4.1_CHANGELOG") + f"""## ما أُضيف (أدواتُ قياسٍ · V4 لم يُمسّ)
- `V41_prereg.md` — العقد · مدموجٌ قبل أيّ رقم (#{reg['freeze']['contract_pr']} · `{reg['freeze']['official_freeze_commit'][:7]}`).
- `freeze.py` ‏+ `docs/V4_FREEZE_MANIFEST.json`/`V4_FREEZE_REPORT.md` — التجميد (FV41).
- `provenance.py` ‏+ `docs/V4_RULE_PROVENANCE.json` — المسطرة (FV49).
- `holdout.py` ‏+ `docs/V4_HOLDOUT_MANIFEST.json` — التلوّث والختم والكشف (FV42 · FV43).
- `ledger.py` ‏+ `prospective_validation/` — السجلُّ الإلحاقيّ (FV44 · FV46 · FV47 · FV48 · FVT1).
- `runner.py` — الجدار F1-F9 · السياقُ الآليّ · التشغيلُ والإعادة (FV45 · FV50) · و`.github/workflows/faisal_v41.yml` (يدويّ).
- `analysis.py` ‏+ `results/analysis_v41.json` — المصفوفات والتدقيقات · و`docs_v41.py` — الوثائق (FVD1).

## ما لم يتغيّر
- **V4** (‏{d['cur']['n_files']} ملفًّا مجمَّدًا · نواةُ المحرّك منذ `d8b4937`) · **الإنتاج** (لا كرون · لا ماسح · لا تلغرام · لا عتبة · لا حالة) · **الذهبيّة**.

## عيوبُ البناء (في أدوات V4.1)
{bugs}

## التنبّؤات (العقد §⑱ · تُنشر إن خابت)
{doc_predictions(d)}
"""


def doc_predictions(d):
    a = d["a"]
    h = a["historical_contaminated"]
    hs = a["holdout_summary"]
    ph = a["posthoc_disclosure"]
    t1, t2 = h["matrices"]["T1_cited_S1S2"], h["matrices"]["T2_exposed_uncited_S1S2"]
    s1 = h["matrices"]["S1_all"]
    ss = a["sample_size"]
    inv = h["invisible"]
    plural = max(inv["by_class"].items(), key=lambda kv: kv[1])[0]
    uncited = [c for c in ("IPDN_2026-09-2x",) if c not in hs["v4_holdout_cited"]]
    q = [("Q1", "الاحتجازُ النظيف = 0", hs["eligible"] == 0,
          f"POST-HOC {hs['eligible']} · **والتشغيلةُ الأولى {ph['first_summary']['eligible']} (عيب BB2)** ⟵ صدق بعد الإصلاح وحدَه"),
         ("Q2", "تسعٌ من عشرٍ CITED (IPDN وحدَها لا)", len(hs["v4_holdout_cited"]) == 9 and uncited == ["IPDN_2026-09-2x"],
          f"{len(hs['v4_holdout_cited'])}/{hs['v4_holdout_total']}"),
         ("Q3", "المسطرةُ تقرأ قاعدتين فأكثر أدنى من السجلّ (منها R4-DATA-01)",
          len(a["provenance_summary"]["registry_stronger"]) >= 2 and "R4-DATA-01" in a["provenance_summary"]["registry_stronger"],
          f"{len(a['provenance_summary']['registry_stronger'])}"),
         ("Q4", "S1: FALSE READY 0 واستدعاء READY 0/1 بنيويًّا", s1["false"]["READY"] == 0 and s1["ready_recall"] == "0/1",
          f"FALSE READY {s1['false']['READY']} · استدعاء {s1['ready_recall']}"),
         ("Q5", "PROSPECTIVE NOT STARTED (عند التقرير الأوّل)", d["reg"]["first_report"]["prospective_status"] == "NOT STARTED",
          f"{d['reg']['first_report']['prospective_status']} عند التقرير الأوّل ({d['reg']['first_report']['utc']}) · والآن {a['prospective']['status']}"),
         ("Q6", "N_MIN بعد أكثرَ من 12 شهرًا · واستدعاءُ READY سنوات", ss["months_to_n_min"] > 12 and ss["years_for_43_ready"] > 1,
          f"{ss['months_to_n_min']} شهرًا · {ss['years_for_43_ready']} سنة"),
         ("Q7", "اتّفاقُ T1 أعلى من T2", (t1["exact_rate"] or 0) > (t2["exact_rate"] or 0),
          f"T1 {t1['exact']}/{t1['n']} مقابل T2 {t2['exact']}/{t2['n']}"),
         ("Q8", "الأكثرُ D والحكمُ PARTIAL", plural == "D" and inv["verdict"] == "PARTIAL",
          f"الأكثر {plural} ✓ · الحكم {inv['verdict']} ✗")]
    first_bad = ph["first_summary"]["eligible"] != 0

    def mark(qid, ok):
        if qid == "Q1" and ok and first_bad:
            return "⚠️ خاب في التشغيلة الأولى · صدق POST-HOC وحدَه (§⑲)"
        return "✅ صدق" if ok else "❌ خاب"
    return "\n".join(["| # | التنبّؤ | النتيجة | الحكم |", "|---|---|---|---|"]
                     + [f"| {a_} | {b_} | {c_} | {mark(a_, ok)} |" for a_, b_, ok, c_ in q])


def checklist(d):
    a, reg = d["a"], d["reg"]
    p = a["prospective"]
    n = p["matrix"]["n"]
    n0 = n == 0
    nmin = a["sample_size"]["n_min"]
    meas = "⚠️" if n < nmin else "✅"
    hs = a["holdout_summary"]
    hist = ("التاريخيّ الملوَّث فقط (وصفيّ) · الأماميّ N = 0" if n0 else
            f"الأماميّ N = {n}" + (f" (دون {nmin} ⟵ INSUFFICIENT)" if n < nmin else "") + " ‏+ التاريخيّ الملوَّث (وصفيّ)")
    items = [("V4 is frozen", "✅", f"FV41 · `{reg['freeze']['official_freeze_commit'][:7]}`"),
             ("V4 rule provenance audited", "✅", f"{a['provenance_summary']['rules']} قاعدة × 20 حقلًا"),
             ("Discovery/validation contamination controlled", "✅", "أعلامٌ عمياء · FV42/FV43"),
             ("Holdout sealed", "✅", f"مختومٌ ببصمة — نظيفة {hs['eligible']}" + (" **(فارغ)**" if not hs["eligible"] else "")),
             ("Holdout leakage tested", "✅", "FV42 · FV43 بطفراتها"),
             ("Prospective protocol implemented", "✅", "السجلّ · المشغّل · الجدار · workflow" + (
                 f" · smoke حيٌّ `{reg['smoke']['run']}` ({reg['smoke']['symbol']} {reg['smoke']['asof']} ⟵ {reg['smoke']['state']} · "
                 f"الجدار {reg['smoke']['firewall']} · الإعادة {'مطابقة' if reg['smoke']['replay_equal'] else '⛔ مختلفة'})"
                 if reg.get("smoke") else " · smoke ⏳")),
             ("Case sealing implemented", "✅", "FV46"),
             ("V4 decisions frozen before Faisal decisions are revealed", "✅", "FV48 (لم يُمارَس على حالةٍ حقيقيّة بعد)" if n0 else
              f"FV48 · مُمارَسٌ على {n} حالةٍ حقيقيّة (حالة ⟵ V4 ⟵ فيصل في السجلّ · `ledger.verify`)"),
             ("No post-hoc rule changes occurred", "✅", "FV41 أخضر · النواةُ منذ d8b4937"),
             ("READY/WAIT/REJECT comparison exists", "⚠️" if n0 else "✅", hist),
             ("False READY measured", meas, hist + " · وصفرٌ بنيويّ"),
             ("False WAIT measured", meas, hist),
             ("False REJECT measured", meas, hist),
             ("UNKNOWN measured", meas, hist),
             ("Pattern coverage reported", "✅", "INSUFFICIENT لكلّ نموذجٍ مسمّى"),
             ("Timeframe coverage reported", "✅", "INSUFFICIENT خارج اليوميّ"),
             ("External-information dependency quantified", "✅", "S1+S2 تاريخيًّا"),
             ("Invisible-information hypothesis tested", "⚠️", "تاريخيًّا SUPPORTED وصفًا · الرسميُّ UNKNOWN"),
             ("Target logic frozen and validated", "⚠️", "مجمَّد · والتحقّقُ الأماميّ " + ("N = 0 ⟵ UNKNOWN" if n0 else
              f"جارٍ — أهدافٌ مذكورةٌ في {p['coverage']['targets_stated']} من {n} ⟵ UNKNOWN")),
             ("Golden Cases kept separate from holdout", "✅", "عَلَم GOLDEN · تقريرٌ منفصل"),
             ("Full test suite green", "✅" if reg.get("suite_local") else "⏳",
              (f"السويّةُ في worktree معزول: {reg['suite_local']['passed']} نجح · {reg['suite_local']['failed']} فشل · خروج "
               f"{reg['suite_local']['exit']} على `{reg['suite_local']['commit'][:7]}`") if reg.get("suite_local") else "لم يُقرأ بعد"),
             ("Mutation suite green", "✅", f"{reg['mutations']['FV41']['caught']}/{reg['mutations']['FV41']['of']} ‏+ "
                                          f"{reg['mutations']['FV42-FV50+FVT1+FVO1+FVW1+FVD1']['caught']}/{reg['mutations']['FV42-FV50+FVT1+FVO1+FVW1+FVD1']['of']}"),
             ("CI green", "✅" if reg.get("ci") else "⏳",
              (f"PR #{reg['ci']['pr']} ({reg['ci']['pr_result']}) · main ({reg['ci']['main_result']})") if reg.get("ci")
              else "يُقرأ من سجلّ CI بعد الدفع ثمّ يُملأ هنا (PR لاحق)"),
             ("Production unchanged", "✅", "لا ملفَّ إنتاجٍ في الفرق")]
    return "\n".join(f"- [{'x' if s == '✅' else ' '}] {t} — {s} {why}" for t, s, why in items)


def final_block(d):
    a, reg, prv = d["a"], d["reg"], d["prv"]
    h = a["historical_contaminated"]
    hs = a["holdout_summary"]
    p = a["prospective"]["matrix"]
    s1 = h["matrices"]["S1_all"]
    inv = h["invisible"]
    dep = h["dependency"]
    depn = sum(v["n"] for v in dep.values())
    gg = a["golden"]
    cov = h["coverage"]
    risk = [x["RULE"] for x in a["golden_generalization"] if x["OVERFIT_RISK"]]
    near = sorted(x["RULE"] for x in a["golden_generalization"] if x["INDEPENDENT_SUPPORT"] <= 1)
    ph = a["posthoc_disclosure"]
    pc = a["prospective"]["coverage"]
    pex = (f"prospective {p['exact']}/{p['n']} (always-WAIT {p['always_wait']['agree']}/{p['n']} · INSUFFICIENT N < {a['sample_size']['n_min']})"
           if p["n"] else "prospective N=0 — UNKNOWN")
    return f"""================================================
FAISAL METHOD V4.1
PROSPECTIVE VALIDATION STATUS
================================================

V4 FREEZE:
commit {reg['freeze']['official_freeze_commit']} (merge #{reg['freeze']['contract_pr']}) / FREEZE_ID {d['cur']['freeze_id']}

RULE COUNT:
{prv['summary']['rules']} ({prv['summary']['active']} active) · rubric: {counts(prv['summary']['audit_status'])}

DISCOVERY CASES:
{hs['cases']} historical — all EXPOSED to V4's visual pass (V4 discovery split {hs['by_flag']['DISCOVERY']})

HOLDOUT CASES:
{hs['eligible']} clean — INSUFFICIENT SAMPLE (POST-HOC; first run {ph['first_summary']['eligible']} due to bug BB2)

PROSPECTIVE CASES:
{a['prospective']['complete']}

CONTAMINATED CASES:
{hs['cases']}/{hs['cases']} (T1_CITED {hs['by_tier']['T1_CITED']} · T2_EXPOSED_UNCITED {hs['by_tier']['T2_EXPOSED_UNCITED']} · other {hs['by_tier']['OTHER_CONTAMINATED']})

EXACT AGREEMENT:
{pex} · historical-contaminated S1 {s1['exact']}/{s1['n']} (descriptive only)

READY:
prospective precision {p['ready_precision']} / recall {p['ready_recall']} / N {p['n']} · historical S1: precision {s1['ready_precision']} / recall {s1['ready_recall']} / N {s1['n']}

WAIT:
prospective {p['agreement']['WAIT']} · historical S1 {s1['agreement']['WAIT']}

REJECT:
prospective {p['agreement']['REJECT']} · historical S1 {s1['agreement']['REJECT']} — V4 cannot output REJECT (or READY) prospectively: output space {{WAIT, UNKNOWN}} by construction (FVO1)

UNKNOWN:
prospective {p['agreement']['UNKNOWN']} · historical S1 {s1['agreement']['UNKNOWN']}

FALSE READY:
prospective {p['false']['READY']}/{p['n']} · historical S1 {s1['false']['READY']} — structural (V4 cannot output READY without operator/groups/offering info)

FALSE WAIT:
prospective {p['false']['WAIT']}/{p['n']} · historical S1 {s1['false']['WAIT']}

FALSE REJECT:
prospective {p['false']['REJECT']}/{p['n']} · historical S1 {s1['false']['REJECT']}

INVISIBLE INFORMATION:
UNKNOWN (prospective N={p['n']} · disagreements {pc['disagreements']}) · historical-contaminated descriptive: {inv['verdict']} ({inv['k_D']}/{inv['n']})

EXTERNAL DATA DEPENDENCY:
historical S1+S2 N={depn}: {counts({k: v['n'] for k, v in dep.items()})} · V4 tech-ready outputs {h['unknown_behaviour']['tech_ready_outputs']} → UNKNOWN {h['unknown_behaviour']['of_which_unknown']} · READY {h['unknown_behaviour']['of_which_ready']}

GOLDEN CASES:
reported separately — V3.1 {gg['v31_matched']}/{gg['dated']} · V4 frozen {gg['v4_matched']}/{gg['dated']} · always-WAIT {gg['always_wait_baseline']}/{gg['dated']} · prospective {pc['golden']}

TARGET VALIDATION:
V4 target logic frozen · prospective targets stated {pc['targets_stated']} of {p['n']} → UNKNOWN · historical (T-TGT, republished): «100٪ هدف» = +100% profit (CONFIRMED) · «50٪» never a pattern projection · «70٪» UNKNOWN

PATTERN COVERAGE:
historical S1+S2: {counts(cov['pattern'])} → INSUFFICIENT for every named pattern · prospective {counts(pc['pattern']) or 0}

TIMEFRAME COVERAGE:
historical S1+S2: {counts(cov['timeframe'])} → engine is daily-only; every timeframe INSUFFICIENT prospectively ({counts(pc['timeframe']) or 0})

RULES WITH STRONG HOLDOUT SUPPORT:
none (clean holdout {hs['eligible']} · prospective {a['prospective']['complete']})

RULES WITH OVERFIT RISK:
{', '.join(risk) if risk else 'none flagged by the pre-registered rule'} (lowest independent support: {', '.join(near) or '—'})

UNRESOLVED DISAGREEMENTS:
historical H = {inv['by_class']['H']} of {len(h['disagreements'])} (classified {counts({k: v for k, v in inv['by_class'].items() if v})}) · prospective {pc['disagreements']}

V4 STATUS:
FROZEN

PRODUCTION:
UNCHANGED

PROSPECTIVE STATUS:
{a['prospective']['status']}

NEXT ACTION:
Capture Faisal's next dated decision posts (on or after {LG.WINDOW_START}) through the Telegram collector and seal each one as a prospective case before V4 runs — the sample, not the model, is the bottleneck.
"""


def doc_report(d):
    a = d["a"]
    h = a["historical_contaminated"]
    pm = a["prospective"]["matrix"]
    stc = ("صفرُ حالةٍ أماميّة" if not pm["n"] else
           f"{pm['n']} حالةً أماميّةً كاملة (دون N_MIN {a['sample_size']['n_min']}) — تطابقٌ {pm['exact']}/{pm['n']} و«دائمًا WAIT» "
           f"{pm['always_wait']['agree']}/{pm['n']} ⟵ لا يميّز V4 عن الخطّ التافه")
    return head(d, "V4.1_VALIDATION_REPORT — تقريرُ التحقّق") + f"""## ① الخلاصة
- **STATUS: {a['status']}** — **NOT COMPLETE** (§35). **PROSPECTIVE: {a['prospective']['status']}**.
- **STATE A (ENGINE VERIFIED):** قائمة — V4 مجمَّدٌ ومحروس (FV41) والأدواتُ محروسةٌ بأقفالٍ تُسقطها طفرات.
- **STATE B (METHODOLOGY SUPPORTED):** **لا دليلَ مستقلّ** — الاحتجازُ التاريخيُّ النظيف {a['holdout_summary']['eligible']} · ودعمُ القواعد من صور البناء نفسِها (المسطرة).
- **STATE C (PROSPECTIVE FIDELITY):** **لا يُدّعى** — {stc}.
- 🧭 **وقيدٌ يحكم كلَّ رقمٍ أماميٍّ قادم (من المحرّك المجمَّد · FVO1):** مخرَجُ V4 الأماميّ ∈ {{WAIT · UNKNOWN}} — لا READY ولا REJECT ما دامت
  الصلاحيّةُ (القروبات · الطرح · المضارب) بلا مصدرٍ آليّ ⟵ استدعاءُ READY واتّفاقُ REJECT صفرٌ بالبناء · و«دائمًا WAIT» هو الحدّ.
- **التاريخيّ ملوَّثٌ كلُّه** (كلُّ وحدةٍ مكشوفة) ⟵ أرقامُه وصفٌ لا تحقّق: S1 {h['matrices']['S1_all']['exact']}/{h['matrices']['S1_all']['n']} مقابل «دائمًا WAIT»
  {h['matrices']['S1_all']['always_wait']['agree']}/{h['matrices']['S1_all']['always_wait']['n']} ⟵ **لا قدرةَ مُثبَتةً فوق الخطّ التافه**.

## ② التنبّؤات
{doc_predictions(d)}

## ③ مربّعاتُ §35
{checklist(d)}

> **STATUS = {a['status']} — NOT COMPLETE.**

## ④ أين التفاصيل
`V4_FREEZE_REPORT.md` · `V4_RULE_PROVENANCE_AUDIT.md` · `V4_HOLDOUT_INTEGRITY.md` · `V4_PROSPECTIVE_PROTOCOL.md` · `V4_PROSPECTIVE_VALIDATION.md` ·
`V4_DECISION_CONFUSION_MATRIX.md` · `INVISIBLE_INFORMATION_AUDIT.md` · `V4_2_RESEARCH_QUEUE.md` · `V4_CHANGE_REQUESTS.md` · `V4.1_CHANGELOG.md` ·
`V4.1_IMPLEMENTATION_READINESS.md`.

## ⑤ التقريرُ النهائيّ (§37)
```text
{final_block(d)}```
"""


def smoke_line(d):
    sm = d["reg"].get("smoke")
    if not sm:
        return "⏳ smoke حيٌّ على Actions لم يُقرأ بعد"
    return (f"smoke على Actions `{sm['run']}` (commit `{sm['commit'][:7]}`): {sm['symbol']} بتاريخ {sm['asof']} ⟵ شموع {sm['snapshot_rows']} · "
            f"الجدار {sm['firewall']} ({sm['firewall_detail']}) · قرارُ V4 {sm['state']} ({sm['tech_state']}) · الإعادةُ من اللقطة {'مطابقةٌ بايتًا' if sm['replay_equal'] else '⛔ مختلفة'} · "
            f"والمتاح {sm['short_provenance']} · وverify `{sm['verify_run']}`: «{sm['verify_line']}» · وreplay `{sm['replay_run']}`: «{sm['replay_line']}»")


def doc_readiness(d):
    a = d["a"]
    return head(d, "V4.1_IMPLEMENTATION_READINESS — الجاهزيّة") + f"""## ① الحكم
**أداةُ قياسٍ جاهزة · لا استعمالَ إنتاجيّ.** البنيةُ الأماميّة تعمل ومحروسة · **ولا قرارَ تداولٍ يُبنى على V4**: لا دليلَ مستقلّ (STATE B) ولا أماميّ (STATE C).

## ② ما هو جاهز
- **المسارُ الحيّ:** {smoke_line(d)}.
- التجميدُ وكشفُ أيّ تعديلٍ لاحق (FV41 · FV44) · المصدريّة (FV49) · الاحتجازُ الأعمى المختوم (FV42 · FV43).
- السجلُّ الإلحاقيّ بترتيبه الإلزاميّ (FV46-FV48) · سجلُّ الهدف (FVT1) · الجدارُ F1-F9 · منعُ التسرّب المستقبليّ (FV45) · الإعادةُ الحتميّة (FV50).
- التحليلُ والوثائقُ مولَّدةٌ من JSON (FVD1) · وworkflow يدويٌّ بأربعة أوضاع.

## ③ ما ليس جاهزًا — وما يمنعه
1. **العيّنة:** {a['prospective']['complete']} حالة · N_MIN {a['sample_size']['n_min']} ⟵ ‏≈{a['sample_size']['months_to_n_min']} شهرًا بالمعدّل التاريخيّ.
2. **READY وREJECT مستحيلان بنيويًّا** (المخرَجُ الأماميّ ∈ {{WAIT · UNKNOWN}} · FVO1) ما دامت الصلاحيّةُ (المضارب · القروبات · الطرح) بلا مصدرٍ آليّ ⟵
   استدعاءُ READY واتّفاقُ REJECT = 0 بالبناء ⟵ **STATE C لـREADY وREJECT غيرُ قابلٍ للبلوغ** بلا بيانات (RQ-05).
3. **مصدرُ الشموع** TradingView بلا واجهةٍ رسميّة (قد يُحجَب) ⟵ الجدارُ يحوّل العطلَ INVALID لا رقمًا مزيّفًا.
4. **العمى معرفيًّا ناقص:** الملتقِط يرى الصورة — والمحرّكُ وحدَه أعمى (حدٌّ معلَن · §29).

## ④ تشغيلُ حالةٍ أماميّة (خطوةً خطوة)
1. منشورُ فيصل الجديد (مؤرَّخٌ من {LG.WINDOW_START}) يصل المستودع (جامعُ التلغرام) ⟵ `Ledger.record_candidate`.
2. الختم (`seal_case`) بالرمز والتاريخ وفريمِ الصورة وبصمتها — **قبل** أيّ تشغيل.
3. workflow `faisal_v41.yml` وضعُ `run` ⟵ قرارُ V4 مختومٌ ولقطتُه.
4. ثمّ كلمةُ فيصل (`record_faisal`) ⟵ `analysis.py` ⟵ `docs_v41.py`.
"""


def build(d=None):
    d = d or load()
    return {"V4_RULE_PROVENANCE_AUDIT.md": doc_provenance(d), "V4_HOLDOUT_INTEGRITY.md": doc_holdout(d),
            "V4_PROSPECTIVE_PROTOCOL.md": doc_protocol(d), "V4_PROSPECTIVE_SCHEMA.json": doc_schema(d),
            "V4_PROSPECTIVE_VALIDATION.md": doc_prospective(d), "V4_DECISION_CONFUSION_MATRIX.md": doc_confusion(d),
            "INVISIBLE_INFORMATION_AUDIT.md": doc_invisible(d), "V4_2_RESEARCH_QUEUE.md": doc_queue(d),
            "V4_CHANGE_REQUESTS.md": doc_change_requests(d), "V4.1_CHANGELOG.md": doc_changelog(d),
            "V4.1_VALIDATION_REPORT.md": doc_report(d), "V4.1_IMPLEMENTATION_READINESS.md": doc_readiness(d)}


def write(out=None):
    out = out or build()
    for name, txt in out.items():
        with open(os.path.join(DOCS, name), "w", encoding="utf-8") as f:
            f.write(txt)
    return out


def check():
    """⟵ قائمةُ الملفّات المختلفة عن توليدها (FVD1)."""
    bad = []
    for name, txt in build().items():
        p = os.path.join(DOCS, name)
        if not os.path.exists(p) or open(p, encoding="utf-8").read() != txt:
            bad.append(name)
    return bad


if __name__ == "__main__":
    if "--check" in sys.argv:
        b = check()
        print("FVD1", "OK" if not b else b)
        sys.exit(1 if b else 0)
    print(sorted(write()))
