# -*- coding: utf-8 -*-
"""🔎📬 «شروطُك الثلاثة» — رسالةٌ يوميّة بالأسهم التي تطابق: RSI أقلّ من 30 · فلوت أقلّ من 4 ملايين · «الشورت»
(المتاح) أقلّ من 20 ألفًا · سعر دولار فأكثر — على كون البوت كلِّه **وتحت المتابعة ضمنًا**.

أمرُ المالك (2026-09-26): «أرسلها كل يوم و حتى الأسهم اللي تحت المتابعة يشملها الاداة» — بعد مسكته «rsi 51 ل mgn» ثمّ
«افحص البوت»: فحصُ الكون كلِّه (`36244720433`) وجد تاريخَ ياهو **غيرَ متّسقٍ مع التقسيمات في 39 من 3,390 رمزًا** (MGN منها)
⇒ **RSI من Polygon adjusted** (مصدرُ التقرير السابق نفسُه) **وياهو للتحقّق**.

**التعريفات (مثبَّتةٌ قبل أيّ رقم — تعريفاتُ `watch_week_probe` بالاسم):**
① **الكون** = `S.get_universe()` ∪ القائمةُ والارتدادُ (`weekly_watchlist.json`) ∪ **تحت المتابعة** (`near_watch.json`).
② **الجلسة** = آخرُ جلسةٍ منتهية (`WW.last_closed_day`) · **والمجدولُ لا يُرسل إلّا إن كانت الجلسةُ اليومَ أو أمسَ بتوقيت نيويورك**
   (عطلةٌ ⇒ صمتٌ بسببٍ مطبوع لا تكرارُ رسالةٍ قديمة) · واليدويُّ بـ`force` يُرسل.
③ **RSI14** = `WW.rsi_at` (‏`S.rsi` على إغلاقات Polygon `adjusted=true` حتى إغلاق الجلسة · ‏21 فأكثر وإلّا مجهول) · **والسعر**
   = إغلاقُ الجلسة نفسِها (`WW.close_at` · آخرُ شمعة adjusted هي الخامّ بالبناء) · ورمزٌ بلا شمعةٍ في الجلسة ⇒ «بائت» ⇒ مجهول.
④ **الفلوت** = `S._yahoo_float(strict=True)` (‏`floatShares` وحدَه) ثمّ فلوتُ البوت المخزَّن (القائمة · `company_cache.json`) بوسمه.
⑤ **«الشورت»** = المتاح (`shares_available` · ChartExchange): صفُّ حصّاد اليوم (`S._harvested_borrow`) أوّلًا ثمّ
   `S.ce_borrow_info` **موزَّعًا على رنرات** (`need[shard::shards]` · حصّةُ الموقع ‏≈50 صفحة لكلّ رنر · #461) · والتعذّرُ
   يُطبع بسببه ولا يُعدّ «لا».
⑥ **الحكم** = `WW.conj(WW.flags(...))`: «نعم» الأربعةُ معلومةٌ وعابرة · «لا» سقط شرطٌ معلوم · «مجهول» غيرُ ذلك.
⑦ **تحقّقُ ياهو** لكلّ مرشّح: `S.rsi` على `S.download_history` — فرقٌ **فوق نقطتين** (`WW.RSI_TOL`) ⇒ «⚠️ مشكوك» في قسمه
   **لا في «يطابق»** · يُطبع الرقمان ولا يُخفى · ومدى نسبة الإغلاقين فوق `SPLIT_RATIO` يُوسَم «تقسيمٌ غيرُ متّسق».
⑧ **حالتُه عند البوت** لكلّ سطر: القائمة (حالةُ المتابعة) · الارتداد · 👀 تحت المتابعة (أسبابُها من الملفّ) · أو ليس عند البوت.
⑨ **حارسُ التغطية:** شموعُ Polygon في الجلسة لأقلّ من `MIN_COVER` من الكون ⇒ **لا قائمة** بل سطرُ عطلٍ صريح (لا «لا يوجد» كاذب).

المراحل (`TC_STAGE`): `scan` (Polygon · الفلوت · ياهو ⟵ `tc_scan.json`) ⟶ `borrow` (المتاح لجزء الرنر ⟵ `tc_borrow_<n>.json`) ⟶
`send` (الحكم والرسالة) · و`all` الثلاثُ في عمليّةٍ واحدة.
الخروج: 0 أُرسلت/طُبعت أو صمتُ عطلةٍ بسببه · 2 بلا مفتاح · 3 تغطيةٌ ناقصة (سطرُ العطل أُرسل) · 4 لا جلسةَ في التقويم.
"""
import concurrent.futures as cf
import datetime as dt
import glob
import json
import os
import sys
import time

