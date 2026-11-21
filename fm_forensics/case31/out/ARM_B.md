# ⚖️ `T-CASE31` — الذراع B: المقارنةُ واختبارُ الخلط (مولَّدٌ آليًّا · لا يُعدَّل باليد)

- المجتمع (B): صفوف 12,662 · **منفجرون 254** (منهم خارج «تحت المتابعة» 0) · ضابطة 12,408 · رماديٌّ مستبعَد 1285 · بلا وسم 0 · أيّامُ قرار 208 (بلا لقطة 0) · ضابطةٌ لم تكتمل نافذتُها 0
- **المجرَّب:** سمات 1,866 (المؤهَّلة بالتغطية 1,725) · شروط 6,194 (الصالحة منفردةً 5,804) · توليفات 10,660 · نماذج 2 × 20 طيّة · خلطات 1,000

## ① نتيجةُ الخلط (القِمم: المرصودُ مقابل المئين 95 لأقصى الخلطات)

| القمّة | المرصود | مئين 95 للخلطات | يفوق من الخلطات | الحكم |
|---|---|---|---|---|
| أقوى شرطٍ منفرد (z) | 9.522 | 3.774 | 100.0% | ✅ يعبر |
| أقوى توليفة (z) | 10.606 | 6.513 | 100.0% | ✅ يعبر |
| أقوى بصمة (z) | 10.606 | 6.513 | 100.0% | ✅ يعبر |
| أقوى سمة استبعاد (اختصار) | 0.000 | 0.000 | 0.0% | ❌ في حدود الصدفة |
| شجرةُ القرار (AUC داخل اليوم) | 0.621 | 0.545 | 100.0% | ✅ يعبر |
| اللوجستيّ (AUC داخل اليوم) | 0.677 | 0.546 | 100.0% | ✅ يعبر |
| الشجرة: منفجرون في أعلى 5% | 0.056 | 0.031 | 100.0% | ✅ يعبر |
| اللوجستيّ: منفجرون في أعلى 5% | 0.064 | 0.030 | 100.0% | ✅ يعبر |

## ② أهمُّ الفروق (السمات مرتّبةً بالفرق المعياريّ · فاصل 95% عنقوديّ بيوم القرار)

| السمة | عند المنفجرين | عند الضابطة | الفرق (رتبة) | الفاصل | مقابل ضابط الزخم | التغطية |
|---|---|---|---|---|---|---|
| `D.atr14_p` | 0.1362 | 0.1085 | +0.159 | [+0.126، +0.190] | 0.109 | 100% |
| `D.bot.atr_p` | 0.1359 | 0.1083 | +0.158 | [+0.125، +0.190] | 0.110 | 100% |
| `D.ema20.slope` | -0.0696 | -0.0349 | -0.155 | [-0.190، -0.119] | -0.121 | 100% |
| `D.ema21.slope` | -0.0698 | -0.0347 | -0.155 | [-0.190، -0.119] | -0.121 | 100% |
| `D.ema8x15.gap` | -0.0543 | -0.0254 | -0.154 | [-0.189، -0.119] | -0.121 | 100% |
| `D.ema15.slope` | -0.0713 | -0.0350 | -0.153 | [-0.188، -0.117] | -0.116 | 100% |
| `D.ema30.slope` | -0.0639 | -0.0343 | -0.153 | [-0.187، -0.117] | -0.125 | 100% |
| `D.ema5x20.gap` | -0.1176 | -0.0531 | -0.153 | [-0.188، -0.118] | -0.117 | 100% |
| `D.ema8x21.gap` | -0.0904 | -0.0470 | -0.153 | [-0.188، -0.117] | -0.123 | 100% |
| `D.ema34.slope` | -0.0633 | -0.0338 | -0.152 | [-0.186، -0.116] | -0.126 | 100% |
| `H4.ema200.slope` | -0.0175 | -0.0111 | -0.152 | [-0.186، -0.118] | -0.122 | 100% |
| `D.ema13.slope` | -0.0712 | -0.0348 | -0.151 | [-0.185، -0.114] | -0.112 | 100% |
| `D.ema10x20.gap` | -0.0688 | -0.0362 | -0.151 | [-0.186، -0.115] | -0.123 | 100% |
| `D.ema40.slope` | -0.0594 | -0.0333 | -0.151 | [-0.184، -0.115] | -0.126 | 100% |
| `D.sma5x20.gap` | -0.1126 | -0.0514 | -0.150 | [-0.183، -0.114] | -0.119 | 100% |
| `W.ema15.dist` | -0.3532 | -0.2099 | -0.150 | [-0.184، -0.113] | -0.128 | 99% |
| `D.ema50.dist` | -0.2816 | -0.1632 | -0.150 | [-0.184، -0.114] | -0.119 | 100% |
| `D.macd.line_p` | -0.1128 | -0.0537 | -0.150 | [-0.185، -0.114] | -0.125 | 100% |
| `W.ema13.dist` | -0.3079 | -0.1808 | -0.149 | [-0.183، -0.113] | -0.124 | 100% |
| `W.ema10.dist` | -0.2420 | -0.1369 | -0.149 | [-0.184، -0.113] | -0.117 | 100% |
| `D.ema55.dist` | -0.3119 | -0.1785 | -0.149 | [-0.183، -0.112] | -0.122 | 100% |
| `D.ema80.dist` | -0.3945 | -0.2521 | -0.149 | [-0.182، -0.113] | -0.129 | 99% |
| `D.bot.ema50_dist` | -0.2804 | -0.1629 | -0.149 | [-0.183، -0.113] | -0.119 | 100% |
| `D.sma13.slope` | -0.0721 | -0.0336 | -0.148 | [-0.182، -0.111] | -0.123 | 100% |
| `H4.ema150.slope` | -0.0192 | -0.0116 | -0.148 | [-0.183، -0.113] | -0.113 | 100% |
| `H4.atr14_p` | 0.0669 | 0.0540 | +0.147 | [+0.118، +0.177] | 0.095 | 100% |
| `H4.ema144.slope` | -0.0191 | -0.0117 | -0.147 | [-0.182، -0.112] | -0.111 | 100% |
| `D.ema89.dist` | -0.4138 | -0.2775 | -0.147 | [-0.180، -0.112] | -0.129 | 99% |
| `D.ema40.dist` | -0.2422 | -0.1320 | -0.147 | [-0.181، -0.112] | -0.112 | 100% |
| `H4.ema34x89.gap` | -0.1226 | -0.0671 | -0.147 | [-0.181، -0.110] | -0.121 | 100% |
| `D.ema50.slope` | -0.0547 | -0.0325 | -0.146 | [-0.179، -0.111] | -0.128 | 100% |
| `H4.ema21x55.gap` | -0.0865 | -0.0433 | -0.146 | [-0.182، -0.108] | -0.109 | 100% |
| `H4.bb.width` | 0.2716 | 0.2015 | +0.146 | [+0.110، +0.179] | 0.082 | 100% |
| `W.sma10.dist` | -0.2428 | -0.1249 | -0.146 | [-0.184، -0.110] | -0.110 | 100% |
| `W.ema8.dist` | -0.2047 | -0.1061 | -0.146 | [-0.181، -0.111] | -0.110 | 100% |
| `H4.sma20x50.gap` | -0.0753 | -0.0376 | -0.146 | [-0.179، -0.110] | -0.116 | 100% |
| `H4.ema40x80.gap` | -0.0906 | -0.0490 | -0.146 | [-0.181، -0.109] | -0.120 | 100% |
| `D.ema100.dist` | -0.4638 | -0.3081 | -0.146 | [-0.179، -0.110] | -0.128 | 98% |
| `H4.sma21x55.gap` | -0.0857 | -0.0422 | -0.145 | [-0.180، -0.109] | -0.119 | 100% |
| `D.ema55.slope` | -0.0533 | -0.0323 | -0.145 | [-0.178، -0.110] | -0.128 | 100% |

## ③ أقوى الشروط المنفردة

| الشرط | z | المنفجرون الحاملون | كلُّ الحاملين | مقابل ضابط الزخم | وسيطُ المهلة (جلسات) |
|---|---|---|---|---|---|
| `D.ema5x20.gap<q20` | 9.52 | 118 | 2,533 | 0.209 | 8 |
| `D.ema8x15.gap<q20` | 9.38 | 117 | 2,533 | 0.210 | 9 |
| `W.sma10.dist<q20` | 9.25 | 116 | 2,531 | 0.198 | 9 |
| `D.sma50.dist<q20` | 9.11 | 115 | 2,529 | 0.197 | 12 |
| `D.ema13.slope<q20` | 9.10 | 115 | 2,533 | 0.190 | 7 |
| `D.ema15.slope<q20` | 9.10 | 115 | 2,533 | 0.191 | 7 |
| `D.ema20.slope<q20` | 9.10 | 115 | 2,533 | 0.197 | 8 |
| `D.ema8x21.gap<q20` | 9.10 | 115 | 2,533 | 0.205 | 10 |
| `H4.ema20x50.gap<q20` | 9.10 | 115 | 2,533 | 0.202 | 9 |
| `D.sma40.dist<q20` | 8.96 | 114 | 2,532 | 0.185 | 10 |
| `D.ema21.slope<q20` | 8.95 | 114 | 2,533 | 0.196 | 8 |
| `D.sma34.dist<q20` | 8.81 | 113 | 2,533 | 0.182 | 8 |
| `D.sma30.dist<q20` | 8.67 | 112 | 2,533 | 0.178 | 8 |
| `D.ema10x20.gap<q20` | 8.67 | 112 | 2,533 | 0.198 | 11 |
| `H4.ema21x55.gap<q20` | 8.67 | 112 | 2,533 | 0.190 | 9 |
| `W.sma8.dist<q20` | 8.67 | 112 | 2,533 | 0.180 | 8 |
| `H4.sma50.slope<q20` | 8.53 | 111 | 2,533 | 0.192 | 7 |
| `px.ret20<q20` | 8.43 | 110 | 2,523 | 0.189 | 6 |
| `D.ema10.slope<q20` | 8.39 | 110 | 2,533 | 0.169 | 6 |
| `D.ema30.dist<q20` | 8.39 | 110 | 2,533 | 0.165 | 7 |

## ④ أقوى التوليفات حتى 3 شروط

| التوليفة | z | المنفجرون | الحاملون | نسبةُ الانفجار | مقابل ضابط الزخم |
|---|---|---|---|---|---|
| `px.ret20<q20` ∧ `W.sma13.dist<q20` ∧ `D.sma21.dist<q20` | 10.61 | 82 | 1,357 | 6.0% | 0.178 |
| `D.ema5x20.gap<q20` ∧ `D.sma34.dist<q20` ∧ `px.ret20<q20` | 10.60 | 101 | 1,849 | 5.5% | 0.204 |
| `D.sma50.dist<q20` ∧ `H4.ema20x50.gap<q20` ∧ `px.ret20<q20` | 10.55 | 89 | 1,542 | 5.8% | 0.187 |
| `px.ret20<q20` ∧ `D.ema10.slope<q20` ∧ `W.sma13.dist<q20` | 10.54 | 78 | 1,267 | 6.2% | 0.169 |
| `H4.ema20x50.gap<q20` ∧ `px.ret20<q20` ∧ `W.sma13.dist<q20` | 10.52 | 84 | 1,418 | 5.9% | 0.181 |
| `D.ema5x20.gap<q20` ∧ `D.sma30.dist<q20` ∧ `W.sma13.dist<q20` | 10.50 | 93 | 1,652 | 5.6% | 0.190 |
| `D.sma30.dist<q20` ∧ `px.ret20<q20` ∧ `W.sma13.dist<q20` | 10.50 | 87 | 1,497 | 5.8% | 0.183 |
| `D.ema13.slope<q20` ∧ `D.ema21.slope<q20` ∧ `px.ret20<q20` | 10.50 | 96 | 1,732 | 5.5% | 0.196 |
| `D.ema5x20.gap<q20` ∧ `D.sma50.dist<q20` ∧ `D.sma30.dist<q20` | 10.50 | 99 | 1,812 | 5.5% | 0.195 |
| `D.ema5x20.gap<q20` ∧ `D.sma30.dist<q20` ∧ `px.ret20<q20` | 10.47 | 101 | 1,871 | 5.4% | 0.201 |
| `D.ema5x20.gap<q20` ∧ `W.sma10.dist<q20` ∧ `D.sma30.dist<q20` | 10.45 | 102 | 1,900 | 5.4% | 0.196 |
| `D.ema5x20.gap<q20` ∧ `px.ret20<q20` ∧ `W.sma13.dist<q20` | 10.44 | 87 | 1,505 | 5.8% | 0.182 |
| `D.ema5x20.gap<q20` ∧ `D.sma50.dist<q20` ∧ `px.ret20<q20` | 10.44 | 92 | 1,636 | 5.6% | 0.189 |
| `D.ema5x20.gap<q20` ∧ `px.ret20<q20` ∧ `D.sma21.dist<q20` | 10.42 | 95 | 1,717 | 5.5% | 0.193 |
| `D.ema5x20.gap<q20` ∧ `D.ema13.slope<q20` ∧ `px.ret20<q20` | 10.41 | 96 | 1,745 | 5.5% | 0.192 |

## ⑤ سماتُ الاستبعاد (أقلُّ من 5% من المنفجرين و20% فأكثر من الضابطة) — **في حدود الصدفة**

| الشرط | يختصر من القائمة | يحمله من المنفجرين |
|---|---|---|
| لا سمةَ بالتعريف | — | — |

## ⑥ لكلّ نوع (الشروطُ المنفردة وحدَها وخلطُها)

| النوع | المنفجرون | أقوى شرط | z | مئين 95 | الحكم |
|---|---|---|---|---|---|
| بخبر | 0 | — | — | — | دون الحدّ — وصفٌ بلا بحث |
| بلا خبر | 0 | — | — | — | دون الحدّ — وصفٌ بلا بحث |
| يومٌ واحد | 97 | `D.sma30.dist<q20` | 8.84 | 3.78 | ✅ يعبر |
| عدّة أيام | 157 | `H4.ema20x50.gap<q20` | 5.69 | 3.79 | ✅ يعبر |
| شمعةٌ واحدة | 174 | `D.ema5x20.gap<q20` | 8.42 | 3.76 | ✅ يعبر |
| موجات | 80 | `H4.sma144.dist<q20` | 5.30 | 3.60 | ✅ يعبر |
| بعد تقسيمٍ عكسيّ | 30 | `W.sma10.above=0` | 1.49 | 0.96 | ✅ يعبر |
| بلا تقسيمٍ حديث | 224 | `D.ema5x20.gap<q20` | 7.87 | 3.85 | ✅ يعبر |

