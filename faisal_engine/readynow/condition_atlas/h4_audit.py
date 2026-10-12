"""Historical 4H readiness reconstruction — source audit, rule tracing, case linkage and the evidence gap (research only).

Question: can the artifacts already stored in the repository reconstruct Faisal's four-hour readiness conditions at
T−10…T−7 before an explosive move, and test whether they add information beyond the daily baselines?

  python3 faisal_engine/readynow/condition_atlas/h4_audit.py            build data/h4_audit.json and the four reports
  python3 faisal_engine/readynow/condition_atlas/h4_audit.py --check    rebuild in memory and compare (exit 1 on drift)

Read-only on every input (listed in SOURCES, SHA-256 recorded in the output) · no network · no production import ·
faisal_engine/readynow/fwd/ is never opened. Writes only data/h4_audit.json and the four HISTORICAL_4H_* / FAISAL_4H_* files.
"""
import bisect
import csv
import glob
import gzip
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
DATA = os.path.join(HERE, "data")
OUT_JSON = os.path.join(DATA, "h4_audit.json")
NY = ZoneInfo("America/New_York")

SOURCES = {   # every file this audit reads (relative to the repository root)
    "register": "fm_forensics/reread/data/reread_records.jsonl",
    "image_dates": "faisal_image_dates.tsv",
    "telegram_meta": "telegram_collect_meta.jsonl",
    "events": "faisal_engine/readynow/disc/data/events.csv.gz",
    "calendar": "faisal_engine/readynow/data/calendar.json",
    "rank_bars": "faisal_engine/data/rank/bars.json.gz",
    "rank_splits": "faisal_engine/data/rank/splits.json",
    "fm_bars": "fm_forensics/data/bars_2026-10-08.json.gz",
    "golden": "faisal_method_v3/v31/golden_fixtures.json",
    "cov30": "faisal_method_v4/results/v4_cov30.json",
    "hubc_card": "chart_cards/blind/2026-10-07/owner-2026-10-07-1.json",
    "hubc_result": "chart_cards/blind/2026-10-07/RESULT.md",
    "cards_real_key": "chart_cards/real/KEY.tsv",
    "cards_real2_key": "chart_cards/real2/KEY.tsv",
    "alerts70": "faisal_engine/alerts70/data/alerts.csv.gz",
    "presession": "presession_ledger.jsonl",
    "phase6": "fm_forensics/phase6/data/PHASE6_LEDGER.jsonl",
    "phase4_audit": "fm_forensics/phase4/DATA_AVAILABILITY_AUDIT.csv",
    "image_inventory": "faisal_recovery/HISTORICAL_IMAGE_INVENTORY.csv",
    "h4_result": "h4_result.md",
    "strength_dev": "faisal_engine/readynow/condition_atlas/data/strength_dev.json",
    "reconcile": "faisal_engine/readynow/condition_atlas/data/reconcile.json",
    "atlas_verdict": "faisal_engine/readynow/condition_atlas/data/verdict.json",
}
P = {k: os.path.join(ROOT, v) for k, v in SOURCES.items()}
SEEDS = ("DLXY", "RETO", "DKI", "SXTC")
ACTIVE = ("HUBC",)
WINDOWS = ("development", "validation", "holdout")

# Price-anchor rules — the project's own (`faisal_price_anchor.py`, 2026-09-19): `ah` ⇒ that day's regular close =
# price ÷ (1 + pct) · `pre` ⇒ the previous regular close = price ÷ (1 + pct) · tolerance 0.75% · a date only when exactly
# one session matches. Applied here offline on the local split-adjusted daily bars (raw = adjusted × later split ratios).
ANCHOR_TOL = 0.75
ANCHOR_W0 = "2025-01-01"
KIND = {"بعد الإغلاق": "ah", "أفتر": "ah", "افتر": "ah", "التداول الليليّ": "ah", "قبل الافتتاح": "pre", "بري": "pre"}
RX_QUOTE = re.compile(r"(بعد الإغلاق|أفتر|افتر|التداول الليليّ|قبل الافتتاح|بري)\s*(\d+\.\d+)\s*[‏‎]?\s*"
                      r"([+\-−‑])\s*(\d+(?:\.\d+)?)%")
H4_ANY = re.compile(r"(4س|4 ?ساع|٤ ?ساع|4H|اربع ساع|أربع ساع)")
H4_FIELD_ONLY = re.compile(r"(أعلى أول 4 ساعات|أعلى أوّل 4 ساعات|أوّل 4 ساعات|أول 4 ساعات|اكتمال أعلى 4H|تأكيد 4H|"
                           r"تأكيدُ 4H|و4H|4H «اختبار ناجح»|RSI 4H|MACD 4H)")
# 4H grids. G_APP: the app split inferred for HUBC (RESULT.md) — four-hour steps anchored on the 09:30 open, cut by the
# extended session. G_NY: calendar buckets 04/08/12/16 (T-H4's convention, closed). Boundaries in NY minutes from 00:00.
GRIDS = {"G_APP": (240, 330, 570, 810, 1050, 1200), "G_NY": (240, 480, 720, 960, 1200)}
# What each closed axis forbids here (DECISIONS_ARCHIVE / *_result.md); none is reopened by this audit.
CLOSED = {
    "T-H4": "4H bucket arms (D0/H1) and the NY 04/08/12/16 convention — closed «اقفل T-H4» 2026-08-28; reopen needs a "
            "session-anchored 4H source + evidence it is Faisal's frame + a new prereg (h4_result.md)",
    "T-SUPDEF": "support-definition tests — closed «اقفل الدعم» 2026-09-19 (SUPDEF_REOPEN)",
    "T-CANDLE": "reversal-candle signals — failed 0/6 (candle_result.md) and treated as a closed selection axis since",
    "T-TRAIL": "exit/target management — closed (TRAIL_REOPEN)",
}


# ───────────────────────── small helpers ─────────────────────────
def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[‎‏​]", "", s or "")).strip()


