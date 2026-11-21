# ⚖️ `T-CASE31` — الذراع A: المقارنةُ واختبارُ الخلط (مولَّدٌ آليًّا · لا يُعدَّل باليد)

- المجتمع (الشهر): صفوف 17,108 · **منفجرون 99** (منهم خارج «تحت المتابعة» 30) · ضابطة 17,009 · رماديٌّ مستبعَد 507 · بلا وسم 2 · أيّامُ قرار 24 (بلا لقطة 1) · ضابطةٌ لم تكتمل نافذتُها 14,331
- **المجرَّب:** سمات 1,932 (المؤهَّلة بالتغطية 1,771) · شروط 6,312 (الصالحة منفردةً 5,983) · توليفات 10,660 · نماذج 2 × 23 طيّة · خلطات 1,000

## ① نتيجةُ الخلط (القِمم: المرصودُ مقابل المئين 95 لأقصى الخلطات)

| القمّة | المرصود | مئين 95 للخلطات | يفوق من الخلطات | الحكم |
|---|---|---|---|---|
| أقوى شرطٍ منفرد (z) | 71.793 | 4.071 | 100.0% | ✅ يعبر |
| أقوى توليفة (z) | 41.450 | 9.853 | 100.0% | ✅ يعبر |
| أقوى بصمة (z) | 71.793 | 9.853 | 100.0% | ✅ يعبر |
| أقوى سمة استبعاد (اختصار) | 0.201 | 0.000 | 100.0% | ✅ يعبر |
| شجرةُ القرار (AUC داخل اليوم) | 0.808 | 0.569 | 100.0% | ✅ يعبر |
| اللوجستيّ (AUC داخل اليوم) | 0.718 | 0.581 | 100.0% | ✅ يعبر |
| الشجرة: منفجرون في أعلى 5% | 0.053 | 0.012 | 100.0% | ✅ يعبر |
| اللوجستيّ: منفجرون في أعلى 5% | 0.024 | 0.010 | 100.0% | ✅ يعبر |

## ② أهمُّ الفروق (السمات مرتّبةً بالفرق المعياريّ · فاصل 95% عنقوديّ بيوم القرار)

| السمة | عند المنفجرين | عند الضابطة | الفرق (رتبة) | الفاصل | مقابل ضابط الزخم | التغطية |
|---|---|---|---|---|---|---|
| `H4.atr14_p` | 0.0930 | 0.0629 | +0.208 | [+0.154، +0.261] | 0.113 | 100% |
| `D.sma10.dist` | -0.1920 | -0.0773 | -0.202 | [-0.264، -0.138] | -0.052 | 100% |
| `D.ema5.dist` | -0.0984 | -0.0382 | -0.198 | [-0.258، -0.128] | -0.050 | 100% |
| `D.ema8.dist` | -0.1593 | -0.0645 | -0.197 | [-0.257، -0.133] | -0.049 | 100% |
| `D.sma13.dist` | -0.2244 | -0.1003 | -0.196 | [-0.258، -0.132] | -0.055 | 100% |
| `D.sma8.dist` | -0.1605 | -0.0620 | -0.196 | [-0.260، -0.126] | -0.042 | 100% |
| `D.ema10.dist` | -0.1928 | -0.0812 | -0.195 | [-0.254، -0.132] | -0.049 | 100% |
| `D.sma15.dist` | -0.2637 | -0.1152 | -0.193 | [-0.253، -0.132] | -0.055 | 100% |
| `D.macd.line_p.d5` | -0.0680 | -0.0082 | -0.190 | [-0.260، -0.118] | -0.054 | 100% |
| `D.ema13.dist` | -0.2510 | -0.1052 | -0.189 | [-0.249، -0.127] | -0.048 | 100% |
| `H4.bb.width` | 0.4205 | 0.2616 | +0.187 | [+0.121، +0.253] | 0.061 | 100% |
| `D.macd.sig_p.d5` | -0.0544 | -0.0091 | -0.186 | [-0.251، -0.120] | -0.066 | 100% |
| `D.ema15.dist` | -0.2697 | -0.1210 | -0.185 | [-0.244، -0.124] | -0.048 | 100% |
| `px.ret10` | -0.3139 | -0.1495 | -0.183 | [-0.237، -0.127] | -0.067 | 100% |
| `D.ema5.slope` | -0.1838 | -0.0803 | -0.183 | [-0.246، -0.118] | -0.046 | 100% |
| `D.sma5.dist` | -0.0952 | -0.0370 | -0.183 | [-0.246، -0.112] | -0.049 | 100% |
| `D.sma20.dist` | -0.3214 | -0.1523 | -0.183 | [-0.244، -0.118] | -0.056 | 100% |
| `D.sma21.dist` | -0.3305 | -0.1598 | -0.180 | [-0.241، -0.116] | -0.054 | 100% |
| `px.ret5` | -0.2194 | -0.0828 | -0.180 | [-0.248، -0.108] | -0.024 | 100% |
| `W.sma5.dist` | -0.2713 | -0.1308 | -0.180 | [-0.239، -0.119] | -0.053 | 100% |
| `D.macd.line_p.d10` | -0.0944 | -0.0170 | -0.177 | [-0.229، -0.129] | -0.086 | 100% |
| `D.sma5.slope` | -0.1692 | -0.0768 | -0.175 | [-0.232، -0.113] | -0.056 | 100% |
| `W.atr14_p.d10` | 0.3827 | 0.0389 | +0.174 | [+0.121، +0.223] | 0.062 | 99% |
| `D.atr14_p` | 0.2235 | 0.1325 | +0.173 | [+0.108، +0.232] | 0.077 | 100% |
| `D.ema8.slope` | -0.1661 | -0.0792 | -0.172 | [-0.231، -0.111] | -0.049 | 100% |
| `D.ema20.dist` | -0.3114 | -0.1587 | -0.171 | [-0.229، -0.106] | -0.044 | 100% |
| `W.ema5.dist.d10` | -0.0858 | -0.0116 | -0.170 | [-0.219، -0.120] | -0.065 | 100% |
| `D.bot.atr_p` | 0.2199 | 0.1325 | +0.170 | [+0.107، +0.227] | 0.077 | 100% |
| `D.ema5.dist.d10` | -0.0583 | -0.0042 | -0.169 | [-0.232، -0.103] | -0.063 | 100% |
| `W.sma8.dist.d10` | -0.1132 | -0.0216 | -0.169 | [-0.215، -0.121] | -0.071 | 100% |
| `D.ema21.dist` | -0.3172 | -0.1654 | -0.169 | [-0.228، -0.104] | -0.044 | 100% |
| `D.ema20.dist.d10` | -0.1061 | -0.0131 | -0.168 | [-0.217، -0.118] | -0.065 | 100% |
| `D.ema21.dist.d10` | -0.1038 | -0.0140 | -0.168 | [-0.216، -0.117] | -0.065 | 100% |
| `D.ema13.dist.d10` | -0.0857 | -0.0080 | -0.168 | [-0.222، -0.109] | -0.065 | 100% |
| `D.ema10.dist.d10` | -0.0881 | -0.0061 | -0.167 | [-0.226، -0.102] | -0.065 | 100% |
| `D.ema15.dist.d10` | -0.0936 | -0.0094 | -0.167 | [-0.219، -0.112] | -0.065 | 100% |
| `D.sma5.dist.d10` | -0.0601 | -0.0054 | -0.167 | [-0.226، -0.106] | -0.068 | 100% |
| `D.sr.res_dist.d10` | 0.5395 | 0.0946 | +0.166 | [+0.109، +0.220] | 0.074 | 100% |
| `D.ema8.dist.d10` | -0.0769 | -0.0053 | -0.166 | [-0.229، -0.097] | -0.063 | 100% |
| `D.atr14_p.d10` | 0.0507 | 0.0077 | +0.165 | [+0.110، +0.217] | 0.059 | 100% |

