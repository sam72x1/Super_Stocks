#!/usr/bin/env python3
"""🗂️ `T-CASE31` — فهرسُ السمات المُلزِم (العقد `T_CASE31_prereg.md` §③) — نقيٌّ بلا شبكة.

القائمةُ **تُولَّد** من القوائم المعلنة أدناه ولا تُكتب باليد: `python3 fm_forensics/case31/case31_catalog.py` يطبع العددَ والبصمة ·
`--list` يطبع كلَّ اسمٍ بنوعه وذراعه. الاسمُ = `{إطار}.{عائلة}.{قياس}` · والنوعُ `num` (رقم) أو `bool` · والذراعُ `AB` (من الشموع
وحدَها ⟵ الذراعان) أو `A` (يلزمه مصدرٌ غيرُ الشموع ⟵ الذراع أ وحدَها) · و`delta=True` ⟵ يُضاف له `.d5` و`.d10` (التغيّرُ في 5 و10 جلسات).
مكتبةُ الحساب (`case31_feat.py`) **يجب أن تُخرج هذه الأسماء بالضبط** (قفل `C31-2`).
"""
import hashlib
import sys

TFS = ("D", "H4", "W")                      # يوميّ · 4 ساعات (جلسةٌ ممتدّة) · أسبوعيّ (من اليوميّ · الأسبوعُ الجاري جزئيًّا حتى يوم القرار)
MA_LENS = (5, 8, 10, 13, 15, 20, 21, 30, 34, 40, 50, 55, 80, 89, 100, 144, 150, 200)      # نصُّ المالك
MA_KINDS = ("sma", "ema")
MA_PAIRS = ((5, 20), (8, 15), (8, 21), (10, 20), (13, 34), (20, 50), (21, 55), (34, 89), (40, 80), (50, 100), (50, 200), (100, 200))
CANDLES = ("hammer", "inv_hammer", "bull_engulf", "piercing", "morning_star", "bull_harami", "three_soldiers", "dragonfly",
           "tweezer_bottom", "bull_marubozu", "shooting_star", "bear_engulf", "dark_cloud", "evening_star", "bear_harami",
           "three_crows", "gravestone", "hanging_man", "doji", "spinning_top", "inside_bar", "outside_bar")
QUANTS = (20, 40, 60, 80)                   # حدودُ الشروط الثنائيّة للرقميّ: مئينيّاتُ **كلّ الصفوف** (منفجرين وضابطة معًا ⟵ لا تعتمد على الوسم)


