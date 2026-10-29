#!/usr/bin/env python3
"""🟠 قبولُ ⑤ لأداة «زخم الفيواب» الحيّة — الجولةُ الثانية (أوامرُ المالك 2026-10-29 بعد الجولة الأولى) · مولِّدٌ حتميٌّ بلا شبكة.

يقرأ مُخرَجات التشغيل المحفوظة في `vwap_live_research/` (كتبها الـworkflow على رنر وفرعِه) ⟵ `vwap_live_acceptance.md`.
`--check` يعيد التوليد ويقارن بايتًا (خروج 1 عند الاختلاف). **وصفٌ لا حكم:** الأرقامُ عدٌّ من الملفّات · وما بعد «استنتاج» أو «فرضيّة» موسوم ·
والتعريفُ T **معايَرٌ على مثال المصدر نفسِه** (AZTR) — حدُّ صدقٍ معلَن لا قياسٌ خارج العيّنة.
"""
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "vwap_live_research")
F = {
    "replay_v1": "replay_2026-10-28.json",            # الجولةُ الأولى: 3×3 الصارم · إغلاقُ الأمس الحرفيّ (‏`40860760895`)
    "replay_T": "replay_2026-10-28_T.json",
    "replay_M": "replay_2026-10-28_M.json",
    "trace_v1": "trace_AZTR_2026-10-26.json",         # ‏`40860757213`
    "trace_T": "trace_AZTR_2026-10-26_T.json",
    "trace_M": "trace_AZTR_2026-10-26_M.json",
    "mfic": "trace_MFIC_2026-10-27.json",
}
DOC = os.path.join(HERE, "vwap_live_acceptance.md")
HUG_PCT = 0.01
L_TOL = 0.95


def load(k):
    return json.load(open(os.path.join(RES, F[k]), encoding="utf-8"))


def _pct(x):
    return "؟" if x is None else f"{x * 100:+.0f}%"


def _arm(r):
    return "A" if r["arm"] == "A" else f"D#{r['n']}"


def _mod(hm):
    return int(hm[:2]) * 60 + int(hm[3:])


def l_parts(candles, end_ny):
    """مكوّناتُ ③ L لحدثٍ 5x3 من شموع trace (وصفٌ يطابق `vwap_momentum_live.liq5` — `VWL15` يتحقّق): فهرسُ شمعة الإكمال ·
    متوسّطُ دولار الثلاث · متوسّطُ ما قبلها (حتى ثلاث · المتاح) · وسيطُ الجلسة حتى الإكمال · إغلاقا الثالثة والأولى."""
    st = [c["s"] for c in candles]
    s_last = _mod(end_ny) - 5
    key = f"{s_last // 60:02d}:{s_last % 60:02d}"
    if key not in st:
        return None
    i = st.index(key)
    hold = [candles[k]["dv"] for k in (i - 2, i - 1, i)]
    prior = [candles[k]["dv"] for k in range(max(0, i - 5), i - 2)]
    return {"i": i, "hold": sum(hold) / 3.0, "prior": (sum(prior) / len(prior)) if prior else None, "n_prior": len(prior),
            "median": statistics.median([c["dv"] for c in candles[:i + 1]]), "c3": candles[i]["c"], "c1": candles[i - 2]["c"]}


def _alerts_line(alerts):
    return " · ".join(f"{_arm(a)} {a['event_end_ny']} ${a['px']} {_pct(a['chg'])}" for a in alerts) or "لا شيء"


