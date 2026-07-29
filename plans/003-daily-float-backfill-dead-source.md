# Plan 003: ردم الفلوت اليومي يستعمل مصدرًا ميتًا — استبدله بالمُثبَت `_yahoo_float`

> **تعليمات المنفِّذ**: اتبع الخطة خطوةً خطوة، وشغّل كل أمر تحقّق. عند أي شرط STOP توقّف
> وأبلغ. حدّث صفّ الخطة في `plans/README.md` عند الانتهاء.
>
> **فحص الانحراف (شغّله أولًا)**:
> `git diff --stat a6457bf..HEAD -- Super_stock.py test_bot.py`

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW (طبقة إثراء/عرض — خارج بوّابة M14 التي تُطبَّق أثناء الفرز)
- **Depends on**: `plans/001-characterization-baseline.md`
- **Category**: bug
- **Planned at**: commit `a6457bf`, 2026-07-28

## Why this matters

في 2026-07-28 أُضيفت `refloat_gate_recheck` لإصلاح مسكة حيّة: سهم PONY بفلوت 277 مليونًا
(‏5.5× الحدّ) بقي في القائمة موسومًا «فلوت غير متاح» لأن M14 تُطبَّق **قبل** الإثراء. الإصلاح
يُعيد الحكم **بعد** أن تصير القيمة متاحة — لكنه يعتمد على أن قناةً ما تملأ الفلوت فعلًا.

قناة الردم اليومي (`Super_stock.py:11172-11178`) تنادي `ce_float_info`، وهي **ميتة منذ
2026-07-24**: نفس الملف يوثّق ذلك بعد 80 سطرًا (`11252-11259`) ويشرح أن صفحة
ChartExchange صارت قِشرة JS وأن البديل المُثبَت هو `_yahoo_float`. فالردم اليومي **لا
يملأ شيئًا أبدًا**، والأسهم التي خُنق ياهو عنها لحظة البوّابة يبقى فلوتها `None` إلى
الأبد ⇒ **إصلاح PONY لا يستطيع أن يعمل عليها**.

بالإضافة: كل نداء ميت يستهلك مهلة 8 ثوانٍ ويحرق قاطع الدائرة `_flt_fails` داخل `enrich`.

**لا يمسّ الفرز**: `apply_float_gate` تعمل أثناء الفرز قبل الإثراء، وهذه الخطة لا تلمسها.

## Current state

### نقطة العطل — الردم اليومي (`Super_stock.py:11169-11178`)

```python
11169        # 🏢 ردم الفلوت المجهول من ChartExchange (اقتراح المستخدم 2026-07-10):
11170        # الأسهم القديمة التي غاب فلوتها (ياهو مخنوق) تُملأ مرة واحدة (الفلوت
11171        # ثابت فيُخزَّن ويبقى). فاشل-آمن، وفقط عند الغياب (نداء واحد/سهم مرّة).
11172        if s.get("float") is None:
11173            try:
11174                _cf = ce_float_info(s["symbol"])
11175                if _cf:
11176                    s["float"] = _cf
11177            except Exception:
11178                pass
```

### الاعتراف الموثّق بأن المصدر ميت — في نفس الملف (`Super_stock.py:11250-11260`)

```python
11250            radar_rows = scan_split_radar(hist, exclude=held_now | stopped,
11251                                          fetch_borrow=ce_borrow_info,
11252                                          # ⚠️ **إصلاح 2026-07-27:** كان `ce_float_info`
11253                                          # وهو **ميت** منذ 07-24 (صفحة CE صارت قِشرة JS —
11254                                          # موثّق بمِجَسّ Actions). فكان الفلوت None دائمًا
...
11259                                          fetch_float=_yahoo_float,
```

### المصدر الميت (`Super_stock.py:3149-3159`)

```python
3149 def ce_float_info(sym: str):
3150     """غلاف شبكي فاشل-آمن لفلوت ChartExchange (صفحة النظرة العامة، ناسداك فقط)."""
3152     try:
3153         r = requests.get("https://chartexchange.com/symbol/"
3154                          f"nasdaq-{sym.lower()}/", headers=BROWSER_UA, timeout=8)
```

### البديل المُثبَت (`Super_stock.py:4886-4898`) — اقرأه قبل الاستعمال

