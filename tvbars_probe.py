# -*- coding: utf-8 -*-
"""🧪 مِجَسٌّ مؤقّت (يُحذف قبل الدمج) — التحقّقُ الطرفيّ من `BARS_SOURCE=tradingview` في `download_history` على كون الفرز كلِّه.

أمرُ المالك 2026-09-30 «حوّل شموع البوت إلى ترندق فيو». **قراءةٌ فقط:** لا تلغرام · لا كتابةَ حالة · لا Polygon.
**معاييرُ القبول مكتوبةٌ هنا قبل أوّل تشغيل** (لا تُعدَّل بعد رؤية رقم) — والدمجُ مشروطٌ بـA1-A4 معًا:
- A1 التغطية: عددُ الإطارات بوضع TradingView (TradingView ∪ احتياطُ ياهو) لا يقلّ عن 99.5% من عددها بوضع ياهو.
- A2 الحصّة: ‏97% فأكثر من إطارات وضع TradingView جاءت من TradingView نفسِه (لا من الاحتياط).
- A3 الزمن: جلبُ TradingView للكون (`tv_download`) في 5 دقائق أو أقلّ.
- A4 السلامة: صفرُ استثناءٍ من `analyze_ticker` على إطارات TradingView.
وصفيّةٌ تُطبَع ولا تحكم: انقلابُ القبول بين المصدرين (C5 المنشور 58 من 3,350) · وسيطُ فرق آخر إغلاقٍ مشترك · وحارسُ `tv_bar_fresh`.
"""
import os
import statistics as st
import sys
import time

os.environ["SPLIT_SOURCE_REPAIR"] = "0"          # Polygon انتهى — المِجَسُّ لا يناديه
import Super_stock as S                          # noqa: E402


def log(*a):
    print(*a, flush=True)


def main():
    uni = S.get_universe()
    log(f"الكون {len(uni)}")
    if len(uni) < 1000:
        log("⛔ لا قياس — الكون أقلّ من 1000")
        return 2
    os.environ["BARS_SOURCE"] = "tradingview"
    t0 = time.time()
    tvh = S.download_history(uni)
    t_tv_all = time.time() - t0
    rep = dict(S.BARS_SOURCE_LAST)
    os.environ.pop("BARS_SOURCE", None)
    t0 = time.time()
    yh = S.download_history(uni)
    t_yh = time.time() - t0
    n_tv_src = sum(1 for d in tvh.values() if (d.attrs or {}).get("bars_src") == "tradingview")
    log(f"\nوضع TradingView: {len(tvh)} إطارًا في {t_tv_all:.0f}ث (منها من TradingView {n_tv_src} · جلبُه {rep.get('secs')}ث · "
        f"احتياطُ ياهو {rep.get('yahoo_got')} من {rep.get('yahoo_asked')}) · قاطع {rep.get('gate')}")
    log(f"وضع ياهو: {len(yh)} إطارًا في {t_yh:.0f}ث")
    log(f"   تعذّر {len(rep.get('none') or [])}: {(rep.get('none') or [])[:30]}")
    log(f"   بلا شموع {len(rep.get('empty') or [])}: {(rep.get('empty') or [])[:30]}")
    log(f"   دون MIN_BARS {len(rep.get('short') or [])}: {(rep.get('short') or [])[:30]}")
    exc, acc_tv, acc_yh, flips, diffs, stale = [], 0, 0, [], [], 0
    exp = S.last_closed_session()
    for s in sorted(set(tvh) & set(yh)):
        dt_, dy = tvh[s], yh[s]
        if (dt_.attrs or {}).get("bars_src") == "tradingview":
            if not S.tv_bar_fresh(dt_):
                stale += 1
            try:
                ct = {str(i)[:10]: float(c) for i, c in zip(dt_.index, dt_["Close"])}
                cy = {str(i)[:10]: float(c) for i, c in zip(dy.index, dy["Close"])}
                com = sorted(set(ct) & set(cy))
                if com and ct[com[-1]] > 0:
                    diffs.append(abs(cy[com[-1]] / ct[com[-1]] - 1))
            except Exception:                                    # noqa: BLE001
                pass
        try:
            vt = S.analyze_ticker(s, dt_)
        except Exception as e:                                   # noqa: BLE001
            exc.append((s, type(e).__name__))
            vt = None
        try:
            vy = S.analyze_ticker(s, dy)
        except Exception:                                        # noqa: BLE001
            vy = None
        acc_tv += vt is not None
        acc_yh += vy is not None
        if (vt is not None) != (vy is not None):
            flips.append((s, "✅" if vy is not None else "—", "✅" if vt is not None else "—"))
    a1 = len(tvh) >= 0.995 * len(yh)
    a2 = (n_tv_src / len(tvh)) >= 0.97 if tvh else False
    a3 = float(rep.get("secs") or 1e9) <= 300
    a4 = not exc
    log(f"\nA1 التغطية: {len(tvh)} مقابل {len(yh)} (‏{len(tvh) / max(1, len(yh)) * 100:.2f}% · الحدّ 99.5%) {'✅' if a1 else '❌'}")
    log(f"A2 الحصّة من TradingView: {n_tv_src} من {len(tvh)} (‏{n_tv_src / max(1, len(tvh)) * 100:.2f}% · الحدّ 97%) {'✅' if a2 else '❌'}")
    log(f"A3 الزمن: {rep.get('secs')}ث (الحدّ 300) {'✅' if a3 else '❌'}")
    log(f"A4 استثناءاتُ analyze_ticker على إطارات TradingView: {len(exc)} {exc[:10]} {'✅' if a4 else '❌'}")
    log(f"\nوصفيّ: القبولُ TradingView {acc_tv} · ياهو {acc_yh} · انقلابٌ {len(flips)}: {flips[:40]}")
    if diffs:
        ds = sorted(diffs)
        log(f"وصفيّ: فرقُ آخر إغلاقٍ مشترك — الوسيط {st.median(ds) * 100:.3f}% · 90٪ {ds[int(0.9 * len(ds)) - 1] * 100:.3f}% · "
            f"فوق 0.5% {sum(1 for d in ds if d > 0.005)} من {len(ds)}")
    log(f"وصفيّ: آخرُ جلسةٍ مكتملة {exp} · إطاراتُ TradingView أقدمُ منها (بلا صفقة · `tv_bar_fresh`=False) {stale}")
    ok = a1 and a2 and a3 and a4
    log(f"\n⚖️ {'✅ يُدمج (A1-A4)' if ok else '❌ لا يُدمج'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
