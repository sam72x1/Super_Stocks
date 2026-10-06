# -*- coding: utf-8 -*-
"""
🧭 FAISAL V4 — جنائيّاتُ النصّ: المكوّنات (§7) · تركيباتُ القرار (§8) · الأهداف (§18) · الرفضُ والانتظار (§13-§15) ·
R-W-SPAN (§12) · التعارض (§28) · تعميمُ القواعد (§17) · رسمُ القرار (§10) — من المرور البصريّ وحدَه (حتميّ · بلا شبكة).

المدخل: `data/visual_pass_v4.jsonl` و`results/cases_v4.json` و`rules_v4.py` و`decision_engine.py` · المخرج: `results/forensics_v4.json`.
⚖️ الطبقة X لا تصنع حكمًا · والاقتباسُ الحرفيّ «…» وحدَه نصُّ فيصل (نصُّ الشارت الآليّ مستبعد) · ولا رقمَ ربحٍ هنا (§24).

🔁 أُعيد بناءُ هذا الملفّ يوم 2026-10-06 بعد ضياع نسخته غيرِ المدفوعة باستعادة الحاوية: الدوالُّ والثوابتُ من نصّها المحفوظ في سجلّ
الجلسة حرفًا (المكوّنات · التدقيق · الأهداف · الرفض · التركيبات · التعميم · الرسم) · وأُكملت ثلاثُ جملٍ مقصوصةٍ في
`GENERIC_NOT_IMPLEMENTED` · وأُعيدت كتابةُ نصوص خمسةَ عشرَ تعارضًا من شواهدها (المعرّفاتُ والحالاتُ كما طُبعت يوم 2026-10-02 حرفًا ·
والأطرافُ من حقول `contradicting` في `rules_v4.py` وملاحظات المرور البصريّ و`data/corrections_v4.json`) — وكلُّ مخرَجٍ قِيس على ما طُبع قبل الضياع.
"""
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import decision_engine as E      # noqa: E402
import rules_v4 as RV            # noqa: E402
import v4_cases as VC            # noqa: E402

OUT = os.path.join(HERE, "results", "forensics_v4.json")
QUOTE = re.compile(r"«([^»]*)»")

# المكوّنُ ⟵ تعبيرُه (حرفيٌّ داخل «…» أو وصفُ المراجع) — §7
COMPONENTS = {
    "W_DOUBLE_BOTTOM": r"\bW\b|قاع(?:ٌ)? ?مزدوج|القاع المزدوج|حرف W|نموذج W",
    "M_DOUBLE_TOP": r"\bM\b(?![A-Z])|قم(?:ة|ه) مزدوج|حرف M|نموذج M|نموذجً M",
    "HEAD_SHOULDERS": r"راس وكتف|رأس وكتف|الرأس والكتف|الراس والكتف|كتف ايسر|كتف ايمن|كتف أيسر|كتف أيمن",
    "INVERSE_HEAD_SHOULDERS": r"(?:راس|رأس) وكتفين مقلوب|مقلوب|معكوس",
    "FLAG": r"\bflag\b|نموذج علم|نموذج العلم|العلم الصاعد|العلم الهابط",   # «مع كل العلم» (المعرفة) ليس نموذجًا
    "PENNANT": r"pennant|راية",
    "TRIANGLE": r"نموذج مثلث|المثلث|مثلث (?:صاعد|هابط|متماثل)|\btriangle\b",   # «رسم مثلث W» = رسمُ W لا نموذجُ مثلّث
    "CHANNEL": r"قناة (?:سعرية|صاعدة|هابطة)|قناه (?:صاعده|هابطه)|\bchannel\b",
    "BREAKOUT": r"اختراق|تحرر|تحرّر|يتحرر|تجاوز",
    "RETEST": r"اعادة الاختبار|إعادة الاختبار|يرجع يختبر|يختبر الدعم|اختبار الدعم|اختبار القاع|يرجع للدعم",
    "FALSE_BREAKOUT": r"رفض الاختراق|الاختراق فاشل|اختراق فاشل|شمعة غبي|شمعه غبي",
    "CONSOLIDATION": r"تجميع|تذبذب|نطاق|ثبات",
    "SUPPORT_RESISTANCE": r"دعم|دعوم|مقاومه|مقاومة|مقاومات",
    "STRUCTURE_HH_HL_LH_LL": r"قمة اعلى|قمه اعلى|قاع اعلى|قاع ادنى|قمة ادنى|\bHH\b|\bHL\b|\bLH\b|\bLL\b",
    "BOS_CHOCH": r"\bBOS\b|CHoCH|CHOCH|كسر الهيكل",
    "ELLIOTT": r"اليوت|إليوت|موجه|موجات|موجة|\bABC\b",
    "FIBONACCI": r"فيبو|فيبوناتشي|\bfib",
    "VOLUME": r"فوليوم|حجم التداول|\bvolume\b",
    "RSI": r"\bRSI\b|\brsi\b|\bRsi\b",
    "CCI": r"\bCCI\b",
    "FSTO": r"\bFSTO\b|قوة التذبذب",
    "MACD": r"\bMACD\b|ماكد",
    "KST": r"\bKST\b",
    "MOVING_AVERAGE": r"متوسط|\bEMA\b|\bMA\d|\bMa\d",
    "VWAP": r"VWAP|فيواب",
    "KLINGER": r"كلنجر|Klinger",
    "WYCKOFF": r"وايكوف|Wyckoff",
    "GAP": r"فجوة|فجوه|فراغ",
    "FALLING_CANDLE": r"شمعة ساقطة|شمعه ساقطه|الشمعه الساقطه|الشمعة الهابطة|الشمعه الهابطه|شمعة الهبوط",
    "HAMMER": r"همر|مطرق",
    "SWEEP": r"سحب سيول|سحب السيول|مسح سيول|مسح السيول",
    "PRESS": r"ضغط",
    "SPLIT": r"تقسيم|مقسم|مقسّم|قسم السهم",
    "SHORT_BORROW": r"شورت|اقتراض",
    "GROUPS": r"قروب",
    "OFFERING": r"طرح|تخفيف",
}
STATUS_RULE = "حرفيٌّ في وحدتين فأكثر من الطبقة 1 ⟵ PROVEN_IN_TEXT · وحدة ⟵ SINGLE_SOURCE · وصفُ المراجع وحدَه ⟵ OBSERVED_ONLY · صفر ⟵ UNKNOWN"
CLOSED = {"HEAD_SHOULDERS": "محورٌ مُغلَق (HSFX_REOPEN · T-HS-FX/RX) — أمثلةُ فيصل قممٌ يُخرَج عندها",
          "INVERSE_HEAD_SHOULDERS": "محورٌ مُغلَق (HSFX_REOPEN)"}


