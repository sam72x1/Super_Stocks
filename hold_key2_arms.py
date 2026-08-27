#!/usr/bin/env python3
"""🕰️🥇② `T-HOLD-KEY-2` — البِركةُ تُبنى بـ`select_top` لا بكون المرشّحين.

العقد `hold_key2_prereg.md` **مدفوعٌ قبل أيّ سطرٍ هنا** (‏`8afd57ee`).
🔒 **قراءةٌ فقط · صفرُ مسٍّ بالإنتاج · لا `LOGIC_VERSION`.**

⚖️ **ومقياسٌ واحدٌ لا اثنان:** كلُّ ما يُعاد استعمالُه يُستورَد **بالاسم** من
`hold_key_arms` و`press_rank_arms` (المجمَّدتَين بأرقامهما المنشورة — `HW2`) ومن
`Super_stock`/`press_radar` الإنتاجية. **والمتغيّرُ الوحيدُ المقصود سطرٌ واحد:**
عضويّةُ البِركة تُشتقّ من `select_top` بسعة `WATCHLIST_SIZE` (‏= ما يقرؤه
`press_radar.build_pool` من `wl["stocks"]`) بدل «كلّ من اجتاز `analyze_ticker`».
ومعه **لازمٌ بنيويٌّ مُعلَنٌ في `§①`**: شبكةُ `Q5` بتقويمٍ مشترك — لأن
`select_top` **مقطعيّ**.
"""
import hashlib
import json
import os
import statistics
import sys
import time

import hold_key_arms as HK             # الأذرع · deliver_prod · hv0/hv8 · live_pool · mover_days
import press_rank_arms as PRA          # r_of · boot_ci · ready_rows · pv0_gate · الثوابت

# ─────────────────────────────── ثوابتُ العقد ───────────────────────────────
# `HW2` — تجميدُ الأداتين اللتين نُشرت أرقامُهما (سابقةُ CAP15).
FROZEN_SHA = {
    "hold_key_arms.py":
        "39643875f649a42fdb5624e3dce76e6dc9721637b76a270472d78e31be8816c0",
    "press_rank_arms.py":
        "6bb28144c1742840c4c45e651f2ae46a354a2928c671b0487047f69cdac10fd7",
}
HW1_MIN_DROP_PCT = 30.0               # §⑤ أثرُ `select_top` غيرُ صفريّ
HW1_PUBLISHED_2023 = 9181             # §⑤ للسياق لا للبوّابة (الشبكةُ تبدّلت)
RANK_FIELDS = ("symbol", "readiness", "score", "rr", "price",
               "tranches", "h4_confirm")               # §⑨-3


def _log(m):
    print(m, flush=True)