def rd_csv(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_register():
    best = {}
    for line in open(P["register"], encoding="utf-8"):
        r = json.loads(line)
        if r["id"] not in best or r.get("rev", 0) >= best[r["id"]].get("rev", 0):
            best[r["id"]] = r
    return best


class Cal:
    def __init__(self):
        self.s = json.load(open(P["calendar"], encoding="utf-8"))["sessions"]
        self.i = {d: k for k, d in enumerate(self.s)}

    def last_on_or_before(self, day):
        k = bisect.bisect_right(self.s, day) - 1
        return k if k >= 0 else None

    def back(self, day, n):
        k = self.i.get(day)
        return self.s[k - n] if k is not None and k - n >= 0 else None


# ───────────────────────── ① the eye-read register: which images carry 4H content ─────────────────────────
def h4_class(r):
    """CHART: the eye-read description says the image shows a four-hour chart · TEXT: the quoted words, meaning or rule
    mention the four-hour frame · FIELD: only an app field («أعلى أول 4 ساعات», «تأكيد 4H») mentions it."""
    seen = H4_FIELD_ONLY.sub("", r["seen"])
    chart = bool(re.search(r"(4 ساعات|أربع ساعات|اربع ساعات|٤ ساعات)", seen))
    words = H4_FIELD_ONLY.sub("", " ".join((r["q"], r["mean"], r["rule"])))
    text = bool(H4_ANY.search(words)) or (not chart and bool(H4_ANY.search(seen)))
    field = bool(H4_FIELD_ONLY.search(" ".join((r["seen"], r["q"]))))
    return [c for c, ok in (("CHART", chart), ("TEXT", text), ("FIELD", field)) if ok]


def upper_bounds(reg):
    """Capture/upload upper bounds: EXIF capture date, batch-name date, Telegram send date (never a market date)."""
    ub = {}
    for row in csv.DictReader(open(P["image_dates"], encoding="utf-8"), delimiter="\t"):
        if row.get("source") in ("exif", "filename") and row.get("date"):
            ub[row["image"].rsplit(".", 1)[0]] = (row["date"], row["source"])
    for line in open(P["telegram_meta"], encoding="utf-8"):
        m = json.loads(line)
        if m.get("saved_name"):
            k = m["saved_name"].rsplit(".", 1)[0]
            d = (m.get("date") or "")[:10]
            if d and (k not in ub or d < ub[k][0]):
                ub[k] = (d, "telegram_send")
    return {k: v for k, v in ub.items() if k in reg}


def card_axis():
    """Month/day axis labels pixel-read on the frozen chart cards (lower bound for the right edge, year not shown)."""
    out = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "chart_cards", "*", "*.json"))):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except (ValueError, OSError):
            continue
        if isinstance(d, dict) and d.get("axis_md"):
            img = d.get("id", "").split("-", 1)[-1]
            out[img] = {"card": os.path.relpath(f, ROOT), "timeframe": d.get("timeframe"), "axis_md": d["axis_md"]}
    return out


# ───────────────────────── ② dating: visible date · MD + bound · local price anchor ─────────────────────────
class Anchor:
    def __init__(self):
        self.bars = json.load(gzip.open(P["rank_bars"], "rt", encoding="utf-8"))["daily"]
        self.spl = json.load(open(P["rank_splits"], encoding="utf-8"))["splits"]

    def later(self, sym, day):
        f = 1.0
        for d, r in self.spl.get(sym, []):
            if d > day:
                f *= r
        return f

    def match(self, sym, kind, px, pct, w0, w1):
        bars = self.bars.get(sym)
        if not bars:
            return "no_data", []
        ref = px / (1 + pct / 100.0)
        hits = []
        for b in bars:
            if w0 <= b[0] <= w1:
                raw = b[4] * self.later(sym, b[0])
                err = abs(raw - ref) / ref * 100.0
                if err <= ANCHOR_TOL:
                    hits.append([b[0], round(raw, 4), round(err, 3)])
        return ("unique" if len(hits) == 1 else "ambiguous" if hits else "none"), hits


def quote_of(r):
    m = RX_QUOTE.search(r["seen"])
    if not m:
        return None
    sign = -1 if m.group(3) in "-−‑" else 1
    return {"kind": KIND[m.group(1)], "label": m.group(1), "px": float(m.group(2)), "pct": sign * float(m.group(4))}


def date_image(r, ub, axis, anc, cal_last):
    """The defensible decision date of one image, with the evidence ladder recorded (never a file time alone)."""
    out = {"visible": None, "md": None, "upper": ub.get(r["id"]), "axis_lower": None, "anchor": None,
           "decision": None, "basis": "UNDATED"}
    if r["dprec"] in ("EXACT", "DAY"):
        out["visible"] = r["date"][:10]
        out["decision"], out["basis"] = r["date"][:10], "VISIBLE_DATE"
        return out
    upper = out["upper"][0] if out["upper"] else None
    if r["dprec"] == "MD":
        out["md"] = r["date"][:5]
        if upper:
            y = int(upper[:4])
            cand = f"{y}-{out['md']}"
            if cand > upper:
                cand = f"{y - 1}-{out['md']}"
            out["decision"], out["basis"] = cand, "VISIBLE_MONTH_DAY+UPLOAD_BOUND"
            return out
        out["basis"] = "VISIBLE_MONTH_DAY_NO_YEAR"
        return out
    if r["dprec"] == "MONTH":
        out["basis"] = "VISIBLE_MONTH_ONLY"
        return out
    ax = axis.get(r["id"])
    lower = None
    if ax:
        y = upper[:4] if upper else "2026"
        lower = max(f"{y}-{x.replace('/', '-')}" for x in ax["axis_md"])
        out["axis_lower"] = lower
        if upper and lower > upper:          # the axis label is later than the capture/upload bound: no defensible date
            out["basis"] = "CONTRADICTORY_BOUNDS"
            return out
    q = quote_of(r)
    if q and len(r["tk"]) == 1:
        st, hits = anc.match(r["tk"][0], q["kind"], q["px"], q["pct"], max(ANCHOR_W0, lower or ANCHOR_W0),
                             upper or cal_last)
        out["anchor"] = dict(q, sym=r["tk"][0], status=st, n_hits=len(hits), hits=hits[:6],
                             window=[max(ANCHOR_W0, lower or ANCHOR_W0), upper or cal_last])
        if st == "unique":
            out["decision"], out["basis"] = hits[0][0], "LOCAL_PRICE_ANCHOR(unique)"
            return out
    out["basis"] = "UPLOAD_BOUND_ONLY" if upper else ("AXIS_LOWER_BOUND_ONLY" if lower else "UNDATED")
    return out


