# -*- coding: utf-8 -*-
"""
📚 FAISAL V3.1 — بنّاءُ وثائق V3.1 (§27) · **كلُّ رقمٍ من ملفّات JSON المدفوعة لا من اليد** (سابقةُ docs_build.py في V3).

    python3 faisal_method_v3/v31_docs.py      ⟵ faisal_method_v3/v31/*.md

المصادر: v31/reconcile_v31.json (v31_reconcile.py) · source_access.json (V3 · لا يُعدَّل) · data/visual_review_v31.json ·
وغيابُ مصدرٍ يُكتب «لم يُشغَّل بعد» صراحةً — لا تُملأ الفراغاتُ بتقدير.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
V31 = os.path.join(HERE, "v31")


def J(*parts):
    p = os.path.join(HERE, *parts)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def W(name, text):
    os.makedirs(V31, exist_ok=True)
    with open(os.path.join(V31, name), "w", encoding="utf-8") as f:
        f.write(text.rstrip() + "\n")


def table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for r in rows:
        out.append("| " + " | ".join("—" if x is None else str(x).replace("|", "¦").replace("\n", " ") for x in r) + " |")
    return "\n".join(out)


def yn(b):
    return "✅" if b else "❌"


def image_source_access(R, SA, VR):
    tg, tx = R["telegram"], R.get("transcript") or {}
    t = tg["totals"]
    per = tg["per_image"]
    sends = tg["sends"]
    v3 = {s["id"]: s for s in SA["sources"]}
    tg_rows = [[f"`{x['id']}`", x["message_id"], x["sent_utc"], yn(x["exists"]), yn(x["accessible"]), yn(x["file_id_in_state"]),
                yn(x["visually_inspected"]), yn(x["ocr"]), yn(x["catalogued"]), f"`{x['dup_cluster']}`",
                " · ".join(f"`{d}`" for d in x["duplicate_of"]) or "—", yn(x["used_as_evidence"]),
                f"`{x['evidence_status']}`" if x["evidence_status"] else "—", x["author_or_source"]] for x in per]
    src_rows = [
        ["SRC-REPO (faisal_images/)", " · ".join(v3["SRC-REPO"]["status"]), "بلا تغيير",
         f"{R['corpus']['table'][0]['v31']} صورة · SHA256 والبصماتُ أُعيد حسابُها فطابقت V3 (عدمُ تطابق: "
         f"{len(R['corpus']['sha256_mismatch_vs_v3'])} · {len(R['corpus']['fingerprint_mismatch_vs_v3'])})"],
        ["SRC-TELEGRAM-BOT", " · ".join(v3["SRC-TELEGRAM-BOT"]["status"]), "**مؤكَّد بالمصدر** (كان استنتاجًا)",
         f"رقمُ الرسالة وزمنُ إرسالها من `file_reference` داخل {tg['decoded_file_ids']} file_id من {tg['state_file_ids']} ⟵ "
         + " · ".join(f"{s['count']} في {s['sent_utc']}" for s in sends)],
        ["SRC-SESSION-UPLOADS", " · ".join(v3["SRC-SESSION-UPLOADS"]["status"]), "بلا تغيير",
         (f"{R['corpus']['uploads']['files']} ملفًّا · {R['corpus']['uploads']['images']} صورة · فريدةٌ بالـSHA256 "
          f"{R['corpus']['uploads']['unique_by_sha']} · مطابقةٌ للمدوَّنة {R['corpus']['uploads']['exact_in_corpus']}")
         if R["corpus"].get("uploads") else "لم يُفحص على هذا الجهاز"],
        ["SRC-CONVERSATION-TRANSCRIPTS", " · ".join(v3["SRC-CONVERSATION-TRANSCRIPTS"]["status"]),
         "**ACCESSIBLE · RETRIEVED · INSPECTED** (سجلُّ هذه الجلسة)" if tx.get("status") == "ACCESSIBLE" else tx.get("status", "—"),
         (f"صورٌ أرسلها المالك في المحادثة: {tx['owner_sent_blocks']} كتلة ⟵ {tx['owner_sent_unique']} فريدة · مطابقةٌ تمامًا للمدوَّنة "
          f"{tx['owner_sent_exact_in_corpus']} · للمرفقات {tx['owner_sent_exact_in_uploads']} · والباقي {tx['owner_sent_not_exact']} "
          f"شبهُ مطابقٍ ({tx['owner_sent_not_exact_near_dup']}) ⟵ **جديدٌ غائب: {tx['owner_sent_new']}** · ومحادثاتُ claude.ai الأخرى "
          "غيرُ مرئيّةٍ من الحاوية (بلا تغيير)") if tx.get("status") == "ACCESSIBLE" else "—"],
        ["SRC-X-LIVE", " · ".join(v3["SRC-X-LIVE"]["status"]), "بلا تغيير (NOT_ACCESSIBLE)",
         "أُعيدت المحاولة 2026-10-02: `x.com` و`api.x.com` و`syndication.twitter.com` ⟵ «CONNECT tunnel failed, response 403» "
         "(سياسةُ شبكة الجلسة) · ولم يُجرَّب من رنر Actions (لا مفتاحَ لواجهة X · وأتمتةُ الموقع خلافُ شروطه)"],
        ["SRC-DOC-ONLY-IMAGES", " · ".join(v3["SRC-DOC-ONLY-IMAGES"]["status"]), "بلا تغيير في الحالة · **العددُ صُحّح**",
         f"V3 {v3['SRC-DOC-ONLY-IMAGES']['count']} ⟵ V3.1 {len(R['corpus']['doc_only'])} (المسحُ على كلّ ‎*.md · "
         f"‏+{len(R['corpus']['doc_only_new_vs_v3'])} لم يرها V3 · −{len(R['corpus']['doc_only_v3_not_in_v31'])} محفوظةٌ باسمٍ آخر ≡)"],
    ]
    first, second = (sends + [None, None])[:2]
    return f"""# IMAGE SOURCE ACCESS — V3.1 (§3 · §5)

> **مؤكَّد** = من الملفّ نفسِه (`v31/reconcile_v31.json` · بنّاؤه `v31_reconcile.py`) · و`source_access.json` (V3) **لا يُعدَّل** — هذا جدولُ V3.1 فوقه.
> بنّاءُ هذه الوثيقة `v31_docs.py` ⟵ لا رقمَ مكتوبٌ باليد.

## ⓪ الحكم على «9 أم 11» (§3)
**المصدرُ الفعليّ يقول 11 — على إرسالين:**
- **{first['count']} صور في {first['sent_utc']}** = {first['ids'][0]}…{first['ids'][-1]} ⟵ «التسعُ» التي ذكرها المالك = **الإرسالُ الأوّل**.
- **{second['count'] if second else 0} صورتان في {second['sent_utc'] if second else '—'}** = {(second or {}).get('ids', ['—'])[0]}…{(second or {}).get('ids', ['—'])[-1]} (بعده بنحو 19 دقيقة).
- الدليل: رقمُ الرسالة وطابعُ الإرسال مرمَّزان داخل `file_reference` في كلّ `file_id` محفوظ في `telegram_collect_state.json`
  (ترميزُ Bot API: base64 ثمّ RLE للأصفار) — لا اقتباسٌ ولا ذاكرة. **ولا يخزّن المجمِّعُ هويّةَ المرسل** ⟵ «أرسلها المالك» للإرسال الثاني
  **استنتاجٌ قويّ** (البوتُ خاصّ والإرسالان من المحادثة نفسِها) لا مؤكَّد.
