"""📈✖️🏃 «التقاطع على راكض الارتكاز» — `T-GCROSS` الملحق 2 (أمرُ المالك 2026-11-05 «قبل الإغلاق — ذراع أخيرة بالتعريف الممتد الذي ثبت»).

**العقد:** `fm_forensics/ema_cross/T_GCROSS_ADDENDUM_2.md` (مدموجٌ قبل أيّ رقم · `GCX2`) — كلُّ بندٍ هنا برقمه هناك.
**الكون** = رموزُ قائمة البوت (`weekly_watchlist.json` · `stocks`) ∪ «تحت المتابعة» (`near_watch.json` · آخرُ فرز) **كما كانا قبل 04:00 نيويورك
من كلّ جلسة** — مجمَّدٌ من تاريخ git في `fm_forensics/ema_cross/data/gcross_runner_universe.json` (`--mode freeze` محلّيًّا · قبل أيّ رقم) ومعه
وقفُ البوت لكلّ رمزٍ في القائمة وأبكرُ مِرساةِ «هنا الدخول» لكلّ رمزٍ ويوم (`tierlink_probe.anchor_history` بالاسم).
**التعريفُ الممتدّ (الملحق 1) بالاسم:** `ema_cross_live.ext_series` · `day_crosses` · `cycles` · `cycle_from` · `control_cycles` · `cross_level` ·
`summarize` · `cluster_boot` · و`golden_cross_scan.fetch_30m` · `to_4h(ext=True)` · `gcrosses` — لا تعريفَ جديدٌ للتقاطع.

الأوضاع: `freeze` (محلّيٌّ: يبني ملفَّ الكون من git ويطبع العدَّ وحدَه) · `measure` (الرنر: ①-⑤ والذراع أ ومثالُ OMH).
🔒 قراءةٌ فقط · لا تلغرام · لا إنتاج · لا جذور · لا H6 · لا بوّابة · **ولا بناءَ حيٍّ قبل الحكم** (أمرُ المالك).
"""
import argparse
import datetime as dt
import json
import os
import random
import subprocess
import sys

import ema_cross_live as G
import golden_cross_scan as GA

V, V3, V4, NY = G.V, G.V3, G.V4, G.NY

UNIVERSE_FILE = "fm_forensics/ema_cross/data/gcross_runner_universe.json"
END_DAY = "2026-11-04"                       # §① الجلساتُ الستّون نفسُها (`§⑤` و`§⑦`)
N_SESSIONS = 60
RUN50, RUN100 = 0.50, 1.00                   # §② ① «+50% و+100% داخل الجلسة» — أمرُ المالك
WIN20 = 0.20                                 # §② ② «ولم يبلغ +20%» — أمرُ المالك
FOLLOW_A = 20                                # §② الذراع أ: «سبق راكضًا» = خلال 20 جلسة بعد يوم التقاطع (نايف «أسبوعي أو شهري» ⟵ شهر)
CUTOFF_NY_MIN = 4 * 60                       # §① الكونُ كما كان قبل 04:00 نيويورك من الجلسة
SINCE_ALERTS = "2026-08-11"
WORKERS = 16


def log(m=""):
    print(m, flush=True)


# ── التجميدُ من git (محلّيًّا · قبل أيّ رقم) ───────────────────────────────────────────────────────────────
def sessions(MC, end_day=END_DAY, n=N_SESSIONS):
    return G.sessions_before(MC, end_day, n)


def _commits(path):
    """[(ثانيةُ الالتزام، hash)] لملفٍّ على HEAD تصاعديًّا."""
    out = subprocess.run(["git", "log", "--format=%ct %H", "--", path], capture_output=True, text=True, check=True).stdout.split()
    pairs = [(int(out[i]), out[i + 1]) for i in range(0, len(out), 2)]
    return sorted(pairs)


def asof(pairs, ts):
    """آخرُ التزامٍ وقتُه قبل `ts` (ثانية) ⟵ hash أو None."""
    best = None
    for t, h in pairs:
        if t < ts:
            best = h
        else:
            break
    return best


