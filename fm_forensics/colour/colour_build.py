"""T-COLOUR builder — deterministic, no network, no candles, no dates.

Reads the eye register (data/colour_records.jsonl) and writes COLOUR_LEVELS.tsv, data/colour_result.json and
T_COLOUR_TABLES.md under the rules of T_COLOUR_protocol.md (pinned by its sha256).

  python3 fm_forensics/colour/colour_build.py            build (exit 9 unless the pinned protocol is on origin/main)
  python3 fm_forensics/colour/colour_build.py --check    rebuild in memory and compare the three outputs byte for byte
  python3 fm_forensics/colour/colour_build.py --guards   synthetic guards
  python3 fm_forensics/colour/colour_build.py --validate pins (local) and register checks only — no measure is computed

Exit codes: 0 done · 1 guards failed or outputs differ · 9 protocol/records pin or register invalid.
"""
import argparse
import collections
import hashlib
import json
import os
import re
import statistics
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PROTO = os.path.join(HERE, "T_COLOUR_protocol.md")
PROTO_SHA256 = "a096109cf86cc9346f3a6f2ec3fb8c49e1ae84602e64980651b3d82c339e8aaa"
DATA = os.path.join(HERE, "data")
REC = os.path.join(DATA, "colour_records.jsonl")
REC_SHA256 = "a9dbce6e98e5e805946bf43e0268135eff9ec0e0857f4f1bb49748a057f8b27e"
FAMILY = os.path.join(DATA, "other_family.json")
KEYTEXT = os.path.join(DATA, "colour_key_text.jsonl")
CORR = os.path.join(DATA, "table_corrections.jsonl")
TABLE = os.path.join(ROOT, "faisal_levels_table.tsv")
IMAGES = os.path.join(ROOT, "faisal_images")
OUT_TSV = os.path.join(HERE, "COLOUR_LEVELS.tsv")
OUT_JSON = os.path.join(DATA, "colour_result.json")
OUT_MD = os.path.join(HERE, "T_COLOUR_TABLES.md")

COLOURS = ("red", "black", "purple", "blue", "orange", "green", "yellow", "grey", "pink", "white", "other")
AUTHORS = ("FAISAL", "UNSIGNED", "FOLLOWER", "THIRD_PARTY", "OWNER", "APP")
NONE_REASONS = ("NOT_CHART", "NO_LINES", "NO_NUMBERS", "LOW_RES", "CROPPED")
TAGS = ("نصّ المنشور", "نصّ الرسالة", "نصّ على الشارت")
KEY_ROLE = {"red": "support", "black": "resistance", "blue": "target_clean", "purple": "bid_entry"}
ZONE_PCT = 6.0      # our ladder: ENTRY_TRANCHES=3 at ENTRY_STEP_PCT=3 -> 0/+3/+6
NEAR_PCT = 1.0      # stop "at" low/support band (protocol §⑤)
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
    if colour == "purple":
        return cls == "bid"
    return True     # unmapped colours never conflict through a label


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
        for f in ("stop", "stop_src", "bids_text", "entries_text"):
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