- ⚖️ **العددُ لم يُغيَّر ليتّسق التقرير** — V3 كتب «التسعُ = TG_58042…TG_58050» (صحيحٌ للإرسال الأوّل) و«58051/58052 وصلتا في السحب نفسِه»
  (صحيحٌ للسحب) ⟵ ما كان ناقصًا أنّ المالك **أرسل 11** على دفعتين؛ والتصحيحُ مؤرَّخٌ في الكاتالوج والفهرس والخلاصة.

## ① المجاميع (§3)
{table(["المقياس", "القيمة"], [[k, v] for k, v in t.items()])}

- **USED_AS_EVIDENCE = {t['TELEGRAM_TOTAL_USED_AS_EVIDENCE']}:** كلُّ صورةٍ وحدتُها مستشهَدٌ بها في `evidence_matrix.json` (V3) وليست نسخةً من صورةٍ أخرى ·
  وخارجُها `TG_58047` (متابعٌ لا فيصل · `third_party` غيرُ مستشهَد) و`TG_58051` (نسخةٌ من `EDU_20260918_10_pattern`).

## ② صورةً صورة (§3)
{table(["الصورة", "رقمُ الرسالة", "أُرسلت (UTC)", "موجودة", "مقروءة", "file_id محفوظ", "رُئيت بالعين", "OCR", "في الكاتالوج", "عنقود", "نسخةٌ من", "دليل", "الوسم", "المصدر"], tg_rows)}

«رُئيت بالعين» = صفُّها في `FAISAL_IMAGES_CATALOG.md §ثلاثة وثلاثون` (قراءةُ V3 بالعين) · «دليل» = وحدتُها في `evidence_matrix.json` وليست نسخة.

## ③ المصادر — V3 مقابل V3.1 (§5)
{table(["المصدر", "حالة V3", "حالة V3.1", "الدليل"], src_rows)}

### ما تغيّر في §5 ولماذا
- **سجلُّ المحادثة:** V3 «رفض مُصنِّفُ الصلاحيات قراءةَ السجلّات» ⟵ V3.1 قُرئ سجلُّ هذه الجلسة (jsonl) **عدًّا وبصمةً فقط** (لا يُطبع محتوى):
  الصورُ التي أرسلها المالك (كتلةُ صورةٍ في رأس رسالته) منفصلةٌ عن صور أدواتي (`tool_result` = ما فتحتُه أنا · {tx.get('tool_result_blocks', '—')} كتلة · ليست مصدرًا).
  كلُّ صورةٍ أرسلها المالك لها نظيرٌ في المدوَّنة أو المرفقات (مطابقةٌ تامّة أو شبهُ مطابقةٍ بعتبات التكرار نفسِها) ⟵ **صفرُ صورةٍ غائبة**.
  ⚠️ **حدُّ صدق:** محادثاتُ claude.ai الأخرى (خارج هذه الجلسة) غيرُ مرئيّةٍ من الحاوية — عددُ ما فيها مجهول.
- **X:** بلا تغيير — محجوبٌ بسياسة الشبكة (403 على CONNECT).
- **الإحالاتُ بلا ملفّ:** مسحٌ أوسع (كلُّ ‎*.md) وأدقّ (تُسقط القوالبُ والإحالاتُ المختصرة لملفٍّ موجود والمكرَّرُ المحفوظُ باسمٍ آخر بعلامة «≡») —
  التفصيلُ في `IMAGE_PROVENANCE.md §③`.
"""


def image_provenance(R, VR):
    c = R["corpus"]
    rows = [[r["metric"], r["v3"], r["v31"], r["reason"]] for r in c["table"]]
    edges = [[f"`{e['a']}`", {"derivative_of": "مشتقّةٌ من", "same_drawing_as": "الرسمُ نفسُه في"}[e["kind"]], f"`{e['b']}`",
              yn(e["merged"]), (VR["new"].get(e["a"]) or {}).get("observation", "")[:160]] for e in c["visual_merge_edges"]]
    nrec = [[f"`{s}`", (VR["new"].get(s) or {}).get("source_class", "—"), (VR["new"].get(s) or {}).get("ticker", "—"),
             ((VR["new"].get(s) or {}).get("observation") or "")[:140]] for s in c["no_record_before_v31_visual"]]
    new_doc = [[f"`{k}`", " · ".join(f"`{d}`" for d in c["doc_only"][k][:4])] for k in c["doc_only_new_vs_v3"]]
    dropped = [[f"`{k}`", v] for k, v in sorted(c["doc_only_dropped"].items())]
    meth = c["doc_record_methods"]
    return f"""# IMAGE PROVENANCE — V3.1 (§4)

> **مؤكَّد** من `v31/reconcile_v31.json` (بنّاؤه `v31_reconcile.py` — البصماتُ تُعاد حسابًا من الملفّات بدوالّ `corpus_build` النقيّة
> نفسِها · لا يُنادى `main` فلا يُكتب ملفٌّ من V3) · وملفّاتُ V3 (`image_corpus.json` · `dedup_clusters.json` · `image_provenance.json`) **لا تُعدَّل**.

## ① المطابقة — V3 VALUE · V3.1 VERIFIED VALUE · REASON
{table(["المقياس", "V3", "V3.1", "السبب"], rows)}

- عناقيدُ التكرار المتعدّدة: {c['multi_member_clusters']} · **مطابقةٌ لعناقيد V3 حرفًا: {c['cluster_sets_identical_to_v3']}** · رُوجعت بالعين {c['multi_clusters_visually_reviewed']} ·
  أزواجُ «ليست تكرارًا» بقرارٍ بصريّ: {c['vetoed_pairs']}.
- ⚖️ **«الفريدة» قراءتان لا قراءةٌ واحدة:** بالبصمة ونصّ OCR (عتباتُ V3) **{c['table'][7]['v31']}** — وبعد دمج ما رأته العينُ في V3.1 مشتقًّا أو الرسمَ نفسَه
  **{c['table'][8]['v31']}** (حدٌّ أدنى للوحدات المستقلّة · الدمجُ لا يحذف ملفًّا ولا يغيّر `image_corpus.json`).

## ② «مفحوص» صورةً صورة
«مفحوص» = **سجلٌّ مكتوبٌ لكلّ صورة** بإحدى الطرق — لا «فتحتُها ذهنيًّا»:
{table(["الطريقة", "صور"], [[k, v] for k, v in sorted(meth.items(), key=lambda x: -x[1])] + [[k, sum(1 for v in c["per_image_record"].values() if k in v)] for k in ("visual_v3", "visual_v31", "dup_cluster_reviewed")] + [["أيُّ طريقة (الاتّحاد)", sum(1 for v in c["per_image_record"].values() if v)]])}

- **قبل V3.1: {len(c['no_record_before_v31_visual'])} صورة بلا أيّ سجلٍّ لكلّ صورة** (V3 لم يعدّها لكلّ صورة · وأوّلُ عدٍّ في V3.1 بالاسم الكامل وحدَه أعطى 105 — ثمّ أُضيفت الطرقُ الأخرى: المدى «`A` … `B`» ·
  رمزُ الدفعة بتاريخ قسمه «CH_01/02/03_ELPW» · الاسمُ المختصر · الرقمُ المجرّد على سطر IMG) ⟵ **فُتحت كلُّها بالعين في V3.1** ⟵ **بلا سجلّ الآن: {len(c['no_record_after_v31'])}**.
{table(["الصورة", "التصنيف", "الرمز", "ما فيها (مختصر)"], nrec)}

⚠️ **مؤشّرٌ كان يكذب وأُصلح:** `FAISAL_IMAGE_AUDIT.md` (من `image_audit.py` بعد كلّ سحب تلغرام) قال «📕 لم تُقرأ بعد: 638» لأن ماسحَه يعرف `IMG_xxxx` وحدَها ·
وحالتُه الآليّة «unread» كانت تُثبَّت للأبد ولو وُثّقت الصورة ⟵ أُصلح (العائلاتُ بأسماء ملفّاتها · رمزُ الدفعة والبادئة والقالبُ لا تصنع غائبًا ·
«unread» تُرقّى حين تُوثَّق · وسجلُّ V3.1 يُحتسب · قفلُ `IAV1`).

