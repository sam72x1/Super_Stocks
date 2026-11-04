#!/usr/bin/env python3
"""🕯️📅 `T-DATE-CANDLES` — خريطةُ صور الكاتالوج ⟵ ملفّات القرص (الملحق 1 · قراءةٌ فقط · بلا شبكة).

صورُ الكاتالوج (`IMG_4xxx`-`IMG_8xxx`) أُرسلت للبوت قديمًا فحفظها الجامعُ باسم `TG_<message_id>`. المطابقةُ بالمحتوى:
① نصُّ الكاتالوج لكلّ صورة (فقرتُها إن وُجدت · وإلّا نصُّ القسم · وإلّا مستوياتُ الجدول) مقابل سجلّ العين `reread_records.jsonl`
   للملفّ (الرمز · الفريم · المستويات · النصّ) — الرقمُ يطابق بتسامح 0.15% أو 0.0005 ⟵ `hits/n` ‏+ اتّفاقُ الرمز.
② dHash وعناقيدُ التكرار من `MASTER_CORPUS_INVENTORY.json` (حقلا `PERCEPTUAL_HASH`/`DUPLICATE_STATUS`) للتأكيد: ملفّان في عنقودٍ
   واحد = صورةٌ واحدة · ولا تُعَدّ صورتا كاتالوج «موجودتين» بملفّين من العنقود نفسِه. ⚠️ أصلُ الكاتالوج غيرُ موجود ⟵ dHash لا يقارن
   الأصلَ بالملفّ بل يثبت تمايزَ الملفّات المطابَقة.
③ القرارُ لكلّ صورة في `DECISIONS` أدناه (بيدٍ مكتوبةٍ بسببها) — والسكربتُ يتحقّق منه آليًّا (الملفُّ على القرص · العددُ المطابق ·
   التمايزُ بالعناقيد) ويكتب `data/image_map.tsv` · و`--check` يعيد البناءَ ويقارن بايتًا.

الثقة: **واثق** (نصُّ الصورة نفسِها يطابق 80% فأكثر من أرقامها وثلاثةً فأكثر · أو نصٌّ حرفيٌّ مميَّز · بلا منافسٍ غيرِ مكرَّر) ·
**مرجّح** (نصٌّ خاصٌّ بالصورة بأرقامٍ أقلّ · أو ترتيبُ وسوم الفريم في عنوان القسم) · **مجموعة** (الملفُّ من صور القسم بنصّه المشترك
وهويّةُ العضو غيرُ محسومة) · **ضعيف** (الرمزُ والفريمُ والتجاورُ وحدَها) — و«موجودة» = الثلاثة الأولى · والضعيفُ يُعَدّ وحدَه.
"""
import csv
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import f0  # noqa: E402

OUT = os.path.join(HERE, "data", "image_map.tsv")
FIELDS = ("catalog_image", "disk_file", "confidence", "units", "basis", "hits", "dhash256", "dup_of", "note")
FOUND = ("واثق", "مرجّح", "مجموعة")
TOL_REL, TOL_ABS = 0.0015, 0.0005

