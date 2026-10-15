"""T-COLOUR builder — deterministic, no network, no candles, no dates.

Reads the eye register (data/colour_records.jsonl) and writes COLOUR_LEVELS.tsv, data/colour_result.json and
T_COLOUR_TABLES.md under the rules of T_COLOUR_protocol.md (pinned by its sha256).

  python3 fm_forensics/colour/colour_build.py            build (exit 9 unless the pinned protocol is on origin/main)
  python3 fm_forensics/colour/colour_build.py --check    rebuild in memory and compare the three outputs byte for byte
  python3 fm_forensics/colour/colour_build.py --guards   synthetic guards
  python3 fm_forensics/colour/colour_build.py --validate pins (local) and register checks only — no measure is computed
  python3 fm_forensics/colour/colour_build.py --heads-sample  the seeded purple sample of amendment ④-⑪ (no measure)

Exit codes: 0 done · 1 guards failed or outputs differ · 8 axis closed · 9 protocol/records pin or register invalid.

🔒 Executed closure (owner «اقفل الالوان» 2026-10-15 · T_COLOUR_RESULT.md §⑮): the build and --heads-sample exit 8 before
any read unless COLOUR_REOPEN=1 (the literal "1"). --check, --guards and --validate stay open: they write nothing and can only
confirm the published, pinned result.
"""
import argparse
import collections
import hashlib
import json
import math
import os
import random
import re
import statistics
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PROTO = os.path.join(HERE, "T_COLOUR_protocol.md")
PROTO_SHA256 = "f0d9d8af80f9e63d1e653df1cbdd7bab727fd41531f17f3190d52a30c8acda2e"
DATA = os.path.join(HERE, "data")

AXIS_CLOSED = True
REOPEN_ENV = "COLOUR_REOPEN"
CLOSED_RC = 8                     # distinct from 0 (ok) · 1 (guards failed / outputs differ) · 9 (pins / register)


def _closed_now():
    """Closed right now? Read at call time; the acknowledgement is the literal "1" (a workflow input defaulting to "0" would
    otherwise lift the closure on every run while looking closed)."""
    return AXIS_CLOSED and (os.environ.get(REOPEN_ENV) or "").strip() != "1"


def closure_notice():
    """The closure text — a pure function so its content is locked, not its shape."""
    return [
        "🔒🔴 محورُ «خطوط فيصل الملوّنة» (`T-COLOUR`) مُغلَق — بأمر المالك «اقفل الالوان» (2026-10-15) · "
        "`fm_forensics/colour/T_COLOUR_RESULT.md §⑮`.",
        "",
        "⚖️ السبب — السؤالُ أُجيب (‏342 من 772 صورة · 1,647 مستوًى · #626):",
        "   • المفتاحُ يصمد حاسمًا في المجموعتين: الأحمرُ تحت السعر 92.77% · الأسودُ والأزرقُ والبنفسجيُّ فوقه.",
        "   • البنفسجيُّ ليس طلبًا ⟵ ①②③ لم تُحسب · ولا لونَ غيرُ الأحمر أغلبُه تحت ⟵ «فيصل لا يرسم مناطقَ دخولٍ بلون».",
        "   • وما بقي مفتوحًا (ضبطُ الرؤوس · قراءةُ «طلب» البنفسجيّ بعد الرقم) لا يغيّر قرارًا إنتاجيًّا — والبروتوكولُ يمنع البوّابة.",
        "",
        "🔓 ولا يُعاد فتحُه إلّا بثلاثةٍ معًا:",
        "   ① مصدرٌ جديدٌ لم يُقَس — وإعادةُ قراءة الصور نفسِها أو تبديلُ التماسّ ليست مصدرًا (والصورُ الجديدة استلامٌ أماميّ).",
        "   ② تسجيلٌ مسبقٌ جديد — البروتوكولُ `T_COLOUR_protocol.md` بتعديله ④ مدموجٌ لا يُعدَّل.",
        "   ③ إذنُ المالك.",
        "   ⚖️ والمفتاحُ COLOUR_REOPEN=1 إقرارٌ بالثلاثة لا التفافٌ عليها — ويُقرأ «1» حرفيًّا.",
    ]
REC = os.path.join(DATA, "colour_records.jsonl")
REC_SHA256 = "cd46e377b3bddd1d64a0d8ac0363467a081caeee9f9235f35254dcbf1a20d4a4"
FAMILY = os.path.join(DATA, "other_family.json")
KEYTEXT = os.path.join(DATA, "colour_key_text.jsonl")
CORR = os.path.join(DATA, "table_corrections.jsonl")
ANPA = os.path.join(DATA, "anpa_case.json")
HEADS = os.path.join(DATA, "purple_heads.jsonl")
TABLE = os.path.join(ROOT, "faisal_levels_table.tsv")
IMAGES = os.path.join(ROOT, "faisal_images")
OUT_TSV = os.path.join(HERE, "COLOUR_LEVELS.tsv")
OUT_JSON = os.path.join(DATA, "colour_result.json")
OUT_MD = os.path.join(HERE, "T_COLOUR_TABLES.md")

COLOURS = ("red", "black", "purple", "blue", "orange", "green", "yellow", "grey", "pink", "white", "other")
AUTHORS = ("FAISAL", "UNSIGNED", "FOLLOWER", "THIRD_PARTY", "OWNER", "APP")
NONE_REASONS = ("NOT_CHART", "NO_LINES", "NO_NUMBERS", "LOW_RES", "CROPPED")
TAGS = ("نصّ المنشور", "نصّ الرسالة", "نصّ على الشارت")
# Amendment ④ (owner correction 2026-10-15): purple has no role from the key — its role is derived from position vs price.
KEY_ROLE = {"red": "support", "black": "resistance", "blue": "target_clean"}
PRICE_SRC = ("ext", "regular", "mid")
WILSON_Z = 1.959964
MIN_LEVELS, MIN_UNITS = 10, 5   # below either: "no_measure" (amendment ④-③)
ZONE_PCT = 6.0      # our ladder: ENTRY_TRANCHES=3 at ENTRY_STEP_PCT=3 -> 0/+3/+6
NEAR_PCT = 1.0      # stop "at" low/support band (protocol §⑤) · and the "at price" band of amendment ④-③
DEPTH_BINS = ("<5", "5-<7", "7-13", ">13-20", ">20-50", ">50")   # 7-13 closed both ends (Faisal's band)

# T-REREAD duplicate targets that are not themselves images in this folder (none expected; kept explicit)
DUP_TARGET_OK = set()

# ───────────────────────────── loading and validation ─────────────────────────────


def _sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _main_blob(path):
    rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
    p = subprocess.run(["git", "-C", ROOT, "show", f"origin/main:{rel}"], capture_output=True)
    return p.stdout if p.returncode == 0 else None


def check_pins(read=None, need_main=True):
    """Exit 9 unless the protocol and the register carry their pinned bytes (and the protocol is on origin/main)."""
    if _sha(PROTO) != PROTO_SHA256:
        print(f"⛔ protocol changed or not pinned: {_sha(PROTO)} ≠ {PROTO_SHA256}")
        sys.exit(9)
    if _sha(REC) != REC_SHA256:
        print(f"⛔ register changed without a new pin: {_sha(REC)} ≠ {REC_SHA256}")
        sys.exit(9)
    if need_main:
        blob = (read or (lambda: _main_blob(PROTO)))()
        got = hashlib.sha256(blob).hexdigest() if blob is not None else None
        if got != PROTO_SHA256:
            print(f"⛔ the pinned protocol is not on origin/main ({got}) — merge it first (git fetch --force)")
            sys.exit(9)


def image_ids(folder=IMAGES):
    return sorted(os.path.splitext(f)[0] for f in os.listdir(folder) if f != "README.md")


def load_register(path=REC):
    """Return (latest record per id, register order, problems). Append-only: rev must rise by one with a why."""
    last, order, probs = {}, [], []
    with open(path, encoding="utf-8") as f:
        for n, ln in enumerate(f, 1):
            if not ln.strip():
                continue
            r = json.loads(ln)
            i, rev = r.get("id"), r.get("rev")
            prev = last.get(i, {}).get("rev", 0)
            if rev != prev + 1:
                probs.append(f"line {n}: {i} rev {rev} after {prev}")
            if rev and rev > 1 and not r.get("why"):
                probs.append(f"line {n}: {i} rev {rev} without why")
            if i not in last:
                order.append(i)
            last[i] = r
    return last, order, probs


def validate(last, ids):
    """Field-level validation of the latest records; returns a list of problems."""
    probs = []
    if sorted(last) != sorted(ids):
        miss, extra = sorted(set(ids) - set(last)), sorted(set(last) - set(ids))
        probs.append(f"register ids ≠ images: missing {miss[:5]} ({len(miss)}) · extra {extra[:5]} ({len(extra)})")
    for i, r in last.items():
        kinds = [k for k in ("charts", "none", "dup_of") if k in r]
        if len(kinds) != 1:
            probs.append(f"{i}: kinds {kinds}")
            continue
        if "none" in r and r["none"] not in NONE_REASONS:
            probs.append(f"{i}: none {r['none']}")
        if "dup_of" in r and r["dup_of"] not in last and r["dup_of"] not in DUP_TARGET_OK:
            probs.append(f"{i}: dup_of {r['dup_of']} unknown")
        for ci, c in enumerate(r.get("charts", [])):
            if c.get("author") not in AUTHORS:
                probs.append(f"{i}#{ci}: author {c.get('author')}")
            if not c.get("levels"):
                probs.append(f"{i}#{ci}: chart without levels")
            seen = set()
            for lv in c.get("levels", []):
                if len(lv) != 4 or lv[0] not in COLOURS or not isinstance(lv[1], (int, float)) or lv[1] <= 0 or lv[3] not in "HML":
                    probs.append(f"{i}#{ci}: level {lv}")
                    continue
                if (lv[0], lv[1]) in seen:
                    probs.append(f"{i}#{ci}: duplicate level {lv[:2]}")
                seen.add((lv[0], lv[1]))
                for t in re.findall(r"\((على الشارت|نص[^()]{0,20})\)", lv[2] or ""):
                    if t not in TAGS:
                        probs.append(f"{i}#{ci}: non-canonical tag ({t})")
            e = c.get("entries_text")
            if e is not None and not (isinstance(e, list) and all(isinstance(x, (int, float)) and x > 0 for x in e)):
                probs.append(f"{i}#{ci}: entries_text {e!r}")
            if c.get("low") is not None and c.get("low_src") not in ("label", "axis"):
                probs.append(f"{i}#{ci}: low_src")
            if c.get("stop") is not None and c.get("stop_src") not in ("text", "line"):
                probs.append(f"{i}#{ci}: stop_src")
            if "price_last" not in c:
                probs.append(f"{i}#{ci}: price_last not read (amendment ④: every chart is read by eye)")
            elif c["price_last"] is not None and not (isinstance(c["price_last"], (int, float)) and c["price_last"] > 0
                                                      and c.get("price_last_src") in PRICE_SRC):
                probs.append(f"{i}#{ci}: price_last {c['price_last']!r}/{c.get('price_last_src')!r}")
    return probs

# ───────────────────────────── labels and roles ─────────────────────────────

_AR = str.maketrans({"ة": "ه", "أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ـ": None})
_DIAC = re.compile(r"[ً-ْٰ]")
ROLE_PAT = (
    ("support", re.compile(r"دعم|دعوم|قاع|وقف|stop")),
    ("resistance", re.compile(r"مقاوم")),
    ("target", re.compile(r"هدف|اهداف")),
    ("bid", re.compile(r"طلب|شراء|دخول|entry")),
    ("gap", re.compile(r"فجوه|قاب|ساقطه")),
    ("drop", re.compile(r"هبوط متوقع|يضغط|ممكن يهبط")),
)


def norm(s):
    """Arabic letter/diacritic normalisation (the three tags hold no role word, so they need no stripping)."""
    return _DIAC.sub("", s or "").translate(_AR).lower()


def label_roles(label):
    """Set of (class, word) named by a label; 'X تحولت لدعم' keeps only the transformed role."""
    t = norm(label)
    out = set()
    for cls, pat in ROLE_PAT:
        for m in pat.finditer(t):
            out.add((cls, m.group(0)))
    if "تحول" in t and any(c == "support" for c, _ in out) and any(c == "resistance" for c, _ in out):
        out = {x for x in out if x[0] != "resistance"}
    return out


def compatible(colour, cls, word):
    if colour == "red":
        return cls == "support" or (cls == "bid" and word == "دخول")
    if colour == "black":
        return cls in ("resistance", "target")
    if colour == "blue":
        return cls == "target"
    return True     # purple (amendment ④) and unmapped colours never conflict through a label


def label_conflict(colour, label):
    roles = label_roles(label)
    if not roles or colour not in KEY_ROLE:
        return False
    return not any(compatible(colour, c, w) for c, w in roles)


# ───────────────────────────── units (merge) ─────────────────────────────


def charts_of(last, order):
    out = []
    for i in order:
        r = last[i]
        for ci, c in enumerate(r.get("charts", [])):
            out.append({"key": f"{i}#{ci}", "id": i, **c, "set": frozenset((lv[0], lv[1]) for lv in c["levels"])})
    return out


def unit_author(members):
    auth = [m["author"] for m in members]
    if "FAISAL" in auth:
        return "FAISAL"
    kinds = {a for a in auth if a != "UNSIGNED"}
    return kinds.pop() if len(kinds) == 1 else "UNSIGNED"


