# Plan 002: إحياء قياس «ربع الساعة» في رادار الانطلاق (ميت في الإنتاج لسببين)

> **تعليمات المنفِّذ**: اتبع الخطة خطوةً خطوة. شغّل كل أمر تحقّق وتأكّد من النتيجة قبل
> الانتقال. عند أي شرط STOP توقّف وأبلغ. عند الانتهاء حدّث صفّ الخطة في `plans/README.md`.
>
> **فحص الانحراف (شغّله أولًا)**:
> `git diff --stat a6457bf..HEAD -- ignition_e2_assemble.py ignition_live.py Super_stock.py test_bot.py`

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW (طبقة قياس بحتة — خارج التنبيه/الفرز/الحالة)
- **Depends on**: `plans/001-characterization-baseline.md`
- **Category**: bug
- **Planned at**: commit `a6457bf`, 2026-07-28

## Why this matters

`CLAUDE.md` يوثّق قاعدة فيصل ⏱️ «ربع الساعة» (JZ‑1س: «لو أعطاك المضارب مجالًا وتذبذبًا
أكثر من ربع ساعة فهي رفعة مضارب؛ وإلا رفعة بلا إذن») ويقول إنها **وُصِلت**:
«`_fire_sustain` في `record_ignition_fires` عند نهاية الجلسة حصرًا». الواقع أن الوصلة
**ميتة في الإنتاج لسببين مستقلَّين**، فالحقل `operator_ok` لا يُكتب أبدًا وسطر التصنيف في
تقرير التطوير (`Super_stock.py:9635-9641`) لا يظهر إطلاقًا.

الأسوأ أن **اختبارات الوحدة خضراء** (`test_bot.py:7354-7364`) لأنها تحقن الجالب وحقل
الطابع الزمني معًا — وهذا بالضبط صنف «اختبار ينجح رغم أن نقطة الاستعمال الحية مكسورة».

المكسب: التصنيف الذي بُني لمعايرة عتبات المضارب يبدأ فعلًا بجمع بيانات، وهو مطلوب قبل
أي قرار على عتبات `IGNITION_USD_*`. **لا يغيّر أي تنبيه.**

## Current state

### السبب الأول: المقاطع لا تنادي `record_ignition_fires` أصلًا

`ignition.yml` يشغّل الرادار دائمًا بـ`IGNITION_SEGMENT: "open"` ثم `"close"`
(`.github/workflows/ignition.yml:56,105`). في `ignition_live.py`:

```python
624    if role:
625        try:
626            if recorder is not None and recorder.alive and session_fires:
627                _fires = [{"symbol": ..., "price": ..., "vol_x": ..., "usd": ...,
628                           "stop": ..., "t1": ...} for r in session_fires]
632                with open(os.path.join(recorder.dir, "segment_fires.json"), "w", ...) as fh:
633                    json.dump({"session_date": session_day, "segment": window["role"],
634                               "fires": _fires}, fh)
...
636    else:
637        # الجلسة الواحدة (القديمة، توافق خلفي) — تسجّل وتدفع كما كانت.
...
647                n_rec = bot.record_ignition_fires(
648                    session_fires, session_day, fetch_bars=bot.polygon_minute_bars)
```

⇒ الفرع `else` (الذي يمرّر `fetch_bars`) **لا يُنفَّذ في الإنتاج إطلاقًا**.
و`segment_fires.json` المكتوب في السطر 632 **لا قارئ له في المستودع كلّه** (تأكّد
بـ`grep -rn segment_fires .`) — فهو artifact ميت أيضًا.

### السبب الثاني: الـassembler ينادي بلا جالب وبلا طابع زمني

`ignition_e2_assemble.py:290-297`:

```python
290        fires = [({"symbol": c.get("symbol"), "stop": [c.get("stop")], "t1": c.get("t1"),
291                   "pivot": c.get("pivot"), "last_price": c.get("signal_price"),
292                   "interp": {"critical_number": {"price": c.get("break_level")}}},
293                  {"price": c.get("signal_price"), "vol_x": c.get("vol_x"),
                      "usd": c.get("signal_usd")},
294                  None) for c in cands if c.get("alert_emitted")]
295        if fires:
296            bot.record_ignition_fires(fires, session_date)
```

- لا `fetch_bars` ⇒ الشرط في `Super_stock.py:9458` يُرجع `{}` فورًا.
- ولا `fired_ts_ms` في قاموس السهم ⇒ نفس السطر يُرجع `{}` حتى لو مُرِّر الجالب.