def list_members(doc):
    """§① رموزُ القائمة = كلُّ `stocks` غيرِ المشطوبة ⟵ {رمز: {stop · added}}."""
    out = {}
    for s in (doc or {}).get("stocks") or ():
        sym = str(s.get("symbol") or "").upper()
        if not sym or s.get("status") == "stopped":
            continue
        out[sym] = {"stop": s.get("stop"), "added": s.get("added")}
    return out


def near_members(doc):
    """§① «تحت المتابعة» = مداخلُ آخر فرزٍ في الملفّ (`last_seen` = أكبرُها) ⟵ [رموز]."""
    if not isinstance(doc, dict) or not doc:
        return []
    last = max(str(v.get("last_seen") or "") for v in doc.values() if isinstance(v, dict))
    return sorted(str(k).upper() for k, v in doc.items() if isinstance(v, dict) and str(v.get("last_seen") or "") == last)


def first_anchor(v, day):
    """§② ③ أبكرُ مِرساةٍ لليوم من لقطة آخر اليوم: `anchor_ms` و`rearm_prev.anchor_ms` (إن كان يومُها نيويوركيًّا هو اليوم) ⟵ (ms، سعر) أو None."""
    cands = []
    for a in (v, (v or {}).get("rearm_prev") or {}):
        try:
            ms, px = int(a["anchor_ms"]), float(a["anchor_price"])
        except (KeyError, TypeError, ValueError):
            continue
        if dt.datetime.fromtimestamp(ms / 1000, tz=NY).date().isoformat() == day:
            cands.append((ms, px))
    return min(cands) if cands else None


def freeze(MC, path=UNIVERSE_FILE):
    from tierlink_probe import anchor_history
    days = sessions(MC)
    wl, nw = _commits("weekly_watchlist.json"), _commits("near_watch.json")
    out = {"end_day": END_DAY, "sessions": days, "days": {}, "alerts": {}}
    for d in days:
        ts = int(V3.ny_ts(d, CUTOFF_NY_MIN))
        hw, hn = asof(wl, ts), asof(nw, ts)
        L = list_members(json.loads(subprocess.run(["git", "show", f"{hw}:weekly_watchlist.json"], capture_output=True, text=True).stdout)) if hw else {}
        N = near_members(json.loads(subprocess.run(["git", "show", f"{hn}:near_watch.json"], capture_output=True, text=True).stdout)) if hn else []
        out["days"][d] = {"L": L, "N": N, "L_commit": hw, "N_commit": hn}
    for (d, sym), v in sorted(anchor_history(SINCE_ALERTS).items()):
        if d in out["days"]:
            fa = first_anchor(v, d)
            if fa:
                out["alerts"].setdefault(d, {})[sym] = {"ms": fa[0], "px": fa[1]}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, sort_keys=True, indent=0)
    u = [len(set(v["L"]) | set(v["N"])) for v in out["days"].values()]
    log(f"🧊 الكون مجمَّدٌ في {path}: {len(days)} جلسة ({days[0]} ⟵ {days[-1]}) · الرموزُ-الأيّام {sum(u)} · الكونُ اليوميّ من {min(u)} إلى {max(u)} · "
        f"رموزٌ متمايزة {len({s for v in out['days'].values() for s in set(v['L']) | set(v['N'])})} · مراسي «هنا الدخول» "
        f"{sum(len(v) for v in out['alerts'].values())} (لم أقرأها)")
    return 0


# ── دوالُّ نقيّة (بلا شبكة · مقفولةٌ في السويّة) ────────────────────────────────────────────────────────
def universe_of(U, d):
    """§① الكونُ يومَ d ⟵ (مجموعةُ الرموز، {رمز: وقفُ القائمة})."""
    v = U["days"].get(d) or {}
    return set(v.get("L") or {}) | set(v.get("N") or ()), dict(v.get("L") or {})


def run_ratio(day_bars, prev_adj):
    """§② ① أعلى `h` في نافذة اليوم [04:00، 20:00) ÷ إغلاقِ الأمس المسوّى − 1 ⟵ (النسبة، دقيقةُ القمّة) أو (None، None)."""
    b = G.regular(day_bars, G.EXT_OP, G.EXT_CL)
    if not b or not prev_adj:
        return None, None
    top = max(b, key=lambda x: x[2])
    return top[2] / prev_adj - 1.0, top[0]


