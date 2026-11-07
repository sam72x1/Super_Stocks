#!/usr/bin/env python3
"""🌘➡️ `T-SHADOW-CONT` — «هل يستمر بعد رسالة الظل؟» (العقد `fm_forensics/shadow_cont/T_SHADOW_CONT_prereg.md` · مدموجٌ قبل أيّ رقم) — قراءةٌ فقط.

`--mode run`: سجلُّ الظلّ المجمَّد (`git show ff8bdc690:shadow_ready_ledger.jsonl`) ⟵ صفوفُ البري في الجلسات الستّين (`vwap_cont.sessions` بالاسم) ⟵
المجموعات S · C20 · C10 ⟵ شموعُ الدقيقة (`tier_fwd_report.fetch_day` بالاسم) ⟵ الدخولُ عند 09:25 والمقاييسُ ①-④ ⟵ الحكمُ والتنبّؤات K1-K7.
🔒 لا تلغرام · لا كتابة في المستودع · لا تغيير إنتاجيّ · وتخرج 9 إن تغيّرت بصمةُ العقد.
"""
import argparse
import datetime as dt
import hashlib
import json
import math
import os
import random
import subprocess
import sys
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

CONTRACT = os.path.join(HERE, "T_SHADOW_CONT_prereg.md")
CONTRACT_SHA = "1ba76504465ba96dfa04a3f0d836da05cd641e908e82330c8aef45aa0094489d"
CONTRACT_RC = 9
LEDGER_REF = "ff8bdc690d788c917b3c4785f5851206c3f71c08"     # §① السجلُّ المجمَّد
LEDGER_FILE = "shadow_ready_ledger.jsonl"
NY = ZoneInfo("America/New_York")
ENTRY_NY, CLOSE_NY, END_NY = 9 * 60 + 25, 16 * 60, 20 * 60  # §③
STOP = 0.10                                                   # §③ ④
GAP_GOV, GAP_DESC = 20.0, 10.0                                # §② C20 · C10
LEVELS = (0.10, 0.20, 0.50)                                   # §③ ①
FLOOR, BARS_FAIL_MAX = 20, 0.10                               # §④
BOOT_N, SEED = 2000, "SHC1"                                   # §④


def log(m=""):
    print(m, flush=True)


def contract_ok(path=CONTRACT):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest() == CONTRACT_SHA
    except OSError:
        return False


# ── نقيّات ─────────────────────────────────────────────────────────────────────────────
def median(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    m = len(xs) // 2
    return xs[m] if len(xs) % 2 else (xs[m - 1] + xs[m]) / 2.0


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def wilson(k, n, z=1.96):
    if not n:
        return None, None
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, c - h), min(1.0, c + h)


def ny_parts(t_ms):
    t = dt.datetime.fromtimestamp(int(t_ms) / 1000, dt.timezone.utc).astimezone(NY)
    return t.date().isoformat(), t.hour * 60 + t.minute


def groups(rows, days):
    """§② ⟵ ({"S","C20","C10": [صف]} · {"after_cut": n لكلّ مجموعة}) · صفوفُ `fwd`/`pre` في الجلسات وحدَها · والمرساةُ عند 09:25 أو بعدها تُستبعَد وتُعَدّ."""
    ds = set(days)
    out = {"S": [], "C20": [], "C10": []}
    cut = {"S": 0, "C20": 0, "C10": 0}
    for r in rows:
        if r.get("sample") != "fwd" or r.get("tod") != "pre" or r.get("date") not in ds:
            continue
        g = r.get("gap_pct")
        names = ["S"] if r.get("shadow") is True else (
            (["C20"] if g is not None and g >= GAP_GOV else []) + (["C10"] if g is not None and g >= GAP_DESC else []))
        try:
            d, m = ny_parts(r.get("anchor_ms"))
            late = d != r["date"] or m >= ENTRY_NY
        except Exception:                                            # noqa: BLE001
            late = True
        for nm in names:
            if late:
                cut[nm] += 1
            else:
                out[nm].append(r)
    return out, cut


