# -*- coding: utf-8 -*-
"""
==========================================================
التحليل الفني الكلاسيكي الشامل (Classical TA Report)
==========================================================
الأداة الثالثة — مستقلة تماماً عن البوت الأساسي وعن التحليل اليدوي.
لا تعدّل أي ملف، لا تكتب أي حالة. تستورد الدوال الجاهزة فقط.

تكتب أي رمز سهم → تقرير فني كلاسيكي على 3 فريمات (شهري/أسبوعي/يومي):
  • التقييم الفني العام لكل فريم (صاعد قوي ← هابط قوي)
  • مؤشر القوة الفني من 100 (اجتهادي، مبني على أركان الكلاسيكي)
  • الدعم والمقاومة (محسوبة من القمم/القيعان المحورية)
  • المتوسطات 20/50/200 + التقاطع الذهبي/الموت
  • الزخم: RSI + MACD + كشف الدايفرجنس
  • الحجم كمؤكِّد
  • أسماء أنماط الشموع (صاعدة وهابطة) على كل فريم
  • خلاصة فنية محايدة (بلا "اشترِ/بِع")

التشغيل (عبر GitHub، مسار مستقل):
  متغير البيئة:  TICKER=AAPL   →   python technical_report.py
"""
import os
import numpy as np
import pandas as pd

try:
    import Super_stock as bot
except ImportError:
    import super_stock as bot


# ==========================================================
# تنبيه إعلان الأرباح القادم (من yfinance — بلا اشتراك)
# ==========================================================
import datetime as _dt

EARNINGS_WARN_DAYS = 7      # ضمن أسبوع → تحذير: الفني معلّق
EARNINGS_INFO_DAYS = 30     # ضمن شهر → معلومة فقط


def _to_date(x):
    """يحوّل أي صيغة تاريخ (date/datetime/Timestamp/نص) إلى date، أو None."""
    try:
        if isinstance(x, _dt.datetime):     # datetime / pandas Timestamp
            return x.date()
        if isinstance(x, _dt.date):         # date صِرف
            return x
        if hasattr(x, "date"):              # numpy datetime64 وغيره
            try:
                return x.date()
            except Exception:
                pass
        return _dt.date.fromisoformat(str(x)[:10])
    except Exception:
        return None


def _http_json(url, timeout=15):
    """يجلب JSON عبر urllib (بلا تبعيات). فاشل-آمن → None عند أي خطأ."""
    import urllib.request, json
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return None


def _http_text(url, timeout=30):
    """يجلب نصاً خاماً (CSV مثلاً) عبر urllib. فاشل-آمن → None عند أي خطأ."""
    import urllib.request
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", "replace")
    except Exception:
        return None


# تخزين مؤقت لتقويم Alpha Vantage: يُجلب مرة واحدة لكل تشغيل (نداء واحد لكل الشركات)
_AV_CACHE = {"loaded": False, "map": {}}


def _load_av_calendar():
    """يجلب تقويم الأرباح الكامل من Alpha Vantage مرة واحدة (CSV لكل الشركات)،
    ويبني خريطة {رمز → أقرب تاريخ أرباح قادم}. نداء واحد فقط لكل تشغيل
    (يحترم حد 25 طلب/يوم المجاني). فاشل-آمن: خريطة فارغة عند أي خطأ."""
    if _AV_CACHE["loaded"]:
        return _AV_CACHE["map"]
    _AV_CACHE["loaded"] = True  # علّمها محمّلة فوراً حتى لو فشلت (لا نكرر النداء)
    key = os.environ.get("ALPHAVANTAGE_KEY", "").strip()
    if not key:
        return _AV_CACHE["map"]
    url = ("https://www.alphavantage.co/query?function=EARNINGS_CALENDAR"
           f"&horizon=3month&apikey={key}")
    text = _http_text(url)
    if not text or "symbol" not in text.lower():
        return _AV_CACHE["map"]
    import csv, io
    try:
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            sym = (row.get("symbol") or "").strip().upper()
            d = _to_date(row.get("reportDate"))
            if not sym or not d:
                continue
            cur = _AV_CACHE["map"].get(sym)
            if cur is None or d < cur:   # نحتفظ بأقرب تاريخ لكل رمز
                _AV_CACHE["map"][sym] = d
    except Exception:
        pass
    return _AV_CACHE["map"]


def _earnings_from_alphavantage(sym):
    """تاريخ أرباح قادم للرمز من تقويم Alpha Vantage المخزّن مؤقتاً."""
    m = _load_av_calendar()
    d = m.get(sym.strip().upper())
    return [d] if d else []


def _earnings_from_fmp(sym):
    """تواريخ أرباح قادمة من Financial Modeling Prep (يحتاج FMP_API_KEY)."""
    key = os.environ.get("FMP_API_KEY", "").strip()
    if not key:
        return []
    url = ("https://financialmodelingprep.com/api/v3/historical/"
           f"earning_calendar/{sym}?apikey={key}")
    data = _http_json(url)
    out = []
    if isinstance(data, list):
        for row in data:
            d = _to_date(row.get("date")) if isinstance(row, dict) else None
            if d:
                out.append(d)
    return out


