# `T-LAYERS` — الملحق 2 (2026-10-14): عطلُ تنفيذٍ في الشرط ④ · والتشغيلةُ الأولى منشورةٌ لا تُمحى

> **العقدُ (#619) والملحقُ 1 (#620) لا يُعدَّل منهما حرف.** هذا الملحقُ **لا يغيّر تعريفًا ولا عتبةً ولا معيارًا ولا مجتمعًا** —
> يُصلح **كودًا خالف نصَّ العقد** ويضيف مُخرَجًا وصفيًّا نصّ عليه العقدُ ولم يُبنَ. ويُدمج قبل التشغيلة الثانية.
> 🔴 **والتشغيلةُ الأولى قُرئت أرقامُها** — فهي منشورةٌ هنا بحرفها ومحفوظةٌ في `data/run1/` ببصماتها، **ولا تُحذف**.

## ① العطلُ (مُثبَتٌ برمزٍ حقيقيّ)
**نصُّ العقد ④:** «لا يومَ `y` بين قاعِ هذه القاعدة و`t−1` (‏`pc(y).bottom = pc(t).bottom`) تحقّق فيه ②∧③ ⟵ **زنادٌ واحدٌ لكلّ قاعدة**».
**والكودُ (`day_state`) كان يتوقّف** عند أوّل يومٍ تختلف فيه القاعدة (`break`) بدل أن **يتخطّاه** ويُكمل إلى قاع القاعدة.
ودالّةُ الإنتاج `pivot_cycle_state` **تتذبذب** في القاعدة التي تقرؤها يومًا بيوم ⟵ فصار للقاعدة الواحدة زنادان:
**INDP** (أرشيف الترتيب): 08-21 ‏`bottom 1.01 · retest_low 0.92 · 8.91%` ⟵ **زناد** · 08-24 ‏`bottom 0.92 · stage 2` ⟵ 08-25 ‏`bottom 1.01 · 0.92 · 8.91%` ⟵ **زنادٌ ثانٍ**
على القاعدة نفسِها (في جدول الإنذار الكاذب مرّتين). **الإصلاح:** اليومُ ذو القاعدة المختلفة (أو بلا قراءة) **يُتخطّى** ولا يُنهي البحث — كما في النصّ.
⟵ أثرُه بالبناء: **أزندةٌ أقلّ لا أكثر** (كلُّ زنادٍ بعد الإصلاح كان زنادًا قبله).

## ② مُخرَجٌ وصفيٌّ نصّ عليه العقدُ ولم يُبنَ (§④): اتّفاقُ المصدرين
«ويُطبع اتّفاقُ الزناد بين المصدرين على أيّام التداخل وصفًا» ⟵ على أيّام المرحلة أ حتى 2026-10-09 (نهاية الأرشيف) ولأعضاء `Q`:
أزندةُ النواة من شموع GEN5 مقابل أزندتها من أرشيف الترتيب ⟵ المشتركة · في GEN5 وحدَه · في الأرشيف وحدَه. **وصفٌ لا حكم.**

## ③ التشغيلةُ الأولى — بحرفها (‏`data/run1/run1_report.txt` · `layers_result.json` ‏`b79f3686922c…`)
```
verdict B-FAIL selection BOOSTED combo ['VOL', 'NODE']
ALL_COVERED_core             med 28.5 range 13-49 zero 0 silence 0 roll3 86.5 total 574 pass False undetermined 0
Q_core                       med 7.5 range 1-14 zero 0 silence 0 roll3 23.0 total 156 pass False undetermined 0
Q_core+VOL                   med 3 range 0-6 zero 2 silence 2 roll3 8 total 48 pass False undetermined 1
Q_core+NODE                  med 4 range 0-7 zero 1 silence 1 roll3 12 total 76 pass False undetermined 1
Q_core+CANDLE                med 1.0 range 0-5 zero 7 silence 3 roll3 5.0 total 33 pass False undetermined 0
Q_core+VOL+NODE              med 1 range 0-3 zero 9 silence 4 roll3 1 total 17 pass True undetermined 1
Q_core+VOL+CANDLE            med 0 range 0-3 zero 10 silence 4 roll3 2 total 14 pass True undetermined 1
Q_core+NODE+CANDLE           med 0 range 0-2 zero 10 silence 4 roll3 3 total 14 pass True undetermined 1
Q_core+VOL+NODE+CANDLE       med 0 range 0-2 zero 17 silence 9 roll3 0 total 3 pass False undetermined 1
Q_NW_core                    med 7.0 range 1-13 zero 0 silence 0 roll3 21.0 total 147 pass False undetermined 0
Q_WL_core                    med 0.5 range 0-2 zero 10 silence 3 roll3 2.0 total 13 pass True undetermined 0
Q_READY_core                 med 0.0 range 0-0 zero 20 silence 20 roll3 0.0 total 0 pass False undetermined 0
PROD_SWEEP_STATE_Q           med 124.0 range 85-149 zero 0 silence 0 roll3 373.0 total 2450 pass False undetermined 0
LIVE_SWEEP_FINGERPRINTS      med 1.0 range 0-3 zero 5 silence 3 roll3 4.0 total 24 pass True undetermined 0
stage B {'events': 40, 'symbols': 40, 'captured_symbols': 0, 'ready_symbols': 2, 'C1': False, 'mde_symbols': 12}
false alarms {'fired': 21, 'resolved': 21, 'false': 18, 'rate': 0.8571, 'symbols_fired': 19, 'symbols_false_only': 17} depth {'n': 40, 'no_sweep': 0, 'median': 57.67, 'q1': 42.05, 'q3': 77.19, 'under_7': 0, 'in_band': 1, 'over_13': 39}
```

## ④ ما يُقرأ حكمًا
**الحكمُ من التشغيلة الثانية** (الكودُ مطابقٌ للنصّ) بالمعايير نفسِها وقاعدة الاختيار نفسِها **بلا أيّ تعديل** · **وتُطبع التشغيلتان جنبًا إلى جنب**
في النتيجة · **وإن اختلف الحكمان يُعلَن الاختلافُ ولا يُختار الأنسب** — والحكمُ الحاكمُ الثانيةُ لأن الأولى خالفت نصَّ العقد لا لأن رقمها لم يُعجب.
