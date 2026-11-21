#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🗂️🔬 `T-CASE31` — وصفُ السمة والشرط بلغةٍ بسيطة (للمخرج النهائيّ §⑦ «أهمُّ 10 فروق») · نقيٌّ بلا بيانات."""
import re

TF = {"D": "اليوميّ", "H4": "4 ساعات", "W": "الأسبوعيّ"}
MA = {"sma": "البسيط", "ema": "الأسّيّ"}
OSC = {"rsi7": "RSI 7", "rsi14": "RSI 14", "rsi21": "RSI 21", "rsi14.bulldiv": "تباعدٌ إيجابيّ في RSI", "rsi14.beardiv": "تباعدٌ سلبيّ في RSI",
       "macd.line_p": "خطُّ MACD (نسبةً للسعر)", "macd.sig_p": "إشارةُ MACD", "macd.hist_p": "أعمدةُ MACD", "macd.hist_pos": "أعمدةُ MACD موجبة",
       "macd.xup10": "تقاطعُ MACD صاعدٌ خلال 10 شموع", "macd.xdn10": "تقاطعُ MACD هابطٌ خلال 10 شموع", "kst.val": "KST", "kst.diff": "KST فوق إشارته",
       "kst.xup10": "تقاطعُ KST صاعدٌ خلال 10 شموع", "kdj.k": "K من KDJ", "kdj.d": "D من KDJ", "kdj.j": "J من KDJ", "stoch.k": "ستوكاستك K",
       "stoch.d": "ستوكاستك D", "stoch.xup10": "تقاطعُ ستوكاستك صاعدٌ خلال 10 شموع", "cci20": "CCI 20", "willr14": "Williams %R", "mfi14": "تدفّقُ المال MFI",
       "kvo.pos": "كلنجر موجب", "kvo.above_sig": "كلنجر فوق إشارته", "adx14": "قوّةُ الاتّجاه ADX", "pdi14": "+DI", "mdi14": "−DI", "di_diff": "+DI ناقص −DI",
       "atr14_p": "التذبذبُ ATR نسبةً للسعر", "bb.width": "عرضُ بولنجر", "bb.pctb": "موضعُ السعر داخل بولنجر", "bb.squeeze_rank": "انضغاطُ بولنجر (رتبةُ العرض)",
       "kc.pos": "موضعُ السعر داخل كلتنر", "kc.squeeze": "انضغاطٌ (بولنجر داخل كلتنر)", "ichi.above_cloud": "فوق سحابة إيشيموكو", "ichi.below_cloud": "تحت سحابة إيشيموكو",
       "ichi.tk_bull": "تنكان فوق كيجن", "ichi.chikou_bull": "تشيكو إيجابيّ", "ichi.thick_p": "سماكةُ السحابة", "don20.pos": "موضعُ السعر في قناة 20 شمعة",
       "don20.low_age": "عمرُ قاع 20 شمعة", "don55.pos": "موضعُ السعر في قناة 55 شمعة", "psar.bull": "PSAR صاعد", "psar.since": "شموعٌ منذ انقلاب PSAR",
       "vwap_w.dist": "البعدُ عن VWAP الأسبوعيّ", "vwap_m.dist": "البعدُ عن VWAP الشهريّ", "st.nr4": "أضيقُ مدًى في 4 شموع", "st.nr7": "أضيقُ مدًى في 7 شموع",
       "st.green10": "نسبةُ الشموع الخضراء في 10", "st.green20": "نسبةُ الشموع الخضراء في 20", "st.hl_run": "قيعانٌ صاعدة متتالية", "st.inside10": "شموعٌ داخليّة في 10",
       "pat.dbl_bottom": "قاعٌ مزدوج", "pat.w_break": "اختراقُ نموذج W", "pat.inv_hs": "رأسٌ وكتفان مقلوب", "pat.fall_wedge": "وتدٌ هابط", "pat.bull_flag": "علمٌ صاعد",
       "pat.cup_handle": "كوبٌ وعروة", "pat.tri_asc": "مثلّثٌ صاعد", "pat.tri_desc": "مثلّثٌ هابط", "pat.tri_sym": "مثلّثٌ متماثل", "pat.flat_base15": "قاعدةٌ مسطّحة 15%",
       "pat.flat_base25": "قاعدةٌ مسطّحة 25%", "wyck.spring10": "سبرنغ وايكوف خلال 10", "wyck.lps15": "آخرُ نقطة دعم (وايكوف) خلال 15", "fib.retr": "نسبةُ ارتداد فيبوناتشي",
       "fib.near_level": "قربَ مستوى فيبوناتشي", "sr.sup_tested": "دعمٌ مُختبَر", "sr.sup_touches": "عددُ لمسات الدعم", "sr.sup_dist": "البعدُ عن الدعم",
       "sr.res_tested": "مقاومةٌ مُختبَرة", "sr.res_touches": "عددُ لمسات المقاومة", "sr.res_dist": "البعدُ عن المقاومة", "gap.above_n": "فجواتٌ غيرُ مغلقة فوق السعر",
       "gap.above_dist": "البعدُ عن أقرب فجوةٍ فوق السعر", "gap.below_n": "فجواتٌ غيرُ مغلقة تحت السعر", "gap.below_dist": "البعدُ عن أقرب فجوةٍ تحت السعر",
       "sma.stack": "ترتيبُ المتوسّطات البسيطة", "ema.stack": "ترتيبُ المتوسّطات الأسّيّة", "sma.nabove": "عددُ المتوسّطات البسيطة تحت السعر",
       "ema.nabove": "عددُ المتوسّطات الأسّيّة تحت السعر"}