def measure(bars, day):
    """§③ لصفٍّ واحد ⟵ (dict | None، السبب). الشموعُ `(t, o, h, l, c, v)` تصاعديّة."""
    if not bars:
        return None, "bars"
    seq = []
    for b in bars:
        d, m = ny_parts(b[0])
        if d == day:
            seq.append((m, b[1], b[2], b[3], b[4]))
    pre = [b for b in seq if b[0] < ENTRY_NY]
    if not pre:
        return None, "no_entry"
    E = pre[-1][4]
    if not E or E <= 0:
        return None, "no_entry"
    n16 = [b for b in seq if ENTRY_NY <= b[0] < CLOSE_NY]
    n20 = [b for b in seq if ENTRY_NY <= b[0] < END_NY]
    if not n16:
        return None, "no_regular"
    out = {"E": E}
    for tag, w in (("16", n16), ("20", n20)):
        hi = max(b[2] for b in w)
        k = next(i for i, b in enumerate(w) if b[2] == hi)
        lo = min(b[3] for b in w[:k + 1])
        out["rise" + tag] = hi / E - 1
        out["dd" + tag] = lo / E - 1
    C = n16[-1][4]
    out["ret_close"] = C / E - 1
    stop = (1 - STOP) * E
    exit_px, stopped = C, False
    for b in n16:
        if b[3] <= stop:
            exit_px, stopped = min(b[1], stop), True
            break
    out["net"] = exit_px / E - 1
    out["stopped"] = stopped
    return out, "ok"


def summarize(ms):
    """①-④ لمجموعة (قيمُ الصفوف المقيسة)."""
    n = len(ms)
    s = {"n": n}
    for tag in ("16", "20"):
        for lv in LEVELS:
            k = sum(1 for m in ms if m["rise" + tag] >= lv)
            lo, hi = wilson(k, n)
            s[f"ge{int(lv * 100)}_{tag}"] = (k, n, (k / n) if n else None, lo, hi)
        s["dd_med_" + tag] = median([m["dd" + tag] for m in ms])
        s["dd10_" + tag] = (sum(1 for m in ms if m["dd" + tag] <= -STOP), n)
    s["close_med"] = median([m["ret_close"] for m in ms])
    s["net_mean"] = mean([m["net"] for m in ms])
    s["net_med"] = median([m["net"] for m in ms])
    s["net_pos"] = (sum(1 for m in ms if m["net"] > 0), n)
    return s


def _stat(by_day, days, grp, fn):
    xs = [m for d in days for m in by_day.get(d, {}).get(grp, [])]
    return fn(xs) if xs else None


def net_mean(ms):
    return mean([m["net"] for m in ms])


def ge20(ms):
    return sum(1 for m in ms if m["rise16"] >= 0.20) / len(ms)


def diff(by_day, days, fn=net_mean):
    a, b = _stat(by_day, days, "S", fn), _stat(by_day, days, "C20", fn)
    return None if a is None or b is None else a - b


def boot(by_day, days, fn=net_mean, n=BOOT_N, seed=SEED):
    """§④ فاصلُ 95% بإعادة سحب الجلسات مع الإرجاع — السحبةُ نفسُها للمجموعتين."""
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        pick = [rng.choice(days) for _ in days]
        xs = {"S": [], "C20": []}
        for d in pick:
            for g in xs:
                xs[g].extend(by_day.get(d, {}).get(g, []))
        if xs["S"] and xs["C20"]:
            out.append(fn(xs["S"]) - fn(xs["C20"]))
    if len(out) < 20:
        return None, None
    out.sort()
    return out[int(0.025 * len(out))], out[min(len(out) - 1, int(0.975 * len(out)))]


def verdict(d_all, ci, d_h1, d_h2, nS, nC):
    if nS < FLOOR or nC < FLOOR:
        return "لا قياس"
    if d_all is None or ci[0] is None:
        return "لا قياس"
    sign = (d_all > 0) - (d_all < 0)
    if ci[0] > 0 or ci[1] < 0:
        if d_h1 is not None and d_h2 is not None and ((d_h1 > 0) - (d_h1 < 0)) == sign == ((d_h2 > 0) - (d_h2 < 0)):
            return "يفرّق"
    return "لا يفرّق"


def predictions(res):
    S = res["sum"]["S"]
    k1 = S["ge10_16"][2]
    k2 = S["ge50_16"][2]
    dd = S["dd10_16"]
    out = [
        ("K1", k1 is not None and 0.45 <= k1 <= 0.75, f"حصّةُ ‏+10% حتى 16:00 {k1:.1%}" if k1 is not None else "—"),
        ("K2", k2 is not None and k2 < 0.25, f"حصّةُ ‏+50% حتى 16:00 {k2:.1%}" if k2 is not None else "—"),
        ("K3", S["close_med"] is not None and S["close_med"] < 0, f"وسيطُ الإغلاق {S['close_med']:+.2%}" if S["close_med"] is not None else "—"),
        ("K4", S["net_mean"] is not None and -0.06 <= S["net_mean"] <= 0.06, f"متوسّطُ ④ {S['net_mean']:+.2%}" if S["net_mean"] is not None else "—"),
        ("K5", res["verdict"] == "لا يفرّق", f"الحكم «{res['verdict']}»"),
        ("K6", dd[1] > 0 and dd[0] / dd[1] > 0.25, f"بلغ −10% قبل أعلاه {dd[0]} من {dd[1]}"),
    ]
    a, b = S["ge20_16"][2], S["ge20_20"][2]
    out.append(("K7", a is not None and b is not None and (b - a) < 0.05, f"‏+20%: حتى 16:00 {a:.1%} · حتى 20:00 {b:.1%}" if a is not None and b is not None else "—"))
    return out


