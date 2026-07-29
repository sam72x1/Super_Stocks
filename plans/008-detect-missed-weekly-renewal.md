# Plan 008: كشف «تجديد الجمعة لم يحدث» — إشعار فقط، بلا لمس قرار التجديد

> **تعليمات المنفِّذ**: اتبع الخطة خطوةً خطوة وشغّل كل أمر تحقّق. عند أي شرط STOP توقّف
> وأبلغ. حدّث صفّ الخطة في `plans/README.md` عند الانتهاء.
>
> **فحص الانحراف (شغّله أولًا)**:
> `git diff --stat a6457bf..HEAD -- Super_stock.py test_bot.py`
>
> 🔴 **حدّ مُلزِم**: هذه الخطة **لا تغيّر متى يُجدَّد** ولا تشتقّ التجديد من
> `weekday()`. القرار الموثّق في `CLAUDE.md` صريح: «**مدفوع بإشارة الجدولة لا بيوم
> الأسبوع**» (أُزيل `WEEKLY_RENEW_DAY` عمدًا). المضاف هنا **إشعار فقط**.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW (طبقة إشعار — `should_renew` تبقى byte-identical)
- **Depends on**: `plans/001-characterization-baseline.md`
- **Category**: bug (رصد فشل صامت)
- **Planned at**: commit `a6457bf`, 2026-07-28

## Why this matters

التجديد الأسبوعي مشروط بإشارة واحدة فقط:

- `daily_screener.yml:60` → `RENEW_ON_CLOSE: ${{ github.event.schedule == '7 22 * * 5' && '1' || '0' }}`
- `Super_stock.py:13329` → `renew_signal = os.environ.get("RENEW_ON_CLOSE","").strip() == "1"`
- `Super_stock.py:6899` → `return renew_signal`

لو **أسقط GitHub** تشغيلة الكرون تلك (سلوك موثّق من GitHub عند الحمل، وهذا المستودع قاس
بنفسه تأخّرات **95-159 دقيقة** — انظر تعليق `ignition.yml:17-24`)، فلن يحدث شيء **ولن
يلاحظ أحد**: القائمة دائمة بتصميمها فلا تنهار، لكن يسقط بصمت في ذلك الأسبوع:

- بناء القائمة الجديدة · تقرير «مصير أسهم الأسبوع الماضي» (`build_fate_report`)
- رسالة الحصاد (`build_wrapup_message`) · التقرير الأسبوعي (`weekly_report`)
- مساعد التطوير (`build_dev_assistant_report`) · تصدير CSV للمشرف (`export_weekly_csvs`)
- أرشفة الأسبوع في `history` · بناء قائمة الارتداد من جديد

كل هذي داخل `run_weekly_renewal` (`10784-11021`). ولا يوجد أي أثر يكشف الغياب.

بعد هذه الخطة: عند تشغيل يومي عادي، لو مضى على آخر تجديد أكثر من `RENEWAL_STALE_DAYS`
(=8، أي أُسقطت جمعة كاملة) يصل **تحذير تلغرام صريح** يخبر المالك أن يشغّل
`force_renew=1` يدويًّا. **القرار يبقى بيده** — لا تجديد تلقائي.

## Current state

### قرار التجديد (`Super_stock.py:6887-6899`) — لا يُعدَّل

```python
6887 def should_renew(wl: dict, force: bool = False,
6888                  renew_signal: bool = False) -> bool:
6889     """متى نفرز السوق كاملاً ونبني قائمة جديدة:
6890     - renew_signal=True: جوب التجديد الأسبوعي (الجمعة 22:00 UTC بعد إغلاق
6891       السوق) — يمرّره الـworkflow عبر RENEW_ON_CLOSE. ...
6893     - قائمة فارغة = تأسيس فوري (أي يوم). | FORCE_RENEW=1 = إجبار يدوي.
6894     القائمة ثابتة دائمة: باقي التشغيلات = متابعة + إضافة الجديد فقط (لا رفرفة)."""
6895     if force:
6896         return True
6897     if not wl.get("stocks") and not wl.get("removed"):
6898         return True  # أول تشغيل — تأسيس فوري
6899     return renew_signal
```