def _earnings_from_finnhub(sym):
    """تواريخ أرباح قادمة من Finnhub (يحتاج FINNHUB_API_KEY)."""
    key = os.environ.get("FINNHUB_API_KEY", "").strip()
    if not key:
        return []
    today = _dt.date.today()
    to = today + _dt.timedelta(days=120)
    url = (f"https://finnhub.io/api/v1/calendar/earnings?from={today}"
           f"&to={to}&symbol={sym}&token={key}")
    data = _http_json(url)
    out = []
    if isinstance(data, dict):
        for row in data.get("earningsCalendar", []) or []:
            d = _to_date(row.get("date")) if isinstance(row, dict) else None
            if d:
                out.append(d)
    return out


def _next_earnings_from_yf(tkr):
    """أقرب تاريخ أرباح قادم من كائن yfinance (احتياطي). يتحمّل الإصدارات."""
    cands = []
    try:
        cal = tkr.calendar
        ed = None
        if isinstance(cal, dict):
            ed = cal.get("Earnings Date")
        elif cal is not None:
            try:
                ed = cal.loc["Earnings Date"].tolist()
            except Exception:
                ed = None
        if ed is not None:
            if not isinstance(ed, (list, tuple)):
                ed = [ed]
            for x in ed:
                d = _to_date(x)
                if d:
                    cands.append(d)
    except Exception:
        pass
    try:
        df = tkr.get_earnings_dates(limit=12)
        if df is not None and len(df):
            for idx in df.index:
                d = _to_date(idx)
                if d:
                    cands.append(d)
    except Exception:
        pass
    return cands


def _next_earnings_date(sym):
    """أقرب تاريخ أرباح قادم (>= اليوم) للرمز. الأولوية:
    Alpha Vantage (تقويم شامل) ← yfinance (احتياطي). يرجع date أو None. فاشل-آمن."""
    today = _dt.date.today()
    cands = []
    # (1) Alpha Vantage — تقويم شامل بنداء واحد مخزّن مؤقتاً
    try:
        cands += _earnings_from_alphavantage(sym)
    except Exception:
        pass
    # (2) مصادر API إضافية اختيارية (تعمل فقط لو مفاتيحها موجودة)
    if not cands:
        try:
            cands += _earnings_from_fmp(sym)
        except Exception:
            pass
    if not cands:
        try:
            cands += _earnings_from_finnhub(sym)
        except Exception:
            pass
    # (3) احتياطي yfinance
    if not cands:
        yf = getattr(bot, "yf", None)
        if yf is not None:
            try:
                cands += _next_earnings_from_yf(yf.Ticker(sym))
            except Exception:
                pass
    future = sorted(d for d in cands if d >= today)
    return future[0] if future else None


def earnings_alert(sym):
    """يرجع (نص_السطر، تحذير؟). فاشل-آمن: عند أي خطأ → غير متوفر."""
    try:
        d = _next_earnings_date(sym)
    except Exception:
        d = None
    if d is None:
        return "📅 تاريخ الأرباح غير متوفر (تحقق يدوياً قبل القرار)", False
    days = (d - _dt.date.today()).days
    ds = d.isoformat()
    if days <= EARNINGS_WARN_DAYS:
        return (f"📅 ⚠️ إعلان أرباح خلال {days} يوم ({ds}) — "
                "الفني معلّق، الأأمن الانتظار حتى بعد الإعلان واستقرار السهم"), True
    if days <= EARNINGS_INFO_DAYS:
        return f"📅 إعلان أرباح بعد {days} يوم ({ds}) — لا خطر قريب", False
    return f"📅 إعلان الأرباح القادم بعد {days} يوم ({ds})", False


# ==========================================================
# أدوات محورية (قمم/قيعان) — أساس الاتجاه والدعم/المقاومة
# ==========================================================
def _pivots(values, order):
    """يرجع (مؤشرات القمم، مؤشرات القيعان) المحلية."""
    n = len(values)
    highs, lows = [], []
    for i in range(order, n - order):
        win = values[i - order:i + order + 1]
        mx, mn = float(np.max(win)), float(np.min(win))
        if values[i] == mx and np.sum(win == mx) == 1:
            highs.append(i)
        if values[i] == mn and np.sum(win == mn) == 1:
            lows.append(i)
    return highs, lows


def _order_for(n):
    if n >= 200:
        return 5
    if n >= 80:
        return 3
    return 2


def _swing_pivots(series, order):
    """قمم/قيعان حقيقية حتى مع اتجاه قوي: نزيل الميل (residual حول متوسط
    متحرك مركزي) ثم نبحث عن القمم/القيعان على الباقي. يرجع مؤشرات فعلية."""
    s = np.asarray(series, dtype=float)
    n = len(s)
    if n < 2 * order + 1:
        return [], []
    w = max(2 * order + 1, 11)
    ma = pd.Series(s).rolling(w, center=True, min_periods=1).mean().values
    resid = s - ma
    return _pivots(resid, order)


