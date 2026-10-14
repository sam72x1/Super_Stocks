"""T-FSWEEP — Faisal's sweeps in his own words, harvested on his NEW posts (contract `FSWEEP_prereg.md`, pinned below and required on
origin/main before any triage or analysis: exit 9 otherwise). Collection and measurement only: no production, threshold, root,
LOGIC_VERSION, V4, H6 or Telegram change.

Every image the Telegram collector saves after BOUNDARY gets exactly one triage row (SWEEP · NONE · UNREADABLE · SEEN) in an
append-only, hash-chained ledger. The governing question H-COLLAPSE is read once (§⑦): before Faisal's post, had the stock broken its
cycle base deeper than 13 %? — the free depth of `five_depth.depth_window(Super_stock.pivot_cycle_state, …, sweep=99)` BY NAME on daily
bars up to t' only. Base identity and %-agreement are NOT computed (closed T-SUPDEF, contract §⑨).

    python3 fm_forensics/fsweep/fsweep.py pending                 # new images not triaged yet
    python3 fm_forensics/fsweep/fsweep.py triage --image TG_1.jpg --decision NONE
    python3 fm_forensics/fsweep/fsweep.py triage --image TG_2.jpg --decision SWEEP --symbol ABC --post-date 2026-10-20T09:40 \
        --date-source visible_in_image --kind EXPECTED --author FAISAL --base 1.20 --low 1.06 --quote "…"
    python3 fm_forensics/fsweep/fsweep.py correct --seq 3 --decision NONE --note "…"
    python3 fm_forensics/fsweep/fsweep.py verify | status | analyze
    python3 fm_forensics/fsweep/fsweep.py --guards                # synthetic guards (no data read)
"""
import argparse
import ast
import datetime as dt
import hashlib
import inspect
import json
import math
import os
import re
import subprocess
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PREREG = os.path.join(HERE, "FSWEEP_prereg.md")
PREREG_SHA256 = "f457a4f9e326bb76fe46879ff47b2f5c74d705360241a5a2055ee1b46a44087a"
LEDGER = os.path.join(HERE, "data", "FSWEEP_LEDGER.jsonl")
RESULT = os.path.join(HERE, "data", "fsweep_result.json")
BARS_DIR = os.path.join(HERE, "data", "bars")
META = os.path.join(ROOT, "telegram_collect_meta.jsonl")
IMG_DIR = os.path.join(ROOT, "faisal_images")

# ── frozen design (the contract quotes each one) ────────────────────────────────────────────────────────
BOUNDARY = "2026-10-15T00:00:00Z"      # §② collected_utc on or after it
DEADLINE = "2027-04-14"                # §② §⑦
TARGET_N, FLOOR_N = 20, 10             # §⑦ eligible units
FRESH_DAYS = 7                         # §⑤ collected − post ≤ 7 days
LEAD, MIN_BARS, SPAN = 20, 60, 80      # §⑥ t'−19 … t' · PIVOT_CYCLE_WIN · jumps span t'−79 … t'
FREE_SWEEP = 99                        # §⑥ no base reset
COLLAPSE_PCT = 13.0                    # §⑥ PIVOT_SWEEP_PCT
SW_LO, SW_HI = 7.0, 13.0               # §⑧ «سحب السيوله متعارف عليه من 7٪ ل 13٪»
FWD = 20                               # §⑧ reached 2× within 20 sessions
CLOSE_ET = (16, 0)                     # §⑥ a post at/after 16:00 New York ⟶ t' is its day
NEW_STATUSES = ("saved", "saved_from_pending")
DECISIONS = ("SWEEP", "NONE", "UNREADABLE", "SEEN")
DATE_SOURCES = ("visible_in_image", "forward_origin", "message_date")
KINDS = ("OBSERVED", "EXPECTED")
AUTHORS = ("FAISAL", "UNSIGNED", "THIRD_PARTY")
SWEEP_FIELDS = ("symbol", "post_date", "date_source", "kind", "author", "base_price", "sweep_low", "sweep_pct", "quote")
QUOTE_MAX = 200
CONFIG_PINS = {"PIVOT_CYCLE_WIN": 60, "METHOD_BOUNCE_MIN_PCT": 10.0, "PIVOT_TEST_TYPICAL_PCT": 20.0, "METHOD_HOLD_TOL": 0.015,
               "STABILITY_MIN": 3}
PROD_SEM_SHA256 = "3b12c5f3b85b9c620662593f499f528429baebe2396cadf7bb1fa71048c262f8"