def _texts(r):
    g = r.get("g") or ""
    rules = " ".join(x.get("txt", "") for x in r.get("rules") or [])
    allt = g + " " + rules
    verb = " ".join(QUOTE.findall(g))
    return verb, allt


def pattern_audit(recs):
    out = {}
    for comp, rx in COMPONENTS.items():
        pat = re.compile(rx)
        cnt = collections.Counter()
        ids = collections.defaultdict(list)
        for r in recs:
            t = VC.tier(r["a"], r.get("ab"))
            verb, allt = _texts(r)
            if pat.search(verb):
                cnt[("verbatim", t)] += 1
                ids[t].append(r["id"])
            elif pat.search(allt):
                cnt[("described", t)] += 1
        v1 = cnt[("verbatim", "1")]
        st = ("PROVEN_IN_TEXT" if v1 >= 2 else ("SINGLE_SOURCE" if v1 == 1 else
              ("OBSERVED_ONLY" if sum(cnt.values()) else "UNKNOWN")))
        out[comp] = {"verbatim_by_tier": {t: cnt[("verbatim", t)] for t in ("1", "2", "2b", "X")},
                     "described_by_tier": {t: cnt[("described", t)] for t in ("1", "2", "2b", "X")},
                     "tier1_examples": sorted(ids["1"])[:8], "status": st, "note": CLOSED.get(comp)}
    return {"rule": STATUS_RULE, "components": out}


TGT_PCT = re.compile(r"(?<![\d.])(50|70|100)\s*[٪%]")
TGT_CLASSES = [("CERTAINTY", r"مضمون|اضمن"), ("PARTIAL_EXIT_QUANTITY", r"كمي|الكمية|الكميه"),
               ("TARGET_PROFIT", r"هدف|اهداف|الهدف|يصعد ل|يوصل|يحقق|ربح يتجاوز"),
               ("ACHIEVED_RISE", r"حقق|دبل|صعد|ارتفع|تمت|جاب"), ("DECLINE_OR_PRESS", r"هبوط|ضغط|سحب|تراجع|نزول|خساره")]


def target_forensics(recs):
    rows = []
    for r in recs:
        t = VC.tier(r["a"], r.get("ab"))
        for q in QUOTE.findall(r.get("g") or ""):
            for m in TGT_PCT.finditer(q):
                ctx = q[max(0, m.start() - 40):m.end() + 40]
                cls = next((c for c, rx in TGT_CLASSES if re.search(rx, ctx)), "OTHER")
                rows.append({"id": r["id"], "author": r["a"], "tier": t, "value": int(m.group(1)), "class": cls, "context": ctx.strip()})
    summ = collections.Counter((x["value"], x["class"], x["tier"]) for x in rows)
    return {"method": "كلُّ «50/70/100٪» داخل اقتباسٍ حرفيٍّ «…» في المرور البصريّ ⟵ صنفٌ من سياق ±40 محرفًا (الترتيب: يقين ⟵ كمّيّة ⟵ هدف/توقّع ⟵ صعودٌ تحقّق ⟵ هبوط/ضغط ⟵ غيره)",
            "occurrences": rows,
            "summary": [{"value": v, "class": c, "tier": t, "n": n} for (v, c, t), n in sorted(summ.items(), key=lambda kv: (kv[0][0], -kv[1]))]}


REASON_BY_PLAN = {"BELOW": "PRICE_LOCATION (انتظارُ منطقةٍ تحت السعر/إعادةُ الاختبار)", "ABOVE": "CONFIRMATION (زنادٌ/تحرّرٌ فوق السعر)",
                  "BOTH": "PRICE_LOCATION + CONFIRMATION", "AT": "HOLD_CONFIRMATION (عند الدعم وينتظر الثبات)",
                  "NONE": "OPERATOR_OR_TIMING (مضارب · بريماركت)"}
