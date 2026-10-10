#!/usr/bin/env python3
"""👁️ T-REREAD — بنّاءُ سجلّ إعادة القراءة البصريّة للمدوّنة كاملة.

قراءةٌ فقط: يقرأ `faisal_images/` (البصمات) والجدولَ الموروث `fm_forensics/IMAGE_UTILIZATION_TABLE.csv`
وسجلَّ العين `data/reread_records.jsonl` (يُكتب باليد بعد رؤية كلّ صورة) ⟵ يكتب المُخرَجات الحتميّة.
لا شبكة · لا تلغرام · لا حالةَ إنتاج · ولا يُعدّل صورةً ولا الجدولَ الموروث.

الأوضاع:
  python3 reread_build.py           يبني المُخرَجات كلَّها
  python3 reread_build.py --order   يكتب REREAD_ORDER.txt وحدَه
  python3 reread_build.py --check   يعيد البناءَ في الذاكرة ويقارن بايتًا (خروج 1 عند الاختلاف)
  python3 reread_build.py --next N  يطبع أوّلَ N معرّفًا لم تُقرأ بعد بالترتيب (مساعدٌ للقراءة)
البروتوكول: VISUAL_REREAD_PROTOCOL.md
"""
import csv
import hashlib
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
IMG_DIR = os.path.join(REPO, "faisal_images")
TABLE = os.path.join(REPO, "fm_forensics", "IMAGE_UTILIZATION_TABLE.csv")
RECORDS = os.path.join(HERE, "data", "reread_records.jsonl")
OUT_ORDER = os.path.join(HERE, "REREAD_ORDER.txt")
OUT_REG = os.path.join(HERE, "VISUAL_REREAD_REGISTER.csv")
OUT_COR = os.path.join(HERE, "REREAD_CORRECTIONS.csv")
OUT_SUM = os.path.join(HERE, "VISUAL_REREAD_SUMMARY.md")

IMG_EXT = (".jpg", ".jpeg", ".png")

LEG = {"C", "P", "I"}
DPREC = {"EXACT", "DAY", "MD", "MONTH", "RELATIVE", "TIME", "NONE"}
AU = {"F", "T", "O", "A", "U"}
ST = {"WATCH", "FOCUS", "WAIT", "READY", "ENTRY", "EXIT", "REJECT", "MULTI", "UNKNOWN", "NONE"}
EV = {"D", "B", "I", "X"}
ROLE = {"R": "RULE_EVIDENCE", "V": "VALIDATION_CASE", "C": "COUNTEREXAMPLE",
        "X": "CONTEXT_ONLY", "N": "NON_EVIDENCE"}
KIND = {"DT", "RS", "ED", "NA"}
TEMPORAL = {"Y", "N", "P"}
NEW = {"N", "R", "D"}
REQUIRED = ("id", "leg", "date", "dprec", "tk", "au", "st", "q", "ev", "role", "topics",
            "seen", "mean", "rule", "perm", "kind", "temporal", "new")

DATE_RE = {
    "EXACT": re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$"),
    "DAY": re.compile(r"^\d{4}-\d{2}-\d{2}$"),
    "MD": re.compile(r"^\d{2}-\d{2}$"),
    "MONTH": re.compile(r"^\d{4}-\d{2}$"),
    "TIME": re.compile(r"^\d{2}:\d{2}$"),
}
FULL_DAY = re.compile(r"\d{4}-\d{2}-\d{2}")

# حالاتُ القرار ⟵ فئةُ المقارنة (البروتوكول §⑤)
DEC_CLASS = {"WAIT": "WAIT", "WATCH": "WATCH", "FOCUS": "WATCH", "READY": "READY", "ENTRY": "READY",
             "REJECT": "REJECT", "MULTI": "MULTI", "NONE": "NONE", "EXIT": "EXIT"}
DECISIVE = {"WAIT", "WATCH", "READY", "REJECT", "EXIT"}
INH_NOCOMPARE = {"", "UNKNOWN", "?"}
INH_AU_F = {"F", "F_inferred"}
INH_AU_T = {"TP", "THIRD_PARTY", "EDU"}

STATUS_ORDER = ("NOT_YET_REVIEWED", "DUPLICATE", "CONTRADICTED", "UNKNOWN", "PARTIALLY_READABLE",
                "INFERRED", "VERIFIED_VISUAL")