def first_pos(xs):
    return next((x for x in xs if x["sign"] == "+"), None)


def win_after(series, x, pct=WIN20):
    """§② ② هل بلغ أعلى `h` بعد دقيقة التقاطع (حتى 20:00) إغلاقَه ×(1+pct)؟"""
    hi = max((b[2] for b in series[x["i"] + 1:]), default=None)
    return hi is not None and hi >= x["px"] * (1.0 + pct)


def exits(series, xs, x, stop=None):
    """§② ④ من دخولٍ بإغلاق التقاطع الإيجابيّ x ⟵ {neg · close · stop} لكلٍّ (سعرُ الخروج، دقيقتُه، النتيجة، حصّةُ الحركة) · وH أعلى `h` بعد الدخول.
    الحصّة = (الخروج − الدخول) ÷ (H − الدخول) وNone إن لم يعلُ H فوق الدخول. والوقفُ: أوّلُ شمعةٍ بعد الدخول أدناها عند الوقف أو تحته ⟵ يُنفَّذ
    بالوقف أو بافتتاحها إن فتحت تحته · وإلّا الإمساكُ حتى آخر شمعة · وبلا وقفٍ ⟵ None."""
    e_i, e = x["i"], x["px"]
    after = series[e_i + 1:]
    H = max((b[2] for b in after), default=e)

    def mk(px, m):
        return {"px": px, "m": m, "ret": px / e - 1.0, "share": (px - e) / (H - e) if H > e else None}
    neg = next((y for y in xs if y["sign"] == "-" and y["i"] > e_i), None)
    last = series[-1]
    out = {"H": H, "neg": mk(neg["px"], neg["m"]) if neg else mk(last[4], last[0]), "close": mk(last[4], last[0]), "stop": None}
    if stop:
        hit = next((b for b in after if b[3] <= stop), None)
        out["stop"] = mk(min(stop, hit[1]), hit[0]) if hit else mk(last[4], last[0])
    return out


def split_factor_since(splits, after_day, upto_day):
    """§② ④ معاملُ تسوية وقفٍ مخزَّن يومَ `after_day` إلى أساس `upto_day`: Π split_from ÷ split_to لكلّ تقسيمٍ نُفِّذ بعده حتى `upto_day` (كـ`V4.price_factor`)."""
    f = 1.0
    for ex, sf, stt in splits or ():
        if after_day < ex <= upto_day and sf and stt:
            f *= sf / stt
    return f


def symday(sym, d, prev_d, by, prev_adj, f, splits_today, stop, alert, seed=G.SEED):
    """كلُّ ما يلزم من رمزٍ ويوم (نقيّ على الشموع المجلوبة) ⟵ صفٌّ مضغوط · وNone إن لم تكن شموع."""
    day_b = (by or {}).get(d) or []
    series, k = G.ext_series((by or {}).get(prev_d) or [], day_b, f)
    if len(series) - k < 2:
        return None
    row = {"sym": sym, "day": d, "k": k, "split": bool(splits_today)}
    r, top_m = run_ratio(day_b, prev_adj)
    row.update({"R": r, "top_m": top_m})
    xs = G.day_crosses(series)
    pos = [x for x in xs if x["sign"] == "+"]
    row["npos"] = len(pos)
    cyc = G.cycles(series, xs, lambda x: True)
    rng = random.Random(f"{seed}:{sym}:{d}")
    ctl = G.control_cycles(series, xs, list(range(k, len(series))), len(cyc), rng)
    row["arm"] = [c["ret"] for c in cyc]
    row["ctl"] = [c["ret"] for c in ctl]
    fp = first_pos(xs)
    if fp is not None:
        row["fp"] = {"m": fp["m"], "px": fp["px"], "lvl": G.cross_level(series, fp), "win20": win_after(series, fp)}
        if r is not None and r >= RUN50:
            ex = exits(series, xs, fp, stop)
            row["ex"] = {"H": ex["H"], **{p: ex[p] for p in ("neg", "close", "stop")}}
    row["alert"] = alert
    return row


