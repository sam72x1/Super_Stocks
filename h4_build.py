"""🕓 `h4_build` — بناءُ شموع الأربع ساعات من ملفّات الدقائق المجمّعة.

العقد: `h4_prereg.md` (‏مدفوعٌ قبل أيّ سطرِ كودِ أداة). **قياس/بحث فقط** —
`Super_stock.py` **لا يستوردها** (مقفول §⑧)، ولا تكتب حالةَ إنتاجٍ ولا ترسل.

⚖️ **اتفاقيةُ الدلاء (‏`§①`) مثبَّتةٌ ولا تُحرَّك:** بتوقيت نيويورك
‏[04:00, 08:00) · [08:00, 12:00) · [12:00, 16:00) · [16:00, 20:00) —
وهي **إعادةُ إنتاج** لا اختيار: تطابق `resample_ohlc(h1, "4h")` على فهرسٍ
نيويوركيّ، وتطابق نافذةَ `kasih_scan.parse_day` (`04:00 ≤ mod < 20:00`).
`O`=أوّل · `H`=أقصى · `L`=أدنى · `C`=آخر · `V`=مجموع · والدلوُ الفارغ
**يُسقَط ولا يُملأ**.

🔒 **وإعادةُ استعمالٍ لا نسخ:** التنزيلُ والقراءةُ وتحويلُ الطابع من
`ah_scan` **بالاسم** (`day_key` · `head_size_mb` · `download` · `ny_minute`
· `_pick`) — فلا يصير للمشروع محلّلا ملفّاتٍ مجمّعة.
"""
import gzip
import os
import pickle
import sys

import ah_scan as AH

H4_EDGES = (4 * 60, 8 * 60, 12 * 60, 16 * 60, 20 * 60)   # §① — لا تُحرَّك
CTRL = "AAPL"                                            # شاهدُ الضبط (`HV3`)


def bucket_of(mod):
    """فهرسُ دلوِ الأربع ساعات لدقيقةِ اليوم (نيويورك) — أو `None` خارج النافذة."""
    if mod is None:
        return None
    for i in range(4):
        if H4_EDGES[i] <= mod < H4_EDGES[i + 1]:
            return i
    return None


def fold_day(fh, universe):
    """يطوي ملفَّ يومٍ من الدقائق إلى دلاءِ 4س. يرجّع
    ‏{رمز: {دلو: [o, h, l, c, v, first_mod, last_mod]}} · ومجموعةَ الدلاء المرئية.

    **مسحةٌ واحدة** بلا تخزينِ الدقائق (يومٌ ‏≈27MB وملايينُ الصفوف)."""
    import csv
    rd = csv.reader(fh)
    header = next(rd)
    i_t = AH._pick(header, "ticker", "symbol")
    i_o = AH._pick(header, "open")
    i_h = AH._pick(header, "high")
    i_l = AH._pick(header, "low")
    i_c = AH._pick(header, "close")
    i_v = AH._pick(header, "volume")
    i_w = AH._pick(header, "window_start", "t", "timestamp")
    if min(i_t, i_o, i_h, i_l, i_c, i_v, i_w) < 0:
        raise KeyError(f"ترويسةٌ ناقصة: {header}")
    out, seen = {}, set()
    for row in rd:
        try:
            sym = row[i_t].strip().upper()
            ns = int(row[i_w])
            o, h = float(row[i_o]), float(row[i_h])
            lo, c = float(row[i_l]), float(row[i_c])
            v = float(row[i_v])
        except (IndexError, ValueError, TypeError):
            continue
        if not sym or (universe and sym not in universe and sym != CTRL):
            continue
        _day, mod = AH.ny_minute(ns)
        b = bucket_of(mod)
        if b is None:
            continue
        seen.add(b)
        d = out.setdefault(sym, {})
        cur = d.get(b)
        if cur is None:
            d[b] = [o, h, lo, c, v, mod, mod]
        else:
            if mod < cur[5]:
                cur[0], cur[5] = o, mod          # أوّلُ دقيقةٍ ⇒ الفتح
            if mod > cur[6]:
                cur[3], cur[6] = c, mod          # آخرُ دقيقةٍ ⇒ الإغلاق
            cur[1] = max(cur[1], h)
            cur[2] = min(cur[2], lo)
            cur[4] += v
    return out, seen


