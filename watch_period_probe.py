# -*- coding: utf-8 -*-
"""🗓️🔎② «التقريران» — Penny لنفس فترة التقرير السابق · والشهر الكامل Penny/Dollar — بتعريفات `watch_week_probe` **بالاسم**.

أمرُ المالك (2026-09-26 · «نفذ البروميت»): «التقرير الأول الذي نفذته سابقًا انتهى بالفعل. لا تعِد تشغيله ولا تعِد حسابه …
التقرير 1 — Penny Stocks لنفس فترة التقرير السابق … التقرير 2 — الشهر الكامل … لا تخلط المجموعتين إطلاقًا في المقام أو
النسبة … والتصنيف يكون حسب السعر عند الارتكاز/الإشارة».

**قراءةٌ فقط** · لا تلغرام · لا كتابةَ حالة. **والتعريفاتُ مستخرَجةٌ من التقرير السابق (`watch_week_result.md` · الحاكمة
`36195923031` والممتدّة `36203459825`) ومن أداتِه — تُستعمل بالاسم لا نسخًا — ومثبَّتةٌ هنا قبل أيّ رقم:**
① **الفترة** `PERIOD_FROM` ⟶ `PERIOD_TO` (أيّامُ التداول بينهما بـ`WW.calendar` حتى آخر جلسةٍ منتهية `WW.last_closed_day`) ·
   التقرير 1 = **2026-09-21 ⟶ 2026-09-25** (فترةُ السابق حرفيًّا) · التقرير 2 = **2026-09-01 ⟶ 2026-09-30** (ويُطبع كم جلسةً منتهيةً منه).
② **المجتمع** = نشطُ `weekly_watchlist.json` في أحدث لقطةٍ على main قبل 09:30 نيويورك من كلّ جلسة (`WW.snapshot_before` ·
   `WW.active_entries`) · والاتّحادُ بالرمز = «الارتكازاتُ المراقَبة» · **وقائمةُ الارتداد مجتمعٌ ثانٍ** (`WW.pullback_entries` ·
   خارجَ الاتّحاد) لا يُخزَّن لها «المتاح» ⇒ ما استوفى الثلاثةَ المعلومة منها **«مجهولُ الشورت»** لا مؤهّلٌ ولا مرفوض.
③ **الشروط** لكلّ (سهم، جلسة d) عند **إغلاق الجلسة السابقة c** (`WW.prev_day`): RSI14 (`WW.rsi_at` · Polygon adjusted) · الفلوت
   و«الشورت» = `float` و`shares_available` (المتاح) **من لقطة d** · الحدودُ بالاسم حصريّة (`WW.flags`) · والمجهولُ مجهول.
④ **الإشارة** = أوّلُ جلسةٍ في الفترة تستوفي الثلاثةَ معًا (RSI · فلوت · شورت) · **والفئة من سعر الإشارة** = إغلاقُ c **الخامّ**
   (`WW.close_at` على `adjusted=false` كتعريف السابق): **Penny = أقلّ من `PX.PX_MIN`** · **Dollar = `PX.PX_MIN` فأكثر** (`WW.flags[3]`
   بعينه) — **وتبقى فئتُه لا تتغيّر بعدها**. والمراقَبُ بلا إشارةٍ يُصنَّف لعدّ «الارتكازات» بسعر c أوّلِ جلسةٍ رُوقب فيها.
⑤ **إزالةُ التكرار** (قاعدةُ السابق): السهمُ مرّةً واحدة بالرمز · إشارتُه الأولى وحدَها · وتكرارُ المطابقة لا يُعَدّ ⇒ **المقام =
   عددُ الأسهم المؤهّلة فعلًا** في كلّ فئةٍ على حدة.
⑥ **الانفجار** (`WW.EXPLODE` · `WW.max_rise`): أقصى `high` adjusted من جلسة الإشارة حتى آخر جلسةٍ منتهية في الفترة ÷ إغلاق c
   adjusted − 1 ⟵ **+50%** «انفجر» (و+100% يُطبع) · ووقتُه يومُ القمّة · **والعمودُ الممتدّ** (`WW.ext_bounds` · `WW.max_rise_ext` ·
   البري والأفتر من دقائق Polygon) بجانبه · وسطرُ الحكم يحمل العمودين (ملحقُ السابق ⑧) · وحركةٌ قبل الإشارة لا تُحتسب بالبناء.
⑦ **الحرّاس بعتبات السابق بالاسم** قبل أيّ رقم: `V-W2` (`WW.MIN_BAR_COVER`) · `V-W1` (`WW.vw1` مع `WW.partial_nominations`) ·
   وللعمود الممتدّ `V-W3`/`V-W4` (`WW.vw4`) — وسقوطُهما ⇒ الممتدُّ «لا حكم» ولا يمسّ النظاميّ.
⑧ **سلسلةُ التحقّق** لكلّ فئة (تراكميّةً داخل الجلسة الواحدة): خامٌ (سهم×جلسة) ⟵ أسهمٌ بعد إزالة التكرار ⟵ الفئة ⟵ فلوت ⟵ RSI ⟵
   شورت ⟵ المؤهّلة ⟵ انفجرت · **وحارسُ اتّساق**: المؤهّلُ بالسلسلة = المؤهّلُ بالإشارة الأولى (فرقٌ ⇒ يُطبع بأسمائه لا يُخفى).
⑨ **شاهدُ الهُويّة مع التقرير السابق (`V-P1`)** — إن وقعت جلساتُ 2026-09-21 ⟶ 25 كلُّها داخل الفترة: عدُّ (سهم×جلسة · RSI · فلوت ·
   متاح · دولار) يطابق المنشور **177 · 4 · 76 · 57 · 156** — عدٌّ لا تحليلُ دولار · والفرقُ يُطبع ولا يُخفى.
⑩ **الفئات** (`PERIOD_CLASSES`): `penny` للتقرير 1 (**لا تُحلَّل أسهمُ الدولار مرّةً أخرى**) · `penny,dollar` للتقرير 2.

الخروج: 0 قياس · 2 بلا مفتاح · 3 حارسٌ ساقط · 4 لا لقطة/لا رمز · 5 ليست قراءةً فقط.
"""
import collections
import datetime as dt
import json
import os
import statistics
import sys

