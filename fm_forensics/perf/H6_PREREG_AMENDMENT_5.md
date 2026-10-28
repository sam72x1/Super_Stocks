# H6 — AMENDMENT 5 (2026-10-28) · a late-arrival path for E5, by the owner's dated exception to §10

> The contract `H6_PREREG.md` stays **unchanged** (SHA-256 `a6f68f745cba189223b1f8258e733dc5e1e538382dfe6533307092d8e942c7ed`, pinned in
> `h6_test.py`). This file is **not** a tool-defect fix: it changes E5 for units whose image reached the bot late, and adds a control-matching
> rule for them. §10 forbids that without the owner; it is therefore a **dated owner exception** (precedent: amendment 1, F1).

## 1. The owner's order and approval (verbatim, 2026-10-28)
> «أضف قبل البدء تعديلًا مسجَّلًا لعقد H6: نافذة الخمس جلسات تُحكم بتاريخ النشر لكن الأهلية لا تسقط إذا وصلت الصورة متأخرة ما دام
> forward_date (ختم الجامع الآلي) قبل الحكم والشموع تُجلب تاريخيًا — العمى محفوظ بتجميد V4. اعرض التعديل نصًا قبل تطبيقه.»

The text of §2 was shown to the owner in full before it was applied. Approval, verbatim: **«طبّق التعديل 5 وابدأ الجزء ب.»** (m6 included.)

## 2. The operative text (Arabic, authoritative)
**م1 — المسارُ في وقته بلا تغيير:** وحدةٌ لها صفُّ جمعٍ في [T، T+5 جلسات] تبقى على العقد والتعديلات 1-4 **بت-بت** (E5-E7 والضوابط والعائلات الأربع).
**م2 — «متأخّرة» بدل «غير مغطّاة»:** وحدةٌ عبرت E1-E4 ولا صفَّ جمعٍ لها في [T، T+5 جلسات] تصير `ELIGIBLE_LATE` لا `NOT_COVERED` إذا تحقّقت الثلاثة:
  - (أ) **ختمُ الوصول آليّ:** لصورتها المحدِّدة صفٌّ `saved` في `telegram_collect_meta.jsonl` بطابعٍ آليّ A (حقلُ `date` وإلّا `collected_utc`) — لا تاريخٌ يكتبه أحد.
  - (ب) **قبل الحكم:** A أبكرُ من لحظة تشغيل `analyze` · ويومُ A ليس قبل T (صورةٌ وصلت قبل نشرها خطأُ تاريخٍ ⟵ `E1:date_ambiguous`).
  - (ج) **جُمعت بعد الوصول:** للسهم صفُّ جمعٍ في يومٍ لا يسبق يومَ A ولا يلي `analyze` — أوّلُه يومُ الجمع المتأخّر C′.
**م3 — الضوابطُ من نافذة القرار لا من يوم الوصول:** ضوابطُ الوحدة المتأخّرة من لوحة **أوّل يومِ تشغيلٍ في [T، T+5 جلسات]** حالتُها OK
(لا من لوحة C′) بالاستبعادات نفسِها وبحدٍّ أدنى 2 · وإلّا `NO_CONTROLS`. **E7 لا يُطبَّق** عليها (يحرس عائلةَ اللقطة A التي لا تُستعمل لها) ويُسجَّل تقسيمٌ بين T وC′ وصفًا.
**م4 — العائلاتُ للمتأخّرة:** B (الطرح) وD (عمرُ التقسيم) تُحسبان كما §5 حرفيًّا **مقابل T** (مؤرّختان من المزوّد). A (الفلوت) وC (المتاح)
**«لا تنطبق»** على الوحدة المتأخّرة وضوابطها — تُستبعد من بسط العائلة ومقامها (ليست `MISSING` ولا تُقدَّر) ⟵ A وC تُختبران على الوحدات في وقتها وحدَها كما العقد.
**م5 — الأرضيّةُ والتغطية:** الأرضيّةُ 15 تعدّ الوحداتِ في وقتها والمتأخّرةَ معًا · وقابليّةُ كلّ عائلة (تغطيةٌ 80% و15 وحدةً بقيمة) على الوحدات التي تنطبق عليها ·
والمتأخّرةُ ليست فشلَ تغطيةٍ في §7.
**م6 — حارسُ الانتقاء (تشديد):** عائلةٌ تُحكم `SUPPORTED` بالمجتمع كلِّه **لا تبقى كذلك** إن كان تقديرُها النقطيّ على الوحدات في وقتها وحدَها
(وفيها 5 فأكثر بقيمة) بإشارةٍ معاكسة ⟵ تُكتب `UNSUPPORTED (late-selection conflict)`. وسطرُ «في وقتها وحدَها» يُطبع بجوار كلّ عائلةٍ دائمًا.
**م7 — بت-بت:** بلا وحدةٍ متأخّرة مؤهَّلة يُطابق كلُّ رمزٍ وحالةٍ وتحليلٍ العقدَ والتعديلات 1-4.

## 3. Why the text is narrower than the order (stated, not hidden)
1. **H6 measures no candle.** «الشموع تُجلب تاريخيًا» applies to nothing in H6. Its four families are of two kinds (contract §5):
   B and D are **provider-dated** (SEC filing dates, split effective dates) and can be judged against T whenever they are collected;
   A and C are **snapshots of the collection day** — the contract forbids SEC `EntityPublicFloat` for A, and no dated history of
   available-to-borrow is reachable (iBorrowDesk unreachable from runners; ChartExchange shows today only). A float or borrow read on
   day C′ two weeks after T is «current data used as historical» (owner condition 5 of the contract) ⟵ m4 keeps A and C on-time only.