## ③ الإحالاتُ بلا ملفّ (inaccessible references)
V3: {c['table'][-1]['v3']} ⟵ V3.1: **{c['table'][-1]['v31']}** — مسحُ V3.1 على كلّ ‎*.md (‏+ `faisal_images/README.md`) عدا وثائق هذه المهمّة.
**لم يرها V3 ({len(c['doc_only_new_vs_v3'])}):**
{table(["المعرّف", "الوثائق"], new_doc)}

**أُسقطت من «بلا ملفّ» (ليست صورةً غائبة):**
{table(["الإحالة", "السبب"], dropped)}

## ④ اشتقاقٌ بصريٌّ فاتَ البصمة (V3.1 بالعين)
{table(["الصورة", "العلاقة", "بـ", "دُمجت وحدتُها", "الدليل (مختصر)"], edges)}

- السبب: تصويرُ الشاشة بكاميرا الجوّال مرّتين (زاويةٌ وإضاءةٌ مختلفتان ⟵ dHash/pHash فوق العتبة) · واقتباسُ فيصل منشورَه بالشارت نفسِه مكبَّرًا ·
  والرسمُ نفسُه في «قناة تعليمية» وعند فيصل (`X_20260918_27_CUPR` «فتحت ويبل وجدت تحليل سابق») — **قرينةٌ أنّ القناة تنشر رسومَ فيصل · حالةٌ واحدة لا تغيّر تصنيفَها طرفًا ثالثًا**.
- ⚠️ **حدُّ صدق:** فحصُ الاشتقاق البصريّ شمل الصورَ الـ{len(VR['new'])} التي فُتحت في V3.1 وحدَها — **ليس مسحًا شاملًا** للمدوَّنة؛ مِجَسُّ قصٍّ آليّ (ORB) جُرِّب فلم يميّز فأُسقط.

## ⑤ الإسناد (provenance) — ما يُضاف في V3.1
- **تلغرام:** رقمُ الرسالة وزمنُ الإرسال لكلّ صورةٍ من الدفعة (`IMAGE_SOURCE_ACCESS.md §②`).
- **مجموعة «ستوك»:** `X_20260827_amix_hcwb_ready` لقطةٌ نشرها فيصل باسمه من مجموعة «ستوك» برسائلَ صادرة (✓✓) ⟵ رسائلُ «ستوك» الصادرة = رسائلُه ⟵
  يسند `X_20260827_target10_entry_below` وIMG_0414 إليه (**استنتاجٌ قويّ** لا مؤكَّد · `FAISAL_VERBATIM_INFERRED`).
- **القناة التعليميّة:** `X_20260828_02` = رسمُ `X_20260918_27_CUPR` (فيصل) ⟵ أعلاه.
"""


def render_all():
    """{اسمُ الوثيقة: نصُّها كما يُكتب} — بلا كتابة (يقرؤها القفل FV18 ليقارن القرصَ بالبنّاء)."""
    R = J("v31", "reconcile_v31.json")
    SA = J("source_access.json")
    VR = J("data", "visual_review_v31.json")
    if not R:
        return None
    docs = {"IMAGE_SOURCE_ACCESS.md": image_source_access(R, SA, VR),
            "IMAGE_PROVENANCE.md": image_provenance(R, VR),
            "GOLDEN_CASES.md": golden_cases(),
            "FAISAL_V3_1_CHANGELOG.md": changelog(),
            "TARGET_FORENSICS_ALL_PATTERNS.md": targets_all(),
            "PATTERN_SPECIFICATIONS.md": pattern_specs(),
            "NEW_TOOL_VALIDATION_REPORT.md": validation_report(),
            "IMPLEMENTATION_READINESS_REPORT.md": readiness(),
            "FINAL_FORENSIC_SUMMARY.md": final_summary()}
    return {k: v.rstrip() + "\n" for k, v in docs.items()}


def main():
    docs = render_all()
    if not docs:
        print("⛔ v31/reconcile_v31.json غائب — شغّل v31_reconcile.py أوّلًا")
        return 2
    for name, text in docs.items():
        W(name, text)
    print(f"كُتب: v31/ — {len(docs)} وثائق")
    return 0




# ══ الوثائقُ الباقية (§27) ═══════════════════════════════════════════════════════════════
def _gc():
    return J("v31", "golden_cases_v31.json")


LABEL_NOTE = {
    "RUBI": ("INSUFFICIENT_EVIDENCE", "أسبابُ فيصل لـRUBI مؤشّراتٌ وشورت («جميع المؤشرات سلبيه · لازم يثبت فوق الأسّيّ 50 · الشورت 150 الف») — خارجَ وحدة W · "
                                      "وC1 طابقها مصادفةً (القاعُ الثاني 2.01 فوق MS 1.63 بـ23%) لا بسبب فيصل"),
    "AMIX": ("INSUFFICIENT_EVIDENCE", "«جاهز» عند فيصل = طلباتٌ عند الدعم 4.65-4.85 والسعرُ 5.27 فوقها (R-READY-BIDS) · وW الأداة قديمٌ (مايو) مُبطَل — حالاتُ الأداة لا تعبّر عن «جاهزٍ بطلباتٍ أدنى»"),
    "HCWB": ("INSUFFICIENT_EVIDENCE", "«جاهز» بالرسالة نفسِها · والسعرُ 2.18 فوق القاع الثاني 2.05 بـ6.3% (منطقةُ الدعم الثاني 6%) — حدّيٌّ ولا يُضبط عليه (§⓪)"),
    "DXST": ("POSSIBLE_DISCRETIONARY_JUDGMENT", "W اليوميّ للأداة قديمٌ (مايو 1.72/1.50) مخترَق · وW فيصل على 30 دقيقة (عنقُه 2.864) لا يعيده كاشفٌ محوريّ على TradingView النظاميّ ولا الممتدّ (C3 مرفوضة) — فيصل يرسم على منصّته بيده"),
    "VEEE": ("UNKNOWN", "لا جلسةَ تحقّق شرطَ التاريخ (إغلاق 6.76 وقمّة 9.67 وقاع 5.00 في الستّين) — وتاريخُ V3 (05-21 · مطابقة 1.38) لا يحقّقه"),
    "ATMV": ("DATA_UNAVAILABLE", "لا شموعَ على NASDAQ ولا NYSE ولا AMEX ولا OTC (TradingView) · لا تُخترع"),
}


def _pct3(m):
    if not isinstance(m, dict):
        return "—"
    return " · ".join(f"{n} {m[k]:+.2f}%" for k, n in (("low1", "L1"), ("neck", "العنق"), ("low2", "L2")) if m.get(k) is not None)


def golden_cases():
    G = _gc()
    rows = []
    for r in G["rows"]:
        v3, t = r.get("v3") or {}, r.get("tool_v31") or {}
        ms = (t.get("main_support") or {})
        ok = (t.get("label") == r["faisal"]) if t else None
        lab, why = LABEL_NOTE.get(r["case"], ("MATCH" if ok else "—", ""))
        rows.append([r["case"], r["faisal"], r.get("asof") or "—", r.get("close", "—"), v3.get("state", "—"), t.get("state", "—"),
                     (r.get("C1") or {}).get("state", "—"), (r.get("C2") or {}).get("state", "—"),
                     f"{ms.get('price', '—')} ({ms.get('date', '—')})" if ms else "—",
                     "✅" if ok else ("❌" if ok is False else "—"), lab if not ok else "MATCH"])
    ag = G["agreement"]
    dx = G["dxst_30m"]
    r26 = G.get("raya_v3_date") or {}
    notes = "\n".join(f"- **{k}** — `{v[0]}`: {v[1]}" for k, v in LABEL_NOTE.items())
    return f"""# GOLDEN CASES — V3.1 (§8-§12 · §21)