# ==========================================================
# 1) الاتجاه (Dow): قمم/قيعان صاعدة أم هابطة
# ==========================================================
def trend_of(df):
    high = df["High"].values.astype(float)
    low = df["Low"].values.astype(float)
    close = df["Close"]
    n = len(close)
    y = close.values.astype(float)

    # الأساس: ميل الانحدار الخطي كنسبة من متوسط السعر (متين ضد ضجيج الأطراف)
    x = np.arange(n, dtype=float)
    slope = float(np.polyfit(x, y, 1)[0])
    rel = slope * (n - 1) / max(float(np.mean(y)), 1e-9) * 100.0  # صافي الميل %

    # تفصيل Dow (HH/HL) إن توفّرت نقاط محورية كافية
    order = _order_for(n)
    hi_idx, _ = _swing_pivots(high, order)
    _, lo_idx = _swing_pivots(low, order)
    dow = None
    if len(hi_idx) >= 2 and len(lo_idx) >= 2:
        hh = high[hi_idx[-1]] > high[hi_idx[-2]]
        hl = low[lo_idx[-1]] > low[lo_idx[-2]]
        lh = high[hi_idx[-1]] < high[hi_idx[-2]]
        ll = low[lo_idx[-1]] < low[lo_idx[-2]]
        if hh and hl:
            dow = "up"
        elif lh and ll:
            dow = "down"
        else:
            dow = "mixed"

    if rel > 15:
        label = "صاعد"
    elif rel < -15:
        label = "هابط"
    else:
        label = "عرضي"

    # صياغة متّسقة: التفصيل يتوافق مع الاتجاه، والتعارض يُعرض كتصحيح قصير
    if label == "صاعد":
        if dow == "up":
            detail = "قمم وقيعان صاعدة (HH/HL)"
        elif dow == "down":
            detail = "اتجاه صاعد مع تصحيح قصير المدى"
        else:
            detail = "ميل صاعد"
    elif label == "هابط":
        if dow == "down":
            detail = "قمم وقيعان هابطة (LH/LL)"
        elif dow == "up":
            detail = "اتجاه هابط مع ارتداد قصير المدى"
        else:
            detail = "ميل هابط"
    else:
        detail = "نطاق عرضي (بلا اتجاه واضح)"
    return label, detail


# ==========================================================
# 2) الدعم والمقاومة (من القمم/القيعان المحورية + تجميع)
# ==========================================================
def _cluster(levels, tol=0.02):
    """يدمج المستويات المتقاربة (ضمن tol٪) في مستوى واحد (المتوسط)."""
    if not levels:
        return []
    levels = sorted(levels)
    out = [[levels[0]]]
    for lv in levels[1:]:
        if abs(lv / out[-1][-1] - 1.0) <= tol:
            out[-1].append(lv)
        else:
            out.append([lv])
    return [round(sum(g) / len(g), 2) for g in out]


def support_resistance(df, price):
    high = df["High"].values.astype(float)
    low = df["Low"].values.astype(float)
    order = _order_for(len(df))
    hi_idx, _ = _swing_pivots(high, order)
    _, lo_idx2 = _swing_pivots(low, order)
    res = _cluster([high[i] for i in hi_idx if high[i] > price * 1.005])
    sup = _cluster([low[i] for i in lo_idx2 if low[i] < price * 0.995])
    # الأقرب أولاً
    res = sorted(res)[:3]
    sup = sorted(sup, reverse=True)[:3]
    return sup, res


# ==========================================================
# 3) المتوسطات 20/50/200 + التقاطع الذهبي/الموت
# ==========================================================
def ma_analysis(close):
    n = len(close)
    out = {"ma20": None, "ma50": None, "ma200": None,
           "pos": [], "cross": None}
    price = float(close.iloc[-1])
    for p, key in ((20, "ma20"), (50, "ma50"), (200, "ma200")):
        if n >= p:
            val = float(close.rolling(p).mean().iloc[-1])
            out[key] = val
            out["pos"].append((p, "فوق" if price >= val else "تحت", val))
    # تقاطع ذهبي/موت (50 مقابل 200) خلال آخر ~15 شمعة
    if n >= 200:
        s50 = close.rolling(50).mean()
        s200 = close.rolling(200).mean()
        diff = (s50 - s200).dropna()
        if len(diff) >= 16:
            recent = diff.iloc[-15:]
            signs = np.sign(recent.values)
            if signs[0] < 0 and signs[-1] > 0:
                out["cross"] = "ذهبي (تقاطع 50 فوق 200) — إيجابي"
            elif signs[0] > 0 and signs[-1] < 0:
                out["cross"] = "موت (تقاطع 50 تحت 200) — سلبي"
            elif float(s50.iloc[-1]) >= float(s200.iloc[-1]):
                out["cross"] = "50 فوق 200 (هيكل صاعد)"
            else:
                out["cross"] = "50 تحت 200 (هيكل هابط)"
    return out


