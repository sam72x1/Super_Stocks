# Plan 006: `monitor_pullback` — تحميل مجمَّع بدل نداء `download_history` لكل رمز

> **تعليمات المنفِّذ**: اتبع الخطة خطوةً خطوة وشغّل كل أمر تحقّق. عند أي شرط STOP توقّف
> وأبلغ. حدّث صفّ الخطة في `plans/README.md` عند الانتهاء.
>
> **فحص الانحراف (شغّله أولًا)**:
> `git diff --stat a6457bf..HEAD -- Super_stock.py pullback_live.py test_bot.py`

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED (يمسّ قناة التنبيه اللحظية الوحيدة — لكن قرار الإطلاق يبقى byte-identical ومقفولًا)
- **Depends on**: `plans/001-characterization-baseline.md`
- **Category**: perf (وفي الأثر: reliability)
- **Planned at**: commit `a6457bf`, 2026-07-28

## Why this matters

`monitor_pullback` ينادي `download_history([sym])` **مرة لكل سهم** داخل حلقة. و
`download_history` ليست نداءً خفيفًا: هي مصمّمة للدفعات — تقسيم + **3 محاولات بتراجع
أُسّي (3ث ثم 6ث)** + `time.sleep(CHUNK_SLEEP=2.0)` + **تمريرة ثانية كاملة** لإعادة
محاولة ما لم يُحمَّل.

الحساب على القيم الحقيقية من `CONFIG`:
- نجاح من أول محاولة: ~3-4 ثوانٍ لكل سهم (تحميل + `sleep(2)` ×2 تمريرتين).
- فشل/خنق ياهو: ~9ث (محاولتا تراجع) + 2ث + ~9ث + 2ث ≈ **22 ثانية لكل سهم**.

وقائمة الارتداد حدّها 15 سهمًا ⇒ **من ~50 ثانية إلى ~5.5 دقائق** تُستهلك **قبل** أي شيء
آخر. والمشكلة أن هذا يقع في `pullback_live.py:50`، **قبل** استدعاء
`monitor_live_events` في السطر 72 — وهو مصدر **تنبيه كسر الوقف**، أي التنبيه الوحيد
المصنَّف «خطر» و«لا يُبوَّب بالمضارب» في كل النظام. ومهلة الجوب
(`.github/workflows/pullback_monitor.yml`) = **15 دقيقة**. فعند خنق ياهو يُقتَل الجوب
قبل التنبيه **وقبل `save_watchlist`/`git_save`**.

بعد هذه الخطة: نداء تحميل مجمَّع واحد، فيهبط زمن هذه المرحلة إلى ثوانٍ ويبقى الوقت
لقناة الخطر.

## Current state

### الدالّة (`Super_stock.py:9758-9782`) — المقتطف الكامل

```python
9758 def monitor_pullback(wl: dict) -> list:
9759     """متابعة يومية لقائمة الارتداد: يحدّث السعر، ويُطلق تنبيهًا عند نزول
9760     السهم لسعر الدعم (ضمن PULLBACK_TRIGGER_PCT). يعيد قائمة المُنبَّه عنها."""
9761     entries = wl.get("pullback") or []
9762     if not entries or yf is None:
9763         return []
9764     triggered = []
9765     buf = 1.0 + CONFIG.get("PULLBACK_TRIGGER_PCT", 2.0) / 100.0
9766     for e in entries:
9767         if e.get("status") == "triggered":
9768             continue
9769         try:
9770             d = download_history([e["symbol"]])
9771             df = d.get(e["symbol"])
9772             if df is None or df.empty:
9773                 continue
9774             lp = float(df["Close"].iloc[-1])
9775             e["last_price"] = round(lp, 4)
9776             if lp <= e["entry"][1] * buf:        # نزل لسعر الدعم
9777                 e["status"] = "triggered"
9778                 e["triggered_date"] = dt.date.today().isoformat()
9779                 triggered.append(e)
9780         except Exception:
9781             continue
9782     return triggered
```

### الدالّة الثقيلة (`Super_stock.py:1142-1169`) — اقرأها كاملةً قبل البدء

