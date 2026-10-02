#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🧪 مِجَسٌّ مؤقّت (يُحذف قبل الدمج) — حارسُ الافتر للمقسّم على TradingView (أمرُ المالك 2026-10-01 «شغّل حارس الافتر
للمقسّم على ترندق فيو»). **قراءةٌ فقط:** لا تلغرام · لا كتابةَ حالة ولا سجلّ · لا git · لا Polygon.

المجتمع: أسماءُ رادار التقسيم في تقرير 09-30 (‏YHC · WOK · NXTT · HAO · INLF · AIXI — أوّلُ ستّةٍ من 12 طُبعت في
السجلّ `36684201530`) ‏+ قائمةُ متابعة الصيّاد ‏+ نشطو القائمة ‏+ «تحت المتابعة» حتى 80 رمزًا (ترتيبٌ حتميّ) · وضبطٌ سائلٌ ثمانية.
القناةُ المستقلّة للتحقّق: سعرُ ما بعد الإغلاق عند ياهو (`postMarketPrice` بطابعه يومَ الجلسة).

══ v1 (‏تصميمُ القناة الواحدة: آخرُ دقيقةٍ ممتدّة في الشارت) — **منشورةٌ لا تُحذف** ══
التشغيلة `36808633641` (جلسة 2026-09-30): ‏AH1 ✅ 8/8 · **AH2 ❌ 43 من 53 = 81.1%** (الحدّ 90%) · AH3 ✅ 1/80 · AH4 ✅ 13.0ث ·
AH5 ✅ 53/53 ⟵ **«لا دمجَ قبل التشخيص»**. والتنبّؤات: (أ) ✅ 45/80 = 56% · (ب) ❌ تعذّر 1 لا صفر · (ج) ❌ 81.1% لا ‏≥95% ·
(د) ❌ 56 من 86 = 65% لا ‏≥90%.
🔬 **التشخيص (من جدول التشغيلة نفسِها · وصفٌ داخلَ العيّنة):** الشارتُ مع ياهو ضمن 2% ‏43 من 53 · الماسحُ (`postmarket_close`)
مع ياهو 71 من 80 · الشارتُ مع الماسح 41 من 52 ⇒ **لا قناةَ تتّفق مع أخرى في 90%** — أسعارُ افترِ الأسهم الرخيصة تتشتّت بين
المزوّدين · والشارتُ بلا شمعةِ افترٍ في 33 رمزًا عند ياهو لها افترُ اليوم نفسِه (حجمُ دقائقه جزئيّ — موثَّق) ⇒ **القناةُ الواحدة لا
تكفي** ⟵ v2.

══ v2 (‏تصميمُ القناتين — `ah_guard_rows` بعد التعديل) ══
لا يُتحقَّق صفٌّ إلّا إن اتّفقت آخرُ دقيقةٍ ممتدّة في الشارت و`postmarket_close` الماسح ضمن `TV_AH_AGREE_PCT` (‏2%)، والسعرُ أدناهما.

⚖️ **معيارُ القبول مكتوبٌ هنا قبل أوّل تشغيلٍ لـv2** (العتباتُ نفسُها بلا إرخاء · والمُضاف AH6 للتغطية):
  AH1 الآليّة: الضبطُ السائل مُتحقَّقٌ (قناتان متّفقتان) في 7 من 8 على الأقلّ.
  AH2 الدقّة: الصفوفُ المُتحقَّقة في المجتمع التي لها سعرُ ياهو مؤرَّخًا بيوم الجلسة ⟵ ‏|سعرُ الحارس ÷ ياهو − 1| ‏≤ 2% في 90%
      فأكثر (‏8 أزواجٍ على الأقلّ · وإلّا «لا حكم»).
  AH3 التعذّر: «تعذّر» الشارت ‏≤ 5% من رموز المجتمع.
  AH4 المسارُ الحيّ: `ah_guard_rows` بالبيئة tradingview على صفوف المجتمع ⟵ صفرُ استثناء · المصدر «tradingview» · سُئل = عددُ
      الصفوف · الماسحُ لم يتعذّر · والزمن ‏≤ 180 ثانية.
  AH5 القرار: على أزواج AH2 ⟵ قرارُ الكتم (‏+20% فوق إغلاق الجلسة) بسعر الحارس = قرارُه بسعر ياهو في 95% فأكثر (‏5 أزواجٍ على الأقلّ ·
      وإلّا «لا حكم»).
  AH6 التغطية: المُتحقَّق ‏≥ 30% من صفوف المجتمع (`engineering` — **مُطّلعٌ على داخل العيّنة**: 41 من 80 = 51% على 09-30).
  ⟵ **AH1 وAH3 وAH4 وAH6 ✅ وAH2 وAH5 غيرُ ساقطين ⇒ يُدمج** · وأيُّ ❌ ⇒ لا دمج.
