"""📈🔓 مولِّدُ وثيقة جدوى v4 (`vwap_mom_feas_v4_result.md`) من `vwap_mom_feas_v4_2026-09.json` — النتيجةُ كما صدرت (الملحق 3 §④-⑤).

`python3 vwap_mom_feas_v4_doc.py` يكتب الوثيقة · و`--check` يقارن بايتًا (خروج 1 إن اختلفت). بلا شبكة · بلا عائد.
"""
import json
import sys

JSON_FILE = "vwap_mom_feas_v4_2026-09.json"
DOC_FILE = "vwap_mom_feas_v4_result.md"
ROWS = (("FULL", "التقاطعُ الكامل (② ≥3) — **الحاكم**"), ("FULL5", "التقاطعُ بـ② ≥5 (مِجَسّ)"),
        ("FULL_rv_unknown_as_pass", "الكامل لو عُدّ ② المجهولُ ناجحًا"), ("C123", "① ∧ ② ∧ ③"), ("C12", "① ∧ ②"),
        ("C1", "① وحده (‏+20%)"), ("C2", "② وحده (≥3)"), ("C2b", "② وحده (≥5)"), ("C3", "③ وحده (L)"), ("C4", "④ وحده (سلكٌ أو 8-K)"),
        ("BASE", "A ∧ ⑤ (السعرُ والنوع)"), ("H0", "A بسعرٍ ≥ 1 وحده (فحصُ الإعادة)"),
        ("DH", "D بعد أوّل FULL"), ("DHL", "D ∧ L بعد أوّل FULL"), ("U1", "مجهول ① (لا إغلاقَ سابق)"),
        ("U2", "مجهول ② (ظهورٌ دون 10)"), ("U4", "مجهول SEC"))
CHG_ORDER = ("<0", "0-10", "10-20", "20-30", "30-50", "50-100", "100+", "?")
RV_ORDER = ("<1", "1-3", "3-5", "5-10", "10-20", "20+", "?")
VERDICT_AR = {"final_close": "**إغلاقٌ نهائيّ** — لا درجةَ في 10-40 ⟵ لا ملحقَ بعد الملحق 3 (أمرُ المالك)",
              "pick": "**اختارت** — درجةٌ في 10-40 ⟵ تُثبَّت `D_MIN` في ملحقٍ مؤرَّخ ويتوقّف العملُ حتى «ابن الأداة»",
              "no_measure": "**لا قياس** — سقط حارسٌ ⟵ تُعاد التشغيلةُ مرّةً واحدة · وإن تكرّر فالقرارُ للمالك"}


def _f(x):
    if isinstance(x, float) and x.is_integer():
        return f"{int(x):,}"
    return f"{x:,}" if isinstance(x, int) else str(x)


def _k(d):
    return f"{int(d) // 1000:,}k" if int(d) < 1_000_000 else f"{int(d) // 1_000_000}M"


