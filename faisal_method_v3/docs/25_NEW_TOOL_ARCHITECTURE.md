# 25 · معماريّةُ الأداة الجديدة (§25) — `faisal_tool.py` · FAISAL-V3 1.0 (2026-10-02)

```
البيانات (TradingView يوميّ ‏+ 30 دقيقة · fetch_daily / fetch_30m)
  ⟵ السياق (production_context: قراءةُ الفارز الإنتاجيّ analyze_ticker للرمز — عرضٌ فقط)
  ⟵ البنية (confirmed_swings ⟵ label_structure)
  ⟵ النموذج (find_w: قاعان · عنق · جاء من فوق)
  ⟵ الحالة (w_state: NO_W · AT_SUPPORT2 · UNSAFE_MIDDLE · BREAKOUT · RETEST_HOLD · FAILED_BREAKOUT · INVALIDATED)
  ⟵ التأكيد (intraday_hold على 30 دقيقة · R-W-05)
  ⟵ الدخول (A الدعم الثاني/السحب · B أوّل اختراق) ⟵ الإبطال (stops)
  ⟵ الأهداف (targets: سلّمُ فيصل · ‏+100% · المقيسةُ للمقارنة)
  ⟵ المخاطرة (rr) ⟵ قائمةُ الفحص (checks: PASS/FAIL/NA بالقاعدة ووسمها)
  ⟵ المخرَج (render_text عربيّ · JSON · PNG)
```
- **نقيّةٌ في قلبها** (`analyze_arrays`) — مصفوفاتٌ تدخل وتقريرٌ يخرج ⟵ قابلةٌ للاختبار بلا شبكة (FV1-FV5).
- **قراءةٌ فقط:** لا حالةَ إنتاج · وتلغرام فقط داخل `if send:` (FV7) والـworkflow يمرّر السرَّ حين `send=1` وحدَه (FV6).