# ═══════════════════════════════════════════════════════════════════════════
# 🚪 `HV0` — **وضعُ التحقّق**: هل تطابق شموعُنا المبنيّة `fetch_4h` الحيّة؟
# ═══════════════════════════════════════════════════════════════════════════
# 🔴 **ولماذا وضعٌ مستقلّ:** `fetch_4h` يقرأ `period="60d"` ⇒ **لا يتقاطع مع
#    سنوات القياس (2023-2025) إطلاقًا** ⇒ لو كُتبت `HV0` داخل مسار السنة لكانت
#    **نيّةً لا حارسًا** (‏درسُ `LV0` في `libvol_result §④`). فتُقاس على أيامٍ
#    حديثةٍ داخل الستّين، والاتفاقيةُ المفحوصةُ **هي هي**.
VERIFY_DAYS = 10            # آخرُ عشر جلساتٍ داخل نافذة الستّين
VERIFY_SYMS = 8             # حجمُ العيّنة (‏`CTRL` + سحبٌ حتميّ)
VERIFY_TOL_PCT = 0.5        # §⑥ — التسامحُ المسجَّل
VERIFY_SCALE_TOL = 0.02     # انحرافُ مقياسٍ فوقه ⇒ تعديلُ تقسيم/توزيع ⇒ يُستبعَد ويُسمّى


def _verify_sample(universe):
    """عيّنةٌ **حتميّة**: شاهدُ الضبط ثمّ الأدنى هاشًا — نفسُ العيّنة كلَّ تشغيلة
    (‏سابقةُ `control_panel` المعتمَدة: بلا انتقاءٍ وبلا عشوائيّةٍ غيرِ قابلةٍ
    للإعادة)."""
    import hashlib
    pool = sorted(s for s in universe if s and s != CTRL)
    pool.sort(key=lambda s: hashlib.sha256(("h4v:" + s).encode()).hexdigest())
    return [CTRL] + pool[:max(0, VERIFY_SYMS - 1)]


def _live_buckets(sym):
    """‏{(يوم, دلو): (o,h,l,c)} من `fetch_4h` الإنتاجيّة **بالاسم** — أو `None`."""
    import Super_stock as S                                      # noqa: PLC0415
    h4 = S.fetch_4h(sym)
    if h4 is None or getattr(h4, "empty", True):
        return None
    out = {}
    for ts, row in h4.iterrows():
        t = ts
        try:
            t = ts.tz_convert("America/New_York") if ts.tzinfo else ts
        except Exception:                                        # noqa: BLE001
            pass
        b = bucket_of(t.hour * 60 + t.minute)
        if b is None:
            continue
        out[(t.strftime("%Y-%m-%d"), b)] = (
            float(row["Open"]), float(row["High"]),
            float(row["Low"]), float(row["Close"]))
    return out or None


