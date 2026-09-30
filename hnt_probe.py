# -*- coding: utf-8 -*-
"""🧪 مِجَسٌّ مؤقّت (يُحذف قبل الدمج) — التحقّقُ الطرفيّ من نقل الصيّادين الأربعة إلى TradingView ‏+ قياسُ اتّساق مقياس سجلّ الحصاد.

أمرُ المالك 2026-09-30 «انقل الصيّادين إلى ترندق فيو». **قراءةٌ فقط:** لا تلغرام · لا كتابةَ حالة (لا git) · لا Polygon.
**معاييرُ القبول مكتوبةٌ هنا قبل أوّل تشغيل** (لا تُعدَّل بعد رؤية رقم) — والدمجُ مشروطٌ بـHP1-HP4 معًا:
- HP1 التغطية: إطاراتُ وضع TradingView (TradingView ∪ احتياطُ ياهو) لا تقلّ عن 99.5% من إطارات وضع ياهو.
- HP2 الحصّة: ‏97% فأكثر من إطارات وضع TradingView جاءت من TradingView نفسِه (لا من الاحتياط).
- HP3 الزمن: جلبُ TradingView للكون (`tv_download`) في 5 دقائق أو أقلّ.
- HP4 السلامة: صفرُ استثناءٍ من مسوح الصيّادين الأربعة على إطارات TradingView (`scan_split_hunter` · `scan_split_filter` ·
  `scan_method_hunter` · و`envelope_scan.decide` لكلّ رمز).
وصفيّةٌ تُطبَع ولا تحكم: المسوحُ على **آخر جلسةٍ مكتملة** في الوضعين (الإطاران مقصوصان عندها — المِجَسُّ يعمل والجلسةُ مفتوحة) ·
مطابقو كلّ صيّادٍ في الوضعين والانقلابُ بسببه لكلّ رمز (فرقُ بيانات = تواريخُ مختلفة أو OHLC فوق 0.5% أو حجمٌ فوق 5% في شمعةٍ
مشتركة · وإلّا «بلا فرق بيانات») · ومرجعُ المطابقين (آخرُ إغلاق) بين المصدرين.
⚖️ **قياسُ مقياس السجلّ (LS)** — يُثبت عطلًا أو ينفيه **ولا يُحسب فيه `hit100` ولا `max_gain`**: لكلّ صفٍّ معلّقٍ بمرجع في
`hunter_ledger.jsonl` — `r` = إغلاقُ يوم جلسته في إطار ياهو الطازج ÷ `ref_close` المجمَّد · و`f` = عاملُ تقسيمات ياهو بعد الجلسة
(`_split_scale_factor`). **العطلُ مُثبَت** إن وُجد صفٌّ واحدٌ فأكثر بـ`r` خارج [0.8، 1.25] ويفسّره تقسيمٌ مؤكَّد (`r × f` داخل
[0.9، 1.1]) — لأن الحاسمَ الحاليّ يقارن قممَ المقياس الجديد بمرجع المقياس القديم. ويُطبَع عددُ المُعرَّضين فيما يحسمه السبتُ
الأوّل (جلساتٌ حتى 2026-08-06) · ونسبةُ إغلاق TradingView إلى المرجع وصفًا.
"""
import math
import os
import statistics as st
import sys
import time

os.environ["SPLIT_SOURCE_REPAIR"] = "0"          # Polygon انتهى — المِجَسُّ لا يناديه
import Super_stock as S                          # noqa: E402
import envelope_scan as ES                       # noqa: E402
import hunter_ledger as LEDGER                   # noqa: E402

TOL_OHLC, TOL_VOL = 0.005, 0.05


def log(*a):
    print(*a, flush=True)


def cut(frames, day):
    out = {}
    for s, d in frames.items():
        try:
            c = d[[str(i)[:10] <= day for i in d.index]]
            if len(c):
                c.attrs.update(getattr(d, "attrs", {}) or {})
                out[s] = c
        except Exception:                                        # noqa: BLE001
            continue
    return out


