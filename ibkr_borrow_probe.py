"""🩺 مِجَسٌّ مؤقّت (2026-09-26 · يُحذف بعد القراءة): ملفُّ IBKR للاقتراض بالجملة.

**السؤال:** بوّابةُ المتاح (`borrow_gate_recheck` · حدُّ 20,000) عمياءُ حين يتعذّر
ChartExchange (‏14 من 14 مرشَّحًا في تجديد 09-26 دخلوا بلا متاح)، والموقعُ يحجب بعد
‏≈50 صفحة لكلّ رنر ⇒ جولاتُ التعبئة الأخيرة تمرّ مجهولةً بفائدة الشك. وChartExchange
نفسُه يعرض بيانات IBKR ⇒ هل ملفُّ IBKR العامّ (`ftp3.interactivebrokers.com` · مستخدم
`shortstock` · `usa.txt`) يصل من رنرات GitHub ويطابق عمودَ «Available»؟

**قراءةٌ فقط · بلا سرّ · بلا تلغرام · لا يكتب حالة.**

⚖️ **معيارُ الاعتماد مكتوبٌ قبل أيّ رقم** (لا يُرخى بعده) — يُعتمد مصدرًا **احتياطيًّا**
لمجهول البوّابة (بعد صفّ الحصّاد · وChartExchange يبقى المرجعَ الأوّل بقرار المالك
2026-07-10) **فقط إذا عبرت الثلاثة معًا:**
- `R1` الوصول: التنزيلُ ينجح خلال 60 ثانية ويُحلَّل منه 5,000 صفٍّ فأكثر.
- `R2` التغطية: 90% فأكثر من رموز حصاد اليوم (متاحُ ChartExchange معلوم) موجودةٌ في الملف.
- `R3` اتّفاقُ قرار البوّابة: 95% فأكثر من الرموز ذات القيمتين تتّفق على «فوق 20,000».
ووصفيٌّ لا يحكم: نسبةُ التطابق التامّ ووسيطُ الفرق النسبيّ.
"""
import ftplib
import io
import json
import statistics
import sys
import time

HOST = "ftp3.interactivebrokers.com"
USER = "shortstock"
FILE = "usa.txt"
GATE = 20000


def fetch(timeout=60):
    t0 = time.time()
    ftp = ftplib.FTP(HOST, timeout=timeout)
    ftp.login(USER, "")
    try:
        names = ftp.nlst()
    except Exception as e:                                   # noqa: BLE001
        names = [f"⚠️ nlst: {type(e).__name__}"]
    buf = io.BytesIO()
    ftp.retrbinary("RETR " + FILE, buf.write)
    try:
        ftp.quit()
    except Exception:                                        # noqa: BLE001
        pass
    return buf.getvalue(), time.time() - t0, names


def _num(s):
    s = (s or "").strip().replace(",", "")
    if not s:
        return None
    over = s.startswith(">")
    try:
        v = int(float(s.lstrip(">")))
    except ValueError:
        return None
    return v + 1 if over else v


def parse(raw: bytes):
    cols, rows, heads = None, {}, []
    for line in raw.decode("utf-8", "replace").splitlines():
        if line.startswith("#"):
            heads.append(line[:120])
            if line.startswith("#SYM"):
                cols = [c.strip() for c in line[1:].split("|")]
            continue
        if not cols:
            continue
        parts = line.split("|")
        rec = dict(zip(cols, parts))
        sym = (rec.get("SYM") or "").strip().upper()
        if not sym:
            continue
        rows[sym] = {"avail": _num(rec.get("AVAILABLE")),
                     "fee": rec.get("FEERATE"), "raw": rec.get("AVAILABLE")}
    return rows, heads


def harvest(path="ctb_log.jsonl"):
    out, last = {}, None
    with open(path, encoding="utf-8") as fh:
        rows = [json.loads(x) for x in fh if x.strip()]
    dates = sorted({r.get("date") for r in rows if r.get("date")})
    last = dates[-1] if dates else None
    for r in rows:
        if r.get("date") == last and r.get("shares_available") is not None:
            out[str(r["symbol"]).upper()] = r
    return out, last


def main():
    try:
        raw, secs, names = fetch()
    except Exception as e:                                   # noqa: BLE001
        print(f"⛔ R1 الوصول ساقط: {type(e).__name__}: {e}")
        return 2
    rows, heads = parse(raw)
    print(f"📥 {len(raw):,} بايت في {secs:.1f} ث · صفوف {len(rows):,} · ملفّات الجذر {names[:12]}")
    for h in heads[:4]:
        print("   ", h)
    r1 = secs <= 60 and len(rows) >= 5000
    hv, day = harvest()
    both, agree, exact, rel = 0, 0, 0, []
    miss = []
    for sym, r in sorted(hv.items()):
        ce = r.get("shares_available")
        ib = (rows.get(sym) or {}).get("avail")
        if ib is None:
            miss.append(sym)
            continue
        both += 1
        agree += int((ce > GATE) == (ib > GATE))
        exact += int(ce == ib)
        if ce:
            rel.append(abs(ib - ce) / ce * 100.0)
        print(f"   {sym:6} CE {ce:>11,} · IBKR {ib:>11,} ({(rows[sym] or {}).get('raw')})"
              f"{'' if (ce > GATE) == (ib > GATE) else '  ⚠️ قرارٌ مختلف'}")
    cov = both / len(hv) * 100.0 if hv else 0.0
    agr = agree / both * 100.0 if both else 0.0
    r2, r3 = cov >= 90.0, agr >= 95.0
    print(f"\n📋 حصادُ {day}: {len(hv)} رمزًا · في الملف {both} · غائب {len(miss)} {miss[:10]}")
    print(f"   تطابقٌ تامّ {exact}/{both} · وسيطُ الفرق النسبيّ "
          f"{statistics.median(rel):.1f}%" if rel else "   —")
    print(f"\n⚖️ R1 الوصول {'✅' if r1 else '❌'} · R2 التغطية {cov:.1f}% {'✅' if r2 else '❌'} · "
          f"R3 اتّفاقُ البوّابة {agr:.1f}% {'✅' if r3 else '❌'}")
    print("🧾 الحكم: " + ("يُعتمد احتياطًا لمجهول البوّابة" if (r1 and r2 and r3)
                         else "لا يُعتمد"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
