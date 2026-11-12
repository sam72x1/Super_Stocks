"""💵🧱 صفقةُ الكرت — التكلفةُ على 2023-2025 و2026 وصفًا وحصّةُ أعلى 5% (`T_BLOCK_addendum_2.md` §③ و§③-ب · قبل أيّ رقم).

قراءةٌ وقياسٌ فقط: لا تلغرام · لا كتابةَ حالة · لا إنتاج. الصفقةُ = ذراعُ CUR3 في `T-TGTLADDER` ② **بالاسم** (`shard_symbol` ·
`entry_row` · `trade_r`) · والتكلفةُ بطريقة `T-SLIP-NBBO`/`T-BTCOST` **بالاسم** (`stage_bar` · `window_of` · `stage_quote` ·
`spread_pct` · `slip_arms.fetch_day`) · والمحورُ المُغلَق `T-TGTLADDER` يُفتح لهذه التشغيلة وحدَها بإقرار المالك (`TGTLADDER_REOPEN=1`).

الأوضاع: `check` (بلا شبكة) · `prep26` · `shard` · `assemble` ⟵ كلُّها تخرج 9 إن تغيّرت بصمةُ الملحق 2 · و8 بلا الإقرار · و3 بلا مفتاح Polygon.
"""
import argparse
import concurrent.futures as _cf
import datetime as dt
import glob
import hashlib
import json
import math
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(HERE, "out", "card")
ADDENDUM_2 = os.path.join(HERE, "T_BLOCK_addendum_2.md")
ADDENDUM_2_SHA = "3d948ddc7b79c7ee6b30457913c7d90f8b3017ab7b1c561ef5a9a2397d84f163"
CONTRACT_RC, CLOSED_RC, KEY_RC = 9, 8, 3
TGL_RUN = "42943607531"                    # §③-ب مادّةُ T-TGTLADDER المنشورة
TGL_DIR = os.path.join(HERE, "out", "tgl")  # يُنزَّل إليه `tgl-prep` و`tgl-shard-*` في الـworkflow
OLD_YEARS = ("2023", "2024", "2025")
PERIOD26 = ("2026-01-02", "2026-12-31")
SESS26_FROM, ALL26_FROM = "2025-10-01", "2025-09-01"
MONTHS26 = [(2025, 10), (2025, 11), (2025, 12)] + [(2026, m) for m in range(1, 12)]
ID_TOL, ID_MIN = 1e-6, 0.99                # §③-ب بوّابةُ الهويّة
COVER_MIN = 0.80                           # §③ التغطية لكلّ سنة
C_MED = 1.8018                             # `T-BTCOST` C-MED (%) حساسيّةٌ ثابتة لكلّ ساق
TOP_FRAC = 0.05
BOOT_B, BOOT_SEED = 2000, "TBLKC"
WORKERS = int(os.environ.get("CARD_WORKERS") or 8)


def log(*a):
    print(*a, flush=True)


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def contract_ok():
    return os.path.exists(ADDENDUM_2) and _sha(ADDENDUM_2) == ADDENDUM_2_SHA


def reopen_ok(env=None):
    """إقرارُ المالك (§⓪-أ) — «1» حرفيًّا."""
    return ((os.environ if env is None else env).get("TGTLADDER_REOPEN") or "").strip() == "1"


def _jdump(obj, path):
    import gzip
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, default=str)


def _jload(path):
    import gzip
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return json.load(fh)


