# FAISAL_STATE_MACHINE — hypothesised states, with evidence class per transition (2026-10-08)

> Hypotheses, not facts. Each state/transition lists the images that support it and the confidence. "DIRECT" = Faisal's own words; "INFERRED" = from his examples; "OWNER" = the owner's testimony about Faisal.

```
UNSEEN ──(universe scan)──▶ SCREENED ──(فرز أول)──▶ FOCUS ──(فرز ثاني: متوسطات · شورت · أخبار)──▶ DEVELOPING
   DEVELOPING ──(القاع ثابت 3-5 جلسات · صعود اختبار 10-20% · رجوع يختبر الدعم)──▶ WATCH («تحت الجاهزية»)
   WATCH ──(جاهز ع جميع المؤشرات)──▶ READY («جاهز 100%» = technically ready, operator not yet)
   READY ──(ضغط المضارب · سحب سيولة 7-13% · استعادة)──▶ TRIGGERED
   TRIGGERED ──(طلبات عند الدعم بدفعات)──▶ ENTERED ──(هدف/خروج عند المقاومة الأولى)──▶ WATCH (re-entry loop)
   any ──(كسر القاع أعمق من مدى السحب · دخول قروبات · طرح معلّق · شورت فوق 20 ألف)──▶ INVALIDATED / ABANDONED
```

| Transition | Evidence | Class | Confidence |
|---|---|---|---|
| SCREENED→FOCUS→DEVELOPING ("فرز 1 / فرز 2 / جاهزية") | X_20260918_22_pipeline (2026-09-13): «متابعة قائمة فرز أول فرز ثاني جاهزية … تحقيق متوسطات شورت الخ تنقل السهم إلى فرز 2 · ضغط السهم بعد جميع ما ذكر نقل إلى جاهزية»; app tabs «قائمتي · الأسهم المملوكة · تحت الجاهزية · جاهز 100%» (X_23) | DIRECT | DIRECTLY_SUPPORTED |
| DEVELOPING→WATCH (base holds, test bounce, retest) | TG_50584 «نظرية الارتكاز» (stages 1–4); X_20260918_85_YMT («5 جلسات · 20% · يرجع يختبر الدعم — هذا أصل التحليل»); IMG_0486 (UPC: 3.10 held → +17% → retest = entry); TG_57870 («تجميع 2.10–2.30 … تحميل بعد سحب السيولة لا قبله») | DIRECT (3+ images) | STRONGLY_SUPPORTED |
| WATCH→READY (all indicators ready) | TG_2090 «جاهز ع جميع المؤشرات … بانتظار فقط دخول المضارب»; TG_1822 (technically complete, wait for operator); TG_1870/IMG_0531 «جاهز للانفجار» = RSI 22–27 + yearly bottom + oscillation 10–20% | DIRECT | DIRECTLY_SUPPORTED |
| READY→TRIGGERED (operator pressure / sweep / reclaim) | TG_57894 (DKI: «الشراء بعد المسح لا قبله · نهج ثابت بكل الأسهم»); WA_31 (SXTC: «بعد الضغط»); TG_58417 (both SXTC entries after pressure+sweep); TG_2097 («ABC لابد تتحقق»); TG_57870 («90% يحدث فيها سحب سيولة») | DIRECT (5 images, 3 tickers) | DIRECTLY_SUPPORTED |
| TRIGGERED→ENTERED (orders at support in tranches) | IMG_0569, X_85_YMT («طلبات فوارق 5 سنت عند الدعم»); counter: TG_1963, IMG_0291 (buy from the ask when liberated) | DIRECT, contested mechanics | SUPPORTED (mechanics informational) |
| ENTERED→exit at first resistance→WATCH (re-entry loop) | X_24_SXTC (exit at 3 then wait for retest); TG_58417/58418 (second wave 2.15–2.25) | DIRECT | STRONGLY_SUPPORTED (SXTC) · single-ticker |
| INVALIDATED: deeper break, groups, offering, short>20k | X_20260905_10/07, IMG_0512/0569 (break → new base); IMG_0488, TG_1835 (groups); X_kwm_offering, TG_50828 (offering); IMG_0150, TG_50578 (short) | DIRECT | SUPPORTED (V4 R4-INV/VAL rules) |
| ABANDONED (silent drop from list) | no image shows an explicit abandonment statement; list churn visible only between app screenshots | — | UNKNOWN |

### Is READY NOW a state, a trigger, or a bot-created abstraction?
- In Faisal's vocabulary "جاهز" is a **state** (technical readiness) that still waits for a **trigger** (operator pressure). Two layers (TG_2090, TG_1822, TG_57894).
- In the bot, `entry_status == ready_now` is a **price-location flag** on a selected member (`near_support`/`sweep_confirmed` and ≤ top tranche). It merges Faisal's WATCH and READY and ignores the trigger entirely, except through `sweep_confirmed` (a daily-bar sweep flag) which is the only trigger-like input.
- Verdict: **bot-created abstraction** that corresponds to Faisal's "inside the zone" condition (R4-ZONE-01), not to his READY (indicators + stability) nor to his TRIGGER (pressure). Confidence: STRONGLY_SUPPORTED by code reading + 5 direct images.

### What cannot be established from the corpus
- The duration Faisal keeps a stock in FOCUS before dropping it (no dated list diffs except 09-13).
- Whether his "فرز أول" is quantitative; only the second screen (averages, short, news) is named.
- How many FOCUS names exist at once (one screenshot: ≈12 visible rows).