def golden_follow(gx_days, run_days, sess, follow=FOLLOW_A):
    """§② الذراع أ: لكلّ يومِ تقاطعٍ ذهبيّ ⟵ هل للرمز نفسِه يومُ ركضٍ (+50%) في الجلسات (يوم التقاطع، +follow] · ونافذتُه كاملة؟"""
    idx = {d: i for i, d in enumerate(sess)}
    out = []
    for d in gx_days:
        i = idx.get(d)
        if i is None:
            continue
        nxt = sess[i + 1:i + 1 + follow]
        out.append({"day": d, "hit": any(x in run_days for x in nxt), "full": len(nxt) == follow, "same": d in run_days})
    return out


# ── القياس (الرنر) ─────────────────────────────────────────────────────────────────────────────────────────
GAP = ("2026-09-29", "2026-10-12")           # فجوةُ مصدر «هنا الدخول» (انقطاعُ Polygon) — تُعَدّ ولا تُستكمَل
COVER_MIN = 0.90                             # §③ تغطيةُ الرموز-الأيّام بالشموع دون 90% ⟵ «لا قياس»


def _pct(v):
    return "—" if v is None else f"{v * 100:+.2f}%"


def _share_txt(v):
    return "—" if v is None else f"{v * 100:.0f}%"


def all_splits(net, d0, d1):
    rows, ok = net.paged("/v3/reference/splits", {"execution_date.gte": d0, "execution_date.lte": d1, "limit": 1000}, cap=200)
    out = {}
    for r in rows:
        try:
            out.setdefault(str(r.get("ticker") or "").upper(), []).append((str(r["execution_date"]), float(r["split_from"]), float(r["split_to"])))
        except (KeyError, TypeError, ValueError):
            continue
    return out, ok