import pandas as pd

import Super_stock as S
import opentry_link_probe as OPL                                     # حدودُ المالك بالاسم
import prelink_probe as P                                            # ticker_daily_adj بالاسم
import prelink_px as PX                                              # PX_MIN بالاسم
import watch_week_probe as WW                                        # flags · conj · rsi_at · close_at بالاسم
from kasih_scan import NY

STAGE = (os.environ.get("TC_STAGE") or "all").strip()
DRY = (os.environ.get("TC_DRY") or "0").strip() == "1"
FORCE = (os.environ.get("TC_FORCE") or "0").strip() == "1"
SHARD = int(os.environ.get("TC_SHARD") or 0)
SHARDS = max(1, int(os.environ.get("TC_SHARDS") or 1))
STATE_FILE = os.environ.get("TC_STATE") or "tc_scan.json"
PARTS_GLOB = os.environ.get("TC_PARTS") or "tc_borrow_*.json"
MIN_COVER = 0.85                 # engineering — كحارس تغطية الصيّادين (‏85%)
CE_CAP = 45                      # engineering — تحت حصّة الموقع ‏≈50 صفحة/رنر (مقيس #461)
CE_PAUSE = 0.6                   # engineering — كحصّاد الاقتراض
WITNESS = "AAPL"                 # شاهدُ الحصّة: صفحتُه تعود دائمًا
SPLIT_RATIO = 1.5                # «تقسيمٌ غيرُ متّسق» — عتبةُ فحص البوت `36244720433`
WORKERS = 8
NEAR_SHOW = 10                   # سقفُ عرض «سقطت بشرطٍ معلوم» — والقصُّ يُعلَن بعدده
BOT_LABEL = {"stocks": "🎯 في قائمة البوت", "pullback": "🔁 في قائمة الارتداد"}


def log(msg=""):
    print(msg, flush=True)


# ─────────────────────────── نقيّة ───────────────────────────
def session_gate(cal, now_ny, force=False):
    """(الجلسة, يُرسَل؟, السبب) — الجلسةُ آخرُ جلسةٍ منتهية · والمجدولُ يُرسل إن كانت **اليومَ أو أمسَ** بتوقيت نيويورك
    (فتشغيلٌ بعد عطلةٍ لا يُعيد رسالةَ جلسةٍ قديمة) · و`force` يُرسل دائمًا."""
    sess = WW.last_closed_day(cal, now_ny)
    today = now_ny.date().isoformat()
    yday = (now_ny.date() - dt.timedelta(days=1)).isoformat()
    if sess is None:
        return None, False, "لا جلسةَ منتهية في التقويم"
    if force:
        return sess, True, "يدويّ (force)"
    if sess in (today, yday):
        return sess, True, "جلسةٌ جديدة"
    return sess, False, f"آخرُ جلسةٍ {sess} ليست اليومَ ولا أمسَ بتوقيت نيويورك (عطلة) — لا تكرار"