VALIDITY_CODES = re.compile(r"GROUP|OFFERING|SHORT_(?:HIGH|550K|80K|65K)|LEAK|NO_GROUPS_CONDITION|SHORT_80K_REMAINING")
TECH_CODES = re.compile(r"^TECH_READY|TECH_CONDITIONS_MET|TECH_READY_PRIVATE_PICK")


def rejection_forensics(cases, recs):
    byid = {r["id"]: r for r in recs}
    rows = []
    for c in cases:
        if c["set"] not in ("S1", "S2", "S3") or c["label4"] not in ("WAIT", "REJECT") or c["best_tier"] not in ("1", "2"):
            continue
        why = sorted({w for sid in c["sids"] for w in (byid.get(sid.split("#")[0], {}).get("why") or [])})
        for sid in c["sids"]:
            r = byid.get(sid.split("#")[0], {})
            if "#" in sid:
                why += [w for w in ((r.get("cases") or [{}])[int(sid.split("#")[1])].get("why") or []) if w not in why]
        reason = REASON_BY_PLAN.get(c.get("plan_F") or "", "UNLABELLED")
        if any(VALIDITY_CODES.search(w) for w in why):
            reason = "VALIDITY (قروبات · طرح · شورت · تسريب)" + (" + " + reason if reason != "UNLABELLED" else "")
        quote = ""
        for sid in c["sids"]:
            r = byid.get(sid.split("#")[0], {})
            for x in r.get("rules") or []:
                if x.get("eff") in ("WAIT", "REJECT", "WATCH"):
                    quote = x.get("txt", "")
                    break
            if quote:
                break
        rows.append({"case": c["case"], "set": c["set"], "label": c["label4"], "tier": c["best_tier"], "plan": c.get("plan_F"),
                     "tech_ready_stated": any(TECH_CODES.search(w) for w in why), "reason_class": reason, "why_codes": why[:12],
                     "quote": quote})
    summ = collections.Counter(r["reason_class"] for r in rows)
    tech = [r for r in rows if r["tech_ready_stated"]]
    return {"rows": rows, "by_reason": dict(summ.most_common()), "tech_ready_but_wait_or_reject": [r["case"] for r in tech],
            "n": len(rows)}


ACCEPT_DESPITE = [
    {"case": "SPRC_2026-07-17", "ids": ["IMG_0395", "TG_1843"], "missing_generic": "اختراقٌ مؤكَّد قبل الشراء",
     "faisal": "«محملين فيه وشاري» عند الدعم · والتحرّرُ 5.60 «إيجابيّة» لاحقة لا شرطُ دخول", "golden": True},
    {"case": "WA_20260918_31_SXTC", "ids": ["WA_20260918_31_SXTC"], "missing_generic": "ثباتٌ عدّة جلسات بعد الاختبار",
     "faisal": "«تم الضغط اليوم ✅ · دخول 1.80 > 1.90» — READY يومَ الضغط (طبقة 2)"},
    {"case": "DSY_2026-04", "ids": ["IMG_0291"], "missing_generic": "شراءٌ بالطلب عند الدعم / إغلاقٌ يوميٌّ مؤكِّد",
     "faisal": "«اخذته الان من العرض الليلي 1.85» (طبقة 2)"},
    {"case": "PPCB_2026-05/06", "ids": ["TG_2059"], "missing_generic": "إعادةُ اختبارٍ بعد الضغط",
     "faisal": "«ماركت ناخذه» بعد «ضغطه المضارب الى 2 وارتد» (ظاهرٌ بوسم)"},
    {"case": "AMIX_2026-08-24", "ids": ["X_20260827_amix_hcwb_ready"], "missing_generic": "شمعةُ انعكاسٍ مؤكِّدة قبل الطلبات",
     "faisal": "«جاهز جدا · دخولنا دفعات من 4.65 > 4.75 > 4.85 · لازم يضغطه تحت 5» — طلباتٌ قبل الضغط", "golden": True},
    {"case": "EZRA_flash", "ids": ["IMG_0617"], "missing_generic": "قاعٌ ثابتٌ 5 جلسات",
     "faisal": "شراءٌ منفَّذٌ عند عودةٍ فوق VWAP بعد هبوطٍ خاطف (2.2597) — نوعُ دخولٍ لحظيّ"},
    {"case": "ELPW_2026-01", "ids": ["X_20260918_66_ELPW"], "missing_generic": "حجمٌ/مؤشّراتٌ مؤكِّدة",
     "faisal": "«جاهز دخول سيوله عاليه من العرض» (مُستعاد) — ثمّ ‏−78% قبل ‏+3000%"},
]
GENERIC_NOT_IMPLEMENTED = [
    {"condition": "اختراقٌ مؤكَّدٌ شرطًا لـREADY", "why_not": "SPRC/AMIX/DSY/SXTC: READY عند الدعم قبل أيّ اختراق · والاختراقُ «إيجابيّةٌ» أو دخولٌ ثانٍ متنازَع عليه (C-BREAKOUT · R4-ENT-02 معلومة)"},
    {"condition": "ثباتُ 3-5 جلسات بعد الاختبار شرطًا لـREADY", "why_not": "SXTC يومَ الضغط · SPRC بعد جلسة · TDIC على شمعة الهمر ⇒ HOLD_ZONE يحدّد الجاهزيّةَ الفنيّة لمسار المنطقة وحدَه · ومسارُ السحب ثمّ العودة (PRESS_RECLAIM) بلا ثبات"},
    {"condition": "حجمٌ مؤكِّد (Volume confirmation)", "why_not": "لا عبارةَ READY واحدةٌ تشترطه · «لا تهمّك السيولة الآن — يهمّك الفوليوم» (DCOY) سياقٌ لا شرط ⇒ معلومةٌ في كائن القرار (volume_vs_20d) لا شرط"},
    {"condition": "تشبّعُ RSI شرطًا", "why_not": "محورُ «الدخول بسعر RSI» مُغلَق (اقفل RSI) · والقائمةُ تذكره سياقًا ⇒ لا يدخل القرار"},
]


