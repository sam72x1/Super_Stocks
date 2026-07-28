# Plan 005: حارس استثناء لكل رمز في كتلة إثراء `scan_market`

> **تعليمات المنفِّذ**: اتبع الخطة خطوةً خطوة وشغّل كل أمر تحقّق. عند أي شرط STOP توقّف
> وأبلغ. حدّث صفّ الخطة في `plans/README.md` عند الانتهاء.
>
> **فحص الانحراف (شغّله أولًا)**:
> `git diff --stat a6457bf..HEAD -- Super_stock.py test_bot.py`
>
> 🔴 **تحذير نطاق مُلزِم**: التعديل داخل `scan_market`. **لا تلمس `analyze_ticker` ولا
> `rank_key` ولا `select_top` ولا `classify_tier` ولا أي عتبة.** الحقول المُثراة كلها
> **عرض/تفسير** بقرار موثّق — إضافتها أو غيابها لا يجوز أن يغيّر العضوية.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: MED (داخل `scan_market` — لكن التعديل حارس فشل فقط، والعضوية محكومة بقفل بصمة)
- **Depends on**: `plans/001-characterization-baseline.md`
- **Category**: bug
- **Planned at**: commit `a6457bf`, 2026-07-28

## Why this matters

بعد أن يجتاز سهمٌ `analyze_ticker`، يُثري `scan_market` نتيجته بثمانية حقول
عرض/تفسير (`Super_stock.py:7400-7410`). **الكتلة كلها بلا `try/except`**: استثناء واحد
على رمز واحد يخرج من `scan_market` → `run_daily_watchlist`/`run_weekly_renewal` (بلا
`try`) → `main()` → `sys.exit(1)`، فتسقط التشغيلة **قبل `git_save`** وتضيع حالة اليوم
(الستوبات المرصودة · أختام الدِدوب · الجاهزية) ولا يصل تقرير.

الدليل أن هذا خلل لا اختيار: **نفس النداءات محاطة بـ`try/except` في
`update_watchlist_status` (`Super_stock.py:7785-7802`)** — التطبيق غير متّسق، والأخطر أن
الجهة غير المحروسة هي التي تُسقط التشغيلة كاملةً.

كذلك `full_stoch` (`Super_stock.py:676-686`) **بلا أي حماية داخلية**، وهي أول ما يُنفَّذ
في السطر 7401-7402 (قبل `fsto_oscillation` الفاشلة-آمنة) — فحمايتها تأتي من النداء لا من نفسها.

بعد هذه الخطة: رمز واحد معطوب = يُسجَّل ويُتخطّى إثراؤه، **والتشغيلة تكمل**.

## Current state

### الكتلة غير المحروسة (`Super_stock.py:7388-7411`)

```python
7388     for sym, df in history.items():
7389         r = analyze_ticker(sym, df)
7390         if r:
7391             # ① (إصلاح تدقيق 2026-07-12): تاريخ **شمعة الترشيح الفعلية** ...
7396             try:
7397                 r["ref_bar"] = df.index[-1].date().isoformat()
7398             except Exception:
7399                 r["ref_bar"] = None
7400             r["behav"] = behavior_rise_profile(df)   # 🧬 بصمة طريقة الارتفاع (حيّ، عرض فقط)
7401             r["fsto_osc"] = fsto_oscillation(        # 🌀 قوة تذبذب FSTO (حيّ، عرض فقط)
7402                 full_stoch(df["High"], df["Low"], df["Close"])[0])
7403             r["klinger"] = klinger_state(            # 📊 كلنجر (حجم — حيّ، عرض فقط)
7404                 df["High"], df["Low"], df["Close"], df["Volume"])
7405             r["cci"] = cci_state(                    # 📉 CCI(14) (حيّ، عرض فقط)
7406                 df["High"], df["Low"], df["Close"])
7407             r["bottom_test"] = bottom_test_state(df)  # 🔁 «القاع 2» (عرض فقط)
7408             r["pump_scar"] = group_pump_scar(df)     # 🕵️ N1 (حيّ، عرض فقط)
7409             r["trendline"] = descending_trendline(df, r["price"])  # §10 (حيّ، عرض فقط)
7410             r["interp"] = build_interpretation(r)    # 🧭 طبقة التفسير/القرار (عرض فقط)
7411             results.append(r)
```

### النمط المرجعي المحروس — انسخه (`Super_stock.py:7785-7802`)

```python
7785         try:
7786             _bh_new = behavior_rise_profile(df)
7787             if _bh_new.get("score") is not None:
7788                 s["behav"] = _bh_new
7789             s["fsto_osc"] = fsto_oscillation(...)
...
7800             s["pump_scar"] = group_pump_scar(df)   # 🕵️ N1 يتجدّد يوميًا (عرض فقط)
7801         except Exception:
7802             pass
```