### الحقول الموجودة سلفًا (استعملها — لا تخترع جديدًا)

`run_weekly_renewal` يكتب عند كل تجديد فعليّ (`Super_stock.py:10967-10974`):

```python
10967     new_wl = dict(wl)
10968     new_wl.update({"week_start": today_iso, "created": today_iso,
10969                    "logic_version": LOGIC_VERSION,
10970                    "stocks": final_stocks,
10971                    "removed": [], "replacements_log": [], "notes": [],
10972                    "pullback": pull_entries,
...
```

⇒ **`wl["week_start"]` هو ختم آخر تجديد ناجح** (بصيغة `YYYY-MM-DD`). القيمة الحيّة
اليوم في `weekly_watchlist.json` هي `"2026-07-28"`.

⚠️ **انتبه لحالة التأجيل**: عند ضعف التغطية يخرج `run_weekly_renewal` مبكرًا
(`10804-10815` و`10834-10845`) **بلا** تحديث `week_start` — وهذا **مقصود ومفيد لنا**:
التأجيل يجب أن يُرصَد أيضًا (تأجيل متكرّر = تجديد لم يحدث فعلًا).

### نقطة الحقن (`Super_stock.py:13327-13339`)

```python
13327     force = os.environ.get("FORCE_RENEW", "").strip() == "1"
13329     renew_signal = os.environ.get("RENEW_ON_CLOSE", "").strip() == "1"
13330     wl = load_watchlist()
13331     if should_renew(wl, force, renew_signal):
...
13337     else:
13338         log("وضع اليوم: متابعة يومية للقائمة الثابتة")
13339         run_daily_watchlist(wl)
```

### كرون الفرع اليومي

`daily_screener.yml` → `- cron: "54 4 * * 2-5"` (الثلاثاء→الجمعة) — أي أربع فرص أسبوعيًّا
لرصد التأخّر، وهو كافٍ.

## Commands you will need

| الغرض | الأمر | المتوقّع |
|-------|-------|----------|
| تثبيت | `pip install -r requirements.txt` | exit 0 |
| بوّابة الاختبار | `python3 test_bot.py; echo "EXIT=$?"` | `EXIT=0` · «0 فشل» |
| فحص صياغة | `python3 -c "import ast;ast.parse(open('Super_stock.py',encoding='utf-8').read())"` | exit 0 |

## Scope

**In scope**:
- `Super_stock.py` — دالّة نقيّة جديدة + نداؤها في `main()` + مفتاح `CONFIG` واحد.
- `test_bot.py`
- `CLAUDE.md` · `HANDOFF.md` (سطر)
- `plans/README.md`

**Out of scope**:
- **`should_renew` — صفر تعديل.** لا وسيط جديد، لا شرط جديد، لا اشتقاق من `weekday()`.
- `run_weekly_renewal` · `run_daily_watchlist` — لا تُعدَّلا.
- `.github/workflows/daily_screener.yml` — الكرون والإشارة لا يتغيّران.
- أي تجديد تلقائي عند التقادم — **ممنوع صراحةً** (يخالف قرارًا موثّقًا).
- أي رفع لـ`LOGIC_VERSION`.

## Git workflow

- الفرع: `advisor/008-renewal-staleness`
- كوميت واحد، مثال:
  `🔔 كشف «تجديد الجمعة لم يحدث» — إشعار فقط (should_renew byte-identical)`
  + `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- **لا push ولا PR.**

## Steps

### Step 1: أضِف عتبة في `CONFIG`

في كتلة `CONFIG` (تبدأ عند `Super_stock.py:106`)، قرب مفاتيح القائمة
(`WATCHLIST_SIZE` · `CONTINUITY_MAX`)، أضِف:

```python
    "RENEWAL_STALE_DAYS": 8,     # 🔔 تقادم التجديد: أكثر من 8 أيام على آخر تجديد ناجح
                                 # = جمعة كاملة سقطت (كرون GitHub قد يُسقط تشغيلة).
                                 # **إشعار فقط** — القرار للمالك (force_renew=1).