def ratio_range(ya, pa):
    """مدى نسبة إغلاقات ياهو إلى Polygon على الأيّام المشتركة (الأكبرُ ÷ الأصغر) ⟵ None إن قلّت عن 20 يومًا ·
    و`ya`/`pa` = {تاريخ: إغلاق}. تقسيمٌ طبّقه مصدرٌ دون الآخر يرفعه فوق `SPLIT_RATIO` (الأرباحُ الموزّعة لا تصنع هذا)."""
    rs = [ya[d] / pa[d] for d in sorted(set(ya) & set(pa)) if ya[d] and pa[d] and ya[d] > 0 and pa[d] > 0]
    if len(rs) < 20:
        return None
    return max(rs) / min(rs)


def shard_of(need, shard, shards):
    """جزءُ الرنر من قائمة المتاح المطلوبة — `need[shard::shards]` (تقسيمٌ تامٌّ منفصل · كحصّاد الاقتراض)."""
    shards = max(1, int(shards))
    return list(need)[int(shard) % shards::shards]


def bot_label(sym, wl, nw):
    """حالةُ السهم عند البوت (عرضٌ فقط): القائمة (حالةُ المتابعة `WW.cont_label`) · الارتداد · تحت المتابعة (أسبابُها)."""
    out = []
    for sec in ("stocks", "pullback"):
        for e in (wl or {}).get(sec) or []:
            if e.get("symbol") == sym and (sec == "pullback" or e.get("status", "active") == "active"):
                tag = WW.cont_label(e) if sec == "stocks" else str(e.get("status") or "")
                out.append(f"{BOT_LABEL[sec]} ({tag})" if tag else BOT_LABEL[sec])
    n = (nw or {}).get(sym) if isinstance(nw, dict) else None
    if n:
        why = [str(x) for x in (n.get("outside") or [])][:2]
        out.append("👀 تحت المتابعة" + (": " + " · ".join(why) if why else ""))
    return " · ".join(out) or "ليس عند البوت"


def verdict(r, tol=None):
    """(الحكم, مشكوك؟) لصفٍّ فيه rsi · px · fl · av · ry — `WW.conj(WW.flags(...))` بالاسم · والشكُّ = فرقُ RSI ياهو
    عن Polygon فوق `tol` نقطة (`WW.RSI_TOL`) · وياهو المجهولُ لا يصنع شكًّا (لا دليلَ نقيض)."""
    tol = WW.RSI_TOL if tol is None else tol
    v = WW.conj(WW.flags(r.get("rsi"), r.get("px"), r.get("fl"), r.get("av")))
    ry, rp = r.get("ry"), r.get("rsi")
    doubt = ry is not None and rp is not None and abs(float(ry) - float(rp)) > tol
    return v, doubt


def near_misses(rows):
    """🔸 أسهمُ البوت (القائمة · الارتداد · تحت المتابعة) التي سقطت **بشرطٍ واحدٍ والثلاثةُ الباقية معلومةٌ وعابرة** ⟵
    [(رمز, السبب)] — تجيب «ليه ما ذكرت سهمي؟» (مسكةُ CETX: سقط بالمتاح وحدَه) · عرضٌ فقط لا يُعدّ مطابقة. ⚠️ ومَن سقط بالفلوت
    لا يُسأل عن متاحه (مجهول) ⇒ لا يُقال «بشرطٍ واحد» فيه — كان التشغيلُ الأوّل يسرد 68 أغلبُها فلوتٌ بعشرات الملايين (ضجيج)."""
    out = []
    names = ("RSI", "الفلوت", "المتاح", "السعر")
    for s in sorted(rows, key=lambda x: rows[x].get("rsi") if rows[x].get("rsi") is not None else 99):
        r = rows[s]
        if r.get("v") is not False or r.get("bot") in (None, "ليس عند البوت"):
            continue
        f = WW.flags(r.get("rsi"), r.get("px"), r.get("fl"), r.get("av"))
        bad = [i for i, x in enumerate(f) if x is False]
        if len(bad) != 1 or any(x is None for x in f):
            continue
        val = {1: _num_txt(r.get("fl")), 2: f"{(r.get('av') or 0):,.0f}"}.get(bad[0], "")
        out.append((s, f"{names[bad[0]]} {val}".strip()))
    return out


