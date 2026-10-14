# `T-FSWEEP` — حصادُ سحوب فيصل بأرقامه هو

> **أمرُ المالك (2026-10-14):** «سجّل حصاد سحوب فيصل». العقدُ `FSWEEP_prereg.md` (مدموجٌ قبل أيّ فرز · بصمتُه في الأداة).
> **جمعٌ وقياسٌ فقط** — لا إنتاج · لا عتبة · لا جذور · لا V4 · لا H6 · لا تلغرام.

## السؤال
حين يكتب فيصل عن **سحب سيولة** على سهم، هل كان السهمُ قبل منشوره قد **كسر قاعدةَ دورته أعمقَ من 13%** (`H-COLLAPSE`)؟
إن نعم ⟵ «7-13%» عنده لا تُقاس من قاعدة الدورة (الأرجح من أحدث قاع) · وإن لا ⟵ الخمسةُ (أعمقُ من 13%) لم يكونوا حالاتِ سحبٍ عنده.

## الحلقة لكلّ صورةٍ جديدة (بعد `2026-10-15T00:00:00Z`)
1. الجامعُ (`telegram_collect.py` · كلَّ 4 ساعات) يحفظها.
2. في الجلسة: `python3 fm_forensics/fsweep/fsweep.py pending` ⟵ ما ينتظر.
3. سجلُّ العين `RR1` ⟵ استلامُ V4.1 إن كانت حالةً عنده ⟵ **ثمّ الفرز هنا**:
   ```bash
   python3 fm_forensics/fsweep/fsweep.py triage --image TG_123.jpg --decision NONE
   python3 fm_forensics/fsweep/fsweep.py triage --image TG_124.jpg --decision SWEEP --symbol ABC \
       --post-date 2026-10-20T09:40 --date-source visible_in_image --kind EXPECTED --author FAISAL \
       --base 1.20 --low 1.06 --quote "نصُّه الحرفيّ"
   python3 fm_forensics/fsweep/fsweep.py correct --seq 3 --decision UNREADABLE --note "السبب"
   ```
4. `verify` (السلسلة · البصمات · الحدّ) و`status` (**عدٌّ فقط** — لا شموع ولا عمق).

## متى يُحكم
مرّةً واحدة: أوّلُ `analyze` بعد **20** وحدةً مؤهَّلة، أو عند `2027-04-14` إن بلغت **10** — وإلّا «لا قياس». قبل ذلك `analyze` يخرج 7.
الشموعُ لقطاتٌ `data/bars/<تاريخ>.json.gz` تُجلب على رنر (TradingView يوميّ مسوّى) — وكلُّ وحدةٍ تقرأ أقدمَ لقطةٍ تغطّيها.

## الخروج
0 تمّ · 1 الحرّاسُ سقطوا · 7 لم يحن · 9 عقدٌ أو بصماتٌ أو سجلٌّ غيرُ سليم.

## الحرّاس والطفرات
`python3 fm_forensics/fsweep/fsweep.py --guards` (FSG1-FSG16 · اصطناعيّة) · `python3 fm_forensics/fsweep/fsweep_mutate.py` (‏38 طفرة · سقطت كلُّها) ·
وقفلُ السويّة `FSW1`.

## ما لا يُحسب
هويّةُ القاعدة وتطابقُ النسبة (رقمُ فيصل مقابل دورتنا) — مقفولةٌ بـ`T-SUPDEF` (العقد §⑨): أرقامُه تُجمع ولا تُقارَن.
