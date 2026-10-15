# `T-ANCHOR-AGE` — هل رقمُ الدعم عندنا قاعُ الخمس جلسات أم قاعٌ قديم؟ (2026-10-15 · بحثٌ فقط)

> برومبتُ المالك بإذنه لهذا المحور وحده · **تشخيصٌ وقياسٌ لا شحن** · لا جذرَ ولا عتبةَ ولا تلغرام · H6 ساري والمِرساةُ مجمَّدة.

| الملفّ | ما هو |
|---|---|
| `ANCHOR_AGE_DEFS.md` | التعريفاتُ والحكمُ **مكتوبةٌ قبل أيّ رقمٍ من الشموع** (`ca27e02d1`) |
| `ANCHOR_AGE_RESULT.md` | **النتيجة** — الحكمُ في أوّل سطر · الخمسة · ANPA وقياسُ 1.740 · حدودُ الصدق · أصغرُ إصلاحٍ مقترَح بلا تنفيذ |
| `ANCHOR_AGE_TABLES.md` | الجداولُ كاملةً — **مولَّدةٌ** من `data/anchor_result.json` (لا تُحرَّر باليد) |
| `anchor_extract.py` | لقطاتُ `weekly_watchlist.json` و`near_watch.json` و`reject_log.json` من تاريخ git ⟵ `data/snapshots.json.gz` · و`--symbols` ⟵ `data/fetch_symbols.json` |
| `anchor_fetch.py` | الشموعُ اليوميّة من TradingView (`adjustment=splits`) بدالّة الإنتاج `Super_stock.tv_download` ⟵ `data/anchor_bars.json.gz` — شُغِّل على رنر بـworkflow مؤقّتٍ على فرعه (تشغيلة `38660715966`) **وحُذف قبل الدمج** |
| `anchor_age.py` | القياس: `pivot_stability` · `tested_level` · الظلّان · الخمسة · ANPA ⟵ المخرَجان · `--check` يعيدهما بايتًا ويتحقّق أن وثيقةَ النتيجة تحمل أرقامَ الـJSON · `--guards` AG1-AG15 |
| `anchor_mutate.py` | جولةُ الطفرات: 22 طفرةً تُسقط كلٌّ قفلَها المسمّى (بلا بايتكود) |

```bash
python3 fm_forensics/anchor_age/anchor_age.py --guards     # 15/15
python3 fm_forensics/anchor_age/anchor_age.py --check      # المخرَجاتُ بايتًا ‏+ أرقامُ الوثيقة
python3 fm_forensics/anchor_age/anchor_mutate.py           # 22/22
```

🔒 **مُغلَقٌ مُنفَّذًا** («اقفل عمر المرساة» 2026-10-15 · `ANCHOR_AGE_RESULT.md §⑫`): البناءُ و`anchor_extract.py` و`anchor_fetch.py`
تخرج 8 بلا `ANCHOR_AGE_REOPEN=1` حرفيًّا · و`--check`/`--guards` مفتوحان · `AAC1` · `AG15`.

🔴 **صورُ ANPA لا تُدفَع** (قِيست في مجلّد الجلسة) · والقياسُ وصفٌ لا يقيس ربحًا · وقفلُ السويّة `AAG1`.
