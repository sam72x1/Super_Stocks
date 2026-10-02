# -*- coding: utf-8 -*-
"""
📐 FAISAL V3.1 — تدقيقُ جرد القواعد بحقولٍ موحّدة (§6) · قراءةٌ فقط · لا يُعدَّل `rule_graph.json` (V3).

    python3 faisal_method_v3/v31_rules.py      ⟵ faisal_method_v3/v31/rule_audit_v31.json

لكلّ قاعدة: RULE_ID · RULE_TEXT · PATTERN · SOURCE_IMAGE_IDS · SUPPORTING_EXAMPLES · CONTRADICTING_EXAMPLES ·
EVIDENCE_STATUS (V3 ثمّ V3.1) · RATIONALE · IMPLEMENTATION_STATUS — وأعلامُ التدقيق:
  DUPLICATE_OF · CONTRADICTED · SINGLE_UNIT_CONFIRMED · PROMOTED_WITHOUT_FAISAL · TEXTBOOK_TA · BACKTEST_DERIVED.
⚖️ «الباكتيست يتحقّق ولا يخترع» (§24): قاعدةٌ مصدرُها قياسٌ لا لفظُ فيصل لا تُرقّى فوق UNKNOWN/PROBABLE.
⚖️ الأعلامُ آليّةٌ (نصٌّ وأرقام) ⟵ تُراجَع · وما يغيّر الحالةَ هنا قاعدتان مكتوبتان أدناه فقط (`V31_DOWNGRADE`).
"""
import collections
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "v31", "rule_audit_v31.json")
STRONG = ("CONFIRMED", "SUPPORTED")
FAISAL_TAGS = ("faisal_verbatim", "faisal_inferred", "faisal_adopted")

