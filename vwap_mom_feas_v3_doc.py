"""يولّد `vwap_mom_feas_v3_result.md` من `vwap_mom_feas_v3_2026-09.json` — لا رقمَ يُكتب باليد (قفلُ `VWM8`: المُخرَجُ = الملفُّ بايتًا).

    python3 vwap_mom_feas_v3_doc.py [json] [out.md]
"""
import json
import sys


def render(r):
    """نصُّ النتيجة من الـJSON (دالّةٌ نقيّة — يقرؤها `VWM8`)."""
    L = r["d_ladder"]
    lab = {250000: "250k", 500000: "500k", 1000000: "1M", 2000000: "2M", 5000000: "5M"}
    med = r["median_by_dmin"]
    tot = r["month_totals"]

    def m(arm, d, k):
        return med[arm][str(d)][k]

    def t(arm, d, k):
        return tot[arm][str(d)][k]

    def fmt(x):
        return f"{x:,}" if isinstance(x, int) else (f"{x:,.1f}".replace(".0", "") if isinstance(x, float) else str(x))

    v = r["verdict"]
    pick = r["D_MIN_pick_by_rule"]
    head = {"stop": "⛔ **لا درجةَ في 10-40 للمرّة الثالثة ⟵ المحورُ يتوقّف وتُكتب النتيجةُ كما هي** (الملحق 2 §④)",
            "pick": f"✅ **القاعدةُ اختارت `D_MIN` = {lab.get(pick, pick)}** ⟵ تُثبَّت في ملحقٍ مؤرَّخ ويتوقّف العمل حتى «ابن الأداة»",
            "no_measure": f"⚠️ **«لا قياس»** ({' · '.join(r['gates_why'])}) ⟵ لا تُطبَّق القاعدة ولا تُعَدّ المرّةَ الثالثة"}[v]
    L1 = []
    L1.append("# 📈🔎 جدوى `T-VWAP-MOM` v3 (الملحق 2: الخبرُ شرطٌ واجب) — النتيجة (عدٌّ بلا عائد)")
    L1.append("")
    L1.append(f"> الملحق `vwap_mom_prereg_addendum_2.md` (مدموجٌ قبل أيّ رقمٍ من v3 · #668) · الأداة `vwap_mom_feas.py` v3 · تشغيلة **`{r['run']}`** على `main` "
              f"`{r['main_sha'][:9]}` · الشهر **{r['month']}** ({len(r['per_day'])} جلسة · {r['seconds']:,.0f} ث) · الأرقامُ في `vwap_mom_feas_v3_2026-09.json`.")
    L1.append("> **لا R ولا عائدَ ولا قمّةَ لاحقة.** نتيجتا v1 وv2 منشورتان كما هما.")
    L1.append("")
    nm = r.get("runs_no_measure") or []
    if nm:
        L1.append(f"> ⚠️ **إفصاح — هذه التشغيلةُ الثالثة لا الثانية:** الملحق 2 §③ يقول «تُعاد التشغيلةُ مرّةً واحدة · وإن تكرّر «لا قياس» فالقرارُ للمالك» · "
                  f"والتشغيلتان {' و'.join(f'`{x}`' for x in nm)} خرجتا «لا قياس» **بصفرِ ملفِّ دقيقةٍ مُنزَّل** (21 من 21 · عطلُ بيئةٍ في صورة الرنر لا نقصُ تغطية) · "
                  "فأُصلح العطلُ (`S3E1` #671 ثمّ `S3G1` #675) وأُعيدت مرّةً ثالثة بتفويض «إصلاح العطل المُثبَت» **لا بقرار المالك** ⟵ "
                  "**اعتمادُ هذه التشغيلة أو إلغاؤها قرارُ المالك** · والإغلاقُ (§⑦) قابلٌ للرجوع بـ`VWM_REOPEN=1`.")
        L1.append("")
    od = r.get("owner_decision") or {}
    if od.get("accepted") is True:
        L1.append(f"> ✅ **قرارُ المالك ({od['date']}): «{od['text']}»** ⟵ التشغيلةُ معتمدةٌ حكمًا للمحور والإغلاقُ (§⑦) نافذ.")
        L1.append("")
    L1.append(f"## ⓪ الحكم: {head}")
    L1.append("")
    L1.append(f"- **القاعدة على وسيط A ∧ C (المجتمع H ∧ C) في اليوم:** " + " · ".join(f"{lab[d]} = {fmt(m('A', d, 'H'))}" for d in L)
              + f" ⟵ المدى المسجَّل {r['d_rule'][0]}-{r['d_rule'][1]}.")
    L1.append(f"- **حارسُ التغطية:** {'يصلح' if r['gates_ok'] else 'سقط: ' + ' · '.join(r['gates_why'])} — المجهول {r['unknown_A_lowest']['unknown']:,} من "
              f"{r['unknown_A_lowest']['denom_with_cik']:,} ممّا له CIK عند 250k (الحدّ 5%) · الأخبار مكتملة={r['news']['complete']} · فهارسُ EDGAR الناقصة "
              f"{len(r['sec']['index_missing'])} · أيّامُ الدقيقة الناقصة {len(r['days_missing'])}.")
    L1.append("")
    L1.append("## ① الوسيطُ في اليوم على كلّ درجة (قبل أيّ اختيار)")
    L1.append("")
    L1.append("| `D_MIN` | A ∧ C: H | A ∧ C: H ∧ L | D (اختبارٌ ثمّ ثبات) | D ∧ L | B ∧ C: H | B ∧ C: H ∧ L | A بلا C: H (v2) |")
    L1.append("|---|---|---|---|---|---|---|---|")
    for d in L:
        L1.append(f"| {lab[d]} | {fmt(m('A', d, 'H'))} | {fmt(m('A', d, 'HL'))} | {fmt(m('A', d, 'DH'))} | {fmt(m('A', d, 'DHL'))} | "
                  f"{fmt(m('B', d, 'H'))} | {fmt(m('B', d, 'HL'))} | {fmt(m('A', d, 'H0'))} |")
    L1.append("")
    L1.append("**مجاميعُ الشهر:**")
    L1.append("")
    L1.append("| `D_MIN` | A ∧ C: H | A ∧ C: H ∧ L | D | D ∧ L | D من A ∧ L ∧ C | المجهول (U) | B ∧ C: H |")
    L1.append("|---|---|---|---|---|---|---|---|")
    for d in L:
        hl = t("A", d, "HL")
        share = f"{100 * t('A', d, 'DH') / hl:.1f}%" if hl else "—"
        L1.append(f"| {lab[d]} | {t('A', d, 'H'):,} | {hl:,} | {t('A', d, 'DH'):,} | {t('A', d, 'DHL'):,} | {share} | {t('A', d, 'U'):,} | {t('B', d, 'H'):,} |")
    L1.append("")
    L1.append("## ② المصدران")
    L1.append("")
    n, s = r["news"], r["sec"]
    L1.append(f"- **أخبار Polygon:** {n['items']:,} خبرًا في {n['pages']} صفحة ({n['from']} ⟵ {n['to']}) · مكتمل={n['complete']} · رموزٌ بخبرٍ خاصّ (≤{r['news_max_tickers']} رموز) "
              f"{n['tickers_strict']:,} · بأيّ خبر {n['tickers_any']:,}.")
    L1.append(f"- **SEC ({' · '.join(r['sec_forms'])}):** خريطةُ الرموز {s['tickers_mapped']:,} · مودِعون في المدى {s['filers']:,} · فهارسُ يوميّة {s['index_days']} "
              f"(ناقص {len(s['index_missing'])}) · رموزُ الأحداث {s['event_symbols']:,} (بـCIK {s['with_cik']:,}) · `submissions` لزم {s['need']:,} · مجهول {s['unknown_ciks']:,}.")
    src = r["src_A_lowest_month"]
    L1.append(f"- **مصدرُ أوّل حدثٍ بمحفّز (A · 250k · الشهر):** أخبارٌ وحدَها {src['news']:,} · SEC وحدَه {src['sec']:,} · كلاهما {src['both']:,} · "
              f"وبلا CIK (أخبارٌ وحدَها) {r['nocik_A_lowest']:,} يومًا-رمزًا.")
    items = r["items_8k_A_lowest"]
    if items:
        L1.append("- **بنودُ 8-K (وصفٌ لا حكم):** " + " · ".join(f"`{k}` {v:,}" for k, v in items.items()))
    L1.append("")
    L1.append("## ③ الحساسيّة (وصفٌ لا يختار)")
    L1.append("")
    L1.append("| `D_MIN` | A ∧ C (الحاكم) | C بأيّ خبرٍ (بلا حدّ الرموز) | C بـ8-K وحدَه (بلا 6-K) |")
    L1.append("|---|---|---|---|")
    for d in L:
        L1.append(f"| {lab[d]} | {fmt(m('A', d, 'H'))} | {fmt(m('A', d, 'H_any'))} | {fmt(m('A', d, 'H_8k'))} |")
    L1.append("")
    L1.append("## ④ التنبّؤات (تُنشر ولا تُحذف)")
    L1.append("")
    L1.append("| التنبّؤ | النتيجة |")
    L1.append("|---|---|")
    p8 = all(m("A", d, "H") > 40 for d in L)
    L1.append(f"| **P8:** لا درجةَ في 10-40 (A ∧ C فوق 40 في الدرجات الخمس) | {'✅' if p8 else '❌ **سقط**'} ({', '.join(fmt(m('A', d, 'H')) for d in L)}) |")
    p9 = src["sec"] > src["news"]
    L1.append(f"| **P9:** SEC وحدَه أكثرُ من Polygon وحدَه عند 250k | {'✅' if p9 else '❌ **سقط**'} ({src['sec']:,} مقابل {src['news']:,}) |")
    hl0 = t("A", L[0], "HL")
    p10 = hl0 > 0 and t("A", L[0], "DH") >= hl0 / 2
    L1.append(f"| **P10:** D بعد نصف A ∧ L ∧ C على الأقلّ عند 250k | {'✅' if p10 else '❌ **سقط**'} ({t('A', L[0], 'DH'):,} من {hl0:,}) |")
    vc = r["v2_check"]
    p11 = vc["compared"] > 0 and vc["mismatch"] == 0
    L1.append(f"| **P11:** الإعادةُ بلا C تطابق v2 في كلّ الأيّام والدرجات | {'✅' if p11 else '❌ **سقط**'} ({vc['mismatch']} فرقًا من {vc['compared']}) |")
    L1.append("")
    L1.append("## ⑤ فحصُ الإعادة")
    L1.append("")
    L1.append(f"- مقابل v2 المنشورة: **{vc['mismatch']} فرقًا من {vc['compared']}** خانة (يوم × ذراع × درجة) · والفحصُ الداخليّ (أحداثُ v3 بلا C = `day_events`): "
              f"**{r['self_mismatch']}** فرقًا.")
    if vc.get("examples"):
        L1.append("- أمثلةُ الفرق (يوم · خانة · v2 · الآن): " + " · ".join(f"{e[0]} {e[1]} {e[2]} ⟵ {e[3]}" for e in vc["examples"][:5]))
    L1.append("")
    L1.append("## ⑥ حدودُ الصدق")
    L1.append("")
    L1.append("- **«حقيقيّ» لا يُميَّز آليًّا** (العقد §⑨) — المقيسُ وجودُ خبرٍ خاصٍّ بالشركة أو إيداعٍ رسميّ · وخبرُ ردّ الفعل داخل النافذة يُحتسب.")
    L1.append("- **CIK الحاليّ:** المشطوبُ أو المغيِّرُ رمزَه بعد سبتمبر بلا إيداعات (تقليلٌ لـC) · والصناديقُ بلا CIK أخبارُها وحدَها.")
    L1.append("- **D** قد يكون التصاقًا بالفيواب لا عودةً بعد اندفاع (لا عتبةَ ابتعادٍ في العقد) · وشهرٌ واحدٌ لا ثلاثُ سنوات.")
    _nc, _dc = r["nocik_A_lowest"], r["unknown_A_lowest"]["denom_with_cik"]
    if _nc + _dc:
        L1.append(f"- **بلا CIK:** {_nc:,} من {_nc + _dc:,} يومًا-رمزًا من A بلا C عند 250k ({100 * _nc / (_nc + _dc):.1f}%) لا رمزَ لها في `company_tickers.json` ⟵ "
                  "محفّزُها من الأخبار وحدَها (SEC معلومٌ صفرًا) · فالمجتمعُ الحاكم **أصغرُ** ممّا لو عُرف CIK لها — ولا يقرّبه هذا إلى 10-40.")
    L1.append("")
    if v == "stop":
        L1.append("## ⑦ الإغلاقُ المُنفَّذ (الملحق 2 §④)")
        L1.append("")
        L1.append("- `vwap_mom_feas.py` يخرج **8** قبل أيّ عمليّة (لا تنزيلَ ولا شبكة) ما لم يكن `VWM_REOPEN=1` حرفيًّا · ومُدخَلُ الـworkflow `reopen` افتراضُه `0` ⟵ مُغلَق (`VWM9`).")
        L1.append("- **ولا يُعاد فتحُه إلّا بثلاثةٍ معًا:** ① مصدرٌ أو محورٌ جديدٌ لم يُقَس · ② تسجيلٌ مسبقٌ جديد (**لا ملحقَ رابعٌ** لتعديل المجتمع) · ③ إذنُ المالك.")
        L1.append("- ما لا يُغلَق: نتائجُ v1/v2/v3 وملفّاتُها تبقى منشورة · وصفوفُ الدفتر (`nayef_verbatim`) كما هي.")
        L1.append("")
    L1.append("🔒 لا شحن · لا تلغرام · لا تغييرَ في `Super_stock.py` ولا في الجذور ولا العتبات.")
    return "\n".join(L1) + "\n"


if __name__ == "__main__":
    _j = sys.argv[1] if len(sys.argv) > 1 else "vwap_mom_feas_v3_2026-09.json"
    _o = sys.argv[2] if len(sys.argv) > 2 else "vwap_mom_feas_v3_result.md"
    _r = json.load(open(_j, encoding="utf-8"))
    open(_o, "w", encoding="utf-8").write(render(_r))
    print("ok", _r["verdict"], _r["D_MIN_pick_by_rule"])
