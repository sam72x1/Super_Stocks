# Plan 004: تحصين بوّابة الفلوت M14 ضد القيم غير الرقمية (تمنع انهيار الفرز كلّه)

> **تعليمات المنفِّذ**: اتبع الخطة خطوةً خطوة وشغّل كل أمر تحقّق. عند أي شرط STOP توقّف
> وأبلغ. حدّث صفّ الخطة في `plans/README.md` عند الانتهاء.
>
> **فحص الانحراف (شغّله أولًا)**:
> `git diff --stat a6457bf..HEAD -- Super_stock.py test_bot.py`
>
> 🔴 **تحذير نطاق مُلزِم**: هذه الخطة تلمس دالّةً في **مسار الفرز**. الشرط المطلق أن
> **قرار البوّابة لا يتغيّر لأي مدخل رقمي صالح**. أي تغيير في القرار = حالة STOP.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: MED (داخل مسار الفرز — لكن التغيير حارس نوع فقط، والسلوك للمدخلات الرقمية byte-identical)
- **Depends on**: `plans/001-characterization-baseline.md`
- **Category**: bug
- **Planned at**: commit `a6457bf`, 2026-07-28

## Why this matters

`apply_float_gate` تقارن قيمة الفلوت وتُنسّقها بلا أي حارس نوع، وهي على المسار الحرج:
`scan_market` (بلا `try`) ← `run_daily_watchlist` / `run_weekly_renewal` (بلا `try`)
← `main()` ← معالِج أعلى المستوى ⇒ `sys.exit(1)`.

النتيجة لو رجعت قيمة فلوت غير رقمية (`NaN` من pandas/yfinance، أو نصّ مثل `"12.5M"`):
**التشغيلة كلها تسقط قبل `git_save`** ⇒ تضيع كل حالة اليوم (الستوبات المرصودة · أختام
الدِدوب · الجاهزية) مع الرنر المؤقّت، ولا يصل تقرير.

الدليل أن هذا الصنف واقعي وليس نظريًّا في هذا المستودع: `CLAUDE.md` يوثّق درسًا صريحًا
من تدقيق 2026-07-27 — «**`NaN` ليس `None`** — احتياط `if x is None` لا يلتقط NaN ⇒
**بوّابة تفشل مفتوحةً**». والأهمّ: **المؤلّف نفسه أضاف هذا الحارس بالضبط** في الطبقة
التالية `refloat_gate_recheck` (`Super_stock.py:7115-7119`) ولم يُضِفه في البوّابة الأصلية.

بعد هذه الخطة: قيمة غير رقمية = تُعامَل معاملة «غير متاح» (فائدة الشك — نفس القاعدة
الموثّقة) بدل إسقاط التشغيلة.

## Current state

### الدالّة المعنيّة (`Super_stock.py:7042-7087`) — المقتطف الكامل للجزء الحرج

```python
7054     limit = CONFIG["FLOAT_GATE_MAX"]
7055     kept, rejected = [], []
7056     for r in results:
7057         fl = r.get("float")          # قد يكون مجلوباً مسبقاً من enrich
7058         if fl is None:               # غير مجلوب بعد → نجلبه الآن
7059             try:
7060                 info = yf.Ticker(r["symbol"]).info or {}
7061                 fl = info.get("floatShares")
7062                 r["float"] = fl
7063                 sp = info.get("shortPercentOfFloat")
7064                 if r.get("short_pct") is None and sp:
7065                     r["short_pct"] = round(sp * 100, 1)
7066             except Exception:
7067                 fl = None
7068             time.sleep(0.10)         # احترام حدود الطلبات
7069         if fl is not None and fl >= limit:
7070             # v2.7: لا يُحذف — يُسجّل نقصًا وينزل لقائمة المراقبة B
7071             r.setdefault("soft_fails", []).append("فلوت كبير")
7072             r.setdefault("flags", []).append(
7073                 f"⚠️ فلوت كبير {int(fl):,} (فوق {limit:,})")
7074             rejected.append((r["symbol"], fl))
7075             kept.append(r)
7076         else:
7077             if fl is not None:
7078                 r.setdefault("flags", []).append(
7079                     f"فلوت {int(fl):,} (صغير ✅)")
7080             else:
7081                 r.setdefault("flags", []).append(
7082                     "فلوت غير متاح — مُرِّر بفائدة الشك")
7083             kept.append(r)
7084     if rejected:
7085         names = "، ".join(f"{s}({int(v):,})" for s, v in rejected)
7086         log(f"بوابة الفلوت (M14) نقلت لقائمة B: {len(rejected)}: {names}")
7087     return kept
```