# ── قواعدُ V3.1 الجديدة — كلٌّ بمصدرها المقروء بالعين (data/visual_review_v31.json · OPUS_GOLD_ENTRY_PACKAGE.md) ─────────
_CK = "X_20260827_checklist_7points"
_CK2 = "X_20260827_checklist_7points_cont"
NEW_V31 = [
    {"id": "R-SUP-MAIN", "pattern": "entry/support", "text": "لا دخولَ قبل الدعم الأساسيّ — «انتظار الدعوم الاساسيه» · «مافيه دخول لين يختبر» · «غير جاهز فنيا انتظار الهبوط»",
     "source_type": "faisal_verbatim", "supporting": ["X_20260827_labt_supports_wait", "X_20260827_raya_notready", "IMG_0697", _CK,
                                                     "X_20260918_12_doublebottom", "X_20260827_amix_hcwb_ready"],
     "contradicting": ["IMG_0697 (تعريفُ الدعم: 1.963 الأحمرُ فوق ذيل القاع 1.830 بـ7.27% — لا «أدنى ذيل»)",
                       "X_20260827_labt_supports_wait (الدعوم 2 و1.80 فوق القاع 1.740)"],
     "status": "CONFIRMED", "impl": "TOOL_V31_ADVISORY",
     "why": "المفهومُ بلفظ فيصل في 6 وحدات مستقلّة ⟵ CONFIRMED · وتعريفُه التشغيليّ «أدنى ذيلٍ منذ قمّة الدورة» (C1) تناقضه ZNB/LABT ⟵ معلومةٌ في الأداة لا تغيّر الحالة"},
    {"id": "R-W-SPAN", "pattern": "W", "text": "القاعُ المزدوج قاعان لا يقع بينهما قاعٌ أدنى منهما (بأكثر من 2%) — وإلّا فالقاعُ الحقيقيّ ذلك الأدنى",
     "source_type": "faisal_inferred", "supporting": ["IMG_0627", "TG_58042", "TG_58043", "TG_58050", "TG_58051"], "contradicting": [],
     "status": "PROBABLE", "impl": "TOOL_V31_ACTIVE",
     "why": "تعريفُ الطرف الثالث (القمّةُ بين القاعين) يطابقه رسمُ فيصل لـDXST (لا شمعةَ تحت القاعين بينهما) ⟵ قاعدةٌ تعريفيّة لا عتبة · عبرت A1-A4 (V31_prereg §④)"},
    {"id": "R-READY-BIDS", "pattern": "entry", "text": "«جاهز» = طلباتٌ عند الدعم (أو ثباتٌ فوق مستوى الانطلاق) لا شراءٌ بالسعر الحاليّ — «السعر الحالي غير صالح للدخول · اما يهبط وندخل او يصعد فوق 3 يثبت ندخل»",
     "source_type": "faisal_verbatim", "supporting": ["X_20260827_amix_hcwb_ready", "X_20260827_target10_entry_below", _CK],
     "contradicting": [], "status": "CONFIRMED", "impl": "NOT_IMPLEMENTED",
     "why": "AMIX/HCWB (فيصل · «جاهز» والسعرُ 5.27 فوق طلباته 4.65-4.85) ‏+ target10 (فيصل باستنتاجٍ قويّ) ‏+ خاتمةُ القائمة السباعيّة «طلبات من 1.60 ل 1.70» ⟵ "
            "حالاتُ الأداة تصف موضعَ السعر الآن فلا تعبّر عن «جاهزٍ بطلباتٍ أدنى» ⟵ سببُ عدم تطابق AMIX/HCWB في الحالات الذهبيّة"},
    {"id": "CK-00", "pattern": "qualification", "text": "RSI يوميّ في تشبّعٍ بيعيّ دون 30", "source_type": "faisal_verbatim", "supporting": [_CK],
     "contradicting": [], "status": "SUPPORTED", "impl": "PRODUCTION",
     "why": "ترويسةُ القائمة · والإنتاجُ على RSI_OVERSOLD=33 (وسيطُ قاع الكاتالوج) و30 حرفُ فيصل في DRCT ⟵ موجودٌ في الإنتاج بعتبةٍ أوسع"},
    {"id": "CK-01", "pattern": "qualification", "text": "ثباتُ السعر فوق متوسّط 30-50", "source_type": "faisal_verbatim",
     "supporting": [_CK, "X_20260827_rubi_read_short150k"], "contradicting": [], "status": "CONFIRMED", "impl": "NOT_IMPLEMENTED",
     "why": "القائمة ‏+ تطبيقُها السلبيّ الحيّ على RUBI («لازم يثبت السهم فوق متوسط الاسي 50») ⟵ وحدتان · الأداةُ لا تُدخله في الحالة (سببُ عدم تطابق RUBI)"},
    {"id": "CK-02", "pattern": "qualification", "text": "قياسُ الدعوم على 4 ساعات واليوميّ مع قراءة الشموع", "source_type": "faisal_verbatim", "supporting": [_CK],
     "contradicting": [], "status": "SUPPORTED", "impl": "PRODUCTION", "why": "منظومةُ الأربع ساعات في الإنتاج (four_hour_levels) · وحدةٌ واحدةٌ هنا"},
    {"id": "CK-03", "pattern": "qualification", "text": "قراءةُ الأخبار وسببُ الهبوط وتاريخُ التقسيم (بنود ①②③)", "source_type": "faisal_verbatim", "supporting": [_CK],
     "contradicting": [], "status": "SUPPORTED", "impl": "PRODUCTION", "why": "scan_news_risk · مرصدُ SEC · تتبّعُ التقسيم في الإنتاج"},
    {"id": "CK-04", "pattern": "qualification", "text": "فريمُ 4 ساعات: هل له صعودُ أفترٍ وبري (بند ④) · وصعودُ اليوميّ بالمؤشّر «وقت ماركت فقط» (بند ⑤)",
     "source_type": "faisal_verbatim", "supporting": [_CK], "contradicting": [], "status": "SUPPORTED", "impl": "DOCUMENTED_ONLY",
     "why": "وحدةٌ واحدة · لا اختبارَ في الأداة"},
    {"id": "CK-05", "pattern": "qualification", "text": "سهمٌ خالٍ من القروبات: الجاهزُ يتذبذب 10% حدًّا أقصى · والقروبُ يرفع بشموعٍ بلا جسم تصل 20% على 4 ساعات",
     "source_type": "faisal_verbatim", "supporting": [_CK], "contradicting": [], "status": "SUPPORTED", "impl": "PRODUCTION",
     "why": "group_pump_scar وخلوُّ القروب في صيّاد المقسّم · وحدةٌ واحدة بأرقامها"},
    {"id": "CK-06", "pattern": "qualification", "text": "أدنى شمعةٍ هبط لها السهم 5 جلسات: هل كسرها على جميع الفريمات — وعدمُ كسرها مع مراقبة الشورت",
     "source_type": "faisal_verbatim", "supporting": [_CK], "contradicting": [], "status": "SUPPORTED", "impl": "PRODUCTION",
     "why": "«شروطك الثلاثة» (ثباتُ 5 جلسات فوق القاع الدقيق) · وحدةٌ واحدة"},
    {"id": "CK-07", "pattern": "entry/stop", "text": "الدخولُ على القاع والوقفُ أدنى سعر — «1.50 قاع دخوله طلبات من 1.60 ل 1.70 وقفه قاعه» · طلباتٌ كلَّ 5 سنت",
     "source_type": "faisal_verbatim", "supporting": [_CK, _CK2], "contradicting": [], "status": "SUPPORTED", "impl": "DOCUMENTED_ONLY",
     "why": "صورتان لمنشورٍ واحد = وحدةٌ واحدة · الوقفُ = القاع (يختلف عن وقف الارتكاز 7% — لا يُخلط)"},
    {"id": "CK-08", "pattern": "timing", "text": "«غالبا قبل الانفجار يتم ضغطه قريب من القاع» · و«ماتم ضغطه … تدخل مباشره ع خط متوسط 50 اكبر من 200 … باول انطلاقة السهم»",
     "source_type": "faisal_verbatim", "supporting": [_CK2], "contradicting": [], "status": "SUPPORTED", "impl": "DOCUMENTED_ONLY",
     "why": "وحدةٌ واحدة · «غالبا» = نزعةٌ لا قاعدة"},
]

