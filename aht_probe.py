#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🧪 مِجَسٌّ مؤقّت (يُحذف قبل الدمج) — حارسُ الافتر للمقسّم على TradingView (أمرُ المالك 2026-10-01 «شغّل حارس الافتر
للمقسّم على ترندق فيو»). **قراءةٌ فقط:** لا تلغرام · لا كتابةَ حالة ولا سجلّ · لا git · لا Polygon.

المجتمع: أسماءُ رادار التقسيم في تقرير 09-30 (‏YHC · WOK · NXTT · HAO · INLF · AIXI — أوّلُ ستّةٍ من 12 طُبعت في
السجلّ `36684201530`) ‏+ قائمةُ متابعة الصيّاد ‏+ نشطو القائمة ‏+ «تحت المتابعة» حتى 80 رمزًا (ترتيبٌ حتميّ) · وضبطٌ سائلٌ ثمانية.
القناتان المستقلّتان للتحقّق: سعرُ ما بعد الإغلاق عند ياهو (`postMarketPrice` بطابعه يومَ الجلسة) · وماسحُ TradingView
(‏`postmarket_close` — المصدرُ نفسُه بقناةٍ أخرى · وصفٌ لا حكم).

⚖️ **معيارُ القبول مكتوبٌ هنا قبل أوّل تشغيل:**
  AH1 الآليّة: سعرُ افترٍ من TradingView لـ7 من 8 على الأقلّ في الضبط السائل.
  AH2 الاتّفاق: حيث يوجد سعرُ ياهو مؤرَّخًا بيوم الجلسة ⟵ ‏|TradingView ÷ ياهو − 1| ‏≤ 2% في 90% من الأزواج فأكثر
      (‏8 أزواجٍ على الأقلّ · وإلّا «لا حكم»).
  AH3 التعذّر: «تعذّر» (لا شموع/خطأ مِقبس) ‏≤ 5% من رموز المجتمع.
  AH4 المسارُ الحيّ: `ah_guard_rows` بالبيئة tradingview على صفوف المجتمع ⟵ صفرُ استثناء · المصدر «tradingview» ·
      سُئل = عددُ الصفوف · والزمن ‏≤ 180 ثانية.
  AH5 القرار: حيث يوجد الزوج ⟵ قرارُ الكتم (‏+20% فوق إغلاق الجلسة) متطابقٌ في 95% فأكثر (‏5 أزواجٍ على الأقلّ · وإلّا «لا حكم»).
  ⟵ **AH1 وAH3 وAH4 ✅ وAH2 وAH5 غيرُ ساقطين ⇒ يُدمج** · وأيُّ ❌ ⇒ لا دمجَ قبل التشخيص.