FLAT = {"px.close": "السعر", "px.drop252": "الهبوطُ من قمّة سنة", "px.atl_dist": "البعدُ عن أدنى سعرٍ تاريخيّ", "px.base20_w": "عرضُ قاعدة 20 جلسة",
        "px.base40_w": "عرضُ قاعدة 40 جلسة", "px.base60_w": "عرضُ قاعدة 60 جلسة", "px.round_dist": "البعدُ عن رقمٍ مدوَّر", "px.ret1": "عائدُ جلسة",
        "px.ret5": "عائدُ 5 جلسات", "px.ret10": "عائدُ 10 جلسات", "px.ret20": "عائدُ 20 جلسة", "px.ret60": "عائدُ 60 جلسة", "px.range_d": "مدى شمعة يوم القرار",
        "px.uwick5": "أكبرُ ذيلٍ علويّ في 5 جلسات", "px.lwick10": "أكبرُ ذيلٍ سفليّ في 10 جلسات", "px.atl_age": "عمرُ أدنى سعرٍ تاريخيّ", "px.low60_age": "عمرُ قاع 60 جلسة",
        "px.base_len": "طولُ القاعدة بالجلسات", "px.below1_30": "جلساتٌ تحت الدولار في 30", "px.expl_n": "عددُ الانفجارات السابقة", "px.expl_age": "جلساتٌ منذ آخر انفجار",
        "px.sweep10": "كسرُ قاعٍ في 10 جلسات", "px.sweep_reclaim": "كسرُ قاعٍ ثمّ استعادتُه", "px.near1": "قربَ الدولار", "px.expl_due": "في موعد إيقاع انفجاراته",
        "vol.usd_med20": "وسيطُ قيمة التداول 20 جلسة", "vol.usd_d": "قيمةُ تداول يوم القرار", "vol.dry5_20": "جفافُ الحجم (5 مقابل 20)", "vol.spike_d": "قفزةُ حجم يوم القرار",
        "vol.updown20": "حجمُ الصاعد مقابل الهابط في 20", "vol.obv_slope10": "ميلُ OBV في 10", "vol.obv_slope20": "ميلُ OBV في 20", "vol.adl_slope10": "ميلُ التجميع/التصريف في 10",
        "vol.adl_slope20": "ميلُ التجميع/التصريف في 20", "vol.cmf20": "تدفّقُ المال CMF 20", "vol.spike10": "قفزةُ حجمٍ في 10 جلسات",
        "sh.ratio_d": "نسبةُ الشورت يومَ القرار", "sh.ratio5": "نسبةُ الشورت في 5 جلسات", "sh.ratio10": "نسبةُ الشورت في 10 جلسات", "sh.vol_d": "حجمُ الشورت اليوميّ",
        "sh.vol_le40k": "حجمُ الشورت 40 ألفًا أو أقلّ", "bw.avail": "المتاحُ للاقتراض", "bw.fee": "رسومُ الاقتراض", "bw.avail_le20k": "المتاحُ 20 ألفًا أو أقلّ",
        "id.float": "الفلوت", "id.shares": "الأسهمُ القائمة", "id.mcap": "القيمةُ السوقيّة", "id.float_turn_d": "تدويرُ الفلوت يومَ القرار", "id.float_turn20": "تدويرُ الفلوت في 20 جلسة",
        "id.age_sessions": "عمرُ الإدراج", "id.is_adr": "إيصالُ إيداع", "id.is_shell_sic": "شركةٌ صوريّة", "id.has_options": "له خيارات", "id.foreign_filer": "مُودِعٌ أجنبيّ",
        "id.c_us": "أمريكيّ", "id.c_cn_hk": "الصين/هونغ كونغ", "id.c_sg": "سنغافورة", "id.c_il": "إسرائيل", "id.c_other": "دولةٌ أخرى", "id.s_health": "قطاعُ الصحّة",
        "id.s_tech": "قطاعُ التقنية", "id.s_finance": "قطاعُ المال", "id.s_consumer": "قطاعُ المستهلك", "id.s_other": "قطاعٌ آخر",
        "cp.rs_n365": "تقسيماتٌ عكسيّة في سنة", "cp.rs_n_all": "تقسيماتٌ عكسيّة في تاريخه", "cp.rs_age_days": "أيّامٌ منذ آخر تقسيمٍ عكسيّ", "cp.rs_le60": "تقسيمٌ عكسيّ خلال 60 يومًا",
        "ed.n424b_90": "نشراتُ طرحٍ في 90 يومًا", "ed.n424b_365": "نشراتُ طرحٍ في سنة", "ed.age_424b": "أيّامٌ منذ آخر نشرة طرح", "ed.n8k_30": "إيداعاتُ 8-K في 30 يومًا",
        "ed.n8k_3": "إيداعاتُ 8-K في 3 أيّام", "ed.n_form4_90": "نماذجُ 4 (المطّلعون) في 90 يومًا", "ed.n_13dg_90": "إيداعاتُ 13D/G في 90 يومًا",
        "ed.defic_days_left": "أيّامٌ باقية على مهلة الإدراج", "ed.results_age": "أيّامٌ منذ آخر نتائج", "ed.shelf_active": "رفُّ طرحٍ فعّال", "ed.s1_365": "S-1 خلال سنة",
        "ed.proxy_75": "دعوةُ مساهمين خلال 75 يومًا", "ed.nt_365": "إيداعٌ متأخّر خلال سنة", "ed.defic_365": "إشعارُ نقص إدراجٍ خلال سنة", "ed.name_change_365": "تغييرُ اسمٍ خلال سنة",
        "ed.results_due30": "نتائجُ متوقَّعة خلال 30 يومًا", "bot.nw_days": "أيّامُه في «تحت المتابعة»", "bot.readiness": "جاهزيّةُ البوت", "bot.score": "درجةُ البوت",
        "bot.n_out": "عددُ النواقص عند البوت", "bot.nw_tracked": "في «تحت المتابعة»", "bot.wall_any": "له جدارُ رفض", "bot.wall_level": "جدارُه «لا مستوى مختبَر»",
        "bot.wall_base": "جدارُه «القاعدة الواسعة»", "bot.in_list": "في القائمة الأسبوعيّة", "bot.in_pullback": "في قائمة الارتداد", "bot.blocked": "محجوبٌ ببوّابةٍ بعد الفرز",
        "bot.faisal_post30": "منشورٌ لفيصل خلال 30 يومًا", "bot.tool20_split_hunter": "نبّه عنه صيّادُ التقسيم خلال 20 جلسة", "bot.tool20_split_filter": "نبّه عنه فلترُ التقسيم خلال 20 جلسة",
        "bot.tool20_method": "نبّه عنه النهجُ العلميّ خلال 20 جلسة", "bot.tool20_press": "نبّه عنه رادارُ الضغط خلال 20 جلسة", "bot.tool20_envelope": "نبّه عنه صيّادُ الغلاف خلال 20 جلسة",
        "bot.tool20_three": "طابق «شروطك الثلاثة» خلال 20 جلسة", "ct.sector3": "منفجرون في قطاعه خلال 3 جلسات", "ct.industry3": "منفجرون في صناعته خلال 3 جلسات",
        "ct.country3": "منفجرون من دولته خلال 3 جلسات"}