def build_units(charts):
    """Merge rules (protocol §④ and changelog ③-8): identical set of the same symbol · strict subset (>=2 shared) of the
    same symbol absorbed into its LARGEST superset (tie: first in register order) · a null-symbol chart identical to a
    known-symbol chart joins it. No chaining: every chart is assigned directly."""
    pos = {c["key"]: n for n, c in enumerate(charts)}
    assign = {}
    by_sym = collections.defaultdict(list)
    for c in charts:
        if c.get("symbol"):
            by_sym[c["symbol"]].append(c)
    for sym, cs in by_sym.items():
        for c in cs:
            sup = [d for d in cs if d is not c and (d["set"] == c["set"] or (c["set"] < d["set"] and len(c["set"]) >= 2))]
            strict = [d for d in sup if c["set"] < d["set"]]
            if strict:
                best = sorted(strict, key=lambda d: (-len(d["set"]), pos[d["key"]]))[0]
                # the target may itself be an identical copy of an earlier chart: anchor to the earliest identical copy
                twin = sorted([d for d in cs if d["set"] == best["set"]], key=lambda d: pos[d["key"]])[0]
                assign[c["key"]] = twin["key"]
            else:
                twin = sorted([d for d in cs if d["set"] == c["set"]], key=lambda d: pos[d["key"]])[0]
                assign[c["key"]] = twin["key"]
    known = [c for c in charts if c.get("symbol")]
    for c in charts:
        if c.get("symbol"):
            continue
        same = sorted([d for d in known if d["set"] == c["set"]], key=lambda d: pos[d["key"]])
        assign[c["key"]] = assign[same[0]["key"]] if same else c["key"]
    groups = collections.OrderedDict()
    for c in charts:
        groups.setdefault(assign[c["key"]], []).append(c)
    units = []
    for anchor, members in groups.items():
        members.sort(key=lambda d: pos[d["key"]])
        chosen = next(d for d in members if d["key"] == anchor)
        labels = collections.defaultdict(list)
        for m in members:
            for lv in m["levels"]:
                if lv[2] and lv[2] not in labels[(lv[0], lv[1])]:
                    labels[(lv[0], lv[1])].append(lv[2])
        fields, filled_from = {}, {}
        for f in ("stop", "stop_src", "bids_text", "entries_text", "price_last", "price_last_src"):
            v = chosen.get(f)
            if v is None:
                for m in members:
                    if m.get(f) is not None:
                        v, filled_from[f] = m[f], m["key"]
                        break
            fields[f] = v
        units.append({
            "unit": anchor, "members": [m["key"] for m in members], "author": unit_author(members),
            "symbol": chosen.get("symbol") or next((m["symbol"] for m in members if m.get("symbol")), None),
            "frame": chosen.get("frame"), "price_now": chosen.get("price_now"),
            "price_last": fields["price_last"], "price_last_src": fields["price_last_src"] if fields["price_last"] is not None else None,
            "low": chosen.get("low"), "low_src": chosen.get("low_src"),
            "stop": fields["stop"], "stop_src": fields["stop_src"],
            "bids_text": fields["bids_text"], "entries_text": fields["entries_text"], "filled_from_member": filled_from,
            "levels": [{"colour": lv[0], "value": lv[1], "label": " · ".join(labels[(lv[0], lv[1])]), "conf": lv[3]}
                       for lv in sorted(chosen["levels"], key=lambda x: -x[1])],
        })
    return units


# ───────────────────────────── roles per unit ─────────────────────────────


def fold_map(family):
    return {(x["id"], x["value"]): x["family"] for x in family["levels"]}


def recolour(units, fmap):
    """Dark-shade sensitivity: an 'other' level folds into its family when any member records it in other_family.json."""
    out = []
    for u in units:
        ids = [k.split("#")[0] for k in u["members"]]
        lv2 = []
        for lv in u["levels"]:
            c = lv["colour"]
            if c == "other":
                fam = next((fmap[(i, lv["value"])] for i in ids if (i, lv["value"]) in fmap), "other")
                c = fam
            lv2.append({**lv, "colour": c})
        out.append({**u, "levels": lv2})
    return out


def _side(rel):
    r = round(rel, 9)       # the ±1% band is closed: float noise at the edge must not flip a side
    return "above" if r > NEAR_PCT else ("below" if r < -NEAR_PCT else "at")


def side_of(v, p):
    """Amendment ④-③: rel_pct to the price and its side (above +1% · below −1% · else at); None without a price."""
    if not p:
        return None, None
    r = (v - p) / p * 100
    return r, _side(r)


def assign_roles(u, above_all=False, price_key="price_last"):
    """Role per level: key role (red · black · blue — Faisal's text), or 'conflict' with reasons (label · inversion
    inside the chart: red above black -> both · blue below red -> both · red above blue -> red). Purple carries no key role
    and no conflict rule (amendment ④). above_all = the sensitivity that needs the level above (or below) ALL lines of the
    other colour. Every level also carries rel/side to the chart price (price_last governs, price_now is a sensitivity)."""
    lv = u["levels"]
    val = {c: [x["value"] for x in lv if x["colour"] == c] for c in ("red", "black", "blue")}

    def above(v, others):
        return bool(others) and (v > max(others) if above_all else v > min(others))

    def below(v, others):
        return bool(others) and (v < min(others) if above_all else v < max(others))
    out = []
    for x in lv:
        c, v, why = x["colour"], x["value"], []
        if label_conflict(c, x["label"]):
            why.append("label")
        if c == "red" and above(v, val["black"]):
            why.append("red>black")
        if c == "black" and below(v, val["red"]):
            why.append("black<red")
        if c == "blue" and below(v, val["red"]):
            why.append("blue<red")
        if c == "red" and above(v, val["blue"]):
            why.append("red>blue")
        role = "conflict" if why else KEY_ROLE.get(c, "unmapped")
        rel, side = side_of(v, u.get(price_key))
        out.append({**x, "role": role, "why": why, "rel": rel, "side": side})
    return out


# ───────────────────────────── measures ─────────────────────────────


def _q(xs):
    xs = sorted(xs)
    if not xs:
        return None
    if len(xs) == 1:
        return {"n": 1, "min": xs[0], "q1": xs[0], "median": xs[0], "q3": xs[0], "max": xs[0]}
    q = statistics.quantiles(xs, n=4, method="inclusive")
    return {"n": len(xs), "min": xs[0], "q1": q[0], "median": statistics.median(xs), "q3": q[2], "max": xs[-1]}


def _r(x):
    return None if x is None else round(x, 2)


def nearest_red(reds, lo, hi):
    def d(s):
        return 0.0 if lo <= s <= hi else min(abs(s - lo), abs(s - hi))
    return sorted(reds, key=lambda s: (round(d(s), 9), -s))[0]


def measure_bids(units, s_rule="nearest", keep_conflict=False, drop_above_price=False):
    rows = []
    for u in units:
        ok = (lambda x: True) if keep_conflict else (lambda x: x["role"] != "conflict")
        P = [x["value"] for x in u["roles"] if x["colour"] == "purple" and ok(x)
             and not (drop_above_price and x["side"] == "above")]
        R = [x["value"] for x in u["roles"] if x["colour"] == "red" and ok(x)]
        if not P or not R:
            continue
        pmin, pmax = min(P), max(P)
        S = nearest_red(R, pmin, pmax) if s_rule == "nearest" else (min(R) if s_rule == "lowest" else max(R))
        lo, hi = (pmin - S) / S * 100, (pmax - S) / S * 100
        cls = "above" if pmin > S else ("below" if pmax < S else "surrounds")
        rows.append({"unit": u["unit"], "symbol": u["symbol"], "S": S, "Pmin": pmin, "Pmax": pmax, "n_purple": len(P),
                     "lo": _r(lo), "hi": _r(hi), "class": cls})
    summ = {}
    for cls in ("above", "surrounds", "below"):
        rs = [r for r in rows if r["class"] == cls]
        summ[cls] = {"n": len(rs), "median_lo": _r(statistics.median([r["lo"] for r in rs])) if rs else None,
                     "median_hi": _r(statistics.median([r["hi"] for r in rs])) if rs else None}
    return {"n": len(rows), "symbols": len({r["symbol"] for r in rows if r["symbol"]}), "classes": summ, "rows": rows}


def measure_entries(units):
    """Written entries (entries_text) against the nearest red (protocol §⑤ ①) — and, amendment ④-⑤, against the chart
    price (price_last) and the width of the written entries against our 6% ladder."""
    rows, prow, wrows = [], [], []
    for u in units:
        E = u.get("entries_text") or []
        R = [x["value"] for x in u["roles"] if x["colour"] == "red" and x["role"] != "conflict"]
        for e in E:
            rel, side = side_of(e, u.get("price_last"))
            if rel is not None:
                prow.append({"unit": u["unit"], "symbol": u["symbol"], "entry": e, "price": u["price_last"], "rel": _r(rel), "side": side})
        if len(E) >= 2:
            wrows.append({"unit": u["unit"], "symbol": u["symbol"], "entries": sorted(E), "width": _r((max(E) - min(E)) / min(E) * 100)})
        if not E or not R:
            continue
        for e in E:
            S = nearest_red(R, e, e)
            rows.append({"unit": u["unit"], "symbol": u["symbol"], "entry": e, "S": S, "pct": _r((e - S) / S * 100)})
    w = [r["width"] for r in wrows]
    return {"n": len(rows), "units": len({r["unit"] for r in rows}), "above": sum(r["pct"] > 0 for r in rows),
            "at": sum(r["pct"] == 0 for r in rows), "below": sum(r["pct"] < 0 for r in rows),
            "median_pct": _r(statistics.median([r["pct"] for r in rows])) if rows else None, "rows": rows,
            "vs_price": {"n": len(prow), "sides": {k: sum(r["side"] == k for r in prow) for k in ("above", "at", "below")},
                         "median_rel": _r(statistics.median([r["rel"] for r in prow])) if prow else None, "rows": prow},
            "written_width": {"n": len(wrows), "le_6": sum(x <= ZONE_PCT for x in w), "gt_6": sum(x > ZONE_PCT for x in w),
                              "median": _r(statistics.median(w)) if w else None, "rows": wrows}}


def measure_width(units, keep_conflict=False):
    rows, single = [], 0
    for u in units:
        P = sorted(x["value"] for x in u["roles"] if x["colour"] == "purple" and (keep_conflict or x["role"] != "conflict"))
        if len(P) == 1:
            single += 1
        if len(P) >= 2:
            rows.append({"unit": u["unit"], "symbol": u["symbol"], "width": _r((P[-1] - P[0]) / P[0] * 100), "n_purple": len(P)})
    w = [r["width"] for r in rows]
    q = _q(w)
    return {"n": len(rows), "single_line": single, "stats": {k: _r(v) if k != "n" else v for k, v in q.items()} if q else None,
            "le_6": sum(x <= ZONE_PCT for x in w), "gt_6": sum(x > ZONE_PCT for x in w), "rows": rows}


def measure_count(units):
    all_n = collections.Counter()
    ok_n = collections.Counter()
    for u in units:
        a = sum(1 for x in u["roles"] if x["colour"] == "purple")
        b = sum(1 for x in u["roles"] if x["colour"] == "purple" and x["role"] != "conflict")
        if a:
            all_n[a] += 1
        if b:
            ok_n[b] += 1
    bids = [{"unit": u["unit"], "bids_text": u["bids_text"]} for u in units if u.get("bids_text") is not None]
    return {"all_numbered": dict(sorted(all_n.items())), "non_conflict": dict(sorted(ok_n.items())), "bids_text": bids}


def _bin(d):
    if d < 5:
        return "<5"
    if d < 7:
        return "5-<7"
    if d <= 13:
        return "7-13"
    if d <= 20:
        return ">13-20"
    if d <= 50:
        return ">20-50"
    return ">50"


def measure_depth(units, srcs=("label",), keep_conflict=False):
    rows, not_below = [], []
    for u in units:
        if u.get("low") is None or u.get("low_src") not in srcs:
            continue
        R = [x["value"] for x in u["roles"] if x["colour"] == "red" and (keep_conflict or x["role"] != "conflict")]
        if not R:
            continue
        above = [r for r in R if r > u["low"]]
        if not above:
            not_below.append({"unit": u["unit"], "symbol": u["symbol"], "low": u["low"], "reds": sorted(R)})
            continue
        rs = min(above)
        d = (rs - u["low"]) / rs * 100
        rows.append({"unit": u["unit"], "symbol": u["symbol"], "R": rs, "low": u["low"], "depth": _r(d), "bin": _bin(d)})
    q = _q([r["depth"] for r in rows])
    bins = collections.Counter(r["bin"] for r in rows)
    return {"n": len(rows), "not_below_any_red": len(not_below), "stats": {k: _r(v) if k != "n" else v for k, v in q.items()} if q else None,
            "bins": {b: bins.get(b, 0) for b in DEPTH_BINS}, "rows": sorted(rows, key=lambda r: r["depth"]),
            "not_below": not_below}


def near(a, b):
    return abs(a - b) <= NEAR_PCT / 100 * b


def measure_stop(units, s_rule="nearest"):
    """Amendment ④-⑦: the support is the red nearest to the stop (tie: the higher) · sensitivity: the lowest red."""
    rows = []
    for u in units:
        st = u.get("stop")
        if st is None:
            continue
        R = [x["value"] for x in u["roles"] if x["colour"] == "red" and x["role"] != "conflict"]
        sup = (nearest_red(R, st, st) if s_rule == "nearest" else min(R)) if R else None
        low = u.get("low")
        if low is not None and st < low * (1 - NEAR_PCT / 100):
            cat = "below_low"
        elif low is not None and near(st, low):
            cat = "at_low"
        elif sup is not None and near(st, sup):
            cat = "at_support"
        elif sup is not None and st > sup * (1 + NEAR_PCT / 100):
            cat = "above_support"
        elif sup is not None and low is not None:
            cat = "between_low_support"
        elif sup is not None:
            cat = "below_support_no_low"
        else:
            cat = "above_low_no_support"
        both = low is not None and sup is not None and near(st, low) and near(st, sup)
        rows.append({"unit": u["unit"], "symbol": u["symbol"], "stop": st, "src": u.get("stop_src"), "low": low, "support": sup,
                     "vs_low_pct": _r((st - low) / low * 100) if low else None,
                     "vs_support_pct": _r((st - sup) / sup * 100) if sup else None, "cat": cat, "at_both": both})
    return {"n": len(rows), "cats": dict(collections.Counter(r["cat"] for r in rows)), "at_both": sum(r["at_both"] for r in rows),
            "rows": rows}


def measure_blue(units):
    rows = []
    for u in units:
        B = [x["value"] for x in u["roles"] if x["colour"] == "blue" and x["role"] != "conflict"]
        K = [x["value"] for x in u["roles"] if x["colour"] == "black" and x["role"] != "conflict"]
        if not B or not K:
            continue
        cls = "all_above" if min(B) > max(K) else ("all_below" if max(B) < min(K) else "mixed")
        rows.append({"unit": u["unit"], "symbol": u["symbol"], "blue": sorted(B), "black": sorted(K), "class": cls})
    return {"n": len(rows), "classes": dict(collections.Counter(r["class"] for r in rows)),
            "not_all_above": [r for r in rows if r["class"] != "all_above"]}


def measure_purple_vs(units, other):
    """Amendment ④-④: within a unit with numbered purple and `other` (blue · black): `other` all below the lowest purple ·
    mixed · all above the highest purple."""
    rows = []
    for u in units:
        P = [x["value"] for x in u["roles"] if x["colour"] == "purple"]
        O = [x["value"] for x in u["roles"] if x["colour"] == other and x["role"] != "conflict"]
        if not P or not O:
            continue
        cls = f"{other}_all_below_purple" if max(O) < min(P) else (f"{other}_all_above_purple" if min(O) > max(P) else "mixed")
        rows.append({"unit": u["unit"], "symbol": u["symbol"], "purple": sorted(P), other: sorted(O), "class": cls})
    return {"n": len(rows), "classes": dict(sorted(collections.Counter(r["class"] for r in rows).items())), "rows": rows}