import opentry_link_probe as OPL                                     # حدودُ المالك بالاسم (للطباعة)
import prelink_probe as P                                            # _selfcheck_readonly بالاسم
import prelink_px as PX                                              # PX_MIN بالاسم
import watch_week_probe as WW                                        # التعريفاتُ كلُّها بالاسم
from kasih_scan import NY

P_FROM = (os.environ.get("PERIOD_FROM") or "").strip()
P_TO = (os.environ.get("PERIOD_TO") or "").strip()
CLASSES = tuple(x.strip() for x in (os.environ.get("PERIOD_CLASSES") or "penny,dollar").split(",") if x.strip())
WEEK_REF = ("2026-09-21", "2026-09-25")                             # ⑨ فترةُ التقرير السابق
PUBLISHED = (177, 4, 76, 57, 156)                                    # ⑨ watch_week_result.md ③ — المجموع
LABEL = {"penny": "🪙 Penny (سعرُ الإشارة الخامّ أقلّ من $1.00)", "dollar": "💵 Dollar (سعرُ الإشارة الخامّ $1.00 فأكثر)"}
UTC = WW.UTC


def log(msg=""):
    print(msg, flush=True)


# ─────────────────────────── نقيّة ───────────────────────────
def klass(px):
    """فئةُ السعر الخامّ — `WW.flags` بعينها (دولارٌ = `PX.PX_MIN` فأكثر) ⟵ penny · dollar · None (مجهول)."""
    f = WW.flags(None, px, None, None)[3]
    return None if f is None else ("dollar" if f else "penny")


def three(f):
    """الاقترانُ على الثلاثة (RSI · فلوت · شورت) — `WW.conj` بالاسم."""
    return WW.conj(f[:3])


def signal_of(per_s):
    """④ أوّلُ جلسةٍ تستوفي الثلاثة ⟵ d أو None."""
    for d in sorted(per_s):
        if three(per_s[d]["f"]) is True:
            return d
    return None