class RecordError(ValueError):
    pass


def disk_images(img_dir=IMG_DIR):
    out = {}
    for f in sorted(os.listdir(img_dir)):
        stem, ext = os.path.splitext(f)
        if ext.lower() not in IMG_EXT:
            continue
        if stem in out:
            raise RecordError(f"معرّفٌ مكرّرٌ على القرص بامتدادين: {stem}")
        out[stem] = f
    return out


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def load_table(path=TABLE):
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    out = {}
    for r in rows:
        if r["IMAGE_ID"] in out:
            raise RecordError(f"صفٌّ مكرّرٌ في الجدول الموروث: {r['IMAGE_ID']}")
        out[r["IMAGE_ID"]] = r
    return out


def validate_record(rec):
    """يرفع RecordError عند أيّ مخالفةٍ للبروتوكول — لا تصحيحَ صامت."""
    rid = rec.get("id", "?")
    miss = [k for k in REQUIRED if k not in rec]
    if miss:
        raise RecordError(f"{rid}: حقولٌ ناقصة {miss}")
    if rec["leg"] not in LEG:
        raise RecordError(f"{rid}: leg")
    if rec["dprec"] not in DPREC:
        raise RecordError(f"{rid}: dprec")
    d = rec["date"]
    if rec["dprec"] == "NONE":
        if d:
            raise RecordError(f"{rid}: تاريخٌ بلا دقّة")
    elif rec["dprec"] == "RELATIVE":
        if not d or FULL_DAY.search(d):
            raise RecordError(f"{rid}: النسبيُّ لا يصير يومًا")
    elif not DATE_RE[rec["dprec"]].match(d):
        raise RecordError(f"{rid}: صيغةُ التاريخ لا تطابق {rec['dprec']}")
    if not isinstance(rec["tk"], list) or any(not isinstance(t, str) or not t for t in rec["tk"]):
        raise RecordError(f"{rid}: tk")
    if rec["au"] not in AU or rec["st"] not in ST or rec["ev"] not in EV:
        raise RecordError(f"{rid}: au/st/ev")
    if rec["role"] not in ROLE or rec["kind"] not in KIND or rec["temporal"] not in TEMPORAL:
        raise RecordError(f"{rid}: role/kind/temporal")
    if rec["new"] not in NEW:
        raise RecordError(f"{rid}: new")
    if rec["new"] == "D" and not rec.get("dup_of"):
        raise RecordError(f"{rid}: نسخةٌ بلا أصل")
    if rec["ev"] == "D" and not rec["q"].strip():
        raise RecordError(f"{rid}: تصريحٌ مباشرٌ بلا اقتباس")
    if rec["kind"] == "RS" and rec["temporal"] == "Y":
        raise RecordError(f"{rid}: الرجعيُّ لا يصلح سجلَّ قرار")
    if rec["leg"] == "I" and rec["ev"] in ("D", "B"):
        raise RecordError(f"{rid}: غيرُ المقروء لا يحمل دليلًا مباشرًا")
    if not isinstance(rec["topics"], list):
        raise RecordError(f"{rid}: topics")
    return rec


def load_records(path=RECORDS):
    """السجلُّ الإلحاقيّ ⟵ {id: [النسخ بترتيبها]} · مكرّرٌ بلا rev صاعدٍ وسببٍ يُسقط البناء."""
    hist = {}
    if not os.path.exists(path):
        return hist
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                raise RecordError(f"سطر {n}: JSON {e}") from e
            validate_record(rec)
            prev = hist.get(rec["id"])
            if prev:
                rev = rec.get("rev")
                last = prev[-1].get("rev", 1)
                if not isinstance(rev, int) or rev != last + 1 or not str(rec.get("why", "")).strip():
                    raise RecordError(f"سطر {n}: {rec['id']} مكرّرٌ بلا rev صاعدٍ وسبب")
                hist[rec["id"]].append(rec)
            else:
                if rec.get("rev", 1) != 1:
                    raise RecordError(f"سطر {n}: {rec['id']} rev بلا سجلٍّ أوّل")
                hist[rec["id"]] = [rec]
    return hist


def _is_dated_decision(r):
    return r.get("DECISION", "") in DEC_CLASS and r["DECISION"] != "NONE" and \
        r.get("DATE", "") not in ("", "UNKNOWN", "UNK")