## ⑦ أقرب الجيران (لكلّ منفجرٍ أشبهُ 5 لم تنفجر في يومه وأكبرُ ما فرّقه)

- **AERT** (2025-09-17) ⟵ LNZA · IVDA · LFWD · ORKT · LMFA — `vol.obv_slope20.d5` -0.77 · `vol.obv_slope20.d10` -0.76 · `vol.updown20.d5` -0.75 · `vol.updown20.d10` -0.74 · `px.ret20.d5` -0.69
- **INBS** (2025-12-30) ⟵ CXAI · IPDN · AIFF · CYCN · BOXL — `vol.obv_slope20.d10` +0.67 · `W.ema55.since` +0.66 · `px.uwick5.d10` -0.63 · `W.ema50.since` +0.63 · `H4.sma200.slope.d10` +0.62
- **LOBO** (2025-04-14) ⟵ ALGS · NEGG · TPST · CALC · HBIO — `sh.ratio5` -0.72 · `sh.ratio_d` -0.69 · `sh.ratio10` -0.68 · `H4.bb.width.d5` +0.58 · `H4.sma8.slope` +0.58
- **LOBO** (2025-11-17) ⟵ CISO · CXAI · GXAI · BTCT · LNZA — `W.ema80.since` -0.70 · `D.adx14.d10` -0.64 · `D.bot.adx.d10` -0.64 · `W.don20.low_age` +0.64 · `px.lwick10.d10` -0.61
- **MSGY** (2025-11-07) ⟵ DKI · BIAF · ISPC · HUBC · JYD — `D.ichi.thick_p.d5` -0.77 · `H4.sma89.dist.d5` +0.75 · `H4.ema20.since` -0.70 · `D.bot.macd_hist_p.d5` +0.69 · `D.ichi.thick_p` -0.67
- **ORKT** (2025-12-05) ⟵ HCWB · IQST · WETO · HYFM · CNTY — `H4.sma30.since` +0.69 · `H4.sma34.since` +0.61 · `H4.willr14` -0.57 · `H4.st.inside10` -0.56 · `H4.kdj.j` -0.53
- **ADGM** (2025-04-16) ⟵ AMOD · FEBO · MBRX · FGL · KSCP — `W.mfi14.d5` +0.68 · `px.base40_w.d10` +0.65 · `D.sma34.slope.d5` -0.63 · `W.mfi14.d10` +0.63 · `W.macd.hist_p.d5` -0.62
- **BTCT** (2025-01-16) ⟵ GREE · ISPC · DUO · COCH · TELO — `D.sma50x200.gap.d10` +0.71 · `D.sma50x200.gap.d5` +0.71 · `px.ret1.d10` -0.70 · `H4.sma50x100.gap.d10` +0.69 · `W.kst.diff` +0.68
- **FEAM** (2025-10-02) ⟵ KXIN · PRFX · GITS · CMCT · KROS — `sh.ratio_d.d5` +0.69 · `sh.ratio_d` +0.68 · `D.st.green10` -0.62 · `D.st.green20` -0.62 · `H4.sma89.slope.d10` -0.59
- **KALA** (2025-11-25) ⟵ DKI · AEMD · ADGM · LGCL · WETO — `H4.sma80.since` -0.87 · `H4.sma89.since` -0.86 · `H4.sma100.since` -0.86 · `H4.ema55.since` -0.78 · `D.sma8.since` +0.73
- **WGS** (2024-01-26) ⟵ KALA · ISPC · EDSA · APM · GLMD — `W.sma55.slope.d10` +0.71 · `vol.usd_med20` +0.69 · `W.sma55.slope.d5` +0.68 · `H4.sma80.since` +0.66 · `H4.st.green20` +0.64
- **APVO** (2025-06-17) ⟵ MYNZ · BDRX · INTS · CAMP · ICU — `px.base40_w.d5` -0.79 · `px.base40_w.d10` -0.66 · `W.sma30.slope.d5` -0.65 · `W.sma30.slope.d10` -0.65 · `H4.st.inside10` -0.63
- **CGTX** (2024-12-17) ⟵ LRHC · JZXN · NDLS · ATLX · BNAI — `vol.obv_slope20` -0.66 · `vol.updown20` -0.66 · `D.sma100.slope.d5` -0.65 · `sh.vol_d.d10` -0.59 · `H4.st.green10.d10` +0.57
- **CMND** (2024-01-23) ⟵ ADIL · MYSZ · HUBC · LGVN · BOXL — `H4.bb.width.d5` -0.77 · `H4.sma10x20.gap.d5` +0.73 · `H4.sma8x21.gap.d5` +0.72 · `H4.macd.line_p.d5` +0.70 · `D.sr.res_dist.d5` -0.69
- **CYCC** (2024-10-15) ⟵ AUUD · DRMA · WLDS · SXTP · TCRT — `W.sma50.slope.d10` -0.73 · `W.sma40.slope.d10` +0.69 · `W.sma50.slope.d5` -0.66 · `W.sma40.slope.d5` +0.65 · `H4.sma144.slope.d10` -0.62
- **FUFU** (2024-06-11) ⟵ APYX · ATER · MIRA · MBRX · GMM — `H4.sma200.slope.d5` +0.72 · `W.rsi21` -0.68 · `W.sma13.since` -0.62 · `D.don20.low_age` +0.60 · `W.rsi14` -0.57
- **IBG** (2025-07-11) ⟵ SPRC · GFAI · GMM · HUIZ · DTSS — `H4.vwap_w.dist` -0.79 · `W.mfi14.d5` -0.78 · `W.rsi21` -0.74 · `px.ret60.d10` -0.72 · `px.low60_age` -0.72
- **IBG** (2025-09-22) ⟵ MNDR · BNZI · GTBP · JSPR · EHGO — `H4.adx14` -0.76 · `H4.sma150.slope.d10` -0.61 · `H4.adx14.d10` -0.60 · `px.ret5.d5` -0.60 · `sh.ratio_d` +0.59
- **JZXN** (2023-07-12) ⟵ RPID · ILAG · MLGO · HTOO · JCSE — `D.bot.mfi.d5` -0.65 · `D.mfi14.d5` -0.65 · `D.st.green10.d10` -0.61 · `W.st.inside10` -0.59 · `H4.st.hl_run` +0.58
- **JZXN** (2024-12-10) ⟵ ABVC · RSLS · MYNZ · EZGO · XOS — `H4.mfi14` +0.76 · `W.mfi14.d5` +0.71 · `W.sma80.slope.d5` +0.66 · `D.st.inside10` +0.65 · `D.sma100.slope.d10` +0.65
- **JZXN** (2025-04-07) ⟵ ALBT · AIFF · MIRA · ICU · ATLX — `px.drop252.d10` -0.95 · `px.drop252.d5` -0.91 · `H4.sma5.slope` +0.76 · `H4.ema5.slope` +0.69 · `px.base40_w.d5` -0.69
- **MOBX** (2024-11-21) ⟵ ALZN · HOLO · IPA · TPST · AQB — `D.psar.since` -0.80 · `W.sma50.slope.d10` -0.68 · `W.sma50.slope.d5` -0.66 · `D.bot.adx` +0.65 · `D.adx14` +0.65
- **PPBT** (2025-10-28) ⟵ CUPR · GLE · BIVI · EJH · INTJ — `D.sma40x80.gap.d5` -0.78 · `H4.sma144.slope` -0.77 · `W.sma10.slope.d5` -0.76 · `D.sma40x80.gap.d10` -0.76 · `D.sma50.slope.d5` -0.75
- **XOS** (2025-02-19) ⟵ LGVN · PRSO · FCEL · CXAI · GLMD — `vol.obv_slope10.d5` -0.76 · `vol.obv_slope10.d10` -0.72 · `D.sr.sup_touches` +0.65 · `vol.obv_slope20.d5` -0.65 · `D.gap.above_n` +0.63
- **XTIA** (2024-06-04) ⟵ DBGI · BFRI · DRMA · ALLR · RR — `W.rsi21` +0.86 · `D.sma50.slope.d10` +0.72 · `W.macd.hist_p.d10` +0.67 · `px.lwick10.d10` +0.65 · `H4.sma200.slope.d10` +0.64
- **GREE** (2023-06-13) ⟵ FEMY · HUDI · CMND · ALPS · DBGI — `H4.sma8.since` +0.74 · `px.base20_w.d10` +0.72 · `px.base20_w.d5` +0.70 · `D.sma34x89.gap.d5` -0.68 · `H4.ema100x200.gap.d10` -0.68
- **IBIO** (2025-10-20) ⟵ TECX · IPW · GRI · INTZ · JUNS — `W.sma34.slope.d10` -0.86 · `W.sma34.slope.d5` -0.83 · `W.sma30.slope.d5` -0.75 · `D.sma150.slope` -0.72 · `W.sma30.slope` -0.71
- **INHD** (2025-11-21) ⟵ BIAF · ICU · ALTS · BNRG · WETO — `D.bot.atr_p.d5` -0.71 · `D.atr14_p.d5` -0.71 · `W.di_diff` +0.69 · `W.pdi14` +0.68 · `H4.sma50x200.gap.d5` +0.64
- **LGVN** (2024-04-05) ⟵ GDC · AZ · MLGO · LAES · GSUN — `H4.sma34.since` -0.90 · `H4.sma40.since` -0.87 · `H4.ema34.since` -0.86 · `H4.ema30.since` -0.85 · `H4.ema40.since` -0.84
- **LGVN** (2024-04-12) ⟵ GDC · MLGO · AZ · CING · ACXP — `vol.dry5_20.d10` +0.85 · `W.mfi14.d10` +0.74 · `H4.bb.width.d10` +0.73 · `H4.atr14_p.d5` +0.71 · `W.mdi14.d5` -0.71
- **TPST** (2024-08-12) ⟵ MNY · ENGN · SPRB · CRIS · ATLX — `W.sma40.slope.d10` -0.73 · `H4.adx14.d5` -0.71 · `W.sma40.slope.d5` -0.67 · `vol.usd_d.d5` +0.64 · `px.round_dist.d5` -0.63
- **XHG** (2024-12-18) ⟵ GLTO · BETR · TPST · MASS · GNLN — `D.st.green10` +0.77 · `W.sma50.slope.d10` +0.75 · `D.st.green10.d10` +0.74 · `D.st.green20.d10` +0.74 · `D.ema5.since` -0.73
- **AKTX** (2024-05-21) ⟵ APYX · DRUG · FAMI · GNLX · FBYD — `H4.sma150.since` +0.80 · `H4.sma144.since` +0.78 · `sh.ratio_d` -0.74 · `D.mfi14.d5` -0.73 · `D.bot.mfi.d5` -0.73
- **AQB** (2025-03-24) ⟵ EZGO · CRBP · DUO · MKZR · MOBX — `vol.adl_slope10.d5` +0.82 · `D.sma144.slope.d5` +0.75 · `D.sma144.slope.d10` +0.69 · `px.round_dist.d10` -0.68 · `D.ichi.thick_p` -0.65
- **CLGN** (2025-07-11) ⟵ HCWB · CAMP · INAB · ERNA · JAGX — `H4.sma80.slope.d10` -0.75 · `H4.sma89.slope.d5` -0.74 · `H4.ichi.thick_p` +0.71 · `H4.sma89.slope.d10` -0.68 · `sh.ratio_d.d10` +0.65
- **ELOX** (2023-04-03) ⟵ IMTE · BJDX · ENVB · WLDS · MSGM — `H4.ema10.since` -0.78 · `H4.ema13.since` -0.77 · `px.close` +0.76 · `H4.ema15.since` -0.75 · `W.sma.stack.d10` +0.70
- **ELOX** (2023-07-10) ⟵ BON · PRPO · ORMP · NCPL · HSCS — `H4.sma100.slope.d5` +0.71 · `H4.adx14` +0.69 · `px.close` +0.69 · `W.sma80.slope.d5` -0.65 · `W.ema89.since` +0.65
- **GLMD** (2023-07-11) ⟵ INTZ · TPST · ALLR · CYCN · GSUN — `px.round_dist` +0.73 · `H4.sma8.since` +0.66 · `px.range_d.d5` +0.57 · `W.macd.hist_p.d5` -0.53 · `px.range_d` +0.53
- **GLMD** (2025-03-14) ⟵ LUCY · ANY · HTOO · MNY · FMST — `W.mfi14.d5` +0.67 · `sh.ratio5` +0.65 · `sh.ratio10` +0.61 · `D.di_diff.d5` +0.60 · `D.sma89.slope.d5` +0.59
- **HCWB** (2025-05-12) ⟵ CURR · ECOR · RSLS · CSAI · INDP — `px.base60_w.d10` -0.68 · `H4.st.green20.d5` +0.64 · `W.mfi14.d10` -0.62 · `H4.st.green20.d10` +0.56 · `sh.ratio_d` +0.53
- **HCWB** (2025-08-22) ⟵ JFBR · FRGT · LGHL · DRMA · AIFF — `H4.st.green10.d5` +0.76 · `px.round_dist.d5` +0.67 · `W.sma34.slope.d5` +0.61 · `D.sma50.slope.d5` +0.55 · `W.mfi14.d5` -0.53
- **IKT** (2024-01-11) ⟵ EDSA · DRIO · PSTV · KALA · ORMP — `px.ret60.d5` -0.73 · `H4.sma50.since` +0.67 · `H4.sma55.since` +0.65 · `W.st.green20.d10` +0.64 · `W.sma5.since` +0.62
- **IVDA** (2024-11-18) ⟵ GSUN · JAGX · MGOL · LOOP · BON — `px.lwick10.d5` -0.74 · `px.range_d` +0.66 · `px.lwick10.d10` -0.65 · `sh.vol_d` +0.65 · `H4.sma144.slope.d5` +0.65
- **IVDA** (2025-11-20) ⟵ GP · BOXL · CXAI · FTFT · BFRG — `D.sr.res_dist.d5` -0.69 · `D.sr.res_dist.d10` -0.63 · `D.ichi.thick_p.d10` -0.58 · `D.cdl.inside_bar.ago` -0.57 · `sh.ratio10.d10` -0.56
- **NEOV** (2024-03-27) ⟵ SGMT · LPTX · MEGL · BRTX · EVAX — `W.mdi14` +0.71 · `H4.sma8.since` +0.62 · `W.di_diff` -0.60 · `W.adx14.d10` +0.59 · `px.lwick10` +0.58
- **RNXT** (2023-12-12) ⟵ CPOP · FBYD · DPRO · MBIO · XRTX — `H4.psar.since` +0.69 · `px.lwick10.d10` -0.66 · `H4.st.inside10` +0.62 · `H4.ema30.since` +0.60 · `H4.sma34x89.gap.d10` -0.59
- **TCTM** (2024-09-26) ⟵ CHNR · AEHR · IMCC · AIMD · BCG — `vol.adl_slope10.d5` -0.69 · `vol.adl_slope10.d10` -0.65 · `H4.mdi14` +0.65 · `vol.adl_slope20.d5` -0.64 · `vol.cmf20.d5` -0.64
- **ABLV** (2024-12-13) ⟵ AQB · BETR · MYNZ · FTFT · EZGO — `H4.cdl.inside_bar.ago` +0.76 · `W.sma15.slope.d10` -0.58 · `H4.st.inside10` -0.53 · `px.lwick10.d5` -0.52 · `vol.usd_d` -0.51
- **AIHS** (2025-09-02) ⟵ HCAI · SXTP · FATN · AMIX · BMGL — `D.sma55.slope.d5` -0.81 · `px.base60_w.d10` +0.69 · `H4.pdi14.d5` -0.61 · `W.bb.squeeze_rank` +0.57 · `W.sma13.slope.d5` -0.56
- **BAOS** (2024-12-23) ⟵ ABVC · MSAI · TPST · LRHC · ABLV — `H4.bb.squeeze_rank.d10` -0.76 · `H4.bb.squeeze_rank` -0.64 · `H4.bb.width.d10` -0.62 · `H4.sma80.since` +0.62 · `vol.spike_d.d10` -0.61
- **BAOS** (2025-01-02) ⟵ ENSC · MYSZ · LRHC · FBLG · JTAI — `W.atr14_p.d10` +0.79 · `W.sma13x34.gap.d5` -0.76 · `W.sma20.slope.d5` -0.74 · `W.ema50.slope.d5` -0.73 · `W.ema55.slope.d5` -0.73
- **BIYA** (2025-11-05) ⟵ KIDZ · ENVB · BGL · BNZI · HCAI — `vol.adl_slope20.d10` +0.89 · `vol.cmf20.d10` +0.89 · `vol.adl_slope20.d5` +0.88 · `vol.cmf20.d5` +0.88 · `H4.sma55.since` -0.76
- **CTNT** (2024-05-13) ⟵ ARBB · HTOO · FTHM · MBRX · ANY — `H4.ichi.thick_p.d10` +0.65 · `H4.sma150.slope.d5` -0.65 · `H4.sma5.slope.d10` +0.64 · `D.sma80.slope.d5` -0.63 · `H4.sma10.since` -0.62
- **CTNT** (2024-12-02) ⟵ EVGN · ALZN · EKSO · GSIW · FRGT — `W.mdi14` -0.72 · `W.rsi14` +0.69 · `D.psar.since` -0.68 · `H4.sma200.slope.d5` -0.66 · `H4.sma200.slope.d10` -0.65
- **LASE** (2024-04-08) ⟵ INSG · CPOP · ENVB · GLTO · TCRT — `px.drop252.d10` -0.75 · `W.ema40.since` -0.72 · `D.st.green10.d10` +0.67 · `W.ema50.since` -0.64 · `W.sma50.slope.d10` +0.61
- **MBRX** (2025-02-12) ⟵ MNTS · HCTI · APLM · TCRX · INDP — `H4.sma150.slope.d10` -0.61 · `H4.mdi14.d5` -0.61 · `D.bot.adx.d10` +0.58 · `D.adx14.d10` +0.58 · `H4.ema5.since` +0.58
- **MBRX** (2025-06-25) ⟵ MSAI · ERNA · NAAS · LPTX · DRMA — `H4.sma8x15.gap` +0.85 · `H4.sma10.slope` +0.82 · `H4.sma8x15.gap.d10` +0.82 · `H4.sma8.slope` +0.78 · `H4.sma10.slope.d10` +0.77
- **MEGL** (2023-04-27) ⟵ GSUN · FAMI · IMTE · IVA · GTBP — `H4.sma200.since` -0.84 · `H4.ema144.since` -0.83 · `H4.ema150.since` -0.83 · `H4.ema200.dist` +0.83 · `H4.ema200.since` -0.79
- **NDRA** (2025-04-22) ⟵ GMM · FCEL · RSLS · BBLG · MNDR — `H4.bb.width.d10` +0.76 · `H4.ema100x200.gap.d10` +0.75 · `H4.sma55.since` -0.75 · `H4.ema50.since` -0.75 · `H4.ema80.since` -0.75
- **OMEX** (2024-11-27) ⟵ GSIW · JBDI · EVGN · FRGT · BNZI — `D.bot.adx` +0.84 · `D.adx14` +0.84 · `H4.ema15.since` +0.78 · `W.macd.line_p.d5` -0.67 · `H4.sma200.slope.d5` -0.66
- **PSTV** (2023-11-02) ⟵ SLDB · TREE · CALC · AEMD · GSUN — `D.ichi.thick_p.d5` +0.72 · `vol.dry5_20.d10` +0.68 · `D.sma40.slope.d5` -0.66 · `vol.spike_d.d10` +0.61 · `H4.sma144.since` -0.57
- **PSTV** (2025-05-30) ⟵ CURR · WIMI · MOVE · GENK · MYNZ — `H4.ema34.since` -0.83 · `H4.sma40.since` -0.82 · `H4.ema40.since` -0.80 · `H4.sma50.since` -0.77 · `H4.ema30.since` -0.75
- **RLYB** (2024-02-05) ⟵ COEP · MYSZ · CETX · PRFX · ACRV — `sh.ratio5.d5` +0.70 · `H4.st.green20` -0.55 · `sh.vol_d` +0.55 · `H4.adx14` +0.54 · `px.low60_age` -0.52
- **RLYB** (2024-03-27) ⟵ AQB · GAME · AIXI · VMAR · DRMA — `D.sma100.slope.d10` -0.60 · `W.sma.stack.d5` -0.59 · `D.ema5.since` -0.58 · `D.sma89.slope.d10` +0.57 · `D.sma5.since` -0.55
- **STSS** (2025-08-07) ⟵ BMEA · ARAI · SLE · ACON · SUNE — `D.sma100.slope.d10` -0.75 · `W.sma21.slope.d10` -0.68 · `W.macd.hist_p.d10` +0.63 · `W.macd.line_p.d10` -0.62 · `W.sma20.slope.d10` -0.62
- **CYN** (2024-11-06) ⟵ IFBD · MGOL · INBS · OMH · BCDA — `W.sma40.slope.d10` -0.63 · `D.bot.mfi.d5` -0.59 · `D.mfi14.d5` -0.59 · `vol.spike_d.d5` -0.58 · `H4.bb.squeeze_rank.d10` -0.57
- **ERNA** (2023-11-30) ⟵ GAME · DPRO · XLO · MNTS · BJDX — `sh.ratio10.d10` -0.67 · `H4.sma50.slope.d5` +0.64 · `H4.psar.since` -0.63 · `W.sma40x80.gap.d10` +0.61 · `H4.ichi.thick_p` +0.58
- **FMST** (2025-04-30) ⟵ EKSO · ENLV · ACXP · LBGJ · OMH — `sh.ratio_d.d10` +0.73 · `H4.sma5.since` +0.66 · `H4.sma40x80.gap.d5` -0.60 · `W.st.green20` -0.59 · `vol.adl_slope10.d5` +0.52
- **GSIW** (2025-02-06) ⟵ AERT · EKSO · CTXR · TCRT · GUTS — `D.sma89.slope.d5` +0.78 · `D.sma89.slope.d10` +0.74 · `W.sma20.slope.d5` +0.74 · `px.round_dist.d10` -0.74 · `sh.ratio5.d5` -0.65
- **HOWL** (2024-10-18) ⟵ MASS · LAES · CABA · GFAI · CXAI — `W.st.green20.d10` -0.74 · `W.st.green20.d5` -0.64 · `H4.sma10.since` +0.53 · `W.sma34x89.gap.d5` -0.53 · `H4.sma55.since` +0.50
- **WLDS** (2023-05-24) ⟵ BNRG · EBON · GSUN · CYN · BANL — `H4.ichi.thick_p` -0.74 · `D.bot.mfi.d10` +0.60 · `H4.sma100.slope.d10` +0.60 · `W.sma.stack.d5` -0.58 · `vol.obv_slope10.d10` +0.57
- **ALGS** (2024-10-23) ⟵ APM · ABLV · AGEN · INTS · LTRN — `D.st.inside10` +0.62 · `H4.sma34.since` +0.57 · `H4.sma200.slope.d5` -0.54 · `H4.kdj.j.d10` -0.54 · `D.sma30.slope.d5` -0.54
- **BOF** (2024-04-23) ⟵ ROMA · CVKD · MBRX · INBS · FEMY — `sh.ratio_d.d10` -0.71 · `sh.ratio10.d10` -0.65 · `H4.st.green10.d10` -0.60 · `sh.ratio5.d10` -0.58 · `sh.ratio10.d5` -0.58
- **BOF** (2024-08-27) ⟵ MKTW · DTSS · GTBP · BOXL · CHNR — `H4.st.green20.d10` +0.63 · `D.psar.since` +0.62 · `vol.adl_slope20.d10` -0.60 · `vol.cmf20.d10` -0.60 · `H4.st.green20` +0.58
- **CALC** (2023-10-24) ⟵ TREE · SEED · DRMA · PRFX · DBGI — `H4.sma200.dist.d10` +0.73 · `px.atl_age` +0.70 · `px.atl_dist` +0.66 · `H4.sma200.slope.d10` +0.66 · `H4.sma50x200.gap.d10` +0.65
- **CALC** (2025-07-10) ⟵ PROP · MSAI · DTSS · KOSS · GMM — `vol.adl_slope10` -0.68 · `D.st.green20` -0.66 · `D.st.inside10` +0.59 · `W.stoch.k.d10` -0.58 · `W.mfi14.d10` -0.58
- **CMCT** (2025-11-05) ⟵ AMIX · LNZA · INAB · HTOO · ORKT — `W.adx14` +0.80 · `px.round_dist.d10` -0.71 · `W.sma34.since` -0.70 · `W.sma55.slope.d5` +0.67 · `sh.ratio5.d10` -0.66
- **CMCT** (2025-11-25) ⟵ AIFU · FEAM · MYNZ · IVF · HCWB — `D.macd.sig_p.d5` +0.87 · `D.macd.sig_p.d10` +0.86 · `D.sma8x15.gap` +0.82 · `D.sma8x21.gap` +0.82 · `D.sma10x20.gap` +0.79
- **COEP** (2024-02-14) ⟵ GTBP · JFBR · CETX · ENSC · ALLR — `D.cdl.inside_bar.ago` +0.72 · `px.range_d.d10` +0.69 · `px.ret1.d5` -0.67 · `px.round_dist.d10` +0.64 · `D.st.inside10` -0.62
- **EJH** (2023-09-27) ⟵ CYCN · ACET · APVO · MNPR · BNGO — `W.macd.hist_p.d10` -0.76 · `H4.di_diff` +0.70 · `W.macd.sig_p.d10` +0.69 · `W.ichi.thick_p.d10` -0.67 · `W.macd.line_p.d10` +0.65
- **EJH** (2024-01-09) ⟵ CMND · PRSO · VMAR · HKIT · AEHL — `H4.macd.hist_p.d10` +0.92 · `H4.macd.hist_p` +0.91 · `W.sma13.slope.d10` -0.86 · `W.sma13x34.gap` +0.85 · `W.sma20.slope` +0.85
- **EJH** (2024-04-03) ⟵ REBN · VMAR · NEOV · GAME · HKIT — `D.bot.macd_hist_p.d10` -0.82 · `D.macd.hist_p.d10` -0.82 · `W.sma20.slope.d5` -0.75 · `W.sma21.slope.d5` -0.73 · `W.ema20.since` +0.71
- **EJH** (2024-06-10) ⟵ CNEY · AUUD · PRFX · HUBC · IFBD — `D.sr.res_dist.d5` -0.69 · `D.sma30.slope.d10` -0.68 · `D.sma34.slope.d5` -0.68 · `px.lwick10` +0.65 · `vol.adl_slope20` +0.64
- **HKPD** (2025-08-25) ⟵ MIGI · FATN · CRIS · LFWD · MRKR — `H4.ema100.since` -0.66 · `D.sma13.since` +0.65 · `W.st.green10.d5` -0.63 · `D.ema10.since` +0.62 · `D.sma150.since` -0.61
- **MBIO** (2025-06-30) ⟵ BDRX · DRMA · GOVX · XHLD · MIGI — `D.ichi.thick_p.d10` -0.76 · `D.ichi.thick_p.d5` -0.63 · `px.round_dist.d10` -0.61 · `sh.ratio_d` -0.59 · `px.lwick10` -0.58
- **REBN** (2025-01-27) ⟵ STTK · CRIS · IMNN · ENLV · MDIA — `W.sma34.slope.d5` -0.81 · `W.sma40x80.gap.d10` +0.79 · `W.sma40x80.gap.d5` +0.78 · `sh.ratio10` -0.70 · `W.sma34.slope.d10` -0.69
- **RNAZ** (2025-01-22) ⟵ COCH · CRVO · INO · PDSB · SPRB — `W.macd.hist_p.d5` -0.77 · `W.macd.hist_p` +0.76 · `D.ichi.thick_p.d5` +0.72 · `W.sma21x55.gap.d10` +0.72 · `D.ichi.thick_p.d10` +0.70
- **SGMT** (2024-01-10) ⟵ EDSA · AIXI · ACRV · NEON · APM — `W.mfi14.d5` +0.58 · `D.cdl.inside_bar.ago` +0.54 · `H4.sma200.slope` -0.54 · `D.sma80.slope` -0.52 · `H4.sma144.slope.d10` +0.52
- **ANTE** (2025-03-11) ⟵ IFBD · CING · JDZG · CCTG · AIXI — `D.sma150.slope` -0.80 · `D.sma150.slope.d5` -0.72 · `D.sma150.slope.d10` -0.71 · `W.stoch.d.d10` +0.62 · `W.ichi.thick_p` -0.60
- **ATGL** (2024-04-19) ⟵ JL · AZ · FTHM · BOXL · IMRX — `D.sma34.slope.d10` +0.80 · `D.sma40.slope.d5` +0.78 · `px.base40_w.d5` -0.78 · `D.sma34.slope.d5` +0.73 · `px.base40_w.d10` -0.73
- **ATGL** (2025-11-14) ⟵ CISO · ATON · ATOM · AKTX · BTCT — `W.ema80.since` -0.79 · `W.ema89.since` -0.79 · `sh.vol_d` -0.67 · `vol.usd_med20` -0.65 · `H4.st.green20.d10` +0.61
- **ATPC** (2024-12-19) ⟵ BETR · TPST · JAGX · MSGM · FBLG — `D.sma89.slope.d10` -0.64 · `W.sma89.since` -0.59 · `D.ema55.since` +0.57 · `vol.usd_med20` -0.57 · `D.adx14.d10` -0.55
- **ATPC** (2025-02-21) ⟵ APLM · HSDT · MNTS · APVO · NCI — `H4.atr14_p` -0.67 · `D.ema5.since` +0.65 · `W.rsi21` +0.65 · `W.sma89.since` -0.64 · `W.ema89.since` -0.62
- **BLBX** (2023-02-24) ⟵ AEMD · CYN · AMTX · NERV · EQ — `H4.sma100.slope.d5` +0.67 · `H4.sma5.dist.d10` -0.65 · `H4.sma21.slope` +0.64 · `D.ema100x200.gap.d5` -0.63 · `H4.ema5.dist.d10` -0.63
- **CADL** (2024-11-21) ⟵ EKSO · BMR · NDLS · GP · CRIS — `H4.sma20.since` -0.63 · `D.psar.since` -0.56 · `px.atl_dist` +0.56 · `W.sma34x89.gap.d10` +0.56 · `W.sma.stack` +0.55
- **CURR** (2024-12-17) ⟵ PRLD · ICU · GLTO · CRBP · RSLS — `W.mfi14.d5` +0.74 · `px.base60_w.d10` +0.71 · `vol.usd_med20` -0.67 · `px.round_dist.d10` +0.63 · `H4.ichi.thick_p.d10` +0.62
- **HCTI** (2023-07-05) ⟵ NCPL · GLMD · MIGI · ORMP · ALT — `sh.ratio_d.d10` +0.60 · `px.drop252.d10` -0.57 · `sh.ratio_d.d5` +0.55 · `H4.st.inside10` -0.54 · `H4.adx14` -0.54
- **HCTI** (2024-12-30) ⟵ LRE · ARBB · BFRG · GNPX · GREE — `H4.sma50.slope.d10` +0.72 · `H4.sma40x80.gap.d5` +0.71 · `H4.adx14.d10` -0.66 · `vol.adl_slope10.d10` +0.65 · `vol.updown20.d10` +0.65
- **JTAI** (2024-12-23) ⟵ BENF · GMM · GLTO · WHLR · DFLI — `H4.sma8.since` +0.82 · `H4.ema8.since` +0.81 · `H4.ema5.since` +0.73 · `px.base40_w.d10` -0.71 · `D.sma144.slope.d10` -0.69
- **KITT** (2024-12-24) ⟵ JAGX · TPST · FBLG · ABVC · DFLI — `px.base_len` -0.74 · `px.lwick10.d10` -0.68 · `D.ema40.since` -0.62 · `vol.updown20.d10` -0.61 · `vol.updown20.d5` -0.59
- **KITT** (2025-12-02) ⟵ HCAI · MTEN · GNPX · IVF · ALTS — `px.base60_w.d10` -0.76 · `px.base60_w.d5` -0.75 · `D.sma55.slope.d10` +0.75 · `D.sma55.slope.d5` +0.73 · `px.lwick10.d10` -0.65
- **MRM** (2025-04-02) ⟵ FCEL · HYFM · GNLN · LOBO · MKZR — `H4.sma200.slope.d10` +0.77 · `D.mfi14` +0.72 · `D.bot.mfi` +0.72 · `H4.ema10.since` +0.69 · `W.sma13.slope.d10` +0.66
- **BMEA** (2023-11-28) ⟵ GFAI · ADIL · BON · BNGO · MRKR — `H4.bb.squeeze_rank` +0.74 · `H4.sma150.since` -0.72 · `H4.ema144.since` -0.68 · `D.sma13.slope.d5` +0.68 · `H4.ema150.since` -0.67
- **CELU** (2025-03-04) ⟵ IVDA · INTZ · GFAI · LIDR · FCEL — `vol.usd_med20.d10` +0.82 · `H4.sma21.since` -0.79 · `vol.usd_med20.d5` +0.79 · `H4.ema20.since` -0.77 · `H4.ema21.since` -0.76
- **ENSC** (2025-04-22) ⟵ ALGS · HBIO · TELO · CNTY · RMTI — `W.ema40x80.gap` -0.74 · `W.ema34x89.gap` -0.73 · `W.ema21x55.gap` -0.73 · `vol.dry5_20.d10` +0.73 · `W.ema55.since` +0.71
- **IFBD** (2023-07-19) ⟵ GLMD · JZXN · INBS · GSUN · GDC — `H4.ichi.thick_p.d5` -0.78 · `vol.spike_d.d10` -0.67 · `vol.usd_d.d10` -0.66 · `H4.st.green20.d10` +0.66 · `H4.sma8.since` -0.65
- **IFBD** (2024-01-22) ⟵ VMAR · JTAI · ESGL · ADIL · HUBC — `H4.sma34.slope.d5` +0.76 · `px.round_dist.d10` -0.71 · `W.ichi.thick_p` +0.67 · `H4.sma30.slope.d5` +0.67 · `W.st.inside10` -0.64
- **INLF** (2025-06-13) ⟵ CAMP · BNZI · AEMD · CNSP · LFWD — `sh.ratio5.d10` -0.81 · `sh.ratio10.d5` -0.81 · `sh.ratio5` -0.68 · `sh.ratio5.d5` -0.63 · `sh.ratio_d` -0.62
- **LRHC** (2024-06-13) ⟵ XPON · ATER · TCRT · CPOP · PRFX — `H4.st.green20.d5` +0.64 · `D.ichi.thick_p.d10` -0.62 · `H4.st.green10.d10` +0.60 · `D.ichi.thick_p.d5` -0.60 · `W.sma8x15.gap.d5` -0.60
- **LUCY** (2023-04-10) ⟵ IMUX · GWAV · ISPC · HYFM · GLMD — `D.sr.sup_touches` +0.65 · `D.sma144.since` -0.64 · `W.sma30.since` -0.63 · `H4.sma8.since` +0.60 · `W.sma34.since` -0.60
- **LUCY** (2024-08-28) ⟵ BMR · CDIO · LRE · MNY · CYCC — `W.sma.stack.d5` +0.65 · `D.sr.res_dist.d5` -0.59 · `H4.cdl.doji.ago` -0.59 · `W.ichi.thick_p.d10` +0.57 · `D.sma34.slope.d10` -0.55
- **MIRA** (2024-07-12) ⟵ ENSC · XRTX · LITM · IDAI · HOTH — `W.sma50.since` -0.72 · `H4.ema55.since` -0.71 · `H4.sma55.since` -0.69 · `W.ema50.since` -0.67 · `D.st.green20.d10` +0.64
- **TCRT** (2025-03-31) ⟵ AIXI · MNY · EHGO · MDIA · HTLM — `sh.ratio5.d5` +0.76 · `H4.mfi14.d10` -0.65 · `px.lwick10.d10` +0.64 · `px.atl_age` -0.61 · `px.low60_age` -0.59
- **ABTS** (2025-09-15) ⟵ MEGL · LEXX · FCUV · MDCX · AMOD — `H4.sma100.slope.d10` -0.74 · `H4.sma100.slope.d5` -0.70 · `vol.dry5_20.d5` +0.70 · `D.st.green20.d10` -0.67 · `vol.adl_slope10.d10` -0.66
- **BIVI** (2024-10-17) ⟵ APM · ABLV · AMIX · WLDS · GOVX — `D.sma20.slope.d5` -0.68 · `D.ema8.since` +0.67 · `D.adx14.d10` +0.66 · `D.bot.adx.d10` +0.66 · `D.st.green10.d5` -0.65
- **CGTL** (2025-06-11) ⟵ HUBC · MYNZ · LFWD · TELO · LITM — `D.sma40.slope.d10` -0.82 · `H4.sma144.slope.d10` -0.81 · `H4.sma150.slope.d10` -0.76 · `H4.sma144.slope.d5` -0.76 · `D.ichi.thick_p` -0.75
- **CGTL** (2025-11-11) ⟵ CHSN · FRSX · KBSX · MDCX · JDZG — `D.sma.stack.d10` +0.73 · `W.kdj.j.d10` +0.73 · `D.sma100.slope.d5` -0.70 · `H4.kdj.j.d5` -0.66 · `D.ema.stack.d10` +0.65
- **DBGI** (2023-08-11) ⟵ RNAZ · IFBD · DRMA · BIVI · NEON — `H4.adx14` -0.77 · `H4.ema10.since` -0.66 · `H4.sma15.since` -0.64 · `px.uwick5.d5` +0.63 · `H4.adx14.d10` -0.59
- **DBGI** (2025-09-23) ⟵ NIPG · GOVX · IMNN · MAAS · LRHC — `px.base60_w.d10` +0.78 · `H4.bb.width` +0.76 · `W.sma34.slope` +0.75 · `W.sma30.slope.d5` -0.74 · `D.atr14_p` +0.71
- **KRRO** (2025-08-12) ⟵ BTOC · HBIO · TRAW · CTNT · KBSX — `D.sma100.slope.d5` -0.67 · `vol.usd_med20` +0.62 · `H4.adx14` -0.59 · `H4.sma200.slope.d5` -0.54 · `px.close` +0.54
- **MSAI** (2024-12-19) ⟵ ABVC · SLE · AVTX · LRHC · IXHL — `D.mdi14.d5` +0.66 · `D.ema15.since` +0.65 · `H4.ema80.since` +0.65 · `D.ema100.since` +0.65 · `W.psar.since` +0.65
- **RDHL** (2024-07-31) ⟵ OMH · ENGN · AQB · PRSO · IMMX — `W.sma10.since` +0.73 · `px.close` -0.63 · `H4.bb.squeeze_rank` +0.62 · `D.sma200.slope` +0.59 · `W.sma13.since` +0.59
- **ZEO** (2024-09-18) ⟵ LRHC · NCPL · SLE · AIMD · DBGI — `H4.ema5.dist` +0.86 · `H4.sma5.dist` +0.85 · `H4.ema8.dist` +0.83 · `H4.sma8.dist` +0.78 · `D.sma55.slope.d5` +0.77
- **ARBB** (2025-02-27) ⟵ GTBP · JDZG · XRTX · CLRO · EVGN — `W.mfi14.d5` -0.76 · `W.mfi14.d10` -0.71 · `W.ema.nabove.d5` -0.64 · `D.ema.nabove.d5` -0.58 · `H4.sma8.slope.d10` +0.53
- **BBLG** (2024-09-13) ⟵ SLE · DBGI · BCG · BENF · CVRX — `H4.sma21.slope.d5` +0.77 · `H4.sma80.slope.d5` +0.77 · `H4.sma20.slope.d5` +0.74 · `D.vwap_m.dist.d10` +0.74 · `H4.vwap_m.dist.d10` +0.73
- **CDLX** (2023-04-03) ⟵ FRGT · SLDB · HTOO · GP · IMUX — `sh.ratio_d.d5` -0.71 · `sh.vol_d.d5` -0.69 · `H4.sma50.since` +0.66 · `D.ema20.since` +0.62 · `D.ema21.since` +0.61
- **CDLX** (2023-07-10) ⟵ ILAG · KINS · CNSP · HUDI · INBS — `vol.usd_d.d10` -0.72 · `W.willr14.d5` -0.69 · `px.ret60.d10` -0.68 · `W.mfi14.d5` -0.67 · `D.stoch.d.d5` -0.65
- **CDT** (2025-04-09) ⟵ ORKT · FCEL · IDAI · CTXR · JUNS — `D.sma55.slope.d5` -0.78 · `H4.cdl.doji.ago` -0.74 · `W.sma80.slope.d10` -0.64 · `H4.sma200.slope.d10` +0.63 · `H4.sma200.slope.d5` +0.60
- **EDBL** (2025-05-19) ⟵ JTAI · HUBC · LSH · GLXG · CETY — `D.don20.low_age` -0.70 · `D.sma34.slope.d5` -0.70 · `H4.sma200.slope.d10` -0.64 · `sh.ratio5.d10` -0.63 · `sh.ratio10.d5` -0.63
- **FTEL** (2024-01-16) ⟵ ADIL · HUBC · VMAR · PRSO · SPRC — `px.ret60.d10` +0.76 · `D.sma100.slope.d5` -0.72 · `px.round_dist.d10` -0.72 · `px.ret1` +0.65 · `W.rsi21` +0.64
- **FTEL** (2025-09-09) ⟵ LUCY · LFWD · DRMA · ONCO · MNTS — `W.sma34.slope.d5` +0.76 · `W.sma34.slope.d10` +0.68 · `D.sr.res_dist.d5` -0.67 · `D.sma200.slope.d5` -0.66 · `px.round_dist` +0.64
- **GELS** (2025-04-21) ⟵ JUNS · CCLD · SERA · EKSO · MBRX — `W.sma5.since` +0.82 · `H4.ema144.since` -0.78 · `H4.ema150.since` -0.77 · `D.sma15.since` +0.73 · `D.ema15.since` +0.70
- **GELS** (2025-09-04) ⟵ GLXG · JFBR · ORKT · CISS · BGL — `H4.mdi14.d5` -0.92 · `H4.di_diff.d5` +0.80 · `H4.di_diff` +0.76 · `H4.mdi14` -0.73 · `W.macd.hist_p.d5` -0.65
- **HOVR** (2024-07-10) ⟵ HCTI · BNRG · IPDN · BMRA · IDAI — `H4.ichi.thick_p.d10` +0.73 · `px.lwick10.d5` +0.68 · `W.sma21.slope.d10` +0.68 · `D.sma80.slope.d10` -0.66 · `D.sma80.slope.d5` -0.64
- **MYSZ** (2024-12-18) ⟵ DFLI · XOS · CBUS · BETR · TPST — `D.st.inside10` +0.80 · `px.uwick5.d5` -0.74 · `H4.st.green10.d10` -0.67 · `D.vwap_w.dist.d5` +0.65 · `H4.ema5.since` -0.65
- **SUGP** (2024-12-24) ⟵ BMEA · LRE · MASS · ISPC · ARBB — `H4.sma5.dist` -0.68 · `D.sma34x89.gap.d10` +0.66 · `px.base20_w.d5` -0.64 · `px.ret1` -0.62 · `H4.ema5.dist` -0.62
- **SUGP** (2025-07-08) ⟵ MWYN · NCEW · CLGN · ALBT · AEMD — `px.ret1.d10` -0.69 · `W.sma.stack.d5` +0.69 · `px.uwick5.d5` +0.69 · `H4.bb.width.d5` +0.64 · `H4.ichi.thick_p.d5` +0.62
- **ADIL** (2024-02-13) ⟵ RLYB · PRFX · AIRE · RKDA · ESGL — `H4.sma50.since` +0.77 · `H4.ema50.since` +0.76 · `W.psar.since` +0.65 · `H4.vwap_m.dist` -0.65 · `H4.ema55.since` +0.63
- **APM** (2023-04-13) ⟵ IMTE · ENVB · IVA · GLMD · RSLS — `D.st.inside10` -0.78 · `D.adx14.d5` -0.72 · `D.bot.adx.d5` -0.72 · `H4.ema5.slope.d10` -0.65 · `px.round_dist` -0.65
- **CELZ** (2023-03-20) ⟵ AEMD · CYCC · RMTI · IMUX · ISPC — `vol.adl_slope20.d10` +0.64 · `vol.cmf20.d10` +0.64 · `px.base20_w.d10` -0.63 · `px.round_dist.d10` -0.61 · `D.sma200.slope.d10` +0.60
- **DRIO** (2025-09-19) ⟵ JSPR · IMNN · FBLG · LIMN · MNDR — `W.ema80.since` +0.74 · `W.ema55.since` +0.73 · `W.sma80.since` +0.72 · `W.ema50.since` +0.69 · `W.ema89.since` +0.64
- **EYPT** (2023-03-24) ⟵ FTFT · ALXO · ENVB · DAVE · CYCC — `H4.st.green20` +0.70 · `D.psar.since` -0.68 · `sh.ratio_d.d10` -0.68 · `H4.st.green20.d10` +0.63 · `D.sma10.since` -0.62
- **LCFY** (2025-06-26) ⟵ CDIO · LOBO · MSAI · EHGO · ERNA — `H4.st.inside10` -0.74 · `H4.cdl.inside_bar.ago` +0.67 · `px.atl_age` +0.64 · `vol.dry5_20.d5` -0.62 · `H4.sma8x15.gap.d5` +0.60
- **MNTS** (2024-08-16) ⟵ PRSO · UCAR · BCDA · APYX · GLTO — `D.sma50.slope.d5` -0.76 · `D.mfi14.d5` -0.67 · `D.bot.mfi.d5` -0.67 · `H4.adx14.d10` -0.62 · `W.mfi14` +0.61
- **MNTS** (2024-10-08) ⟵ AUUD · TENX · CING · GNLN · IMMX — `W.sma55.slope.d10` +0.73 · `H4.sma89.slope.d10` -0.67 · `W.sma55.slope.d5` +0.65 · `D.sma200.slope.d5` +0.63 · `W.sma50.slope.d5` -0.63
- **SXTC** (2025-04-16) ⟵ GMM · AXTI · CNTY · CALC · MFI — `px.range_d.d5` +0.78 · `W.adx14.d5` -0.75 · `px.uwick5.d5` +0.68 · `W.ema50.since` +0.67 · `W.sma50.since` +0.66
- **XRTX** (2024-02-16) ⟵ EPOW · MBIO · ANGH · MBOT · ABVC — `W.sma21x55.gap.d5` -0.62 · `D.ichi.thick_p.d5` -0.59 · `W.sma20x50.gap.d10` -0.58 · `W.sma21.slope.d5` -0.58 · `W.sma21.slope.d10` -0.57
- **XRTX** (2024-08-28) ⟵ CYCC · SXTC · CDIO · DBGI · CLRO — `vol.dry5_20.d5` +0.67 · `H4.di_diff` +0.59 · `H4.mdi14` -0.57 · `H4.mfi14.d10` +0.56 · `H4.cdl.doji.ago` -0.52
- **AGEN** (2025-04-04) ⟵ FCEL · BTOC · HTLM · MKTW · CISS — `D.ichi.thick_p` -0.66 · `px.round_dist` +0.58 · `H4.sma40.since` +0.54 · `H4.ema40.since` +0.53 · `D.ichi.thick_p.d5` -0.52
- **AIMD** (2024-02-28) ⟵ GOVX · PCSA · RR · GDHG · GTBP — `W.sma80.slope.d5` +0.71 · `W.mfi14` +0.71 · `W.sma80.slope.d10` +0.70 · `sh.ratio5` -0.68 · `D.sma13.slope.d5` -0.62
- **AMIX** (2024-10-25) ⟵ REBN · HOLO · AEHL · BCDA · CXAI — `px.base40_w.d5` +0.70 · `px.base40_w.d10` +0.67 · `px.base60_w.d10` -0.66 · `D.sma34.slope.d10` -0.65 · `px.base60_w.d5` -0.64
- **AUUD** (2023-06-09) ⟵ CMND · BNRG · DOGZ · IMUX · BANL — `H4.bb.width` +0.70 · `vol.dry5_20` +0.68 · `H4.adx14.d10` +0.67 · `H4.bb.width.d10` +0.66 · `H4.bb.squeeze_rank.d10` +0.66
- **AUUD** (2024-04-05) ⟵ LAES · GDC · AEHR · GSUN · IFBD — `D.adx14.d5` -0.70 · `D.bot.adx.d5` -0.70 · `D.adx14.d10` -0.69 · `D.bot.adx.d10` -0.69 · `D.sr.res_dist.d10` -0.61
- **AVTX** (2024-03-27) ⟵ MEGL · FBIO · DRMA · OMH · AEMD — `H4.bb.width` +0.74 · `D.don20.pos.d10` -0.71 · `H4.bb.squeeze_rank` +0.67 · `D.cci20.d10` -0.66 · `vol.usd_d` +0.65
- **BENF** (2024-09-05) ⟵ AKAN · ICU · CYN · AUUD · APVO — `vol.updown20.d10` +0.75 · `vol.obv_slope20.d10` +0.71 · `W.sma8x15.gap.d10` -0.65 · `D.sma200.slope.d10` -0.62 · `vol.dry5_20.d5` -0.62
- **BENF** (2025-09-29) ⟵ DBGI · KXIN · NIPG · JDZG · GITS — `H4.sma34.slope.d5` +0.71 · `D.ema100x200.gap.d10` -0.66 · `H4.sma89.dist.d5` +0.64 · `H4.sma50.dist.d10` +0.64 · `H4.sma80.dist.d10` +0.64
- **BKYI** (2024-12-26) ⟵ MSGM · AIXI · ABVC · MIRA · GSUN — `px.base_len` -0.61 · `W.ema21.since` +0.56 · `W.ema20.since` +0.55 · `H4.ema.stack.d10` -0.55 · `px.range_d` -0.54
- **BON** (2023-01-27) ⟵ FTHM · AZ · KINS · MDIA · JCSE — `D.sma21.slope.d5` -0.72 · `D.sma20.slope.d5` -0.66 · `sh.ratio_d.d10` -0.66 · `D.sma80.slope.d10` -0.65 · `D.sma80.slope.d5` -0.64
- **BON** (2025-03-13) ⟵ MNY · HTOO · ANY · HSDT · MRKR — `W.pdi14.d5` +0.71 · `W.di_diff.d5` +0.69 · `H4.mfi14.d5` +0.67 · `sh.ratio5.d5` +0.67 · `D.mdi14` -0.67
- **BON** (2025-09-08) ⟵ CLRB · CRIS · AMIX · BMGL · FATN — `W.sma.stack.d5` +0.76 · `D.sma5.since` +0.75 · `D.ema5.since` +0.72 · `vol.obv_slope10.d5` +0.66 · `W.sma34.slope.d10` -0.65
- **GNLN** (2024-10-25) ⟵ REBN · AEHL · HOLO · CXAI · ASST — `D.sma40.slope.d10` +0.78 · `D.ema100x200.gap.d10` +0.72 · `px.base40_w.d5` +0.71 · `D.sma50.slope.d10` -0.68 · `px.base40_w.d10` +0.67
- **ISPC** (2025-09-04) ⟵ MRKR · HUBC · CAPR · BDRX · GTBP — `H4.ema21.since` -0.88 · `H4.sma30.since` -0.86 · `H4.sma50.since` -0.83 · `H4.ema30.since` -0.83 · `H4.sma34.since` -0.83
- **MDIA** (2024-06-07) ⟵ GSIT · BMR · AISP · MSAI · CPOP — `D.psar.since` -0.79 · `D.sma50x200.gap.d10` +0.77 · `D.sma50x200.gap.d5` +0.75 · `W.sma21.slope.d5` -0.67 · `D.fib.retr` +0.67
- **MGOL** (2024-01-05) ⟵ MNPR · JCSE · ISPC · MBIO · FAMI — `W.sma8.since` +0.73 · `W.sma10.since` +0.71 · `sh.ratio5.d5` -0.70 · `vol.adl_slope10.d5` -0.69 · `W.ema5.since` +0.65
- **MLGO** (2023-09-11) ⟵ CBIO · BIAF · WLDS · PSTV · IMUX — `W.sma34.slope.d5` +0.79 · `W.sma40.dist.d10` +0.74 · `W.sma40.slope` -0.74 · `W.sma34.slope.d10` +0.72 · `W.pdi14` +0.69
- **MLGO** (2025-02-20) ⟵ FEBO · LNKS · HAO · MKDW · GSIW — `H4.bb.squeeze_rank` +0.85 · `H4.bb.width.d10` +0.80 · `H4.ema150.dist` +0.79 · `H4.ema144.dist` +0.78 · `H4.ema200.dist` +0.76
- **MSS** (2024-01-25) ⟵ VMAR · PRSO · BOXL · JTAI · AEHL — `D.macd.sig_p.d10` +0.72 · `D.sma21.slope.d5` +0.71 · `D.macd.sig_p.d5` +0.69 · `D.sma20.slope.d10` +0.69 · `H4.sma50x100.gap.d10` +0.68
- **MSS** (2024-12-16) ⟵ IXHL · JZXN · LRHC · SLE · ABVC — `vol.spike_d.d5` +0.77 · `H4.bb.squeeze_rank` +0.73 · `H4.sma10.dist.d10` +0.67 · `H4.bb.squeeze_rank.d5` +0.66 · `H4.sma8.dist.d10` +0.65
- **NA** (2025-06-03) ⟵ RMTI · LFWD · ECOR · SNAL · PROP — `vol.dry5_20.d10` +0.71 · `vol.spike_d.d10` +0.61 · `W.kdj.k.d10` -0.56 · `px.lwick10` +0.54 · `W.sma30.slope.d5` +0.54
- **RLMD** (2025-08-27) ⟵ CRBP · CTXR · ARTV · CLRB · SERA — `px.ret60.d10` -0.72 · `W.sma13x34.gap.d5` -0.68 · `W.sma34.slope` +0.66 · `W.sma13x34.gap.d10` -0.62 · `px.round_dist` +0.60
- **RLMD** (2025-09-04) ⟵ RMTI · NCI · AIHS · SERA · CRIS — `W.sma34x89.gap.d10` +0.61 · `H4.cdl.doji.ago` -0.61 · `px.expl_age` -0.61 · `W.sma34x89.gap.d5` +0.60 · `vol.adl_slope20` +0.59
- **ABVC** (2023-07-31) ⟵ DRMA · ACON · CADL · GSUN · JZXN — `H4.mfi14` +0.82 · `vol.obv_slope10.d10` +0.79 · `H4.mdi14.d10` -0.77 · `vol.obv_slope10` +0.74 · `vol.adl_slope10.d5` -0.74
- **ABVC** (2023-12-13) ⟵ LIXT · MNTS · FAMI · GFAI · AEI — `D.sr.res_dist.d5` -0.73 · `H4.adx14.d10` -0.65 · `D.sma80.since` -0.61 · `H4.kst.diff.d10` +0.61 · `W.sma20.slope.d5` +0.59
- **AFJK** (2025-12-05) ⟵ LSH · BGLC · LHSW · ALTS · GTBP — `W.st.green10` +0.73 · `px.base20_w.d5` -0.69 · `H4.sma50.slope.d5` +0.64 · `px.atl_dist.d10` +0.63 · `px.base20_w.d10` -0.63
- **AFJK** (2025-12-17) ⟵ KROS · SUGP · BMRA · BLNE · ERNA — `H4.sma8.dist.d5` +0.66 · `D.sr.res_dist` +0.66 · `W.adx14` +0.65 · `D.st.green20.d5` +0.65 · `vol.usd_d.d10` +0.63
- **BCG** (2025-11-13) ⟵ XPON · NCPL · GLXG · AKAN · GELS — `vol.obv_slope10.d5` -0.75 · `vol.obv_slope20.d5` -0.73 · `vol.updown20.d5` -0.64 · `vol.obv_slope20` -0.62 · `vol.updown20` -0.60
- **BEAT** (2023-12-20) ⟵ BAOS · LRHC · DPRO · CTNT · MBIO — `H4.pdi14.d5` +0.70 · `H4.di_diff.d5` +0.69 · `H4.mdi14.d5` -0.63 · `D.don20.pos.d5` +0.60 · `px.drop252.d5` -0.60
- **EVGN** (2025-06-09) ⟵ TRIB · ICU · DRMA · LGVN · CISS — `W.sma55.slope.d10` -0.66 · `sh.ratio10.d10` -0.62 · `sh.ratio_d` -0.54 · `W.bb.squeeze_rank.d5` -0.49 · `D.gap.below_n` +0.48
- **FLYE** (2024-12-20) ⟵ DFLI · FLUX · CELZ · GLTO · SLE — `W.sma8x21.gap.d10` +0.69 · `W.sma21.slope.d5` +0.67 · `W.sma20.slope.d10` +0.66 · `D.sma100.slope.d5` +0.63 · `H4.st.green20.d10` -0.61
- **GOVX** (2024-08-09) ⟵ GREE · LRHC · CHNR · UCAR · ATLX — `D.adx14.d5` -0.65 · `D.bot.adx.d5` -0.65 · `H4.ichi.thick_p.d5` +0.65 · `D.adx14.d10` -0.60 · `D.bot.adx.d10` -0.60
- **ICCM** (2023-11-27) ⟵ RKDA · ADIL · FBYD · BJDX · OMH — `px.atl_dist` +0.71 · `H4.cdl.inside_bar.ago` +0.68 · `H4.ema80.since` -0.67 · `H4.sma144.since` -0.65 · `H4.sma150.since` -0.65
- **IMCC** (2023-05-12) ⟵ FAMI · KITT · GOVX · RPID · KSCP — `px.lwick10` +0.61 · `H4.sma150.slope.d5` -0.60 · `H4.sma200.slope.d10` -0.57 · `D.sma.nabove.d10` -0.56 · `sh.ratio5.d5` -0.56
- **IMCC** (2025-11-17) ⟵ BGL · HUBC · BTCT · HYFM · CXAI — `W.sma20.slope.d5` +0.68 · `H4.sma50.slope.d5` +0.67 · `sh.ratio5.d5` -0.63 · `D.sma13.slope.d5` +0.62 · `H4.sma55.slope.d5` +0.61
- **MNY** (2024-02-07) ⟵ JTAI · HUBC · COEP · ACRV · MYNZ — `D.st.green20.d10` -0.67 · `D.ichi.thick_p.d10` -0.62 · `px.low60_age` +0.59 · `px.close` -0.57 · `D.st.inside10` -0.57
- **QMCO** (2024-11-20) ⟵ XOS · NDLS · ENLV · GNLX · MFI — `H4.adx14.d5` -0.72 · `W.sma10.slope.d10` +0.66 · `H4.sma15.since` -0.65 · `H4.ema13.since` -0.65 · `W.adx14.d5` -0.61
- **RR** (2024-07-18) ⟵ OMH · SABS · MSGM · ENSC · HOTH — `D.st.inside10` -0.81 · `W.ema8.since` -0.69 · `W.ema34.since` -0.67 · `D.st.hl_run` +0.66 · `px.uwick5` +0.66
- **RR** (2024-08-06) ⟵ APYX · GREE · SGMT · PRSO · ENGN — `px.base60_w` +0.68 · `vol.dry5_20.d10` -0.66 · `H4.ichi.thick_p` +0.65 · `vol.spike_d.d10` -0.65 · `H4.adx14.d5` -0.65
- **RSLS** (2025-03-31) ⟵ HYFM · EZGO · LOBO · ALGS · MBIO — `H4.sma100.slope.d5` +0.70 · `H4.ema5.since` -0.69 · `H4.sma89.slope.d10` +0.68 · `H4.ichi.thick_p.d10` -0.65 · `D.bot.macd_hist_p.d5` +0.65
- **RSLS** (2025-04-09) ⟵ PCSA · CTXR · IDAI · GNLN · HBIO — `W.mfi14.d10` +0.87 · `px.ret1` -0.86 · `H4.sma100.since` -0.83 · `H4.ema34.since` -0.81 · `px.close` +0.79
- **RSLS** (2025-08-12) ⟵ APVO · SLE · FRGT · ENVB · CLRB — `D.sma89.slope.d5` -0.88 · `D.sma89.slope.d10` -0.74 · `vol.usd_med20.d5` +0.69 · `W.sma21.slope.d5` +0.67 · `H4.sma150.slope.d10` +0.66
- **AGMH** (2025-09-08) ⟵ ICON · ACXP · AMOD · LFWD · LUCY — `px.lwick10` +0.72 · `H4.sma13.since` +0.72 · `H4.bb.squeeze_rank.d5` -0.68 · `H4.psar.since` +0.66 · `H4.bb.width.d5` -0.66
- **BCTX** (2024-11-20) ⟵ BMR · RNAZ · PRSO · HSCS · CCTG — `W.sma.stack.d5` +0.66 · `D.st.inside10` +0.62 · `D.sma100.slope.d5` +0.60 · `H4.adx14.d5` -0.59 · `D.ema5.since` -0.50
- **COCH** (2025-10-06) ⟵ BTOC · ELUT · LBGJ · GOVX · CMCT — `D.mdi14.d10` -0.69 · `D.sma5.slope.d5` +0.65 · `D.sma10.since` -0.64 · `H4.sma20x50.gap.d5` +0.62 · `px.round_dist.d10` +0.62
- **CRIS** (2023-11-03) ⟵ MBIO · ACRV · PRFX · AEMD · MYNZ — `px.range_d` -0.75 · `px.range_d.d10` -0.67 · `D.cdl.inside_bar.ago` -0.57 · `H4.psar.since` +0.55 · `D.ema20.since` +0.55
- **EDSA** (2025-01-23) ⟵ INDP · HOWL · PDSB · STTK · CRIS — `sh.ratio5` -0.81 · `sh.ratio10` -0.78 · `D.ema21.since` +0.74 · `D.ema20.since` +0.74 · `sh.ratio10.d10` -0.71
- **EYEN** (2025-06-13) ⟵ EVAX · INO · ATLX · AUUD · HOWL — `D.sma144.slope.d10` -0.78 · `W.stoch.k.d5` -0.76 · `H4.atr14_p` +0.74 · `D.sma144.slope.d5` -0.72 · `D.sma200.slope.d5` +0.72
- **FEMY** (2023-07-26) ⟵ GSUN · LPTX · ACON · CYCN · JZXN — `W.mfi14` -0.71 · `D.mfi14.d10` -0.66 · `D.bot.mfi.d10` -0.66 · `H4.psar.since` -0.64 · `D.sma200.since` +0.63
- **HTCR** (2025-08-20) ⟵ ALGS · CISS · GIFT · BNRG · KBSX — `D.sma89.since` -0.71 · `sh.ratio5.d5` +0.68 · `vol.adl_slope20.d5` -0.67 · `vol.cmf20.d5` -0.67 · `px.lwick10.d5` -0.65
- **ICU** (2025-06-24) ⟵ PRFX · NAAS · MSAI · GOVX · LPTX — `W.st.green10.d10` +0.74 · `W.st.green10.d5` +0.71 · `W.st.green20.d5` +0.66 · `H4.sma5.slope.d5` +0.66 · `D.ichi.thick_p.d10` +0.61
- **MINM** (2024-08-01) ⟵ MSGM · HKIT · HOWL · APM · CDIO — `H4.ema100.since` -0.69 · `H4.sma144.since` -0.65 · `H4.sma100.since` -0.65 · `H4.sma150.since` -0.65 · `vol.spike_d.d5` -0.64
- **MNDR** (2025-11-19) ⟵ JYD · DRMA · BBLG · AEMD · DKI — `W.rsi14` +0.78 · `D.st.green10.d10` +0.73 · `W.sma80.since` -0.68 · `W.ema80.since` -0.67 · `vol.adl_slope10.d10` +0.66
- **XPON** (2024-12-27) ⟵ CTXR · ICU · GMM · FEBO · GNLN — `W.macd.hist_p.d5` -0.86 · `W.macd.hist_p.d10` -0.80 · `D.sma100.slope.d10` +0.77 · `H4.ema80.since` -0.74 · `D.ema21.since` -0.73
- **XPON** (2025-08-13) ⟵ TRAW · MNDR · CTNT · KRRO · WIMI — `W.stoch.k.d10` -0.78 · `W.stoch.d.d5` -0.78 · `W.stoch.d.d10` -0.77 · `W.rsi14` -0.76 · `W.kdj.k.d10` -0.75
- **ANGH** (2023-05-01) ⟵ BON · EFOI · NDRA · IFBD · GOVX — `px.range_d.d10` +0.70 · `vol.adl_slope20` -0.68 · `vol.cmf20` -0.68 · `H4.sma5.dist.d10` -0.59 · `H4.sma8.dist.d10` -0.57
- **ANGH** (2024-03-19) ⟵ POLA · AIXI · CENN · WLDS · MYSZ — `H4.sma5.dist.d10` -0.74 · `H4.sma5.dist` -0.72 · `H4.ema5.dist` -0.71 · `px.ret1.d10` -0.70 · `D.mdi14.d5` +0.67
- **AQMS** (2024-11-20) ⟵ NDLS · ENLV · EZGO · CRIS · ASST — `H4.sma10.since` -0.77 · `H4.sma8.since` -0.74 · `H4.st.green20.d5` +0.71 · `H4.atr14_p.d10` -0.63 · `H4.st.green10` +0.55
- **BCDA** (2023-11-13) ⟵ LMFA · AEMD · ADIL · COSM · BEEM — `sh.ratio_d` +0.72 · `vol.adl_slope10.d5` -0.71 · `px.close` -0.68 · `H4.sma100.since` -0.66 · `D.sma34.since` -0.64
- **BCDA** (2024-08-28) ⟵ DBGI · BON · AUUD · GMM · GNLX — `sh.ratio10.d10` +0.78 · `H4.cci20` +0.77 · `H4.ema.nabove.d5` +0.76 · `H4.bb.pctb.d5` +0.76 · `H4.sma100.dist.d5` +0.74
- **CISS** (2025-09-15) ⟵ MNDR · LFWD · XOS · MNTS · XPON — `H4.ichi.thick_p.d5` +0.74 · `px.base20_w.d10` +0.73 · `D.adx14.d5` +0.66 · `D.bot.adx.d5` +0.66 · `D.adx14.d10` +0.66
- **COSM** (2023-09-11) ⟵ LIXT · SLDB · BANL · FRGT · ACET — `W.sma80.slope.d10` -0.69 · `W.sma80.slope.d5` -0.68 · `W.ichi.thick_p.d5` -0.68 · `H4.sma40x80.gap.d5` -0.62 · `W.sma34.slope.d5` +0.62
- **COSM** (2024-06-27) ⟵ VMAR · DRUG · POLA · GMM · HKIT — `D.bot.stochrsi_k.d5` -0.76 · `vol.usd_d` +0.72 · `sh.ratio_d` +0.66 · `D.ema.stack.d5` -0.66 · `D.stoch.k.d5` -0.66
- **CPOP** (2024-06-24) ⟵ ATER · GAME · DBGI · GXAI · JL — `W.mfi14` +0.71 · `H4.sma80.slope.d5` +0.71 · `D.sma21.slope.d5` +0.68 · `D.sr.res_dist.d5` -0.66 · `D.ichi.thick_p` -0.66
- **DRUG** (2023-07-12) ⟵ COEP · MDIA · ANGH · INTZ · CADL — `W.mfi14` +0.60 · `px.below1_30` +0.58 · `D.psar.since` -0.55 · `W.sma21.since` -0.53 · `W.sma40.slope.d10` +0.52
- **GDC** (2023-08-25) ⟵ SLDB · LIXT · GAME · BANL · GLMD — `W.sma21x55.gap.d5` +0.66 · `H4.sma5.since` -0.65 · `D.sma80.slope.d5` -0.64 · `W.don20.low_age` +0.64 · `W.sma21x55.gap.d10` +0.63
- **GDC** (2024-08-14) ⟵ COCH · FUFU · MGOL · ABLV · INTZ — `H4.sma144.since` +0.75 · `H4.sma150.since` +0.73 · `W.sma10.since` +0.68 · `W.bb.squeeze_rank.d5` +0.68 · `D.sma50.since` +0.67
- **GDC** (2024-11-08) ⟵ GOVX · ASST · BON · TELO · TPST — `D.bot.adx` +0.64 · `D.adx14` +0.64 · `px.range_d` +0.62 · `sh.ratio_d` -0.57 · `H4.ichi.thick_p.d5` -0.57
- **GDC** (2025-02-21) ⟵ MNTS · FEBO · CLRO · LPTX · NCI — `D.sma80.slope.d10` +0.61 · `sh.ratio5.d10` -0.61 · `sh.ratio10.d5` -0.60 · `W.mfi14.d5` -0.60 · `sh.ratio_d.d10` -0.59
- **GDC** (2025-08-21) ⟵ DWSN · SERA · GMM · CRBP · EVAX — `sh.ratio10.d5` +0.73 · `sh.ratio5.d10` +0.73 · `sh.ratio5` +0.69 · `W.sma21.slope.d10` -0.61 · `W.sma20.slope.d10` -0.60
- **GLXG** (2025-04-04) ⟵ UCAR · EHGO · IFBD · COCH · CISS — `W.rsi21` +0.74 · `W.rsi14` +0.67 · `D.sma80.slope.d10` +0.66 · `W.adx14` -0.64 · `W.ema30.since` -0.62
- **KIDZ** (2025-09-08) ⟵ ACXP · LFWD · PCLA · GVH · IMNN — `D.ichi.thick_p.d10` -0.88 · `W.sma.stack.d10` +0.70 · `vol.usd_d.d5` +0.69 · `sh.vol_d.d5` +0.67 · `px.range_d.d5` +0.64
- **AEI** (2024-05-23) ⟵ DRUG · JTAI · ASST · CING · MIRA — `vol.spike_d` -0.73 · `D.ema21.since` +0.73 · `D.ema20.since` +0.73 · `vol.spike_d.d10` -0.71 · `sh.ratio5.d5` -0.69
- **BNZI** (2025-12-31) ⟵ HOLO · LGVN · IQST · GP · SUNE — `D.sma200.slope.d5` +0.62 · `px.close` +0.57 · `W.sma80.slope.d10` +0.57 · `D.bb.squeeze_rank` -0.57 · `D.sma150.slope.d5` -0.56
- **EUDA** (2023-04-21) ⟵ RPID · AIMD · LVLU · HYFM · GLMD — `W.adx14.d10` -0.62 · `D.sma144.slope.d5` -0.61 · `vol.adl_slope20.d5` -0.60 · `vol.cmf20.d5` -0.60 · `H4.st.inside10` +0.59
- **EUDA** (2023-08-10) ⟵ BBLG · BTOG · ALLR · LUCY · KPRX — `W.sma40.slope.d10` -0.68 · `D.sma20.since` -0.67 · `W.sma40.slope.d5` -0.65 · `D.sma200.slope.d10` -0.63 · `D.sma55.slope.d5` -0.63
- **EUDA** (2025-09-23) ⟵ GTBP · BNZI · LIMN · MNDR · JSPR — `D.ema15.since` -0.80 · `D.psar.since` -0.77 · `px.atl_age` +0.72 · `D.sma15.since` -0.68 · `vol.adl_slope20` -0.66
- **FRGT** (2023-03-31) ⟵ IMUX · ALXO · ENVB · HSCS · HTOO — `H4.ema20.since` -0.89 · `H4.ema21.since` -0.88 · `H4.sma30.since` -0.87 · `H4.sma34.since` -0.85 · `H4.ema15.since` -0.78
- **HSDT** (2024-11-29) ⟵ ALZN · EZGO · IPA · XOS · JAGX — `H4.psar.since` +0.72 · `D.sma144.slope.d10` +0.71 · `D.bb.squeeze_rank.d5` +0.64 · `D.sma144.slope.d5` +0.63 · `D.bb.squeeze_rank.d10` +0.59
- **HSDT** (2025-06-10) ⟵ CYCC · MBRX · JDZG · EHGO · FTFT — `W.sma55.slope.d5` +0.68 · `W.sma55.slope.d10` +0.67 · `W.st.green10` -0.63 · `H4.sma150.since` +0.61 · `H4.sma144.since` +0.61
- **CETX** (2025-12-04) ⟵ INDP · HCWB · CURX · IQST · ALBT — `H4.sma50.since` -0.86 · `H4.sma8.slope.d10` -0.74 · `px.range_d.d10` +0.70 · `H4.sma8x15.gap.d10` -0.69 · `H4.sma10.slope.d10` -0.69
- **CNSP** (2023-10-12) ⟵ HTOO · DRUG · FAMI · ACET · HUDI — `D.sma20.since` -0.72 · `D.ema15.since` -0.69 · `W.sma21.slope.d5` +0.56 · `px.atl_dist` +0.55 · `D.adx14.d10` -0.53
- **DOGZ** (2023-12-06) ⟵ DPRO · XLO · FBYD · BFRI · MNTS — `D.st.green10.d5` -0.69 · `D.st.green10.d10` -0.67 · `H4.ema30.since` +0.65 · `H4.ema34.since` +0.65 · `D.ema8.since` +0.65
- **DOGZ** (2024-02-21) ⟵ RKDA · CCLD · MSGM · BMRA · IMTE — `D.sma30.slope.d5` -0.80 · `W.sma20.since` +0.76 · `W.sma21.since` +0.75 · `H4.sma80.slope.d5` -0.74 · `W.ema15.since` +0.74
- **HYFM** (2025-04-09) ⟵ ARCT · KSCP · GLMD · RMTI · GP — `D.sma8.since` +0.75 · `W.st.green10.d5` -0.70 · `H4.ema40.since` -0.68 · `H4.sma40.since` -0.68 · `H4.ema34.since` -0.68
- **KDLY** (2025-05-01) ⟵ MIRA · EKSO · GXAI · FLYE · ENLV — `D.sma50.slope.d5` -0.66 · `W.sma.stack` +0.65 · `D.sma50.slope.d10` -0.64 · `W.ema.stack` +0.61 · `px.close` +0.60
- **LMFA** (2024-05-15) ⟵ ABVC · HOTH · HTOO · FEMY · MIRA — `px.close` +0.67 · `H4.pdi14` +0.67 · `H4.sma80.slope.d5` -0.63 · `H4.pdi14.d10` +0.61 · `px.drop252.d5` -0.60
- **LPTX** (2025-11-11) ⟵ MDCX · GXAI · XPON · BCTX · TELO — `D.sr.sup_dist.d5` -0.70 · `D.sma200.slope.d5` +0.68 · `D.bot.kst_diff.d5` +0.64 · `D.kst.diff.d5` +0.64 · `D.bot.kst_diff.d10` +0.63
- **MSGM** (2025-04-14) ⟵ ENLV · TPST · CALC · BBLG · GP — `D.psar.since` -0.54 · `H4.ema15.since` +0.53 · `px.atl_dist.d10` +0.53 · `H4.sma5.since` +0.53 · `W.mdi14.d5` +0.52
- **MTC** (2025-11-04) ⟵ LGHL · CETY · ORKT · RDHL · KSCP — `vol.usd_med20.d5` +0.70 · `D.sr.sup_dist` +0.68 · `sh.ratio5.d5` -0.67 · `vol.usd_med20.d10` +0.64 · `vol.dry5_20.d10` +0.61
- **MTEN** (2025-12-17) ⟵ JZXN · LRHC · GOVX · IQST · ALBT — `H4.sma150.slope.d5` +0.85 · `D.sma30.slope.d5` +0.76 · `D.sma100.slope.d5` +0.73 · `W.kst.diff.d5` +0.72 · `D.bot.macd_hist_p` +0.71
- **OMH** (2025-04-16) ⟵ LMFA · FCEL · BBLG · GP · IFBD — `W.ema89.since` -0.67 · `W.sma80.slope.d5` -0.67 · `D.gap.above_n` +0.63 · `D.sma20.slope.d10` +0.63 · `W.sma80.slope.d10` -0.60
- **SLE** (2025-09-16) ⟵ BDRX · LFWD · LUCY · ONCO · INAB — `vol.obv_slope20.d5` -0.64 · `vol.updown20.d5` -0.62 · `H4.st.green10` +0.61 · `W.sma20.slope.d5` -0.56 · `px.base60_w.d10` +0.56
- **ACON** (2023-05-26) ⟵ ICCM · CNET · KALA · LUCY · GREE — `H4.sma8.since` -0.70 · `H4.sma10.since` -0.70 · `D.bb.squeeze_rank.d5` -0.68 · `vol.adl_slope20.d5` +0.68 · `vol.cmf20.d5` +0.68
- **AMOD** (2025-07-22) ⟵ ALZN · BMEA · MAAS · SPPL · BJDX — `W.ichi.thick_p` -0.72 · `W.sma34.slope.d5` -0.64 · `W.sma34.slope.d10` -0.63 · `W.ema10.since` +0.60 · `D.sma50.slope.d5` -0.57
- **AMST** (2023-03-31) ⟵ GP · ABVC · SLDB · ISPC · DERM — `D.sma21.since` +0.81 · `D.sma20.since` +0.80 · `D.psar.since` +0.69 · `vol.obv_slope20.d5` -0.69 · `vol.updown20.d5` -0.68
- **ARQQ** (2024-10-14) ⟵ HOVR · AGEN · AEHL · AISP · MDIA — `H4.sma40.since` -0.65 · `px.ret1.d10` -0.63 · `W.adx14.d10` +0.61 · `D.vwap_m.dist.d10` -0.61 · `vol.obv_slope10.d5` -0.61
- **ARQQ** (2024-11-06) ⟵ AUUD · GFAI · CPOP · LAES · DRMA — `W.ema15.since` -0.76 · `px.base20_w` +0.73 · `D.fib.retr` +0.70 · `D.sr.sup_dist` +0.70 · `D.don20.low_age` +0.66
- **BLNE** (2025-08-26) ⟵ MBRX · AIFU · JFBR · HUBC · IQST — `H4.st.green20` +0.73 · `H4.st.green20.d10` +0.68 · `H4.st.green10.d10` +0.63 · `px.round_dist.d10` +0.60 · `H4.ema5.since` -0.60
- **CAMP** (2025-12-08) ⟵ SNAL · FEAM · BMRA · CMMB · ALZN — `D.fib.retr.d5` -0.74 · `W.ema30.slope.d5` -0.69 · `W.ema21.slope.d5` -0.69 · `px.ret60.d10` -0.69 · `W.ema20.slope.d5` -0.69
- **CETY** (2024-02-13) ⟵ ACON · LICN · GTBP · FRGT · COEP — `W.cci20.d10` +0.78 · `sh.ratio10` +0.67 · `px.ret1.d5` +0.65 · `px.uwick5.d5` +0.63 · `px.ret1` +0.62
- **DPRO** (2025-06-04) ⟵ IVDA · AVTX · PRFX · ATLX · DMRC — `vol.adl_slope20.d5` -0.77 · `vol.cmf20.d5` -0.77 · `H4.kdj.d.d5` -0.68 · `D.psar.since` +0.66 · `H4.don20.pos.d5` -0.65
- **GWAV** (2024-12-02) ⟵ ASTI · TPST · HSCS · CRIS · BETR — `W.ichi.thick_p.d10` +0.72 · `px.close` -0.65 · `W.sma34.slope.d10` +0.64 · `W.sma34.slope.d5` +0.60 · `D.ema40.since` +0.56
- **GWAV** (2025-10-10) ⟵ EJH · SUNE · EHGO · JSPR · KITT — `px.ret1` +0.78 · `H4.sma200.slope.d5` -0.76 · `D.sma34.since` -0.73 · `H4.sma.nabove.d5` +0.72 · `H4.sma200.slope.d10` -0.71
- **NEGG** (2025-05-09) ⟵ CNTY · MSAI · SFHG · CMTL · CALC — `H4.sma80.since` +0.80 · `px.expl_n` +0.69 · `D.sma34.since` +0.67 · `D.sma30.since` +0.64 · `H4.st.hl_run` +0.62
- **RPGL** (2025-12-26) ⟵ FOFO · LGVN · RECT · MEGL · CRIS — `H4.don55.pos.d10` +0.73 · `H4.sma30.since` -0.73 · `H4.sma150.slope.d10` +0.73 · `H4.ema30.since` -0.71 · `D.bb.width.d10` -0.70

