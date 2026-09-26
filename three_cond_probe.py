# -*- coding: utf-8 -*-
"""🔎 مِجَسٌّ مؤقّت (2026-09-26 · يُحذف بعد القراءة): «الأسهمُ التي توافق شروطي الثلاثة الآن» — كونُ البوت كلُّه.

سؤالُ المالك (2026-09-26): «سهم cext سهم ارتكاز و شورته و فلوته مناسب ومع ذلك ما ذكرته؟ + سهم فيصل اللي جبته انت
عن طريق الشارت؟ … ليه ما تعطيني الأسهم اللي توافق الشروط الثلاثة و انت متاكد».

**قراءةٌ فقط** · بلا تلغرام (لا سرَّ له في الـworkflow) · لا كتابةَ حالة · ولا commit. **والتعريفاتُ مثبَّتةٌ هنا قبل أيّ رقم —
هي تعريفاتُ `watch_week_probe` نفسُها بالاسم** (‏`WW.flags` · `WW.conj` · وحدودُ المالك `OPL`/`PX`):
① **الكون** = `S.get_universe()` (كونُ الفرز نفسُه) · **الشموع** = `S.download_history` (ياهو كالفرز) · وآخرُ شمعةٍ يجب أن تكون
   **آخرَ جلسةٍ في البيانات** (الأكثرُ تكرارًا) وإلّا «بائت» ⇒ مجهول.
② **RSI14** = `S.rsi` على `Close` حتى آخر شمعة · **السعر** = آخرُ إغلاق (فوق الدولار = `PX.PX_MIN`).
③ **الفلوت** = `S._yahoo_float(sym, strict=True)` (‏`floatShares` وحدَه) لمن عبر ② وحدَه.
④ **«الشورت»** = المتاحُ (`shares_available` · ChartExchange — سطرُ «شورت» في الكرت): صفُّ حصّاد اليوم أوّلًا (`S._harvested_borrow`)
   ثمّ `S.ce_borrow_info` لمن عبر ②③ ثمّ CETX وSXTC ثمّ مجهولِ الفلوت · بسقف `CE_CAP` نداءً (حصّةُ الموقع ‏≈50/رنر) وشاهدٍ في
   الأوّل والآخر · **والتعذّرُ يُطبع بسببه ولا يُعدّ «لا»**.
⑤ **الحكم** = `WW.conj(WW.flags(...))`: «نعم» الأربعةُ معلومةٌ وعابرة · «لا» سقط شرطٌ معلوم · «مجهول» غيرُ ذلك.
⑥ لكلّ مطابقٍ ومجهول: **حالتُه عند البوت** — في القائمة/الارتداد (`weekly_watchlist.json`) · تحت المتابعة (`near_watch.json`)
   · وهُويّةُ الارتكاز الآن (`S.analyze_ticker` بالاسم ⟵ «مؤهّل» أو رمزُ الرفض).
⑦ **CETX وSXTC يُطبعان دائمًا** بقيمهما الأربع وحكمهما.
⑧ **شاهدُ هُويّة:** RSI SXTC المحسوب يطابق `rsi_now` المخزَّن في `near_watch.json` (من فرز اليوم) ضمن نقطة — وإلّا ⚠️.

الخروج: 0 قياس · 3 شاهدٌ ساقط (الأرقامُ تُطبع وتُقرأ بحذر) · 4 لا بيانات.
"""
import collections
import datetime as dt
import json
import os
import sys
import time

import Super_stock as S
import opentry_link_probe as OPL                                     # حدودُ المالك بالاسم
import prelink_px as PX                                              # PX_MIN بالاسم
import watch_week_probe as WW                                        # flags · conj بالاسم

NAMED = ("CETX", "SXTC")
CE_CAP = int(os.environ.get("CE_CAP") or 45)     # engineering — تحت حصّة الموقع ‏≈50 صفحة/رنر (مقيس #461)
CE_PAUSE = 0.6                                   # engineering — كحصّاد الاقتراض
WITNESS = "AAPL"                                 # شاهدُ الحصّة: صفحتُه تعود دائمًا
RSI_TOL = 1.0                                    # ⑧