لاحظ أن `update_watchlist_status` يفصل `interp` في `try` **مستقلّ** (`7806-7811`) بحارس
«لا-يمسح» — استرشد به.

### حصانة الدوال (مفحوصة آليًّا — لا تفترض غيرها)

| الدالّة | جسمها كلّه داخل try؟ |
|---------|----------------------|
| `full_stoch` (676) | **لا · ولا حتى try جزئي** |
| `fsto_oscillation` (689) | نعم |
| `klinger_state` (750) | نعم |
| `cci_state` (787) | نعم |
| `behavior_rise_profile` (1529) | نعم |
| `group_pump_scar` (1606) | نعم |
| `descending_trendline` (1691) | نعم |
| `bottom_test_state` (5139) | نعم |
| `build_interpretation` (6043) | **لا** (فيها try جزئية فقط) |

⇒ الخطران الحقيقيان: `full_stoch` و`build_interpretation`.

### مسار الانفجار

`7449` (`apply_float_gate` داخل `scan_market`) ← `11067`/`10825` (بلا `try`) ←
`13331-13339` (`main`) ← `13717-13729` (`sys.exit(1)`). و`git_save` في `13714` داخل
`run_performance_system` **آخر** الدالّة ⇒ لا يُنفَّذ.

### قيد صون العضوية

`CLAUDE.md` ينصّ أن `behav`/`fsto_osc`/`interp` وغيرها **خارج `rank_key`/`select_top`**،
وأن هناك أقفال getsource تحرس ذلك. الخطة تُبقيها كما هي: الحقول المفقودة تصير `None`
(نفس ما يحدث لسجلّ قديم بلا الحقول) ولا تغيّر ترتيبًا ولا عضوية.

## Commands you will need

| الغرض | الأمر | المتوقّع |
|-------|-------|----------|
| تثبيت | `pip install -r requirements.txt` | exit 0 |
| بوّابة الاختبار | `python3 test_bot.py; echo "EXIT=$?"` | `EXIT=0` · «0 فشل» |
| فحص صياغة | `python3 -c "import ast;ast.parse(open('Super_stock.py',encoding='utf-8').read())"` | exit 0 |

## Scope

**In scope**:
- `Super_stock.py` — **فقط** الكتلة `7400-7411` داخل `scan_market`.
- `test_bot.py`
- `CLAUDE.md` · `HANDOFF.md` (سطر)
- `plans/README.md`

**Out of scope**:
- `analyze_ticker` · `rank_key` · `select_top` · `classify_tier` · `entry_status` ·
  `backtest_symbol` · `apply_short_gate` · `apply_float_gate` — **صفر تعديل**.
- الدوال الثماني نفسها (`behavior_rise_profile` … `build_interpretation`) — **لا تُعدَّل
  داخليًّا**؛ الحماية عند نقطة النداء. (تحصين `full_stoch` داخليًّا مؤجَّل — انظر
  «Maintenance notes».)
- `update_watchlist_status` — محروس أصلًا.
- إضافة `try` حول `scan_market` نفسها في `run_daily_watchlist` — قد يخفي أعطالًا حقيقية
  في التحميل/البوّابات؛ **الحماية عند المصدر أدقّ**.
- أي رفع لـ`LOGIC_VERSION`.

## Git workflow