# ── دوالُّ نقيّة ─────────────────────────────────────────────────────────────────────────────────
def trade_legs(rows, i, entry, stop, targets, win=20, eps=1e-6):
    """مرآةُ `tgtladder.trade_r` حرفيًّا تُرجع السيقانَ أيضًا (`TBK14` يطابق R بالعوالم العشوائيّة):
    {"r"، "risk"، "fill"، "legs": [{"k"، "px"، "w"، "kind"، "side"}]} أو None حين يُرجع `trade_r` (None، …)."""
    try:
        E, st = float(entry), float(stop)
        tg = sorted(float(t) for t in targets if t is not None and float(t) > 0)
    except (TypeError, ValueError):
        return None
    if not (st > 0 and E - st > eps * E) or not tg or i < 1 or i + 2 * win - 1 > len(rows):
        return None
    k0 = fill = None
    for k in range(i, i + win):
        if float(rows[k][3]) <= E:
            k0, fill = k, min(float(rows[k][1]), E)
            break
    if k0 is None or fill <= st:
        return None
    risk = E - st
    w = 1.0 / len(tg)
    left = list(tg)
    leg = {t: None for t in tg}
    legs = [{"k": k0, "px": fill, "w": 1.0, "kind": "entry", "side": "down"}]

    def _out():
        return {"r": round(sum(leg.values()) / risk, 6), "risk": risk, "fill": fill, "legs": legs}
    for k in range(k0, k0 + win):
        o, h, lo = float(rows[k][1]), float(rows[k][2]), float(rows[k][3])
        if lo < st:
            px = min(o, st) if k > k0 else st
            for t in left:
                leg[t] = w * (px - fill)
            legs.append({"k": k, "px": px, "w": w * len(left), "kind": "stop", "side": "down"})
            return _out()
        if k == k0:
            continue
        for t in list(left):
            if h >= t:
                leg[t] = w * (max(o, t) - fill)
                left.remove(t)
                legs.append({"k": k, "px": max(o, t), "w": w, "kind": "target", "side": "up"})
        if not left:
            return _out()
    kc = k0 + win - 1
    c_end = float(rows[kc][4])
    for t in left:
        leg[t] = w * (c_end - fill)
    legs.append({"k": kc, "px": c_end, "w": w * len(left), "kind": "close", "side": "close"})
    return _out()


def r_after(r, risk, legs):
    """§③-ب R بعد التكلفة = R − Σ(c/2 × السعر × الحصّة) ÷ المخاطرة · وساقٌ بلا c ⟵ None."""
    if r is None or not risk:
        return None
    cost = 0.0
    for lg in legs:
        c = lg.get("c")
        if c is None:
            return None
        cost += (float(c) / 100.0) / 2.0 * float(lg["px"]) * float(lg["w"])
    return r - cost / risk


def r_fixed(r, risk, legs, c_pct=C_MED):
    return r_after(r, risk, [dict(lg, c=c_pct) for lg in legs])


def top_share(rs, frac=TOP_FRAC):
    """(أعلى 5% سقفًا ÷ المجموع الصافي · ÷ مجموع الموجب) — None عند صفرٍ في المقام."""
    xs = sorted((float(x) for x in rs if x is not None), reverse=True)
    if not xs:
        return None, None
    k = max(1, math.ceil(frac * len(xs)))
    top = sum(xs[:k])
    net, pos = sum(xs), sum(x for x in xs if x > 0)
    return (top / net if net else None), (top / pos if pos else None)


def boot_mean(by_sym, b=BOOT_B, seed=BOOT_SEED):
    syms = sorted(by_sym)
    allv = [v for s in syms for v in by_sym[s]]
    if not allv:
        return None, (None, None)
    rng = random.Random(seed)
    ms = []
    for _ in range(b):
        v = [x for s in (syms[rng.randrange(len(syms))] for _ in syms) for x in by_sym[s]]
        if v:
            ms.append(sum(v) / len(v))
    ms.sort()
    return sum(allv) / len(allv), (ms[int(0.025 * len(ms))], ms[int(0.975 * len(ms)) - 1])


def sign_verdict(ci):
    """§③ «موجبٌ بعد التكلفة» · «لا يُعرف» · «سالبٌ»."""
    lo, hi = ci
    if lo is None or hi is None:
        return "لا قياس"
    if lo > 0:
        return "موجبٌ بعد التكلفة"
    if hi < 0:
        return "سالبٌ بعد التكلفة"
    return "لا يُعرف"


