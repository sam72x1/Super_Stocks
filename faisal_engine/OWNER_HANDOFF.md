# OWNER_HANDOFF — تسليمُ المالك (2026-10-09)

## كيف تشغّلها (قراءةٌ فقط · بلا أسرار · بلا شبكة)
```bash
cd Super_Stocks
FAISAL_ONLY=1 python3 faisal_engine/engine.py SXTC --asof 2026-09-10      # قراءةُ رمزٍ عند تاريخ (JSON كامل · الشموعُ قبل التاريخ حصرًا)
FAISAL_ONLY=1 python3 faisal_engine/replay.py                             # الإعادةُ كاملةً ⟵ faisal_engine/out/ (≈2 دقيقة)
python3 faisal_engine/ledger.py && python3 faisal_engine/source_audit.py && python3 faisal_engine/docs.py   # السجلُّ والتدقيقُ والوثائق
python3 test_bot.py        # السويّةُ كاملةً (أقفال FE0-FE9 قبل LEAK0)
```
- المدخلات: الشموعُ المجمَّدة `fm_forensics/data/bars_2026-10-08.json.gz` · SEC `sec_2026-10-08.json.gz` · الخطُّ الزمنيّ `phase3/FAISAL_TIMELINE.csv` · ضوابطُ المرحلة 4.
- لرمزٍ خارج الملفّ المجمَّد: `engine.evaluate(symbol, rows, asof, context)` تقبل أيَّ صفوف [date,o,h,l,c,v] وسياقًا مؤرَّخًا — والغائبُ None = UNKNOWN.

## ما تغيّر في الإنتاج
- **لا شيء.** الملفّاتُ الجديدة كلُّها تحت `faisal_engine/` ‏+ أقفالٌ في `test_bot.py` ‏+ استثناءُ `.gitignore` لمخرجات CSV. لا workflow · لا كرون · لا تلغرام · لا V4 · لا H6.

## الحالة
- **B. IMPLEMENTED, BUT PERFORMANCE NOT ESTABLISHED** — والتفصيلُ في `VALIDATION_REPORT.md` و`BASELINE_COMPARISON.md` و`KNOWN_FAILURES.md`.

## ما يلزمك أنت (لا توصيةَ بمرحلةٍ جديدة)
- لا شيء لتشغيل الأداة. إن أردتَ قياسَ إنذار الفرز الكاذب على الكون كلِّه أو تحقيقَ الصلاحيّة أماميًّا فذلك قرارُك (عقدُ H6 يجمع المتاحَ أصلًا حتى 2027-04-09).