def log(msg=""):
    print(msg, flush=True)


def _fmt(x, f="{:,.0f}"):
    return "—" if x is None else f.format(x)


def _mark(x):
    return "؟" if x is None else ("✅" if x else "❌")


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:                                                # noqa: BLE001
        return default


def bot_status(sym, wl, nw):
    out = []
    for sec, lab in (("stocks", "في القائمة"), ("pullback", "في الارتداد")):
        for x in wl.get(sec) or []:
            if x.get("symbol") == sym:
                out.append(f"{lab}({x.get('cont_status') or x.get('status') or ''})")
    n = nw.get(sym) if isinstance(nw, dict) else None
    if n:
        out.append("تحت المتابعة: " + " · ".join(n.get("outside") or []))
    return " · ".join(out) or "ليس عند البوت"


def identity(sym, df):
    """هُويّةُ الارتكاز الآن بـ`S.analyze_ticker` بالاسم ⟵ «مؤهّل» أو رمزُ الرفض."""
    try:
        S._REJECT_REASONS.pop(sym, None)
        r = S.analyze_ticker(sym, df)
        if r:
            return "مؤهّل ارتكاز"
        return "مرفوض: " + str(S._REJECT_REASONS.get(sym) or "؟")
    except Exception as e:                                           # noqa: BLE001
        return f"تعذّر: {type(e).__name__}"


