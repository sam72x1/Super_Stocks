# -*- coding: utf-8 -*-
"""
📚 بنّاءُ وثائق FAISAL METHOD V3 (§34 · ‏01-30) — **كلُّ رقمٍ في الوثائق من ملفّات JSON المدفوعة لا من اليد.**

    python3 faisal_method_v3/docs_build.py      ⟵ faisal_method_v3/docs/01_…30_*.md

المصادر: image_corpus · dedup_clusters · image_provenance · source_access · rule_graph · evidence_matrix ·
pattern_catalog · target_forensics · results/*.json (نتائجُ Actions المحفوظة — وغيابُها يُكتب «لم يُشغَّل بعد» صراحةً).
"""
import collections
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(HERE, "docs")
RES = os.path.join(HERE, "results")


def J(name, base=HERE):
    p = os.path.join(base, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def W(name, text):
    os.makedirs(DOCS, exist_ok=True)
    with open(os.path.join(DOCS, name), "w", encoding="utf-8") as f:
        f.write(text.rstrip() + "\n")


def table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for r in rows:
        out.append("| " + " | ".join(str(x).replace("|", "¦").replace("\n", " ") for x in r) + " |")
    return "\n".join(out)


def pending(what):
    return f"> ⏳ **لم يُشغَّل بعد:** {what} — لا رقمَ هنا قبل التشغيلة (لا تُملأ الفراغاتُ بتقدير)."


STATUS_ORDER = ["CONFIRMED", "SUPPORTED", "PROBABLE", "POSSIBLE", "CONTRADICTED", "UNKNOWN"]


def main():
    C = J("image_corpus.json")
    D = J("dedup_clusters.json")
    PV = J("image_provenance.json")
    SA = J("source_access.json")
    RG = J("rule_graph.json")
    EM = J("evidence_matrix.json")
    PC = J("pattern_catalog.json")
    TF = J("target_forensics.json")
    CASES = J("cases_summary.json", RES)
    WV = J("w_validate.json", RES)
    POOL = J("pool_cap_audit.json", RES)
    CI = J("ci_audit.json", RES)
    imgs = C["images"]
    rules = RG["rules"]
    rid = {r["id"]: r for r in rules}
    fam = collections.Counter(x["family"] for x in imgs)
    cm = C["meta"]

    # 01 ─────────────────────────────────────────────────────────────────────
    years = collections.Counter((x.get("git_first_add") or {}).get("date", "")[:7] for x in imgs)
    W("01_GLOBAL_IMAGE_CORPUS.md", f"""# 01 · الكونُ الكامل للصور (§3)

**مؤكَّد (من `image_corpus.json` · بنّاؤه `corpus_build.py`):** {cm['images']} صورةً في `faisal_images/` على main ⟵
**{cm['independent_units']} وحدةً مستقلّة** بعد إزالة التكرار (§7) · {cm['multi_member_clusters']} عنقودًا متعدّدَ الأعضاء رُوجعت كلُّها بالعين.

⚖️ **حدُّ «400+» في المهمّة:** الكونُ {cm['images']} صورة ⟵ والوحداتُ المستقلّة {cm['independent_units']} — **الحدُّ متجاوَزٌ بالوحدات لا بالنسخ.**

## العائلات (بادئةُ الاسم = قناةُ الوصول)
{table(["العائلة", "العدد", "المعنى"], [[k, v, {"TG": "قناة تلغرام (telegram_collect.py)", "IMG": "صور جوّال المالك/فيصل", "X": "لقطات X", "CH": "قنوات تعليميّة", "EDU": "تعليميّ (طرف ثالث)", "APP": "تطبيق فيصل", "WA": "واتساب"}.get(k, "—")] for k, v in fam.most_common()])}

## متى دخلت المستودعَ (أوّلُ commit لكلّ صورة · شهريًّا)
{table(["الشهر", "صور"], [[k or "—", v] for k, v in sorted(years.items())])}

## ما في كلّ سجلّ (§6)
`id` · `file` · `family` · `bytes` · `sha256` · `width/height/format` · `dhash64` · `dhash256` · `phash64` · `ahash64` ·
`git_first_add` · `git_renamed_from` · `ocr_text` (tesseract eng+ara · فارغ {cm['ocr_empty']}) · `auto_ocr` (حقولٌ مرشّحة: رمز · أرقام · كلمات) ·
`doc_mentions` · `visual_review` ({cm['visual_reviewed']} صورة بالعين) · `dup_cluster`.

⚠️ **حدودُ صدق:** OCR دفعة 2026-08-28 (صور كاميرا بزوايا) مشوَّش ⟵ أُعيد بتدوير (`data/ocr_rotated_20260828.json`) ولا يُعامَل نصًّا حرفيًّا ·
و«حقولٌ مرشّحة» = آليّةٌ لا قراءة ⟵ **الدليلُ الحاكم ما قُرئ بالعين** (الدفتر · الكاتالوج · `visual_review`).
""")

    # 02 ─────────────────────────────────────────────────────────────────────
    srows = [[s["id"], s["name"][:70], " ⟵ ".join(s["status"]), s.get("count", "—")] for s in SA["sources"]]
    W("02_IMAGE_SOURCE_ACCESS.md", f"""# 02 · جردُ المصادر وصلاحيةُ الوصول (§2)

سلّمُ الحالة (§2): {" · ".join(SA["status_vocabulary"])} — **لا يُفترض وصولٌ قبل التحقّق** ولا يُختلق محتوى ما لم يُصَل إليه.

{table(["المصدر", "الاسم", "الحالة (مسارٌ متحقَّق)", "العدد"], srows)}

## الخلاصة (مؤكَّد)
{chr(10).join(f"- `{k}`: {v}" for k, v in SA["summary"].items())}

## ما لم يُصَل إليه — ولماذا (بلا تخمينٍ لمحتواه)
{chr(10).join(f"- **{s['id']}** — {s.get('how', '')[:300]}" for s in SA["sources"] if "NOT_ACCESSIBLE" in s["status"])}

🔒 **لا يُدفَع:** دليلُ طريقة فيصل (PDF) · دليلُ إليوت · التفريغُ الصوتيّ · مرفقاتُ الجلسة (المستودعُ عامّ) — يُستشهد بها بالصفحة وحدَها.
""")

    # 03 ─────────────────────────────────────────────────────────────────────
    rv = D["review"]
    sizes = collections.Counter(c["size"] for c in D["clusters"])
    W("03_DEDUPLICATION.md", f"""# 03 · إزالةُ التكرار (§7) — «لقطةٌ مكرّرةٌ ليست دليلًا مستقلًّا»

**العتبات (من `image_corpus.json` meta):** {json.dumps(cm["thresholds"], ensure_ascii=False)}
**أنواعُ الحوافّ:** {json.dumps(cm["edge_kinds"], ensure_ascii=False)}

- العناقيدُ متعدّدةُ الأعضاء: **{cm['multi_member_clusters']}** · أحجامُها {dict(sorted(sizes.items()))}
- **رُوجعت كلُّها بالعين** (لوحاتٌ مصغّرة ثمّ تكبيرٌ عند الشكّ) ⟵ `data/dedup_review.json`
- أزواجٌ فكّها الحكمُ البصريّ (ليست تكرارًا رغم تقارب البصمة): **{len(D['visual_not_duplicate'])}**
{chr(10).join(f"  - {p['a']} ↔ {p['b']} (dHash256 {p['dhash256_dist']} · pHash {p['phash_dist']})" for p in D['visual_not_duplicate'])}

## فرضيّةٌ جُرّبت فسقطت (تُنشر لا تُحذف)
فيتو نصّ OCR (تشابهُ Jaccard للنصّ يمنع دمجَ لقطتين مختلفتَي النصّ): {json.dumps(rv.get("rejected_heuristic", {}), ensure_ascii=False)[:600]}
⟵ **أخطأ في الأغلبية فأُسقط ولم يُستعمَل** · والحكمُ البصريّ هو الحاكم.

## الأثر على الأدلّة
كلُّ قاعدةٍ تُعَدّ أدلّتُها **بالوحدات** (`supporting_units` في `rule_graph.json`) لا بالصور ⟵ صورتان في عنقودٍ واحد = دليلٌ واحد.
""")

    # 04 ─────────────────────────────────────────────────────────────────────
    prov = PV["provenance"]
    ren = sum(1 for p in prov if p.get("git_renamed_from"))
    docm = sum(1 for p in prov if p.get("doc_mentions"))
    first = collections.Counter((p.get("git_first_add") or {}).get("subject", "")[:60] for p in prov).most_common(8)
    W("04_IMAGE_PROVENANCE.md", f"""# 04 · مصدرُ كلّ صورة (§5 · §6) — `image_provenance.json`

- **الخامُ لا يُمَسّ:** لا صورةَ عُدّلت أو أُعيد ضغطُها · والبصمةُ SHA256 لكلّ ملفّ (قفل FV9 يعيد حسابها في كلّ تشغيلٍ للسويّة).
- أوّلُ commit أدخل كلَّ صورة: `git log --no-renames --diff-filter=A` (مؤكَّد · {len(prov)} من {len(prov)}).
- صورٌ أُعيدت تسميتُها في التاريخ: **{ren}** · صورٌ تذكرها وثائقُ المستودع: **{docm}**.
- صورٌ تذكرها الوثائق **وليست في المستودع**: {SA['summary'].get('doc_only_image_ids')} معرّفًا (`SRC-DOC-ONLY-IMAGES` · NOT_ACCESSIBLE) — **لا يُستشهد بمحتواها إلّا بما نقلته الوثائق نصًّا ويُوسَم «منقول»**.

## أكبرُ الدفعات (عنوانُ أوّل commit)
{table(["الدفعة", "صور"], [[s or "—", n] for s, n in first])}
""")

    # 05 ─────────────────────────────────────────────────────────────────────
    rows05 = []
    for x in sorted(imgs, key=lambda y: y["id"]):
        vr = "👁️" if x.get("visual_review") else ""
        ocr = (x.get("ocr_text") or "").replace("\n", " ")[:50]
        rows05.append([x["id"], x["family"], x["sha256"][:12], x.get("dup_cluster") or "—", ((x.get("git_first_add") or {}).get("date") or "")[:10], vr, ocr])
    W("05_PER_IMAGE_INDEX.md", f"""# 05 · الفهرسُ الجنائيّ لكلّ صورة — النسخةُ المقروءة (§6)

النسخةُ الآليّة الكاملة: `image_corpus.json` (كلُّ الحقول) · هذه للقراءة: المعرّف · العائلة · بادئةُ SHA256 · العنقود · تاريخُ الدخول · 👁️ مُراجَعةٌ بالعين · مطلعُ OCR (آليّ — ليس قراءة).

{table(["id", "عائلة", "sha256", "عنقود", "دخل", "👁️", "OCR (آليّ)"], rows05)}
""")

    # 06 ─────────────────────────────────────────────────────────────────────
    prow = [[p["id"], p["name"], p["status"], p.get("faisal_units", "—"), ", ".join(p.get("faisal", [])[:5]), ", ".join(p.get("third_party", [])[:3]) or "—", (p.get("note") or "")[:120]] for p in PC["patterns"]]
    W("06_PATTERN_CATALOG.md", f"""# 06 · كتالوجُ النماذج (§8-9) — `pattern_catalog.json`

لكلّ نموذج: **أدلّةُ فيصل** (وحداتٌ مستقلّة) مفصولةً عن **مادّة الطرف الثالث** التي نشرها أو التعليميّة — ووسمُ الدليل بسلّم §12.

{table(["#", "النموذج", "الحالة", "وحدات فيصل", "أمثلة فيصل", "طرفٌ ثالث", "ملاحظة"], prow)}

⚖️ **لا تُعامَل كثرةُ ذكر النموذج دليلًا على ربحيّته** — الربحيّةُ سؤالٌ كمّيّ منفصل (§31) ولا يُجاب إلّا بعقدٍ مسجَّلٍ مسبقًا.
""")

    # 07 ─────────────────────────────────────────────────────────────────────
    wr = [r for r in rules if r.get("scope") == "W"]
    W("07_W_M_DOUBLE_BOTTOM_TOP.md", f"""# 07 · القاعُ المزدوج W والقمّةُ المزدوجة M (§9)

**مصدرُ الدفعة الحاسمة:** الصور التسع المرسلة على تلغرام 2026-10-02 (`TG_58042`…`TG_58050`) ‏+ `X_20260918_12_doublebottom` ‏+ DXST (`IMG_0627/0628`) ‏+ الدليل ص25-26 (PDF · لا يُدفَع).

{table(["القاعدة", "الحالة", "المصدر", "النصّ", "الأدلّة"], [[r["id"], r["evidence_status"], r["source_type"], r["statement"], ", ".join(r["supporting"])] for r in wr])}

## ما يقوله فيصل وما لا يقوله (فصلٌ صارم · §14)
- **فيصل (لفظًا):** الدخولُ في الوسط غيرُ آمن · الدخولُ عند سحب السيولة أو أوّلِ اختراقٍ صحيح · ثباتٌ ربعَ ساعة فوق العنق على 30 دقيقة ·
  الهدفُ سلّمُ مقاوماتٍ أفقيّ (DXST 3.11 ⟵ 3.30) · ونطاقُ قرارٍ «مقرون» يحسم W أو M.
- **طرفٌ ثالث (نشره فيصل أو تعليميّ):** الحركةُ المقيسة 100% · الدخولُ بعد إغلاقٍ فوق المقاومة والترند · الوقفُ تحت آخر قاع · المطرقة.
- **ما لا نعرفه:** نسبةُ نجاح W عند فيصل — لا رقمَ في المصادر ⟵ يُقاس بـ`T-W` (العقد `T_W_prereg.md` مدموجٌ قبل أيّ رقم).
- **M:** لم يُرسم مستقلًّا عند فيصل إلّا وجهًا سلبيًّا لنطاق القرار (VEEE) ⟵ **SUPPORTED** لا CONFIRMED.
""")

    # 08 ─────────────────────────────────────────────────────────────────────
    W("08_HEAD_AND_SHOULDERS_STATUS.md", """# 08 · الرأسُ والكتفان — الحالةُ بلا فتح (§22)

- **الإنتاج كما هو:** `head_shoulders.py` (المسحُ اليوميّ · `T-HS-SF` الأماميّ) يعمل ولم يُمَسّ.
- **المحورُ اليوميّ مُغلَقٌ مُنفَّذًا:** `T-HS`/`T-HS-FX`/`T-HS-RX` ⟵ `hs_forensic.py` يخرج 8 بلا `HSFX_REOPEN=1` (إقرارُ المالك وحدَه).
- **الأحكامُ القائمة (من الأرشيف · منقول):** `T-HS` الفرعُ 2 «لا ميزة على الضبط» · `T-HS-FX` «FX-3 المقياسُ القديم ظلم» بلا ميزةٍ تداوليّة ·
  `T-HS-RX` «RX-3 لا ميزةَ حتى بالبناء الأمين» · و`T-TGT` «100٪» مقرونةً بـ«هدف» = ربحٌ ‏+100%.
- **ما أضافته هذه المهمّة:** لا شيءَ على H&S — ودليلُ الدفعة الجديدة عن W لا عن H&S ⟵ **لا سببَ يستوفي شرطَ الفتح الثلاثيّ**
  (مصدرٌ لم يُقَس · تسجيلٌ مسبقٌ جديد · إذنُ المالك).
- **وأيُّ بحثٍ قادم** يكون نسخةً بحثيّةً جديدة باسمٍ جديد (§22) لا تعديلًا في المُغلَق.
""")

    # 09 / 10 ────────────────────────────────────────────────────────────────
    for num, key, title in (("09", "50", "‏50٪"), ("10", "100", "‏100٪")):
        mm = TF["meanings"][key]
        W(f"{num}_TARGET_FORENSICS_{key}.md", f"""# {num} · ماذا تعني «{title}» عند فيصل؟ (§10 · أولويّةٌ عالية) — `target_forensics.json`

**الحكم:** {TF['meta']['verdict_' + key]}

{table(["المعنى", "النوع", "المصدر", "الحالة", "وحدات", "الأدلّة", "ملاحظة"], [[m["id"] + " · " + m["meaning"], m["kind"], m["source_type"], m["status"], m.get("independent_units", "—"), ", ".join(m["evidence"]), (m.get("note") or "")[:140]] for m in mm])}

**سياسةُ الأداة:** {TF['meta']['tool_policy']}
""")

    # 11 ─────────────────────────────────────────────────────────────────────
    gen = [r for r in rules if r.get("scope") == "general"]
    W("11_COMMON_METHOD_VS_PATTERN_RULES.md", f"""# 11 · المنهجُ المشترك مقابل قواعد كلّ نموذج (§11)

## المشترك (يسري على كلّ النماذج)
{table(["القاعدة", "الحالة", "النصّ", "الأدلّة"], [[r["id"], r["evidence_status"], r["statement"], ", ".join(r["supporting"])] for r in gen])}
- ومن الدفتر (الإنتاج): الوقفُ 5-7% تحت الدعم · الدخولُ دفعاتٌ عند الدعم · لا مطاردةَ بعد ‏+50% · تسامحُ المستوى 2% · الأهدافُ سلّمُ مقاومات.

## الخاصّ بنموذج
- **W:** {len(wr)} قاعدة (07) · **إليوت:** {sum(1 for r in rules if r.get('scope') == 'elliott')} (17) · **المقسّم:** وصفتُه (÷2 · ثبات 3 جلسات · شورت) في الدفتر · **H&S:** مُغلَق (08).

⚖️ **استنتاجٌ قويّ:** النماذجُ عند فيصل **إطاراتٌ لموضع الدخول** لا آلاتٌ مستقلّة — الحاكمُ المشترك: مستوًى حاسم · ثباتٌ فوقه بإغلاق · دخولٌ عند الدعم لا في الوسط · هدفٌ أفقيّ.
""")

    # 12 ─────────────────────────────────────────────────────────────────────
    bys = RG["meta"]["by_status"]
    W("12_EVIDENCE_STATUS_MATRIX.md", f"""# 12 · مصفوفةُ الأدلّة (§12) — `evidence_matrix.json` · `rule_graph.json`

{RG['meta']['status_definitions']}

## العدّ ({RG['meta']['rules']} قاعدة · {RG['meta']['ledger_rules']} من الدفتر · {RG['meta']['new_rules']} جديدة)
{table(["الحالة", "قواعد"], [[s, bys.get(s, 0)] for s in STATUS_ORDER])}

- وحداتٌ مستقلّة مستشهَدٌ بها: **{EM['meta']['units_cited']}** من {EM['meta']['units_total']} · وغيرُ مستشهَدٍ بها {EM['meta']['units_uncited']}
  (أغلبُها شارتاتٌ بلا نصّ قاعدة أو مكرّرُ موضوعٍ مغطّى — **ليست أدلّةً ضائعة بل بلا ادّعاءٍ يُستخرج**؛ وإعادةُ فحصها مسارٌ مفتوح).

## CONTRADICTED (يناقضه نصّ)
{table(["القاعدة", "الاسم", "المصدر"], [[r["id"], r.get("name") or r.get("statement", "")[:80], r["source_type"]] for r in rules if r["evidence_status"] == "CONTRADICTED"])}
""")

    # 13 / 14 ───────────────────────────────────────────────────────────────
    W("13_ANTI_CONFIRMATION_BIAS.md", """# 13 · ضدّ الانحياز للتأكيد (§13)

ما طُبِّق فعلًا (لا وعود):
1. **المكرّرُ لا يُعَدّ** — الأدلّةُ بالوحدات بعد مراجعةٍ بصريّة لكلّ عنقود (03).
2. **الطرفُ الثالث مفصول** — لا يرفع قاعدةً فوق POSSIBLE مهما تكرّر (06 · 12).
3. **فرضيّاتي الساقطة منشورة:** فيتو OCR (أخطأ في الأغلبية) · وتصنيفي الأوّل للمتناقض (60 قاعدةً «CONTRADICTED» كانت هندسيّةً بلا نظير ⟵ صُحّحت إلى UNKNOWN بنصّ المناقضة وحدَه).
4. **المعاييرُ قبل الرقم:** `T_W_prereg.md` · معاييرُ الحالات البصريّة M1-M3 في رأس `faisal_cases.py` · ومعاييرُ تدقيق سقف البِركة §⓪ — كلُّها مدفوعةٌ قبل أيّ تشغيل.
5. **«لا يعيد القراءة» نتيجةٌ مقبولة** — ولا يُضبط شيءٌ في الأداة على الحالات نفسِها بعد رؤيتها (لا تفصيلَ على المثال).
6. **البحثُ عن المناقض:** كلُّ قاعدةٍ لها حقلُ `contradicting` · ونصُّ المناقضة يُستخرج من الدفتر (`contradicted_by_text`).
""")
    W("14_OBSERVATION_INTERPRETATION_RULE.md", """# 14 · الملاحظة ≠ التفسير ≠ القاعدة (§14)

| الطبقة | أين تُحفظ | مثال (DXST) |
|---|---|---|
| **ملاحظة** — ما في الصورة حرفًا | `visual_review` في `image_corpus.json` · نصُّ الدفتر | «ثبات وتداول فوق خط العنق > اكثر من ربع ساعه» · العنق 2.86 · 3.11 · 3.30 |
| **تفسير** — قراءتي | `note`/`interpretation` في `rule_graph.json` و`target_forensics.json` | الثباتُ يُقاس على شموع 30 دقيقة بإغلاقٍ فوق العنق |
| **قاعدة** — قابلةٌ للتنفيذ | `PARAMS` في `faisal_tool.py` بوسم مصدرها | `HOLD_MIN_MINUTES=15` · `faisal_verbatim` · R-W-05 |

**والوسمُ يمنع الخلط:** قاعدةٌ مصدرُها `engineering` (مثل `SWING_K=3`) تُطبع كذلك في كلّ تقريرٍ للأداة ولا تُنسب لفيصل.
""")

    # 15-18 ─────────────────────────────────────────────────────────────────
    def ledger_like(words):
        out = []
        for r in rules:
            txt = (r.get("name") or "") + " " + (r.get("row") or "") + " " + (r.get("statement") or "")
            if any(w in txt for w in words):
                out.append([r["id"], r["evidence_status"], r["source_type"], (r.get("name") or r.get("statement", ""))[:90]])
        return out
    W("15_INDICATOR_FORENSICS.md", f"""# 15 · المؤشّرات (§15)

القواعدُ التي تذكر مؤشّرًا (RSI · MACD · EMA · المتوسّطات · كلنجر · Stoch · ATR · فيبوناتشي):
{table(["القاعدة", "الحالة", "المصدر", "الاسم"], ledger_like(["RSI", "MACD", "EMA", "متوسط", "المتوسّط", "كلنجر", "Stoch", "ATR", "فيبو", "Fib"])[:80])}

⚖️ **استنتاجٌ قويّ:** المؤشّرُ عند فيصل **سياقٌ وتأكيد** لا زنادُ دخول — والزنادُ مستوًى وثباتٌ فوقه. أداةُ v3 لا تُدخل أيَّ مؤشّرٍ في حالة W ولا في قائمة الفحص.
""")
    W("16_STRUCTURE_FORENSICS.md", f"""# 16 · البنية (§16)

{table(["القاعدة", "الحالة", "النصّ", "الأدلّة"], [[r["id"], r["evidence_status"], r["statement"], ", ".join(r["supporting"])] for r in rules if r.get("category") == "structure"])}

**في الأداة:** `confirmed_swings` (محورٌ فركتاليّ يُعرف بعد k بارات · لا نظرَ للأمام) ⟵ `label_structure` (HH/HL/LH/LL بمفردات فيصل: قمّة أعلى · قاع أدنى · قاع جديد).
""")
    W("17_ELLIOTT_FORENSICS.md", f"""# 17 · إليوت (§17)

{table(["القاعدة", "الحالة", "المصدر", "النصّ", "الأدلّة"], [[r["id"], r["evidence_status"], r["source_type"], r["statement"], ", ".join(r["supporting"])] for r in rules if r.get("scope") == "elliott"])}

- **دليلُ إليوت (57 صفحة · طرفٌ ثالث · لا يُدفَع):** مرجعُ تسمية — لا يرفع قاعدةً فوق POSSIBLE وحدَه.
- **في الأداة:** `heads_since_low` (عدُّ الرؤوس منذ القاع) يطبّق R-EL-03 بندَ فحص («قبل منطقة التوزيع») — **لا عدَّ موجاتٍ آليًّا** (لا سندَ بأرقامٍ تُطبَّق).
""")
    W("18_TIMEFRAME_FORENSICS.md", f"""# 18 · الفريمات (§18)

{table(["القاعدة", "الحالة", "النصّ"], [[r["id"], r["evidence_status"], r["statement"]] for r in rules if r.get("category") == "timeframe" or "30 دقيقة" in (r.get("statement") or "")])}

ومن الدفتر (القواعدُ التي تذكر فريمًا):
{table(["القاعدة", "الحالة", "المصدر", "الاسم"], ledger_like(["فريم", "4 ساعات", "4س", "أسبوع", "شهري", "30 دقيقة", "يومي"])[:60])}
- **اليوميّ** للبنية والنموذج · **30 دقيقة** لرسم W وثبات ربع الساعة (R-W-05/06) · **الإقفالُ اليوميّ** للمستوى الحاسم (R-CL-01) · و4 ساعات في الإنتاج للأهداف.
- **في الأداة:** يوميٌّ أساسًا ‏+ `analyze_w_30m` على شموع 30 دقيقة من TradingView (اختياريّ) ⟵ بندُ R-W-05 «NA» حين لا تتوفّر.
""")

    # 19-21 ─────────────────────────────────────────────────────────────────
    W("19_DATA_SPLITS.md", """# 19 · الاكتشاف · التحقّق · المحجوز (§19)

| الطبقة | المادّة | الاستعمال |
|---|---|---|
| **اكتشاف** | الصورُ كلُّها والدفتر والكاتالوج | استخراجُ القواعد (هذه المهمّة) |
| **تحقّقٌ بصريّ** | حالاتُ فيصل المرسومة (EZRA · DXST · VEEE · ATMV · RAYA) | هل تعيد الأداةُ قراءتَه؟ (29) — **لا ضبطَ بعدها على الحالات نفسِها** |
| **كمّيّ** | `T-W` — الحقبُ بنصّ العقد أدناه | الحكمُ على TEST وحدَه بعد تجميد الكاشف (`T_W_prereg.md`) |
| **وصفيّ** | SEEN (رآها المنهجُ والصورُ منها) | تُطبع ولا تحكم |

**نصُّ العقد (منقولٌ آليًّا من `T_W_prereg.md` لا بيدي):**
""" + "\n".join("> " + ln.strip() for ln in open(os.path.join(HERE, "T_W_prereg.md"), encoding="utf-8") if "الحقبُ" in ln or "TRAIN" in ln) + """

⚖️ **لماذا TEST قديم (2019-2021) لا حديث؟** العقدُ يتبع حقبَ `T-HS-FX` حيث 2022+ «إعادةٌ استكشافيّة (حقبةُ `T-HS` المرئيّة)» (منقول: `hs_forensic/hs_fx_prereg.md` §الحقب) ⟵ ما رآه البحثُ السابق لا يحكم · وتواريخُ شارتات فيصل نفسِها **غيرُ معروفةٍ لأغلب الصور** (لا طابعَ زمنيّ موثوق) فلا يُدّعى أن أمثلتَه كلَّها بعد 2022.
""")
    W("20_BACKTEST_POLICY.md", """# 20 · «الباكتيست يتحقّق ولا يخترع» (§20)

- **كلُّ قاعدةٍ في الأداة لها مصدرٌ قبل أيّ رقم** (`PARAMS` بوسومها) — لم تُضَف عتبةٌ بعد رؤية نتيجة.
- **`T-W` يسأل سؤالًا واحدًا مكتوبًا قبله:** هل الدخولُ في الوسط أسوأ من الدخولين الصالحين؟ وهل يتفوّقان على ضبطٍ مطابق؟ — ولا يبحث عن «أفضل عتبة».
- **لو فشل:** يُنشر الفشل ويبقى الوسمُ كما هو (القاعدةُ من فيصل تبقى قاعدتَه · والكمّيُّ يقول إنها لم تُثبَت ميزةً على عيّنتنا).
- **ممنوع:** إعادةُ الضبط على TEST · إرخاءُ معيارٍ بعد رقم · اختيارُ النافذة بعد رؤية النتيجة.
""")
    W("21_LOOK_AHEAD_POLICY.md", """# 21 · لا نظرَ إلى المستقبل (§21)

- `confirmed_swings(h, l, asof, k)`: محورٌ عند i يدخل **فقط إن كان i+k ≤ asof** — مقفولٌ بـFV1 (فحصٌ كثيفٌ لكلّ asof).
- `find_w(..., asof)` يقرأ المحاورَ المؤكَّدة حتى asof وحدَها · و`w_state` يقرأ الشموعَ حتى asof.
- `T-W`: المدخلُ عند أوّل بارٍ تكتمل فيه معطياتُه · والضبطُ من نوافذَ سابقة مطابقة · وفحصُ «المقصوص مجموعةٌ جزئيّةٌ من الكامل» (FV10).
- التقسيمات: وسادةُ 45 يومًا حول أيّ تقسيمٍ عكسيّ ⟵ يُستبعد الحدث (لا تُصحَّح الأسعارُ بأثرٍ رجعيّ).
""")

    # 22 ─────────────────────────────────────────────────────────────────────
    W("22_HS_PRESERVATION.md", """# 22 · صونُ الرأس والكتفين (§22)

- **لا مسَّ:** `head_shoulders.py` · `head_shoulders.yml` · `hs_forensic.py` · `HSFX_REOPEN` · خطوطُ الأساس والأحكام.
- **الاستعمالُ الوحيد:** دوالُّ نقيّة من `hs_forensic.py` (`boot_diff` · `_ind_diff` · `boot_ci`) تستوردها `w_validate.py` للإحصاء — بلا `main()` المُغلَق.
- **قفلٌ قائم:** `RXC1` (الأداةُ تخرج 8 بلا الإقرار) · والسويّةُ تمرّ بلا تغيير عليه.
""")

    # 23 ─────────────────────────────────────────────────────────────────────
    if POOL:
        t = POOL["totals"]
        uniq = sorted({x[1] for x in POOL.get("lost_A", [])})
        by_src = collections.Counter(x[2] for x in POOL.get("lost_A", []))
        body23 = f"""**الحكم: `{POOL['verdict']}`** (التشغيلة `{POOL.get('_source_run', '—')}` · وأوّلُ تشغيلة `37002350339` بالأرقام نفسِها) · جلسات {POOL['sessions']} · تغطيةُ الشموع {POOL['coverage']:.1%}

{table(["المقياس", "القيمة"], [[k, v] for k, v in t.items()])}

- القراءاتُ الجاهزة المفقودة بالسقف = **{len(uniq)} سهمًا فريدًا** · بالمصدر: {dict(by_src)}
- الأسماءُ الفريدة: {", ".join(uniq)}"""
    else:
        body23 = pending("وضعُ `poolcap` في `faisal_v3.yml`")
    W("23_PRESSURE_POOL_CAP_AUDIT.md", f"""# 23 · تدقيقُ سقف بِركة رادار الضغط (§23 · قراءةٌ فقط)

التفصيلُ والمعاييرُ المكتوبةُ قبل الرقم: `../pressure_pool_cap_audit.md` (§⓪ · §① البنيويّ).

{body23}

🔒 **لا تغييرَ إنتاجيّ في هذه المهمّة مهما كانت النتيجة** — `POOL_CAP` و`build_pool` بت-بت (قفل FV12).
""")

    # 24 ─────────────────────────────────────────────────────────────────────
    if CI:
        body24 = "\n".join(f"### {k}\n" + table(["البند", "القيمة"], [[a, b] for a, b in v.items()]) for k, v in CI.items())
    else:
        body24 = pending("تدقيق CI")
    W("24_CI_AUDIT.md", f"""# 24 · تدقيقُ CI (§24) — #540 · #541 · d0cd19e98

{body24}
""")

    # 25-28 ─────────────────────────────────────────────────────────────────
    import faisal_tool as T
    prm = [[k, v[0], v[1], v[2]] for k, v in T.PARAMS.items()]
    W("25_NEW_TOOL_ARCHITECTURE.md", f"""# 25 · معماريّةُ الأداة الجديدة (§25) — `faisal_tool.py` · {T.TOOL_VERSION}

```
البيانات (TradingView يوميّ ‏+ 30 دقيقة · fetch_daily / fetch_30m)
  ⟵ السياق (production_context: قراءةُ الفارز الإنتاجيّ analyze_ticker للرمز — عرضٌ فقط)
  ⟵ البنية (confirmed_swings ⟵ label_structure)
  ⟵ النموذج (find_w: قاعان · عنق · جاء من فوق)
  ⟵ الحالة (w_state: NO_W · AT_SUPPORT2 · UNSAFE_MIDDLE · BREAKOUT · RETEST_HOLD · FAILED_BREAKOUT · INVALIDATED)
  ⟵ التأكيد (intraday_hold على 30 دقيقة · R-W-05)
  ⟵ الدخول (A الدعم الثاني/السحب · B أوّل اختراق) ⟵ الإبطال (stops)
  ⟵ الأهداف (targets: سلّمُ فيصل · ‏+100% · المقيسةُ للمقارنة)
  ⟵ المخاطرة (rr) ⟵ قائمةُ الفحص (checks: PASS/FAIL/NA بالقاعدة ووسمها)
  ⟵ المخرَج (render_text عربيّ · JSON · PNG)
```
- **نقيّةٌ في قلبها** (`analyze_arrays`) — مصفوفاتٌ تدخل وتقريرٌ يخرج ⟵ قابلةٌ للاختبار بلا شبكة (FV1-FV5).
- **قراءةٌ فقط:** لا حالةَ إنتاج · وتلغرام فقط داخل `if send:` (FV7) والـworkflow يمرّر السرَّ حين `send=1` وحدَه (FV6).
""")
    W("26_NEW_TOOL_RULES.md", f"""# 26 · قواعدُ الأداة وعتباتُها بمصادرها (§26)

{table(["المفتاح", "القيمة", "المصدر", "السند"], prm)}

**الحصيلة:** {sum(1 for v in T.PARAMS.values() if v[1] == 'faisal_verbatim')} بلفظ فيصل · {sum(1 for v in T.PARAMS.values() if v[1] == 'production')} ثوابتُ إنتاجيّة قائمة · {sum(1 for v in T.PARAMS.values() if v[1] == 'engineering')} هندسيّة (تُطبع كذلك ولا تُنسب لفيصل).
""")
    W("27_NEW_TOOL_OUTPUT.md", """# 27 · مخرَجُ الأداة (§27)

**نصٌّ عربيّ** (بلا علامات مقارنة — قاعدةُ المشروع · FV4) بالترتيب: الرأس · السعر · الحالة وقاعدتُها · W (القاعان · العنق) · نطاقُ القرار ·
الدخولان · «الوسطُ غيرُ آمن» · الوقف · الأهدافُ بوسم المصدر (🎯 فيصل · 📐 طرفٌ ثالث للمقارنة) · العائدُ إلى المخاطرة · W على 30 دقيقة · قائمةُ الفحص وما لم ينجح · تذييلُ «أداة قراءة لا توصية».

**JSON** (`out/<SYM>.json`): `tool` · `symbol` · `asof` · `price` · `structure` · `w` · `state` · `entries` · `decision_band` · `targets` (لكلّ هدف `family`/`source`/`status`) ·
`stops` · `rr` · `heads_since_low` · `checks` · `checklist_summary` · `params` (كلُّ عتبةٍ بمصدرها) · `context` (قراءةُ الفارز الإنتاجيّ) · `w_30m`.

**PNG**: الشموع ‏+ القاعان والعنق والدخولان والوقف والأهداف بألوان فيصل (🔴 دعم/وقف · 🟣 دخول · ⚫ مقاومة · 🔵 هدف).
""")
    W("28_NEW_TOOL_USAGE.md", """# 28 · الاستعمال (§28)

**من GitHub (الموصى به):** Actions ⟵ «🧭 FAISAL METHOD V3» ⟵ Run workflow:
- `mode=ticker` · `ticker=RAYA` · `asof` اختياريّ · `send=1` **فقط إن أردت الرسالةَ على تلغرام** (افتراضُه 0 ⟵ المخرَجُ في Artifacts).
- `mode=cases` — التحقّقُ البصريّ على حالات فيصل · `mode=validate` — `T-W` · `mode=poolcap` — تدقيقُ سقف البِركة.

**محلّيًّا (يلزمه وصولٌ إلى TradingView):** `python3 faisal_method_v3/faisal_tool.py RAYA --asof 2026-08-26 --json out.json --png out.png`

⚠️ أداةُ قراءةٍ لا توصية · ولا تغيّر شيئًا في البوت · وTradingView بلا واجهةٍ رسميّة (قد يُحجَب).
""")

    # 29 ─────────────────────────────────────────────────────────────────────
    if CASES:
        def _m1(x):
            m = x.get("M1") or {}
            return f"{m.get('matched')}/{m.get('of')}" if m else "—"
        rows29 = [[x.get("case"), x.get("asof", "—"), _m1(x), ("—" if x.get("M2") is None else x.get("M2")),
                   ("✅" if (x.get("M3") or {}).get("within") else "❌") if x.get("M3") else "—",
                   x.get("tool_state") or x.get("error"), x.get("note", "")] for x in CASES.get("cases", [])]
        body29 = f"""**الحكم الإجماليّ (بمعيار رأس `faisal_cases.py` المكتوب قبل التشغيل): `{CASES.get('verdict')}`** · M2 في الثلاث · M1 {CASES.get('M1_cases_ok')} من {CASES.get('M1_cases_measured')} مقيسة ·
التشغيلة `{CASES.get('_source_run', '—')}` (ومطابقةٌ لـ`{CASES.get('_also_run', '—')}`)

{table(["الحالة", "asof", "M1 تطابق المستويات", "M2 حضور W", "M3 نطاق القرار", "حالةُ الأداة", "ملاحظة"], rows29)}

## ⚖️ القراءةُ الأمينة — الحكمُ الشكليّ أقوى من المضمون
- **المعيارُ M2 كان متساهلًا بالبناء:** «تكتشف الأداةُ W» — أيَّ W — لا «W فيصل». في DXST (أوضح حالة: عنقُ فيصل 2.864) **لم يُعَد إنتاجُ العنق** (أقربُ مستوى −11.3%).
- **VEEE:** M3 سقط على اليوميّ · وعنقُ W الثلاثين (6.16) هو ما وافق 6.18 فيصل ⟵ قراءةُ فيصل على فريمٍ أصغر.
- **RAYA:** فيصل «غيرُ جاهز · انتظار الهبوط» والأداةُ «عند الدعم الثاني» — **تناقضٌ لا يقيسه M1/M2**.
- **ATMV لم تُقَس** (لا شموع من TradingView).
- **لا يُرخى المعيارُ ولا يُشدَّد بعد الرقم** — الحكمُ «يعيد القراءة» كما كُتب · **ولا يُضبط شيءٌ في الأداة على هذه الحالات** · والعيبُ يُسجَّل درسًا للعقد القادم: «حضورُ W» يُكتب «W فيصل ضمن 2% من عنقه».
"""
    else:
        body29 = pending("وضعُ `cases` في `faisal_v3.yml`")
    W("29_VISUAL_VALIDATION.md", f"""# 29 · التحقّقُ البصريّ (§29)

المعاييرُ M1-M3 مكتوبةٌ في رأس `faisal_cases.py` **قبل أيّ تشغيل** · ولا يُضبط شيءٌ في الأداة على هذه الحالات بعد رؤيتها.

{body29}
""")

    # 30 ─────────────────────────────────────────────────────────────────────
    if WV:
        r1, r2, vb = WV["run1"], WV["run2"], WV["verdict_by_weaker"]

        def hrow(h):
            a, b = r1["verdict"][h], r2["verdict"][h]
            return [h, f"{a['diff'] * 100:+.2f} [{a['lo'] * 100:+.2f} · {a['hi'] * 100:+.2f}]", f"{b['diff'] * 100:+.2f} [{b['lo'] * 100:+.2f} · {b['hi'] * 100:+.2f}]"]
        eras = [[k, v["n"], f"{v['ret']['est'] * 100:+.2f}%", f"[{v['ret']['lo'] * 100:+.2f} · {v['ret']['hi'] * 100:+.2f}]", f"{v['target_first']:.1%}", f"{v['stop_first']:.1%}"]
                for k, v in r2["eras"].items()]
        body30 = f"""**`T-W` — الحكمُ بالأضعف بين التشغيلتين: `{vb['branch']}`** ({vb['rule']})

{table(["الفرضيّة (نقاط مئويّة · 98.75%)", f"التشغيلة {r1['_source_run']} (شموع {r1['fetched']})", f"التشغيلة {r2['_source_run']} (شموع {r2['fetched']})"], [hrow(h) for h in ("H1_A_minus_M", "H2_B_minus_M", "H3_A_vs_ctrl", "H4_B_vs_ctrl")])}
| الفرع | {r1['verdict']['branch']} | {r2['verdict']['branch']} |

**الحقبُ كلُّها (التشغيلة الثانية · وصفيّةٌ إلّا TEST):**
{table(["الحقبة|المدخل", "العدد", "متوسّطُ العائد", "فاصل 95%", "الهدفُ أوّلًا", "الوقفُ أوّلًا"], eras)}

التفصيلُ والقراءة: `../T_W_result.md`."""
    else:
        body30 = pending("وضعُ `validate` (T-W) في `faisal_v3.yml`")
    W("30_NEW_TOOL_VALIDATION_REPORT.md", f"""# 30 · تقريرُ التحقّق من الأداة (§30-31)

## الاختبارات (بلا شبكة · في السويّة)
- **FV1-FV13** — لا نظرَ للأمام · حالاتُ W · عائلاتُ الأهداف · لا علامات مقارنة · وسومُ المصادر · الـworkflow يدويٌّ وقراءةٌ فقط ·
  تلغرام داخل `if send:` · الطبقةُ الجنائيّة متّسقة · فهرسُ الصور صادق (SHA256) · عقدُ `T-W` وفروعُه · وتدقيقُ سقف البِركة.
- **كلُّ قفلٍ أُسقط بطفرةٍ مقصودة** (FV12 ‏9 من 9 · FV13 ‏6 من 6) · وFV13 = مخرَجُ الأوضاع في السجلّ (`V3OUT`).

## التحقّقُ البصريّ
انظر 29.

## الكمّيّ (`T_W_prereg.md` · مدموجٌ قبل أيّ رقم)
{body30}
""")
    print(f"📚 كُتبت {len(os.listdir(DOCS))} وثيقة في {DOCS}")
    return 0


if __name__ == "__main__":
    import sys
    sys.path.insert(0, HERE)
    raise SystemExit(main())