# ───────────────────────── ③ episodes and the link of a decision date to them ─────────────────────────
def load_events():
    ev = defaultdict(list)
    for e in rd_csv(P["events"]):
        ev[e["sym"]].append(e)
    return ev


def intraday_only(cal, bars, eps, k0, k1):
    """Sessions in [k0, k1] whose daily high is ≥ 70% over the prior close outside every detected episode — an intraday
    threshold event, kept apart from the daily-close episodes."""
    if not bars:
        return []
    by = {b[0]: b for b in bars}
    spans = []
    for e in eps:
        o = cal.i.get(e["onset"])
        if o is not None:
            spans.append((o, max(cal.i.get(x, o) for x in (e["peak"], e["d1"], e["q"]) if x)))
    out = []
    for k in range(max(1, k0), min(k1, len(cal.s) - 1) + 1):
        b, p = by.get(cal.s[k]), by.get(cal.s[k - 1])
        if b and p and p[4] > 0 and b[2] / p[4] - 1 >= 0.70 and not any(a <= k <= z for a, z in spans):
            out.append({"session": cal.s[k], "sessions_after": k - k0 + 1,
                        "high_vs_prior_close_pct": round((b[2] / p[4] - 1) * 100, 1),
                        "close_vs_prior_close_pct": round((b[4] / p[4] - 1) * 100, 1)})
    return out


def relation(cal, eps, day, bars=None):
    """Position of a decision session relative to every episode of the symbol (all qualities; IN_EVENT wins)."""
    k = cal.last_on_or_before(day)
    if k is None:
        return {"status": "BEFORE_CALENDAR"}
    dec = cal.s[k]
    rel = []
    for e in eps:
        o = cal.i.get(e["onset"])
        if o is None:
            continue
        end = max(cal.i.get(x, o) for x in (e["peak"], e["d1"], e["q"]) if x)
        if o <= k <= end:
            rel.append(("IN_EVENT", e))
        elif k < o:
            rel.append((o - k, e))
    ahead = sorted((x for x in rel if x[0] != "IN_EVENT"), key=lambda x: x[0])
    clean = [x for x in ahead if x[1]["quality"] == "OK"]
    if any(x[0] == "IN_EVENT" for x in rel):
        e = next(x[1] for x in rel if x[0] == "IN_EVENT")
        nxt = {"next_clean_onset": clean[0][1]["onset"], "sessions_to_next_clean_onset": clean[0][0]} if clean else {}
        return {"decision_session": dec, "status": "IN_EVENT", "episode": f"{e['sym']}|{e['onset']}",
                "quality": e["quality"], **nxt}
    if not clean:
        st = "CENSORED_LT10_SESSIONS_AFTER" if k + 10 > len(cal.s) - 1 else "NO_LATER_CLEAN_EPISODE"
        return {"decision_session": dec, "status": st, "sessions_of_data_after": len(cal.s) - 1 - k,
                "intraday_only_within_10": intraday_only(cal, bars, eps, k + 1, k + 10)}
    n, e = clean[0]
    st = "T7_10" if 7 <= n <= 10 else ("T1_6" if n <= 6 else ("T11_30" if n <= 30 else "T31_PLUS"))
    between = [x for x in ahead if x[0] < n]
    return {"decision_session": dec, "status": st, "sessions_to_onset": n, "episode": f"{e['sym']}|{e['onset']}",
            "onset": e["onset"], "q": e["q"], "x70": e["x70"], "d1": e["d1"], "kind": e["kind"],
            "earlier_episode_in_between": [f"{x[1]['sym']}|{x[1]['onset']}" for x in between]}


# ───────────────────────── ④ the intraday bar stores ─────────────────────────
def ny(ms):
    return datetime.fromtimestamp(ms / 1000, timezone.utc).astimezone(NY)


def bucket(minute, grid):
    b = GRIDS[grid]
    for k in range(len(b) - 1):
        if b[k] <= minute < b[k + 1]:
            return k
    return None


def grid_ok(bar_minutes, step, grid):
    """A grid is constructible from bars of length `step` when no bar straddles a grid boundary."""
    for m in bar_minutes:
        for edge in GRIDS[grid][1:-1]:
            if m < edge < m + step:
                return False
    return True