def order_ids(ids, table):
    """ترتيبُ القراءة (البروتوكول §②) — حتميّ."""
    def tier(i):
        r = table.get(i, {})
        unlinked = r.get("USED_CLASS") == "NOT_TRACED" or (not r.get("LEDGER_KEYS") and not r.get("V4_RULES"))
        eye = r.get("EYE_READ_FM") == "yes"
        sub = 0 if _is_dated_decision(r) else (1 if r.get("ROLE") in ("RULE_EVIDENCE", "COUNTEREXAMPLE") else 2)
        if r.get("USED_CLASS") == "NOT_TRACED":
            return (0, 0, i)
        if eye:
            return (3, sub, i)
        if unlinked:
            return (1, sub, i)
        return (2, sub, i)
    return sorted(ids, key=tier), {i: tier(i)[:2] for i in ids}


TIER_NAME = {0: "أ-NOT_TRACED", 1: "أ-بلا مصدر ولا قاعدة", 2: "ب-موروثة غير متحقَّقة", 3: "هـ-مقروءة سابقًا"}
SUB_NAME = {0: "ج-قرار مؤرَّخ", 1: "د-قاعدة/مضادّ", 2: "الباقي"}


def _tickers(s):
    return {t.strip().rstrip("?") for t in (s or "").split("|") if t.strip().rstrip("?")}


def compare(rec, inh):
    """أعلامٌ وتصحيحات: [(field, inherited, eye, kind)] — kind ∈ {CONTRADICTED, FLAG}."""
    out = []
    if not inh:
        return out
    # القرار
    idec = inh.get("DECISION", "")
    if idec not in INH_NOCOMPARE:
        ic, ec = DEC_CLASS.get(idec), DEC_CLASS.get(rec["st"])
        if ec and ic and ic != ec:
            contra = (ic == "NONE" and ec in DECISIVE) or (ec == "NONE" and ic in DECISIVE) or \
                     (ic in DECISIVE and ec in DECISIVE)
            if ic == "MULTI" or ec == "MULTI":
                contra = False
            out.append(("DECISION", idec, rec["st"], "CONTRADICTED" if contra else "FLAG"))
    # الدور
    irole = inh.get("ROLE", "")
    if irole in ROLE.values() and irole != ROLE[rec["role"]]:
        out.append(("ROLE", irole, ROLE[rec["role"]], "CONTRADICTED"))
    # الرمز
    it, et = _tickers(inh.get("TICKER")), set(rec["tk"])
    if it and et and not (it & et):
        out.append(("TICKER", "|".join(sorted(it)), "|".join(sorted(et)), "CONTRADICTED"))
    elif it and not et:
        out.append(("TICKER_NOT_VISIBLE", "|".join(sorted(it)), "", "FLAG"))
    # الكاتب
    ia = inh.get("AUTHOR", "")
    if rec["au"] == "T" and ia in INH_AU_F:
        out.append(("AUTHOR", ia, "T", "CONTRADICTED"))
    elif rec["au"] == "F" and ia not in INH_AU_F and ia not in INH_NOCOMPARE and ia != "U":
        out.append(("AUTHOR", ia, "F", "CONTRADICTED"))
    elif rec["au"] == "U" and ia in INH_AU_F:
        out.append(("AUTHOR_NOT_VISIBLE", ia, "U", "FLAG"))
    # التاريخ
    idate = inh.get("DATE", "")
    if idate not in ("", "UNKNOWN", "UNK") and rec["dprec"] == "NONE":
        out.append(("DATE_NOT_VISIBLE", idate, "", "FLAG"))
    elif idate not in ("", "UNKNOWN", "UNK") and rec["dprec"] in ("DAY", "EXACT") and \
            FULL_DAY.match(idate) and not rec["date"].startswith(idate[:10]):
        out.append(("DATE", idate, rec["date"], "CONTRADICTED"))
    elif idate not in ("", "UNKNOWN", "UNK") and rec["dprec"] == "MD" and \
            FULL_DAY.match(idate) and idate[5:10] != rec["date"]:
        # تعديلٌ مؤرَّخ 2026-10-10: شهرٌ-يومٌ ظاهرٌ بلا سنة يخالف الموروث ⟵ علمٌ لا تناقض
        # (قد يكون الفرقُ منطقةً زمنيّة) — والسببُ في ملاحظة السجلّ
        out.append(("DATE_MD_DIFFERS", idate, rec["date"], "FLAG"))
    return out


