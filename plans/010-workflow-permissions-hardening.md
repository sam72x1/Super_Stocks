# Plan 010: صلاحيات صريحة لكل workflow + منع حقن مدخلات الـdispatch في الصدفة

> **تعليمات المنفِّذ**: اتبع الخطة خطوةً خطوة وشغّل كل أمر تحقّق. عند أي شرط STOP توقّف
> وأبلغ. حدّث صفّ الخطة في `plans/README.md` عند الانتهاء.
>
> **فحص الانحراف (شغّله أولًا)**: `git diff --stat a6457bf..HEAD -- .github/workflows/`

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW-MED (خطأ في تحديد الصلاحية يكسر جوبًا كان يدفع للريبو — الخطة تحدّد لكل ملف صراحةً)
- **Depends on**: none
- **Category**: security (least privilege + injection hardening)
- **Planned at**: commit `a6457bf`, 2026-07-28

## Why this matters

المستودع يطبّق `permissions:` صراحةً في **13** من 23 workflow (وبدقّة: `contents: write`
حيث يُدفَع للريبو، و`contents: read` حيث لا يُدفَع). لكن **10 ملفات بلا أي كتلة
`permissions:`** ⇒ ترث الافتراضي على مستوى المستودع/المنظّمة، وهو في كثير من الحسابات
**قراءة وكتابة على كل النطاقات**. اثنان منها يعملان **بكرون** (`split_hunter.yml` ·
`scan_earnings.yml`) فالتعرّض مستمرّ لا لحظي.

وثانيًا: `acc_verify.yml:43` يُدخل مدخل `workflow_dispatch` مباشرةً في **نصّ صدفة**:

```yaml
          NAME="acc-verify-${{ github.event.inputs.year }}"
```

وهو النمط المضاد المعروف في GitHub Actions (script injection). التعرّض محدود هنا لأن
الـdispatch يقتصر على من يملك صلاحية الكتابة، لكن الإصلاح يكاد يكون بلا تكلفة والمستودع
**يمرّر بقيّة المدخلات عبر `env:` أصلًا** (`daily_screener.yml:60` · `analyze.yml:31` ·
`backtest.yml:129`) — أي أن النمط الصحيح مطبَّق في كل مكان تقريبًا، وهذا استثناء شاذّ.

بعد هذه الخطة: كل workflow يعلن أقلّ صلاحية يحتاجها، ولا مدخل مستخدم يدخل صدفةً مباشرة.

## Current state

### الملفات العشرة بلا `permissions:` (مفحوصة آليًّا)

```
acc_report.yml      acc_verify.yml     analyze_asof.yml   analyze.yml
hand_check.yml      ignition_verify.yml polygon_health.yml scan_earnings.yml
split_hunter.yml    technical.yml
```

### النمط المطبَّق أصلًا في المستودع (اقتدِ به)

- **يدفع للريبو ⇒ `contents: write`**: `daily_screener.yml:2-3` ·
  `pullback_monitor.yml` · `ignition.yml:12-13` · `hand_flow.yml` ·
  `cline_weekly_review.yml:18-19` · `e2_recover.yml:6-7`.
- **لا يدفع ⇒ `contents: read`**: `tests.yml` · `hand_digest.yml:2-3` ·
  `backtest.yml:2-3` · `freeze.yml:5-6` · `faisal_combo.yml:4-5`.

### موضع الحقن (`.github/workflows/acc_verify.yml:41-45` تقريبًا)

```yaml
          NAME="acc-verify-${{ github.event.inputs.year }}"
```

بينما نفس الملف يمرّر المدخل الآخر **بشكل صحيح** عبر `env:` (السطر 60):

```yaml
          ACC_VERIFY_YEAR: ${{ github.event.inputs.year }}
```

### تحقّق حاسم قبل تحديد الصلاحية: أيّ من العشرة يدفع للريبو؟

الدفع يحدث حصرًا عبر `bot.git_save(...)` (`Super_stock.py:13360`) أو عبر خطوة
`git push` صريحة في الـYAML. الأدوات التي تشغّلها الملفات العشرة:

| الملف | يشغّل | يدفع؟ |
|-------|-------|-------|
| `split_hunter.yml` | `split_hunter.py` | **لا** (docstring: «لا تحفظ شيئًا») |
| `scan_earnings.yml` | `technical_report.py` | تحقّق في الخطوة 1 |
| `polygon_health.yml` | `polygon_health.py` | **لا** (عرض/تشخيص) |
| `hand_check.yml` | `hand_check.py` | **لا** (عرض/تشخيص) |
| `analyze.yml` · `analyze_asof.yml` | `analyze_one.py` · `analyze_asof.py` | **لا** |
| `technical.yml` | `technical_report.py` | تحقّق في الخطوة 1 |
| `ignition_verify.yml` | `ignition_verify.py` | تحقّق في الخطوة 1 |
| `acc_verify.yml` · `acc_report.yml` | `acc_verify.py` / تنزيل artifacts | تحقّق في الخطوة 1 |

