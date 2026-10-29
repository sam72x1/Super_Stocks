"""يولّد T_REBUILD_2026_result.md من data/y26_result_2026-10-29.json — لا رقمَ يُكتب باليد (عقد `T_REBUILD_2026_prereg.md`)."""
import json, sys
J, OUT = sys.argv[1], sys.argv[2]
r = json.load(open(J, encoding="utf-8"))
st = r["stats"]
def pct(x): return "—" if x is None else f"{100 * x:.1f}%"
def pq(x): return "—" if x is None else f"{100 * x:+.1f}%"
def ci(a, k=100, f=".1f"): return "—" if not a else f"[{k * a[0]:{f}}، {k * a[1]:{f}}]"
def cipp(a): return "—" if not a else f"[{100 * a[0]:+.2f}، {100 * a[1]:+.2f}]"
NM = {"NEW": "**الجديدة** (الدرجةُ المجمَّدة ≥ θ)", "BASE2": "BASE2", "CURRENT": "CURRENT (القبولُ ببوّابات الإنتاج)"}
H = (("2026-01-02", "2026-05-15"), ("2026-05-18", "2026-09-30"))
L = []
L.append("# 🧭 `T-REBUILD-26` — القائمةُ الجديدة المجمَّدة على 2026 (عيّنةٌ لم تُلمس) مرّةً واحدة · ووقفُ القاع · والهبوطُ قبل ‏+50%")
L.append("")
L.append(f"> العقد `T_REBUILD_2026_prereg.md` (#670 · بصمته `{r['contract_sha'][:12]}…`) · التجميد بصمته `{r['freeze_sha'][:12]}…` (θ = {r['theta']}) · "
         f"تشغيلة **`{r['run']}`** على main `{r['main_sha'][:9]}` ({r['created_at']}) · الأرقامُ في `data/{r['file']}`.")
L.append("> **مرّةً واحدة:** وضعُ `y26` يرفض (خروج 7) بعد وجود هذا الملفّ · ولا يُعاد ولا يُرخى شيءٌ بعده · ولا شحنَ مهما كانت النتيجة.")
L.append("")
L.append(f"## ⓪ الحكم: الفرع {r['branch']} — «{r['verdict']}»")
L.append("")
n, b, c = st["NEW"], st["BASE2"], st["CURRENT"]
L.append(f"- **الجديدة {pct(n['share'])} مقابل BASE2 {pct(b['share'])} وCURRENT {pct(c['share'])}** · بعبء {n['burden']}/جلسة مقابل {b['burden']} و{c['burden']}.")
_sp0 = r["pivot_stops"]["NEW"]["SP0"]
_nx, _bx = r["mae"]["NEW"]["non_exploded_q"], r["mae"]["BASE2"]["non_exploded_q"]
_tl = r["tested_level_stops"]
L.append(f"- 🔴 **لكنّ القاعَ لا يحمي الصفقة (وصف):** بلغ ‏+50% قبل لمس القاع (SP0) {_sp0['hit50_first']} من {_sp0['n']} = {pct(_sp0['share'])} وحدَها · "
         f"ووسيطُ أدنى سعرٍ لغير المنفجرين في الجديدة {100 * _nx[2]:.1f}% مقابل BASE2 {100 * _bx[2]:.1f}% ⟵ القائمةُ تنتقي منفجرين أكثر **وتنتقي معهم هبوطًا أعمق**.")
L.append(f"- و{_tl['unknown_level']} من {n['entries']} بلا مستوًى مختبَر ⟵ ترفضها بوّابةُ الإنتاج (`M_لا_مستوى_مختبر` · مجمَّدةٌ بعقد H6) ⟵ أيُّ استعمالٍ قرارُ المالك.")
L.append("")
L.append("## ① القوائم الثلاث على 2026 (الإدخالاتُ الجديدة · المنفجر = ‏+50% في 20 جلسة)")
L.append("")
L.append("| القائمة | الإدخالات | العبء/جلسة | الموسوم | منفجر | الحصّة | الوسمُ مجهول |")
L.append("|---|---|---|---|---|---|---|")
for k in ("NEW", "BASE2", "CURRENT"):
    s = st[k]
    L.append(f"| {NM[k]} | {s['entries']:,} | {s['burden']} | {s['labelled']:,} | {s['exploded']:,} | {pct(s['share'])} | {s['unknown']:,} |")
L.append("")
L.append(f"- جلساتُ 2026: {r['sessions']} · تغطيةُ الشموع {100 * r['coverage']:.2f}% (حدُّ «لا قياس» 85%) · تشخيصُ الشموع: "
         + " · ".join(f"{k} {v:,}" for k, v in sorted(r["bars_diag"].items())))