# ── ledger (pure) ───────────────────────────────────────────────────────────────────────────────────────
def canon(row):
    return json.dumps({k: v for k, v in row.items() if k != "row_hash"}, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def row_hash(row):
    return hashlib.sha256(canon(row).encode("utf-8")).hexdigest()


def load_jsonl(path):
    if not os.path.exists(path):
        return []
    return [json.loads(ln) for ln in open(path, encoding="utf-8") if ln.strip()]


def new_images(meta_rows, boundary=BOUNDARY):
    """§② saved_name ⟶ its meta row: new content (saved / saved_from_pending) collected on or after the boundary."""
    out = {}
    for r in meta_rows:
        n = r.get("saved_name")
        if n and r.get("status") in NEW_STATUSES and str(r.get("collected_utc") or "") >= boundary:
            out.setdefault(n, r)
    return out


def _num(v):
    return v is None or (isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and v > 0)


def _post_date_ok(s):
    return isinstance(s, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}(T\d{2}:\d{2})?", s) is not None and _parse_post(s) is not None


def _parse_post(s):
    try:
        if "T" in s:
            return dt.datetime.strptime(s, "%Y-%m-%dT%H:%M")
        return dt.datetime.strptime(s, "%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def validate_payload(p):
    """Schema of one triage decision ⟶ list of errors (empty = valid). Unknown is null, never 0."""
    err = []
    d = p.get("decision")
    if d not in DECISIONS:
        return [f"decision {d!r}"]
    extra = set(p) - set(SWEEP_FIELDS) - {"decision", "note"}
    if extra:
        err.append(f"unknown fields {sorted(extra)}")
    if p.get("note") is not None and (not isinstance(p["note"], str) or len(p["note"]) > QUOTE_MAX):
        err.append("note")
    if d != "SWEEP":
        if any(p.get(f) is not None for f in SWEEP_FIELDS):
            err.append("sweep fields on a non-SWEEP row")
        return err
    if not isinstance(p.get("symbol"), str) or not re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,9}", p["symbol"]):
        err.append("symbol")
    if not _post_date_ok(p.get("post_date")):
        err.append("post_date")
    if p.get("date_source") not in DATE_SOURCES:
        err.append("date_source")
    if p.get("kind") not in KINDS:
        err.append("kind")
    if p.get("author") not in AUTHORS:
        err.append("author")
    for f in ("base_price", "sweep_low", "sweep_pct"):
        if not _num(p.get(f)):
            err.append(f)
    q = p.get("quote")
    if q is not None and (not isinstance(q, str) or len(q) > QUOTE_MAX):
        err.append("quote")
    return err


def make_row(rows, body):
    """Append-ready row: seq, prev (GENESIS first), row_hash over the canonical JSON without row_hash."""
    row = dict(body, seq=len(rows) + 1, prev=rows[-1]["row_hash"] if rows else "GENESIS")
    row["row_hash"] = row_hash(row)
    return row


def verify_rows(rows, imgs, file_sha=None, result_len=None):
    """§④ ⟶ list of errors. imgs = new_images(meta). file_sha(name) ⟶ sha256 of the saved file (None = missing)."""
    err, seen, triage_seq = [], set(), {}
    prev = "GENESIS"
    for i, r in enumerate(rows):
        tag = f"row {i + 1}"
        if r.get("seq") != i + 1:
            err.append(f"{tag}: seq {r.get('seq')}")
        if r.get("prev") != prev:
            err.append(f"{tag}: broken chain")
        if r.get("row_hash") != row_hash(r):
            err.append(f"{tag}: row_hash")
        prev = r.get("row_hash")
        kind = r.get("row")
        payload = {k: r[k] for k in r if k in SWEEP_FIELDS or k in ("decision", "note")}
        err += [f"{tag}: {e}" for e in validate_payload(payload)]
        if kind == "TRIAGE":
            n = r.get("image")
            if n in seen:
                err.append(f"{tag}: {n} triaged twice")
            seen.add(n)
            triage_seq[r.get("seq")] = n
            m = imgs.get(n)
            if m is None:
                err.append(f"{tag}: {n} is not a new image after the boundary")
                continue
            if r.get("image_sha256") != m.get("sha256"):
                err.append(f"{tag}: sha differs from the meta row")
            if file_sha is not None and file_sha(n) != m.get("sha256"):
                err.append(f"{tag}: sha differs from the saved file")
            if r.get("collected_utc") != m.get("collected_utc"):
                err.append(f"{tag}: collected_utc differs from the meta row")
            if str(r.get("triaged_utc") or "") < str(m.get("collected_utc") or "~"):
                err.append(f"{tag}: triaged before collected")
        elif kind == "CORRECTION":
            if r.get("target") not in triage_seq:
                err.append(f"{tag}: correction of a missing triage row {r.get('target')}")
            elif r.get("image") != triage_seq[r["target"]]:
                err.append(f"{tag}: correction image mismatch")
            if result_len is not None and r.get("seq", 0) > result_len:
                err.append(f"{tag}: correction after the analysis")
        else:
            err.append(f"{tag}: row type {kind!r}")
    return err


def effective(rows):
    """image ⟶ the effective decision (original triage, then corrections in seq order) with its triage seq and collected_utc."""
    out = {}
    for r in rows:
        payload = {k: r.get(k) for k in SWEEP_FIELDS + ("decision", "note")}
        if r.get("row") == "TRIAGE":
            out[r["image"]] = dict(payload, image=r["image"], seq=r["seq"], collected_utc=r["collected_utc"])
        elif r.get("row") == "CORRECTION" and r.get("image") in out:
            base = out[r["image"]]
            out[r["image"]] = dict(payload, image=base["image"], seq=base["seq"], collected_utc=base["collected_utc"])
    return out


# ── units, t', stop rule (pure) ─────────────────────────────────────────────────────────────────────────
def cutoff_day(post_date):
    """§⑥ the last calendar day whose session closed before the post (New York): at/after 16:00 ⟶ its day · else and date-only ⟶ the day before."""
    p = _parse_post(post_date)
    if "T" in post_date and (p.hour, p.minute) >= CLOSE_ET:
        return p.date()
    return p.date() - dt.timedelta(days=1)


def eligibility(e):
    """§⑤ ⟶ None (eligible) or the reason."""
    if e.get("decision") != "SWEEP":
        return "not_sweep"
    if e.get("author") != "FAISAL":
        return f"author_{e.get('author')}"
    if e.get("date_source") not in ("visible_in_image", "forward_origin"):
        return "no_post_date"
    col = dt.datetime.strptime(e["collected_utc"], "%Y-%m-%dT%H:%M:%SZ").date()
    if (col - _parse_post(e["post_date"]).date()).days > FRESH_DAYS:
        return "stale_post"
    return None


def units(eff):
    """§⑤ the first eligible SWEEP per symbol (by post date, then seq) ⟶ (units, ineligible reason counts)."""
    ok, why = [], {}
    for e in sorted(eff.values(), key=lambda e: e["seq"]):
        if e.get("decision") != "SWEEP":
            continue
        r = eligibility(e)
        if r:
            why[r] = why.get(r, 0) + 1
        else:
            ok.append(e)
    first = {}
    for e in sorted(ok, key=lambda e: (_parse_post(e["post_date"]), e["seq"])):
        if e["symbol"] in first:
            why["repeat_symbol"] = why.get("repeat_symbol", 0) + 1
        else:
            first[e["symbol"]] = e
    return list(first.values()), why


def stop_rule(n_units, today, deadline=DEADLINE):
    """§⑦ ⟶ RUN · WAIT · NO_MEASURE (today, deadline: ISO dates)."""
    if n_units >= TARGET_N:
        return "RUN"
    if str(today) >= deadline:
        return "RUN" if n_units >= FLOOR_N else "NO_MEASURE"
    return "WAIT"


def stated_pct(e):
    if e.get("sweep_pct") is not None:
        return float(e["sweep_pct"])
    if e.get("base_price") is not None and e.get("sweep_low") is not None:
        return round((float(e["base_price"]) - float(e["sweep_low"])) / float(e["base_price"]) * 100.0, 4)
    return None


# ── measure (pure on injected functions) ────────────────────────────────────────────────────────────────
def pick_snapshot(snaps, sym, cut):
    """§⑥ the EARLIEST snapshot fetched after `cut` with ≥ SPAN bars up to `cut` ⟶ (name, rows) or (None, None).
    snaps: [(fetch_date ISO, name, {"daily": {...}})] in any order."""
    for fdate, name, blob in sorted(snaps, key=lambda s: (s[0], s[1])):
        rows = ((blob or {}).get("daily") or {}).get(sym) or []
        if fdate > cut.isoformat() and sum(1 for r in rows if str(r[0])[:10] <= cut.isoformat()) >= SPAN:
            return name, rows
    return None, None


def bars_ready(snaps, unit_list):
    """§⑦ a bars snapshot fetched after the latest t' among the units must exist before any verdict is written."""
    if not unit_list:
        return True
    last = max(cutoff_day(e["post_date"]) for e in unit_list).isoformat()
    return any(s[0] > last for s in snaps)


def classify(pc_fn, df, k, depth_fn, jumps_fn):
    """§⑥ ⟶ (class, depth row). class ∈ COLLAPSE · NO_COLLAPSE · NO_SWEEP · UNKNOWN:<why>. k = position of t' + 1."""
    if df is None or k < SPAN:
        return "UNKNOWN:no_bars", None
    if jumps_fn(df, k):
        return "UNKNOWN:jump", None
    d = depth_fn(pc_fn, df, k, lead=LEAD, sweep=FREE_SWEEP)
    if d.get("depth") is None:
        return ("NO_SWEEP", d) if d.get("why") == "no_sweep_in_window" else (f"UNKNOWN:{d.get('why')}", d)
    return ("COLLAPSE" if float(d["depth"]) > COLLAPSE_PCT else "NO_COLLAPSE"), d


def reached_2x(df, k):
    """§⑧ descriptive: max high over the FWD sessions after t' ≥ 2 × close(t') ⟶ True · False · None (fewer than FWD sessions)."""
    if df is None or len(df) < k + FWD:
        return None
    return bool(float(df["High"].iloc[k: k + FWD].max()) >= 2.0 * float(df["Close"].iloc[k - 1]))


def wilson(k, n, z=1.959964):
    if n <= 0:
        return None
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, c - h), min(1.0, c + h)