ثلاثة مواضع تنهار على غير-رقم: `7069` (`fl >= limit` مع نصّ ⇒ `TypeError`) ·
`7073`/`7079` (`int(fl)` مع `NaN` ⇒ `ValueError`) · `7085` (نفس الشيء).

### الحارس القائم الذي يجب محاكاته (`Super_stock.py:7112-7119`)

```python
7112         # ⚠️ فاشل-آمن **إلزامي**: هذي الدالّة صارت في مسار الاختيار الحيّ، فاستثناء فيها
7113         # (فلوت بقيمة غير رقمية مثلًا) كان يكسر الفرز اليومي كلّه. أي خلل ⇒ نُبقي السهم
7114         # كما هو = سلوك ما قبل الإصلاح حرفيًّا، ولا نُسقط أحدًا بسبب عطل قراءة.
7115         try:
7116             fl = r.get("float")
7117             big = fl is not None and float(fl) >= limit
7118         except (TypeError, ValueError):
7119             big = False
```

### مسار الانفجار (تأكّد منه بنفسك)

- `Super_stock.py:7449` → `results = apply_float_gate(results)` داخل `scan_market`، بلا `try`.
- `Super_stock.py:11067` → `results, hist = scan_market()` داخل `run_daily_watchlist`، بلا `try`.
- `Super_stock.py:10825` → نفس الشيء داخل `run_weekly_renewal`.
- `Super_stock.py:13717-13729` → المعالِج الأعلى يرسل تلغرام ثم `sys.exit(1)`.
- `git_save` يُنادى فقط في `run_performance_system` **آخر** الدالّة (`13714`).

### قيود مُلزِمة

- `apply_short_gate` (`6991`) فيها نفس الصنف (`srt >= limit` و`int(srt)`) لكن مصادرها
  (`finra_daily_short:3012` تُرجع `int`) أقلّ خطرًا. **قرار النطاق: عالِجها بنفس النمط
  في نفس الخطة** لأنها على نفس المسار الحرج — لكن **بشرط أن يبقى القرار مطابقًا حرفيًّا**.
- `apply_short_gate` مذكورة في أقفال getsource قائمة. **لا تغيّر اسمها ولا توقيعها ولا
  تُدخل أي دالّة جديدة داخل جسمها**؛ استعمل `float()`/`try` مباشرةً.
- **لا رفع `LOGIC_VERSION`**: القرار للمدخلات الصالحة لم يتغيّر، والمستويات/الدخول/الوقف
  لم تُمَسّ.

## Commands you will need

| الغرض | الأمر | المتوقّع |
|-------|-------|----------|
| تثبيت | `pip install -r requirements.txt` | exit 0 |
| بوّابة الاختبار | `python3 test_bot.py; echo "EXIT=$?"` | `EXIT=0` · «0 فشل» |
| فحص صياغة | `python3 -c "import ast;ast.parse(open('Super_stock.py',encoding='utf-8').read())"` | exit 0 |
| بصمة الجذور | انظر الخطوة 4 | بصمات مطابقة عدا الدالّتين المقصودتين |

## Scope

**In scope**:
- `Super_stock.py` — **فقط** جسمَي `apply_float_gate` (7042-7087) و`apply_short_gate`
  (6991-7039).
- `test_bot.py` (تعديل اختبار توصيف واحد من خطة 001 + إضافات)
- `CLAUDE.md` · `HANDOFF.md` (سطر)
- `plans/README.md`