2. **There is no `forward_date` in the images that matter.** Every photo saved since 2026-10-08 (87: 4 + 61 + 22) has `forward_type: none`
   in `telegram_collect_meta.jsonl` — screenshots, not forwards. The machine stamp that exists is the message `date` / `collected_utc`.
   T (the publication day) stays the eye reading of the post's own date, exactly as E1 today. m2(a) uses the collector's stamp for the
   «arrived before the verdict» condition, which is what that stamp can prove.
3. **Blindness.** V4 is frozen (`freeze_id 5f291a3b…`), so a late image cannot tune the instrument. H6's own risk is different and is not
   removed by the freeze: a post sent late may be **chosen** after its move was seen. H6 features are not outcomes, but if B/D correlate
   with outcome, late selection biases them. m6 is a tightening (§10 allows tightening) that stops a late-driven SUPPORTED.

## 4. Before any number
- `h6_test.py status` prints no prevalence and no effect; `analyze` has never run (`out/H6_RESULT.json` absent) ⟵ this change is made
  before any feature number is seen.

## 5. Effect today and the bit-identical check (repository state of 2026-10-28, old vs new `build_status`, `today` = 2026-10-28)
- One unit changes path: **ANPA (CASE_0007, T 2026-10-14)** `NOT_COVERED (E5)` ⟵ candidate `ELIGIBLE_LATE`: images TG_76012/TG_76013
  sent 2026-10-27T13:15:37Z and saved 14:17Z (`forward_type: none`); Phase 6 ledger rows for ANPA: 42, all collected 2026-10-28 (C′);
  panels OK on 10-14 … 10-21 (16 tickers each, pool 2026-10-08) ⟵ m3 takes the panel of 10-14. Its label and controls are checked by the tool.
- **Measured:** 14 of 15 cases keep the same status and code. CASE_0007 (ANPA) `NOT_COVERED (E5:no_collection_within_5_sessions)` ⟵
  **`ELIGIBLE_LATE (E5L:late_arrival)`**: arrival 2026-10-27T13:15:37Z · C′ 2026-10-28 (lag 10 sessions) · controls from the panel of
  2026-10-14: CMTL · GMM · CTXR · VRXA · no reverse split between T and C′.
- Eligible units **3 ⟵ 4** of 15 (late 1). Coverage failures **1 ⟵ 0**. A and C are computed on the 3 on-time units; B and D on all 4.
  The status prints coverage counts only — no prevalence, no effect.
- 🔴 The lesson recorded on 2026-10-28 («a post that reaches us after its five sessions never counts in H6») is **replaced** by:
  «it counts for B and D only» — prompt sending is still what makes A and C (float, borrow) count.

## 6. Tool notes (how m1-m7 read in `h6_test.py`)
- `arrival_stamps(root)` reads `telegram_collect_meta.jsonl` (saved photos): image id ⟶ earliest `date` (else `collected_utc`).
- The late path runs only after the on-time window has closed (amendment 3 is unchanged) and only when `build_status` passes the stamps.
- Arrived but not yet collected ⟵ `PENDING_COLLECTION (E5L:arrived_<day>_awaiting_collection)` — counts toward nothing, like amendment 3.
- An arrival stamp at or after the run ⟵ `NOT_COVERED (E5:arrival_after_run)`. No panel in [T, T+5] ⟵ `NO_CONTROLS (E6:no_panel_day_in_decision_window)`.
- m6 threshold `LATE_SIGN_MIN = 5`; the on-time summary is stored for every family (`ontime`) and printed in the verdict.

## 7. Locks (in `test_bot.py`, before `LEAK0`)
- `H6L1` behavioural, synthetic root (`_h6_world` ‏+ a `telegram_collect_meta.jsonl`):
  - a late unit with an arrival stamp, a ledger row after arrival and a panel in [T, T+5] is `ELIGIBLE_LATE`: C′ 2026-10-28, controls from the
    panel of T's window (not C′);
  - A and C are computed on the 3 on-time units, B and D on all 4;
  - no stamp ⟵ `NOT_COVERED`; a stamp before T ⟵ `E1:date_ambiguous`;
  - no collection after arrival (none at all, or only before arrival) ⟵ `PENDING_COLLECTION`; no panel in the window ⟵ `NO_CONTROLS`;
  - the same call without stamps returns the old `NOT_COVERED`, and the on-time units stay `ELIGIBLE`.
- `H6L2` m6: `late_selection_conflict` is true at 5 on-time units with a negative effect only (4, zero and positive are false), `LATE_SIGN_MIN` = 5,
  and `analyze` turns SUPPORTED into `UNSUPPORTED (late-selection conflict)` from it and stores `ontime` for every family.
- **Mutations, 10 of 10 caught:**
  - H6L1: the late path skipped · the before-T check removed · collection days not bounded by arrival · controls from C′ · late units in A/C ·
    late units not counted · B added to the snapshot families.
  - H6L2: `LATE_SIGN_MIN` 4 · `<= 0` · the conflict not applied.