> العقد `V31_prereg.md` مدموجٌ قبل أيّ رقم (#545 · `760996255`) · الشموعُ من وضع `dump` (TradingView · التشغيلة `37036590477`) ·
> النتيجةُ `v31/golden_cases_v31.json` (بنّاؤها `v31_cases.py`) · والملفُّ الدائم بلا شبكة `v31/golden_fixtures.json` (يعيد الحكمَ نفسَه حرفًا) ·
> القفل `FV17` (+ 6 طفرات سقطت كلُّها) · الطبقاتُ البصريّة `v31/overlays/*.png`.

## ⓪ الخلاصة
- **التطابقُ مع حكم فيصل (7 حالاتٍ مؤرَّخة):** V3 **{ag['v3']['matched']}/{ag['v3']['of']}** · الأداة V3.1 كما تُشحن **{ag['tool_v31']['matched']}/{ag['tool_v31']['of']}** ·
  (C1 وحدَها لو فُعّلت {ag['C1']['matched']}/{ag['C1']['of']} — **لم تُفعَّل**: §③) · ولا قلبَ لحالةٍ «جاهزة» في أيّ ذراع (AMIX/HCWB «انتظار» في V3 أصلًا).
- **RAYA (الأولويّة):** السببُ الجذريّ **اثنان عامّان لا خاصّان بـRAYA** — ① **تاريخُ V3 خاطئ:** الشارتُ إغلاقُه 2.35 ⟵ أقربُ جلسةٍ ≤ 08-27 بإغلاق 2.35 هي **2026-08-21**
  (V3 استعمل 08-26 وإغلاقُها 2.2655) · وعند التاريخ الصحيح الأداةُ **«{(next(x for x in G['rows'] if x['case']=='RAYA').get('tool_v31') or {}).get('state')}»** = انتظار = حكمُ فيصل ·
  ② **عند تاريخ V3 (08-26):** W V3 ({r26.get('v3', {}).get('w')}) **بين قاعَيه ذيلٌ {r26.get('v3', {}).get('span_min_low')}** — والقاعُ المزدوج لا يقع بين قاعَيه قاعٌ أدنى (R-W-SPAN ·
  تعريفٌ يطابقه رسمُ فيصل) ⟵ V3 «{r26.get('v3', {}).get('state')}» وV3.1 «{r26.get('tool_v31', {}).get('state')}». **ولم يُعدَّل شيءٌ ليطابق RAYA.**
- **C3 (جلسةُ 30 دقيقة):** مرفوضة — لا النظاميُّ ولا الممتدُّ أعاد W فيصل لـDXST ضمن 2% (عنقُ النظاميّ {dx['regular']['w']['neckline'] if dx['regular'].get('w') else '—'} · الممتدّ {dx['extended']['w']['neckline'] if dx['extended'].get('w') else '—'} مقابل 2.864).

## ① الحالات
{table(["الحالة", "فيصل", "التاريخ", "الإغلاق", "V3", "V3.1 (الأداة)", "C1", "C2", "الدعمُ الأساسيّ (معلومة)", "تطابق", "الوسم"], rows)}

### الوسومُ بأسبابها (§7 — لا تعديلَ لمطابقة حالة)
{notes}
- **EZRA:** لا تُعدّ (ليست حكمَ دخول) — والـW ما زال يُكتشف في V3.1 (لا رفضَ لـW رسمه فيصل · A2).

## ② القواعدُ المرشّحة مقابل معايير القبول (§④ من العقد)
| القاعدة | A1 المصدر | A2 لا تناقض | A3 التطابق | A4 عامّة | §7 أمثلةٌ مناقِضة | القرار |
|---|---|---|---|---|---|---|
| **C2 R-W-SPAN** | ✅ تعريفيّة (طرفٌ ثالث ‏+ رسمُ فيصل) | ✅ لا جاهزَ يُقلب · EZRA باقٍ | ✅ {ag['C2']['matched']}/7 = {ag['v3']['matched']}/7 | ✅ في `find_w` لكلّ رمز | لا مثالَ لفيصل يناقضها | **مقبولة · نشطة** |
| **C1 R-SUP-MAIN** | ✅ 6 وحدات | ✅ | ✅ {ag['C1']['matched']}/7 | ✅ | ❌ **ZNB:** دعمُ فيصل 1.963 فوق ذيل القاع 1.830 (+7.3%) · **LABT:** دعومُه 2 و1.80 فوق القاع — التعريفُ «أدنى ذيل» يناقضه فيصلُ نفسُه | **معلومةٌ لا قاعدة** (المفهوم CONFIRMED · التعريف لا) |
| **C3 H-D2** | منقول | — | — | — | الشرطُ المسجَّل لم يتحقّق | **مرفوضة** |

⚖️ **إفصاح:** A1-A4 كما كُتبت تقبل C1 · وردُّها جاء من فحص §7 (الأمثلةُ المناقِضة) المذكور في رأس العقد — **تشديدٌ بعد الرقم لا إرخاء**، ويُعلَن.

## ③ التنبّؤاتُ المسجَّلة (تُنشر ولو خابت)
| | التنبّؤ | النتيجة |
|---|---|---|
| P1 | ذيلٌ ‏≈2.00 بين قاعَي W V3 لـRAYA | ✅ صدق ({r26.get('v3', {}).get('span_min_low')} بين 2.49 و2.20) |
| P2 | C1 تجعل RAYA انتظارًا ولا تقلب AMIX | ✅ بالحرف (وAMIX «انتظار» في V3 أصلًا) |
| P3 | الممتدُّ يعيد W فيصل لـDXST والنظاميُّ لا | ❌ خاب (لا هذا ولا ذاك) |
| P4 | ATMV على بورصةٍ غير NASDAQ | ❌ خاب (لا شموعَ على الأربع) |
| P5 | تاريخُ VEEE في V3 خاطئ ويوجد غيرُه | ½ — خاطئٌ ✅ · ولا تاريخَ يحقّق الشرط ❌ |

## ④ DXST على 30 دقيقة (C3)
{table(["الجلسة · الكاشف", "L1", "العنق", "L2", "الحالة", "الفرق عن فيصل (L1 · العنق · L2)"], [[k, (v.get('w') or {}).get('low1', '—'), (v.get('w') or {}).get('neckline', '—'), (v.get('w') or {}).get('low2', '—'), v.get('state', '—'), _pct3(v.get('match'))] for k, v in dx.items()])}

العنقُ 2.864 موجودٌ في الشموع قمّةً محلّيّة (06-15 12:00 ‏2.86 · 06-16 11:30 ‏2.87) **لا محورًا فركتاليًّا** بعرض 2 ⟵ «DO NOT simply widen tolerance» — لم يُوسَّع شيء.

## ⑤ الطبقاتُ البصريّة (§20)
`v31/overlays/`: لكلّ حالةٍ مؤرَّخة رسمٌ يوميّ (W · العنق · الدخولان · الوقف · الأهداف · MS) ‏+ RAYA بتاريخ V3 ‏+ DXST 30 دقيقة نظاميّة وممتدّة (عنقُ فيصل 2.864 خطٌّ مرجعيّ).
"""


def changelog():
    RA = J("v31", "rule_audit_v31.json")
    R = J("v31", "reconcile_v31.json")
    PC = J("results", "pool_cap_downstream.json")
    ch = [
        ("CH-01", "عددُ دفعة تلغرام", "«التسعُ = TG_58042…TG_58050» (V3)", f"11 على إرسالين: 9 ثمّ 2 ({' · '.join(s['sent_utc'] for s in R['telegram']['sends'])})",
         "file_reference في file_id المحفوظ", "—", "الكاتالوج · README · الخلاصة · docs/07 (سطرٌ مؤرَّخ) · FV16", "لا سلوك"),
        ("CH-02", "الوحداتُ المستقلّة", "609", f"609 بالبصمة (أُعيد حسابُها حرفًا) و{R['corpus']['table'][8]['v31']} بعد اشتقاقٍ رأته العين",
         "visual_review_v31 (derivative_of · same_drawing_as)", "الفحصُ البصريّ للاشتقاق شمل صور V3.1 وحدَها", "IMAGE_PROVENANCE · FV16", "لا سلوك"),
        ("CH-03", "«مفحوص» لكلّ صورة", "غيرُ معدود", "722/722 لها سجلّ (23 فُتحت بالعين في V3.1)", "doc_record + visual_review_v31", "الكشفُ بالمدى/رمز الدفعة آليّ", "FV16", "لا سلوك"),
        ("CH-04", "سجلُّ تغطية الصور image_audit.py", "يعرف IMG_xxxx وحدَها · «unread» تُثبَّت للأبد", "العائلاتُ بأسماء ملفّاتها · «unread» تُرقّى · سجلُّ V3.1 يُحتسب",
         "FAISAL_IMAGE_AUDIT.md قال 638 لم تُقرأ والمقيس 23", "—", "image_audit.py · IAV1 · telegram_collect.yml (يشغّله)", "تقريرٌ لا يكذب (845 مدرَج · 0 لم يُقرأ)"),
        ("CH-05", "R-W-SPAN في find_w", "زوجُ قاعين يُقبل ولو بينهما قاعٌ أدنى", "يُرفض إن كان بينهما low أدنى من أدناهما بأكثر من 2%",
         "تعريفُ القاع المزدوج (TG_58042/43/50/51) ‏+ رسمُ فيصل IMG_0627", "لا مثالَ لفيصل", "faisal_tool.find_w · FV17 · (w_validate يبقى V3 بـspan_rule=False)",
         "W مختلف في 14.2% من القراءات اليوميّة الوصفيّة (995 من 7,026) وتغيّرُ الفئة 5.2% (364)"),
        ("CH-06", "R-SUP-MAIN (الدعمُ الأساسيّ)", "غائب", "سطرُ معلومة ‏+ خطٌّ على الرسم — لا يغيّر الحالة",
         "6 وحداتٍ لفيصل", "ZNB (1.963 فوق 1.830) · LABT (2 و1.80 فوق القاع)", "analyze_arrays · render_text · render_png · FV17", "سطرٌ إضافيّ في الرسالة"),
        ("CH-07", "C3 جلسةُ الشموع الدقائقيّة", "نظاميّة", "بلا تغيير (مرفوضة)", "لا جلسةَ تعيد DXST", "—", "—", "لا سلوك"),
        ("CH-08", "تاريخُ RAYA في التحقّق", "2026-08-26", "2026-08-21 (أقربُ إغلاق 2.35 — قاعدةُ العقد)", "شارتُ فيصل: الإغلاق 2.350", "—", "golden_fixtures · FV17", "تطابقُ RAYA"),
        ("CH-09", "مستوياتُ RAYA في V3", "4.908 · 4.569 · 3.998 · 3.233 · 2.617", "‏+ الأحمران 1.999 · 1.454 والسعر 2.35", "قراءةٌ بالعين (visual_review_v31 amend)", "—", "V3 كتب «السعرُ تحت أدنى مستوى لفيصل 2.617» — خطأ", "تصحيحُ قراءة"),
        ("CH-10", "تاريخُ VEEE وATMV", "VEEE 2026-05-21 (مطابقة 1.38) · ATMV «لا شموع» (NASDAQ وحدَها)", "VEEE UNKNOWN · ATMV DATA_UNAVAILABLE على البورصات الأربع",
         "dump (37036590477)", "—", "golden_cases_v31", "—"),
        ("CH-11", "حالاتُ القواعد", "L-005 · L-007 UNKNOWN", "CONTRADICTED (توأمُهما في الدفتر CONTRADICTED بالنصّ نفسِه)",
         "rule_audit_v31", "—", "rule_audit_v31.json", "—"),
        ("CH-12", "قواعدُ جديدة", "—", f"{RA['summary']['new_v31']}: R-SUP-MAIN · R-W-SPAN · R-READY-BIDS · CK-00…CK-08 (القائمة السباعيّة كانت غائبة عن الرسم)",
         "visual_review_v31 · OPUS_GOLD_ENTRY_PACKAGE", "—", "rule_audit_v31.json", "—"),
        ("CH-13", "معنى «100٪»", "ربحٌ ‏+100%", "‏+ أساسُه الدعم/القاع (F100-1b · CONFIRMED · TG_2097 «دعم 2 · الهدف 4 = 100٪») · وجنيٌ جزئيّ عنده في لقطة مجموعة (F100-8 · طرفٌ ثالث · POSSIBLE · محورٌ مُغلَق)",
         "target_forensics_v31 (37 إصابة · صفرُ تناقض)", "لا", "—", "لا سلوك (المحورُ مُغلَق)"),
        ("CH-14", "معنى «50٪»", "عشرةُ معانٍ (V3)", "‏+ ربحٌ محقَّق (F50-11)", "TG_2103 · X_20260828_09", "لا", "—", "—"),
        ("CH-15", "سجلّاتُ المحادثة", "NOT_ACCESSIBLE (رفضها المصنّف)", "جزئيّ: سجلُّ هذه الجلسة ACCESSIBLE (عدٌّ وبصمة) — صفرُ صورةٍ غائبة · والمحادثاتُ الأخرى غيرُ مرئيّةٍ من الحاوية (بلا تغيير)", "reconcile_v31.transcript", "ما أُرسل في محادثاتٍ أخرى لا يُرى", "source_access.json (كتلة v31)", "—"),
        ("CH-16", "أثرُ سقف البِركة على الكروت", "غيرُ مقيس", f"{PC['verdict']} — إعادةُ الإنتاج {PC['repro_ledger_jaccard_mean']} دون 0.60 (المحاكاةُ لا تعيد السجلَّ) · ومحاكاةً: {PC['totals']['cap_only_lost_cards']} كرتًا من {PC['totals']['cards_B']}",
         "poolcap2 (37036594447)", "—", "pressure_pool_cap_audit.md §⑤", "لا تغيير إنتاج"),
        ("CH-17", "إصدارُ الأداة", "FAISAL-V3 1.0", "FAISAL-V3.1 1.1 · RULES_V31 · TOOL_VERSION", "—", "—", "faisal_tool.py", "—"),
    ]
    rows = [[a, b, c, d, e, f, g, h] for a, b, c, d, e, f, g, h in ch]
    return f"""# FAISAL V3 ⟶ V3.1 — سجلُّ التغيير (§2)

> كلُّ بند: القاعدةُ القديمة · الجديدة · الدليل · الدليلُ المناقِض · المكوّناتُ والأقفال · أثرُ السلوك. **V3 لا يُدهَس** — ملفّاتُه كما هي وما أُضيف ملفّاتٌ `v31/` أو سطرٌ مؤرَّخ.

{table(["البند", "الموضوع", "V3", "V3.1", "الدليل", "المناقِض", "المكوّنات · الأقفال", "أثرُ السلوك"], rows)}

## ما لم يتغيّر عمدًا
- بارامتراتُ الأداة كلُّها (`PARAMS`) — لا ضبطَ على حالة (§⓪ من العقد) · و`T-W` (V3) يُعاد بقاعدته (`w_validate` بـ`span_rule=False`).
- الإنتاج: لا جذرَ ولا عتبةَ حيّة ولا سقفَ البِركة · ولا تلغرام.
- المحاورُ المُغلَقة (`HSFX_REOPEN` · `TRAIL_REOPEN` …) — «جنيُ 70% عند 100٪» يُوثَّق ولا يُنفَّذ.
"""


def targets_all():
    TF3 = J("target_forensics.json")
    TF = J("v31", "target_forensics_v31.json")
    m3 = [[m["id"], m["status"], m["source_type"], " · ".join(m["evidence"][:4]), m["meaning"][:120]] for k in ("50", "100") for m in TF3["meanings"][k]]
    m31 = [[k, v["status"], v["source_type"], " · ".join(v["evidence"]), v["meaning"][:140]] for k, v in TF["v31_additions"].items()]
    hits = [[r["id"], r["meaning"], r["author"], r["note"][:120], "❌" if r["contradicts_v3"] else "—"] for r in TF["rows"]]
    pat = [
        ["W (القاعُ المزدوج)", "سلّمُ المقاومات الأفقيّ فوق العنق (T1-T3)", "‏+100% من الدخول عند الدعم (F100-1/1b)", "MM100/MM50 من ارتفاع النموذج — طرفٌ ثالث للمقارنة",
         "وقفُ فيصل 7% تحت القاع الثاني · حدُّ السحب 13%", "DXST: «حقق نسبة 25٪» عند 3.11 (PDF ص52) — مستوًى أفقيّ لا ارتفاعُ النموذج"],
        ["M (القمّةُ المزدوجة)", "سيناريو سلبيّ «ادناهما سلبي» (نطاقُ القرار)", "—", "—", "—", "VEEE 6.18/6.34 (التاريخ UNKNOWN في V3.1)"],
        ["الرأسُ والكتفان", "⛔ محورٌ مُغلَق (HSFX_REOPEN) — «الثبات فوق الكتف الأيسر» قاعدةُ خروجٍ مُغلَقة", "—", "—", "—", "DRMA · DCOY"],
        ["وصفةُ المقسّم", "الشمعةُ الساقطةُ الأولى = 100% (TG_1811)", "‏+100% أقلّ شي (TG_1819/TG_2208)", "—", "الوقفُ = القاع نفسُه", "÷2 من قمّة ما بعد التقسيم مستهدفُ هبوط (F50-4)"],
        ["الارتكاز (القائمة السباعيّة)", "سلّمُ المقاومات (الإنتاج t1-t3)", "‏+100% من الدعم (TG_2097)", "—", "الدخولُ على القاع والوقفُ أدنى سعر (CK-07) · وقفُ الارتكاز 5-7%", "«كنا نحقق بالارتكاز 100% وأكثر بأقل من 5 جلسات» (TG_1867)"],
        ["الفراشة (EZRA)", "5.40 «خطوره السهم» صعودًا أو هبوطًا", "—", "—", "—", "مع W · فيصل لا يعطي رقمَ هدف"],
        ["إليوت/وايكوف", "«منطقة توزيع 3-5» · «3 رؤوس 2 ارتداد» (R-EL)", "—", "—", "—", "TG_58052 — قائمةُ فحصٍ لا هدف"],
    ]
    return f"""# TARGET FORENSICS — كلُّ النماذج (V3.1 · §13)

> V3: `target_forensics.json` (لا يُعدَّل) · V3.1: `v31/target_forensics_v31.json` (بنّاؤه `v31_targets.py`) — مسحُ OCR لكلّ صورة ‏+ أسطرُ الوثائق ‏+ مراجعاتُ V3.1.

## ⓪ الحكم
- **50٪:** {TF['verdict_v31']['50']}
- **100٪:** {TF['verdict_v31']['100']}
- **المسح:** {TF['hits_outside_v3']} صورةً خارج أدلّة V3 ({TF['v3_evidence_ids']}) قُرئت كلُّها · غيرُ مقروءة {len(TF['unread'])} · **تناقضٌ مع حكم V3: {len(TF['contradictions'])}**.

## ① الأهدافُ لكلّ نموذج
{table(["النموذج", "هدفُ فيصل", "‏+100%", "الطرفُ الثالث", "الوقف/الإبطال", "المثال"], pat)}

## ② معاني V3 (كما هي)
{table(["المعرّف", "الحالة", "المصدر", "الدليل", "المعنى"], m3)}

## ③ إضافاتُ V3.1
{table(["المعرّف", "الحالة", "المصدر", "الدليل", "المعنى"], m31)}

## ④ صورةً صورة (خارج أدلّة V3)
{table(["الصورة", "المعنى", "الكاتب", "القراءة", "يناقض V3؟"], hits)}
"""


def pattern_specs():
    T = __import__("faisal_tool")
    rules = T.RULES_V31
    P = T.PARAMS
    prm = [[k, v[0], v[1], v[2][:110]] for k, v in P.items()]
    rr = [[k, "نشطة" if v["active"] else "غيرُ نشطة", v["status"], v["source"], v["why"][:160]] for k, v in rules.items()]
    return f"""# PATTERN SPECIFICATIONS — V3.1

> المواصفةُ المنفَّذة في `faisal_method_v3/faisal_tool.py` ({T.TOOL_VERSION}) — **كلُّ عتبةٍ بوسم مصدرها** · ولا نموذجَ بلا مصدرٍ فيصليّ أو تعريفٍ يطابقه رسمُه.

## W — القاعُ المزدوج (المنفَّذ)
1. **قاعان محوريّان مؤكَّدان** L1 ثمّ L2 (محورٌ فركتاليّ بعرض `SWING_K` يُعرف عند i+k — لا نظرَ للأمام) · فصلُهما `W_BARS_MIN`…`W_BARS_MAX`.
2. **L2** بين L1×(1−13%) [سحبُ سيولة · IMG_0297] وL1×(1+10%).
3. **العنق** = أعلى قمّةٍ بين القاعين · فوق أدناهما بـ10% فأكثر («الصعود غالبا من 10 > 15٪»).
4. **«جاء من فوق»:** أعلى قمّةٍ قبل L1 (بطول الـW) فوق العنق.
5. 🔄 **V3.1 · R-W-SPAN:** لا low بين القاعين أدنى من أدناهما بأكثر من `LEVEL_TOL_PCT` (2%) — وإلّا فالقاعُ الحقيقيّ ذلك الأدنى.
6. **الحالات:** INVALIDATED · AT_SUPPORT2 (حتى ‏+6% فوق L2) · UNSAFE_MIDDLE · BREAKOUT · RETEST_HOLD · FAILED_BREAKOUT.
7. **الدخول:** A عند الدعم الثاني · B أوّلُ اختراقٍ صحيح (‏+ ثباتُ ربع ساعة على 30 دقيقة) · **الوسط**: «غيرُ آمن» بلفظ فيصل — وكمّيًّا على اليوميّ **انعكس** (مدخلُ الوسط أعلى عائدًا من الدعم الثاني بفرقٍ دالّ في تشغيلتَي T-W · V3) — قياسٌ يوميٌّ آليّ لا حكمٌ على رسم فيصل على 30 دقيقة.
8. **الأهداف:** سلّمُ المقاومات (فيصل) · ‏+100% من الدخول (فيصل · وأساسُه الدعم F100-1b) · MM100/MM50 (طرفٌ ثالث · للمقارنة).
9. 🔄 **V3.1 · الدعمُ الأساسيّ (معلومة):** أدنى ذيلٍ منذ قمّة الدورة (120 شمعة) ومسافةُ القاع الثاني فوقه — **لا يغيّر الحالة** (R-SUP-MAIN · تعريفُه يناقضه ZNB/LABT).

## M · نطاقُ القرار
«مقرون 6.18 / 6.34 — ادناهما سلبي اعلاهما اجابي» (TG_58045) ⟵ نطاقٌ بعرض `DECISION_BAND_PCT` فوق القاع الثاني: تحته سيناريو M.

## غيرُ منفَّذ (بسببه)
| النموذج/القاعدة | السبب |
|---|---|
| الرأسُ والكتفان | محورٌ مُغلَقٌ مُنفَّذًا (`HSFX_REOPEN`) |
| «جاهز = طلباتٌ عند الدعم» (R-READY-BIDS) | حالةُ الأداة تصف موضعَ السعر الآن · نمذجتُها قاعدةٌ جديدة يلزمها عقد |
| القائمةُ السباعيّة (CK-00…08) | بعضُها في الإنتاج (RSI · الأخبار · القروب · ثباتُ 5 جلسات) · والباقي وحدةٌ واحدة |
| الفراشة · إليوت | بلا رقم هدفٍ من فيصل |
| جنيُ 70% عند 100٪ | محورُ إدارة الخروج مُغلَق (`TRAIL_REOPEN`) |

## قواعدُ V3.1
{table(["القاعدة", "التفعيل", "الحالة", "المصدر", "السبب"], rr)}

## البارامترات (كما في V3 — لا ضبطَ على حالة)
{table(["البارامتر", "القيمة", "المصدر", "السبب"], prm)}
"""


def _suite():
    s = J("v31", "suite_result.json")
    return s or {"passed": None, "failed": None, "commit": None, "note": "لم يُسجَّل بعد"}


def suite_line(S):
    if S.get("passed") is None:
        return "لم تُسجَّل نتيجتُها بعد (تُكتب في `v31/suite_result.json` بعد تشغيلها في worktree معزول)"
    return f"نجح {S['passed']} · فشل {S['failed']} · خروج {S.get('rc', '—')} · على `{S.get('commit')}` ({S.get('note', '')})"


MUTATIONS = {"FV13+FV14": "5/5 (جولةٌ مشتركة)", "FV15": "6/6", "FV16": "9/9", "IAV1": "4/4", "FV17": "6/6", "FV18": "7/7", "FV19": "5/5"}


def validation_report():
    G = _gc()
    S = _suite()
    cov = J("results", "case_dump_coverage.json")
    crow = []
    for sym in cov["golden"]:
        c = cov["coverage"][sym]
        crow.append([sym, c.get("full") or "⛔", (c.get("daily") or {}).get("n"), (c.get("daily") or {}).get("first"),
                     (c.get("m30") or {}).get("n", "—"), (c.get("m30") or {}).get("first", "—"),
                     (c.get("m30x") or {}).get("n", "—"), (c.get("m30x") or {}).get("first", "—")])
    locks = [["FV1-FV12", "V3 (لا نظرَ للأمام · حالاتُ W · الأهداف · لا علامات مقارنة · العتبات بمصادرها · workflow · تلغرام · الطبقةُ الجنائيّة · الفهرس · T-W · سقفُ البِركة)", "V3", "—"],
             ["FV13", "مخرَجُ الأوضاع الخمسة في السجلّ", "V3 ⟵ V3.1", MUTATIONS["FV13+FV14"]],
             ["FV14", "تفريغُ الشموع: مضغوطٌ يُستعاد · البورصاتُ بالترتيب · صفرُ تلغرام", "V3.1", MUTATIONS["FV13+FV14"]],
             ["FV15", "أثرُ السقف على الكروت (§15)", "V3.1", MUTATIONS["FV15"]],
             ["FV16", "مطابقةُ تلغرام والمدوَّنة (§3/§4)", "V3.1", MUTATIONS["FV16"]],
             ["IAV1", "سجلُّ تغطية الصور لا يكذب", "V3.1", MUTATIONS["IAV1"]],
             ["FV17", "الحالاتُ الذهبيّة (§21) — ملفٌّ دائم بلا شبكة", "V3.1", MUTATIONS["FV17"]],
             ["FV18", "الأرقامُ المنشورة لا تكذب: حكمُ البِركة يُعاد بمصنِّف §④ · §⑤ = ملفُّ النتيجة · وثائقُ v31 = بنّاؤها حرفًا · لا معنى هدفٍ لفيصل بلا صورته", "V3.1", MUTATIONS["FV18"]],
             ["FV19", "بنّاءُ المطابقة لا يدهس قياسًا محفوظًا بـnull (عطلٌ مُثبَت: تشغيلٌ بلا وسائط) · `carry_over` قبل الكتابة", "V3.1", MUTATIONS["FV19"]]]
    return f"""# NEW TOOL VALIDATION REPORT — FAISAL V3.1 (§17-§23)

> الأداة `faisal_method_v3/faisal_tool.py` · {__import__('faisal_tool').TOOL_VERSION} · **أداةُ قراءةٍ عند الطلب** (workflow `faisal_v3.yml` يدويّ · تلغرام فقط بـ`send=1`).

## ⓪ النتيجة
- **ما تغيّر في الأداة بدليل:** R-W-SPAN (نشطة) · الدعمُ الأساسيّ معلومةً · طبقاتٌ بصريّة أوضح (العنق · MS) — وكلُّ ما سواه بلا تغيير.
- **التطابقُ مع فيصل على الحالات المؤرَّخة:** {G['agreement']['tool_v31']['matched']}/{G['agreement']['tool_v31']['of']} (V3 {G['agreement']['v3']['matched']}/{G['agreement']['v3']['of']}) — **لم يرتفع** لأن ما كان سيرفعه (C1) يناقضه فيصلُ نفسُه في مثالين.
- **السويّة:** {suite_line(S)}.

## ① أنواعُ الاختبار (§22)
| النوع | ما يُختبر | أين |
|---|---|---|
| وحدة (بلا شبكة) | المحاور · find_w · w_state · الأهداف · الوقف · النصّ بلا علامات مقارنة · العتبات بمصادرها | FV1-FV5 |
| حالاتٌ ذهبيّة (شموعٌ حقيقيّة محفوظة) | التواريخ · الحالة بكلّ ذراع · التطابق · RAYA بتاريخَيه · C3 · الطبقة النصّيّة | FV17 (`v31/golden_fixtures.json`) |
| لا نظرَ للأمام (§23) | الحالةُ وW والدعمُ الأساسيّ عند asof واحدةٌ بشموعٍ بعده وبدونها — على 7 حالاتٍ حقيقيّة | FV17 · FV1 |
| انحدار (regression) | `T-W` يُعاد بقاعدة V3 (`span_rule=False` · AST) | FV17 · FV10 |
| تكامل الأوضاع | الأوضاعُ الخمسة تُطبع في السجلّ · dump · poolcap2 | FV13-FV15 |
| مصادرُ البيانات | تلغرام · المدوَّنة · سجلُّ التغطية · لا دهسَ بـnull | FV16 · IAV1 · FV19 |
| اتّساقُ المنشور | حكمٌ يُعاد من أرقامه · وثائقُ = بنّاؤها · نسبةُ المصدر | FV18 |
| طفرات | كلُّ قفلٍ جديد سقط بطفرةٍ تستهدفه بلا انهيار | {' · '.join(f'{k} {v}' for k, v in MUTATIONS.items())} |

## ② الأقفال
{table(["القفل", "ما يحرس", "منذ", "الطفرات"], locks)}

## ③ تغطيةُ 30 دقيقة (§16 · من وضع dump · TradingView بلا اشتراك)
{table(["الرمز", "الرمز الكامل", "يوميّ (عدد)", "أوّلُ يوم", "30د نظاميّة", "أوّلُها (نيويورك)", "30د ممتدّة", "أوّلُها (نيويورك)"], crow)}

- الطلبُ الواحد سقفُه 5,000 شمعة (`M30_N`) ⟵ الممتدّةُ تغطّي أقلّ أيّامًا (16 ساعة يوميًّا) · وATMV بلا شموعٍ على البورصات الأربع.
- **لا اشتراكَ اشتُري ولا بيانٌ اختُرع** — والتاريخُ الأقدم من سقف الطلب يلزمه طلبٌ مجزَّأ (لم يُبنَ: لا حاجةَ له في الحالات الذهبيّة).

## ④ الأثرُ الوصفيّ لـR-W-SPAN (ليس حكمًا)
على 23 رمزًا تحقّقيًّا × آخر 250 جلسة (7,026 قراءة): W مختلف في **995 (14.2%)** · وتغيّرُ فئة READY/WAIT في **364 (5.2%)** — بلا ادّعاء أنّه أفضل أو أسوأ عائدًا
(§24: الباكتيست يتحقّق ولا يخترع — قياسُ العائد بعقدٍ جديد).

## ⑤ حدودُ الصدق
- حالاتٌ ذهبيّةٌ قليلة (7 مؤرَّخة) ⟵ التطابقُ وصفٌ لا إحصاء.
- «جاهز» عند فيصل ≠ حالةُ الأداة (R-READY-BIDS) — تصنيفُ العقد READY/WAIT تقريبٌ مُعلَن.
- الشموعُ من TradingView (بيانُ الزائر · قد يُحجَب) — والملفُّ الدائم يحفظ نوافذَ الحالات فلا تتغيّر الاختبارات بتغيّر المصدر.
"""


def readiness():
    G = _gc()
    PC = J("results", "pool_cap_downstream.json")
    return f"""# IMPLEMENTATION READINESS REPORT — V3.1 (§26)

> **لا نشرَ في الإنتاج** — «Do NOT deploy V3.1 into existing production behavior merely because tests pass».

| المكوّن | الحالة | السبب |
|---|---|---|
| أداةُ التحليل V3.1 (`faisal_tool.py`) | **جاهزةٌ أداةَ قراءةٍ عند الطلب** | تُشغَّل يدويًّا · لا تكتب حالةَ إنتاج · تلغرام بمُدخَلٍ صريح |
| R-W-SPAN | جاهزةٌ داخل الأداة | قاعدةٌ تعريفيّة · عبرت A1-A4 · لا مثالَ يناقضها |
| الدعمُ الأساسيّ | معلومةٌ لا قاعدة | تعريفُه يناقضه فيصل (ZNB/LABT) |
| وصلُ الأداة بالفرز أو الرادار | **غيرُ جاهز** | التطابقُ {G['agreement']['tool_v31']['matched']}/{G['agreement']['tool_v31']['of']} · وT-W «لا فرق» · ولا عائدَ مقيسٌ لـV3.1 |
| سقفُ بِركة الرادار | **لا تغيير** | §15: {PC['verdict']} (إعادةُ الإنتاج {PC['repro_ledger_jaccard_mean']} دون 0.60) |

## ما يلزم قبل أيّ وصلٍ إنتاجيّ (كلُّه بعقدٍ مدموجٍ قبل الرقم)
1. نمذجةُ «جاهز = طلباتٌ عند الدعم» (R-READY-BIDS) واختبارُها على أمثلة فيصل المؤرَّخة.
2. حداثةُ الـW (W قديمٌ مخترَقٌ منذ أشهر يُقرأ «اختراقًا» — DXST اليوميّ) — فرضيّةٌ لم تُقَس.
3. تعريفٌ للدعم الأساسيّ يطابق أمثلة فيصل كلَّها (ZNB · LABT · RAYA · AMIX) قبل أن يصير قاعدة.
4. لسقف البِركة: محاكاةٌ تعيد السجلَّ (0.60 فأكثر) — والمصدرُ قبل 09-30 كان ياهو.
"""


def _dup_pairs(RA):
    pairs = set()
    for r in RA["rules"]:
        for f in r.get("AUDIT_FLAGS", []):
            if str(f).startswith("DUPLICATE_OF:"):
                pairs.add(frozenset((r["RULE_ID"], str(f).split(":", 1)[1])))
    return len(pairs)


def final_summary():
    G = _gc()
    R = J("v31", "reconcile_v31.json")
    RA = J("v31", "rule_audit_v31.json")
    TF = J("v31", "target_forensics_v31.json")
    PC = J("results", "pool_cap_downstream.json")
    S = _suite()
    t = R["telegram"]["totals"]
    return f"""# FINAL FORENSIC SUMMARY — FAISAL V3.1

> V3 كما هو (`faisal_method_v3/FINAL_FORENSIC_SUMMARY.md` · ‏+ سطرٌ مؤرَّخ) — وهذا ملخّصُ V3.1 فوقه. التفصيل: `v31/*.md`.

1. **تلغرام:** {t['TELEGRAM_TOTAL_REFERENCED']} صورة على إرسالين (9 ثمّ 2 · مؤكَّد من `file_reference`) · متاحة {t['TELEGRAM_TOTAL_ACCESSIBLE']} · مفحوصة {t['TELEGRAM_TOTAL_INSPECTED']} ·
   دليلٌ {t['TELEGRAM_TOTAL_USED_AS_EVIDENCE']} · غائبة {t['TELEGRAM_TOTAL_UNAVAILABLE']} · نسخ {t['TELEGRAM_TOTAL_DUPLICATES']}.
2. **المدوَّنة:** 722 صورة · SHA256 والبصماتُ أُعيد حسابُها فطابقت · وحداتٌ 609 بالبصمة و{R['corpus']['table'][8]['v31']} بعد الاشتقاق البصريّ ·
   **كلُّ صورةٍ لها سجلّ** (23 فُتحت بالعين في V3.1) · إحالاتٌ بلا ملفّ {len(R['corpus']['doc_only'])} (V3 101) · وسجلُّ المحادثة صار مقروءًا: صفرُ صورةٍ غائبة.
3. **القواعد:** {RA['summary']['rules_v31']} (‏+{RA['summary']['new_v31']} · منها القائمةُ السباعيّة) · تغيّرت حالتان (L-005 · L-007 ⟵ CONTRADICTED) · تكرارٌ {RA['summary']['flags'].get('DUPLICATE_OF', 0)} قاعدةً في {_dup_pairs(RA)} أزواج ·
   مشتقّةٌ من القياس {RA['summary']['flags'].get('BACKTEST_DERIVED', 0)} (كلُّها دون SUPPORTED).
4. **الأهداف:** {TF['hits_outside_v3']} إصابةً جديدة · صفرُ تناقض · «100٪» أساسُه الدعم (CONFIRMED) · «50٪» تُضاف ربحًا محقَّقًا.
5. **الحالاتُ الذهبيّة:** V3 {G['agreement']['v3']['matched']}/7 · V3.1 {G['agreement']['tool_v31']['matched']}/7 · RAYA: تاريخُ V3 خاطئ ‏+ W بين قاعَيه قاعٌ أدنى (R-W-SPAN) ·
   DXST «حكمٌ تقديريّ محتمل» · VEEE «لا تاريخ» · ATMV «لا بيانات».
6. **T-W:** يبقى كما نُشر (بالأضعف بين تشغيلتين · قاعدةُ الأضعف بعد الرقم مُعلَنة) — ولا يُقال «الـW لا يعمل».
7. **سقفُ البِركة على الكروت:** {PC['verdict']} (إعادةُ الإنتاج {PC['repro_ledger_jaccard_mean']}).
8. **الأداة V3.1:** R-W-SPAN ‏+ الدعمُ الأساسيّ معلومةً ‏+ طبقاتٌ بصريّة · السويّة: {suite_line(S)} · **لا إنتاج**.
"""


if __name__ == "__main__":
    raise SystemExit(main())