🔒 **والمسارُ خلف مفتاح `AH_GUARD_TV`=«1» مطفأٍ في الإنتاج** ⇒ دمجُ الكود المطفأ لا يغيّر شيئًا · **وهذا المعيارُ يحكم إشعالَ
المفتاح** (ضبطُه في `split_hunter.yml` و`daily_screener.yml` · وتحديثُ قفل `AHT10` إقرارًا) — لا دمجَ الكود المطفأ.
⏰ **والحاكمةُ أوّلُ تشغيلةٍ على جلسةٍ بعد 2026-09-30 وبعد 20:05 نيويورك من يومها** (خارجَ العيّنة التي شُخِّص عليها التصميم ·
والافترُ مكتمل) · وأيُّ تشغيلةٍ على 09-30 أو قبل اكتمال الافتر **وصفٌ لا حكم** (خروج 4).
🔮 تنبّؤاتُ v2 قبل الرقم (تُنشر ولا تُحذف): (أ′) المُتحقَّق 35-60% من المجتمع · (ب′) AH2 ‏≥95% · (ج′) AH5 ‏100% · (د′) التعذّر 0-2.
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
IN_SAMPLE = "2026-09-30"                 # الجلسةُ التي شُخِّص عليها التصميم ⟵ وصفٌ لا حكم
CRIT = {"AH1": 7, "AH2_PCT": 2.0, "AH2_SHARE": 90.0, "AH2_MIN": 8, "AH3": 5.0, "AH4_S": 180.0,
        "AH5_SHARE": 95.0, "AH5_MIN": 5, "AH6": 30.0, "MUTE": 20.0}


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
    ny = ZoneInfo("America/New_York")
    now_ny = dt.datetime.now(dt.timezone.utc).astimezone(ny)
    d = dt.date.fromisoformat(str(sess))
    ah_done = now_ny >= dt.datetime(d.year, d.month, d.day, 20, 5, tzinfo=ny)
    governing = (str(sess) > IN_SAMPLE) and ah_done
    pop, refs = population()
    allsyms = CONTROL + pop
    agree_pct = float(S.TV_AH_AGREE_PCT)
    print(f"⏰ آخرُ جلسةٍ مكتملة {sess} · الآن {now_ny:%Y-%m-%d %H:%M} نيويورك · الافترُ مكتمل={ah_done} · "
          f"{'حاكمة' if governing else 'وصفٌ لا حكم'} · المجتمع {len(pop)} · الضبط {len(CONTROL)} · حدُّ الاتّفاق {agree_pct:g}%")
    cut_ms = int(dt.datetime(d.year, d.month, d.day, 16, 0, tzinfo=ny).timestamp() * 1000)

    # ── ① القناةُ الأولى: دقائقُ يوم الجلسة على مِقبسٍ واحد ⟵ آخرُ دقيقةٍ ممتدّة (الدالّتان الإنتاجيّتان بالاسم) ──
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

    # ── ② القناةُ الثانية: الماسح بالدالّة الإنتاجيّة نفسِها ──
    pm = S.tv_postmarket_map()
    print(f"🛰️ الماسح: {'تعذّر' if pm is None else f'{len(pm)} رمزًا بقيمة postmarket_close'}")

    # ── ③ ياهو: سعرُ ما بعد الإغلاق مؤرَّخًا (القناةُ المستقلّة) ──
    yr = {}
    try:
        import yfinance as yf
        for s in allsyms:
            try:
                inf = yf.Ticker(s).info or {}
                ypm, ypmt = inf.get("postMarketPrice"), inf.get("postMarketTime")
                rm, rmt = inf.get("regularMarketPrice"), inf.get("regularMarketTime")
                yr[s] = {"pm": float(ypm) if ypm else None, "pm_day": ny_day_of(ypmt) if ypmt else None,
                         "rm": float(rm) if rm else None, "rm_day": ny_day_of(rmt) if rmt else None}
            except Exception:                                    # noqa: BLE001
                yr[s] = {}
            time.sleep(0.15)
    except Exception as e:                                       # noqa: BLE001
        errors.append(f"ياهو: {e!r}")

    # ── سعرُ الحارس لكلّ رمز بقاعدة v2 (للمقارنة بياهو — والمسارُ الحيّ يُشغَّل مستقلًّا في ④) ──
    def guard_px(s):
        t = tvr.get(s) or {}
        if t.get("st") != "got" or not t.get("ah"):
            return None, t.get("st", "fail")
        sc = (pm or {}).get(s) or (pm or {}).get(s.replace("-", "."))
        if sc is None:
            return None, "no_scan"
        if abs(t["ah"] / sc - 1.0) * 100.0 > agree_pct:
            return None, "disagree"
        return min(t["ah"], sc), "ok"

    # ── ④ المسارُ الحيّ نفسُه: ah_guard_rows بالبيئة tradingview على صفوف المجتمع ──
    rows = []
    for s in pop:
        price = (tvr.get(s) or {}).get("reg") or (yr.get(s) or {}).get("rm")
        rows.append({"symbol": s, "price": price, "ref": refs.get(s)})
    os.environ["BARS_SOURCE"] = "tradingview"
    os.environ["AH_GUARD_TV"] = "1"                   # المفتاحُ يُشعَل للمِجَسّ وحدَه (مطفأٌ في الإنتاج)
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
    print("\nالرمز | الحالة | الشارت | الماسح | الحارس | إغلاق TV | ياهو افتر (يومه) | فرقُ الحارس عن ياهو%")
    pairs, dec_pairs, gst = [], [], {}
    for s in allsyms:
        t, y = tvr.get(s) or {}, yr.get(s) or {}
        g, st = guard_px(s)
        gst[s] = st
        diff = None
        if g and y.get("pm") and y.get("pm_day") == sess:
            diff = (g / y["pm"] - 1.0) * 100.0
            if s not in CONTROL:
                pairs.append((s, diff))
                base = t.get("reg") or y.get("rm")
                if base:
                    dec_pairs.append((s, (g / base - 1) * 100 > CRIT["MUTE"], (y["pm"] / base - 1) * 100 > CRIT["MUTE"]))
        print(f"{s} | {st} | {t.get('ah')} | {(pm or {}).get(s)} | {g} | {t.get('reg')} | {y.get('pm')} ({y.get('pm_day')}) | "
              f"{'' if diff is None else f'{diff:+.2f}'}")

    # ── الحكم (آخرُ الأسطر) ──
    ctl_ok = sum(1 for s in CONTROL if gst.get(s) == "ok")
    pop_st = [gst.get(s, "fail") for s in pop]
    n_fail = pop_st.count("fail")
    fail_pct = 100.0 * n_fail / max(1, len(pop))
    ver_pct = 100.0 * pop_st.count("ok") / max(1, len(pop))
    ok2 = [p for p in pairs if abs(p[1]) <= CRIT["AH2_PCT"]]
    share2 = 100.0 * len(ok2) / len(pairs) if pairs else 0.0
    agree5 = [p for p in dec_pairs if p[1] == p[2]]
    share5 = 100.0 * len(agree5) / len(dec_pairs) if dec_pairs else 0.0

    v1 = ctl_ok >= CRIT["AH1"]
    v2 = None if len(pairs) < CRIT["AH2_MIN"] else share2 >= CRIT["AH2_SHARE"]
    v3 = fail_pct <= CRIT["AH3"]
    v4 = (live_ok and rep.get("src") == "tradingview" and rep.get("asked") == len(rows) and pm is not None
          and t_live <= CRIT["AH4_S"])
    v5 = None if len(dec_pairs) < CRIT["AH5_MIN"] else share5 >= CRIT["AH5_SHARE"]
    v6 = ver_pct >= CRIT["AH6"]
    mark = {True: "✅", False: "❌", None: "⚪ لا حكم"}

    print("\n══════ النتيجة")
    print(f"• المجتمع: مُتحقَّق {pop_st.count('ok')} · بلا افتر {pop_st.count('no_ah')} · بلا ماسح {pop_st.count('no_scan')} · "
          f"اختلاف {pop_st.count('disagree')} · تعذّر {n_fail} من {len(pop)} · زمنُ الشارت {t_tv:.1f}ث لـ{len(allsyms)}")
    print(f"• المسارُ الحيّ: {rep} · مكتوم {muted} · غيرُ مُتحقَّق {len(unv)} · {t_live:.1f}ث"
          f" · اتّساقُه مع الجدول: قُرئ {rep.get('got')} مقابل {pop_st.count('ok')}")
    print(f"• أخطاء: {errors[:8]}")
    print(f"AH1 الضبطُ السائل مُتحقَّق: {ctl_ok} من {len(CONTROL)} ⟵ {mark[v1]}")
    print(f"AH2 الدقّة ضمن {CRIT['AH2_PCT']}%: {len(ok2)} من {len(pairs)} = {share2:.1f}% ⟵ {mark[v2]}")
    print(f"AH3 التعذّر: {n_fail} من {len(pop)} = {fail_pct:.1f}% ⟵ {mark[v3]}")
    print(f"AH4 المسارُ الحيّ: src={rep.get('src')} · asked={rep.get('asked')}/{len(rows)} · الماسح "
          f"{'تعذّر' if pm is None else 'سليم'} · {t_live:.1f}ث ⟵ {mark[v4]}")
    print(f"AH5 تطابقُ قرار الكتم: {len(agree5)} من {len(dec_pairs)} = {share5:.1f}% ⟵ {mark[v5]}")
    print(f"AH6 التغطية: {pop_st.count('ok')} من {len(pop)} = {ver_pct:.1f}% ⟵ {mark[v6]}")
    passed = v1 and v3 and v4 and v6 and v2 is not False and v5 is not False
    if not governing:
        print(f"⟵ ⚪ وصفٌ لا حكم (الجلسة {sess} · الافترُ مكتمل={ah_done}) — الحاكمةُ أوّلُ جلسةٍ بعد {IN_SAMPLE} بعد 20:05 نيويورك"
              + (" · والمعيارُ كان سيعبر" if passed else " · والمعيارُ كان سيسقط"))
        return 4
    print("⟵ الحكم: " + ("✅ يُدمج" if passed else "❌ لا دمج"))
    return 0 if passed else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:                                            # noqa: BLE001
        traceback.print_exc()
        sys.exit(2)