```python
1150     size = CONFIG["CHUNK_SIZE"]
1151     chunks = [tickers[i:i + size] for i in range(0, len(tickers), size)]
1152     for n, chunk in enumerate(chunks, 1):
1154         data = _download_chunk(chunk, start)
1155         if data is not None:
1156             _extract_into(out, data, chunk)
1157         time.sleep(CONFIG["CHUNK_SLEEP"])
1158     # تمريرة ثانية: إعادة محاولة الرموز التي لم تُحمّل
1159     missing = [t for t in tickers if t not in out]
1160     if missing:
1162         for i in range(0, len(missing), size):
1164             data = _download_chunk(sub, start)
1166                 _extract_into(out, data, sub)
1167             time.sleep(CONFIG["CHUNK_SLEEP"])
```

القيم من `CONFIG`: `CHUNK_SIZE=250` · `CHUNK_SLEEP=2.0` · `DOWNLOAD_RETRIES=3` ·
`RETRY_BACKOFF=3.0` · `MIN_BARS=120` (فلتر داخل `_extract_into:1136`).

### نقطة النداء (`pullback_live.py:41-56`)

```python
41 def main():
42     wl = bot.load_watchlist()
43     snap = _stamp_snapshot(wl)     # 🛡️ للاسترجاع عند إخفاق الإرسال
44     alerts = []
45     # (1) مراقبة الارتداد: تنبيه أول ما ينزل سهم لسعر الدعم
46     entries = [e for e in (wl.get("pullback") or [])
47                if e.get("status") != "triggered"]
48     if entries:
49         bot.log(f"مراقبة الارتداد اللحظية: فحص {len(entries)} سهم...")
50         triggered = bot.monitor_pullback(wl)
```

ويُنادى أيضًا من `run_daily_watchlist` (`Super_stock.py:11218`) داخل `try/except`.

### مهلة الجوب

`.github/workflows/pullback_monitor.yml` → `timeout-minutes: 15` ·
`cron: "13,43 11-23 * * 1-5"`.

## Commands you will need

| الغرض | الأمر | المتوقّع |
|-------|-------|----------|
| تثبيت | `pip install -r requirements.txt` | exit 0 |
| بوّابة الاختبار | `python3 test_bot.py; echo "EXIT=$?"` | `EXIT=0` · «0 فشل» |
| فحص صياغة | `python3 -c "import ast;ast.parse(open('Super_stock.py',encoding='utf-8').read())"` | exit 0 |

## Scope

**In scope**:
- `Super_stock.py` — **فقط** جسم `monitor_pullback` (9758-9782).
- `test_bot.py`
- `CLAUDE.md` · `HANDOFF.md` (سطر)
- `plans/README.md`

**Out of scope**:
- `download_history` · `_download_chunk` · `_extract_into` — **لا تُعدَّل**؛ يستعملها
  الفرز الكامل والباكتيست، وأي تغيير فيها له نطاق أوسع بكثير.
- `PULLBACK_TRIGGER_PCT` · `PULLBACK_SIZE` · أي عتبة — **لا تُمَسّ**.
- منطق الإطلاق `lp <= e["entry"][1] * buf` — **byte-identical**.
- `pullback_live.py` — لا يتغيّر (نفس التوقيع، نفس القيمة المرجَعة).
- `monitor_live_events` — خارج النطاق تمامًا.
- أي رفع لـ`LOGIC_VERSION` (طبقة تتبّع/تنبيه).

## Git workflow