def assign_roles(u, above_all=False):
    """Role per level: key role, or 'conflict' with reasons (label · inversion). Inversion is judged inside the chart:
    red above black -> both · blue below red -> both · purple above black -> purple only. above_all = the sensitivity
    that needs the level above (or below) ALL lines of the other colour."""
    lv = u["levels"]
    val = {c: [x["value"] for x in lv if x["colour"] == c] for c in ("red", "black", "blue", "purple")}

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
        if c == "purple" and above(v, val["black"]):
            why.append("purple>black")
        role = "conflict" if why else KEY_ROLE.get(c, "unmapped")
        pos = []
        p = u.get("price_now")
        if p:
            if c == "red" and v > p:
                pos.append("red_above_price")
            if c == "black" and v < p:
                pos.append("black_below_price")
            if c == "blue" and v < p:
                pos.append("blue_below_price")
            if c == "purple" and v > p:
                pos.append("purple_above_price")
        out.append({**x, "role": role, "why": why, "pos": pos})
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
             and not (drop_above_price and "purple_above_price" in x["pos"])]
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
    rows = []
    for u in units:
        E = u.get("entries_text") or []
        R = [x["value"] for x in u["roles"] if x["colour"] == "red" and x["role"] != "conflict"]
        if not E or not R:
            continue
        for e in E:
            S = nearest_red(R, e, e)
            rows.append({"unit": u["unit"], "symbol": u["symbol"], "entry": e, "S": S, "pct": _r((e - S) / S * 100)})
    return {"n": len(rows), "units": len({r["unit"] for r in rows}), "above": sum(r["pct"] > 0 for r in rows),
            "at": sum(r["pct"] == 0 for r in rows), "below": sum(r["pct"] < 0 for r in rows),
            "median_pct": _r(statistics.median([r["pct"] for r in rows])) if rows else None, "rows": rows}


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


def measure_stop(units, bids):
    S_of = {r["unit"]: r["S"] for r in bids["rows"]}
    rows = []
    for u in units:
        st = u.get("stop")
        if st is None:
            continue
        R = [x["value"] for x in u["roles"] if x["colour"] == "red" and x["role"] != "conflict"]
        sup = S_of.get(u["unit"], min(R) if R else None)
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


def measure_all(units):
    bids = measure_bids(units)
    return {"units": len(units), "symbols": len({u["symbol"] for u in units if u["symbol"]}),
            "m1_bid_vs_support": bids, "m1_entries_text": measure_entries(units),
            "m2_zone_width": measure_width(units), "m3_bid_count": measure_count(units),
            "m4_depth": measure_depth(units), "m5_stop": measure_stop(units, bids), "m6_blue_vs_black": measure_blue(units),
            "key_table": key_table(units), "conflicts": conflicts(units)}


def headline(m):
    b = m["m1_bid_vs_support"]["classes"]
    m1 = max(("above", "surrounds", "below"), key=lambda c: (b[c]["n"], c)) if any(b[c]["n"] for c in b) else None
    w = m["m2_zone_width"]["stats"]
    m2 = None if not w else ("le_6" if w["median"] <= ZONE_PCT else "gt_6")
    d = m["m4_depth"]["stats"]
    m4 = None if not d else _bin(d["median"])
    c = m["m5_stop"]["cats"]
    m5 = max(sorted(c), key=lambda k: c[k]) if c else None
    k = m["m6_blue_vs_black"]["classes"]
    m6 = max(sorted(k), key=lambda x: k[x]) if k else None
    return {"m1_majority": m1, "m2_median_vs_6": m2, "m4_median_bin": m4, "m5_modal": m5, "m6_majority": m6}


def sensitivities(units_primary, units_fold, units_aall):
    g2 = {"FAISAL", "UNSIGNED"}

    def sel(us):
        return [u for u in us if u["author"] in g2]
    base = measure_all(sel(units_primary))
    out = {"governing": headline(base)}
    out["fold_dark_shades"] = headline(measure_all(sel(units_fold)))
    out["inversion_above_all"] = headline(measure_all(sel(units_aall)))
    p = sel(units_primary)
    for name, kw in (("S_lowest_red", {"s_rule": "lowest"}), ("S_highest_red", {"s_rule": "highest"}),
                     ("conflicts_kept", {"keep_conflict": True}), ("purple_above_price_out", {"drop_above_price": True})):
        b = measure_bids(p, **kw)
        out[name] = {"m1": {c: b["classes"][c]["n"] for c in b["classes"]}, "n": b["n"]}
    out["depth_with_axis"] = {k: v for k, v in measure_depth(p, srcs=("label", "axis")).items() if k in ("n", "stats", "bins")}
    out["width_conflicts_kept"] = {k: v for k, v in measure_width(p, keep_conflict=True).items() if k in ("n", "stats", "le_6", "gt_6")}
    changed = [k for k in ("fold_dark_shades", "inversion_above_all") if out[k] != out["governing"]]
    out["changed_headlines"] = {k: {h: (out["governing"][h], out[k][h]) for h in out["governing"] if out[k][h] != out["governing"][h]}
                                for k in changed}
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