def orders_at_support():
    r = RV.RULES_V4["R4-ENT-01"]
    return {"question": "هل يشترط فيصل الطلباتِ عند الدعم؟", "classification": "ENTRY_MECHANISM_PREFERRED (SUPPORTING · ليس شرطَ قرار)",
            "supporting": r["supporting"], "contradicting": r["contradicting"],
            "conclusion": "آليّةُ الدخول الأولى المفضّلة («ما اخاطر» · «شرا من العرض خساره») · والشراءُ من العرض مقبولٌ في الدخول الثاني وعند التحرّر "
                          "(AZI · DSY · PPCB) ⇒ لا يُبنى عليه READY/WAIT — جوابُ §15: لا تُطبَّق شرطًا"}


RWSPAN = {
    "question": "هل R-W-SPAN قاعدةٌ عامّةٌ لفيصل؟",
    "v31_basis": "تعريفُ طرفٍ ثالث (TG_58042/43/50/51) يطابقه رسمُ فيصل IMG_0627 · وصفرُ مثالٍ يناقضه",
    "v4_finding": "المعنى العامّ «القاعُ الحقيقيُّ هو الأدنى · وكسرُه يعيد التحليل» مسنودٌ مستقلًّا (R4-BOT-01 · R4-INV-01): "
                  "TG_50584 «أدنى شمعة القاع» · X_20260905_10 «كسر 1.81 تصنع تحليل اخر» · X_20260905_07 «إن كسر 2.08 يذهب إلى 1.70» · IMG_0689",
    "contradiction_search": "بحثٌ في 609 وحدة عن W مقبولٍ رغم قاعٍ داخليٍّ أدنى: صفرُ مثالٍ لفيصل · وRAYA (ذهبيّ) يوافق (دعمُه 1.999 = القاعُ الداخليّ)",
    "decision": "SUBSUMED — يُعمَّم في R4-BOT-01 (القاع = أدنى ذيلٍ منذ قمّة الدورة) ولا يُستعمل قاعدةً مستقلّة في V4 · وV3.1 محفوظٌ كما هو",
    "status": "SUPPORTED (المعنى العامّ) · والصيغةُ الهندسيّة الخاصّة بـW (2% بين القاعين) POSSIBLE",
}