def measure_depth2(units, srcs=("label",)):
    """Amendment ④-⑥ (owner hypothesis «his two supports and the sweep target»): units with >= 2 reds above the low."""
    rows = []
    for u in units:
        if u.get("low") is None or u.get("low_src") not in srcs:
            continue
        R = sorted(x["value"] for x in u["roles"] if x["colour"] == "red" and x["role"] != "conflict" and x["value"] > u["low"])
        if len(R) < 2:
            continue
        r1, r2 = R[0], R[1]
        d1, d2 = (r1 - u["low"]) / r1 * 100, (r2 - u["low"]) / r2 * 100
        rows.append({"unit": u["unit"], "symbol": u["symbol"], "low": u["low"], "R1": r1, "R2": r2, "d1": _r(d1), "d2": _r(d2),
                     "bin1": _bin(d1), "bin2": _bin(d2), "both_7_13": 7 <= d1 <= 13 and 7 <= d2 <= 13})
    n = len(rows)
    both = sum(r["both_7_13"] for r in rows)
    verdict = "no_measure" if n < 10 else ("supported_descriptive" if both * 2 >= n else "dropped_descriptive")
    joint = collections.Counter(f"{r['bin1']}|{r['bin2']}" for r in rows)
    return {"n": n, "both_7_13": both, "verdict": verdict, "joint": dict(sorted(joint.items())),
            "d1": _q([r["d1"] for r in rows]), "d2": _q([r["d2"] for r in rows]), "rows": rows}


def wilson_lo(k, n):
    if n == 0:
        return None
    z, ph = WILSON_Z, k / n
    return (ph + z * z / (2 * n) - z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n))) / (1 + z * z / n)


def derived_role(lv_sides, unit_sides):
    """Amendment ④-③ rule (written before any number): the side holding more than half of the levels AND of the unit votes
    names the role · 'decisive' when Wilson's lower 95% bound exceeds one half in both, else 'likely' · otherwise
    'undecided' · fewer than MIN_LEVELS levels or MIN_UNITS units: 'no_measure'."""
    n, m = len(lv_sides), len(unit_sides)
    if n < MIN_LEVELS or m < MIN_UNITS:
        return "no_measure", None
    for side, name in (("below", "below_support_entry"), ("above", "above_resistance_target")):
        kl, ku = sum(x == side for x in lv_sides), sum(x == side for x in unit_sides)
        if kl * 2 > n and ku * 2 > m:
            return name, ("decisive" if wilson_lo(kl, n) > 0.5 and wilson_lo(ku, m) > 0.5 else "likely")
    return "undecided", None


def shade_map(family):
    return {(x["id"], x["value"]): x["shade"] for x in family["levels"]}


def derived_map(units, shades=None):
    """Amendment ④-③: per colour (and per shade of 'other' when `shades` is given) — levels, units, symbols, rel_pct
    quartiles, side shares and the derived role. Levels of every role count (purple has no conflict rule; red/black/blue
    conflicts are counted too — position is read, not role)."""
    per = collections.defaultdict(lambda: {"rels": [], "sides": [], "unit_rels": collections.defaultdict(list), "symbols": set()})
    no_price = collections.Counter()
    for u in units:
        ids = [k.split("#")[0] for k in u["members"]] if "members" in u else []
        for x in u["roles"]:
            keys = [x["colour"]]
            if shades is not None and x["colour"] == "other":
                sh = next((shades[(i, x["value"])] for i in ids if (i, x["value"]) in shades), "?")
                keys.append("other:" + sh)
            for k in keys:
                if x["side"] is None:
                    no_price[k] += 1
                    continue
                d = per[k]
                d["rels"].append(x["rel"])
                d["sides"].append(x["side"])
                d["unit_rels"][u["unit"]].append(x["rel"])
                if u.get("symbol"):
                    d["symbols"].add(u["symbol"])
    out = {}
    for k in sorted(per, key=lambda k: (k.startswith("other:"), COLOURS.index(k.split(":")[0]) if k.split(":")[0] in COLOURS else 99, k)):
        d = per[k]
        n = len(d["rels"])
        uv = [_side(statistics.median(v)) for v in d["unit_rels"].values()]
        role, strength = derived_role(d["sides"], uv)
        q = _q(d["rels"])
        out[k] = {"levels": n, "units": len(d["unit_rels"]), "symbols": len(d["symbols"]),
                  "median_rel": _r(q["median"]) if q else None, "q1": _r(q["q1"]) if q else None, "q3": _r(q["q3"]) if q else None,
                  "pct_above": _r(100 * d["sides"].count("above") / n), "pct_at": _r(100 * d["sides"].count("at") / n),
                  "pct_below": _r(100 * d["sides"].count("below") / n),
                  "units_above": uv.count("above"), "units_at": uv.count("at"), "units_below": uv.count("below"),
                  "role": role, "strength": strength, "no_price_levels": no_price.get(k, 0)}
    for k, v in no_price.items():
        if k not in out:
            out[k] = {"levels": 0, "units": 0, "symbols": 0, "role": "no_measure", "strength": None, "no_price_levels": v}
    return out


def key_table(units):
    t = collections.defaultdict(collections.Counter)
    for u in units:
        for x in u["roles"]:
            if not x["label"]:
                continue
            roles = label_roles(x["label"])
            t[x["colour"]]["labelled"] += 1
            if not roles:
                t[x["colour"]]["neutral"] += 1
            for c in sorted({c for c, _ in roles}):
                t[x["colour"]][c] += 1
            if roles and x["colour"] in KEY_ROLE:
                t[x["colour"]]["compatible" if not label_conflict(x["colour"], x["label"]) else "incompatible"] += 1
    return {c: dict(sorted(v.items())) for c, v in sorted(t.items())}


def posthoc_labelled_purple(units):
    """POST-HOC — written after the governing numbers were read, NOT in the protocol, carries no verdict: every labelled
    purple level by the role its label names (§③ words · 'neutral' when none) and its side to price_last; the rows whose label
    names a bid or a support are printed by name. It explains a contradiction seen in the numbers (purple sits above the
    price in the map while its labels name bids), it does not test anything."""
    t = collections.defaultdict(collections.Counter)
    rows = []
    for u in units:
        for x in u["roles"]:
            if x["colour"] != "purple" or not x["label"]:
                continue
            roles = sorted({c for c, _ in label_roles(x["label"])}) or ["neutral"]
            for c in roles:
                t[c][x["side"] or "no_price"] += 1
            if {"bid", "support"} & set(roles):
                rows.append({"unit": u["unit"], "symbol": u["symbol"], "value": x["value"], "roles": roles,
                             "side": x["side"], "rel": None if x["rel"] is None else _r(x["rel"]), "label": x["label"]})
    return {"by_role": {c: dict(sorted(v.items())) for c, v in sorted(t.items())}, "rows": rows}


def conflicts(units):
    out = []
    for u in units:
        for x in u["roles"]:
            if x["role"] == "conflict":
                out.append({"unit": u["unit"], "symbol": u["symbol"], "author": u["author"], "colour": x["colour"],
                            "value": x["value"], "why": x["why"], "label": x["label"]})
    return out


GROUPS = (("G1_FAISAL", {"FAISAL"}), ("G2_FAISAL_UNSIGNED", {"FAISAL", "UNSIGNED"}), ("THIRD_PARTY", {"THIRD_PARTY"}),
          ("FOLLOWER", {"FOLLOWER"}), ("OWNER", {"OWNER"}), ("APP", {"APP"}))


GATE_OFF = "not computed: the derived map does not make purple a bid (amendment ④-②)"
BELOW, ABOVE = "below_support_entry", "above_resistance_target"
HEAD_CLASSES = ("RED_BODY_TOP", "RED_BODY_OTHER", "RED_WICK_TOP", "GREEN", "NO_CANDLE", "UNREADABLE")
HEAD_SEED, HEAD_N, HEAD_MIN = 20261015, 40, 10
HEAD_PRECEDENCE = ("RED_BODY_TOP", "RED_WICK_TOP", "RED_BODY_OTHER", "GREEN", "NO_CANDLE")   # ④-⑪ clarification 1


def purple_gate(maps):
    """Amendment ④-②: ①②③ (purple as bid) open only when purple's derived role is 'below' in BOTH G1 and G2."""
    return all(maps.get(g, {}).get("purple", {}).get("role") == BELOW for g in ("G1_FAISAL", "G2_FAISAL_UNSIGNED"))


def measure_all(units, shades=None, gate=False):
    """purple_gate: ①②③ of §⑤ (purple as bid) are computed only when the derived purple role is 'below' in G1 and G2."""
    m = {"units": len(units), "symbols": len({u["symbol"] for u in units if u["symbol"]}),
         "derived_map": derived_map(units, shades), "m1_entries_text": measure_entries(units),
         "bids_text_written": [{"unit": u["unit"], "bids_text": u["bids_text"]} for u in units if u.get("bids_text") is not None],
         "m4_depth": measure_depth(units), "m4b_two_supports": measure_depth2(units), "m5_stop": measure_stop(units),
         "m6_blue_vs_black": measure_blue(units), "m6b_purple_vs_blue": measure_purple_vs(units, "blue"),
         "m6c_purple_vs_black": measure_purple_vs(units, "black"), "key_table": key_table(units), "conflicts": conflicts(units),
         "posthoc_labelled_purple": posthoc_labelled_purple(units)}
    if gate:
        m["m1_bid_vs_support"] = measure_bids(units)
        m["m2_zone_width"] = measure_width(units)
        m["m3_bid_count"] = measure_count(units)
    else:
        m["m1_bid_vs_support"] = m["m2_zone_width"] = m["m3_bid_count"] = GATE_OFF
    return m


def _modal(cnt):
    return max(sorted(cnt), key=lambda k: cnt[k]) if cnt else None


def headline(m):
    dm = m["derived_map"]
    roles = {c: (dm[c]["role"], dm[c]["strength"]) if c in dm else ("no_measure", None) for c in ("red", "black", "blue", "purple")}
    below_colours = sorted(k for k, v in dm.items() if v["role"] == BELOW and k != "red")
    h = {"roles": roles, "below_colours_other_than_red": below_colours,
         "red_not_below": roles["red"][0] == ABOVE, "black_below": roles["black"][0] == BELOW}
    if isinstance(m["m1_bid_vs_support"], dict):
        b = m["m1_bid_vs_support"]["classes"]
        h["m1_majority"] = max(("above", "surrounds", "below"), key=lambda c: (b[c]["n"], c)) if any(b[c]["n"] for c in b) else None
        w = m["m2_zone_width"]["stats"]
        h["m2_median_vs_6"] = None if not w else ("le_6" if w["median"] <= ZONE_PCT else "gt_6")
    else:
        h["m1_majority"] = h["m2_median_vs_6"] = GATE_OFF
    ww = m["m1_entries_text"]["written_width"]
    h["entries_width_median_vs_6"] = None if ww["median"] is None else ("le_6" if ww["median"] <= ZONE_PCT else "gt_6")
    d = m["m4_depth"]["stats"]
    h["m4_median_bin"] = None if not d else _bin(d["median"])
    h["m4b_verdict"] = m["m4b_two_supports"]["verdict"]
    h["m5_modal"] = _modal(m["m5_stop"]["cats"])
    h["m6_majority"] = _modal(m["m6_blue_vs_black"]["classes"])
    h["m6b_majority"] = _modal(m["m6b_purple_vs_blue"]["classes"])
    h["m6c_majority"] = _modal(m["m6c_purple_vs_black"]["classes"])
    return h


def sensitivities(units_primary, units_fold, units_aall, units_pnow, shades, gate):
    g2 = {"FAISAL", "UNSIGNED"}

    def sel(us):
        return [u for u in us if u["author"] in g2]
    out = {"governing": headline(measure_all(sel(units_primary), shades, gate))}
    out["fold_dark_shades"] = headline(measure_all(sel(units_fold), None, gate))
    out["inversion_above_all"] = headline(measure_all(sel(units_aall), shades, gate))
    out["price_now_axis_tag"] = headline(measure_all(sel(units_pnow), shades, gate))
    p = sel(units_primary)
    if gate:
        for name, kw in (("S_lowest_red", {"s_rule": "lowest"}), ("S_highest_red", {"s_rule": "highest"}),
                         ("purple_above_price_out", {"drop_above_price": True})):
            b = measure_bids(p, **kw)
            out[name] = {"m1": {c: b["classes"][c]["n"] for c in b["classes"]}, "n": b["n"]}
    out["stop_lowest_red"] = {k: v for k, v in measure_stop(p, s_rule="lowest").items() if k in ("n", "cats", "at_both")}
    out["depth_with_axis"] = {k: v for k, v in measure_depth(p, srcs=("label", "axis")).items() if k in ("n", "stats", "bins")}
    out["depth_conflicts_kept"] = {k: v for k, v in measure_depth(p, keep_conflict=True).items() if k in ("n", "stats", "bins")}
    out["two_supports_with_axis"] = {k: v for k, v in measure_depth2(p, srcs=("label", "axis")).items() if k in ("n", "both_7_13", "verdict")}
    keys = ("fold_dark_shades", "inversion_above_all", "price_now_axis_tag")
    out["changed_headlines"] = {k: {h: (out["governing"][h], out[k][h]) for h in out["governing"] if out[k][h] != out["governing"][h]}
                                for k in keys if out[k] != out["governing"]}
    return out


# ───────────────────────────── catalog and Phase A ─────────────────────────────


def resolve_images(s, disk):
    out = []
    for tok in (s or "").split():
        tok = re.sub(r"\.(jpg|jpeg|png)$", "", tok)
        m = re.match(r"^IMG_(\d+(?:/\d+)*)$", tok)
        if m:
            out += [f"IMG_{n}" for n in m.group(1).split("/")]
            continue
        m = re.match(r"^(CH|TG|X|WA)_(\d\d(?:/\d\d)*)_([A-Z]+)$", tok)
        if m:
            out += [f"{m.group(1)}_20260918_{n}_{m.group(3)}" for n in m.group(2).split("/")]
            continue
        out.append(tok)
    return [i for i in out if i in disk], out


def head_sample(folded_units, n=HEAD_N, seed=HEAD_SEED):
    """Amendment ④-⑪: G2 units (Faisal + unsigned) holding a purple-family level in the folded reading, sorted by unit id ⟶
    Random(seed).sample(units, n) ⟶ one level per unit by rng.choice over its purple values sorted ascending."""
    cands = sorted((u for u in folded_units if u["author"] in ("FAISAL", "UNSIGNED")
                    and any(x["colour"] == "purple" for x in u["levels"])), key=lambda u: u["unit"])
    rng = random.Random(seed)
    picked = rng.sample(cands, min(n, len(cands)))
    out = []
    for u in picked:
        v = rng.choice(sorted(x["value"] for x in u["levels"] if x["colour"] == "purple"))
        out.append({"unit": u["unit"], "value": v, "symbol": u["symbol"], "author": u["author"]})
    return out