## ③ أقوى الشروط المنفردة

| الشرط | z | المنفجرون الحاملون | كلُّ الحاملين | مقابل ضابط الزخم | وسيطُ المهلة (جلسات) |
|---|---|---|---|---|---|
| `bot.nw_tracked=0` | 71.79 | 30 | 30 | 0.292 | 1 |
| `W.sma55.above=1` | 8.66 | 8 | 123 | 0.079 | 21 |
| `W.sma50.above=1` | 7.98 | 8 | 141 | 0.079 | 21 |
| `D.ema15.dist<q20` | 7.94 | 55 | 3,420 | 0.158 | 3 |
| `W.ichi.below_cloud=0` | 7.74 | 8 | 148 | 0.077 | 21 |
| `px.ret10<q20` | 7.72 | 54 | 3,418 | 0.196 | 3 |
| `D.sma20.dist<q20` | 7.71 | 54 | 3,419 | 0.175 | 4 |
| `D.ema21.dist<q20` | 7.71 | 54 | 3,419 | 0.183 | 4 |
| `D.sma13.dist<q20` | 7.71 | 54 | 3,420 | 0.141 | 3 |
| `D.ema10.dist<q20` | 7.71 | 54 | 3,421 | 0.131 | 3 |
| `W.atr14_p.d10>q80` | 7.54 | 53 | 3,396 | 0.213 | 4 |
| `D.macd.line_p.d5<q20` | 7.49 | 53 | 3,418 | 0.127 | 3 |
| `px.ret5<q20` | 7.49 | 53 | 3,418 | 0.068 | 2 |
| `D.sma21.dist<q20` | 7.49 | 53 | 3,419 | 0.166 | 3 |
| `D.sma30.dist<q20` | 7.49 | 53 | 3,419 | 0.188 | 5 |
| `D.sma34.dist<q20` | 7.49 | 53 | 3,419 | 0.195 | 5 |
| `D.ema20.dist<q20` | 7.49 | 53 | 3,419 | 0.170 | 4 |
| `D.sma15.dist<q20` | 7.49 | 53 | 3,420 | 0.135 | 3 |
| `D.ema13.dist<q20` | 7.49 | 53 | 3,420 | 0.131 | 3 |
| `D.sma10.dist<q20` | 7.48 | 53 | 3,421 | 0.109 | 3 |

## ④ أقوى التوليفات حتى 3 شروط

| التوليفة | z | المنفجرون | الحاملون | نسبةُ الانفجار | مقابل ضابط الزخم |
|---|---|---|---|---|---|
| `bot.nw_tracked=0` ∧ `H4.macd.line_p<q20` | 41.45 | 10 | 10 | 100.0% | 0.094 |
| `bot.nw_tracked=0` ∧ `D.sma8.dist<q20` | 39.32 | 9 | 9 | 100.0% | 0.083 |
| `bot.nw_tracked=0` ∧ `D.ema5.slope<q20` | 39.32 | 9 | 9 | 100.0% | 0.083 |
| `bot.nw_tracked=0` ∧ `D.macd.line_p.d5<q20` | 39.32 | 9 | 9 | 100.0% | 0.083 |
| `bot.nw_tracked=0` ∧ `D.atr14_p.d10>q80` | 39.32 | 9 | 9 | 100.0% | 0.094 |
| `bot.nw_tracked=0` ∧ `D.bot.atr_p.d10>q80` | 39.32 | 9 | 9 | 100.0% | 0.094 |
| `bot.nw_tracked=0` ∧ `px.ret5<q20` | 39.32 | 9 | 9 | 100.0% | 0.094 |
| `bot.nw_tracked=0` ∧ `D.atr14_p.d10>q80` ∧ `D.bot.atr_p.d10>q80` | 39.32 | 9 | 9 | 100.0% | 0.094 |
| `bot.nw_tracked=0` ∧ `H4.macd.line_p<q20` ∧ `D.sma8.dist<q20` | 39.32 | 9 | 9 | 100.0% | 0.083 |
| `bot.nw_tracked=0` ∧ `D.sma13.dist<q20` | 37.07 | 8 | 8 | 100.0% | 0.073 |
| `bot.nw_tracked=0` ∧ `D.sma20.dist<q20` | 37.07 | 8 | 8 | 100.0% | 0.073 |
| `bot.nw_tracked=0` ∧ `D.ema15.dist<q20` | 37.07 | 8 | 8 | 100.0% | 0.073 |
| `bot.nw_tracked=0` ∧ `H4.sma40.dist<q20` | 37.07 | 8 | 8 | 100.0% | 0.073 |
| `bot.nw_tracked=0` ∧ `H4.ema21.dist<q20` | 37.07 | 8 | 8 | 100.0% | 0.062 |
| `bot.nw_tracked=0` ∧ `H4.ema13x34.gap<q20` | 37.07 | 8 | 8 | 100.0% | 0.073 |

## ⑤ سماتُ الاستبعاد (أقلُّ من 5% من المنفجرين و20% فأكثر من الضابطة)

| الشرط | يختصر من القائمة | يحمله من المنفجرين |
|---|---|---|
| `W.ema5.dist.d10>q80` | 20.1% | 2.0% |
| `D.di_diff.d10>q80` | 20.1% | 2.0% |
| `D.sma8.dist.d10>q80` | 20.1% | 4.0% |
| `D.ema21.dist.d10>q80` | 20.1% | 4.0% |
| `D.mdi14.d10<q20` | 20.1% | 3.0% |
| `D.kc.pos.d10>q80` | 20.1% | 3.0% |
| `D.pdi14.d10>q80` | 20.1% | 4.0% |

## ⑥ لكلّ نوع (الشروطُ المنفردة وحدَها وخلطُها)

| النوع | المنفجرون | أقوى شرط | z | مئين 95 | الحكم |
|---|---|---|---|---|---|
| بخبر | 38 | `bot.nw_tracked=0` | 62.51 | 4.15 | ✅ يعبر |
| بلا خبر | 58 | `bot.nw_tracked=0` | 67.02 | 4.09 | ✅ يعبر |
| يومٌ واحد | 49 | `bot.nw_tracked=0` | 65.83 | 4.11 | ✅ يعبر |
| عدّة أيام | 50 | `bot.nw_tracked=0` | 68.95 | 4.12 | ✅ يعبر |
| شمعةٌ واحدة | 73 | `bot.nw_tracked=0` | 64.76 | 4.04 | ✅ يعبر |
| موجات | 26 | `bot.nw_tracked=0` | 70.46 | 4.09 | ✅ يعبر |
| بعد تقسيمٍ عكسيّ | 13 | `cp.rs_le60=1` | 9.75 | 4.00 | ✅ يعبر |
| بلا تقسيمٍ حديث | 86 | `bot.nw_tracked=0` | 75.73 | 4.06 | ✅ يعبر |