```

**Verify**: `grep -n "RENEWAL_STALE_DAYS" Super_stock.py` → مطابقتان (التعريف + الاستعمال لاحقًا).

### Step 2: دالّة نقيّة `renewal_staleness`

أضِفها **بعد** `should_renew` مباشرةً. مواصفاتها الكاملة:

```python
def renewal_staleness(wl: dict, today=None, max_days=None):
    """🔔 هل تأخّر التجديد الأسبوعي؟ **نقيّة · فاشلة-آمنة · إشعار فقط.**

    ⚠️ **لا تؤثّر على `should_renew` إطلاقًا** — قرار التجديد يبقى مدفوعًا بإشارة
    الجدولة (`RENEW_ON_CLOSE`) لا بيوم الأسبوع ولا بالتقادم (قرار موثّق في CLAUDE.md).
    هذي ترصد أن **جمعةً سقطت** (GitHub قد يُسقط تشغيلة كرون، والمستودع قاس تأخّرات
    95-159 دقيقة) فلا يمرّ الغياب بصمت.

    يرجّع None (لا تقادم / تعذّرت القراءة) أو dict:
      {"last": "YYYY-MM-DD", "days": int, "max_days": int}
    """
```

المنطق:
1. `ref = wl.get("week_start")`. لو غائب/غير نصّ ⇒ `return None` (لا نُنذر على قائمة
   تأسيسية أو ملف قديم).
2. `today = today or dt.date.today()`; اقبل نصًّا ISO أو `date`.
3. `max_days = max_days if max_days is not None else CONFIG["RENEWAL_STALE_DAYS"]`.
4. حلّل `ref` بـ`dt.date.fromisoformat(str(ref)[:10])` داخل `try` — أي فشل ⇒ `None`.
5. `days = (today - last).days`. لو `days > max_days` ⇒ أرجِع الـdict، وإلا `None`.
6. **قيمة سالبة** (`week_start` في المستقبل — ساعة رنر مغلوطة) ⇒ `None` لا إنذار.

### Step 3: دالّة عرض `renewal_stale_message`

دالّة نقيّة ثانية تحوّل الـdict إلى نصّ تلغرام عربي، بلا علامات مقارنة
(**قاعدة مُلزِمة في `CLAUDE.md`: ممنوع `≥ ≤ > <` في أي نصّ معروض** — استعمل «مضى … يومًا»
و«المتوقّع كل 7 أيام»). يجب أن يذكر:

- تاريخ آخر تجديد وعدد الأيام.
- أن المتوقّع تجديد كل أسبوع (الجمعة بعد الإغلاق).
- السببين المحتملين: **إسقاط GitHub لتشغيلة الكرون**، أو **تأجيل التجديد لضعف تغطية
  البيانات** (`run_weekly_renewal` يخرج مبكرًا في تلك الحالة بلا تحديث `week_start`).
- الإجراء: «شغّل Daily Pivot Screener بـ`force_renew=1`».
- طمأنة صريحة: **القائمة النشطة محفوظة والمتابعة مستمرّة** (فلا يُقرأ التحذير هلعًا).

### Step 4: اربطها في `main()` — الفرع اليومي فقط

في `Super_stock.py:13337-13339` (فرع `else`)، **قبل** `run_daily_watchlist(wl)`:

```python
    else:
        log("وضع اليوم: متابعة يومية للقائمة الثابتة")
        # 🔔 رصد سقوط جمعة التجديد (إشعار فقط — لا يغيّر قرار التجديد إطلاقًا).
        try:
            _st = renewal_staleness(wl)
            if _st:
                _m = renewal_stale_message(_st)
                log(_m)
                send_telegram(_m + "\n\n" + FOOTER)
        except Exception as _e:                      # فاشل-آمن مطلق
            log(f"⚠️ رصد تقادم التجديد: {_e}")
        run_daily_watchlist(wl)