🔮 تنبّؤاتٌ قبل الرقم (تُنشر ولا تُحذف): (أ) نسبةُ القراءة في المجتمع 40-85% (افترُ السنتات متقطّع) · (ب) التعذّر صفر ·
(ج) الاتّفاقُ ضمن 2% ‏≥95% من الأزواج · (د) إغلاقُ الجلسة من آخر دقيقةٍ نظاميّة عند TradingView ضمن 1% من ياهو في 90% فأكثر.
"""
import datetime as dt
import json
import os
import sys
import time
import traceback

FIXED = ["YHC", "WOK", "NXTT", "HAO", "INLF", "AIXI"]
CONTROL = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "META", "AMD", "INTC"]
CAP = 80
CRIT = {"AH1": 7, "AH2_PCT": 2.0, "AH2_SHARE": 90.0, "AH2_MIN": 8, "AH3": 5.0, "AH4_S": 180.0,
        "AH5_SHARE": 95.0, "AH5_MIN": 5, "MUTE": 20.0}


def _load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:                                            # noqa: BLE001
        return {}


def population():
    syms, refs = list(FIXED), {}
    hw = _load("hunter_watchlist.json")
    for s in (hw.get("stocks") or []):
        if isinstance(s, dict) and s.get("symbol"):
            syms.append(str(s["symbol"]).upper())
            try:
                refs[str(s["symbol"]).upper()] = float(s.get("ref")) if s.get("ref") else None
            except (TypeError, ValueError):
                pass
    wl = _load("weekly_watchlist.json")
    syms += sorted(str(s.get("symbol")).upper() for s in (wl.get("stocks") or [])
                   if isinstance(s, dict) and s.get("status") == "active" and s.get("symbol"))
    nw = _load("near_watch.json")
    syms += sorted(str(k).upper() for k in (nw.keys() if isinstance(nw, dict) else []))
    out, seen = [], set()
    for s in syms:
        if s and s not in seen and s not in CONTROL:
            seen.add(s)
            out.append(s)
    return out[:CAP], refs


def ny_day_of(epoch_s):
    from zoneinfo import ZoneInfo
    return dt.datetime.fromtimestamp(int(epoch_s), tz=dt.timezone.utc).astimezone(
        ZoneInfo("America/New_York")).date().isoformat()


def main() -> int:
    import Super_stock as S
    import tv_data as TV
    from zoneinfo import ZoneInfo

    errors = []
    sess = S.last_closed_session()
    pop, refs = population()
    allsyms = CONTROL + pop
    print(f"⏰ آخرُ جلسةٍ مكتملة {sess} · المجتمع {len(pop)} (منها الثابتة {len(FIXED)}) · الضبط {len(CONTROL)}")
    d = dt.date.fromisoformat(str(sess))
    ny = ZoneInfo("America/New_York")
    cut_ms = int(dt.datetime(d.year, d.month, d.day, 16, 0, tzinfo=ny).timestamp() * 1000)

    # ── ① TradingView: دقائقُ يوم الجلسة على مِقبسٍ واحد ⟵ سعرُ الافتر (الدالّتان الإنتاجيّتان بالاسم) ──
    tvr = {}
    t0 = time.monotonic()
    ch = None
    try:
        ch = TV.Chart()
        for s in allsyms:
            try:
                bars = S.tv_session_minutes(s, sess, chart=ch)
                if bars is None:
                    tvr[s] = {"st": "fail"}
                    continue
                px = S.extended_last_price(s, sess, fetch_bars=lambda _s, _d: bars)
                reg = [b for b in bars if b["t"] < cut_ms]
                last_reg = max(reg, key=lambda b: b["t"])["c"] if reg else None
                tvr[s] = {"st": "got" if px else "no_ah", "ah": px, "reg": last_reg, "n": len(bars)}
            except Exception as e:                               # noqa: BLE001
                tvr[s] = {"st": "fail"}
                errors.append(f"TV {s}: {e!r}")
    except Exception as e:                                       # noqa: BLE001
        errors.append(f"مِقبس: {e!r}")
    finally:
        if ch is not None:
            ch.close()
    t_tv = time.monotonic() - t0

    # ── ② ياهو: سعرُ ما بعد الإغلاق مؤرَّخًا (قناةٌ مستقلّة) ──
    yr = {}
    try:
        import yfinance as yf
        for s in allsyms:
            try:
                inf = yf.Ticker(s).info or {}
                pm, pmt = inf.get("postMarketPrice"), inf.get("postMarketTime")
                rm, rmt = inf.get("regularMarketPrice"), inf.get("regularMarketTime")
                yr[s] = {"pm": float(pm) if pm else None, "pm_day": ny_day_of(pmt) if pmt else None,
                         "rm": float(rm) if rm else None, "rm_day": ny_day_of(rmt) if rmt else None}
            except Exception:                                    # noqa: BLE001
                yr[s] = {}
            time.sleep(0.15)
    except Exception as e:                                       # noqa: BLE001
        errors.append(f"ياهو: {e!r}")

    # ── ③ ماسحُ TradingView: postmarket_close (المصدرُ نفسُه بقناةٍ أخرى · وصف) ──
    scan_pm = {}
    try:
        snap = TV.scan(["name", "close", "postmarket_close"])
        if snap is None:
            raise RuntimeError("scan=None")
        for full, row in snap.items():                           # {«EXCH:SYM»: {عمود: قيمة}} — ناسداك يغلب عند التكرار
            nm = str(full).split(":")[-1].upper()
            if nm not in scan_pm or str(full).startswith("NASDAQ:"):
                scan_pm[nm] = (row or {}).get("postmarket_close")
        print(f"🛰️ الماسح: {len(scan_pm)} صفًّا بحقل postmarket_close")
    except Exception as e:                                       # noqa: BLE001
        print(f"🛰️ الماسح: تعذّر حقل postmarket_close ({type(e).__name__}) — وصفٌ فقط")

    # ── ④ المسارُ الحيّ نفسُه: ah_guard_rows بالبيئة tradingview على صفوف المجتمع ──
    rows = []
    for s in pop:
        price = (tvr.get(s) or {}).get("reg") or (yr.get(s) or {}).get("rm")
        rows.append({"symbol": s, "price": price, "ref": refs.get(s)})
    os.environ["BARS_SOURCE"] = "tradingview"
    t1 = time.monotonic()
    try:
        kept, unv = S.ah_guard_rows(rows, sess)
        rep = dict(S.AH_GUARD_LAST)
        live_ok = True
    except Exception as e:                                       # noqa: BLE001
        kept, unv, rep, live_ok = [], [], {}, False
        errors.append(f"ah_guard_rows: {e!r}")
    t_live = time.monotonic() - t1
    muted = sorted(set(r["symbol"] for r in rows) - set(r["symbol"] for r in kept))

    # ── الجدول ──
    print("\nالرمز | TV | افتر TV | إغلاق TV | ياهو افتر (يومه) | ياهو إغلاق | ماسح | فرق%")
    pairs, dec_pairs, regp = [], [], []
    for s in allsyms:
        t, y = tvr.get(s) or {}, yr.get(s) or {}
        diff = None
        if t.get("ah") and y.get("pm") and y.get("pm_day") == sess:
            diff = (t["ah"] / y["pm"] - 1.0) * 100.0
            pairs.append((s, diff))
            base = t.get("reg") or y.get("rm")
            if base:
                dec_pairs.append((s, (t["ah"] / base - 1) * 100 > CRIT["MUTE"], (y["pm"] / base - 1) * 100 > CRIT["MUTE"]))
        if t.get("reg") and y.get("rm") and y.get("rm_day") == sess:
            regp.append((s, (t["reg"] / y["rm"] - 1.0) * 100.0))
        print(f"{s} | {t.get('st', '—')} | {t.get('ah')} | {t.get('reg')} | {y.get('pm')} ({y.get('pm_day')}) | "
              f"{y.get('rm')} | {scan_pm.get(s)} | {'' if diff is None else f'{diff:+.2f}'}")

    # ── الحكم (آخرُ الأسطر) ──
    ctl_got = sum(1 for s in CONTROL if (tvr.get(s) or {}).get("st") == "got")
    pop_st = [(tvr.get(s) or {}).get("st", "fail") for s in pop]
    n_fail = pop_st.count("fail")
    fail_pct = 100.0 * n_fail / max(1, len(pop))
    ok2 = [p for p in pairs if abs(p[1]) <= CRIT["AH2_PCT"]]
    share2 = 100.0 * len(ok2) / len(pairs) if pairs else 0.0
    agree5 = [p for p in dec_pairs if p[1] == p[2]]
    share5 = 100.0 * len(agree5) / len(dec_pairs) if dec_pairs else 0.0
    reg_ok = [p for p in regp if abs(p[1]) <= 1.0]

    v1 = ctl_got >= CRIT["AH1"]
    v2 = None if len(pairs) < CRIT["AH2_MIN"] else share2 >= CRIT["AH2_SHARE"]
    v3 = fail_pct <= CRIT["AH3"]
    v4 = (live_ok and rep.get("src") == "tradingview" and rep.get("asked") == len(rows) and t_live <= CRIT["AH4_S"])
    v5 = None if len(dec_pairs) < CRIT["AH5_MIN"] else share5 >= CRIT["AH5_SHARE"]
    mark = {True: "✅", False: "❌", None: "⚪ لا حكم"}

    print("\n══════ النتيجة")
    print(f"• المجتمع: قُرئ {pop_st.count('got')} · بلا صفقةٍ بعد الإغلاق {pop_st.count('no_ah')} · تعذّر {n_fail} من {len(pop)}"
          f" · زمنُ TradingView {t_tv:.1f}ث لـ{len(allsyms)}")
    print(f"• المسارُ الحيّ: {rep} · مكتوم {muted} · غيرُ مُتحقَّق {len(unv)} · {t_live:.1f}ث")
    print(f"• (د) إغلاقُ الجلسة TradingView مقابل ياهو ضمن 1%: {len(reg_ok)} من {len(regp)}")
    print(f"• أخطاء: {errors[:8]}")
    print(f"AH1 الضبطُ السائل: {ctl_got} من {len(CONTROL)} ⟵ {mark[v1]}")
    print(f"AH2 الاتّفاق ضمن {CRIT['AH2_PCT']}%: {len(ok2)} من {len(pairs)} = {share2:.1f}% ⟵ {mark[v2]}")
    print(f"AH3 التعذّر: {n_fail} من {len(pop)} = {fail_pct:.1f}% ⟵ {mark[v3]}")
    print(f"AH4 المسارُ الحيّ: src={rep.get('src')} · asked={rep.get('asked')}/{len(rows)} · {t_live:.1f}ث ⟵ {mark[v4]}")
    print(f"AH5 تطابقُ قرار الكتم: {len(agree5)} من {len(dec_pairs)} = {share5:.1f}% ⟵ {mark[v5]}")
    passed = v1 and v3 and v4 and v2 is not False and v5 is not False
    print("⟵ الحكم: " + ("✅ يُدمج" if passed else "❌ لا دمجَ قبل التشخيص"))
    return 0 if passed else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:                                            # noqa: BLE001
        traceback.print_exc()
        sys.exit(2)
