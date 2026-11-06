#!/usr/bin/env python3
"""🚪📋 `T-LISTGATE` — «أيُّ بوّابةٍ تُخرج الراكضَ من القائمة الأسبوعيّة؟» (العقد `LISTGATE_prereg.md` مدموجٌ قبل أيّ رقم).

`--mode truth`  (git وحدَه): المجتمع (`gcross_runner_universe.json` ‏N) ‏+ الراكضون (`runners_60.json`) ‏+ الحقيقةُ من `reject_log.json` عند `N_commit`
                ‏+ `PASS(d)` و`walls_n` من `reject_stats` ⟵ `out/truth.json.gz`.
`--mode replay` (Polygon): `replay_hist` (قواعدُ يومها · K3) و`replay_today` (`r0`/`r1`) بـ`gate_inventory.run_once` بالاسم ⟵ `out/replay.json.gz`.
`--mode report`: الجداول والأحكام والتنبّؤات ⟵ `LISTGATE_RESULT.md` وسطرُ `LISTGATE_JSON`.
🔒 قراءةٌ فقط · لا تلغرام · لا تغييرَ على بوّابة · المرساةُ تُقاس ولا تُمسّ (H6) · وتخرج 9 إن تغيّرت بصمةُ العقد.
"""
import argparse
import datetime as dt
import gzip
import hashlib
import importlib.util
import json
import os
import statistics
import subprocess
import sys
import time
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
CONTRACT = os.path.join(HERE, "LISTGATE_prereg.md")
CONTRACT_SHA = "75f63b682430c5ee9877cd63bae644e0bd562577b905bbbc0307b6c04a985bf9"
CONTRACT_RC = 9
UNIVERSE = os.path.join(ROOT, "fm_forensics", "ema_cross", "data", "gcross_runner_universe.json")
RUNNERS = os.path.join(ROOT, "fm_forensics", "rrgate", "data", "runners_60.json")
PROV = os.path.join(ROOT, "faisal_engine", "data", "gate_provenance.json")
OUT = os.path.join(HERE, "out")
F_TRUTH = os.path.join(OUT, "truth.json.gz")
F_REPLAY = os.path.join(OUT, "replay.json.gz")
RESULT = os.path.join(HERE, "LISTGATE_RESULT.md")
NY = ZoneInfo("America/New_York")
AGREE_MIN = 0.80              # §② بوّابةُ صدق الإعادة
FLOOR = 20                    # §② §③ الأرضيّة
MISS_MAX = 0.10               # §⑤ شموعٌ متعذّرة
RISE_HIST = 214.7286870417835  # K3 — قبل #686
CHASE_MERGE = "2026-10-29T20:23:47+00:00"   # #686 (045176dc3) دُمج
BARS_FROM = "2024-06-01"      # 800 يوم قبل أوّل جلسة (= `rrgate.NW_FROM`)
BARS_TO = "2026-11-05"
LOOKBACK_DAYS = 800           # = `rebuild.HISTORY_DAYS`
PROV_LABEL = {"DIRECT_FAISAL_EVIDENCE": "فيصل (نصّ)", "INFERRED_FROM_FAISAL_EVIDENCE": "فيصل (مستنتجٌ من أسهمه)",
              "OWNER_POLICY": "مالك", "ENGINEERING_GUARD": "اجتهاد"}


def log(m=""):
    print(m, flush=True)


def contract_ok(path=CONTRACT):
    try:
        return hashlib.sha256(open(path, "rb").read()).hexdigest() == CONTRACT_SHA
    except OSError:
        return False


def _mod(name, rel):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, *rel.split("/")))
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def _rg():
    return _mod("listgate_rrgate", "fm_forensics/rrgate/rrgate.py")


def _gi():
    return _mod("listgate_gate_inventory", "faisal_engine/gate_inventory.py")


# ── pure ────────────────────────────────────────────────────────────────────────────────────────────────
def gate_of(key, reason_gate=None):
    """🔒 **نقيّة**: مفتاحُ جدار السجلّ/سببُ الرفض ⟵ البوّابة (`gate_inventory._reason_gate` بالاسم · وغيرُ المعروف كما هو ومنه «PASS»)."""
    if key in (None, ""):
        return None
    rg = reason_gate or _gi()._reason_gate
    return rg(str(key))