def bar_stores(cal, ev):
    fm = json.load(gzip.open(P["fm_bars"], "rt", encoding="utf-8"))
    g = json.load(open(P["golden"], encoding="utf-8"))
    stores = []
    for sym, rows in sorted(fm["hourly"].items()):
        days = defaultdict(list)
        for r in rows:
            t = ny(r[0])
            days[t.date().isoformat()].append(t.hour * 60 + t.minute)
        stores.append({"store": SOURCES["fm_bars"] + " · hourly", "sym": sym, "fields": "ts, high, low (no open, close, "
                       "volume)", "step": 60, "first": min(days), "last": max(days), "rows": len(rows),
                       "sessions": len(days), "days": days, "ohlc": False,
                       "provenance": "TradingView, split-adjusted, extended hours (bars seen 04:00–19:00 NY), the "
                                     "1,000 most recent bars per symbol, collected " + fm["meta"]["utc"]})
    for key, label in (("m30", "regular"), ("m30x", "extended")):
        for sym, rows in g[key].items():
            days = defaultdict(list)
            for r in rows:
                hh, mm = int(r[0][11:13]), int(r[0][14:16])
                days[r[0][:10]].append(hh * 60 + mm)
            stores.append({"store": SOURCES["golden"] + f" · {key}", "sym": sym, "fields": "ts, open, high, low, "
                           "close, volume", "step": 30, "first": min(days), "last": max(days), "rows": len(rows),
                           "sessions": len(days), "days": days, "ohlc": True,
                           "provenance": f"30-minute {label} bars ending at Faisal's DXST post time "
                                         f"({g['dates'][sym]['how']})"})
    out = []
    for s in stores:
        mins = [m for v in s["days"].values() for m in v]
        grids = {gname: grid_ok(mins, s["step"], gname) for gname in GRIDS}
        eps = []
        for e in ev.get(s["sym"], []):
            w = [cal.back(e["onset"], k) for k in (10, 9, 8, 7)]
            if None in w:
                continue
            per = []
            for d in w:
                ms = s["days"].get(d, [])
                per.append({"session": d, "bars": len(ms),
                            **{f"{gname}_buckets": (len({bucket(m, gname) for m in ms} - {None}) if grids[gname]
                                                    else None) for gname in GRIDS},
                            **{f"{gname}_of": len(GRIDS[gname]) - 1 for gname in GRIDS}})
            if not any(s["first"] <= d <= s["last"] for d in w):      # the T−10…T−7 window is outside the store
                continue
            eps.append({"episode": f"{e['sym']}|{e['onset']}", "quality": e["quality"], "kind": e["kind"],
                        "onset": e["onset"], "q": e["q"], "x70": e["x70"], "d1": e["d1"],
                        "window_T10_T7": per, "sessions_with_bars": sum(1 for p in per if p["bars"])})
        out.append({k: v for k, v in s.items() if k != "days"} | {"grids_constructible": grids, "episodes": eps})
    return out


def cov30_note():
    d = json.load(open(P["cov30"], encoding="utf-8"))
    cov = d.get("coverage", {})
    ok = sorted(s for s, v in cov.items() if v.get("regular"))
    first = sorted(v["regular"]["first"][:10] for v in cov.values() if v.get("regular"))
    return {"run": d.get("_source_run"), "symbols_requested": len(cov), "symbols_returned": len(ok),
            "oldest_regular_bar": first[0] if first else None, "bars_stored_locally": False,
            "note": "coverage metadata only (first/last/count per symbol); the 30-minute bars were not saved"}


# ───────────────────────── ⑤ the atlas population: who could be evaluated at T−10…T−7 ─────────────────────────
def population(stores):
    sys.path.insert(0, HERE)
    import ca_lib as L                                                    # noqa: E402
    import rn_disc_dev as D                                               # noqa: E402
    cover = defaultdict(list)
    for s in stores:
        cover[s["sym"]].append((s["first"], s["last"], s["ohlc"]))
    rec = json.load(open(P["reconcile"], encoding="utf-8"))["R5"]
    out = {}
    for w in WINDOWS:
        rows, _by, _m = L.load(w)
        events, _six = D.events(rows, w)
        elig = [e for e in events if e["pos_rows"]]
        lab = Counter(r["lab"] for r in rows)
        cov_rows = [r for r in rows if any(a <= r["t"] <= b for a, b, _o in cover.get(r["sym"], []))]
        cov_ohlc = [r for r in rows if any(a <= r["t"] <= b and o for a, b, o in cover.get(r["sym"], []))]
        e_cov = sorted({f"{e['sym']}|{e['launch']}" for e in elig
                        if any(any(a <= r["t"] <= b for a, b, _o in cover.get(r["sym"], [])) for r in e["pos_rows"])})
        e_ohlc = sorted({f"{e['sym']}|{e['launch']}" for e in elig
                         if any(any(a <= r["t"] <= b and o for a, b, o in cover.get(r["sym"], []))
                                for r in e["pos_rows"])})
        missed6 = rec[w]["top6_missed"]
        out[w] = {"pivot_days": len(rows), "labels": dict(sorted(lab.items())), "eligible_events": len(elig),
                  "eligible_events_reconcile": rec[w]["eligible"], "captured_by_ready": rec[w]["captured_by_ready"],
                  "missed": rec[w]["missed"],
                  "rows_with_any_intraday_bar": len(cov_rows),
                  "rows_with_any_intraday_bar_by_label": dict(sorted(Counter(r["lab"] for r in cov_rows).items())),
                  "rows_with_intraday_ohlc": len(cov_ohlc),
                  "pos710_rows_with_intraday_ohlc": sum(1 for r in cov_ohlc if r["lab"] == "POS710"),
                  "neg_rows_with_intraday_ohlc": sum(1 for r in cov_ohlc if r["lab"] == "NEG"),
                  "symbols_with_intraday_bar": sorted({r["sym"] for r in cov_rows}),
                  "eligible_events_with_any_intraday_bar": e_cov, "eligible_events_with_intraday_ohlc": e_ohlc,
                  "top6_missed": [{"sym": x["sym"], "onset": x["onset"], "peak_gain": x["peak_gain"]}
                                  for x in missed6]}
    return out