- الفرع: `advisor/006-batch-pullback`
- كوميت واحد، مثال:
  `⚡ monitor_pullback: تحميل مجمَّع واحد بدل نداء لكل رمز (كان يأكل مهلة جوب المراقبة)`
  + `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- **لا push ولا PR.**

## Steps

### Step 1: أضِف جالبًا محقونًا (يمكّن الاختبار بلا شبكة)

غيّر التوقيع إلى:

```python
def monitor_pullback(wl: dict, fetch_hist=None) -> list:
```

بحيث `fetch_hist` دالّة تأخذ **قائمة رموز** وتُرجع `dict[sym] -> DataFrame`، والافتراضي
`download_history`. هذا يطابق نمط الحقن المستعمل في المستودع
(`scan_ignition(fetch_bars=...)` · `scan_split_hunter(fetch_splits=...)` ·
`monitor_live_events(fetch_operator=...)`).

⚠️ **الوسيط اختياري بقيمة `None`** فكل المستدعين القائمين (`pullback_live.py:50` و
`Super_stock.py:11218`) يعملون بلا تغيير.

**Verify**: `grep -n "def monitor_pullback" Super_stock.py` يُظهر الوسيط الجديد ·
`grep -rn "monitor_pullback(" --include="*.py" .` يُظهر أن كل النداءات القائمة بوسيط واحد.

### Step 2: جمّع التحميل في نداء واحد

أعِد كتابة الجسم بحيث:

1. تُبنى قائمة الرموز غير المُطلَقة **مرة واحدة**:
   `pend = [e for e in entries if e.get("status") != "triggered"]`
2. `if not pend: return []`
3. نداء واحد: `hist = (fetch_hist or download_history)([e["symbol"] for e in pend])`
   داخل `try/except` يُرجع `{}` عند الفشل ويسجّل بـ`log` (لا صمت).
4. الحلقة تقرأ `hist.get(e["symbol"])` وتُطبّق **نفس** منطق الإطلاق حرفيًّا (نفس
   `buf` · نفس المقارنة · نفس ترتيب الإسنادات: `last_price` ثم `status` ثم
   `triggered_date` ثم `append`).
5. `try/except: continue` لكل سهم يبقى (سهم واحد معطوب لا يمنع البقيّة).
6. **ترتيب `triggered` يجب أن يطابق ترتيب `entries` الأصلي** — القائمة تُعرض للمستخدم
   في `build_pullback_section` (`9731`)، فالترتيب سلوك مرئي.

⚠️ **لا تُدخل أي `time.sleep` جديد** ولا تغيّر ما يُخزَّن في المدخلات.

**Verify**: `python3 -c "import ast;ast.parse(open('Super_stock.py',encoding='utf-8').read())"` → exit 0.

### Step 3: عدّل توصيف خطة 001

اختبار الخطوة 5 في خطة 001 يؤكّد أن **عدد النداءات = عدد الأسهم غير المُطلَقة**.
اقلبه: صار المتوقّع **نداء واحد بالضبط**، وأن **وسيطه قائمة تحوي كل الرموز غير
المُطلَقة ولا تحوي المُطلَقة**.

لو خطة 001 لم تُنفَّذ ⇒ **STOP**.

**Verify**: `python3 test_bot.py; echo "EXIT=$?"` → `EXIT=0` · «0 فشل».

### Step 4: قفل تكافؤ السلوك (الأهمّ)

أضِف تحت `# ===== خطة 006: تكافؤ monitor_pullback المجمَّع =====` اختبارًا يقارن
النتيجة بين الجالب المجمَّع ومحاكاة السلوك القديم على **نفس المدخلات**:

- ابنِ قائمة `pullback` من ≥6 سجلّات تغطّي: أقلّ من العتبة بكثير · **عند العتبة بالضبط**
  (`lp == entry[1]*buf`) · فوقها بقليل · `status="triggered"` مسبقًا · رمز بلا بيانات
  (`None`) · رمز بإطار فارغ.
- شغّل `monitor_pullback(wl, fetch_hist=<مجمَّع مزيّف>)`.
- أكّد لكل سجلّ: `status` · `triggered_date` · `last_price` · وأن قائمة المُرجَع
  **بنفس الترتيب** المتوقّع.
- أكّد أن السجلّ `triggered` مسبقًا **لم يُمَسّ** (`last_price` لم يتغيّر).

**Verify**: `python3 test_bot.py; echo "EXIT=$?"` → `EXIT=0` · «0 فشل» · العدد زاد ≥6.

### Step 5: اختبار عدد النداءات وحدود الفشل

1. **نداء واحد**: عدّاد الجالب = 1 مهما بلغ عدد السجلّات.
2. **فشل الجالب كلّه** (يرمي) ⇒ `monitor_pullback` تُرجع `[]` **ولا ترمي** · وتُطبع
   رسالة `log` (قفل ضد الصمت).
3. **جالب يُرجع `{}`** ⇒ `[]` بلا رمي، ولا سجلّ يتغيّر.
4. **`yf is None`** ⇒ `[]` فورًا بلا أي نداء (السلوك القائم في `9762` محفوظ).
5. **`pullback` فارغة/غائبة** ⇒ `[]` بلا نداء.

**Verify**: `python3 test_bot.py; echo "EXIT=$?"` → `EXIT=0` · «0 فشل».

### Step 6: اختبار الطفرة (إلزامي)

1. غيّر `lp <= e["entry"][1] * buf` إلى `lp < e["entry"][1]` → يجب أن تسقط حالة
   «عند العتبة بالضبط» من الخطوة 4. أرجِعه.