`_yahoo_float(sym)` — مُثبَت بمِجَسّ Actions على JEM/CHSN/GEOS/PTN وموثّق في `CLAUDE.md`:
«البديل المثبَت = فلوت ياهو (`_yahoo_float`: floatShares→sharesOutstanding)».
**اقرأ توقيعها الفعلي وقيمتها المرجَعة قبل الوصل** — لا تفترض.

### الاستعمال الثاني للمصدر الميت — داخل `enrich` (`Super_stock.py:4214-4229`)

```python
4218                if (r["float"] is None
4219                        and _bor_budget[0] < 25 and _flt_fails[0] < 3):
4220                    _bor_budget[0] += 1
4221                    try:
4222                        _cf = ce_float_info(sym)
...
4229                        _flt_fails[0] += 1
```

هنا هو **آخر ملاذ** بعد ياهو والذاكرة، فأثره أقل — لكنه يحرق الميزانية والقاطع بلا فائدة.

### قيد النطاق (من `CLAUDE.md`)

> «🔒 عرض فقط — خارج بوابة الفلوت M14 (تُطبَّق أثناء الفرز قبل enrich وتُمرّر المجهول
> بفائدة الشك؛ مقفول getsource: CE خارج apply_float_gate)»

⇒ يوجد اختبار قفل يتحقّق أن دوال CE **ليست** داخل `apply_float_gate`. تعديلك يجب ألّا
يكسره. تأكّد بـ`grep -n "apply_float_gate" test_bot.py`.

## Commands you will need

| الغرض | الأمر | المتوقّع |
|-------|-------|----------|
| تثبيت | `pip install -r requirements.txt` | exit 0 |
| بوّابة الاختبار | `python3 test_bot.py; echo "EXIT=$?"` | `EXIT=0` · «0 فشل» |
| مواضع المصدر الميت | `grep -n "ce_float_info" Super_stock.py` | بعد الإصلاح: التعريف + 0 أو 1 نداء احتياطي |
| فحص صياغة | `python3 -c "import ast;ast.parse(open('Super_stock.py',encoding='utf-8').read())"` | exit 0 |

## Scope

**In scope**:
- `Super_stock.py` — **فقط** كتلة الردم اليومي (`11172-11178`) وكتلة آخر الملاذ داخل
  `enrich` (`4218-4229`).
- `test_bot.py` (إضافة اختبارات)
- `CLAUDE.md` · `HANDOFF.md` (سطر توثيق)
- `plans/README.md`

**Out of scope**:
- `apply_float_gate` (`7042-7087`) و`refloat_gate_recheck` (`7090-7130`) — **لا تُعدَّلا
  هنا**. (تحصينهما مكانه الخطة 004.)
- `_yahoo_float` (`4886`) و`ce_float_info` (`3149`) و`_parse_ce_float` (`3132`) —
  **لا تُحذف ولا تُعدَّل**؛ الحذف يكسر أقفال getsource ويُفقد المحلّل لو عادت الصفحة.
- `ce_borrow_info` (`3104`) — **مصدر مختلف وحيّ** (صفحة `/borrow-fee/`). لا تلمسه.
- `scan_split_radar` و`scan_split_hunter` — يستعملان `_yahoo_float` أصلًا.
- أي رفع لـ`LOGIC_VERSION` — هذه طبقة إثراء/عرض، والقاعدة لا تنطبق.

## Git workflow