def _num_txt(x):
    """عددٌ بالعربيّة المختصرة للفلوت (مليون/ألف) — عرضٌ فقط."""
    if x is None:
        return "—"
    x = float(x)
    if x >= 1e6:
        return f"{x / 1e6:.2f} مليون"
    if x >= 1e3:
        return f"{x:,.0f}"
    return f"{x:,.0f}"


def build_message(st, rows):
    """نصُّ الرسالة (HTML تلغرام) — ✅ يطابق · ⚠️ مشكوك · ❔ مجهول · والتذييلُ بالعدّادات. **بلا علامات مقارنة.**"""
    sess = st.get("sess")
    lines = [f"🔎 <b>شروطك الثلاثة</b> — إغلاق {sess}",
             f"RSI أقلّ من {OPL.RSI_OWNER:g} · فلوت أقلّ من {OPL.FLOAT_OWNER / 1e6:g} ملايين · شورت (المتاح) أقلّ من "
             f"{OPL.AVAIL_OWNER:,} · سعر {PX.PX_MIN:g} دولار فأكثر",
             "(RSI من Polygon · وياهو للتحقّق)", ""]
    yes = sorted((s for s, r in rows.items() if r["v"] is True and not r["doubt"]), key=lambda s: rows[s]["rsi"])
    dbt = sorted((s for s, r in rows.items() if r["v"] is True and r["doubt"]), key=lambda s: rows[s]["rsi"])
    unk = sorted((s for s, r in rows.items() if r["v"] is None), key=lambda s: rows[s]["rsi"] if rows[s]["rsi"] is not None else 99)
    lines.append(f"✅ <b>يطابق: {len(yes)}</b>")
    for i, s in enumerate(yes, 1):
        r = rows[s]
        lines.append(f"{i}. ${s} · ${r['px']:.2f} · RSI {r['rsi']:.1f} · فلوت {_num_txt(r['fl'])} · متاح {r['av']:,.0f}")
        lines.append(f"   ↳ {r['bot']}")
    if not yes:
        lines.append("لا سهمَ يطابق الأربعةَ معًا في هذه الجلسة.")
    if dbt:
        tol = "نقطتين" if WW.RSI_TOL == 2 else f"{WW.RSI_TOL:g} نقاط"
        lines += ["", f"⚠️ <b>مشكوك — RSI ياهو يختلف عن Polygon بأكثر من {tol}: {len(dbt)}</b> (لا تُعدّ مطابقة)"]
        for s in dbt:
            r = rows[s]
            why = " · تقسيمٌ غيرُ متّسق بين المصدرين" if (r.get("ratio") or 0) > SPLIT_RATIO else ""
            lines.append(f"• ${s} · RSI Polygon {r['rsi']:.1f} · ياهو {r['ry']:.1f}{why} · ${r['px']:.2f} · {r['bot']}")
    if unk:
        lines += ["", f"❔ <b>مجهول — شرطٌ لم يُقَس ولم يسقط غيرُه: {len(unk)}</b>"]
        for s in unk:
            r = rows[s]
            miss = []
            if r.get("fl") is None:
                miss.append("الفلوت")
            if r.get("av") is None:
                miss.append("المتاح" + (f" ({r['av_src']})" if r.get("av_src") else ""))
            lines.append(f"• ${s} · RSI {_fmt1(r['rsi'])} · ${_fmt2(r['px'])} · الناقص: {' · '.join(miss) or '—'} · {r['bot']}")
    near = near_misses(rows)
    if near:
        lines += ["", f"🔸 <b>من أسهم البوت — سقطت بشرطٍ واحد (والثلاثةُ الباقية عابرة): {len(near)}</b>"]
        for s, why in near[:NEAR_SHOW]:
            lines.append(f"• ${s} · RSI {_fmt1(rows[s]['rsi'])} · {why} · {rows[s]['bot']}")
        if len(near) > NEAR_SHOW:
            lines.append(f"… و{len(near) - NEAR_SHOW} غيرُها (القصُّ مُعلَن)")
    c = st.get("counts") or {}
    lines += ["", f"🧾 الكون {c.get('universe', 0):,} · بشمعة الجلسة من Polygon {c.get('fresh', 0):,} · "
                  f"RSI أقلّ من {OPL.RSI_OWNER:g} وسعرٌ دولارٌ فأكثر {c.get('c2', 0)} · منها فلوتٌ أقلّ من الحدّ أو مجهول "
                  f"{c.get('c3', 0)} · المتاح: حصاد {c.get('av_harvest', 0)} · الموقع {c.get('av_ce', 0)} · "
                  f"تعذّر {c.get('av_fail', 0)}"]
    return S._rtl_join(lines)