## Commands you will need

| الغرض | الأمر | المتوقّع |
|-------|-------|----------|
| الملفات بلا صلاحيات | `cd .github/workflows && for f in *.yml; do grep -q "permissions:" $f \|\| echo "NO-PERM: $f"; done` | قبل: 10 أسطر · بعد: **صفر** |
| كشف الدفع | `grep -n "git_save\|git push" <script>.py` | انظر الخطوة 1 |
| مدخلات في الصدفة | `grep -n 'run:' -A20 .github/workflows/*.yml \| grep 'github.event.inputs'` | بعد الإصلاح: لا مطابقة داخل كتل `run:` |
| بوّابة الاختبار | `python3 test_bot.py; echo "EXIT=$?"` | `EXIT=0` · «0 فشل» |

## Scope

**In scope**:
- الملفات العشرة أعلاه داخل `.github/workflows/` — **إضافة كتلة `permissions:` فقط**،
  زائد إصلاح الحقن في `acc_verify.yml`.
- `plans/README.md`

**Out of scope**:
- الـ13 workflow التي تعلن صلاحياتها أصلًا — **لا تُمَسّ**.
- أي كرون · أي `env:` · أي سرّ · أي `concurrency` · أي `timeout-minutes`.
- أي ملف `.py`.
- تشديد صلاحيات الملفات التي تدفع فعلًا (كلها معلنة أصلًا وصحيحة).
- إعداد الافتراضي على مستوى المستودع (خارج الريبو — أوصِ به للمالك في الملاحظات).

## Git workflow

- الفرع: `advisor/010-workflow-permissions`
- كوميت واحد، مثال:
  `🔐 صلاحيات صريحة لعشرة workflows + مدخل الـdispatch يمرّ عبر env لا الصدفة`
  + `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- **لا push ولا PR.**

## Steps

### Step 1: حدّد لكل ملف هل يدفع للريبو (لا تخمّن)

لكل واحد من العشرة، افتح خطوة `run:` واعرف السكربت، ثم:

```
grep -n "git_save\|git push\|git commit" <script>.py
```

**وانتبه للاستدعاء غير المباشر**: بعض السكربتات تستدعي دوالّ من `Super_stock` تدفع
داخليًّا. تحقّق تحديدًا من:
- `run_performance_system` (`Super_stock.py:13699`) ⇒ ينادي `git_save` في `13714`.
- `record_ignition_fires`/`record_ignition_universe` ⇒ يكتبان ملفًّا محليًّا فقط.

سجّل جدولًا: `<file> → read | write` مع سطر السبب. لو تعذّر الحسم لملف بعد فحصين ⇒
اختر **`contents: write`** (الآمن ضدّ الكسر) واذكر التردّد في الكوميت.

**Verify**: جدول من عشرة صفوف، لكل صفّ سببه.

### Step 2: أضِف الكتل

في كل ملف، أضِف بعد سطر `name:` مباشرةً (نفس موضعها في `daily_screener.yml:2-3`):

```yaml
permissions:
  contents: read      # (أو write — حسب جدول الخطوة 1)
```

مع تعليق عربي سطر واحد يذكر السبب، مثلًا:
`# عرض/تنبيه فقط — لا يدفع للريبو (split_hunter.py لا يحفظ حالة).`

⚠️ **لا تستعمل `permissions: {}`** — بعض الأفعال (checkout على مستودع خاصّ) تحتاج
`contents: read` صراحةً.

**Verify**:
```
cd .github/workflows && for f in *.yml; do grep -q "permissions:" $f || echo "NO-PERM: $f"; done
```
→ **لا مخرجات**.

### Step 3: أصلح الحقن في `acc_verify.yml`

بدّل الاستعمال المباشر في الصدفة بمتغيّر بيئة، على نمط بقيّة المستودع:

```yaml
        env:
          YEAR: ${{ github.event.inputs.year }}
        run: |
          NAME="acc-verify-${YEAR}"
          ...
```

⚠️ **لا تغيّر ما يفعله السكربت** — فقط طريقة وصول القيمة. تأكّد أن كل استعمالات
`$NAME` اللاحقة في نفس كتلة `run:` ما زالت تعمل (اقرأ الكتلة كاملةً قبل التعديل).

**Verify**:
```
grep -n 'NAME=' .github/workflows/acc_verify.yml
```
→ يُظهر `${YEAR}` لا `${{ ... }}`.

### Step 4: امسح بقيّة الملفات بحثًا عن نفس النمط

```
grep -rn 'github.event.inputs' .github/workflows/ | grep -v ':.*[A-Z_]*: \${{'
```

راجع كل مطابقة يدويًّا: المسموح هو الاستعمال داخل `env:` أو `with:` أو تعبير `if:`
(GitHub يقيّمها بلا صدفة). **الممنوع** هو الاستعمال داخل نصّ `run:`.

لو ظهرت مطابقة ثانية داخل `run:`، أصلحها بنفس نمط الخطوة 3.

**Verify**: كل مطابقة إمّا داخل `env:`/`with:`/`if:` أو مُصلَحة.

