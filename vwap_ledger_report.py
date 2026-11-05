#!/usr/bin/env python3
"""📋🟠 سجلُّ «زخم الفيواب» منذ الملحق 5 — قراءةٌ فقط (أمرُ المالك 2026-11-05 «اطبع سجل الفيواب منذ الملحق 5»).

لكلّ تنبيهٍ مُرسَلٍ بتعريف الملحق 5 (`def == "A5"`) من `vwap_live_ledger.jsonl`:
  الرمز · سعرُ التنبيه · أعلى سعرٍ بعده حتى الآن (دقائقُ Polygon من دقيقة التنبيه إلى اليوم — البري والنظاميّ والأفتر — مسوّاةً بالتقسيم
  إلى مقياس يوم التنبيه) · وهل أغلقت شمعةُ 5 دقائق تحت الفيواب بعده ومتى (`vwap_momentum_live.harvest` بالاسم: يومُ التنبيه وحدَه لأن
  الفيواب يُصفَّر كلَّ جلسة) · وموضعُ الرمز المُركَّز (`FOCUS` · DNUT) بين التنبيهات.

🔒 عرضٌ فقط: لا تلغرام · لا كتابةَ في السجلّ ولا في أيّ ملفّ · لا قاعدةَ ولا عتبة · والحكمُ على الأداة الحيّة للمالك بعد 30 تنبيهًا (عدٌّ بلا حكم).
"""
import datetime as dt
import os
import sys

import vwap_momentum_live as V

DEF_SINCE = "A5"                   # الملحق 5 (2026-10-31) — والتنبيهاتُ قبله (`def` غائب) خارج السجلّ المطلوب
FOCUS = "DNUT"                     # الرمزُ الذي سأل عنه المالك


def log(m=""):
    print(m, flush=True)


def a5_alerts(rows):
    """التنبيهاتُ المُرسَلة بتعريف الملحق 5 مرتّبةً زمنيًّا."""
    out = [r for r in rows if r.get("kind") == "alert" and r.get("sent") and r.get("def") == DEF_SINCE]
    return sorted(out, key=lambda r: (r["date"], r.get("event_end_mod") or 0, r["sym"], r.get("arm") or "", r.get("n") or 0))


def split_mult(splits, alert_day, day):
    """مضاعفُ تسوية سعر يومٍ لاحق إلى مقياس يوم التنبيه: Π split_to ÷ split_from لكلّ تقسيمٍ نُفِّذ بعد يوم التنبيه حتى ذلك اليوم
    (عكسيٌّ 10:1 ⟵ ‏0.1 · أماميٌّ 1:2 ⟵ ‏2)."""
    f = 1.0
    for ex, sf, stt in splits or ():
        if alert_day < ex <= day and sf and stt:
            f *= stt / sf
    return f


def session_of(m, op, cl):
    return "بري" if m < op else ("نظاميّ" if m < cl else "أفتر")


def max_after(by_day, alert_day, alert_mod, splits):
    """أعلى سعرٍ بعد التنبيه حتى آخر دقيقةٍ متاحة ⟵ (السعر بمقياس يوم التنبيه، اليوم، الدقيقة) أو None."""
    best = None
    for d in sorted(by_day or {}):
        if d < alert_day:
            continue
        f = split_mult(splits, alert_day, d)
        for b in by_day[d]:
            if d == alert_day and b[0] < alert_mod:
                continue
            h = b[2] * f
            if best is None or h > best[0]:
                best = (h, d, b[0])
    return best