def group_legs(legs):
    """سيقانٌ في اليوم نفسِه بالسعر والاتّجاه نفسِهما ⟵ قياسٌ واحد (المفتاح)."""
    return {(lg["day"], round(float(lg["px_adj"]), 8), lg["side"]) for lg in legs}


# ── القياس على الشبكة ────────────────────────────────────────────────────────────────────────────
def measure_key(sym, key, dclose, fetch_day=None, window=None, bars=None):
    """(c% أو None، السبب) لساقٍ واحدة بطريقة `T-BTCOST` بالاسم · وساقُ الإغلاق آخرُ صفقةٍ في آخر دقيقةٍ نظاميّة."""
    sys.path.insert(0, ROOT)
    import btcost_arms as BC
    import slip_arms as SL
    import slip_nbbo_arms as NB
    day, level, side = key
    if bars is None:
        bars = (fetch_day or SL.fetch_day)(sym, day)
    if side == "close":
        sess = SL.session_slice(bars) if bars else []
        if not sess:
            return None, "no_minutes"
        if not SL.scale_ok(sess[-1]["c"], dclose):
            return None, "raw_scale_unverified"
        bar = sess[-1]
        win = (window or BC.window_of)((sym, day, int(bar["t"])))
        tr, qs = (win or {}).get("t"), (win or {}).get("q")
        if not tr or not qs:
            return None, "no_quotes"
        tms = int(tr[-1]["t"])
        q = NB.prevailing(qs, tms)
        if q is None or tms - int(q["t"]) > BC.STALE_MS:
            return None, "stale_quote" if q is not None else "no_quotes"
        c = BC.spread_pct(q)
        return (c, "ok") if c is not None else (None, "no_quotes")
    leg = {"level": level, "side": side, "dclose": dclose}
    (why, _d), bar = BC.stage_bar(leg, bars)
    if why != "ok":
        return None, why
    win = (window or BC.window_of)((sym, day, int(bar["t"])))
    (why, _d), pay = BC.stage_quote(leg, bar, win)
    if why != "ok":
        return None, why
    c = BC.spread_pct(pay)
    return (c, "ok") if c is not None else (None, "no_quotes")


# ── الأوضاع ──────────────────────────────────────────────────────────────────────────────────────
def _tgl():
    sys.path.insert(0, os.path.join(ROOT, "fm_forensics", "tgtladder"))
    sys.path.insert(0, ROOT)
    import tgtladder as TGL
    return TGL


def _last_session(RB):
    """آخرُ جلسةٍ قبل يوم التشغيل (`rebuild.sessions_between` بالاسم)."""
    sys.path.insert(0, ROOT)
    import market_calendar as MC
    y = (dt.date.today() - dt.timedelta(days=1)).isoformat()
    return RB.sessions_between("2026-10-01", y, MC)[-1]


def mode_prep26(key):
    TGL = _tgl()
    RB = TGL._rb()
    RB.mode_bases_prep(key, months=MONTHS26, sess_from=SESS26_FROM, sess_to=_last_session(RB), all_from=ALL26_FROM,
                       out=os.path.join(OUT, "prep26.json.gz"), tag="cardcost_prep26",
                       splits_range=(RB.BARS_FROM, dt.date.today().isoformat()))
    return 0 if os.path.exists(os.path.join(OUT, "prep26.json.gz")) else 5


def tgl_keys(tgl_dir=TGL_DIR):
    """مفاتيحُ T-TGTLADDER (رمز، D) ⟵ R المخزَّن لذراع CUR3 والتعبئة."""
    out = {}
    for p in sorted(glob.glob(os.path.join(tgl_dir, "shard_*.json.gz"))):
        for sym, es in (_jload(p).get("rows") or {}).items():
            for e in es:
                out[(sym, e["d"])] = {"r_cur": e.get("r_cur"), "filled": e.get("filled")}
    return out


