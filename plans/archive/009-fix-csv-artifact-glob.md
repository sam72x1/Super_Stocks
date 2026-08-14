# Plan 009: إصلاح مسار artifact الـCSV في `daily_screener.yml` (نمط بلا منتِج)

> **تعليمات المنفِّذ**: اتبع الخطة خطوةً خطوة وشغّل كل أمر تحقّق. عند أي شرط STOP توقّف
> وأبلغ. حدّث صفّ الخطة في `plans/README.md` عند الانتهاء.
>
> **فحص الانحراف (شغّله أولًا)**:
> `git diff --stat a6457bf..HEAD -- .github/workflows/daily_screener.yml Super_stock.py`

## Status

- **Priority**: P3
- **Effort**: XS
- **Risk**: LOW (تعديل سطر واحد في workflow · لا يمسّ منطقًا)
- **Depends on**: none
- **Category**: dx (config بلا قارئ)
- **Planned at**: commit `a6457bf`, 2026-07-28

## Why this matters

`daily_screener.yml` يرفع artifact باسم `screener-report` من النمط
`screener_report_*.csv`. **لا شيء في المستودع كلّه يُنتج ملفًا بهذا الاسم.** والبحث
الشامل يؤكّد ذلك: المطابقة الوحيدة لكلمة `screener_report` في المستودع هي **سطر
الـworkflow نفسه**.

النتيجة اليوم: الخطوة تنجح دائمًا بلا شيء (`if-no-files-found: ignore` يبتلع الغياب)،
و**مُخرَجات CSV الحقيقية للتشغيلة تضيع مع الرنر**:
- المسار اليومي يكتب `daily_watch_<date>.csv` (`Super_stock.py:11266,10777`) — **يضيع**.
- مسار التجديد يكتب `weekly_list_<date>.csv` (`Super_stock.py:11008`) — **يضيع** (وإن
  كانت ملفات `trades/signals/missed` تُرسَل لتلغرام مستقلّةً عبر `export_weekly_csvs`).

وهي بالضبط الملفات التي يحتاجها المالك عند تدقيق تشغيلة بعينها. `*.csv` في `.gitignore`
فلا تدخل الريبو، والـartifact كان الوسيلة الوحيدة لاسترجاعها.

## Current state

### `.github/workflows/daily_screener.yml:65-72` (نهاية الملف)

```yaml
      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: screener-report
          path: screener_report_*.csv
          if-no-files-found: ignore
```

### كاتبا الـCSV الوحيدان في `Super_stock.py`

```python
10773 def write_csv(rows: list, prefix: str) -> None:
10774     if not (CONFIG["REPORT_CSV"] and rows):
10775         return
10776     try:
10777         fn = f"{prefix}_{dt.date.today().isoformat()}.csv"
10778         pd.DataFrame(rows).to_csv(fn, index=False, encoding="utf-8-sig")
```

```python
6662 def _write_csv_file(rows: list, prefix: str):
6667         fn = f"{prefix}_{dt.date.today().isoformat()}.csv"
```

### البادئات المستعملة فعلًا

| البادئة | نقطة النداء | المسار |
|---------|-------------|--------|
| `daily_watch` | `Super_stock.py:11271` | يومي |
| `weekly_list` | `Super_stock.py:11016` | تجديد |
| `trades` · `signals` · `missed` | `Super_stock.py:6709-6712` | تجديد (تُرسَل لتلغرام أيضًا) |

### `.gitignore`

```
*.csv
```

⇒ الملفات لا تُلتقط بـgit؛ الـartifact هو القناة الوحيدة.

## Commands you will need

| الغرض | الأمر | المتوقّع |
|-------|-------|----------|
| إثبات غياب المنتِج | `grep -rn "screener_report" --include="*.py" --include="*.yml" .` | مطابقة واحدة فقط: سطر الـworkflow |
| البادئات الفعلية | `grep -n "write_csv(\|_write_csv_file(" Super_stock.py` | يُظهر `daily_watch` · `weekly_list` · `trades` · `signals` · `missed` |
| بوّابة الاختبار | `python3 test_bot.py; echo "EXIT=$?"` | `EXIT=0` · «0 فشل» |

## Scope

**In scope**:
- `.github/workflows/daily_screener.yml` — خطوة `Upload report` فقط.
- `plans/README.md`

**Out of scope**:
- `Super_stock.py` — **صفر تعديل**. لا تُعِد تسمية `write_csv` ولا بادئاته: الأسماء
  تظهر في السجلّ (`log(f"حُفظ التقرير: {fn}")`) والمالك يعرفها.
- `.gitignore` — `*.csv` مقصود (لا نُدخل مُخرَجات يومية في تاريخ git).
- `export_weekly_csvs` (`6675`) وإرسال المستندات لتلغرام — يعمل ولا يُمَسّ.
- أي workflow آخر.

## Git workflow

- الفرع: `advisor/009-csv-artifact`
- كوميت واحد، مثال:
  `📎 artifact الفرز كان يرفع نمطًا لا منتِج له — التقارير اليومية/الأسبوعية كانت تضيع`
  + `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- **لا push ولا PR.**

## Steps

### Step 1: أثبت الغياب بنفسك

```
grep -rn "screener_report" --include="*.py" --include="*.yml" .
```

**المتوقّع: مطابقة واحدة فقط** — `.github/workflows/daily_screener.yml:71`.
لو ظهرت مطابقة ثانية (منتِج فعليّ) ⇒ **STOP**: التشخيص انحرف.

### Step 2: صحّح النمط

عدّل الخطوة إلى الأنماط الحقيقية، مع الإبقاء على `if: always()` و
`if-no-files-found: ignore` (اليوم اليومي لا يُنتج `weekly_list_*` والعكس، فالغياب
الجزئي طبيعي):

```yaml
      # 📎 **إصلاح 2026-07-28:** كان النمط `screener_report_*.csv` و**لا شيء ينتجه**
      #    في المستودع كلّه (البادئات الفعلية من `write_csv`/`_write_csv_file`:
      #    daily_watch · weekly_list · trades · signals · missed) ⇒ الخطوة كانت تنجح
      #    فارغةً وتقارير التشغيلة تضيع مع الرنر (و`*.csv` في .gitignore فلا بديل).
      #    `if-no-files-found: ignore` يبقى: اليومي لا ينتج weekly_list والعكس.
      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: screener-report-${{ github.run_id }}
          path: |
            daily_watch_*.csv
            weekly_list_*.csv
            trades_*.csv
            signals_*.csv
            missed_*.csv
          retention-days: 30
          if-no-files-found: ignore