L.append("")
L.append("## ② شروطُ §④ بنصّها")
L.append("")
L.append("| الشرط | القيمة | يعبر |")
L.append("|---|---|---|")
d = r["diff_ci_new_vs_base2"]
L.append(f"| فاصلُ (الجديدة − BASE2) فوق الصفر | {cipp(d)} نقطة | {'✅' if d and d[0] > 0 else '❌'} |")
L.append(f"| الجديدة ≥ CURRENT تقديرًا نقطيًّا | {pct(n['share'])} مقابل {pct(c['share'])} | "
         f"{'✅' if n['share'] is not None and c['share'] is not None and n['share'] >= c['share'] else '❌'} |")
for (a, z), hv in zip(H, r["halves_diff"]):
    _hv = "—" if hv is None else f"{100 * hv:+.2f} نقطة"
    L.append(f"| الفرقُ عن BASE2 موجبٌ في {a}…{z} | {_hv} | {'✅' if hv is not None and hv > 0 else '❌'} |")
meas = n["entries"] >= 100 and n["exploded"] >= 15 and r["coverage"] >= 0.85
L.append(f"| «لا قياس»: إدخالاتُ الجديدة ≥ 100 ∧ منفجروها ≥ 15 ∧ التغطية ≥ 85% | {n['entries']} · {n['exploded']} · {100 * r['coverage']:.2f}% | "
         f"{'✅ قابلٌ للقياس' if meas else '❌ لا قياس'} |")
L.append("")
L.append("⟵ الترتيبُ بنصّ العقد (`test_verdict` بالاسم): «لا قياس» أوّلًا ثمّ «تُقبل» ثمّ «التعقيدُ لم يضف شيئًا» ثمّ «لا يُقبل».")
L.append("")
L.append("## ③ «من كلّ 10 أسهمٍ في القائمة الجديدة: كم انفجر»")
L.append("")
_o10 = "—" if r["of10"] is None else r["of10"]
_o10c = "—" if not r["of10_ci"] else "[" + str(r["of10_ci"][0]) + "، " + str(r["of10_ci"][1]) + "]"
L.append(f"**{_o10} من 10** · فاصلٌ عنقوديٌّ 95% {_o10c}")
L.append("")
L.append("## ④ وقفُ القاع (§⑤ · وصفٌ لا حكم · «بلغ ‏+50% قبل أن يلمس الوقف» على [D، D+19] · يومُ اللمستين ⟵ الوقفُ أوّلًا)")
L.append("")
L.append("| القائمة | SP0 = القاعُ (`pivot`) | [فاصل] | SP5 = 0.95 × القاع | [فاصل] | بلا قاع | مسافةُ الوقف (10·25·50·75·90) |")
L.append("|---|---|---|---|---|---|---|")
for k in ("NEW", "BASE2", "CURRENT"):
    p = r["pivot_stops"][k]
    dq = "—" if not p["dist_q"] else " · ".join(f"{100 * x:.1f}%" for x in p["dist_q"])
    L.append(f"| {NM[k]} | {p['SP0']['hit50_first']} من {p['SP0']['n']:,} = {pct(p['SP0']['share'])} | {ci(p['SP0']['ci95'])} | "
             f"{p['SP5']['hit50_first']} من {p['SP5']['n']:,} = {pct(p['SP5']['share'])} | {ci(p['SP5']['ci95'])} | {p['no_pivot']} | {dq} |")
t = r["tested_level_stops"]
L.append("")
L.append(f"- **وبجانبه S0 (`tested_level`) حيث وُجد في الجديدة:** S0 {t['S0']['hit50_first']} من {t['S0']['n']} · S5 {t['S5']['hit50_first']} من {t['S5']['n']} · "
         f"بلا مستوًى مختبَر {t['unknown_level']} (ترفضها بوّابةُ الإنتاج `M_لا_مستوى_مختبر` · مجمَّدةٌ بعقد H6).")
