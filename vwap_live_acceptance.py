#!/usr/bin/env python3
"""🟠 قبولُ ⑤ لأداة «زخم الفيواب» الحيّة (أمرُ المالك 2026-10-29) — مولِّدٌ حتميٌّ بلا شبكة.

يقرأ مُخرَجَي التشغيل المحفوظين (`vwap_live_research/replay_<آخر جلسة>.json` و`trace_AZTR_2026-10-26.json` — كتبهما الـworkflow على
رنر) ⟵ `vwap_live_acceptance.md`. `--check` يعيد التوليد ويقارن بايتًا (خروج 1 عند الاختلاف). **وصفٌ لا حكم:** الأرقامُ عدٌّ من الملفّين
وما بعد «استنتاج» أو «فرضيّة» موسومٌ بذلك — والكرونُ لا يُفعَّل إلّا بموافقة المالك على هذه الوثيقة.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "vwap_live_research")
REPLAY = os.path.join(RES, "replay_2026-10-28.json")
TRACE = os.path.join(RES, "trace_AZTR_2026-10-26.json")
DOC = os.path.join(HERE, "vwap_live_acceptance.md")
HUG_PCT = 0.01          # «يلامس الفيواب»: سعرُ الإكمال ضمن 1% منه — وصفٌ لا شرط (هندسيّ · `RETEST_TOL` نفسُه)
PIN_MIN = 3             # «سعرٌ ثابت»: ثلاثُ تنبيهاتٍ فأكثر للرمز في اليوم بسعر إكمالٍ واحد


def _pct(x):
    return "؟" if x is None else f"{x * 100:+.0f}%"


def _arm(r):
    return "A" if r["arm"] == "A" else f"D#{r['n']}"


def concerns(rp):
    """ملاحظاتٌ للعين مشتقّةٌ من الأرقام وحدَها: D تلامس الفيواب · إكمالٌ عند الجرس · سعرٌ ثابت عبر تنبيهات الرمز."""
    al = rp["alerts"]
    hug = [r for r in al if r["arm"] == "D" and r.get("vwap") and abs(r["px"] / r["vwap"] - 1.0) <= HUG_PCT]
    bell = [r for r in al if r["event_end_ny"] == "16:00"]
    by = {}
    for r in al:
        by.setdefault((r["date"], r["sym"]), []).append(r)
    pins = [(k, v) for k, v in by.items() if len(v) >= PIN_MIN and len({x["px"] for x in v}) == 1]
    return hug, bell, pins


def _mod(hm):
    return int(hm[:2]) * 60 + int(hm[3:])


def liq_parts(candles, end_ny):
    """مكوّناتُ ③ L لحدثٍ 5x3 من شموع trace: (فهرسُ شمعة الإكمال، الدولارُ الآن، الدولارُ قبلها، إغلاقُ الثالثة، إغلاقُ الأولى) —
    نسخةٌ وصفيّة لـ`vwap_mom_feas.liq_ok` على الأرقام المطبوعة (`VWL15` يطابقها بها)."""
    st = [c["s"] for c in candles]
    s_last = _mod(end_ny) - 5
    key = f"{s_last // 60:02d}:{s_last % 60:02d}"
    if key not in st:
        return None
    i = st.index(key)
    if i < 5:
        return {"i": i, "now": None, "before": None}
    now = sum(candles[k]["dv"] for k in (i - 2, i - 1, i))
    before = sum(candles[k]["dv"] for k in (i - 5, i - 4, i - 3))
    return {"i": i, "now": now, "before": before, "c3": candles[i]["c"], "c1": candles[i - 2]["c"]}


def hypo_d_chain(touches, after_ny, chg_min=0.20, px_max=20.0, px_min=1.0, cap=3):
    """«لو كان A كاملًا عند `after_ny`» ⟵ سلسلةُ D من جدول اللمسات (ثباتٌ بـL بعد أوّل لمسةٍ تبدأ عند الحدّ أو بعده) حتى `cap` —
    وصفٌ لتعريف الملحق 3 (`evaluate`) على أرقام trace، لا تنبيهٌ ولا قاعدة."""
    out, after = [], _mod(after_ny)
    while len(out) < cap:
        t = next((x for x in touches if _mod(x["s"]) >= after), None)
        if t is None or not (t.get("d_hold") or {}).get("with_L"):
            break
        h = t["d_hold"]["with_L"]
        if px_min <= h["px"] < px_max and h.get("chg_last_close") is not None and h["chg_last_close"] >= chg_min:
            out.append({"touch": t["s"], **h})
        after = _mod(h["end_ny"])
    return out


def build():
    rp = json.load(open(REPLAY, encoding="utf-8"))
    tr = json.load(open(TRACE, encoding="utf-8"))
    L = []
    w = L.append
    w("# 🟠 قبولُ ⑤ — أداةُ «زخم الفيواب» الحيّة (قبل أيّ كرون)")
    w("")
    w("> **مولَّدٌ** بـ`python3 vwap_live_acceptance.py` من ملفَّي التشغيل في `vwap_live_research/` (replay ‏`40860760895` · trace ‏`40860757213` · "
      "كلاهما 2026-10-29 على الفرع) · `--check` يعيده بايتًا (`VWL15`).")
    w("> **الحالة: بلا كرون ولا تلغرام** — التفعيلُ بموافقة المالك وحدَها (أمرُه ⑤). الأداةُ بقواعد الملحق 3 بالحرف وقراراتِ المالك الأربعة")
    w("> (D_MIN ‏250 ألف · السعرُ من 1.00 · RVOL من 04:00 · المتأخّرُ أكثرَ من 10 دقائق لا يُرسَل ويُسجَّل).")
    w("")
    al = rp["alerts"]
    na = sum(1 for r in al if r["arm"] == "A")
    w("## ① الإعادةُ الصامتة على آخر 5 جلسات مكتملة")
    w("")
    w(f"الجلسات: {' · '.join(rp['days'])} · **التنبيهاتُ التي كانت ستُرسَل: {len(al)}** (A ‏{na} · D ‏{len(al) - na}) · "
      f"نداءات Polygon/SEC {rp['calls']} · تعذّر {rp['fails']}.")
    w("")
    w("| الجلسة | مرشّحون | رموزٌ بكسر | أحداثُ كسر | كاملة | تنبيهات | عاديٌّ بلا إغلاق أمس | خلافُ الحلقة |")
    w("|---|---|---|---|---|---|---|---|")
    for d in rp["days"]:
        p = rp["per_day"].get(d) or {}
        if not p.get("ok"):
            w(f"| {d} | ⛔ {' · '.join(p.get('why') or [])} | | | | | | |")
            continue
        w(f"| {d} | {p['candidates']} | {p['symbols_with_breaks']} | {p['a_events']} | {p['a_full']} | {p['alerts']} | "
          f"{p.get('no_prev_close', '؟')} | {p['loop_vs_full_mismatch']} |")
    w("")
    w("**كلُّ تنبيهٍ كان سيُرسَل** (وقتُ إكمال الشمعة بتوقيت نيويورك · السعرُ إغلاقُها · التغيّرُ عن إغلاق الأمس المسوّى):")
    w("")
    w("| # | الجلسة | الوقت | الرمز | الذراع | السعر | التغيّر | RVOL | الفيواب | الخبر |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(al, 1):
        w(f"| {i} | {r['date']} | {r['event_end_ny']} | {r['sym']} | {_arm(r)} | {r['px']} | {_pct(r['chg'])} | "
          f"{r['rvol']} | {r['vwap']} | {(r.get('news') or '—').replace('|', '/')} |")
    w("")
    hug, bell, pins = concerns(rp)
    w("### ملاحظاتٌ للمراجعة بالعين (مشتقّةٌ من الأرقام · التفسيرُ موسوم)")
    w("")
    w(f"- **سعرٌ ثابتٌ عبر {PIN_MIN} تنبيهاتٍ فأكثر للرمز:** "
      + (" · ".join(f"{s} {d} ({len(v)} تنبيهات على {v[0]['px']})" for (d, s), v in pins) or "لا شيء")
      + " — *فرضيّة:* سهمُ صفقة استحواذٍ مثبَّتُ السعر (8-K بند 1.01) — الحركةُ لا تتحرّك فلا موجة.")
    w(f"- **D يُكمل ملاصقًا للفيواب (ضمن {HUG_PCT * 100:.0f}%):** "
      + (" · ".join(f"{r['sym']} {r['date']} {_arm(r)} {r['event_end_ny']}" for r in hug) or "لا شيء")
      + " — تعريفُ D (الملحق 2 §②) لا يشترط ابتعادًا ولا عتبةَ ابتعادٍ تُخترع ⟵ يُذكر ولا يُصلَح.")
    w("- **إكمالٌ عند الجرس 16:00:** "
      + (" · ".join(f"{r['sym']} {r['date']} {_arm(r)}" for r in bell) or "لا شيء")
      + " — الشمعةُ تُغلق مع الجلسة فيصل التنبيهُ بعد انتهاء النظاميّة (‏≈16:00:25).")
    w("- **النوع:** المرجعُ يسمّي بعضَ صناديق الاستثمار المغلقة/BDC «CS» (مثالُ الإعادة: MFIC) ⟵ لا تُستبعد بالنوع — *استنتاجٌ قويّ* من "
      "اسم الشركة لا من حقلٍ في Polygon.")
    near = rp.get("near") or []
    miss = {}
    for r in near:
        miss[r["missing"]] = miss.get(r["missing"], 0) + 1
    npc = [rp["per_day"][d].get("no_prev_close") for d in rp["days"] if rp["per_day"].get(d, {}).get("ok")]
    w(f"- **رموزٌ عاديّةٌ بلا إغلاق أمسٍ في المجمَّعة:** {' · '.join(str(x) for x in npc)} في الجلسات الخمس (سعرُ اليوم من 1 إلى ما دون 20) — "
      "أغلبُ أسمائها صناديقُ استحواذٍ ووحداتٌ بلا تداولٍ يومي · ومنها كلُّ سهمٍ موقوفٍ عاد (AZTR) ⟵ لا يدخل المرشِّحَ أبدًا.")
    w(f"- **القريبون (شرطٌ واحدٌ ناقص):** {len(near)} حدثًا · " + " · ".join(f"{k} {v}" for k, v in sorted(miss.items(), key=lambda x: -x[1]))
      + " — الخبرُ هو الشرطُ الحاكم الأكثر (حدُّ صدق ④: PRNewswire/Business Wire/Accesswire غائبة عن Polygon).")
    w("")
    w("## ② اختبارُ المثال: AZTR جلسة 2026-10-26")
    w("")
    pd_ = tr.get("prev_diag") or {}
    lc = tr.get("last_close") or {}
    daily = pd_.get("daily") or []
    w(f"**ما التقطته الأداة: {len(tr.get('alerts') or [])} تنبيه.** لمساتُ الفيواب في النظاميّة {len(tr.get('touches') or [])} · "
      f"أحداثُ كسر A {len(tr.get('events') or [])}.")
    w("")
    w("**لماذا — السببُ الأوّل (بيانات · مؤكَّد من Polygon):** إغلاقُ الأمس غائبٌ عن المجمَّعة "
      f"({pd_.get('prev_session')} · {pd_.get('grouped_symbols')} رمزًا بلا AZTR) ⟵ ① «مجهول». "
      f"شموعُ AZTR اليوميّة في النافذة: {' · '.join(str(x['d']) + ' ' + str(x['c']) for x in daily)} ⟵ **لا تداولَ من بعد "
      f"{lc.get('d', '؟')} حتى عودته يومَ 2026-10-26** · والتقسيماتُ: {pd_.get('splits')} (عكسيّ 10:1 يومَ العودة).")
    w("")
    w("| حدثُ الكسر | السعر | ① بالقاعدة | ما سقط | ③ L: دولارُ الشموع الثلاث · الثلاث قبلها |")
    w("|---|---|---|---|---|")
    for e in tr.get("events") or []:
        lp = liq_parts(tr.get("candles") or [], e["end_ny"]) if e["kind"] == "5x3" else None
        lq = ("—" if lp is None else (f"لا ستَّ شموعٍ نظاميّة قبله (شمعةُ الإكمال رقم {lp['i'] + 1} من الافتتاح) ⟵ L غيرُ ممكنٍ بالبناء"
                                     if lp["now"] is None else f"${lp['now']:,.0f} · ${lp['before']:,.0f} ({lp['now'] / lp['before'] - 1:+.1%})"))
        w(f"| {e['end_ny']} ({e['kind']}) | {e['px']} | {_pct(e['chg'])} | {' · '.join(e['why'])} | {lq} |")
    w("")
    wf = tr.get("whatif_last_close")
    if wf and lc:
        w(f"**«ماذا لو» — وصفٌ لا قاعدة:** لو عُدّ «إغلاقُ الأمس» آخرَ إغلاقٍ قبل اليوم ({lc['d']} · {lc['c']} × عاملُ التقسيم "
          f"{lc['split_factor']:g} = {lc['adj']:.4f}) لكانت التنبيهات {len(wf['alerts'])}"
          + (": " + " · ".join(f"{_arm(a)} {a['end_ny']} ${a['px']} {_pct(a['chg'])}" for a in wf["alerts"]) if wf["alerts"] else "")
          + " · وأحداثُ الكسر: " + " · ".join(f"{e['end_ny']} {_pct(e['chg'])} ⟵ {' · '.join(e['why']) or 'كامل'}" for e in wf["events"]) + ".")
        w("")
    evs = tr.get("events") or []
    if evs and lc:
        ch = hypo_d_chain(tr.get("touches") or [], evs[0]["end_ny"])
        w(f"**«ماذا لو كان A الأوّل ({evs[0]['end_ny']}) كاملًا» — وصفٌ لا قاعدة:** سلسلةُ D بتعريف الملحق 3 كانت ستكون "
          + (" · ".join(f"D#{k} عند {d['end_ny']} (لمسة {d['touch']} · ${d['px']} · {_pct(d['chg_last_close'])})" for k, d in enumerate(ch, 1))
             or "فارغة") + ".")
        w("")
    w("**اللمسات وثباتُ D بعد كلّ لمسة** (اللمسةُ = قاعُ شمعة 5د حتى 1.01 × الفيواب · الثباتُ بتعريف D: ثلاثُ إغلاقاتٍ فوقه أو شمعةُ 15 فوقه · "
      "«بـL» = مع شرط السيولة):")
    w("")
    w("| اللمسة | القاع | الفيواب | ثباتٌ بـL | ثباتٌ بلا L | التغيّرُ بآخر إغلاق |")
    w("|---|---|---|---|---|---|")
    for t in tr.get("touches") or []:
        h = t.get("d_hold") or {}
        a, b = h.get("with_L"), h.get("without_L")
        w(f"| {t['s']} | {t['low']} | {t['vwap']} | {a['end_ny'] + ' ' + a['kind'] if a else '—'} | "
          f"{b['end_ny'] + ' ' + b['kind'] if b else '—'} | {_pct((a or b or {}).get('chg_last_close'))} |")
    w("")
    ext = tr.get("ext") or {}
    w(f"**خارج النظاميّة (VWAP من 04:00 · خارج نطاق الأداة بتعريف ①):** لمسات {len(ext.get('touches_outside_regular') or [])} · "
      f"كسور {len(ext.get('breaks_outside_regular') or [])}.")
    w("")
    w("**الحكمُ على المثال (عدٌّ لا رأي):** الأداةُ **لم تلتقط شيئًا** من لمسات AZTR — والسببان بالترتيب: ① إغلاقُ الأمس مجهولٌ لسهمٍ موقوفٍ "
      "عاد بتقسيم · ثمّ ③ L سقط في حدثَي الكسر النظاميَّين معًا (الأوّلُ قبل أن تكتمل ستُّ شموعٍ من الافتتاح · والثاني بفارقٍ صغيرٍ في الدولار) "
      "⟵ ولا D بلا A كاملٍ قبله (تعريفُ الملحق 3) · **ولو اكتمل A الأوّل (إغلاقُ أمسٍ معلوم ‏+ L) لالتقطت D الثلاث** كما في السطر أعلاه.")
    w("")
    w("⚠️ **حدُّ صدقٍ في المثال نفسِه:** دفترُ المصادر سجّل محورَ وقت لقطة نايف «18:00–21:00» ونسبه للجلسة الممتدّة · وإن كانت اللقطةُ "
      "بتوقيت الرياض فهي **11:00–14:00 نيويورك = النظاميّة** (فرقُ 7 ساعات قبل 2026-11-01) — *فرضيّةٌ محتملة* لا تُحسم إلّا بالصورة.")
    w("")
    w("## ③ السويّةُ والأقفال والجذور")
    w("")
    w("- أقفالُ `VWL1`-`VWL15` (كلُّ شرطٍ من ① بقفلٍ سلوكيّ وطفرةٍ تُسقطه) · والسويّةُ الكاملة في شجرةٍ معزولة بخروج 0 قبل الدفع.")
    w("- `Super_stock.py` والجذورُ الاثنا عشر بت-بت (الأداةُ تستورد الإرسالَ والحفظ وحدَهما) · والقائمةُ و«تحت المتابعة» لا تُمَسّ.")
    w("")
    return "\n".join(L) + "\n"


def main(argv):
    txt = build()
    if "--check" in argv:
        cur = open(DOC, encoding="utf-8").read() if os.path.exists(DOC) else ""
        if cur != txt:
            print("⛔ vwap_live_acceptance.md لا يطابق المولِّد")
            return 1
        print("✅ vwap_live_acceptance.md مطابق")
        return 0
    with open(DOC, "w", encoding="utf-8") as f:
        f.write(txt)
    print(f"✅ كُتب {DOC}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