- الفرع: `advisor/003-float-backfill`
- كوميت واحد، مثال:
  `🏢 ردم الفلوت اليومي كان يستدعي مصدرًا ميتًا (CE) — البديل المُثبَت _yahoo_float`
  + `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- **لا push ولا PR.**

## Steps

### Step 1: اقرأ `_yahoo_float` وتأكّد من عقدها

اقرأ `Super_stock.py:4886-4898` كاملةً. تأكّد من: نوع القيمة المرجَعة عند النجاح، وأنها
تُرجع `None` عند الفشل، وأنها فاشلة-آمنة (لا ترمي). **لو لم تكن فاشلة-آمنة ⇒ STOP**
(الردم اليومي داخل حلقة على كل سهم نشط؛ استثناء غير محروس هناك يُسقط التقرير اليومي).

**Verify**: `sed -n '4886,4900p' Super_stock.py` → الدالّة موجودة ومحاطة بـ`try/except`.

### Step 2: بدّل مصدر الردم اليومي

في `Super_stock.py:11172-11178` بدّل `ce_float_info` بـ`_yahoo_float`، **مع الإبقاء على
كل الحراس القائمة**: شرط `if s.get("float") is None` · `try/except` · `if _cf`.

حدّث التعليق العربي فوق الكتلة ليقول الحقيقة: أن مصدر CE مات 2026-07-24 (قِشرة JS،
مُثبَت بمِجَسّ Actions) وأن البديل المُثبَت هو ياهو، **وأن هذي القناة هي التي تُغذّي
`refloat_gate_recheck` فبقاؤها ميتة كان يُبقي علّة PONY على الأسهم المخنوقة**.

⚠️ **لا تُضِف أي `time.sleep` ولا تُغيّر ترتيب الحلقة.** الحلقة تمرّ على كل سهم نشط
(حتى `CONTINUITY_MAX`=60)، ونداء ياهو الإضافي يقع **فقط** عند غياب الفلوت.

**Verify**: `sed -n '11165,11182p' Super_stock.py` يُظهر `_yahoo_float` والحراس الثلاثة.

### Step 3: بدّل آخر الملاذ داخل `enrich`

في `Super_stock.py:4218-4229` بدّل `ce_float_info(sym)` بـ`_yahoo_float(sym)`.

⚠️ **قرار دقيق**: `enrich` يجرّب ياهو `.info` أوّلًا (`4212-4213`) عبر `_fetch_info`
بثلاث محاولات. `_yahoo_float` كذلك تضرب ياهو. فالاحتياط قد يكون مكرّرًا **إلا** أن
`_yahoo_float` تسقط إلى `sharesOutstanding` وهو مسار مختلف. **أبقِ الاحتياط** ولكن:
- أبقِ حارسَي الميزانية والقاطع (`_bor_budget[0] < 25` و`_flt_fails[0] < 3`) كما هما.
- حدّث التعليق ليشرح أن المصدر تبدّل ولماذا (سقوط لـ`sharesOutstanding` = مسار مختلف).

لو تبيّن لك من قراءة `_yahoo_float` أنها **نفس** استدعاء `_fetch_info` حرفيًّا بلا مسار
إضافي، فاحذف كتلة الاحتياط كاملةً بدل تبديلها **واذكر ذلك في رسالة الكوميت**.

**Verify**: `grep -n "ce_float_info" Super_stock.py` → المتبقّي هو التعريف (`3149`) فقط
أو التعريف + صفر نداءات.

### Step 4: اختبارات (بلا شبكة)

أضِف في نهاية `test_bot.py` كتلة `# ===== خطة 003: ردم الفلوت من المصدر المُثبَت =====`.

النداء داخل حلقة في `run_daily_watchlist` وهي دالّة كبيرة يصعب استدعاؤها في اختبار.
لذلك اختبر بالطريقة التالية:

1. **قفل مصدر:** استعمل `inspect.getsource(S.run_daily_watchlist)` وأكّد أن النصّ
   **لا يحتوي** `ce_float_info` ويحتوي `_yahoo_float`. هذا قفل انحدار مباشر ضد عودة
   المصدر الميت. (نمط `getsource` مستعمل في المستودع أصلًا — ابحث عن `getsource` في
   `test_bot.py` واتّبعه.)
2. **قفل مصدر ثانٍ:** نفس الفحص على `inspect.getsource(S.enrich)`.
3. **قفل صون:** أكّد أن `inspect.getsource(S.apply_float_gate)` **لا يحتوي**
   `_yahoo_float` ولا `ce_float_info` (البوّابة تبقى نقيّة — قفل C3 قائم).
4. **قفل عدم الحذف:** أكّد أن `S.ce_float_info` و`S._parse_ce_float` ما زالتا موجودتين
   (`callable(...)`) — الحذف ممنوع بالنطاق.

**Verify**: `python3 test_bot.py; echo "EXIT=$?"` → `EXIT=0` · «0 فشل» · العدد زاد ≥4.

### Step 5: اختبار الطفرة (إلزامي)