def analyze(measured, cut, fails, days_all):
    """measured: {grp: [(day, sym, m)]} ⟵ النتيجة."""
    res = {"cut": cut, "fails": fails, "sum": {}, "n_rows": {g: len(v) for g, v in measured.items()}}
    for g, v in measured.items():
        res["sum"][g] = summarize([m for _d, _s, m in v])
    by_day = {}
    for g in ("S", "C20"):
        for d, _s, m in measured[g]:
            by_day.setdefault(d, {}).setdefault(g, []).append(m)
    days = sorted(by_day)
    res["days"] = len(days)
    half = len(days) // 2
    h1, h2 = days[:half], days[half:]
    d_all = diff(by_day, days)
    ci = boot(by_day, days)
    res["gov"] = {"diff": d_all, "ci": ci, "h1": diff(by_day, h1), "h2": diff(by_day, h2)}
    tot = {g: len(measured[g]) + sum(fails[g].values()) for g in ("S", "C20")}
    bad = any(tot[g] and fails[g].get("bars", 0) / tot[g] > BARS_FAIL_MAX for g in ("S", "C20"))
    res["cov_ok"] = not bad
    v = verdict(d_all, ci, res["gov"]["h1"], res["gov"]["h2"], len(measured["S"]), len(measured["C20"]))
    res["verdict"] = "لا قياس" if bad else v
    res["desc20"] = {"diff": diff(by_day, days, ge20), "ci": boot(by_day, days, ge20)}
    res["pred"] = predictions(res)
    res["days_frame"] = len(days_all)
    return res


def _pc(x):
    return "—" if x is None else f"{x:+.1%}"


def report_lines(res):
    L = [f"🌘➡️ T-SHADOW-CONT · الجلساتُ ذاتُ صفوف {res['days']} (من إطار {res['days_frame']}) · صفوفٌ مقيسة S {res['n_rows']['S']} · C20 {res['n_rows']['C20']} · C10 {res['n_rows']['C10']}",
         f"   مستبعَد (مرساةٌ بعد 09:25): {res['cut']} · تعذّر: {res['fails']}"]
    hdr = "| المقياس | S | C20 (الحاكم) | C10 (وصف) |"
    L += ["", hdr, "|---|---|---|---|"]
    for tag, lab in (("16", "حتى 16:00"), ("20", "حتى 20:00")):
        for lv in LEVELS:
            key = f"ge{int(lv * 100)}_{tag}"
            cells = []
            for g in ("S", "C20", "C10"):
                k, n, p, lo, hi = res["sum"][g][key]
                cells.append("—" if p is None else f"{k}/{n} = {p:.1%} [{lo:.0%}، {hi:.0%}]")
            L.append(f"| ① ‏+{int(lv * 100)}% {lab} | " + " | ".join(cells) + " |")
        L.append(f"| ② وسيطُ الأدنى قبل الأعلى {lab} | " + " | ".join(_pc(res["sum"][g]["dd_med_" + tag]) for g in ("S", "C20", "C10")) + " |")
        L.append(f"| ② بلغ −10% قبل أعلاه {lab} | " + " | ".join(f"{res['sum'][g]['dd10_' + tag][0]}/{res['sum'][g]['dd10_' + tag][1]}" for g in ("S", "C20", "C10")) + " |")
    L.append("| ③ وسيطُ الإغلاق النظاميّ مقابل الدخول | " + " | ".join(_pc(res["sum"][g]["close_med"]) for g in ("S", "C20", "C10")) + " |")
    L.append("| ④ بوقف −10%: المتوسّط | " + " | ".join(_pc(res["sum"][g]["net_mean"]) for g in ("S", "C20", "C10")) + " |")
    L.append("| ④ بوقف −10%: الوسيط | " + " | ".join(_pc(res["sum"][g]["net_med"]) for g in ("S", "C20", "C10")) + " |")
    L.append("| ④ موجب | " + " | ".join(f"{res['sum'][g]['net_pos'][0]}/{res['sum'][g]['net_pos'][1]}" for g in ("S", "C20", "C10")) + " |")
    G = res["gov"]
    L += ["", f"⚖️ الحاكم (متوسّطُ ④ S − C20): {_pc(G['diff'])} [{_pc(G['ci'][0])}، {_pc(G['ci'][1])}] · النصفان {_pc(G['h1'])} · {_pc(G['h2'])} ⟵ «{res['verdict']}»",
          f"   وصفًا: فرقُ حصّة ‏+20% حتى 16:00 {_pc(res['desc20']['diff'])} [{_pc(res['desc20']['ci'][0])}، {_pc(res['desc20']['ci'][1])}]",
          "   التنبّؤات: " + " · ".join(f"{k} {'✅' if ok else '❌'} {t}" for k, ok, t in res["pred"])]
    return L