def readings(classes):
    """§⑦ reading A (NO_SWEEP = no collapse) and B (NO_SWEEP excluded) ⟶ dicts with n, k, wilson."""
    col = sum(1 for c in classes if c == "COLLAPSE")
    det_a = sum(1 for c in classes if c in ("COLLAPSE", "NO_COLLAPSE", "NO_SWEEP"))
    det_b = sum(1 for c in classes if c in ("COLLAPSE", "NO_COLLAPSE"))
    return ({"n": det_a, "k": col, "wilson": wilson(col, det_a)}, {"n": det_b, "k": col, "wilson": wilson(col, det_b)})


def verdict(a, b):
    """§⑦ by the weakest: SUPPORTED needs lo > 0.5 in BOTH readings, REFUTED hi < 0.5 in BOTH · fewer than FLOOR_N in A ⟶ NO-MEASURE."""
    if a["n"] < FLOOR_N:
        return "NO-MEASURE"
    wa, wb = a["wilson"], b["wilson"]
    if wa and wb and wa[0] > 0.5 and wb[0] > 0.5:
        return "SUPPORTED"
    if wa and wb and wa[1] < 0.5 and wb[1] < 0.5:
        return "REFUTED"
    return "INCONCLUSIVE"


def quantiles(vals):
    v = sorted(vals)

    def q(p):
        if not v:
            return None
        i = (len(v) - 1) * p
        lo, hi = int(math.floor(i)), int(math.ceil(i))
        return round(v[lo] + (v[hi] - v[lo]) * (i - lo), 2)
    return {"n": len(v), "q25": q(0.25), "median": q(0.5), "q75": q(0.75), "in_band": sum(1 for x in v if SW_LO <= x <= SW_HI)}


# ── pins and gates ──────────────────────────────────────────────────────────────────────────────────────
def _sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest() if os.path.exists(path) else None


def semantic_sha(fns):
    """sha256 of the functions' AST without their docstrings (a docstring edit does not change the measure)."""
    parts = []
    for f in fns:
        tree = ast.parse(textwrap.dedent(inspect.getsource(f)))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.body and isinstance(node.body[0], ast.Expr) \
                    and isinstance(getattr(node.body[0], "value", None), ast.Constant) and isinstance(node.body[0].value.value, str):
                node.body = node.body[1:] or [ast.Pass()]
        parts.append(ast.dump(tree))
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()


def _main_blob(path):
    rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
    p = subprocess.run(["git", "-C", ROOT, "show", f"origin/main:{rel}"], capture_output=True)
    return p.stdout if p.returncode == 0 else None


def check_merged(read=None):
    """«يُدمج في main قبل أيّ فرز»: the local contract AND origin/main must carry the pinned bytes, else exit 9."""
    if _sha(PREREG) != PREREG_SHA256:
        print(f"⛔ contract changed or not pinned: {_sha(PREREG)} ≠ {PREREG_SHA256}")
        sys.exit(9)
    blob = (read or (lambda: _main_blob(PREREG)))()
    got = hashlib.sha256(blob).hexdigest() if blob is not None else None
    if got != PREREG_SHA256:
        print(f"⛔ the pinned contract is not on origin/main ({got}) — merge it first (git fetch --force)")
        sys.exit(9)


def _mods():
    for p in (os.path.join(ROOT, "fm_forensics", "gen5"), os.path.join(ROOT, "fm_forensics", "layers"), ROOT):
        if p not in sys.path:
            sys.path.insert(0, p)
    import gen5_features as G
    import five_depth as FD
    return G.S(), FD