def unknown_of(per_s):
    """أوّلُ جلسةٍ اقترانُها «مجهول» — لسهمٍ بلا إشارةٍ ولا جلسةٍ ساقطةٍ كلُّها ⟵ d أو None."""
    if signal_of(per_s) is not None:
        return None
    for d in sorted(per_s):
        if three(per_s[d]["f"]) is None:
            return d
    return None


def chain(per, syms, k):
    """⑧ سلسلةُ التحقّق للفئة k — تراكميّةً داخل الجلسة الواحدة ⟵ [(الاسم, عددُ الأسهم, الأسماء)]."""
    def has(s, pred):
        return any(pred(per[s][d]) for d in per[s])

    def kc(r):
        return klass(r["px"]) == k
    s1 = [s for s in syms if has(s, kc)]
    s2 = [s for s in s1 if has(s, lambda r: kc(r) and r["f"][1] is True)]
    s3 = [s for s in s2 if has(s, lambda r: kc(r) and r["f"][1] is True and r["f"][0] is True)]
    s4 = [s for s in s3 if has(s, lambda r: kc(r) and r["f"][1] is True and r["f"][0] is True and r["f"][2] is True)]
    return [("الفئة", len(s1), s1), ("فلوت", len(s2), s2), ("RSI", len(s3), s3), ("شورت", len(s4), s4)]


def stats(xs):
    """(المتوسّط, الوسيط, الأكبر) لقائمة نسبٍ معلومة ⟵ None للفارغة."""
    xs = [x for x in xs if x is not None]
    if not xs:
        return None, None, None
    return sum(xs) / len(xs), statistics.median(xs), max(xs)


def outcome(adj, c, d_sig, last_day, mins, seen, now_utc):
    """⑥ نتيجةُ الإشارة: النظاميّ (`WW.max_rise`) والممتدّ (`WW.max_rise_ext`) من جلسة الإشارة حتى آخر جلسة ⟵ dict."""
    c0 = WW.close_at(adj, c)
    mr, mday = WW.max_rise(adj, c, d_sig, last_day)
    st, en = WW.ext_bounds(d_sig, seen, last_day, now_utc)
    xm, xms = WW.max_rise_ext(mins or [], c0, st, en)

    def hi(p):
        return None if p is None or not c0 else c0 * (1.0 + p / 100.0)
    return {"c0": c0, "reg": mr, "reg_day": mday, "reg_hi": hi(mr), "ext": xm, "ext_ms": xms, "ext_hi": hi(xm)}


def _fmt(x, f="{:,.0f}"):
    return "—" if x is None else f.format(x)


def _pct(x):
    return "—" if x is None else f"{x:+.1f}%"