# §28 — مصفوفةُ التعارض: لا يُخفى تعارضٌ ولا يُحسم بالأنسب · والحالةُ كما حُكمت (وأُعيدت نصوصُ C-OPTIMING … C-FOGGY من شواهدها 2026-10-06)
CONTRADICTIONS = [
    {"id": "C-BREAKOUT", "rules": ["R4-ENT-02"], "side_a": ["TG_2197 «دخول المضاربين > بعد الاختراق ربح سريع قليل امن»", "TG_57862", "IMG_0602"],
     "side_b": ["TG_1840 «تشري ع الاختراق اعرف انك خسران … الاختراق فاشل الدخول فيه»"], "status": "UNRESOLVED",
     "engine_effect": "R4-ENT-02 INFORMATIONAL — لا يقلب الحالة"},
    {"id": "C-CYCLE-VS-CHECKLIST", "rules": ["R4-CYC-01", "R4-HOLD-01"], "side_a": ["X_20260918_85_YMT «هذا اصل التحليل»", "TG_50584"],
     "side_b": ["X_20260827_checklist_7points: دخولٌ عند القاع بعد ثبات 5 جلسات بلا صعود اختبار"], "status": "PARTIALLY_RESOLVED",
     "engine_effect": "حالتان فنيّتان: BASE_HELD (قائمةُ الفحص) وRETEST_HELD (الدورة) — كلتاهما جاهزيّةٌ فنيّة"},
    {"id": "C-OPTIMING", "rules": ["R4-OP-01"],
     "side_a": ["TG_1822 EHGO «ننتظر فقط مضارب»", "TG_2218 CDIO «جاهز … بانتظار فقط دخول المضارب»", "X_20260827_amix_hcwb_ready HCWB «ننتظر ضغط المضارب»"],
     "side_b": ["X_20260827_checklist_7points_cont «ماتم ضغطه … تدخل مباشره ع خط متوسط 50 > 200»",
                "X_20260827_amix_hcwb_ready AMIX «جاهز جدا · دخولنا دفعات من 4.65 > 4.75 > 4.85 · لازم يضغطه تحت 5» — طلباتٌ قبل الضغط"],
     "status": "UNRESOLVED",
     "engine_effect": "بصمةُ المضارب غيرُ مرئيّةٍ في الشموع إلّا بالسحب والعودة ⟵ R4-OP-01 قراريّتُها UNKNOWN · والجاهزيّةُ الفنيّةُ بلا معلومة ⟵ UNKNOWN لا READY"},
    {"id": "C-SHORT-THRESHOLD", "rules": ["R4-VAL-SHORT-01"],
     "side_a": ["IMG_0150 WORX «تابعه لين يبقى الشورت تحت 20 الف»", "IMG_0151 «شورته تحت 20 الف»", "TG_50578 DCOY «باقي 80 الف شورت ننتظر»"],
     "side_b": ["TG_2196 ONCO «شورت 150 الف» وخطّةٌ كاملة", "TG_1831 LABT «الشورت 55 الف متوفر» ولم يمنع التحليل (طبقة 2)"],
     "status": "UNRESOLVED",
     "engine_effect": "R4-VAL-SHORT-01 PROBABLE: متاحٌ فوق 20,000 ⟵ WAIT حين تُعطى المعلومة · وغيابُها ⟵ UNKNOWN (لا ترقية)"},
    {"id": "C-SUPPORT10", "rules": ["R4-INV-01", "R4-SWEEP-01"],
     "side_a": ["X_20260905_10 YMT «كسر 1.81 تصنع تحليل اخر بنفس النهج»", "X_20260905_07 BTOG «إن كسر قاع 2.08 يذهب إلى 1.70»",
                "IMG_0569 MNDR «1.40 اخطر مرحله للوقف»"],
     "side_b": ["TG_2017 ENPH «هبوط مسح سيوله اسفل الدعم 29» (‏−11..−13%) ثمّ صعود", "TG_2127 ELAB كسرٌ ‏≈−39% تحت الأحمر 3.033 ثمّ صعودٌ كبير"],
     "status": "UNRESOLVED",
     "engine_effect": "كسرٌ أعمق من SWEEP_MAX_PCT (13%) ⟵ BROKEN_NEW_BASE (WAIT) · وما بعده قاعٌ جديد يُعاد تحليلُه — لا READY"},
    {"id": "C-SWEEP-DEPTH", "rules": ["R4-SWEEP-01"],
     "side_a": ["TG_50584 «سحب السيوله 5٪ ادنى شمعة القاع»", "IMG_0177 «مسح سيوله 10٪ تحت القاع»"],
     "side_b": ["TG_57874 «سبرنت داون 10٪ > 15٪»", "TG_57870 «15٪ من متوسط التجميع»", "IMG_0297 (EDU) «7٪ ل 13٪»"],
     "status": "RANGE_NOT_NUMBER",
     "engine_effect": "SWEEP_MAX_PCT = 13 (faisal_tier2b) حدٌّ أعلى · وإسقاطا 5/10 معلومة · لا رقمَ واحدًا لفيصل"},
    {"id": "C-STOP-REF", "rules": ["R4-STOP-01"],
     "side_a": ["X_20260827_checklist_7points «الوقف القاع»", "TG_2106 «وقفك صارم الدعم الاول»"],
     "side_b": ["X_20260918_61_VEEE «7٪ من دخولنا»", "TG_1978 «الاحمر دعم + وقف -5٪»", "TG_2098 HUBC «وقف 7٪»"],
     "status": "UNRESOLVED",
     "engine_effect": "ثلاثُ عائلاتِ وقفٍ موسومة في كائن القرار (القاع · ‏−5/−7% تحت الدعم · 7% من الدخول) — لا تُخلط ولا تغيّر الحالة"},
    {"id": "C-STOP-VS-SWEEP", "rules": ["R4-STOP-01", "R4-SWEEP-01"],
     "side_a": ["TG_1978 «وقف -5٪»", "TG_2098 HUBC «وقف 7٪»", "TG_2017 «الوقف عند المتداولين من 5-7٪»"],
     "side_b": ["IMG_0297 (EDU) «7٪ ل 13٪»", "TG_57875 OMH ‏−11.8%", "TG_57881 CIIT ‏−11.5%", "TG_57894 DKI ‏−8.4%"],
     "status": "UNRESOLVED",
     "engine_effect": "وقفُ 5-7% يقع داخل مدى السحب المقبول (حتى 13%) ⟵ الإبطالُ في المحرّك كسرٌ أعمق من 13% لا ضربُ الوقف"},
    {"id": "C-HOLD-SESSIONS", "rules": ["R4-HOLD-01"],
     "side_a": ["X_20260918_85_YMT «اكثر من 5 جلسات»", "X_20260827_checklist_7points «5 جلسات»"],
     "side_b": ["IMG_0151 «حافظ ع قاعه لمدة 3 جلسات»", "X_20260827_kwm_150_watch3 «مراقبه لمدة 3 جلسات»", "TG_2066 «3-5 جلسات» (طبقة 2)"],
     "status": "RANGE_NOT_NUMBER",
     "engine_effect": "HOLD_MIN = 5 (faisal_verbatim) للقاع · وHOLD_ZONE = 3 للمنطقة — يُدوَّن ولا يُحسم (و«الخمسة» قِيست في T-GOLD-ENTRY P6 ربحًا لا وفاءً)"},
    {"id": "C-GROUPS", "rules": ["R4-VAL-GRP-01"],
     "side_a": ["IMG_0151 «الشرط خالي من القروبات ✅»", "IMG_0488 «دخول سيوله قروبات … لا انا ولا اكبر محلل يستطيع قراءة الشموع»",
                "IMG_0316 JZ «دخل قروب غبي … المضارب الغى جميع الاهداف»"],
     "side_b": ["X_20260905_10 YMT «لايهم حتى لو دخل قروب ورفعه 20٪ · المضارب اذا بيحقق اهدافه راح يهبط فيه»"],
     "status": "PARTIALLY_RESOLVED",
     "engine_effect": "groups = True ⟵ REJECT للقرار الجديد · وسهمُ متابعةٍ قائمٌ يبقى بأهداف المضارب (YMT) — الفرقُ دخولٌ جديد مقابل مركزٍ قائم"},
    {"id": "C-AUTO-LEVELS", "rules": [],
     "side_a": ["CH_20260918_32_SXTC مقابل CH_20260918_25_SXTC (اليومُ نفسُه بطقمي خطوط)", "CH_20260918_45_NUWE مقابل CH_20260918_39_NUWE (السعرُ نفسُه 0.7755)",
                "CH_20260918_63_ELPW مقابل CH_20260918_65_ELPW (اللحظةُ نفسُها)"],
     "side_b": ["X_20260905_10 «دايما ارسم المقاومه باللاين الاسود»"],
     "status": "RESOLVED_FOR_V4",
     "engine_effect": "خطوطُ التطبيق تتبع مدى العرض ⟵ وسومُ المستويات من نصّ فيصل وحدَه ولا تُعدّ الخطوطُ سندًا (C13)"},
    {"id": "C-SUCCESS-DEF", "rules": ["R4-TGT-01"],
     "side_a": ["IMG_0628 «يبقى علم التحليل وان خرب السهم فتره لابد يرجع يحقق شموعه»"],
     "side_b": ["تعريفُ الأداة: الهدفُ قبل الإبطال (T-TGT · hs_forensic/TARGET_FORENSICS.md)"],
     "status": "UNRESOLVED",
     "engine_effect": "لا مقياسَ ربحٍ في V4 (§24) · والتعريفان يُعلَنان ولا يُوفَّقان"},
    {"id": "C-AUTHOR-DARKCHANNEL", "rules": [],
     "side_a": ["IMG_0303 نسخةٌ حرفيّة من منشور فيصل الظاهر TG_1807 بوسم «# نصائح تعليمية»"],
     "side_b": ["IMG_0289 · IMG_0294 · IMG_0295 منشوراتٌ بلا اسمٍ ظاهر · والقناةُ تنشر لنفسها أيضًا (TG_50596 · TG_20260918_30_targets7)"],
     "status": "UNRESOLVED_OWNER_QUESTION",
     "engine_effect": "منشوراتُ القناة طبقة 2b (حساسيّةٌ فقط) ولا تصنع وسمًا · وهويّةُ القناة سؤالٌ للمالك"},
    {"id": "C-AUTHOR-PALMTREE", "rules": [],
     "side_a": ["استنتاجٌ مبكّر في مرور V4: فقاعاتُ واتساب الخضراء بخلفيّة النخلة = مشرفُ القناة لا فيصل"],
     "side_b": ["X_20260827_amix_pressure_497: منشورُ فيصل على X (‏@kisar_) يضمّن لقطةَ المجموعة بالخلفيّة نفسِها"],
     "status": "RESOLVED (النخيلُ جهازُ فيصل)",
     "engine_effect": "سُحب الاستنتاج (C10) · لقطاتُ النخلة غيرُ المنشورة طبقة 2 (INFERRED_DEVICE_LINKED · حساسيّةٌ فقط)"},
    {"id": "C-TRIG-ABOVE-HOLDER", "rules": [],
     "side_a": ["IMG_0319 JZ «في حال صعد المضارب 4 مقاومه مهم يتحرر منها» ⟵ WAIT بالاصطلاح", "IMG_0393 SPRC «5.50 لو تجاوزها تكمن الاجابيه»"],
     "side_b": ["IMG_0393 «تحديث لبعض الاسهم السابقه» — تحديثٌ لحاملي مركزٍ قائم لا قرارُ دخولٍ جديد",
                "IMG_0645 TDIC «2.69 مهم ثباته فوقها» ثمّ READY صريحٌ (IMG_0659)"],
     "status": "RESOLVED_BY_CONVENTION",
     "engine_effect": "الصريحُ يعلو الاصطلاح (V4_prereg §③) · وشرطُ «فوق السعر» لحاملٍ ⟵ HOLD_STATUS لا WAIT جديد"},
    {"id": "C-T7", "rules": ["R4-TGT-01"],
     "side_a": ["الكاتالوج (:1463 · §سابع وعشرون) «الهدف السابع»"],
     "side_b": ["TG_20260918_30_targets7 «يوصل 7» — سعرٌ ($7 · ‏+250% من ‏≈$2)", "TG_20260918_08_NTCL"],
     "status": "RESOLVED ($7 سعر · STRONGLY_SUPPORTED)",
     "engine_effect": "تصحيحُ الكاتالوج (C06) · لا كود"},
    {"id": "C-FOGGY", "rules": [],
     "side_a": ["الكاتالوج :1470 «مدخلي بالمناطق الضبابيّة الأولى» (إثبات)"],
     "side_b": ["X_20260918_13_NUWE (فيصل ظاهر) «مادخل السهم بالمناطق الضبابيه الاولى» (نفي)", "TG_20260918_38_NUWE «مادخل مناطق ضبابيه الان»"],
     "status": "DISSOLVED (خطأُ قراءة)",
     "engine_effect": "قراءةٌ معكوسة صُحّحت (C07) ⟵ فيصل والقناة يتّفقان: لا دخولَ في المناطق الضبابيّة"},
    {"id": "C-MA-TARGET", "rules": ["R4-TGT-01"], "side_a": ["TG_2063 «ثاني هدف: متوسط 20 أو 50» (كاتبٌ غيرُ مؤكَّد)"], "side_b": ["الأهدافُ = سلّمُ المقاومات (D5)"],
     "status": "UNRESOLVED", "engine_effect": "لا هدفَ من متوسّط"},
    {"id": "C-PURPLE", "rules": [], "side_a": ["FUSE «ثبات دعم = دخول» · PPBT «مناطق طلب»"], "side_b": ["ELPW هدفُ شمعةٍ هابطة · TG_2003 مستوياتٌ وسيطة"],
     "status": "PRIMARY=DEMAND · NOT EXCLUSIVE", "engine_effect": "الألوانُ لا تدخل المحرّك"},
]