**Out of scope**:
- **قيمة أي عتبة**: `FLOAT_GATE_MAX` · `SHORT_GATE_MAX` · `WATCH_MAX_FAILS`. لا تُمَسّ.
- **منطق القرار**: «كبير ⇒ نقص ولا يُحذف» و«مجهول ⇒ يمرّ بفائدة الشك» قاعدتان محسومتان.
- `refloat_gate_recheck` · `classify_tier` · `rank_key` · `select_top` · `analyze_ticker`
  · `backtest_symbol` — **صفر تعديل**.
- إضافة أي مصدر بيانات جديد (مكان الخطة 003).
- `try/except` حول `scan_market` نفسها (مكان الخطة 005).

## Git workflow

- الفرع: `advisor/004-float-gate-types`
- كوميت واحد، مثال:
  `🛡️ M14/M13: حارس نوع يمنع انهيار الفرز كلّه على فلوت/شورت غير رقمي (القرار byte-identical)`
  + `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- **لا push ولا PR.**

## Steps

### Step 1: التقط بصمة القرار قبل التعديل

اكتب سكربتًا مؤقّتًا في `/tmp` (لا داخل المستودع) يبني قائمة نتائج اصطناعية بقيم فلوت
رقمية متنوّعة — تشمل: `0` · `1` · `limit-1` · `limit` · `limit+1` · `10*limit` · `None`
· `float(limit)` · قيمة `numpy.int64(limit)` — ويطبع لكل سهم `(soft_fails, flags)` بعد
`apply_float_gate`. احفظ المخرج في `/tmp/m14_before.txt`.

كرّر نفس الشيء لـ`apply_short_gate` (مع تعطيل الشبكة بحقن: اضبط
`S.CONFIG["SHORT_GATE_REQUIRED"]=True` وبدّل `S.fintel_short` و`S.finra_daily_short`
بدوالّ مزيّفة تُرجع خريطة ثابتة). احفظ في `/tmp/m13_before.txt`.

**Verify**: الملفان موجودان وغير فارغين.

### Step 2: حصّن `apply_float_gate`

عدّل الجزء الحرج بحيث:

1. تُشتقّ قيمة رقمية آمنة **مرة واحدة** قبل الفرع، بنفس دلالة `refloat_gate_recheck`:

```python
        # 🛡️ حارس نوع (تدقيق 2026-07-28): قيمة الفلوت قد تصل NaN (pandas/yfinance) أو نصًّا.
        # كانت المقارنة/التنسيق يرميان ⇒ **سقوط الفرز كلّه** قبل git_save (تضيع حالة اليوم).
        # درس CLAUDE.md: «NaN ليس None». نفس حارس refloat_gate_recheck حرفيًّا:
        # غير الرقمي = **مجهول** ⇒ يمرّ بفائدة الشك (القاعدة المحسومة)، لا يُرفَض ولا يُسقِط.
        try:
            fl_num = float(fl) if fl is not None else None
            if fl_num is not None and fl_num != fl_num:   # NaN
                fl_num = None
        except (TypeError, ValueError):
            fl_num = None