# ───────────────────────── ⑥ Faisal's 4H conditions — verbatim, interpretation, hypothesis kept apart ─────────────────────────
RULES = [
    dict(id="R4H-1", name="holding together at the lowest low on 4H", purpose="technical strength (readiness state)",
         src=[("IMG_0177", "هنا بيكون ع فريم 4 ساعات متماسك عند ادنى قاع"),
              ("IMG_0177", "قبل يصعد لازم يكون فيه ضغط او مسح سيوله 10٪ تحت القاع")],
         numbers="none for «متماسك» · 10% is the sweep depth, not a 4H width",
         interpretation="before the rise the 4H candles stay compact at the base low; the rise is preceded by "
                        "pressure or a ~10% sweep below the low",
         calc="none given in the source",
         hypothesis="HYPOTHESIS ONLY: no 4H close below the base low over the last N 4H candles and a 4H range "
                    "width under W — N and W are not in the source",
         data="4H OHLC (close needed) around the base for T−10…T−7, positives and matched controls",
         proxies=["B05_HOLD3", "B05b_HOLD5", "B09_TIGHT_NEAR_LOW"]),
    dict(id="R4H-2", name="supports measured on 4H and daily · lowest candle unbroken for 5 sessions on all frames",
         purpose="pivot validity / technical strength",
         src=[("X_20260827_checklist_7points", "مع قياس الدعوم ع فريم 4 ساعات و يومي مع قرآة الشموع"),
              ("X_20260827_checklist_7points", "يبقى لك ادنى شمعه هبط لها السهم 5 جلسات هل كسرها اولا ع جميع الفريمات")],
         numbers="5 sessions (explicit)",
         interpretation="the exact low is read on the 4H frame as well as the daily, and must hold for 5 sessions",
         calc="lowest 4H low of the base not broken during the following 5 sessions (lows only)",
         hypothesis="the reference low (which candle) is the stock's new low; the sessions are daily sessions — "
                    "both read from the example, not stated as a definition",
         data="4H or hourly lows (extended hours) — lows suffice", proxies=["B05b_HOLD5", "B05_HOLD3"]),
    dict(id="R4H-3", name="free of groups (readable candles; no bodiless ~20% 4H candles)",
         purpose="restrict risky entries / validity — not a timing signal",
         src=[("X_20260827_checklist_7points", "سهم جاهز محافظ ع تذبذب نقاط 10٪ حد اقصى"),
              ("X_20260827_checklist_7points", "القروبات ترفع السهم بشموع غبيه توصل 20٪ تجد شمعه طويله خضرا او حمرا "
                                               "بدون جسم ع فريم 4 ساعات"),
              ("IMG_0151", "الشرط خالي من القروبات"),
              ("IMG_0488", "دخول سيوله قروبات او غيره لا انا ولا اكبر محلل يستطيع قراءة الشموع"),
              ("X_20260827_labt_supports_wait", "شمعة غبيه بعد تحليلنا السابق")],
         numbers="20% (how far a group candle reaches) · 10% (maximum oscillation of a ready stock) · «بدون جسم» "
                 "has no number",
         interpretation="a long green or red 4H candle without a body, reaching about 20%, marks group activity; a "
                        "ready stock oscillates 10% at most; group entry makes the candles unreadable",
         calc="none — the 20% has no stated base (open, prior close, low?) and «بدون جسم» no body ratio",
         hypothesis="HYPOTHESIS ONLY: a 4H candle with range ≥ 20% of the prior 4H close and body ≤ X% of its range "
                    "(X not in the source; the atlas's daily proxy used 25%)",
         data="4H OHLC (body needs open and close) on the same grid Faisal reads",
         proxies=["I04_GROUP_PROXY", "A11_NO_GROUP_PROXY", "B09_TIGHT_NEAR_LOW"]),
    dict(id="R4H-4", name="4H rise in the after-hours or pre-market", purpose="upcoming timing",
         src=[("X_20260827_checklist_7points", "فريم 4 ساعات هل له صعود افتر بري او لا")],
         numbers="none", interpretation="whether the extended-hours 4H candles already show a rise",
         calc="none given", hypothesis="HYPOTHESIS ONLY: an extended-hours 4H candle closing ≥ R% above the prior "
                                       "regular close (R not in the source)",
         data="extended-hours 4H OHLC for the population (pre-market and after-hours)", proxies=[]),
    dict(id="R4H-5", name="a falling 4H candle waits for the daily to test it", purpose="timing (WAIT) / levels",
         src=[("TG_1815", "اذا كان فيه شمعه ساقطه ع 4 ساعات انتظر يختبرها فريم يومي"),
              ("TG_50587", "لما تشوف شمعه ساقطه ع فريم 4 ساعات انتظر السهم يختبرها"),
              ("TG_50832", "لكل شمعه حمرا ذيل وراس الذيل مقاومه الراس هدف")],
         numbers="none for «ساقطة» · TG_50832's 25% per candle is a target (exit axis, closed)",
         interpretation="a falling (red, gapped-down) 4H candle is a level the price is expected to come back to; "
                        "act after the daily tests it",
         calc="none — «شمعة ساقطة» is not defined numerically",
         hypothesis="HYPOTHESIS ONLY: the head/tail of the last large red 4H candle above price as the next level",
         data="4H OHLC", proxies=["B22_MA20_FLAT"]),
    dict(id="R4H-6", name="the head of the falling 4H candle turns from resistance into support (not broken)",
         purpose="levels / entry location", closed="T-SUPDEF",
         src=[("TG_1860", "تحدد الشموع ع فريم 4 ساعات · ترجع للشمعه السابقه · تجد شمعة الهبوط راسها 4.71 تعتبر مقاومه"),
              ("TG_1860", "كانت مقاومه تحولت لدعم · لم يكسرها السهم"),
              ("IMG_0319", "الشمعه واضحه المقاومه ع فريم 4 ساعات 2.87 شمعة ساقطه سابقا"),
              ("TG_1858", "يحول الفريم ع 4 ساعات 2 مفترض مايرجع لها كدعم اساسي 2.20 دعم فرعي"),
              ("IMG_0698", "فريم 4 ساعات دعم 2 اذا كسرها بيروح تحت")],
         numbers="price examples only (4.71, 2.87, 2, 2.20)",
         interpretation="levels are taken from 4H candles: a prior falling candle's head is resistance, then support "
                        "once reclaimed; a break of the 4H support means a deeper fall",
         calc="none general", hypothesis="a support definition — testing it would be a support-definition test "
                                         "(closed axis T-SUPDEF)",
         data="4H OHLC", proxies=["B07_RETEST", "B18_TOUCHES"]),
    dict(id="R4H-7", name="a hammer at the 4H low", purpose="confirmation", closed="T-CANDLE",
         src=[("IMG_0569", "جسم شمعة القاع 1.50 بدون راس · تسمى مطرقه او همر"),
              ("IMG_0569", "ع فريم 4 ساعات الشرح"),
              ("TG_1824", "ادنى قاع 2.08 = ع فريم 4 ساعات شمعة همر صاعده")],
         numbers="none", interpretation="the base candle on 4H is a hammer (bottom body without a head)",
         calc="the shape only (no ratios in the source)", hypothesis="body/wick ratios are the bot's, not Faisal's",
         data="4H OHLC", proxies=["K01_HAMMER", "K02_RED_HAMMER", "B20_CANDLE_AT_SUPPORT"]),
    dict(id="R4H-8", name="a sweep shown by a 4H wick below the base, then back above the support",
         purpose="upcoming timing / strength",
         src=[("TG_1822", "فريم 4 ساعات ذيل شمعة 1.30 ( مسح سيولة )"),
              ("TG_1822", "سحب السيوله اسفل الشمعه 10٪ تقريبا ورجع صعد فوق الدعم"),
              ("TG_20260918_38_NUWE", "هنا تتابع القاع 69 سنت ع 4 ساعات ع يومي يختلف 71 سنت")],
         numbers="~10% (EHGO example) · the project's 7–13% band is from IMG_0297 (not a 4H statement)",
         interpretation="the sweep is seen as a 4H wick under the base and a return above the support; the 4H low "
                        "can differ from the daily low",
         calc="4H low below the base by about 10%, then a 4H close back above the support",
         hypothesis="the depth band and the reclaim horizon are not given for 4H",
         data="4H lows and closes (a close is needed for the reclaim)", proxies=["B08_SWEEP"]),
    dict(id="R4H-9", name="targets set on the 4H (and daily) falling candles", purpose="exit / targets",
         closed="T-TRAIL",
         src=[("TG_1860", "الاهداف تحددها ع فريم يومي + 4 ساعات"),
              ("TG_1969", "تقرر الاهداف ع فريم 4 ساعات شمعة الهدف 2.18 = شمعة الهبوط"),
              ("TG_50830", "فريم 4 ساعات الاهداف مشروط بفريم 5 دقايق"),
              ("TG_2196", "شمعه 4 ساعات عنده هدف 10")],
         numbers="price examples only", interpretation="targets, not readiness — outside this question",
         calc="displayed by the bot (red-candle heads on 4H)", hypothesis="—", data="—", proxies=[]),
]
NON_FAISAL = [   # kept apart: app output and third-party material (never Faisal's rule)
    dict(id="APP-1", who="app (A)", src=[("TG_57917", "اليومي يحدد الدورة و4H يؤكد توقيت الدعم"),
                                          ("TG_58401", "تأكيد 4H اختبار ناجح"),
                                          ("TG_57876", "الزخم اليومي و4H لم يتحسن بعد")],
         note="the app's design: daily for the cycle, 4H for the support timing; its «تأكيد 4H» chip has no stated "
              "formula"),
    dict(id="APP-2", who="third-party app (A)", src=[("TG_58420", "الشروط الفنية على فريم 4 ساعات")],
         note="eight weighted conditions on 4H (RSI from the daily); measured as daily proxies in the atlas, never Faisal's"),
    dict(id="APP-3", who="app (A)", src=[("TG_57912", "أعلى أول 4 ساعات $6.00")],
         note="split-day card: the first 4-hour high after a reverse split as a target zone (displayed by the bot)"),
    dict(id="EDU-1", who="third-party channel (T)", src=[("EDU_20260827_dki_group_candle", "شمعة قروب الشكوى لله")],
         note="the phrase «شمعة قروب» is a channel's caption on a DKI intraday spike (4.07 → 5.05 and back) — not "
              "Faisal's definition; his rule is R4H-3"),
]