_PUNCT = re.compile(r"[«»\"'`*_()\[\]{}·,.:;!?؟،\-–—⟵⟶→/\\|]+")
_CONTRA = re.compile(r"يناقض|عكسُه|التناقض|مختلفتان")
_BT = re.compile(r"\bT-[A-Z0-9]|باكتيست|backtest|قِيس|مقيس|تجربة|الحكم:", re.I)


def norm(t):
    return re.sub(r"\s+", " ", _PUNCT.sub(" ", t or "")).strip()


def tokens(t):
    return {w for w in norm(t).split() if len(w) > 2}


def implementation(r, tool_src, cfg_keys):
    rid, row = r["id"], (r.get("row") or r.get("statement") or "")
    if rid.startswith("L-"):
        return "PRODUCTION" if any(k in row for k in cfg_keys) else "DOCUMENTED_ONLY"
    return "TOOL_V31" if rid in tool_src else "NOT_IMPLEMENTED"


def audit(rules, tool_src, cfg_keys):
    out = []
    by_norm = collections.defaultdict(list)
    for r in rules:
        by_norm[norm(r.get("statement") or r.get("name"))].append(r["id"])
    toks = {r["id"]: tokens(r.get("statement") or r.get("name")) for r in rules}
    stat = {r["id"]: r.get("evidence_status") for r in rules}
    ids = [r["id"] for r in rules]
    for r in rules:
        rid = r["id"]
        text = r.get("statement") or r.get("name") or ""
        st3 = r.get("evidence_status")
        src = r.get("source_type")
        units = int(r.get("supporting_units") or 0)
        flags = []
        dup = [x for x in by_norm[norm(text)] if x != rid]
        if not dup:
            a = toks[rid]
            if len(a) >= 4:
                dup = [x for x in ids if x != rid and len(toks[x]) >= 4 and len(a & toks[x]) / len(a | toks[x]) >= 0.8]
        if dup:
            flags.append("DUPLICATE_OF:" + ",".join(dup[:5]))
        if st3 == "CONTRADICTED" or r.get("contradicted_by_text"):
            flags.append("CONTRADICTED")
        if st3 == "CONFIRMED" and units <= 1:
            flags.append("SINGLE_UNIT_CONFIRMED")
        if st3 in STRONG and src not in FAISAL_TAGS:
            flags.append("PROMOTED_WITHOUT_FAISAL")
        if src == "third_party":
            flags.append("TEXTBOOK_TA")
        if _BT.search(r.get("row") or "") and src in ("engineering", "unsourced", "faisal_inferred"):
            flags.append("BACKTEST_DERIVED")
        st31, change = st3, None
        for f, new, why in V31_DOWNGRADE:
            if f in flags and st3 in STRONG:
                st31 = new
                change = {"old": st3, "new": new, "reason": why}
                break
        # قاعدةٌ واحدة بحالتين (صفّان في الدفتر بنصٍّ واحد): إن كان توأمُها CONTRADICTED وصفُّها هي يذكر المناقضةَ نفسَها ⟵ CONTRADICTED
        twins = [x for x in by_norm[norm(text)] if x != rid]
        if st31 != "CONTRADICTED" and any(stat.get(x) == "CONTRADICTED" for x in twins) and _CONTRA.search(r.get("row") or ""):
            change = {"old": st3, "new": "CONTRADICTED",
                      "reason": f"توأمُها في الدفتر {','.join(x for x in twins if stat.get(x) == 'CONTRADICTED')} CONTRADICTED وصفُّها يذكر المناقضةَ نفسَها — قاعدةٌ واحدة لا تحمل حالتين"}
            st31 = "CONTRADICTED"
        out.append({"RULE_ID": rid, "RULE_TEXT": text[:400], "PATTERN": r.get("scope") or r.get("category") or (r.get("section") or "")[:60],
                    "SOURCE_IMAGE_IDS": r.get("supporting") or [], "SUPPORTING_EXAMPLES": units,
                    "CONTRADICTING_EXAMPLES": r.get("contradicting") or [], "SOURCE_TAG": src,
                    "EVIDENCE_STATUS_V3": st3, "EVIDENCE_STATUS": st31,
                    "RATIONALE": (r.get("note") or "")[:300] or f"وسمُ المصدر {src} · وحداتٌ مستقلّة {units}",
                    "IMPLEMENTATION_STATUS": implementation(r, tool_src, cfg_keys), "AUDIT_FLAGS": flags, "V31_CHANGE": change})
    return out