def prod_walls(entry):
    """🔒 **نقيّة**: مدخلُ `reject_log` ⟵ {رمز: مفتاحُ جداره} (الجدرانُ المعيَّنة تحمل عيّنتها وحدَها)."""
    out = {}
    for k, syms in ((entry or {}).get("walls") or {}).items():
        for s in syms or []:
            out[str(s).upper()] = k
    return out


def pass_load(stats_entry):
    """🔒 **نقيّة**: `PASS(d)` = `valid` − مجموعُ أعداد الجدران (§④) ⟵ عددٌ أو None."""
    try:
        return int(stats_entry["valid"]) - sum(int(v) for v in (stats_entry.get("stats") or {}).values())
    except (KeyError, TypeError, ValueError):
        return None


def cutoff_session(commit_iso, session_info=None):
    """🔒 **نقيّة** (بحقن `session_info`): آخرُ جلسةٍ أُغلقت قبل لحظة الالتزام (نيويورك · إغلاقُ التقويم)."""
    if session_info is None:
        import market_calendar as mc
        session_info = mc.session_info
    t = dt.datetime.fromisoformat(commit_iso).astimezone(NY)
    d = t.date()
    for _ in range(15):
        if d.weekday() < 5:
            si = session_info(d.isoformat()) or {}
            close = si.get("close_ny_min")
            if close is not None:
                end = dt.datetime(d.year, d.month, d.day, close // 60, close % 60, tzinfo=NY)
                if end <= t:
                    return d.isoformat()
        d -= dt.timedelta(days=1)
    return None


def rise_for(commit_iso):
    """🔒 **نقيّة**: K3 — `RECENT_RISE_BLOCK_PCT` يومَ الفرز: 214.73 قبل دمج #686 و35 بعده."""
    return RISE_HIST if dt.datetime.fromisoformat(commit_iso) < dt.datetime.fromisoformat(CHASE_MERGE) else 35.0


def agreement(pairs):
    """🔒 **نقيّة**: [(بوّابةُ الإنتاج، بوّابةُ الإعادة)] ⟵ (المتّفق، المقارَن) — المقارَنُ ما كانت إعادتُه جدارًا أو PASS."""
    cmp_ = [(a, b) for a, b in pairs if a and b and b not in ("NO_BARS", "ERROR")]
    return sum(1 for a, b in cmp_ if a == b), len(cmp_)


def admitted_by(r0, r1):
    """🔒 **نقيّة**: (r0، r1) ⟵ البوّابةُ التي تُدخل الصفَّ إن أُزيلت وحدَها أو None (§③): r0 جدارٌ g1 ∧ r1 = PASS."""
    if not r0 or r0[0] != "REJECT" or not r1 or r1[0] != "PASS":
        return None
    return r0[1]


def cost_verdict(lo_med, hi_med, pass_med):
    """🔒 **نقيّة** (§④): «داخل الميزانية» إن الأعلى ≤ PASS · «خارجها» إن الأدنى > PASS · وإلّا «غيرُ محسوم»."""
    if None in (lo_med, hi_med, pass_med):
        return "لا قياس"
    if hi_med <= pass_med:
        return "داخل الميزانية"
    if lo_med > pass_med:
        return "خارجها"
    return "غيرُ محسوم"


def selective_verdict(k, n, base_k, base_n, wilson=None, floor=FLOOR):
    """🔒 **نقيّة** (§③): «انتقائيّة» إن فاصلُ الدقّة فوق نسبة الراكضين في المجتمع لا يتداخل · و«لا قياس» دون الأرضيّة."""
    wilson = wilson or _rg().wilson
    if n < floor or not base_n:
        return "لا قياس"
    lo, _hi = wilson(k, n)
    return "انتقائيّة" if lo is not None and lo > base_k / base_n else "غيرُ انتقائيّة"


# ── truth (git) ────────────────────────────────────────────────────────────────────────────────────────
def _git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def _git_json(commit, path):
    try:
        return json.loads(_git("show", f"{commit}:{path}"))
    except (subprocess.CalledProcessError, ValueError):
        return None


def mode_truth():
    U = json.load(open(UNIVERSE, encoding="utf-8"))
    R = json.load(open(RUNNERS, encoding="utf-8"))
    r50 = {(x["sym"], x["day"]) for x in R["rows"]}
    r100 = {(x["sym"], x["day"]) for x in R["rows"] if float(x["R"]) >= 1.0}
    sessions, rows, pop = {}, [], {"runners50": len(r50), "runners100": len(r100), "in_N": 0, "in_L": 0, "neither": 0}
    for d in sorted(U["days"]):
        v = U["days"][d]
        N, L, c = set(v.get("N") or []), set(v.get("L") or {}), v.get("N_commit")
        for s, dd in r50:
            if dd == d:
                pop["in_N" if s in N else ("in_L" if s in L else "neither")] += 1
        if not c:
            continue
        rl = _git_json(c, "reject_log.json") or []
        last = max(rl, key=lambda e: e.get("date") or "") if rl else {}
        ww = _git_json(c, "weekly_watchlist.json") or {}
        st = next((e for e in reversed(ww.get("reject_stats") or []) if e.get("date") == last.get("date")), None)
        ct = _git("show", "-s", "--format=%cI", c).strip()
        sessions[d] = {"commit": c, "commit_time": ct, "sort_date": last.get("date"), "cutoff": cutoff_session(ct),
                       "rise": rise_for(ct), "pass": pass_load(st), "walls_n": last.get("walls_n") or {},
                       "sampled": last.get("sampled") or [], "n_N": len(N)}
        pw = prod_walls(last)
        for s in sorted(N):
            rows.append({"sym": s, "day": d, "r50": int((s, d) in r50), "r100": int((s, d) in r100), "prod_key": pw.get(s)})
    os.makedirs(OUT, exist_ok=True)
    with gzip.open(F_TRUTH, "wt", encoding="utf-8") as f:
        json.dump({"contract_sha": CONTRACT_SHA, "population": pop, "sessions": sessions, "rows": rows}, f, ensure_ascii=False)
    log(f"🗂️ truth: جلسات {len(sessions)} · صفوف {len(rows)} · راكضو N {pop['in_N']} (L {pop['in_L']} · خارج {pop['neither']})")
    return 0


# ── replay (Polygon) ───────────────────────────────────────────────────────────────────────────────────
def frame_until(rows, splits, cutoff, rg=None, rb=None):
    """شموعٌ حتى `cutoff` (شاملة) بمقياسها (`rebuild.asof_scale` بالاسم) ونافذةُ 800 يوم ⟵ DataFrame أو None."""
    rg, rb = rg or _rg(), rb or _rg()._rebuild()
    nxt = (dt.date.fromisoformat(cutoff) + dt.timedelta(days=1)).isoformat()
    lo = (dt.date.fromisoformat(nxt) - dt.timedelta(LOOKBACK_DAYS)).isoformat()
    sub = [x for x in rb.asof_scale(rows, splits, nxt) if x[0] >= lo]
    return rg._df(sub) if sub else None


def replay_row(S, gi, sym, df, rise_hist):
    """(`replay_hist`، `r0`، `r1`) لصفٍّ واحد — `run_once` بالاسم · و`RECENT_RISE_BLOCK_PCT` يُضبط ويُستعاد."""
    keep = S.CONFIG.get("RECENT_RISE_BLOCK_PCT")
    try:
        S.CONFIG["RECENT_RISE_BLOCK_PCT"] = rise_hist
        h = gi.run_once(S, sym, df, ())
        S.CONFIG["RECENT_RISE_BLOCK_PCT"] = 35.0
        r0 = gi.run_once(S, sym, df, ())
        r1 = None
        if r0[0] == "REJECT":
            g1 = gi._reason_gate(r0[1])
            if g1 in gi.NEUTRAL:
                r1 = gi.run_once(S, sym, df, (g1,))
    finally:
        S.CONFIG["RECENT_RISE_BLOCK_PCT"] = keep
    return h, r0, r1


def mode_replay(key, fetch=None):
    T = json.load(gzip.open(F_TRUTH, "rt", encoding="utf-8"))
    rg = _rg()
    S = rg._S()
    gi = _gi()
    syms = sorted({r["sym"] for r in T["rows"]})
    if fetch is None:
        bars, diag = rg._bars_many(syms, BARS_FROM, BARS_TO, key)
        splits = rg._splits_by(BARS_FROM, BARS_TO, key)
    else:
        bars, diag, splits = fetch(syms)
    out, t0 = [], time.time()
    for n, r in enumerate(T["rows"]):
        ses = T["sessions"][r["day"]]
        rows = bars.get(r["sym"]) or []
        df = frame_until(rows, splits.get(r["sym"]) or [], ses["cutoff"], rg) if rows and ses.get("cutoff") else None
        if df is None or len(df) == 0:
            out.append({"h": ["NO_BARS", ""], "r0": None, "r1": None})
            continue
        h, r0, r1 = replay_row(S, gi, r["sym"], df, ses["rise"])
        out.append({"h": list(h), "r0": list(r0), "r1": (list(r1) if r1 else None)})
        if n % 2000 == 0:
            log(f"replay {n + 1}/{len(T['rows'])} · {round(time.time() - t0)}s")
    with gzip.open(F_REPLAY, "wt", encoding="utf-8") as f:
        json.dump({"contract_sha": CONTRACT_SHA, "bars_diag": diag, "replay": out}, f, ensure_ascii=False)
    log(f"🔁 replay: {len(out)} صفًّا · شموع {diag}")
    return 0


# ── report ─────────────────────────────────────────────────────────────────────────────────────────────
def _pct(k, n):
    return f"{100.0 * k / n:.1f}%" if n else "—"


def _ci(w):
    return f"[{100 * w[0]:.1f}، {100 * w[1]:.1f}]" if w and None not in w else "—"


def final_gates(T, RP, gate=None):
    """🔒 **نقيّة** (بحقن `gate`): لكلّ صفٍّ (البوّابة، المصدر) ومعها الاتّفاق — `prod` أوّلًا ثمّ `replay_hist` إن عبرت بوّابةُ الصدق (§②)."""
    gate = gate or gate_of
    hist = []
    for x in RP:
        h = x.get("h") or [None, None]
        hist.append(gate(h[1]) if h[0] == "REJECT" else h[0])
    prod = [gate(r.get("prod_key")) for r in T["rows"]]
    k, n = agreement([(p, h) for p, h in zip(prod, hist) if p])
    ok = bool(n) and k / n >= AGREE_MIN
    out = []
    for p, h in zip(prod, hist):
        if p:
            out.append((p, "prod"))
        elif ok and h not in (None, "NO_BARS", "ERROR"):
            out.append((h, "replay"))
        elif h in ("NO_BARS", "ERROR"):
            out.append(("غيرُ مقيس", "none"))
        else:
            out.append(("غيرُ موثوق", "none"))
    return out, (k, n, ok)


def mode_report():
    T = json.load(gzip.open(F_TRUTH, "rt", encoding="utf-8"))
    RP = json.load(gzip.open(F_REPLAY, "rt", encoding="utf-8"))["replay"]
    rg, gi = _rg(), _gi()
    S = rg._S()
    prov = {g["id"]: g for g in json.load(open(PROV, encoding="utf-8"))["gates"]}
    rows = T["rows"]
    fin, (ak, an, aok) = final_gates(T, RP)
    nob = sum(1 for x in RP if (x.get("h") or [None])[0] in ("NO_BARS", "ERROR"))
    miss_ok = nob <= MISS_MAX * len(rows)

    def label(g):
        pid = gi.GATE_ID.get(g)
        p = (prov.get(pid) or {}).get("provenance")
        return PROV_LABEL.get(p, "—"), ", ".join(f"{k}={S.CONFIG.get(k)}" for k in (gi.NEUTRAL.get(g) or {})) or ("ANCHOR_MODE=" + str(S.CONFIG.get("ANCHOR_MODE")) if g == "ANCHOR" else "—")

    run_ix = [i for i, r in enumerate(rows) if r["r50"]]
    base_ix = [i for i, r in enumerate(rows) if not r["r50"]]
    nR, nB = len(run_ix), len(base_ix)
    gates = sorted({fin[i][0] for i in range(len(rows))}, key=lambda g: (-sum(1 for i in run_ix if fin[i][0] == g), g))
    L = ["# 🚪📋 `T-LISTGATE` — النتيجة (مولَّدةٌ بـ`listgate.py --mode report` · لا رقمَ باليد)", ""]
    pop = T["population"]
    L += [f"**المجتمع:** راكضو ‏+50% {pop['runners50']} (‏+100% {pop['runners100']}) · في «تحت المتابعة» عشيّتَهم **{pop['in_N']}** · في القائمة {pop['in_L']} · خارج الاثنين {pop['neither']} ·"
          f" صفوفُ «تحت المتابعة» {len(rows)} (راكضون {nR} · أساس {nB}) · جلسات {len(T['sessions'])}.", "",
          f"**بوّابةُ الصدق (§②):** الإعادةُ بقواعد يومها تتّفق مع سجلّ الإنتاج في **{ak} من {an} ({_pct(ak, an)})** ⟵ {'تُعتمد' if aok else 'غيرُ موثوقة — الجدولُ على سجلّ الإنتاج وحدَه'} ·"
          f" شموعٌ متعذّرة {nob} ({_pct(nob, len(rows))}) ⟵ {'ضمن الحدّ' if miss_ok else 'فوق 10% — أجزاءُ الإعادة «لا قياس»'}.", "",
          "## ② البوّابةُ الأولى في آخر فرزٍ قبل الركض", "",
          "| البوّابة | المصدر | العتبة النافذة | راكضون +50% | حصّتهم [Wilson] | أساس | حصّته [Wilson] | الحكم | +100% |", "|---|---|---|---|---|---|---|---|---|"]
    verdicts = {}
    for g in gates:
        kr = sum(1 for i in run_ix if fin[i][0] == g)
        kb = sum(1 for i in base_ix if fin[i][0] == g)
        k1 = sum(1 for i in run_ix if fin[i][0] == g and rows[i]["r100"])
        v = rg.compare_verdict(kr, nR, kb, nB, floor=FLOOR) if g not in ("غيرُ مقيس", "غيرُ موثوق") else "—"
        verdicts[g] = v
        src, cfg = label(g)
        L.append(f"| {g}{' 🔒H6' if g == 'ANCHOR' else ''} | {src} | {cfg} | {kr} | {_pct(kr, nR)} {_ci(rg.wilson(kr, nR))} | {kb} | {_pct(kb, nB)} {_ci(rg.wilson(kb, nB))} | {v} | {k1} |")
    rr_run = sum(1 for i in run_ix if fin[i][0] == "SOFT" and str(rows[i].get("prod_key") or (RP[i].get("h") or ["", ""])[1]).startswith("RR+"))
    src_n = {s: sum(1 for i in range(len(rows)) if fin[i][1] == s) for s in ("prod", "replay", "none")}
    L += ["", f"وصفًا: «النواقص» بين الراكضين منها {rr_run} والعائدُ/المخاطرة ضمنها («RR+نواقص») · مصدرُ البوّابة: سجلُّ الإنتاج {src_n['prod']} · الإعادة {src_n['replay']} · بلا {src_n['none']}.", ""]
    # ③ الإزالة
    adm = [admitted_by(tuple(x["r0"]) if x.get("r0") else None, tuple(x["r1"]) if x.get("r1") else None) for x in RP]
    adm_g = [gi._reason_gate(a) if a else None for a in adm]
    valid = [i for i, x in enumerate(RP) if (x.get("r0") or [None])[0] in ("REJECT", "PASS")]
    base_k = sum(1 for i in valid if rows[i]["r50"])
    base_n = len(valid)
    agates = sorted({g for g in adm_g if g}, key=lambda g: -sum(1 for i in valid if adm_g[i] == g and rows[i]["r50"]))
    L += ["## ③ إزالةُ كلّ بوّابةٍ وحدَها (بقواعد اليوم · `analyze_ticker` وحدَه)", "",
          f"نسبةُ الراكضين في المجتمع المُعاد: {base_k} من {base_n} ({_pct(base_k, base_n)}) · وعابرو `analyze_ticker` بقواعد اليوم بلا إزالة: "
          f"{sum(1 for i in valid if RP[i]['r0'][0] == 'PASS')}.", "",
          "| البوّابة | المصدر | راكضون يدخلون | غيرُ راكضين | الدقّة [Wilson] | انتقائيّة؟ | كلفةٌ يوميّة دنيا (وسيط) | عُليا (وسيط) | PASS (وسيط) | الميزانية 2× |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    days = sorted(T["sessions"])
    pass_med = statistics.median([T["sessions"][d]["pass"] for d in days if T["sessions"][d].get("pass") is not None] or [0]) if days else None
    removal = {}
    for g in agates:
        R_ = sum(1 for i in valid if adm_g[i] == g and rows[i]["r50"])
        Q_ = sum(1 for i in valid if adm_g[i] == g and not rows[i]["r50"])
        sel = selective_verdict(R_, R_ + Q_, base_k, base_n, rg.wilson)
        lo_d, hi_d = [], []
        for d in days:
            ses = T["sessions"][d]
            if ses.get("pass") is None:
                continue
            lo_d.append(sum(1 for i in valid if rows[i]["day"] == d and adm_g[i] == g))
            hi_d.append(sum(int(n) for k, n in (ses.get("walls_n") or {}).items() if gate_of(k) == g))
        lo_m = statistics.median(lo_d) if lo_d else None
        hi_m = statistics.median(hi_d) if hi_d else None
        cv = cost_verdict(lo_m, hi_m, pass_med)
        removal[g] = {"R": R_, "Q": Q_, "sel": sel, "cost": cv, "lo": lo_m, "hi": hi_m}
        L.append(f"| {g}{' 🔒H6' if g == 'ANCHOR' else ''} | {label(g)[0]} | {R_} | {Q_} | {_pct(R_, R_ + Q_)} {_ci(rg.wilson(R_, R_ + Q_))} | {sel} | {lo_m} | {hi_m} | {pass_med} | {cv} |")
    nr_in = sum(1 for i in valid if rows[i]["r50"])
    none_single = sum(1 for i in valid if rows[i]["r50"] and not adm_g[i] and RP[i]["r0"][0] == "REJECT")
    L += ["", f"راكضون لا تُدخلهم إزالةُ أيّ بوّابةٍ وحدَها (بوّابتان فأكثر): {none_single} من {nr_in} · ⚠️ «يدخل» = يعبر `analyze_ticker` وما بعده (الشورت/الفلوت/المتاح/السلامة/السعة) لا يُعاد ⟵ حدٌّ أعلى.", ""]
    # ⑥ التنبّؤات
    top = gates[0] if gates else None
    maxR = max((v["R"] for v in removal.values()), default=0)
    preds = {
        "P1": an > 0 and ak / an >= AGREE_MIN,
        "P2": top == "ANCHOR",
        "P3": verdicts.get("ANCHOR") in ("لا فرق", "أقلّ"),
        "P4": not [g for g, v in verdicts.items() if v == "أكثرُ تمثيلًا" and g != "M4_RISE"],
        "P5": nr_in > 0 and maxR <= 0.25 * nr_in,
        "P6": not [g for g, v in removal.items() if v["sel"] == "انتقائيّة"],
        "P7": (removal.get("ANCHOR") or {}).get("cost") in ("خارجها", "غيرُ محسوم"),
    }
    L += ["## ⑥ التنبّؤات (منشورةٌ قبل الرقم)", ""] + [f"- `{k}` {'✅' if v else '❌'}" for k, v in preds.items()]
    L += ["", "🔒 لا تغييرَ على أيّ بوّابة · المرساةُ (H6) تُقاس ولا تُمسّ · وأيُّ إزالةٍ عقدٌ آخر (ثلاث سنوات PIT · ضبطُ زخم) وقرارُ المالك."]
    open(RESULT, "w", encoding="utf-8").write("\n".join(L) + "\n")
    js = {"agree": [ak, an], "nob": nob, "runners_in_N": pop["in_N"], "first_gate": {g: sum(1 for i in run_ix if fin[i][0] == g) for g in gates},
          "verdicts": verdicts, "removal": removal, "pass_med": pass_med, "preds": preds}
    log("LISTGATE_JSON " + json.dumps(js, ensure_ascii=False))
    log("\n".join(L))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("truth", "replay", "report"), required=True)
    a = ap.parse_args(argv)
    if not contract_ok():
        log(f"⛔ بصمةُ العقد تغيّرت — خروج {CONTRACT_RC}")
        return CONTRACT_RC
    if a.mode == "truth":
        return mode_truth()
    if a.mode == "replay":
        key = (os.environ.get("POLYGON_API_KEY") or "").strip()
        if not key:
            log("🔑 لا مفتاحَ Polygon — خروج 2")
            return 2
        return mode_replay(key)
    return mode_report()


if __name__ == "__main__":
    sys.exit(main())
