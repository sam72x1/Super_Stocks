"""يولّد T_REBUILD_b3_result_add4.md من data/b3_add4_2026-10-29.json — لا رقمَ يُكتب باليد."""
import json, sys
J, OUT = sys.argv[1], sys.argv[2]
r = json.load(open(J, encoding="utf-8"))
it = r["items"]; cols = it["cols"]
def pct(x): return "—" if x is None else f"{100 * x:.2f}%"
def pp(x): return f"{100 * x:+.2f}"
def ci(a): return "—" if a is None else f"[{a[0]:.3f}، {a[1]:.3f}]"
def cipp(a): return f"[{pp(a[0])}، {pp(a[1])}]"
vc = {}
for v in cols.values(): vc[v["verdict"]] = vc.get(v["verdict"], 0) + 1
L = []
L.append("# 🧭 `T-REBUILD` §⑦ — الجردُ المقصوص (B3) بالملحق 4: العددُ تطابق · ولا بندَ «تضيف» ولا «تنقص»")
L.append("")
L.append(f"> الملحق 4 (#669) · المرجعُ `data/{r['reference']['file']}` (تشغيلة `bases` **`{r['reference']['run']}`** على `{r['reference']['main_sha'][:9]}` · #672) · "
         f"تشغيلةُ B3 **`{r['run']}`** على main `{r['main_sha'][:9]}` ({r['created_at']}) بتحضير تشغيلة المرجع نفسِها (`prep_run={r['prep_run']}`) · "
         f"الملحق 2 ببصمته `{r['addendum2_sha'][:12]}…` · الأرقامُ في `data/b3_add4_2026-10-29.json`.")
L.append("> **ملحقةٌ لا ماحية:** نتيجةُ «لا حكم» الأولى (`T_REBUILD_b3_result.md` · 3,266 مقابل 3,267) منشورةٌ كما صدرت.")
L.append("")
L.append(f"## ⓪ الحكم: العددُ تطابق ({r['entries']:,} = {r['entries_expected']:,} · الأساس {r['base']}) — البنودُ الثمانية: "
         + " · ".join(f"«{k}» {n}" for k, n in sorted(vc.items(), key=lambda x: -x[1])))
L.append("")
L.append(f"- **الوحدات:** {it['units']:,} إدخالًا جديدًا لـBASE2 على TRAIN ({r['train_sessions']} جلسة) · موسومٌ {it['labelled']:,} · منفجرٌ {it['exploded']:,} "
         f"(حصّةُ الأساس {pct(it['base_share'])}) · {it['symbols']:,} رمزًا · {it['strata']} طبقة · بونفيروني m = {it['m']} · z = {it['z']}.")
L.append("- **القاعدة (الملحق 2 · §⑦ بنصّ الملحق 1 §②):** «تضيف» = فاصلُ فرق الحصّة فوق الصفر ∧ فاصلُ MH فوق 1 ∧ العبء ≥ 0.15/جلسة · «تنقص» = فاصلُ الفرق تحت الصفر · "
         "و«لا تفرّق — لا مقارنة» حين يعبر الكلُّ (لا مجموعةَ مقارنة).")
L.append("")
L.append("| البند | في الإنتاج | يعبر | حصّةُ المنفجرين بين العابرين | الفرقُ عن الأساس (نقطة) [فاصل] | MH [فاصل] | العبء/جلسة | الحكم |")
L.append("|---|---|---|---|---|---|---|---|")
for k, v in cols.items():
    mh = "—" if v["mh_rr"] is None else f"{v['mh_rr']:.3f} {ci(v['mh_ci'])}"
    L.append(f"| `{k}` | {r['prod_state'][k]} | {v['pass']:,} | {pct(v['share_pass'])} | {pp(v['diff'])} {cipp(v['diff_ci'])} | {mh} | {v['burden']} | **{v['verdict']}** |")