`Super_stock.py:9450-9469`:

```python
9455        lvl = _ignition_break_level(s)
9456        # (السطر التالي)
9457        t0 = s.get("fired_ts_ms")
9458        if not fetch_bars or not lvl or not t0:
9459            return {}
9460        bars = fetch_bars(s.get("symbol"), minutes=int(need_min) * 30)
...
9463        after = [b for b in bars if (b.get("t") or 0) >= float(t0)]
9464        su = operator_sustain(after, lvl, min_minutes=need_min)
```

### المصدر المتوفّر للطابع الزمني

مسجّل القياس يكتب في كل candidate الحقلَين `telegram_sent_at_ms` و`trigger_bar_start`
(`ignition_measurement.py:454,481,588`). `ignition_live.py:575` يستعمل
`int(time.time()*1000)` في المسار القديم، وهو معادل دلاليًّا لـ`telegram_sent_at_ms`.
⇒ **`telegram_sent_at_ms` هو المصدر الصحيح**، و`trigger_bar_start` احتياط.

### توفّر المفتاح في جوب الـassembler

`.github/workflows/ignition.yml:146-149`:

```yaml
      - name: Assemble session (merge + post-close backfill)
        env:
          POLYGON_API_KEY: ${{ secrets.POLYGON_API_KEY }}   # لـbackfill بعد الإغلاق
        run: python ignition_e2_assemble.py
```

⇒ `bot.polygon_minute_bars` سيعمل هناك. والـassembler يعمل **بعد الإغلاق** فالدقائق
اللاحقة موجودة فعلًا (بخلاف لحظة الإطلاق).

### قيد النطاق (من `CLAUDE.md`)

`operator_sustain` و`_fire_sustain` **مقفولتان خارج جذور الاختيار** باختبار
`getsource` (`test_bot.py:7370-7371`). **لا تنقلهما ولا تستدعهما من أي جذر.** هذه الخطة
تبقيهما في طبقة القياس تمامًا.

## Commands you will need

| الغرض | الأمر | المتوقّع |
|-------|-------|----------|
| تثبيت | `pip install -r requirements.txt` | exit 0 |
| بوّابة الاختبار | `python3 test_bot.py; echo "EXIT=$?"` | `EXIT=0` · «0 فشل» |
| تأكيد موت الـartifact | `grep -rn "segment_fires" --include="*.py" --include="*.yml" .` | مطابقة واحدة فقط في `ignition_live.py` |
| فحص صياغة | `python3 -c "import ast,sys;[ast.parse(open(f,encoding='utf-8').read()) for f in ('ignition_e2_assemble.py','Super_stock.py')]"` | exit 0 |

## Scope

**In scope**:
- `ignition_e2_assemble.py`
- `test_bot.py` (إضافة اختبارات)
- `plans/README.md`

**Out of scope**:
- `Super_stock.py` — `_fire_sustain` و`record_ignition_fires` و`operator_sustain`
  **لا تُعدَّل**؛ توقيعاتها صحيحة والعطل في نقطة النداء.
- `ignition_live.py` — لا تلمسه. الفرع `if role:` صحيح بقرار معماري موثّق
  (`ignition.yml:150-157`: «الـassembler وحده يدفع مرة واحدة»).
- `.github/workflows/ignition.yml` — المفتاح موجود سلفًا.
- أي تغيير على شرط الإطلاق/العتبات/نصّ التنبيه.

## Git workflow

