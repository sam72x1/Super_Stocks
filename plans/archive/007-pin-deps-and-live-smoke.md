# Plan 007: تثبيت الاعتماديات + فحص دخان حيّ — سدّ فجوة «CI أخضر وإنتاج مكسور»

> **تعليمات المنفِّذ**: اتبع الخطة خطوةً خطوة وشغّل كل أمر تحقّق. عند أي شرط STOP توقّف
> وأبلغ. حدّث صفّ الخطة في `plans/README.md` عند الانتهاء.
>
> **فحص الانحراف (شغّله أولًا)**:
> `git diff --stat a6457bf..HEAD -- requirements.txt .github/workflows/`

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW (بنية تحتية — لا يمسّ منطق فرز/تنبيه)
- **Depends on**: none
- **Category**: dependencies / dx
- **Planned at**: commit `a6457bf`, 2026-07-28

## Why this matters

كل workflow إنتاجي يبدأ بـ`pip install -r requirements.txt`، والملف **غير مثبَّت**:

```
yfinance>=0.2.40
pandas>=2.0
numpy>=1.24
requests>=2.31
```

`yfinance` مكتبة تكشط بيانات بلا عقد API مستقرّ، وتُصدر إصدارات تكسر شكل مُخرَج
`yf.download` و`Ticker().info` بلا سابق إنذار. الرنر ينزل **آخر إصدار وقت التشغيل**،
فقد يختلف بين تشغيلتين متتاليتين لنفس الكوميت.

والفجوة الأخطر: **سويّة الاختبارات تعمل بلا إنترنت بتصميمها** (كل الجالبات محقونة/
مقلَّدة، `tests.yml` يقول ذلك صراحةً). فكسر yfinance **لا يُسقط أي اختبار** — تبقى
`tests.yml` خضراء بينما الإنتاج يقرأ صفر بيانات. حراس التغطية القائمة
(`DATA_HEALTH_MIN_PCT=85` · `run_daily_watchlist:11106`) ستمنع الضرر (لا تُضاف أسهم)
لكنها **لا تشخّص السبب**: المالك سيرى «تغطية ضعيفة» يوميًّا بلا معرفة أنها ترقية مكتبة.

بعد هذه الخطة: الإصدارات مثبَّتة (تشغيلات قابلة للتكرار) + workflow يدوي/أسبوعي واحد
يكشف كسر التوافق **قبل** أن يظهر بصمت في التقرير اليومي.

## Current state

### `requirements.txt` (الملف كاملًا)

```
yfinance>=0.2.40
pandas>=2.0
numpy>=1.24
requests>=2.31
```

### المستهلكون (كلهم يثبّتون من نفس الملف)

`grep -rn "requirements.txt" .github/workflows/` يُظهر أن كل الـworkflows تفعل
`pip install -r requirements.txt`، بينها الإنتاجية: `daily_screener.yml` ·
`pullback_monitor.yml` · `ignition.yml` · `hand_digest.yml` · `split_hunter.yml` ·
`hand_flow.yml` · `scan_earnings.yml`.

### `.github/workflows/tests.yml` — الاعتراف الصريح

```yaml
      # السويّة تعمل بلا إنترنت بتصميمها (كل الجالبات محقونة/مقلَّدة) — أي فشل هنا
      # فشل حقيقي في المنطق، لا عطل شبكة.
      - name: Run full test suite
        run: python3 test_bot.py
```

مع `python-version: "3.11"` و`cache: pip`.

### الحراس القائمة التي ستمتصّ الضرر لكن لا تشخّصه

- `Super_stock.py:7382-7384` — تحذير تغطية داخل `scan_market`.
- `Super_stock.py:11106-11123` — `coverage_ok` يمنع إضافة أسهم جديدة + سطر تنبيه بالتقرير.
- `Super_stock.py:10834-10845` — إلغاء التجديد الأسبوعي عند ضعف التغطية.

## Commands you will need