# ==========================================================
# 4) الزخم: RSI + MACD + الدايفرجنس
# ==========================================================
def momentum(close):
    rs = bot.rsi(close)
    rv = float(rs.iloc[-1])
    state = ("تشبع شرائي" if rv >= 70 else
             "تشبع بيعي" if rv <= 30 else "محايد")
    slope = "صاعد" if rv > float(rs.iloc[-2]) else "هابط"
    ml, msig = bot.macd(close)
    macd_state = ("إيجابي (الخط فوق الإشارة)"
                  if float(ml.iloc[-1]) >= float(msig.iloc[-1])
                  else "سلبي (الخط تحت الإشارة)")
    hist = float(ml.iloc[-1]) - float(msig.iloc[-1])
    return {"rsi": rv, "rsi_state": state, "rsi_slope": slope,
            "macd_state": macd_state, "macd_hist": hist}


def divergence(df):
    """دايفرجنس RSI على آخر نافذة: سعر قاع أدنى/RSI قاع أعلى = صاعد (والعكس)."""
    close = df["Close"]
    n = len(close)
    if n < 40:
        return None, ""
    win = min(60, n)
    seg_p = df["Low"].values.astype(float)[-win:]
    seg_ph = df["High"].values.astype(float)[-win:]
    rs = bot.rsi(close).values[-win:]
    order = 3
    # قيعان/قمم سعرية (بعد إزالة الميل)
    _, lo_idx = _swing_pivots(seg_p, order)
    hi_idx, _ = _swing_pivots(seg_ph, order)
    if len(lo_idx) >= 2:
        a, b = lo_idx[-2], lo_idx[-1]
        if seg_p[b] < seg_p[a] and rs[b] > rs[a]:
            return "صاعد", "السعر قاع أدنى والـRSI قاع أعلى (دايفرجنس صاعد)"
    if len(hi_idx) >= 2:
        a, b = hi_idx[-2], hi_idx[-1]
        if seg_ph[b] > seg_ph[a] and rs[b] < rs[a]:
            return "هابط", "السعر قمة أعلى والـRSI قمة أدنى (دايفرجنس هابط)"
    return None, ""


# ==========================================================
# 5) الحجم كمؤكِّد
# ==========================================================
def volume_confirm(df):
    vol = df["Volume"].values.astype(float)
    close = df["Close"].values.astype(float)
    if len(vol) < 21:
        return "بيانات حجم غير كافية"
    v_now = float(np.mean(vol[-3:]))
    v_avg = float(np.mean(vol[-20:]))
    up = close[-1] >= close[-4] if len(close) >= 4 else True
    if v_avg <= 0:
        return "غير متاح"
    ratio = v_now / v_avg
    if ratio >= 1.3:
        return (f"حجم مرتفع ({ratio:.1f}× المعدل) يؤكّد "
                f"{'الصعود' if up else 'الهبوط'}")
    if ratio <= 0.7:
        return f"حجم منخفض ({ratio:.1f}× المعدل) — حركة ضعيفة الإسناد"
    return f"حجم طبيعي ({ratio:.1f}× المعدل)"


# ==========================================================
# 6) أنماط الشموع الهابطة (تكمّل الصاعدة المستوردة من البوت)
# ==========================================================
def _bearish_at(o, h, l, c, i, resistance):
    found = []
    body, rng, up, dn, green = bot._candle(o, h, l, c, i)
    if rng <= 0:
        return found
    small_up = up <= max(body * 0.5, 0.10 * rng)
    small_dn = dn <= max(body * 0.5, 0.10 * rng)
    near_top = resistance > 0 and h[i] >= resistance * 0.97
    # نجمة هابطة: جسم صغير أسفل + ظل علوي طويل (عند قمة)
    if body <= 0.40 * rng and up >= 2.0 * body and small_dn:
        found.append("نجمة هابطة" if near_top else "نجمة هابطة (محتملة)")
    # رجل مشنوق: شكل مطرقة لكن عند قمة
    if body <= 0.40 * rng and dn >= 2.0 * body and small_up and near_top:
        found.append("رجل مشنوق")
    # شاهد القبر: دوجي بظل علوي طويل
    if body <= 0.10 * rng and up >= 2.0 * max(rng * 0.10, 1e-9) and small_dn:
        found.append("دوجي شاهد القبر")
    if i >= 1:
        pgreen = c[i - 1] > o[i - 1]
        pb = abs(c[i - 1] - o[i - 1])
        # ابتلاع هابط
        if pgreen and (not green) and o[i] >= c[i - 1] and c[i] <= o[i - 1] \
                and body > pb:
            found.append("ابتلاع هابط")
        # حجاب غائم مظلم
        if pgreen and (not green) and o[i] > c[i - 1] \
                and c[i] < (o[i - 1] + c[i - 1]) / 2.0 and c[i] > o[i - 1]:
            found.append("حجاب غائم مظلم")
    if i >= 2:
        g0 = c[i - 2] > o[i - 2]; r0 = h[i - 2] - l[i - 2]
        b0 = abs(c[i - 2] - o[i - 2]); b1 = abs(c[i - 1] - o[i - 1])
        # نجمة المساء
        if g0 and r0 > 0 and b0 >= 0.40 * r0 and b1 <= 0.50 * b0 \
                and (not green) and c[i] < (o[i - 2] + c[i - 2]) / 2.0:
            found.append("نجمة المساء")
        # ثلاثة غربان سود
        red0 = c[i - 2] < o[i - 2]; red1 = c[i - 1] < o[i - 1]
        if red0 and red1 and (not green) and c[i] < c[i - 1] < c[i - 2] \
                and body >= 0.50 * rng:
            found.append("ثلاثة غربان سود")
    return found