BOT = {"rsi14": "RSI بإعداد البوت", "macd_hist_p": "أعمدةُ MACD بإعداد البوت", "kst_diff": "KST بإعداد البوت", "mfi": "MFI بإعداد البوت", "willr": "%R بإعداد البوت",
       "atr_p": "ATR بإعداد البوت", "bb_pctb": "بولنجر بإعداد البوت", "stochrsi_k": "StochRSI بإعداد البوت", "fsto_k": "FSTO بإعداد البوت", "cci14": "CCI 14 بإعداد البوت",
       "adx": "ADX بإعداد البوت", "klinger_bull": "كلنجر البوت إيجابيّ", "ema30_dist": "البعدُ عن EMA 30 (إعدادُ البوت)", "ema50_dist": "البعدُ عن EMA 50 (إعدادُ البوت)"}
CDL = {"hammer": "مطرقة", "inv_hammer": "مطرقةٌ مقلوبة", "bull_engulf": "ابتلاعٌ شرائيّ", "piercing": "شمعةٌ ثاقبة", "morning_star": "نجمةُ الصباح", "bull_harami": "هارامي شرائيّ",
       "three_soldiers": "ثلاثةُ جنود", "dragonfly": "دوجي اليعسوب", "tweezer_bottom": "ملقطُ قاع", "bull_marubozu": "ماروبوزو أخضر", "shooting_star": "شهاب",
       "bear_engulf": "ابتلاعٌ بيعيّ", "dark_cloud": "سحابةٌ قاتمة", "evening_star": "نجمةُ المساء", "bear_harami": "هارامي بيعيّ", "three_crows": "ثلاثةُ غربان",
       "gravestone": "دوجي شاهد القبر", "hanging_man": "الرجلُ المشنوق", "doji": "دوجي", "spinning_top": "قمّةٌ دوّارة", "inside_bar": "شمعةٌ داخليّة", "outside_bar": "شمعةٌ خارجيّة"}