| الغرض | الأمر | المتوقّع |
|-------|-------|----------|
| نسخ Python المستعمَل | `python3 -V` | يجب أن يكون 3.11.x؛ غيره ⇒ انظر STOP |
| النسخ المثبَّتة حاليًّا | `python3 -m pip freeze \| grep -Ei "^(yfinance\|pandas\|numpy\|requests)="` | 4 أسطر بنسخ محدّدة |
| تثبيت | `pip install -r requirements.txt` | exit 0 |
| بوّابة الاختبار | `python3 test_bot.py; echo "EXIT=$?"` | `EXIT=0` · «0 فشل» |
| صحّة YAML | `python3 -c "import sys,glob;[__import__('json') for _ in ()]"` — استعمل بدلها الأمر في الخطوة 3 | — |

## Scope

**In scope**:
- `requirements.txt`
- `.github/workflows/deps_smoke.yml` (**ملف جديد**)
- `deps_smoke.py` (**ملف جديد** في الجذر)
- `CLAUDE.md` · `HANDOFF.md` · `README.md` (سطر)
- `plans/README.md`

**Out of scope**:
- `.github/workflows/tests.yml` — **لا تحوّله إلى اختبار شبكة**. تصميمه «بلا إنترنت»
  قرار صحيح: يفصل فشل المنطق عن عطل الشبكة. الفحص الحيّ يذهب لـworkflow **منفصل**.
- أي ملف `.py` قائم — **صفر تعديل** على منطق البوت.
- ترقية أي مكتبة إلى إصدار أحدث — هذه الخطة **تثبّت ما يعمل اليوم** فقط.
- إضافة مكتبات جديدة (لا `pip-tools` ولا `poetry` ولا `uv`) — قرار معماري للمالك.

## Git workflow