def check_pins(S, FD):
    got = semantic_sha((S.pivot_cycle_state, FD.depth_window, FD.jumps, FD.frame))
    if got != PROD_SEM_SHA256:
        print(f"⛔ reused functions changed: {got} ≠ {PROD_SEM_SHA256}")
        sys.exit(9)
    cfg = {k: S.CONFIG.get(k) for k in CONFIG_PINS}
    if cfg != CONFIG_PINS:
        print(f"⛔ cycle settings changed: {cfg} ≠ {CONFIG_PINS}")
        sys.exit(9)


# ── commands ────────────────────────────────────────────────────────────────────────────────────────────
def _now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _file_sha(name):
    return _sha(os.path.join(IMG_DIR, name))


def _state():
    rows = load_jsonl(LEDGER)
    imgs = new_images(load_jsonl(META))
    res = json.load(open(RESULT, encoding="utf-8")) if os.path.exists(RESULT) else None
    return rows, imgs, res


def _append(row):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def cmd_pending(_a):
    rows, imgs, _ = _state()
    done = {r.get("image") for r in rows if r.get("row") == "TRIAGE"}
    todo = [imgs[n] for n in sorted(imgs, key=lambda n: (imgs[n].get("collected_utc") or "", n)) if n not in done]
    print(f"🧾 T-FSWEEP · صورٌ جديدة بعد {BOUNDARY}: {len(imgs)} · مفروزة {len(done & set(imgs))} · تنتظر الفرز {len(todo)}")
    for m in todo:
        fwd = (m.get("forward") or {}).get("date") if isinstance(m.get("forward"), dict) else None
        print(f"   {m['saved_name']} · جُمعت {m.get('collected_utc')} · أُرسلت {m.get('date')} · توجيه {m.get('forward_type')}"
              f"{' ' + fwd if fwd else ''} · ألبوم {m.get('media_group_id') or '—'} · ملفّ {'✓' if _file_sha(m['saved_name']) else '✗'}")
    if todo:
        print("   ↳ الترتيب: سجلُّ العين RR1 ⟵ استلامُ V4.1 إن كانت حالة ⟵ ثمّ `triage` هنا (العقد §③-د).")
    return 0


def _payload(a):
    p = {"decision": a.decision}
    for f, v in (("symbol", a.symbol), ("post_date", a.post_date), ("date_source", a.date_source), ("kind", a.kind),
                 ("author", a.author), ("base_price", a.base), ("sweep_low", a.low), ("sweep_pct", a.pct), ("quote", a.quote)):
        if v is not None:
            p[f] = v.upper() if f == "symbol" else v
    if a.note:
        p["note"] = a.note
    return p


def cmd_triage(a):
    check_merged()
    rows, imgs, res = _state()
    errs = verify_rows(rows, imgs, _file_sha, res and res.get("ledger_len"))
    if errs:
        print("⛔ the ledger is not sound:", *errs[:10], sep="\n   ")
        return 9
    m = imgs.get(a.image)
    if m is None:
        print(f"⛔ {a.image} is not a new image collected after {BOUNDARY}")
        return 9
    if any(r.get("row") == "TRIAGE" and r.get("image") == a.image for r in rows):
        print(f"⛔ {a.image} is already triaged — use `correct`")
        return 9
    if _file_sha(a.image) != m.get("sha256"):
        print(f"⛔ {a.image}: the saved file does not match its meta sha")
        return 9
    p = _payload(a)
    e = validate_payload(p)
    if e:
        print("⛔ invalid triage:", e)
        return 9
    row = make_row(rows, dict(p, row="TRIAGE", image=a.image, image_sha256=m["sha256"], collected_utc=m["collected_utc"],
                              triaged_utc=_now()))
    errs = verify_rows(rows + [row], imgs, _file_sha)
    if errs:
        print("⛔ the new row would break the ledger:", *errs[:10], sep="\n   ")
        return 9
    _append(row)
    print(f"✅ seq {row['seq']} · {a.image} · {p['decision']}")
    return 0


def cmd_correct(a):
    check_merged()
    rows, imgs, res = _state()
    if res is not None:
        print("⛔ no correction after the analysis (contract §③-ج)")
        return 9
    tgt = next((r for r in rows if r.get("row") == "TRIAGE" and r.get("seq") == a.seq), None)
    if tgt is None:
        print(f"⛔ no triage row with seq {a.seq}")
        return 9
    p = _payload(a)
    e = validate_payload(p)
    if e:
        print("⛔ invalid correction:", e)
        return 9
    row = make_row(rows, dict(p, row="CORRECTION", target=a.seq, image=tgt["image"], triaged_utc=_now()))
    errs = verify_rows(rows + [row], imgs, _file_sha)
    if errs:
        print("⛔ the correction would break the ledger:", *errs[:10], sep="\n   ")
        return 9
    _append(row)
    print(f"✅ seq {row['seq']} · correction of {a.seq} · {p['decision']}")
    return 0


def cmd_verify(_a):
    rows, imgs, res = _state()
    errs = verify_rows(rows, imgs, _file_sha, res and res.get("ledger_len"))
    if errs:
        print(f"⛔ T-FSWEEP ledger: {len(errs)} error(s)", *errs[:20], sep="\n   ")
        return 9
    print(f"✅ T-FSWEEP ledger sound · {len(rows)} row(s) · {len(imgs)} new image(s) after {BOUNDARY}")
    return 0


def cmd_status(_a):
    """Counts only — no bars, no depth (the governing measure stays unread until §⑦)."""
    rows, imgs, res = _state()
    errs = verify_rows(rows, imgs, _file_sha, res and res.get("ledger_len"))
    if errs:
        print(f"⛔ T-FSWEEP ledger: {len(errs)} error(s) — run `verify`")
        return 9
    eff = effective(rows)
    dec = {}
    for e in eff.values():
        dec[e["decision"]] = dec.get(e["decision"], 0) + 1
    u, why = units(eff)
    today = dt.datetime.now(dt.timezone.utc).date()
    left = (dt.date.fromisoformat(DEADLINE) - today).days
    print(f"🧾 T-FSWEEP · صورٌ جديدة {len(imgs)} · مفروزة {len(eff)} · تنتظر {len(set(imgs) - set(eff))} · القرارات {dec or '—'}")
    print(f"   الوحداتُ المؤهَّلة {len(u)} من {TARGET_N} (الأرضيّة {FLOOR_N}) · غيرُ المؤهَّل {why or '—'} · "
          f"المهلة {DEADLINE} (بعد {left} يومًا) · القاعدة: {stop_rule(len(u), today.isoformat())}"
          f"{' · النتيجة مكتوبة' if res else ''}")
    return 0