# (صورةُ الكاتالوج، الملفّ، الثقة، الأساس، الملاحظة) — الملفُّ «» = غيرُ موجود
DECISIONS = [
    ("IMG_4685", "TG_2127", "واثق", "table", "RSI14 17.512 وأفتر 2.020 حرفًا · TG_1988 يومٌ آخر (RSI 20.770)"),
    ("IMG_5954", "TG_2005", "واثق", "section", "أفتر 4.200 · المستوياتُ الأربعة · قمّة 5.350"),
    ("IMG_6005", "TG_2046", "واثق", "own", "فقرةُ 6005: قمّة 7.210 · «فجوه سعريه» · المستوياتُ كلُّها"),
    ("IMG_6004", "TG_2047", "مجموعة", "section", "{6004·6006} ⟵ {TG_2047 (مقصوصُ TG_2121: منشور 30/03 ‏+ شارت أفتر 4.500) · TG_2045} · الرسائلُ 2045-2047 متتالية"),
    ("IMG_6006", "TG_2045", "مجموعة", "section", "انظر IMG_6004 · TG_2045 بري 5.71 بالمستويات نفسِها"),
    ("IMG_6215", "TG_2115", "واثق", "section", "3.105 (+32.13%) = بصمةُ مرساة السعر"),
    ("IMG_6206", "TG_2120", "واثق", "section", "بري 1.670 · KST وMACD(10,20,3) حرفًا"),
    ("IMG_6216", "TG_2116", "واثق", "section", "Diamond Bottom · المستويات"),
    ("IMG_6297", "TG_2111", "واثق", "section", "1.630 · المستويات"),
    ("IMG_6295", "TG_2110", "مجموعة", "section", "{6295·6298} ⟵ TG_2110 وحدَه (TG_2114 نسختُه RESIZE)"),
    ("IMG_6298", "", "غير موجود", "section", "TG_2114 نسخةُ TG_2110 نفسِها (RESIZE · dHash) ⟵ لا ملفَّ ثانٍ مميَّز"),
    ("IMG_6390", "TG_2105", "واثق", "section", "MACD(12,26,9) ‏−0.214/−0.277 حرفًا"),
    ("IMG_6457", "TG_2536", "مجموعة", "section", "{6457·6459·6458} ⟵ TG_2536 (يوميّ بالأرقام) · ويوميٌّ ولحظيّ مصغَّران بلا أرقام"),
    ("IMG_6459", "TG_2541", "ضعيف", "symbol", "ARAI يوميّ مصغَّرٌ بلا أرقامٍ مقروءة (143×310)"),
    ("IMG_6458", "TG_2539", "ضعيف", "symbol", "ARAI بدقيقةٍ مصغَّرٌ بلا أرقامٍ مقروءة (143×310)"),
    ("IMG_6456", "TG_1941", "واثق", "own", "فقرةُ 6456: 10.38 (+316.87%) · MACD 0.89/0.24/0.66"),
    ("IMG_6455", "TG_1942", "واثق", "own", "فقرةُ 6455: أفتر 3.920 (+31.54%) · المستويات"),
    ("IMG_6464", "TG_2523", "واثق", "section", "أفتر 2.930 · المستويات"),
    ("IMG_6460", "TG_2533", "واثق", "section", "بري 1.170 (+103.37%) · 5 دقائق"),
    ("IMG_6462", "TG_2525", "واثق", "section", "بري 2.070 (+36.18%) · دقيقة"),
    ("IMG_6461", "TG_2530", "واثق", "section", "بري 13.16 · MACD ‏−1.15/−1.00"),
    ("IMG_6466", "TG_2004", "واثق", "section", "أفتر 1.742 · 5 دقائق · المستويات"),
    ("IMG_6465", "TG_2038", "واثق", "own", "فقرةُ 6465: المستوياتُ العشرة · أفتر 1.555"),
    ("IMG_6776", "TG_1973", "مرجّح", "section", "بطاقةُ Engulfing 03/10/2026 · Close 1.83 · أفتر 1.400"),
    ("IMG_6470", "TG_2000", "واثق", "section", "RSI14 37.34 · أفتر 6.26 · المستويات"),
    ("IMG_6701", "TG_1982", "مجموعة", "section", "{6701·6705·6702} = 5د · أسبوعيّ · تغريدة ⟵ {TG_1982 · TG_1983 · TG_1981}"),
    ("IMG_6705", "TG_1983", "مجموعة", "section", "انظر IMG_6701 · TG_1983 مكبَّرُ شارت TG_1981"),
    ("IMG_6702", "TG_1981", "مجموعة", "section", "انظر IMG_6701 · منشورُ فيصل «3.80 ثبات الدعم»"),
    ("IMG_6478", "TG_1994", "واثق", "own", "فقرةُ 6478: DMA(10,50,10) · VWAP 1.246 · RSI 45.247"),
    ("IMG_6480", "TG_1932", "مجموعة", "own", "فقرةُ (6480/6482): بري 2.960 · VMA5 15.87M ⟵ TG_1932"),
    ("IMG_6482", "TG_1986", "ضعيف", "symbol", "مقصوصُ TG_1932 — نسخةٌ من الشارت نفسِه لا صورةٌ ثانيةٌ مؤكَّدة"),
    ("IMG_6479", "TG_1933", "ضعيف", "symbol", "تغريدةُ CDIO (بري 2.960) · الكاتالوجُ لا يقتبس التغريدات"),
    ("IMG_6481", "TG_1989", "ضعيف", "symbol", "تغريدةُ CDIO (أفتر 1.240) · الكاتالوجُ لا يقتبس التغريدات"),
    ("IMG_6761", "TG_1977", "واثق", "section", "تلميحُ الشمعة 04/15/2026 · O 4.840 H 4.860 L 4.560 C 4.74 · VWAP 3.325 — الرمزُ غيرُ ظاهر"),
    ("IMG_6807", "TG_1972", "واثق", "table", "المستوياتُ الأربعة · المحورُ 04/17-05/25"),
    ("IMG_6782", "TG_1971", "واثق", "own", "فقرةُ 6782: أفتر 14.60 · MACD ‏−4.38/−3.65/−0.73"),
    ("IMG_7362", "TG_2104", "واثق", "own", "فقرةُ 7362: 146.02 (+149.65%) · RSI 77.03"),
    ("IMG_8082", "TG_2035", "واثق", "own", "فقرةُ 8082: 7.85 · 23.04/16.51/9.53/14.02/11.84/6.11/7.04"),
    ("IMG_7360", "", "غير موجود", "own", "نسخةُ SMX مقصوصةُ الرأس (RSI 31.53 · 241.84/205/181/158/138) — لا ملفّ يطابق"),
    ("IMG_6816", "TG_1968", "واثق", "table", "بري 1.910 · المستوياتُ الخمسة"),
    ("IMG_7014", "TG_1949", "واثق", "own", "فقرةُ 4س: قمّة 3.080 · قاع 1.410 · المستويات"),
    ("IMG_7028", "TG_1912", "واثق", "own", "فقرةُ 7028: «آخر دعم فنيًا ما يكسره 1.80» حرفًا · قمّة 5.390"),
    ("IMG_7027", "TG_1913", "واثق", "own", "فقرةُ 7027: «رسم المقاومة + الأهداف في حال الصعود» حرفًا · 30 دقيقة"),
    ("IMG_7029", "TG_1911", "واثق", "own", "فقرةُ 7029: «2.14 شمعة الصعود السابقة فنيًا = تكون دعم» حرفًا · 5 دقائق"),
    ("IMG_8107", "TG_2011", "مجموعة", "section", "{8107·8108} ⟵ {TG_2011 مصغَّر · TG_2012 مكبَّر} · أفتر 1.620"),
    ("IMG_8108", "TG_2012", "مجموعة", "section", "انظر IMG_8107"),
    ("IMG_8109", "TG_2007", "مجموعة", "section", "{8109·8110·8111} = ٤س/أسبوعيّ ⟵ {TG_2007 · TG_2008 · TG_2009} متتالية"),
    ("IMG_8110", "TG_2008", "مجموعة", "section", "انظر IMG_8109"),
    ("IMG_8111", "TG_2009", "مجموعة", "section", "انظر IMG_8109 · TG_2009 أسبوعيّ قمّة 40.39"),
    ("IMG_8114", "TG_1896", "مرجّح", "section", "وسمُ القسم «٤س/يومي (8114/8115)» ⟵ 8114 ‏4س: قمّة 26.350 · 10.451/4.718"),
    ("IMG_8115", "TG_1893", "مرجّح", "section", "8115 يوميّ: MA5 4.046 · MA20 5.497 · RSI 35.30 حرفًا"),
    ("IMG_8116", "TG_1901", "مرجّح", "section", "وسمُ القسم «يومي/أسبوعي (8116/8120)» ⟵ 8116 يوميّ: 15.14"),
    ("IMG_8120", "TG_1900", "مرجّح", "section", "8120 أسبوعيّ · المستوياتُ نفسُها"),
    ("IMG_8137", "TG_1881", "واثق", "section", "أفتر 1.591 · المستويات"),
    ("IMG_8187", "TG_1877", "مجموعة", "section", "{8187·8188} ⟵ {TG_1877 (أفتر 7.40 · MACD ‏−3.68/−4.33) · TG_1872 (MA5 7.928 · MA20 9.433 · RSI 25.51)}"),
    ("IMG_8188", "TG_1872", "مجموعة", "section", "انظر IMG_8187"),
    ("IMG_8096", "TG_2022", "واثق", "own", "عنوانُ القسم: بري ‏+9.54% · MA5 7.264 · MA20 6.356 · 3.509"),
    ("IMG_8118", "TG_1903", "مجموعة", "section", "مستوياتُ القسم ⟵ TG_1903 · ومنافسُه TG_1902 (التعليقُ «شمعة هبوط المضارب») — العضوُ غيرُ محسوم"),
    ("IMG_8130", "TG_1892", "مرجّح", "section", "تغريدة 8130 «تهييض 4 مرات» ⟵ TG_1892 «تم تهييض السهم 4 مرات»"),
    ("IMG_8090", "TG_2020", "مجموعة", "section", "{8090·8099·8134·8135} ⟵ {TG_2020 يوميّ شموع · TG_2021 يوميّ خطّيّ}"),
    ("IMG_8099", "TG_2021", "مجموعة", "section", "انظر IMG_8090"),
    ("IMG_8134", "", "غير موجود", "section", "لا ملفَّ ثالثٌ مميَّز (TG_2019 لقطةُ بحثٍ مركّبة)"),
    ("IMG_8135", "", "غير موجود", "section", "انظر IMG_8134"),
]