```

🔴 **الترتيب مقصود**: الإشعار **قبل** `run_daily_watchlist` كي يصل حتى لو سقطت التشغيلة
بعده. و`try/except` مطلق كي لا يُسقط الرصدُ المتابعةَ اليومية أبدًا.

⚠️ **ديدوب**: التشغيل اليومي أربع مرات أسبوعيًّا ⇒ حتى أربع رسائل. **هذا مقصود ومقبول**
(تحذير حالة لا تنبيه سوق) ويطابق أسلوب «تنبيه تأجيل التجديد» القائم (`10840-10842`).
**لا تضف حالة دِدوب مخزَّنة** — تعني كتابة في ملف الحالة من مسار إشعار، وهو ما يتجنّبه
المستودع.

**Verify**: `python3 -c "import ast;ast.parse(open('Super_stock.py',encoding='utf-8').read())"` → exit 0.

### Step 5: اختبارات

أضِف تحت `# ===== خطة 008: رصد تقادم التجديد =====`:

1. `week_start` = اليوم ⇒ `None`.
2. `week_start` = اليوم − 7 ⇒ `None` (الأسبوع الطبيعي لا يُنذر — **قفل ضد الإزعاج**).
3. `week_start` = اليوم − 8 ⇒ `None` (الحدّ نفسه لا يُنذر؛ `days > max_days`).
4. `week_start` = اليوم − 9 ⇒ dict فيه `days == 9`.
5. `week_start` غائب ⇒ `None`.
6. `week_start = "غير-تاريخ"` ⇒ `None` بلا رمي.
7. `week_start` في المستقبل (اليوم + 3) ⇒ `None`.
8. `max_days` محقون (مثلًا 3) يتجاوز `CONFIG` ⇒ يُنذر عند 4 أيام.
9. `renewal_stale_message` تُنتج نصًّا يحوي التاريخ وعدد الأيام و«force_renew».
10. **قفل اللغة**: النصّ **لا يحوي** أيًّا من `≥ ≤ > <` (قاعدة `CLAUDE.md`).
11. **قفل الصون الحاسم**:
    `inspect.getsource(S.should_renew)` **لا يحوي** `renewal_staleness` ولا
    `RENEWAL_STALE_DAYS` ولا `weekday` — قرار التجديد لم يُمَسّ.
12. اختبارات `should_renew` الخمسة من خطة 001 ما زالت تمرّ (لا تعِد كتابتها، تأكّد فقط).

**Verify**: `python3 test_bot.py; echo "EXIT=$?"` → `EXIT=0` · «0 فشل» · العدد زاد ≥11.

### Step 6: اختبار الطفرة (إلزامي)

1. غيّر `days > max_days` إلى `days >= max_days` → يجب أن يسقط اختبار (3).
   **هذي طفرة حدّ تخوم — ضرورية**: `CLAUDE.md` يوثّق أن حدًّا غير مقفول كُشف بالطفرة
   وحدها في T-CMAG. أرجِعها.
2. أضِف `renewal_staleness` داخل جسم `should_renew` → يجب أن يسقط قفل (11). أرجِعه.
3. أزِل `try/except` حول النداء في `main()` واجعل `renewal_staleness` ترمي → يجب أن
   يسقط اختبار يتحقّق أن `main()` لا ترمي (أضِفه إن لم يكن). أرجِعه.

احكم بـ`python3 test_bot.py; echo "EXIT=$?"` ⇒ `EXIT` غير صفري **و** «N فشل» > 0.