def summarize_rows(rows, U, sess):
    """التجميع (نقيّ على الصفوف) ⟵ dict الملخّص · يُطبع ويُختبر."""
    ok_rows = [r for r in rows if not r["split"]]
    run50 = [r for r in ok_rows if r["R"] is not None and r["R"] >= RUN50]
    run100 = [r for r in ok_rows if r["R"] is not None and r["R"] >= RUN100]
    by_day50 = {d: sum(1 for r in run50 if r["day"] == d) for d in sess}
    by_day100 = {d: sum(1 for r in run100 if r["day"] == d) for d in sess}
    big_days = [d for d in sess if by_day100[d]]
    two = []
    for d in big_days:
        cr = [r for r in ok_rows if r["day"] == d and r.get("fp")]
        w = sum(1 for r in cr if r["fp"]["win20"])
        two.append({"day": d, "crossers": len(cr), "win20": w, "false": len(cr) - w, "run100": by_day100[d]})
    th = []
    for r in sorted(run50, key=lambda r: (r["day"], r["sym"])):
        fp, al = r.get("fp"), r.get("alert")
        am = None if not al else int((al["ms"] / 1000 - V3.ny_ts(r["day"], 0)) // 60)
        th.append({"sym": r["sym"], "day": r["day"], "R": r["R"], "top_m": r["top_m"], "fp_m": None if not fp else fp["m"],
                   "fp_px": None if not fp else fp["px"], "fp_lvl": None if not fp else fp["lvl"], "al_m": am,
                   "al_px": None if not al else al["px"], "gap": GAP[0] <= r["day"] <= GAP[1], "ex": r.get("ex")})
    four = {}
    for pol in ("neg", "close", "stop"):
        xs = [t["ex"][pol] for t in th if t["ex"] and t["ex"][pol]]
        sh = [x["share"] for x in xs if x["share"] is not None]
        four[pol] = {"n": len(xs), "ret_med": G._median([x["ret"] for x in xs]), "share_med": G._median(sh),
                     "share_mean": (sum(sh) / len(sh)) if sh else None}
    pairs_all = {(r["sym"], r["day"]): (r["arm"], r["ctl"]) for r in ok_rows if r["arm"]}
    pairs_run = {k: v for k, v in pairs_all.items() if any(k == (r["sym"], r["day"]) for r in run50)}
    five = {}
    for nm, pr in (("all", pairs_all), ("run50", pairs_run)):
        arm = [{"ret": x, "maxp": 0.0, "dur": 0, "exit": "neg"} for a, _c in pr.values() for x in a]
        ctl = [{"ret": x, "maxp": 0.0, "dur": 0, "exit": "neg"} for _a, c in pr.values() for x in c]
        sa, sc = G.summarize(arm), G.summarize(ctl)
        boot = G.cluster_boot(pr) if len(arm) >= G.MIN_CYCLES else (None, None, None)
        five[nm] = {"n": sa["n"], "sd": len(pr), "arm_med": sa["median"], "arm_mean": sa["mean"], "ctl_med": sc["median"], "ctl_mean": sc["mean"],
                    "arm_neg": sa["neg"][0], "ctl_neg": sc["neg"][0], "boot": boot,
                    "verdict": "لا قياس" if len(arm) < G.MIN_CYCLES else ("يتفوّق" if boot[1] is not None and boot[1] > 0 else "لا يتفوّق")}
    return {"rows": len(rows), "split_days": len(rows) - len(ok_rows), "R_unknown": sum(1 for r in ok_rows if r["R"] is None),
            "run50": len(run50), "run100": len(run100), "run50_syms": len({r["sym"] for r in run50}), "run100_syms": len({r["sym"] for r in run100}),
            "days_run50": sum(1 for d in sess if by_day50[d]), "days_run100": len(big_days),
            "med_run50_day": G._median([by_day50[d] for d in sess]), "two": two, "three": th, "four": four, "five": five}


def final_verdict(cover, verdict):
    """§② الحكمُ الحاكم: التغطيةُ دون 90% ⟵ «لا قياس» وإلّا حكمُ ⑤ على الكون كلِّه."""
    return "لا قياس" if cover < COVER_MIN else verdict


def mode_measure(MC, path=UNIVERSE_FILE):
    from concurrent.futures import ThreadPoolExecutor
    key, ua = os.environ.get("POLYGON_API_KEY", "").strip(), (os.environ.get("SEC_CONTACT") or "").strip()
    if not key or not ua:
        log("⛔ مفتاحُ Polygon أو SEC_CONTACT غائب — لا عمل")
        return 2
    U = json.load(open(path, encoding="utf-8"))
    sess = U["sessions"]
    net = V.Net(key, ua)
    prev = {d: V3._prev_session(d, MC) for d in sess}
    log(f"📅 الملحق 2 · الجلسات {len(sess)}: {sess[0]} ⟵ {sess[-1]} · الكونُ المجمَّد {sum(len(universe_of(U, d)[0]) for d in sess)} رمز-يوم · "
        f"التعريفُ الممتدّ المتّصل · 8/15 · البذرة {G.SEED}")
    with ThreadPoolExecutor(8) as pool:
        days = dict(zip(sess, pool.map(lambda d: V.Day(net, d, MC, replay=True), sess)))
    bad = [d for d in sess if not days[d].ok]
    splits, sp_ok = all_splits(net, "2025-01-01", sess[-1])
    log(f"🧾 أيّامٌ بمرجعٍ ناقص {len(bad)} {bad[:5]} · التقسيمات {sum(len(v) for v in splits.values())} ({'كاملة' if sp_ok else 'ناقصة'})")
    syms = sorted({s for d in sess for s in universe_of(U, d)[0]})
    gx_hits, measurable, failed, failed_30 = {}, 0, [], 0

    def work(sym):
        by = net.minutes(sym, prev[sess[0]], sess[-1])
        out = []
        if by is None:
            return sym, None, None
        for d in sess:
            uni, L = universe_of(U, d)
            if sym not in uni:
                continue
            sp = splits.get(sym, ())
            stop = None
            if sym in L and L[sym].get("stop"):
                try:
                    stop = float(L[sym]["stop"]) * split_factor_since(sp, str(L[sym].get("added") or d), d)
                except (TypeError, ValueError):
                    stop = None
            r = symday(sym, d, prev[d], by, days[d].prev_adj(sym), V4.price_factor(sp, d), [s for s in sp if s[0] == d], stop,
                       (U["alerts"].get(d) or {}).get(sym))
            if r is not None:
                out.append(r)
        b30 = GA.fetch_30m(net, sym, GA.HISTORY_FROM, sess[-1])
        ga = None
        if b30 is not None:
            b4 = GA.to_4h(b30, True)
            okm, gx = GA.gcrosses(b4)
            ga = {"measurable": okm, "golden": sorted({GA.ny_day(x["ts"]) for x in gx if x["kind"] == "golden"})}
        return sym, out, ga
    rows = []
    with ThreadPoolExecutor(WORKERS) as pool:
        for i, (sym, out, ga) in enumerate(pool.map(work, syms)):
            if out is None:
                failed.append(sym)
            else:
                rows.extend(out)
            if ga is None:
                failed_30 += 1
            else:
                measurable += int(ga["measurable"])
                gx_hits[sym] = [d for d in ga["golden"] if d in sess and sym in universe_of(U, d)[0]]
            if (i + 1) % 100 == 0:
                log(f"   … {i + 1}/{len(syms)} رمز · صفوف {len(rows)} · تعذّر {len(failed)}")
    total_sd = sum(len(universe_of(U, d)[0]) for d in sess)
    cover = len(rows) / total_sd if total_sd else 0.0
    S = summarize_rows(rows, U, sess)
    log(f"🩺 التغطية: صفوفٌ بشموع {len(rows)} من {total_sd} رمز-يوم ({cover * 100:.1f}%) · رموزٌ تعذّرت دقائقُها {len(failed)} · نداءات {net.calls} · تعذّر {net.fails}")
    log("")
    log(f"① الراكضون (الممتدّ · أعلى اليوم ÷ إغلاق الأمس المسوّى · يومُ التقسيم مستبعَد = {S['split_days']} · مرجعٌ مجهول {S['R_unknown']}):")
    log(f"   ‏+50% فأكثر: {S['run50']} رمز-يوم ({S['run50_syms']} رمزًا) · في {S['days_run50']} جلسة من {len(sess)} · وسيطُ اليوم {S['med_run50_day']}")
    log(f"   ‏+100% فأكثر: {S['run100']} رمز-يوم ({S['run100_syms']} رمزًا) · في {S['days_run100']} جلسة من {len(sess)}")
    log("② أيّامُ الراكض الكبير (+100%): المتقاطعون إيجابيًّا 8/15 في اليوم · بلغ +20% بعد أوّل تقاطع · لم يبلغ (كاذب):")
    tc = sum(t["crossers"] for t in S["two"])
    tw = sum(t["win20"] for t in S["two"])
    tr = sum(t["run100"] for t in S["two"])
    for t in S["two"]:
        log(f"   {t['day']}: راكضون كبار {t['run100']} · متقاطعون {t['crossers']} · بلغ +20% {t['win20']} · كاذب {t['false']}")
    log(f"   ⟵ المجموع: متقاطعون {tc} · بلغ +20% {tw} · كاذب {tc - tw} · **كاذبٌ لكلّ رابحٍ +20%** {('—' if not tw else round((tc - tw) / tw, 1))} · "
        f"**وكاذبٌ لكلّ راكضٍ كبير** {('—' if not tr else round((tc - tw) / tr, 1))}")
    log("③ الراكضون (+50%): أوّلُ تقاطعٍ إيجابيٍّ مقابل أبكر «هنا الدخول» (الوقت · السعر · ونسبةُ كلٍّ من إغلاق الأمس إلى القمّة):")
    both = [t for t in S["three"] if t["fp_m"] is not None and t["al_m"] is not None]
    for t in S["three"]:
        log(f"   ${t['sym']} {t['day']} · قمّة {_pct(t['R'])} عند {G.hm(t['top_m'])} · تقاطع "
            + ("—" if t["fp_m"] is None else f"{G.hm(t['fp_m'])} ${t['fp_px']:g} (مستوى {t['fp_lvl']:.4g})") + " · هنا الدخول "
            + ("—" + (" (فجوةُ المصدر)" if t["gap"] else "") if t["al_m"] is None else f"{G.hm(t['al_m'])} ${t['al_px']:g}"))
    cf = sum(1 for t in both if t["fp_m"] < t["al_m"])
    log(f"   ⟵ بالاثنين {len(both)} من {len(S['three'])} · التقاطعُ أوّلًا {cf} · التنبيهُ أوّلًا {sum(1 for t in both if t['al_m'] < t['fp_m'])} · "
        f"معًا {sum(1 for t in both if t['al_m'] == t['fp_m'])} · وسيطُ (التنبيه − التقاطع) {G._median([t['al_m'] - t['fp_m'] for t in both])} دقيقة · "
        f"بلا تنبيه {sum(1 for t in S['three'] if t['al_m'] is None)} (منها في الفجوة {sum(1 for t in S['three'] if t['al_m'] is None and t['gap'])}) · "
        f"بلا تقاطع {sum(1 for t in S['three'] if t['fp_m'] is None)}")
    log("④ الخروج على الراكضين (دخولٌ بأوّل تقاطعٍ إيجابيّ) — حصّةُ الحركة = (الخروج − الدخول) ÷ (أعلى ما بعد الدخول − الدخول):")
    for pol, nm in (("neg", "التقاطع السلبيّ"), ("close", "الإمساك حتى آخر دقيقة (قبل 20:00)"), ("stop", "وقفُ البوت (وإلّا الإمساك)")):
        f4 = S["four"][pol]
        log(f"   {nm}: n {f4['n']} · وسيطُ النتيجة {_pct(f4['ret_med'])} · وسيطُ الحصّة {_share_txt(f4['share_med'])} · متوسّطُها {_share_txt(f4['share_mean'])}")
    log("⑤ الضابطُ العشوائيّ نفسُه (دخولٌ بدقيقةٍ عشوائيّة من نافذة اليوم · خروجٌ بالسلبيّ التالي) — بوتستراب عنقوديّ على الرمز-اليوم:")
    for nm, lab in (("all", "الكونُ كلُّه (الحاكم)"), ("run50", "أيّامُ الراكضين وحدَها (وصفًا · نظرٌ للأمام)")):
        f5 = S["five"][nm]
        b = f5["boot"]
        log(f"   {lab}: دورات {f5['n']} على {f5['sd']} رمز-يوم · الوسيط {_pct(f5['arm_med'])} مقابل {_pct(f5['ctl_med'])} · المتوسّط {_pct(f5['arm_mean'])} "
            f"مقابل {_pct(f5['ctl_mean'])} · سالبة {f5['arm_neg']} مقابل {f5['ctl_neg']} · الفرق {_pct(b[0])} [{_pct(b[1])} ، {_pct(b[2])}] ⟵ **{f5['verdict']}**")
    run_days = {}
    for t in S["three"]:
        run_days.setdefault(t["sym"], set()).add(t["day"])
    gf = [g for sym, ds in gx_hits.items() for g in golden_follow(ds, run_days.get(sym, set()), sess)]
    base_n = base_k = 0
    for d_i, d in enumerate(sess[:-FOLLOW_A]):
        nxt = sess[d_i + 1:d_i + 1 + FOLLOW_A]
        for sym in universe_of(U, d)[0]:
            base_n += 1
            base_k += int(any(x in run_days.get(sym, ()) for x in nxt))
    full = [g for g in gf if g["full"]]
    log(f"⭐ الذراع أ (ذهبيّ 4س ممتدّ · SMA50/200) في الكون نفسِه: رموزٌ قيست {len(syms) - failed_30} · مؤهَّلةٌ (201 شمعة فأكثر) {measurable} · "
        f"تقاطعاتٌ ذهبيّة في الجلسات الستّين والرمزُ في الكون يومَها {len(gf)} · سبقت راكضًا (+50% خلال {FOLLOW_A} جلسة) "
        f"{sum(g['hit'] for g in gf)} · بنافذةٍ كاملة {sum(g['hit'] for g in full)} من {len(full)} · ويومَ التقاطع نفسِه {sum(g['same'] for g in gf)} · "
        f"والأساسُ (أيُّ رمز-يومٍ في الكون بنافذةٍ كاملة) {base_k} من {base_n} = {('—' if not base_n else f'{base_k / base_n * 100:.2f}%')}")
    out = {"mode": "runner", "sessions": [sess[0], sess[-1], len(sess)], "cover": cover, "failed": len(failed), "bad_days": bad,
           "summary": {k: v for k, v in S.items() if k != "three"}, "three": S["three"],
           "golden": {"measured": len(syms) - failed_30, "measurable": measurable, "n": len(gf), "hit": sum(g["hit"] for g in gf),
                      "full": len(full), "full_hit": sum(g["hit"] for g in full), "same": sum(g["same"] for g in gf), "base": [base_k, base_n]},
           "calls": net.calls, "fails": net.fails}
    omh = omh_example(net, MC, U)
    out["omh"] = omh
    out["verdict"] = final_verdict(cover, S["five"]["all"]["verdict"])
    log(f"⚖️ **الحكم (الحاكم = الكونُ كلُّه · 8/15 ممتدّ مقابل الضابط):** {out['verdict']}" + (" (التغطية دون 90%)" if cover < COVER_MIN else ""))
    log("GCROSS_JSON " + json.dumps(out, ensure_ascii=False, sort_keys=True, default=str))
    return 0


def omh_example(net, MC, U, sym="OMH", d="2026-11-04"):
    """مثالُ OMH ‏11-04 كاملًا: العضويّة · الركض · التقاطعات · أوّلُ إيجابيّ · «هنا الدخول» · الخروجُ بالسياسات الثلاث · والضابط."""
    D = V.Day(net, d, MC, replay=True)
    by = net.minutes(sym, D.prev, d)
    if by is None or not by.get(d):
        log(f"⛔ مثالُ {sym} {d}: تعذّرت الدقائق")
        return None
    uni, L = universe_of(U, d)
    stop = None if sym not in L else L[sym].get("stop")
    r = symday(sym, d, D.prev, by, D.prev_adj(sym), V4.price_factor(D.splits.get(sym, ()), d), [], stop, (U["alerts"].get(d) or {}).get(sym))
    series, _k = G.ext_series(by.get(D.prev) or [], by[d], V4.price_factor(D.splits.get(sym, ()), d))
    xs = G.day_crosses(series)
    log(f"🧪 مثالُ ${sym} {d}: في الكون؟ {'نعم (القائمة)' if sym in L else ('نعم (تحت المتابعة)' if sym in uni else 'لا')} · القمّة {_pct(r['R'])} عند "
        f"{G.hm(r['top_m']) if r['top_m'] is not None else '—'} · تقاطعاتُ اليوم {len(xs)} (إيجابيّة {r['npos']}) · «هنا الدخول» "
        + ("—" if not r.get("alert") else f"{dt.datetime.fromtimestamp(r['alert']['ms'] / 1000, tz=NY).strftime('%H:%M')} ${r['alert']['px']:g}"))
    if r.get("fp"):
        log(f"   أوّلُ إيجابيّ {G.hm(r['fp']['m'])} ${r['fp']['px']:g} (مستوى {r['fp']['lvl']:.4g}) · بلغ +20% بعده؟ {'نعم' if r['fp']['win20'] else 'لا'}")
    if r.get("ex"):
        for pol, nm in (("neg", "السلبيّ"), ("close", "الإمساك"), ("stop", "وقفُ البوت")):
            e = r["ex"][pol]
            log(f"   خروجٌ {nm}: " + ("— (لا وقفَ للرمز)" if e is None else f"{G.hm(e['m'])} ${e['px']:g} · {_pct(e['ret'])} · حصّة {_share_txt(e['share'])}"))
    log(f"   الدورات {len(r['arm'])}: متوسّطُها {_pct(sum(r['arm']) / len(r['arm']) if r['arm'] else None)} · والضابطُ {_pct(sum(r['ctl']) / len(r['ctl']) if r['ctl'] else None)}")
    return {k: r.get(k) for k in ("R", "top_m", "npos", "fp", "ex", "alert")} | {"in_universe": sym in uni, "in_list": sym in L}


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--mode", default="measure", choices=("freeze", "measure"))
    a = p.parse_args(argv)
    import market_calendar as MC
    if a.mode == "freeze":
        return freeze(MC)
    return mode_measure(MC)


if __name__ == "__main__":
    sys.exit(main())