def build(rows, minutes_of, splits_of, session_info):
    """صفوفُ التقرير — `minutes_of(sym, d_from)` ⟵ {يوم: دقائق} أو None · `splits_of(sym, d_from)` ⟵ ([(ex، sf، stt)]، مكتمل؟)."""
    al = a5_alerts(rows)
    hv = {r.get("of"): r for r in rows if r.get("kind") == "harvest"}
    first = {}
    for r in al:
        first.setdefault(r["sym"], r["date"])
    cache = {}
    out = []
    for r in al:
        sym, day, mod, px = r["sym"], r["date"], r.get("event_end_mod"), r.get("px")
        if sym not in cache:
            cache[sym] = (minutes_of(sym, first[sym]), splits_of(sym, first[sym]))
        by, (sp, sp_ok) = cache[sym]
        info = session_info(day) or {}
        op, cl = info.get("open_ny_min"), info.get("close_ny_min")
        row = {"date": day, "sym": sym, "arm": r.get("arm"), "n": r.get("n"), "alert_ny": r.get("event_end_ny"), "alert_mod": mod,
               "px": px, "key": r.get("key"), "split_ok": bool(sp_ok), "splits": [s for s in (sp or []) if s[0] > day]}
        if not by or op is None or cl is None or not px:
            row["status"] = "تعذّر"
            out.append(row)
            continue
        mx = max_after(by, day, mod, sp)
        row["status"] = "ok"
        if mx is not None:
            row.update(max_px=round(mx[0], 4), max_gain=round(mx[0] / px - 1.0, 4), max_day=mx[1], max_ny=V._hm(mx[2]),
                       max_session=session_of(mx[2], op, cl))
        bars = by.get(day) or []
        h = V.harvest(bars, op, cl, mod, px) if bars else {}
        row.update(exit_ny=h.get("exit_ny"), exit_px=h.get("exit_px"), ret_exit=h.get("ret_exit"),
                   at_close=bool(mod is not None and mod >= cl))
        led = hv.get(r.get("key"))
        row["harvest_match"] = None if led is None else (led.get("exit_ny") == h.get("exit_ny") and led.get("exit_px") == h.get("exit_px"))
        out.append(row)
    ranked = sorted((x for x in out if x.get("max_gain") is not None), key=lambda x: -x["max_gain"])
    for i, x in enumerate(ranked, 1):
        x["rank"] = i
    return out, len(ranked)


def _pct(x):
    return "—" if x is None else f"{x * 100:+.1f}%"