L.append("- ⚠️ **SP0 ليس وقفَ الإنتاج** (الإنتاجُ `tested_level`) ولا يُشحن · ومحورُ إدارة الخروج مُغلَق (`TRAIL_REOPEN`).")
L.append("")
L.append("## ⑤ الهبوطُ قبل ‏+50% (§⑥ · MAE = أدنى Low ÷ إغلاق D−1 − 1 · وصفٌ لا حكم)")
L.append("")
L.append("| القائمة | منفجرون | متشائمٌ [D، τ] (10·25·50·75·90) | متفائلٌ [D، τ−1] | غيرُ منفجرين | أدنى [D، D+19] لغير المنفجر (الوسيط) |")
L.append("|---|---|---|---|---|---|")
for k in ("NEW", "BASE2", "CURRENT"):
    m = r["mae"][k]
    fq = lambda q: "—" if not q else " · ".join(f"{100 * x:.1f}%" for x in q)
    _nxm = "—" if not m["non_exploded_q"] else f"{100 * m['non_exploded_q'][2]:.1f}%"
    L.append(f"| {NM[k]} | {m['exploded_n']:,} | {fq(m['pess_q'])} | {fq(m['opt_q'])} | {m['non_exploded_n']:,} | "
             f"{_nxm} |")
L.append("")
L.append("| القائمة | MAE المتشائم ≤ −10% | ≤ −20% | ≤ −30% | ≤ −50% |")
L.append("|---|---|---|---|---|")
for k in ("NEW", "BASE2", "CURRENT"):
    m = r["mae"][k]
    cells = []
    for tt in ("10", "20", "30", "50"):
        e = m["pess_le"][tt]
        cells.append(f"{e['hit']} من {e['n']} = {pct(e['share'])} {ci(e['ci95'])}")
    L.append(f"| {NM[k]} | " + " | ".join(cells) + " |")
L.append("")
L.append("- عدمُ تطابق الوسم بين عمودَي المنفجر (حارس): " + " · ".join(f"{k} {r['mae'][k]['label_mismatch']}" for k in ("NEW", "BASE2", "CURRENT")) + ".")
L.append("")
L.append("## ⑥ التنبّؤات (تُنشر ولا تُحذف)")
L.append("")
L.append("| التنبّؤ | النتيجة |")
L.append("|---|---|")
p1 = r["branch"] == 1
L.append(f"| **RB26-P1:** الفرعُ 1 «تُقبل على 2026» | {'✅' if p1 else '❌ **سقط**'} (الفرع {r['branch']} «{r['verdict']}») |")
sp0 = r["pivot_stops"]["NEW"]["SP0"]
p2 = sp0["share"] is not None and sp0["share"] < 0.5
L.append(f"| **RB26-P2:** «بلغ ‏+50% قبل SP0» أقلُّ من نصف إدخالات الجديدة | {'✅' if p2 else '❌ **سقط**'} ({pct(sp0['share'])}) |")
pm = r["mae"]["NEW"]["pess_q"]
p3 = bool(pm) and pm[2] < -0.15
_pm = "—" if not pm else f"{100 * pm[2]:.1f}%"
L.append(f"| **RB26-P3:** وسيطُ MAE المتشائم للمنفجرين في الجديدة أعمقُ من −15% | {'✅' if p3 else '❌ **سقط**'} ({_pm}) |")
L.append("")
L.append("## ⑦ البوّاباتُ المطفأة في الإنتاج (أمرُ المالك: تُطبع في كلّ نتيجة)")
L.append("")
L.append("| البند | حالتُه في الإنتاج |")
L.append("|---|---|")
for k, v in r["production_off"]:
    L.append(f"| `{k}` | {v.replace('مطفأة', '**مطفأة**', 1) if v.startswith('مطفأة') else v} |")
L.append("")
L.append("## ⑧ حدودُ الصدق (مُعلَنةٌ في العقد قبل الأرقام §⑨)")
L.append("")
L.append("- جدولُ §⑤ في العقد الأصليّ رأى 2026 وصفًا (RSI يومَ READY) ⟵ تلوّثٌ ضعيفٌ مُعلَن · والدرجةُ صُمّمت بعده على TRAIN.")
L.append("- الكونُ والوكيلُ والمطفأ كما §⑭ من العقد · وبوّابةُ المتاح لم تُقَس (لا تاريخ).")
L.append("- SP0 من شموعٍ يوميّة (لمسُ الوقف و‏+50% في يومٍ واحد ⟵ الوقفُ أوّلًا · متشائم) · ولا أفترَ ولا بري.")
L.append("- 2026 نافذةٌ واحدة (9 أشهر) · والحكمُ هنا تكرارٌ لحكم TEST لا بديلٌ عنه.")
L.append("")
L.append("🔒 لا شحن · لا تلغرام · لا `LOGIC_VERSION` · لا V4 · لا عتبة ولا جذر ولا مرساة (H6) · ولا تعديلَ للدرجة ولا لـθ · وأيُّ استعمالٍ قرارُ المالك.")
open(OUT, "w", encoding="utf-8").write("\n".join(L) + "\n")
print("ok", r["branch"], r["verdict"])