def catalog_section(last, disk, corr):
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
    b = measure_bids(cu)
    w = measure_width(cu)
    actions = collections.Counter(c["action"] for c in corr)
    return {"table_rows": len(rows), "rows_on_disk": len(on), "rows_catalog_only": len(off),
            "images_in_table": len({i for r, _ in on + off for i in resolve_images(r["images"], disk)[1]}),
            "on_disk_vs_eye": dict(match),
            "catalog_only_groups": len(cu), "catalog_only_m1": {c: b["classes"][c] for c in b["classes"]}, "catalog_only_m1_n": b["n"],
            "catalog_only_m2": {k: v for k, v in w.items() if k in ("n", "single_line", "stats", "le_6", "gt_6")},
            "phase_a": {"rows": len(corr), "actions": dict(sorted(actions.items())),
                        "purple_rows": sum(1 for c in corr if c["colour"] == "purple"),
                        "groups": len({c["line"] for c in corr})}}


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
            "revisions": sum(1 for r in last.values() if r["rev"] > 1)}


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
        fmap = fold_map(json.load(f))
    for u in units:
        u["roles"] = assign_roles(u)
    folded = recolour(units, fmap)
    for u in folded:
        u["roles"] = assign_roles(u)
    aall = [{**u, "roles": assign_roles(u, above_all=True)} for u in units]
    with open(KEYTEXT, encoding="utf-8") as f:
        key_text = [json.loads(ln) for ln in f if ln.strip()]
    with open(CORR, encoding="utf-8") as f:
        corr = [json.loads(ln) for ln in f if ln.strip()]
    res = {"coverage": coverage(last, charts, units, ids), "groups": {}}
    for name, auths in GROUPS:
        sel = [u for u in units if u["author"] in auths]
        res["groups"][name] = measure_all(sel) if sel else {"units": 0}
    res["sensitivity_G2"] = sensitivities(units, folded, aall)
    res["fold_changed_levels"] = sum(1 for a, b in zip(units, folded) for x, y in zip(a["levels"], b["levels"]) if x["colour"] != y["colour"])
    res["camera_corrections"] = sorted(r["id"] for r in last.values() if r["rev"] > 1 and "X_20260918_27_CUPR" in (r.get("why") or ""))
    res["filled_from_member"] = sum(1 for u in units if u["filled_from_member"])
    res["key_text"] = {a: [k for k in key_text if k["author"] == a and not k["same_as"]] for a in AUTHORS if any(k["author"] == a for k in key_text)}
    res["catalog"] = catalog_section(last, set(ids), corr)
    res["null_symbol_twins"] = sum(1 for u in units if not u["symbol"] and any(v is not u and not v["symbol"] and
                                   {(x["colour"], x["value"]) for x in v["levels"]} == {(x["colour"], x["value"]) for x in u["levels"]} for v in units))
    return units, folded, res


def render_tsv(units, folded):
    cols = ("unit", "members", "author", "symbol", "frame", "colour", "colour_folded", "value", "label", "conf", "role", "why",
            "pos", "price_now", "low", "low_src")
    lines = ["\t".join(cols)]
    for u, f in zip(units, folded):
        for x, y in zip(u["roles"], f["roles"]):
            row = (u["unit"], " ".join(u["members"]), u["author"], u["symbol"] or "", u["frame"] or "", x["colour"], y["colour"],
                   repr(x["value"]), x["label"].replace("\t", " "), x["conf"], x["role"], ",".join(x["why"]), ",".join(x["pos"]),
                   "" if u["price_now"] is None else repr(u["price_now"]), "" if u["low"] is None else repr(u["low"]), u["low_src"] or "")
            lines.append("\t".join(str(c) for c in row))
    return "\n".join(lines) + "\n"