```

2. استعمل `fl_num` في **الشرط والتنسيق والتسجيل** (`7069` · `7073` · `7077-7079` ·
   `7074` و`7085`)، بحيث `fl_num is None` ⇒ الفرع «غير متاح — مُرِّر بفائدة الشك».
3. **لا تغيّر** ما يُخزَّن في `r["float"]` (يبقى كما جاء من المصدر — طبقات العرض
   والخطة 003 تعتمد عليه).

⚠️ استبدل كل `int(fl)` بـ`int(fl_num)`، وكل `fl >= limit` بـ`fl_num >= limit`،
و`rejected.append((r["symbol"], fl))` بـ`fl_num`.

**Verify**: `python3 -c "import ast;ast.parse(open('Super_stock.py',encoding='utf-8').read())"` → exit 0.

### Step 3: طبّق نفس النمط على `apply_short_gate`

في `Super_stock.py:7013-7035`، بعد استخراج `srt` من الـdict (السطر `7017-7018`)، اشتقّ
`srt_num` بنفس الطريقة واستعمله في `7023` و`7027` و`7032` و`7037`.
**لا تغيّر** ما يُخزَّن في `r["finra_short"]` (السطر `7021-7022`) — العرض والذاكرة يعتمدانه.

**Verify**: `python3 -c "import ast;ast.parse(open('Super_stock.py',encoding='utf-8').read())"` → exit 0.

### Step 4: أثبت أن القرار لم يتغيّر (بصمة قبل/بعد)

أعِد تشغيل سكربتَي الخطوة 1 واحفظ في `/tmp/m14_after.txt` و`/tmp/m13_after.txt`، ثم:

```
diff /tmp/m14_before.txt /tmp/m14_after.txt && echo "M14 IDENTICAL"
diff /tmp/m13_before.txt /tmp/m13_after.txt && echo "M13 IDENTICAL"
```

**الاثنان يجب أن يخرجا `IDENTICAL`.** أي فرق = **STOP فورًا** (غيّرت القرار).

### Step 5: قلب اختبار التوصيف من خطة 001

في `test_bot.py` جِد الاختبار المُعلَّم:
`"🧪 توصيف: apply_float_gate ترمي على فلوت نصّي (يُغيَّر في خطة 004)"`
واقلبه: صار المتوقّع أنها **لا ترمي** وأن السهم يبقى موسومًا «غير متاح».
حدّث اسمه وأزِل تعليق التحذير `# ⚠️ خطة 004 ستقلب هذا التوقّع...`.

> لو لم تجد الاختبار (خطة 001 لم تُنفَّذ) ⇒ **STOP**: نفّذ 001 أولًا.

**Verify**: `grep -n "يُغيَّر في خطة 004" test_bot.py` → لا مطابقة.

### Step 6: اختبارات جديدة

أضِف تحت `# ===== خطة 004: حارس نوع بوّابتَي M13/M14 =====`:

1. `float("nan")` كفلوت ⇒ لا يرمي · لا «فلوت كبير» في `soft_fails` · flag «غير متاح».
2. `"12.5M"` (نصّ غير قابل للتحويل) ⇒ نفس النتيجة، لا رمي.
3. `"60000000"` (نصّ رقمي فوق الحدّ) ⇒ يُعامَل **رقمًا** ⇒ «فلوت كبير» يُضاف.
   (هذا يوثّق قرارًا صريحًا: النصّ الرقمي يُقبَل — اذكره في وصف الاختبار.)
4. `numpy.float64(limit)` ⇒ «فلوت كبير» (سلوك اليوم محفوظ).
5. نفس (1) و(2) على `apply_short_gate` بشورت `float("nan")` ونصّ.
6. **قفل انحدار حاسم**: `apply_float_gate` على قائمة فيها سهم بقيمة سامّة **وسهم سليم
   بعده** ⇒ الاثنان يعودان في `kept` (السهم السامّ لا يمنع معالجة ما بعده).

**Verify**: `python3 test_bot.py; echo "EXIT=$?"` → `EXIT=0` · «0 فشل» · العدد زاد ≥6.

### Step 7: اختبار الطفرة (إلزامي)

1. أرجِع `fl >= limit` مكان `fl_num >= limit` → يجب أن يسقط اختبار (2). أرجِع الإصلاح.
2. اجعل `fl_num = None` دائمًا → يجب أن تسقط اختبارات (3) و(4) وبصمة الخطوة 4. أرجِعه.
3. اجعل الحارس يلتقط `Exception` بدل `(TypeError, ValueError)` وتأكّد أن الاختبارات
   ما زالت تمرّ — **ثم أرجِع الضيّق**: التقاط `Exception` العريض ممنوع هنا (يخفي عيوبًا
   أخرى داخل الحلقة).

احكم بـ`python3 test_bot.py; echo "EXIT=$?"` ⇒ `EXIT` غير صفري **و** «N فشل» > 0.

**Verify**: بعد الإرجاع → `EXIT=0` · «0 فشل» وبصمة الخطوة 4 ما زالت `IDENTICAL`.