- الفرع: `advisor/002-fire-sustain`
- كوميت واحد، مثال:
  `⏱️ إحياء قياس «ربع الساعة»: الـassembler كان ينادي record_ignition_fires بلا جالب ولا طابع`
  + `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- **لا push ولا PR.**

## Steps

### Step 1: مرّر الطابع الزمني والجالب من الـassembler

في `ignition_e2_assemble.py`، عدّل بناء `fires` (السطور 290-296) بحيث:

1. يضيف `"fired_ts_ms"` إلى قاموس السهم، مأخوذًا من
   `c.get("telegram_sent_at_ms") or c.get("trigger_bar_start")` — **بهذا الترتيب**
   (وقت الإرسال الفعلي أصدق؛ بداية شمعة الزناد احتياط).
2. يمرّر `fetch_bars=bot.polygon_minute_bars` إلى `record_ignition_fires`.

أضِف تعليقًا عربيًّا فوق التعديل يشرح **لماذا** (على نمط المستودع)، يذكر: أن هذا هو
النداء الوحيد الحيّ لأن المقاطع لا تسجّل، وأن المفتاح متوفّر في هذا الجوب، وأن الـassembler
يعمل بعد الإغلاق فالدقائق اللاحقة موجودة.

⚠️ **لا تُسقط `if fires:`** ولا تغيّر شرط `c.get("alert_emitted")` — الأساس `emitted`
قرار موثّق (انظر `e2_recover.py:131-139`).

⚠️ الكتلة كلها داخل `try/except` قائم (`ignition_e2_assemble.py:284,298`) — **أبقِها
كذلك**: أي فشل شبكة هنا يجب ألّا يُسقط الـassembler.

**Verify**:
`python3 -c "import ast;ast.parse(open('ignition_e2_assemble.py',encoding='utf-8').read())"` → exit 0
و`grep -n "fired_ts_ms" ignition_e2_assemble.py` → مطابقة واحدة على الأقل
و`grep -n "fetch_bars=bot.polygon_minute_bars" ignition_e2_assemble.py` → مطابقة واحدة.

### Step 2: اختبار طرف-لطرف بلا شبكة

أضِف في نهاية `test_bot.py` كتلة تحت `# ===== خطة 002: ربع الساعة في الـassembler =====`:

استورد الـassembler كوحدة (`import ignition_e2_assemble as A`) وابنِ اختبارًا **نقيًّا**
لدالّة بناء `fires`. إن كان بناء `fires` مضمّنًا داخل `main()` وغير قابل للاستدعاء
مستقلًّا، **استخرجه أولًا** إلى دالّة صغيرة نقيّة في `ignition_e2_assemble.py`، مثلًا:

```python
def _fires_from_candidates(cands):
    """يبني وسائط record_ignition_fires من candidates.jsonl. نقيّة وقابلة للاختبار.
    ⏱️ fired_ts_ms إلزامي وإلا يُرجع _fire_sustain قاموسًا فارغًا (قياس ربع الساعة ميت)."""
```

ثم ينادي `main()` هذه الدالّة. (هذا استخراج بلا تغيير سلوك — مسموح داخل النطاق.)

الاختبارات المطلوبة:
1. candidate فيه `telegram_sent_at_ms` ⇒ `fires[0][0]["fired_ts_ms"]` يساويه.
2. candidate بلا `telegram_sent_at_ms` وفيه `trigger_bar_start` ⇒ يُستعمل الاحتياط.
3. candidate بلا الاثنين ⇒ `fired_ts_ms` يساوي `None` (ولا يرمي).
4. candidate بـ`alert_emitted=False` ⇒ **لا يظهر** في `fires`.
5. **الاختبار الحاسم (طرف-لطرف):** مرّر مُخرَج `_fires_from_candidates` إلى
   `S.record_ignition_fires(fires, "2026-07-28", fetch_bars=<جالب مزيّف>)` حيث الجالب
   يُرجع شموعًا ثابتة فوق `break_level` لمدة ≥`CONFIG["OPERATOR_SUSTAIN_MIN"]` دقيقة،
   وأكّد أن السجلّ الناتج يحوي `operator_ok is True` و`sustain_min >= 15`.

   ⚠️ `record_ignition_fires` تكتب `IGNITION_LOG_FILE` عبر `_atomic_write_json`. لتجنّب
   الكتابة على ملف المستودع، بدّل `S.IGNITION_LOG_FILE` مؤقّتًا لمسار داخل
   `tempfile.mkdtemp()` وأعِد القيمة الأصلية بعد الاختبار، واحذف الملف المؤقّت.
   **STOP** لو لم تستطع ضمان ذلك — لا تكتب على `ignition_log.json` الحقيقي.

**Verify**: `python3 test_bot.py; echo "EXIT=$?"` → `EXIT=0` · «0 فشل» ·
و`git status --porcelain ignition_log.json` **فارغ**.

### Step 3: اختبار الطفرة (إلزامي)

1. أزِل `fetch_bars=bot.polygon_minute_bars` من نداء الـassembler → يجب أن يسقط اختبار
   الحالة 5. أرجِعها.
2. غيّر مصدر `fired_ts_ms` إلى `None` ثابتة → يجب أن يسقط اختبارا الحالة 1 و5. أرجِعه.

