#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🥇📅 **حصيلةُ التصنيف على جلسةٍ بعينها** — العقد `tier_days_prereg.md`
(مدفوعٌ قبل أيّ رقم).

يجيب سؤالَ المالك (‏2026-08-22): «كم عددُ الأسهم التي أعطيتَني تصنيفَها **قوي**
وواصلت، وعددُ التي **خسرت من التنبيه**، مع النسب» — على **ما أطلقه البوتُ حيًّا**
لا على السوق كلِّه.

⚖️ **قراءةٌ فقط:** لا يرسل ولا يكتب حالةً ولا يمسّ عتبة · والإنتاجُ لا يستورده.
🔒 **ومقياسٌ واحدٌ لا اثنان:** المِرساةُ من `kasih_scan.first_anchor` (وهي
`liq_stage_events` الإنتاجيّة بالنمط القانونيّ) · والحسمُ من `kasih_scan.resolve`
· والخصائصُ من `kasih2_scan.k2_features` · **والفئةُ من `Super_stock.liq_tier`
حرفيًّا** — صفرُ منطقٍ مكرّر.

⛔ **مِجَسٌّ وصفيٌّ لا اختبارُ فرضية** (‏§⓪ من العقد): التصنيفُ دائريٌّ بالإعلان
⇒ لا يُقرأ منه «يتنبّأ» ولا «لا يتنبّأ».
"""
import datetime as dt
import gzip
import json
import os
import statistics as st_

os.environ.setdefault("SCREENER_MODE", "BACKTEST")

import ah_scan as AH                                             # noqa: E402
import kasih_scan as KS                                          # noqa: E402
import kasih2_scan as K2                                         # noqa: E402
import Super_stock as S                                          # noqa: E402

FIRED_FILE = "tier_days_fired.json"
TIER_ORDER = ("قوي", "متوسط", "ضعيف", "بلا تصنيف")


def exit_price(rows, a_ms: int, anchor_low: float):
    """سعرُ الخروج البنيويّ (أوّلُ إغلاقِ دقيقةٍ دون قاع شمعة المِرساة) —
    أو إغلاقُ آخر شمعةٍ إن لم يقع (‏`eod`). يُرجع `(السعر، الطابع، وقع؟)`."""
    last = None
    for b in rows:
        t, _o, _h, _l, c, _v = b
        if t <= a_ms:
            continue
        last = (float(c), int(t))
        if c < anchor_low:
            return (float(c), int(t), True)
    return ((last[0], last[1], False) if last else (None, None, False))


def outcome(entry, mx_pct, ex_px, broke):
    """الحصيلةُ بتعريفات العقد §④ — **بلا تعريفٍ جديد**."""
    if entry is None or entry <= 0 or mx_pct is None:
        return ("تعذّر", None)
    if mx_pct >= KS.KASIH_PCT:
        return ("واصلت", mx_pct)
    if broke and ex_px:
        return ("خسرت", (ex_px / entry - 1.0) * 100.0)
    return ("معلّقة", (ex_px / entry - 1.0) * 100.0 if ex_px else None)


def true_e5(rows, a_ms: int, entry: float):
    """💵 **سعرُ كرت M5 حرفيًّا** — آخرُ إغلاقٍ قبل `المِرساة+5د` **بلا قطعٍ
    عند الخروج البنيويّ**.

    🔴 **ولماذا لا يكفي `entry_view.e5`:** حلقتُها تنكسر عند أوّل إغلاقٍ دون
    قاع المِرساة، فإن وقع الكسرُ في الدقيقة الثانية بقي `e5` **إغلاقَ الدقيقة
    الثانية** ومُنع تجميدُه ⇒ يُطبَع «سعرُ M5» وهو ليس كذلك، و`mg5` يعود
    `None` فيُقرأ «تعذّر» وهو **كسرٌ سابقٌ للخمس**. ⛔ ولا تُمَسّ `entry_view`
    (أرقامُ `kasih2` منشورةٌ عليها) — يُحسَب هنا للعرض وحده.

    يُرجع `(سعرُ الخمس، هل كُسر القاعُ قبل اكتمالها؟)`."""
    ab = next((b for b in rows if b[0] == a_ms), None)
    if ab is None or entry <= 0:
        return (None, False)
    alow, e5, broke5, seen = ab[3], entry, False, False
    for b in rows:
        t, _o, _h, _l, c, _v = b
        if t <= a_ms:
            continue
        if t >= a_ms + KS.ENTRY5_MIN * 60_000:
            break
        seen = True
        e5 = float(c)
        if c < alow:
            broke5 = True
    return ((e5 if seen else None), broke5)


def _med(xs):
    xs = [x for x in xs if x is not None]
    return round(st_.median(xs), 1) if xs else None


def main() -> int:                                               # noqa: C901
    if not (os.environ.get("AWS_ACCESS_KEY_ID") or "").strip():
        print("⛔ لا مفاتيح S3 — لا قياس (ولا يُخمَّن رقم).")
        return 2
    day = (os.environ.get("TIER_DAY") or "").strip()
    if not day:
        print("⛔ لا TIER_DAY.")
        return 2
    try:
        fired_all = json.load(open(FIRED_FILE, encoding="utf-8"))
    except Exception as e:                                       # noqa: BLE001
        print(f"⛔ تعذّرت قراءة {FIRED_FILE}: {type(e).__name__}: {e}")
        return 2
    fired = fired_all.get(day) or {}
    if not fired:
        print(f"⛔ لا مراسيَ مُطلَقةٌ مسجَّلةٌ ليوم {day} في {FIRED_FILE}.")
        return 4
    m5 = {s: v for s, v in fired.items() if "M5" in (v.get("sent") or [])}
    KS.log(f"🥇📅 حصيلةُ التصنيف — {day} · أُطلق {len(fired)} · "
           f"**بلغ M5 {len(m5)}** (المقامُ الحاكم، عقد §①)")

    seed = KS.weekdays((dt.date.fromisoformat(day)
                        - dt.timedelta(days=7)).isoformat(),
                       (dt.date.fromisoformat(day)
                        - dt.timedelta(days=1)).isoformat())[-3:]
    prev_close: dict = {}
    for sd in seed:
        k = AH.day_key(sd)
        mb, ep = AH.head_size_mb(k)
        if mb is None:
            continue
        dest = f"/tmp/tierd-{sd}.csv.gz"
        if not AH.download(k, dest, ep):
            continue
        try:
            with gzip.open(dest, "rt") as fh:
                _b, closes = KS.parse_day(fh, set())
            prev_close.update(closes)
            KS.log(f"🌱 بذرةُ إغلاق الأمس من {sd}: {len(closes):,} رمزًا")
        except (OSError, KeyError, ValueError) as e:             # noqa: BLE001
            KS.log(f"   ⛔ {sd}: {type(e).__name__}: {e}")
        finally:
            try:
                os.remove(dest)
            except OSError:
                pass
    if not prev_close:
        print("⛔ تعذّرت بذرةُ إغلاق الأمس ⇒ لا فجوةَ ⇒ لا توليفة ⇒ لا حكم.")
        return 3

    key = AH.day_key(day)
    mb, ep = AH.head_size_mb(key)
    if mb is None:
        print(f"⛔ ملفُّ {day} غيرُ متاح.")
        return 3
    dest = f"/tmp/tierd-{day}.csv.gz"
    if not AH.download(key, dest, ep):
        print(f"⛔ تعذّر تنزيلُ {day}.")
        return 3
    with gzip.open(dest, "rt") as fh:
        bars, _c = KS.parse_day(fh, set(m5))
    try:
        os.remove(dest)
    except OSError:
        pass

    rows_out, miss = [], []
    for sym in sorted(m5):
        b = bars.get(sym)
        if not b:
            miss.append((sym, "لا شموعَ في الملفّ"))
            continue
        e = KS.first_anchor(b)
        if e is None:
            miss.append((sym, "لم تُكشَف مِرساة"))
            continue
        a_ms, entry = int(e["anchor_ms"]), float(e["price"])
        pc = prev_close.get(sym)
        res = KS.resolve(b, a_ms, entry)
        if res is None:
            miss.append((sym, "تعذّر الحسم"))
            continue
        ev = K2.entry_view(b, a_ms, entry, pc)
        usd5 = KS.f2_usd5(b, a_ms)
        usd1 = float(e.get("usd") or 0)
        f2key = S._ignition_candle_class(usd5)[0]
        gap = (entry / pc - 1.0) * 100.0 if pc else None
        k2 = K2.k2_features(b, a_ms, entry, f2key, gap, usd1, usd5)
        # 🔴 **`kasih_j1` تقرأ `ev["class"]`** — وأوّلُ صياغةٍ لي مرّرت
        #    `anchor_cls` (مفتاحٌ لا وجود له) ⇒ J1 صفرٌ في 60 صفًّا وعمودٌ
        #    ميّت. صنفُ «المفتاحِ المتخيَّل» بعينه (‏wire-check §①).
        tev = {"stage": "M5", "k2": k2, "class": (f2key, ""),
               "anchor_price": entry, "prev_close": pc}
        t = S.liq_tier(tev)
        alow = float(res["anchor_low"])
        ex_px, ex_ms, broke = exit_price(b, a_ms, alow)
        e5, broke5 = true_e5(b, a_ms, entry)
        o1, p1 = outcome(entry, res.get("mg_after"), ex_px, broke)
        # 🔴 **قصورُ صياغةٍ في عقدي أُعلنه ولا أستفيد من غموضه** (‏§④ لم ينصّ
        #    على مَن يُكسَر قاعُه **قبل** اكتمال الخمس): `mg5` يعود `None`
        #    فيُقرأ «تعذّر». والنصُّ الحرفيّ للعقد «خسرت = خروجٌ بنيويٌّ دون
        #    بلوغ 30%» **ينطبق عليها**، فتُحسَب خسارةً وتُعَدّ **مُعلَنةً على
        #    حدة** — والقراءةُ تُصعّب على الفئة ولا تُسهّل.
        o5, p5 = outcome(e5, (ev or {}).get("mg5"), ex_px, broke)
        if o5 == "تعذّر" and broke and ex_px and e5:
            o5, p5 = "خسرت", (ex_px / e5 - 1.0) * 100.0
        live = fired[sym]
        drift = (None if not live.get("anchor_ms")
                 else round((a_ms - int(live["anchor_ms"])) / 60_000))
        rows_out.append({
            "sym": sym, "tier": (t[0] if t else "بلا تصنيف"),
            "green": (t[1] if t else None), "got": (t[2] if t else None),
            "j1": bool(S.kasih_j1(tev)[0]), "gap": gap, "f2": f2key,
            "broke5": bool(broke5),
            "live_k2": bool((fired.get(sym) or {}).get("k2")),
            "e1": entry, "e5": e5, "mg1": res.get("mg_after"),
            "mg5": (ev or {}).get("mg5"), "exit": res["exit"],
            "ex_px": ex_px, "o1": o1, "p1": p1, "o5": o5, "p5": p5,
            "drift": drift, "k100": res.get("kasih100"),
            "k50": res.get("kasih50")})

    print("\n" + "=" * 78)
    print(f"🥇📅 حصيلةُ التصنيف — {day} · العقد tier_days_prereg.md "
          "(مدفوعٌ قبل أيّ رقم)")
    print("=" * 78)
    print(KS.MEASURE_CUT_NOTE)          # ✂️ مصدرٌ واحد — لا نسخةَ نصٍّ هنا
    print(f"📥 أُطلق {len(fired)} · بلغ M5 **{len(m5)}** · قِيس "
          f"{len(rows_out)} · تعذّر {len(miss)}")
    for s, why in miss:
        print(f"   ⛔ {s}: {why}   (يُسمّى ولا يُطوى — عقد §⑥-5)")

    print("\n" + "-" * 78)
    print("① جدولُ كلّ سهمٍ بالاسم (بلا قصّ) — الحاكمُ سعرُ M5")
    print("-" * 78)
    hdr = (f"{'رمز':<7}{'الفئة':<8}{'مواصلة':<8}{'J1':<4}{'فجوة%':>7}"
           f"{'M1':>8}{'M5':>8}{'أقصى5%':>8}{'الحصيلة':<9}{'نسبة5%':>8}"
           f"{'خروج':<7}{'انزياح':>7}")
    print(hdr)
    for r in sorted(rows_out, key=lambda x: (TIER_ORDER.index(x["tier"]),
                                             -(x["mg5"] or -999))):
        cnt = f"{r['green']}/{r['got']}" if r["got"] else "—"
        j1s = "✅" if r["j1"] else "—"
        gp = f"{r['gap']:.0f}" if r["gap"] is not None else "—"
        e5s = f"{r['e5']:.4f}" if r["e5"] else "—"
        mg = f"{r['mg5']:.1f}" if r["mg5"] is not None else "—"
        pp = f"{r['p5']:+.1f}" if r["p5"] is not None else "—"
        dr = f"{r['drift']:+d}د" if r["drift"] is not None else "—"
        if r.get("broke5"):
            dr = "🔻" + dr
        if not r.get("live_k2"):
            dr = "♻️" + dr        # ♻️ = تصنيفٌ مُعادُ البناء لا حيّ
        print(f"{r['sym']:<7}{r['tier']:<8}{cnt:<8}{j1s:<4}{gp:>7}"
              f"{r['e1']:>8.4f}{e5s:>8}{mg:>8}{r['o5']:<9}{pp:>8}"
              f"{r['exit']:<7}{dr:>7}")

    print("\n" + "-" * 78)
    print("② التجميعُ لكلّ فئة (سعرُ M5 — التصنيفُ يصل عنده)")
    print("-" * 78)
    print(f"{'الفئة':<10}{'العدد':>6}{'واصلت':>7}{'خسرت':>7}{'معلّقة':>7}"
          f"{'تعذّر':>7}{'%واصلت':>8}{'وسيطُ أقصى%':>12}{'وسيطُ الخسارة%':>15}")
    for tk in TIER_ORDER:
        g = [r for r in rows_out if r["tier"] == tk]
        if not g:
            continue
        w = [r for r in g if r["o5"] == "واصلت"]
        l_ = [r for r in g if r["o5"] == "خسرت"]
        p = [r for r in g if r["o5"] == "معلّقة"]
        u = [r for r in g if r["o5"] == "تعذّر"]
        n_res = len(w) + len(l_)
        pct = f"{100 * len(w) / n_res:.0f}%" if n_res else "—"
        # 🔴 **السلّةُ الرابعة تُطبَع** — كانت تُحتسَب في «العدد» ولا تظهر في
        #    أيّ عمودِ حصيلة ⇒ الصفُّ لا يتوازن = **قصٌّ صامت** (كشفه تدقيقٌ
        #    خصوميّ 2026-08-22). ومقلوبُ مبدأ الأداة نفسِها التي تُسمّي كلَّ
        #    متعذّرٍ في `miss` بسببه.
        print(f"{tk:<10}{len(g):>6}{len(w):>7}{len(l_):>7}{len(p):>7}{len(u):>7}"
              f"{pct:>8}{str(_med([r['mg5'] for r in g])):>12}"
              f"{str(_med([r['p5'] for r in l_])):>15}")
    tot = rows_out
    w = [r for r in tot if r["o5"] == "واصلت"]
    l_ = [r for r in tot if r["o5"] == "خسرت"]
    print(f"{'المجموع':<10}{len(tot):>6}{len(w):>7}{len(l_):>7}"
          f"{len([r for r in tot if r['o5'] == 'معلّقة']):>7}"
          f"{len([r for r in tot if r['o5'] == 'تعذّر']):>7}")

    _b5 = [r for r in tot if r.get("broke5")]
    print(f"\n🔻 **كُسر قاعُ المِرساة قبل اكتمال الخمس: {len(_b5)}** "
          f"(‏{', '.join(r['sym'] for r in _b5) or 'لا شيء'}) — وسمُ M5 يصل "
          "**بعد** الخروج البنيويّ ⇒ تُحسَب «خسرت» بنصّ العقد §④ حرفيًّا، "
          "وتُعلَن هنا لأن العقدَ لم ينصّ عليها (قصورُ صياغةٍ منّي).")
    for _t in TIER_ORDER:
        _g = [r for r in _b5 if r["tier"] == _t]
        if _g:
            print(f"   ↳ {_t}: {len(_g)}")

    print("\n③ وصفيّاتٌ تُنشَر ولا تحكم: "
          f"بلغ +50% ⟶ {sum(1 for r in tot if r['k50'])} · "
          f"+100% ⟶ {sum(1 for r in tot if r['k100'])}")
    print("\n⚠️ حدودُ صدقٍ (عقد §⑥) — تُقرأ **مع** الأرقام لا بعدها:")
    print("   1) العيّنةُ آحادٌ لكلّ فئة ⇒ فواصلُ ويلسون هائلة ⇒ لا قرارَ إحصائيّ.")
    print("   2) الدائريّةُ مُعلَنة: التصنيفُ وصفٌ لا تنبّؤ (‏§⓪).")
    print("   3) «واصلت» **لمسُ سعرٍ** لا صفقةٌ منفَّذة (بلا انزلاقٍ ولا حجم).")
    print("   4) يومان متجاوران ⇒ سوقٌ واحدٌ لا تعميم.")
    print("   5) «انزياح» = فرقُ مِرساة الأداة عن الحيّة بالدقائق (يُطبَع لا يُخفى).")
    # 🔴🔴 **أثقلُ حدٍّ — صُحِّح 2026-08-22 بتدقيقٍ خصوميّ:** كان مغروسًا يقول
    #    «‏08-20 مقامُه أصغر» **والمقيسُ يكذّبه** (‏37 مقابل 23). والحقيقةُ
    #    أعمق: `k2` (حاملُ التصنيف) شُحن **‏08-20 ‏06:33** و`liq_tier` ‏13:10
    #    ⇒ صفوفٌ سبقتهما **بلا تصنيفٍ حيٍّ إطلاقًا**، والأداةُ تُعيد بناءه
    #    **بأثرٍ رجعيّ** ⇒ يُحسَب ويُطبَع لكلّ يومٍ بلا غرسِ تاريخ.
    _lv = sum(1 for s_ in m5 if (fired.get(s_) or {}).get("k2"))
    print(f"   6) 🔴 **تصنيفٌ حيٌّ في {_lv} من {len(m5)} فقط** — والباقي "
          "يُعاد بناؤه **بأثرٍ رجعيّ** من دقائق Polygon (‏`k2` شُحن 08-20 "
          "‏06:33 و`liq_tier` ‏13:10) ⇒ **ليس ما رآه المالكُ موسومًا**.")
    print("   7) 🔻 = كُسر القاعُ قبل الخمس ⇒ «سعرُ M5» فيها إغلاقُ الدقيقة "
          "الرابعة **بعد** كسرٍ واقع ⇒ دخولٌ ورقيٌّ لا يُشترى.")
    with open(f"tier_days_{day}.jsonl", "w", encoding="utf-8") as fo:
        for r in rows_out:
            fo.write(json.dumps(r, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
