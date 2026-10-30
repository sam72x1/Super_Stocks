# -*- coding: utf-8 -*-
"""🕯️🔬 `T-WICK` — مولّدُ وثيقة النتيجة من ملفّي البيانات المحفوظين (حتميّ · بلا شبكة).

    python3 fm_forensics/wick/wick_doc.py          ⟵ يكتب T_WICK_RESULT.md (ويُبقي ما كُتب يدويًّا بعد الجزء المولَّد)
    python3 fm_forensics/wick/wick_doc.py --check  ⟵ يعيد التوليد ويقارن (خروج 1 عند الاختلاف)

المدخلات: `data/units_eval.json` (① · RESULT_JSON لتشغيلة units_eval) · `data/pop_result.json` (②③ · RESULT_JSON لتشغيلة pop) · `data/runs.json`.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DOC = os.path.join(HERE, "T_WICK_RESULT.md")
KIND = {"ready": "جاهز", "add": "إضافة"}


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


def _yn(b):
    return "—" if b is None else ("نعم" if b else "لا")


def predictions(units, pop):
    """§⑥ — بطاقةُ التنبّؤات تُحسب من البيانات نفسِها (لا بيد)."""
    sm = units["summary"]
    cetx = next((u for u in units["units"] if u["sym"] == "CETX" and u["kind"] == "add"), {})
    out = []
    r, a = sm["ready"]["r50"], sm["add"]["r50"]
    out.append(("W1", "الجاهزون بذيلٍ 50% فأكثر بين 2 و8 · والإضافات بين 8 و30", f"الجاهزون {r} · الإضافات {a}",
                2 <= r <= 8 and 8 <= a <= 30))
    cw = cetx.get("wick")
    out.append(("W2", "CETX ذيلُه 50% فأكثر ونسبتُه بين 70% و90%", f"{_p(cw)} يومَ {cetx.get('wick_date', '—')}",
                cw is not None and 0.70 <= cw <= 0.90))
    if pop.get("rungs"):
        r50 = pop["rungs"]["r50"]
        share = r50["wick"]["n"] / pop["labelled"] if pop["labelled"] else None
        out.append(("W3", "إدخالاتُ BASE2 بذيلٍ 50% فأكثر بين 2% و8%", _p(share), share is not None and 0.02 <= share <= 0.08))
        out.append(("W4", "Δ الخام عند 50% موجب والحكم «الذيلُ يرفع»", f"Δ {_pt(r50['delta_raw'])} · «{r50['verdict']}»",
                    (r50["delta_raw"] or 0) > 0 and r50["verdict"] == "الذيلُ يرفع"))
        sh = [v["share"] for v in pop["dose"].values()]
        mono = all(x is not None for x in sh) and all(b > a for a, b in zip(sh, sh[1:]))
        out.append(("W5", "الجرعةُ صاعدةٌ رتيبًا عبر الخانات الأربع", " ⟵ ".join(_p(x) for x in sh), mono))
        it = pop.get("intersection") or {}
        pw = it.get("p_p3_given_w")
        out.append(("W6", "P(P3 \\| ذيل) بين 10% و40% والتصنيف «مستقلّ»", f"{_p(pw)} · «{pop.get('intersection_class')}»",
                    pw is not None and 0.10 <= pw <= 0.40 and pop.get("intersection_class") == "مستقلّ"))
    else:
        for k in ("W3", "W4", "W5", "W6"):
            out.append((k, "—", "«لا قياس» في ② ⟵ لا يُقيَّم", None))
    return out


def render(units, pop, meta):
    L = ["# 🕯️🔬 `T-WICK` «عمى الذيل» — النتيجة", "",
         f"> العقد `T_WICK_prereg.md` (بصمة `{units.get('contract_sha', '')[:12]}`) · ① تشغيلة `{meta.get('units_run', '—')}` · "
         f"②③ تشغيلة `{meta.get('pop_run', '—')}` · قياسٌ فقط: لا بوّابةَ ولا عرضَ ولا عتبة.", ""]
    sm = units["summary"]
    L += ["## ① الوحدات — الذيلُ العلويّ في الجلسات الخمس حتى يوم الترشيح", ""]
    for kind in ("ready", "add"):
        s = sm[kind]
        L.append(f"- **{KIND[kind]} ({s['units']}):** قُيّمت {s['evaluated']} · بلا شموع {s['nodata']} · ذيلٌ 30% فأكثر {s['r30']} · "
                 f"**50% فأكثر {s['r50']}** · 80% فأكثر {s['r80']} · ومنها بذيلٍ 50% فأكثر ووسمٍ مكتمل {s['labelled_r50']} انفجر منها "
                 f"{s['exploded_r50']} (وصفيّ)")
    edge = [u for u in units["units"] if not u.get("nodata") and any(round(u["wick"], 4) >= g and not u[f"r{int(g * 100)}"]
                                                                     for g in (0.30, 0.50, 0.80))]
    if edge:
        L.append("- ⚠️ **حدُّ الدرجة بالضبط (فاصلةٌ عائمة):** " + " · ".join(
            f"{u['sym']} ({KIND[u['kind']]}) High {u['high']} ÷ Close {u['close']} = {_p(u['wick'])} بالضبط ⟵ لم تَعُدّه الأداةُ في درجة "
            + "/".join(str(int(g * 100)) for g in (0.30, 0.50, 0.80) if round(u["wick"], 4) >= g and not u[f"r{int(g * 100)}"]) + "%"
            for u in edge) + " — بالتعريف المكتوب (§① «فأكثر») يُعَدّ · والدرجةُ الحاكمة 50% لا تمسّها")
    L += ["", "### الأسماءُ بذيلٍ 30% فأكثر (الاسم · النسبة · التاريخ)", "",
          "| النوع | الرمز | يومُ القرار | شمعةُ الترشيح | الذيل | يومُ الذيل | High | Close | 50% فأكثر | انفجر بعدها (وصفيّ) |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    rows = [u for u in units["units"] if not u.get("nodata") and u["wick"] >= 0.30]
    for u in sorted(rows, key=lambda u: (u["kind"], -u["wick"])):
        L.append(f"| {KIND[u['kind']]} | {u['sym']} | {u['D']} | {u.get('ref_bar') or '—'} | {_p(u['wick'])} | {u['wick_date']} | "
                 f"{u['high']} | {u['close']} | {'✅' if u['r50'] else ''} | {_yn(u.get('exploded'))} |")
    nod = sorted(f"{u['sym']} ({KIND[u['kind']]} {u['D']})" for u in units["units"] if u.get("nodata"))
    L += ["", f"- بلا شموع ({len(nod)}): " + (" · ".join(nod) if nod else "لا شيء"), ""]
    L += ["## ② ثلاثُ سنوات — مجتمعُ الجزء ب (BASE2)", "",
          f"- رموزُ الاتّحاد {pop['symbols']} · التغطية {_p(pop['coverage'])} {'✅' if pop['coverage_ok'] else '❌'} · تشخيصُ الشموع {pop['bars_diag']}",
          "- **بوّابةُ الهويّة:** " + " · ".join(f"{p} {v['n']} مقابل {v['pub']} {'✅' if v['ok'] else '❌'}" for p, v in pop["identity"].items()),
          f"- الإدخالات {pop['entries']} · بوسمٍ مكتمل {pop['labelled']} · بلا وسم {pop['unlabelled']} · حدودُ خُمُسيّات الزخم {pop['mom_cuts']}", ""]
    if pop.get("rungs"):
        for key, name in (("r30", "30%"), ("r50", "50% (الحاكمة)"), ("r80", "80%")):
            s = pop["rungs"][key]
            L += [f"### ذيلٌ {name}", "",
                  "| المجموعة | إدخالات | رموز | انفجر 50% في 20 جلسة | الحصّة | ويلسون 95% |", "|---|---|---|---|---|---|",
                  f"| له ذيل | {s['wick']['n']} | {s['wick']['tickers']} | {s['wick']['exp']} | {_p(s['wick']['share'])} | {_w(s['wick']['wilson'])} |",
                  f"| لا ذيل | {s['none']['n']} | {s['none']['tickers']} | {s['none']['exp']} | {_p(s['none']['share'])} | {_w(s['none']['wilson'])} |",
                  "",
                  f"- **Δ الخام** {_pt(s['delta_raw'])} · فاصل {_ci(s['delta_raw_ci'])} · **Δ بعد ضبط الزخم** {_pt(s['delta_strat'])} · فاصل {_ci(s['delta_strat_ci'])}",
                  "- السنوات: " + " · ".join(f"{y} Δ {_pt(v['delta'])} (له ذيل {v['n_wick']} · لا ذيل {v['n_none']})" for y, v in s["years"].items()),
                  f"- C-MOM (وصفيّ): أعلى {s['cmom']['n']} زخمًا ⟵ حصّتُهم {_p(s['cmom']['share'])} · أدنى أثرٍ قابلٍ للكشف ‏≈{_pt(s['mde80'])} · "
                  f"الأرضيّات {'✅' if s['floors_ok'] else '❌'}",
                  f"- **الحكم (§④ بالأضعف): «{s['verdict']}»**", ""]
        L += ["### الجرعة (وصفيّ)", "", "| الذيل | إدخالات | انفجر | الحصّة | ويلسون 95% |", "|---|---|---|---|---|"]
        for k, v in pop["dose"].items():
            L.append(f"| {k} | {v['n']} | {v['exp']} | {_p(v['share'])} | {_w(v['wilson'])} |")
        L.append("")
    else:
        L += [f"- **الحكم: «{pop['verdict']}»** — لا حصصَ ولا فواصل (§④)", ""]
    L += ["## ③ التقاطعُ مع الزوج P3 «سبايكُ حجمٍ ثمّ هبوط 20%» (عند 50%)", ""]
    it = pop.get("intersection")
    if it:
        c = it["cells"]
        L += ["| | P3 نعم | P3 لا |", "|---|---|---|",
              f"| ذيلٌ 50% فأكثر | {c['W1P1']['n']} (انفجر {c['W1P1']['exp']} · {_p(c['W1P1']['share'])}) | {c['W1P0']['n']} (انفجر {c['W1P0']['exp']} · {_p(c['W1P0']['share'])}) |",
              f"| لا ذيل | {c['W0P1']['n']} (انفجر {c['W0P1']['exp']} · {_p(c['W0P1']['share'])}) | {c['W0P0']['n']} (انفجر {c['W0P0']['exp']} · {_p(c['W0P0']['share'])}) |",
              "",
              f"- P(P3 | ذيل) {_p(it['p_p3_given_w'])} · P(ذيل | P3) {_p(it['p_w_given_p3'])} · phi {it['phi']}",
              f"- Δ الذيل مطبَّقًا على طبقتَي P3 {_pt(it['dW_given_P3'])} {_ci(it['dW_given_P3_ci'])} · Δ P3 مطبَّقًا على طبقتَي الذيل "
              f"{_pt(it['dP3_given_W'])} {_ci(it['dP3_given_W_ci'])}",
              f"- الخام: Δ الذيل {_pt(it['dW_raw'])} {_ci(it['dW_raw_ci'])} · Δ P3 {_pt(it['dP3_raw'])} {_ci(it['dP3_raw_ci'])} · "
              f"Δ الذيل داخل P3 = 0 وحدَها {_pt(it['dW_within_P3_0'])}",
              f"- **التصنيف (§⑤ بالأضعف): «{pop.get('intersection_class')}»**", ""]
    else:
        L += [f"- **التصنيف: «{pop.get('intersection_class', 'لا يُحكم')}»** — ② «لا قياس»", ""]
    L += ["## ⑥ التنبّؤات — كما كُتبت قبل الرقم", "", "| # | التنبّؤ | الرقم | صدق؟ |", "|---|---|---|---|"]
    for k, txt, got, ok in predictions(units, pop):
        L.append(f"| {k} | {txt} | {got} | {'—' if ok is None else ('✅' if ok else '❌')} |")
    return "\n".join(L) + "\n"


def main():
    units = json.load(open(os.path.join(HERE, "data", "units_eval.json"), encoding="utf-8"))
    pop = json.load(open(os.path.join(HERE, "data", "pop_result.json"), encoding="utf-8"))
    meta = json.load(open(os.path.join(HERE, "data", "runs.json"), encoding="utf-8"))
    txt = render(units, pop, meta)
    cur = open(OUT_DOC, encoding="utf-8").read() if os.path.exists(OUT_DOC) else ""
    if "--check" in sys.argv:
        print("✅ متطابق" if cur.startswith(txt) else "❌ مختلف")
        return 0 if cur.startswith(txt) else 1
    if cur.startswith(txt):
        print("لا تغيير")
        return 0
    open(OUT_DOC, "w", encoding="utf-8").write(txt)
    print(f"كُتب {OUT_DOC}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