- الفرع: `advisor/005-scan-market-guard`
- كوميت واحد، مثال:
  `🛡️ scan_market: استثناء رمز واحد في كتلة الإثراء كان يُسقط الفرز كلّه قبل git_save`
  + `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- **لا push ولا PR.**

## Steps

### Step 1: لفّ الكتلة بحارس لكل رمز

عدّل `Super_stock.py:7400-7410` بحيث:

1. الحقول الثمانية داخل `try` واحد؛ عند الاستثناء: **سجّل** بـ`log(...)` (لا `pass`
   صامتة — درس `CLAUDE.md`: «كل مسارات الفشل الصامتة») ثم **تابع** إضافة `r` للنتائج.
2. `r["interp"]` في `try` **منفصل** بعده (كما في `update_watchlist_status:7806-7811`)،
   لأن `build_interpretation` تقرأ الحقول السابقة فقد تسقط وحدها.
3. **`results.append(r)` يبقى خارج كل `try`** — السهم يدخل النتائج دائمًا ما دام
   `analyze_ticker` قبله بنجاح. هذا حاسم لصون العضوية.
4. الحقول التي لم تُملأ تبقى غائبة (`r.get(...)` يُرجع `None` في كل المستهلكين) —
   **لا تضع قيمًا افتراضية مُختلَقة**.

الشكل المطلوب:

```python
            # 🛡️ حارس لكل رمز (تدقيق 2026-07-28): هذي **حقول عرض/تفسير** لا تدخل
            # rank_key/select_top، لكنها كانت بلا حارس — فاستثناء على رمز واحد يخرج من
            # scan_market ⇒ يسقط run_daily_watchlist/run_weekly_renewal ⇒ **التشغيلة
            # كلّها تموت قبل git_save** (تضيع الستوبات وأختام الدِدوب والجاهزية بلا تقرير).
            # (`update_watchlist_status:7785-7802` كانت محروسة والفرز لا — تطبيق غير متّسق.)
            # فاشل-آمن: الحقل الغائب = None عند كل المستهلكين = سلوك سجلّ قديم بلا الحقل.
            try:
                r["behav"] = behavior_rise_profile(df)
                ...
                r["trendline"] = descending_trendline(df, r["price"])
            except Exception as _e:
                log(f"⚠️ إثراء عرض {sym}: {type(_e).__name__}: {_e} — تُخطّي الحقول، "
                    "السهم يبقى في نتائج الفرز (العضوية غير متأثّرة).")
            try:
                r["interp"] = build_interpretation(r)
            except Exception as _e:
                log(f"⚠️ تفسير {sym}: {type(_e).__name__}: {_e}")
            results.append(r)
```

**Verify**: `python3 -c "import ast;ast.parse(open('Super_stock.py',encoding='utf-8').read())"` → exit 0.

### Step 2: قلب اختبار التوصيف من خطة 001

🔴 **مقاس تجريبيًّا** (طفرة M4 وقت تنفيذ خطة 001 = محاكاة هذا الإصلاح): الإصلاح
يُسقط **اختبارًا واحدًا بالضبط**:

```
🧪 توصيف·الفرز: استثناء في كتلة الإثراء يُسقط scan_market كلّها (يُغيَّر في خطة 005)
```

اقلبه: المتوقّع أن `scan_market()` **لا ترمي**، وأن السهم يبقى في النتائج **مع
`interp` غائبًا** (`_c4_ok[0].get("interp") is None`). أزِل تعليق
`# ⚠️⚠️ خطة 005 ستقلب...` واحذف «يُغيَّر في خطة 005» من الاسم.

⚠️ الاختبار المجاور `🧪 توصيف·الفرز: المسار السليم يملأ حقول الإثراء (behav/fsto/interp)`
**يجب أن يبقى أخضر بلا تعديل** — لو سقط فمعناه أن لفّك ابتلع المسار السليم أيضًا.

> بنية الاختبار جاهزة في `test_bot.py` (كتلة `_c4_*`): تضبط `S.MODE="TEST"` وتحقن
> `download_history`/`fintel_short`/`finra_daily_short` وتضع `S.yf=None`.
> لو كانت خطة 001 قد وسمت هذه الخطوة `BLOCKED`، فاكتبه بنفس النمط.

**Verify**: `grep -n "يُغيَّر في خطة 005" test_bot.py` → لا مطابقة.

### Step 3: قفل العضوية (الأهمّ)

أضِف اختبارًا يثبت أن **مجموعة الرموز الناتجة لا تتغيّر** بسقوط الإثراء:

- شغّل `scan_market` مرّتين على نفس البيانات المزيّفة: مرّة والدوال سليمة، ومرّة
  و`S.build_interpretation` مبدَّلة بدالّة ترمي دائمًا.
- أكّد: `set(rows_ok) == set(rows_broken)` على `symbol`، **و** أن ترتيب الرموز متطابق
  (`[r["symbol"] for r in ...]` متساويان) — لأن `rank_key` يقرأ `readiness`/`score`/`rr`
  وهي من `analyze_ticker` لا من كتلة الإثراء.
- أكّد أن `rows_broken[0].get("interp") is None`.

**Verify**: `python3 test_bot.py; echo "EXIT=$?"` → `EXIT=0` · «0 فشل».

### Step 4: اختبارات إضافية

1. سقوط `full_stoch` (بدّلها بدالّة ترمي) ⇒ `scan_market` تكمل و`fsto_osc` غائب،
   **وبقيّة حقول الإثراء بعده غائبة أيضًا** (نفس `try`) — وثّق ذلك صراحةً في وصف
   الاختبار حتى لا يُقرأ لاحقًا مفاجأةً.