def detect_bearish(df, scan_last):
    o = df["Open"].values.astype(float)
    h = df["High"].values.astype(float)
    l = df["Low"].values.astype(float)
    c = df["Close"].values.astype(float)
    n = len(c)
    if n < 3:
        return []
    resistance = float(np.max(h[-min(30, n):]))
    found = []
    for i in range(max(2, n - scan_last), n):
        for p in _bearish_at(o, h, l, c, i, resistance):
            if p not in found:
                found.append(p)
    return found


# ==========================================================
# تحليل فريم واحد + درجته الجزئية
# ==========================================================
def analyze_tf(df, name, scan_last):
    close = df["Close"]
    price = float(close.iloc[-1])
    tr, tr_detail = trend_of(df)
    sup, res = support_resistance(df, price)
    mas = ma_analysis(close)
    mom = momentum(close)
    div, div_detail = divergence(df)
    volc = volume_confirm(df)
    bulls = bot.detect_candle_patterns(df, scan_last)
    bears = detect_bearish(df, scan_last)

    # ===== مؤشرات كلاسيكية إضافية (معلومات فقط — لا تمسّ الدرجة/الحكم) =====
    extra = {"adx": None, "boll": None, "stoch": None, "fib": None}
    # قوة الاتجاه ADX/DMI (Wilder): الاتجاه له قوّة، مب اتجاه فقط
    try:
        pdi, mdi, adx = bot.dmi_adx(df["High"], df["Low"], close)
        a = float(adx.iloc[-1])
        p_di, m_di = float(pdi.iloc[-1]), float(mdi.iloc[-1])
        if np.isfinite(a) and a > 0:
            strength = ("قوي جداً" if a >= 40 else "قوي" if a >= 25
                        else "ناشئ" if a >= 20 else "ضعيف/عرضي")
            di = "+DI" if p_di > m_di else "−DI"
            extra["adx"] = (f"ADX {a:.0f} ({strength}) · {di} مهيمن → "
                            f"ميل {'صاعد' if p_di > m_di else 'هابط'}")
    except Exception:
        pass
    # بولنجر باند: الموقع داخل الحزمة + الانضغاط (تجميع)
    try:
        _, _, _, pctb, width = bot.bollinger(close)
        b, w = float(pctb.iloc[-1]), float(width.iloc[-1])
        if np.isfinite(b) and np.isfinite(w):
            pos = ("فوق الحزمة العليا" if b >= 1.0 else
                   "تحت الحزمة السفلى" if b <= 0.0 else
                   "قرب العليا" if b >= 0.8 else
                   "قرب السفلى" if b <= 0.2 else "وسط الحزمة")
            ws = width.dropna()
            squeeze = ""
            if len(ws) >= 40 and w <= float(ws.tail(120).min()) * 1.15:
                squeeze = " · انضغاط (تجميع — احتمال انفجار)"
            extra["boll"] = f"%B {b*100:.0f} — {pos}{squeeze}"
    except Exception:
        pass
    # ستوكاستيك RSI: زخم كلاسيكي يكمّل RSI
    try:
        kline, dline = bot.stoch_rsi(close)
        kk, dd = float(kline.iloc[-1]), float(dline.iloc[-1])
        if np.isfinite(kk) and np.isfinite(dd):
            st = ("تشبع شرائي" if kk >= 80 else
                  "تشبع بيعي" if kk <= 20 else "محايد")
            extra["stoch"] = (f"%K {kk:.0f}/%D {dd:.0f} ({st}، "
                              f"{'K فوق D' if kk >= dd else 'K تحت D'})")
    except Exception:
        pass
    # فيبوناتشي التصحيحي: مناطق ارتداد 38.2/50/61.8 من آخر سوينغ
    try:
        seg = df.tail(min(len(df), 160))
        sw_lo, sw_hi = float(seg["Low"].min()), float(seg["High"].max())
        fib = bot.fibonacci_levels(sw_lo, sw_hi)
        lv = {k: fib[k] for k in ("0.382", "0.500", "0.618") if k in fib}
        if lv:
            extra["fib"] = (sw_lo, sw_hi, lv)
    except Exception:
        pass

    # ===== الدرجة الجزئية [-100, +100] =====
    s = 0.0
    s += {"صاعد": 40, "هابط": -40, "عرضي": 0}[tr]
    if mas["ma50"] is not None:
        s += 15 if price >= mas["ma50"] else -15
    if mas["ma200"] is not None:
        s += 15 if price >= mas["ma200"] else -15
    if mas["cross"]:
        if "ذهبي" in mas["cross"] or "50 فوق" in mas["cross"]:
            s += 10
        elif "موت" in mas["cross"] or "50 تحت" in mas["cross"]:
            s -= 10
    s += max(-15, min(15, (mom["rsi"] - 50) / 50 * 15))
    if mom["rsi"] <= 30:
        s += 5
    elif mom["rsi"] >= 70:
        s -= 5
    s += 10 if "إيجابي" in mom["macd_state"] else -10
    if div == "صاعد":
        s += 15
    elif div == "هابط":
        s -= 15
    if "يؤكّد الصعود" in volc:
        s += 5
    elif "يؤكّد الهبوط" in volc:
        s -= 5
    s = max(-100.0, min(100.0, s))

    return {"name": name, "price": price, "trend": tr, "trend_detail": tr_detail,
            "support": sup, "resistance": res, "ma": mas, "mom": mom,
            "div": div, "div_detail": div_detail, "vol": volc,
            "bulls": bulls, "bears": bears, "extra": extra, "subscore": s}


