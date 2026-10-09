# -*- coding: utf-8 -*-
"""🧭🏁 RANKING_RESULT.md من rank_summary.json وجدول الحالات — كلُّ رقمٍ من المخرَج الملتزَم (لا رقمَ باليد)."""


def _p(c):
    return "—" if not c or c[2] is None else f"{c[0]}/{c[1]} = {c[2]*100:.1f}% [{c[3]*100:.1f}، {c[4]*100:.1f}]"


def _d(x):
    if not x or x.get("point") is None:
        return "—"
    return f"{x['point']:+.3f} · 95% [{x['ci95'][0]:+.3f}، {x['ci95'][1]:+.3f}] · 98.33% [{x['ci9833'][0]:+.3f}، {x['ci9833'][1]:+.3f}] (عناقيد {x['clusters']})"


def render(S, eps, anc):
    V = [v for v in S["capture"] if v not in ("bot_operational", "bot_standardized", "random_U", "random_P")]
    c = S["capture"]; f = S["fidelity"]; d = S["daily"]
    L = ["# 🧭🏁 RANKING_RESULT — المرتِّبُ تحت ميزانيةٍ ثابتة (مولَّدٌ من `out/rank_summary.json`)", "",
         f"> العقد `RANKING_PROTOCOL.md` (مدموجٌ قبل أيّ ترتيب) · الوسم **{S['label']}** · المرتِّب {S['ranker']} · تشغيلةُ إعادة البناء {S['run_id']}",
         f"> جلساتٌ محسوبة {S['sessions_computed']} · جلساتُ التقييم {S['eval_sessions']} · الوحدات {S['units']} (قابلةٌ للتقييم {S['units_evaluable']}) · "
         f"الحلقات {S['episodes']} (قابلةٌ للتقييم **{S['episodes_evaluable']}** · رموز {S['tickers_evaluable']})", "",
         "## ① أمانةُ إعادة البناء (قبل أيّ رقمِ ترتيب)",
         f"- F1 وسيطُ |الخطأ النسبيّ| لعدد PASS مقابل المخزَّن: {f['F1_pass_abs_rel_err_median']} ({f['dates_F1']} تاريخًا)",
         f"- F2 وسيطُ استرجاع جدار اللمستين: {f['F2_wall_recall_median']} · جاكارد {f['F2_wall_jaccard_median']} ({f['dates_F2']} تاريخًا)",
         f"- F3 وسيطُ الكون المعاد ÷ valid المخزَّن: {f['F3_universe_ratio_median']}",
         f"- وسمُ خطّ الأساس التشغيليّ: **{f['operational_baseline_label']}** · اتّساقُ مراحل الجدار مع الاختبار السابق: {f['stage_consistency_with_previous_test']}", "",
         "## ② العبءُ اليوميّ (وسيط · مدى)",
         f"- الكون {d['universe_median']} · مجتمعُ المحرّك {d['pool_median']} {d['pool_range']} · البوت PASS {d['bot_pass_median']} {d['bot_pass_range']}",
         f"- أقصى قائمة: 25 ⟵ {d['shortlist_max'][25]} · 50 ⟵ {d['shortlist_max'][50]} · 108 ⟵ {d['shortlist_max'][108]} · وسيطُ نسبة الكون عند 108: {d['pct_universe_108_median']}%",
         f"- وسيطُ المراحل: {d['stage_median']} · وسيطُ الأصناف الزمنيّة: {d['temporal_median']}", "",
         "## ③ الالتقاط — الحلقات (التاريخُ الدقيق والمبكر منفصلان أبدًا)",
         "| النظام | K | دقيق (Wilson 95%) | مبكر 5 جلسات (Wilson 95%) | وحدات دقيق | وحدات مبكر |", "|---|---|---|---|---|---|"]
    for v in V:
        for K in (25, 50, 108):
            x = c[v][K]
            L.append(f"| {v} | {K} | {_p(x['exact'])} | {_p(x['early'])} | {x['unit_exact'][0]}/{x['unit_exact'][1]} | {x['unit_early'][0]}/{x['unit_early'][1]} |")
    bo = c["bot_operational"]
    L.append(f"| البوت تشغيليًّا (حجمُه الفعليّ · وسيط {bo['daily_size_median']}) | — | {_p(bo['exact'])} | {_p(bo['early'])} | {bo['unit_exact'][0]}/{bo['unit_exact'][1]} | {bo['unit_early'][0]}/{bo['unit_early'][1]} |")
    for K in (25, 50, 108):
        bs = c["bot_standardized"][K]
        L.append(f"| البوت بميزانيةٍ معيارية (rank_key) | {K} | {bs['exact'][0]}/{bs['exact'][1]} | {bs['early'][0]}/{bs['early'][1]} | — | — |")
    for K in (25, 50, 108):
        r = c["random_U"][K]
        L.append(f"| عشوائيٌّ من الكون R-U | {K} | متوقَّع {r['exact_expected']} · MC 95% [{r['exact_mc']['p2_5']}، {r['exact_mc']['p97_5']}] | "
                 f"متوقَّع {r['early_expected']} · MC 95% [{r['early_mc']['p2_5']}، {r['early_mc']['p97_5']}] | — | — |")
    for K in (25, 50, 108):
        L.append(f"| عشوائيٌّ من المجتمع R-P | {K} | متوقَّع {c['random_P'][K]['exact_expected']} | — | — | — |")
    L += ["", "### توزيعُ رتب الحالات يومَ القرار", "| المتغيّر | 1–25 | 26–50 | 51–108 | أبعد من 108 | خارج المجتمع | وسيطُ الرتبة | المراحل يومَ القرار |", "|---|---|---|---|---|---|---|---|"]
    for v in V:
        b = c[v]["rank_buckets"]
        L.append(f"| {v} | {b['1-25']} | {b['26-50']} | {b['51-108']} | {b['>108']} | {b['not_in_pool']} | {c[v]['rank_median_in_pool']} | {c[v]['stage_at_T']} |")
    L += ["", "## ④ المقارنة مع خطّ الأساس (K = 108 · بوتستراب عنقوديّ على الرموز · seed 20261009)",
          "| المتغيّر | النوع | مقابل التشغيليّ | مقابل المعياريّ 108 | أدنى LOO رمز (أيّ رمز) | أدنى LOO تاريخ | الطيّ الاستكشافيّ | الطيّ التحقّقيّ |", "|---|---|---|---|---|---|---|---|"]
    for v in V:
        for kind in ("exact", "early"):
            x = S["comparisons"][v][kind]; fo = x["folds"]
            L.append(f"| {v} | {kind} | {_d(x['vs_operational'])} | {_d(x['vs_standardized_108'])} | {x['loo_vs_operational']['min_ticker']} ({x['loo_vs_operational']['argmin_ticker']}) | "
                     f"{x['loo_vs_operational']['min_date']} | {fo['DISCOVERY']['variant']}−{fo['DISCOVERY']['bot_op']} من {fo['DISCOVERY']['episodes']} | "
                     f"{fo['VALIDATION']['variant']}−{fo['VALIDATION']['bot_op']} من {fo['VALIDATION']['episodes']} |")
    L += [f"- الطيّان بلا رمزٍ مشترك: {S['folds_disjoint_tickers']} · حساسيّةٌ بلا الحلقات الغامضة: {S['sensitivity_unambiguous']}",
          f"- فرضيّةُ H-C (الالتقاط الدقيق 108 لـC حسب الصنف الزمنيّ يومَ القرار): {S['H_C_by_temporal_class']}", "",
          "## ⑤ الحالات (حلقة · المتغيّر C إلا ما ذُكر)", "| الحلقة | T_e | الطيّ | فيصل | الغموض | المرحلة يومَها | البوت | A | B | C | دقيق C 25/50/108 | مبكر C 108 | أوّلُ إدراج C (رتبة · مرحلة · جلساتٌ قبل) |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for e in eps:
        if not e.get("evaluable"):
            L.append(f"| {e['episode_id']} | {e['T_e']} | {e['fold']} | {e['first_state']} | {e['ambiguity'] or '—'} | UNEVALUABLE ({e.get('unevaluable_reason')}) | — | — | — | — | — | — | — |")
            continue
        L.append(f"| {e['episode_id']} | {e['T_e']} | {e['fold']} | {e['first_state']} | {e['ambiguity'] or '—'} | {e['stage_T']} ({e.get('first_failed_T') or e.get('tech_T') or ''}) | "
                 f"{e['bot_res_T']}{('/' + e['bot_gate_T']) if e.get('bot_gate_T') else ''} | {e.get('A_rank') or '—'} | {e.get('B_rank') or '—'} | {e.get('C_rank') or '—'} | "
                 f"{e.get('C_exact_25')}/{e.get('C_exact_50')}/{e.get('C_exact_108')} | {e.get('C_early_108')} | "
                 f"{(str(e.get('C_first_rank')) + ' · ' + str(e.get('C_first_stage')) + ' · ' + str(e.get('C_first_lead'))) if e.get('C_first_incl') else '—'} |")
    L += ["", "## ⑥ التشخيص (الفئةُ الأوّليّة لكلّ متغيّر · الكلّ ثمّ الطيّ الاستكشافيّ وحدَه)"]
    for v in V:
        L.append(f"- {v}: {S['failures_primary'][v]} · الاستكشافيّ: {S['failures_primary_discovery'][v]}")
    L += ["", "## ⑦ DKI · SXTC · HUBC (كلُّ جلسةٍ في `out/rank_anchor_cases.csv`)"]
    for tk in ("DKI", "SXTC", "HUBC"):
        xs = [a for a in anc if a["ticker"] == tk]
        inu = [a for a in xs if a["in_universe"]]
        st = {}
        for a in inu:
            st[a["stage"]] = st.get(a["stage"], 0) + 1
        best = {v: min([int(a[f"{v}_rank"]) for a in inu if a.get(f"{v}_rank") not in ("", None)] or [None], key=lambda z: (z is None, z)) for v in V}
        L.append(f"- {tk}: جلساتٌ في الكون {len(inu)}/{len(xs)} · المراحل {st} · البوت PASS {sum(1 for a in inu if a['bot'] == 'PASS')} · أفضلُ رتبة {best}")
    for v, x in (S.get("posthoc") or {}).items():
        L += ["", f"## ⑦-ب التصحيحُ اللاحق {v} (`RANKING_PROTOCOL_ADDENDA.md` · {x['label']})",
              f"- اختبارُ القبول (i) مستهدَف DKI/NUWE: {x['acceptance_i_targeted']} · (ii) الاستكشافيّ: {x['acceptance_ii_discovery']} ⟵ **{'مقبول' if x['acceptance_passed'] else 'مرفوض'}**",
              f"- مكسوبٌ مقابل C (دقيق 108): {x['gained_vs_C']} · مفقود: {x['lost_vs_C']} · مبكر مكسوب {x['early_gained_vs_C']} · مفقود {x['early_lost_vs_C']}",
              f"- معاييرُ §⑪ لو كان مسجَّلًا (للعلم وحدَه): {x['criteria_if_it_were_preregistered']}"]
    L += ["", "## ⑧ التنبّؤات المسجَّلة", f"- {S['predictions']}", "", "## ⑨ الحكم بقاعدة §⑪",
          f"- المتغيّرُ المفضَّل (قاعدة §⑩ · بين A/B/C المسجَّلة وحدَها): **{S['preferred_variant']}** — اختيارٌ بين ثلاثة ⟵ عدمُ يقينِ اختيارٍ مُعلَن (بونفيروني 98.33%)",
          f"- **{S['verdict']['verdict']} — {S['verdict']['text']}** · {S['verdict'].get('criteria')}", ""]
    return "\n".join(L) + "\n"