## ⑦ أقرب الجيران (لكلّ منفجرٍ أشبهُ 5 لم تنفجر في يومه وأكبرُ ما فرّقه)

- **BTOG** (2026-10-29) ⟵ MYSZ · SBFM · DFLI · SCNI · CIGL — `H4.sma30.since` -0.76 · `D.sma80.slope.d10` +0.75 · `D.sma80.slope.d5` +0.74 · `W.sma40.slope.d5` +0.70 · `H4.sma34.slope.d5` -0.69
- **CHSN** (2026-10-27) ⟵ SURG · RDGT · MTEN · IBG · SLMT — `D.sma144.slope.d5` -0.90 · `D.sma144.slope.d10` -0.87 · `H4.ema200.dist` -0.84 · `H4.ema144.since` +0.84 · `H4.ema150.since` +0.84
- **FRTT** (2026-11-16) ⟵ SAEN · XGPU · CELZ · ACTU · BEEM — `vol.obv_slope20` +0.64 · `vol.updown20` +0.64 · `D.sma89.slope.d5` -0.54 · `D.sma.stack.d5` +0.50 · `D.sma100.slope.d5` +0.50
- **PEPG** (2026-11-09) ⟵ SPHL · MAMO · RMCF · AKTX · FOFO — `vol.usd_med20` +0.62 · `D.sma50x100.gap.d10` -0.62 · `W.sma34x89.gap.d10` -0.61 · `D.sma50x100.gap.d5` -0.61 · `vol.usd_d` +0.60
- **SLSN** (2026-11-12) ⟵ CDIO · BFRG · HUCK · MREO · ENVB — `vol.obv_slope20.d5` -0.87 · `vol.updown20.d5` -0.79 · `vol.obv_slope10` -0.73 · `D.sma144.since` +0.72 · `D.sma150.since` +0.72
- **SVRE** (2026-11-17) ⟵ AMIX · GNLN · ACTU · CODX · TNON — `D.sma30.slope.d5` +0.84 · `ed.results_age` +0.83 · `H4.sma89.slope.d5` +0.74 · `D.sma30.slope.d10` +0.74 · `px.expl_age` +0.68
- **ULBI** (2026-10-27) ⟵ INSG · GDTC · GOGO · ATXG · WVVIP — `D.st.green20.d5` -0.77 · `H4.bb.width` +0.69 · `D.sma50.slope.d10` -0.64 · `sh.ratio_d` +0.63 · `D.sma50.slope.d5` -0.61
- **VIVK** (2026-11-05) ⟵ HCTI · LGHL · ELAB · KIDZ · ENLV — `px.range_d.d10` -0.87 · `W.sma55.slope.d10` +0.79 · `vol.spike_d.d10` -0.76 · `D.ichi.thick_p.d10` +0.73 · `D.adx14` -0.73
- **NCPL** (2026-10-28) ⟵ ENSC · COSM · OLB · FLYE · REFR — `W.ema.stack.d10` +0.83 · `H4.ema15.since` -0.77 · `H4.sma20.since` -0.76 · `W.bb.width.d10` +0.74 · `W.sma21.slope.d5` -0.74
- **NUAI** (2026-11-05) ⟵ AAOI · BTDR · KEEL · CIFR · PDYN — `sh.vol_d.d5` -0.93 · `vol.usd_d.d5` -0.93 · `vol.usd_d.d10` -0.90 · `sh.vol_d.d10` -0.75 · `px.round_dist.d5` +0.64
- **RAYA** (2026-11-05) ⟵ TRNR · CAPS · MYSZ · AZI · FRSX — `H4.sma5.since` -0.74 · `H4.ema5.since` -0.73 · `H4.sma8.since` -0.70 · `H4.sma10.since` -0.66 · `D.sma144.slope.d5` -0.65
- **SEAT** (2026-11-18) ⟵ CVRX · IHRT · PIII · FMFC · ARAY — `W.sma55.since` +0.63 · `H4.ichi.thick_p` -0.61 · `H4.bb.width.d10` -0.57 · `W.ema55.since` +0.57 · `W.sma50.since` +0.54
- **CRMT** (2026-10-21) ⟵ ANTA · AIIO · NEXR · MBAI · FMFC — `W.sma55.slope.d5` +0.74 · `W.sma55.slope.d10` +0.74 · `D.sma10x20.gap` +0.67 · `px.lwick10.d10` +0.63 · `H4.sma144.slope.d5` -0.62
- **INO** (2026-10-30) ⟵ NGEN · ZENA · DRK · IPWR · EPSM — `H4.bb.width` +0.81 · `px.lwick10` +0.77 · `px.lwick10.d5` +0.69 · `H4.pdi14` +0.68 · `H4.bb.width.d10` +0.68
- **PMAX** (2026-10-30) ⟵ ICCM · CYN · HCTI · ARTL · SCAG — `W.sma15.since` -0.73 · `W.ema10.since` -0.72 · `W.sma13.since` -0.69 · `D.sma80.since` -0.68 · `W.sma10.since` -0.64
- **GP** (2026-11-11) ⟵ POLA · AMCI · LOT · ADGM · AUID — `H4.sma144.slope.d10` +0.79 · `H4.sma150.slope.d10` +0.78 · `H4.sma80.slope.d5` +0.71 · `px.lwick10.d10` -0.65 · `D.macd.hist_p` +0.61
- **LABT** (2026-11-04) ⟵ DBGI · AIAI · PPCB · NEXR · GOVX — `D.sma89.slope.d5` +0.81 · `H4.ichi.thick_p.d10` -0.75 · `D.st.green10` +0.74 · `vol.adl_slope10` +0.74 · `vol.adl_slope20` +0.73
- **SPHL** (2026-10-20) ⟵ AKTX · GURE · PULM · NEUP · GTBP — `W.sma40x80.gap.d5` -0.76 · `W.sma40.slope.d5` -0.71 · `H4.st.inside10` -0.70 · `vol.updown20.d10` +0.68 · `D.cci20.d5` -0.68
- **AEYE** (2026-10-19) ⟵ SUPX · HUCK · WETH · JFU · RECT — `D.sma.nabove` +0.56 · `H4.stoch.d.d10` -0.56 · `D.ema.nabove` +0.55 · `D.don20.pos.d5` +0.53 · `vol.obv_slope20.d5` +0.51
- **AIOK** (2026-10-19) ⟵ KG · NVX · IMNN · METCB · LENZ — `H4.rsi21` +0.65 · `H4.rsi14` +0.65 · `sh.ratio5.d5` -0.51 · `sh.ratio_d` -0.50 · `sh.ratio_d.d5` -0.47
- **CENN** (2026-11-10) ⟵ ABTS · LOT · GOAI · CHGA · POLA — `vol.dry5_20.d10` -0.77 · `px.uwick5.d10` -0.77 · `px.range_d.d10` -0.66 · `H4.bb.width.d5` -0.63 · `H4.atr14_p.d5` -0.63
- **NWGL** (2026-11-06) ⟵ CJMB · ADVB · OPNW · DRIO · MGRX — `H4.sma55.slope.d10` +0.78 · `W.sma13x34.gap.d10` +0.77 · `H4.ema10.since` -0.76 · `H4.sma55.slope.d5` +0.76 · `W.sma13x34.gap.d5` +0.75
- **PARA** (2026-11-02) ⟵ NEXR · CETX · DBGI · CXAI · ENLV — `D.sma150.slope.d5` -0.74 · `H4.ichi.thick_p.d5` -0.66 · `D.sma150.slope.d10` -0.63 · `W.sma34.slope.d10` -0.61 · `H4.mfi14` +0.59
- **SKYA** (2026-11-17) ⟵ SHPH · KMRK · FFTT · BGMS · PSIG — `sh.ratio10.d5` +0.72 · `sh.ratio5.d10` +0.72 · `sh.ratio5.d5` +0.67 · `vol.usd_med20.d5` -0.66 · `sh.ratio10.d10` +0.58
- **AIHS** (2026-11-05) ⟵ QTEX · ENSC · XRPN · TAOX · FFR — `H4.vwap_w.dist.d10` +0.74 · `H4.ema8.dist.d10` +0.72 · `H4.sma10.dist.d10` +0.70 · `H4.ema10.dist.d10` +0.70 · `H4.ema5.dist.d10` +0.70
- **ESLA** (2026-11-06) ⟵ NBP · TYGO · HQ · IMTE · FCDH — `H4.sma8.slope.d5` +0.79 · `H4.kst.diff.d5` +0.76 · `H4.macd.hist_p.d5` +0.69 · `D.st.inside10` -0.68 · `H4.bb.width.d10` -0.67
- **JXG** (2026-11-03) ⟵ GURE · ARQ · CUPR · NVNO · GRAN — `W.ema80.since` +0.65 · `H4.cdl.inside_bar.ago` +0.61 · `W.sma80.since` +0.60 · `px.expl_n` +0.59 · `H4.ema.nabove.d10` -0.55
- **RETO** (2026-11-03) ⟵ ENLV · WHLR · ICCM · HCTI · NIVF — `D.sr.res_dist.d5` -0.96 · `H4.sma200.slope.d5` +0.92 · `D.sr.res_dist.d10` -0.91 · `H4.sma200.slope.d10` +0.79 · `W.kc.pos` +0.79
- **SEGG** (2026-10-29) ⟵ NRSN · CYN · TMCR · MYSZ · PAVM — `H4.sma40.since` -0.75 · `W.adx14.d10` -0.72 · `H4.sma30.since` -0.70 · `W.pdi14` +0.70 · `W.adx14.d5` -0.70
- **TREO** (2026-10-26) ⟵ FEMY · MCRB · LIQT · BTOC · TVRD — `H4.sma40.slope.d5` -0.52 · `sh.ratio_d.d5` -0.45 · `W.sma10.since` -0.42 · `W.ema10.since` -0.40 · `px.atl_age` +0.40
- **ZNB** (2026-11-02) ⟵ SRTM · BJDX · EDBL · DFNS · ARTL — `W.ichi.thick_p.d5` -0.87 · `D.sma5.since` -0.82 · `W.macd.hist_p.d5` -0.77 · `D.mfi14` +0.74 · `D.bot.mfi` +0.74
- **CMCT** (2026-11-06) ⟵ JZ · RDGT · HRTX · RDHL · FLYE — `W.ema5.slope.d5` -0.71 · `H4.sma80.slope.d5` -0.66 · `H4.sma34.slope.d5` -0.66 · `px.ret60.d10` -0.66 · `H4.sma34.slope` -0.64
- **ELOG** (2026-11-10) ⟵ GLND · QTEX · LFS · SVIA · USDE — `sh.ratio10.d5` +0.82 · `sh.ratio5.d10` +0.82 · `D.sma21x55.gap.d10` +0.74 · `H4.sma100x200.gap.d5` +0.74 · `W.sma8.slope.d10` +0.70
- **NXAT** (2026-11-19) ⟵ ARTL · KITT · ATYR · JTAI · ISPC — `px.base60_w.d10` -0.69 · `ed.results_age` +0.67 · `px.round_dist.d5` +0.63 · `D.sma150.slope.d5` +0.55 · `H4.sma200.slope.d10` +0.54
- **RBNE** (2026-10-20) ⟵ OBAI · SRTM · CHGA · EYPT · SPRC — `D.sma50x100.gap.d10` +0.79 · `D.sma50x100.gap.d5` +0.79 · `D.sma200.slope.d5` +0.73 · `W.sma10x20.gap.d10` +0.73 · `D.sma55.slope.d5` +0.70
- **XLAB** (2026-11-11) ⟵ AMCI · PRPL · NOMA · FCDH · PASW — `H4.kst.diff.d10` +0.85 · `D.bb.width.d10` -0.74 · `D.bb.width.d5` -0.72 · `D.cdl.inside_bar.ago` +0.64 · `D.don20.low_age` +0.64
- **ATGL** (2026-10-19) ⟵ PLSM · OPEN · KLXE · SLBT · GAIA — `px.base60_w` +0.65 · `sh.ratio_d.d10` +0.63 · `H4.atr14_p` +0.62 · `sh.ratio_d` +0.59 · `px.atl_dist` +0.59
- **HIHO** (2026-11-13) ⟵ GURE · GITS · AEC · WKHS · QS — `px.below1_30` +0.62 · `D.ema.stack.d10` +0.59 · `H4.pdi14` +0.57 · `vol.updown20.d10` +0.54 · `H4.di_diff` +0.54
- **POM** (2026-10-26) ⟵ CGTL · VTIX · AIFC · ANTA · INVZ — `vol.adl_slope10` +0.82 · `vol.adl_slope20.d10` +0.81 · `vol.cmf20.d10` +0.81 · `vol.adl_slope20.d5` +0.78 · `vol.cmf20.d5` +0.78
- **SDA** (2026-11-05) ⟵ SCAG · AIFC · BAER · GRSD · POLA — `H4.sma8x15.gap.d5` +0.70 · `H4.mfi14` +0.69 · `H4.ichi.thick_p.d10` -0.68 · `W.sma80.slope.d5` +0.63 · `H4.psar.since` -0.62
- **SLGB** (2026-10-29) ⟵ FUSE · HCWB · PLSM · ASPI · BGL — `H4.bb.width.d10` +0.80 · `H4.bb.squeeze_rank` +0.78 · `H4.bb.width` +0.76 · `H4.ema200.since` -0.76 · `vol.dry5_20` +0.74
- **CNSY** (2026-11-02) ⟵ LX · MIST · INTS · TDUP · SILO — `W.sma5.since` +0.68 · `cp.rs_n_all` +0.61 · `sh.ratio_d.d5` -0.58 · `W.sma55.slope.d10` -0.57 · `W.sma55.slope.d5` -0.53
- **IFBD** (2026-10-30) ⟵ BFRG · CDIO · BTCS · IVDA · WYHG — `H4.adx14` +0.68 · `W.sma50.slope.d5` -0.64 · `px.expl_age` +0.63 · `W.sma50.slope.d10` -0.61 · `D.fib.retr.d10` +0.59
- **INLF** (2026-10-28) ⟵ YFOR · JAGX · OBAI · NNOX · EYPT — `W.sma34.slope.d5` +0.80 · `W.sma5x20.gap.d5` +0.75 · `W.sma34.slope.d10` +0.73 · `D.sma80.slope.d5` +0.72 · `W.sma5x20.gap.d10` +0.72
- **MEDS** (2026-11-17) ⟵ GTBP · VRAX · ARAY · SKYQ · YOUL — `px.base40_w.d10` -0.82 · `W.sma10x20.gap.d5` +0.81 · `px.base40_w.d5` -0.76 · `W.sma10x20.gap.d10` +0.76 · `W.macd.hist_p.d5` +0.73
- **ONEG** (2026-10-29) ⟵ KLXE · ARQ · HTCR · UXIN · HERE — `W.pdi14` +0.83 · `W.di_diff` +0.77 · `D.st.green20.d10` +0.66 · `D.st.green20.d5` +0.64 · `D.sma89.slope.d5` -0.63
- **WHLR** (2026-11-10) ⟵ ENLV · ELAB · VIVK · FFAI · GMEX — `D.sma80.slope.d5` -0.75 · `H4.ichi.thick_p.d5` +0.74 · `D.sma89.slope.d5` +0.73 · `D.sma21.slope.d5` +0.73 · `W.mfi14` +0.72
- **BKHA** (2026-10-20) ⟵ HAIN · LUCD · MDXH · NWGL · CJMB — `px.uwick5.d5` -0.95 · `vol.spike_d.d5` -0.92 · `vol.dry5_20.d5` -0.90 · `px.round_dist.d5` -0.88 · `H4.adx14.d5` -0.84
- **RAIN** (2026-11-12) ⟵ SAEN · NEGG · XGPU · DEFT · NAMI — `W.mfi14.d5` +0.68 · `H4.sma50.since` -0.68 · `H4.sma55.since` -0.66 · `W.mfi14.d10` +0.64 · `px.round_dist.d10` -0.63
- **WCT** (2026-11-06) ⟵ TGL · TRUG · DXST · DFLI · NXL — `H4.sma89.slope.d5` +0.88 · `H4.sma80.slope.d5` +0.86 · `H4.sma80.slope.d10` +0.84 · `H4.sma89.slope.d10` +0.77 · `W.rsi21` +0.74
- **ADXN** (2026-11-10) ⟵ NVX · WVE · METCB · AEC · THH — `D.psar.since` +0.76 · `W.ema89.since` +0.67 · `D.stoch.d.d10` -0.58 · `H4.st.green10` -0.58 · `px.expl_n` +0.57
- **KWM** (2026-11-19) ⟵ ARTL · KITT · ATYR · JTAI · ISPC — `px.base60_w.d10` -0.69 · `px.round_dist.d5` +0.63 · `D.sma150.slope.d5` +0.55 · `H4.sma200.slope.d10` +0.54 · `px.base40_w.d5` +0.54
- **NOMA** (2026-11-13) ⟵ TYGO · SLBT · VRRM · RTB · FMFC — `px.drop252.d10` -0.69 · `D.adx14.d5` -0.69 · `D.bot.adx.d5` -0.69 · `H4.don55.pos.d10` +0.67 · `H4.don55.pos` +0.58
- **NUWE** (2026-10-26) ⟵ NEXR · DBGI · GNPX · XXII · OBAI — `H4.ichi.thick_p.d10` -0.83 · `px.base60_w.d5` -0.76 · `D.psar.since` -0.74 · `px.base60_w.d10` -0.72 · `H4.ema5.dist` +0.71
- **SGLY** (2026-10-27) ⟵ MBAI · AMIX · IPDN · NNOX · VWAV — `D.sr.res_dist.d5` -0.76 · `vol.adl_slope20` +0.59 · `vol.cmf20` +0.59 · `px.round_dist.d5` +0.54 · `D.bot.adx` -0.53
- **SMTK** (2026-11-10) ⟵ BRNX · MDCX · TGL · TRUG · HUBC — `H4.ichi.thick_p.d10` -0.78 · `D.sma55.slope.d10` +0.76 · `W.sma8x15.gap.d5` +0.68 · `W.sma8x15.gap.d10` +0.66 · `H4.atr14_p.d10` +0.62
- **TANH** (2026-10-21) ⟵ XRTX · CENN · NYXH · BIOX · HAIN — `D.adx14.d5` -0.79 · `D.bot.adx.d5` -0.79 · `px.expl_age` -0.70 · `vol.spike_d.d10` -0.68 · `H4.cdl.doji.ago` -0.65
- **ZJK** (2026-11-19) ⟵ KPRX · NA · VIP · BEEM · MYSE — `ed.results_age` +0.60 · `D.st.inside10` +0.57 · `sh.ratio10.d10` +0.54 · `H4.mfi14` +0.50 · `W.ema89.since` -0.49
- **AEHL** (2026-11-04) ⟵ AUUD · GIPR · HRTX · MSAI · MRNO — `H4.sma30.since` -0.76 · `H4.ema30.since` -0.71 · `H4.sma34.since` -0.71 · `D.sr.res_dist.d5` +0.67 · `H4.ema34.since` -0.67
- **GDHG** (2026-11-13) ⟵ MLGO · JZXN · UK · ACON · RVSN — `id.float` +0.56 · `W.sma13.since` +0.54 · `W.macd.hist_p.d5` +0.51 · `sh.ratio10.d5` -0.51 · `sh.ratio5.d10` -0.51
- **RDAC** (2026-11-02) ⟵ SNOA · ARQ · SNGX · UONE · CDIO — `px.base60_w` +0.77 · `D.ichi.thick_p` +0.74 · `sh.ratio5.d5` -0.65 · `ed.n_13dg_90` +0.64 · `H4.atr14_p` +0.63
- **SAIQ** (2026-10-19) ⟵ FUSE · OFAL · VERI · PLSM · LGO — `H4.sma34.since` -0.71 · `H4.ema30.since` -0.70 · `H4.bb.width` +0.66 · `H4.kst.diff` -0.65 · `H4.sma5.slope.d10` -0.65
- **SLS** (2026-11-16) ⟵ INOD · HQ · BTCS · FCEL · IPWR — `H4.sma8.since` -0.74 · `H4.pdi14.d5` +0.74 · `H4.ema5.since` -0.72 · `vol.usd_d.d5` +0.71 · `vol.usd_med20.d10` +0.70
- **AIMD** (2026-11-11) ⟵ FOXX · LCFY · ARAY · DRIO · BRAG — `px.expl_n` +0.69 · `D.adx14.d5` -0.68 · `D.bot.adx.d5` -0.68 · `D.st.green10.d5` +0.63 · `vol.spike_d.d5` -0.62
- **AKAN** (2026-11-12) ⟵ HCWB · NXTS · CSAI · DFSC · FFAI — `D.sr.res_dist.d5` -0.57 · `D.sma200.slope.d10` +0.57 · `px.lwick10.d10` -0.53 · `D.sma80.slope.d5` -0.53 · `W.ichi.thick_p.d5` +0.53
- **MSS** (2026-11-19) ⟵ JTAI · ARTL · INVZ · ISPC · TNON — `H4.st.green20` +0.75 · `H4.sma8.since` -0.70 · `H4.sma10.since` -0.70 · `H4.sma5.slope` +0.69 · `ed.results_age` +0.67
- **NNOX** (2026-11-09) ⟵ MYSZ · PBK · SLBT · TPST · AIFC — `D.psar.since` -0.55 · `ed.n_form4_90` +0.53 · `D.sma40.slope.d5` -0.51 · `W.mfi14` -0.50 · `H4.sma8.since` +0.50
- **SAGT** (2026-10-19) ⟵ LOOP · IBIO · CGTL · AKBA · HIT — `W.adx14.d5` -0.67 · `W.adx14.d10` -0.65 · `H4.sma5.since` +0.55 · `px.lwick10` +0.54 · `W.stoch.d.d10` +0.53
- **CLRO** (2026-10-22) ⟵ ADVB · XRTX · OPNW · SLNH · YXT — `D.sma55.slope.d10` +0.77 · `H4.sma15.since` -0.71 · `px.lwick10.d10` -0.65 · `H4.ema10.since` -0.64 · `vol.obv_slope20` +0.63
- **FISN** (2026-11-05) ⟵ CBRS · AIIO · SWMR · WYFI · TPST — `ed.results_age` -0.56 · `D.gap.above_n` -0.49 · `ed.n_form4_90` -0.48 · `D.sma34.slope.d5` -0.47 · `W.rsi14.d10` +0.46
- **TTEC** (2026-11-09) ⟵ INSG · SMXT · GDTC · GRAN · SNGX — `D.don55.pos.d10` +0.67 · `W.bb.squeeze_rank` +0.65 · `D.don20.low_age` -0.60 · `H4.st.green10.d5` -0.57 · `H4.sma.nabove.d5` +0.57
- **VAI** (2026-11-05) ⟵ QTEX · ENSC · XRPN · TAOX · FFR — `H4.vwap_w.dist.d10` +0.74 · `H4.ema8.dist.d10` +0.72 · `H4.sma10.dist.d10` +0.70 · `H4.ema10.dist.d10` +0.70 · `H4.ema5.dist.d10` +0.70
- **VWAV** (2026-11-16) ⟵ IPDN · APVO · ARAI · SLBT · FMFC — `D.macd.hist_p` +0.83 · `D.bot.macd_hist_p` +0.83 · `H4.sma144.slope.d5` +0.83 · `D.macd.hist_p.d5` +0.81 · `D.bot.macd_hist_p.d5` +0.81
- **XHLD** (2026-11-05) ⟵ SWMR · NCI · ZTG · CRBP · LTRN — `H4.sma89.slope` +0.81 · `D.don20.low_age` +0.79 · `H4.sma100.slope` +0.79 · `W.sma10x20.gap` +0.77 · `D.sma50x100.gap` +0.75
- **CRIS** (2026-10-28) ⟵ RKDA · GNPX · RIME · CAPS · PSNY — `D.ema10.since` -0.63 · `D.st.green20` -0.57 · `D.sma200.slope.d5` +0.56 · `D.sma50.slope.d10` +0.56 · `px.expl_age` -0.54
- **GMM** (2026-11-11) ⟵ FNUC · DCOY · ERNA · ARTL · HDRN — `ed.n8k_30` +0.64 · `D.sma20.since` +0.58 · `sh.ratio10.d5` -0.56 · `sh.ratio5.d10` -0.56 · `D.ichi.thick_p.d10` -0.55
- **NTCL** (2026-11-04) ⟵ BRNX · IPW · TC · SMTK · NRSN — `W.rsi14` +0.77 · `W.rsi21` +0.70 · `W.rsi7` +0.69 · `H4.ema10.since` -0.67 · `W.st.inside10` +0.64
- **SNT** (2026-11-05) ⟵ ICMB · INSG · METCB · KTOS · VISN — `H4.st.green20` +0.72 · `H4.st.green20.d10` +0.72 · `H4.st.green20.d5` +0.68 · `sh.ratio_d.d5` +0.67 · `ed.results_age` +0.64
- **BRAI** (2026-10-26) ⟵ ITOC · GOAI · RENX · AMST · BGDE — `H4.st.green10.d5` +0.77 · `px.expl_n` -0.74 · `H4.st.green10.d10` +0.68 · `D.ichi.thick_p` +0.65 · `H4.don55.pos` +0.65
- **ONFO** (2026-11-12) ⟵ KIDZ · OBAI · ICCM · PWCM · QCLS — `H4.sma200.slope.d10` +0.71 · `H4.sma200.slope.d5` +0.67 · `W.mfi14` +0.64 · `sh.ratio5.d5` +0.63 · `D.sma89.slope.d10` -0.63
- **CIGL** (2026-11-19) ⟵ RKDA · WKSP · ORGO · NNOX · ANTA — `D.ichi.thick_p.d5` -0.74 · `vol.spike_d.d5` +0.71 · `D.sma200.slope.d5` -0.67 · `sh.ratio10.d5` -0.67 · `sh.ratio5.d10` -0.67
- **CYAB** (2026-11-10) ⟵ TPST · TRNR · AIFC · DFNS · CYN — `H4.ema100x200.gap.d5` +0.87 · `H4.ema50x200.gap.d5` +0.83 · `H4.ema100x200.gap.d10` +0.80 · `H4.ema50x200.gap.d10` +0.72 · `px.expl_n` -0.63
- **MF** (2026-10-28) ⟵ GOAI · AZIO · SVRE · IMNN · MTVA — `px.lwick10.d5` +0.78 · `H4.sma10x20.gap.d10` +0.77 · `W.don20.low_age` +0.75 · `vol.dry5_20.d5` -0.71 · `px.lwick10.d10` +0.69
- **STAK** (2026-10-21) ⟵ SNAL · AMPG · OTLK · PLSM · PN — `vol.obv_slope10.d5` -0.71 · `H4.ema144.since` -0.69 · `vol.adl_slope10.d5` -0.69 · `H4.ema150.since` -0.68 · `H4.sma200.since` -0.68
- **XCH** (2026-10-19) ⟵ PWCM · DBGI · VTIX · CIGL · POM — `D.ichi.thick_p.d5` -0.85 · `D.pdi14.d5` +0.75 · `W.adx14` -0.74 · `W.rsi21` +0.70 · `D.ema5.since` -0.70
- **AZI** (2026-11-16) ⟵ TRNR · ISPC · DETX · NEXM · AIFC — `W.ichi.thick_p.d5` -0.89 · `W.ichi.thick_p.d10` -0.88 · `W.mfi14` +0.69 · `H4.pdi14` +0.64 · `W.sma40.slope.d5` +0.60
- **BGIN** (2026-11-11) ⟵ FAC · RANI · NEON · CDIO · METC — `sh.ratio5.d5` +0.78 · `sh.ratio10.d5` +0.74 · `sh.ratio5.d10` +0.74 · `sh.ratio10.d10` +0.69 · `H4.st.green20.d5` -0.64
- **FCUV** (2026-11-12) ⟵ AGMH · KSCP · AIDX · SAEN · NEGG — `W.mfi14.d5` +0.64 · `cp.rs_n365` +0.62 · `W.sma15.slope.d5` -0.61 · `W.don20.low_age` +0.61 · `W.rsi7` +0.61
- **FTFT** (2026-10-27) ⟵ VTGN · TNON · AIDX · JTAI · WSHP — `D.kst.diff.d10` +0.77 · `D.bot.kst_diff.d10` +0.77 · `px.atl_dist` +0.67 · `px.low60_age` +0.67 · `W.don20.low_age` +0.66
- **OMH** (2026-11-03) ⟵ AIXI · CPOP · ZEO · WNW · FAMI — `W.sma15.slope.d5` -0.85 · `D.ichi.thick_p.d5` +0.82 · `W.bb.width.d10` +0.72 · `D.ichi.thick_p.d10` +0.68 · `W.sma15.slope.d10` -0.65
- **PCLA** (2026-10-28) ⟵ CDIO · IXHL · BTCS · DEFT · NVNO — `H4.st.green20.d10` -0.71 · `W.sma21.slope.d10` -0.68 · `W.sma21.slope.d5` -0.68 · `W.kst.val.d10` -0.66 · `W.adx14` +0.65
- **REKR** (2026-10-26) ⟵ NMTC · MCRB · MIST · GRSD · LOOP — `H4.ema34.since` -0.66 · `H4.sma34.since` -0.66 · `H4.sma30.since` -0.52 · `H4.ema30.since` -0.52 · `sh.vol_d.d10` +0.49
- **SMX** (2026-11-05) ⟵ TRUG · DCX · OBAI · TGL · CISS — `H4.ichi.thick_p.d5` -0.91 · `W.ichi.thick_p.d10` -0.86 · `W.st.green20` +0.82 · `W.sma20.slope.d10` +0.79 · `px.ret1` +0.79
- **TDTH** (2026-11-06) ⟵ NMTC · AXNX · SGLY · KUST · UPB — `D.sma144.slope.d10` +0.65 · `D.sma144.slope.d5` +0.62 · `D.sma30.slope.d10` -0.62 · `W.kst.diff.d5` -0.59 · `H4.sma200.slope.d5` -0.58
- **VIVS** (2026-11-18) ⟵ TAOP · ERNA · BRTX · GNPX · NHTC — `H4.st.green10` +0.65 · `H4.st.inside10` +0.57 · `H4.sma8.since` -0.56 · `W.sma40x80.gap.d5` -0.55 · `sh.ratio5.d5` -0.54
- **GIBO** (2026-10-29) ⟵ KMRK · BGM · DUO · SHPH · GOGO — `W.sma34.since` -0.73 · `W.sma40.since` -0.69 · `D.sma200.since` -0.69 · `W.rsi21` -0.67 · `px.expl_age` -0.65
- **NCT** (2026-11-10) ⟵ GOVX · AIIO · ADGM · CSAI · CVRX — `px.base40_w.d10` -0.89 · `D.macd.hist_p.d5` +0.80 · `D.bot.macd_hist_p.d5` +0.80 · `H4.sma144.slope.d10` +0.73 · `D.macd.hist_p.d10` +0.72
- **RPGL** (2026-10-22) ⟵ YFOR · SCNI · FXHO · AMOD · SPRC — `W.sma50.since` -0.79 · `W.ema50.since` -0.77 · `W.ema40.since` -0.68 · `W.bb.width.d5` +0.68 · `H4.sma50x200.gap.d10` +0.65
- **ZJYL** (2026-10-29) ⟵ SUPX · LXEH · RMCF · GRAN · NBP — `H4.mfi14.d10` -0.71 · `H4.mfi14` -0.63 · `H4.pdi14.d10` -0.59 · `D.sma100.slope.d5` -0.58 · `ed.n_13dg_90` +0.56