def predictions(r):
    """P12-P17 (الملحق 3 §⑤) ⟵ [(الرمز، النصّ، صدق؟)] — الحكمُ من الـJSON وحدَه."""
    med = r["median_by_dmin"]
    lad = [str(d) for d in r["d_ladder"]]
    lo, hi = lad[0], lad[-1]
    cov = r.get("coverage_C123_lowest") or {}
    den = sum(cov.values())
    share = (cov.get("both", 0) + cov.get("wire", 0) + cov.get("sec8k", 0)) / den if den else None
    wi = (r.get("news") or {}).get("wire_items") or {}
    rep = r.get("replay_v3_H0") or {}
    out = [
        ("P12", f"`FULL` عند 250k بين 2 و10 وعند 5M بين 1 و6 — الفعليّ {_f(med[lo]['FULL'])} و{_f(med[hi]['FULL'])}",
         2 <= med[lo]["FULL"] <= 10 and 1 <= med[hi]["FULL"] <= 6),
        ("P13", f"لا درجةَ في 10-40 والكتلةُ تحت 10 — الفعليّ: الحكم «{r['verdict']}» · `FULL` " + " · ".join(_f(med[d]["FULL"]) for d in lad),
         r["verdict"] == "final_close" and all(med[d]["FULL"] < 10 for d in lad)),
        ("P14", f"`C1` عند 250k بين 20 و80 و`C2` بين 200 و1,000 — الفعليّ {_f(med[lo]['C1'])} و{_f(med[lo]['C2'])}",
         20 <= med[lo]["C1"] <= 80 and 200 <= med[lo]["C2"] <= 1000),
        ("P15", "GlobeNewswire أكبرُ الأسلاك عناصرَ — الفعليّ " + (" · ".join(f"{k} {_f(v)}" for k, v in sorted(wi.items(), key=lambda x: -x[1])) or "لا عناصر"),
         bool(wi) and max(wi, key=wi.get) == "GlobeNewswire"),
        ("P16", "④ في 25-60% من `C123` عند 250k — الفعليّ " + (f"{share:.1%} ({_f(den - cov.get('none', 0) - cov.get('sec6k_only', 0))} من {_f(den)})" if den else "لا مقام"),
         share is not None and 0.25 <= share <= 0.60),
        ("P17", f"فحصُ الإعادة صفرُ فرق — الفعليّ {_f(rep.get('mismatch'))} من {_f(rep.get('compared'))}",
         rep.get("mismatch") == 0 and rep.get("compared", 0) > 0),
    ]
    return out