COMBO_GROUPS = {
    "PATTERN": ["W_DOUBLE_BOTTOM", "M_DOUBLE_TOP", "HEAD_SHOULDERS", "INVERSE_HEAD_SHOULDERS", "FLAG", "PENNANT", "TRIANGLE", "CHANNEL"],
    "SUPPORT": ["SUPPORT_RESISTANCE"], "BREAKOUT": ["BREAKOUT"], "RETEST": ["RETEST"],
    "INDICATORS": ["RSI", "CCI", "FSTO", "MACD", "KST", "MOVING_AVERAGE", "VWAP", "KLINGER", "FIBONACCI"],
    "STRUCTURE": ["STRUCTURE_HH_HL_LH_LL", "BOS_CHOCH", "SWEEP", "PRESS", "FALLING_CANDLE", "GAP", "CONSOLIDATION"],
    "VALIDITY": ["GROUPS", "OFFERING", "SHORT_BORROW"],
}


def _case_verbatim(c, byid):
    """نصُّ فيصل الحرفيُّ للحالة: الاقتباساتُ «…» في سجلّات عباراتها (الطبقة X مستبعدة)."""
    out = []
    for sid in c.get("sids") or []:
        r = byid.get(sid.split("#")[0])
        if r and VC.tier(r["a"], r.get("ab")) != "X":
            out.append(_texts(r)[0])
    return " ".join(out)