def build():
    rv1, rT, rM = load("replay_v1"), load("replay_T"), load("replay_M")
    tv1, tT, tM, mf = load("trace_v1"), load("trace_T"), load("trace_M"), load("mfic")
    L = []
    w = L.append
    w("# 🟠 قبولُ ⑤ — أداةُ «زخم الفيواب» الحيّة · الجولةُ الثانية (قبل الكرون)")
    w("")
    w("> **مولَّدٌ** بـ`python3 vwap_live_acceptance.py` من ملفّات `vwap_live_research/` · `--check` يعيده بايتًا (`VWL15`).")
    w("> **أوامرُ المالك 2026-10-29 (الجولة الثانية):** «اعتمد آخر إغلاق للموقوف» · توقيتُ لقطة AZTR بالرياض (= النظاميّة) · ③ L يُعاد تعريفُه بأبسط صيغة "
      "تلتقط AZTR 11:05 وتُبقي رفض نمط القروبات — تعريفان وأثرُهما · الصناديقُ بكود SIC · وسما «📌 استحواذ نقدي» و«⏱️ قرب الإغلاق» عرضًا بلا رفض · "
      "**وشرطُ التفعيل: AZTR يُلتقَط (A ثمّ لمسات D).**")
    w("")
    a_T = tT.get("alerts") or []
    ok = bool(a_T) and a_T[0]["arm"] == "A" and any(a["arm"] == "D" for a in a_T)
    w("## ① الخلاصة")
    w("")
    w(f"- **شرطُ التفعيل: {'✅ مستوفى' if ok else '⛔ غيرُ مستوفى'}** — AZTR 2026-10-26 بتعريف الإنتاج T: {_alerts_line(a_T)}.")
    w(f"- **تعريفُ الإنتاج: T** (تسامحُ 5% مع المتاح) — يُجيز كسرَي A النظاميَّين (09:55 · 11:05) · و**M** (وسيطُ الجلسة) يُسقط 11:05 "
      f"وإن التقط AZTR بـA 09:55: {_alerts_line(tM.get('alerts') or [])}.")
    w("- ⚠️ **حدُّ صدق:** التسامحُ 5% والمقارنةُ بالمتاح **معايَرةٌ على مثال المصدر نفسِه** (AZTR 11:05 سقط بـ2%) — لا قياسَ خارج العيّنة يسندها ·"
      " والحكمُ الحقيقيّ في سجلّ الحصاد الأماميّ بعد 30 تنبيهًا.")
    w("")
    w("## ② التعريفان وأثرُهما")
    w("")
    w("| | الجولة 1 (3×3 صارم · إغلاقُ الأمس الحرفيّ) | **T** — متوسّطُ دولار الثلاث ≥ 0.95 × ما قبلها (المتاح) | M — متوسّطُ الثلاث ≥ وسيطِ الجلسة |")
    w("|---|---|---|---|")
    for d in rT["days"]:
        cnt = [sum(1 for a in r["alerts"] if a["date"] == d) for r in (rv1, rT, rM)]
        w(f"| {d} | {cnt[0]} | {cnt[1]} | {cnt[2]} |")
    tot = [len(r["alerts"]) for r in (rv1, rT, rM)]
    syms = [len({(a['date'], a['sym']) for a in r["alerts"]}) for r in (rv1, rT, rM)]
    w(f"| **المجموع** | {tot[0]} | **{tot[1]}** | {tot[2]} |")
    w(f"| رموزٌ/يوم | {syms[0]} | {syms[1]} | {syms[2]} |")
    w(f"| AZTR 10-26 | {_alerts_line(tv1.get('alerts') or [])} | {_alerts_line(a_T)} | {_alerts_line(tM.get('alerts') or [])} |")
    w(f"| نداءات · تعذّر | {rv1['calls']} · {rv1['fails']} | {rT['calls']} · {rT['fails']} | {rM['calls']} · {rM['fails']} |")
    w("")
    kT = {(a["date"], a["sym"], a["arm"], a["n"], a["event_end_ny"]) for a in rT["alerts"]}
    kM = {(a["date"], a["sym"], a["arm"], a["n"], a["event_end_ny"]) for a in rM["alerts"]}
    k1 = {(a["date"], a["sym"], a["arm"], a["n"], a["event_end_ny"]) for a in rv1["alerts"]}
    fmt = lambda ks: " · ".join(f"{s} {d[5:]} {('A' if arm == 'A' else 'D#' + str(n))} {t}" for d, s, arm, n, t in sorted(ks)) or "لا شيء"   # noqa: E731
    w(f"- **في T لا في الجولة 1:** {fmt(kT - k1)}")
    w(f"- **في الجولة 1 لا في T:** {fmt(k1 - kT)}")
    w(f"- **في T لا في M:** {fmt(kT - kM)} · **في M لا في T:** {fmt(kM - kT)}")
    w("- ورفضُ نمط القروبات («شمعتين يرتفع ويهبد») كما هو في التعريفين: إغلاقُ الثالثة ≥ إغلاقِ الأولى · و15د إغلاقٌ ≥ افتتاح.")
    w("")
    w("## ③ الإعادةُ الصامتة بتعريف الإنتاج T (‏10-22…10-28) — للمراجعة بالعين")
    w("")
    w("| الجلسة | مرشّحون | رموزٌ بكسر | أحداثُ كسر | كاملة | تنبيهات | بلا إغلاقٍ في المجمَّعة | حسمه آخرُ إغلاق | خلافُ الحلقة |")
    w("|---|---|---|---|---|---|---|---|---|")
    for d in rT["days"]:
        p = rT["per_day"][d]
        w(f"| {d} | {p['candidates']} | {p['symbols_with_breaks']} | {p['a_events']} | {p['a_full']} | {p['alerts']} | {p['no_prev_close']} | "
          f"{p.get('last_close_used', '؟')} | {p['loop_vs_full_mismatch']} |")
    w("")
    lc_al = sorted({(a["date"], a["sym"], a["prev_src"]) for a in rT["alerts"] if str(a.get("prev_src") or "").startswith("last_close ")})
    w("- **تنبيهاتٌ مرجعُ تغيّرها آخرُ إغلاقٍ لا مجمَّعةُ الأمس:** " + (" · ".join(f"{s_} {d[5:]} ({src.split(' ', 1)[1]})" for d, s_, src in lc_al)
                                                                       or "لا شيء")
      + " — وأغلبُ ما يحسمه آخرُ الإغلاق كلَّ يوم صناديقُ استحواذٍ ووحداتٌ بلا تداولٍ يوميّ (لا تبلغ الشروط).")
    w("")
    w("| # | الجلسة | الوقت | الرمز | الذراع | السعر | التغيّر | RVOL | الفيواب | SIC | الوسوم | مرجعُ التغيّر | الخبر |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(rT["alerts"], 1):
        w(f"| {i} | {r['date']} | {r['event_end_ny']} | {r['sym']} | {_arm(r)} | {r['px']} | {_pct(r['chg'])} | {r['rvol']} | {r['vwap']} | "
          f"{r.get('sic') or '—'} | {' · '.join(r.get('tags') or []) or '—'} | {r.get('prev_src') or '—'} | "
          f"{(r.get('news') or '—').replace('|', '/')} |")
    w("")
    hug = [r for r in rT["alerts"] if r["arm"] == "D" and r.get("vwap") and abs(r["px"] / r["vwap"] - 1.0) <= HUG_PCT]
    w(f"- **D يُكمل ملاصقًا للفيواب (ضمن {HUG_PCT * 100:.0f}% · وصفٌ لا شرط):** "
      + (" · ".join(f"{r['sym']} {r['date'][5:]} {_arm(r)} {r['event_end_ny']}" for r in hug) or "لا شيء") + ".")
    w("")
    w("## ④ AZTR 2026-10-26 — اللمساتُ الثلاث (توقيتُ الرياض = النظاميّة بإقرار المالك)")
    w("")
    w(f"إغلاقُ الأمس: **{tT.get('prev_src')}** = {tT.get('prev_adj')} (موقوفٌ بعده حتى العودة يومَ 10-26 بتقسيمٍ عكسيّ 10:1 · قبل الأمر كان «مجهولًا»).")
    w("")
    w("| كسرُ A | التغيّر | ③ متوسّطُ دولار الثلاث | ما قبلها (المتاح) | T: النسبة | وسيطُ الجلسة | M | الجولة 1 |")
    w("|---|---|---|---|---|---|---|---|")
    ev_m = {e["end_ny"]: e for e in tM.get("events") or []}
    for e in tT.get("events") or []:
        lp = l_parts(tT.get("candles") or [], e["end_ny"]) if e["kind"] == "5x3" else None
        if lp is None:
            w(f"| {e['end_ny']} ({e['kind']}) | {_pct(e['chg'])} | — | — | {'✅' if e['L'] else '⛔'} | — | "
              f"{'✅' if (ev_m.get(e['end_ny']) or {}).get('L') else '⛔'} | — |")
            continue
        ratio = None if lp["prior"] is None else lp["hold"] / lp["prior"]
        prior_s = "—" if lp["prior"] is None else "${:,.0f} ({} شموع)".format(lp["prior"], lp["n_prior"])
        ratio_s = "—" if ratio is None else "{:.3f}".format(ratio)
        t_ok = "✅" if e["L"] else "⛔"
        m_ok = "✅" if (ev_m.get(e["end_ny"]) or {}).get("L") else "⛔"
        w(f"| {e['end_ny']} ({e['kind']}) | {_pct(e['chg'])} | ${lp['hold']:,.0f} | {prior_s} | {ratio_s} {t_ok} | ${lp['median']:,.0f} | {m_ok} | ⛔ |")
    w("")
    w("| اللمسة | القاع | الفيواب | ثباتٌ بـL (T) | ثباتٌ بلا L |")
    w("|---|---|---|---|---|")
    for t in tT.get("touches") or []:
        h = t.get("d_hold") or {}
        a, b = h.get("with_L"), h.get("without_L")
        w(f"| {t['s']} | {t['low']} | {t['vwap']} | {a['end_ny'] + ' ' + a['kind'] if a else '—'} | {b['end_ny'] + ' ' + b['kind'] if b else '—'} |")
    w("")
    w("**وموجاتُ نايف الثلاث** («3 مرات السهم يعطيك على موجات وكل موجة ربحها قريب 50٪») في نافذة لقطته 11:00–14:00 نيويورك: الأداةُ بـT "
      "تُطلق D عند " + " · ".join(a["event_end_ny"] for a in a_T if a["arm"] == "D") + " (الموجةُ الأولى بدأت قبل نافذة اللقطة · A 09:55) — "
      "*مطابقةُ اللمسات بلمسات لقطته استنتاجٌ لا يُحسم إلّا بالصورة*.")
    w("")
    w("## ⑤ الصناديقُ بكود SIC — MFIC")
    w("")
    w(f"MFIC 2026-10-27: `sic` في EDGAR = «{mf.get('sic') or ''}» ⟵ **{'مستبعَد: ' + mf['excl'] if mf.get('excl') else 'لا كود ⟵ لا يُستبعد بالقاعدة'}** · "
      f"تنبيهاتُه بـT: {_alerts_line(mf.get('alerts') or [])}. **حدُّ صدق:** شركاتُ تطوير الأعمال (BDC) قد تُسجَّل بلا SIC فلا تلتقطها القائمة "
      "(6722 · 6726 · 6798) — ولا قاعدةَ جديدة بلا أمر.")
    w("")
    w("## ⑥ السويّةُ والأقفال والجذور")
    w("")
    w("- `VWL1`-`VWL18` (‏`VWL16` تعريفا L ومطابقةُ v2 بت-بت · `VWL17` آخرُ إغلاقٍ للموقوف · `VWL18` الصناديقُ والوسمان) · والطفراتُ كلُّها سقطت بقفلها "
      "(سوى واحدةٍ مكافئةٍ بالبناء: «ماذا لو» = القاعدة حين يُعتمد آخرُ الإغلاق) · والسويّةُ الكاملة معزولةٌ بخروج 0 قبل الدفع.")
    w("- `Super_stock.py` والجذورُ بت-بت · `vwap_mom_feas*.py` (أدواتُ المحور المُغلَق) بت-بت — تعريفُ L الجديد في الأداة الحيّة وحدَها.")
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