### Step 5: تحقّق من صحّة كل الـYAML

```
python3 - <<'EOF'
import glob, sys
try:
    import yaml
except ImportError:
    print("SKIP: لا مكتبة yaml — اذكر ذلك في الكوميت"); sys.exit(0)
bad = []
for f in sorted(glob.glob(".github/workflows/*.yml")):
    d = yaml.safe_load(open(f, encoding="utf-8"))
    if "permissions" not in d:
        bad.append(("no-permissions", f))
    p = d.get("permissions")
    if isinstance(p, dict) and p.get("contents") not in ("read", "write"):
        bad.append(("bad-contents", f))
print("BAD:", bad if bad else "none")
assert not bad
print("ALL WORKFLOWS OK")
EOF
```

**المتوقّع**: `ALL WORKFLOWS OK` (أو `SKIP`).

⚠️ لو ظهر `no-permissions` لملف كان يعلنها على مستوى **الجوب** لا الـworkflow، فهذا
مقبول — عدّل السكربت ليقبل الحالتين واذكر ذلك.

### Step 6: تأكيد عدم المساس بغير المقصود

```
git diff a6457bf..HEAD -- .github/workflows/
```

راجع الـdiff بعينك وأكّد أنه **لا يمسّ**: أي `cron:` · أي `secrets.*` ·
`RENEW_ON_CLOSE` · أي `concurrency` · أي `timeout-minutes` · أي `run:` عدا كتلة
`acc_verify.yml` المقصودة.

**Verify**: `git diff a6457bf..HEAD -- .github/workflows/ | grep -E "^[-+].*cron:"` → **لا مخرجات**.

### Step 7: بوّابة الاختبار

`python3 test_bot.py; echo "EXIT=$?"` → `EXIT=0` · «0 فشل».

## Test plan

- لا اختبارات وحدة (تغييرات YAML خارج نطاق `test_bot.py`).
- التحقّق الآلي البديل:
  - عدّاد «بلا صلاحيات» = صفر (الخطوة 2).
  - محمّل الـYAML يمرّ على 23 ملفًّا (الخطوة 5).
  - لا `github.event.inputs` داخل أي كتلة `run:` (الخطوة 4).
  - لا سطر `cron:` في الـdiff (الخطوة 6).
  - `python3 test_bot.py` → exit 0.
- **لا تشغّل أي workflow** للتحقّق.

## Done criteria

- [ ] `cd .github/workflows && for f in *.yml; do grep -q "permissions:" $f || echo "NO-PERM: $f"; done` → **لا مخرجات**
- [ ] سكربت الخطوة 5 يطبع `ALL WORKFLOWS OK` (أو `SKIP` موثّق)
- [ ] `grep -n 'NAME=' .github/workflows/acc_verify.yml` يُظهر `${YEAR}`
- [ ] لا `${{ github.event.inputs.* }}` داخل أي كتلة `run:` في المستودع
- [ ] `git diff a6457bf..HEAD -- .github/workflows/ | grep -E "^[-+].*(cron:|secrets\.)"` → **لا مخرجات**
- [ ] `git diff a6457bf..HEAD -- '*.py'` **فارغ**
- [ ] `python3 test_bot.py; echo "EXIT=$?"` → `EXIT=0` · «0 فشل»
- [ ] جدول الخطوة 1 (عشرة صفوف بأسبابها) مضمَّن في رسالة الكوميت
- [ ] صفّ 010 في `plans/README.md` محدَّث

## STOP conditions

- تعذّر الحسم لملفين أو أكثر في الخطوة 1 ⇒ أبلغ بجدولك بدل التخمين الجماعي.
- الـdiff لمس أي `cron:` أو أي سرّ أو `RENEW_ON_CLOSE`.
- وجدت نفسك تعدّل أي ملف `.py`.
- وجدت نفسك تُضيّق صلاحية ملف **يدفع فعلًا** إلى `read` — سيكسر دفعه بصمت.
- فكّرت في تشغيل أي workflow — **ممنوع**.

## Maintenance notes

- **توصية للمالك (خارج نطاق التنفيذ)**: اضبط الافتراضي في
  Settings → Actions → Workflow permissions إلى **Read repository contents**، فتصير
  الإعلانات الصريحة شبكة أمان مزدوجة. لا تفعلها نيابةً عنه.
- **قاعدة**: كل workflow جديد يُنشأ **يعلن `permissions:`** — أضِفها لقائمة المراجعة.
- المراجِع يدقّق: أن كل ملف يدفع فعلًا حصل على `write` (وإلا كسر صامت) · أن لا كرون
  تحرّك · أن الحقن أُصلح بـ`env` لا باقتباس.
- **مؤجَّل عمدًا**: تثبيت الأفعال بـSHA بدل الوسوم (`actions/checkout@v4` →
  `@<sha>`) — تشديد سلسلة إمداد مشروع لكنه يضيف عبء صيانة مستمرًّا؛ قرار مالك مستقلّ.