def verify_main() -> int:
    """يبني أيامًا حديثةً لعيّنةٍ صغيرة ويقارنها بـ`fetch_4h` — بوّابةُ `HV0`."""
    import datetime as _dt
    if not (os.environ.get("AWS_ACCESS_KEY_ID") or "").strip():
        print("⛔ لا مفاتيح S3 — لا تحقّق (ولا يُخمَّن رقم).")
        return 2
    frozen = (os.environ.get("BT_FROZEN_PATH") or "").strip()
    universe = set()
    if frozen and os.path.exists(frozen):
        os.environ.setdefault("SCREENER_MODE", "BACKTEST")
        import Super_stock as S                                  # noqa: PLC0415
        hist, _sp, _asof = S.load_frozen_dataset(frozen)
        universe = set(hist or {})
    syms = _verify_sample(universe)
    print(f"🔎 عيّنةُ `HV0` الحتميّة ({len(syms)}): " + " · ".join(syms))

    today = _dt.date.today()
    days = [d for d in AH.trading_days(str(today - _dt.timedelta(days=50)),
                                       str(today - _dt.timedelta(days=2)))]
    days = days[-VERIFY_DAYS:]
    if len(days) < 3:
        print(f"⛔ أيامٌ غيرُ كافية للتحقّق ({len(days)}).")
        return 3
    print(f"📅 الأيامُ المفحوصة ({len(days)}): {days[0]} ⟵⟶ {days[-1]}")

    built = {s: {} for s in syms}
    got = []
    for day in days:
        key = AH.day_key(day)
        mb, ep = AH.head_size_mb(key)
        if mb is None:
            print(f"   ⚠️ {day}: لا ملفّ")
            continue
        dest = f"/tmp/h4v-{day}.csv.gz"
        if not AH.download(key, dest, ep):
            print(f"   ⚠️ {day}: تعذّر التنزيل")
            continue
        try:
            with gzip.open(dest, "rt") as fh:
                folded, _seen = fold_day(fh, set(syms))
        except (OSError, KeyError, ValueError) as e:
            print(f"   ⛔ {day}: {type(e).__name__}: {e}")
            folded = {}
        finally:
            try:
                os.remove(dest)
            except OSError:
                pass
        if folded:
            got.append(day)
        for s, bl in folded.items():
            for b, v in bl.items():
                built[s][(day, b)] = (v[0], v[1], v[2], v[3])

    tot_cmp = tot_ok = 0
    day_cnt_ok = day_cnt_all = 0
    used, skipped = [], []
    for s in syms:
        mine = built.get(s) or {}
        live = _live_buckets(s)
        if not mine or not live:
            skipped.append(f"{s}(بلا بيانات)")
            continue
        common = sorted(set(mine) & set(live))
        if len(common) < 8:
            skipped.append(f"{s}(تقاطع {len(common)})")
            continue
        # 📏 مقياسٌ وسيطٌ يعزل تعديلَ التقسيم/التوزيع (‏`auto_adjust=True` عند
        #    ياهو مقابل أسعارٍ خام في `minute_aggs`) — والمنحرفُ يُستبعَد ويُسمّى.
        ratios = sorted(live[k][3] / mine[k][3]
                        for k in common if mine[k][3] > 0)
        scale = ratios[len(ratios) // 2] if ratios else 1.0
        if abs(scale - 1.0) > VERIFY_SCALE_TOL:
            skipped.append(f"{s}(مقياس {scale:.3f} — تعديلٌ لا اتفاقية)")
            continue
        ok = 0
        for k in common:
            a, b_ = mine[k], live[k]
            if all(b_[j] > 0 and abs(a[j] * scale - b_[j]) / b_[j] * 100.0
                   <= VERIFY_TOL_PCT for j in range(4)):
                ok += 1
        tot_cmp += len(common)
        tot_ok += ok
        dm, dl = {}, {}
        for (d, _b) in mine:
            dm[d] = dm.get(d, 0) + 1
        for (d, _b) in live:
            if d in dm:
                dl[d] = dl.get(d, 0) + 1
        for d in dm:
            if d in dl:
                day_cnt_all += 1
                day_cnt_ok += int(dm[d] == dl[d])
        used.append(f"{s}({ok}/{len(common)})")

    p_ok = (tot_ok / tot_cmp * 100.0) if tot_cmp else 0.0
    p_cnt = (day_cnt_ok / day_cnt_all * 100.0) if day_cnt_all else 0.0
    print(f"\n🚪 `HV0` — الأيامُ المبنيّة {len(got)}/{len(days)}")
    print(f"   المقارَنة: {' · '.join(used) if used else '—'}")
    if skipped:
        print(f"   المستبعَد ({len(skipped)}): {' · '.join(skipped)}")
    print(f"   دلاءٌ ضمن تسامح {VERIFY_TOL_PCT}%: {tot_ok}/{tot_cmp} = "
          f"{p_ok:.1f}% {'✅' if p_ok >= 95.0 else '❌'}")
    print(f"   أيامٌ بعددِ دلاءٍ مطابق: {day_cnt_ok}/{day_cnt_all} = "
          f"{p_cnt:.1f}% {'✅' if p_cnt >= 95.0 else '❌'}")
    if len(used) < 3 or p_ok < 95.0 or p_cnt < 95.0:
        print("⛔ `HV0` ساقطة ⇒ خروج 3 — **عطبُ أداةٍ لا نتيجة**، "
              "ولا تُشغَّل الأذرعُ قبل عبورها.")
        return 3
    print("✅ `HV0` تعبر — اتفاقيةُ الدلاء تُعيد إنتاجَ `fetch_4h` الحيّة.")
    return 0


def main() -> int:
    if not (os.environ.get("AWS_ACCESS_KEY_ID") or "").strip():
        print("⛔ لا مفاتيح S3 — لا بناء (ولا يُخمَّن رقم).")
        return 2
    year = (os.environ.get("H4_YEAR") or "").strip()
    if not year:
        print("⛔ لا `H4_YEAR`.")
        return 2
    # 🔒 الكونُ من اللقطة المجمَّدة نفسِها ⇒ `D0` و`H1` على **نفس المجتمع**
    #    (الميزانيةُ الثابتة — قاعدةُ `karpathy/autoresearch` المعتمَدة).
    frozen = (os.environ.get("BT_FROZEN_PATH") or "").strip()
    universe = set()
    if frozen and os.path.exists(frozen):
        os.environ.setdefault("SCREENER_MODE", "BACKTEST")
        import Super_stock as S
        hist, _sp, asof = S.load_frozen_dataset(frozen)
        universe = set(hist or {})
        print(f"🧊 الكون من اللقطة: {len(universe):,} رمزًا · as-of {asof}")
    if not universe:
        print("⛔ كونٌ فارغ — اللقطةُ إلزاميّةٌ لتثبيت الميزانية.")
        return 2

    days = AH.trading_days(f"{year}-01-01", f"{year}-12-31")
    store, missing, day_buckets = {}, [], {}
    for day in days:
        key = AH.day_key(day)
        mb, ep = AH.head_size_mb(key)
        if mb is None:
            missing.append(day)
            continue
        dest = f"/tmp/h4-{day}.csv.gz"
        if not AH.download(key, dest, ep):
            missing.append(day)
            continue
        try:
            with gzip.open(dest, "rt") as fh:
                folded, seen = fold_day(fh, universe)
        except (OSError, KeyError, ValueError) as e:
            print(f"   ⛔ {day}: تعذّرت القراءة ({type(e).__name__}: {e})")
            missing.append(day)
            folded, seen = {}, set()
        finally:
            try:
                os.remove(dest)
            except OSError:
                pass
        if not folded:
            continue
        day_buckets[day] = sorted(seen)
        for sym, bl in folded.items():
            rows = store.setdefault(sym, [])
            for b in sorted(bl):
                o, h, lo, c, v, _f, _l = bl[b]
                rows.append((day, b, o, h, lo, c, v))
        if len(day_buckets) % 20 == 0:
            print(f"   … {len(day_buckets)}/{len(days)} يومًا · "
                  f"{len(store):,} رمزًا", flush=True)

    n_ok, n_all = len(day_buckets), len(days)
    cov = (n_ok / n_all * 100.0) if n_all else 0.0
    full4 = sum(1 for v in day_buckets.values() if len(v) == 4)
    p4 = (full4 / n_ok * 100.0) if n_ok else 0.0
    ctrl = [r for r in store.get(CTRL, [])]
    ctrl_days = {}
    for d, b, *_rest in ctrl:
        ctrl_days.setdefault(d, set()).add(b)
    ctrl4 = sum(1 for s in ctrl_days.values() if len(s) == 4)
    ctrl_vol_ok = all(r[6] > 0 for r in ctrl)
    p_ctrl = (ctrl4 / len(ctrl_days) * 100.0) if ctrl_days else 0.0

    print(f"\n🕓 H4 — سنة {year}")
    print(f"   🚪 `HV1` التغطية: {n_ok}/{n_all} = {cov:.1f}% "
          f"{'✅' if cov >= 95.0 else '❌'}")
    if missing:
        print(f"      المفقودُ بتواريخه ({len(missing)}): "
              + ", ".join(missing[:40]) + (" …" if len(missing) > 40 else ""))
    print(f"   🚪 `HV2` أيامٌ بأربعة دلاء: {full4}/{n_ok} = {p4:.1f}% "
          f"{'✅' if p4 >= 95.0 else '❌'}")
    print(f"   🚪 `HV3` شاهدُ الضبط {CTRL}: {ctrl4}/{len(ctrl_days)} = "
          f"{p_ctrl:.1f}% بأربعة دلاء · حجمٌ موجبٌ في الكلّ "
          f"{'✅' if ctrl_vol_ok else '❌'}")
    print(f"   📦 المخزون: {len(store):,} رمزًا · "
          f"{sum(len(v) for v in store.values()):,} شمعة 4س")
    if cov < 95.0 or p4 < 95.0 or p_ctrl < 95.0 or not ctrl_vol_ok:
        print("⛔ بوّابةٌ ساقطة ⇒ خروج 3 (عطبُ أداةٍ لا نتيجة).")
        return 3

    out = f"h4_{year}.pkl.gz"
    with gzip.open(out, "wb") as fh:
        pickle.dump({"year": year, "edges": H4_EDGES, "bars": store,
                     "days": sorted(day_buckets), "missing": missing}, fh, 4)
    print(f"✅ كُتب {out} ({os.path.getsize(out)/1e6:.1f}MB)")
    return 0


if __name__ == "__main__":
    _mode = (os.environ.get("H4_MODE") or "build").strip().lower()
    sys.exit(verify_main() if _mode == "verify" else main())
