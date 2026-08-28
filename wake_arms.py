#!/usr/bin/env python3
"""🔔 `T-WAKE` — بوّابةُ الإيقاظ: نافذةُ إعادة التنبيه وحصرُ الكرت بالمستيقظين.

العقد `wake_prereg.md` **مدفوعٌ قبل أيّ سطرٍ هنا** (‏`85c7b8b9`).
🔒 **قراءةٌ فقط · صفرُ مسٍّ بالإنتاج · لا `LOGIC_VERSION`.**

⚖️ **مقياسٌ واحدٌ لا اثنان:** المجتمعُ `D_live2` **يُبنى بدوالِّ
`hold_key2_arms` المجمَّدة بالاسم** (‏`grid_dates` · `q5_grid_cal` ·
`top_by_date` · `enrich2` · `hw1_gate`) ومعها `hold_key_arms.live_pool` —
**ولا يُعاد بناءُ صفٍّ واحد**. والمتغيّرُ الوحيدُ شقّا الإيقاظ (‏§①).

🔴 **ولماذا `deliver_wake` نسخةٌ مُوسَّعة لا نداءٌ للمجمَّدة:**
`hold_key_arms.deliver_prod` مجمَّدةٌ بثوابتها (‏`PR.should_alert` و
`base = fire if fire else xs`) ⇒ تعديلُها يُبطل أرقامًا منشورة (‏CAP15).
**و`WV0` يُثبت أن الموسَّعة عند `(5, False)` تُعيدها بت-بت** — سابقةُ
`V0`/`RV0`/`BV0`.
"""
import hashlib
import json
import os
import statistics
import sys
import time

import hold_key2_arms as HK2           # §② بناءُ D_live2 — grid_dates · q5_grid_cal · top_by_date · enrich2 · hw1_gate
import hold_key_arms as HK             # live_pool · mover_days · order_b0 · hv8_agree · deliver_prod
import press_rank_arms as PRA          # ready_rows · r_of · boot_ci · dedupe_violations · pv0_gate

# ─────────────────────────────── ثوابتُ العقد ───────────────────────────────
# `WW1` — تجميدُ الأدوات الثلاث التي نُشرت أرقامُها (سابقةُ CAP15 · §⑨-1).
FROZEN_SHA = {
    "hold_key2_arms.py":
        "6c8f7d2a2d8c24f0347a9abb1e45626df4c3ea25b54f30c3a7b896c72230bd73",
    "hold_key_arms.py":
        "39643875f649a42fdb5624e3dce76e6dc9721637b76a270472d78e31be8816c0",
    "press_rank_arms.py":
        "6bb28144c1742840c4c45e651f2ae46a354a2928c671b0487047f69cdac10fd7",
}

# §③ الأذرعُ الأربع — (الاسم، نافذةُ إعادة التنبيه، إكمالٌ من الهادئين)
ARMS = (("W0", 5, False), ("W1", 1, False), ("W2", 10, False), ("W3", 5, True))

QUAL_TOL_R = 0.02          # §④-1 مُعادٌ حرفيًّا من T-STABILITY/T-BASE-475
COST_MAX_PCT = 50.0        # §④-3 مُعادٌ حرفيًّا من T-CUMRISE §④

# §⑤ `WV0` — جسرٌ إلى `B0` المنشور في `hold_key2_result.md §②`
PUB_B0_NET = {"2023": 0.1598, "2024": 1.7639, "2025": 1.7794}
PUB_B0_CARDS = {"2023": 1323, "2024": 1508, "2025": 1451}
PUB_B0_BIND = {"2023": 47, "2024": 75, "2025": 60}


def _log(m):
    print(m, flush=True)