def status_of(rec, diffs):
    if rec is None:
        return "NOT_YET_REVIEWED"
    if rec["new"] == "D":
        return "DUPLICATE"
    if any(k == "CONTRADICTED" for *_, k in diffs):
        return "CONTRADICTED"
    if rec["leg"] == "I":
        return "UNKNOWN"
    if rec["leg"] == "P":
        return "PARTIALLY_READABLE"
    if rec["ev"] in ("I", "X"):
        return "INFERRED"
    return "VERIFIED_VISUAL"


REG_COLS = ["IMAGE_ID", "PATH", "SHA256", "ORDER", "TIER", "STATUS", "FLAGS", "REV",
            "LEG", "DATE_SHOWN", "DPREC", "TICKERS", "AUTHOR", "STATE", "QUOTE", "EV", "ROLE",
            "TOPICS", "KIND", "TEMPORAL", "NEW", "DUP_OF", "LINK",
            "INH_ROLE", "INH_DATE", "INH_TICKER", "INH_AUTHOR", "INH_DECISION", "INH_USED_CLASS",
            "INH_LEDGER_KEYS", "INH_V4_RULES", "INH_EYE_READ_FM"]
COR_COLS = ["IMAGE_ID", "FIELD", "KIND", "INHERITED", "EYE", "QUOTE", "AFFECTED_USED_CLASS",
            "AFFECTED_LEDGER_KEYS", "AFFECTED_V4_RULES", "REV"]


def _csv(rows, cols):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow(r)
    return buf.getvalue()


def build(img_dir=IMG_DIR, table_path=TABLE, records_path=RECORDS):
    disk = disk_images(img_dir)
    table = load_table(table_path)
    hist = load_records(records_path)
    stray = sorted(set(hist) - set(disk))
    if stray:
        raise RecordError(f"سجلٌّ لمعرّفٍ ليس على القرص: {stray[:5]}")
    for i, h in hist.items():
        d = h[-1].get("dup_of")
        if d and d not in disk:
            raise RecordError(f"{i}: dup_of لمعرّفٍ ليس على القرص {d}")
    ordered, tiers = order_ids(list(disk), table)
    reg, cor = [], []
    for n, i in enumerate(ordered, 1):
        inh = table.get(i, {})
        rec = hist[i][-1] if i in hist else None
        diffs = compare(rec, inh) if rec else []
        st = status_of(rec, diffs)
        t0, t1 = tiers[i]
        row = {
            "IMAGE_ID": i, "PATH": f"faisal_images/{disk[i]}",
            "SHA256": sha256_file(os.path.join(img_dir, disk[i])),
            "ORDER": n, "TIER": f"{TIER_NAME[t0]}/{SUB_NAME[t1] if t0 else ''}".rstrip("/"),
            "STATUS": st, "FLAGS": "|".join(f for f, _, _, k in diffs if k == "FLAG"),
            "REV": rec.get("rev", 1) if rec else "",
            "INH_ROLE": inh.get("ROLE", ""), "INH_DATE": inh.get("DATE", ""),
            "INH_TICKER": inh.get("TICKER", ""), "INH_AUTHOR": inh.get("AUTHOR", ""),
            "INH_DECISION": inh.get("DECISION", ""), "INH_USED_CLASS": inh.get("USED_CLASS", ""),
            "INH_LEDGER_KEYS": inh.get("LEDGER_KEYS", ""), "INH_V4_RULES": inh.get("V4_RULES", ""),
            "INH_EYE_READ_FM": inh.get("EYE_READ_FM", ""),
        }
        if rec:
            row.update({
                "LEG": rec["leg"], "DATE_SHOWN": rec["date"], "DPREC": rec["dprec"],
                "TICKERS": "|".join(rec["tk"]), "AUTHOR": rec["au"], "STATE": rec["st"],
                "QUOTE": rec["q"], "EV": rec["ev"], "ROLE": ROLE[rec["role"]],
                "TOPICS": "|".join(rec["topics"]), "KIND": rec["kind"], "TEMPORAL": rec["temporal"],
                "NEW": rec["new"], "DUP_OF": rec.get("dup_of", ""), "LINK": rec.get("link", ""),
            })
        reg.append(row)
        for f, a, b, k in diffs:
            cor.append({"IMAGE_ID": i, "FIELD": f, "KIND": k, "INHERITED": a, "EYE": b,
                        "QUOTE": rec["q"], "AFFECTED_USED_CLASS": inh.get("USED_CLASS", ""),
                        "AFFECTED_LEDGER_KEYS": inh.get("LEDGER_KEYS", ""),
                        "AFFECTED_V4_RULES": inh.get("V4_RULES", ""), "REV": rec.get("rev", 1)})
    order_txt = "".join(f"{n}\t{i}\t{reg[n - 1]['TIER']}\n" for n, i in enumerate(ordered, 1))
    return {OUT_ORDER: order_txt, OUT_REG: _csv(reg, REG_COLS), OUT_COR: _csv(cor, COR_COLS),
            OUT_SUM: summary_md(reg, cor, len(disk), len(table), hist)}


