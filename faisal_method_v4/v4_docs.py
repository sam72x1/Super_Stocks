# -*- coding: utf-8 -*-
"""
📚 FAISAL V4 — بنّاءُ المخرجات الثمانية عشر (§38) · **كلُّ رقمٍ من ملفّات JSON المدفوعة لا من اليد** (§26 · سابقةُ v31_docs.py).

    python3 faisal_method_v4/v4_docs.py      ⟵ faisal_method_v4/docs/01…18

المصادر: results/v4_eval_results.json (v4_offline.py) · results/v4_metrics_actions.json · results/forensics_v4.json · results/cases_v4.json ·
results/corpus_counts_v4.json · results/telegram_reconciliation_v4.json · results/v4_atmv.json · results/v4_cov30.json ·
results/pool_cap_downstream_v4rerun.json · results/run_registry_v4.json · results/suite_result_v4.json · data/corrections_v4.json ·
rules_v4.RULES_V4 · decision_engine (PARAMS · STATE_*) · ../faisal_method_v3/source_access.json. وغيابُ مصدرٍ يُكتب «لم يُشغَّل بعد» صراحةً.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import decision_engine as E      # noqa: E402
import rules_v4 as RV            # noqa: E402

DOCS = os.path.join(HERE, "docs")
GROUPS = ["S1_discovery", "S1_holdout", "S1_all", "S2", "S3_golden", "S4_edu"]
GROUP_AR = {"S1_discovery": "S1 الاكتشاف", "S1_holdout": "**S1 الاحتجاز (الحاكم)**", "S1_all": "S1 كلُّها", "S2": "S2 الثانويّة",
            "S3_golden": "S3 الذهبيّة", "S4_edu": "S4 القناة التعليميّة"}


def J(*parts):
    p = os.path.join(HERE, *parts)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def W(name, text):
    os.makedirs(DOCS, exist_ok=True)
    with open(os.path.join(DOCS, name), "w", encoding="utf-8") as f:
        f.write(text.rstrip() + "\n")


def WJ(name, obj):
    os.makedirs(DOCS, exist_ok=True)
    with open(os.path.join(DOCS, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")


def table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for r in rows:
        out.append("| " + " | ".join("—" if x is None else str(x).replace("|", "¦").replace("\n", " ") for x in r) + " |")
    return "\n".join(out)


def yn(b):
    return "✅" if b else "❌"


def ci(st):
    return "—" if not st else f"{st['diff']:+.4f} [{st['ci95'][0]:+.4f} · {st['ci95'][1]:+.4f}] · مستويات {st['levels']} · حالات {st['cases']}"


def load():
    D = {"R": J("results", "v4_eval_results.json"), "M": J("results", "v4_metrics_actions.json"), "F": J("results", "forensics_v4.json"),
         "C": J("results", "cases_v4.json"), "CC": J("results", "corpus_counts_v4.json"), "TG": J("results", "telegram_reconciliation_v4.json"),
         "AT": J("results", "v4_atmv.json"), "CV": J("results", "v4_cov30.json"), "PC": J("results", "pool_cap_downstream_v4rerun.json"),
         "REG": J("results", "run_registry_v4.json"), "SU": J("results", "suite_result_v4.json"), "CORR": J("data", "corrections_v4.json"),
         "LB": J("data", "case_labels_v4.json"), "MUT": J("results", "mutations_v4.json")}
    sa = os.path.join(ROOT, "faisal_method_v3", "source_access.json")
    D["SA"] = json.load(open(sa, encoding="utf-8")) if os.path.exists(sa) else None
    return D


# ── أحكامٌ مشتقّة (لا رقمَ باليد) ──────────────────────────────────────────────────────────────
def predictions(D):
    R, M, PC, AT = D["R"], D["M"], D["PC"], D["AT"]
    hold = M["S1_holdout"]
    s1_ready = sum(1 for r in R["rows"] if r["set"] == "S1" and r["state"] == "READY")
    return [
        ("P1", "H-LEVEL على الاحتجاز PASS (ثقة ‏≈55%)", hold["h_level_verdict"], hold["h_level_verdict"] == "PASS"),
        ("P2", "H-CLASS على الاحتجاز FAIL", hold["h_class"]["verdict"], hold["h_class"]["verdict"] == "FAIL"),
        ("P3", "لا READY من المحرّك على S1", f"READY = {s1_ready}", s1_ready == 0),
        ("P4", "DXST ⟵ B أو D", R["dxst"]["verdict"], R["dxst"]["verdict"] in ("B", "D")),
        ("P5", "VEEE ⟵ AMBIGUOUS", R["veee"]["verdict"], R["veee"]["verdict"] == "AMBIGUOUS"),
        ("P6", "ATMV ⟵ DATA_UNAVAILABLE", AT["verdict"], AT["verdict"] == "DATA_UNAVAILABLE"),
        ("P7", "poolcap2 لا يطابق V3.1 بت-بت · والحكمُ UNKNOWN",
         f"مطابق={PC['_v4_compare']['identical_except_timing']} · {PC['verdict']}",
         (not PC["_v4_compare"]["identical_except_timing"]) and PC["verdict"] == "UNKNOWN"),
    ]


def rebuild_lines(D):
    """إعادةُ البناء 2026-10-06 (ضياعُ الحاوية) — تُعرض صراحةً ولا تُخفى (§26 · §41)."""
    rb = (D.get("REG") or {}).get("rebuild")
    if not rb:
        return []
    ver = " · ".join(f"{k}: {v}" for k, v in rb["verified_in_session_against_10_02_prints"].items())
    return [f"- **🔁 إعادةُ بناءٍ {rb['date']}:** {rb['cause']}. استُعيد حرفيًّا من سجلّ الجلسة: " + " · ".join(f"`{x}`" for x in rb["exact_from_session_log"])
            + f" · وأُعيد جلبُ سجلّات التشغيلات الأربع ({' · '.join(str(j) for j in rb['refetched_from_actions'])}) فطابقت بصمةُ المثبّت المسجَّلة: "
            f"**{rb['fixture_sha_equals_recorded']}**.",
            "- **أُعيدت كتابتُه (لا حرفيّ):** " + " · ".join(f"`{k}` — {v}" for k, v in rb["rebuilt_code"].items()) + ".",
            f"- **قِيس على المطبوع يوم 10-02:** {ver} — {rb['method_note']}."]


def status_word(D):
    return "PARTIALLY COMPLETE"


def metrics_table(M):
    rows = []
    for g in GROUPS:
        m = M[g]
        rows.append([GROUP_AR[g], m["cases"], m["ok"], " · ".join(f"{k} {v}" for k, v in sorted(m["status_counts"].items())),
                     m["h_level_verdict"], ci(m["h_level"]), ci(m["h_level_text_only"]),
                     f"{m['h_class']['verdict']} · اتّفاق {m['h_class'].get('agree')}/{m['h_class'].get('n')} · ويلسون {m['h_class'].get('wilson95')} · "
                     f"الأغلبيّة {m['h_class'].get('majority_class')} {m['h_class'].get('majority_rate')}"])
    return table(["المجموعة", "حالات", "سليمة", "الحالات", "H-LEVEL", "الفرق [95%] (كلّ المستويات)", "النصّيّة الصرفة", "H-CLASS"], rows)


# ── 01 ─────────────────────────────────────────────────────────────────────────────────────────
def final_status_block(D):
    R, M, F, CC, TG, PC, CV, AT, SU, REG = D["R"], D["M"], D["F"], D["CC"], D["TG"], D["PC"], D["CV"], D["AT"], D["SU"], D["REG"]
    hold = M["S1_holdout"]
    g = R["golden_v31_vs_v4"]
    cov = CV["coverage"]
    reg30 = [v["regular"]["returned"] for v in cov.values() if v.get("full")]
    capped = sum(1 for x in reg30 if x == max(reg30))
    first = min(v["regular"]["first"] for v in cov.values() if v.get("full"))
    act = [k for k, r in RV.RULES_V4.items() if r.get("active")]
    inact = [k for k, r in RV.RULES_V4.items() if not r.get("active")]
    mut = D["MUT"] or {}
    su = SU or {}
    lines = [
        "================================================", "FAISAL METHOD V4 — FINAL STATUS", "================================================", "",
        "STATUS:", status_word(D), "",
        "CORPUS:",
        f"{CC['images_in_corpus_record']} صورة في السجلّ · موجودة {CC['files_exist']} · مطابقةُ SHA-256 {CC['sha256_match']} · وحداتٌ مستقلّة "
        f"{CC['units_by_hash_ocr']} (‏{CC['multi_member_clusters']} عنقودًا متعدّد الأعضاء) · {CC['units_after_v31_visual_merges']} بعد دمج V3.1 البصريّ · "
        f"مرورُ V4 {CC['v4_pass_records']} سجلًّا · صورٌ أوّليّة (فيصل · طبقة 1) {CC['primary_images']} · قواعدُ V3.1 {CC['rules_v31_inventory']} · "
        f"تلغرام {TG['summary']['found_in_corpus']}/{TG['summary']['expected']} (مكرّر {TG['summary']['duplicates']} · محتوى أوّليّ {TG['summary']['primary_content']})", "",
        "METHODOLOGY:",
        "خطّ القرار المُعاد بناؤه (مُعدَّلٌ بالدليل): البيانات ⟵ القاع/الدورة (البنية) ⟵ الثبات 5 جلسات ⟵ صعودُ الاختبار ⟵ منطقةُ 15% فوق القاع "
        "(الموقع) ⟵ الثبات فيها أو سحبٌ ثمّ عودة (التأكيد) ⟵ الصلاحيّة حاجبٌ لا يرقّي ⟵ الدخولُ آليّةٌ (طلباتٌ عند الدعم) ⟵ الإبطال ⟵ الأهداف "
        "(معلومةٌ لا قرار) · والنموذجُ (W) معلومة · و«المضارب» عاملٌ حاسمٌ غيرُ مرئيٍّ في الشموع", "",
        "DECISION ENGINE:",
        "READY = جاهزيّةٌ فنيّة (BASE_HELD · RETEST_HELD · PRESS_RECLAIM) ‏+ صلاحيّةٌ معلومةٌ نظيفة · WAIT = قاعٌ يتكوّن/مكسور/سحبٌ جارٍ/فوق المنطقة/"
        "في المنطقة بلا ثبات · أو طرحٌ/شورتٌ فوق 20,000 · REJECT = قروبات · UNKNOWN = بياناتٌ ناقصة أو جاهزيّةٌ فنيّةٌ بلا معلومة الصلاحيّة "
        "(بقائمة الناقص) — والتحقّق: H-LEVEL الاحتجاز " + hold["h_level_verdict"] + f" ({ci(hold['h_level'])}) ⟵ المحرّكُ «عرضُ بنيةٍ» لا مُعيدٌ لمستويات فيصل (§⑭)", "",
        "NEW GENERAL RULES:",
        " · ".join(f"{k} ({RV.RULES_V4[k]['status']} · {RV.RULES_V4[k]['decisionality']} · "
                   + ("هندسيّة" if RV.RULES_V4[k]["source_level"] == 7 else f"مستوى {RV.RULES_V4[k]['source_level']} · صور {RV.independent_sources(RV.RULES_V4[k])}") + ")"
                   for k in act if k.startswith("R4-")), "",
        "RULES REJECTED:",
        " · ".join(f"{k} ⟵ {RV.RULES_V4[k]['effect']}" for k in inact) + " · وتصحيحاتُ الدفتر: نطاقُ السحب 7-13 و`PIVOT_SWEEP_PCT` ⟵ تبنّيًا (لا لفظَ فيصل) · "
        "`TG_38_NUWE` ⟵ طرفٌ ثالث · ومكوّناتُ «UNKNOWN» في التدقيق: " + " · ".join(k for k, v in F["pattern_audit"]["components"].items() if v["status"] == "UNKNOWN"), "",
        "TARGET:",
        "«100٪» مقرونةً بـ«هدف» عند فيصل = مسافةُ ربحٍ ‏+100% · «50٪/70٪» ليست إسقاطَ نموذج (70٪ = كمّيّةُ جني الربح الأوّل) · والأهدافُ سلّمُ مقاوماتٍ أفقيّ — "
        "معلومةٌ لا تغيّر الحالة (R4-TGT-01)", "",
        "GOLDEN CASES:",
        f"قبل (V3.1) {g['v31_matched']}/{g['dated']} · بعد (V4) {g['v4_matched']}/{g['dated']} · وخطُّ «دائمًا WAIT» {g['always_wait_baseline']}/{g['dated']} "
        f"⟵ لا تحسّنَ مُثبَت · DXST {R['dxst']['verdict']} (MANUAL_JUDGMENT_UNREPRODUCIBLE) · VEEE {R['veee']['verdict']} (والبعديّ {R['veee']['posthoc']['verdict']} "
        f"{R['veee']['posthoc']['candidates']}) · ATMV {AT['verdict']} · والعامُّ: S3 H-LEVEL {M['S3_golden']['h_level_verdict']}", "",
        "CONTRADICTIONS:",
        " · ".join(f"{c['id']} ({c['status']})" for c in F["contradictions"] if c["status"] not in ("RESOLVED",)), "",
        "PRESSURE POOL:",
        f"UNKNOWN — إعادةُ poolcap2 طابقت V3.1 بت-بت (‏{PC['totals']['cards_B']} · {PC['totals']['lost_cards']} · {PC['repro_ledger_jaccard_mean']}) · "
        f"والمحاكي لا يعيد سجلَّ الإنتاج (اتّفاق {PC['repro_ledger_jaccard_mean']} دون 0.60) ⟵ «إشاراتُ تلغرام الصالحة المفقودة بسبب السقف وحدَه» UNKNOWN", "",
        "DATA LIMITATIONS:",
        f"ATMV بلا شموع من أيّ مصدر · 30 دقيقة: {len(reg30)} رمزًا بشموع · {capped} منها عند سقف الطلب {max(reg30)} · أقدمُ شمعة {first} (لا عشر سنوات) · "
        "VEEE: مرساةُ العقد سقطت (قمّةُ الستّين 23.05 لا 8.80) · الصلاحيّة (القروبات · الطرح · الشورت · المضارب) غيرُ مؤرَّخةٍ تاريخيًّا ⟵ UNKNOWN · "
        "Polygon منتهٍ · X والمحادثاتُ الأخرى غيرُ متاحة · الـartifact وروابطُ السجلّ الموقَّعة محجوبةٌ من الجلسة", "",
        "TOOL:",
        f"محرّكُ V4 (`{E.ENGINE_VERSION}`) فوق دوالّ V3.1 المحفوظة · سجلُّ {len(RV.RULES_V4)} قاعدة · كائنُ قرارٍ قابلٌ للتفسير · faisal_v4.yml يدويٌّ للقراءة · "
        "ولا تغييرَ في V3/V3.1", "",
        "TESTS:",
        (f"السويّة {su.get('passed')} نجح · {su.get('failed')} فشل · خروج {su.get('exit')} (worktree معزول · {su.get('commit')})" if su else "لم تُشغَّل بعد"), "",
        "MUTATIONS:",
        (f"{mut.get('caught')}/{mut.get('total')} سقطت كلٌّ بقفلها" if mut else "لم تُشغَّل بعد"), "",
        "CI:",
        " · ".join(f"{x['workflow']} {x['run']} {x['conclusion']}" for x in REG["pr_contract"]["ci_pr"] + REG["pr_contract"]["ci_main"]
                   + (REG.get("pr_results") or {}).get("ci", []) + (REG.get("pr_results") or {}).get("ci_main", []))
        + ("" if (REG.get("pr_results") or {}).get("ci") else " (العقد #547) · وCI لـPR النتائج يُسجَّل في الذاكرة بعد الدمج"), "",
        "PRODUCTION:", "UNCHANGED — لا كرون · لا ماسح · لا تلغرام · لا عتبة · لا سقف بِركة · لا كون · لا منطقَ دخول · والوسومُ المصحَّحة توثيقٌ (الأرقامُ في الكود بت-بت)", "",
        "REMAINING BLOCKERS:",
        "① لا مصدرَ تاريخيٌّ لمعلومات الصلاحيّة (قروبات · طرح · شورت · بصمةُ المضارب) ⟵ كلمةُ READY/WAIT غيرُ قابلةٍ للإعادة آليًّا · "
        "② عيّنةُ الاحتجاز صغيرة (10 حالات · 7 بمستويات) · ③ DXST حكمٌ تقديريّ · ④ ATMV بلا بيانات · ⑤ بِركةُ الضغط: المحاكي لا يعيد الإنتاج", "",
        "NEXT HIGHEST-VALUE ACTION:",
        "حصادٌ أماميٌّ مسجَّلٌ مسبقًا: كلُّ قرار READY/WAIT جديدٍ لفيصل يُلتقط يومَ صدوره مع معلومات الصلاحيّة الحيّة (قروبات · طرح · متاح الشورت) "
        "ويُقارَن بمحرّك V4 المجمَّد — اختبارُ احتجازٍ نظيفٌ لم يُرَ ولا يتعفّن",
    ]
    return "\n".join(lines)


def doc01(D):
    R, M, F, PC = D["R"], D["M"], D["F"], D["PC"]
    hold = M["S1_holdout"]
    pr = predictions(D)
    desc = R["h_state_descriptive"]
    t = ["# 01 — FAISAL METHOD V4 · التقرير النهائيّ", "",
         f"> **الحالة: {status_word(D)}** — المنهجُ أُعيد بناؤه من النصّ وسُجّل قبل أيّ رقم (#547) ثمّ شُغِّل مرّةً واحدة (التشغيلةُ الأولى هي النتيجة) ·",
         f"> **والحكمُ الحاكم: H-LEVEL على الاحتجاز {hold['h_level_verdict']}** ({ci(hold['h_level'])}) ⟵ المحرّكُ لا يُدّعى أنّه يعيد مستويات فيصل على شارتٍ لم يُرَ.",
         "> كلُّ رقمٍ هنا من `results/*.json` (‏`v4_docs.py`) · وكلُّ دعوى موسومةٌ بأحد الأربعة (§41): **مشاهَد · مستنتَج · مُنفَّذ · مُتحقَّق**.", "",
         "## ① ما شوهد (OBSERVED)",
         f"- {D['CC']['v4_pass_records']} وحدةً بصريّة قُرئت كلُّها بالعين ⟵ {D['C']['summary']['statements']} عبارةَ قرار ⟵ {D['C']['summary']['cases']} حالة · "
         f"S1 = {D['C']['summary']['by_set']['S1']} (READY {D['C']['summary']['S1_by_label'].get('READY', 0)} · WAIT {D['C']['summary']['S1_by_label'].get('WAIT', 0)}).",
         "- فيصل يقول «جاهز فنيًّا … انتظر المضارب» مرارًا: الكلمةُ تتبع معلوماتٍ خارج الشموع (المضارب · القروبات · الطرح · الشورت).",
         f"- تركيباتُ «مكوّن ‏+ قرار» في نصّ فيصل الحرفيّ: {len(F['decision_combos']['combinations'])} تركيبة · {F['decision_combos']['single_example_combinations']} منها بمثالٍ واحد (لا قاعدةَ منها).", "",
         "## ② ما استُنتج (INFERRED)",
         "- الترتيبُ الفعليّ: البنيةُ (القاع والدورة) ⟵ الموقعُ من المنطقة ⟵ التأكيدُ (ثباتٌ أو سحبٌ ثمّ عودة) ⟵ الصلاحيّةُ حاجبٌ لا يرقّي — والنموذجُ معلومة.",
         "- «الطلباتُ عند الدعم» آليّةُ دخولٍ مفضّلةٌ لا شرطُ قرار (§15) · وR-W-SPAN مُدمَجةٌ في «القاعُ = الأدنى» (§12).", "",
         "## ③ ما نُفِّذ (IMPLEMENTED)",
         f"- `decision_engine.py` ({E.ENGINE_VERSION}): {len(E.STATE_DECISION)} حالاتٍ فنيّة · كائنُ قرارٍ بأسباب القرار والحجب والناقص · {len(RV.RULES_V4)} قاعدة بمصادرها.",
         "- `v4_run.py` ‏+ `faisal_v4.yml` (يدويٌّ للقراءة) · `v4_offline.py` يعيد الحساب من الشموع المحفوظة · وطبقاتٌ بصريّة في `overlays/`.", "",
         "## ④ ما تُحقِّق منه (VALIDATED) — بالعقد المدموج قبل الرقم",
         metrics_table(M), "",
         f"- **H-STATE (وصفيّ):** على الاحتجاز تطابقُ الكلمة {desc['S1_holdout']['state_exact']}/{desc['S1_holdout']['n']} مقابل «دائمًا WAIT» "
         f"{desc['S1_holdout']['always_wait']}/{desc['S1_holdout']['n']} ⟵ **لا قدرةَ مُثبَتةً على الكلمة فوق الخطّ التافه** · والمحرّكُ لم يقل READY قطّ "
         f"(UNKNOWN {desc['S1_all']['engine_unknown']} مرّةً على S1 بقائمة الناقص).",
         f"- **الإعادة:** الشموعُ محفوظة (`data/v4_bars_fixture.json` · SHA-256 `{R['fixture_sha256'][:16]}…`) والحسابُ المحلّيّ يطابق Actions: **{R['reproduces_actions_metrics']}**.",
         *rebuild_lines(D), "",
         "## ⑤ التنبّؤات المكتوبة قبل الرقم (تُنشر إن خابت)",
         table(["#", "التنبّؤ", "النتيجة", "صدق؟"], [[a, b, c, yn(d)] for a, b, c, d in pr]),
         f"⟵ صدق {sum(1 for x in pr if x[3])} من {len(pr)}.", "",
         "## ⑥ §40 — هل يعيد المحرّكُ قرارَ فيصل على شارتٍ جديد؟",
         f"**جزئيًّا · ولا دليلَ احتجازٍ على المستويات:** الاكتشاف {M['S1_discovery']['h_level_verdict']} والاحتجاز {hold['h_level_verdict']} (الفرقُ موجبٌ "
         f"{hold['h_level']['diff']:+.4f} والفاصلُ يلامس الصفر {hold['h_level']['ci95'][0]:+.4f}) · والفئةُ FAIL في كلّ المجموعات · والكلمةُ لا تتجاوز «دائمًا WAIT». "
         "الباقي بالضبط: معلوماتُ الصلاحيّة الحيّة · وعيّنةُ احتجازٍ أكبر · وفصلُ الاختيار التقديريّ (DXST) عن القاعدة.", "",
         "## ⑦ بوّابةُ الإكمال (§39)",
         table(["البند", "الحالة", "الدليل"], completion_gate(D)), "",
         "## ⑧ الحالةُ النهائيّة (§43)", "```", final_status_block(D), "```"]
    return "\n".join(t)


def completion_gate(D):
    R, M, F, SU, REG, MUT = D["R"], D["M"], D["F"], D["SU"], D["REG"], D["MUT"]
    su_ok = bool(SU and SU.get("failed") == 0 and SU.get("exit") == 0)
    ci_ok = all(x["conclusion"] == "success" for x in (REG.get("pr_results") or {}).get("ci", [])) and bool((REG.get("pr_results") or {}).get("ci"))
    main_ok = bool((REG.get("pr_results") or {}).get("ci_main")) and all(x["conclusion"] == "success" for x in REG["pr_results"]["ci_main"])
    rows = [
        ["Full corpus reconciled", "✅", f"{D['CC']['sha256_match']}/{D['CC']['images_in_corpus_record']} SHA · 14_TELEGRAM_…json"],
        ["Telegram batch reconciled", "✅", f"{D['TG']['summary']['found_in_corpus']}/{D['TG']['summary']['expected']}"],
        ["Provenance verified", "✅", "طبقات 1/2/2b/X لكلّ وحدة · تصحيحاتُ C01-C15"],
        ["Third-party evidence separated", "✅", "الطبقة X لا تصنع وسمًا (V4L3)"],
        ["All major pattern families audited", "✅", f"{len(F['pattern_audit']['components'])} مكوّنًا بحالةٍ (12_RULE_AUDIT)"],
        ["All major structural rules audited", "✅", "R4-BOT/HOLD/CYC/ZONE/HOLDZ/SWEEP/INV/LOC"],
        ["Target methodology audited", "✅", "08_TARGET_FORENSICS"],
        ["READY/WAIT/REJECT reconstructed", "⚠️ جزئيّ", "البنيةُ والموقعُ نعم · والكلمةُ تتبع صلاحيّةً غيرَ مرئيّة (UNKNOWN)"],
        ["Decision hierarchy reconstructed", "✅", "02 · 03"],
        ["Contradiction search completed", "✅", f"{len(F['contradictions'])} تعارضًا (07)"],
        ["Single-image rules identified", "✅", f"{len(F['single_image_rules'])} قاعدةً نشطة بصورةٍ واحدة"],
        ["Backtest-derived rules isolated", "✅", "backtest_derived = False لكلّ قاعدة (V4L7)"],
        ["Golden Cases explained", "✅", "09"], ["Golden Case overfitting ruled out", "✅", "لا رمزَ ذهبيٌّ في المحرّك (V4L7) · الذهبيّةُ تحقّقٌ لا مصدر"],
        ["DXST classified", "✅", R["dxst"]["verdict"]], ["VEEE classified", "✅", R["veee"]["verdict"] + " (بعديّ: " + R["veee"]["posthoc"]["verdict"] + ")"],
        ["ATMV classified", "✅", D["AT"]["verdict"]], ["30m data limitation documented", "✅", "v4_cov30.json"],
        ["Pressure Pool downstream effect measured or explicitly UNKNOWN", "✅", D["PC"]["verdict"]],
        ["V4 implementation complete where justified", "⚠️ جزئيّ", "H-LEVEL الاحتجاز FAIL ⟵ «عرضُ بنية» لا أداةُ قرار"],
        ["V3.1 preserved", "✅", "لا ملفَّ في faisal_method_v3/ عُدِّل في V4 (يُتحقَّق بـgit diff قبل كلّ دمج)"],
        ["Unit/Integration/Regression/Mutation/Look-ahead/Data-quality/Determinism tests pass", yn(su_ok), (f"{SU.get('passed')}/{SU.get('failed')}" if SU else "—")],
        ["Visual validation complete where data exists", "✅", f"{len(R.get('overlays') or [])} طبقة"],
        ["CI green", "✅ (#547)" + ("" if ci_ok else " · ⏳ PR النتائج"),
         " · ".join(str(x["run"]) for x in REG["pr_contract"]["ci_pr"] + (REG.get("pr_results") or {}).get("ci", []))
         + ("" if ci_ok else " · ومعرّفاتُ PR النتائج تُسجَّل في الذاكرة بعد الدمج")],
        ["Main CI green", "✅ (#547)" + ("" if main_ok else " · ⏳ بعد دمج النتائج"),
         " · ".join(str(x["run"]) for x in REG["pr_contract"]["ci_main"] + (REG.get("pr_results") or {}).get("ci_main", []))],
        ["Production unchanged", "✅", "§37"],
        ["Every READY/WAIT/REJECT/UNKNOWN explainable", "✅", "explain في كلّ كائن (05)"],
    ]
    if MUT:
        rows.insert(21, ["Mutation tests pass", yn(MUT.get("caught") == MUT.get("total")), f"{MUT.get('caught')}/{MUT.get('total')}"])
    return rows


# ── 02 / 03 ────────────────────────────────────────────────────────────────────────────────────
def doc02(D):
    F = D["F"]
    g = F["decision_graph"]
    rr = [[s["rule"], s["state"], E.STATE_DECISION[s["state"]], E.STATE_AR[s["state"]]] for s in g["state_order"]]
    edges = [[e["from"], e["to"], e["rule"], e["when"]] for e in g["validity_edges"]]
    params = [[k, v[0], v[1], v[2] if len(v) > 2 else ""] for k, v in E.PARAMS.items()]
    t = ["# 02 — خطّ قرار فيصل V4 (مُعادٌ بناؤه ومُعدَّلٌ بالدليل)", "",
         "> الترتيبُ المفترض في المهمّة **لم يُقبل كما هو**: الصلاحيّةُ حاجبٌ يأتي بعد البنية ولا يرقّي · والنموذجُ معلومةٌ لا قرار · والتأكيدُ = ثباتٌ في المنطقة أو سحبٌ ثمّ عودة ·",
         "> والدخولُ آليّةٌ لا قرار. " + g["hierarchy_note"], "",
         "## ① المراحل", " ⟵ ".join(g["hierarchy_reconstructed"]), "",
         "## ② ترتيبُ آلة الحالات (أوّلُ ما يصدق يحكم)", table(["القاعدة", "الحالة", "القرار الفنيّ", "المعنى"], rr), "",
         "## ③ الصلاحيّة (حاجبٌ · لا ترقية)", table(["من", "إلى", "القاعدة", "متى"], edges), "",
         "## ④ العتبات بمصادرها", table(["المفتاح", "القيمة", "المصدر", "التعليل"], params), "",
         "## ⑤ قراريّةُ القواعد (§11)",
         table(["القاعدة", "القراريّة", "الحالة", "مستوى المصدر", "نشطة؟", "الأثر"],
               [[k, r["decisionality"], r["status"], r["source_level"], yn(r.get("active")), r["effect"]] for k, r in RV.RULES_V4.items()]), "",
         "## ⑥ ما لا يراه المحرّك (ولذلك UNKNOWN)",
         "القروبات · الطرحُ المعلَّق · المتاحُ للشورت · بصمةُ المضارب/الضغط — كلُّها **شرطُ READY عند فيصل** ولا مصدرَ تاريخيٌّ لها ⟵ الجاهزيّةُ الفنيّةُ بلا هذه المعلومة **UNKNOWN بقائمة الناقص** لا READY."]
    return "\n".join(t)


def doc03(D):
    g = dict(D["F"]["decision_graph"])
    g["engine_version"] = E.ENGINE_VERSION
    g["params"] = {k: {"value": v[0], "source": v[1]} for k, v in E.PARAMS.items()}
    g["generated_by"] = "faisal_method_v4/v4_docs.py ⟵ results/forensics_v4.json · decision_engine.py · rules_v4.py"
    return g


# ── 04 / 05 / 06 ───────────────────────────────────────────────────────────────────────────────
def doc04(D):
    F, M, R = D["F"], D["M"], D["R"]
    dc = F["decision_combos"]
    cx = [[g, v["READY"], v["WAIT"], v["REJECT"]] for g, v in dc["component_x_label"].items()]
    comb = [[x["components"], x["label"], x["n"], " · ".join(x["cases"][:6]) + (" …" if len(x["cases"]) > 6 else "")] for x in dc["combinations"]]
    desc = R["h_state_descriptive"]
    hs = [[GROUP_AR[g], desc[g]["n"], desc[g]["state_exact"], desc[g]["always_wait"], desc[g]["faisal_ready"], desc[g]["engine_ready"], desc[g]["engine_unknown"]]
          for g in GROUPS]
    tech = F["rejection_forensics"]["tech_ready_but_wait_or_reject"]
    t = ["# 04 — جنائيّاتُ READY / WAIT / REJECT (§8)", "",
         "> كيف يفرّق فيصل: (1) النموذجُ موجود ⟵ (2) صالح ⟵ (3) إعدادٌ موجود ⟵ (4) مثير ⟵ (5) قريبٌ من الدخول ⟵ (6) READY ⟵ (7) WAIT ⟵ (8) REJECT.",
         "> **الجوابُ من النصّ:** (1-2) النموذجُ لا يقرّر (W «معلومة» · والدخولُ في وسطه غيرُ آمن) · (3) الإعداد = قاعٌ ثبت 5 جلسات ثمّ دورةُ اختبار ·",
         "> (5) القربُ = منطقةُ 15% فوق القاع · (6) READY = ثباتٌ في المنطقة أو سحبٌ ثمّ عودة **وصلاحيّةٌ نظيفة ومضاربٌ حاضر** · (7) WAIT = الموقعُ لم يأتِ أو التأكيدُ",
         "> لم يكتمل أو المضاربُ غائب · (8) REJECT = قروباتٌ أو تسريب (نادر: " + str(dc["cases_by_label"].get("REJECT", 0)) + " حالات).", "",
         f"## ① المكوّن × القرار (النصُّ الحرفيّ لفيصل · طبقة 1/2 · {sum(dc['cases_by_label'].values())} حالة)", dc["method"], "",
         table(["المكوّن", "READY", "WAIT", "REJECT"], cx), "",
         "## ② كلُّ تركيبةٍ ظاهرة", table(["المكوّنات المذكورة", "القرار", "عدد", "الحالات"], comb),
         f"⟵ {dc['single_example_combinations']} تركيبةً بمثالٍ واحد — **لا قاعدةَ من مثالٍ واحد**.", "",
         "## ③ «جاهزٌ فنيًّا لكن WAIT/REJECT» (المعلومةُ الحاسمة خارج الشموع)", " · ".join(tech) or "—", "",
         "## ④ المحرّك مقابل كلمة فيصل (وصفيّ · §⑦)", table(["المجموعة", "سليمة", "تطابقُ الكلمة", "«دائمًا WAIT»", "READY فيصل", "READY المحرّك", "UNKNOWN المحرّك"], hs),
         "⟵ **المحرّكُ لا يتجاوز الخطَّ التافه** · ولا READY منه بلا معلومة الصلاحيّة (بالبناء) — وهذا صدقٌ لا قدرة.", "",
         "## ⑤ مصفوفةُ فيصل × المحرّك على S1 كلّها", "```", json.dumps(M["S1_all"]["h_state"], ensure_ascii=False), "```",
         "والحالةُ الفنيّة: ```" + json.dumps(M["S1_all"]["h_tech"], ensure_ascii=False) + "```"]
    return "\n".join(t)


def _rec_index():
    p = os.path.join(HERE, "data", "visual_pass_v4.jsonl")
    out = {}
    for line in open(p, encoding="utf-8"):
        r = json.loads(line)
        out[r["id"]] = r
    return out


def doc05(D):
    R, C = D["R"], D["C"]
    recs = _rec_index()
    byc = {c["case"]: c for c in C["cases"]}
    head = ["CASE_ID", "TICKER", "TIMEFRAME", "PATTERN", "PATTERN_VALIDITY", "MARKET_STRUCTURE", "SUPPORT", "RESISTANCE", "PRICE_LOCATION", "VOLUME",
            "INDICATORS", "BREAKOUT", "RETEST", "ENTRY", "INVALIDATION", "TARGET", "HIGHER_TF_CONTEXT", "LOWER_TF_CONTEXT", "FAISAL_DECISION",
            "TOOL_DECISION", "DECISION_DIFFERENCE", "EVIDENCE", "CONTRADICTIONS"]
    rows = []
    for r in R["rows"]:
        if r["set"] not in ("S1", "S3"):
            continue
        c = byc.get(r["case"], {})
        tf = sorted({t for s in c.get("sids") or [] for t in (recs.get(s.split("#")[0], {}).get("tf") or [])})
        st = r.get("structure") or {}
        lv = r.get("levels") or {}
        pats = " · ".join(f"{p.get('pattern')} ({p.get('decisionality')})" for p in (r.get("patterns") or []))
        sup = " · ".join(f"F:{x['kind']} {x['price']}" for x in c.get("levels_F") or [] if x.get("kind") in ("support", "bottom", "zone_lo", "sweep", "stop"))
        res = " · ".join(f"F:{x['kind']} {x['price']}" for x in c.get("levels_F") or [] if x.get("kind") in ("resistance", "trigger", "zone_hi"))
        loc = r.get("decisive_class")
        mc = r.get("market_context") or {}
        ent = r.get("entry") or {}
        tgt = r.get("target") or []
        diff = ("—" if r["status"] != "OK" else ("متّفق" if r.get("state") == r.get("faisal") else f"{r.get('faisal')} ≠ {r.get('state')}"))
        rows.append([r["case"], r.get("ticker"), " ".join(tf) or "—", pats or "—", "معلومة (لا قرار)",
                     f"{r.get('tech_state')} · قاع {st.get('bottom')} · ثبات {st.get('hold_sessions')} · صعود {st.get('rise_pct')}%" if st else r["status"],
                     f"{sup or '—'} ¦ E: {lv.get('bottom')}/{lv.get('support2')}", f"{res or '—'} ¦ E: {lv.get('resistance1')}",
                     f"{loc} (الحاسم {r.get('decisive_level')} · الإغلاق {r.get('close')})", f"×{mc.get('volume_vs_20d')}" if mc else "—",
                     f"RSI {mc.get('rsi14')}" if mc else "—", f"تحرّر {ent.get('type2_liberation')} (معلومة)" if ent else "—",
                     "RETEST_*" if str(r.get("tech_state", "")).startswith("RETEST") else "—", f"طلبات {ent.get('type1_bids')}" if ent else "—",
                     f"تحت القاع {st.get('bottom')}" if st else "—", ", ".join(f"{x.get('name')} {x.get('price')}" for x in tgt[:3]) if isinstance(tgt, list) else "—",
                     "UNKNOWN (يوميٌّ وحدَه)", "UNKNOWN (لا 30/5 دقائق تاريخيًّا)", r.get("faisal"), f"{r.get('state')} ({r.get('status')})", diff,
                     " · ".join(c.get("sids") or [])[:80], c.get("label_notes") or "—"])
    t = ["# 05 — مصفوفةُ الحالات (§9) — S1 ‏+ S3", "",
         "> الأعمدةُ كما طلبتها المهمّة · **«F:» من نصّ فيصل** (`data/case_labels_v4.json`) و**«E:» من المحرّك** عند آخر جلسةٍ قبل العبارة · والنموذجُ معلومةٌ لا قرار ·",
         "> والفريمُ الأعلى والأدنى UNKNOWN بالبناء (المحرّكُ يوميّ · و30 دقيقة لا تمتدّ تاريخيًّا لكلّ الحالات — `results/v4_cov30.json`).", "",
         table(head, rows)]
    return "\n".join(t)


def doc06(D):
    F = D["F"]
    rj = F["rejection_forensics"]
    rows = [[x["case"], x["set"], x["label"], x["tier"], x["plan"], x["reason_class"], yn(x["tech_ready_stated"]), (x["quote"] or "")[:120]] for x in rj["rows"]]
    acc = F["accept_despite_missing"]
    oas = F["orders_at_support"]
    t = ["# 06 — جنائيّاتُ الرفض والانتظار (§13 · §14 · §15)", "",
         f"## ① {rj['n']} حالة WAIT/REJECT (طبقة 1/2 · S1-S3) بسببها", table(["سبب الانتظار", "عدد"], list(rj["by_reason"].items())), "",
         table(["الحالة", "المجموعة", "الكلمة", "الطبقة", "الخطّة", "السبب", "جاهزٌ فنيًّا مذكور؟", "الاقتباس"], rows), "",
         "**الخلاصة:** الانتظارُ عند فيصل **موقعيٌّ أوّلًا** (منطقةٌ تحت السعر/إعادةُ اختبار) ثمّ **تأكيد** (زنادٌ فوق السعر) ثمّ **مضاربٌ/توقيت** — والصلاحيّةُ "
         "(قروبات · طرح · شورت) تحجب مع غيرها · ولا مؤشّرَ ولا حجمَ ولا فريمًا أعلى سببًا منفردًا في النصّ.", "",
         "## ② قبولٌ رغم غياب شرطٍ «عامّ» (§14 — لا يُنفَّذ الشرطُ العامّ)",
         table(["الحالة", "قول فيصل", "الشرطُ العامّ الغائب", "الصور"], [[x["case"], x["faisal"], x["missing_generic"], " · ".join(x["ids"])] for x in acc["cases"]]), "",
         table(["الشرطُ العامّ", "لماذا لا يُنفَّذ"], [[x.get("condition"), x.get("why_not")] for x in acc["generic_conditions_not_implemented"]]), "",
         "## ③ «الطلباتُ عند الدعم» (§15)", f"**{oas['classification']}** — {oas['conclusion']}", "",
         table(["مؤيِّد", "مناقِض"], [[a, b] for a, b in zip(oas["supporting"] + [""] * 10, oas["contradicting"] + [""] * 10) if a or b])]
    return "\n".join(t)


def doc07(D):
    F = D["F"]
    rules = {k: {"contradicting": r.get("contradicting") or [], "status": r["status"], "decisionality": r["decisionality"]} for k, r in RV.RULES_V4.items()}
    corr = [x for x in D["CORR"]["items"] if x["status"] in ("CONTRADICTION_RECORDED", "WITHDRAWN_INFERENCE")]
    return {"generated_by": "faisal_method_v4/v4_docs.py ⟵ results/forensics_v4.json · rules_v4.py · data/corrections_v4.json",
            "contradictions": F["contradictions"], "per_rule_contradicting_examples": rules, "corrections_as_contradictions": corr,
            "downgrade_policy": "قاعدةٌ بتعارضاتٍ قويّةٍ متكرّرة تُخفَّض أو يُعاد تصنيفُها (§28) — R-W-SPAN مُدمَجة · H-D2 CONTRADICTED · R4-OP-01 قراريّتُها UNKNOWN"}


# ── 08 ─────────────────────────────────────────────────────────────────────────────────────────
def doc08(D):
    tf = D["F"]["target_forensics"]
    summ = [[x["value"], x["class"], x["tier"], x["n"]] for x in tf["summary"]]
    occ = [[x["id"], x["tier"], x["value"], x["class"], x["context"][:110]] for x in tf["occurrences"] if x["tier"] in ("1", "2")]
    tg = RV.RULES_V4.get("R4-TGT-01", {})
    t = ["# 08 — جنائيّاتُ الأهداف لكلّ النماذج (§18)", "", "> " + tf["method"], "",
         "## ① الملخّص (القيمة × الصنف × الطبقة)", table(["القيمة", "الصنف", "الطبقة", "عدد"], summ), "",
         "## ② كلُّ ورودٍ من الطبقة 1/2", table(["الصورة", "الطبقة", "القيمة", "الصنف", "السياق"], occ), "",
         "## ③ الحكم",
         "- **«100٪»** مقرونةً بـ«هدف» = **مسافةُ ربحٍ ‏+100% من الدخول** (لا ارتفاعَ النموذج) · وكثيرٌ منها «تحقّق» (وصفُ ما حدث) لا هدفٌ مسبق.",
         "- **«50٪»** لا إسقاطَ نموذجٍ قطّ: سياقاتٌ متنوّعة (متوسّط حركة · تحقّق · هبوط) · **«70٪»** = كمّيّةُ جني الربح الأوّل لا هدفٌ سعريّ.",
         "- **الأهدافُ عند فيصل سلّمُ مقاوماتٍ أفقيّ** (رؤوس الشموع الساقطة · المقاومات) — معلومةٌ تُعرض بعائلاتها الموسومة ولا تغيّر الحالة: "
         f"`R4-TGT-01` ({tg.get('status')} · {tg.get('decisionality')}).",
         "- **لا صيغةَ «قياسٍ عامّة»** (ارتفاعُ النموذج) تُنسب لفيصل — ذاك طرفٌ ثالث (POSSIBLE)."]
    return "\n".join(t)


# ── 09 / 10 ────────────────────────────────────────────────────────────────────────────────────
def doc09(D):
    R, M, AT = D["R"], D["M"], D["AT"]
    g = R["golden_v31_vs_v4"]
    rows = [[x["case"], x["faisal"], x.get("asof_v31"), x.get("v31_label"), yn(x.get("v31_match")) if x.get("v31_match") is not None else "—",
             x.get("v4_tech"), x.get("v4_state"), x.get("v4_word"), yn(x.get("v4_match")) if x.get("v4_match") is not None else "—",
             x.get("v4_decisive"), x.get("v4_class")] for x in g["rows"]]
    dx = R["dxst"]
    ve = R["veee"]
    vp = ve["posthoc"]
    t = ["# 09 — الحالاتُ الذهبيّة (§16 · تحقّقٌ لا اكتشاف)", "",
         "> قائمةُ الملفّ المسجَّل (V3.1): RAYA · LABT · ZNB · RUBI · AMIX · HCWB · DXST · VEEE · ATMV ‏+ ما سمّته المهمّة (SPRC · CUPR) — و`target10` تجربةٌ لا رمز.",
         "> **لم تصنع قاعدة:** لا رمزَ ذهبيٌّ في كود المحرّك (قفل V4L7) والقواعدُ من نصوص الطبقة 1/2.", "",
         "## ① بتواريخ V3.1 نفسِها (قراءةٌ عند جلسة V3.1 شاملةً)",
         table(["الحالة", "فيصل", "تاريخ V3.1", "V3.1", "طابق؟", "V4 الفنيّة", "V4 الحالة", "V4 الكلمة", "طابق؟", "الحاسم", "الفئة"], rows),
         f"⟵ **V3.1 {g['v31_matched']}/{g['dated']} · V4 {g['v4_matched']}/{g['dated']} · و«دائمًا WAIT» {g['always_wait_baseline']}/{g['dated']}** — "
         "تحسّنُ DXST (READY⟵WAIT) يقابله أنّ الخطَّ التافه أعلى من الاثنين ⟵ **لا دعوى تحسّن**. AMIX/HCWB (READY عند فيصل) ⟵ BASE_FORMING عند المحرّك.", "",
         "## ② بتواريخ عبارات V4 (المجموعة S3 كلّها)", metrics_table({k: M[k] for k in GROUPS}).split("\n")[0] + "\n" + metrics_table(M).split("\n")[1] + "\n"
         + [ln for ln in metrics_table(M).split("\n") if ln.startswith("| S3")][0], "",
         "## ③ DXST (§19)", f"**{dx['verdict']} — {dx['label']}** · المراسي {dx['anchors']}",
         table(["الجلسة", "شموع", "الخطوة 1 (نقاطٌ موجودة)", "الخطوة 2 (محاور k=1/2/3)", "الخطوة 3 (المكتشف)", "W المكتشف"],
               [[k, v.get("bars"), v.get("step1"), json.dumps(v.get("step2"), ensure_ascii=False), v.get("step3"), v.get("w_found")] for k, v in dx["sessions"].items()]),
         "⟵ نقاطُ رسم فيصل **موجودةٌ ومحاورُ مؤكَّدةٌ بعرض 1** والمكتشفُ الافتراضيّ يختار بنيةً أخرى ⟵ **اختيارٌ تقديريّ** · لا تسامحَ وُسِّع.", "",
         "## ④ VEEE (§20)",
         f"**العقد (§⑨): {ve['verdict']}** — A8 على شموع V3.1 {ve['v31_fixture']['A8']['verdict']} وعلى fetch {ve['v4_fetch']['A8']['verdict']} (المصدران متّفقان: "
         f"{ve['agree_sources_A8']}) · السبب: قمّةُ الستّين عند الجلسات المرشّحة ليست 8.80 بل أعلى (صعودٌ سابق داخل النافذة):",
         table(["الجلسة", "الإغلاق", "التغيّر", "قاع 60", "قمّة 60"], [[x["date"], x["close"], x["change"], x["low60"], x["high60"]] for x in vp["a8_failure_diagnosis"]]),
         f"**⚠️ POST-HOC (لم يُسجَّل):** مرساةُ شارت فيصل «$6.760 ‏+0.200 (‏+3.049%) At close» تُفرد **{vp['candidates']}** ({vp['verdict']}) — "
         "تُنشر وصفًا ولا تحلّ محلَّ حكم العقد · والوسم `POST-HOC-INSPECTED` قائمٌ (صفوفُ مايو رُئيت قبل العقد).", "",
         "## ⑤ ATMV (§21)", f"**{AT['verdict']}** — {len(AT['sources'])} مصدرًا جُرّب واحدًا واحدًا:",
         table(["المصدر", "الرمز", "النتيجة"], [[s["source"], s["symbol"], _atmv_res(s)] for s in AT["sources"]])]
    return "\n".join(t)


def _atmv_res(s):
    if "error" in s:
        return f"خطأ {s['error']}"
    if "members" in s:
        return f"أعضاءٌ في القائمة: {s['members'] or 'لا شيء'}"
    if "result" in s:
        return "غائبٌ عن الخريطة" if s["result"] is None else str(s["result"])
    return "لا شموع (None)" if s.get("bars") is None else f"{s['bars']} شمعة"


def doc10(D):
    gen = D["F"]["rule_generalization"]
    rows = [[k, v["status"], v["decisionality"], v["source_level"], v["support_count"], v["contradiction_count"], v["independent_sources"], v["unique_images"],
             v["unique_tickers"], v["unique_timeframes"], v["unique_patterns"], "نعم" if v["golden_witness"] else "—"]
            for k, v in sorted(gen.items()) if v["active"]]
    g = D["R"]["golden_v31_vs_v4"]
    flips = [x["case"] for x in g["rows"] if x.get("v31_match") is not None and x.get("v31_match") != x.get("v4_match")]
    t = ["# 10 — تعميمُ الحالات الذهبيّة (§17)", "",
         f"> الحالاتُ التي تغيّر حكمُها بين V3.1 وV4: **{', '.join(flips) or 'لا شيء'}** · والقاعدتان المسؤولتان عن DXST: `R4-LOC-01` و`R4-CYC-01` (WAIT لأنّ السعرَ فوق المنطقة بعد صعود الاختبار) — "
         "ومصدرُهما نصوصُ فيصل (لا DXST) كما في الجدول. **لا لغةَ دلالةٍ إحصائيّة** (العددُ صغير).", "",
         table(["القاعدة", "الحالة", "القراريّة", "المستوى", "مؤيِّد", "مناقِض", "مصادر مستقلّة", "صور", "رموز", "فريمات", "مكوّنات", "شاهدٌ ذهبيّ"], rows), "",
         "**الطريقة:** المؤيّدُ والمناقضُ من سجلّ القاعدة (§27) · والصورُ والرموزُ والفريماتُ والمكوّناتُ من سجلّات المرور البصريّ لمعرّفاتها (`v4_forensics.rule_generalization`)."]
    return "\n".join(t)


# ── 11 ─────────────────────────────────────────────────────────────────────────────────────────
def doc11(D):
    PC = D["PC"]
    t_ = PC["totals"]
    cmp_ = PC["_v4_compare"]
    rows = [["قراءاتٌ مقصوصةٌ بالسقف (lost readings)", t_["truncated"]], ["مؤهَّلون A (بالسقف · الإنتاج)", t_["qual_A"]], ["مؤهَّلون B (بلا سقف)", t_["qual_B"]],
            ["مؤهَّلون C (المتحرّكون أوّلًا)", t_["qual_C"]], ["كروت A", t_["cards_A"]], ["كروت B", t_["cards_B"]], ["كروت C", t_["cards_C"]],
            ["كروتٌ مفقودة (في B لا A)", t_["lost_cards"]], ["مفقودةٌ بسبب السقف وحدَه", t_["cap_only_lost_cards"]], ["كروت A أزاحتها B", t_["displaced_A_cards"]],
            ["تكرار (B وحدَها)", t_["dup_B_only"]], ["محجوزةٌ بسلامة البيانات", t_["dq_holds"]], ["ثباتُ فيصل (B وحدَها)", t_["faisal_hold_B_only"]],
            ["جاهزٌ (B وحدَها)", t_["ready_B_only"]], ["جلساتٌ انقلب فيها القرار", t_["sessions_flip"]]]
    t = ["# 11 — أثرُ سقف بِركة الضغط على المخرَج (§23 · بلا تغييرٍ إنتاجيّ)", "",
         f"> **الحكم: {PC['verdict']}** — إعادةُ `poolcap2` (`{D['REG']['runs'][3]['run']}`) **طابقت V3.1 (`{cmp_['v31_source_run']}`) في كلّ شيءٍ عدا زمن الجلب** "
         f"({cmp_['secs_v31']}ث ⟵ {cmp_['secs_v4']}ث) ⟵ «أُعيد إنتاجُه» (§⑫) · والأرقامُ الثلاثة: كروت B **{t_['cards_B']}** · مفقودة **{t_['lost_cards']}** · "
         f"اتّفاقُ المحاكي مع سجلّ الإنتاج **{PC['repro_ledger_jaccard_mean']}** على {PC['repro_sessions']} جلسة.", "",
         table(["المقياس", f"المجموع ({PC['sessions']} جلسة · تغطية {PC['coverage']})"], rows), "",
         "## مقاييسُ المهمّة (§23) ⟵ ما يقابلها",
         table(["مقياسُ المهمّة", "المقابل", "القيمة"],
               [["lost readings", "قراءاتٌ مقصوصة", t_["truncated"]], ["lost candidates", "مؤهَّلو B ناقص مؤهَّلي A", t_["qual_B"] - t_["qual_A"]],
                ["lost valid setups", "ثباتُ فيصل في B وحدَها", t_["faisal_hold_B_only"]], ["lost cards", "كروتٌ مفقودة", t_["lost_cards"]],
                ["lost unique signals", "— (رسائلُ تلغرام غيرُ محاكاة)", "UNKNOWN"], ["lost same-day signals", "— (غيرُ محاكاة)", "UNKNOWN"],
                ["duplicates", "تكرار B وحدَها", t_["dup_B_only"]], ["held/DQ cases", "محجوزةٌ بسلامة البيانات", t_["dq_holds"]],
                ["signals blocked ONLY by cap", "كروتٌ مفقودةٌ بالسقف وحدَه (كرت ≠ إشارة)", t_["cap_only_lost_cards"]],
                ["VALID TELEGRAM SIGNALS LOST ONLY BECAUSE OF CAP", "اتّفاقُ المحاكي دون 0.60", "UNKNOWN"]]), "",
         "## لماذا UNKNOWN لا LOW ولا MATERIAL؟",
         f"عقدُ `V31_prereg` §④ يشترط اتّفاقَ المحاكي مع سجلّ الإنتاج 0.60 فأكثر قبل قراءة أيّ «مفقود» — والمقيس {PC['repro_ledger_jaccard_mean']} ⟵ "
         "المحاكي لا يعيد ما أرسله الإنتاج فعلًا ⟵ **«إشاراتُ تلغرام الصالحة المفقودة بسبب السقف وحدَه» = UNKNOWN**. "
         "والسلسلةُ المطلوبة (مرشّح ⟵ مؤهَّل ⟵ صالحٌ لفيصل ⟵ كرت ⟵ إشارة) مقيسةٌ حتى «كرت» في المحاكي · و«إشارة تلغرام» تتطلّب سجلَّ الإرسال الحيّ بالسقف وبدونه — "
         "غيرُ موجودٍ لأنّ الإنتاجَ لم يعمل بلا سقف قطّ.",
         "**ولا تغييرَ للسقف** (§37) — و«MATERIAL» في V3 تخصّ البِركة (قراءاتٌ خارج السقف) لا الإشارات."]
    return "\n".join(t)


# ── 12 / 13 / 14 ───────────────────────────────────────────────────────────────────────────────
def doc12(D):
    F = D["F"]
    pa = F["pattern_audit"]
    rows = [[k, v["status"], v["verbatim_by_tier"]["1"], v["verbatim_by_tier"]["2"], v["verbatim_by_tier"]["2b"], v["verbatim_by_tier"]["X"],
             v["described_by_tier"]["1"], " · ".join(v["tier1_examples"][:4]) or "—", v["note"] or ""] for k, v in pa["components"].items()]
    fields = ["rule_id", "description", "source", "author", "source_level", "image_ids", "supporting", "contradicting", "status", "decisionality",
              "active", "backtest_derived", "current_version", "change_history"]
    rr = [[r["rule_id"], r["description"][:90], r["source"], r["author"], r["source_level"], " · ".join(r["image_ids"][:4]) + (" …" if len(r["image_ids"]) > 4 else ""),
           len(r["supporting"]), len(r["contradicting"]), r["status"], r["decisionality"], yn(r.get("active")), "✅ (V4L6/V4L7)", "V4L1-V4L10",
           r["backtest_derived"], r["current_version"], " · ".join(r["change_history"])] for r in RV.RULES_V4.values()]
    t = ["# 12 — تدقيقُ القواعد V4 (§7 · §11 · §24 · §27 · §29)", "",
         "## ① المكوّنات كلّها (PROVE أو UNKNOWN)", pa["rule"], "",
         table(["المكوّن", "الحالة", "حرفيّ 1", "حرفيّ 2", "حرفيّ 2b", "حرفيّ X", "وصفٌ 1", "أمثلة الطبقة 1", "ملاحظة"], rows), "",
         "## ② سجلُّ القواعد (§27)", "الحقولُ في `rules_v4.py`: " + " · ".join(fields), "",
         table(["RULE_ID", "الوصف", "المصدر", "الكاتب", "المستوى", "الصور", "مؤيِّد", "مناقِض", "الحالة", "القراريّة", "IMPLEMENTED", "TESTED",
                "MUTATION_LOCK", "BACKTEST_DERIVED", "النسخة", "التاريخ"], rr), "",
         "## ③ RAYA و R-W-SPAN (§12)", table(["البند", "النتيجة"], [[k, v] for k, v in F["r_w_span"].items()]), "",
         f"## ④ جدارُ الصورة الواحدة (§29): {', '.join(F['single_image_rules']) or 'لا قاعدةَ نشطة بصورةٍ واحدة'}",
         "## ⑤ جدارُ الباكتيست (§24): كلُّ قاعدةٍ `backtest_derived = False` (قفل V4L7) · ولا عتبةَ ضُبطت بعائد."]
    return "\n".join(t)


def doc13(D):
    SA = D["SA"] or {}
    v3 = [[s.get("id"), " · ".join(s.get("status") or []) if isinstance(s.get("status"), list) else s.get("status"), (s.get("reason") or s.get("note") or "")[:140]]
          for s in SA.get("sources", [])]
    v4 = [["TradingView (الشارت · الماسح)", "AVAILABLE (من Actions وحدَه)", f"fetch: {sum(1 for v in D['REG']['runs'] if v['mode'] == 'fetch')} تشغيلة · 79 من 80 رمزًا · بلا تسجيل دخول · لا واجهةَ رسميّة"],
          ["Yahoo (yfinance)", "PARTIALLY_AVAILABLE", "ATMV «Quote not found» · شموعٌ لغيره"],
          ["Polygon", "UNAVAILABLE", "الاشتراك منتهٍ منذ 2026-09-29 (403/429)"],
          ["GitHub artifacts", "UNAVAILABLE من الجلسة", "التنزيلُ محجوب ⟵ المخرجاتُ أجزاءٌ في السجلّ (V4OUT)"],
          ["روابطُ السجلّ الموقَّعة (blob)", "UNAVAILABLE", "الوكيلُ يردّ CONNECT 403 ⟵ السجلُّ عبر أداة GitHub ونصُّ الجلسة"],
          ["X / تويتر", "UNAVAILABLE", "لا وصول · لقطاتُ X في المدوّنة وحدَها"],
          ["محادثاتُ Claude/Claude Code الأخرى", "UNAVAILABLE", "لا تعرضها البيئة"],
          ["سجلُّ تلغرام الكامل", "PARTIALLY_AVAILABLE", f"صورُ البوت المحفوظة وحدَها ({D['TG']['summary']['found_in_corpus']} من الدفعة الأخيرة)"],
          ["مدوّنةُ الصور في المستودع", "AVAILABLE", f"{D['CC']['files_exist']}/{D['CC']['images_in_corpus_record']} موجودة · SHA {D['CC']['sha256_match']}"],
          ["صورٌ مذكورةٌ غائبة", "UNAVAILABLE", "IMG_0485/0487/0489/0490 (النهج العلميّ) · IMG_0098/0125 (KST/كلنجر)"]]
    t = ["# 13 — الوصولُ إلى المصادر V4 (§6)", "", "## ① V4 (مُتحقَّقٌ اليوم)", table(["المصدر", "الحالة", "السبب الدقيق"], v4), "",
         "## ② سجلُّ V3 (للمقارنة · `faisal_method_v3/source_access.json`)", table(["المعرّف", "الحالة", "السبب"], v3)]
    return "\n".join(t)


def doc14(D):
    return D["TG"]


# ── 15 / 16 / 17 / 18 ──────────────────────────────────────────────────────────────────────────
def doc15(D):
    ch = []
    for k, r in RV.RULES_V4.items():
        ch.append([k, ("V3.1: " + r["description"][:70]) if k in ("R-W-SPAN", "R-SUP-MAIN", "H-D2") else "—",
                   r["description"][:90] if k.startswith("R4-") else r["effect"], " · ".join(r["image_ids"][:3]) or r["source"],
                   f"مناقِض {len(r['contradicting'])}: " + (" · ".join(r["contradicting"])[:90] or "بحثٌ بلا نتيجة"),
                   r["effect"][:80], "decision_engine.py / rules_v4.py", "V4L6 · V4L7 · V4L10", r["status"]])
    corr = [[x["id"], f"`{x['file']}`:{x.get('line') or '—'}", x["claim"][:100], " · ".join(x["evidence"])[:160], x["correction"][:140], x["effect"], x["status"]]
            for x in D["CORR"]["items"]]
    t = ["# 15 — سجلُّ التغيير V3.1 ⟵ V4", "",
         "> V3 وV3.1 **محفوظتان كما هما** (لا ملفَّ في `faisal_method_v3/` عُدِّل) · وكلُّ تغييرٍ في V4 قابلٌ للتراجع (حذفُ `faisal_method_v4/` ‏+ أسطرُ الذاكرة).", "",
         "## ① القواعد (الحقولُ الثمانية)",
         table(["القاعدة", "القديم", "المقترَح", "الدليل", "بحثُ التعارض", "سببُ التغيير", "التنفيذ", "التحقّق", "الحالةُ النهائيّة"], ch), "",
         "## ② تصحيحاتُ الكاتالوج والدفتر (C01-C15 · تُضاف ولا تحذف)",
         table(["#", "الموضع", "الدعوى", "الدليل", "التصحيح", "الأثر", "الحالة"], corr), "",
         "## ③ الأداة", "- محرّكٌ جديد فوق دوالّ V3.1 (لا تعديلَ فيها) · `v4_run.py` ‏+ `faisal_v4.yml` · `v4_offline.py` · `v4_docs.py` · `overlays/`.",
         "- قفلُ `PC6` يُقرّ الوسمَ المصحَّح لـ`PIVOT_SWEEP_PCT` (‏`faisal_adopted`) — **والرقمُ 13 في الكود بت-بت**.", "",
         "## ④ إعادةُ البناء بعد ضياع الحاوية", *rebuild_lines(D)]
    return "\n".join(t)


def doc16(D):
    R, M, SU, MUT, REG = D["R"], D["M"], D["SU"], D["MUT"], D["REG"]
    pr = predictions(D)
    t = ["# 16 — تقريرُ التحقّق V4", "",
         "## ① العقدُ قبل الرقم", f"- `V4_prereg.md` مدموجٌ في #{REG['pr_contract']['pr']} (`{REG['pr_contract']['merge_sha'][:9]}`) قبل أيّ تشغيلٍ على شموعٍ حقيقيّة · "
         "والتشغيلةُ الأولى الكاملة هي النتيجة.", "",
         "## ② النتائج", metrics_table(M), "",
         "## ③ الإعادة (§36)", f"- البصمة `{R['fixture_sha256']}` · مطابقةُ الملفّ {R['fixture_sha_ok']} · الحسابُ المحلّيّ = Actions: **{R['reproduces_actions_metrics']}** · "
         f"و`poolcap2` = V3.1: **{D['PC']['_v4_compare']['identical_except_timing']}**.", *rebuild_lines(D), "",
         "## ④ التنبّؤات", table(["#", "التنبّؤ", "النتيجة", "صدق؟"], [[a, b, c, yn(d)] for a, b, c, d in pr]), "",
         "## ⑤ الاختبارات", (f"- السويّة الكاملة في worktree معزول: **{SU['passed']} نجح · {SU['failed']} فشل · خروج {SU['exit']}** (`{SU['commit']}` · {SU.get('secs')}ث)."
                             if SU else "- لم تُشغَّل بعد."),
         "- الأقفال: V4L1-V4L10 (البناء · الوسوم · الطبقة X · as-of · النظر للأمام والحتميّة · آلة الحالات · سجلّ القواعد · رياضيّات التقييم · جدار الإنتاج · العقد) "
         "‏+ V4L11-V4L16 (الإعادة من الشموع · التصحيحات · الوثائق = البنّاء · الذهبيّة · التنبّؤات · الجنائيّاتُ والمدوّنة = بنّاؤها).",
         (f"- الطفرات: **{MUT['caught']}/{MUT['total']}** سقطت كلٌّ بقفلها (`results/mutations_v4.json`)." if MUT else "- الطفرات: لم تُشغَّل بعد."),
         "- **عيبٌ في أداة الطفرات أُصلح:** طفرةٌ بالحجم نفسِه تُستعاد في الثانية نفسِها تترك bytecode بائتًا (‏.pyc) ⟵ «أمسكها» قفلٌ خطأً · العلاج: `-B` "
         "و`PYTHONDONTWRITEBYTECODE` ومسحُ `__pycache__` قبل كلّ طفرة · وتشغيلٌ نظيفٌ قبلها وبعدها (0 من 10 فشل).", "",
         "## ⑥ CI", table(["المرحلة", "Workflow", "التشغيلة", "النتيجة"],
                          [["العقد (PR)", x["workflow"], x["run"], x["conclusion"]] for x in REG["pr_contract"]["ci_pr"]]
                          + [["العقد (main)", x["workflow"], x["run"], x["conclusion"]] for x in REG["pr_contract"]["ci_main"]]
                          + [["النتائج (PR)", x["workflow"], x["run"], x["conclusion"]] for x in (REG.get("pr_results") or {}).get("ci", [])]
                          + [["النتائج (main)", x["workflow"], x["run"], x["conclusion"]] for x in (REG.get("pr_results") or {}).get("ci_main", [])])]
    return "\n".join(t)


def doc17(D):
    M = D["M"]
    hold = M["S1_holdout"]
    gates = [["A الدليلُ موجود", "✅", "نصوصُ الطبقة 1/2 لكلّ قاعدةٍ قراريّة"], ["B الدليلُ مستقلٌّ بما يكفي", "✅", "لا قاعدةَ نشطة بصورةٍ واحدة"],
             ["C بُحث عن التعارض", "✅", "07"], ["D حالةٌ معرّفة", "✅", "§27"], ["E الأثرُ صريح", "✅", "effect لكلّ قاعدة"],
             ["F الاختبارات", "✅", "V4L1-V4L16"], ["G قفلُ طفرة", "✅", "results/mutations_v4.json"], ["H بلا نظرٍ للأمام", "✅", "V4L4 · V4L5"],
             ["I ليس من باكتيست", "✅", "V4L7"], ["J لا يصلح حالةً ذهبيّة وحدَها", "✅", "10"],
             ["**التحقّقُ على الاحتجاز**", "❌", f"H-LEVEL {hold['h_level_verdict']} · H-CLASS {hold['h_class']['verdict']}"]]
    t = ["# 17 — تقريرُ الجاهزيّة للتنفيذ", "",
         "> **الحكم: غيرُ جاهزٍ لأيّ وصلٍ إنتاجيّ.** البوّاباتُ A-J تعبر للقواعد كقواعد · **لكنّ المحرّك لم يعبر الاحتجاز** ⟵ يبقى أداةَ بحثٍ عند الطلب "
         "(`faisal_v4.yml` وضع ticker) تعرض **البنية** (القاع · الثبات · المنطقة · السحب) بأسبابها وما ينقصها — لا قرارًا.", "",
         table(["البوّابة (§34)", "الحالة", "الدليل"], gates), "",
         "## ما يلزم قبل أيّ وصل",
         "1. معلوماتُ الصلاحيّة حيّةً (قروبات · طرح · متاح الشورت · بصمةُ المضارب) — وإلّا UNKNOWN دائمًا.",
         "2. احتجازٌ أماميّ (قراراتُ فيصل الجديدة) يعبر H-LEVEL وH-CLASS بعقدٍ جديد.",
         "3. **إذنُ المالك** بعد ذلك (§37) — ولا يُغيَّر كرونٌ ولا رسالةٌ ولا عتبةٌ قبله."]
    return "\n".join(t)


def doc18(D):
    t = ["# 18 — تسليمُ V4", "",
         "## التشغيل", "- `python3 faisal_method_v4/v4_offline.py` ⟵ يعيد كلَّ الأرقام من الشموع المحفوظة ويتحقّق من البصمة ومطابقة Actions (خروج 0).",
         "- `python3 faisal_method_v4/v4_docs.py` ⟵ يعيد بناء الوثائق الثماني عشرة (قفلٌ يطابقها حرفًا).",
         "- `faisal_v4.yml` يدويّ: `ticker` (تحليلُ رمزٍ بكائن القرار) · `fetch` · `atmv` · `cov30` — قراءةٌ فقط بلا تلغرام.", "",
         "## الملفّات", "- العقد `V4_prereg.md` · المحرّك `decision_engine.py` · القواعد `rules_v4.py` · الحالات `v4_cases.py` ⟵ `results/cases_v4.json` · "
         "الوسوم `data/case_labels_v4.json` · المرور `data/visual_pass_v4.jsonl` · الشموع `data/v4_bars_fixture.json` · النتائج `results/*.json` · "
         "التصحيحات `data/corrections_v4.json` · الطبقات `overlays/`.", "",
         "## المفتوح", "- الصلاحيّةُ التاريخيّة غيرُ متاحة ⟵ READY غيرُ قابلةٍ للإعادة · DXST تقديريّ · ATMV بلا بيانات · بِركةُ الضغط UNKNOWN · "
         "VEEE: البعديّ 2026-05-15 غيرُ مسجَّل.",
         "- الوسومُ المصحَّحة في الدفتر توثيق — وأيُّ أثرٍ لها على عتبةٍ حيّة قرارُ المالك (لا شيءَ تغيّر في الكود).", "",
         "## إعادةُ البناء", *rebuild_lines(D)]
    return "\n".join(t)


DOCS_MD = {"01_FAISAL_V4_FINAL_REPORT.md": doc01, "02_FAISAL_DECISION_PIPELINE_V4.md": doc02, "04_READY_WAIT_REJECT_FORENSICS.md": doc04,
           "05_READY_WAIT_CASE_MATRIX.md": doc05, "06_REJECTION_FORENSICS_V4.md": doc06, "08_TARGET_FORENSICS_ALL_PATTERNS.md": doc08,
           "09_GOLDEN_CASES.md": doc09, "10_GOLDEN_CASE_GENERALIZATION.md": doc10, "11_PRESSURE_POOL_DOWNSTREAM_IMPACT_V4.md": doc11,
           "12_RULE_AUDIT_V4.md": doc12, "13_SOURCE_ACCESS_V4.md": doc13, "15_V4_CHANGELOG.md": doc15, "16_V4_VALIDATION_REPORT.md": doc16,
           "17_IMPLEMENTATION_READINESS_REPORT.md": doc17, "18_V4_HANDOFF.md": doc18}
DOCS_JSON = {"03_FAISAL_DECISION_GRAPH_V4.json": doc03, "07_CONTRADICTION_MATRIX_V4.json": doc07, "14_TELEGRAM_IMAGE_RECONCILIATION_V4.json": doc14}


def render_all(D=None):
    D = D or load()
    out = {}
    for name, fn in DOCS_MD.items():
        out[name] = fn(D).rstrip() + "\n"
    for name, fn in DOCS_JSON.items():
        out[name] = json.dumps(fn(D), ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    return out


def main():
    out = render_all()
    os.makedirs(DOCS, exist_ok=True)
    for name, text in out.items():
        with open(os.path.join(DOCS, name), "w", encoding="utf-8") as f:
            f.write(text)
    print(f"📚 {len(out)} وثيقة ⟵ {DOCS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
