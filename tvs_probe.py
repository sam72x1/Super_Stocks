#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🧪 مِجَسٌّ مؤقّت `tvs_probe` (يُحذف قبل الدمج · بلا تلغرام ولا كتابة حالة ولا git):
التقسيماتُ **غيرُ المسوّاة** في شموع TradingView اليوميّة — مسارُ الإنتاج نفسُه (`S.tv_download`) الذي صار مصدرَ
البوت (#491) والصيّادين الأربعة (#502).

الدافع (مُثبَت 2026-09-30 · `hnt_diag` ‏36749313735): WOK عكسيّ 1:100 يومَ 2025-10-21 لم يسوِّه TradingView
(إغلاقُ 10-20 عنده 359 وعند ياهو 36,000 ثمّ 37,200 عند الاثنين) — ولم يمسّ قرارَ ذلك اليوم · **وانتشارُه غيرُ مقيس.**

═══ المعيارُ مكتوبٌ قبل أوّل تشغيل (لا يُرخى بعد الرقم) ═══
TS0 (صحّةُ القياس): إطاراتُ TradingView لـ97% فأكثر ممّا أعطاه ياهو إطارًا · وتقسيماتُ ياهو قُرئت لـ95% فأكثر من رموز
     إطارات TradingView (عمودُ «Stock Splits» من `yf.download(actions=True)` بدفعاتٍ · «قُرئ» = إغلاقٌ واحدٌ غيرُ فارغ
     على الأقلّ) — وإلّا «لا قياس» (خروج 3).
TS1 (العطل): زوجُ (رمز، تقسيم) «غيرُ مسوّى» إن كان التقسيمُ عند ياهو داخل نافذة الإطار وأوّلُ شمعةٍ عند TradingView
     في يومه أو بعده تقفز عن سابقتها بمقدار 1/النسبة: |log((c_j/c_{j-1})·v)| ≤ log(1.25) — تعريفُ `unadjusted_jump`
     في `hunter_outcomes.py` بالاسم (لا نسخة) · و«مسوّى» إن لم تقفز · والنسبةُ = غيرُ المسوّى ÷ كلّ الأزواج.
TS2 (الأثر): لكلّ رمزٍ فيه زوجٌ غيرُ مسوّى: `S.analyze_ticker` على إطار TradingView ثمّ على إطار ياهو للرمز نفسِه
     (قبولٌ = نتيجةٌ غيرُ None) · وعضويّتُه في القائمة النشطة (`weekly_watchlist.json` · stocks نشطة) — وصف.
الحكم:
  ① «عطلٌ مُثبَت يلزمه إصلاح» إن وُجد رمزٌ غيرُ مسوّى واحدٌ فأكثر **ينقلب قرارُه** (TS2) **أو هو نشطٌ في القائمة**.
  ② وإلّا «حدٌّ معلَنٌ بنسبته» (يُكتب في الذاكرة بالرقم) — والإصلاحُ الوقائيّ خيارٌ يُعرض لا يُنفَّذ تلقائيًّا.
"""
import math
import sys
import time

TOL = 0.25


def splits_from_yahoo(S, syms, start, chunk=250):
    """{رمز: [(يوم ISO، نسبة)]} من عمود «Stock Splits» · ومعه عددُ الرموز التي قُرئت (حاضرةٌ في النتيجة)."""
    out, seen = {}, set()
    yf = S.yf
    for i in range(0, len(syms), chunk):
        part = syms[i:i + chunk]
        data = None
        for a in range(3):
            try:
                data = yf.download(part, start=start, interval="1d", auto_adjust=True, actions=True,
                                   group_by="ticker", threads=True, progress=False)
                if data is not None and len(data):
                    break
            except Exception as e:                               # noqa: BLE001
                print(f"   ⚠️ دفعة {i // chunk + 1}: {e}")
            time.sleep(3 * (2 ** a))
        if data is None or not len(data):
            continue
        lv0 = set(data.columns.get_level_values(0)) if hasattr(data.columns, "levels") else set()
        for s in part:
            try:
                df = data[s] if len(part) > 1 or s in lv0 else data
                if "Stock Splits" not in df.columns or df["Close"].dropna().empty:
                    continue
                seen.add(s)
                ss = df["Stock Splits"].dropna()
                ss = ss[ss > 0]
                out[s] = [(str(ix)[:10], float(v)) for ix, v in ss.items() if float(v) != 1.0]
            except Exception:                                    # noqa: BLE001
                continue
        print(f"   تقسيماتُ ياهو: دفعة {i // chunk + 1} · قُرئ {len(seen)} حتى الآن", flush=True)
    return out, seen


def classify(df, events, tol=TOL):
    """[(يوم، نسبة، «unadjusted»|«adjusted»|«no_bar»، القفزة)] لكلّ تقسيمٍ داخل نافذة الإطار."""
    res = []
    try:
        idx = [str(x)[:10] for x in df.index]
        cl = [float(c) for c in df["Close"].values]
    except Exception:                                            # noqa: BLE001
        return res
    if not idx:
        return res
    for d, v in events:
        if d <= idx[0] or d > idx[-1]:
            continue                                             # خارج النافذة (أو يومُها الأوّل)
        j = next((k for k, x in enumerate(idx) if x >= d), None)
        if j is None or j == 0 or cl[j - 1] <= 0 or cl[j] <= 0:
            res.append((d, v, "no_bar", None))
            continue
        jump = cl[j] / cl[j - 1]
        un = abs(math.log(jump * float(v))) <= math.log(1.0 + tol)
        res.append((d, v, "unadjusted" if un else "adjusted", round(jump, 4)))
    return res


def main() -> int:
    import datetime as dt
    import json
    import os
    os.environ.pop("BARS_SOURCE", None)                       # tv_download يُنادى مباشرةً · وياهو بلا البيئة
    import Super_stock as S
    import hunter_outcomes as HO
    today = dt.date.today()
    start = (today - dt.timedelta(days=int(S.CONFIG.get("HISTORY_DAYS", 800)))).isoformat()
    uni = S.get_universe() or []
    print(f"الكون {len(uni)} · النافذة من {start}")
    tv, rep = S.tv_download(uni, start=start)
    print(S._tv_bars_line(rep))
    yh = S.download_history(uni)                                 # ياهو كما في الإنتاج بلا البيئة
    print(f"ياهو: {len(yh)} إطارًا")
    sp, seen = splits_from_yahoo(S, sorted(uni), start)
    ts0a = len(tv) / max(1, len(yh)) * 100
    ts0b = len(seen & set(tv)) / max(1, len(tv)) * 100
    print(f"TS0: إطاراتُ TradingView {len(tv)} مقابل ياهو {len(yh)} ({ts0a:.2f}%) · تقسيماتُ ياهو قُرئت لـ{len(seen & set(tv))} من {len(tv)} رمزًا بإطار TradingView ({ts0b:.2f}%)")
    pairs, bad, nobar, disagree = 0, [], 0, []
    for s, df in tv.items():
        ev = sp.get(s) or []
        for d, v, st, jump in classify(df, ev):
            if st == "no_bar":
                nobar += 1
                continue
            pairs += 1
            # 🔒 الحكمُ بدالّة الإنتاج نفسِها (بالاسم) على الحدث وحدَه — تطابقُ المعيار حرفًا
            try:
                un_prod = HO.unadjusted_jump(df, [(d, v)])
            except Exception:                                    # noqa: BLE001
                un_prod = None
            if (st == "unadjusted") != bool(un_prod):
                disagree.append((s, d, st, un_prod))
            if un_prod:                                          # الحكمُ بدالّة الإنتاج وحدَها (المعيار TS1)
                bad.append((s, d, v, jump, st, un_prod))
    print(f"TS1: أزواجُ (رمز، تقسيم) داخل النوافذ {pairs} · غيرُ مسوّاة {len(bad)} ({len(bad) / max(1, pairs) * 100:.2f}%) · بلا شمعة {nobar}"
          f" · رموزٌ متأثّرة {len({b[0] for b in bad})} من {len(tv)}")
    # وصفٌ لا يحكم: المقياسُ نفسُه على إطارات ياهو (هل الخللُ في المصدر أم في التقسيم؟)
    ypairs, ybad = 0, []
    for s, df in yh.items():
        for d, v, st, jump in classify(df, sp.get(s) or []):
            if st == "no_bar":
                continue
            ypairs += 1
            if st == "unadjusted":
                ybad.append((s, d, v, jump))
    print(f"   وصف · ياهو بالمقياس نفسِه: أزواج {ypairs} · غيرُ مسوّاة {len(ybad)} {[b[0] for b in ybad[:20]]}")
    print(f"   فحصٌ ذاتيّ: خلافُ المصنِّف المحلّيّ مع unadjusted_jump = {len(disagree)} {disagree[:10]}")
    for s, d, v, jump, st, up in bad[:60]:
        print(f"   {s} {d} نسبة {v:g} · قفزة ×{jump} · {st} · unadjusted_jump={up}")
    try:
        wl = json.load(open("weekly_watchlist.json", encoding="utf-8"))
        active = {str(x.get("symbol")) for x in (wl.get("stocks") or []) if x.get("status") == "active"}
    except Exception:                                            # noqa: BLE001
        active = set()
    flips, act = [], []
    for s in sorted({b[0] for b in bad}):
        a_tv = a_yh = None
        try:
            a_tv = S.analyze_ticker(s, tv[s]) is not None
        except Exception as e:                                   # noqa: BLE001
            a_tv = f"⛔ {type(e).__name__}"
        try:
            a_yh = (S.analyze_ticker(s, yh[s]) is not None) if s in yh else "—"
        except Exception as e:                                   # noqa: BLE001
            a_yh = f"⛔ {type(e).__name__}"
        tag = "نشط" if s in active else ""
        print(f"   TS2 {s}: TradingView {a_tv} · ياهو {a_yh} {tag}")
        if isinstance(a_tv, bool) and isinstance(a_yh, bool) and a_tv != a_yh:
            flips.append(s)
        if s in active:
            act.append(s)
    print(f"TS2: انقلابُ قرار {len(flips)} {flips} · نشطٌ في القائمة {len(act)} {act}")
    if ts0a < 97 or ts0b < 95:
        print("⚖️ TS0 ساقط ⇒ «لا قياس»")
        return 3
    verdict = "① عطلٌ مُثبَت يلزمه إصلاح" if (flips or act) else "② حدٌّ معلَنٌ بنسبته"
    print(f"⚖️ الحكم: {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