def catalog():
    """⟵ قائمةُ (الاسم، النوع، الذراع، delta) مرتّبةً كما تُولَّد."""
    F = []

    def add(name, kind="num", arm="AB", delta=None):
        F.append((name, kind, arm, (kind == "num") if delta is None else bool(delta)))

    for tf in TFS:
        # ②-أ المتوسّطات
        for k in MA_KINDS:
            for n in MA_LENS:
                add(f"{tf}.{k}{n}.dist")                       # الإغلاق ÷ المتوسّط − 1
                add(f"{tf}.{k}{n}.slope")                      # المتوسّط ÷ قيمته قبل 5 شموع − 1
                add(f"{tf}.{k}{n}.above", "bool")              # الإغلاقُ فوقه
                add(f"{tf}.{k}{n}.since", delta=False)         # شموعٌ منذ آخر تقاطعٍ للإغلاق معه (سقف 250)
            for a, b in MA_PAIRS:
                add(f"{tf}.{k}{a}x{b}.gap")                    # السريع ÷ البطيء − 1
                add(f"{tf}.{k}{a}x{b}.xup10", "bool")          # تقاطعٌ صاعد في آخر 10 شموع
                add(f"{tf}.{k}{a}x{b}.xdn10", "bool")          # تقاطعٌ هابط في آخر 10 شموع
            add(f"{tf}.{k}.stack")                             # نسبةُ الأزواج المتجاورة المرتّبة صعودًا (الأقصر فوق الأطول)
            add(f"{tf}.{k}.nabove")                            # عددُ المتوسّطات التي فوقها الإغلاق
        # ②-ب المؤشّرات (الإعداداتُ المعروفة)
        for n in (7, 14, 21):
            add(f"{tf}.rsi{n}")
        add(f"{tf}.rsi14.bulldiv", "bool")
        add(f"{tf}.rsi14.beardiv", "bool")
        for m in ("line_p", "sig_p", "hist_p"):
            add(f"{tf}.macd.{m}")
        for m in ("hist_pos", "xup10", "xdn10"):
            add(f"{tf}.macd.{m}", "bool")
        add(f"{tf}.kst.val")
        add(f"{tf}.kst.diff")
        add(f"{tf}.kst.xup10", "bool")
        for m in ("k", "d", "j"):
            add(f"{tf}.kdj.{m}")
        add(f"{tf}.stoch.k")
        add(f"{tf}.stoch.d")
        add(f"{tf}.stoch.xup10", "bool")
        add(f"{tf}.cci20")
        add(f"{tf}.willr14")
        add(f"{tf}.mfi14")
        add(f"{tf}.kvo.pos", "bool")
        add(f"{tf}.kvo.above_sig", "bool")
        for m in ("adx14", "pdi14", "mdi14", "di_diff"):
            add(f"{tf}.{m}")
        add(f"{tf}.atr14_p")
        add(f"{tf}.bb.width")
        add(f"{tf}.bb.pctb")
        add(f"{tf}.bb.squeeze_rank")
        add(f"{tf}.kc.pos")
        add(f"{tf}.kc.squeeze", "bool")
        for m in ("above_cloud", "below_cloud", "tk_bull", "chikou_bull"):
            add(f"{tf}.ichi.{m}", "bool")
        add(f"{tf}.ichi.thick_p")
        add(f"{tf}.don20.pos")
        add(f"{tf}.don20.low_age", delta=False)
        add(f"{tf}.don55.pos")
        add(f"{tf}.psar.bull", "bool")
        add(f"{tf}.psar.since", delta=False)
        if tf != "W":
            add(f"{tf}.vwap_w.dist")
            add(f"{tf}.vwap_m.dist")
        # ②-د البنية
        add(f"{tf}.st.nr4", "bool")
        add(f"{tf}.st.nr7", "bool")
        add(f"{tf}.st.green10")
        add(f"{tf}.st.green20")
        add(f"{tf}.st.hl_run", delta=False)
        add(f"{tf}.st.inside10", delta=False)
        # ②-ج الشموع (اليوميّ و4 ساعات — نصُّ المالك)
        if tf != "W":
            for c in CANDLES:
                add(f"{tf}.cdl.{c}.any10", "bool")
                add(f"{tf}.cdl.{c}.ago", delta=False)
    # إعداداتُ البوت المحميّة كما هي (دوالُّ `Super_stock` بالاسم · اليوميّ)
    for m in ("rsi14", "macd_hist_p", "kst_diff", "mfi", "willr", "atr_p", "bb_pctb", "stochrsi_k", "fsto_k", "cci14", "adx",
              "ema30_dist", "ema50_dist"):
        add(f"D.bot.{m}")
    add("D.bot.klinger_bull", "bool")
    # ②-ج النماذج · وايكوف · فيبوناتشي · الدعوم والمقاومات (اليوميّ · وثلاثةٌ على 4 ساعات)
    for p in ("dbl_bottom", "w_break", "inv_hs", "fall_wedge", "bull_flag", "cup_handle", "tri_asc", "tri_desc", "tri_sym",
              "flat_base15", "flat_base25"):
        add(f"D.pat.{p}", "bool")
    for p in ("dbl_bottom", "flat_base15"):
        add(f"H4.pat.{p}", "bool")
    add("D.wyck.spring10", "bool")
    add("D.wyck.lps15", "bool")
    add("H4.wyck.spring10", "bool")
    add("D.fib.retr")
    add("D.fib.near_level", "bool")
    add("D.sr.sup_tested", "bool")
    add("D.sr.sup_touches", delta=False)
    add("D.sr.sup_dist")
    add("D.sr.res_tested", "bool")
    add("D.sr.res_touches", delta=False)
    add("D.sr.res_dist")
    for m in ("above_n", "above_dist", "below_n", "below_dist"):
        add(f"D.gap.{m}", delta=False)
    # ①-و السعر
    for m in ("close", "drop252", "atl_dist", "base20_w", "base40_w", "base60_w", "round_dist", "ret1", "ret5", "ret10", "ret20",
              "ret60", "range_d", "uwick5", "lwick10"):
        add(f"px.{m}")
    for m in ("atl_age", "low60_age", "base_len", "below1_30", "expl_n", "expl_age"):
        add(f"px.{m}", delta=False)
    for m in ("sweep10", "sweep_reclaim", "near1", "expl_due"):
        add(f"px.{m}", "bool")
    # ①-ز الحجم والتجميع
    for m in ("usd_med20", "usd_d", "dry5_20", "spike_d", "updown20", "obv_slope10", "obv_slope20", "adl_slope10", "adl_slope20",
              "cmf20"):
        add(f"vol.{m}")
    add("vol.spike10", "bool")
    # ①-ح الشورت (FINRA يوميّ ⟵ الذراعان) والاقتراض (حصادُ البوت ⟵ أ)
    for m in ("ratio_d", "ratio5", "ratio10", "vol_d"):
        add(f"sh.{m}")
    add("sh.vol_le40k", "bool")
    add("bw.avail", arm="A", delta=False)
    add("bw.fee", arm="A", delta=False)
    add("bw.avail_le20k", "bool", "A")
    # ①-أ الهوية (أ)
    for m in ("float", "shares", "mcap", "float_turn_d", "float_turn20", "age_sessions"):
        add(f"id.{m}", arm="A", delta=False)
    for m in ("is_adr", "is_shell_sic", "has_options", "foreign_filer", "c_us", "c_cn_hk", "c_sg", "c_il", "c_other",
              "s_health", "s_tech", "s_finance", "s_consumer", "s_other"):
        add(f"id.{m}", "bool", "A")
    # ①-ب/ج/د/هـ الشركة والتمويل والإدراج والملكيّة والتقويم (EDGAR وياهو ⟵ أ)
    for m in ("rs_n365", "rs_n_all", "rs_age_days"):
        add(f"cp.{m}", arm="A", delta=False)
    add("cp.rs_le60", "bool", "A")
    for m in ("n424b_90", "n424b_365", "age_424b", "n8k_30", "n8k_3", "n_form4_90", "n_13dg_90", "defic_days_left", "results_age"):
        add(f"ed.{m}", arm="A", delta=False)
    for m in ("shelf_active", "s1_365", "proxy_75", "nt_365", "defic_365", "name_change_365", "results_due30"):
        add(f"ed.{m}", "bool", "A")
    # ①-ك حالتُه عند البوت (لقطاتُ git وسجلّاتُ الأدوات ⟵ أ)
    for m in ("nw_days", "readiness", "score", "n_out"):
        add(f"bot.{m}", arm="A", delta=(m == "readiness"))
    for m in ("nw_tracked", "wall_any", "wall_level", "wall_base", "in_list", "in_pullback", "blocked", "faisal_post30",
              "tool20_split_hunter", "tool20_split_filter", "tool20_method", "tool20_press", "tool20_envelope", "tool20_three"):
        add(f"bot.{m}", "bool", "A")
    # ①-ل العدوى (كونُ البوت ⟵ أ)
    for m in ("sector3", "industry3", "country3"):
        add(f"ct.{m}", "bool", "A")
    return F


