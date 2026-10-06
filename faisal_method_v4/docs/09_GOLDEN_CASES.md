# 09 — الحالاتُ الذهبيّة (§16 · تحقّقٌ لا اكتشاف)

> قائمةُ الملفّ المسجَّل (V3.1): RAYA · LABT · ZNB · RUBI · AMIX · HCWB · DXST · VEEE · ATMV ‏+ ما سمّته المهمّة (SPRC · CUPR) — و`target10` تجربةٌ لا رمز.
> **لم تصنع قاعدة:** لا رمزَ ذهبيٌّ في كود المحرّك (قفل V4L7) والقواعدُ من نصوص الطبقة 1/2.

## ① بتواريخ V3.1 نفسِها (قراءةٌ عند جلسة V3.1 شاملةً)
| الحالة | فيصل | تاريخ V3.1 | V3.1 | طابق؟ | V4 الفنيّة | V4 الحالة | V4 الكلمة | طابق؟ | الحاسم | الفئة |
|---|---|---|---|---|---|---|---|---|---|---|
| RAYA | WAIT | 2026-08-21 | WAIT | ✅ | RETEST_PENDING | WAIT | WAIT | ✅ | 2.0 | BELOW |
| LABT | WAIT | 2026-08-21 | WAIT | ✅ | RETEST_PENDING | WAIT | WAIT | ✅ | 2.0437 | BELOW |
| ZNB | WAIT | 2026-07-31 | WAIT | ✅ | RETEST_PENDING | WAIT | WAIT | ✅ | 1.84 | BELOW |
| RUBI | WAIT | 2026-08-21 | READY | ❌ | RETEST_HELD | UNKNOWN | READY | ❌ | 1.76 | AT |
| AMIX | READY | 2026-08-21 | WAIT | ❌ | BASE_FORMING | WAIT | WAIT | ❌ | 5.14 | AT |
| HCWB | READY | 2026-08-21 | WAIT | ❌ | BASE_FORMING | WAIT | WAIT | ❌ | 2.05 | BELOW |
| DXST | WAIT | 2026-06-15 | READY | ❌ | RETEST_PENDING | WAIT | WAIT | ✅ | 1.56 | BELOW |
| VEEE | WAIT | — | — | — | — | UNKNOWN | — | — | — | — |
| ATMV | WAIT | — | — | — | — | UNKNOWN | — | — | — | — |
⟵ **V3.1 3/7 · V4 4/7 · و«دائمًا WAIT» 5/7** — تحسّنُ DXST (READY⟵WAIT) يقابله أنّ الخطَّ التافه أعلى من الاثنين ⟵ **لا دعوى تحسّن**. AMIX/HCWB (READY عند فيصل) ⟵ BASE_FORMING عند المحرّك.

## ② بتواريخ عبارات V4 (المجموعة S3 كلّها)
| المجموعة | حالات | سليمة | الحالات | H-LEVEL | الفرق [95%] (كلّ المستويات) | النصّيّة الصرفة | H-CLASS |
|---|---|---|---|---|---|---|---|
| S3 الذهبيّة | 19 | 16 | NO_BARS 1 · OK 16 · SCALE_MISMATCH 2 | FAIL | +0.1272 [-0.0316 · +0.2939] · مستويات 29 · حالات 11 | +0.1272 [-0.0316 · +0.2939] · مستويات 29 · حالات 11 | FAIL · اتّفاق 5/15 · ويلسون [0.1518, 0.5829] · الأغلبيّة BELOW 0.4 |

