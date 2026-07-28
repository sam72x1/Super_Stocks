# -*- coding: utf-8 -*-
"""🔬 مِجَسّ «النقل من OTC» — **مؤقّت، يُحذف بعد قراءة نتيجته.**

السؤال (فيصل TG_2077: «هل السهم صاعد سابقًا أو هابط أو مقسم أو طرح أو **نقل من otc**»):
هل نضيف «النقل من OTC» حدثًا مؤسِّسًا ثالثًا بجانب التقسيم العكسي والطرح الجديد؟

**لا يُجاب بالتقدير.** المِجَسّ يحسم ثلاثة أسئلة بتشغيلة واحدة:

  ① **هل الإشارة موجودة أصلًا؟** نموذج SEC `8-A12B` = تسجيل ورقة في **بورصة**
     (المادة 12(b)). هل يظهر فعلًا في `data.sec.gov/submissions` ويُقرأ تاريخه؟
  ② **هل هو مكرّر لما نلتقطه؟** المُنتقِل يُجبَر غالبًا على **تقسيم عكسي** (ليتجاوز
     حدّ السعر) و/أو **طرح** (لحقوق المساهمين) — وكلاهما منفَّذ عندنا. فلو كان كل
     مُنتقِل يحمل أحدهما ⇒ الوسم الثالث **يضيف صفرًا للاختيار**.
  ③ **هل تاريخ ياهو يشمل فترة OTC؟** لو لا، فالسهم يبدو بلا تاريخ ⇒ يسقط على
     M1/M2 (يحتاج انفجارًا ≥100% ثم انهيارًا ≥50%) **مهما وسمناه**.

⚠️ **حدّ صدق مُعلَن قبل النتيجة:** `8-A12B` يشمل **الاكتتابات الجديدة (IPO)** أيضًا،
فهو «سُجِّلت في بورصة» لا «انتقلت من OTC». التمييز يحتاج تاريخ تداول OTC سابقًا —
والمِجَسّ يقيسه بالسؤال ③ (تاريخ يسبق التسجيل = تداول سابق ⇒ الأرجح نقلٌ لا اكتتاب).

قراءة فقط · لا يمسّ الفرز ولا الحالة · لا يطبع أي سرّ.
"""
import datetime as dt
import os
import time

import requests

import Super_stock as S

SAMPLE = int(os.environ.get("OTC_SAMPLE") or 220)   # كم رمزًا نفحص
YEARS = int(os.environ.get("OTC_YEARS") or 3)       # نافذة «تسجيل حديث»


def _filings(cik):
    """قائمة (نموذج، تاريخ) لكل إيداعات الشركة الحديثة. فاشلة-آمنة → []."""
    try:
        r = requests.get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json",
                         headers=S.SEC_UA, timeout=40)
        r.raise_for_status()
        rec = ((r.json().get("filings") or {}).get("recent")) or {}
        return list(zip(rec.get("form", []) or [], rec.get("filingDate", []) or []))
    except Exception:                                        # noqa: BLE001
        return []