def expanded():
    """⟵ الأسماءُ كلُّها بعد إضافة `.d5`/`.d10` للرقميّ ذي الدلتا: [(الاسم، النوع، الذراع)]."""
    out = []
    for name, kind, arm, delta in catalog():
        out.append((name, kind, arm))
        if delta:
            out.append((name + ".d5", "num", arm))
            out.append((name + ".d10", "num", arm))
    return out


def conditions(names=None):
    """⟵ أسماءُ الشروط الثنائيّة المجرَّبة: للرقميّ أربعةٌ (`<q20` · `<q40` · `>q60` · `>q80`) وللمنطقيّ اثنان (`=1` · `=0`)."""
    out = []
    for name, kind, arm in (names or expanded()):
        if kind == "bool":
            out += [(name + "=1", arm), (name + "=0", arm)]
        else:
            out += [(f"{name}<q{QUANTS[0]}", arm), (f"{name}<q{QUANTS[1]}", arm), (f"{name}>q{QUANTS[2]}", arm), (f"{name}>q{QUANTS[3]}", arm)]
    return out


def sha():
    return hashlib.sha256("\n".join(f"{n}|{k}|{a}" for n, k, a in expanded()).encode("utf-8")).hexdigest()


def summary():
    ex = expanded()
    cond = conditions(ex)
    return {"base": len(catalog()), "features": len(ex), "features_AB": sum(1 for x in ex if x[2] == "AB"),
            "features_A_only": sum(1 for x in ex if x[2] == "A"), "conditions": len(cond),
            "conditions_AB": sum(1 for x in cond if x[1] == "AB"), "sha": sha()}


if __name__ == "__main__":
    if "--list" in sys.argv:
        for n, k, a in expanded():
            print(f"{n}\t{k}\t{a}")
    else:
        s = summary()
        print(" · ".join(f"{k}={v}" for k, v in s.items()))