def decision_combos(cases, recs):
    """§8: لكلّ حالةٍ (طبقة 1/2 · READY/WAIT/REJECT) أيُّ المكوّنات ذكرها فيصل حرفيًّا ⟵ عدُّ «المكوّن + القرار» وكلُّ تركيبةٍ ظاهرة."""
    byid = {r["id"]: r for r in recs}
    rx = {g: re.compile("|".join("(?:" + COMPONENTS[c] + ")" for c in comps)) for g, comps in COMBO_GROUPS.items()}
    pair = collections.defaultdict(lambda: collections.Counter())
    pair_ids = collections.defaultdict(list)
    combos = collections.Counter()
    combo_ids = collections.defaultdict(list)
    n = collections.Counter()
    for c in cases:
        if c.get("label4") not in ("READY", "WAIT", "REJECT") or c.get("best_tier") not in ("1", "2"):
            continue
        txt = _case_verbatim(c, byid)
        present = sorted(g for g, p in rx.items() if p.search(txt))
        n[c["label4"]] += 1
        for g in present:
            pair[g][c["label4"]] += 1
            pair_ids[(g, c["label4"])].append(c["case"])
        key = (" + ".join(present) or "NONE_MENTIONED", c["label4"])
        combos[key] += 1
        combo_ids[key].append(c["case"])
    return {"method": "الحالاتُ بطبقة 1/2 وبكلمة READY/WAIT/REJECT · المكوّنُ «موجود» إن ذكره فيصل حرفيًّا داخل «…» في سجلّ عبارته (نصُّ الشارت الآليّ مستبعد)",
            "cases_by_label": dict(n),
            "component_x_label": {g: {lab: pair[g][lab] for lab in ("READY", "WAIT", "REJECT")} for g in COMBO_GROUPS},
            "component_x_label_cases": {f"{g}+{lab}": sorted(v) for (g, lab), v in sorted(pair_ids.items())},
            "combinations": [{"components": k[0], "label": k[1], "n": v, "cases": sorted(combo_ids[k])}
                             for k, v in sorted(combos.items(), key=lambda kv: (-kv[1], kv[0]))],
            "single_example_combinations": sum(1 for v in combos.values() if v == 1)}