def strictest(v_old, v_full):
    """🔧 `CORRECTION_PROTOCOL.md §②` (نقيّة): «يفرّق» لا تُقال إلّا بالتعريفين · و«لا قياس» بأحدهما تحكم · وإلّا «لا يفرّق»."""
    if "لا قياس" in (v_old, v_full):
        return "لا قياس"
    return "يفرّق" if (v_old == "يفرّق" and v_full == "يفرّق") else "لا يفرّق"


def extra_exited(base, extra):
    """🔧 صفوفُ المراسي الخارجة (`exited`) من مُخرَج `shadow_ready` (الملحق 1) غيرُ الموجودة في السجلّ المجمَّد ⟵ تُضاف إليه."""
    have = {(r.get("date"), r.get("symbol")) for r in base}
    return [r for r in (extra or []) if r.get("exited") and (r.get("date"), r.get("symbol")) not in have]


def load_ledger(ref=LEDGER_REF):
    txt = subprocess.run(["git", "show", f"{ref}:{LEDGER_FILE}"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [json.loads(x) for x in txt.splitlines() if x.strip()]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("run", "check"), default="run")
    ap.add_argument("--extra-rows", default=None)   # 🔧 CORRECTION_PROTOCOL.md §②: صفوفُ shadow_ready (SHADOW_DUMP=1) JSON
    a = ap.parse_args(argv)
    if not contract_ok():
        log(f"⛔ بصمةُ العقد `{CONTRACT}` تغيّرت أو غاب — المدموجُ لا يُعدَّل (خروج {CONTRACT_RC})")
        return CONTRACT_RC
    if a.mode == "check":
        log("✅ العقدُ مطابقٌ لبصمته")
        return 0
    import market_calendar as MC
    import vwap_cont as VC
    from tier_fwd_report import fetch_day
    key = (os.environ.get("POLYGON_API_KEY") or "").strip()
    if not key:
        log("⛔ بلا مفتاح Polygon — لا قياس")
        return 3
    days = VC.sessions(MC)
    base = load_ledger()
    grp, cut = groups(base, days)
    cache = {}

    def _measure_groups(grp_):
        measured_, fails_ = {g: [] for g in grp_}, {g: {} for g in grp_}
        for g, rows in grp_.items():
            for r in rows:
                k = (r["symbol"], r["date"])
                if k not in cache:
                    cache[k] = measure(fetch_day(r["symbol"], r["date"], key), r["date"])
                m, why = cache[k]
                if m is None:
                    fails_[g][why] = fails_[g].get(why, 0) + 1
                else:
                    measured_[g].append((r["date"], r["symbol"], m))
        return measured_, fails_
    measured, fails = _measure_groups(grp)
    res = analyze(measured, cut, fails, days)
    for ln in report_lines(res):
        log(ln)
    if a.extra_rows:
        ex = extra_exited(base, json.load(open(a.extra_rows, encoding="utf-8")))
        grp_f, cut_f = groups(base + ex, days)
        measured_f, fails_f = _measure_groups(grp_f)
        res_f = analyze(measured_f, cut_f, fails_f, days)
        log(f"\n## 🔧 بالتعريف المصحَّح (`CORRECTION_PROTOCOL.md §②`) — صفوفٌ خارجةٌ مضافة {len(ex)} "
            f"(منها في S {sum(1 for r in ex if r.get('shadow'))})")
        for ln in report_lines(res_f):
            log(ln)
        log(f"\n⚖️ الحكمُ بالتعريف القديم «{res['verdict']}» · بالمصحَّح «{res_f['verdict']}» ⟵ الأشدّ «{strictest(res['verdict'], res_f['verdict'])}»")
    log("SHC_ROWS " + json.dumps({g: [(d, s, {k: (round(v, 6) if isinstance(v, float) else v) for k, v in m.items()}) for d, s, m in v]
                                 for g, v in measured.items()}, ensure_ascii=False))
    log("SHC_JSON " + json.dumps({k: v for k, v in res.items()}, ensure_ascii=False, default=str))
    return 0 if res["cov_ok"] else 4


if __name__ == "__main__":
    sys.exit(main())