**Verify**: بعد الإرجاع → `EXIT=0` · «0 فشل».

### Step 7: التوثيق

في `CLAUDE.md` (قسم «النظام الحالي» بند 1 حيث يُشرح التجديد) و`HANDOFF.md`:
سطر يقول إن رصد التقادم أُضيف **إشعارًا فقط**، وأن `should_renew` byte-identical ومقفولة
باختبار، وأن السبب أن إسقاط GitHub لتشغيلة الكرون كان يمرّ بلا أي أثر.

## Test plan

- **الملف**: `test_bot.py` (إضافة في النهاية).
- **النمط المرجعي**: اختبارات الدوال النقيّة القائمة (`_ignition_outcome` مثلًا) +
  أقفال `getsource`.
- **التغطية**: 8 حالات حدّية للدالّة النقيّة · قفل اللغة · قفل صون `should_renew` ·
  قفل «`main` لا ترمي» + 3 طفرات.
- **التحقّق**: `python3 test_bot.py` → exit 0 · «0 فشل».

## Done criteria

- [ ] `python3 test_bot.py; echo "EXIT=$?"` → `EXIT=0` · «0 فشل»
- [ ] `python3 -c "import Super_stock as S,inspect;src=inspect.getsource(S.should_renew);assert 'renewal_staleness' not in src and 'weekday' not in src and 'RENEWAL_STALE_DAYS' not in src"` → exit 0
- [ ] `git diff a6457bf..HEAD -- Super_stock.py` لا يمسّ جسم `should_renew` (راجعه سطرًا سطرًا)
- [ ] `git diff a6457bf..HEAD -- .github/` **فارغ**
- [ ] `LOGIC_VERSION` **لم يتغيّر**
- [ ] `git status --porcelain weekly_watchlist.json alerts_history.json` **فارغ**
- [ ] الطفرات الثلاث أُجريت وأُرجعت (موثّق في الكوميت)
- [ ] صفّ 008 في `plans/README.md` محدَّث

## STOP conditions

- وجدت نفسك تعدّل `should_renew` أو تجعل التقادم يُطلق تجديدًا تلقائيًّا ⇒ **توقّف
  فورًا**؛ هذا يخالف قرارًا موثّقًا صراحةً في `CLAUDE.md`.
- وجدت نفسك تكتب حالة دِدوب في `weekly_watchlist.json` من مسار الإشعار.
- اكتشفت أن `week_start` **لا يُحدَّث عند التجديد الناجح** (اقرأ `10967-10975` وتأكّد) ⇒
  المرجع خاطئ؛ أبلغ بدل أن تخترع حقلًا جديدًا.
- استعملت `≥ ≤ > <` في أي نصّ معروض.
- فكّرت في تشغيل أي workflow حيّ — **ممنوع**.

## Maintenance notes

- **حسّاسية العتبة**: 8 أيام تسمح بجمعة واحدة متأخّرة بضع ساعات، وتُنذر عند سقوط جمعة
  كاملة. لو ظهر إزعاج، الضبط يكون على `RENEWAL_STALE_DAYS` وحده — لا تُغيّر المنطق.
- تفاعل مقصود: تأجيل التجديد لضعف التغطية (`10804-10815`, `10834-10845`) **لا يحدّث
  `week_start`**، فتأجيلان متتاليان سيُنذران — وهذا هو المطلوب بالضبط.
- المراجِع يدقّق: أن `should_renew` byte-identical · أن الإشعار **قبل**
  `run_daily_watchlist` وداخل `try` · أن النصّ بلا علامات مقارنة.
- **مؤجَّل عمدًا**: رصد مماثل لسقوط كرونات أخرى (`ignition.yml` · `hand_flow.yml` ·
  `split_hunter.yml`). لوحة «حالة جمع البيانات» (`_collection_health_block:9659`) تغطّي
  جزءًا منها؛ توسيعها خطة مستقلّة.