def load_heads(path=HEADS):
    """Latest eye reading per (unit, value) — append-only, rev rises by one with a why after the first · each reading lists
    every contact and its class is the highest contact by HEAD_PRECEDENCE (UNREADABLE: no contacts) · the latest record
    carries `first_class` = the rev-1 class (the first reading, printed for disclosure, never governing)."""
    last, first, probs = {}, {}, []
    if not os.path.exists(path):
        return last, probs
    with open(path, encoding="utf-8") as f:
        for n, ln in enumerate(f, 1):
            if not ln.strip():
                continue
            r = json.loads(ln)
            k = (r.get("unit"), r.get("value"))
            prev = last.get(k, {}).get("rev", 0)
            if r.get("rev") != prev + 1:
                probs.append(f"heads line {n}: {k} rev {r.get('rev')} after {prev}")
            if r.get("rev", 0) > 1 and not r.get("why"):
                probs.append(f"heads line {n}: {k} rev without why")
            cls, con = r.get("class"), r.get("contacts")
            if cls not in HEAD_CLASSES:
                probs.append(f"heads line {n}: class {cls}")
            elif not isinstance(con, list) or any(c not in HEAD_PRECEDENCE for c in con):
                probs.append(f"heads line {n}: {k} contacts {con!r}")
            elif cls == "UNREADABLE":
                if con:
                    probs.append(f"heads line {n}: {k} UNREADABLE with contacts")
            elif not con or cls != min(con, key=HEAD_PRECEDENCE.index):
                probs.append(f"heads line {n}: {k} class {cls} is not the highest contact {con}")
            if r.get("rev") == 1:
                first[k] = cls
            last[k] = r
    return {k: {**r, "first_class": first.get(k)} for k, r in last.items()}, probs


def measure_heads(sample, heads):
    """Amendment ④-⑪ verdict: readable = every class but UNREADABLE · supported_descriptive when RED_BODY_TOP is half of the
    readable or more · dropped_descriptive otherwise · fewer than HEAD_MIN readable: no_measure · sensitivity adds RED_WICK_TOP ·
    `first_reading` = the same tallies on the rev-1 classes (disclosure only — the governing reading is the latest rev)."""
    rows, not_read = [], []
    keys = {(x["unit"], x["value"]) for x in sample}
    for x in sample:
        h = heads.get((x["unit"], x["value"]))
        if h is None:
            not_read.append(x)
            continue
        rows.append({**x, "class": h["class"], "first_class": h.get("first_class") or h["class"],
                     "contacts": h.get("contacts", []), "note": h.get("note", ""), "why": h.get("why", "")})

    def tally(field):
        cnt = collections.Counter(r[field] for r in rows)
        readable = sum(v for k, v in cnt.items() if k != "UNREADABLE")

        def verdict(k):
            return "no_measure" if readable < HEAD_MIN else ("supported_descriptive" if k * 2 >= readable else "dropped_descriptive")
        top = cnt.get("RED_BODY_TOP", 0)
        loose = top + cnt.get("RED_WICK_TOP", 0)
        return ({c: cnt.get(c, 0) for c in HEAD_CLASSES}, readable,
                verdict(top) if not not_read else "incomplete", verdict(loose) if not not_read else "incomplete")
    classes, readable, v, sens = tally("class")
    f_classes, f_readable, f_v, f_sens = tally("first_class")
    return {"sample": len(sample), "read": len(rows), "not_read": len(not_read), "extra_readings": len(set(heads) - keys),
            "classes": classes, "readable": readable, "verdict": v, "sensitivity_top_or_wick": sens,
            "first_reading": {"classes": f_classes, "readable": f_readable, "verdict": f_v, "sensitivity_top_or_wick": f_sens},
            "revised": sum(r["class"] != r["first_class"] for r in rows), "rows": rows}


def purple_family(colour, fam):
    return colour == "purple" or (colour == "other" and fam == "purple")


def bid_entry_review(rows, last, disk, fmap):
    """Amendment ④-⑧: each catalog row with role bid_entry against the eye register — its matching level (within 1%) in
    an image on disk, that chart's price_last and the side ⟶ SURVIVES (below) · RECLASSIFIED_ABOVE · RECLASSIFIED_AT ·
    NO_PRICE · NOT_FOUND · UNVERIFIABLE (no image on disk)."""
    out = []
    for r in rows:
        if r["role"] != "bid_entry":
            continue
        v = float(r["level"])
        d, _ = resolve_images(r["images"], disk)
        base = {"line": r["line"], "images": r["images"], "symbol": r["symbol"], "colour": r["colour"], "level": v}
        if not d:
            out.append({**base, "action": "UNVERIFIABLE"})
            continue
        cand = []
        for n_i, i in enumerate(d):
            for k, c in enumerate(last[i].get("charts", [])):
                for lv in c["levels"]:
                    if abs(lv[1] - v) <= 0.01 * v:
                        fam = fmap.get((i, lv[1]))
                        cand.append((0 if purple_family(lv[0], fam) else 1, abs(lv[1] - v), n_i, k, i, lv, c))
        if not cand:
            out.append({**base, "action": "NOT_FOUND", "disk_ids": d})
            continue
        _, _, _, k, i, lv, c = sorted(cand, key=lambda t: t[:4])[0]
        eye = {"eye_id": f"{i}#{k}", "eye_colour": lv[0], "eye_value": lv[1], "eye_purple_family": purple_family(lv[0], fmap.get((i, lv[1]))),
               "price_last": c.get("price_last")}
        rel, side = side_of(lv[1], c.get("price_last"))
        if side is None:
            out.append({**base, **eye, "action": "NO_PRICE"})
            continue
        act = {"below": "SURVIVES", "above": "RECLASSIFIED_ABOVE", "at": "RECLASSIFIED_AT"}[side]
        out.append({**base, **eye, "rel": _r(rel), "side": side, "action": act})
    cnt = collections.Counter(x["action"] for x in out)
    return {"n": len(out), "actions": dict(sorted(cnt.items())),
            "eye_not_purple_family": sum(1 for x in out if x.get("eye_purple_family") is False), "rows": out}


def anpa_case(path, maps, fold_maps):
    """Amendment ④-⑨: ANPA is printed as an independent witness (not counted in the map) — each drawn level's side to the
    after-hours price and to the regular price tag, and the derived role of its colour (shade row for 'other') per group,
    governing and folded."""
    with open(path, encoding="utf-8") as f:
        a = json.load(f)
    rows = []
    for c in a["charts"]:
        for colour, value, shade, family in c["levels"]:
            r1, s1 = side_of(value, c["price_last"])
            r0, s0 = side_of(value, c["price_now"])
            key = colour if colour != "other" else "other:" + shade
            rows.append({"chart": c["name"], "colour": colour, "shade": shade, "family": family, "value": value,
                         "rel_last": _r(r1), "side_last": s1, "rel_now": _r(r0), "side_now": s0,
                         "derived": {g: m.get(key, {}).get("role", "no_measure") for g, m in maps.items()},
                         "derived_fold": {g: m.get(family, {}).get("role", "no_measure") for g, m in fold_maps.items()}})
    return {"id": a["id"], "posts": a["posts"], "not_levels": a["not_levels"], "notes": a["notes"], "rows": rows,
            "charts": [{k: c[k] for k in ("name", "kind", "frame", "price_last", "price_last_src", "price_now", "bid", "ask", "low", "low_src")}
                       for c in a["charts"]]}