# ==========================================================
# حساب الفريمات والدرجة (مشترك بين التقرير الفردي والماسح)
# ==========================================================
def _tfs_and_score(df):
    """يبني فريمات التحليل ويحسب الدرجة [0..100] والحكم. df يومي جاهز."""
    weekly = bot.resample_ohlc(df, "W")
    monthly = bot.resample_ohlc(df, "ME")
    tfs = [analyze_tf(df, "اليومي", 5)]
    if len(weekly) >= 30:
        tfs.append(analyze_tf(weekly, "الأسبوعي", 3))
    if len(monthly) >= 12:
        tfs.append(analyze_tf(monthly, "الشهري", 2))
    weights = {"اليومي": 0.45, "الأسبوعي": 0.35, "الشهري": 0.20}
    wsum = sum(weights[t["name"]] for t in tfs)
    raw = sum(t["subscore"] * weights[t["name"]] for t in tfs) / wsum
    score = max(0, min(100, int(round((raw + 100) / 2.0))))
    if score >= 75:
        verdict = "صاعد قوي 🟢"
    elif score >= 60:
        verdict = "صاعد 🟢"
    elif score >= 45:
        verdict = "محايد 🟡"
    elif score >= 30:
        verdict = "هابط 🔴"
    else:
        verdict = "هابط قوي 🔴"
    return tfs, score, verdict


# ==========================================================
# التقرير الكامل
# ==========================================================
def technical_report(sym):
    sym = sym.strip().upper()
    try:
        data = bot.download_history([sym])
    except Exception as e:
        return None, f"تعذّر الاتصال لجلب بيانات {sym}: {e}"
    df = data.get(sym)
    if df is None or len(df) < 60:
        return None, (f"تعذّر جلب بيانات كافية لـ {sym} "
                      "(رمز خاطئ أو سهم جديد جداً).")

    tfs, score, verdict = _tfs_and_score(df)
    earn_label, earn_warn = earnings_alert(sym)
    return {"symbol": sym, "price": float(df["Close"].iloc[-1]),
            "score": score, "verdict": verdict, "tfs": tfs,
            "earnings": earn_label, "earnings_warn": earn_warn}, None


# ==========================================================
# بناء رسالة تيليجرام
# ==========================================================
def _fmt_levels(levels):
    return "، ".join(f"${x:.2f}" for x in levels) if levels else "—"