def rule_generalization(recs):
    """§17: لكلّ قاعدةٍ نشطة — المؤيّد · المناقض · المصادرُ المستقلّة · الصورُ والرموزُ والفريماتُ والمكوّناتُ الفريدة (من سجلّات صورها)."""
    byid = {r["id"]: r for r in recs}
    out = {}
    for k, r in RV.RULES_V4.items():
        ids = sorted(set(r.get("image_ids") or []))
        found = [byid[i] for i in ids if i in byid]
        tick = sorted({t for x in found for t in (x.get("t") or [])})
        tfs = sorted({t for x in found for t in (x.get("tf") or [])})
        comps = sorted({c for x in found for c, p in COMPONENTS.items() if re.search(p, _texts(x)[0])})
        out[k] = {"active": r.get("active"), "status": r["status"], "decisionality": r["decisionality"], "source_level": r["source_level"],
                  "support_count": len(r.get("supporting") or []), "contradiction_count": len(r.get("contradicting") or []),
                  "independent_sources": RV.independent_sources(r), "unique_images": len(found), "images_missing_from_pass": [i for i in ids if i not in byid],
                  "unique_tickers": len(tick), "tickers": tick, "unique_timeframes": len(tfs), "timeframes": tfs,
                  "unique_patterns": len(comps), "patterns": comps, "golden_witness": r.get("golden_witness") or []}
    return out


def decision_graph():
    nodes = [{"id": s, "decision": E.STATE_DECISION[s], "rule": E.STATE_RULE[s], "label": E.STATE_AR[s]} for s in E.STATE_DECISION]
    stages = ["DATA", "DATA_QUALITY", "MARKET_CONTEXT", "STRUCTURE", "PATTERN", "SUPPORT_RESISTANCE", "PRICE_LOCATION", "CONFIRMATION",
              "VALIDITY", "ENTRY", "INVALIDATION", "TARGET", "DECISION", "EXPLANATION"]
    order = [("R4-DATA-01", "DATA_INSUFFICIENT"), ("R4-INV-01", "BROKEN_NEW_BASE"), ("R4-SWEEP-01", "PRESS_RECLAIM"),
             ("R4-SWEEP-01", "SWEEP_ACTIVE"), ("R4-HOLD-01", "BASE_FORMING"), ("R4-CYC-01", "BASE_HELD"),
             ("R4-LOC-01", "RETEST_PENDING"), ("R4-HOLDZ-01", "RETEST_HELD"), ("R4-HOLDZ-01", "RETEST_IN_PROGRESS")]
    edges = [{"from": "TECH_READY", "to": "REJECT", "rule": "R4-VAL-GRP-01", "when": "groups = True (وفي أيّ حالة)"},
             {"from": "TECH_READY", "to": "WAIT", "rule": "R4-VAL-OFF-01 · R4-VAL-SHORT-01", "when": "طرحٌ معلَّق أو متاحٌ فوق 20,000"},
             {"from": "TECH_READY", "to": "UNKNOWN", "rule": "R4-OP-01", "when": "معلومةٌ ناقصة (قروبات · طرح · شورت · بصمةُ المضارب)"},
             {"from": "TECH_READY", "to": "READY", "rule": "—", "when": "الصلاحيّةُ كاملةٌ نظيفة"}]
    rules = {k: {x: v[x] for x in ("status", "decisionality", "source_level")} for k, v in RV.RULES_V4.items()}
    return {"hierarchy_reconstructed": stages,
            "hierarchy_note": "ترتيبُ المهمّة مُعدَّلٌ بالدليل: الصلاحيّةُ (أخبار · طرح · قروبات · شورت) **حاجبٌ** يأتي بعد البنية ولا يرقّي (ADIL TG_2064 · KWM) · "
                              "والنموذجُ (W) معلومةٌ لا قرار · والتأكيدُ = ثباتٌ في المنطقة أو سحبٌ ثمّ عودة · والدخولُ آليّةٌ لا قرار",
            "state_order": [{"rule": r, "state": s} for r, s in order], "states": nodes, "validity_edges": edges, "rules": rules}


def build():
    recs = VC.load_records()
    cases = json.load(open(os.path.join(HERE, "results", "cases_v4.json"), encoding="utf-8"))["cases"]
    return {"generated_by": "faisal_method_v4/v4_forensics.py",
            "pattern_audit": pattern_audit(recs), "target_forensics": target_forensics(recs),
            "rejection_forensics": rejection_forensics(cases, recs),
            "accept_despite_missing": {"cases": ACCEPT_DESPITE, "generic_conditions_not_implemented": GENERIC_NOT_IMPLEMENTED},
            "orders_at_support": orders_at_support(), "r_w_span": RWSPAN, "contradictions": CONTRADICTIONS,
            "decision_graph": decision_graph(), "single_image_rules": RV.single_image_rules(),
            "decision_combos": decision_combos(cases, recs), "rule_generalization": rule_generalization(recs)}


def main():
    doc = build()
    json.dump(doc, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
    pa = doc["pattern_audit"]["components"]
    print({k: v["status"] for k, v in pa.items()})
    print("targets:", doc["target_forensics"]["summary"][:12])
    print("rejections:", doc["rejection_forensics"]["n"], doc["rejection_forensics"]["by_reason"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