- الفرع: `advisor/007-pin-deps`
- كوميت واحد، مثال:
  `📌 تثبيت الاعتماديات + فحص دخان حيّ (الاختبارات بلا إنترنت لا تكشف كسر yfinance)`
  + `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- **لا push ولا PR.**

## Steps

### Step 1: التقط النسخ العاملة اليوم

شغّل:

```
python3 -m pip freeze | grep -Ei "^(yfinance|pandas|numpy|requests)="
```

سجّل الأربع نسخًا. **لو أيٌّ منها غير مثبَّت في بيئتك، ثبّت من الملف الحالي أولًا**
(`pip install -r requirements.txt`) ثم أعِد الالتقاط.

**Verify**: الأمر يطبع أربعة أسطر بصيغة `name==X.Y.Z`.

### Step 2: ثبّت `requirements.txt`

اكتب الملف بالنسخ الملتقطة **بالضبط** مع تعليق يشرح السبب. الشكل:

```
# 📌 مثبَّتة عمدًا (تدقيق 2026-07-28): كل workflow إنتاجي يثبّت من هنا وقت التشغيل،
#    و`yfinance` تكسر شكل مُخرَج `download`/`Ticker().info` بين الإصدارات بلا إنذار.
#    والأخطر: سويّة `test_bot.py` تعمل **بلا إنترنت** (جالبات محقونة) فتبقى خضراء
#    والإنتاج يقرأ صفر بيانات ⇒ «تغطية ضعيفة» يوميًّا بلا تشخيص. التثبيت يجعل
#    التشغيلات قابلة للتكرار، والترقية تصير **قرارًا واعيًا** يمرّ بـdeps_smoke.yml.
yfinance==<النسخة الملتقطة>
pandas==<النسخة الملتقطة>
numpy==<النسخة الملتقطة>
requests==<النسخة الملتقطة>
```

⚠️ **لا تضف اعتماديات متعدّية** (`lxml` · `beautifulsoup4` …). الهدف تثبيت المباشرة فقط
بلا قفل كامل — القفل الكامل قرار معماري للمالك.

**Verify**:
`pip install -r requirements.txt` → exit 0
`python3 test_bot.py; echo "EXIT=$?"` → `EXIT=0` · «0 فشل»

### Step 3: اكتب `deps_smoke.py` — فحص دخان حيّ صريح

سكربت مستقلّ في الجذر، على نمط `polygon_health.py` (اقرأه أولًا كنموذج: هو أداة
تشخيص مستقلّة تُرسل حكمًا لتلغرام ولا تلمس أي حالة).

المطلوب أن يفحص **العقود التي يعتمدها البوت فعلًا**، لا مجرّد «هل تستورد المكتبة»:

1. `import yfinance, pandas, numpy, requests` ويطبع نسخة كلٍّ.
2. `Super_stock.get_universe()` ⇒ يجب أن يُرجع قائمة طولها > 1000. (يكشف كسر
   nasdaqtrader أو الفلترة.)
3. `Super_stock.download_history(["AAPL", "MSFT", "GEOS"])` ⇒ يجب أن يُرجع dict فيه
   ≥2 مفاتيح، وكل إطار فيه الأعمدة `Open High Low Close Volume` وطوله ≥ `CONFIG["MIN_BARS"]`.
   (يكشف كسر شكل `yf.download`/`group_by="ticker"`.)
4. `yfinance.Ticker("AAPL").info` ⇒ dict فيه `sector` أو `floatShares` أو `country`.
   (يكشف كسر `.info` الذي يعتمده `_fetch_info`/`apply_float_gate`.)
5. آخر شمعة لـ`AAPL` عمرها ≤ 7 أيام تقويمية. (يكشف بيانات بائتة.)

الحكم: ✅ لو نجح الخمسة · ❌ وإلا، مع تفصيل أيّها سقط. يُرسل لتلغرام **ويُطبع في السجلّ**
(مثل `polygon_health.py` تمامًا: `bot.log(msg)` ثم `bot.send_telegram(msg + FOOTER)`).
والخروج **غير صفري عند أي سقوط** فتظهر الوظيفة حمراء في Actions حتى لو تعذّر تلغرام.

🔴 **قيود إلزامية**:
- **لا يستورد ولا يستدعي أي دالّة تكتب حالة**: ممنوع `save_watchlist` · `git_save` ·
  `_atomic_write_json` · `record_*`.
- **لا يطبع أي سرّ**؛ لا يلمس `POLYGON_API_KEY`.
- كل نداء شبكة داخل `try/except` يحوّل الاستثناء إلى «سقط» لا إلى انهيار.
- رموز الفحص ثابتة في السكربت (لا تقرأ `weekly_watchlist.json`).

**Verify**:
`python3 -c "import ast;ast.parse(open('deps_smoke.py',encoding='utf-8').read())"` → exit 0
`grep -nE "git_save|save_watchlist|_atomic_write_json|record_ignition" deps_smoke.py` → **لا مطابقة**

### Step 4: `deps_smoke.yml`

workflow جديد:

- `on: workflow_dispatch` **و** `schedule: - cron: "37 6 * * 1"` (الاثنين، دقيقة غير
  مستديرة — درس الكرون الموثّق في هذا المستودع).
- `permissions: contents: read` (صريحة).
- `concurrency: group: deps-smoke` مستقلّة (لا تدخل `super-stocks-state`).
- `timeout-minutes: 20`.
- Python `3.11` (مطابقة الإنتاج) · `pip install -r requirements.txt` ·
  `run: python deps_smoke.py`.
- الأسرار: `TELEGRAM_BOT_TOKEN` و`TELEGRAM_CHAT_ID` فقط. **لا `POLYGON_API_KEY`.**
- تعليق عربي في الرأس يشرح الغرض: «`tests.yml` تعمل بلا إنترنت فلا تكشف كسر yfinance —
  هذا الجوب هو الكاشف الوحيد».

**Verify**: تأكّد من صحّة الـYAML:
```
python3 - <<'EOF'
import sys
try:
    import yaml
except ImportError:
    sys.exit(0)   # لا مكتبة yaml ⇒ تخطَّ الفحص (اذكر ذلك في الكوميت)