def _fmt1(x):
    return "—" if x is None else f"{x:.1f}"


def _fmt2(x):
    return "—" if x is None else f"{x:.2f}"


def failure_message(sess, why):
    """سطرُ عطلٍ صريح بدل القائمة (حارسُ التغطية/البيانات البائتة) — لا «لا يوجد» كاذب."""
    return S._rtl_join([f"🔎 <b>شروطك الثلاثة</b> — إغلاق {sess}",
                        f"⚠️ تعذّر الفحص اليوم: {why}",
                        "لا تُقرأ الرسالةُ «لا يوجد» — البياناتُ ناقصة، وتُعاد غدًا."])


# ─────────────────────────── الجلب ───────────────────────────
def fetch_polygon(syms, d0, d1, key, workers=WORKERS):
    """{رمز: صفوف adjusted} بـ`P.ticker_daily_adj` بالاسم — متوازيًا · والتعذّرُ ⟵ []."""
    def one(s):
        try:
            return s, P.ticker_daily_adj(s, d0, d1, key) or []
        except Exception:                                            # noqa: BLE001
            return s, []
    out = {}
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        for i, (s, rows) in enumerate(ex.map(one, syms), 1):
            out[s] = rows
            if i % 500 == 0:
                log(f"   … Polygon {i}/{len(syms)}")
    return out


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:                                                # noqa: BLE001
        return default


def _dump(path, obj):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False)