def _snapshots():
    import gzip
    out = []
    if os.path.isdir(BARS_DIR):
        for n in sorted(os.listdir(BARS_DIR)):
            m = re.fullmatch(r"(\d{4}-\d{2}-\d{2})\.json\.gz", n)
            if m:
                out.append((m.group(1), n, json.load(gzip.open(os.path.join(BARS_DIR, n), "rt", encoding="utf-8"))))
    return out


def cmd_analyze(_a):
    check_merged()
    rows, imgs, res = _state()
    errs = verify_rows(rows, imgs, _file_sha, res and res.get("ledger_len"))
    if errs:
        print("⛔ the ledger is not sound:", *errs[:10], sep="\n   ")
        return 9
    if res is not None:
        print("ℹ️ the result is already written (once, contract §⑦):")
        print(json.dumps(res, ensure_ascii=False, indent=1))
        return 0
    eff = effective(rows)
    u, why = units(eff)
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    rule = stop_rule(len(u), today)
    if rule == "WAIT":
        print(f"⏳ not yet: {len(u)} eligible unit(s) of {TARGET_N} before {DEADLINE} (contract §⑦)")
        return 7
    out = {"prereg_sha256": PREREG_SHA256, "analyzed_utc": _now(), "ledger_len": len(rows),
           "ledger_head": rows[-1]["row_hash"] if rows else "GENESIS", "rule": rule, "units": [], "ineligible": why}
    if rule == "NO_MEASURE":
        out.update(verdict="NO-MEASURE", reason=f"{len(u)} eligible unit(s) at the deadline, fewer than {FLOOR_N}")
    else:
        snaps = _snapshots()
        if not bars_ready(snaps, u):
            print("⏳ not yet: no bars snapshot fetched after the latest t' among the units (contract §⑦) — nothing written")
            return 7
        S, FD = _mods()
        check_pins(S, FD)
        out["snapshots"] = {n: _sha(os.path.join(BARS_DIR, n)) for _, n, _b in snaps}
        classes = []
        for e in u:
            cut = cutoff_day(e["post_date"])
            name, bars = pick_snapshot(snaps, e["symbol"], cut)
            df = FD.frame(bars) if bars else None
            k = sum(1 for r in bars if str(r[0])[:10] <= cut.isoformat()) if bars else 0
            cls, d = classify(S.pivot_cycle_state, df, k, FD.depth_window, FD.jumps)
            classes.append(cls)
            out["units"].append({"symbol": e["symbol"], "image": e["image"], "post_date": e["post_date"], "cutoff": cut.isoformat(),
                                 "t_prime": df.index[k - 1].date().isoformat() if df is not None and k else None, "snapshot": name,
                                 "class": cls, "depth": d, "kind": e["kind"], "stated_pct": stated_pct(e),
                                 "reached_2x": reached_2x(df, k) if df is not None and k else None})
        a, b = readings(classes)
        out.update(reading_A=a, reading_B=b, verdict=verdict(a, b))
    sp = [x for x in (stated_pct(e) for e in u) if x is not None]
    out["descriptive"] = {"stated_pct": quantiles(sp),
                          "kind": {k: sum(1 for e in u if e["kind"] == k) for k in KINDS},
                          "all_sweep_rows_by_author": {k: sum(1 for e in eff.values() if e["decision"] == "SWEEP" and e["author"] == k)
                                                       for k in AUTHORS}}
    out["predictions"] = {"P1_supported": out.get("verdict") == "SUPPORTED",
                          "P2_band_share_ge_70": (out["descriptive"]["stated_pct"]["in_band"] / len(sp) >= 0.7) if sp else None,
                          "P3_target_before_deadline": len(u) >= TARGET_N and today < DEADLINE}
    json.dump(out, open(RESULT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


# ── guards (synthetic · no data read) ───────────────────────────────────────────────────────────────────
def guards():
    import io
    import contextlib
    bad = []

    def check(name, ok, info=""):
        print(f"{'✅' if ok else '❌'} {name}{'' if ok else ' · ' + str(info)}")
        if not ok:
            bad.append(name)

    meta = [{"saved_name": "TG_1.jpg", "status": "saved", "collected_utc": "2026-10-14T23:59:59Z", "sha256": "a"},
            {"saved_name": "TG_2.jpg", "status": "saved", "collected_utc": "2026-10-15T00:00:00Z", "sha256": "b"},
            {"saved_name": "TG_3.jpg", "status": "dup", "collected_utc": "2026-10-16T00:00:00Z", "sha256": "c"},
            {"saved_name": "TG_4.jpg", "status": "saved_from_pending", "collected_utc": "2026-10-17T01:00:00Z", "sha256": "d"},
            {"kind": "heartbeat", "status": "heartbeat", "collected_utc": "2026-10-18T00:00:00Z"}]
    imgs = new_images(meta)
    check("FSG1 الحدّ والحالة: قبل الحدّ ومكرّرٌ ونبضٌ لا تُفرز · عند الحدّ وما بعده يُفرز", sorted(imgs) == ["TG_2.jpg", "TG_4.jpg"], sorted(imgs))

    sw = {"decision": "SWEEP", "symbol": "ABC", "post_date": "2026-10-20T09:40", "date_source": "visible_in_image", "kind": "EXPECTED",
          "author": "FAISAL", "base_price": 1.2, "sweep_low": 1.06, "sweep_pct": None, "quote": "يسحب السيولة"}
    check("FSG2 مخطّطُ SWEEP السليم يمرّ", validate_payload(sw) == [], validate_payload(sw))
    errs = {k: validate_payload(dict(sw, **{k: v})) for k, v in (("symbol", None), ("post_date", "2026-13-01"), ("kind", "X"),
                                                                    ("author", "faisal"), ("base_price", 0), ("sweep_pct", -3.0),
                                                                    ("date_source", "guess"), ("quote", "x" * 201))}
    check("FSG2 كلُّ حقلٍ فاسدٍ يُرفض (والصفرُ ليس مجهولًا)", all(errs.values()), {k: v for k, v in errs.items() if not v})
    check("FSG2 قرارٌ غيرُ SWEEP لا يحمل حقولَ السحب", validate_payload({"decision": "NONE", "symbol": "ABC"}) != []
          and validate_payload({"decision": "NONE", "note": "عامّ"}) == [] and validate_payload({"decision": "MAYBE"}) != [])

    def mk(rows, name, p, triaged="2026-10-15T01:00:00Z"):
        m = next(x for x in meta if x.get("saved_name") == name)
        return make_row(rows, dict(p, row="TRIAGE", image=name, image_sha256=m["sha256"], collected_utc=m["collected_utc"],
                                   triaged_utc=triaged))
    rows = []
    rows.append(mk(rows, "TG_2.jpg", {"decision": "NONE"}))
    rows.append(mk(rows, "TG_4.jpg", sw, "2026-10-17T02:00:00Z"))
    fs = {"TG_2.jpg": "b", "TG_4.jpg": "d"}.get
    check("FSG3 سجلٌّ سليمٌ يمرّ", verify_rows(rows, imgs, fs) == [], verify_rows(rows, imgs, fs))
    t = [dict(r) for r in rows]
    t[0]["decision"] = "SWEEP"
    check("FSG3 تعديلُ صفٍّ يُكسر البصمة", any("row_hash" in e for e in verify_rows(t, imgs, fs)))
    check("FSG3 حذفُ صفٍّ أو تبديلُ ترتيبٍ يُكسر السلسلة", verify_rows(rows[1:], imgs, fs) != [] and verify_rows(rows[::-1], imgs, fs) != [])
    forged = dict(rows[1], prev="GENESIS")
    forged["row_hash"] = row_hash(forged)
    check("FSG3 صفٌّ مزوَّرٌ بتسلسلٍ صحيحٍ وبصمةٍ معادة يُكسر السلسلة", any("broken chain" in e for e in verify_rows([rows[0], forged], imgs, fs)))
    r3 = rows + [mk(rows, "TG_2.jpg", {"decision": "NONE"})]
    check("FSG4 صورةٌ مفروزةٌ مرّتين تسقط", any("twice" in e for e in verify_rows(r3, imgs, fs)))
    r4 = rows + [make_row(rows, {"decision": "NONE", "row": "TRIAGE", "image": "TG_1.jpg", "image_sha256": "a",
                                 "collected_utc": "2026-10-14T23:59:59Z", "triaged_utc": "2026-10-15T01:00:00Z"})]
    check("FSG4 صورةٌ قبل الحدّ تسقط", any("not a new image" in e for e in verify_rows(r4, imgs, fs)))
    check("FSG4 بصمةُ الملفّ المخالفة تسقط", any("saved file" in e for e in verify_rows(rows, imgs, {"TG_2.jpg": "x", "TG_4.jpg": "d"}.get)))
    r5 = [mk([], "TG_2.jpg", {"decision": "NONE"}, "2026-10-14T00:00:00Z")]
    check("FSG4 فرزٌ قبل الجمع يسقط", any("before collected" in e for e in verify_rows(r5, imgs, fs)))

    cor = make_row(rows, {"decision": "NONE", "row": "CORRECTION", "target": 2, "image": "TG_4.jpg", "triaged_utc": "2026-10-18T00:00:00Z"})
    rc = rows + [cor]
    check("FSG5 التصحيحُ يُلحق ولا يمحو · والنافذُ آخرُه", verify_rows(rc, imgs, fs) == [] and effective(rc)["TG_4.jpg"]["decision"] == "NONE"
          and effective(rows)["TG_4.jpg"]["decision"] == "SWEEP" and len(rc) == 3)
    bad_c = rows + [make_row(rows, {"decision": "NONE", "row": "CORRECTION", "target": 9, "image": "TG_4.jpg", "triaged_utc": "x"})]
    check("FSG5 تصحيحُ صفٍّ غيرِ موجود · وتصحيحٌ بعد التحليل يسقطان", any("missing triage" in e for e in verify_rows(bad_c, imgs, fs))
          and any("after the analysis" in e for e in verify_rows(rc, imgs, fs, result_len=2)))

    def e(sym, seq, post, col, **kw):
        return dict({"decision": "SWEEP", "symbol": sym, "post_date": post, "date_source": "visible_in_image", "kind": "EXPECTED",
                     "author": "FAISAL", "seq": seq, "collected_utc": col, "image": f"TG_{seq}.jpg"}, **kw)
    eff = {x["image"]: x for x in (
        e("AAA", 1, "2026-10-20", "2026-10-20T10:00:00Z"),
        e("AAA", 2, "2026-10-18", "2026-10-21T10:00:00Z"),                       # earlier post ⟶ the unit
        e("BBB", 3, "2026-10-20", "2026-10-20T10:00:00Z", author="UNSIGNED"),
        e("CCC", 4, "2026-10-20", "2026-10-20T10:00:00Z", date_source="message_date"),
        e("DDD", 5, "2026-10-01", "2026-10-20T10:00:00Z"),                       # 19 days old ⟶ stale
        e("EEE", 6, "2026-10-13", "2026-10-20T10:00:00Z"),                       # exactly 7 days ⟶ fresh
        dict(e("FFF", 7, "2026-10-20", "2026-10-20T10:00:00Z"), decision="NONE"))}
    u, why = units(eff)
    check("FSG6 الوحدة: أوّلُ مؤهَّلٍ لكلّ رمزٍ بتاريخ المنشور · وغيرُ الموقَّع وبلا تاريخٍ والقديمُ يُعَدّ ولا يحكم",
          sorted((x["symbol"], x["seq"]) for x in u) == [("AAA", 2), ("EEE", 6)]
          and why == {"author_UNSIGNED": 1, "no_post_date": 1, "stale_post": 1, "repeat_symbol": 1}, (u, why))

    cd = {p: cutoff_day(p).isoformat() for p in ("2026-10-20T15:59", "2026-10-20T16:00", "2026-10-20", "2026-10-19T09:00")}
    check("FSG7 t': قبل 16:00 وتاريخٌ بلا وقت ⟵ ما قبله · عند 16:00 فما بعد ⟵ يومُه",
          cd == {"2026-10-20T15:59": "2026-10-19", "2026-10-20T16:00": "2026-10-20", "2026-10-20": "2026-10-19",
                 "2026-10-19T09:00": "2026-10-18"}, cd)

    check("FSG8 قاعدةُ الإيقاف: 20 ⟵ تشغيل · دونها قبل المهلة ⟵ انتظار · عند المهلة 10 ⟵ تشغيل وأقلّ ⟵ لا قياس",
          [stop_rule(20, "2026-11-01"), stop_rule(19, "2027-04-13"), stop_rule(10, "2027-04-14"), stop_rule(9, "2027-04-14"),
           stop_rule(25, "2026-10-20")] == ["RUN", "WAIT", "RUN", "NO_MEASURE", "RUN"])

    class _DF:
        def __init__(self, n):
            self.n = n

        def __len__(self):
            return self.n
    seen_k = []

    def fake_depth(depth, why=None):
        def f(pc_fn, df, k, lead, sweep):
            seen_k.append((k, lead, sweep))
            return {"depth": depth, "why": why}
        return f
    cl = {name: classify(None, _DF(200), 100, fd, lambda df, k: jumps)[0] for name, fd, jumps in (
        ("d14", fake_depth(14.0), []), ("d13", fake_depth(13.0), []), ("none", fake_depth(None, "no_sweep_in_window"), []),
        ("short", fake_depth(None, "short_history"), []), ("jump", fake_depth(30.0), [["2026-10-01", 4.0]]))}
    check("FSG9 الانهيار أكبرُ من 13 حصرًا · لا سحب ⟵ NO_SWEEP · قصيرٌ وقفزةٌ ⟵ مجهول",
          cl == {"d14": "COLLAPSE", "d13": "NO_COLLAPSE", "none": "NO_SWEEP", "short": "UNKNOWN:short_history", "jump": "UNKNOWN:jump"}, cl)
    check("FSG9 العمقُ الحرّ يُطلب بنافذة 20 وبلا إعادة قاعدة (sweep=99) وبموضع t'+1",
          seen_k and all(x == (100, LEAD, FREE_SWEEP) for x in seen_k), seen_k)
    check("FSG9 أقلُّ من 80 شمعةً حتى t' أو بلا شموع ⟵ مجهول", classify(None, _DF(200), 79, fake_depth(20.0), lambda df, k: [])[0]
          == "UNKNOWN:no_bars" and classify(None, None, 100, fake_depth(20.0), lambda df, k: [])[0] == "UNKNOWN:no_bars")

    a, b = readings(["COLLAPSE"] * 15 + ["NO_COLLAPSE"] * 5)
    a2, b2 = readings(["COLLAPSE"] * 14 + ["NO_COLLAPSE"] * 3 + ["NO_SWEEP"] * 3)
    a3, b3 = readings(["NO_COLLAPSE"] * 15 + ["COLLAPSE"] * 0 + ["NO_SWEEP"] * 5)
    a4, b4 = readings(["COLLAPSE"] * 4 + ["NO_COLLAPSE"] * 4 + ["UNKNOWN:jump"] * 12)
    check("FSG10 الحكمُ بالأضعف: 15/20 ⟵ يُدعم · 14 مع 3 بلا سحب ⟵ القراءة أ تحت ⟵ غيرُ حاسم · صفرٌ ⟵ يُكذَّب · دون 10 محسومة ⟵ لا قياس",
          [verdict(a, b), verdict(a2, b2), verdict(a3, b3), verdict(a4, b4)] == ["SUPPORTED", "INCONCLUSIVE", "REFUTED", "NO-MEASURE"],
          [verdict(a, b), verdict(a2, b2), verdict(a3, b3), verdict(a4, b4)])
    w = wilson(15, 20)
    check("FSG10 ويلسون 15/20 حدُّه الأدنى 0.53 (العقد §⑪)", w and abs(w[0] - 0.531) < 0.002, w)

    check("FSG11 النسبةُ المكتوبة: نسبتُه ثمّ رقماه ثمّ مجهولة (لا صفر)",
          stated_pct({"sweep_pct": 9.0, "base_price": 1, "sweep_low": 0.5}) == 9.0
          and abs(stated_pct({"base_price": 2.0, "sweep_low": 1.8}) - 10.0) < 1e-9 and stated_pct({"base_price": 2.0}) is None)
    qs = quantiles([5.0, 7.0, 10.0, 13.0, 14.0])
    check("FSG11 الحزمةُ 7-13 شاملة الطرفين", qs["in_band"] == 3 and qs["median"] == 10.0, qs)

    cut = dt.date(2026, 10, 19)
    rows80 = [[(dt.date(2026, 6, 1) + dt.timedelta(days=i)).isoformat(), 1, 1, 1, 1, 1] for i in range(141)]  # last 2026-10-19
    snaps = [("2026-10-19", "a", {"daily": {"ABC": rows80}}), ("2026-11-01", "c", {"daily": {"ABC": rows80}}),
             ("2026-10-25", "b", {"daily": {"ABC": rows80[-79:]}}), ("2026-10-30", "d", {"daily": {"ABC": rows80}})]
    check("FSG12 اللقطة: أقدمُ لقطةٍ جُلبت بعد t' وفيها 80 شمعةً حتى t'", pick_snapshot(snaps, "ABC", cut)[0] == "d"
          and pick_snapshot(snaps, "XYZ", cut) == (None, None), pick_snapshot(snaps, "ABC", cut)[0])

    uu = [{"post_date": "2026-10-20T09:00"}, {"post_date": "2026-11-02"}]          # latest cutoff 2026-11-01
    check("FSG16 لا حكمَ قبل لقطةٍ جُلبت بعد آخر t' (§⑦): قبلها أو عندها ⟵ لا · بعدها ⟵ نعم",
          [bars_ready([("2026-10-25", "a", {})], uu), bars_ready([("2026-11-01", "a", {})], uu), bars_ready([("2026-11-02", "a", {})], uu),
           bars_ready([], [])] == [False, False, True, True])
    _ast = ast.parse(inspect.getsource(sys.modules[__name__]))
    _an = next(n for n in _ast.body if isinstance(n, ast.FunctionDef) and n.name == "cmd_analyze")
    _calls = sorted((c.lineno, getattr(c.func, "id", None) or getattr(c.func, "attr", None)) for c in ast.walk(_an) if isinstance(c, ast.Call))
    _first = {nm: min((ln for ln, c in _calls if c == nm), default=None) for nm in ("bars_ready", "_mods", "dump")}
    check("FSG16 التحليلُ يسأل عن اللقطة قبل أن يحسب أو يكتب", None not in _first.values()
          and _first["bars_ready"] < _first["_mods"] and _first["bars_ready"] < _first["dump"], _first)
    reads = []
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            check_merged(read=lambda: reads.append(1) or b"other")
            rc = 0
        except SystemExit as ex:
            rc = ex.code
    check("FSG13 بلا العقد المثبَّت على main ⟵ خروج 9 (والقراءةُ من main حصلت)", rc == 9 and reads == [1], (rc, reads))

    import tempfile
    mod = sys.modules[__name__]
    keep = {k: getattr(mod, k) for k in ("META", "IMG_DIR", "LEDGER", "RESULT", "check_merged", "_now")}
    beh = {}
    with tempfile.TemporaryDirectory() as td:
        try:
            os.makedirs(os.path.join(td, "img"))
            tm = []
            for n, body, col in (("TG_20.jpg", b"p20", "2026-10-16T00:00:00Z"), ("TG_21.jpg", b"p21", "2026-10-21T00:00:00Z")):
                open(os.path.join(td, "img", n), "wb").write(body)
                tm.append({"saved_name": n, "status": "saved", "collected_utc": col, "sha256": hashlib.sha256(body).hexdigest()})
            open(os.path.join(td, "meta.jsonl"), "w").write("\n".join(json.dumps(m) for m in tm) + "\n")
            mod.META, mod.IMG_DIR = os.path.join(td, "meta.jsonl"), os.path.join(td, "img")
            mod.LEDGER, mod.RESULT = os.path.join(td, "L.jsonl"), os.path.join(td, "R.json")
            mod.check_merged = lambda read=None: None
            mod._now = lambda: "2026-10-20T00:00:00Z"

            def n_rows():
                return len(load_jsonl(mod.LEDGER))
            with contextlib.redirect_stdout(io.StringIO()):
                beh["ok"] = (main(["triage", "--image", "TG_20.jpg", "--decision", "NONE"]), n_rows())
                _b = io.StringIO()
                with contextlib.redirect_stdout(_b):
                    beh["twice"] = (main(["triage", "--image", "TG_20.jpg", "--decision", "UNREADABLE"]), n_rows(),
                                    "use `correct`" in _b.getvalue())
                beh["future"] = (main(["triage", "--image", "TG_21.jpg", "--decision", "NONE"]), n_rows())
                beh["correct"] = (main(["correct", "--seq", "1", "--decision", "UNREADABLE"]), n_rows())
                open(mod.RESULT, "w").write(json.dumps({"ledger_len": 2}))
                beh["after"] = (main(["correct", "--seq", "1", "--decision", "NONE"]), n_rows())
                beh["verify"] = main(["verify"])
        except Exception as ex:                      # noqa: BLE001
            beh["crash"] = f"{type(ex).__name__}: {ex}"
        finally:
            for k, v in keep.items():
                setattr(mod, k, v)
    check("FSG15 سلوكيًّا: الفرزُ يُلحق صفًّا · ومرّتين يُرفض ويُحال للتصحيح · وصفٌّ يكسر السجلّ لا يُكتب · والتصحيحُ يُلحق ويُمنع بعد التحليل",
          beh == {"ok": (0, 1), "twice": (9, 1, True), "future": (9, 1), "correct": (0, 2), "after": (9, 2), "verify": 0}, beh)

    src = inspect.getsource(sys.modules[__name__])
    tree = ast.parse(src)
    fdefs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}

    def names_in(fn):
        return {getattr(x, "attr", None) or getattr(x, "id", None) for x in ast.walk(fdefs[fn])}
    check("FSG14 موصولٌ: التحليلُ ينادي العمقَ الحرّ والقفزةَ والإطار ودورةَ الإنتاج بالاسم ويفحص البصمات والدمج",
          {"depth_window", "jumps", "frame", "pivot_cycle_state", "check_pins", "check_merged", "classify"} <= names_in("cmd_analyze"))
    check("FSG14 الحالةُ والتحقّقُ والانتظار لا يقرأون شموعًا ولا عمقًا (عدٌّ فقط)",
          not ({"_mods", "_snapshots", "classify", "depth_window"} & (names_in("cmd_status") | names_in("cmd_verify") | names_in("cmd_pending"))))
    check("FSG14 الفرزُ والتصحيحُ يشترطان الدمج", "check_merged" in names_in("cmd_triage") and "check_merged" in names_in("cmd_correct"))
    print(f"\n{'✅ الحرّاس كلُّهم' if not bad else '❌ سقط: ' + ' · '.join(bad)}")
    return bad


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--guards" in argv:
        return 1 if guards() else 0
    ap = argparse.ArgumentParser(prog="fsweep.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for c in ("pending", "verify", "status", "analyze"):
        sub.add_parser(c)
    for c in ("triage", "correct"):
        p = sub.add_parser(c)
        if c == "triage":
            p.add_argument("--image", required=True)
        else:
            p.add_argument("--seq", type=int, required=True)
        p.add_argument("--decision", required=True, choices=DECISIONS)
        p.add_argument("--symbol")
        p.add_argument("--post-date", dest="post_date")
        p.add_argument("--date-source", dest="date_source", choices=DATE_SOURCES)
        p.add_argument("--kind", choices=KINDS)
        p.add_argument("--author", choices=AUTHORS)
        p.add_argument("--base", type=float)
        p.add_argument("--low", type=float)
        p.add_argument("--pct", type=float)
        p.add_argument("--quote")
        p.add_argument("--note")
    a = ap.parse_args(argv)
    return {"pending": cmd_pending, "triage": cmd_triage, "correct": cmd_correct, "verify": cmd_verify, "status": cmd_status,
            "analyze": cmd_analyze}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