```

ملاحظتان مقصودتان:
- `${{ github.run_id }}` في الاسم: يمنع تعارض أسماء الـartifacts بين تشغيلات
  (نمط مستعمل أصلًا في `ignition.yml:69,119,191`).
- `retention-days: 30`: `ignition.yml` يستعمل 90 لبيانات القياس؛ 30 كافٍ لتقارير يومية.

### Step 3: تحقّق من صحّة الـYAML

```
python3 - <<'EOF'
import sys
try:
    import yaml
except ImportError:
    print("SKIP: لا مكتبة yaml — اذكر ذلك في الكوميت"); sys.exit(0)
d = yaml.safe_load(open(".github/workflows/daily_screener.yml", encoding="utf-8"))
up = [s for s in d["jobs"]["screen"]["steps"] if s.get("name") == "Upload report"][0]
paths = [p.strip() for p in up["with"]["path"].strip().splitlines()]
assert "screener_report_*.csv" not in paths, "النمط الميت ما زال موجودًا"
for need in ("daily_watch_*.csv", "weekly_list_*.csv"):
    assert need in paths, f"ناقص: {need}"
assert d["jobs"]["screen"]["steps"][0]["uses"].startswith("actions/checkout")
print("YAML OK")
EOF
```

**المتوقّع**: `YAML OK` (أو `SKIP` لو المكتبة غير مثبّتة).

### Step 4: تأكّد أن شيئًا آخر لم يتغيّر

```
git diff a6457bf..HEAD -- .github/workflows/daily_screener.yml
```

راجع الـdiff بعينك: يجب أن يمسّ **فقط** خطوة `Upload report`. تحديدًا **لا يمسّ**:
سطرَي الكرون (`54 4 * * 2-5` و`7 22 * * 5`) · مطابقة `RENEW_ON_CLOSE` · `permissions`
· `concurrency` · `timeout-minutes` · كتلة `env`.

🔴 **تحذير مقترن**: `RENEW_ON_CLOSE` يطابق نصّ كرون التجديد **حرفيًّا**
(`daily_screener.yml:60`). أي مسّ بذلك السطر يعطّل التجديد الأسبوعي بصمت.

**Verify**: الـdiff محصور في خطوة `Upload report`.

### Step 5: بوّابة الاختبار

`python3 test_bot.py; echo "EXIT=$?"` → `EXIT=0` · «0 فشل»
(لا يُفترض أن يتأثّر شيء — هذا تأكيد لا أكثر.)

## Test plan

- لا اختبارات وحدة: التغيير في YAML خارج نطاق `test_bot.py`.
- التحقّق الآلي البديل:
  - `grep -rn "screener_report" --include="*.py" --include="*.yml" .` → **لا مطابقة**.
  - سكربت تحميل الـYAML في الخطوة 3 → `YAML OK`.
  - `python3 test_bot.py` → exit 0 · «0 فشل».
- **لا تشغّل `daily_screener.yml`** للتحقّق — تشغيل حيّ ممنوع.

## Done criteria

- [ ] `grep -rn "screener_report" --include="*.py" --include="*.yml" .` → **لا مطابقة**
- [ ] سكربت الخطوة 3 يطبع `YAML OK` (أو `SKIP` موثّق في الكوميت)
- [ ] `python3 test_bot.py; echo "EXIT=$?"` → `EXIT=0` · «0 فشل»
- [ ] `git diff a6457bf..HEAD -- .github/workflows/daily_screener.yml` محصور في خطوة
      `Upload report` (لا كرون · لا `RENEW_ON_CLOSE` · لا `env` · لا `permissions`)
- [ ] `git status --porcelain` لا يُظهر ملفات خارج `daily_screener.yml` و`plans/README.md`
- [ ] صفّ 009 في `plans/README.md` محدَّث

## STOP conditions

- ظهر منتِج فعليّ لـ`screener_report_*.csv` في الخطوة 1.
- الـdiff لمس سطر كرون أو `RENEW_ON_CLOSE`.
- وجدت نفسك تعدّل `Super_stock.py` أو `.gitignore`.
- فكّرت في تشغيل `daily_screener.yml` — **ممنوع**.

## Maintenance notes

- **قاعدة**: أي بادئة CSV جديدة تُضاف لـ`write_csv`/`_write_csv_file` يجب أن تُضاف
  لقائمة `path` هنا، وإلا ضاع الملف بصمت. اذكر ذلك في التعليق فوق الخطوة.
- المراجِع يدقّق: أن سطرَي الكرون و`RENEW_ON_CLOSE` لم يُمَسّا.
- **مؤجَّل عمدًا**: مراجعة بقيّة الـworkflows بحثًا عن أنماط artifact بلا منتِج
  (`backtest.yml` · `acc_verify.yml` · `freeze.yml`). كلها يدوية فأثر الفقد أقلّ،
  ويستحقّ تمريرة منفصلة.