def render(out, n_ranked, today):
    """أسطرُ التقرير (Markdown) — كلُّ تنبيهٍ صفّ · والقصُّ يُعلَن · وDNUT قسمٌ في آخره."""
    L = [f"# 📋🟠 سجلُّ «زخم الفيواب» منذ الملحق 5 — حتى {today}", "",
         f"التنبيهاتُ المُرسَلة بتعريف `A5`: **{len(out)}** · مقيسةٌ {sum(1 for x in out if x['status'] == 'ok')} · "
         f"تعذّر {sum(1 for x in out if x['status'] != 'ok')}", "",
         "| # | اليوم | الرمز | الذراع | وقتُ التنبيه | سعرُ التنبيه | أعلى سعرٍ بعده حتى الآن | متى | إغلاقُ 5د تحت الفيواب (يومَ التنبيه) |",
         "|---|---|---|---|---|---|---|---|---|"]
    for i, x in enumerate(out, 1):
        if x["status"] != "ok":
            L.append(f"| {i} | {x['date']} | {x['sym']} | {x['arm']} | {x['alert_ny']} | ${x['px']} | تعذّرت الشموع | — | — |")
            continue
        sp = "" if x["split_ok"] else " ⚠️تقسيماتٌ تعذّرت"
        sp += "".join(f" ✂️{ex[5:]} {sf:g}:{stt:g}" for ex, sf, stt in x["splits"])
        mx = "—" if x.get("max_px") is None else f"${x['max_px']:g} ({_pct(x['max_gain'])}){sp}"
        when = "—" if x.get("max_day") is None else f"{x['max_day'][5:]} {x['max_ny']} {x['max_session']}"
        if x.get("at_close"):
            ex = "التنبيهُ عند الإغلاق — لا شمعةَ 5د نظاميّة بعده"
        elif x.get("exit_ny"):
            ex = f"نعم {x['exit_ny']} عند ${x['exit_px']:g} ({_pct(x['ret_exit'])})"
        else:
            ex = "لا — حتى إغلاق الجلسة"
        foc = " ⬅️" if x["sym"] == FOCUS else ""
        L.append(f"| {i} | {x['date'][5:]} | **{x['sym']}**{foc} | {x['arm']} | {x['alert_ny']} | ${x['px']:g} | {mx} | {when} | {ex} |")
    ok = [x for x in out if x["status"] == "ok"]
    gains = sorted(x["max_gain"] for x in ok if x.get("max_gain") is not None)
    exits = [x for x in ok if x.get("exit_ny")]
    closes = [x for x in ok if x.get("at_close")]
    if gains:
        med = gains[len(gains) // 2] if len(gains) % 2 else (gains[len(gains) // 2 - 1] + gains[len(gains) // 2]) / 2
        L += ["", f"**الوصف:** وسيطُ أعلى صعودٍ بعد التنبيه حتى الآن {_pct(med)} · بلغ ‏+20% فأكثر "
                  f"{sum(1 for g in gains if g >= 0.20)} من {len(gains)} · ولم يتجاوز سعرَ التنبيه {sum(1 for g in gains if g <= 0)} · "
                  f"أغلق 5د تحت الفيواب يومَ التنبيه {len(exits)} · ولم يُغلق تحته حتى الإغلاق {len(ok) - len(exits) - len(closes)} · "
                  f"تنبيهٌ عند الإغلاق {len(closes)}"]
    mm = [x for x in ok if x.get("harvest_match") is not None]
    L += [f"**التحقّق:** خروجُ 5د المحسوب هنا يطابق صفَّ الحصاد في السجلّ في {sum(1 for x in mm if x['harvest_match'])} من {len(mm)}"]
    foc = [x for x in out if x["sym"] == FOCUS]
    L += ["", f"## {FOCUS}"]
    if not foc:
        L.append(f"لا تنبيهَ لـ{FOCUS} في السجلّ منذ الملحق 5.")
    for x in foc:
        rk = f"المرتبة {x['rank']} من {n_ranked} بأعلى صعودٍ بعد التنبيه" if x.get("rank") else "بلا ترتيب (تعذّر)"
        L.append(f"- {x['date']} ذراع {x['arm']} عند {x['alert_ny']} بسعر ${x['px']:g} ⟵ أعلى بعده ${x.get('max_px', '—')} "
                 f"({_pct(x.get('max_gain'))}) {x.get('max_day', '')} {x.get('max_ny', '')} {x.get('max_session', '')} · {rk}")
    L += ["", "**حدودُ القراءة:** أعلى سعرٍ يشمل البري والأفتر (قد يكون في تداولٍ رقيق — العمودُ يسمّي الجلسة) · والصعودُ «حتى الآن» يكبر "
              "بعمر التنبيه (تنبيهُ 11-02 أُتيحت له أيّامٌ أكثر من تنبيه اليوم) · وإغلاقُ 5د تحت الفيواب يومَ التنبيه وحدَه (الفيواب يُصفَّر كلَّ جلسة) · "
              "عدٌّ بلا حكم."]
    return L


def main(argv=None):
    key = (os.environ.get("POLYGON_API_KEY") or "").strip()
    if not key:
        log("⛔ لا مفتاح Polygon — لا عمل (يُعلَن ولا يُكتَم)")
        return 2
    import market_calendar as MC
    net = V.Net(key, (os.environ.get("SEC_CONTACT") or "").strip())
    today = dt.datetime.now(tz=V.NY).date().isoformat()

    def minutes_of(sym, d0):
        return net.minutes(sym, d0, today)

    def splits_of(sym, d0):
        rows, ok = net.paged("/v3/reference/splits", {"ticker": sym, "execution_date.gt": d0, "limit": 1000})
        sp = [(str(r.get("execution_date")), float(r.get("split_from") or 0), float(r.get("split_to") or 0)) for r in rows or ()]
        return sp, ok

    out, n_ranked = build(V.read_ledger(), minutes_of, splits_of, MC.session_info)
    for ln in render(out, n_ranked, today):
        log(ln)
    log(f"\n🌐 نداءات Polygon {net.calls} · تعذّر {net.fails}")
    return 0 if all(x["status"] == "ok" for x in out) else 4


if __name__ == "__main__":
    sys.exit(main())
