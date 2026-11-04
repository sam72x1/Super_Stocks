#!/usr/bin/env python3
"""🕯️📅 `T-DATE-CANDLES` — مجتمعُ ① بالملحق 1 (قراءةٌ فقط · بلا شبكة · بلا كتابة).

العقد `T_DATE_CANDLES_prereg.md` ‏+ الملحق `T_DATE_CANDLES_ADDENDUM_1.md` §④ — كلاهما مدموجان قبل أيّ رقمِ دقّة.
- **(A)** الوحداتُ المؤرَّخة بالرقم (`price`/`indicator`) بصورةٍ موجودة في الخريطة يحمل سجلُّ عينها بصمةَ المرساة
  (`faisal_derived_dates.tsv`) — والحقيقةُ تاريخُ المرساة.
- **(C)** شارتاتُ القرص بتاريخٍ تقويميٍّ مقروءٍ بالعين (`dprec` ‏EXACT أو DAY) ورمزٍ واحد وفريمٍ واحدٍ مدعوم — والحقيقةُ ذلك التاريخ.
- لا (B): تاريخُ رأس الدفعة أو اسمِ الملفّ تاريخُ الوصول لا تاريخُ الشارت.
- الفريمُ داخل اليوم يلزمه وقتٌ معلنٌ بتوقيت نيويورك في الصورة (‏«ET») وإلّا يُستبعد (‏±1 شمعة لا تُحسب بلا وقت).
- العنقودُ المكرَّر (EXACT · NEAR · RESIZE · CROP) صورةٌ واحدة · وما طابق اختبارًا في (A) لا يُعاد في (C).

الخروج: 0 = المجتمعُ يبلغ الحدّ 33 · 3 = «لا قياس».
"""
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import f0  # noqa: E402

FLOOR = 33                                   # الملحق 1: نصُّ المالك «أكمل ① بملحق الحد 33»
DATE_PRECS = ("EXACT", "DAY")
TF_MAP = {"D": "1D", "W": "1W", "4H": "4H", "2H": "2H", "1H": "1H", "30m": "30m"}   # ما يُبحث بـ`chart_id_tv` (1D · 1W · 240e/a30)
INTRADAY = ("4H", "2H", "1H", "30m")
DUP_REL = ("EXACT", "NEAR", "RESIZE", "CROP")
RC_PASS, RC_NO_MEASURE = 0, 3


def _nums(t):
    return [float(x) for x in re.findall(r"(?<![\d.])-?(\d+(?:\.\d+)?)(?![\d.])", t or "")]


def _text(rec):
    return " ".join(str(rec.get(k, "")) for k in ("seen", "q", "note", "mean"))


def _cluster(fid, inv):
    ds = (inv.get(fid) or {}).get("DUPLICATE_STATUS") or {}
    return ds.get("of") if ds.get("relation") in DUP_REL and ds.get("of") else fid


