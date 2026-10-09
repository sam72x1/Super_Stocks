# 🧭 FAISAL RESEARCH ENGINE (`faisal_engine/`) — محرّكُ بحثٍ معزول (2026-10-09)

**قراءةٌ فقط · لا إنتاج · لا تلغرام · لا V4 يُعدَّل · لا H6 يُمَسّ.** يُعيد بناءَ عمليّة فيصل (SCREEN ⟵ FOCUS ⟵ WATCH ⟵ READY ⟵ TRIGGER) فوق
نواة V4 المجمَّدة والفارز الإنتاجيّ المجمَّد بلا جدار اللمستين، بقراءةٍ آمنةٍ من النظر للأمام وصلاحيّةٍ مؤرَّخة، وUNKNOWN لكلّ ما لا مصدرَ له.

| الملفّ | الدور |
|---|---|
| `engine.py` | القلب: `evaluate(symbol, rows, asof, context, label, screen)` ⟵ سجلٌّ قابلٌ للتفسير (§8) · CLI: `engine.py SYM --asof DATE` |
| `data.py` | مِقبسُ الشموع/التقسيمات/SEC المجمَّدة (2026-10-08) · السياقُ المؤرَّخ |
| `replay.py` | الإعادةُ التاريخيّة وفق `REPLAY_PROTOCOL.md` ⟵ `out/` (units · controls · lead_time · summary.json) |
| `ledger.py` | `FAISAL_RULE_LEDGER.json/.csv` — القواعدُ بأصناف الدليل الخمسة ومعرّفاتِ الصور |
| `source_audit.py` | `out/source_audit.json` — مصالحةُ المدوّنة والمصادر |
| `docs.py` | يبني الوثائق السبع من JSON/CSV (لا رقمَ باليد) |
| `SOURCE_RECOVERY_AUDIT.md` · `FAISAL_METHOD_SPEC.md` · `HISTORICAL_REPLAY_REPORT.md` · `BASELINE_COMPARISON.md` · `KNOWN_FAILURES.md` · `VALIDATION_REPORT.md` · `OWNER_HANDOFF.md` | المخرجاتُ المطلوبة |

## التشغيل
```bash
FAISAL_ONLY=1 python3 faisal_engine/engine.py DKI --asof 2026-09-14
FAISAL_ONLY=1 python3 faisal_engine/replay.py          # ≈2 دقيقة · يكتب faisal_engine/out/ وحدَه
python3 faisal_engine/ledger.py && python3 faisal_engine/source_audit.py && python3 faisal_engine/docs.py
python3 test_bot.py                                     # أقفال FE0-FE9 (قبل LEAK0)
```
المراحل: `INSUFFICIENT_DATA` · `REJECTED` (أوّلُ بوّابةٍ ساقطة مسمّاة) · `FOCUS` · `WATCH` · `READY` · `TRIGGER` · `HOLD` (مانعُ صلاحيّةٍ مؤرَّخ).
الوسوم: `HISTORICAL` · `EXPLORATORY` · `LIVE`. الحكمُ الحاليّ: **IMPLEMENTED, BUT PERFORMANCE NOT ESTABLISHED** (`VALIDATION_REPORT.md`).