def render(rep):
    L = [f"📐 <b>التحليل الفني الكلاسيكي: {rep['symbol']}</b>",
         f"السعر الحالي: ${rep['price']:.2f}",
         f"التقييم العام: <b>{rep['verdict']}</b>",
         f"مؤشر القوة الفني: <b>{rep['score']}/100</b> "
         f"<i>(اجتهادي — ملخّص مساعد، ليس معياراً عالمياً)</i>"]
    if rep.get("earnings"):
        L.append(("<b>" + rep["earnings"] + "</b>") if rep.get("earnings_warn")
                 else rep["earnings"])
    L.append("")
    for t in rep["tfs"]:
        L.append(f"━━━━━ <b>الفريم {t['name']}</b> ━━━━━")
        L.append(f"📈 الاتجاه: <b>{t['trend']}</b> ({t['trend_detail']})")
        L.append(f"🟥 المقاومات: {_fmt_levels(t['resistance'])}")
        L.append(f"🟩 الدعوم: {_fmt_levels(t['support'])}")
        # المتوسطات
        if t["ma"]["pos"]:
            pos = "، ".join(f"{p}: {d}" for p, d, _ in t["ma"]["pos"])
            L.append(f"📊 المتوسطات (السعر) → {pos}")
        if t["ma"]["cross"]:
            L.append(f"   تقاطع: {t['ma']['cross']}")
        # الزخم
        m = t["mom"]
        L.append(f"⚡ RSI: {m['rsi']:.0f} ({m['rsi_state']}، {m['rsi_slope']}) "
                 f"| MACD: {m['macd_state']}")
        if t["div"]:
            L.append(f"🔀 دايفرجنس: {t['div']} — {t['div_detail']}")
        # الحجم
        L.append(f"🔊 الحجم: {t['vol']}")
        # مؤشرات كلاسيكية إضافية (معلومات)
        ex = t.get("extra") or {}
        if ex.get("adx"):
            L.append(f"💪 قوة الاتجاه: {ex['adx']}")
        if ex.get("boll"):
            L.append(f"📉 بولنجر: {ex['boll']}")
        if ex.get("stoch"):
            L.append(f"🎚️ ستوكاستيك RSI: {ex['stoch']}")
        if ex.get("fib"):
            lo_, hi_, lv = ex["fib"]
            ftxt = "، ".join(f"{k}: ${v:.2f}" for k, v in lv.items())
            L.append(f"🔱 فيبوناتشي (قاع ${lo_:.2f}→قمة ${hi_:.2f}): {ftxt}")
        # الشموع
        if t["bulls"]:
            L.append("🕯️ شموع صاعدة: " + "، ".join(t["bulls"]))
        if t["bears"]:
            L.append("🕯️ شموع هابطة: " + "، ".join(t["bears"]))
        if not t["bulls"] and not t["bears"]:
            L.append("🕯️ لا أنماط شموع واضحة")
        L.append("")
    # خلاصة محايدة
    ups = sum(1 for t in rep["tfs"] if t["trend"] == "صاعد")
    downs = sum(1 for t in rep["tfs"] if t["trend"] == "هابط")
    if ups > downs:
        summ = "الاتجاه العام مائل للصعود عبر الفريمات."
    elif downs > ups:
        summ = "الاتجاه العام مائل للهبوط عبر الفريمات."
    else:
        summ = "الاتجاه مختلط بين الفريمات — لا إجماع واضح."
    L.append(f"🧭 <b>الخلاصة الفنية:</b> {summ} "
             "راقب المقاومة كحاجز والدعم كأرضية. (تحليل فني، ليس توصية.)")
    if rep.get("earnings_warn"):
        L.append("⚠️ <b>تنبيه:</b> يوجد إعلان أرباح وشيك — مهما كان التقييم "
                 "الفني قوياً، الأرقام قد تكسر الحركة بفجوة سعرية. الأأمن "
                 "الانتظار حتى بعد الإعلان.")
    L.append("")
    L.append(bot.FOOTER)
    return "\n".join(L)


# ==========================================================
# الماسح اليومي: أسهم ناسداك القوية فنياً + إعلان أرباح قريب
# ==========================================================
SCAN_MIN_PRICE = 2.0           # لا سنتات — أقل سعر مقبول
SCAN_MIN_DOLLAR_VOL = 1_000_000  # أرضية سيولة (تستبعد النانو-كاب)
SCAN_MIN_SCORE = 60            # القوة الفنية الدنيا (خُفّضت من 70)
SCAN_EARN_WINDOW = 14          # إعلان أرباح خلال كم يوم يُعتبر «قريب»
SCAN_MIN_BARS = 200            # نحتاج تاريخ كافٍ (متوسط 200 + شهري)


def _earnings_days(sym):
    """عدد الأيام حتى أقرب إعلان أرباح قادم، أو None. فاشل-آمن."""
    try:
        d = _next_earnings_date(sym)
    except Exception:
        return None
    if d is None:
        return None
    return (d - _dt.date.today()).days