def population(units, derived, mapping, recs, inv, disk):
    """نقيّة: الوحداتُ ‏+ المراسي ‏+ الخريطة ‏+ سجلّاتُ العين ‏+ الجرد ‏+ القرص ⟵ {"A": […], "C": […], "excluded": […]}."""
    A, C, ex, seen_cl, a_keys = [], [], [], set(), set()
    for (sym, line), u in units.items():
        if not (u["src"] & set(f0.NUMERIC_SOURCES)):
            continue
        d = derived.get((sym, line))
        if not d:
            ex.append({"unit": f"{sym}|{line}", "why": "بلا مرساة"}); continue
        fp = [float(v) for v in re.findall(r"(\d+\.\d+)", d["fingerprint"])]   # كسورُ البصمة وحدَها (لا بارامتراتُ MACD ولا 14)
        cands = []
        for img in u["images"]:
            fid = mapping.get(img)
            if fid and fid in disk and fid in recs:
                ns = [abs(v) for v in _nums(_text(recs[fid]))]
                hit = sum(1 for v in fp if any(abs(n - v) <= max(0.0015 * v, 0.0005) for n in ns))
                cands.append((hit, fid))
        cands = [c for c in cands if fp and c[0] == len(fp)]
        if not cands:
            ex.append({"unit": f"{sym}|{line}", "why": "لا صورةَ تحمل بصمةَ المرساة"}); continue
        fid = sorted(cands)[-1][1]
        tf = (inv.get(fid) or {}).get("TIMEFRAME") or []
        key = (_cluster(fid, inv), d["date"])
        if key in a_keys:
            continue                                   # سطرا الوحدة على الصورة والتاريخ نفسِهما = اختبارٌ واحد
        if len(tf) != 1 or tf[0] not in TF_MAP:
            ex.append({"unit": f"{sym}|{line}", "file": fid, "why": f"فريمٌ غيرُ مدعوم {tf}"}); continue
        a_keys.add(key); seen_cl.add(key[0])
        A.append({"tier": "A", "unit": f"{sym}|{line}", "file": fid, "symbol": sym, "frame": TF_MAP[tf[0]], "truth": d["date"],
                  "truth_src": d["method"]})
    a_sym_date = {(r["symbol"], r["truth"]) for r in A}
    for fid in sorted(recs, key=lambda s: (s.split("_")[0], int(re.sub(r"\D", "", (s.split("_") + [""])[1]) or 0), s)):
        x = recs[fid]
        if fid not in disk or x.get("dprec") not in DATE_PRECS:
            continue
        m = re.match(r"^(\d{4}-\d{2}-\d{2})(?: (\d{2}):(\d{2}))?$", str(x.get("date", "")).strip())
        if not m:
            ex.append({"file": fid, "why": "تاريخٌ غيرُ تقويميّ"}); continue
        tk = x.get("tk") or []
        r = inv.get(fid) or {}
        tf = r.get("TIMEFRAME") or []
        itk = r.get("TICKER") or []
        if len(tk) != 1 or (itk and itk != tk):
            ex.append({"file": fid, "why": f"رمزٌ غيرُ واحد {tk}"}); continue
        if len(tf) != 1 or tf[0] not in TF_MAP:
            ex.append({"file": fid, "why": f"فريمٌ غيرُ مدعوم {tf}"}); continue
        if tf[0] in INTRADAY and not (m.group(2) and re.search(r"\bET\b", _text(x))):
            ex.append({"file": fid, "why": "داخل اليوم بلا وقتٍ معلنٍ بتوقيت نيويورك"}); continue
        cl = _cluster(fid, inv)
        if cl in seen_cl:
            ex.append({"file": fid, "why": f"نسخةُ {cl}"}); continue
        if (tk[0], m.group(1)) in a_sym_date:
            ex.append({"file": fid, "why": "مكرَّرٌ في (A)"}); continue
        seen_cl.add(cl)
        C.append({"tier": "C", "file": fid, "symbol": tk[0], "frame": TF_MAP[tf[0]], "truth": m.group(1),
                  "truth_time": f"{m.group(2)}:{m.group(3)}" if m.group(2) else "", "truth_src": f"eye:{x['dprec']}"})
    return {"A": A, "C": C, "excluded": ex}


def load():
    rows = list(csv.DictReader(open(os.path.join(ROOT, "faisal_levels_table.tsv"), encoding="utf-8"), delimiter="\t"))
    derived = {(r["symbol"], r["line"]): r for r in csv.DictReader(open(os.path.join(ROOT, "faisal_derived_dates.tsv"),
                                                                         encoding="utf-8"), delimiter="\t")}
    recs = {}
    for l in open(os.path.join(ROOT, "fm_forensics", "reread", "data", "reread_records.jsonl"), encoding="utf-8"):
        x = json.loads(l)
        recs[x["id"]] = x
    inv = {r["IMAGE_ID"]: r for r in json.load(open(os.path.join(ROOT, "faisal_method_v41", "corpus_audit",
                                                                    "MASTER_CORPUS_INVENTORY.json"), encoding="utf-8"))["rows"]}
    disk = {os.path.splitext(f)[0] for f in os.listdir(os.path.join(ROOT, "faisal_images"))}
    return f0.units(rows), derived, f0._mapping(), recs, inv, disk


def main():
    import closed                                                  # noqa: PLC0415  🔒 الملحق 5 §⑤
    _rc = closed.gate("population")
    if _rc is not None:
        return _rc
    P = population(*load())
    n = len(P["A"]) + len(P["C"])
    print(f"① بنصّ العقد (السعر/المؤشّر): {len(P['A'])} اختبارًا · بالملحق 1 (‏+ تاريخٌ مقروءٌ بالعين): {len(P['C'])} ⟵ المجموع {n} · الحدّ {FLOOR}")
    for r in P["A"] + P["C"]:
        print(f"   {r['tier']} {r['symbol']:6} {r['frame']:4} {r['truth']} {r.get('truth_time','')} ⟵ {r['file']} ({r['truth_src']})")
    why = {}
    for e in P["excluded"]:
        why[e["why"].split(" [")[0].split(" {")[0]] = why.get(e["why"].split(" [")[0].split(" {")[0], 0) + 1
    print("🚫 المستبعَد: " + " · ".join(f"{k} {v}" for k, v in sorted(why.items(), key=lambda kv: -kv[1])))
    ok = n >= FLOOR
    print(f"⚖️ {'المجتمعُ يبلغ الحدّ ⟵ تُبنى البطاقاتُ قبل أيّ بحث' if ok else 'دون الحدّ ⟵ «لا قياس» · المحورُ متوقّف (الملحق 1 §⑥)'}")
    return RC_PASS if ok else RC_NO_MEASURE


if __name__ == "__main__":
    sys.exit(main())
