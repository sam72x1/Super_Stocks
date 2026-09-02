#!/usr/bin/env python3
"""🌅🥇 `T-J1PM` — حصادٌ أماميّ لـ«J1 في البريماركت» (العقد `j1pm_prereg.md`).

قراءةٌ فقط · بلا كرون · بلا تلغرام · بلا كتابةِ حالة · والإنتاجُ لا يستوردها.
🔒 **مقياسٌ واحدٌ لا اثنان:** السجلُّ عبر `tier_fwd_report.load_ledger` · الشموعُ عبر
`tier_fwd_report.fetch_day` (‏`adjusted=false`) · والانفجارُ عبر `sym_day_probe.full_day_max`
و`exit_point` **بالاسم** — هي عينُ الدوالّ التي أنتجت أرقامَ `T-TIERLINK`.

الحكمُ لا يُطبَع قبل الأرضية (‏≥60 في `A` و≥150 مجمَّعًا) — «لا حكم» والعدّادان وحدَهما."""
import datetime as dt
import json
import os
import sys

from tier_fwd_report import fetch_day, load_ledger          # بالاسم
from sym_day_probe import full_day_max, exit_point           # بالاسم
from kasih_scan import NY, wilson                            # بالاسم

SINCE = os.environ.get("J1PM_SINCE", "2026-09-03")          # §② اليومُ التالي لدفع العقد
EXPL = 50.0                                                  # «انفجرت» ‏+50% (‏T-TIERLINK)
MIN_A, MIN_ALL = 60, 150                                     # §③-3
SEP = 2.0                                                    # §③-1


def is_pre(anchor_ms) -> bool:
    """`tod == "pre"` بتعريف `tierlink_probe` حرفيًّا: ساعةُ نيويورك قبل 09:30."""
    t = dt.datetime.fromtimestamp(float(anchor_ms) / 1000.0, tz=NY)
    return (t.hour + t.minute / 60.0) < 9.5


def classify(row) -> str:
    """`A` = J1 **و** بريماركت · وإلّا `Ā`. الصفُّ بلا `anchor_ms` ⇒ `?` (يُعَدّ ولا يُنسَب)."""
    try:
        if row.get("anchor_ms") is None:
            return "?"
        return "A" if (bool(row.get("j1")) and is_pre(row["anchor_ms"])) else "Ā"
    except (TypeError, ValueError):
        return "?"


def resolve(row, bars):
    """`exploded50` من سعر كرت `M5` (‏`e5`) على **يوم المِرساة كاملًا** بلا قصّ + الرفيق `mg_cut`."""
    try:
        e5 = float(row.get("e5") or 0)
        a_ms = int(row["anchor_ms"])
        if e5 <= 0 or not bars:
            return None
        card_ms = a_ms + 4 * 60_000
        mg_day, _ = full_day_max(bars, card_ms, e5)
        if mg_day is None:
            return None
        alow = row.get("anchor_low")
        _, ex_ms = exit_point(bars, card_ms, float(alow)) if alow else (None, None)
        if ex_ms:
            pre = [x for x in bars if card_ms < x[0] < ex_ms]
            mg_cut = max((x[2] / e5 - 1) * 100 for x in pre) if pre else 0.0
        else:
            mg_cut = mg_day
        return {"mg_day": mg_day, "mg_cut": mg_cut, "exploded50": mg_day >= EXPL}
    except (TypeError, ValueError, KeyError):
        return None