def catalog_section(last, disk, corr, fmap, gate):
    import csv
    with open(TABLE, encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    on, off = [], []
    for r in rows:
        d, _ = resolve_images(r["images"], disk)
        (on if d else off).append((r, d))
    # on-disk rows: governed by the eye register — compare
    match = collections.Counter()
    for r, d in on:
        v, c = float(r["level"]), r["colour"]
        eye = [(lv[0], lv[1]) for i in d for ch in last[i].get("charts", []) for lv in ch["levels"]]
        if (c, v) in eye:
            match["same_colour_value"] += 1
        elif any(abs(ev - v) <= 1e-9 for _, ev in eye):
            match["value_other_colour"] += 1
        else:
            match["absent_in_eye"] += 1
    # catalog-only groups: measure ① on the catalog roles, with the same inversion rule
    groups = collections.OrderedDict()
    for r, _ in off:
        groups.setdefault((r["line"], r["images"], r["symbol"], r["frame"]), []).append(r)
    cu = []
    for k, rs in groups.items():
        lv = [{"colour": r["colour"], "value": float(r["level"]), "label": "", "conf": "M"} for r in rs]
        u = {"unit": "catalog:" + k[0] + ":" + k[3], "symbol": k[2] or None, "price_now": None, "levels": lv,
             "author": "UNSIGNED", "low": None, "low_src": None, "stop": None, "entries_text": None, "bids_text": None}
        u["roles"] = assign_roles(u)
        cu.append(u)
    actions = collections.Counter(c["action"] for c in corr)
    out = {"table_rows": len(rows), "rows_on_disk": len(on), "rows_catalog_only": len(off),
           "images_in_table": len({i for r, _ in on + off for i in resolve_images(r["images"], disk)[1]}),
           "on_disk_vs_eye": dict(match), "catalog_only_groups": len(cu),
           "bid_entry_review": bid_entry_review(rows, last, disk, fmap)}
    if gate:
        b, w = measure_bids(cu), measure_width(cu)
        out["catalog_only_m1"] = {c: b["classes"][c] for c in b["classes"]}
        out["catalog_only_m1_n"] = b["n"]
        out["catalog_only_m2"] = {k: v for k, v in w.items() if k in ("n", "single_line", "stats", "le_6", "gt_6")}
    else:
        out["catalog_only_m1"] = out["catalog_only_m2"] = GATE_OFF
    out.update({
            "phase_a": {"rows": len(corr), "actions": dict(sorted(actions.items())),
                        "purple_rows": sum(1 for c in corr if c["colour"] == "purple"),
                        "groups": len({c["line"] for c in corr}),
                        "note": "candidate definition (±30% from S) rested on the suspended map; DROP/CORRECT are map-independent (amendment ④-⑩)"}})
    return out


# ───────────────────────────── build ─────────────────────────────


def coverage(last, charts, units, ids):
    kinds = collections.Counter("charts" if "charts" in r else ("dup_of" if "dup_of" in r else "none") for r in last.values())
    reasons = collections.Counter(r["none"] for r in last.values() if "none" in r)
    levels = [lv for c in charts for lv in c["levels"]]
    ulev = [lv for u in units for lv in u["levels"]]
    return {"files_in_folder": len(ids) + 1, "images": len(ids), "records": len(last),
            "images_with_numbered_levels": kinds["charts"], "pct_of_images": _r(kinds["charts"] / len(ids) * 100),
            "pct_of_files": _r(kinds["charts"] / (len(ids) + 1) * 100),
            "duplicates": kinds["dup_of"], "none": dict(sorted(reasons.items())), "triage_thumb": sum(1 for r in last.values() if r.get("triage") == "thumb"),
            "charts": len(charts), "units": len(units), "merged_away": len(charts) - len(units),
            "units_by_author": dict(sorted(collections.Counter(u["author"] for u in units).items())),
            "units_without_symbol": sum(1 for u in units if not u["symbol"]), "symbols": len({u["symbol"] for u in units if u["symbol"]}),
            "chart_levels": len(levels), "unit_levels": len(ulev),
            "unit_levels_by_colour": dict(sorted(collections.Counter(lv["colour"] for lv in ulev).items())),
            "conf_share": {k: _r(v / len(ulev) * 100) for k, v in sorted(collections.Counter(lv["conf"] for lv in ulev).items())},
            "unnumbered_lines": sum(sum((c.get("unnumbered") or {}).values()) for c in charts),
            "revisions": sum(1 for r in last.values() if r["rev"] > 1),
            "price_last_charts": dict(sorted(collections.Counter(c.get("price_last_src") if c.get("price_last") is not None else "none"
                                                                for c in charts).items())),
            "price_last_units": sum(1 for u in units if u.get("price_last") is not None),
            "price_last_from_member": sum(1 for u in units if "price_last" in u["filled_from_member"]),
            "price_now_units": sum(1 for u in units if u.get("price_now") is not None)}


def build():
    ids = image_ids()
    last, order, probs = load_register()
    probs += validate(last, ids)
    if probs:
        for p in probs[:30]:
            print("⛔", p)
        sys.exit(9)
    charts = charts_of(last, order)
    units = build_units(charts)
    with open(FAMILY, encoding="utf-8") as f:
        fam = json.load(f)
    fmap, shades = fold_map(fam), shade_map(fam)
    for u in units:
        u["roles"] = assign_roles(u)
    folded = recolour(units, fmap)
    for u in folded:
        u["roles"] = assign_roles(u)
    aall = [{**u, "roles": assign_roles(u, above_all=True)} for u in units]
    heads, hprobs = load_heads()
    if hprobs:
        for p in hprobs[:30]:
            print("⛔", p)
        sys.exit(9)
    pnow = [{**u, "roles": assign_roles(u, price_key="price_now")} for u in units]
    with open(KEYTEXT, encoding="utf-8") as f:
        key_text = [json.loads(ln) for ln in f if ln.strip()]
    with open(CORR, encoding="utf-8") as f:
        corr = [json.loads(ln) for ln in f if ln.strip()]
    sel = {name: [u for u in units if u["author"] in auths] for name, auths in GROUPS}
    pre = {name: derived_map(us, shades) for name, us in sel.items() if us}
    gate = purple_gate(pre)
    res = {"coverage": coverage(last, charts, units, ids), "purple_gate": gate, "groups": {}}
    for name, us in sel.items():
        res["groups"][name] = measure_all(us, shades, gate) if us else {"units": 0}
    fold_maps = {name: derived_map([u for u in folded if u["author"] in auths]) for name, auths in GROUPS
                 if any(u["author"] in auths for u in folded)}
    res["fold_maps"] = fold_maps
    res["sensitivity_G2"] = sensitivities(units, folded, aall, pnow, shades, gate)
    res["fold_changed_levels"] = sum(1 for a, b in zip(units, folded) for x, y in zip(a["levels"], b["levels"]) if x["colour"] != y["colour"])
    res["camera_corrections"] = sorted(r["id"] for r in last.values() if r["rev"] > 1 and "X_20260918_27_CUPR" in (r.get("why") or ""))
    res["filled_from_member"] = sum(1 for u in units if u["filled_from_member"])
    res["key_text"] = {a: [k for k in key_text if k["author"] == a and not k["same_as"]] for a in AUTHORS if any(k["author"] == a for k in key_text)}
    res["catalog"] = catalog_section(last, set(ids), corr, fmap, gate)
    res["anpa"] = anpa_case(ANPA, {g: res["groups"][g]["derived_map"] for g in ("G1_FAISAL", "G2_FAISAL_UNSIGNED")},
                            {g: fold_maps.get(g, {}) for g in ("G1_FAISAL", "G2_FAISAL_UNSIGNED")})
    res["purple_heads"] = measure_heads(head_sample(folded), heads)
    res["null_symbol_twins"] = sum(1 for u in units if not u["symbol"] and any(v is not u and not v["symbol"] and
                                   {(x["colour"], x["value"]) for x in v["levels"]} == {(x["colour"], x["value"]) for x in u["levels"]} for v in units))
    return units, folded, res


def render_tsv(units, folded):
    cols = ("unit", "members", "author", "symbol", "frame", "colour", "colour_folded", "value", "label", "conf", "role", "why",
            "price_last", "price_last_src", "rel_pct", "side", "price_now", "low", "low_src")
    lines = ["\t".join(cols)]
    for u, f in zip(units, folded):
        for x, y in zip(u["roles"], f["roles"]):
            row = (u["unit"], " ".join(u["members"]), u["author"], u["symbol"] or "", u["frame"] or "", x["colour"], y["colour"],
                   repr(x["value"]), x["label"].replace("\t", " "), x["conf"], x["role"], ",".join(x["why"]),
                   "" if u["price_last"] is None else repr(u["price_last"]), u["price_last_src"] or "",
                   "" if x["rel"] is None else f"{x['rel']:.2f}", x["side"] or "",
                   "" if u["price_now"] is None else repr(u["price_now"]), "" if u["low"] is None else repr(u["low"]), u["low_src"] or "")
            lines.append("\t".join(str(c) for c in row))
    return "\n".join(lines) + "\n"


def _fmt(v):
    return "—" if v is None else (f"{v:g}" if isinstance(v, (int, float)) else str(v))


ROLE_AR = {BELOW: "تحت ⟵ دعم/دخول", ABOVE: "فوق ⟵ مقاومة/هدف", "undecided": "غير محسوم", "no_measure": "لا قياس"}
STRENGTH_AR = {"decisive": "حاسم", "likely": "مرجّح", None: ""}


def _map_table(dm):
    L = ["| اللون | مستويات | وحدات | رموز | وسيط rel % | الربيعيّان | % فوق | % عند | % تحت | وحداتٌ فوق/عند/تحت | الدور المشتقّ | بلا سعر |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, v in dm.items():
        if not v["levels"]:
            L.append(f"| {k} | 0 | 0 | 0 | — | — | — | — | — | — | لا قياس | {v['no_price_levels']} |")
            continue
        L.append(f"| {k} | {v['levels']} | {v['units']} | {v['symbols']} | {_fmt(v['median_rel'])} | {_fmt(v['q1'])}/{_fmt(v['q3'])} | "
                 f"{_fmt(v['pct_above'])} | {_fmt(v['pct_at'])} | {_fmt(v['pct_below'])} | {v['units_above']}/{v['units_at']}/{v['units_below']} | "
                 f"{ROLE_AR[v['role']]} {STRENGTH_AR[v['strength']]} | {v['no_price_levels']} |")
    return L


def render_md(res):
    c = res["coverage"]
    L = ["# `T-COLOUR` — الجداول (مولَّدةٌ من `data/colour_result.json` بـ`colour_build.py` · لا تُحرَّر باليد)", ""]
    L += ["## التغطية", "", "| البند | العدد |", "|---|---|"]
    for k in ("files_in_folder", "images", "images_with_numbered_levels", "pct_of_images", "pct_of_files", "duplicates", "triage_thumb",
              "charts", "units", "merged_away", "units_without_symbol", "symbols", "unit_levels", "unnumbered_lines", "revisions",
              "price_last_units", "price_last_from_member", "price_now_units"):
        L.append(f"| `{k}` | {_fmt(c[k])} |")
    for k in ("none", "units_by_author", "unit_levels_by_colour", "price_last_charts"):
        L.append(f"| `{k}` | {' · '.join(f'{a} {b}' for a, b in c[k].items())} |")
    L.append(f"| `conf_share` % | {' · '.join(f'{k} {v}' for k, v in c['conf_share'].items())} |")
    L += ["", f"**بوّابةُ البنفسجيّ (التعديل ④-②):** {'مفتوحة — ①②③ تُحسب' if res['purple_gate'] else 'مغلقة — ①②③ لا تُحسب'}", ""]
    for g, m in res["groups"].items():
        if not m.get("units"):
            L += [f"## {g}: لا وحدات", ""]
            continue
        L += [f"## {g} — {m['units']} وحدة · {m['symbols']} رمزًا", "", "**⓪ الخريطةُ المشتقّة** (`rel_pct` إلى `price_last` · ‏±1% «عند»):", ""]
        L += _map_table(m["derived_map"])
        fm = res["fold_maps"].get(g)
        if fm:
            L += ["", "**⓪ بقراءة الطيّ** (الدرجاتُ الداكنة إلى عائلتها):", ""] + _map_table(fm)
        e = m["m1_entries_text"]
        vp, ww = e["vs_price"], e["written_width"]
        L += ["", f"**الدخولُ المكتوب نصًّا:** للأحمر الأقرب {e['n']} سعرًا في {e['units']} وحدة · فوقه {e['above']} · عنده {e['at']} · تحته {e['below']} · "
              f"الوسيط {_fmt(e['median_pct'])}% · وللسعر {vp['n']} · فوق {vp['sides']['above']} · عند {vp['sides']['at']} · تحت {vp['sides']['below']} · "
              f"الوسيط {_fmt(vp['median_rel'])}% · وعرضُ المكتوب (سعران فأكثر) {ww['n']} وحدة · الوسيط {_fmt(ww['median'])}% · 6% أو أقلّ {ww['le_6']} · فوقها {ww['gt_6']}", ""]
        if isinstance(m["m1_bid_vs_support"], dict):
            b = m["m1_bid_vs_support"]
            L += [f"**① البنفسجيُّ مقابل الدعم** — {b['n']} وحدة", "", "| الفئة | العدد | وسيط lo % | وسيط hi % |", "|---|---|---|---|"]
            for cls in ("above", "surrounds", "below"):
                x = b["classes"][cls]
                L.append(f"| {cls} | {x['n']} | {_fmt(x['median_lo'])} | {_fmt(x['median_hi'])} |")
            w = m["m2_zone_width"]
            st = w["stats"] or {}
            L += ["", f"**② عرضُ البنفسجيّ** — {w['n']} وحدة · خطٌّ واحد {w['single_line']} · الوسيط {_fmt(st.get('median'))}% · 6% أو أقلّ {w['le_6']} · فوقها {w['gt_6']}",
                  "", f"**③ عددُ البنفسجيّات** — {m['m3_bid_count']['all_numbered']}", ""]
        else:
            L += [f"**①②③ (البنفسجيُّ طلبًا):** {GATE_OFF}", ""]
        L += [f"**عددُ الطلبات مكتوبًا (`bids_text`):** {len(m['bids_text_written'])} وحدة", ""]
        d = m["m4_depth"]
        st = d["stats"] or {}
        L += [f"**④ العمقُ تحت الأحمر** (`low_src=label`) — {d['n']} وحدة · لم ينزل تحت أيّ أحمر {d['not_below_any_red']} · "
              f"الوسيط {_fmt(_r(st.get('median')))}% · الربيعيّان {_fmt(_r(st.get('q1')))}/{_fmt(_r(st.get('q3')))} · المدى {_fmt(_r(st.get('min')))}-{_fmt(_r(st.get('max')))}",
              "", "| الفئة | " + " | ".join(d["bins"]) + " |", "|---|" + "---|" * len(d["bins"]),
              "| العدد | " + " | ".join(str(v) for v in d["bins"].values()) + " |", "",
              "التوزيعُ كما يخرج: " + " · ".join(f"{r['depth']}" for r in d["rows"]), ""]
        t2 = m["m4b_two_supports"]
        L += [f"**④-ب دعماه وهدفُ الكنسة** — {t2['n']} وحدة بأحمرين فوق القاع · الاثنان داخل 7-13 {t2['both_7_13']} ⟵ {t2['verdict']} · "
              f"الجدولُ المشترك (d1|d2): {' · '.join(f'{k} {v}' for k, v in t2['joint'].items())}", ""]
        for r in t2["rows"]:
            L.append(f"- `{r['unit']}` {_fmt(r['symbol'])}: القاع {r['low']:g} · R1 {r['R1']:g} ({r['d1']}%) · R2 {r['R2']:g} ({r['d2']}%)")
        st = m["m5_stop"]
        L += ["", f"**⑤ الوقف** (الدعم = الأحمرُ الأقربُ إلى الوقف) — {st['n']} وحدة · {' · '.join(f'{k2} {v}' for k2, v in sorted(st['cats'].items()))} · عند القاع والدعم معًا {st['at_both']}", ""]
        for r in st["rows"]:
            L.append(f"- `{r['unit']}` {_fmt(r['symbol'])}: الوقف {r['stop']:g} ({r['src']}) · القاع {_fmt(r['low'])} ({_fmt(r['vs_low_pct'])}%) · الدعم {_fmt(r['support'])} ({_fmt(r['vs_support_pct'])}%) ⟵ {r['cat']}")
        for key, title in (("m6_blue_vs_black", "⑥ الأزرقُ مقابل الأسود"), ("m6b_purple_vs_blue", "⑥-ب البنفسجيُّ مقابل الأزرق"),
                           ("m6c_purple_vs_black", "⑥-ج البنفسجيُّ مقابل الأسود")):
            bb = m[key]
            L += ["", f"**{title}** — {bb['n']} وحدة · {' · '.join(f'{k2} {v}' for k2, v in sorted(bb['classes'].items()))}", ""]
        for r in m["m6_blue_vs_black"]["not_all_above"]:
            L.append(f"- `{r['unit']}` {_fmt(r['symbol'])}: أزرق {r['blue']} · أسود {r['black']} ⟵ {r['class']}")
        cols = ("labelled", "support", "resistance", "target", "bid", "gap", "drop", "neutral", "compatible", "incompatible")
        L += ["", "**جدولُ المفتاح** (خطوطٌ ذاتُ ملصق · البنفسجيُّ بلا حكمِ توافق):", "", "| اللون | " + " | ".join(cols) + " |", "|---|" + "---|" * len(cols)]
        for col, v in m["key_table"].items():
            L.append(f"| {col} | " + " | ".join(str(v.get(x, 0)) for x in cols) + " |")
        L += ["", f"**التعارضات بأسمائها ({len(m['conflicts'])}):**", ""]
        for x in m["conflicts"]:
            L.append(f"- `{x['unit']}` {_fmt(x['symbol'])} · {x['colour']} {x['value']:g} · {','.join(x['why'])}" + (f" · «{x['label']}»" if x["label"] else ""))
        ph = m["posthoc_labelled_purple"]
        L += ["", "**قراءةٌ بعد الرقم — غيرُ مسجَّلةٍ في البروتوكول ولا تحكم:** البنفسجيُّ ذو الملصق بدور ملصقه وموضعه من `price_last`", ""]
        for c, v in ph["by_role"].items():
            L.append(f"- {c}: " + " · ".join(f"{k2} {n}" for k2, n in v.items()))
        for r in ph["rows"]:
            L.append(f"- `{r['unit']}` {_fmt(r['symbol'])} · {r['value']:g} · {','.join(r['roles'])} · {r['side'] or '—'} ({_fmt(r['rel'])}%) · «{r['label']}»")
        L.append("")
    s_ = res["sensitivity_G2"]
    L += ["## الحساسيّة (المجموعة الثانية FAISAL ∪ UNSIGNED)", "", "```json", json.dumps(s_, ensure_ascii=False, indent=1, sort_keys=True), "```", ""]
    cat = res["catalog"]
    br = cat["bid_entry_review"]
    L += ["## صفوفُ `bid_entry` في الجدول القائم (التعديل ④-⑧)", "", f"{br['n']} صفًّا · {' · '.join(f'{k} {v}' for k, v in br['actions'].items())} · "
          f"لونُ العين ليس من عائلة البنفسجيّ {br['eye_not_purple_family']}", "", "| السطر | الصور | الرمز | المستوى | العين | price_last | rel % | الحكم |", "|---|---|---|---|---|---|---|---|"]
    for r in br["rows"]:
        L.append(f"| {r['line']} | {r['images']} | {r['symbol'] or '—'} | {r['level']:g} | {r.get('eye_colour', '—')} {_fmt(r.get('eye_value'))} | "
                 f"{_fmt(r.get('price_last'))} | {_fmt(r.get('rel'))} | {r['action']} |")
    rest = {k: v for k, v in cat.items() if k != "bid_entry_review"}
    L += ["", "## الكاتالوج القائم ومرحلة أ", "", "```json", json.dumps(rest, ensure_ascii=False, indent=1, sort_keys=True), "```", ""]
    ph = res["purple_heads"]
    L += ["## فرضيّةُ «البنفسجيُّ رؤوسُ الشموع الحمرا الساقطة» — عيّنةٌ بالعين داخل الصورة (التعديل ④-⑪)", "",
          f"العيّنة {ph['sample']} (بذرة {HEAD_SEED}) · قُرئ {ph['read']} · لم يُقرأ {ph['not_read']} · مقروءٌ {ph['readable']} · "
          f"**الحكم: {ph['verdict']}** · والحساسيّة (رأسُ الجسم أو الذيل) {ph['sensitivity_top_or_wick']}", "",
          f"القراءةُ الأولى (rev 1 — للإفصاح لا تحكم): {ph['first_reading']['verdict']} · والحساسيّة {ph['first_reading']['sensitivity_top_or_wick']} · "
          f"وغيّرت المراجعةُ فئةَ {ph['revised']} من {ph['read']}", "",
          "| الفئة | العدد | القراءةُ الأولى |", "|---|---|---|"]
    for c in HEAD_CLASSES:
        L.append(f"| {c} | {ph['classes'][c]} | {ph['first_reading']['classes'][c]} |")
    L += ["", "| الوحدة | الرمز | المستوى | الفئة | القراءةُ الأولى | التماسّات | ملاحظة | سببُ المراجعة |", "|---|---|---|---|---|---|---|---|"]
    for r in ph["rows"]:
        L.append(f"| {r['unit']} | {r['symbol'] or '—'} | {r['value']:g} | {r['class']} | {r['first_class']} | {' · '.join(r['contacts'])} | "
                 f"{r['note']} | {r['why'] or '—'} |")
    L.append("")
    a = res["anpa"]
    L += ["## ANPA — شاهدٌ مستقلّ لا يدخل الخريطة (التعديل ④-⑨)", ""]
    for ps in a["posts"]:
        L.append(f"- {ps['time_ksa']} (السعوديّة) · " + (f"«{ps['text']}»" if ps.get("text") else "—") + f" · {ps.get('source', '')}"
                 + (f" · {ps['indicators']}" if ps.get("indicators") else ""))
    for ch_ in a["charts"]:
        L.append(f"- الشارت {ch_['name']} ({ch_['kind']} · {ch_['frame']}): price_last {ch_['price_last']} ({ch_['price_last_src']}) · وسمُ السعر {ch_['price_now']} · "
                 f"طلب {ch_['bid']} · عرض {ch_['ask']} · القاع {ch_['low']} ({ch_['low_src']})")
    for nl in a["not_levels"]:
        L.append(f"- ليس مستوًى: {nl['value']} — {nl['why']}")
    L += ["", "| الشارت | اللون | الدرجة | المستوى | rel إلى price_last | الموضع | rel إلى الوسم | الدور المشتقّ G1 / G2 | بالطيّ G1 / G2 |", "|---|---|---|---|---|---|---|---|---|"]
    for r in a["rows"]:
        L.append(f"| {r['chart']} | {r['colour']} | {r['shade'] or '—'} | {r['value']:g} | {r['rel_last']} | {r['side_last']} | {r['rel_now']} | "
                 f"{ROLE_AR.get(r['derived']['G1_FAISAL'], r['derived']['G1_FAISAL'])} / {ROLE_AR.get(r['derived']['G2_FAISAL_UNSIGNED'], r['derived']['G2_FAISAL_UNSIGNED'])} | "
                 f"{ROLE_AR.get(r['derived_fold']['G1_FAISAL'], r['derived_fold']['G1_FAISAL'])} / {ROLE_AR.get(r['derived_fold']['G2_FAISAL_UNSIGNED'], r['derived_fold']['G2_FAISAL_UNSIGNED'])} |")
    for nt in a["notes"]:
        L.append(f"- {nt}")
    L += ["", "## مفتاحُ الألوان بلفظ المصادر (بلا المكرّر)", ""]
    for au, ks in res["key_text"].items():
        for k in ks:
            L.append(f"- {au} · `{k['id']}` · {k['colour']} ⟵ {k['role']} · «{k['phrase']}»")
    L += ["", f"طيُّ الدرجات غيّر لون {res['fold_changed_levels']} مستوًى في الوحدات · تصحيحاتُ الكاميرا {res['camera_corrections']} · "
          f"وحداتٌ أُكمل حقلُها من عضوٍ غيرِ المختار {res['filled_from_member']} · وحداتٌ بلا رمزٍ لها توأمٌ مطابقٌ بلا رمز {res['null_symbol_twins']}", ""]
    return "\n".join(L)


def outputs():
    units, folded, res = build()
    js = json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    return {OUT_TSV: render_tsv(units, folded), OUT_JSON: js, OUT_MD: render_md(res)}


# ───────────────────────────── guards ─────────────────────────────


def guards():
    ok = []

    def g(name, fn):
        """Each guard is a thunk returning (cond, detail); a crash is a clean failure, never a collapse."""
        try:
            cond, why = fn()
        except Exception as e:                                      # noqa: BLE001
            cond, why = False, f"⛔ رمى: {type(e).__name__}: {e}"
        ok.append(bool(cond))
        print(("✅ " if cond else "❌ ") + name + ("" if cond else f" — {why}"))

    def first(rows):
        return rows[0] if rows else {}

    def ch(key, sym, levels, author="UNSIGNED", **kw):
        c = {"key": key, "id": key.split("#")[0], "author": author, "symbol": sym, "frame": "D", "price_now": kw.get("price"),
             "price_last": kw.get("plast"), "price_last_src": "ext" if kw.get("plast") else None,
             "low": kw.get("low"), "low_src": kw.get("low_src", "label" if kw.get("low") else None), "stop": kw.get("stop"),
             "stop_src": "text" if kw.get("stop") else None, "bids_text": None, "entries_text": kw.get("entries"),
             "levels": [[c_, v, kw.get("labels", {}).get(v, ""), "H"] for c_, v in levels]}
        c["set"] = frozenset((a, b) for a, b in levels)
        return c

    def roles(levels, price=None, above_all=False):
        u = {"levels": [{"colour": c, "value": v, "label": lab, "conf": "H"} for c, v, lab in levels], "price_last": price}
        return {(x["colour"], x["value"]): (x["role"], x["why"], x["side"]) for x in assign_roles(u, above_all)}

    def mk(levels, **kw):
        u = {"unit": kw.get("unit", "u"), "symbol": "S", "price_now": kw.get("pnow"), "price_last": kw.get("price"),
             "low": kw.get("low"), "low_src": "label",
             "stop": kw.get("stop"), "stop_src": "text", "entries_text": kw.get("entries"), "bids_text": None, "author": "FAISAL",
             "levels": [{"colour": c, "value": v, "label": "", "conf": "H"} for c, v in levels]}
        u["roles"] = assign_roles(u)
        return u

    # CG1 labels
    g("CG1 «مقاومه تحولت لدعم» = دعم وحدَه", lambda: (label_roles("مقاومه تحولت لدعم") == {("support", "دعم")}, label_roles("مقاومه تحولت لدعم")))
    g("CG1 الأحمرُ مع «دخول» متوافق · والبنفسجيُّ بلا حكمِ توافق (التعديل ④): «مقاومه» لا تعارضه",
      lambda: (not label_conflict("red", "دخول 1.40 (نصّ الرسالة)") and not label_conflict("purple", "مقاومه") and "purple" not in KEY_ROLE, ""))
    g("CG1 أزرقُ «الدعم الاساسي» تعارض · أسودُ «هدف» متوافق · ملصقٌ بلا دور محايد",
      lambda: (label_conflict("blue", "الدعم الاساسي") and not label_conflict("black", "هدف 4") and not label_conflict("red", "تحرر السهم"), ""))
    g("CG1 الوسمُ لا يُقرأ دورًا · والملصقُ بلا دورٍ لا يعارض", lambda: (label_roles("1.53 (نصّ المنشور)") == set()
      and not label_conflict("blue", "1.53 (نصّ المنشور)"), label_roles("1.53 (نصّ المنشور)")))
    g("CG1 التطبيعُ العربيّ: «فجوة» و«الأهداف» تُقرآن", lambda: ({c for c, _ in label_roles("فجوة سعرية")} == {"gap"}
      and {c for c, _ in label_roles("الأهداف ب الازرق")} == {"target"}, (label_roles("فجوة سعرية"), label_roles("الأهداف ب الازرق"))))
    # CG2 inversion
    r1 = lambda: roles([("red", 5.0, ""), ("black", 4.0, ""), ("black", 6.0, "")])        # noqa: E731
    g("CG2 أحمرُ فوق أسود ⟵ الاثنان", lambda: (r1()[("red", 5.0)][0] == "conflict" and r1()[("black", 4.0)][0] == "conflict"
      and r1()[("black", 6.0)][0] == "resistance", r1()))
    r2 = lambda: roles([("red", 5.0, ""), ("blue", 4.0, ""), ("blue", 7.0, "")])          # noqa: E731
    g("CG2 أزرقُ تحت أحمر ⟵ الاثنان · والأزرقُ فوقه سليم", lambda: (r2()[("blue", 4.0)][0] == "conflict" and r2()[("red", 5.0)][0] == "conflict"
      and r2()[("blue", 7.0)][0] == "target_clean", r2()))
    r3 = lambda: roles([("purple", 9.0, ""), ("black", 8.0, ""), ("red", 1.0, "")])       # noqa: E731
    g("CG2 بنفسجيٌّ فوق أسود ليس تعارضًا بعد التعديل ④ · ودورُه غيرُ مسنَدٍ من المفتاح", lambda: (r3()[("purple", 9.0)][:2] == ("unmapped", [])
      and r3()[("black", 8.0)][0] == "resistance", r3()))
    r4 = lambda: roles([("purple", 0.9, ""), ("red", 1.0, ""), ("blue", 3.0, ""), ("black", 4.0, "")])   # noqa: E731
    g("CG2 بنفسجيٌّ تحت أحمر وأزرقُ تحت أسود ليسا تعارضًا", lambda: (all(v[0] != "conflict" for v in r4().values()), r4()))
    r5 = lambda: roles([("red", 5.0, ""), ("black", 4.0, ""), ("black", 6.0, "")], above_all=True)       # noqa: E731
    g("CG2 حساسيّةُ «فوق كلِّه»: الأحمرُ تحت أعلى أسود ليس تعارضًا", lambda: (r5()[("red", 5.0)][0] == "support", r5()))
    r6 = lambda: roles([("red", 5.0, ""), ("purple", 6.0, ""), ("other", 4.03, "")], price=4.0)              # noqa: E731
    g("CG2 الموضعُ مقابل السعر وسمٌ لا تعارض (فوق · عند ±1%)", lambda: (r6()[("red", 5.0)][:3] == ("support", [], "above")
      and r6()[("purple", 6.0)][2] == "above" and r6()[("other", 4.03)][2] == "at", r6()))
    # CG3 merge
    A = ch("A#0", "X", [("red", 1.0), ("black", 2.0)])
    B = ch("B#0", "X", [("red", 1.0), ("black", 2.0)], author="FAISAL")
    C = ch("C#0", "X", [("red", 1.0), ("black", 2.0), ("blue", 3.0)])
    D = ch("D#0", "X", [("red", 1.0), ("black", 2.0), ("purple", 0.5), ("blue", 9.0)])
    E = ch("E#0", None, [("red", 1.0), ("black", 2.0), ("blue", 3.0)])
    F = ch("F#0", "Y", [("red", 1.0)])
    G_ = ch("G#0", "Y", [("red", 1.0), ("black", 7.0)])
    N = ch("N#0", None, [("red", 1.0), ("black", 7.0)])
    N2 = ch("N2#0", None, [("red", 1.0), ("blue", 9.0)])     # a strict subset of D, identical to nothing

    def by():
        return {u["unit"]: u for u in build_units([A, B, C, D, E, F, G_, N, N2])}
    g("CG3 الجزءُ يُمتصّ في أكبر شامل · والشاملان المتنافران يبقيان", lambda: (set(by()) == {"C#0", "D#0", "F#0", "G#0", "N2#0"}
      and set(by()["D#0"]["members"]) == {"A#0", "B#0", "D#0"} and set(by()["C#0"]["members"]) == {"C#0", "E#0"}
      and set(by()["G#0"]["members"]) == {"G#0", "N#0"}, {k: v["members"] for k, v in by().items()}))
    g("CG3 الكاتبُ FAISAL إن كان أيُّ عضوٍ فيصل · وإلّا UNSIGNED", lambda: (by()["D#0"]["author"] == "FAISAL" and by()["C#0"]["author"] == "UNSIGNED", ""))
    g("CG3 خطٌّ واحدٌ مشترك لا يدمج (اثنان فأكثر)", lambda: (by().get("F#0", {}).get("members") == ["F#0"], by().get("F#0")))
    g("CG3 ما بلا رمز يندمج بالمطابق تمامًا وحدَه (لا بالشامل)", lambda: (by()["C#0"]["symbol"] == "X" and "N2#0" in by()
      and by()["N2#0"]["symbol"] is None, sorted(by())))
    H = ch("H#0", "Z", [("red", 1.0), ("black", 2.0)], author="THIRD_PARTY")
    I2 = ch("I#0", "Z", [("red", 1.0), ("black", 2.0), ("blue", 4.0)])
    g("CG3 الكاتبُ الصنفُ الوحيدُ غيرُ UNSIGNED", lambda: ([u["author"] for u in build_units([H, I2])] == ["THIRD_PARTY"],
                                                       [u["author"] for u in build_units([H, I2])]))
    H2 = ch("H#0", "Z", [("red", 1.0), ("black", 2.0)], author="THIRD_PARTY")
    I3 = ch("I#0", "Z", [("red", 1.0), ("black", 2.0), ("blue", 4.0)], author="FAISAL")
    g("CG3 فيصلُ مع طرفٍ ثالث ⟵ FAISAL", lambda: ([u["author"] for u in build_units([H2, I3])] == ["FAISAL"], [u["author"] for u in build_units([H2, I3])]))
    J = ch("J#0", "W", [("red", 1.0), ("black", 2.0)], labels={1.0: "دعم"})
    K = ch("K#0", "W", [("red", 1.0), ("black", 2.0), ("blue", 3.0)], labels={1.0: "قاع"})

    def lab():
        return {x["value"]: x["label"] for x in build_units([J, K])[0]["levels"]}
    g("CG3 ملصقُ الوحدة اتّحادُ ملصقات الأعضاء", lambda: (lab()[1.0] in ("قاع · دعم", "دعم · قاع"), lab()))
    # CG4 measure ①
    g("CG4 S = الأحمرُ الأقربُ إلى مجال البنفسجيّ", lambda: (first(measure_bids([mk([("purple", 2.0), ("purple", 2.2), ("red", 1.5), ("red", 1.9)])])["rows"]).get("S") == 1.9
      and first(measure_bids([mk([("purple", 2.0), ("purple", 2.2), ("red", 1.5), ("red", 1.9)])])["rows"]).get("class") == "above", ""))
    b2 = lambda: first(measure_bids([mk([("purple", 1.8), ("purple", 2.2), ("red", 2.0)])])["rows"])      # noqa: E731
    g("CG4 الأحمرُ داخل المجال ⟵ يحيط", lambda: (b2().get("class") == "surrounds" and b2().get("lo") == -10.0 and b2().get("hi") == 10.0, b2()))
    b3 = lambda: first(measure_bids([mk([("purple", 2.0), ("purple", 2.5), ("red", 2.0)])])["rows"])      # noqa: E731
    g("CG4 Pmin = S ⟵ يحيط لا فوق", lambda: (b3().get("class") == "surrounds" and b3().get("lo") == 0.0, b3()))
    b4 = lambda: first(measure_bids([mk([("purple", 2.0), ("red", 1.8), ("red", 2.2)])])["rows"])         # noqa: E731
    g("CG4 التعادلُ للأعلى", lambda: (b4().get("S") == 2.2 and b4().get("class") == "below", b4()))
    g("CG4 حساسيّةُ أدنى أحمر", lambda: (first(measure_bids([mk([("purple", 2.0), ("red", 1.0), ("red", 3.0)])], s_rule="lowest")["rows"]).get("S") == 1.0, ""))
    e1 = lambda: measure_entries([mk([("red", 2.0)], entries=[2.1, 1.9])])                                # noqa: E731
    g("CG4 الدخولُ المكتوب نسبةً للأحمر الأقرب", lambda: (e1()["above"] == 1 and e1()["below"] == 1 and e1()["median_pct"] == 0.0, e1()))
    e2 = lambda: measure_entries([mk([("red", 1.0), ("red", 2.0)], entries=[2.1])])                       # noqa: E731
    g("CG4 الدخولُ للأحمر الأقرب لا الأدنى", lambda: (first(e2()["rows"]).get("S") == 2.0 and first(e2()["rows"]).get("pct") == 5.0, e2()))
    # CG5 ② ③
    w1 = lambda: measure_width([mk([("purple", 2.0), ("purple", 2.12)]), mk([("purple", 3.0)])])          # noqa: E731
    g("CG5 العرضُ (Pmax−Pmin)÷Pmin · وخطٌّ واحد لا يدخل الوسيط", lambda: (w1()["n"] == 1 and first(w1()["rows"]).get("width") == 6.0
      and w1()["le_6"] == 1 and w1()["single_line"] == 1, w1()))
    k1 = lambda: measure_count([mk([("purple", 2.0), ("purple", 9.0), ("black", 5.0)]), mk([("purple", 1.0)])])   # noqa: E731
    g("CG5 العدُّ لكلّ وحدة (والبنفسجيُّ فوق الأسود لا يُسقَط بعد التعديل ④)", lambda: (k1()["all_numbered"] == {1: 1, 2: 1}
      and k1()["non_conflict"] == {1: 1, 2: 1}, k1()))
    # CG6 ④
    d1 = lambda: first(measure_depth([mk([("red", 2.0), ("red", 3.0)], low=1.8)])["rows"])                 # noqa: E731
    g("CG6 R* أدنى أحمرَ فوق القاع", lambda: (d1().get("R") == 2.0 and d1().get("depth") == 10.0 and d1().get("bin") == "7-13", d1()))
    d2 = lambda: measure_depth([mk([("red", 2.0)], low=2.0)])                                             # noqa: E731
    g("CG6 القاعُ عند الأحمر أو فوقه ⟵ «لم ينزل تحت أيّ أحمر»", lambda: (d2()["n"] == 0 and d2()["not_below_any_red"] == 1, d2()))
    xs = (4.99, 5.0, 6.99, 7.0, 13.0, 13.01, 20.0, 50.0, 50.01)
    g("CG6 حدودُ الفئات (5 · 7 · 13 · 20 · 50)", lambda: ([_bin(x) for x in xs] == ["<5", "5-<7", "5-<7", "7-13", "7-13", ">13-20", ">13-20", ">20-50", ">50"],
                                                   [_bin(x) for x in xs]))

    def ax():
        u = mk([("red", 2.0)], low=1.8)
        u["low_src"] = "axis"
        return u
    g("CG6 الحاكمُ low_src=label · والمحورُ حساسيّة", lambda: (measure_depth([ax()])["n"] == 0 and measure_depth([ax()], srcs=("label", "axis"))["n"] == 1, ""))
    # CG7 ⑤
    cats = lambda: [first(measure_stop([mk([("red", 2.0)], low=1.5, stop=s)])["rows"]).get("cat")    # noqa: E731
                    for s in (1.4, 1.5, 1.522, 1.8, 2.0, 2.5)]
    g("CG7 فئاتُ الوقف بنطاق ±1%", lambda: (cats() == ["below_low", "at_low", "between_low_support", "between_low_support", "at_support", "above_support"], cats()))
    # CG8 ⑥
    bl = lambda: measure_blue([mk([("blue", 5.0), ("black", 4.0)]), mk([("blue", 3.0), ("black", 4.0)]),       # noqa: E731
                               mk([("blue", 5.0), ("blue", 3.5), ("black", 4.0)]), mk([("blue", 5.0), ("black", 4.0), ("black", 6.0)])])
    g("CG8 الأزرقُ فوق كلّ أسود · تحت كلّه · متداخل", lambda: (bl()["classes"] == {"all_above": 1, "all_below": 1, "mixed": 2}, bl()["classes"]))
    # CG9 validation
    bad1 = {"Z": {"id": "Z", "rev": 1, "charts": [{"author": "FAISAL", "levels": [["red", 1.0, "x (على الشارت)", "H"]]}]}}
    g("CG9 الوسمُ غيرُ القانونيّ يُرفض", lambda: (any("non-canonical" in p for p in validate(bad1, ["Z"])), validate(bad1, ["Z"])))
    bad2 = {"Z": {"id": "Z", "rev": 1, "charts": [{"author": "FAISAL", "entries_text": "1.8", "levels": [["red", 1.0, "", "H"]]}]}}
    g("CG9 `entries_text` نصٌّ يُرفض (قائمةُ أرقام)", lambda: (any("entries_text" in p for p in validate(bad2, ["Z"])), validate(bad2, ["Z"])))
    g("CG9 صورةٌ بلا سجلّ تُرفض", lambda: (any("register ids" in p for p in validate({}, ["Z"])), ""))
    # CG10 fold
    q = {"unit": "Q#0", "members": ["Q#0"], "levels": [{"colour": "other", "value": 2.0, "label": "", "conf": "H"},
                                                        {"colour": "other", "value": 3.0, "label": "", "conf": "H"}]}
    g("CG10 طيُّ الدرجات من الملفّ وحدَه", lambda: ([x["colour"] for x in recolour([q], {("Q", 2.0): "red", ("Q", 3.0): "other"})[0]["levels"]] == ["red", "other"], ""))
    # CG12 position to the price (amendment ④-③)
    sides = lambda: [side_of(v, 1.0)[1] for v in (1.0101, 1.01, 1.0, 0.99, 0.9899)] + [side_of(2.0, None)[1]]   # noqa: E731
    g("CG12 «عند» ±1% · فوقه وتحته · وبلا سعرٍ لا موضع", lambda: (sides() == ["above", "at", "at", "at", "below", None], sides()))
    u12 = {"levels": [{"colour": "red", "value": 2.0, "label": "", "conf": "H"}], "price_last": 1.8, "price_now": 2.2}
    g("CG12 price_last يحكم و price_now حساسيّة", lambda: (assign_roles(u12)[0]["side"] == "above"
      and assign_roles(u12, price_key="price_now")[0]["side"] == "below", ""))
    P1 = ch("P#0", "Q", [("red", 1.0), ("black", 2.0)], plast=1.5)
    P2 = ch("P2#0", "Q", [("red", 1.0), ("black", 2.0), ("blue", 3.0)])
    g("CG12 سعرُ الوحدة من المختار وإلّا من عضوٍ له سعر (يُعَدّ)", lambda: ((lambda u: u["price_last"] == 1.5 and u["price_last_src"] == "ext"
      and "price_last" in u["filled_from_member"])(build_units([P1, P2])[0]), build_units([P1, P2])[0]["price_last"]))
    # CG13 derived role
    g("CG13 أغلبُ المستويات والوحدات تحت ⟵ تحت · مرجّحٌ دون ويلسون", lambda: (derived_role(["below"] * 7 + ["above"] * 3, ["below"] * 4 + ["above"])
      == (BELOW, "likely"), derived_role(["below"] * 7 + ["above"] * 3, ["below"] * 4 + ["above"])))
    g("CG13 حاسمٌ حين يتجاوز حدُّ ويلسون الأدنى النصفَ في القراءتين", lambda: (derived_role(["above"] * 28 + ["below"] * 2, ["above"] * 10)
      == (ABOVE, "decisive") and derived_role(["above"] * 28 + ["below"] * 2, ["above"] * 4 + ["below"]) == (ABOVE, "likely"),
      derived_role(["above"] * 28 + ["below"] * 2, ["above"] * 4 + ["below"])))
    g("CG13 المستوياتُ تحت والوحداتُ فوق ⟵ غيرُ محسوم", lambda: (derived_role(["below"] * 8 + ["above"] * 2, ["above"] * 3 + ["below"] * 2)
      == ("undecided", None), ""))
    g("CG13 النصفُ بالضبط ليس أغلبيّة · و«عند» في المقام", lambda: (derived_role(["below"] * 5 + ["above"] * 5, ["below"] * 5) == ("undecided", None)
      and derived_role(["below"] * 5 + ["at"] * 5, ["below"] * 5) == ("undecided", None), ""))
    g("CG13 دون 10 مستوياتٍ أو 5 وحداتٍ لا قياس", lambda: (derived_role(["below"] * 9, ["below"] * 9)[0] == "no_measure"
      and derived_role(["below"] * 12, ["below"] * 4)[0] == "no_measure", ""))
    g("CG13 حدُّ ويلسون الأدنى", lambda: (abs(wilson_lo(7, 10) - 0.3968) < 1e-3 and abs(wilson_lo(28, 30) - 0.7868) < 1e-3, wilson_lo(7, 10)))

    def dmap():
        us = [mk([("purple", 0.95), ("purple", 0.96), ("purple", 1.3)], price=1.0, unit="a"),
              {**mk([("other", 2.0)], price=1.0, unit="b"), "members": ["X#0"]}]
        us[0]["members"] = ["Y#0"]
        return derived_map(us, {("X", 2.0): "بنفسجيٌّ معتم"})
    g("CG13 صوتُ الوحدة وسيطُ موضعها · وصفُّ الدرجة بجانب other", lambda: (dmap()["purple"]["units_below"] == 1 and dmap()["purple"]["pct_above"] == 33.33
      and "other:بنفسجيٌّ معتم" in dmap() and dmap()["other"]["levels"] == 1, sorted(dmap())))
    g("CG13 البوّابةُ تُفتح بالمجموعتين معًا", lambda: (purple_gate({"G1_FAISAL": {"purple": {"role": BELOW}}, "G2_FAISAL_UNSIGNED": {"purple": {"role": BELOW}}})
      and not purple_gate({"G1_FAISAL": {"purple": {"role": BELOW}}, "G2_FAISAL_UNSIGNED": {"purple": {"role": "undecided"}}})
      and measure_all([mk([("purple", 1.0), ("red", 0.9)])])["m1_bid_vs_support"] == GATE_OFF
      and isinstance(measure_all([mk([("purple", 1.0), ("red", 0.9)])], gate=True)["m1_bid_vs_support"], dict), ""))
    # CG14 purple vs blue/black · two supports · stop · entries
    pv = lambda: measure_purple_vs([mk([("purple", 3.0), ("blue", 2.6)]), mk([("purple", 3.0), ("blue", 3.5)]),        # noqa: E731
                                    mk([("purple", 3.0), ("purple", 4.0), ("blue", 3.5)])], "blue")["classes"]
    g("CG14 الأزرقُ تحت البنفسجيّ كلِّه · فوقه · متداخل", lambda: (pv() == {"blue_all_above_purple": 1, "blue_all_below_purple": 1, "mixed": 1}, pv()))
    t2 = lambda: first(measure_depth2([mk([("red", 1.74), ("red", 1.858), ("red", 3.0)], low=1.6)])["rows"])            # noqa: E731
    g("CG14 R1 أدنى أحمرَ فوق القاع وR2 التالي", lambda: (t2().get("R1") == 1.74 and t2().get("R2") == 1.858 and t2().get("d1") == 8.05
      and t2().get("d2") == 13.89 and t2().get("both_7_13") is False, t2()))
    vd = lambda: [measure_depth2([mk([("red", 1.1), ("red", 1.12)], low=1.0, unit=str(i)) for i in range(n)])["verdict"] for n in (9, 10)]   # noqa: E731
    vh = lambda: measure_depth2([mk([("red", 1.1), ("red", 1.12)], low=1.0, unit=f"a{i}") for i in range(5)]            # noqa: E731
                                + [mk([("red", 1.3), ("red", 1.4)], low=1.0, unit=f"b{i}") for i in range(5)])
    g("CG14 دون 10 وحداتٍ لا قياس · والنصفُ فأكثر يُدعم", lambda: (vd() == ["no_measure", "supported_descriptive"]
      and vh()["both_7_13"] == 5 and vh()["verdict"] == "supported_descriptive", (vd(), vh()["verdict"])))
    sp = lambda: [first(measure_stop([mk([("red", 1.0), ("red", 2.0)], stop=1.95)], s_rule=r)["rows"]).get("cat") for r in ("nearest", "lowest")]   # noqa: E731
    g("CG14 الوقف: الدعمُ الأحمرُ الأقربُ إليه · والحساسيّةُ أدناه", lambda: (sp() == ["below_support_no_low", "above_support"], sp()))
    en = lambda: measure_entries([mk([("red", 1.7)], price=1.8, entries=[1.70, 1.85])])                                  # noqa: E731
    g("CG14 الدخولُ المكتوب مقابل السعر وعرضُه مقابل 6%", lambda: (en()["vs_price"]["sides"] == {"above": 1, "at": 0, "below": 1}
      and en()["written_width"]["rows"][0]["width"] == 8.82 and en()["written_width"]["gt_6"] == 1
      and measure_entries([mk([("red", 1.0)], price=1.1, entries=[1.0, 1.06])])["written_width"]["le_6"] == 1, en()["written_width"]))
    # CG15 bid_entry review

    def review():
        last_ = {"I1": {"charts": [{"price_last": 2.0, "levels": [["purple", 2.5, "", "H"], ["purple", 1.5, "", "H"]]}]},
                 "I2": {"charts": [{"price_last": None, "levels": [["purple", 3.0, "", "H"]]}]},
                 "I3": {"charts": [{"price_last": 2.0, "levels": [["other", 1.8, "", "H"], ["black", 5.0, "", "H"]]}]},
                 "I4": {"charts": [{"price_last": 3.0, "levels": [["black", 2.0, "", "H"], ["purple", 2.015, "", "H"]]}]}}
        rows = [{"role": "bid_entry", "level": v, "images": i, "line": str(n), "symbol": "", "colour": "purple"}
                for n, (v, i) in enumerate(((2.5, "I1"), (1.5, "I1"), (3.0, "I2"), (9.0, "I1"), (1.0, "OFF"), (1.81, "I3"), (5.0, "I3"), (2.0, "I4"), (1.525, "I1")))]
        rows.append({"role": "support", "level": 1.0, "images": "I1", "line": "x", "symbol": "", "colour": "red"})
        return bid_entry_review(rows, last_, {"I1", "I2", "I3", "I4"}, {("I3", 1.8): "purple"})
    g("CG15 صفوفُ bid_entry: ينجو تحت السعر · يُعاد فوقه · بلا سعر · غائب · خارج القرص · والداكنُ من عائلة البنفسجيّ · والبنفسجيُّ قبل الأقرب",
      lambda: ([r["action"] for r in review()["rows"]] == ["RECLASSIFIED_ABOVE", "SURVIVES", "NO_PRICE", "NOT_FOUND", "UNVERIFIABLE", "SURVIVES",
                                                          "RECLASSIFIED_ABOVE", "SURVIVES", "NOT_FOUND"]
               and review()["n"] == 9 and review()["eye_not_purple_family"] == 1 and review()["rows"][5]["eye_purple_family"] is True
               and review()["rows"][7]["eye_colour"] == "purple" and review()["rows"][7]["eye_value"] == 2.015,
               [r["action"] for r in review()["rows"]]))
    # CG16 validation of price_last · ANPA
    pv1 = {"Z": {"id": "Z", "rev": 1, "charts": [{"author": "FAISAL", "levels": [["red", 1.0, "", "H"]]}]}}
    pv2 = {"Z": {"id": "Z", "rev": 1, "charts": [{"author": "FAISAL", "price_last": 1.0, "price_last_src": "axis", "levels": [["red", 1.0, "", "H"]]}]}}
    pv3 = {"Z": {"id": "Z", "rev": 1, "charts": [{"author": "FAISAL", "price_last": None, "levels": [["red", 1.0, "", "H"]]}]}}
    g("CG16 كلُّ شارتٍ قُرئ سعرُه (المفتاحُ حاضر) · والمصدرُ من الثلاثة · والمجهولُ null مقبول",
      lambda: (any("price_last not read" in p for p in validate(pv1, ["Z"])) and any("price_last 1.0" in p for p in validate(pv2, ["Z"]))
               and not validate(pv3, ["Z"]), (validate(pv1, ["Z"]), validate(pv2, ["Z"]), validate(pv3, ["Z"]))))

    def anpa_t():
        import tempfile
        d = {"id": "T", "posts": [], "not_levels": [], "notes": [],
             "charts": [{"name": "L", "kind": "candles", "frame": "D", "price_last": 2.0, "price_last_src": "ext", "price_now": 1.9,
                         "bid": None, "ask": None, "low": 1.5, "low_src": "label",
                         "levels": [["other", 3.0, "بنفسجيٌّ معتم", "purple"], ["red", 2.1, None, "red"], ["red", 1.95, None, "red"]]}]}
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(d, f)
        try:
            return anpa_case(f.name, {"G1_FAISAL": {"other:بنفسجيٌّ معتم": {"role": ABOVE}, "red": {"role": BELOW}}},
                             {"G1_FAISAL": {"purple": {"role": "undecided"}}})
        finally:
            os.remove(f.name)
    g("CG16 ANPA: الموضعُ إلى price_last والوسم · ودورُ الدرجة والطيّ", lambda: ((lambda a: [r["side_last"] for r in a["rows"]] == ["above", "above", "below"] and a["rows"][2]["side_now"] == "above"
      and a["rows"][1]["side_now"] == "above" and a["rows"][0]["derived"]["G1_FAISAL"] == ABOVE and a["rows"][0]["derived_fold"]["G1_FAISAL"] == "undecided"
      and a["rows"][1]["derived_fold"]["G1_FAISAL"] == "no_measure")(anpa_t()), anpa_t()["rows"]))
    # CG17 purple-heads sample and verdict (amendment ④-⑪)
    def hs_units():
        us = []
        for n_, auth in enumerate(["FAISAL", "UNSIGNED", "THIRD_PARTY", "FAISAL", "UNSIGNED"] * 12):
            lv = [{"colour": "purple", "value": 2.0 + n_ / 100}, {"colour": "purple", "value": 3.0 + n_ / 100}] if n_ % 7 else [{"colour": "red", "value": 1.0}]
            us.append({"unit": f"U{n_:03d}", "author": auth, "symbol": None, "levels": lv})
        return us
    g("CG17 العيّنةُ ثابتةٌ بالبذرة · من المجموعة الثانية ومن عائلة البنفسجيّ · مستوًى واحدٌ لكلّ وحدة",
      lambda: ((lambda a, b: a == b and len(a) == 40 and len({x["unit"] for x in a}) == 40
                and all(x["author"] in ("FAISAL", "UNSIGNED") for x in a)
                and all(int(x["unit"][1:]) % 7 for x in a)
                and head_sample(hs_units(), seed=1) != a)(head_sample(hs_units()), head_sample(list(reversed(hs_units())))),
               head_sample(hs_units())[:3]))
    smp = [{"unit": f"U{i}", "value": 1.0, "symbol": None, "author": "FAISAL"} for i in range(12)]
    hd = lambda cls: {(f"U{i}", 1.0): {"class": c, "rev": 1} for i, c in enumerate(cls)}                                   # noqa: E731
    g("CG17 الحكم: النصفُ فأكثر يُدعم · «غيرُ مقروء» خارج المقام · دون 10 لا قياس · والناقصُ incomplete",
      lambda: (measure_heads(smp, hd(["RED_BODY_TOP"] * 5 + ["GREEN"] * 5 + ["UNREADABLE"] * 2))["verdict"] == "supported_descriptive"
               and measure_heads(smp, hd(["RED_BODY_TOP"] * 4 + ["GREEN"] * 6 + ["UNREADABLE"] * 2))["verdict"] == "dropped_descriptive"
               and measure_heads(smp, hd(["RED_BODY_TOP"] * 4 + ["RED_WICK_TOP"] * 2 + ["GREEN"] * 4 + ["UNREADABLE"] * 2))["sensitivity_top_or_wick"] == "supported_descriptive"
               and measure_heads(smp, hd(["RED_BODY_TOP"] * 9 + ["UNREADABLE"] * 3))["verdict"] == "no_measure"
               and measure_heads(smp, hd(["RED_BODY_TOP"] * 11))["verdict"] == "incomplete", ""))

    def lh(lines):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
            f.write("\n".join(json.dumps(x, ensure_ascii=False) for x in lines) + "\n")
        try:
            return load_heads(f.name)
        finally:
            os.remove(f.name)
    G_, N_ = ["GREEN"], ["NO_CANDLE"]
    HS_PIN = [("U019", 3.0 + 19 / 100), ("U018", 2.0 + 18 / 100), ("U041", 2.0 + 41 / 100)]   # the fixture's first three picks at seed 20261015
    g("CG17 سجلُّ الرؤوس: فئةٌ من الستّ · rev صاعدةٌ بسبب",
      lambda: (not lh([{"unit": "A", "value": 1.0, "rev": 1, "class": "GREEN", "contacts": G_},
                       {"unit": "A", "value": 1.0, "rev": 2, "class": "NO_CANDLE", "contacts": N_, "why": "x"}])[1]
               and lh([{"unit": "A", "value": 1.0, "rev": 1, "class": "PURPLE", "contacts": G_}])[1]
               and lh([{"unit": "A", "value": 1.0, "rev": 1, "class": "GREEN", "contacts": G_}, {"unit": "A", "value": 1.0, "rev": 2, "class": "GREEN", "contacts": G_}])[1]
               and lh([{"unit": "A", "value": 1.0, "rev": 2, "class": "GREEN", "contacts": G_, "why": "x"}])[1], ""))
    one = lambda cls, con: lh([{"unit": "A", "value": 1.0, "rev": 1, "class": cls, "contacts": con}])[1]                      # noqa: E731
    g("CG18 الفئةُ أعلى التماسّات بالأسبقيّة (جسمٌ ⟵ رأسُ ذيل ⟵ جزءٌ آخر ⟵ خضراء ⟵ لا شمعة) · وغيرُ المقروء بلا تماسّ",
      lambda: (not one("RED_BODY_TOP", ["GREEN", "RED_WICK_TOP", "RED_BODY_TOP"]) and not one("RED_WICK_TOP", ["RED_BODY_OTHER", "RED_WICK_TOP"])
               and not one("RED_BODY_OTHER", ["GREEN", "RED_BODY_OTHER"]) and not one("UNREADABLE", [])
               and one("RED_WICK_TOP", ["RED_WICK_TOP", "RED_BODY_TOP"]) and one("RED_BODY_OTHER", ["RED_WICK_TOP", "RED_BODY_OTHER"])
               and one("GREEN", ["GREEN", "RED_BODY_OTHER"]) and one("UNREADABLE", ["GREEN"]) and one("GREEN", [])
               and one("GREEN", ["GREEN", "PURPLE"]) and one("GREEN", "GREEN"), ""))

    def fr():
        hs = lh([{"unit": "A", "value": 1.0, "rev": 1, "class": "RED_WICK_TOP", "contacts": ["RED_WICK_TOP"]},
                 {"unit": "A", "value": 1.0, "rev": 2, "class": "RED_BODY_TOP", "contacts": ["RED_BODY_TOP"], "why": "x"},
                 {"unit": "B", "value": 2.0, "rev": 1, "class": "GREEN", "contacts": ["GREEN"]},
                 {"unit": "C", "value": 3.0, "rev": 1, "class": "NO_CANDLE", "contacts": ["NO_CANDLE"]}])[0]
        return hs, measure_heads([{"unit": u, "value": v, "symbol": None, "author": "FAISAL"} for u, v in (("A", 1.0), ("B", 2.0), ("C", 3.0))], hs)
    g("CG18 القراءةُ الأولى من rev 1 لا من الأخيرة · وعددُ المراجَع · والحكمُ من الأخيرة",
      lambda: ((lambda hs, m: hs[("A", 1.0)]["first_class"] == "RED_WICK_TOP" and m["revised"] == 1
               and m["classes"]["RED_BODY_TOP"] == 1 and m["first_reading"]["classes"]["RED_BODY_TOP"] == 0
               and m["first_reading"]["classes"]["RED_WICK_TOP"] == 1 and m["first_reading"]["readable"] == 3)(*fr()), fr()[1]["first_reading"]))
    g("CG18 ثوابتُ العيّنة كما في البروتوكول (‏20261015 · 40 · 10) · والعيّنةُ على الملحق مثبَّتةٌ برؤوسها الثلاثة",
      lambda: ((HEAD_SEED, HEAD_N, HEAD_MIN) == (20261015, 40, 10)
               and [(x["unit"], x["value"]) for x in head_sample(hs_units())[:3]] == HS_PIN, head_sample(hs_units())[:3]))
    def phu():
        lv = lambda c, v, lab, side, rel: {"colour": c, "value": v, "label": lab, "side": side, "rel": rel}          # noqa: E731
        return posthoc_labelled_purple([
            {"unit": "A#0", "symbol": "AAA", "roles": [lv("purple", 2.7, "مناطق طلب 2.70", "below", -5.0),
                                                      lv("purple", 4.0, "", "above", 40.0),
                                                      lv("purple", 5.0, "ابيض", "above", 75.0),
                                                      lv("red", 2.5, "مناطق طلب", "below", -12.0)]},
            {"unit": "B#0", "symbol": "BBB", "roles": [lv("purple", 9.0, "دعم 9", "above", 30.0),
                                                      lv("purple", 7.0, "هدف 7", None, None)]}])
    g("CG19 قراءةُ ما بعد الرقم: البنفسجيُّ ذو الملصق وحدَه بدوره وموضعه · والصفوفُ للطلب والدعم وحدَهما بأسمائها",
      lambda: ((lambda p: p["by_role"] == {"bid": {"below": 1}, "neutral": {"above": 1}, "support": {"above": 1}, "target": {"no_price": 1}}
               and [(r["unit"], r["value"], r["side"]) for r in p["rows"]] == [("A#0", 2.7, "below"), ("B#0", 9.0, "above")])(phu()), phu()))
    def closed_with(v):
        old = os.environ.get(REOPEN_ENV)
        try:
            if v is None:
                os.environ.pop(REOPEN_ENV, None)
            else:
                os.environ[REOPEN_ENV] = v
            return _closed_now()
        finally:
            if old is None:
                os.environ.pop(REOPEN_ENV, None)
            else:
                os.environ[REOPEN_ENV] = old
    g("CG20 الإغلاقُ يُقرأ وقتَ النداء: غائبٌ · «0» · «true» · «yes» ⟵ مُغلَق · و«1» وحدَه (بمسافاته) ⟵ مفتوح · والرمزُ 8",
      lambda: (AXIS_CLOSED is True and REOPEN_ENV == "COLOUR_REOPEN" and CLOSED_RC == 8
               and all(closed_with(v) for v in (None, "", "0", "true", "yes", "11"))
               and not closed_with("1") and not closed_with(" 1 "), [closed_with(v) for v in (None, "0", "1")]))
    # CG11 pins

    def pins():
        import contextlib
        import io
        codes = []
        with open(PROTO, "rb") as f:
            good = f.read()
        for rd in (lambda: good, lambda: None, lambda: good + b" "):
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    check_pins(read=rd)
                codes.append(0)
            except SystemExit as ex:
                codes.append(ex.code)
        return codes == [0, 9, 9], codes
    g("CG11 البروتوكولُ على main ببصمته ⟵ يمضي · غائبٌ أو مختلف ⟵ 9", pins)
    print(("✅ الحرّاس كلُّهم" if all(ok) else "❌ سقط حارس") + f" ({sum(ok)}/{len(ok)})")
    return 0 if all(ok) else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--guards", action="store_true")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--heads-sample", action="store_true")
    a = ap.parse_args(argv)
    if a.guards:
        return guards()
    if a.validate:
        check_pins(need_main=False)
        last, _, probs = load_register()
        probs += validate(last, image_ids())
        probs += load_heads()[1]
        for p in probs[:30]:
            print("⛔", p)
        print("✅ السجلُّ سليم" if not probs else f"⛔ {len(probs)} مشكلة")
        return 0 if not probs else 9
    if a.heads_sample:
        if _closed_now():
            for ln in closure_notice():
                print(ln)
            return CLOSED_RC
        check_pins(need_main=False)
        last, order, _ = load_register()
        with open(FAMILY, encoding="utf-8") as f:
            fm = fold_map(json.load(f))
        for x in head_sample(recolour(build_units(charts_of(last, order)), fm)):
            print(json.dumps(x, ensure_ascii=False))
        return 0
    if a.check:
        check_pins(need_main=False)
        outs = outputs()
        bad = [os.path.relpath(p, ROOT) for p, s in outs.items() if not os.path.exists(p) or open(p, encoding="utf-8").read() != s]
        print("✅ المخرَجاتُ تُعاد بايتًا" if not bad else f"❌ تختلف: {bad}")
        return 0 if not bad else 1
    if _closed_now():
        for ln in closure_notice():
            print(ln)
        return CLOSED_RC
    check_pins()
    for p, s in outputs().items():
        with open(p, "w", encoding="utf-8") as f:
            f.write(s)
        print("✍️", os.path.relpath(p, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