## ③ DXST (§19)
**D — MANUAL_JUDGMENT_UNREPRODUCIBLE (اختيارٌ تقديريّ بين بُنًى صالحة)** · المراسي {'L1': 2.4, 'L2': 2.55, 'NECK': 2.864}
| الجلسة | شموع | الخطوة 1 (نقاطٌ موجودة) | الخطوة 2 (محاور k=1/2/3) | الخطوة 3 (المكتشف) | W المكتشف |
|---|---|---|---|---|---|
| extended | 120 | ['2026-06-12 15:30', '2026-06-15 09:00', '2026-06-15 13:00'] | {"1": ["2026-06-12 15:30", "2026-06-15 12:00", "2026-06-15 14:30"], "2": null, "3": null} | False | {'low1': 2.48, 'low2': 2.585, 'neckline': 2.76} |
| regular | 120 | ['2026-06-12 15:30', '2026-06-15 11:30', '2026-06-15 13:00'] | {"1": ["2026-06-12 15:30", "2026-06-15 12:00", "2026-06-15 14:30"], "2": null, "3": null} | False | {'low1': 2.5, 'low2': 2.36, 'neckline': 2.66} |
⟵ نقاطُ رسم فيصل **موجودةٌ ومحاورُ مؤكَّدةٌ بعرض 1** والمكتشفُ الافتراضيّ يختار بنيةً أخرى ⟵ **اختيارٌ تقديريّ** · لا تسامحَ وُسِّع.

## ④ VEEE (§20)
**العقد (§⑨): UNKNOWN** — A8 على شموع V3.1 UNKNOWN وعلى fetch UNKNOWN (المصدران متّفقان: True) · السبب: قمّةُ الستّين عند الجلسات المرشّحة ليست 8.80 بل أعلى (صعودٌ سابق داخل النافذة):
| الجلسة | الإغلاق | التغيّر | قاع 60 | قمّة 60 |
|---|---|---|---|---|
| 2026-04-28 | 6.8265 | -0.1332 | 5.7572 | 65.49 |
| 2026-05-15 | 6.76 | 0.2 | 5.0 | 23.0547 |
| 2026-05-21 | 6.7 | 0.64 | 5.0 | 23.0547 |
| 2026-05-27 | 6.75 | 0.06 | 5.0 | 23.0547 |
| 2026-06-10 | 6.74 | 0.75 | 5.0 | 18.5 |
**⚠️ POST-HOC (لم يُسجَّل):** مرساةُ شارت فيصل «$6.760 ‏+0.200 (‏+3.049%) At close» تُفرد **['2026-05-15']** (DATED_POSTHOC) — تُنشر وصفًا ولا تحلّ محلَّ حكم العقد · والوسم `POST-HOC-INSPECTED` قائمٌ (صفوفُ مايو رُئيت قبل العقد).

## ⑤ ATMV (§21)
**DATA_UNAVAILABLE** — 25 مصدرًا جُرّب واحدًا واحدًا:
| المصدر | الرمز | النتيجة |
|---|---|---|
| TradingView scanner map | ATMV | غائبٌ عن الخريطة |
| TradingView chart | NASDAQ:ATMV | لا شموع (None) |
| TradingView chart | NYSE:ATMV | لا شموع (None) |
| TradingView chart | AMEX:ATMV | لا شموع (None) |
| TradingView chart | OTC:ATMV | لا شموع (None) |
| Yahoo (yfinance) | ATMV | 0 شمعة |
| TradingView scanner map | ATMVU | غائبٌ عن الخريطة |
| TradingView chart | NASDAQ:ATMVU | لا شموع (None) |
| TradingView chart | NYSE:ATMVU | لا شموع (None) |
| TradingView chart | AMEX:ATMVU | لا شموع (None) |
| TradingView chart | OTC:ATMVU | لا شموع (None) |
| Yahoo (yfinance) | ATMVU | 0 شمعة |
| TradingView scanner map | ATMVR | غائبٌ عن الخريطة |
| TradingView chart | NASDAQ:ATMVR | لا شموع (None) |
| TradingView chart | NYSE:ATMVR | لا شموع (None) |
| TradingView chart | AMEX:ATMVR | لا شموع (None) |
| TradingView chart | OTC:ATMVR | لا شموع (None) |
| Yahoo (yfinance) | ATMVR | 0 شمعة |
| TradingView scanner map | ATMVW | غائبٌ عن الخريطة |
| TradingView chart | NASDAQ:ATMVW | لا شموع (None) |
| TradingView chart | NYSE:ATMVW | لا شموع (None) |
| TradingView chart | AMEX:ATMVW | لا شموع (None) |
| TradingView chart | OTC:ATMVW | لا شموع (None) |
| Yahoo (yfinance) | ATMVW | 0 شمعة |
| NASDAQ universe (production list) | ATMV* | أعضاءٌ في القائمة: لا شيء |