def _sha(path):
    try:
        with open(path, "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()
    except OSError:
        return ""


def hw2_frozen():
    """**`HW2`**: الأداتان المجمَّدتان لم تُمَسّا (‏CAP15) — تُقارَن بصمتاهما."""
    out = {}
    for p, exp in FROZEN_SHA.items():
        got = _sha(p)
        out[p] = (got[:16] == exp[:16], got[:16], exp[:16])
    return out


# ───────────────────── §① شبكةُ `Q5` بتقويمٍ مشترك (لازمُ `select_top`) ─────────────────────

def grid_dates(hist, yr):
    """تقويمُ الكون داخل النافذة، ثم **كلُّ `Q5_STRIDE` جلسة**.

    🔴 مقطعيّةُ `select_top` تُلزمه: رموزٌ تُعايَن كلٌّ في تاريخٍ آخر لا تُقارَن.
    النافذة: من قبل السنة بـ`PQ_MAX_BACK` جلسةً إلى آخرها."""
    seen = set()
    for df in hist.values():
        if df is None:
            continue
        for d in df.index:
            seen.add(str(d)[:10])
    days = sorted(seen)
    if not days:
        return []
    ys = [i for i, d in enumerate(days) if not yr or d[:4] == str(yr)]
    if not ys:
        return []
    lo = max(0, ys[0] - HK.PQ_MAX_BACK - 5)
    hi = min(len(days), ys[-1] + 1)
    return days[lo:hi:HK.Q5_STRIDE]


def q5_grid_cal(sym, df, gset, min_pos):
    """تأهّلُ رمزٍ على تواريخ الشبكة — `analyze_ticker` **بالاسم**، فرزًا أو ارتدادًا.

    يُرجع `(الموضع، التاريخ، صفٌّ مصغَّر يحمل حقولَ `rank_key` وحدَها)` (‏§⑨-3)."""
    import Super_stock as S                                     # noqa: PLC0415
    out = []
    days = [str(d)[:10] for d in df.index]
    for i, d in enumerate(days):
        if i < min_pos or d not in gset:
            continue
        sl = df.iloc[:i + 1]
        r = None
        try:
            r = S.analyze_ticker(sym, sl) or \
                S.analyze_ticker(sym, sl, pullback=True)
        except Exception:                                       # noqa: BLE001
            continue
        if not r:
            continue
        mini = {k: r.get(k) for k in RANK_FIELDS}
        mini["symbol"] = sym
        out.append((i, d, mini))
    return out


def top_by_date(grids):
    """§①: `rank_key` ثم `select_top` **بالاسم** لكلّ تاريخِ شبكة.

    يُرجع `{التاريخ: مجموعةُ الرموز المُسلَّمة}` — أي `wl["stocks"]` المُعادُ بناؤه."""
    import Super_stock as S                                     # noqa: PLC0415
    cap = int(S.CONFIG.get("WATCHLIST_SIZE", 15))
    per = {}
    for g in grids.values():
        for _i, d, mini in g:
            per.setdefault(d, []).append(mini)
    out = {}
    for d, xs in per.items():
        xs.sort(key=S.rank_key)                                  # ترتيبُ الإنتاج
        out[d] = {r["symbol"] for r in S.select_top(xs, cap, set())}
    return out, cap


# ────────────────────────── الإحياءُ وبناءُ البِركة ──────────────────────────

def enrich2(rows, grids, movers, pos_of, top_dates):
    """يُعيد استعمالَ `hold_key_arms.enrich` **بالاسم** لـ`prev_q`/`pq_date`/
    `live_mv`، **ثم يُبدّل `live_q` وحدَه** بعضويّة `select_top` (‏§①).

    🔴 **وفارقٌ يُعلَن — عضويّةُ البِركة بلا فجوةِ الثلاث جلسات:** `prev_q`
    **مفتاحُ ترتيبٍ** يشترط `gp <= p - 3` (نصُّ `prev_qualified`)، أمّا
    `wl["stocks"]` فيضمّ ما اختير **صباحَ اليوم نفسِه** ⇒ الفجوةُ لا تخصّ
    العضويّة. والأداةُ السابقة ربطت `live_q` بـ`prev_q` فورثت الفجوةَ سهوًا.
    ⇒ هنا تُفصلان: `prev_q` **بت-بت من `HK.enrich`** (وحارسُه `HV8`)،
    والعضويّةُ بلا فجوة.

    ⚖️ **و`live_q_old` يُحسَب بالاصطلاح نفسِه** (تأهّلٌ خامّ بلا فجوة) فتقيس
    `HW1` **أثرَ `select_top` وحدَه** لا فارقَ الفجوة معه."""
    import press_radar as PR                                    # noqa: PLC0415
    pos_grid = {s: [(i, d) for i, d, _m in g] for s, g in grids.items()}
    HK.enrich(rows, pos_grid, movers, pos_of)      # prev_q · pq_date · live_mv
    raw_of, top_of = {}, {}
    for sy, g in grids.items():
        raw_of[sy] = [d for _i, d, _m in g]
    for d, syms in top_dates.items():
        for sy in syms:
            top_of.setdefault(sy, []).append(d)
    for r in rows:
        s_, sym = r["session"], r["symbol"]
        r["live_q_old"] = any(HK._within(d, s_, PR.MEMORY_DAYS)
                              for d in (raw_of.get(sym) or []))
        r["live_q"] = any(HK._within(d, s_, PR.MEMORY_DAYS)
                          for d in (top_of.get(sym) or []))
    return rows


def hw1_gate(rows):
    """**`HW1`**: أثرُ `select_top` غيرُ صفريّ — نصيبُ `live_q` ينخفض 30% فأكثر."""
    old = sum(1 for r in rows if r.get("live_q_old"))
    new = sum(1 for r in rows if r.get("live_q"))
    drop = 100.0 * (1.0 - new / old) if old else 0.0
    return (drop >= HW1_MIN_DROP_PCT), old, new, drop


# ──────────────────────────────── التقرير ────────────────────────────────

def _crit(nets, ci, a2):
    """المعايير ①②③ لسنةٍ واحدة (‏④ الأرضيةُ تُفحَص في السنة نفسها)."""
    return {"d": nets["B1"] - nets["B0"],
            "ci_lo": ci["lo"], "ci_hi": ci["hi"],
            "above_p95": nets["B1"] > a2["p95"]}


def report2(rows_full, rows_live, cut, n_syms, n_seen, year, hv8, pq_share,
            hw1, cap) -> int:
    import press_backtest as PB                                  # noqa: PLC0415
    import press_radar as PR                                     # noqa: PLC0415
    rw = PB.r_win_value()
    _log(f"\n{'—' * 74}\n📊 T-HOLD-KEY-2 سنة {year} — رموزٌ مفحوصة {n_syms} · "
         f"جاهزٌ (كون) {len(rows_full)} · جاهزٌ (بِركة) {len(rows_live)} · "
         f"R_win={rw:.2f} · سعةُ `select_top`={cap}")

    cov = 100.0 * n_syms / max(n_seen, 1)
    _log(f"   🩺 `HV7` التغطية {cov:.1f}% ({n_syms} من {n_seen}) · "
         f"مفقودٌ {n_seen - n_syms}")
    if cov < PRA.COVERAGE_MIN:
        _log(f"   ⛔ `HV7` دون {PRA.COVERAGE_MIN}% ⇒ خروج 3.")
        return 3
    if not rows_full or not rows_live:
        _log("   ⛔ صفرُ صفٍّ (بصمةُ الـ`no-op`) ⇒ خروج 4.")
        return 4

    ok0, net0, exp0 = HK.hv0_bridge(rows_full, rw, year)
    _log(f"   {'✅' if ok0 else '⛔'} `HV0` جسرُ الأمس: A0={net0:+.4f} "
         f"(المنشور {exp0})")
    if not ok0:
        _log("   ⛔ `HV0` تفرّقٌ عن `press_rank_result §①` ⇒ عطبُ أداة (خروج 3).")
        return 3

    _log(f"   {'✅' if hv8[0] >= HK.HV8_MIN_AGREE else '⛔'} `HV8` توافقُ شبكة "
         f"`Q5` (تقويمٌ مشترك) مع `prev_qualified` = {hv8[0]:.1f}% (ن={hv8[1]})")
    if hv8[0] < HK.HV8_MIN_AGREE:
        _log(f"   ⛔ `HV8` دون {HK.HV8_MIN_AGREE}% ⇒ الشبكةُ لم تُثبت (خروج 3).")
        return 3

    _log(f"   📐 `HV2` نصيبُ `prev_q` الصادق = {pq_share:.1f}%")
    if not (0.0 < pq_share < 100.0):
        _log("   ⛔ `HV2` الإحياءُ منحلّ ⇒ خروج 4.")
        return 4

    # 📎 §② أمرُ المالك «طبع الكامل» — **قبل** بوّابة الكثافة فلا يكتمه سقوطُها.
    rf = HK.run_arms(rows_full, rw, "D_full")
    fs = rf["_sessions"]
    fnets = {k: sum(rf[k]["per_sess"].values()) / max(1, len(fs))
             for k in ("B0", "B1", "B3")}
    fd1 = [rf["B1"]["per_sess"][s] - rf["B0"]["per_sess"][s] for s in fs]
    fd3 = [rf["B3"]["per_sess"][s] - rf["B0"]["per_sess"][s] for s in fs]
    fci1, fci3 = PRA.boot_ci(fd1), PRA.boot_ci(fd3)
    _log("   ┌─ 📎 `D_full` **وصفيٌّ لا يحكم** (‏§② · أمرُ «طبع الكامل») ───────")
    for name in ("B0", "B1", "B3"):
        _log(HK._arm_line(name, rf, rw)[0])
    _log(f"   │ B2 العشوائيّ: وسيط {rf['_a2']['med']:+.4f} · مئين 95 "
         f"{rf['_a2']['p95']:+.4f}")
    _log(f"   │ B1−B0 = {fnets['B1'] - fnets['B0']:+.4f} "
         f"[{fci1['lo']:+.4f},{fci1['hi']:+.4f}] · B3−B0 = "
         f"{fnets['B3'] - fnets['B0']:+.4f} [{fci3['lo']:+.4f},{fci3['hi']:+.4f}]")
    _log("   └─ ⛔ لا يُنقَل إليه حكمٌ ولا يُقاس بمعايير §④ ─────────────────")

    okw, old, new, drop = hw1
    _log(f"   {'✅' if okw else '⛔'} `HW1` أثرُ `select_top`: صفوفُ `live_q` "
         f"{old} ⟶ {new} (انخفاضٌ {drop:.1f}% · الحدّ {HW1_MIN_DROP_PCT}) "
         f"· والمنشورُ في `T-HOLD-KEY` لسنة 2023 = {HW1_PUBLISHED_2023}")
    if not okw:
        _log("   ⛔ `HW1` الإصلاحُ بلا أثرٍ مادّيّ ⇒ عطبُ وصفةٍ لا نتيجة "
             "(خروج 4).")
        return 4

    by = {}
    for r in rows_live:
        by.setdefault(r["session"], []).append(r)
    sess = sorted(by)
    if len(sess) < PRA.FLOOR_SESSIONS:
        _log(f"   ⛔ الأرضية: الجلسات {len(sess)} دون {PRA.FLOOR_SESSIONS} "
             "⇒ لا حكم (خروج 4).")
        return 4
    per_n = [len(by[s]) for s in sess]
    med = statistics.median(per_n)
    _log(f"   📐 `HV4` وسيطُ الجاهزين/جلسة في `D_live2` = {med:.1f} "
         f"(المدى {min(per_n)}-{max(per_n)}) · قُصّ بالسقف {cut}")
    if not (HK.LIVE_MED_MIN <= med <= HK.LIVE_MED_MAX):
        _log(f"   ⛔ `HV4` خارج [{HK.LIVE_MED_MIN},{HK.LIVE_MED_MAX}] ⇒ ليست "
             "كثافةً حيّة (خروج 4).")
        return 4

    res = HK.run_arms(rows_live, rw, "D_live2")
    set0 = {(c["s"], c["sym"]) for c in res["B0"]["cards"]}
    set1 = {(c["s"], c["sym"]) for c in res["B1"]["cards"]}
    only1 = len(set1 - set0)
    _log(f"   📐 `HV5` كروتٌ تُسلّمها `B1` ولا تُسلّمها `B0`: {only1}")
    if only1 == 0:
        _log("   ⛔ `HV5` `B1` لم تتفرّق عن `B0` ⇒ `no-op` (خروج 4).")
        return 4

    bad = {k: PRA.dedupe_violations(res[k]["cards"]) for k in ("B0", "B1", "B3")}
    _log("   📐 `HV6` خرقُ الدِدوب: " + " · ".join(f"{k}={v}" for k, v in bad.items()))
    if any(bad.values()):
        _log("   ⛔ `HV6` الدِدوبُ غيرُ نافذ ⇒ خروج 3.")
        return 3

    _log("   ┌─ 🥇 `D_live2` الحاكم (صافي R المُسلَّم لكلّ جلسة) ──────────────")
    nets = {}
    for name in ("B0", "B1", "B3"):
        line, net = HK._arm_line(name, res, rw)
        nets[name] = net
        _log(line)
    _log(f"   │ B2 العشوائيّ: وسيط {res['_a2']['med']:+.4f} · مئين 95 "
         f"{res['_a2']['p95']:+.4f} (‏{PRA.N_SEEDS} بذرة)")
    _log("   └───────────────────────────────────────────────────────────")

    n_cards0 = len(res["B0"]["cards"])
    if n_cards0 < PRA.FLOOR_CARDS:
        _log(f"   ⛔ الأرضية: كروتُ `B0` {n_cards0} دون {PRA.FLOOR_CARDS} "
             "⇒ لا حكم (خروج 4).")
        return 4

    d1 = [res["B1"]["per_sess"][s] - res["B0"]["per_sess"][s] for s in sess]
    d3 = [res["B3"]["per_sess"][s] - res["B0"]["per_sess"][s] for s in sess]
    ci1, ci3 = PRA.boot_ci(d1), PRA.boot_ci(d3)
    _log(f"   📐 B1−B0 = {nets['B1'] - nets['B0']:+.4f} "
         f"[{ci1['lo']:+.4f},{ci1['hi']:+.4f}] · B3−B0 = "
         f"{nets['B3'] - nets['B0']:+.4f} [{ci3['lo']:+.4f},{ci3['hi']:+.4f}] · "
         f"B1 فوق مئين95؟ {'نعم' if nets['B1'] > res['_a2']['p95'] else 'لا'}")

    _log("DIFF2 " + json.dumps({"year": year,
                                "d1": [round(x, 6) for x in d1],
                                "d3": [round(x, 6) for x in d3]},
                               ensure_ascii=False))
    _log("HOLD2 " + json.dumps(
        {"year": year, "sessions": len(sess), "ready_full": len(rows_full),
         "ready_live": len(rows_live), "median_live": med, "pool_cut": cut,
         "cap": cap, "bind": res["B0"]["bind"], "pq_share": round(pq_share, 1),
         "hv8": round(hv8[0], 1), "hw1_old": old, "hw1_new": new,
         "hw1_drop": round(drop, 1), "r_win": round(rw, 4), "only1": only1,
         "a2_med": round(res["_a2"]["med"], 4),
         "a2_p95": round(res["_a2"]["p95"], 4),
         "live": {k: round(nets[k], 4) for k in nets},
         "full": {k: round(fnets[k], 4) for k in fnets},
         "full_ci1": {"lo": round(fci1["lo"], 4), "hi": round(fci1["hi"], 4)},
         "full_ci3": {"lo": round(fci3["lo"], 4), "hi": round(fci3["hi"], 4)},
         "full_a2": {"med": round(rf["_a2"]["med"], 4),
                     "p95": round(rf["_a2"]["p95"], 4)},
         "ci1": {"lo": round(ci1["lo"], 4), "hi": round(ci1["hi"], 4)},
         "ci3": {"lo": round(ci3["lo"], 4), "hi": round(ci3["hi"], 4)},
         "crit": _crit(nets, ci1, res["_a2"]),
         "cards": {k: len(res[k]["cards"]) for k in ("B0", "B1", "B3")}},
        ensure_ascii=False))
    return 0


def main() -> int:
    import Super_stock as S                                      # noqa: PLC0415
    import press_radar as PR                                     # noqa: PLC0415
    import rebound_arms as RB                                    # noqa: PLC0415
    year = (os.environ.get("BACKTEST_YEAR") or "?").strip()
    path = os.environ.get("BT_FROZEN_PATH") or "frozen_backtest.pkl.gz"
    _log(f"\n{'=' * 78}\n🕰️🥇② T-HOLD-KEY-2 — سنة {year}\n{'=' * 78}")

    fz = hw2_frozen()
    for p, (ok, got, exp) in fz.items():
        _log(f"   {'✅' if ok else '⛔'} `HW2` تجميد {p}: {got} "
             f"(المثبَّت {exp})")
    if not all(v[0] for v in fz.values()):
        _log("   ⛔ `HW2` أداةٌ مجمَّدةٌ تغيّرت ⇒ أرقامُها المنشورة تُبطَل "
             "(خروج 3).")
        return 3

    if not os.path.exists(path):
        _log(f"⛔ اللقطة المجمَّدة مفقودة ({path!r}) ⇒ خروج 2.")
        return 2
    hist, _sp, asof = S.load_frozen_dataset(path)
    _log(f"📦 لقطة as-of {asof} · رموز {len(hist)}")
    yr = year if year and year != "?" else None

    ok, dec, k = PRA.pv0_gate(hist, yr)
    exp_w = HK.PV0_WINNERS.get(str(year))
    ok = ok and (exp_w is None or k == exp_w)
    _log(f"   {'✅' if ok else '⛔'} `HV1` HOLD3 محسومة={dec} · فائزة={k} "
         f"(المنشور {PRA.PV0_RESOLVED.get(str(year), '؟')} · {exp_w})")
    if not ok:
        _log("   ⛔ `HV1` تفرّقٌ عن أرقام §⑬ المنشورة ⇒ عطبُ أداة (خروج 3).")
        return 3

    gdates = grid_dates(hist, yr)
    gset = set(gdates)
    _log(f"   📅 شبكةُ `Q5` بتقويمٍ مشترك: {len(gdates)} تاريخًا "
         f"(خطوة {HK.Q5_STRIDE})")
    if not gdates:
        _log("   ⛔ صفرُ تاريخِ شبكة ⇒ خروج 4.")
        return 4

    syms = [s for s, d in hist.items()
            if d is not None and len(d) >= RB.MIN_BARS + 5]
    t0 = time.perf_counter()
    done = 0
    for sym in syms[:HK.PROBE_SYMS]:
        q5_grid_cal(sym, hist[sym], gset, RB.MIN_BARS)
        done += 1
    per = (time.perf_counter() - t0) / max(1, done)
    proj = per * len(syms)
    _log(f"   📐 `HV3` كلفةُ الشبكة: {per*1000:.0f}ms للرمز ⇒ الإسقاط "
         f"{proj/60:.1f} دقيقة لـ{len(syms)} رمزًا (السقف {HK.BUDGET_SEC/60:.0f})")
    if proj > HK.BUDGET_SEC:
        _log("   ⛔ `HV3` الإسقاطُ يتجاوز الميزانية ⇒ خروج 6.")
        return 6

    grids, movers, pos_of, rows, n_syms, n_seen = {}, {}, {}, [], 0, 0
    for sym, df in hist.items():
        n_seen += 1
        if df is None or len(df) < RB.MIN_BARS + 5:
            continue
        n_syms += 1
        grids[sym] = q5_grid_cal(sym, df, gset, RB.MIN_BARS)
        movers[sym] = HK.mover_days(df)
        pos_of[sym] = {str(d)[:10]: i for i, d in enumerate(df.index)}
        rows.extend(PRA.ready_rows(sym, df, yr))
        if n_syms % 500 == 0:
            _log(f"  … مشى {n_syms} رمزًا · صفوفٌ جاهزة {len(rows)}")

    top_dates, cap = top_by_date(grids)
    n_hits = sum(len(g) for g in grids.values())
    n_top = sum(len(v) for v in top_dates.values())
    _log(f"   🧮 تأهّلٌ خام {n_hits} · وبعد `select_top` (سعة {cap}) {n_top} "
         f"على {len(top_dates)} تاريخًا")

    enrich2(rows, grids, movers, pos_of, top_dates)
    pq_share = 100.0 * sum(1 for r in rows if r.get("prev_q")) / max(1, len(rows))
    pos_grid = {s: [(i, d) for i, d, _m in g] for s, g in grids.items()}
    hv8 = HK.hv8_agree(rows, hist, pos_grid, pos_of)
    hw1 = hw1_gate(rows)
    rows_live, cut = HK.live_pool(rows)
    _log(f"   📡 البِركةُ المُعادُ بناؤها بـ`select_top`: ترشيحٌ حيّ "
         f"{sum(1 for r in rows if r.get('live_q'))} · متحرّك "
         f"{sum(1 for r in rows if r.get('live_mv'))} · "
         f"`MEMORY_DAYS`={PR.MEMORY_DAYS} · `POOL_CAP`={PR.POOL_CAP}")
    return report2(rows, rows_live, cut, n_syms, n_seen, year, hv8, pq_share,
                   hw1, cap)


if __name__ == "__main__":
    sys.exit(main())