def verify_quotes(reg):
    """Every excerpt must be a substring of the register's quote or description of that image (verbatim check)."""
    bad = []
    for grp in (RULES, NON_FAISAL):
        for x in grp:
            for img, ex in x["src"]:
                r = reg.get(img)
                hay = norm(" ".join((r["q"], r["seen"]))) if r else ""
                if norm(ex) not in hay:
                    bad.append((x["id"], img, ex))
    return bad


def rule_rows(reg, strength):
    out = []
    for x in RULES:
        src = []
        for img, ex in x["src"]:
            r = reg[img]
            src.append({"image": img, "excerpt": ex, "author": r["au"], "date_precision": r["dprec"],
                        "date": r["date"], "tickers": r["tk"],
                        "owner_attribution": "Faisal (owner, 2026-09-23)" if img == "TG_50832" else None})
        prox = []
        for f in x["proxies"]:
            s = strength.get(f)
            if s:
                prox.append({"flag": f, "dev_lift": s["lift"], "dev_lift_ci": s["lift_ci"], "recall": s["recall"]})
        out.append({k: v for k, v in x.items() if k not in ("src", "proxies")} | {"sources": src, "daily_proxies": prox})
    return out


# ───────────────────────── ⑦ the 4H grid: what is known about the frame Faisal reads ─────────────────────────
GRID_EVIDENCE = [
    ("hubc_result", "0.0269", "HUBC 4H on the app split: rms 0.0269"),
    ("hubc_result", "0.0690", "TradingView native 4H: 0.0690"),
    ("hubc_result", "04:00 · 05:30 · 09:30 · 13:30 · 17:30", "inferred split 04:00 · 05:30 · 09:30 · 13:30 · 17:30 NY"),
    ("hubc_result", "مستنتَجٌ بالمطابقة", "the split is inferred by matching, not displayed"),
    ("h4_result", "137/217", "T-H4 HV0: 137/217 buckets within 0.5% (needed 95%)"),
    ("h4_result", "34/40 = 85%", "AAPL control 34/40 = 85%"),
]


def grid_evidence():
    out = []
    for k, needle, text in GRID_EVIDENCE:
        out.append({"source": SOURCES[k], "needle": needle, "claim": text,
                    "found": needle in open(P[k], encoding="utf-8").read()})
    return out