yaml.safe_load(open(".github/workflows/deps_smoke.yml", encoding="utf-8"))
print("YAML OK")
EOF
```

### Step 5: تأكّد أن السكربت لا يكسر السويّة

`deps_smoke.py` يستورد `Super_stock` ويضرب الشبكة عند التشغيل فقط. تأكّد أن
`python3 test_bot.py` لا يستورده ولا يتأثّر به.

**Verify**:
`grep -n "deps_smoke" test_bot.py` → **لا مطابقة**
`python3 test_bot.py; echo "EXIT=$?"` → `EXIT=0` · «0 فشل»

### Step 6: التوثيق

- `README.md`: أضِف سطرًا تحت قسم الاختبارات: أن `tests.yml` بلا إنترنت وأن
  `deps_smoke.yml` هو فحص التوافق الحيّ.
- `CLAUDE.md`: أضِف `deps_smoke.py` إلى قائمة «الملفات المهمّة» و`deps_smoke.yml` إلى
  قائمة `.github/workflows/`، مع سطر: **الاعتماديات مثبَّتة عمدًا وترقيتها قرار واعٍ
  يمرّ بهذا الفحص.**
- `HANDOFF.md`: سطر مقابل.

**Verify**: `grep -n "deps_smoke" README.md CLAUDE.md HANDOFF.md` → مطابقة في الثلاثة.

## Test plan

- لا اختبارات وحدة جديدة في `test_bot.py`: `deps_smoke.py` **أداة شبكة بطبيعتها**
  ومحاكاتها في السويّة تعيد إنتاج نفس الفجوة التي نسدّها.
- التحقّق البديل (كلها آلية):
  - `python3 test_bot.py` → exit 0 · «0 فشل» (لم يتأثّر شيء).
  - `python3 -c "import ast;ast.parse(...)"` على `deps_smoke.py`.
  - grep يمنع أي دالّة كتابة حالة داخل `deps_smoke.py`.
  - تحميل YAML بنجاح.
- **التشغيل الحيّ لـ`deps_smoke.yml` = قرار المالك** (يستهلك أسرار تلغرام) — لا تشغّله.

## Done criteria

- [ ] `requirements.txt` يحوي أربعة أسطر `==` بنسخ محدّدة + تعليق السبب
- [ ] `pip install -r requirements.txt` → exit 0
- [ ] `python3 test_bot.py; echo "EXIT=$?"` → `EXIT=0` · «0 فشل»
- [ ] `deps_smoke.py` موجود ويمرّ فحص الصياغة
- [ ] `grep -nE "git_save|save_watchlist|_atomic_write_json|record_ignition" deps_smoke.py` → **لا مطابقة**
- [ ] `.github/workflows/deps_smoke.yml` موجود، فيه `permissions: contents: read`،
      **بلا** `POLYGON_API_KEY`، وكرونه بدقيقة غير مستديرة
- [ ] `git status --porcelain` لا يُظهر ملفات خارج القائمة في «In scope»
- [ ] `git diff a6457bf..HEAD -- Super_stock.py test_bot.py` **فارغ**
- [ ] صفّ 007 في `plans/README.md` محدَّث

## STOP conditions

- `python3 -V` ليست 3.11.x ⇒ **توقّف وأبلغ**: النسخ الملتقطة قد لا تطابق ما يحلّه
  الرنر على 3.11، فالتثبيت من بيئة مختلفة قد يكسر الإنتاج.
- `python3 test_bot.py` سقط بعد التثبيت ⇒ إحدى النسخ الملتقطة غير متوافقة؛ **لا تخفّف
  التثبيت لتمرير الاختبار** — أبلغ بالنسخة والخطأ.
- وجدت نفسك تُرقّي مكتبة أو تضيف واحدة جديدة.
- وجدت نفسك تعدّل `tests.yml` ليضرب الشبكة.
- فكّرت في تشغيل `deps_smoke.yml` أو أي workflow حيّ — **ممنوع؛ قرار المالك.**

## Maintenance notes

- **بروتوكول الترقية** (اكتبه في تعليق `requirements.txt`): غيّر النسخة على فرع →
  `python3 test_bot.py` → شغّل `deps_smoke.yml` يدويًّا → ادمج فقط عند ✅.
- المراجِع يدقّق: أن التثبيت `==` لا `~=` · أن الفحص الحيّ خارج `tests.yml` · أن
  `deps_smoke.py` لا يكتب حالة ولا يأخذ مفتاح Polygon.
- **مؤجَّل عمدًا**: قفل كامل (`pip-compile`/hashes) — يضيف أداة بناء جديدة، قرار مالك.
- **مؤجَّل عمدًا**: فحص دخان لمنافذ Polygon — مغطًّى أصلًا بـ`polygon_health.yml`
  (يدوي). لو أراد المالك جدولته فذلك تغيير سطر واحد هناك، لا خطة جديدة.