### Step 8: التوثيق

أضِف في `CLAUDE.md` (قرب فقرة M14/إعادة تقييم M14) وفي `HANDOFF.md` سطرًا:
أن حارس النوع أُضيف لبوّابتَي M13/M14، وأن **القرار للمدخلات الرقمية byte-identical**
(مُثبَت ببصمة قبل/بعد)، وأن غير الرقمي = مجهول يمرّ بفائدة الشك، وأن السبب أن انهيار
البوّابة كان يُسقط التشغيلة **قبل** `git_save`.

## Test plan

- **الملف**: `test_bot.py` (تعديل اختبار واحد + إضافة 6).
- **النمط المرجعي**: كتلة التوصيف من خطة 001، ونمط `check(...)` القائم.
- **التغطية**: NaN · نصّ غير رقمي · نصّ رقمي · نوع numpy · نفس الشيء على M13 · قفل
  «سهم سامّ لا يمنع من بعده».
- **التحقّق**: `python3 test_bot.py` → exit 0 · «0 فشل» + بصمة قبل/بعد `IDENTICAL`.

## Done criteria

- [ ] `python3 test_bot.py; echo "EXIT=$?"` → `EXIT=0` · «0 فشل»
- [ ] `diff /tmp/m14_before.txt /tmp/m14_after.txt` فارغ · نفس الشيء لـ M13
- [ ] `grep -n "int(fl)" Super_stock.py` → لا مطابقة داخل `apply_float_gate`
- [ ] `grep -n "except (TypeError, ValueError)" Super_stock.py` → ≥3 مطابقات
      (`refloat_gate_recheck` + البوّابتان)
- [ ] `python3 -c "import Super_stock as S,inspect;src=inspect.getsource(S.apply_float_gate);assert 'except Exception' not in src"` → exit 0
- [ ] `git diff a6457bf..HEAD -- Super_stock.py` يمسّ **فقط** جسمَي `apply_float_gate`
      و`apply_short_gate` (راجع الـdiff سطرًا سطرًا وأكّده في رسالة الكوميت)
- [ ] `LOGIC_VERSION` **لم يتغيّر**
- [ ] `git status --porcelain weekly_watchlist.json alerts_history.json company_cache.json` **فارغ**
- [ ] الطفرات الثلاث أُجريت وأُرجعت (موثّق في الكوميت)
- [ ] صفّ 004 في `plans/README.md` محدَّث

## STOP conditions

- بصمة الخطوة 4 ليست متطابقة ⇒ **توقّف فورًا**؛ غيّرتَ قرار بوّابة.
- اختبار التوصيف من خطة 001 غير موجود ⇒ نفّذ 001 أولًا.
- وجدت نفسك تعدّل عتبةً، أو `classify_tier`، أو أي جذر اختيار.
- وجدت نفسك تفكّر برفع `LOGIC_VERSION` ⇒ معناه أنك خرجت عن النطاق.
- كسر تعديلك أي قفل getsource قائم في `test_bot.py`.
- فكّرت في تشغيل أي workflow حيّ — **ممنوع**.

## Maintenance notes

- المبدأ المستخلَص (اذكره في وصف الـPR للمالك): **كل قيمة قادمة من مصدر خارجي وتُقارَن
  أو تُنسَّق على مسار الفرز تحتاج حارس نوع**؛ غير الرقمي = مجهول لا رفض ولا انهيار.
- المراجِع يدقّق: بصمة قبل/بعد · أن `r["float"]`/`r["finra_short"]` المخزَّنين لم يتغيّرا
  · أن الالتقاط ضيّق (`TypeError, ValueError`) لا `Exception`.
- تفاعل: الخطة 003 تُدخل قيمًا جديدة لحقل `float` من `_yahoo_float`؛ هذا الحارس يغطّيها.
- **مؤجَّل عمدًا**: تحصين مشابه لبقيّة الحقول العددية القادمة من الشبكة
  (`short_pct` · `borrow_fee` · `shares_available`). هي في طبقات عرض محروسة أصلًا،
  فلا تُخلط بهذه الخطة.