# ─────────────────────────── المراحل ───────────────────────────
def stage_scan(now=None, key=None, fetch=None, universe=None, yahoo=None, yfloat=None, harvested=None,
               wl=None, nw=None, cache=None):
    """① ⟶ ④ + ⑦: الكون · Polygon · RSI والسعر · الفلوت · ياهو للتحقّق · وقائمةُ المتاح المطلوبة ⟵ الحالة (dict)."""
    now = now or dt.datetime.now(tz=NY)
    fetch = fetch or fetch_polygon
    cal = WW.calendar(now.year)
    sess, send, why = session_gate(cal, now, FORCE)
    st = {"sess": sess, "send": send, "why": why, "now": now.isoformat(), "rows": {}, "need": [], "counts": {},
          "fail": None}
    log(f"🔎 الجلسة {sess} · يُرسَل: {send} ({why})")
    if not sess or not send:
        return st                            # عطلةٌ/لا جلسة ⇒ صفرُ جلب (لا Polygon ولا ياهو ولا موقع)
    wl = load_json(WW.WL_FILE, {}) if wl is None else wl
    nw = load_json(S.NEAR_WATCH_FILE, {}) if nw is None else nw
    extra = sorted({e.get("symbol") for sec in ("stocks", "pullback") for e in (wl.get(sec) or []) if e.get("symbol")}
                   | set(nw if isinstance(nw, dict) else {}))
    uni = sorted(set(universe() if universe else S.get_universe()) | set(extra))
    d0 = (dt.date.fromisoformat(sess) - dt.timedelta(days=WW.HIST_DAYS)).isoformat()
    log(f"👥 الكون {len(uni)} (منه القائمة والارتداد وتحت المتابعة {len(extra)}) · Polygon {d0} ⟶ {sess} …")
    pg = fetch(uni, d0, sess, key)
    fresh = [s for s in uni if (pg.get(s) or []) and pg[s][-1][0] == sess]
    cover = len(fresh) / len(uni) if uni else 0.0
    st["counts"].update({"universe": len(uni), "polygon": sum(1 for s in uni if pg.get(s)), "fresh": len(fresh)})
    log(f"🩺 شمعةُ الجلسة من Polygon: {len(fresh)} من {len(uni)} = {cover * 100:.1f}% (الحدّ {MIN_COVER * 100:.0f}%)")
    if cover < MIN_COVER:
        st["fail"] = f"شموعُ Polygon لجلسة {sess} لم تكتمل ({len(fresh)} من {len(uni)})"
        return st
    rows = {}
    for s in fresh:
        rsi = WW.rsi_at(pg[s], sess)
        px = WW.close_at(pg[s], sess)
        if rsi is not None and px is not None and rsi < OPL.RSI_OWNER and px >= PX.PX_MIN:
            rows[s] = {"rsi": rsi, "px": px, "fl": None, "fl_src": "", "av": None, "av_src": "", "ry": None,
                       "ratio": None, "bot": bot_label(s, wl, nw)}
    st["counts"]["c2"] = len(rows)
    log(f"② RSI أقلّ من {OPL.RSI_OWNER:g} وسعرٌ دولارٌ فأكثر (Polygon): {len(rows)}")
    cache = load_json(S.COMPANY_FILE, {}) if cache is None else cache
    wl_fl = {e.get("symbol"): e.get("float") for sec in ("stocks", "pullback") for e in (wl.get(sec) or [])}
    for s in sorted(rows):
        fl = (yfloat or (lambda x: S._yahoo_float(x, strict=True)))(s)
        if fl:
            rows[s]["fl"], rows[s]["fl_src"] = float(fl), "ياهو"
        elif wl_fl.get(s):
            rows[s]["fl"], rows[s]["fl_src"] = float(wl_fl[s]), "قائمة البوت"
        elif isinstance(cache.get(s), dict) and cache[s].get("float"):
            rows[s]["fl"], rows[s]["fl_src"] = float(cache[s]["float"]), "ذاكرة البوت"
        if yfloat is None:
            time.sleep(0.3)
    c3 = [s for s in rows if rows[s]["fl"] is None or rows[s]["fl"] < OPL.FLOAT_OWNER]
    st["counts"]["c3"] = len(c3)
    log(f"③ فلوتٌ أقلّ من {OPL.FLOAT_OWNER:,} أو مجهول: {len(c3)} (مجهول {sum(1 for s in c3 if rows[s]['fl'] is None)})")
    yh = (yahoo or S.download_history)(sorted(c3)) if c3 else {}
    for s in c3:
        ydf = yh.get(s)
        if ydf is None or not len(ydf):
            continue
        ya = {i.date().isoformat(): float(c) for i, c in ydf["Close"].items()}
        cut = [ya[d] for d in sorted(ya) if d <= sess]
        if len(cut) >= WW.MIN_RSI_BARS:
            rows[s]["ry"] = float(S.rsi(pd.Series(cut)).iloc[-1])
        rows[s]["ratio"] = ratio_range(ya, {r[0]: r[4] for r in pg[s][-260:]})
    hv = (harvested or S._harvested_borrow)(dt.datetime.now(dt.timezone.utc).date().isoformat())
    need = []
    for s in sorted(c3, key=lambda x: (rows[x]["fl"] is None, rows[x]["rsi"])):
        h = hv.get(s)
        if h and h.get("shares_available") is not None:
            rows[s]["av"], rows[s]["av_src"] = float(h["shares_available"]), "حصاد اليوم"
        else:
            need.append(s)
    st["rows"], st["need"] = rows, need
    st["counts"]["av_harvest"] = sum(1 for s in c3 if rows[s]["av_src"] == "حصاد اليوم")
    log(f"⑤ المتاح: من حصاد اليوم {st['counts']['av_harvest']} · مطلوبٌ من الموقع {len(need)} {need[:40]}")
    return st