L.append("")
L.append("## ① التنبّؤ (يُنشر ولا يُحذف)")
L.append("")
a = cols["ANCHOR_TWO_TOUCH"]
ok = a["verdict"] == "تنقص"
L.append("| التنبّؤ | النتيجة |")
L.append("|---|---|")
L.append(f"| **RB-P4:** مرساةُ اللمستين «تنقص» على TRAIN | {'✅' if ok else '❌ **سقط**'} — «{a['verdict']}» (الفرق {pp(a['diff'])} {cipp(a['diff_ci'])} · MH {a['mh_rr']:.3f} {ci(a['mh_ci'])} · يعبرها {a['pass']:,} من {it['units']:,}) |")
L.append("")
L.append("## ② الوقفُ والدفعات (وصفٌ لا حكم · على العابرين بمستوًى مختبَر)")
L.append("")
s = r["stop"]
L.append(f"- **بلغ ‏+50% قبل الوقف:** S0 (المستوى المختبَر) {s['S0_hit50_first']} من {s['n']} = {pct(s['S0_share'])} · S5 (−5%) {s['S5_hit50_first']} من {s['n']} = {pct(s['S5_share'])} · "
         f"فرقُ S5 − S0 {cipp(s['S5_minus_S0_ci95'])} نقطة.")
L.append("")
L.append("| الدفعة | تعبّأت | [فاصل] | المنفجرون | التُقطوا | [فاصل] | فوق السعر |")
L.append("|---|---|---|---|---|---|---|")
for t in r["tranches"]:
    L.append(f"| {t['k'] + 1} | {t['fill']} من {t['n']} = {pct(t['fill_share'])} | {ci(t['fill_ci95'])} | {t['exploded_n']} | {t['caught']} = {pct(t['caught_share'])} | {ci(t['caught_ci95'])} | {t['above_price']} |")
L.append("")
L.append(f"- {r['t0_equals_s0']}.")
L.append("")
L.append("## ③ ما لم يُقَس")
L.append("")
for k, v in r["not_measured"].items():
    L.append(f"- `{k}`: {v}.")
L.append("")
L.append("## ④ البوّاباتُ المطفأة في الإنتاج (أمرُ المالك: تُطبع في كلّ نتيجة)")
L.append("")
L.append("| البند | حالتُه في الإنتاج |")
L.append("|---|---|")
for k, v in r["prod_off"]:
    L.append(f"| `{k}` | {v.replace('مطفأة', '**مطفأة**', 1) if v.startswith('مطفأة') else v} |")
L.append("")
L.append("## ⑤ فرقُ المرجع المُعاد عن الأوّل (وصفٌ لمراجعة البيانات · لا يدخل حكمًا · الملحق 4 §③)")
L.append("")
L.append("| النافذة | الأساس | الحقل | المرجعُ الأوّل | المُعاد |")
L.append("|---|---|---|---|---|")
for w, bs in r["bases_diff_vs_first"].items():
    for b, ks in bs.items():
        for k, (x0, x1) in ks.items():
            L.append(f"| {w} | {b} | {k} | {x0:,} | {x1:,} |")
L.append("")
L.append("## ⑥ حدودُ الصدق")
L.append("")
nc = [k for k, v in cols.items() if v["verdict"] == "لا تفرّق — لا مقارنة"]
L.append(f"- **{len(nc)} بنودٍ يعبرها كلُّ إدخالٍ** (" + " · ".join(f"`{k}`" for k in nc) + ") ⟵ لا مجموعةَ مقارنة داخل BASE2 ⟵ «لا تفرّق — لا مقارنة» وصفٌ لبناء الأساس لا حكمٌ على البند.")
_nd = it['units'] - cols['RSI_OVERSOLD']['pass']
L.append(f"- `RSI_OVERSOLD` يُسقط {'إدخالًا واحدًا' if _nd == 1 else str(_nd) + ' إدخالًا'} فقط ⟵ فاصلُ MH {ci(cols['RSI_OVERSOLD']['mh_ci'])} من وحدةٍ واحدة تقريبًا "
         f"(بوتستراب بلا قيمة في {cols['RSI_OVERSOLD']['boot_nan']} من 2000) ⟵ لا يُقرأ.")
L.append("- **مرساةُ اللمستين قِيست ولا تُشحَن** (مجمَّدةٌ بعقد H6) · والوقفُ والدفعاتُ على شموعٍ يوميّة (لمسُ الوقف و‏+50% في يومٍ واحد ⟵ الوقفُ أوّلًا).")
L.append("- **TRAIN وحدَه** (2023-01 ⟵ 2024-03) · ولا VAL ولا TEST في هذا الجرد بالبناء.")
L.append("")
L.append("🔒 لا شحن · لا تلغرام · لا `LOGIC_VERSION` · لا V4 · لا عتبة ولا جذر ولا مرساة · وأيُّ استعمالٍ قرارُ المالك.")
open(OUT, "w", encoding="utf-8").write("\n".join(L) + "\n")
print("ok", vc)