2. سقوط `descending_trendline` ⇒ نفس السلوك.
3. كل الدوال سليمة ⇒ **كل** الحقول الثمانية موجودة (قفل ضد لفّ زائد يبتلع الصحيح).
4. رسالة `log` تُطبع عند السقوط (التقط `stdout` أو بدّل `S.log` بجامع) — قفل ضد الصمت.

**Verify**: `python3 test_bot.py; echo "EXIT=$?"` → `EXIT=0` · «0 فشل» · العدد زاد ≥5.

### Step 5: اختبار الطفرة (إلزامي)

1. أزِل الـ`try` حول الكتلة → يجب أن تسقط اختبارات (1) و(2) والقفل في الخطوة 3.
   أرجِعه.
2. انقل `results.append(r)` **داخل** الـ`try` → يجب أن يسقط قفل العضوية (الخطوة 3).
   أرجِعه. **هذي أهمّ طفرة**: تُثبت أن القفل يحرس العضوية فعلًا.
3. استبدل `log(...)` بـ`pass` → يجب أن يسقط اختبار (4). أرجِعه.

احكم بـ`python3 test_bot.py; echo "EXIT=$?"` ⇒ `EXIT` غير صفري **و** «N فشل» > 0.

**Verify**: بعد الإرجاع → `EXIT=0` · «0 فشل».

### Step 6: التوثيق

سطر في `CLAUDE.md` و`HANDOFF.md`: أن كتلة الإثراء في `scan_market` صارت محروسة لكل
رمز، وأن **العضوية والترتيب byte-identical** (مقفولان باختبار)، وأن السبب أن الكتلة
كانت الفارق الوحيد غير المحروس مقابل `update_watchlist_status`.

## Test plan

- **الملف**: `test_bot.py` (قلب اختبار + إضافة 5).
- **النمط المرجعي**: كتلة التوصيف من خطة 001، ونمط تبديل دوالّ الوحدة القائم في `test_bot.py`.
- **التغطية**: قلب التوصيف · قفل العضوية والترتيب · سقوط `full_stoch` ·
  سقوط `descending_trendline` · المسار السليم كامل الحقول · وجود سطر السجلّ.
- **التحقّق**: `python3 test_bot.py` → exit 0 · «0 فشل».

## Done criteria

- [ ] `python3 test_bot.py; echo "EXIT=$?"` → `EXIT=0` · «0 فشل»
- [ ] `python3 -c "import Super_stock as S,inspect;src=inspect.getsource(S.scan_market);assert src.count('try:')>=4"` → exit 0
- [ ] `git diff a6457bf..HEAD -- Super_stock.py` يمسّ **فقط** أسطرًا داخل `scan_market`
      (راجع الـdiff سطرًا سطرًا وأكّده في الكوميت)
- [ ] `LOGIC_VERSION` **لم يتغيّر**
- [ ] `git status --porcelain weekly_watchlist.json alerts_history.json company_cache.json` **فارغ**
- [ ] الطفرات الثلاث أُجريت وأُرجعت (موثّق في الكوميت)
- [ ] صفّ 005 في `plans/README.md` محدَّث

## STOP conditions

- قفل العضوية في الخطوة 3 لم ينجح ⇒ توقّف؛ التغيير يمسّ الاختيار.
- وجدت نفسك تعدّل أي دالّة من الثماني، أو أي جذر اختيار.
- وجدت نفسك تضع قيمًا افتراضية للحقول الغائبة (`0` · `{}` · `"—"`) — ممنوع؛ الغياب
  = `None` = سلوك السجلّ القديم.
- فكّرت في لفّ `scan_market` نفسها بـ`try` في `run_daily_watchlist` — خارج النطاق.
- فكّرت في تشغيل أي workflow حيّ — **ممنوع**.

## Maintenance notes

- أي حقل عرض/تفسير جديد يُضاف مستقبلًا في هذه الكتلة **يجب أن يدخل داخل نفس الـ`try`**.
  اذكر ذلك في التعليق فوق الكتلة.
- المراجِع يدقّق: أن `results.append(r)` خارج الـ`try` · أن الالتقاط يسجّل ولا يصمت ·
  أن قفل العضوية والترتيب موجود.
- **مؤجَّل عمدًا**: تحصين `full_stoch` داخليًّا (`Super_stock.py:676-686`) — لها مستهلكون
  آخرون (`hand_check.py` · `update_watchlist_status`) وتغييرها يستحقّ خطة مستقلّة
  بتوصيف لكل مستهلك.
- مؤجَّل عمدًا: حراسة مماثلة داخل `scan_pullback` (`7343-7362`) — محروسة أصلًا بـ`try`
  حول `analyze_ticker`، لكنها لا تُثري، فلا خطر مطابق.
