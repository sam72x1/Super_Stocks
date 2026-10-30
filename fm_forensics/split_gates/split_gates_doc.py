# -*- coding: utf-8 -*-
"""🧮🔬 `T-SPLITGATES` — مولّدُ وثيقة النتيجة من ملفّي البيانات المحفوظين (حتميّ · بلا شبكة).

    python3 fm_forensics/split_gates/split_gates_doc.py          ⟵ يكتب SPLIT_GATES_RESULT.md
    python3 fm_forensics/split_gates/split_gates_doc.py --check  ⟵ يعيد التوليد ويقارن بايتًا (خروج 1 عند الاختلاف)

المدخلان: `data/units_eval.json` (② · RESULT_JSON لتشغيلة units_eval) و`data/pop_result.json` (③④ · RESULT_JSON لتشغيلة pop).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DOC = os.path.join(HERE, "SPLIT_GATES_RESULT.md")
OUT_DOC_A1 = os.path.join(HERE, "SPLIT_GATES_ADDENDUM_1_RESULT.md")   # الملحق 1 (episodes_result.json ‏+ units_diag.json)
FF_AR = {"price": "السعر خارج 1-10", "setup": "بعيدٌ عن ÷2 أو بلا تقسيم",
         "G1": "G1 صعد فوق 20%", "G2": "G2 لا ثبات ثانٍ", "entry": "فوق الطلبات",
         "group": "قروب", None: "يمرّ الكلّ"}


def _p(x, d=1):
    return "—" if x is None else f"{x * 100:.{d}f}%"


def _pt(x):
    return "—" if x is None else f"{x * 100:+.1f} نقطة"


def _ci(c):
    if not c or c[0] is None:
        return "—"
    return f"[{c[0] * 100:+.1f}، {c[1] * 100:+.1f}]"


def _w(c):
    if not c or c[0] is None:
        return "—"
    return f"[{c[0] * 100:.1f}، {c[1] * 100:.1f}]"


RUNG_TXT = {"R0": "R0 الإنتاج", "R1": "R1 تسامح 2%", "R2": "R2 تسامح 3%", "R3": "R3 نافذة 60",
            "R4": "R4 تسامح 3% ‏+ نافذة 60", "R5": "R5 ارتداد 20% ‏+ تسامح 2%"}


def _n(x, suf=""):
    return "—" if x is None else f"{x}{suf}"


def render_addendum(ep, dg, meta):
    L = ["# 🧮🔬 `T-SPLITGATES` — الملحق 1 · النتيجة: G2 على مستوى الحلقة · والوحداتُ التي ترفضها G2 وحدَها", "",
         f"> الملحق `SPLIT_GATES_ADDENDUM_1.md` (بصمة `{ep.get('addendum_sha', '')[:12]}`) · الحلقات تشغيلة `{meta.get('episodes_run', '—')}` "
         f"على شرائح `{ep.get('pop_run')}` · الوحدات تشغيلة `{meta.get('diag_run', '—')}` · قياسٌ فقط ولا تغييرَ على أيّ بوّابة.", ""]
    idt = ep["identity"]
    L += ["## ① بوّابةُ الهويّة", "",
          f"- الشرائح {ep['shards']} · الرموز {ep['symbols']} · تشخيصُ الشموع {ep['bars_diag']} · G2 من الشرائح: ترفض {idt['rej']} · "
          f"تعبر {idt['pass']} (العدد · المنفجرون) ⟵ **{'✅ تطابق المنشور' if idt['ok'] else '❌ لا تطابق — «لا قياس»'}**", ""]
    if not idt["ok"]:
        return "\n".join(L) + "\n"
    nv, cp = ep["never"], ep["complete"]
    L += ["## ② الحلقات — «لم يكتمل» (المرفوض) مقابل «اكتمل» (العابر)", "",
          f"- الحلقات {ep['episodes']} ({ep['tickers']} رمزًا) · أُسقط: بلا نتيجة يومَ E0 {ep['dropped']['no_exp_e0']} · "
          f"نافذةٌ تتجاوز 2025-12-31 {ep['dropped']['truncated_xto']} · بلا نتيجة يومَ C {ep['dropped']['no_exp_c']} · "
          f"حلقاتٌ تمتدّ نافذتُها خارج نافذة الحدث {ep['beyond_rows_episodes']}", "",
          "| المجموعة | حلقات | رموز | انفجر 50% في 20 جلسة | الحصّة | ويلسون 95% | يومُ القياس |", "|---|---|---|---|---|---|---|",
          f"| لم يكتمل | {nv['n']} | {nv['tickers']} | {nv['exp']} | {_p(nv['share'])} | {_w(nv['wilson'])} | E0 |",
          f"| اكتمل | {cp['n']} | {cp['tickers']} | {cp['exp']} | {_p(cp['share'])} | {_w(cp['wilson'])} | C |", "",
          f"- **Δ_G الخام** {_pt(ep['delta_raw'])} · فاصل {_ci(ep['delta_raw_ci'])} · **Δ_G المطبَّق** {_pt(ep['delta_strat'])} · "
          f"فاصل {_ci(ep['delta_strat_ci'])} · حدودُ الخُمُسيّات {ep['mom_cuts']}",
          "- السنوات (بسنة E0): " + " · ".join(f"{y} Δ {_pt(v['delta'])} (لم يكتمل {v['n_never']} · اكتمل {v['n_complete']})"
                                              for y, v in ep["years"].items()),
          f"- أدنى أثرٍ قابلٍ للكشف ‏≈{_pt(ep['mde80'])} · الأرضيّات {'✅' if ep['floors_ok'] else '❌'} · شهودُ G2 {'✅' if ep['witness_g2_ok'] else '❌'}",
          f"- **الحكم (§③ بالأضعف): «{ep['verdict']}»**", ""]
    v1, v2, v3, v4, v5, v6 = (ep[k] for k in ("V1", "V2", "V3", "V4", "V5", "V6"))
    L += ["## ③ وصفيٌّ لا يحكم (§④)", "",
          f"- **V1 القاعدةُ المشتركة (يومَ E0 للمجموعتين):** اكتمل {v1['complete_e0']['exp']} من {v1['complete_e0']['n']} = {_p(v1['complete_e0']['share'])} · "
          f"لم يكتمل {v1['never_e0']['exp']} من {v1['never_e0']['n']} = {_p(v1['never_e0']['share'])}",
          f"- **V2 كلفةُ الانتظار (داخل المكتمل):** من E0 {_p(v2['complete_e0_share'])} · من C {_p(v2['complete_c_share'])} · "
          f"انفجر من E0 لا من C {v2['exp_e0_not_c']} · من C لا من E0 {v2['exp_c_not_e0']}",
          f"- **V3 التأخّر E0 ⟵ C (جلسات):** الوسيط {_n(v3['median'])} · الربيعان {_n(v3['q1'])}-{_n(v3['q3'])} · "
          f"التوزيع: 0 ⟵ {v3['bins']['0']} · 1-5 ⟵ {v3['bins']['1-5']} · 6-10 ⟵ {v3['bins']['6-10']} · 11-19 ⟵ {v3['bins']['11-19']}",
          f"- **V4** المكتملُ الذي يمرّ منطقةَ الطلبات يومَ C أيضًا: {v4['complete_entry_ok']} من {v4['complete']}",
          f"- **V5** الاكتمالُ في أيّ يومٍ من الحلقة: {v5['complete_any_in_episode']} من {v5['episodes']}",
          f"- **V6 السياستان:** بلا G2 (الدخولُ يومَ E0 لكلّ حلقة) ⟵ {v6['noG2_exp_per100']} انفجارًا لكلّ 100 حلقة · حصّةُ الدخول {_p(v6['noG2_share'])} · "
          f"بـG2 (الدخولُ يومَ C للمكتمل) ⟵ {v6['G2_exp_per100']} لكلّ 100 حلقة · {v6['G2_entries']} دخولًا · حصّةُ الدخول {_p(v6['G2_share'])}", ""]
    L += ["## ④ الوحداتُ الـ16 — الشموع والسلّم وما بعدها (المنظور الأساسيّ · آخرُ 30 شمعة)", "",
          "| الوحدة | أدنى Low (يومُه) | جلساتٌ بعده | أعلى ارتدادٍ بعده | أدنى Low بعد القمّة/القاع | يكتمل على | أوّلُ R0 بعد D | أوّلُ مرورٍ كامل | انفجر 50% · أعلى صعود (جلسات) |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in dg["units"]:
        p = r.get("prim") or {}
        fw = r["forward"]
        if p.get("nodata"):
            L.append(f"| {r['unit']} | لا شموع ({p.get('bars')}) | — | — | — | — | — | — | — |")
            continue
        f = p["facts"] or {}
        ok = [k for k, v in (p.get("rungs") or {}).items() if v]
        exp = "لم تكتمل الجلسات" if fw["exploded"] is None else ("✅" if fw["exploded"] else "❌")
        r0 = "—" if not fw["first_R0"] else "+%d (%s)" % (fw["first_R0"][0], fw["first_R0"][1])
        al = "—" if not fw["first_all"] else "+%d (%s)" % (fw["first_all"][0], fw["first_all"][1])
        rung = "، ".join(RUNG_TXT[k].split()[0] for k in ok) or "لا شيء"
        L.append(f"| {r['unit']} | {f.get('low')} ({f.get('low_date')}) | {f.get('bars_after')} | {_n(f.get('bounce_pct'), '%')} | "
                 f"{_n(f.get('retest_gap_pct'), '%')} | {rung} | {r0} | {al} | "
                 f"{exp} · {_n(fw['max_rise_pct'], '%')} ({fw['sessions']}) |")
    L += ["", "- **السلّم:** " + " · ".join(RUNG_TXT.values()) + " — `method_sequence` بالاسم بمعاملاتها (الملحق §⑤).", ""]
    return "\n".join(L) + "\n"


def render(units, pop, meta):
    L = ["# 🧮🔬 `T-SPLITGATES` — النتيجة", "",
         f"> العقد `SPLIT_GATES_prereg.md` (بصمة `{units.get('contract_sha', '')[:12]}`) · ② تشغيلة `{meta.get('units_run', '—')}` · "
         f"③④ تشغيلة `{meta.get('pop_run', '—')}` · قياسٌ فقط ولا تغييرَ على أيّ بوّابة.", ""]
    sm = units["summary"]
    L += ["## ② الوحداتُ المؤرَّخة (173)", ""]
    for tag, name in (("prim", "الأساسيّ (قبل D حصرًا)"), ("sens", "الحسّاسيّة (حتى D)")):
        s = sm[tag]
        L.append(f"- **{name}:** قُيّمت {s['evaluated']} · بلا شموع {s['nodata']} · مشمولةٌ بالفلتر (تقسيمٌ عكسيٌّ خلال 120 يومًا) "
                 f"{s['applicable']} · G1 تقول «لا» {s['g1_says_reject']} · **G1 وحدَها {s['sole_G1']}** · "
                 f"G2 تقول «لا» داخل setup {s['g2_says_reject_in_setup']} · **G2 وحدَها {s['sole_G2']}** · "
                 f"تمرّ الشروطَ المحسوبةَ كلَّها {s['passes_all']}")
        L.append("  - أوّلُ سقوط: " + " · ".join(f"{FF_AR[k]} {v}" for k, v in s["first_fail"].items()))
    rg, wg = sm["repro_g1"], sm["witness_g2"]
    L += ["", f"- **بوّابةُ إعادة الإنتاج (§⑥):** G1 {rg['hit']} من {rg['of']} {'✅' if rg['ok'] else '❌'} · "
              f"شهودُ G2 {wg['hit']} من {wg['of']} {'✅' if wg['ok'] else '❌'}", ""]
    L += ["### المشمولةُ بالفلتر — الاسم والنسبة لكلّ وحدة (المنظور الأساسيّ)", "",
          "| الوحدة | المصدر | أوّلُ سقوط | صعد بعد التقسيم | G2 | G1 وحدَها | G2 وحدَها | الحسّاسيّة |", "|---|---|---|---|---|---|---|---|"]
    for r in units["units"]:
        p, q = r.get("prim") or {}, r.get("sens") or {}
        if not (p.get("applicable") or q.get("applicable") or "logged_rose_pct" in r or r.get("logged_g2")):
            continue
        rose = "—" if p.get("rose_pct") is None else f"{p['rose_pct']:.1f}%"
        if "logged_rose_pct" in r:
            rose += f" (السجلّ {r['logged_rose_pct']}%)"
        sens = "—" if q.get("nodata") else f"{FF_AR.get(q.get('first_fail'), q.get('first_fail'))}"
        L.append(f"| {r['unit']} | {'/'.join(r['sources'])} | {FF_AR.get(p.get('first_fail'), 'لا شموع') if not p.get('nodata') else 'لا شموع'} | "
                 f"{rose} | {'✅' if p.get('seq_ok') else '❌'} | {'⛔' if p.get('sole_G1') else ''} | {'⛔' if p.get('sole_G2') else ''} | {sens} |")
    L += ["", "## ③④ ثلاثُ سنوات (PIT)", "",
          f"- رموزُ التقسيم العكسيّ {pop['symbols']} · التغطية {_p(pop['coverage'])} {'✅' if pop['coverage_ok'] else '❌'} · "
          f"تشخيصُ الشموع {pop['bars_diag']}", ""]
    for g, name in (("G1", "③ G1 «صعد فوق 20% أوّل التقسيم» — المرفوضُ = من صعد فوق 20%"),
                    ("G2", "④ G2 «لم يكتمل ثبات الدعم الثاني» — المرفوضُ = من لم يكتمل تسلسلُه")):
        s = pop[g]
        L += [f"### {name}", "",
              "| المجموعة | إدخالات | رموز | انفجر 50% في 20 جلسة | الحصّة | ويلسون 95% |", "|---|---|---|---|---|---|",
              f"| ترفضها البوّابة | {s['rej']['n']} | {s['rej']['tickers']} | {s['rej']['exp']} | {_p(s['rej']['share'])} | {_w(s['rej']['wilson'])} |",
              f"| تعبرها | {s['pass']['n']} | {s['pass']['tickers']} | {s['pass']['exp']} | {_p(s['pass']['share'])} | {_w(s['pass']['wilson'])} |",
              "",
              f"- **Δ الخام** {_pt(s['delta_raw'])} · فاصل {_ci(s['delta_raw_ci'])} · **Δ بعد ضبط الزخم** {_pt(s['delta_strat'])} · "
              f"فاصل {_ci(s['delta_strat_ci'])} · حدودُ خُمُسيّات عائد 20 جلسة {s['mom_cuts']}",
              "- السنوات: " + " · ".join(f"{y} Δ {_pt(v['delta'])} (ترفض {v['n_rej']} · تعبر {v['n_pass']})" for y, v in s["years"].items()),
              f"- C-MOM (وصفيّ): إقصاءُ {s['cmom']['n']} الأعلى زخمًا ⟵ حصّةُ انفجارهم {_p(s['cmom']['share'])} · "
              f"أدنى أثرٍ قابلٍ للكشف ‏≈{_pt(s['mde80'])} · الأرضيّات {'✅' if s['floors_ok'] else '❌'}",
              f"- **الحكم (§⑧ بالأضعف): «{s['verdict']}»**", ""]
    return "\n".join(L) + "\n"


def main():
    units = json.load(open(os.path.join(HERE, "data", "units_eval.json"), encoding="utf-8"))
    pop = json.load(open(os.path.join(HERE, "data", "pop_result.json"), encoding="utf-8"))
    meta = json.load(open(os.path.join(HERE, "data", "runs.json"), encoding="utf-8"))
    docs = [(OUT_DOC, render(units, pop, meta))]
    ep_p, dg_p = os.path.join(HERE, "data", "episodes_result.json"), os.path.join(HERE, "data", "units_diag.json")
    if os.path.exists(ep_p) and os.path.exists(dg_p):           # الملحق 1
        docs.append((OUT_DOC_A1, render_addendum(json.load(open(ep_p, encoding="utf-8")),
                                                  json.load(open(dg_p, encoding="utf-8")), meta)))
    if "--check" in sys.argv:
        bad = [p for p, txt in docs if not (os.path.exists(p) and open(p, encoding="utf-8").read().startswith(txt))]
        print("✅ متطابق" if not bad else "❌ مختلف: " + " · ".join(os.path.basename(p) for p in bad))
        return 0 if not bad else 1
    for p, txt in docs:                                        # الذيلُ اليدويّ بعد الجزء المولَّد لا يُدهَس
        if os.path.exists(p) and open(p, encoding="utf-8").read().startswith(txt):
            print(f"بلا تغيير {p}")
            continue
        open(p, "w", encoding="utf-8").write(txt)
        print(f"كُتب {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