def judge(a_n, a_k, o_n, o_k, halves_ok):
    """§③ — يرجّع (حكم، أسطر). «لا حكم» قبل الأرضية."""
    if a_n < MIN_A or (a_n + o_n) < MIN_ALL:
        return ("لا حكم", [f"⏳ الأرضيةُ لم تُبلَغ: A={a_n}/{MIN_A} · الكلّ={a_n + o_n}/{MIN_ALL}"])
    ra, ro = a_k / a_n, (o_k / o_n if o_n else 0.0)
    la, ha = wilson(a_k, a_n)
    lo_, ho = wilson(o_k, o_n) if o_n else (0.0, 0.0)
    c1 = ra >= SEP * ro
    c2 = la > ho
    lines = [f"① ‏{ra*100:.1f}% مقابل {ro*100:.1f}% ⇒ {'✅' if c1 else '🔴'} (‏≥2×)",
             f"② Wilson A [{la*100:.0f}·{ha*100:.0f}] مقابل Ā [{lo_*100:.0f}·{ho*100:.0f}] ⇒ {'✅' if c2 else '🔴'}",
             f"③ الأرضية ✅ (A={a_n} · الكلّ={a_n + o_n})",
             f"④ النصفان ⇒ {'✅' if halves_ok else '🔴'}"]
    ok = c1 and c2 and halves_ok
    return ("عبرت" if ok else "فشلت", lines)


def main() -> int:
    key = os.environ.get("POLYGON_API_KEY", "")
    if not key:
        print("⛔ بلا POLYGON_API_KEY — لا قياس"); return 2
    rows = load_ledger()
    fwd = [r for r in rows if str(r.get("date") or "") >= SINCE]
    ins = [r for r in rows if str(r.get("date") or "") < SINCE]
    print(f"📒 السجلّ {len(rows)} صفًّا · أماميّ (منذ {SINCE}) {len(fwd)} · داخل العيّنة {len(ins)}")
    cache = {}

    def _bars(sym, day):
        k = (sym, day)
        if k not in cache:
            cache[k] = fetch_day(sym, day, key)
        return cache[k]

    def tally(rs, label):
        cnt = {"A": [0, 0], "Ā": [0, 0], "?": [0, 0]}; pend = 0; big_out = []
        per = []
        for r in rs:
            c = classify(r)
            o = resolve(r, _bars(r["symbol"], r["date"]))
            if o is None:
                pend += 1; continue
            cnt[c][0] += 1; cnt[c][1] += int(o["exploded50"])
            per.append((r["date"], c, o))
            if o["mg_day"] >= 150 and c != "A":
                big_out.append(f"{r['symbol']} {r['date']} +{o['mg_day']:.0f}%")
        a_n, a_k = cnt["A"]; o_n, o_k = cnt["Ā"]
        print(f"\n== {label} ==")
        print(f"A (J1∧بريماركت): {a_k}/{a_n} = {(a_k / a_n * 100) if a_n else 0:.1f}% · "
              f"Ā: {o_k}/{o_n} = {(o_k / o_n * 100) if o_n else 0:.1f}% · بلا وقت {cnt['?'][0]} · معلَّق/تعذّر {pend}")
        if big_out:
            print("   🔎 ‏≥+150% خارج A: " + " · ".join(big_out[:8]))
        return a_n, a_k, o_n, o_k, per

    tally(ins, "داخل العيّنة (مجتمع T-TIERLINK) — لا يحكم")
    a_n, a_k, o_n, o_k, per = tally(fwd, "أماميّ — الحاكم")
    # ④ النصفان
    halves_ok = False
    if per:
        per.sort(key=lambda x: x[0]); mid = len(per) // 2
        def _rate(sub, c):
            n = sum(1 for _, cc, _ in sub if cc == c); k = sum(o["exploded50"] for _, cc, o in sub if cc == c)
            return (k / n) if n else None
        h = [(_rate(per[:mid], "A"), _rate(per[:mid], "Ā")), (_rate(per[mid:], "A"), _rate(per[mid:], "Ā"))]
        halves_ok = all(a is not None and b is not None and a > b for a, b in h)
        print(f"   النصفان: {h}")
    verdict, lines = judge(a_n, a_k, o_n, o_k, halves_ok)
    print("\n🏁 الحكم (العقد §③): " + verdict)
    for ln in lines:
        print("   " + ln)
    print(json.dumps({"verdict": verdict, "A": [a_n, a_k], "Ā": [o_n, o_k], "since": SINCE},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