def _fmt(v):
    return "—" if v is None else (f"{v:g}" if isinstance(v, (int, float)) else str(v))


def render_md(res):
    c = res["coverage"]
    L = ["# `T-COLOUR` — الجداول (مولَّدةٌ من `data/colour_result.json` بـ`colour_build.py` · لا تُحرَّر باليد)", ""]
    L += ["## التغطية", "", "| البند | العدد |", "|---|---|"]
    for k in ("files_in_folder", "images", "images_with_numbered_levels", "pct_of_images", "pct_of_files", "duplicates", "triage_thumb",
              "charts", "units", "merged_away", "units_without_symbol", "symbols", "unit_levels", "unnumbered_lines", "revisions"):
        L.append(f"| `{k}` | {_fmt(c[k])} |")
    L.append(f"| `none` | {' · '.join(f'{k} {v}' for k, v in c['none'].items())} |")
    L.append(f"| `units_by_author` | {' · '.join(f'{k} {v}' for k, v in c['units_by_author'].items())} |")
    L.append(f"| `unit_levels_by_colour` | {' · '.join(f'{k} {v}' for k, v in c['unit_levels_by_colour'].items())} |")
    L.append(f"| `conf_share` % | {' · '.join(f'{k} {v}' for k, v in c['conf_share'].items())} |")
    L.append("")
    for g, m in res["groups"].items():
        if not m.get("units"):
            L += [f"## {g}: لا وحدات", ""]
            continue
        L += [f"## {g} — {m['units']} وحدة · {m['symbols']} رمزًا", ""]
        b = m["m1_bid_vs_support"]
        L += [f"**① الطلبُ مقابل الدعم** — {b['n']} وحدة · {b['symbols']} رمزًا", "", "| الفئة | العدد | وسيط lo % | وسيط hi % |", "|---|---|---|---|"]
        for cls in ("above", "surrounds", "below"):
            x = b["classes"][cls]
            L.append(f"| {cls} | {x['n']} | {_fmt(x['median_lo'])} | {_fmt(x['median_hi'])} |")
        L += ["", "| الوحدة | الرمز | S | Pmin | Pmax | lo % | hi % | الفئة |", "|---|---|---|---|---|---|---|---|"]
        for r in b["rows"]:
            L.append(f"| `{r['unit']}` | {_fmt(r['symbol'])} | {r['S']:g} | {r['Pmin']:g} | {r['Pmax']:g} | {r['lo']} | {r['hi']} | {r['class']} |")
        e = m["m1_entries_text"]
        L += ["", f"**① وصفٌ موازٍ — الدخولُ المكتوب نصًّا:** {e['n']} سعرًا في {e['units']} وحدة · فوق الأحمر {e['above']} · عنده {e['at']} · تحته {e['below']} · الوسيط {_fmt(e['median_pct'])}%", ""]
        w = m["m2_zone_width"]
        s = w["stats"] or {}
        L += [f"**② عرضُ منطقة الطلب** — {w['n']} وحدة ببنفسجيّين فأكثر · وخطٌّ واحد {w['single_line']} · "
              f"الوسيط {_fmt(s.get('median'))}% · الربيعيّان {_fmt(s.get('q1'))}/{_fmt(s.get('q3'))} · المدى {_fmt(s.get('min'))}-{_fmt(s.get('max'))} · "
              f"6% أو أقلّ {w['le_6']} · فوق 6% {w['gt_6']}", ""]
        k = m["m3_bid_count"]
        L += [f"**③ عددُ البنفسجيّات المرقَّمة لكلّ وحدة** — كلُّها: {k['all_numbered']} · غيرُ المتعارضة: {k['non_conflict']} · `bids_text` {len(k['bids_text'])}", ""]
        d = m["m4_depth"]
        s = d["stats"] or {}
        L += [f"**④ العمقُ تحت الأحمر** (`low_src=label`) — {d['n']} وحدة · لم ينزل تحت أيّ أحمر {d['not_below_any_red']} · "
              f"الوسيط {_fmt(s.get('median'))}% · الربيعيّان {_fmt(s.get('q1'))}/{_fmt(s.get('q3'))} · المدى {_fmt(s.get('min'))}-{_fmt(s.get('max'))}",
              "", "| الفئة | " + " | ".join(d["bins"]) + " |", "|---|" + "---|" * len(d["bins"]),
              "| العدد | " + " | ".join(str(v) for v in d["bins"].values()) + " |", "",
              "التوزيعُ كما يخرج: " + " · ".join(f"{r['depth']}" for r in d["rows"]), ""]
        st = m["m5_stop"]
        L += [f"**⑤ الوقف** — {st['n']} وحدة · {' · '.join(f'{k2} {v}' for k2, v in sorted(st['cats'].items()))} · عند القاع والدعم معًا {st['at_both']}", ""]
        for r in st["rows"]:
            L.append(f"- `{r['unit']}` {_fmt(r['symbol'])}: الوقف {r['stop']:g} ({r['src']}) · القاع {_fmt(r['low'])} ({_fmt(r['vs_low_pct'])}%) · الدعم {_fmt(r['support'])} ({_fmt(r['vs_support_pct'])}%) ⟵ {r['cat']}")
        bb = m["m6_blue_vs_black"]
        L += ["", f"**⑥ الأزرقُ مقابل الأسود** — {bb['n']} وحدة · {' · '.join(f'{k2} {v}' for k2, v in sorted(bb['classes'].items()))}", ""]
        for r in bb["not_all_above"]:
            L.append(f"- `{r['unit']}` {_fmt(r['symbol'])}: أزرق {r['blue']} · أسود {r['black']} ⟵ {r['class']}")
        L += ["", "**جدولُ المفتاح** (خطوطٌ ذاتُ ملصق):", "", "| اللون | " + " | ".join(("labelled", "support", "resistance", "target", "bid", "gap", "drop", "neutral", "compatible", "incompatible")) + " |",
              "|---|" + "---|" * 10]
        for col, v in m["key_table"].items():
            L.append(f"| {col} | " + " | ".join(str(v.get(x, 0)) for x in ("labelled", "support", "resistance", "target", "bid", "gap", "drop", "neutral", "compatible", "incompatible")) + " |")
        L += ["", f"**التعارضات بأسمائها ({len(m['conflicts'])}):**", ""]
        for x in m["conflicts"]:
            L.append(f"- `{x['unit']}` {_fmt(x['symbol'])} · {x['colour']} {x['value']:g} · {','.join(x['why'])}" + (f" · «{x['label']}»" if x["label"] else ""))
        L.append("")
    s = res["sensitivity_G2"]
    L += ["## الحساسيّة (المجموعة الثانية FAISAL ∪ UNSIGNED)", "", "```json", json.dumps(s, ensure_ascii=False, indent=1, sort_keys=True), "```", ""]
    L += ["## الكاتالوج القائم ومرحلة أ", "", "```json", json.dumps(res["catalog"], ensure_ascii=False, indent=1, sort_keys=True), "```", ""]
    L += ["## مفتاحُ الألوان بلفظ المصادر (بلا المكرّر)", ""]
    for a, ks in res["key_text"].items():
        for k in ks:
            L.append(f"- {a} · `{k['id']}` · {k['colour']} ⟵ {k['role']} · «{k['phrase']}»")
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
             "low": kw.get("low"), "low_src": kw.get("low_src", "label" if kw.get("low") else None), "stop": kw.get("stop"),
             "stop_src": "text" if kw.get("stop") else None, "bids_text": None, "entries_text": kw.get("entries"),
             "levels": [[c_, v, kw.get("labels", {}).get(v, ""), "H"] for c_, v in levels]}
        c["set"] = frozenset((a, b) for a, b in levels)
        return c

    def roles(levels, price=None, above_all=False):
        u = {"levels": [{"colour": c, "value": v, "label": lab, "conf": "H"} for c, v, lab in levels], "price_now": price}
        return {(x["colour"], x["value"]): (x["role"], x["why"], x["pos"]) for x in assign_roles(u, above_all)}

    def mk(levels, **kw):
        u = {"unit": "u", "symbol": "S", "price_now": kw.get("price"), "low": kw.get("low"), "low_src": "label",
             "stop": kw.get("stop"), "stop_src": "text", "entries_text": kw.get("entries"), "bids_text": None, "author": "FAISAL",
             "levels": [{"colour": c, "value": v, "label": "", "conf": "H"} for c, v in levels]}
        u["roles"] = assign_roles(u)
        return u

    # CG1 labels
    g("CG1 «مقاومه تحولت لدعم» = دعم وحدَه", lambda: (label_roles("مقاومه تحولت لدعم") == {("support", "دعم")}, label_roles("مقاومه تحولت لدعم")))
    g("CG1 الأحمرُ مع «دخول» متوافق · والبنفسجيُّ مع «ثبات دعم = دخول» متوافق",
      lambda: (not label_conflict("red", "دخول 1.40 (نصّ الرسالة)") and not label_conflict("purple", "ثبات دعم = دخول"), ""))
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
    g("CG2 بنفسجيٌّ فوق أسود ⟵ البنفسجيُّ وحدَه", lambda: (r3()[("purple", 9.0)][0] == "conflict" and r3()[("black", 8.0)][0] == "resistance", r3()))
    r4 = lambda: roles([("purple", 0.9, ""), ("red", 1.0, ""), ("blue", 3.0, ""), ("black", 4.0, "")])   # noqa: E731
    g("CG2 بنفسجيٌّ تحت أحمر وأزرقُ تحت أسود ليسا تعارضًا", lambda: (all(v[0] != "conflict" for v in r4().values()), r4()))
    r5 = lambda: roles([("red", 5.0, ""), ("black", 4.0, ""), ("black", 6.0, "")], above_all=True)       # noqa: E731
    g("CG2 حساسيّةُ «فوق كلِّه»: الأحمرُ تحت أعلى أسود ليس تعارضًا", lambda: (r5()[("red", 5.0)][0] == "support", r5()))
    r6 = lambda: roles([("red", 5.0, ""), ("purple", 6.0, "")], price=4.0)                                # noqa: E731
    g("CG2 الموضعُ مقابل السعر وسمٌ لا تعارض", lambda: (r6()[("red", 5.0)][0] == "support" and "red_above_price" in r6()[("red", 5.0)][2]
      and "purple_above_price" in r6()[("purple", 6.0)][2], r6()))
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
    k1 = lambda: measure_count([mk([("purple", 2.0), ("purple", 9.0), ("black", 5.0)])])                   # noqa: E731
    g("CG5 العدُّ كلُّه وغيرُ المتعارض منفصلان", lambda: (k1()["all_numbered"] == {2: 1} and k1()["non_conflict"] == {1: 1}, k1()))
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
    cats = lambda: [first(measure_stop([mk([("red", 2.0)], low=1.5, stop=s)], {"rows": []})["rows"]).get("cat")    # noqa: E731
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
    a = ap.parse_args(argv)
    if a.guards:
        return guards()
    if a.validate:
        check_pins(need_main=False)
        last, _, probs = load_register()
        probs += validate(last, image_ids())
        for p in probs[:30]:
            print("⛔", p)
        print("✅ السجلُّ سليم" if not probs else f"⛔ {len(probs)} مشكلة")
        return 0 if not probs else 9
    if a.check:
        check_pins(need_main=False)
        outs = outputs()
        bad = [os.path.relpath(p, ROOT) for p, s in outs.items() if not os.path.exists(p) or open(p, encoding="utf-8").read() != s]
        print("✅ المخرَجاتُ تُعاد بايتًا" if not bad else f"❌ تختلف: {bad}")
        return 0 if not bad else 1
    check_pins()
    for p, s in outputs().items():
        with open(p, "w", encoding="utf-8") as f:
            f.write(s)
        print("✍️", os.path.relpath(p, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