MA_PART = {"dist": "بُعدُ السعر عن المتوسّط {k} {n}", "slope": "ميلُ المتوسّط {k} {n}", "above": "السعرُ فوق المتوسّط {k} {n}", "since": "شموعٌ منذ عبور المتوسّط {k} {n}"}
X_PART = {"gap": "الفرقُ بين المتوسّطين {k} {a} و{b}", "above": "المتوسّط {k} {a} فوق {b}", "xup10": "تقاطعٌ صاعد للمتوسّطين {k} {a}/{b} خلال 10 شموع",
          "xdn10": "تقاطعٌ هابط للمتوسّطين {k} {a}/{b} خلال 10 شموع", "since": "شموعٌ منذ تقاطع المتوسّطين {k} {a}/{b}"}


def feature(name):
    """اسمُ سمةٍ من الفهرس ⟵ وصفٌ عربيٌّ بسيط · والمجهولُ يعود باسمه كما هو."""
    delta = ""
    m = re.search(r"\.d(5|10)$", name)
    if m:
        name, delta = name[:m.start()], f" — تغيّرُه في {m.group(1)} جلسات"
    if name in FLAT:
        return FLAT[name] + delta
    tf, _, rest = name.partition(".")
    if tf not in TF:
        return name + delta
    out = None
    m = re.fullmatch(r"(sma|ema)(\d+)x(\d+)\.(\w+)", rest)
    if m and m.group(4) in X_PART:
        out = X_PART[m.group(4)].format(k=MA[m.group(1)], a=m.group(2), b=m.group(3))
    m2 = re.fullmatch(r"(sma|ema)(\d+)\.(\w+)", rest)
    if out is None and m2 and m2.group(3) in MA_PART:
        out = MA_PART[m2.group(3)].format(k=MA[m2.group(1)], n=m2.group(2))
    m3 = re.fullmatch(r"cdl\.(\w+)\.(any10|ago)", rest)
    if out is None and m3 and m3.group(1) in CDL:
        out = (f"شمعة «{CDL[m3.group(1)]}» في آخر 10 شموع" if m3.group(2) == "any10" else f"شموعٌ منذ آخر «{CDL[m3.group(1)]}»")
    if out is None and rest.startswith("bot.") and rest[4:] in BOT:
        out = BOT[rest[4:]]
    if out is None:
        out = OSC.get(rest)
    return (f"{out} ({TF[tf]})" if out else name) + delta


def condition(text):
    """نصُّ الشرط («اسم=1» · «اسم<q20» · «اسم>q80») ⟵ جملةٌ بسيطة."""
    if text.endswith("=1"):
        return feature(text[:-2]) + ": نعم"
    if text.endswith("=0"):
        return feature(text[:-2]) + ": لا"
    m = re.fullmatch(r"(.+)([<>])q(\d+)", text)
    if not m:
        return text
    word = {("<", "20"): "في أدنى خُمس الصفوف", ("<", "40"): "دون 40% من الصفوف", (">", "60"): "فوق 60% من الصفوف", (">", "80"): "في أعلى خُمس الصفوف"}
    return feature(m.group(1)) + ": " + word.get((m.group(2), m.group(3)), f"{m.group(2)} المئين {m.group(3)}")
