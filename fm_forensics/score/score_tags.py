"""T-SCORE stage A — layer ③ of the weights: what Faisal names while he waits.

Reads the eye-read register of the whole corpus (`fm_forensics/reread/data/reread_records.jsonl` · 772 images · the latest
revision of each id wins) and counts, over Faisal's own WAIT statements (author F · state WAIT), how many distinct statements
mention each condition. A fixed dictionary (below) — no market data, no outcome, nothing after the evidence boundary
(the register is the sealed historical corpus). Deterministic; `--check` rebuilds and compares byte-for-byte.

    python3 fm_forensics/score/score_tags.py           # writes data/wait_tags.json
    python3 fm_forensics/score/score_tags.py --check   # rebuild + compare
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
REGISTER = os.path.join(ROOT, "fm_forensics", "reread", "data", "reread_records.jsonl")
OUT = os.path.join(HERE, "data", "wait_tags.json")

# category ⟶ (score component it weights, or None = named but not measurable on daily bars) · regex on normalized text
CATEGORIES = {
    "RSI": ("RSI", r"rsi"),
    "HOLD": ("HOLD+HOLDZ", r"ثبات|يثبت|ثبت|يحافظ|حافظ|المحافظه|ماكسر|لاكسر|عدم كسر|لا يكسر|مايكسر"),
    "TEST": ("CYC", r"يختبر|اختبار|اختبر"),
    "ZONE": ("ZONE", r"انتظار الهبوط|ينزل|تنتظر \d|انتظر \d|لاختبار الدعوم|مناطق الطلب|انتظار الدعوم|انتظار تحقيق الدعم"
                     r"|تكوين دعوم"),
    "SWEEP": ("SWEEP", r"سحب السيوله|سحب سيوله|مسح سيوله|مسح السيوله"),
    "GAP": ("GAP", r"فجوه|فراغ"),
    "OPERATOR": (None, r"مضارب|ضغط"),
    "SHORT": (None, r"شورت|اقتراض"),
    "OFFERING": (None, r"طرح|تخفيف"),
    "GROUPS": (None, r"قروب"),
    "BREAKOUT": (None, r"تحرر|تجاوز|خط العنق|اختراق|فوق المقاومه"),
    "VOLUME": (None, r"فوليوم|تدوير|سيوله سالب"),
    "NEWS": (None, r"خبر|اخبار|اعلان"),
}

_DIAC = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭـ‌-‏]")


def norm(s):
    """Arabic normalisation for matching: no diacritics/tatweel/marks · أ إ آ ⟵ ا · ة ⟵ ه · ى ⟵ ي · Latin lower-case."""
    s = _DIAC.sub("", s or "")
    s = s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ة", "ه").replace("ى", "ي")
    return re.sub(r"\s+", " ", s.lower()).strip()


def latest(records):
    """The register is append-only: a later line for the same id is its newer revision."""
    out = {}
    for r in records:
        out[r["id"]] = r
    return out


def dedupe(items):
    """Drop a statement whose normalized letters+digits are contained in a longer kept statement (the same words quoted
    twice, or a shorter excerpt of the same post). Deterministic: longest first, then id."""
    key = {i: re.sub(r"[^0-9a-zء-ي]", "", norm(q)) for i, q in items}
    order = sorted(key, key=lambda i: (-len(key[i]), i))
    kept, dropped = [], []
    for i in order:
        if not key[i] or any(key[i] in key[j] for j in kept):
            dropped.append(i)
        else:
            kept.append(i)
    return sorted(kept), sorted(dropped)


def label(q):
    t = norm(q)
    return sorted(c for c, (_, rx) in CATEGORIES.items() if re.search(rx, t))


def build(register=REGISTER):
    recs = latest(json.loads(line) for line in open(register, encoding="utf-8") if line.strip())
    out = {"source": os.path.relpath(register, ROOT).replace(os.sep, "/"), "unique_ids": len(recs), "sets": {}}
    for name, authors in (("faisal", ("F",)), ("faisal_plus_unattributed", ("F", "U"))):
        w = sorted((r["id"], r.get("q") or "") for r in recs.values() if r.get("st") == "WAIT" and r.get("au") in authors)
        kept, dropped = dedupe(w)
        q = dict(w)
        labels = {i: label(q[i]) for i in kept}
        counts = {c: sum(1 for i in kept if c in labels[i]) for c in CATEGORIES}
        out["sets"][name] = {"authors": list(authors), "wait_records": len(w), "kept": len(kept), "dropped_duplicates": dropped,
                             "counts": counts, "labels": labels, "none_named": sorted(i for i in kept if not labels[i])}
    out["categories"] = {c: {"component": comp, "regex": rx} for c, (comp, rx) in CATEGORIES.items()}
    return out


def dump(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


if __name__ == "__main__":
    text = dump(build())
    if "--check" in sys.argv:
        same = os.path.exists(OUT) and open(OUT, encoding="utf-8").read() == text
        print("wait_tags --check:", "OK" if same else "DIFFERS")
        sys.exit(0 if same else 1)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(text)
    d = json.loads(text)["sets"]
    for k, v in d.items():
        print(k, "records", v["wait_records"], "kept", v["kept"], "none named", len(v["none_named"]))
        print("  ", json.dumps(v["counts"], ensure_ascii=False))
