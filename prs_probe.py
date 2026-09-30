#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🧪 مِجَسٌّ مؤقّت (يُحذف قبل الدمج) — رادارُ الضغط وحاصدُه على TradingView مقابل ياهو (أمرُ المالك 2026-09-30
«انقل رادار الضغط إلى ترندق فيو»). **قراءةٌ فقط:** لا تلغرام · لا كتابةَ حالة ولا سجلّ · لا git.

⚖️ **معيارُ القبول مكتوبٌ هنا قبل أوّل تشغيل (نمطُ HP1-HP4 في #502):**
  PR1 التغطية: إطاراتُ وضع TradingView (مع احتياط ياهو) ‏≥ 99.5% من إطارات ياهو وحدَه على بِركة الرادار نفسِها.
  PR2 من TradingView: الموسومُ `tradingview` ‏≥ 97% من إطارات وضع TradingView.
  PR3 الزمن: تحميلُ البِركة بوضع TradingView ‏≤ 300 ثانية.
  PR4 صفرُ استثناءٍ في خطوات المِجَسّ الحاكمة (التحميلان · القراءة · الافتر).
  PR5 الافتر: `extended_last_price(fetch_bars=tv_session_minutes)` يُرجع سعرًا لحافظٍ واحدٍ على الأقلّ وصفرُ استثناء.
  ⟵ **PR1-PR4 كلُّها ✅ ⇒ يُدمج نقلُ الشموع** · وPR5 ساقط ⇒ يُدمج ويُعلَن «الافترُ لم يُستعَد» (فاشلٌ-آمنٌ كاليوم).
وصفيٌّ بلا حدّ (يُطبع ولا يحكم): المطابقُ/الحافظُ/المستيقظُ على المصدرين وانقلاباتُه بسببٍ مُسمًّى · وإطاراتُ TradingView بلا
شمعة آخر جلسةٍ مكتملة · وتغطيةُ الافتر ونِسَبُه · وأثرُ حارس التقسيم غير المسوّى على صفوف السجلّ القائمة (ياهو) ·
وحسمُ السجلّ نفسِه على شموع TradingView للمقارنة.
🔮 **تنبّؤاتٌ قبل الرقم (تُنشر ولا تُحذف):** (أ) الانقلاباتُ قليلة (‏≤5% من المطابقين) وأغلبُها أيّامٌ عند ياهو وحدَه (حشوُه) ·
(ب) إطاراتُ TradingView بلا شمعة الجلسة ‏≤3% من البِركة · (ج) تغطيةُ الافتر للحافظين بين 50% و90% (سابقةُ `T-TVPRE` ‏76%) ·
(د) صفوفُ السجلّ التي يعلّمها حارسُ التقسيم على ياهو قليلة (‏0-5) ومنها TNMG ‏08-14 إن بقي تقسيمُه غيرَ مسوّى عند ياهو.
"""
import os
import sys
import time
import traceback

CRIT = {"PR1": 99.5, "PR2": 97.0, "PR3": 300.0}


def main() -> int:
    import Super_stock as S
    import press_radar as PR
    import press_harvest as PH
    import split_hunter as H
    import hunter_ledger as HL
    import hunter_outcomes as HO

    errors = []
    ok_gate, sess = H.session_gate()
    session_iso = str(sess)
    last_closed = S.last_closed_session()
    wl = S.load_watchlist() or {}
    state = PR.load_state(PR.STATE_FILE)
    pool, cut = PR.build_pool(wl, state, session_iso)
    print(f"⏰ الجلسة (session_gate) {session_iso} · آخرُ جلسةٍ مكتملة {last_closed} · البِركة {len(pool)} (قُصّ {cut})")

    # ── التحميلان ──────────────────────────────────────────────────────────
    old = os.environ.pop("BARS_SOURCE", None)
    try:
        t0 = time.monotonic()
        hy = S.download_history(list(pool)) or {}
        ty = time.monotonic() - t0
    except Exception as e:                                       # noqa: BLE001
        errors.append(f"ياهو: {e!r}")
        hy, ty = {}, 0.0
    os.environ["BARS_SOURCE"] = "tradingview"
    try:
        t0 = time.monotonic()
        ht = S.download_history(list(pool)) or {}
        tt = time.monotonic() - t0
    except Exception as e:                                       # noqa: BLE001
        errors.append(f"TradingView: {e!r}")
        ht, tt = {}, 0.0
    ny = sum(1 for d in hy.values() if d is not None and not getattr(d, "empty", True))
    nt = sum(1 for d in ht.values() if d is not None and not getattr(d, "empty", True))
    ntv = sum(1 for d in ht.values() if HL.frame_src(d) == HL.SRC_TV)
    pr1 = 100.0 * nt / max(1, ny)
    pr2 = 100.0 * ntv / max(1, nt)
    print(f"📥 ياهو {ny} في {ty:.1f}ث · وضعُ TradingView {nt} (منها TradingView {ntv}) في {tt:.1f}ث")

    # ── القراءة على المصدرين ────────────────────────────────────────────────
    def reads(h):
        out = {}
        for s in pool:
            d = h.get(s)
            if d is None or getattr(d, "empty", True):
                continue
            try:
                r = PR.press_read(d, w=PR.ALERT_W)
            except Exception as e:                               # noqa: BLE001
                errors.append(f"press_read {s}: {e!r}")
                r = None
            if r:
                w = PR.wake_read(d, ah_pct=None)
                out[s] = {"hold": int(r.get("hold_sessions") or 0), "awake": bool(w.get("awake")),
                          "close": r.get("close"), "low": r.get("press_low")}
        return out

    ry, rt = reads(hy), reads(ht)
    ready_y = {s for s, v in ry.items() if v["hold"] >= PR.READY_HOLD}
    ready_t = {s for s, v in rt.items() if v["hold"] >= PR.READY_HOLD}
    print(f"🗜️ المطابق: ياهو {len(ry)} · TradingView {len(rt)} · مشترك {len(set(ry) & set(rt))}")
    print(f"   الحافظ ({PR.READY_HOLD}+): ياهو {len(ready_y)} · TradingView {len(ready_t)} · مشترك {len(ready_y & ready_t)}")
    print(f"   المستيقظ بلا افتر: ياهو {sum(v['awake'] for v in ry.values())} · "
          f"TradingView {sum(v['awake'] for v in rt.values())}")

    def why(s):
        a, b = hy.get(s), ht.get(s)
        try:
            da = {str(x)[:10] for x in a.index} if a is not None else set()
            db = {str(x)[:10] for x in b.index} if b is not None else set()
            only_y = sorted(d for d in da - db if d >= min(db or da or {""}))
            only_t = sorted(db - da)
            if only_y:
                return f"أيّامٌ عند ياهو وحدَه {len(only_y)} (آخرُها {only_y[-1]})"
            if only_t:
                return f"أيّامٌ عند TradingView وحدَه {len(only_t)}"
            return "فرقُ OHLC"
        except Exception as e:                                   # noqa: BLE001
            return f"تعذّر ({type(e).__name__})"

    flips = sorted((set(ry) ^ set(rt)) | {s for s in set(ry) & set(rt)
                                          if (ry[s]["hold"] >= PR.READY_HOLD) != (rt[s]["hold"] >= PR.READY_HOLD)})
    print(f"🔁 انقلاباتُ المطابقة/الحفظ: {len(flips)}")
    for s in flips[:40]:
        print(f"   {s}: ياهو={ry.get(s)} · TradingView={rt.get(s)} · السبب: {why(s)}")

    # ── الطزاجة ─────────────────────────────────────────────────────────────
    summ = PR.bars_src_summary(ht, last_closed)
    print(f"📺 إطاراتُ TradingView بلا شمعة آخر جلسةٍ مكتملة ({last_closed}): {len(summ['stale'])} من {summ['tv']} — "
          f"{', '.join(summ['stale'][:20])}")

    # ── الافتر من TradingView ───────────────────────────────────────────────
    ah_ok, ah_asked, ah_vals = 0, 0, []
    try:
        import tv_data as TVD
        ch = TVD.Chart()
        try:
            for s in sorted(ready_t):
                ah_asked += 1
                try:
                    ext = S.extended_last_price(s, session_iso,
                                                fetch_bars=lambda _s, _d: S.tv_session_minutes(_s, _d, chart=ch))
                except Exception as e:                           # noqa: BLE001
                    errors.append(f"افتر {s}: {e!r}")
                    ext = None
                if ext:
                    ah_ok += 1
                    cl = float(rt[s]["close"] or 0)
                    if cl > 0:
                        ah_vals.append((s, round((float(ext) / cl - 1.0) * 100.0, 1)))
        finally:
            ch.close()
    except Exception as e:                                       # noqa: BLE001
        errors.append(f"مِقبس الافتر: {e!r}")
    hot = [x for x in ah_vals if abs(x[1]) >= float(S.CONFIG.get("PM_MOVE_PCT", 10))]
    print(f"🌙 الافتر ({session_iso}): قُرئ {ah_ok} من {ah_asked} حافظًا · فوق عتبة الصحوة {len(hot)}: {hot[:15]}")
    print(f"   أكبرُ النِّسَب: {sorted(ah_vals, key=lambda x: -abs(x[1]))[:10]}")

    # ── الحاصد: أثرُ حارس التقسيم على السجلّ القائم · وحسمُه على TradingView للمقارنة ───────────
    try:
        rows, bad = PH.load_ledger()
        syms = sorted({str(r.get("symbol")) for r in rows if r.get("symbol")})
        fx = HO.src_fetchers(S, log=print)
        dy, dtv = {}, {}
        for k in range(0, len(syms), 60):
            dy.update(fx[HL.SRC_YAHOO](syms[k:k + 60]) or {})
        dtv.update(fx[HL.SRC_TV](syms) or {})
        spl = lambda _s, _d: HO.split_events_after(S._fetch_splits(_s), _d)  # noqa: E731
        base = [PH.resolve_row(r, dy.get(str(r.get("symbol")))) for r in rows]
        guard = [PH.resolve_row(r, dy.get(str(r.get("symbol"))), split_events=spl) for r in rows]
        ontv = [PH.resolve_row(r, dtv.get(str(r.get("symbol"))), split_events=spl) for r in rows]
        flag = [(g["symbol"], g["session"], b["outcome"]) for b, g in zip(base, guard) if g["outcome"] != b["outcome"]]
        print(f"📒 السجلّ: {len(rows)} صفًّا · {len(syms)} رمزًا · ياهو {len(dy)} · TradingView {len(dtv)}")
        print(f"⚖️ حارسُ التقسيم على ياهو غيّر {len(flag)} صفًّا (كانت ⟵ split_unadjusted): {flag[:20]}")
        cmp_ = {}
        for b, t in zip(guard, ontv):
            k = (b["outcome"], t["outcome"])
            cmp_[k] = cmp_.get(k, 0) + 1
        diff = {k: v for k, v in cmp_.items() if k[0] != k[1]}
        print(f"🔁 الحسمُ على ياهو مقابل TradingView (وصفٌ · الصفوفُ القديمة تبقى على ياهو): مختلفٌ "
              f"{sum(diff.values())} من {len(rows)} · {sorted(diff.items(), key=lambda x: -x[1])[:12]}")
    except Exception as e:                                       # noqa: BLE001
        errors.append(f"الحاصد: {e!r}")
        traceback.print_exc()

    # ── الحكم ───────────────────────────────────────────────────────────────
    v1, v2, v3, v4 = pr1 >= CRIT["PR1"], pr2 >= CRIT["PR2"], tt <= CRIT["PR3"], not errors
    v5 = ah_ok >= 1 and not [e for e in errors if e.startswith(("افتر", "مِقبس"))]
    print("=" * 70)
    print(f"PR1 التغطية {pr1:.2f}% (الحدّ {CRIT['PR1']}%) {'✅' if v1 else '❌'}")
    print(f"PR2 من TradingView {pr2:.2f}% (الحدّ {CRIT['PR2']}%) {'✅' if v2 else '❌'}")
    print(f"PR3 الزمن {tt:.1f}ث (الحدّ {CRIT['PR3']:.0f}) {'✅' if v3 else '❌'}")
    print(f"PR4 صفرُ استثناء {'✅' if v4 else '❌ ' + ' | '.join(errors[:5])}")
    print(f"PR5 الافتر {ah_ok} من {ah_asked} {'✅' if v5 else '❌'}")
    verdict = ("يُدمج" if (v1 and v2 and v3 and v4) else "لا يُدمج")
    print(f"⚖️ الحكم المسجَّل: {verdict}" + ("" if v5 or not (v1 and v2 and v3 and v4)
                                             else " · والافترُ لم يُستعَد (يُعلَن)"))
    if old is None:
        os.environ.pop("BARS_SOURCE", None)
    else:
        os.environ["BARS_SOURCE"] = old
    return 0


if __name__ == "__main__":
    os.environ.setdefault("SCREENER_MODE", "DIGEST")
    sys.exit(main())
