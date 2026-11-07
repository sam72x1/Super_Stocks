#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""👁️ `T-OEWIDE` — لو راقب «هنا الدخول» «تحت المتابعة» كاملًا بدل السلّتين (العقد `OEWIDE_prereg.md` · مدموجٌ قبل أيّ رقم).

`--mode chunk --part i --parts n` (الرنر · Polygon · تاريخُ git): جلساتُ الجزء ⟵ الكونان `U(s)`/`W(s)` من لقطات git ⟵ شموعُ كلّ رمز-يوم ⟵
`nofire.replay` بالاسم مرّةً بكلّ كون (وبوّابةُ المضارب `nofire.op_gate`) ⟵ J1 من أوّل حدث `M5` (`kasih_j1` بالاسم) ⟵ JSON.
`--mode pool --chunks …`: الجمعُ ⟵ زمنُ الدورة من سجلّات العامل (GitHub API) ⟵ التقرير والتنبّؤات.
🔒 قراءةٌ فقط: لا تلغرام · لا كتابةَ في المستودع · لا تغييرَ على العامل.
"""
import argparse
import bisect
import datetime as dt
import hashlib
import importlib.util
import json
import os
import re
import statistics
import sys
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

CONTRACT = os.path.join(HERE, "OEWIDE_prereg.md")
CONTRACT_SHA = "fc19b346e8e10dfc067f191ddf262301abcc364cf49c3d97afc2935f4e6a7f8a"
G42 = os.path.join(HERE, "data", "g2_42.json")
G42_SHA = "7d16f31872072e77c396bd806584dae07fbc00969ad7b921d6c932e20a79cf62"
RUNNERS = os.path.join(ROOT, "fm_forensics", "rrgate", "data", "runners_60.json")
UNIVERSE = os.path.join(ROOT, "fm_forensics", "ema_cross", "data", "gcross_runner_universe.json")
CONTRACT_RC = 9
NY = ZoneInfo("America/New_York")
TRUTH_MIN, BARS_FAIL_MAX = 0.85, 0.10                         # §④
J1_WAIT_MIN = 10                                              # §② حدثُ M5 حتى 10 دقائق بعد المِرساة
CYCLE_S, SLOT_S = 60, 15 * 60                                 # ⓪-K5 · الأمر
LOG_DAYS, LOG_RUNS_MAX = 30, 20                               # §③-4
SIZES = (600, 800)
RUN50, RUN100 = 0.5, 1.0
WORKERS = 16


def log(m=""):
    print(m, flush=True)


def _load(name, rel):
    sp = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    mod = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(mod)
    return mod


def _sha(path):
    try:
        return hashlib.sha256(open(path, "rb").read()).hexdigest()
    except OSError:
        return None


def contract_ok():
    return _sha(CONTRACT) == CONTRACT_SHA and _sha(G42) == G42_SHA


# ── دوالُّ نقيّة ──────────────────────────────────────────────────────────────────────────────
def wide_set(near):
    """⓪-K2: كلُّ صفٍّ قاموسيٍّ غيرِ محجوبٍ في `near_watch.json` ⟵ رموزٌ بأحرفٍ كبيرة."""
    return {str(k).upper() for k, v in (near or {}).items() if isinstance(v, dict) and not v.get("blocked")}


def membership(points, sym, which):
    """[(ثانية، U، W)] ⟵ دالّةُ عضويّةٍ s (ملّي) ⟵ آخرُ نقطةٍ قبلها (لا شيءَ قبل الأولى ⟵ خطأ)."""
    tl = sorted((t, sym in (u if which == "U" else w)) for t, u, w in points)
    ts = [t for t, _m in tl]

    def f(s_ms):
        i = bisect.bisect_right(ts, s_ms / 1000.0) - 1
        return bool(i >= 0 and tl[i][1])
    return f


def same_membership(points, sym):
    return all((sym in u) == (sym in w) for _t, u, w in points)


def wilson(k, n, z=1.96):
    if not n:
        return (None, None, None)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / den
    return (p, max(0.0, c - h), min(1.0, c + h))


def r_class(R):
    if R is None:
        return None
    return "run100" if R >= RUN100 else ("mid" if R >= RUN50 else "false")


def cycle_pairs(text):
    """«💰 التغطية: N من M في X ث» ⟵ [(M، X)] (الكونُ كلُّه وزمنُ مسحه)."""
    return [(int(b), float(c)) for _a, b, c in re.findall(r"💰 التغطية: (\d+) من (\d+) في ([\d.]+)ث", text or "")]


def sec_per_symbol(pairs):
    v = [x / n for n, x in pairs if n > 0]
    return statistics.median(v) if v else None


def predictions(res):
    t = res.get("truth") or {}
    g = res.get("g42") or {}
    c = res.get("cost") or {}
    j = res.get("j1") or {}
    cy = res.get("cycle") or {}
    pU, pW = (c.get("precU") or (None,))[0], (c.get("precW") or (None,))[0]
    add = c.get("added_false_day")
    cut = j.get("cut_added_false")
    keep42 = j.get("keep42_share")
    return [
        ("W1", bool(t.get("ok")), f"صدقُ الإعادة {t.get('share') if t.get('share') is None else round(t['share'] * 100, 1)}%"),
        ("W2", g.get("caught") is not None and 30 <= g["caught"] <= 40, f"الملتقَط {g.get('caught')} من {g.get('n')}"),
        ("W3", g.get("left_med") is not None and 0.5 <= g["left_med"] <= 0.8, f"وسيطُ ما بقي {g.get('left_med')}"),
        ("W4", add is not None and 8 <= add <= 20, f"الكاذبُ المضاف يوميًّا {add}"),
        ("W5", pU is not None and pW is not None and pW < pU,
         f"دقّةُ W {None if pW is None else round(pW, 3)} · U {None if pU is None else round(pU, 3)}"),
        ("W6", cut is not None and keep42 is not None and cut >= 0.9 and 0.3 <= keep42 <= 0.6, f"J1 يقصّ {cut} · ويُبقي من الـ42 {keep42}"),
        ("W7", cy.get("at800") is not None and cy["at800"] < 30, f"الدورة على 800 {cy.get('at800')} ث"),
        ("W8", c.get("split_share") is not None and c["split_share"] <= 0.05, f"المستبعَدُ بالتقسيم {c.get('split_share')}"),
    ]


# ── الشبكة وgit ───────────────────────────────────────────────────────────────────────────────
def day_points(NOF, bot, day, commits):
    """②: نقاطُ تغيّر الكون في [04:00، 20:00) ⟵ [(ثانية، U، W)] من لقطات الملفّات الأربعة (`live_watch_universe` بالاسم · `cap=10**9`)."""
    t0, t1 = NOF.ny_ts(day, NOF.OP_NY), NOF.ny_ts(day, NOF.END_NY)
    pts = sorted({t for f in NOF.LIST_FILES for t, _h in commits[f] if t0 < t < t1} | {t0})
    out = []
    for t in pts:
        docs = []
        for f in NOF.LIST_FILES:
            h = None
            for ct, hh in commits[f]:
                if ct <= t:
                    h = hh
                else:
                    break
            docs.append(NOF.show_json(h, f) if h else None)
        wl, near, press, hunter = docs
        near = near if isinstance(near, dict) else {}
        try:
            uni, _ = bot.live_watch_universe(wl or {}, near, press or {}, hunter or {}, cap=10 ** 9, today_iso=day)
            U = {r.get("symbol") for r in uni}
        except Exception:                                            # noqa: BLE001
            U = set()
        out.append((t, U, U | wide_set(near)))
    return out


def rp(NOF, bot, bars, day, ok, tc, op):
    """`nofire.replay` بالاسم ⟵ ثمّ متابعةُ المسح حتى 10 دقائق بعد المِرساة لالتقاط أوّل `M5` (بالحالة المحمولة نفسِها)."""
    rec = {}

    def fn(w, st, **kw):
        ev, st2 = bot.liq_stage_events(w, st, **kw)
        rec["st"] = st2
        return ev, st2
    r = NOF.replay(bars, day, ok, tc, op, stage_fn=fn)
    out = {"a": r["anchor_ms"], "at": r["at_ms"], "muted": r["muted"], "capped": r["capped"], "m5": None}
    if not r["anchor_ms"]:
        return out
    st, ts, win = dict(rec.get("st") or {}), [b["t"] for b in bars], int(bot.LIQ_WINDOW_MIN)
    for _m, s in NOF.sweep_times(day):
        if s <= r["at_ms"]:
            continue
        if s > r["at_ms"] + J1_WAIT_MIN * 60_000:
            break
        if ok is not None and not ok(s):
            continue
        w = bars[bisect.bisect_left(ts, s - win * 60_000):bisect.bisect_left(ts, s)]
        if not w:
            continue
        ev, st = bot.liq_stage_events(w, st, now_ms=s, rearm=True, tc=None)
        m5 = next((e for e in ev if e.get("stage") == "M5"), None)
        if m5:
            out["m5"] = {"class": list(m5.get("class") or []), "anchor_price": m5.get("anchor_price")}
            break
    return out


def is_j1(bot, m5, p0):
    if not m5 or not p0:
        return False
    return bool(bot.kasih_j1(dict(m5, prev_close=p0))[0])


def dailies_all(sym, d0, d1, key):
    import requests
    try:
        r = requests.get(f"https://api.polygon.io/v2/aggs/ticker/{sym}/range/1/day/{d0}/{d1}",
                         params={"adjusted": "false", "sort": "asc", "limit": 400}, headers={"Authorization": f"Bearer {key}"}, timeout=30)
        if r.status_code != 200:
            return None
        return [(dt.datetime.fromtimestamp(b["t"] / 1000, tz=NY).date().isoformat(), float(b["h"]), float(b["c"]))
                for b in (r.json() or {}).get("results") or []]
    except Exception:                                                # noqa: BLE001
        return None


def mode_chunk(part, parts, out_path):
    from concurrent.futures import ThreadPoolExecutor
    import Super_stock as bot
    from tier_fwd_report import fetch_day
    from shadow_ready import split_ratio
    NOF = _load("nofire_ow", "fm_forensics/nofire/nofire.py")
    LVS = _load("lvs_ow", "fm_forensics/live_vs_shadow/live_vs_shadow.py")
    key = (os.environ.get("POLYGON_API_KEY") or "").strip()
    if not key or not os.environ.get("GITHUB_TOKEN"):
        log("⛔ لا مفتاح Polygon أو GITHUB_TOKEN — لا قياس")
        return 3
    RN = json.load(open(RUNNERS, encoding="utf-8"))
    G = json.load(open(G42, encoding="utf-8"))["rows"]
    U0 = json.load(open(UNIVERSE, encoding="utf-8"))
    sessions = sorted(U0["sessions"])                          # §① الستّون نفسُها (= runners_60.json «sessions»)
    assert len(sessions) == RN["sessions"][2] and sessions[0] == RN["sessions"][0] and sessions[-1] == RN["sessions"][1]
    days = sessions[part::parts]
    alerts = LVS.rebuild_alerts(U0, True)                      # CORRECTION_PROTOCOL.md §① (المصحَّحة)
    src = set(LVS.source_days(dict(U0, alerts=alerts)))
    jobs, _n_jobs, _n_runs = NOF.worker_jobs(days)                # ⟵ ({يوم: [(بدء، نهاية، id)]}، عددُ التشغيلات المقيسة، الكلّ)
    commits = {f: NOF.file_commits(f) for f in NOF.LIST_FILES}
    log(f"👁️ الجزء {part + 1}/{parts}: {len(days)} جلسة ({days[0]} … {days[-1]}) · مراسٍ مصحَّحة على أيّامه "
        f"{sum(len(alerts.get(d) or {}) for d in days)} · أيّامُ مصدرٍ منه {sum(1 for d in days if d in src)}")
    run_by = {(r["sym"], r["day"]) for r in RN["rows"] if r.get("R", 0) >= RUN100}
    g42 = {(r["sym"], r["day"]) for r in G}
    d_min = (dt.date.fromisoformat(sessions[0]) - dt.timedelta(days=12)).isoformat()
    d_max = (dt.date.fromisoformat(sessions[-1]) + dt.timedelta(days=2)).isoformat()
    dly_c = {}
    out = {"part": part, "parts": parts, "days": days, "sd": 0, "bars_fail": 0, "u_size": {}, "w_size": {}, "fires": [], "g42": [],
           "truth": {"n": 0, "hit": 0, "outside_u": 0, "miss": []}, "replay_calls": 0}
    for d in days:
        pts = day_points(NOF, bot, d, commits)
        out["u_size"][d] = [min(len(u) for _t, u, _w in pts), max(len(u) for _t, u, _w in pts)]
        out["w_size"][d] = [min(len(w) for _t, _u, w in pts), max(len(w) for _t, _u, w in pts)]
        syms = set().union(*[w for _t, _u, w in pts]) | {s for s, dd in run_by if dd == d} | set(alerts.get(d) or {})
        with ThreadPoolExecutor(WORKERS) as pool:
            raw = dict(zip(sorted(syms), pool.map(lambda s: fetch_day(s, d, key), sorted(syms))))
        need_d = [s for s in syms if s not in dly_c]
        with ThreadPoolExecutor(WORKERS) as pool:
            for s, v in zip(need_d, pool.map(lambda s: dailies_all(s, d_min, d_max, key), need_d)):
                dly_c[s] = v
        alive = NOF.intervals_fn([(a, b) for a, b, _i in jobs.get(d, [])])
        tc_day = NOF.TC_FROM <= d <= NOF.TC_TO
        n_fail = 0
        for sym in sorted(syms):
            out["sd"] += 1
            bars = NOF.bar_dicts(raw.get(sym), d)
            if len(bars) < 5:
                n_fail += 1
                continue
            _pd, p0 = LVS.prev_close(dly_c.get(sym), d)
            tc = ({"usd": bot.LIQ_TC_USD, "pct": bot.LIQ_TC_PCT, "prev_close": float(p0)} if (p0 and tc_day) else None)
            inU, inW = membership(pts, sym, "U"), membership(pts, sym, "W")
            op = NOF.op_gate(sym, key)
            rU = rp(NOF, bot, bars, d, inU, tc, op)
            rW = rU if same_membership(pts, sym) else rp(NOF, bot, bars, d, inW, tc, op)
            out["replay_calls"] += 1 if rW is rU else 2
            seq = LVS.day_seq(raw.get(sym), d)
            R = LVS.day_R(seq, p0)[0] if p0 else None
            al = (alerts.get(d) or {}).get(sym)
            if al and d in src:
                if inU(int(al["ms"])):
                    out["truth"]["n"] += 1
                    if rU["a"]:
                        out["truth"]["hit"] += 1
                    elif len(out["truth"]["miss"]) < 40:
                        out["truth"]["miss"].append(f"{sym} {d}")
                else:
                    out["truth"]["outside_u"] += 1
            if rU["a"] or rW["a"]:
                sr = split_ratio(sym, _pd, d, key) if _pd else None
                out["fires"].append({"sym": sym, "d": d, "U": bool(rU["a"]), "W": bool(rW["a"]), "R": R,
                                     "split": bool(sr is not None and sr != 1.0),
                                     "j1U": is_j1(bot, rU["m5"], p0), "j1W": is_j1(bot, rW["m5"], p0)})
            if (sym, d) in g42:
                ok_act = (lambda s, _w=inW: _w(s) and alive(s))
                rA = rp(NOF, bot, bars, d, ok_act, tc, op)
                row = {"sym": sym, "d": d, "caughtU": bool(rU["a"]), "caughtW": bool(rW["a"]), "caughtW_actual": bool(rA["a"]),
                       "j1W": is_j1(bot, rW["m5"], p0), "R": R}
                if rW["a"]:
                    fm = LVS.ny_parts(rW["a"])[1]
                    px = next((b["c"] for b in bars if b["t"] == rW["a"]), None)
                    row.update({"m": fm, **(LVS.after_stats(seq, fm, px, p0) or {})})
                out["g42"].append(row)
        out["bars_fail"] += n_fail
        log(f"   {d}: رموز {len(syms)} · U {out['u_size'][d]} · W {out['w_size'][d]} · بلا شموع {n_fail} · "
            f"إطلاقاتٌ حتى الآن {len(out['fires'])}")
    json.dump(out, open(out_path, "w", encoding="utf-8"), ensure_ascii=False)
    log(f"✅ الجزء {part + 1}: رموزٌ-أيّام {out['sd']} · بلا شموع {out['bars_fail']} · إطلاقات {len(out['fires'])} · الـ42 هنا {len(out['g42'])}")
    return 0


def _gh_get(path, params=None, raw=False):
    import requests
    tok, repo = os.environ.get("GITHUB_TOKEN", "").strip(), os.environ.get("GITHUB_REPOSITORY", "").strip()
    r = requests.get(f"https://api.github.com/repos/{repo}{path}", params=params or {}, timeout=60,
                     headers={"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json"})
    return r.content.decode("utf-8", "replace") if raw else r.json()   # السجلُّ text/plain بلا charset ⟵ requests يفكّه ISO-8859-1 فيعمى العربيّ (`42367314215`)


def cycle_from_logs(now=None):
    """§③-4: آخرُ `LOG_RUNS_MAX` تشغيلةٍ ناجحةٍ لـ`operator_entry.yml` في `LOG_DAYS` يومًا ⟵ أزواجُ (الكون، الثواني)."""
    now = now or dt.datetime.now(dt.timezone.utc)
    since = (now - dt.timedelta(days=LOG_DAYS)).date().isoformat()
    js = _gh_get("/actions/workflows/operator_entry.yml/runs", {"status": "success", "per_page": 100, "created": f">={since}"})
    runs = [r for r in (js.get("workflow_runs") or []) if r.get("conclusion") == "success"][:LOG_RUNS_MAX]
    pairs, used = [], 0
    for r in runs:
        try:
            jobs = _gh_get(f"/actions/runs/{r['id']}/jobs").get("jobs") or []
            for j in jobs:
                txt = _gh_get(f"/actions/jobs/{j['id']}/logs", raw=True)
                got = cycle_pairs(txt)
                if got:
                    pairs += got
                    used += 1
        except Exception:                                            # noqa: BLE001
            continue
    return pairs, used, len(runs)


def aggregate(chunks, pairs=None):
    """§③: من أجزاء `mode_chunk` (نقيّة على المُدخلات) ⟵ النتيجة."""
    days = sorted({d for c in chunks for d in c["days"]})
    nd = len(days) or 1
    sd = sum(c["sd"] for c in chunks)
    bf = sum(c["bars_fail"] for c in chunks)
    fires = [f for c in chunks for f in c["fires"]]
    tr = {"n": sum(c["truth"]["n"] for c in chunks), "hit": sum(c["truth"]["hit"] for c in chunks),
          "outside_u": sum(c["truth"]["outside_u"] for c in chunks), "miss": [m for c in chunks for m in c["truth"]["miss"]][:40]}
    tr["share"] = tr["hit"] / tr["n"] if tr["n"] else None
    tr["ok"] = bool(tr["share"] is not None and tr["share"] >= TRUTH_MIN)
    bars_ok = not sd or bf / sd <= BARS_FAIL_MAX
    res = {"days": nd, "sd": sd, "bars_fail": bf, "bars_ok": bars_ok, "truth": tr}
    usable = [f for f in fires if not f["split"] and r_class(f["R"]) is not None]
    nsplit = sum(1 for f in fires if f["split"])
    fU = [f for f in usable if f["U"]]
    fW = [f for f in usable if f["W"]]
    cls = lambda xs, k: sum(1 for f in xs if r_class(f["R"]) == k)   # noqa: E731
    falseU, falseW = cls(fU, "false"), cls(fW, "false")
    res["cost"] = {"firesU": len(fU), "firesW": len(fW), "falseU": falseU, "falseW": falseW,
                   "run100U": cls(fU, "run100"), "run100W": cls(fW, "run100"),
                   "fires_day_U": len(fU) / nd, "fires_day_W": len(fW) / nd,
                   "false_day_U": falseU / nd, "false_day_W": falseW / nd,
                   "added_false_day": round((falseW - falseU) / nd, 2),
                   "added_run100": cls(fW, "run100") - cls(fU, "run100"),
                   "precU": wilson(cls(fU, "run100"), len(fU)), "precW": wilson(cls(fW, "run100"), len(fW)),
                   "split_n": nsplit, "split_share": round(nsplit / len(fires), 4) if fires else None}
    add_r = cls(fW, "run100") - cls(fU, "run100")
    res["cost"]["false_per_added_runner"] = round((falseW - falseU) / add_r, 2) if add_r > 0 else None
    g = [r for c in chunks for r in c["g42"]]
    caught = [r for r in g if r["caughtW"]]
    lefts = [r["left"] for r in caught if r.get("left") is not None]
    res["g42"] = {"n": len(g), "caught": len(caught), "caught_actual": sum(1 for r in g if r["caughtW_actual"]),
                  "caughtU": sum(1 for r in g if r["caughtU"]),
                  "m_med": statistics.median([r["m"] for r in caught]) if caught else None,
                  "pct_med": statistics.median([r["pct"] for r in caught if r.get("pct") is not None]) if caught else None,
                  "left_med": round(statistics.median(lefts), 3) if lefts else None,
                  "gain_med": statistics.median([r["gain"] for r in caught if r.get("gain") is not None]) if caught else None,
                  "rows": sorted(g, key=lambda r: (r["d"], r["sym"]))}
    jW = [f for f in fW if f["j1W"]]
    added_false = [f for f in fW if r_class(f["R"]) == "false" and not f["U"]]
    res["j1"] = {"firesW_j1": len(jW), "false_j1": cls(jW, "false"), "run100_j1": cls(jW, "run100"),
                 "prec_j1": wilson(cls(jW, "run100"), len(jW)),
                 "added_false": len(added_false), "added_false_kept": sum(1 for f in added_false if f["j1W"]),
                 "cut_added_false": round(1 - sum(1 for f in added_false if f["j1W"]) / len(added_false), 3) if added_false else None,
                 "keep42": sum(1 for r in caught if r.get("j1W")),
                 "keep42_share": round(sum(1 for r in caught if r.get("j1W")) / len(caught), 3) if caught else None}
    wmax = [c["w_size"][d][1] for c in chunks for d in c["w_size"]]
    umax = [c["u_size"][d][1] for c in chunks for d in c["u_size"]]
    sps = sec_per_symbol(pairs or [])
    res["cycle"] = {"pairs": len(pairs or []), "sec_per_sym": sps,
                    "w_med": statistics.median(wmax) if wmax else None, "w_max": max(wmax) if wmax else None,
                    "u_med": statistics.median(umax) if umax else None,
                    "at_w_med": round(sps * statistics.median(wmax), 1) if (sps and wmax) else None,
                    "at_w_max": round(sps * max(wmax), 1) if (sps and wmax) else None,
                    "at600": round(sps * 600, 1) if sps else None, "at800": round(sps * 800, 1) if sps else None}
    return res


def _pc(x):
    return "—" if x is None else f"{x * 100:+.1f}%"


def _hm(m):
    return "—" if m is None else f"{int(m) // 60:02d}:{int(m) % 60:02d}"


def _p0(x, nd=1):
    return "—" if x is None else f"{x * 100:.{nd}f}%"


def _w(t):
    p, lo, hi = t
    return "—" if p is None else f"{p * 100:.1f}% [{lo * 100:.1f}، {hi * 100:.1f}]"


def report_lines(res, meta):
    c, g, j, cy, t = res["cost"], res["g42"], res["j1"], res["cycle"], res["truth"]
    L = ["# 👁️ `T-OEWIDE` — النتيجة (مولَّدةٌ بـ`oewide.py --mode pool` · لا رقمَ باليد)", "",
         f"**التشغيلة:** {meta.get('run')} · main `{(meta.get('sha') or '')[:9]}` · جلسات {res['days']} · رموزٌ-أيّام {res['sd']} · بلا شموع "
         f"{res['bars_fail']} ({'✅' if res['bars_ok'] else '⛔'})", "",
         f"**بوّابةُ صدق الإعادة (§④):** {t['hit']} من {t['n']} إطلاقًا حيًّا (مصحَّحًا) لرمزٍ في `U` أعادته إعادةُ `U` = "
         f"{_p0(t['share'])} ⟵ {'تُعتمد' if t['ok'] else '«لا قياس»'} · وإطلاقاتٌ حيّةٌ رمزُها خارج `U` المُعاد "
         f"{t['outside_u']}"]
    if t["miss"]:
        L.append("   لم تُعَد: " + " · ".join(t["miss"][:20]))
    if not (t["ok"] and res["bars_ok"]):
        L += ["", "⛔ **«لا قياس»** — البوّابةُ أو الشموع لم تعبر (§④) · ما يلي وصفٌ لا يُقرأ."]
    L += ["", "## ① الـ42 بكون `W` (العاملُ حيٌّ دائمًا — الحاكم)", "",
          f"- **الملتقَط {g['caught']} من {g['n']}** · وبالتشغيل الفعليّ (وصفًا) {g['caught_actual']} · وبكون `U` (شاهدُ ضبط) {g['caughtU']}",
          f"- الدقيقةُ بالوسيط {_hm(g['m_med'])} · من إغلاق الأمس {_pc(g['pct_med'])} · "
          f"**ما بقي من الحركة {_p0(g['left_med'])}** · المكسبُ المتاح بعده {_pc(g['gain_med'])}", "",
          "| الرمز | اليوم | R | `W` | الدقيقة | من الأمس | بقي | J1 | فعليًّا |", "|---|---|---|---|---|---|---|---|---|"]
    for r in g["rows"]:
        L.append(f"| {r['sym']} | {r['d'][5:]} | {_pc(r.get('R'))} | {'✅' if r['caughtW'] else '—'} | "
                 f"{_hm(r.get('m'))} | {_pc(r.get('pct'))} | "
                 f"{_p0(r.get('left'), 0)} | {'J1' if r.get('j1W') else '—'} | {'✅' if r['caughtW_actual'] else '—'} |")
    L += ["", "## ② الكلفة على الـ60 جلسة (العاملُ حيٌّ دائمًا)", "",
          "| | `U` (اليوم) | `W` (تحت المتابعة كاملًا) |", "|---|---|---|",
          f"| الإطلاقاتُ اليوميّة | {c['fires_day_U']:.1f} | {c['fires_day_W']:.1f} |",
          f"| الكاذبُ اليوميّ (R دون 50%) | {c['false_day_U']:.1f} | {c['false_day_W']:.1f} |",
          f"| راكضو +100% المُطلَق لهم | {c['run100U']} | {c['run100W']} |",
          f"| دقّةُ الإطلاق | {_w(c['precU'])} | {_w(c['precW'])} |", "",
          f"**الكاذبُ المُضاف يوميًّا (الحاكم): {c['added_false_day']}** · راكضو +100% المضافون {c['added_run100']} · كاذبٌ لكلّ راكضٍ مضاف "
          f"{c['false_per_added_runner']} · المستبعَدُ بالتقسيم {c['split_n']} ({_p0(c['split_share'])})",
          "", "## ③ ذراعُ J1 على `W`", "",
          f"- إطلاقاتُ J1 {j['firesW_j1']} · كاذبُها {j['false_j1']} · راكضوها +100% {j['run100_j1']} · دقّتُها {_w(j['prec_j1'])}",
          f"- من الكاذب **المُضاف** {j['added_false']}: يبقى بـJ1 {j['added_false_kept']} (يقصّ {_p0(j['cut_added_false'])})",
          f"- من الـ42 الملتقَطين يبقى بـJ1 **{j['keep42']}** ({_p0(j['keep42_share'])})",
          "", "## ④ الكلفةُ التشغيليّة", "",
          f"- من سجلّات العامل: {cy['pairs']} قراءةً «💰 التغطية» ⟵ **{'—' if cy['sec_per_sym'] is None else round(cy['sec_per_sym'] * 1000, 1)} ملّي ثانية لكلّ رمز** (الوسيط)",
          f"- الكونُ: `U` وسيطُ أقصاه اليوميّ {cy['u_med']} · `W` وسيطُه {cy['w_med']} وأقصاه {cy['w_max']}",
          f"- زمنُ الدورة المتوقَّع: `W` بالوسيط {cy['at_w_med']} ث · بالأقصى {cy['at_w_max']} ث · على 600 ⟵ {cy['at600']} ث · على 800 ⟵ {cy['at800']} ث "
          f"(الدورةُ كلَّ {CYCLE_S} ث · والفتحةُ {SLOT_S // 60} دقيقة)",
          f"- الشموع: Polygon `/v2/aggs` دقيقةً — طلبٌ لكلّ رمزٍ في كلّ دورة ⟵ على 800 ‏≈800 طلب/دقيقة · و8 خيوط (`LIQ_WORKERS`)",
          "", "## ⑤ التنبّؤات (منشورةٌ قبل الرقم)", ""]
    for k, ok, txt in predictions(res):
        L.append(f"- `{k}` {'✅' if ok else '❌'} {txt}")
    L += ["", "🔒 لا تغييرَ على العامل ولا الكون · الإعادةُ بقواعد اليوم على شموع Polygon المنشورة · والقرارُ للمالك."]
    return L


def mode_pool(paths):
    chunks = [json.load(open(p, encoding="utf-8")) for p in paths]
    pairs, used, nruns = cycle_from_logs()
    log(f"⏱️ سجلّاتُ العامل: {len(pairs)} قراءةً من {used} وظيفة ({nruns} تشغيلة)")
    res = aggregate(chunks, pairs)
    meta = {"run": os.environ.get("GITHUB_RUN_ID"), "sha": os.environ.get("GITHUB_SHA")}
    for ln in report_lines(res, meta):
        log(ln)
    log("OEWIDE_JSON " + json.dumps({"res": res, "preds": predictions(res), "meta": meta}, ensure_ascii=False, default=str))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("check", "chunk", "pool"), default="check")
    ap.add_argument("--part", type=int, default=0)
    ap.add_argument("--parts", type=int, default=1)
    ap.add_argument("--out", default="oewide_part.json")
    ap.add_argument("chunks", nargs="*")
    a = ap.parse_args(argv)
    if not contract_ok():
        log(f"⛔ بصمةُ العقد أو الـ42 تغيّرت — المدموجُ لا يُعدَّل (خروج {CONTRACT_RC})")
        return CONTRACT_RC
    if a.mode == "check":
        log("✅ العقدُ والـ42 مطابقان لبصمتيهما")
        return 0
    if a.mode == "chunk":
        return mode_chunk(a.part, a.parts, a.out)
    return mode_pool(a.chunks)


if __name__ == "__main__":
    sys.exit(main())