def stage_borrow(st, shard=SHARD, shards=SHARDS, ce=None, pause=CE_PAUSE):
    """⑤ المتاحُ لجزء الرنر `need[shard::shards]` من ChartExchange — شاهدٌ أوّلًا وآخرًا · وتعذّرٌ بسببه ⟵ {رمز: {av, why}}."""
    ce = ce or S.ce_borrow_info
    mine = shard_of(st.get("need") or [], shard, shards)[:CE_CAP]
    out = {}
    w0 = ce(WITNESS)
    for s in mine:
        d = {}
        if pause:
            time.sleep(pause)
        info = ce(s, diag=d)
        av = (info or {}).get("shares_available")
        out[s] = {"av": None if av is None else float(av), "why": None if av is not None else str(d.get("reason") or "؟")}
    w1 = ce(WITNESS)
    log(f"🩺 جزء {int(shard) % max(1, int(shards)) + 1} من {max(1, int(shards))}: {len(mine)} رمزًا · شاهدٌ أوّلًا "
        f"{'✓' if (w0 or {}).get('shares_available') is not None else '✗'} · آخرًا "
        f"{'✓' if (w1 or {}).get('shares_available') is not None else '✗'} · تعذّر "
        f"{sum(1 for v in out.values() if v['av'] is None)}")
    return out


def stage_send(st, parts, send=None):
    """⑥ ⟶ ⑨: دمجُ المتاح · الحكم · الرسالة · والإرسالُ (إلّا في `DRY`) ⟵ رمزُ الخروج."""
    send = send or S.send_telegram
    if not st.get("sess"):
        log("⛔ لا جلسة")
        return 4
    if not st.get("send"):
        log(f"🔕 لا إرسال: {st.get('why')}")
        return 0
    if st.get("fail"):
        msg = failure_message(st["sess"], st["fail"])
        log(msg)
        if not DRY:
            send(msg + "\n\n" + S.FOOTER)
        return 3
    rows = st.get("rows") or {}
    merged = {}
    for p in parts:
        merged.update(p or {})
    ok_ce = fail_ce = 0
    for s, v in merged.items():
        if s not in rows:
            continue
        if v.get("av") is not None:
            rows[s]["av"], rows[s]["av_src"] = float(v["av"]), "الموقع"
            ok_ce += 1
        else:
            rows[s]["av_src"] = "تعذّر: " + str(v.get("why") or "؟")
            fail_ce += 1
    for s in st.get("need") or []:
        if s in rows and s not in merged:
            rows[s]["av_src"] = "لم يُسأل (حصّة الموقع)"
            fail_ce += 1
    st.setdefault("counts", {}).update({"av_ce": ok_ce, "av_fail": fail_ce})
    for s, r in rows.items():
        r["v"], r["doubt"] = verdict(r)
    msg = build_message(st, rows)
    log(msg)
    if DRY:
        log("🧪 TC_DRY=1 — طُبعت ولم تُرسل")
        return 0
    send(msg + "\n\n" + S.FOOTER)
    return 0


def main() -> int:
    key = (os.environ.get("POLYGON_API_KEY") or "").strip()
    if STAGE in ("scan", "all") and not key:
        log("⛔ بلا POLYGON_API_KEY")
        return 2
    if STAGE == "scan":
        _dump(STATE_FILE, stage_scan(key=key))
        return 0
    if STAGE == "borrow":
        st = load_json(STATE_FILE, {})
        _dump(os.environ.get("TC_PART") or f"tc_borrow_{SHARD}.json", stage_borrow(st))
        return 0
    if STAGE == "send":
        st = load_json(STATE_FILE, {})
        parts = [load_json(p, {}) for p in sorted(glob.glob(PARTS_GLOB, recursive=True))]
        log(f"📦 أجزاءُ المتاح: {len(parts)}")
        return stage_send(st, parts)
    st = stage_scan(key=key)
    return stage_send(st, [stage_borrow(st, 0, 1)])


if __name__ == "__main__":
    sys.exit(main())