def data_diff(a, b):
    try:
        ra = {str(i)[:10]: v for i, v in zip(a.index, a[["Open", "High", "Low", "Close", "Volume"]].values)}
        rb = {str(i)[:10]: v for i, v in zip(b.index, b[["Open", "High", "Low", "Close", "Volume"]].values)}
        oa, ob = sorted(set(ra) - set(rb)), sorted(set(rb) - set(ra))
        if oa or ob:
            return f"تواريخ: عند TradingView وحدَه {len(oa)} {oa[-3:]} · عند ياهو وحدَه {len(ob)} {ob[-3:]}"
        wp, wv, wd = 0.0, 0.0, None
        for k in ra:
            x, y = ra[k], rb[k]
            for j in range(4):
                if y[j] and abs(x[j] / y[j] - 1) > wp:
                    wp, wd = abs(x[j] / y[j] - 1), k
            if y[4] and abs(x[4] / y[4] - 1) > wv:
                wv = abs(x[4] / y[4] - 1)
        if wp > TOL_OHLC or wv > TOL_VOL:
            return f"OHLC حتى {wp * 100:.2f}% ({wd}) · حجمٌ حتى {wv * 100:.1f}%"
        return None
    except Exception as e:                                       # noqa: BLE001
        return f"تعذّر ({type(e).__name__})"


def scans(hist, sess, edges):
    out, exc = {}, []
    for name, fn in (("split", lambda: S.scan_split_hunter(hist)),
                     ("split_filter", lambda: S.scan_split_filter(hist, today=sess)),
                     ("method", lambda: S.scan_method_hunter(hist, today=sess, fetch_h4=S.fetch_4h))):
        t0 = time.time()
        try:
            out[name] = sorted(str(r.get("symbol")) for r in (fn() or []))
        except Exception as e:                                   # noqa: BLE001
            exc.append((name, type(e).__name__, str(e)[:120]))
            out[name] = None
        log(f"   {name}: {out[name] if out[name] is None else len(out[name])} في {time.time() - t0:.0f}ث")
    t0, hits, ex_env = time.time(), [], 0
    for sym, df in hist.items():
        if df is None or len(df) < 60:
            continue
        try:
            good, _why, vals = ES.decide(S, sym, df, edges)
        except Exception as e:                                   # noqa: BLE001
            ex_env += 1
            if ex_env <= 5:
                exc.append(("envelope", sym, type(e).__name__))
            continue
        if good and vals is not None:
            hits.append(sym)
    if ex_env > 5:
        exc.append(("envelope", f"و{ex_env - 5} غيرُها", ""))
    out["envelope"] = sorted(hits)
    log(f"   envelope: {len(hits)} في {time.time() - t0:.0f}ث")
    return out, exc