def summary_md(reg, cor, n_disk, n_table, hist):
    from collections import Counter
    st = Counter(r["STATUS"] for r in reg)
    read = n_disk - st["NOT_YET_REVIEWED"]
    revs = sum(len(h) - 1 for h in hist.values())
    lines = [
        "# 👁️ ملخّصُ إعادة القراءة البصريّة (`T-REREAD`)",
        "",
        "> مولَّدٌ من `reread_build.py` — لا يُحرَّر باليد · `--check` يعيده بايتًا.",
        "",
        f"- **الصورُ على القرص:** {n_disk} · صفوفُ الجدول الموروث: {n_table}",
        f"- **قُرئت بالعين في هذه المهمّة:** {read} من {n_disk}"
        + (" — **التغطيةُ كاملة**" if read == n_disk else " — **التغطيةُ غيرُ مكتملة: لا يُقال إن التدقيق اكتمل**"),
        f"- **مراجعاتُ سجلّاتٍ سابقة (rev):** {revs}",
        "",
        "| الحالة | العدد |",
        "|---|---|",
    ]
    lines += [f"| `{s}` | {st.get(s, 0)} |" for s in STATUS_ORDER]
    flags = Counter(f for r in reg for f in r["FLAGS"].split("|") if f)
    kinds = Counter((c["FIELD"], c["KIND"]) for c in cor)
    lines += ["", "| العلم/الحقل (مقابل الموروث) | النوع | العدد |", "|---|---|---|"]
    lines += [f"| `{f}` | {k} | {n} |" for (f, k), n in sorted(kinds.items())]
    if not kinds:
        lines.append("| — | — | 0 |")
    lines += ["", f"- أعلامٌ على صفوف السجلّ: {sum(flags.values())}", ""]
    return "\n".join(lines)


def write_all(outs):
    for p, txt in outs.items():
        with open(p, "w", encoding="utf-8", newline="") as fh:
            fh.write(txt)


def check(outs):
    bad = []
    for p, txt in outs.items():
        try:
            with open(p, encoding="utf-8", newline="") as fh:
                if fh.read() != txt:
                    bad.append(os.path.basename(p))
        except FileNotFoundError:
            bad.append(os.path.basename(p) + " (غائب)")
    return bad


def main(argv):
    outs = build()
    if "--check" in argv:
        bad = check(outs)
        if bad:
            print("⛔ مُخرَجاتٌ لا تطابق إعادةَ البناء:", ", ".join(bad))
            return 1
        print("✅ المُخرَجاتُ تطابق إعادةَ البناء بايتًا")
        return 0
    if "--next" in argv:
        k = int(argv[argv.index("--next") + 1])
        hist = load_records()
        ids = [ln.split("\t")[1] for ln in outs[OUT_ORDER].splitlines()]
        todo = [i for i in ids if i not in hist]
        print(f"باقٍ {len(todo)} من {len(ids)}")
        disk = disk_images()
        for i in todo[:k]:
            print(os.path.join(IMG_DIR, disk[i]))
        return 0
    if "--order" in argv:
        write_all({OUT_ORDER: outs[OUT_ORDER]})
        return 0
    write_all(outs)
    print("✅ بُني:", ", ".join(os.path.basename(p) for p in outs))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