def _sha(path):
    try:
        with open(path, "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()
    except OSError:
        return ""


def ww1_frozen():
    """**`WW1`**: الأدواتُ الثلاثُ المجمَّدة لم تُمَسّ — تُقارَن بصماتُها."""
    out = {}
    for p, exp in FROZEN_SHA.items():
        got = _sha(p)
        out[p] = (got[:16] == exp[:16], got[:16], exp[:16])
    return out


# ───────────────────── §① بوّابةُ الإيقاظ — الشقّان معًا ─────────────────────

def wake_should_alert(entry, today_iso, realert_days):
    """`press_radar.should_alert` **بوسيطٍ للنافذة** — عند القيمة الإنتاجية
    (‏`REALERT_DAYS`) يعيدها حرفيًّا (مقفولٌ `WK2`)."""
    import press_radar as PR                                     # noqa: PLC0415
    last = (entry or {}).get("last_alert")
    if not last:
        return True
    gap = PR._days_between(last, today_iso)
    return gap is None or gap >= realert_days


def dedupe_viol_win(cards, realert_days):
    """`WV6`: صفرُ رمزٍ يُسلَّم مرّتين **داخل نافذة الذراع نفسِها** — نسخةٌ
    بوسيطٍ من `press_rank_arms.dedupe_violations` (مقفولةٌ `WK3` عند 5)."""
    import press_radar as PR                                     # noqa: PLC0415
    last, bad = {}, 0
    for c in cards:
        prev = last.get(c["sym"])
        if prev is not None:
            gap = PR._days_between(prev, c["s"])
            if gap is not None and gap < realert_days:
                bad += 1
        last[c["sym"]] = c["s"]
    return bad


def deliver_wake(by_sess, sessions, order_fn, rw, realert_days,
                 fill_from_quiet):
    """قاعدةُ عددِ كروت الإنتاج (‏`press_radar.py:604,618,622`) **بشقَّي الإيقاظ
    وسيطَين**:

    · `realert_days` — نافذةُ الدِدوب (الإنتاج 5).
    · `fill_from_quiet` — إن `False` فالمستيقظون **يحصرون** الكرت بلا إكمال
      (الإنتاج)؛ وإن `True` فهم **يتقدّمون** ويُكمَل من الهادئين حتى السقف.

    ⚖️ وعند `(REALERT_DAYS, False)` تُعيد `hold_key_arms.deliver_prod` **بت-بت**
    (‏`WV0`). وتُرجع معها عدّادَ ما كتمه الدِدوب (‏`WV5`)."""
    import press_radar as PR                                     # noqa: PLC0415
    mem, per_sess, cards = {}, {}, []
    n_bind = n_seen = n_muted = 0
    for s in sessions:
        pool = by_sess.get(s, [])
        n_seen += len(pool)
        cand = [r for r in pool
                if wake_should_alert(mem.get(r["symbol"], {}), s, realert_days)]
        n_muted += len(pool) - len(cand)
        xs = order_fn(cand)
        fire = [r for r in xs if (r.get("wake") or {}).get("awake")]
        if fill_from_quiet:
            quiet = [r for r in xs if not (r.get("wake") or {}).get("awake")]
            base = fire + quiet
        else:
            base = fire if fire else xs
        if len(base) > PR.ALERT_CAP:
            n_bind += 1
        picked = base[:PR.ALERT_CAP]
        tot = 0.0
        for r in picked:
            mem[r["symbol"]] = {"last_alert": s}
            tot += PRA.r_of(r["oc"], rw)
            cards.append({"s": s, "sym": r["symbol"], "oc": r["oc"]})
        per_sess[s] = tot
    return {"per_sess": per_sess, "cards": cards, "bind": n_bind,
            "seen": n_seen, "muted": n_muted}


def run_wake(rows, rw):
    """يشغّل الأذرعَ الأربع على مجتمعٍ واحدٍ وميزانيةٍ واحدة (‏§③)."""
    by_sess = {}
    for r in rows:
        by_sess.setdefault(r["session"], []).append(r)
    sessions = sorted(by_sess)
    res = {"_sessions": sessions}
    for name, days, fill in ARMS:
        res[name] = deliver_wake(by_sess, sessions, HK.order_b0, rw, days, fill)
    return res


def arm_stats(d, sessions, rw):
    """المقاييسُ الثلاثة (‏§④): `R`/كرت حاكمًا · و`R`/جلسة والكروتُ رفيقَين."""
    dec = [c for c in d["cards"] if c["oc"] in ("win", "loss")]
    win = sum(1 for c in dec if c["oc"] == "win")
    tot = sum(d["per_sess"].values())
    n_cards = len(d["cards"])
    return {"cards": n_cards, "dec": len(dec), "win": win,
            "r_card": tot / max(1, n_cards),
            "r_sess": tot / max(1, len(sessions)),
            "hit": 100.0 * win / max(1, len(dec)),
            "bind": d["bind"], "muted_pct": 100.0 * d["muted"] / max(1, d["seen"])}


# ──────────────────────────────── التقرير ────────────────────────────────

def report(rows_live, n_syms, n_seen, year, hv8, med, mute_ref) -> int:
    import press_backtest as PB                                  # noqa: PLC0415
    import press_radar as PR                                     # noqa: PLC0415
    rw = PB.r_win_value()
    _log(f"\n{'—' * 74}\n🔔 T-WAKE سنة {year} — رموزٌ مفحوصة {n_syms} · "
         f"جاهزٌ (بِركة) {len(rows_live)} · R_win={rw:.2f} · "
         f"`REALERT_DAYS`={PR.REALERT_DAYS} · `ALERT_CAP`={PR.ALERT_CAP}")

    cov = 100.0 * n_syms / max(n_seen, 1)
    _log(f"   🩺 `WV7` التغطية {cov:.1f}% ({n_syms} من {n_seen})")
    if cov < PRA.COVERAGE_MIN:
        _log(f"   ⛔ `WV7` دون {PRA.COVERAGE_MIN}% ⇒ خروج 3.")
        return 3
    if not rows_live:
        _log("   ⛔ صفرُ صفٍّ (بصمةُ الـ`no-op`) ⇒ خروج 4.")
        return 4

    _log(f"   {'✅' if hv8[0] >= HK.HV8_MIN_AGREE else '⛔'} `HV8` توافقُ شبكة "
         f"`Q5` = {hv8[0]:.1f}% (ن={hv8[1]})")
    if hv8[0] < HK.HV8_MIN_AGREE:
        _log(f"   ⛔ `HV8` دون {HK.HV8_MIN_AGREE}% ⇒ خروج 3.")
        return 3

    res = run_wake(rows_live, rw)
    sess = res["_sessions"]

    # ── `WV0` — جسرُ التكامل: `W0` يُعيد `deliver_prod` والمنشورَ بت-بت ──
    by_sess = {}
    for r in rows_live:
        by_sess.setdefault(r["session"], []).append(r)
    ref = HK.deliver_prod(by_sess, sess, HK.order_b0, rw)
    same = (res["W0"]["per_sess"] == ref["per_sess"]
            and res["W0"]["cards"] == ref["cards"]
            and res["W0"]["bind"] == ref["bind"])
    st0 = arm_stats(res["W0"], sess, rw)
    pub_n, pub_c, pub_b = (PUB_B0_NET.get(str(year)),
                           PUB_B0_CARDS.get(str(year)),
                           PUB_B0_BIND.get(str(year)))
    pub_ok = (pub_n is None
              or (abs(st0["r_sess"] - pub_n) < 5e-5
                  and st0["cards"] == pub_c and st0["bind"] == pub_b))
    _log(f"   {'✅' if (same and pub_ok) else '⛔'} `WV0` `W0` يُعيد "
         f"`deliver_prod` بت-بت={same} · والمنشورَ في `hold_key2_result §②` "
         f"(‏{st0['r_sess']:+.4f} مقابل {pub_n} · كروت {st0['cards']} مقابل "
         f"{pub_c} · بنّد {st0['bind']} مقابل {pub_b})={pub_ok}")
    if not (same and pub_ok):
        _log("   ⛔ `WV0` تفرّقٌ عن المرجع ⇒ عطبُ أداة (خروج 3).")
        return 3

    # ── `WV4` الكثافة · `WV5` الدِدوبُ يكتم فعلًا ──
    _log(f"   📐 `WV4` وسيطُ الجاهزين/جلسة = {med:.1f}")
    if not (HK.LIVE_MED_MIN <= med <= HK.LIVE_MED_MAX):
        _log(f"   ⛔ `WV4` خارج [{HK.LIVE_MED_MIN},{HK.LIVE_MED_MAX}] ⇒ خروج 4.")
        return 4
    _log(f"   📐 `WV5` نصيبُ ما يكتمه الدِدوب في `W0` = "
         f"{st0['muted_pct']:.1f}% (من {res['W0']['seen']} صفًّا) · "
         f"وجلساتٌ فيها مستيقظٌ فأكثر = {mute_ref:.1f}%")
    if not (0.0 < st0["muted_pct"] < 100.0):
        _log("   ⛔ `WV5` الدِدوبُ منحلّ ⇒ `no-op` (خروج 4).")
        return 4

    # ── `WV6` الدِدوبُ نافذٌ داخلَ نافذة كلّ ذراع ──
    bad = {n: dedupe_viol_win(res[n]["cards"], d)
           for n, d, _f in ARMS}
    _log("   📐 `WV6` خرقُ الدِدوب (بنافذة كلّ ذراع): "
         + " · ".join(f"{k}={v}" for k, v in bad.items()))
    if any(bad.values()):
        _log("   ⛔ `WV6` الدِدوبُ غيرُ نافذ ⇒ خروج 3.")
        return 3

    # ── الجدول ──
    stats = {n: arm_stats(res[n], sess, rw) for n, _d, _f in ARMS}
    _log("   ┌─ 🔔 الأذرعُ الأربع (الحاكم: `R` لكلّ كرت — §④) ──────────────")
    for n, d, f in ARMS:
        s = stats[n]
        _log(f"   │ {n} (دِدوب {d}ج · إكمال={'نعم' if f else 'لا'}): "
             f"R/كرت {s['r_card']:+.4f} · R/جلسة {s['r_sess']:+.4f} · كروت "
             f"{s['cards']} · فائز {s['win']} · بلغ الهدف {s['hit']:.2f}% · "
             f"بنّد {s['bind']} · كتم {s['muted_pct']:.1f}%")
    _log("   └───────────────────────────────────────────────────────────")

    # ── `WV2` الأذرعُ تتفرّق — **بقائمة الكروت لا بعددها وحدَه** ──
    # (عددٌ متساوٍ بمحتوًى مختلفٍ تفرّقٌ حقيقيّ · وهو المتوقَّعُ لـ`W3` بنصّ
    #  `W-P4` حين لا يبنّد السقف ⇒ العدُّ وحدَه بوّابةٌ عمياء.)
    diff = [n for n, _d, _f in ARMS[1:]
            if res[n]["cards"] != res["W0"]["cards"]]
    _log(f"   📐 `WV2` أذرعٌ تفترق عن `W0` بقائمة الكروت: {diff or 'لا شيء'} "
         + " · ".join(f"{n}Δكروت={stats[n]['cards'] - stats['W0']['cards']:+d}"
                      for n, _d, _f in ARMS[1:]))
    if not diff:
        _log("   ⛔ `WV2` صفرُ تفرّق ⇒ `no-op` (خروج 4).")
        return 4

    # ── `WV3` الأرضيتان ──
    if len(sess) < PRA.FLOOR_SESSIONS:
        _log(f"   ⛔ الأرضية: الجلسات {len(sess)} دون {PRA.FLOOR_SESSIONS} "
             "⇒ لا حكم (خروج 4).")
        return 4
    if stats["W0"]["cards"] < PRA.FLOOR_CARDS:
        _log(f"   ⛔ الأرضية: كروتُ `W0` {stats['W0']['cards']} دون "
             f"{PRA.FLOOR_CARDS} ⇒ لا حكم (خروج 4).")
        return 4

    # ── المعاييرُ الثلاثة لهذي السنة (‏④ يُحسم مجمَّعًا في ملفّ النتيجة) ──
    crit = {}
    for n, _d, _f in ARMS[1:]:
        s = stats[n]
        crit[n] = {
            "c1": (s["r_card"] - stats["W0"]["r_card"]) >= -QUAL_TOL_R,
            "c2": s["win"] > stats["W0"]["win"],
            "c3": (100.0 * (s["cards"] - stats["W0"]["cards"])
                   / max(1, stats["W0"]["cards"])) <= COST_MAX_PCT,
            "d_rcard": s["r_card"] - stats["W0"]["r_card"],
            "d_win": s["win"] - stats["W0"]["win"],
            "d_cards_pct": (100.0 * (s["cards"] - stats["W0"]["cards"])
                            / max(1, stats["W0"]["cards"])),
        }
        _log(f"   🎯 {n}: ①{'✅' if crit[n]['c1'] else '🔴'} "
             f"(‏{crit[n]['d_rcard']:+.4f} · الحدّ ‏−{QUAL_TOL_R}) · "
             f"②{'✅' if crit[n]['c2'] else '🔴'} (فائزون {crit[n]['d_win']:+d}) "
             f"· ③{'✅' if crit[n]['c3'] else '🔴'} "
             f"(كروت {crit[n]['d_cards_pct']:+.1f}% · الحدّ ‏+{COST_MAX_PCT})")

    _log("WAKE " + json.dumps(
        {"year": year, "sessions": len(sess), "ready_live": len(rows_live),
         "median_live": med, "r_win": round(rw, 4), "hv8": round(hv8[0], 1),
         "awake_sess_pct": round(mute_ref, 1),
         "arms": {n: {k: (round(v, 4) if isinstance(v, float) else v)
                      for k, v in stats[n].items()} for n, _d, _f in ARMS},
         "crit": {n: {k: (round(v, 4) if isinstance(v, float) else v)
                      for k, v in crit[n].items()} for n in crit}},
        ensure_ascii=False))
    return 0


def main() -> int:
    import Super_stock as S                                      # noqa: PLC0415
    import press_radar as PR                                     # noqa: PLC0415
    import rebound_arms as RB                                    # noqa: PLC0415
    year = (os.environ.get("BACKTEST_YEAR") or "?").strip()
    path = os.environ.get("BT_FROZEN_PATH") or "frozen_backtest.pkl.gz"
    _log(f"\n{'=' * 78}\n🔔 T-WAKE — سنة {year}\n{'=' * 78}")

    fz = ww1_frozen()
    for p, (ok, got, exp) in fz.items():
        _log(f"   {'✅' if ok else '⛔'} `WW1` تجميد {p}: {got} (المثبَّت {exp})")
    if not all(v[0] for v in fz.values()):
        _log("   ⛔ `WW1` أداةٌ مجمَّدةٌ تغيّرت ⇒ أرقامُها المنشورة تُبطَل "
             "(خروج 3).")
        return 3

    if not os.path.exists(path):
        _log(f"⛔ اللقطة المجمَّدة مفقودة ({path!r}) ⇒ خروج 2.")
        return 2
    hist, _sp, asof = S.load_frozen_dataset(path)
    _log(f"📦 لقطة as-of {asof} · رموز {len(hist)}")
    yr = year if year and year != "?" else None

    gdates = HK2.grid_dates(hist, yr)
    gset = set(gdates)
    _log(f"   📅 شبكةُ `Q5` بتقويمٍ مشترك: {len(gdates)} تاريخًا")
    if not gdates:
        _log("   ⛔ صفرُ تاريخِ شبكة ⇒ خروج 4.")
        return 4

    t0 = time.perf_counter()
    grids, movers, pos_of, rows, n_syms, n_seen = {}, {}, {}, [], 0, 0
    for sym, df in hist.items():
        n_seen += 1
        if df is None or len(df) < RB.MIN_BARS + 5:
            continue
        n_syms += 1
        grids[sym] = HK2.q5_grid_cal(sym, df, gset, RB.MIN_BARS)
        movers[sym] = HK.mover_days(df)
        pos_of[sym] = {str(d)[:10]: i for i, d in enumerate(df.index)}
        rows.extend(PRA.ready_rows(sym, df, yr))
        if n_syms % 500 == 0:
            _log(f"  … مشى {n_syms} رمزًا · صفوفٌ جاهزة {len(rows)} · "
                 f"{(time.perf_counter() - t0) / 60:.1f} دقيقة")

    top_dates, cap = HK2.top_by_date(grids)
    HK2.enrich2(rows, grids, movers, pos_of, top_dates)
    pos_grid = {s: [(i, d) for i, d, _m in g] for s, g in grids.items()}
    hv8 = HK.hv8_agree(rows, hist, pos_grid, pos_of)
    rows_live, cut = HK.live_pool(rows)
    _log(f"   📡 البِركةُ بـ`select_top` (سعة {cap}): صفوفٌ حيّة "
         f"{len(rows_live)} · قُصّ بالسقف {cut}")

    by = {}
    for r in rows_live:
        by.setdefault(r["session"], []).append(r)
    med = statistics.median([len(v) for v in by.values()]) if by else 0.0
    awake_sess = sum(1 for v in by.values()
                     if any((r.get("wake") or {}).get("awake") for r in v))
    mute_ref = 100.0 * awake_sess / max(1, len(by))
    return report(rows_live, n_syms, n_seen, year, hv8, med, mute_ref)


if __name__ == "__main__":
    sys.exit(main())