# ───────────────────────── ⑧ build ─────────────────────────
def build():
    cal = Cal()
    reg = load_register()
    ev = load_events()
    strength = json.load(open(P["strength_dev"], encoding="utf-8"))["strength"]
    ub = upper_bounds(reg)
    axis = card_axis()
    anc = Anchor()
    imgs = []
    for iid, r in sorted(reg.items()):
        cls = h4_class(r)
        if not cls:
            continue
        rec = {"id": iid, "class": cls, "author": r["au"], "duplicate_of": r.get("dup_of"), "tickers": r["tk"],
               "date_precision": r["dprec"], "date_text": r["date"], "temporal": r["temporal"], "state": r["st"],
               "role": r["role"]}
        if not r.get("dup_of"):
            rec["dating"] = date_image(r, ub, axis, anc, cal.s[-1])
            if rec["dating"]["decision"] and r["tk"]:
                rec["links"] = {}
                for tk in r["tk"]:
                    if tk not in anc.bars:
                        rec["links"][tk] = {"status": "NOT_IN_LOCAL_UNIVERSE"}
                    elif not ev.get(tk):
                        rec["links"][tk] = {"status": "NO_EPISODE_IN_EVENTS",
                                            "decision_session": cal.s[cal.last_on_or_before(rec["dating"]["decision"])]}
                    else:
                        rec["links"][tk] = relation(cal, ev[tk], rec["dating"]["decision"], anc.bars.get(tk))
        imgs.append(rec)
    stores = bar_stores(cal, ev)
    pop = population(stores)
    alerts = rd_csv(P["alerts70"])
    seeds = {}
    k25 = cal.last_on_or_before("2025-05-01") + 1
    for s in SEEDS + ACTIVE:
        eps = []
        for e in ev.get(s, []):
            if e["onset"] < "2025-05-01":
                continue
            t10, end = cal.back(e["onset"], 10), max(x for x in (e["q"], e["d1"], e["peak"]) if x)
            rec_al = sorted({f"{a['date']} {a['anchor_et']}".strip() for a in alerts
                             if a["symbol"] == s and t10 and t10 <= a["date"] <= end})
            eps.append({"episode": f"{e['sym']}|{e['onset']}", "quality": e["quality"], "kind": e["kind"],
                        "onset": e["onset"], "q": e["q"], "x70": e["x70"], "d1": e["d1"], "T10": t10,
                        "T7": cal.back(e["onset"], 7), "recorded_intraday_alerts_T10_to_end": rec_al})
        seeds[s] = {"episodes": eps,
                    "intraday_only_spikes": intraday_only(cal, anc.bars.get(s), ev.get(s, []), k25, len(cal.s) - 1),
                    "h4_images": [i["id"] for i in imgs if s in i["tickers"]],
                    "h4_images_placed": [{"id": i["id"], **i["links"][s]} for i in imgs
                                         if s in i["tickers"] and i.get("links", {}).get(s)],
                    "bar_stores": [{"store": b["store"], "first": b["first"], "last": b["last"], "ohlc": b["ohlc"]}
                                   for b in stores if b["sym"] == s]}
    missed = []
    for w in WINDOWS:
        for x in pop[w]["top6_missed"]:
            sym, on = x["sym"], x["onset"]
            t10, t7 = cal.back(on, 10), cal.back(on, 7)
            imgs_s = [i for i in imgs if sym in i["tickers"] and not i["duplicate_of"]]
            placed = [{"id": i["id"], **i["links"][sym]} for i in imgs_s if i.get("links", {}).get(sym)]
            bars_s = [b["store"] for b in stores if b["sym"] == sym and t10 and b["first"] <= t7 and b["last"] >= t10]
            missed.append({"window": w, "sym": sym, "onset": on, "peak_gain": x["peak_gain"], "T10": t10, "T7": t7,
                           "h4_images_any_date": [i["id"] for i in imgs_s], "placed": placed,
                           "placed_at_T7_10": [z["id"] for z in placed if z.get("status") == "T7_10"
                                               and z.get("episode") == f"{sym}|{on}"],
                           "intraday_stores_covering_T10_T7": bars_s})
    hubc = json.load(open(P["hubc_card"], encoding="utf-8"))
    res = {
        "sources": {k: {"path": v, "sha256": sha(P[k])} for k, v in SOURCES.items()},
        "calendar": {"first": cal.s[0], "last": cal.s[-1], "sessions": len(cal.s)},
        "quote_check": verify_quotes(reg),
        "images": imgs,
        "image_counts": image_counts(imgs),
        "stores": stores,
        "cov30": cov30_note(),
        "hubc_card": {"bars": len(hubc.get("bars", [])), "timeframe_field": hubc.get("timeframe"),
                      "window": "2026-09-23 09:30 → 2026-09-29 09:30 (inferred by matching, RESULT.md)",
                      "events_after_card": [f"{e['sym']}|{e['onset']}" for e in ev.get("HUBC", [])
                                            if e["onset"] >= "2026-09-23"]},
        "alerts70": {"rows": len(alerts), "first": min(a["date"] for a in alerts), "last": max(a["date"] for a in alerts),
                     "fields": "symbol, date, anchor time (ET), price/volume at the anchor — timestamps, not bars"},
        "population": pop,
        "seeds": seeds,
        "missed_winners": missed,
        "rules": rule_rows(reg, strength),
        "non_faisal": NON_FAISAL,
        "grid_evidence": grid_evidence(),
        "closed_axes": CLOSED,
        "atlas_prior": atlas_prior(),
    }
    res["verdict"] = verdict(res)
    return res