# ما يغيّر الحالةَ في V3.1 — قاعدتان مكتوبتان قبل العدّ وتُطبَّقان آليًّا:
V31_DOWNGRADE = [
    ("PROMOTED_WITHOUT_FAISAL", "UNKNOWN", "قاعدةٌ بلا مصدرٍ فيصليّ (engineering/unsourced/third_party) لا تبقى SUPPORTED فما فوق (§12 · §24)"),
    ("SINGLE_UNIT_CONFIRMED", "SUPPORTED", "CONFIRMED يلزمه وحدتان مستقلّتان (تعريفُ V3 نفسُه) — وحدةٌ واحدة = SUPPORTED"),
]


def main(out=OUT):
    g = json.load(open(os.path.join(HERE, "rule_graph.json"), encoding="utf-8"))
    tool_src = open(os.path.join(HERE, "faisal_tool.py"), encoding="utf-8").read()
    s = open(os.path.join(ROOT, "Super_stock.py"), encoding="utf-8").read()
    m = re.search(r"\nCONFIG\s*=\s*\{", s)
    cfg = set(re.findall(r'^\s+"([A-Z][A-Z0-9_]+)"\s*:', s[m.start():m.start() + 60000], re.M)) if m else set()
    recs = audit(g["rules"], tool_src, cfg)
    for n in NEW_V31:
        recs.append({"RULE_ID": n["id"], "RULE_TEXT": n["text"], "PATTERN": n["pattern"], "SOURCE_IMAGE_IDS": n["supporting"],
                     "SUPPORTING_EXAMPLES": len(n["supporting"]), "CONTRADICTING_EXAMPLES": n["contradicting"],
                     "SOURCE_TAG": n["source_type"], "EVIDENCE_STATUS_V3": None, "EVIDENCE_STATUS": n["status"],
                     "RATIONALE": n["why"], "IMPLEMENTATION_STATUS": n["impl"], "AUDIT_FLAGS": ["NEW_IN_V31"], "V31_CHANGE": {"old": None, "new": n["status"], "reason": "قاعدةٌ أُضيفت في V3.1"}})
    flags = collections.Counter(f.split(":")[0] for r in recs for f in r["AUDIT_FLAGS"])
    summ = {"rules_v3": len(g["rules"]), "rules_v31": len(recs), "new_v31": len(NEW_V31),
            "status_v3": dict(collections.Counter(r["EVIDENCE_STATUS_V3"] for r in recs if r["EVIDENCE_STATUS_V3"])),
            "status_v31": dict(collections.Counter(r["EVIDENCE_STATUS"] for r in recs)),
            "changed": sum(1 for r in recs if r["V31_CHANGE"] and r["EVIDENCE_STATUS_V3"]),
            "flags": dict(flags), "implementation": dict(collections.Counter(r["IMPLEMENTATION_STATUS"] for r in recs)),
            "downgrade_rules": [{"flag": f, "to": t, "why": w} for f, t, w in V31_DOWNGRADE]}
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump({"summary": summ, "rules": recs}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(summ, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