def render(r):
    lad = [str(d) for d in r["d_ladder"]]
    med, tot = r["median_by_dmin"], r["month_totals"]
    L = []
    L.append("# 📈🔓 `T-VWAP-MOM` — جدوى v4 «التقاطعُ الكامل» (الملحق 3) · النتيجةُ كما صدرت")
    L.append("")
    L.append(f"> تشغيلة `{r.get('run')}` على main `{str(r.get('main_sha', ''))[:9]}` · الشهر {r['month']} · {len(r['per_day'])} جلسة · "
             f"قبلها {r['rvol_win']} جلسةً لـ② ({r['prior_sessions'][0]} ⟵ {r['prior_sessions'][1]}) · بصمةُ الملحق `{r['add3_sha'][:12]}` · "
             f"**عدٌّ بلا عائد** · مولَّدةٌ من `{JSON_FILE}` بـ`vwap_mom_feas_v4_doc.py`.")
    L.append("> 🔓 **فُتح المحورُ لهذه التشغيلة بقرار المالك** (2026-10-29 · `VWM_REOPEN=1`) · والتعريفاتُ كلُّها في الملحق 3 مدموجةٌ قبل أيّ رقم.")
    L.append("")
    L.append(f"## ⓪ الحكم: {VERDICT_AR.get(r['verdict'], r['verdict'])}")
    L.append("")
    L.append("- **القاعدة على وسيط `FULL` في اليوم (A ∧ ① ‏+20% ∧ ② ≥3 ∧ ③ L ∧ ④ سلكٌ أو 8-K ∧ ⑤):** "
             + " · ".join(f"{_k(d)} = **{_f(med[d]['FULL'])}**" for d in lad)
             + f" ⟵ `D_MIN` = {r.get('D_MIN_pick_by_rule')} · الحارس: {'يصلح' if r['gates_ok'] else 'لا قياس ' + str(r['gates_why'])}")
    L.append("")
    L.append("## ① الوسيطُ في اليوم لكلّ درجة (ومجموعُ الشهر بين قوسين)")
    L.append("")
    L.append("| المجتمع | " + " | ".join(_k(d) for d in lad) + " |")
    L.append("|---|" + "---|" * len(lad))
    for key, lab in ROWS:
        L.append(f"| {lab} | " + " | ".join(f"{_f(med[d][key])} ({_f(tot[d][key])})" for d in lad) + " |")
    L.append("")
    L.append("## ② أين الكتلة — ① و② وحدهما على 250k (وحدةُ العدّ رمزٌ/يوم · أعلى قيمةٍ في أحداث `BASE` له · مجموعُ الشهر)")
    L.append("")
    hc, hr, cx = r.get("hist_chg_lowest") or {}, r.get("hist_rvol_lowest") or {}, r.get("cross_lowest") or {}
    L.append("**① التغيّرُ عن إغلاق الأمس (%):** " + " · ".join(f"{b}: {_f(hc.get(b, 0))}" for b in CHG_ORDER))
    L.append("")
    L.append("**② السيولةُ النسبيّة (×):** " + " · ".join(f"{b}: {_f(hr.get(b, 0))}" for b in RV_ORDER))
    L.append("")
    L.append("| ① \\ ② | " + " | ".join(RV_ORDER) + " |")
    L.append("|---|" + "---|" * len(RV_ORDER))
    for bc in CHG_ORDER:
        L.append(f"| {bc} | " + " | ".join(_f(cx.get(f"{bc}|{br}", 0)) for br in RV_ORDER) + " |")
    L.append("")
    n = r.get("news") or {}
    s = r.get("sec") or {}
    cov = r.get("coverage_C123_lowest") or {}
    src = r.get("src_FULL_lowest") or {}
    L.append("## ③ تغطيةُ المصدرين")
    L.append("")
    L.append(f"- **أخبارُ Polygon:** {_f(n.get('items'))} خبرًا في {_f(n.get('pages'))} صفحة · مكتمل={n.get('complete')} · رموزٌ بخبرِ سلك {_f(n.get('wire_symbols'))}")
    L.append("- **عناصرُ كلّ سلك:** " + (" · ".join(f"{k} {_f(v)}" for k, v in sorted((n.get('wire_items') or {}).items(), key=lambda x: -x[1])) or "لا شيء")
             + " · **ومن أيّ حقل:** " + (" · ".join(f"{k} {_f(v)}" for k, v in sorted((n.get('wire_fields') or {}).items())) or "—"))
    L.append("- **أكثرُ الناشرين في الموجز (ما سوى الأسلاك لا يُحتسب):** " + " · ".join(f"{k} {_f(v)}" for k, v in (n.get("top_publishers") or {}).items()))
    L.append(f"- **SEC:** خريطة {_f(s.get('tickers_mapped'))} · مودِعو 8-K/6-K في المدى {_f(s.get('filers'))} · submissions {_f(s.get('need'))} · "
             f"مجهول {_f(s.get('unknown_ciks'))} · CIK بـSIC ‏6770 {_f(s.get('spac_ciks'))} · فهارسُ ناقصة {s.get('index_missing')}")
    L.append("- **على رموز/أيّام `C123` عند 250k:** " + " · ".join(f"{k} {_f(v)}" for k, v in cov.items())
             + " · **ومصدرُ أوّل `FULL`:** " + " · ".join(f"{k} {_f(v)}" for k, v in src.items()))
    L.append("")
    g = r.get("gate_counts") or {}
    ref = r.get("reference") or {}
    L.append("## ④ الحرّاس")
    L.append("")
    L.append(f"- الحارس: **{'يصلح' if r['gates_ok'] else 'لا قياس'}** {r['gates_why'] or ''} · ملفّاتُ دقيقة ناقصة {r.get('days_missing')} · "
             f"إغلاقٌ سابقٌ ناقص {ref.get('prev_missing')} · تقسيمات {_f(ref.get('splits'))} (مكتمل {ref.get('splits_complete')}) · "
             f"أنواع {_f(ref.get('types'))} (مكتمل {ref.get('types_complete')} · بالتفاصيل {_f(ref.get('type_details'))})")
    L.append(f"- مجهولُ SEC {_f(g.get('sec_unknown'))} من {_f(g.get('sec_denom'))} (`C123` ذاتُ CIK عند 250k) · بلا CIK {_f(g.get('nocik_c123'))} · "
             f"النوعُ المجهول {_f(g.get('type_unknown'))} من {_f(g.get('type_denom'))} (① بسعرٍ في ⑤ عند 250k) · "
             f"مُقصًى بالنوع {_f(g.get('type_excl_c1'))} · SPAC {_f(g.get('spac_c1'))}")
    L.append("")
    rep = r.get("replay_v3_H0") or {}
    L.append("## ⑤ فحصُ الإعادة مقابل `H0` في v3")
    L.append("")
    L.append(f"- {_f(rep.get('mismatch'))} فرقًا من {_f(rep.get('compared'))} مقارنة (يومٌ × درجة)" + (f" · أمثلة {rep.get('examples')}" if rep.get("examples") else ""))
    L.append("")
    L.append("## ⑥ التنبّؤات قبل الأرقام (الملحق 3 §⑤ — تُنشر ولا تُحذف)")
    L.append("")
    for code, text, ok in predictions(r):
        L.append(f"- **{code}:** {text} ⟵ {'✅ صدق' if ok else '❌ **سقط**'}")
    L.append("")
    lo_rule = int(r["d_rule"][0])
    c123_max = max(med[d]["C123"] for d in lad)
    c1_max = max(med[d]["C1"] for d in lad)
    wi = n.get("wire_items") or {}
    missing = [w for w in ("GlobeNewswire", "PRNewswire", "Business Wire", "Accesswire") if not wi.get(w)]
    L.append("## ⑦ حدودُ الصدق والمتانة (من الأرقام أعلاه)")
    L.append("")
    L.append(f"- **أسلاكٌ غائبةٌ عن موجز Polygon في الشهر:** {' · '.join(missing) if missing else 'لا شيء'} — فقناةُ السلك عمليًّا "
             + (" · ".join(f"{k} وحدَه" for k in wi) if wi else "معدومة") + " ‏+ 8-K · والموجزُ كلُّه "
             + f"{len(n.get('top_publishers') or {})} ناشرين ({' · '.join(n.get('top_publishers') or {})}).")
    L.append(f"- **والحكمُ لا يتوقّف على ④:** أعلى وسيطٍ لـ`C123` (① ∧ ② ∧ ③ بلا خبر) على الدرجات {c123_max} · ولـ`C1` (① وحده) {c1_max} — "
             + ("**كلاهما دون 10** ⟵ لا درجةَ في 10-40 ولو تحقّق ④ في كلّ حدث." if max(c123_max, c1_max) < lo_rule
                else "وأحدُهما ليس دون 10 ⟵ الحكمُ قد يتغيّر بتغطيةٍ أوسع للأسلاك."))
    L.append("- **شهرٌ واحد (2026-09)** · عدٌّ بلا عائد · وحدةُ العدّ رمزٌ/يوم.")
    L.append("")
    L.append("## ⑧ ما بعدها")
    L.append("")
    if r["verdict"] == "final_close":
        L.append("- **إغلاقٌ نهائيّ بأمر المالك:** «إن لم تقع درجة في 10-40 فالإغلاق نهائي ولا ملحق بعده» ⟵ `vwap_mom_feas.py` و`vwap_mom_feas_v4.py` "
                 "يخرجان 8 · ونصُّ الإغلاق يُحدَّث إلى «نهائيّ» · ولا عائدَ حُسب.")
    elif r["verdict"] == "pick":
        L.append("- **اختارت:** تُثبَّت `D_MIN` في ملحقٍ مؤرَّخ (العقد §③) ويتوقّف العملُ حتى «ابن الأداة» · ولا عائد.")
    else:
        L.append("- **لا قياس:** تُعاد التشغيلةُ مرّةً واحدة بلا تغييرٍ في التعريفات · وإن تكرّر فالقرارُ للمالك.")
    L.append("")
    return "\n".join(L) + "\n"


def main(argv):
    r = json.load(open(JSON_FILE, encoding="utf-8"))
    doc = render(r)
    if "--check" in argv:
        old = open(DOC_FILE, encoding="utf-8").read()
        print("✅ مطابقة" if old == doc else "⛔ الوثيقةُ لا تطابق المولِّد")
        return 0 if old == doc else 1
    open(DOC_FILE, "w", encoding="utf-8").write(doc)
    print(f"كُتبت {DOC_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