def _enumerate(TGL, RB, S, AD, PH, prep, syms, key, bars_to, period, keep=None):
    """إدخالاتُ CUR3 بمولِّد T-TGTLADDER بالاسم + سيقانُها (التقاطُ نداء `trade_r` الأوّل في `entry_row`)."""
    cur, _piv = AD.cfgs_of(S, RB)
    RB.install_stubs(S)
    G5 = RB._gen5_ext()
    member = {}
    for d in prep["sessions"]:
        for s in prep["snapshots"].get(d[:7], []):
            member.setdefault(s, []).append(d)
    six = {d: n for n, d in enumerate(prep["sessions"])}
    cache = {}

    def _proxy(sym, day):
        if (sym, day) not in cache:
            code, body = RB._get(RB.PROXY_URL.format(t=sym, d=day, k=key))
            try:
                cache[(sym, day)] = json.loads(body or b"{}").get("results", {}).get("share_class_shares_outstanding")
            except Exception:                                   # noqa: BLE001
                cache[(sym, day)] = None
        return cache[(sym, day)]
    cap = []
    orig_tr, orig_er, orig_period = TGL.trade_r, TGL.entry_row, TGL.PERIOD

    def tr_cap(rows, i, entry, stop, targets, win=TGL.WIN):
        cap.append((rows, i, entry, stop, list(targets or [])))
        return orig_tr(rows, i, entry, stop, targets, win)

    def er_wrap(S_, RB_, sym, rows, i, sub, f, r0, hourly, d=None):
        cap.clear()
        er = orig_er(S_, RB_, sym, rows, i, sub, f, r0, hourly, d=d)
        er["f"] = f
        if cap:
            rs, ii, E, st, cur3 = cap[0]
            tl = trade_legs(rs, ii, E, st, cur3, win=TGL.WIN)
            if tl:
                for lg in tl["legs"]:
                    lg["day"] = rows[lg["k"]][0]
                    lg["px_adj"] = lg["px"] / f if f else lg["px"]
                    lg["dclose"] = float(rows[lg["k"]][4])
                er["card"] = {"r": tl["r"], "risk": tl["risk"], "legs": tl["legs"]}
        return er
    units, tot, diag = [], {}, {}
    TGL.trade_r, TGL.entry_row, TGL.PERIOD = tr_cap, er_wrap, period
    try:
        for n, sym in enumerate(syms):
            df, why = PH.polygon_daily(sym, RB.BARS_FROM, bars_to, key)
            rows = RB._rows(df) if df is not None else []
            diag[why.split("(")[0]] = diag.get(why.split("(")[0], 0) + 1
            out, cnt = TGL.shard_symbol(sym, rows, prep["splits"].get(sym), member.get(sym, []), six, prep["prev_of"], prep["finra"],
                                        _proxy, S, cur, G5, RB, key)
            for k, v in cnt.items():
                tot[k] = tot.get(k, 0) + v
            for er in out:
                if keep is not None and (sym, er["d"]) not in keep:
                    continue
                units.append({"sym": sym, "d": er["d"], "y": er["d"][:4], "filled": bool(er.get("filled")),
                              "r_cur": er.get("r_cur"), "card": er.get("card")})
            if n % 25 == 0:
                log(f"   {n + 1}/{len(syms)} · {tot} · وحدات {len(units)}")
    finally:
        TGL.trade_r, TGL.entry_row, TGL.PERIOD = orig_tr, orig_er, orig_period
    return units, tot, diag