def scan_nasdaq_earnings():
    """يفرز ناسداك → الأقوياء فنياً (≥SCAN_MIN_SCORE) فوق السعر/السيولة،
    ثم يُبقي من عندهم إعلان أرباح خلال SCAN_EARN_WINDOW يوم. يرجع قائمة."""
    bot.log("🌐 جلب قائمة ناسداك...")
    try:
        universe = bot.get_universe()
    except Exception as e:
        bot.log(f"تعذّر جلب الكون: {e}")
        return []
    bot.log(f"الكون: {len(universe)} رمز — جاري التحميل بالجملة (قد يطول)...")
    try:
        data = bot.download_history(universe)
    except Exception as e:
        bot.log(f"تعذّر التحميل: {e}")
        return []

    # المرحلة 1: ترشيح فني + سعر + سيولة (في الذاكرة، بلا تنزيل إضافي)
    strong = []
    checked = 0
    for sym, df in data.items():
        if df is None or len(df) < SCAN_MIN_BARS:
            continue
        try:
            price = float(df["Close"].iloc[-1])
            if price < SCAN_MIN_PRICE:                 # لا سنتات
                continue
            dvol = float((df["Close"] * df["Volume"]).tail(20).mean())
            if dvol < SCAN_MIN_DOLLAR_VOL:             # لا نانو-كاب
                continue
            tfs, score, verdict = _tfs_and_score(df)
            checked += 1
            if score >= SCAN_MIN_SCORE:
                strong.append({"symbol": sym, "price": price,
                               "score": score, "verdict": verdict,
                               "dvol": dvol})
        except Exception:
            continue
    bot.log(f"حُلِّل {checked} سهماً · أقوياء فنياً: {len(strong)}")

    # حمّل تقويم Alpha Vantage مرة واحدة (نداء واحد لكل الشركات)
    _cal = _load_av_calendar()
    if _cal:
        bot.log(f"تقويم Alpha Vantage: {len(_cal)} شركة")
    else:
        bot.log("تقويم Alpha Vantage فارغ → احتياطي yfinance")

    # المرحلة 2: فحص الأرباح للأقوياء فقط (عددهم قليل → سريع)
    out = []
    for s in strong:
        days = _earnings_days(s["symbol"])
        if days is not None and 0 <= days <= SCAN_EARN_WINDOW:
            s["earn_days"] = days
            s["earn_date"] = (_dt.date.today()
                              + _dt.timedelta(days=days)).isoformat()
            out.append(s)
    out.sort(key=lambda x: (-x["score"], x["earn_days"]))
    bot.log(f"✅ مرشحون (قوي فنياً + أرباح خلال {SCAN_EARN_WINDOW}ي): {len(out)}")
    return out


def render_scan(results):
    today = _dt.date.today().isoformat()
    if not results:
        return ("🗓️ <b>مرشحو ناسداك (قوي فنياً + إعلان أرباح قريب)</b>\n"
                f"التاريخ: {today}\n\n"
                "لا توجد أسهم تطابق الشروط اليوم "
                f"(قوة فنية ≥ {SCAN_MIN_SCORE}، سعر ≥ ${SCAN_MIN_PRICE:.0f}، "
                f"أرباح خلال {SCAN_EARN_WINDOW} يوم).\n\n" + bot.FOOTER)
    L = ["🗓️ <b>مرشحو ناسداك (قوي فنياً + إعلان أرباح قريب)</b>",
         f"التاريخ: {today} | العدد: {len(results)}",
         f"<i>الشروط: قوة فنية ≥ {SCAN_MIN_SCORE} · سعر ≥ "
         f"${SCAN_MIN_PRICE:.0f} · سيولة ≥ "
         f"${SCAN_MIN_DOLLAR_VOL/1e6:.0f}M · أرباح ≤ {SCAN_EARN_WINDOW}ي</i>",
         ""]
    for i, s in enumerate(results, 1):
        warn = "⚠️ " if s["earn_days"] <= EARNINGS_WARN_DAYS else ""
        L.append(f"{i}) 📌 <b>{s['symbol']}</b> — {s['score']}/100 "
                 f"({s['verdict']})")
        L.append(f"   💵 ${s['price']:.2f} | سيولة ${s['dvol']/1e6:.1f}M")
        L.append(f"   📅 {warn}إعلان أرباح خلال {s['earn_days']} يوم "
                 f"({s['earn_date']})")
    L.append("")
    L.append("💡 الفكرة: راقبها وانتظر <b>نتيجة</b> الإعلان. ادخل فقط لو "
             "كانت النتيجة إيجابية <b>وتفاعل السعر صعوداً بحجم</b> — "
             "احذر «اشترِ الإشاعة وبِع الخبر».")
    L.append("")
    L.append(bot.FOOTER)
    return "\n".join(L)


# ==========================================================
# التشغيل
# ==========================================================
def main():
    # وضع المسح اليومي
    if os.environ.get("SCAN_EARNINGS", "").strip() in ("1", "true", "yes"):
        bot.log("🗓️ بدء مسح ناسداك (قوي فنياً + أرباح قريبة)...")
        results = scan_nasdaq_earnings()
        bot.send_telegram(render_scan(results))
        bot.log("✅ أُرسلت قائمة المرشحين.")
        return
    # وضع التحليل الفردي
    sym = os.environ.get("TICKER", "").strip()
    if not sym:
        bot.log("⚠️ ضع TICKER=الرمز (تحليل فردي) أو SCAN_EARNINGS=1 (مسح يومي).")
        return
    bot.log(f"📐 تقرير فني كلاسيكي للسهم: {sym}")
    rep, err = technical_report(sym)
    if rep is None:
        msg = f"📐 <b>تحليل فني: {sym.upper()}</b>\n\n⚠️ {err}\n\n{bot.FOOTER}"
        bot.send_telegram(msg)
        bot.log(f"تعذّر: {err}")
        return
    bot.send_telegram(render(rep))
    bot.log("✅ أُرسل التقرير الفني الكلاسيكي.")


if __name__ == "__main__":
    main()