2. أزِل شرط `status == "triggered"` من بناء `pend` → يجب أن يسقط اختبار «المُطلَق مسبقًا
   لم يُمَسّ» واختبار وسيط النداء من الخطوة 3. أرجِعه.
3. اعكس ترتيب `triggered` → يجب أن يسقط قفل الترتيب. أرجِعه.

احكم بـ`python3 test_bot.py; echo "EXIT=$?"` ⇒ `EXIT` غير صفري **و** «N فشل» > 0.

**Verify**: بعد الإرجاع → `EXIT=0` · «0 فشل».

### Step 7: التوثيق

سطر في `CLAUDE.md` (قسم قائمة مراقبة الارتداد) و`HANDOFF.md`: أن `monitor_pullback` صار
نداء تحميل مجمَّعًا واحدًا، **وقرار الإطلاق byte-identical مقفول باختبار**، وأن السبب
أن النداء لكل رمز كان يستهلك حتى ~5.5 دقائق من مهلة الجوب (15د) **قبل** قناة تنبيه
كسر الوقف. اذكر الوسيط الجديد `fetch_hist` (حقن للاختبار).

## Test plan

- **الملف**: `test_bot.py` (قلب توصيف واحد + إضافة ≥10).
- **النمط المرجعي**: اختبارات `scan_ignition` بحقن `fetch_bars` — ابحث عن
  `scan_ignition(` في `test_bot.py` واتبع أسلوبها.
- **التغطية**: تكافؤ الحالات الستّ · نداء واحد · فشل الجالب · `{}` · `yf is None` ·
  قائمة فارغة · قفل الترتيب.
- **التحقّق**: `python3 test_bot.py` → exit 0 · «0 فشل».

## Done criteria

- [ ] `python3 test_bot.py; echo "EXIT=$?"` → `EXIT=0` · «0 فشل»
- [ ] `python3 -c "import Super_stock as S,inspect;src=inspect.getsource(S.monitor_pullback);assert src.count('download_history')<=1 and 'fetch_hist' in src"` → exit 0
- [ ] `git diff a6457bf..HEAD -- Super_stock.py` يمسّ **فقط** جسم `monitor_pullback`
- [ ] `git diff a6457bf..HEAD -- pullback_live.py .github/` **فارغ**
- [ ] `LOGIC_VERSION` **لم يتغيّر**
- [ ] `git status --porcelain weekly_watchlist.json alerts_history.json` **فارغ**
- [ ] الطفرات الثلاث أُجريت وأُرجعت (موثّق في الكوميت)
- [ ] صفّ 006 في `plans/README.md` محدَّث

## STOP conditions

- توصيف خطة 001 (الخطوة 5) غير موجود ⇒ نفّذ 001 أولًا.
- اختبار التكافؤ في الخطوة 4 أظهر أي فرق في `status`/`triggered_date`/`last_price`/الترتيب.
- وجدت نفسك تعدّل `download_history` أو أي عتبة أو `pullback_live.py`.
- اكتشفت مستدعيًا ثالثًا لـ`monitor_pullback` يعتمد على السلوك القديم لكل رمز.
- فكّرت في تشغيل `pullback_monitor.yml` أو أي workflow حيّ — **ممنوع**.

## Maintenance notes

- `download_history` تُطبّق `MIN_BARS=120` في `_extract_into` (`1136`) — سهم بتاريخ
  أقصر يغيب من الخريطة سواء نُودي مفردًا أو مجمَّعًا، فالسلوك محفوظ. **لا تخفّف هذا الفلتر.**
- المراجِع يدقّق: عدد النداءات = 1 · منطق العتبة byte-identical · الترتيب محفوظ ·
  المُطلَق مسبقًا مستثنى من الوسيط.
- تفاعل مستقبلي: لو رُفع `PULLBACK_SIZE` فوق `CHUNK_SIZE=250` فسيقسّم `download_history`
  تلقائيًّا — لا حاجة لتعديل هنا.
- **مؤجَّل عمدًا وبإصرار**: `monitor_live_events` (`8331`) ينادي Polygon لكل رمز
  (بريماركت/أفتر/دقائق/تدفق). لم يُدمج هنا لأن منافذ Polygon مختلفة ولا تقبل التجميع،
  ولأن حراس النافذة الزمنية تُصفّر النداءات خارج نوافذها. **لكن سقف الميزانية هناك غير
  موجود** — يستحقّ خطة مستقلّة إن أظهر تحقيقُ الخطة 012 ضغطًا على مهلة الجوب.