def _cost_units(units):
    """تقيس كلَّ ساقٍ فريدة لكلّ رمز بخيوط (`WORKERS`) وتكتب c في السيقان."""
    jobs = {}
    for u in units:
        cd = u.get("card")
        if not cd:
            continue
        for lg in cd["legs"]:
            jobs.setdefault((u["sym"], (lg["day"], round(float(lg["px_adj"]), 8), lg["side"])), float(lg["dclose"]))
    sys.path.insert(0, ROOT)
    import slip_arms as SL
    days = sorted({(s, k[0]) for (s, k) in jobs})
    bars = {}
    with _cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:      # شموعُ الدقيقة مرّةً لكلّ (رمز، يوم)
        for sd, b in zip(days, ex.map(lambda x: SL.fetch_day(*x), days)):
            bars[sd] = b
    res = {}
    with _cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(measure_key, s, k, dc, None, None, bars.get((s, k[0])) or []): (s, k) for (s, k), dc in jobs.items()}
        for f in _cf.as_completed(futs):
            try:
                res[futs[f]] = f.result()
            except Exception as e:                                # noqa: BLE001
                res[futs[f]] = (None, f"error:{type(e).__name__}")
    for u in units:
        cd = u.get("card")
        if not cd:
            continue
        for lg in cd["legs"]:
            c, why = res.get((u["sym"], (lg["day"], round(float(lg["px_adj"]), 8), lg["side"])), (None, "missing"))
            lg["c"], lg["why"] = c, why
    return len(jobs)


def mode_shard(key, shard, nshards):
    TGL = _tgl()
    RB = TGL._rb()
    os.environ["FAISAL_ONLY"] = "0"
    sys.path.insert(0, os.path.join(ROOT, "fm_forensics", "appdiff"))
    import appdiff as AD
    import Super_stock as S
    import pit_history as PH
    keys = tgl_keys()
    t0 = time.time()
    out = {"shard": shard}
    # ① 2023-2025: مادّةُ T-TGTLADDER ومفاتيحُها
    p_old = os.path.join(TGL_DIR, "prep.json.gz")
    if keys and os.path.exists(p_old):
        prep = _jload(p_old)
        syms = sorted({s for s, _d in keys})[shard::nshards]
        u, tot, diag = _enumerate(TGL, RB, S, AD, PH, prep, syms, key, TGL.BARS_TO, TGL.PERIOD, keep=set(keys))
        n_legs = _cost_units(u)
        out["old"] = {"units": u, "counts": tot, "diag": diag, "syms": len(syms), "leg_keys": n_legs,
                      "stored": {f"{s}|{d}": v for (s, d), v in keys.items() if s in set(syms)}}
        log(f"shard {shard}: 2023-2025 وحدات {len(u)} · سيقان {n_legs} · {int(time.time() - t0)}ث")
    else:
        log(f"shard {shard}: ⛔ مادّةُ T-TGTLADDER غائبة ({TGL_DIR})")
    # ② 2026
    p26 = os.path.join(OUT, "prep26.json.gz")
    if os.path.exists(p26):
        prep = _jload(p26)
        syms = prep["union"][shard::nshards]
        u, tot, diag = _enumerate(TGL, RB, S, AD, PH, prep, syms, key, dt.date.today().isoformat(), PERIOD26)
        n_legs = _cost_units(u)
        out["y26"] = {"units": u, "counts": tot, "diag": diag, "syms": len(syms), "leg_keys": n_legs}
        log(f"shard {shard}: 2026 وحدات {len(u)} · سيقان {n_legs} · {int(time.time() - t0)}ث")
    _jdump(out, os.path.join(OUT, f"card_{shard:02d}.json.gz"))
    return 0