# ─────────────────────────── الرئيسيّ ───────────────────────────
def main(now=None, d_from=None, d_to=None, classes=None) -> int:    # noqa: PLR0911, PLR0912, PLR0915
    if not P._selfcheck_readonly(open(__file__, encoding="utf-8").read()):
        log("⛔ ليست قراءةً فقط")
        return 5
    key = (os.environ.get("POLYGON_API_KEY") or "").strip()
    if not key:
        log("⛔ بلا POLYGON_API_KEY")
        return 2
    now = now or dt.datetime.now(tz=NY)
    classes = tuple(classes or CLASSES)
    cal = WW.calendar(now.year)
    last_day = WW.last_closed_day(cal, now)
    d_from, d_to = (d_from or P_FROM or WW.monday_of(last_day)), (d_to or P_TO or last_day)
    full = [d for d in cal if d_from <= d <= d_to]
    days_all = [d for d in full if d <= last_day]
    commits = WW.wl_commits()
    lists, pb_by = {}, {}
    for d in days_all:
        sb = WW.snapshot_before(commits, WW.open_utc(d))
        if not sb:
            continue
        js = WW.load_snapshot(sb[1])
        if js is None:
            continue
        lists[d] = (sb[0], sb[1], WW.active_entries(js))
        pb_by[d] = WW.pullback_entries(js)
    if not lists:
        log(f"⛔ لا لقطةَ قبل أيّ جلسة في {d_from} ⟶ {d_to}")
        return 4
    days = sorted(lists)
    log(f"🗓️🔎② الفترة {d_from} ⟶ {d_to}: {len(days)} من {len(full)} جلسة منتهية ({days[0]} ⟶ {days[-1]}) · الفئات: "
        f"{', '.join(classes)} · الشروط: RSI أقلّ من {OPL.RSI_OWNER:g} · فلوت أقلّ من {OPL.FLOAT_OWNER:,} · «شورت» (المتاح) أقلّ "
        f"من {OPL.AVAIL_OWNER:,} · الفئة من سعر الإشارة الخامّ (حدُّ الدولار ${PX.PX_MIN:.2f})")
    union = sorted({s for d in days for s in lists[d][2]})
    if not union:
        log("⛔ صفرُ رمز")
        return 4
    first_entry, last_entry = {}, {}
    for d in days:
        for s, e in lists[d][2].items():
            first_entry.setdefault(s, e)
            last_entry[s] = e
    pb_union = sorted({s for d in days for s in pb_by.get(d, {})} - set(union))
    log(f"👥 المراقَبة (القائمة): {len(union)} · والارتداد خارجها: {len(pb_union)}")

    d0 = (dt.date.fromisoformat(days[0]) - dt.timedelta(days=WW.HIST_DAYS)).isoformat()
    adj_by, raw_by = {}, {}
    for i, s in enumerate(union + pb_union, 1):
        adj_by[s], raw_by[s] = WW.fetch_bars(s, d0, days[-1], key)
        if i % 25 == 0:
            log(f"   … {i}/{len(union) + len(pb_union)}")
    covered = [s for s in union if adj_by.get(s)]
    cover = len(covered) / len(union)
    log(f"🩺 V-W2 الشموع: {len(covered)} من {len(union)} = {cover * 100:.1f}% (الحدّ {WW.MIN_BAR_COVER * 100:.0f}%) · "
        f"بلا شموع: {', '.join(s for s in union if not adj_by.get(s)) or 'لا أحد'}")
    if cover < WW.MIN_BAR_COVER:
        log("⛔ V-W2 ساقط — لا رقم")
        return 3
    since = WW.prev_day(cal, days[0]) or days[0]
    part = WW.partial_nominations(commits, first_entry, since)
    agree, n1, rows1 = WW.vw1(first_entry, adj_by, since, exclude=part)
    log(f"🔒 V-W1 RSI عند `ref_bar` مقابل المخزَّن (ترشيحاتٌ من {since}): {sum(1 for r in rows1 if r[4])}/{n1} = "
        f"{agree * 100:.1f}% ضمن {WW.RSI_TOL:g} نقطة (الحدّ {WW.V_AGREE * 100:.0f}% على {WW.V_MIN_N} فأكثر) · خارج المقارنة "
        f"(قبل إغلاق جلسة شمعتهم) {len(part)}")
    for r in rows1:
        if not r[4]:
            log(f"      ✗ {r[0]:6} ref {r[1]} · مخزَّن {r[2]:.1f} · محسوب {r[3]:.1f}")
    if n1 >= WW.V_MIN_N and agree < WW.V_AGREE:
        log("⛔ V-W1 ساقط — RSI المحسوب لا يطابق RSI البوت ⇒ لا رقم")
        return 3
    if n1 < WW.V_MIN_N:
        log(f"⚠️ V-W1 «لا يُحكم» (n={n1} دون {WW.V_MIN_N}) — يُكمَل بلا تأكيد هُويّة RSI")

    # ── لكلّ (سهم، جلسة) ──
    per = collections.defaultdict(dict)
    for d in days:
        c = WW.prev_day(cal, d)
        for s, e in lists[d][2].items():
            rsi = WW.rsi_at(adj_by.get(s) or [], c)
            px = WW.close_at(raw_by.get(s) or [], c)
            fl, av = WW._num(e.get("float")), WW._num(e.get("shares_available"))
            per[s][d] = {"c": c, "rsi": rsi, "px": px, "float": fl, "avail": av, "f": WW.flags(rsi, px, fl, av)}
    pper = collections.defaultdict(dict)
    for d in days:
        c = WW.prev_day(cal, d)
        for s, e in pb_by.get(d, {}).items():
            if s in pb_union:
                rsi = WW.rsi_at(adj_by.get(s) or [], c)
                px = WW.close_at(raw_by.get(s) or [], c)
                fl = WW._num(e.get("float"))
                pper[s][d] = {"c": c, "rsi": rsi, "px": px, "float": fl, "avail": None, "f": WW.flags(rsi, px, fl, None),
                              "status": e.get("status")}

    # ── ⑨ شاهدُ الهُويّة مع التقرير السابق ──
    if all(d in days for d in [x for x in full if WEEK_REF[0] <= x <= WEEK_REF[1]]) and WEEK_REF[0] in days:
        wk = [(s, d) for d in days if WEEK_REF[0] <= d <= WEEK_REF[1] for s in lists[d][2]]
        got = (len(wk),) + tuple(sum(1 for s, d in wk if per[s][d]["f"][i] is True) for i in range(4))
        log(f"🪪 V-P1 شاهدُ الهُويّة مع التقرير السابق (أسبوع {WEEK_REF[0]} ⟶ {WEEK_REF[1]} · سهم×جلسة · RSI · فلوت · متاح · "
            f"دولار): محسوب {got} مقابل المنشور {PUBLISHED} ⟵ " + ("✓ يطابق" if got == PUBLISHED else
                                                                "⚠️ **يختلف — يُطبع ولا يُخفى**"))

    # ── ⑧ الجلسةُ الممتدّة — حارساها قبل أيّ رقمٍ ممتدّ ──
    now_utc = now.astimezone(UTC)
    week_lo = WW.ext_bounds(days[0], None, days[-1], now_utc)[0]
    d1_by = {s: sorted(per[s])[0] for s in union}
    seen = WW.first_seen_map(commits, d1_by, week_lo)
    pseen = WW.first_seen_map(commits, {s: sorted(pper[s])[0] for s in pb_union if pper.get(s)}, week_lo,
                              pick=WW.pullback_entries)
    mins_by, reg, ext = {}, {}, {}
    for s in union + pb_union:
        mins_by[s] = WW.fetch_minutes(s, days[0], days[-1], key)
    for s in union:
        c1 = per[s][d1_by[s]]["c"]
        reg[s] = WW.max_rise(adj_by.get(s) or [], c1, d1_by[s], days[-1])
        st, en = WW.ext_bounds(d1_by[s], seen.get(s), days[-1], now_utc)
        ext[s] = WW.max_rise_ext(mins_by[s], WW.close_at(adj_by.get(s) or [], c1), st, en)
    n_min = sum(1 for s in union if mins_by.get(s))
    mcov = n_min / len(union)
    agree4, n4, bad4 = WW.vw4([(s, reg[s][0], ext[s][0]) for s in union])
    ext_ok = mcov >= WW.MIN_MIN_COVER and n4 > 0 and agree4 >= WW.MIN_EXT_AGREE
    log(f"🩺 V-W3 شموعُ الدقيقة: {n_min} من {len(union)} = {mcov * 100:.1f}% · 🔒 V-W4 {n4 - len(bad4)}/{n4} = "
        f"{agree4 * 100:.1f}% ⟵ الممتدّ {'قائم' if ext_ok else '«لا حكم»'}"
        + (" · الشاذّون: " + ", ".join(f"{b[0]} {b[1]:+.1f}/{b[2]:+.1f}" for b in bad4) if bad4 else ""))

    # ── ④ الإشارةُ والفئة ──
    sig = {s: signal_of(per[s]) for s in union}
    cls = {}
    for s in union:
        d = sig[s] or unknown_of(per[s]) or d1_by[s]
        cls[s] = klass(per[s][d]["px"])
    raw_pairs = sum(len(per[s]) for s in union)
    log("")
    log("=" * 78)
    log(f"🔗 السلسلة: خامٌ (سهم×جلسة) {raw_pairs} ⟵ بعد إزالة التكرار (أسهم) {len(union)} · بلا سعرٍ عند الإشارة/الارتكاز "
        f"{sum(1 for s in union if cls[s] is None)}")
    log("=" * 78)
    summary = {"from": d_from, "to": d_to, "sessions": len(days), "sessions_full": len(full), "watched": len(union),
               "pullback": len(pb_union), "raw_pairs": raw_pairs, "ext_ok": ext_ok, "classes": {}}
    for k in classes:
        ch = chain(per, union, k)
        q = sorted((s for s in union if sig[s] and klass(per[s][sig[s]]["px"]) == k), key=lambda s: sig[s])
        unk = sorted(s for s in union if not sig[s] and unknown_of(per[s]) and cls[s] == k)
        watched_k = sum(1 for s in union if cls[s] == k)
        log("")
        log(f"{LABEL[k]}")
        log("   🔗 " + " ⟵ ".join(f"{n} {c}" for n, c, _x in ch) + f" ⟵ المؤهّلة (بالإشارة الأولى) {len(q)}")
        diff = sorted(set(ch[-1][2]) ^ set(q))
        if diff:
            log(f"   ⚠️ اختلافُ السلسلة عن قاعدة الإشارة الأولى: {', '.join(diff)} (الفئةُ تُحسم بسعر الإشارة الأولى)")
        rows = []
        for s in q:
            r = per[s][sig[s]]
            o = outcome(adj_by[s], r["c"], sig[s], days[-1], mins_by.get(s), seen.get(s), now_utc)
            k_sessions = sum(1 for d in per[s] if three(per[s][d]["f"]) is True)
            rows.append((s, r, o, k_sessions))
            split_note = ""
            if r["px"] and o["c0"] and abs(o["c0"] / r["px"] - 1.0) > 0.01:
                split_note = f" · ⚠️ مسوًّى (تقسيمٌ لاحق ×{o['c0'] / r['px']:.2f})"
            log(f"   🎯 {s:6} إشارة {sig[s]} (إغلاق {r['c']}) · RSI {_fmt(r['rsi'], '{:.1f}')} · فلوت {_fmt(r['float'])} · "
                f"متاح {_fmt(r['avail'])} · سعر الإشارة ${_fmt(r['px'], '{:.3f}')} (خامّ) · جلساتُ المطابقة {k_sessions} · "
                f"أقصى صعودٍ بعدها {_pct(o['reg'])} ({o['reg_day'] or '—'} · أعلى {_fmt(o['reg_hi'], '{:.4g}')} مسوًّى) · "
                + (f"ممتدًّا {_pct(o['ext'])} ({WW._when(o['ext_ms']) if o['ext_ms'] else '—'} · أعلى "
                   f"{_fmt(o['ext_hi'], '{:.4g}')})" if ext_ok else "ممتدًّا: لا حكم")
                + f" · انفجر +50%: {'نعم' if (o['reg'] or -1e9) >= WW.EXPLODE[0] else 'لا'} نظاميًّا"
                + (f" · {'نعم' if (o['ext'] or -1e9) >= WW.EXPLODE[0] else 'لا'} ممتدًّا" if ext_ok else "")
                + f" · حالتُه: {WW.cont_label(last_entry[s])}{split_note}")
        if not q:
            log("   لا سهمَ مؤهّل")
        if unk:
            log(f"   ❔ مجهولٌ (شرطٌ غيرُ معلوم ولا شرطَ ساقط): {', '.join(unk)}")
        e50 = [x for x in rows if (x[2]["reg"] or -1e9) >= WW.EXPLODE[0]]
        e100 = [x for x in rows if (x[2]["reg"] or -1e9) >= WW.EXPLODE[1]]
        x50 = [x for x in rows if ext_ok and (x[2]["ext"] or -1e9) >= WW.EXPLODE[0]]
        x100 = [x for x in rows if ext_ok and (x[2]["ext"] or -1e9) >= WW.EXPLODE[1]]
        mean_r, med_r, max_r = stats([x[2]["reg"] for x in rows])
        mean_x, med_x, max_x = stats([x[2]["ext"] for x in rows]) if ext_ok else (None, None, None)
        # ── الارتداد (مجتمعٌ ثانٍ · الشورت مجهولٌ بالبناء) ──
        prow = []
        for s in pb_union:
            if not pper.get(s):
                continue
            hit = [d for d in sorted(pper[s]) if pper[s][d]["f"][0] is True and pper[s][d]["f"][1] is True
                   and klass(pper[s][d]["px"]) == k]
            first_two = next((d for d in sorted(pper[s]) if pper[s][d]["f"][0] is True and pper[s][d]["f"][1] is True), None)
            if not hit or hit[0] != first_two:
                continue
            r = pper[s][hit[0]]
            o = outcome(adj_by.get(s) or [], r["c"], hit[0], days[-1], mins_by.get(s), pseen.get(s), now_utc)
            prow.append((s, r, o, hit[0]))
            log(f"   🔁 {s:6} [ارتداد · {r.get('status') or '—'}] إشارةُ الثلاثة المعلومة {hit[0]} · RSI {_fmt(r['rsi'], '{:.1f}')} · "
                f"فلوت {_fmt(r['float'])} · المتاحُ مجهولٌ بالبناء · سعر ${_fmt(r['px'], '{:.3f}')} · أقصى صعودٍ {_pct(o['reg'])} "
                f"({o['reg_day'] or '—'})" + (f" · ممتدًّا {_pct(o['ext'])}" if ext_ok else ""))
        pb50 = sum(1 for x in prow if (x[2]["reg"] or -1e9) >= WW.EXPLODE[0])
        pbx50 = sum(1 for x in prow if ext_ok and (x[2]["ext"] or -1e9) >= WW.EXPLODE[0])
        rate = f"{len(e50)}/{len(q)} = {len(e50) / len(q) * 100:.1f}%" if q else "—"
        xrate = (f"{len(x50)}/{len(q)} = {len(x50) / len(q) * 100:.1f}%" if q else "—") if ext_ok else "لا حكم"
        log(f"   🏁 {k.upper()}: المراقَبة {watched_k} · المؤهّلة {len(q)} · انفجرت +50% نظاميًّا {rate} (و+100% {len(e100)}) · "
            f"شاملًا البري والأفتر {xrate}" + (f" (و+100% {len(x100)})" if ext_ok else "")
            + f" · متوسّطُ الحركة {_pct(mean_r)} · الوسيط {_pct(med_r)} · الأكبر {_pct(max_r)}"
            + (f" · ممتدًّا: {_pct(mean_x)} · {_pct(med_x)} · {_pct(max_x)}" if ext_ok else "")
            + f" · مجهول {len(unk)} · الارتداد: يستوفي الثلاثةَ المعلومة {len(prow)} بلغ منها +50% {pb50}"
            + (f" (ممتدًّا {pbx50})" if ext_ok else ""))
        summary["classes"][k] = {
            "watched": watched_k, "chain": [(c, n) for c, n, _x in ch], "chain_diff": diff, "qualified": len(q),
            "exploded_reg": len(e50), "exploded_reg100": len(e100), "exploded_ext": len(x50) if ext_ok else None,
            "exploded_ext100": len(x100) if ext_ok else None, "mean_reg": mean_r, "median_reg": med_r, "max_reg": max_r,
            "mean_ext": mean_x, "median_ext": med_x, "max_ext": max_x, "unknown": unk,
            "rows": [{"sym": s, "signal": sig[s], "c": r["c"], "rsi": r["rsi"], "float": r["float"], "avail": r["avail"],
                      "px": r["px"], "reg": o["reg"], "reg_day": o["reg_day"], "reg_hi": o["reg_hi"], "ext": o["ext"],
                      "ext_when": WW._when(o["ext_ms"]) if o["ext_ms"] else None, "ext_hi": o["ext_hi"], "k": kk}
                     for s, r, o, kk in rows],
            "pullback": [{"sym": s, "signal": d, "c": r["c"], "rsi": r["rsi"], "float": r["float"], "px": r["px"],
                          "reg": o["reg"], "reg_day": o["reg_day"], "ext": o["ext"]} for s, r, o, d in prow]}
    log("")
    log("JSON " + json.dumps(summary, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