def main():
    print("🔬 مِجَسّ النقل من OTC — يقرأ فقط\n")
    uni = S.get_universe()
    print(f"كون ناسداك: {len(uni)} رمزًا")
    cmap = S.sec_cik_map()
    print(f"خريطة CIK: {len(cmap)} رمزًا\n")

    # عيّنة من صغار السعر (فئة الارتكاز) — نحمّل الأسعار مرّة واحدة
    hist = S.download_history(uni[:SAMPLE * 3])
    cheap = []
    for sym, df in (hist or {}).items():
        try:
            px = float(df["Close"].values[-1])
            if 0.3 <= px <= 12.0:
                cheap.append(sym)
        except Exception:                                    # noqa: BLE001
            continue
    cheap = cheap[:SAMPLE]
    print(f"عيّنة الفحص (سعر 0.3–12): {len(cheap)} رمزًا\n")

    cutoff = (dt.date.today() - dt.timedelta(days=365 * YEARS)).isoformat()
    found, no_cik, errs = [], 0, 0
    for i, sym in enumerate(cheap, 1):
        cik = cmap.get(sym.upper())
        if not cik:
            no_cik += 1
            continue
        fl = _filings(cik)
        if not fl:
            errs += 1
            continue
        reg = [(f, d) for f, d in fl
               if (f or "").strip().upper().startswith("8-A12") and d >= cutoff]
        if reg:
            reg.sort(key=lambda x: x[1], reverse=True)
            found.append({"sym": sym, "form": reg[0][0], "date": reg[0][1]})
        time.sleep(0.12)                                     # أدب SEC
        if i % 40 == 0:
            print(f"  … {i}/{len(cheap)} · وجدنا {len(found)}")

    print(f"\n① **الإشارة:** {len(found)} رمزًا لديه `8-A12*` خلال {YEARS} سنوات "
          f"(بلا CIK {no_cik} · أخطاء {errs})")
    if not found:
        print("   ⇒ الإشارة لا تظهر في العيّنة — لا أساس للبناء عليها.")
        return 0

    # ②+③ لكل مُسجَّل: تقسيم عكسي؟ طرح؟ وهل التاريخ يسبق التسجيل؟
    print("\n② **التكرار** و③ **تاريخ ما قبل الإدراج**:\n")
    print("| الرمز | النموذج | التاريخ | تقسيم عكسي حديث | طرح | تاريخ يسبق التسجيل |")
    print("|---|---|---|---|---|---|")
    n_split = n_off = n_hist = 0
    for f in found:
        sym = f["sym"]
        # تقسيم عكسي خلال ±180 يومًا من التسجيل
        rev = "—"
        try:
            sp = S.yf.Ticker(sym).splits if S.yf is not None else None
            if sp is not None and len(sp):
                rd = dt.date.fromisoformat(f["date"])
                hits = [str(d.date()) for d, v in zip(sp.index, sp.values)
                        if float(v) < 1.0
                        and abs((d.date() - rd).days) <= 180]
                rev = hits[-1] if hits else "لا"
                if hits:
                    n_split += 1
        except Exception:                                    # noqa: BLE001
            rev = "تعذّر"
        # طرح (نشرة نهائية) قرب التسجيل
        off = "—"
        try:
            fl = _filings(cmap.get(sym.upper()))
            ob = [d for fm, d in fl
                  if (fm or "").strip().upper() in ("424B1", "424B4", "424B5")]
            off = (max(ob) if ob else "لا")
            if ob:
                n_off += 1
        except Exception:                                    # noqa: BLE001
            off = "تعذّر"
        # تاريخ الأسعار: هل يبدأ قبل تاريخ التسجيل؟
        hb = "—"
        try:
            d0 = S.yf.download(sym, period="max", progress=False,
                               auto_adjust=False)
            if d0 is not None and len(d0):
                first = str(d0.index[0].date())
                hb = f"{first} {'✅' if first < f['date'] else '❌'}"
                if first < f["date"]:
                    n_hist += 1
        except Exception:                                    # noqa: BLE001
            hb = "تعذّر"
        print(f"| {sym} | {f['form']} | {f['date']} | {rev} | {off} | {hb} |")
        time.sleep(0.12)

    t = len(found)
    print(f"\n## الخلاصة العددية (على {t} مُسجَّلًا)\n")
    print(f"- يحمل **تقسيمًا عكسيًّا** قرب التسجيل: **{n_split}/{t}** "
          f"({100*n_split//max(1,t)}%)")
    print(f"- يحمل **طرحًا** (424B): **{n_off}/{t}** ({100*n_off//max(1,t)}%)")
    print(f"- تاريخ أسعاره **يسبق** التسجيل (⇒ تداول سابق، الأرجح نقل لا اكتتاب): "
          f"**{n_hist}/{t}** ({100*n_hist//max(1,t)}%)")
    print(f"\n⇒ **قرار الإضافة**: لو (تقسيم ∪ طرح) يغطّي ~كل المُسجَّلين فالوسم الثالث "
          f"مكرّر ⇒ يُسجَّل ولا يُنفَّذ. ولو بقيت شريحة معتبرة **بلا** أيٍّ منهما "
          f"**ومع تاريخ يسبق التسجيل** ⇒ يستحقّ التنفيذ."
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