1. أرجِع `ce_float_info` مكان `_yahoo_float` في الردم اليومي → يجب أن يسقط قفل (1).
   أرجِع الإصلاح.
2. أضِف `_yahoo_float` داخل جسم `apply_float_gate` → يجب أن يسقط قفل (3). أرجِعه.

احكم بـ`python3 test_bot.py; echo "EXIT=$?"` ⇒ `EXIT` غير صفري **و** «N فشل» > 0.

**Verify**: بعد الإرجاع → `EXIT=0` · «0 فشل».

### Step 6: التوثيق

- في `CLAUDE.md`: عدّل السطر الذي يذكر «🏢 احتياط ChartExchange للفلوت … ردم يومي» ليقول
  إن المصدر تبدّل إلى `_yahoo_float` بعد ثبوت موت صفحة CE، وأن هذي القناة هي التي
  تُغذّي `refloat_gate_recheck`.
- في `HANDOFF.md`: أضِف سطرًا بنفس الأسلوب.

**Verify**: `grep -n "_yahoo_float" CLAUDE.md HANDOFF.md` → مطابقة على الأقل في كلٍّ.

## Test plan

- **الملف**: `test_bot.py` (إضافة في النهاية).
- **النمط المرجعي**: اختبارات `getsource` القائمة (ابحث عن `getsource` في `test_bot.py`).
- **التغطية**: 4 أقفال (اثنان للتبديل، واحد للصون، واحد لعدم الحذف) + طفرتان.
- **التحقّق**: `python3 test_bot.py` → exit 0 · «0 فشل».

## Done criteria

- [ ] `python3 test_bot.py; echo "EXIT=$?"` → `EXIT=0` · «0 فشل»
- [ ] `grep -c "ce_float_info" Super_stock.py` ≤ 2 (التعريف + توقيعه في docstring)
- [ ] `grep -n "_yahoo_float" Super_stock.py` يُظهر النداء داخل `run_daily_watchlist`
- [ ] `python3 -c "import Super_stock as S,inspect;assert '_yahoo_float' not in inspect.getsource(S.apply_float_gate)"` → exit 0
- [ ] `git status --porcelain` لا يُظهر ملفات خارج: `Super_stock.py` `test_bot.py`
      `CLAUDE.md` `HANDOFF.md` `plans/README.md`
- [ ] `git status --porcelain weekly_watchlist.json company_cache.json alerts_history.json` **فارغ**
- [ ] الطفرتان أُجريتا وأُرجعتا (موثّق في الكوميت)
- [ ] صفّ 003 في `plans/README.md` محدَّث

## STOP conditions

- `_yahoo_float` ليست فاشلة-آمنة (ترمي استثناءً) — أبلغ بدل أن تلفّها بنفسك في
  `run_daily_watchlist`.
- مقتطفات «الحالة الحالية» لا تطابق الكود الحيّ.
- اكتشفت أن صفحة CE للنظرة العامة **عادت للعمل** (لا تتحقّق من ذلك بنداء شبكة من هنا —
  إن ورد دليل من المالك) ⇒ أبلغ؛ القرار عندئذٍ للمالك.
- كسر تعديلك أي قفل getsource قائم.
- فكّرت في تشغيل `daily_screener.yml` أو أي workflow حيّ — **ممنوع**.

## Maintenance notes

- بعد هذا الإصلاح تصير سلسلة الفلوت: ياهو `.info` (في `enrich`) ← الذاكرة ←
  `_yahoo_float` (احتياط + ردم يومي). **لا مصدر ثالث** حتى يثبت أحدهما حيًّا بمِجَسّ.
- المراجِع يدقّق: أن `apply_float_gate` **لم تُمَسّ** · أن الحراس الثلاثة باقية في
  كتلة الردم · أن `ce_float_info` لم تُحذف.
- تفاعل مستقبلي: أي تغيير على `refloat_gate_recheck` يعتمد على أن هذي القناة تعمل —
  اذكرها في أي مراجعة لها.
- **مؤجَّل عمدًا**: مِجَسّ Actions للتأكّد من تغطية `_yahoo_float` الحيّة على أسهم
  القائمة. يحتاج تشغيل workflow بأسرار = قرار مالك (انظر الخطة 012 لنمط التحقيق).