def atlas_prior():
    """The sealed atlas verdict and the reconciliation's daily group-candle proxy (read, never recomputed here)."""
    v = json.load(open(P["atlas_verdict"], encoding="utf-8"))
    r2 = json.load(open(P["reconcile"], encoding="utf-8"))["R2"]
    keys = ("lift", "lift_ci95", "matched_ratio", "matched_ci95", "minus_DROP_k_pp", "minus_DROP_k_ci95",
            "minus_VOLAT_k_pp", "minus_VOLAT_k_ci95")
    return {"verdict": v["verdict"], "classification": v["classification"],
            "I04_GROUP_PROXY": {w: {k: r2[w]["I04_GROUP_PROXY"][k] for k in keys} for w in WINDOWS}}


def image_counts(imgs):
    uniq = [i for i in imgs if not i["duplicate_of"]]
    c = {"all_with_4h_content": len(imgs), "unique": len(uniq),
         "by_class": dict(sorted(Counter("+".join(i["class"]) for i in uniq).items())),
         "by_author": dict(sorted(Counter(i["author"] for i in uniq).items())),
         "by_basis": dict(sorted(Counter(i["dating"]["basis"] for i in uniq).items())),
         "charts_with_ticker": sum(1 for i in uniq if "CHART" in i["class"] and i["tickers"])}
    placed = [(i["id"], tk, x) for i in uniq for tk, x in i.get("links", {}).items()]
    basis = {i["id"]: i["dating"]["basis"] for i in uniq}
    c["placed_links"] = len(placed)
    c["placed_by_status"] = dict(sorted(Counter(x["status"] for _i, _t, x in placed).items()))
    c["placed_T7_10_not_in_event"] = sorted(f"{i}:{t}" for i, t, x in placed if x["status"] == "T7_10")
    near = []
    for i, t, x in placed:     # the closest any dated chart comes to T−10…T−7 — reported, never counted as a case
        if x["status"] == "IN_EVENT" and 7 <= x.get("sessions_to_next_clean_onset", 0) <= 10:
            near.append({"id": i, "sym": t, "decision_session": x["decision_session"], "basis": basis[i],
                         "why_not": "IN_EVENT",
                         "detail": f"inside {x['episode']} ({x['quality']}); next clean onset {x['next_clean_onset']} "
                                   f"is {x['sessions_to_next_clean_onset']} sessions later"})
        for z in x.get("intraday_only_within_10", []):
            if 7 <= z["sessions_after"] <= 10:
                near.append({"id": i, "sym": t, "decision_session": x["decision_session"], "basis": basis[i],
                             "why_not": "INTRADAY_ONLY_EVENT",
                             "detail": f"{z['sessions_after']} sessions before an intraday-only threshold on {z['session']} "
                                       f"(high +{z['high_vs_prior_close_pct']}%, close {z['close_vs_prior_close_pct']:+}%) "
                                       f"— no daily-close episode"})
    c["near_misses"] = sorted(near, key=lambda z: (z["sym"], z["id"]))
    anc = [i["dating"]["anchor"] for i in uniq if i["dating"].get("anchor")]
    c["anchor_attempts"] = len(anc)
    c["anchor_by_status"] = dict(sorted(Counter(a["status"] for a in anc).items()))
    return c


def verdict(res):
    """The minimum a formal 4H test needs inside the study windows: intraday OHLC at T−10…T−7 for some positives, for some
    comparable inactive pivots, and for at least two independent events. Deliberately lax (it is not a power requirement)
    so that a failure cannot be an artefact of a strict bar; it was set after the inventory had been read."""
    pop = res["population"]
    pos_ohlc = sum(p["pos710_rows_with_intraday_ohlc"] for p in pop.values())
    neg_ohlc = sum(p["neg_rows_with_intraday_ohlc"] for p in pop.values())
    ev_ohlc = sorted({e for p in pop.values() for e in p["eligible_events_with_intraday_ohlc"]})
    ev_any = sorted({e for p in pop.values() for e in p["eligible_events_with_any_intraday_bar"]})
    elig = sum(p["eligible_events"] for p in pop.values())
    rows = sum(p["pivot_days"] for p in pop.values())
    placed = res["image_counts"]["placed_T7_10_not_in_event"]
    ok = pos_ohlc > 0 and neg_ohlc > 0 and len(ev_ohlc) >= 2
    return {"formal_test_performed": False if not ok else None,
            "status": "TEST_NOT_PERFORMED — EVIDENCE GAP" if not ok else "DATA_SUFFICIENT_FOR_A_TEST",
            "eligible_events_all_windows": elig, "pivot_days_all_windows": rows,
            "eligible_events_with_intraday_ohlc": ev_ohlc, "eligible_events_with_any_intraday_bar": ev_any,
            "pos710_rows_with_intraday_ohlc": pos_ohlc, "neg_rows_with_intraday_ohlc": neg_ohlc,
            "dated_charts_at_T7_10_not_in_event": placed,
            "baselines_compared": "none — no candidate could be computed on the evaluable population"}


# ───────────────────────── ⑨ render ─────────────────────────
from h4_report import render_all                                          # noqa: E402


def main():
    check = "--check" in sys.argv
    res = build()
    blob = json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    docs = render_all(res)
    if check:
        bad = []
        if not os.path.exists(OUT_JSON) or open(OUT_JSON, encoding="utf-8").read() != blob:
            bad.append(os.path.relpath(OUT_JSON, ROOT))
        for name, text in docs.items():
            p = os.path.join(HERE, name)
            if not os.path.exists(p) or open(p, encoding="utf-8").read() != text:
                bad.append(name)
        if res["quote_check"]:
            bad.append(f"quote_check: {res['quote_check']}")
        print("h4_audit --check:", "OK" if not bad else f"DRIFT {bad}")
        sys.exit(1 if bad else 0)
    os.makedirs(DATA, exist_ok=True)
    open(OUT_JSON, "w", encoding="utf-8").write(blob)
    for name, text in docs.items():
        open(os.path.join(HERE, name), "w", encoding="utf-8").write(text)
    print("h4_audit: wrote", os.path.relpath(OUT_JSON, ROOT), "and", ", ".join(sorted(docs)))
    print("verdict:", res["verdict"]["status"])


if __name__ == "__main__":
    main()