احكم برمز الخروج **والسطر الأخير** معًا:
`python3 test_bot.py; echo "EXIT=$?"` ⇒ `EXIT` غير صفري **و** «N فشل» بعدد > 0.

**Verify**: بعد إرجاع الطفرتين → `python3 test_bot.py; echo "EXIT=$?"` → `EXIT=0` · «0 فشل».

### Step 4: وثّق الحقيقة في `CLAUDE.md` و`HANDOFF.md`

`CLAUDE.md` يقول اليوم إن «ربع الساعة **وُصِلت**». صحّح الجملة بحيث تذكر أن الوصلة كانت
**ميتة في الإنتاج** حتى هذا الإصلاح، وأن النداء الحيّ الوحيد هو الـassembler، وأن
`segment_fires.json` بلا قارئ. أضِف سطرًا مقابلًا في `HANDOFF.md` بنفس الأسلوب.

> 🔴 المستودع يوثّق تصحيحاته الذاتية صراحةً («تصحيح ذاتي») — اتّبع نفس الصياغة ولا تحذف
> النصّ القديم بل صحّحه معلَّمًا.

**Verify**: `grep -n "ربع الساعة" CLAUDE.md HANDOFF.md` يُظهر النصّ المصحَّح.

## Test plan

- **الملف**: `test_bot.py` (إضافة في النهاية).
- **النمط المرجعي**: `test_bot.py:7334-7371`.
- **التغطية**: 5 اختبارات (الحالات أعلاه) + طفرتان مُوثَّقتان في رسالة الكوميت.
- **التحقّق**: `python3 test_bot.py` → exit 0 · «0 فشل» · العدد زاد ≥5.

## Done criteria

- [ ] `python3 test_bot.py; echo "EXIT=$?"` → `EXIT=0` · «0 فشل»
- [ ] `grep -n "fetch_bars=bot.polygon_minute_bars" ignition_e2_assemble.py` → مطابقة واحدة
- [ ] `grep -n "fired_ts_ms" ignition_e2_assemble.py` → مطابقة واحدة على الأقل
- [ ] `git diff a6457bf..HEAD -- Super_stock.py ignition_live.py .github/` **فارغ**
- [ ] `git status --porcelain ignition_log.json ignition_universe.json weekly_watchlist.json` **فارغ**
- [ ] الطفرتان في الخطوة 3 أُجريتا وأسقطتا الاختبارات ثم أُرجعتا (موثّق في الكوميت)
- [ ] `CLAUDE.md` و`HANDOFF.md` يذكران التصحيح
- [ ] صفّ 002 في `plans/README.md` محدَّث

## STOP conditions

- مقتطفات «الحالة الحالية» لا تطابق الكود الحيّ.
- وجدت أن `record_ignition_fires` **تُنادى فعلًا** من مكان ثالث حيّ في الإنتاج
  (تأكّد بـ`grep -rn "record_ignition_fires" --include="*.py" .`) ⇒ التشخيص انحرف، أبلغ.
- لم تستطع منع الاختبار من الكتابة على `ignition_log.json` الحقيقي.
- وجدت نفسك مضطرًّا لتعديل `Super_stock.py` أو `ignition_live.py` أو أي `.yml`.
- فكّرت في تشغيل `ignition.yml` أو أي workflow حيّ للتحقّق — **ممنوع**؛ التحقّق بالاختبارات فقط.

## Maintenance notes

- لو أُعيد يومًا تشغيل الرادار في «الجلسة الواحدة» (`IGNITION_SEGMENT` فارغ)، فالمسار
  القديم في `ignition_live.py:636-659` يمرّر الجالب أصلًا — لا ازدواج ولا تعارض.
- المراجِع يدقّق: أن الشرط `alert_emitted` لم يتغيّر · أن `try/except` حول الكتلة باقٍ ·
  أن لا نداء شبكة أُضيف داخل خيط التنبيه (الـassembler جوب منفصل بعد الإغلاق).
- **مؤجَّل عمدًا**: حذف `segment_fires.json` الميت من `ignition_live.py:626-633` — تُركت
  للخطة 011 (تنظيف) حتى لا تخلط تنظيفًا بإصلاح.
- بعد أسابيع من الجمع: سطر «⏱️ ربع الساعة» في تقرير التطوير سيبدأ بالظهور. **لا يُبنى
  عليه قرار عتبات قبل بلوغ `IGNITION_OUTCOME_MIN` وموافقة المالك** (قاعدة `CLAUDE.md`).
