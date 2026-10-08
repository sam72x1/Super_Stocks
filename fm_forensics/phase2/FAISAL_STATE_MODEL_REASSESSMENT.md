# FAISAL_STATE_MODEL_REASSESSMENT — Phase 1's FOCUS→WATCH→READY→TRIGGER re-tested against the corpus (2026-10-08)

> Method: each state and each transition is re-tested against (a) the 14 images visually re-verified in Phase 2, (b) the 64 of Phase 1, and (c) the inventory decision labels (769 rows). Future price movement is never used as evidence of a state. Verdict per state: CONFIRMED · MODIFIED · REJECTED · INSUFFICIENT_EVIDENCE.

| State | Phase 1 definition | Re-test evidence (DIRECT unless noted) | Verdict |
|---|---|---|---|
| **Focus** (selection + repeated attention) | persistent list; inputs: founding event, prior liquidity, validity filters | X_22_pipeline («قائمتي / تحت الجاهزية / جاهز 100%»); X_checklist_7points (7 explicit selection questions incl. «تاريخ التقسيم», news, groups, short); TG_1824 (LNAI card: split date, liberation high, low, float, news); TG_2191 (EZRA «متابعة 2 … متابعة فقط»); TG_1821 (owner/third-party screener + «تأكد ما فيه قروبات»); TG_2103 (CRE open 2025-08) | **CONFIRMED** — and refined: the focus card is anchored on the **split date** (TG_1807 «حقق متوسط 30 يوم من تاريخ التقسيم»; TG_1811/TG_1813 «قسمة أعلى شمعة أول افتتاح بعد التقسيم ÷2»). The reference regime starts at the split, not at a 52-week high. |
| **Watch** (base holds, test bounce, retest) | 3–5 sessions hold; bounce 10–20%; retest | X_13_NUWE («قاع ⟵ صعود اختبار مقاومة ⟵ هبوط اختبار دعم» · «الآن إما ثبات ع الدعم الأول = تحميل، أو كسره لسحب السيولة»); IMG_0689 («مراقبة الدعم 2.72 … لانتظار الماركت وتحقيق ضغط أو اكتفى بالدعم»); TG_2185 (DRCT «متابعة الضغط للشمعة الساقطة · ثبات إيجابي عدم ثبات سلبي»); TG_1819/IMG_0151 («حافظ ع قاعه 3 جلسات»); X_checklist («أدنى شمعة 5 جلسات هل كسرها») | **CONFIRMED** |
| **Ready** (technically ready) | zone + hold + RSI ≤ ~33 + indicators | TG_2218/TG_2089 («جاهز ع جميع المؤشرات والشموع … بانتظار فقط دخول المضارب»); TG_1810/TG_2042 («أسهم الدورة الزمنية تكون في مناطق تشبع بيعي RSI»); X_checklist («RSI تشبع بيعي ع اليومي ما دون 30 · ثبات السعر أعلى من متوسط 30-50»); TG_57884 (Faisal shows the owner's app card «الدعم المعتمد 2.26 · 64/100») | **CONFIRMED** — Ready is a *state* that explicitly waits for the operator. |
| **Trigger** (operator pressure) | sweep 7–13% then reclaim | TG_57894 (DKI «الشراء بعد المسح»), WA_31, TG_58417 (both SXTC entries after pressure), TG_2097 (ABC), TG_57870 (90%), TG_57879 (KSA «سحب السيولة −25% ثم العودة فوق الدعم 2.26» → Faisal ✅), TG_57884 («الموجات الهابطة −25% بعد اختبار المقاومة») · **counter-branch:** X_13_NUWE and IMG_0689 accept **hold at the first support without a sweep** («ثبات ع الدعم الأول = إيجابية تحميل مشاركات أو كسره لسحب السيولة») | **MODIFIED** — Trigger = *either* (a) hold at the first support with loading (operator absorbs) *or* (b) sweep below it then reclaim. The sweep depth is not fixed (7–13% EDU; 10% EHGO; −25% CIIT) → no fixed number. |
| **Entry** (orders) | tranches at support, not from the ask; buy after the trigger | TG_1811 («الدخول أثناء تحقيق القاعدة طلبات وعدم شرا من العرض»), IMG_0291 («أخذته من العرض الليلي» = counter), TG_1807 («الدخول 1.70>1.80» after MA30 reached) | **CONFIRMED (mechanics contested)** — distinct from Trigger: entry is the order placement, trigger is the market event. |

## Transition checks
- Focus → Watch: via MA30 from the split date / base formation (TG_1807, TG_1811) — CONFIRMED.
- Watch → Ready: indicators + hold (TG_2218, X_checklist) — CONFIRMED.
- Ready → Trigger: operator event, two forms (above) — MODIFIED.
- Trigger → Entry: orders at support (TG_1811) — CONFIRMED.
- Exit → Watch loop: X_24_SXTC, TG_58417 — CONFIRMED (one ticker, two waves; other tickers: TG_1807 «صعد وغطى شموعه» single wave).
- Invalidation: deeper break → new base (X_20260905_10/07, IMG_0689 «كسره = ذهاب إلى دعوم أخرى») — CONFIRMED.
- Abandonment: still INSUFFICIENT_EVIDENCE (no image shows a drop decision).

## Net result
Phase 1 model survives with one modification (Trigger has a no-sweep branch) and one refinement (Focus is anchored on the split date = Faisal's chart reference regime). No state is rejected. The modification matters for the root-cause question: a bot that requires a sweep before READY would be *more* wrong than one that doesn't; what Faisal requires is an operator read at the first support, which no daily-bar tool can see.
