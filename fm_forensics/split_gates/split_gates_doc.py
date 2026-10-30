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
    txt = render(units, pop, meta)
    if "--check" in sys.argv:
        cur = open(OUT_DOC, encoding="utf-8").read() if os.path.exists(OUT_DOC) else ""
        print("✅ متطابق" if cur.startswith(txt) else "❌ مختلف")
        return 0 if cur.startswith(txt) else 1
    open(OUT_DOC, "w", encoding="utf-8").write(txt)
    print(f"كُتب {OUT_DOC}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