def summarize(units, stored=None):
    """لكلّ سنة: R قبل/بعد (NBBO) · بعد (C-MED) · التغطية · حصّةُ أعلى 5% · والهويّةُ مع المخزَّن (2023-2025)."""
    rows = []
    id_n = id_ok = 0
    built = {f"{u['sym']}|{u['d']}": u for u in units}
    if stored is not None:                       # §③-ب الهويّة على مجتمع +0.332 (معبَّأةٌ في المخزَّن بـr_cur)
        pop = [k for k, v in stored.items() if v.get("filled") and v.get("r_cur") is not None]
        id_n = len(pop)
        units = []
        for k in pop:
            u = built.get(k)
            cd = (u or {}).get("card")
            if u and cd and abs(float(stored[k]["r_cur"]) - float(cd["r"])) <= ID_TOL:
                id_ok += 1
                units.append(u)
    for u in units:
        cd = u.get("card")
        if stored is None and (not u.get("filled") or not cd):
            continue
        rows.append({"sym": u["sym"], "y": u["y"], "r": cd["r"], "ra": r_after(cd["r"], cd["risk"], cd["legs"]),
                     "rf": r_fixed(cd["r"], cd["risk"], cd["legs"]),
                     "why": [lg.get("why") for lg in cd["legs"] if lg.get("c") is None]})
    out = {"id": [id_ok, id_n], "years": {}}
    for y in sorted({r["y"] for r in rows}) + ["ALL"]:
        rs = [r for r in rows if y == "ALL" or r["y"] == y]
        if y == "ALL" and stored is None:
            continue
        by_b, by_a, by_f = {}, {}, {}
        for r in rs:
            by_b.setdefault(r["sym"], []).append(r["r"])
            by_f.setdefault(r["sym"], []).append(r["rf"])
            if r["ra"] is not None:
                by_a.setdefault(r["sym"], []).append(r["ra"])
        n_a = sum(len(v) for v in by_a.values())
        cover = n_a / len(rs) if rs else 0.0
        mb, cb = boot_mean(by_b)
        ma, ca = boot_mean(by_a)
        mf, cf = boot_mean(by_f)
        med = lambda xs: (sorted(xs)[len(xs) // 2] if xs else None)
        whys = {}
        for r in rs:
            for w in r["why"]:
                whys[w] = whys.get(w, 0) + 1
        out["years"][y] = {"n": len(rs), "before": [mb, cb], "after": [ma, ca], "fixed": [mf, cf], "cover": cover, "n_after": n_a,
                           "med_before": med([r["r"] for r in rs]), "med_after": med([r["ra"] for r in rs if r["ra"] is not None]),
                           "top_before": top_share([r["r"] for r in rs]),
                           "top_after": top_share([r["ra"] for r in rs if r["ra"] is not None]),
                           "cover_ok": cover >= COVER_MIN, "drop_why": whys}
    return out


def mode_assemble(nshards):
    paths = sorted(glob.glob(os.path.join(OUT, "**", "card_*.json.gz"), recursive=True))
    shards = [_jload(p) for p in paths]
    got = sorted({s["shard"] for s in shards})
    if got != list(range(nshards)):
        log(f"⛔ شرائحُ ناقصة {sorted(set(range(nshards)) - set(got))} — «لا قياس»")
        return 7
    old_u, old_st, y26_u, cnt_old, cnt_26 = [], {}, [], {}, {}
    for sh in shards:
        if sh.get("old"):
            old_u.extend(sh["old"]["units"])
            old_st.update(sh["old"]["stored"])
            for k, v in sh["old"]["counts"].items():
                cnt_old[k] = cnt_old.get(k, 0) + v
        if sh.get("y26"):
            y26_u.extend(sh["y26"]["units"])
            for k, v in sh["y26"]["counts"].items():
                cnt_26[k] = cnt_26.get(k, 0) + v
    A = summarize(old_u, old_st)
    B = summarize(y26_u)
    id_ok, id_n = A["id"]
    id_pass = id_n > 0 and id_ok / id_n >= ID_MIN
    all_ = A["years"].get("ALL") or {}
    cov_all = all(A["years"].get(y, {}).get("cover_ok") for y in OLD_YEARS)
    verdict = sign_verdict(all_.get("after", [None, (None, None)])[1]) if (id_pass and cov_all) else "لا قياس"
    f = lambda x: "—" if x is None else f"{x:+.3f}"
    fc = lambda c: f"[{f(c[0])}، {f(c[1])}]" if c and c[0] is not None else "[—]"
    pc = lambda x: "—" if x is None else f"{100 * x:.0f}%"
    log("")
    log("=" * 70)
    log(f"💵 صفقةُ الكرت — الملحق 2 §③ · التشغيلة {os.environ.get('GITHUB_RUN_ID')}")
    log(f"2023-2025: مفاتيحُ T-TGTLADDER {len(old_st)} · مُعادةٌ {len(old_u)} · الهويّة {id_ok}/{id_n} ({pc(id_ok / id_n if id_n else None)}) "
        f"{'✅' if id_pass else '❌'} · العدّادات {cnt_old}")
    for y in list(OLD_YEARS) + ["ALL"]:
        r = A["years"].get(y)
        if not r:
            continue
        log(f"   {y}: n={r['n']} · قبل {f(r['before'][0])} {fc(r['before'][1])} (وسيط {f(r['med_before'])}) · بعد NBBO {f(r['after'][0])} "
            f"{fc(r['after'][1])} (وسيط {f(r['med_after'])} · مقيسة {r['n_after']} = {pc(r['cover'])}{'' if r['cover_ok'] else ' ⟵ دون 80%'}) · "
            f"بعد C-MED {f(r['fixed'][0])} {fc(r['fixed'][1])} · أعلى 5% من الصافي قبل {pc(r['top_before'][0])} بعد {pc(r['top_after'][0])} · "
            f"من الموجب قبل {pc(r['top_before'][1])} بعد {pc(r['top_after'][1])} · أسبابُ السقوط {r['drop_why']}")
    log(f"⚖️ المجمَّع 2023-2025 بعد التكلفة: **{verdict}**")
    for y, r in sorted(B["years"].items()):
        log(f"   2026 وصفًا ({y}): n={r['n']} · قبل {f(r['before'][0])} {fc(r['before'][1])} (وسيط {f(r['med_before'])}) · بعد NBBO "
            f"{f(r['after'][0])} {fc(r['after'][1])} (مقيسة {pc(r['cover'])}) · بعد C-MED {f(r['fixed'][0])} · أعلى 5% من الصافي قبل "
            f"{pc(r['top_before'][0])} بعد {pc(r['top_after'][0])}")
    log(f"   2026 العدّادات {cnt_26} · وحداتٌ {len(y26_u)} · معبَّأة {sum(1 for u in y26_u if u.get('filled'))}")
    print("CARD_JSON " + json.dumps({"A": A, "B": B, "verdict": verdict, "id_pass": id_pass, "counts_old": cnt_old,
                                     "counts_26": cnt_26}, ensure_ascii=False, default=str))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="check", choices=("check", "prep26", "shard", "assemble"))
    a = ap.parse_args(argv)
    if not contract_ok():
        log("⛔ بصمةُ الملحق 2 تغيّرت — لا تشغيل")
        return CONTRACT_RC
    if a.mode == "check":
        log("✅ الملحق 2 مطابق")
        return 0
    if not reopen_ok():
        log("🔒 T-TGTLADDER مُغلَق — التشغيلُ بإقرار المالك وحدَه (TGTLADDER_REOPEN=1 · الملحق 2 §⓪-أ)")
        return CLOSED_RC
    if a.mode == "assemble":
        return mode_assemble(int(os.environ.get("NSHARDS", "20")))
    key = (os.environ.get("POLYGON_API_KEY") or "").strip()
    if not key:
        log("⛔ بلا مفتاح Polygon — لا قياس")
        return KEY_RC
    if a.mode == "prep26":
        return mode_prep26(key)
    return mode_shard(key, int(os.environ.get("SHARD", "0")), int(os.environ.get("NSHARDS", "20")))


if __name__ == "__main__":
    sys.exit(main())