def main() -> int:                                                   # noqa: PLR0912, PLR0915
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    uni = S.get_universe()
    for s in NAMED:
        if s not in uni:
            log(f"ℹ️ {s} ليس في كون ناسداك المفلتَر — يُضاف للقياس")
            uni.append(s)
    hist = S.download_history(uni)
    if not hist:
        log("⛔ لا بيانات")
        return 4
    last = {s: df.index[-1].date().isoformat() for s, df in hist.items() if len(df)}
    sess = collections.Counter(last.values()).most_common(1)[0][0]
    log(f"📅 آخرُ جلسة (الأكثرُ تكرارًا): {sess} · طازج {sum(v == sess for v in last.values())} من {len(last)}")

    rows = {}
    for s, df in hist.items():
        fresh = last.get(s) == sess
        rsi = px = None
        if fresh and len(df) >= 21:
            try:
                rsi = float(S.rsi(df["Close"]).iloc[-1])
                px = float(df["Close"].iloc[-1])
            except Exception:                                        # noqa: BLE001
                rsi = px = None
        rows[s] = {"rsi": rsi, "px": px, "fl": None, "av": None, "src": "", "fresh": fresh}

    c2 = [s for s, r in rows.items() if r["rsi"] is not None and r["rsi"] < OPL.RSI_OWNER
          and r["px"] is not None and r["px"] >= PX.PX_MIN]
    log(f"② RSI أقلّ من {OPL.RSI_OWNER:g} وفوق الدولار: {len(c2)}")
    for s in sorted(set(c2) | set(n for n in NAMED if n in rows)):
        rows[s]["fl"] = S._yahoo_float(s, strict=True)
        time.sleep(0.3)
    c3 = [s for s in c2 if rows[s]["fl"] is not None and rows[s]["fl"] < OPL.FLOAT_OWNER]
    unk_fl = [s for s in c2 if rows[s]["fl"] is None]
    log(f"③ فلوتٌ أقلّ من {OPL.FLOAT_OWNER:,}: {len(c3)} · فلوتٌ مجهول: {len(unk_fl)} {unk_fl[:30]}")

    hv = S._harvested_borrow(today)
    order = []
    for s in c3 + [n for n in NAMED if n in rows] + unk_fl:
        if s not in order:
            order.append(s)
    asked, why = 0, collections.Counter()
    w0 = S.ce_borrow_info(WITNESS)
    log(f"🩺 شاهدُ الحصّة أوّلًا ({WITNESS}): {'✓' if w0.get('shares_available') is not None else '✗'}")
    skipped = []
    for s in order:
        h = hv.get(s)
        if h and h.get("shares_available") is not None:
            rows[s]["av"], rows[s]["src"] = h["shares_available"], f"حصاد {today}"
            continue
        if asked >= CE_CAP:
            skipped.append(s)
            continue
        d = {}
        time.sleep(CE_PAUSE)
        info = S.ce_borrow_info(s, diag=d)
        asked += 1
        if info.get("shares_available") is not None:
            rows[s]["av"], rows[s]["src"] = info["shares_available"], "ChartExchange الآن"
        else:
            rows[s]["src"] = "تعذّر: " + str(d.get("reason") or "؟")
            why[d.get("reason") or "؟"] += 1
    w1 = S.ce_borrow_info(WITNESS)
    log(f"🩺 شاهدُ الحصّة آخرًا ({WITNESS}): {'✓' if w1.get('shares_available') is not None else '✗'} · "
        f"نداءات {asked} من سقف {CE_CAP} · تعذّر {dict(why)} · لم يُسأل (السقف) {len(skipped)} {skipped[:30]}")

    wl = load_json("weekly_watchlist.json", {})
    nw = load_json("near_watch.json", {})
    verdict = {}
    for s, r in rows.items():
        verdict[s] = WW.conj(WW.flags(r["rsi"], r["px"], r["fl"], r["av"]))

    def line(s):
        r = rows[s]
        fl = WW.flags(r["rsi"], r["px"], r["fl"], r["av"])
        return (f"  {s:6} ${_fmt(r['px'], '{:.2f}')} · RSI {_fmt(r['rsi'], '{:.1f}')} {_mark(fl[0])} · "
                f"فلوت {_fmt(r['fl'])} {_mark(fl[1])} · متاح {_fmt(r['av'])} {_mark(fl[2])} ({r['src'] or '—'}) · "
                f"دولار {_mark(fl[3])} ⟵ {identity(s, hist[s])} · {bot_status(s, wl, nw)}")

    rc = 0
    sx = rows.get("SXTC")
    ref = (nw.get("SXTC") or {}).get("rsi_now") if isinstance(nw, dict) else None
    if sx and sx["rsi"] is not None and ref is not None:
        ok = abs(sx["rsi"] - float(ref)) <= RSI_TOL
        log(f"⑧ شاهدُ الهُويّة: RSI SXTC المحسوب {sx['rsi']:.2f} مقابل المخزَّن {float(ref):.2f} ⟵ {'✓' if ok else '⚠️ ساقط'}")
        rc = 0 if ok else 3
    else:
        log("⑧ شاهدُ الهُويّة: لا قيمة للمقارنة ⟵ ⚠️")

    log("\n⑦ السهمان المسمَّيان:")
    for s in NAMED:
        log(line(s) if s in rows else f"  {s}: لا شموع")
    unk = sorted(s for s in c2 if verdict[s] is None)
    yes = sorted((s for s in rows if verdict[s] is True), key=lambda s: rows[s]["rsi"])
    log(f"\n❔ مجهولٌ (شرطٌ غيرُ معلوم ولم يسقط غيرُه) — {len(unk)}:")
    for s in unk:
        log(line(s))
    log(f"\n✅ يطابق الأربعةَ (RSI أقلّ من {OPL.RSI_OWNER:g} · فلوت أقلّ من {OPL.FLOAT_OWNER:,} · متاح أقلّ من "
        f"{OPL.AVAIL_OWNER:,} · فوق الدولار) — {len(yes)}:")
    for s in yes:
        log(line(s))
    log(f"\n🧾 الكون {len(uni)} · شموع {len(hist)} · جلسة {sess} · ② {len(c2)} · ③ {len(c3)} (مجهول الفلوت {len(unk_fl)}) · "
        f"مطابق {len(yes)} · مجهول {len(unk)}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