def main():
    uni = S.get_universe()
    log(f"الكون {len(uni)}")
    if len(uni) < 1000:
        log("⛔ لا قياس — الكون أقلّ من 1000")
        return 2
    os.environ["BARS_SOURCE"] = "tradingview"
    t0 = time.time()
    tvh = S.download_history(uni)
    t_tv = time.time() - t0
    rep = dict(S.BARS_SOURCE_LAST)
    os.environ.pop("BARS_SOURCE", None)
    t0 = time.time()
    yh = S.download_history(uni)
    t_yh = time.time() - t0
    n_tv_src = sum(1 for d in tvh.values() if LEDGER.frame_src(d) == "tradingview")
    log(f"\nوضع TradingView: {len(tvh)} إطارًا في {t_tv:.0f}ث (من TradingView {n_tv_src} · جلبُه {rep.get('secs')}ث · "
        f"احتياطُ ياهو {rep.get('yahoo_got')} من {rep.get('yahoo_asked')}) · قاطع {rep.get('gate')}")
    log(f"وضع ياهو: {len(yh)} إطارًا في {t_yh:.0f}ث")
    day = S.last_closed_session()
    log(f"آخرُ جلسةٍ مكتملة: {day} (الإطاران مقصوصان عندها للمسوح)")
    tvc, yhc = cut(tvh, day), cut(yh, day)
    s_tv = max(d.index[-1] for d in tvc.values()).date()
    s_yh = max(d.index[-1] for d in yhc.values()).date()
    log(f"جلسةُ البيانات: TradingView {s_tv} · ياهو {s_yh} {'✅' if s_tv == s_yh else '⚠️ تختلف'}")
    edges = ES.load_edges()
    log("\n— المسوحُ على إطارات ياهو —")
    m_yh, exc_yh = scans(yhc, s_yh, edges)
    log("— المسوحُ على إطارات TradingView —")
    m_tv, exc_tv = scans(tvc, s_tv, edges)
    log(f"\nاستثناءاتُ ياهو (مرجع): {exc_yh}")
    for name in ("split", "split_filter", "method", "envelope"):
        a, b = set(m_yh.get(name) or []), set(m_tv.get(name) or [])
        fl = sorted(a ^ b)
        log(f"\n🪝 {name}: ياهو {len(a)} · TradingView {len(b)} · مشترك {len(a & b)} · انقلاب {len(fl)}")
        nod = 0
        for s in fl:
            why = data_diff(tvc[s], yhc[s]) if (s in tvc and s in yhc) else "إطارٌ غائب في أحد الوضعين"
            nod += why is None
            if fl.index(s) < 40:
                log(f"   {s}: {'ياهو ✅ · TradingView —' if s in a else 'ياهو — · TradingView ✅'} · "
                    f"{why or 'بلا فرق بيانات'} · src={LEDGER.frame_src(tvc.get(s))}")
        log(f"   ⇒ انقلابٌ بلا فرق بيانات: {nod}")
        diffs = []
        for s in sorted(a & b):
            try:
                diffs.append(abs(float(tvc[s]['Close'].iloc[-1]) / float(yhc[s]['Close'].iloc[-1]) - 1))
            except Exception:                                    # noqa: BLE001
                pass
        if diffs:
            log(f"   مرجعُ المطابقين (آخرُ إغلاق) TradingView مقابل ياهو: الوسيط {st.median(diffs) * 100:.3f}% · "
                f"الأقصى {max(diffs) * 100:.3f}% · فوق 0.5% {sum(1 for d in diffs if d > 0.005)} من {len(diffs)}")

    # ⚖️ LS — مقياسُ سجلّ الحصاد
    log("\n═══ ⚖️ LS مقياسُ سجلّ الحصاد (لا hit100 ولا max_gain) ═══")
    rows = [r for r in LEDGER.load() if not r.get("outcome") and r.get("ref_close")]
    syms = sorted({r["symbol"] for r in rows})
    yall = dict(yh)
    miss = [s for s in syms if s not in yall]
    if miss:
        yall.update(S.download_history(miss) or {})
    tall = {s: d for s, d in tvh.items() if LEDGER.frame_src(d) == "tradingview"}
    miss_t = [s for s in syms if s not in tall]
    if miss_t:
        try:
            got, _r = S.tv_download(miss_t, (S.dt.date.today() - S.dt.timedelta(days=S.CONFIG["HISTORY_DAYS"])).isoformat())
            tall.update(got or {})
        except Exception as e:                                   # noqa: BLE001
            log(f"⚠️ TradingView للغائبين تعذّر ({type(e).__name__})")

    def close_at(df, d0):
        px = [float(c) for i, c in zip(df.index, df["Close"].values) if str(i)[:10] <= d0]
        return px[-1] if px else None

    n = len(rows)
    nof, match, mild, mis, first, first_mis = 0, 0, 0, [], 0, 0
    tv_r = []
    for r in rows:
        d0 = str(r["session"])[:10]
        if d0 <= "2026-08-06":
            first += 1
        df = yall.get(r["symbol"])
        c = close_at(df, d0) if df is not None else None
        if c is None:
            nof += 1
            continue
        rr = c / float(r["ref_close"])
        dt_ = tall.get(r["symbol"])
        ct = close_at(dt_, d0) if dt_ is not None else None
        if ct:
            tv_r.append(ct / float(r["ref_close"]))
        if abs(rr - 1) <= 0.02:
            match += 1
        elif 0.8 <= rr <= 1.25:
            mild += 1
        else:
            mis.append((r, rr))
            if d0 <= "2026-08-06":
                first_mis += 1
    log(f"صفوفٌ معلّقة بمرجع: {n} ({len(syms)} رمزًا) · بلا إطار ياهو {nof}")
    log(f"r = إغلاقُ يوم الجلسة الطازج ÷ المرجع: تطابقٌ (±2%) {match} · بين 2% وخارج [0.8، 1.25] {mild} · "
        f"**خارج [0.8، 1.25] {len(mis)}**")
    log(f"السبتُ الأوّل (جلساتٌ حتى 2026-08-06): {first} صفًّا · منها خارج [0.8، 1.25] {first_mis}")
    expl, rows_out = 0, []
    for r, rr in sorted(mis, key=lambda x: -abs(math.log(x[1])))[:400]:
        f = S._split_scale_factor(S._fetch_splits(r["symbol"]), str(r["session"])[:10])
        ok = 0.9 <= rr * f <= 1.1 and f != 1.0
        expl += ok
        rows_out.append((r["hunter"], r["session"], r["symbol"], float(r["ref_close"]), rr, f, ok))
    log(f"منها يفسّرها تقسيمٌ مؤكَّد (r×f في [0.9، 1.1]): {expl} من {min(len(mis), 400)}")
    for h, se, sy, ref, rr, f, ok in rows_out[:40]:
        log(f"   {h} {se} {sy}: ref {ref:.4g} · r {rr:.3f} · f {f:.4g} · r×f {rr * f:.3f} {'✅ تقسيم' if ok else '❔'}")
    if tv_r:
        tr = sorted(abs(x - 1) for x in tv_r)
        log(f"وصفيّ: إغلاقُ TradingView يوم الجلسة ÷ المرجع — الوسيط {st.median(tr) * 100:.2f}% · فوق 2% "
            f"{sum(1 for x in tr if x > 0.02)} من {len(tr)} · خارج [0.8، 1.25] "
            f"{sum(1 for x in tv_r if not 0.8 <= x <= 1.25)}")
    log(f"⚖️ LS: العطلُ {'✅ مُثبَت' if expl else '❌ غيرُ مُثبَت'} ({expl} صفًّا يفسّره تقسيمٌ مؤكَّد)")

    hp1 = len(tvh) >= 0.995 * len(yh)
    hp2 = (n_tv_src / len(tvh)) >= 0.97 if tvh else False
    hp3 = float(rep.get("secs") or 1e9) <= 300
    hp4 = not exc_tv
    log(f"\nHP1 التغطية: {len(tvh)} مقابل {len(yh)} (‏{len(tvh) / max(1, len(yh)) * 100:.2f}% · الحدّ 99.5%) {'✅' if hp1 else '❌'}")
    log(f"HP2 الحصّة من TradingView: {n_tv_src} من {len(tvh)} (‏{n_tv_src / max(1, len(tvh)) * 100:.2f}% · الحدّ 97%) "
        f"{'✅' if hp2 else '❌'}")
    log(f"HP3 الزمن: {rep.get('secs')}ث (الحدّ 300) {'✅' if hp3 else '❌'}")
    log(f"HP4 استثناءاتُ المسوح على TradingView: {exc_tv} {'✅' if hp4 else '❌'}")
    ok = hp1 and hp2 and hp3 and hp4
    log(f"\n⚖️ {'✅ يُدمج (HP1-HP4)' if ok else '❌ لا يُدمج'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