def _nums(t):
    return sorted({float(x) for x in re.findall(r"(?<![\d.])(\d+(?:\.\d+)?)(?![\d.])", t or "")})


def targets(rows):
    """الصورُ الـ71 مرجعًا: صورُ الوحدات المؤرَّخة بالرقم ‏+ صورُ غير المؤرَّخة (بتكرارها بين المجموعتين)."""
    U = f0.units(rows)
    refs, distinct, units = 0, {}, {}
    for k, u in U.items():
        grp = "numeric" if u["src"] & set(f0.NUMERIC_SOURCES) else ("undated" if u["src"] == {""} else None)
        if not grp:
            continue
        for i in u["images"]:
            distinct.setdefault(i, set()).add(grp)
            units.setdefault(i, []).append(f"{k[0]}|{k[1]}")
    num = {i for i, g in distinct.items() if "numeric" in g}
    und = {i for i, g in distinct.items() if "undated" in g}
    refs = len(num) + len(und)
    return distinct, units, num, und, refs


def build():
    rows = list(csv.DictReader(open(os.path.join(ROOT, "faisal_levels_table.tsv"), encoding="utf-8"), delimiter="\t"))
    distinct, units, num, und, refs = targets(rows)
    recs = {}
    for l in open(os.path.join(ROOT, "fm_forensics", "reread", "data", "reread_records.jsonl"), encoding="utf-8"):
        x = json.loads(l)
        recs[x["id"]] = x
    inv = {r["IMAGE_ID"]: r for r in json.load(open(os.path.join(ROOT, "faisal_method_v41", "corpus_audit",
                                                                    "MASTER_CORPUS_INVENTORY.json"), encoding="utf-8"))["rows"]}
    disk = {os.path.splitext(f)[0] for f in os.listdir(os.path.join(ROOT, "faisal_images"))}
    lev = {}
    for r in rows:
        for i in f0.expand_images(r["images"]):
            try:
                lev.setdefault(i, set()).add(float(r["level"]))
            except ValueError:
                pass
    dec = {d[0]: d for d in DECISIONS}
    assert set(dec) == set(distinct), ("صورٌ بلا قرار", sorted(set(distinct) ^ set(dec)))
    out, clusters = [], {}
    for img in sorted(distinct, key=lambda s: int(s.split("_")[1])):
        _, f, conf, basis, note = dec[img]
        dh = dup = hits = ""
        if f:
            assert f in disk, f"{img}: {f} ليس على القرص"
            assert f in recs, f"{img}: {f} بلا سجلّ عين"
            r = inv.get(f) or {}
            dh = (r.get("PERCEPTUAL_HASH") or {}).get("dhash256") or ""
            ds = r.get("DUPLICATE_STATUS") or {}
            dup = ds.get("of") if ds.get("relation") in ("EXACT", "NEAR", "CROP", "RESIZE") else ""
            # النسخةُ (EXACT · NEAR · RESIZE) = الصورةُ نفسُها ⟵ عنقودٌ واحد · والمقصوصُ (CROP) صورةٌ مشتقّةٌ مستقلّةٌ تُوسَم
            cl = dup if ds.get("relation") in ("EXACT", "NEAR", "RESIZE") else f
            if conf in FOUND:
                assert cl not in clusters, f"{img}: {f} من عنقود {cl} المطابَق سلفًا لـ{clusters[cl]}"
                clusters[cl] = img
            text = " ".join(str(recs[f].get(k, "")) for k in ("seen", "q", "note", "mean"))
            ns = _nums(text)
            L = sorted(lev.get(img, ()))
            h = [v for v in L if any(abs(n - v) <= max(TOL_REL * v, TOL_ABS) for n in ns)]
            hits = f"{len(h)}/{len(L)}" if L else "—"
            tk = recs[f].get("tk") or []
            sym = {u.split("|")[0] for u in units[img] if u.split("|")[0]}
            if sym and tk:
                assert sym & set(tk), f"{img}: الرمزُ {sym} ≠ {tk}"
        fname = next((x for x in sorted(os.listdir(os.path.join(ROOT, "faisal_images"))) if os.path.splitext(x)[0] == f), "") if f else ""
        out.append({"catalog_image": img, "disk_file": fname,
                    "confidence": conf, "units": ",".join(units[img]), "basis": basis, "hits": hits, "dhash256": dh,
                    "dup_of": dup or "", "note": note})
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=FIELDS, delimiter="\t", lineterminator="\n")
    w.writeheader()
    w.writerows(out)
    found = {r["catalog_image"] for r in out if r["confidence"] in FOUND}
    weak = {r["catalog_image"] for r in out if r["confidence"] == "ضعيف"}
    summary = {"distinct": len(distinct), "refs": refs, "found_distinct": len(found),
               "found_refs": len(found & num) + len(found & und), "weak": len(weak),
               "missing": len(distinct) - len(found) - len(weak),
               "numeric_found": sorted(found & num), "undated_found": len(found & und), "undated_total": len(und),
               "numeric_total": len(num)}
    return buf.getvalue(), summary


def main(argv):
    text, s = build()
    if "--check" in argv:
        ok = os.path.exists(OUT) and open(OUT, encoding="utf-8").read() == text
        print("✅ الخريطةُ مطابقة" if ok else "⛔ الخريطةُ تختلف عن البناء")
        return 0 if ok else 1
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"🗺️ المراجعُ {s['refs']} (المؤرَّخةُ بالرقم {s['numeric_total']} · غيرُ المؤرَّخة {s['undated_total']}) = {s['distinct']} صورةً مميّزة")
    print(f"✅ موجودة (واثق · مرجّح · مجموعة): {s['found_refs']} من {s['refs']} مرجعًا = {s['found_distinct']} من {s['distinct']} صورة")
    print(f"   المؤرَّخةُ بالرقم: {len(s['numeric_found'])} من {s['numeric_total']} · غيرُ المؤرَّخة: {s['undated_found']} من {s['undated_total']}")
    print(f"🔸 ضعيف (الرمز والفريم وحدَهما): {s['weak']} · ⛔ غيرُ موجود: {s['missing']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