## ⑧ «ما فات البوت»

- سببُ رفض الفرز عند يوم القرار (بأرقام الإنتاج): M4_base_واسعة 23 · M_لا_مستوى_مختبر 23 · M1_سعر 21 · M2_هبوط_تحت_40 17 · M3_انفجار_تحت_60 6 · مرشّح 6 · M2_هبوط_فوق_97 3
- جدارُ صفّ «تحت المتابعة» للمتابَعين: — 64 · M1 سعر 2 · M3 انفجار تحت 60 1 · M4 عرض القاعدة فوق حدّ الفرز 1 · لا مستوى مختبَر بلمستين (مرساةُ الفرز) 1

| السهم | يوم القرار | في المتابعة | رفضُ الفرز | الجدار | الناقصُ وهامشُه | الجاهزيّة |
|---|---|---|---|---|---|---|
| AEYE | 2026-10-19 | لا | M2_هبوط_تحت_40 | — | — | — |
| AIOK | 2026-10-19 | لا | M2_هبوط_تحت_40 | — | — | — |
| ATGL | 2026-10-19 | لا | مرشّح | — | — | — |
| SAGT | 2026-10-19 | لا | مرشّح | — | — | — |
| SAIQ | 2026-10-19 | نعم | M3_انفجار_تحت_60 | — | — | 25 |
| XCH | 2026-10-19 | نعم | M4_base_واسعة | — | — | 30 |
| BKHA | 2026-10-20 | نعم | M3_انفجار_تحت_60 | — | — | 35 |
| RBNE | 2026-10-20 | نعم | M1_سعر | — | — | 0 |
| SPHL | 2026-10-20 | نعم | M_لا_مستوى_مختبر | — | — | 60 |
| CRMT | 2026-10-21 | نعم | M4_base_واسعة | — | — | 0 |
| STAK | 2026-10-21 | نعم | M_لا_مستوى_مختبر | — | — | 35 |
| TANH | 2026-10-21 | نعم | M_لا_مستوى_مختبر | — | — | 0 |
| CLRO | 2026-10-22 | نعم | M4_base_واسعة | — | — | 60 |
| RPGL | 2026-10-22 | نعم | M2_هبوط_فوق_97 | — | — | 0 |
| BRAI | 2026-10-26 | نعم | M4_base_واسعة | — | — | 0 |
| NUWE | 2026-10-26 | نعم | M4_base_واسعة | — | — | 20 |
| POM | 2026-10-26 | نعم | M4_base_واسعة | — | — | 30 |
| REKR | 2026-10-26 | نعم | M1_سعر | — | — | 0 |
| TREO | 2026-10-26 | لا | M3_انفجار_تحت_60 | — | — | — |
| CHSN | 2026-10-27 | نعم | M_لا_مستوى_مختبر | — | — | 70 |
| FTFT | 2026-10-27 | نعم | M_لا_مستوى_مختبر | — | — | 0 |
| SGLY | 2026-10-27 | نعم | M1_سعر | — | — | 20 |
| ULBI | 2026-10-27 | لا | M2_هبوط_تحت_40 | — | — | — |
| CRIS | 2026-10-28 | نعم | M4_base_واسعة | — | — | 60 |
| INLF | 2026-10-28 | نعم | M1_سعر | — | — | 25 |
| MF | 2026-10-28 | نعم | M4_base_واسعة | — | — | 0 |
| NCPL | 2026-10-28 | لا | M2_هبوط_تحت_40 | — | — | — |
| PCLA | 2026-10-28 | لا | M2_هبوط_تحت_40 | — | — | — |
| BTOG | 2026-10-29 | لا | M4_base_واسعة | — | — | — |
| GIBO | 2026-10-29 | لا | M2_هبوط_تحت_40 | — | — | — |
| ONEG | 2026-10-29 | نعم | M_لا_مستوى_مختبر | — | — | 40 |
| SEGG | 2026-10-29 | نعم | M_لا_مستوى_مختبر | — | — | 10 |
| SLGB | 2026-10-29 | نعم | M1_سعر | — | — | 20 |
| ZJYL | 2026-10-29 | لا | مرشّح | — | — | — |
| IFBD | 2026-10-30 | لا | M2_هبوط_تحت_40 | — | — | — |
| INO | 2026-10-30 | نعم | M_لا_مستوى_مختبر | — | — | 0 |
| PMAX | 2026-10-30 | نعم | M_لا_مستوى_مختبر | — | — | 20 |
| CNSY | 2026-11-02 | نعم | M_لا_مستوى_مختبر | — | — | 35 |
| PARA | 2026-11-02 | نعم | M4_base_واسعة | — | — | 0 |
| RDAC | 2026-11-02 | نعم | M_لا_مستوى_مختبر | — | — | 60 |
| ZNB | 2026-11-02 | لا | M2_هبوط_فوق_97 | — | — | — |
| JXG | 2026-11-03 | لا | M2_هبوط_تحت_40 | — | — | — |
| OMH | 2026-11-03 | لا | مرشّح | — | — | — |
| RETO | 2026-11-03 | نعم | M4_base_واسعة | — | — | 20 |
| AEHL | 2026-11-04 | نعم | M4_base_واسعة | — | — | 10 |
| LABT | 2026-11-04 | نعم | M1_سعر | — | — | 35 |
| NTCL | 2026-11-04 | نعم | M4_base_واسعة | — | — | 50 |
| AIHS | 2026-11-05 | لا | M2_هبوط_تحت_40 | — | — | — |
| FISN | 2026-11-05 | لا | M3_انفجار_تحت_60 | — | — | — |
| NUAI | 2026-11-05 | نعم | M4_base_واسعة | — | — | 0 |
| RAYA | 2026-11-05 | نعم | M_لا_مستوى_مختبر | — | — | 0 |
| SDA | 2026-11-05 | نعم | M1_سعر | — | — | 0 |
| SMX | 2026-11-05 | نعم | M2_هبوط_فوق_97 | — | — | 55 |
| SNT | 2026-11-05 | نعم | M_لا_مستوى_مختبر | — | — | 10 |
| VAI | 2026-11-05 | لا | M2_هبوط_تحت_40 | — | — | — |
| VIVK | 2026-11-05 | نعم | M1_سعر | — | — | 10 |
| XHLD | 2026-11-05 | نعم | M4_base_واسعة | — | — | 45 |
| CMCT | 2026-11-06 | نعم | M_لا_مستوى_مختبر | — | — | 35 |
| ESLA | 2026-11-06 | نعم | M1_سعر | — | — | 25 |
| NWGL | 2026-11-06 | نعم | M4_base_واسعة | — | — | 10 |
| TDTH | 2026-11-06 | نعم | M_لا_مستوى_مختبر | — | — | 60 |
| WCT | 2026-11-06 | لا | M_لا_مستوى_مختبر | — | — | — |
| NNOX | 2026-11-09 | نعم | M1_سعر | — | — | 15 |
| PEPG | 2026-11-09 | لا | M2_هبوط_تحت_40 | — | — | — |
| TTEC | 2026-11-09 | لا | M2_هبوط_تحت_40 | — | — | — |
| ADXN | 2026-11-10 | نعم | مرشّح | — | — | 35 |
| CENN | 2026-11-10 | نعم | M1_سعر | — | — | 0 |
| CYAB | 2026-11-10 | نعم | M1_سعر | — | — | 25 |
| ELOG | 2026-11-10 | نعم | M_لا_مستوى_مختبر | — | — | 15 |
| NCT | 2026-11-10 | نعم | M4_base_واسعة | — | — | 10 |
| SMTK | 2026-11-10 | نعم | M1_سعر | — | — | 60 |
| WHLR | 2026-11-10 | نعم | M1_سعر | — | — | 10 |
| AIMD | 2026-11-11 | نعم | M4_base_واسعة | — | — | 20 |
| BGIN | 2026-11-11 | لا | M2_هبوط_تحت_40 | — | — | — |
| GMM | 2026-11-11 | نعم | مرشّح | — | — | 60 |
| GP | 2026-11-11 | نعم | M4_base_واسعة | — | — | 35 |
| XLAB | 2026-11-11 | لا | M4_base_واسعة | — | — | — |
| AKAN | 2026-11-12 | نعم | M_لا_مستوى_مختبر | — | — | 20 |
| FCUV | 2026-11-12 | نعم | M_لا_مستوى_مختبر | — | — | 35 |
| ONFO | 2026-11-12 | نعم | M1_سعر | — | — | 25 |
| RAIN | 2026-11-12 | نعم | M_لا_مستوى_مختبر | — | — | 10 |
| SLSN | 2026-11-12 | لا | M2_هبوط_تحت_40 | — | — | — |
| GDHG | 2026-11-13 | نعم | M_لا_مستوى_مختبر | — | — | 0 |
| HIHO | 2026-11-13 | لا | M2_هبوط_تحت_40 | — | — | — |
| NOMA | 2026-11-13 | نعم | M3_انفجار_تحت_60 | — | — | 0 |
| AZI | 2026-11-16 | نعم | M_لا_مستوى_مختبر | — | — | 0 |
| FRTT | 2026-11-16 | لا | M1_سعر | — | — | — |
| SLS | 2026-11-16 | لا | M2_هبوط_تحت_40 | — | — | — |
| VWAV | 2026-11-16 | نعم | M1_سعر | — | — | 10 |
| MEDS | 2026-11-17 | نعم | M4_base_واسعة | — | — | 15 |
| SKYA | 2026-11-17 | لا | M2_هبوط_تحت_40 | — | — | — |
| SVRE | 2026-11-17 | نعم | M4_base_واسعة | — | — | 10 |
| SEAT | 2026-11-18 | نعم | M3_انفجار_تحت_60 | M3 انفجار تحت 60 | M3 الانفجار السابق (دون الحدّ) (هامش 23.84%) | 50 |
| VIVS | 2026-11-18 | لا | M1_سعر | — | — | — |
| CIGL | 2026-11-19 | نعم | M1_سعر | M1 سعر | M1 السعر (دون الحدّ) (هامش 56.45%) | 60 |
| KWM | 2026-11-19 | لا | M1_سعر | — | — | — |
| MSS | 2026-11-19 | نعم | M_لا_مستوى_مختبر | لا مستوى مختبَر بلمستين (مرساةُ الفرز) | — | 0 |
| NXAT | 2026-11-19 | نعم | M1_سعر | M1 سعر | M1 السعر (دون الحدّ) (هامش 44.08%) | 10 |
| ZJK | 2026-11-19 | نعم | M4_base_واسعة | M4 عرض القاعدة فوق حدّ الفرز | M5 السيولة الدولارية (دون الحدّ) (هامش 6.28%) | 0 |

## ⑨ الصفقة (وصف): شراءُ افتتاح اليوم التالي للقرار وبيعُ إغلاق الجلسة العشرين · كلفة 1.8%

- المنفجرون: متوسّط 28.6% · وسيط 10.1% · خاسرون 45.5% (من 99)
- الضابطة: متوسّط -24.7% · وسيط -23.4% · خاسرون 90.7% (من 17,009)