## ⑧ «ما فات البوت»

- سببُ رفض الفرز عند يوم القرار (بأرقام الإنتاج): غير مقيس 254
- جدارُ صفّ «تحت المتابعة» للمتابَعين: —

| السهم | يوم القرار | في المتابعة | رفضُ الفرز | الجدار | الناقصُ وهامشُه | الجاهزيّة |
|---|---|---|---|---|---|---|
| BON | 2023-01-27 | لا | غير مقيس | — | — | — |
| BLBX | 2023-02-24 | لا | غير مقيس | — | — | — |
| CELZ | 2023-03-20 | لا | غير مقيس | — | — | — |
| EYPT | 2023-03-24 | لا | غير مقيس | — | — | — |
| AMST | 2023-03-31 | لا | غير مقيس | — | — | — |
| FRGT | 2023-03-31 | لا | غير مقيس | — | — | — |
| CDLX | 2023-04-03 | لا | غير مقيس | — | — | — |
| ELOX | 2023-04-03 | لا | غير مقيس | — | — | — |
| LUCY | 2023-04-10 | لا | غير مقيس | — | — | — |
| APM | 2023-04-13 | لا | غير مقيس | — | — | — |
| EUDA | 2023-04-21 | لا | غير مقيس | — | — | — |
| MEGL | 2023-04-27 | لا | غير مقيس | — | — | — |
| ANGH | 2023-05-01 | لا | غير مقيس | — | — | — |
| IMCC | 2023-05-12 | لا | غير مقيس | — | — | — |
| WLDS | 2023-05-24 | لا | غير مقيس | — | — | — |
| ACON | 2023-05-26 | لا | غير مقيس | — | — | — |
| AUUD | 2023-06-09 | لا | غير مقيس | — | — | — |
| GREE | 2023-06-13 | لا | غير مقيس | — | — | — |
| HCTI | 2023-07-05 | لا | غير مقيس | — | — | — |
| CDLX | 2023-07-10 | لا | غير مقيس | — | — | — |
| ELOX | 2023-07-10 | لا | غير مقيس | — | — | — |
| GLMD | 2023-07-11 | لا | غير مقيس | — | — | — |
| DRUG | 2023-07-12 | لا | غير مقيس | — | — | — |
| JZXN | 2023-07-12 | لا | غير مقيس | — | — | — |
| IFBD | 2023-07-19 | لا | غير مقيس | — | — | — |
| FEMY | 2023-07-26 | لا | غير مقيس | — | — | — |
| ABVC | 2023-07-31 | لا | غير مقيس | — | — | — |
| EUDA | 2023-08-10 | لا | غير مقيس | — | — | — |
| DBGI | 2023-08-11 | لا | غير مقيس | — | — | — |
| GDC | 2023-08-25 | لا | غير مقيس | — | — | — |
| COSM | 2023-09-11 | لا | غير مقيس | — | — | — |
| MLGO | 2023-09-11 | لا | غير مقيس | — | — | — |
| EJH | 2023-09-27 | لا | غير مقيس | — | — | — |
| CNSP | 2023-10-12 | لا | غير مقيس | — | — | — |
| CALC | 2023-10-24 | لا | غير مقيس | — | — | — |
| PSTV | 2023-11-02 | لا | غير مقيس | — | — | — |
| CRIS | 2023-11-03 | لا | غير مقيس | — | — | — |
| BCDA | 2023-11-13 | لا | غير مقيس | — | — | — |
| ICCM | 2023-11-27 | لا | غير مقيس | — | — | — |
| BMEA | 2023-11-28 | لا | غير مقيس | — | — | — |
| ERNA | 2023-11-30 | لا | غير مقيس | — | — | — |
| DOGZ | 2023-12-06 | لا | غير مقيس | — | — | — |
| RNXT | 2023-12-12 | لا | غير مقيس | — | — | — |
| ABVC | 2023-12-13 | لا | غير مقيس | — | — | — |
| BEAT | 2023-12-20 | لا | غير مقيس | — | — | — |
| MGOL | 2024-01-05 | لا | غير مقيس | — | — | — |
| EJH | 2024-01-09 | لا | غير مقيس | — | — | — |
| SGMT | 2024-01-10 | لا | غير مقيس | — | — | — |
| IKT | 2024-01-11 | لا | غير مقيس | — | — | — |
| FTEL | 2024-01-16 | لا | غير مقيس | — | — | — |
| IFBD | 2024-01-22 | لا | غير مقيس | — | — | — |
| CMND | 2024-01-23 | لا | غير مقيس | — | — | — |
| MSS | 2024-01-25 | لا | غير مقيس | — | — | — |
| WGS | 2024-01-26 | لا | غير مقيس | — | — | — |
| RLYB | 2024-02-05 | لا | غير مقيس | — | — | — |
| MNY | 2024-02-07 | لا | غير مقيس | — | — | — |
| ADIL | 2024-02-13 | لا | غير مقيس | — | — | — |
| CETY | 2024-02-13 | لا | غير مقيس | — | — | — |
| COEP | 2024-02-14 | لا | غير مقيس | — | — | — |
| XRTX | 2024-02-16 | لا | غير مقيس | — | — | — |
| DOGZ | 2024-02-21 | لا | غير مقيس | — | — | — |
| AIMD | 2024-02-28 | لا | غير مقيس | — | — | — |
| ANGH | 2024-03-19 | لا | غير مقيس | — | — | — |
| AVTX | 2024-03-27 | لا | غير مقيس | — | — | — |
| NEOV | 2024-03-27 | لا | غير مقيس | — | — | — |
| RLYB | 2024-03-27 | لا | غير مقيس | — | — | — |
| EJH | 2024-04-03 | لا | غير مقيس | — | — | — |
| AUUD | 2024-04-05 | لا | غير مقيس | — | — | — |
| LGVN | 2024-04-05 | لا | غير مقيس | — | — | — |
| LASE | 2024-04-08 | لا | غير مقيس | — | — | — |
| LGVN | 2024-04-12 | لا | غير مقيس | — | — | — |
| ATGL | 2024-04-19 | لا | غير مقيس | — | — | — |
| BOF | 2024-04-23 | لا | غير مقيس | — | — | — |
| CTNT | 2024-05-13 | لا | غير مقيس | — | — | — |
| LMFA | 2024-05-15 | لا | غير مقيس | — | — | — |
| AKTX | 2024-05-21 | لا | غير مقيس | — | — | — |
| AEI | 2024-05-23 | لا | غير مقيس | — | — | — |
| XTIA | 2024-06-04 | لا | غير مقيس | — | — | — |
| MDIA | 2024-06-07 | لا | غير مقيس | — | — | — |
| EJH | 2024-06-10 | لا | غير مقيس | — | — | — |
| FUFU | 2024-06-11 | لا | غير مقيس | — | — | — |
| LRHC | 2024-06-13 | لا | غير مقيس | — | — | — |
| CPOP | 2024-06-24 | لا | غير مقيس | — | — | — |
| COSM | 2024-06-27 | لا | غير مقيس | — | — | — |
| HOVR | 2024-07-10 | لا | غير مقيس | — | — | — |
| MIRA | 2024-07-12 | لا | غير مقيس | — | — | — |
| RR | 2024-07-18 | لا | غير مقيس | — | — | — |
| RDHL | 2024-07-31 | لا | غير مقيس | — | — | — |
| MINM | 2024-08-01 | لا | غير مقيس | — | — | — |
| RR | 2024-08-06 | لا | غير مقيس | — | — | — |
| GOVX | 2024-08-09 | لا | غير مقيس | — | — | — |
| TPST | 2024-08-12 | لا | غير مقيس | — | — | — |
| GDC | 2024-08-14 | لا | غير مقيس | — | — | — |
| MNTS | 2024-08-16 | لا | غير مقيس | — | — | — |
| BOF | 2024-08-27 | لا | غير مقيس | — | — | — |
| BCDA | 2024-08-28 | لا | غير مقيس | — | — | — |
| LUCY | 2024-08-28 | لا | غير مقيس | — | — | — |
| XRTX | 2024-08-28 | لا | غير مقيس | — | — | — |
| BENF | 2024-09-05 | لا | غير مقيس | — | — | — |
| BBLG | 2024-09-13 | لا | غير مقيس | — | — | — |
| ZEO | 2024-09-18 | لا | غير مقيس | — | — | — |
| TCTM | 2024-09-26 | لا | غير مقيس | — | — | — |
| MNTS | 2024-10-08 | لا | غير مقيس | — | — | — |
| ARQQ | 2024-10-14 | لا | غير مقيس | — | — | — |
| CYCC | 2024-10-15 | لا | غير مقيس | — | — | — |
| BIVI | 2024-10-17 | لا | غير مقيس | — | — | — |
| HOWL | 2024-10-18 | لا | غير مقيس | — | — | — |
| ALGS | 2024-10-23 | لا | غير مقيس | — | — | — |
| AMIX | 2024-10-25 | لا | غير مقيس | — | — | — |
| GNLN | 2024-10-25 | لا | غير مقيس | — | — | — |
| ARQQ | 2024-11-06 | لا | غير مقيس | — | — | — |
| CYN | 2024-11-06 | لا | غير مقيس | — | — | — |
| GDC | 2024-11-08 | لا | غير مقيس | — | — | — |
| IVDA | 2024-11-18 | لا | غير مقيس | — | — | — |
| AQMS | 2024-11-20 | لا | غير مقيس | — | — | — |
| BCTX | 2024-11-20 | لا | غير مقيس | — | — | — |
| QMCO | 2024-11-20 | لا | غير مقيس | — | — | — |
| CADL | 2024-11-21 | لا | غير مقيس | — | — | — |
| MOBX | 2024-11-21 | لا | غير مقيس | — | — | — |
| OMEX | 2024-11-27 | لا | غير مقيس | — | — | — |
| HSDT | 2024-11-29 | لا | غير مقيس | — | — | — |
| CTNT | 2024-12-02 | لا | غير مقيس | — | — | — |
| GWAV | 2024-12-02 | لا | غير مقيس | — | — | — |
| JZXN | 2024-12-10 | لا | غير مقيس | — | — | — |
| ABLV | 2024-12-13 | لا | غير مقيس | — | — | — |
| MSS | 2024-12-16 | لا | غير مقيس | — | — | — |
| CGTX | 2024-12-17 | لا | غير مقيس | — | — | — |
| CURR | 2024-12-17 | لا | غير مقيس | — | — | — |
| MYSZ | 2024-12-18 | لا | غير مقيس | — | — | — |
| XHG | 2024-12-18 | لا | غير مقيس | — | — | — |
| ATPC | 2024-12-19 | لا | غير مقيس | — | — | — |
| MSAI | 2024-12-19 | لا | غير مقيس | — | — | — |
| FLYE | 2024-12-20 | لا | غير مقيس | — | — | — |
| BAOS | 2024-12-23 | لا | غير مقيس | — | — | — |
| JTAI | 2024-12-23 | لا | غير مقيس | — | — | — |
| KITT | 2024-12-24 | لا | غير مقيس | — | — | — |
| SUGP | 2024-12-24 | لا | غير مقيس | — | — | — |
| BKYI | 2024-12-26 | لا | غير مقيس | — | — | — |
| XPON | 2024-12-27 | لا | غير مقيس | — | — | — |
| HCTI | 2024-12-30 | لا | غير مقيس | — | — | — |
| BAOS | 2025-01-02 | لا | غير مقيس | — | — | — |
| BTCT | 2025-01-16 | لا | غير مقيس | — | — | — |
| RNAZ | 2025-01-22 | لا | غير مقيس | — | — | — |
| EDSA | 2025-01-23 | لا | غير مقيس | — | — | — |
| REBN | 2025-01-27 | لا | غير مقيس | — | — | — |
| GSIW | 2025-02-06 | لا | غير مقيس | — | — | — |
| MBRX | 2025-02-12 | لا | غير مقيس | — | — | — |
| XOS | 2025-02-19 | لا | غير مقيس | — | — | — |
| MLGO | 2025-02-20 | لا | غير مقيس | — | — | — |
| ATPC | 2025-02-21 | لا | غير مقيس | — | — | — |
| GDC | 2025-02-21 | لا | غير مقيس | — | — | — |
| ARBB | 2025-02-27 | لا | غير مقيس | — | — | — |
| CELU | 2025-03-04 | لا | غير مقيس | — | — | — |
| ANTE | 2025-03-11 | لا | غير مقيس | — | — | — |
| BON | 2025-03-13 | لا | غير مقيس | — | — | — |
| GLMD | 2025-03-14 | لا | غير مقيس | — | — | — |
| AQB | 2025-03-24 | لا | غير مقيس | — | — | — |
| RSLS | 2025-03-31 | لا | غير مقيس | — | — | — |
| TCRT | 2025-03-31 | لا | غير مقيس | — | — | — |
| MRM | 2025-04-02 | لا | غير مقيس | — | — | — |
| AGEN | 2025-04-04 | لا | غير مقيس | — | — | — |
| GLXG | 2025-04-04 | لا | غير مقيس | — | — | — |
| JZXN | 2025-04-07 | لا | غير مقيس | — | — | — |
| CDT | 2025-04-09 | لا | غير مقيس | — | — | — |
| HYFM | 2025-04-09 | لا | غير مقيس | — | — | — |
| RSLS | 2025-04-09 | لا | غير مقيس | — | — | — |
| LOBO | 2025-04-14 | لا | غير مقيس | — | — | — |
| MSGM | 2025-04-14 | لا | غير مقيس | — | — | — |
| ADGM | 2025-04-16 | لا | غير مقيس | — | — | — |
| OMH | 2025-04-16 | لا | غير مقيس | — | — | — |
| SXTC | 2025-04-16 | لا | غير مقيس | — | — | — |
| GELS | 2025-04-21 | لا | غير مقيس | — | — | — |
| ENSC | 2025-04-22 | لا | غير مقيس | — | — | — |
| NDRA | 2025-04-22 | لا | غير مقيس | — | — | — |
| FMST | 2025-04-30 | لا | غير مقيس | — | — | — |
| KDLY | 2025-05-01 | لا | غير مقيس | — | — | — |
| NEGG | 2025-05-09 | لا | غير مقيس | — | — | — |
| HCWB | 2025-05-12 | لا | غير مقيس | — | — | — |
| EDBL | 2025-05-19 | لا | غير مقيس | — | — | — |
| PSTV | 2025-05-30 | لا | غير مقيس | — | — | — |
| NA | 2025-06-03 | لا | غير مقيس | — | — | — |
| DPRO | 2025-06-04 | لا | غير مقيس | — | — | — |
| EVGN | 2025-06-09 | لا | غير مقيس | — | — | — |
| HSDT | 2025-06-10 | لا | غير مقيس | — | — | — |
| CGTL | 2025-06-11 | لا | غير مقيس | — | — | — |
| EYEN | 2025-06-13 | لا | غير مقيس | — | — | — |
| INLF | 2025-06-13 | لا | غير مقيس | — | — | — |
| APVO | 2025-06-17 | لا | غير مقيس | — | — | — |
| ICU | 2025-06-24 | لا | غير مقيس | — | — | — |
| MBRX | 2025-06-25 | لا | غير مقيس | — | — | — |
| LCFY | 2025-06-26 | لا | غير مقيس | — | — | — |
| MBIO | 2025-06-30 | لا | غير مقيس | — | — | — |
| SUGP | 2025-07-08 | لا | غير مقيس | — | — | — |
| CALC | 2025-07-10 | لا | غير مقيس | — | — | — |
| CLGN | 2025-07-11 | لا | غير مقيس | — | — | — |
| IBG | 2025-07-11 | لا | غير مقيس | — | — | — |
| AMOD | 2025-07-22 | لا | غير مقيس | — | — | — |
| STSS | 2025-08-07 | لا | غير مقيس | — | — | — |
| KRRO | 2025-08-12 | لا | غير مقيس | — | — | — |
| RSLS | 2025-08-12 | لا | غير مقيس | — | — | — |
| XPON | 2025-08-13 | لا | غير مقيس | — | — | — |
| HTCR | 2025-08-20 | لا | غير مقيس | — | — | — |
| GDC | 2025-08-21 | لا | غير مقيس | — | — | — |
| HCWB | 2025-08-22 | لا | غير مقيس | — | — | — |
| HKPD | 2025-08-25 | لا | غير مقيس | — | — | — |
| BLNE | 2025-08-26 | لا | غير مقيس | — | — | — |
| RLMD | 2025-08-27 | لا | غير مقيس | — | — | — |
| AIHS | 2025-09-02 | لا | غير مقيس | — | — | — |
| GELS | 2025-09-04 | لا | غير مقيس | — | — | — |
| ISPC | 2025-09-04 | لا | غير مقيس | — | — | — |
| RLMD | 2025-09-04 | لا | غير مقيس | — | — | — |
| AGMH | 2025-09-08 | لا | غير مقيس | — | — | — |
| BON | 2025-09-08 | لا | غير مقيس | — | — | — |
| KIDZ | 2025-09-08 | لا | غير مقيس | — | — | — |
| FTEL | 2025-09-09 | لا | غير مقيس | — | — | — |
| ABTS | 2025-09-15 | لا | غير مقيس | — | — | — |
| CISS | 2025-09-15 | لا | غير مقيس | — | — | — |
| SLE | 2025-09-16 | لا | غير مقيس | — | — | — |
| AERT | 2025-09-17 | لا | غير مقيس | — | — | — |
| DRIO | 2025-09-19 | لا | غير مقيس | — | — | — |
| IBG | 2025-09-22 | لا | غير مقيس | — | — | — |
| DBGI | 2025-09-23 | لا | غير مقيس | — | — | — |
| EUDA | 2025-09-23 | لا | غير مقيس | — | — | — |
| BENF | 2025-09-29 | لا | غير مقيس | — | — | — |
| FEAM | 2025-10-02 | لا | غير مقيس | — | — | — |
| COCH | 2025-10-06 | لا | غير مقيس | — | — | — |
| GWAV | 2025-10-10 | لا | غير مقيس | — | — | — |
| IBIO | 2025-10-20 | لا | غير مقيس | — | — | — |
| PPBT | 2025-10-28 | لا | غير مقيس | — | — | — |
| MTC | 2025-11-04 | لا | غير مقيس | — | — | — |
| BIYA | 2025-11-05 | لا | غير مقيس | — | — | — |
| CMCT | 2025-11-05 | لا | غير مقيس | — | — | — |
| MSGY | 2025-11-07 | لا | غير مقيس | — | — | — |
| CGTL | 2025-11-11 | لا | غير مقيس | — | — | — |
| LPTX | 2025-11-11 | لا | غير مقيس | — | — | — |
| BCG | 2025-11-13 | لا | غير مقيس | — | — | — |
| ATGL | 2025-11-14 | لا | غير مقيس | — | — | — |
| IMCC | 2025-11-17 | لا | غير مقيس | — | — | — |
| LOBO | 2025-11-17 | لا | غير مقيس | — | — | — |
| MNDR | 2025-11-19 | لا | غير مقيس | — | — | — |
| IVDA | 2025-11-20 | لا | غير مقيس | — | — | — |
| INHD | 2025-11-21 | لا | غير مقيس | — | — | — |
| CMCT | 2025-11-25 | لا | غير مقيس | — | — | — |
| KALA | 2025-11-25 | لا | غير مقيس | — | — | — |
| KITT | 2025-12-02 | لا | غير مقيس | — | — | — |
| CETX | 2025-12-04 | لا | غير مقيس | — | — | — |
| AFJK | 2025-12-05 | لا | غير مقيس | — | — | — |
| ORKT | 2025-12-05 | لا | غير مقيس | — | — | — |
| CAMP | 2025-12-08 | لا | غير مقيس | — | — | — |
| AFJK | 2025-12-17 | لا | غير مقيس | — | — | — |
| MTEN | 2025-12-17 | لا | غير مقيس | — | — | — |
| RPGL | 2025-12-26 | لا | غير مقيس | — | — | — |
| INBS | 2025-12-30 | لا | غير مقيس | — | — | — |
| BNZI | 2025-12-31 | لا | غير مقيس | — | — | — |

## ⑨ الصفقة (وصف): شراءُ افتتاح اليوم التالي للقرار وبيعُ إغلاق الجلسة العشرين · كلفة 1.8%

- المنفجرون: متوسّط 50.1% · وسيط 24.7% · خاسرون 38.2% (من 254)
- الضابطة: متوسّط -8.9% · وسيط -9.1% · خاسرون 68.0% (من 12,408)

