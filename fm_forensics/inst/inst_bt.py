"""🏛️📜 T-INST-BT «فلتر المؤسسات تاريخيًّا» — أداةُ العقد `T_INST_BT_prereg.md` (قراءةٌ فقط · لا تلغرام · لا إنتاج).

الأوضاع: `check` (بصمةُ العقد) · `run` (كلُّ شيءٍ على رنر: 13F ⟵ الربط ⟵ ① ⟵ ② ⟵ ③ ⟵ ④ ⟵ ⑤ ⟵ `out_bt/bt.json.gz` وسطرُ `INSTBT_JSON`).
المادّة: مجموعاتُ 13F من SEC (والربعُ الثالث 2026 من إيداعات EDGAR) · FTD (CUSIP↔رمز) · Polygon (التفاصيل بتاريخ · الشموع · التقسيمات) ·
`runners_60.json` · `gcross_runner_universe.json` · شرائحُ T-TGTLADDER (`K4_TGL_DIR`) · `near_watch.json` من git عند `N_commit`."""
import argparse
import datetime as dt
import glob
import gzip
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import threading
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CONTRACT = os.path.join(HERE, "T_INST_BT_prereg.md")
CONTRACT_SHA = "99705712b47cd9ee2c3527dbb154eb342996259443a29e9e9dcb2dc3d6def461"
OUT = os.path.join(HERE, "out_bt")
FINVIZ = os.path.join(HERE, "data", "finviz_inst_20261115.json")
RUNNERS = os.path.join(ROOT, "fm_forensics", "rrgate", "data", "runners_60.json")
UNIV = os.path.join(ROOT, "fm_forensics", "ema_cross", "data", "gcross_runner_universe.json")
F13_PAGE = "https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets"
FTD_PAGE = "https://www.sec.gov/data-research/sec-markets-data/fails-deliver-data"

IO_MIN, IT_MIN, PRICE_MAX, CAP_MAX = 0.20, 0.10, 7.0, 50e6
REC_MIN, PREC_MIN = 0.70, 0.50
V1_MIN, V2_MIN, V3_MIN = 5000, 0.70, 0.80
FLOOR, FLOOR4 = 20, 10
BOOT_SEED = "TINSTBT"
FTD_WIN = 183
ACCEPT_Q, ACCEPT_CUTOFF, ACCEPT_CLOSE = (2026, 3), "2026-11-14", "2026-11-13"
Q3_PERIODS = [(2022, 4), (2023, 1), (2023, 2), (2023, 3), (2023, 4), (2024, 1), (2024, 2), (2024, 3), (2024, 4),
              (2025, 1), (2025, 2), (2025, 3)]
HORIZONS, LEVELS = (20, 40, 60), (0.5, 1.0)
LOOKBACK = 60
MM_EXTRA = ("hrt financial",)
SUFFIX = {"inc", "incorporated", "corp", "corporation", "ltd", "limited", "plc", "co", "company", "holdings"}
NONCOMMON = ("WARRANT", "RIGHT", "UNIT", "NOTE", "PFD", "PREFERRED")
CONTRACT_RC, DATA_RC, KEY_RC = 9, 7, 3


def log(*a):
    print(*a, flush=True)


def contract_ok(path=CONTRACT, sha=CONTRACT_SHA):
    try:
        return hashlib.sha256(open(path, "rb").read()).hexdigest() == sha
    except OSError:
        return False


def _inst():
    sys.path.insert(0, HERE)
    import inst as I
    return I


# ── نقيّة ────────────────────────────────────────────────────────────────────────────────────────
def quarter_end(y, q):
    return dt.date(y, 3 * q, {3: 31, 6: 30, 9: 30, 12: 31}[3 * q]).isoformat()


def prev_q(y, q):
    return (y, q - 1) if q > 1 else (y - 1, 4)


def is_session(d, holidays):
    x = dt.date.fromisoformat(d)
    return x.weekday() < 5 and d not in holidays


def deadline(qend, holidays):
    """نهايةُ الربع + 45 يومًا ⟵ أوّلُ جلسةٍ في ذلك اليوم أو بعده."""
    x = dt.date.fromisoformat(qend) + dt.timedelta(days=45)
    while not is_session(x.isoformat(), holidays):
        x += dt.timedelta(days=1)
    return x.isoformat()


def norm_name(s):
    w = re.sub(r"[^a-z0-9 ]", " ", str(s or "").lower().replace("&", " and ")).split()
    while w and w[-1] in SUFFIX:
        w.pop()
    return " ".join(w)


def common_class(title):
    t = str(title or "").upper()
    return not any(k in t for k in NONCOMMON)


def select_filings(subs, cutoff):
    """subs [(acc, cik, date, type, amend)] لربعٍ واحد ⟵ الإيداعاتُ الصالحة: لكلّ مُودِع أحدثُ أصليٍّ أو «RESTATEMENT» حتى cutoff ‏+ «NEW HOLDINGS» بعده حتى cutoff."""
    by = {}
    for acc, cik, d, typ, am in subs:
        if d and d <= cutoff:
            by.setdefault(cik, []).append((d, acc, typ, str(am or "").upper()))
    out = []
    for cik, rows in by.items():
        rows.sort()
        base = [r for r in rows if not r[2].endswith("/A") or "RESTATEMENT" in r[3]]
        if not base:
            continue
        b = base[-1]
        out.append(b[1])
        out += [r[1] for r in rows if r[2].endswith("/A") and "NEW HOLDINGS" in r[3] and r[0] >= b[0] and r[1] != b[1]]
    return sorted(out)


def tri_and(vals):
    if any(v is False for v in vals):
        return False
    if any(v is None for v in vals):
        return None
    return True


def io_it(h, hp, shares):
    """⟵ (IO أو None، شرطُ IO، شرطُ IT، «جديد»؟) · h/hp None = بلا CUSIP مربوط."""
    if h is None:
        return None, None, None, False
    io_ = (h / shares) if shares else None
    c_io = None if io_ is None else io_ > IO_MIN
    if hp is None:
        c_it = None
    elif hp == 0:
        c_it = h > 0
    else:
        c_it = h / hp - 1 > IT_MIN
    return io_, c_io, c_it, bool(hp == 0 and h > 0)


def match_state(exch, close, shares_t, c_io, c_it):
    c_x = None if exch is None else exch == "XNAS"
    c_p = None if close is None else close < PRICE_MAX
    c_c = None if (close is None or not shares_t) else close * shares_t < CAP_MAX
    return tri_and([c_x, c_p, c_c, c_io, c_it])


def pick_ftd(rows, qend, win=FTD_WIN):
    """rows [(تاريخ، cusip)] لرمز ⟵ الـCUSIP الأقربُ تاريخًا لنهاية الربع داخل ±win يومًا أو None."""
    e = dt.date.fromisoformat(qend)
    best = None
    for d, c in rows:
        try:
            gap = abs((dt.date.fromisoformat(d) - e).days)
        except ValueError:
            continue
        if gap <= win and (best is None or gap < best[0]):
            best = (gap, c)
    return best[1] if best else None


def outcome_hits(bars, i0, n, lvl):
    """bars [(يوم، high، close)] · i0 مؤشّرُ t ⟵ True/False أو None (أقلُّ من n جلسة)."""
    if i0 is None or i0 + n >= len(bars) or not bars[i0][2]:
        return None
    return max(b[1] for b in bars[i0 + 1:i0 + n + 1]) >= bars[i0][2] * (1 + lvl)


def year_verdict(n_m, lo, hi, floor=FLOOR):
    if n_m < floor or lo is None:
        return "لا قياس"
    if lo > 0:
        return "يرفع"
    if hi < 0:
        return "يخفض"
    return "لا فرق قابل للكشف"


RANK = {"لا قياس": 0, "يخفض": 1, "لا فرق قابل للكشف": 2, "يرفع": 3}


def weakest(vs):
    return min(vs, key=lambda v: RANK[v]) if vs else "لا قياس"


def mm_share(deltas, names, mm):
    """deltas {cik: Δأسهم} · names {cik: اسم} ⟵ حصّةُ مُودِعي القائمة من مجموع الزيادات الموجبة أو None."""
    pos = {c: v for c, v in deltas.items() if v > 0}
    tot = sum(pos.values())
    if not tot:
        return None
    return sum(v for c, v in pos.items() if mm(names.get(c, ""))) / tot


def accept_verdict(ours, finviz):
    inter = sorted(set(ours) & set(finviz))
    rec = len(inter) / len(finviz) if finviz else 0.0
    prec = len(inter) / len(ours) if ours else 0.0
    return {"inter": inter, "recall": rec, "precision": prec, "accepted": rec >= REC_MIN and prec >= PREC_MIN}


# ── الجلب ───────────────────────────────────────────────────────────────────────────────────────
_LOCK = threading.Lock()
_LAST = [0.0]


def _sec_get(url, contact, tries=4, binary=False):
    import requests
    for i in range(tries):
        with _LOCK:
            w = 0.125 - (time.time() - _LAST[0])
            if w > 0:
                time.sleep(w)
            _LAST[0] = time.time()
        try:
            r = requests.get(url, headers={"User-Agent": contact}, timeout=120)
            if r.status_code == 200:
                return r.content if binary else r.text
            if r.status_code in (404, 410):
                return None
        except Exception:                                        # noqa: BLE001
            pass
        time.sleep(3 * (i + 1))
    return None


def _poly(url, key, tries=4):
    import requests
    for i in range(tries):
        try:
            r = requests.get(url + ("&" if "?" in url else "?") + "apiKey=" + key, timeout=60)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 404:
                return None
        except Exception:                                        # noqa: BLE001
            pass
        time.sleep(2 * (i + 1))
    return None


def links(page, pat, contact):
    t = _sec_get(page, contact) or ""
    return sorted({("https://www.sec.gov" + x) if x.startswith("/") else x for x in re.findall(r'href="([^"]*' + pat + r'[^"]*)"', t)})


def zip_window(url):
    """اسمُ مجموعة 13F ⟵ (من، إلى) نافذةُ تواريخ الإيداع."""
    n = url.rsplit("/", 1)[-1]
    m = re.match(r"(\d{4})q(\d)_form13f", n)
    if m:
        y, q = int(m.group(1)), int(m.group(2))
        return dt.date(y, 3 * q - 2, 1).isoformat(), quarter_end(y, q)
    m = re.match(r"(\d{2}[a-z]{3}\d{4})-(\d{2}[a-z]{3}\d{4})_form13f", n)
    if m:
        f = lambda s: dt.datetime.strptime(s, "%d%b%Y").date().isoformat()
        return f(m.group(1)), f(m.group(2))
    return None


def read_zip_subs(zb):
    import pandas as pd
    z = zipfile.ZipFile(io.BytesIO(zb))
    rd = lambda n, cols: pd.read_csv(z.open(n), sep="\t", dtype=str, usecols=cols, quoting=3, keep_default_na=False, on_bad_lines="skip")
    s = rd("SUBMISSION.tsv", ["ACCESSION_NUMBER", "FILING_DATE", "SUBMISSIONTYPE", "CIK", "PERIODOFREPORT"])
    c = rd("COVERPAGE.tsv", ["ACCESSION_NUMBER", "AMENDMENTTYPE", "FILINGMANAGER_NAME"])
    s = s.merge(c, on="ACCESSION_NUMBER", how="left").fillna("")
    out = []
    for r in s.itertuples(index=False):
        try:
            fd = dt.datetime.strptime(r.FILING_DATE, "%d-%b-%Y").date().isoformat()
            pe = dt.datetime.strptime(r.PERIODOFREPORT, "%d-%b-%Y").date().isoformat()
        except ValueError:
            continue
        if r.SUBMISSIONTYPE in ("13F-HR", "13F-HR/A"):
            out.append((r.ACCESSION_NUMBER, r.CIK, fd, r.SUBMISSIONTYPE, r.AMENDMENTTYPE, pe, r.FILINGMANAGER_NAME))
    return out


def read_zip_info(zb, accs):
    """⟵ DataFrame (acc, cusip, shares) لصفوف SH بلا PUTCALL في accs ‏+ وصفُ CUSIP {cusip: (اسم، فئة، figi)}."""
    import pandas as pd
    z = zipfile.ZipFile(io.BytesIO(zb))
    cols = ["ACCESSION_NUMBER", "NAMEOFISSUER", "TITLEOFCLASS", "CUSIP", "FIGI", "SSHPRNAMT", "SSHPRNAMTTYPE", "PUTCALL"]
    parts, meta = [], {}
    for ch in pd.read_csv(z.open("INFOTABLE.tsv"), sep="\t", dtype=str, usecols=cols, quoting=3, keep_default_na=False,
                          on_bad_lines="skip", chunksize=1_000_000):
        ch = ch[ch["ACCESSION_NUMBER"].isin(accs) & (ch["SSHPRNAMTTYPE"] == "SH") & (ch["PUTCALL"] == "")]
        ch = ch.assign(CUSIP=ch["CUSIP"].str.upper().str.strip(), shares=pd.to_numeric(ch["SSHPRNAMT"], errors="coerce").fillna(0))
        for r in ch.drop_duplicates("CUSIP")[["CUSIP", "NAMEOFISSUER", "TITLEOFCLASS", "FIGI"]].itertuples(index=False):
            meta.setdefault(r.CUSIP, (r.NAMEOFISSUER, r.TITLEOFCLASS, r.FIGI))
        parts.append(ch.groupby(["ACCESSION_NUMBER", "CUSIP"], as_index=False)["shares"].sum())
    df = pd.concat(parts) if parts else pd.DataFrame(columns=["ACCESSION_NUMBER", "CUSIP", "shares"])
    return df.rename(columns={"ACCESSION_NUMBER": "acc", "CUSIP": "cusip"}), meta


_TAG = lambda t: re.compile(r"<(?:\w+:)?" + t + r">\s*([^<]*?)\s*</(?:\w+:)?" + t + ">", re.I)
_T_INFO = re.compile(r"<(?:\w+:)?infoTable>(.*?)</(?:\w+:)?infoTable>", re.I | re.S)
_T = {k: _TAG(k) for k in ("nameOfIssuer", "titleOfClass", "cusip", "figi", "sshPrnamt", "sshPrnamtType", "putCall",
                           "periodOfReport", "amendmentType", "name")}


def parse_edgar_13f(txt):
    """ملفُّ إيداع 13F الكامل ⟵ (نهايةُ الربع، نوعُ التعديل، اسمُ المُودِع، [(cusip، اسم، فئة، figi، أسهم)] لـSH بلا putCall)."""
    g = lambda k, s: (_T[k].search(s).group(1) if _T[k].search(s) else "")
    pe = g("periodOfReport", txt)
    try:
        pe = dt.datetime.strptime(pe, "%m-%d-%Y").date().isoformat()
    except ValueError:
        pe = ""
    m = re.search(r"COMPANY CONFORMED NAME:\s*(.+)", txt)
    rows = []
    for blk in _T_INFO.findall(txt):
        if g("putCall", blk) or g("sshPrnamtType", blk).upper() != "SH":
            continue
        try:
            sh = float(g("sshPrnamt", blk).replace(",", ""))
        except ValueError:
            continue
        rows.append((g("cusip", blk).upper(), g("nameOfIssuer", blk), g("titleOfClass", blk), g("figi", blk), sh))
    return pe, g("amendmentType", txt), (m.group(1).strip() if m else ""), rows


# ── القراءة ───────────────────────────────────────────────────────────────────────────────────────
def load_holidays():
    sys.path.insert(0, ROOT)
    import market_calendar as MC
    return set(MC.HOLIDAYS)


def sessions_between(a, b, holidays):
    x, out = dt.date.fromisoformat(a), []
    while x.isoformat() <= b:
        if is_session(x.isoformat(), holidays):
            out.append(x.isoformat())
        x += dt.timedelta(days=1)
    return out


def tgl_entries(d):
    rows = {}
    for f in sorted(glob.glob(os.path.join(d or "", "shard_*.json.gz"))):
        rows.update(json.load(gzip.open(f, "rt", encoding="utf-8")).get("rows") or {})
    return sorted({(s, e.get("d")) for s, es in rows.items() for e in (es or []) if e.get("d")})


def _git_json(commit, path):
    try:
        return json.loads(subprocess.run(["git", "show", f"{commit}:{path}"], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
    except Exception:                                            # noqa: BLE001
        return None


# ── التشغيل ──────────────────────────────────────────────────────────────────────────────────────
def mode_run(key, contact):
    import pandas as pd
    I = _inst()
    mm = lambda n: I.is_mm(n) or any(re.search(r"(^|[^a-z])" + re.escape(k) + r"([^a-z]|$)", " ".join(str(n).lower().split())) for k in MM_EXTRA)
    H = load_holidays()
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    res = {"gates": {}, "counts": {}}

    # 0) الكونُ والفترات
    entries = tgl_entries(os.environ.get("K4_TGL_DIR"))
    log(f"📥 CURRENT من T-TGTLADDER: {len(entries)} إدخالًا")
    if len(entries) != 4465:
        log("⚠️ عددُ CURRENT ليس 4,465 — يُطبع ويمضي (F5)")
    R60 = json.load(open(RUNNERS, encoding="utf-8"))
    U = json.load(open(UNIV, encoding="utf-8"))
    sys.path.insert(0, os.path.join(ROOT, "fm_forensics", "live_vs_shadow"))
    import live_vs_shadow as LVS
    src_days = set(LVS.source_days(U))
    r50 = [(r["sym"], r["day"]) for r in R60["rows"] if r["R"] >= 0.5]
    r100 = [(s, d) for s, d in r50 if next(r["R"] for r in R60["rows"] if r["sym"] == s and r["day"] == d) >= 1.0]
    r195 = [(s, d) for s, d in r100 if d in src_days]
    log(f"📥 الراكضون: ‏+50% {len(r50)} · ‏+100% {len(r100)} · في أيّام المصدر {len(r195)}")
    sess60 = sorted(U["days"])
    allsess = sessions_between("2022-08-01", "2026-11-13", H)
    prev_s = {allsess[i]: allsess[i - 1] for i in range(1, len(allsess))}

    periods = {}
    for (y, q) in Q3_PERIODS + [(2025, 4), (2026, 1), (2026, 2), ACCEPT_Q]:
        for p in ((y, q), prev_q(y, q)):
            e = quarter_end(*p)
            periods[p] = {"end": e, "T": deadline(e, H)}
    periods[ACCEPT_Q]["cut"] = ACCEPT_CUTOFF
    for p, v in periods.items():
        v.setdefault("cut", v["T"])

    # 1) 13F من المجموعات
    zl = [u for u in links(F13_PAGE, r"_form13f\.zip", contact) if zip_window(u)]
    log(f"📦 مجموعاتُ 13F المتاحة: {len(zl)}")
    need = {p: v for p, v in periods.items() if p != ACCEPT_Q}
    zuse = [u for u in zl if any(zip_window(u)[0] <= v["cut"] and zip_window(u)[1] > v["end"] for v in need.values())]
    subs_all, zbytes = {p: [] for p in periods}, {}
    names = {}
    for u in zuse:
        zb = _sec_get(u, contact, binary=True)
        if zb is None:
            log(f"⛔ تعذّر {u}")
            continue
        zbytes[u] = zb
        for acc, cik, fd, typ, am, pe, nm in read_zip_subs(zb):
            names[cik] = nm
            for p, v in need.items():
                if pe == v["end"]:
                    subs_all[p].append((acc, cik, fd, typ, am))
        log(f"   {u.rsplit('/', 1)[-1]} · {len(zb) / 1e6:.0f}MB · {int(time.time() - t0)}ث")
    valid = {p: select_filings(subs_all[p], v["cut"]) for p, v in need.items()}
    acc_cik = {acc: cik for p in need for acc, cik, *_ in subs_all[p]}
    hold, meta = {}, {}
    for u, zb in zbytes.items():
        accs = {a for p in need for a in valid[p]}
        df, mt = read_zip_info(zb, accs)
        for c, v in mt.items():
            meta.setdefault(c, v)
        df["cik"] = df["acc"].map(acc_cik)
        for p in need:
            sub = df[df["acc"].isin(set(valid[p]))]
            if len(sub):
                hold[p] = pd.concat([hold[p], sub]) if p in hold else sub
        log(f"   جدولُ {u.rsplit('/', 1)[-1]}: {len(df)} صفًّا · {int(time.time() - t0)}ث")
    zbytes.clear()

    # 1ب) الربعُ الثالث 2026 من EDGAR
    idx = (_sec_get("https://www.sec.gov/Archives/edgar/full-index/2026/QTR4/form.idx", contact) or "").splitlines()
    fl = []
    for ln in idx:
        m = re.match(r"(13F-HR(?:/A)?)\s+.+?\s+(\d+)\s+(\d{4}-\d{2}-\d{2})\s+(edgar/\S+\.txt)", ln)
        if m and m.group(3) <= ACCEPT_CUTOFF:
            fl.append((m.group(1), m.group(2), m.group(3), m.group(4)))
    log(f"📄 EDGAR ‏2026Q4 form.idx: إيداعاتُ 13F حتى {ACCEPT_CUTOFF}: {len(fl)}")

    def one(f):
        typ, cik, d, path = f
        txt = _sec_get("https://www.sec.gov/Archives/" + path, contact)
        if txt is None:
            return f, None
        return f, parse_edgar_13f(txt)
    q3subs, q3rows, q3fail = [], {}, 0
    with ThreadPoolExecutor(8) as ex:
        for k, (f, pr) in enumerate(ex.map(one, fl)):
            if pr is None:
                q3fail += 1
                continue
            pe, am, nm, rows = pr
            if pe != periods[ACCEPT_Q]["end"]:
                continue
            acc = f[3].rsplit("/", 1)[-1][:-4]
            names[f[1]] = nm or names.get(f[1], "")
            q3subs.append((acc, f[1], f[2], f[0], am))
            q3rows[acc] = rows
            if k % 1000 == 0:
                log(f"   EDGAR {k}/{len(fl)} · {int(time.time() - t0)}ث")
    valid[ACCEPT_Q] = select_filings(q3subs, ACCEPT_CUTOFF)
    acc2cik = {a: c for a, c, *_ in q3subs}
    recs = []
    for acc in valid[ACCEPT_Q]:
        cik = acc2cik[acc]
        for cu, nm, cl, fg, sh in q3rows.get(acc, []):
            recs.append((acc, cu, sh, cik))
            meta.setdefault(cu, (nm, cl, fg))
    hold[ACCEPT_Q] = pd.DataFrame(recs, columns=["acc", "cusip", "shares", "cik"])
    q3rows.clear()
    res["counts"]["filings"] = {f"{p[0]}Q{p[1]}": len(valid[p]) for p in sorted(valid)}
    res["counts"]["edgar_fail"] = q3fail
    res["gates"]["V1"] = {f"{p[0]}Q{p[1]}": len(valid[p]) >= V1_MIN for p in sorted(valid)}
    log(f"V1 الإيداعاتُ الصالحة: {res['counts']['filings']} · تعذّر EDGAR {q3fail}")
    Hq = {p: hold[p].groupby("cusip")["shares"].sum().to_dict() if p in hold else {} for p in periods}
    by_figi = {}
    by_name = {}
    for c, (nm, cl, fg) in meta.items():
        if fg:
            by_figi.setdefault(fg.strip().upper(), set()).add(c)
        if common_class(cl):
            by_name.setdefault(norm_name(nm), set()).add(c)

    # 2) FTD
    fz = [u for u in links(FTD_PAGE, r"cnsfails\d{6}[ab]\.zip", contact)]
    ftd = {}
    for u in fz:
        m = re.search(r"cnsfails(\d{4})(\d{2})", u)
        if not m or not ("2022-01" <= f"{m.group(1)}-{m.group(2)}" <= "2026-11"):
            continue
        zb = _sec_get(u, contact, binary=True)
        if not zb:
            continue
        z = zipfile.ZipFile(io.BytesIO(zb))
        for ln in z.read(z.namelist()[0]).decode("latin-1").splitlines()[1:]:
            p_ = ln.split("|")
            if len(p_) > 3 and len(p_[0]) == 8 and p_[1] and p_[2]:
                ftd.setdefault(p_[2].strip().upper(), set()).add((f"{p_[0][:4]}-{p_[0][4:6]}-{p_[0][6:]}", p_[1].strip().upper()))
    log(f"📄 FTD: {len(ftd)} رمزًا · {int(time.time() - t0)}ث")

    # 3) Polygon
    det_cache = {}

    def details(sym, d):
        k = (sym, d)
        if k not in det_cache:
            j = _poly(f"https://api.polygon.io/v3/reference/tickers/{sym}?date={d}", key)
            det_cache[k] = (j or {}).get("results") or {}
        return det_cache[k]

    def prefetch(pairs):
        pairs = [p for p in set(pairs) if p not in det_cache]
        with ThreadPoolExecutor(12) as ex:
            list(ex.map(lambda p: details(*p), pairs))

    grouped = {}

    def closes(d):
        if d not in grouped:
            j = _poly(f"https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/{d}?adjusted=true", key) or {}
            grouped[d] = {r["T"]: r.get("c") for r in j.get("results") or []}
        return grouped[d]

    def cusips_for(sym, p):
        e = periods[p]["end"]
        dd = details(sym, e)
        fg = str(dd.get("share_class_figi") or "").upper()
        if fg and by_figi.get(fg):
            return sorted(by_figi[fg]), "a"
        c = pick_ftd(ftd.get(sym, ()), e)
        if c:
            return [c], "b"
        nm = norm_name(dd.get("name"))
        if nm and by_name.get(nm):
            return sorted(by_name[nm]), "c"
        return None, None

    def hq(sym, p):
        cs, src = cusips_for(sym, p)
        if cs is None:
            return None, None
        return sum(Hq[p].get(c, 0) for c in cs), src

    def state(sym, p, t, ctrl=None):
        """⟵ dict: الحالة (True/False/None) · IO · IT · مصدرُ الربط · جديد."""
        h, src = hq(sym, p)
        hp, _ = hq(sym, prev_q(*p))
        sh_q = details(sym, periods[p]["end"])
        shares_q = sh_q.get("share_class_shares_outstanding") or sh_q.get("weighted_shares_outstanding")
        io_, c_io, c_it, new = io_it(h, hp, shares_q)
        st = {"src": src, "io": io_, "it": (None if (h is None or not hp) else h / hp - 1), "new": new, "c_io": c_io, "c_it": c_it,
              "has_shares": bool(shares_q)}
        if c_io is False or c_it is False:
            st["m"] = False
            return st
        dt_ = details(sym, t)
        cl = (ctrl if ctrl is not None else closes(t)).get(sym)
        st["m"] = match_state(dt_.get("primary_exchange"), cl, dt_.get("share_class_shares_outstanding") or dt_.get("weighted_shares_outstanding"),
                              c_io, c_it)
        return st

    def coverage(syms, p):
        mp = [s for s in syms if hq(s, p)[0] is not None]
        sh = [s for s in mp if (details(s, periods[p]["end"]).get("share_class_shares_outstanding")
                                or details(s, periods[p]["end"]).get("weighted_shares_outstanding"))]
        srcs = {}
        for s in mp:
            k = cusips_for(s, p)[1]
            srcs[k] = srcs.get(k, 0) + 1
        return {"n": len(syms), "mapped": len(mp), "shares": len(sh), "src": srcs,
                "V2": (len(mp) / len(syms) >= V2_MIN) if syms else False, "V3": (len(sh) / len(mp) >= V3_MIN) if mp else False}

    # ① القبول
    fv = json.load(open(FINVIZ, encoding="utf-8"))
    nas = []
    url = "https://api.polygon.io/v3/reference/tickers?market=stocks&exchange=XNAS&type=CS&active=true&date=" + ACCEPT_CLOSE + "&limit=1000"
    while url:
        j = _poly(url, key) or {}
        nas += [r["ticker"] for r in j.get("results") or []]
        url = j.get("next_url")
    nas = sorted(set(nas) | set(fv["tickers"]))
    pq = prev_q(*ACCEPT_Q)
    prefetch([(s, periods[ACCEPT_Q]["end"]) for s in nas] + [(s, periods[pq]["end"]) for s in nas])
    cov1 = coverage(nas, ACCEPT_Q)
    c13 = closes(ACCEPT_CLOSE)
    with ThreadPoolExecutor(12) as ex:
        st1 = dict(zip(nas, ex.map(lambda s: state(s, ACCEPT_Q, ACCEPT_CLOSE, c13), nas)))
    ours = sorted(s for s, v in st1.items() if v["m"] is True)
    acc = accept_verdict(ours, fv["tickers"])
    fvrow = {s: {"io": (fv["ownership"].get(s) or {}).get("Inst Own"), "it": (fv["ownership"].get(s) or {}).get("Inst Trans")} for s in fv["tickers"]}
    res["accept"] = {"coverage": cov1, "ours": ours, **acc, "finviz": {s: {**fvrow[s], **{k: st1[s][k] for k in ("m", "io", "it", "src", "new")}}
                                                                  for s in fv["tickers"]},
                     "unknown": sum(1 for v in st1.values() if v["m"] is None), "universe": len(nas)}
    gate1 = cov1["V2"] and cov1["V3"] and res["gates"]["V1"].get(f"{ACCEPT_Q[0]}Q{ACCEPT_Q[1]}", False)
    res["accept"]["verdict"] = ("تُقبل" if acc["accepted"] else "لا تُقبل") if gate1 else "لا قياس"
    log(f"① القبول: مجموعتنا {len(ours)} · finviz {len(fv['tickers'])} · التقاطع {len(acc['inter'])} · الاسترجاع {acc['recall']:.1%} · "
        f"الدقّة {acc['precision']:.1%} · التغطية {cov1} ⟵ {res['accept']['verdict']} · {int(time.time() - t0)}ث")
    ok = res["accept"]["verdict"] == "تُقبل"
    tag = "" if ok else " (وصفٌ — لا حكم)"

    # ② الـ60 جلسة
    rows2 = []
    nwc = {}
    for d in sess60:
        t = prev_s.get(d)
        p = (2026, 2) if t and t >= periods[(2026, 2)]["T"] else (2026, 1)
        nw = list(U["days"][d].get("N") or ())
        for s in nw:
            rows2.append((s, d, t, p))
        nwc[d] = U["days"][d].get("N_commit")
    syms2 = sorted({s for s, *_ in rows2} | {s for s, _ in r50})
    for p in ((2026, 1), (2026, 2), (2025, 4)):
        prefetch([(s, periods[p]["end"]) for s in syms2])
    cov2 = {f"{p[0]}Q{p[1]}": coverage(syms2, p) for p in ((2026, 1), (2026, 2))}
    qp = lambda d: (2026, 2) if prev_s.get(d, "") >= periods[(2026, 2)]["T"] else (2026, 1)
    q_m = {}
    for s in syms2:
        for p in ((2026, 1), (2026, 2)):
            q_m[(s, p)] = state(s, p, periods[p]["end"], {})["m"]    # بلا إغلاق ⟵ الكاذبُ الربعيّ وحدَه يُحسم هنا
    prefetch([(s, prev_s[d]) for s, d in {(s, d) for s, d, *_ in rows2} | set(r50) if prev_s.get(d) and q_m.get((s, qp(d))) is not False])
    run50 = set(r50)
    m2, units2 = {}, []
    with ThreadPoolExecutor(12) as ex:
        sts = list(ex.map(lambda r: state(r[0], r[3], r[2]) if r[2] else None, rows2))
    for (s, d, t, p), st in zip(rows2, sts):
        if not t:
            continue
        m2[(s, d)] = st
        c0, c5 = closes(t).get(s), None
        i = allsess.index(t) if t in allsess else None
        if i is not None and i >= 5:
            c5 = closes(allsess[i - 5]).get(s)
        r5 = (c0 / c5 - 1) if (c0 and c5) else None
        units2.append({"s": s, "d": d, "m": st["m"], "run": (s, d) in run50, "r5": r5})
    def m_of(s, d):
        if (s, d) in m2:
            return m2[(s, d)]["m"]
        t = prev_s.get(d)
        return state(s, qp(d), t)["m"] if t else None
    share = lambda xs: (sum(1 for x in xs if x is True), sum(1 for x in xs if x is not None))
    a708 = share([m_of(s, d) for s, d in r50])
    a195 = share([m_of(s, d) for s, d in r195])
    a248 = share([m_of(s, d) for s, d in r100])
    anw = share([u["m"] for u in units2])
    known = [u for u in units2 if u["m"] is not None and u["r5"] is not None]
    edges = I.quintile_edges([u["r5"] for u in known])
    bu = [(u["s"], "I" if u["m"] else "R", I.quintile_of(u["r5"], edges), 1 if u["run"] else 0) for u in known]
    est, (lo, hi) = I.boot_adj(bu, seed=BOOT_SEED)
    km = sum(1 for u in known if u["m"] and u["run"]); nm_ = sum(1 for u in known if u["m"])
    ku = sum(1 for u in known if not u["m"] and u["run"]); nu = sum(1 for u in known if not u["m"])
    v2b = year_verdict(nm_, lo, hi)
    res["sixty"] = {"coverage": cov2, "r708": a708, "r195": a195, "r248": a248, "nw": anw,
                    "w708": I.wilson(*a708), "w195": I.wilson(*a195), "wnw": I.wilson(*anw),
                    "prec_m": (km, nm_, I.wilson(km, nm_)), "prec_u": (ku, nu, I.wilson(ku, nu)), "adj": (est, lo, hi), "verdict": v2b,
                    "unknown_rows": sum(1 for u in units2 if u["m"] is None)}
    log(f"② المطابقون: بين الـ708 {a708} · الـ195 {a195} · الـ248 {a248} · «تحت المتابعة» {anw} · الدقّة مطابق {km}/{nm_} مقابل {ku}/{nu} · "
        f"المضبوط {est} [{lo}، {hi}] ⟵ {v2b}{tag}")

    # ⑤ الجاهزية على صفوف ②
    nout = {}
    for d, c in nwc.items():
        j = _git_json(c, "near_watch.json") if c else None
        nout[d] = {s: (e.get("n_out") if isinstance(e, dict) else None) for s, e in (j or {}).items()}
    cells = {}
    for u in known:
        no = nout.get(u["d"], {}).get(u["s"])
        if no is None:
            continue
        near = no <= 1
        k = ("M" if u["m"] else "-") + ("C" if near else "-")
        cells.setdefault(k, [0, 0])
        cells[k][1] += 1
        cells[k][0] += 1 if u["run"] else 0
    sub5 = [(u["s"], "I" if u["m"] else "R", I.quintile_of(u["r5"], edges), 1 if u["run"] else 0) for u in known
            if (nout.get(u["d"], {}).get(u["s"]) is not None and nout[u["d"]][u["s"]] <= 1)]
    e5 = I.boot_adj(sub5, seed=BOOT_SEED)
    res["ready"] = {"cells": {k: (v[0], v[1], I.wilson(*v)) for k, v in cells.items()}, "adj_MC_vs_C": e5,
                    "verdict": year_verdict(cells.get("MC", [0, 0])[1], *(e5[1]))}
    log(f"⑤ الجاهزية: {res['ready']['cells']} · (مطابق∧قريب) − (قريبٌ وحدَه) {e5} ⟵ {res['ready']['verdict']}{tag}")

    # ③ ثلاث سنوات
    units3, per_q = [], {}
    ent_by_day = {}
    for s, d in entries:
        ent_by_day.setdefault(d, set()).add(s)
    for p in Q3_PERIODS:
        T = periods[p]["T"]
        i = allsess.index(T)
        win = allsess[max(0, i - LOOKBACK + 1):i + 1]
        Uq = sorted(set().union(*[ent_by_day.get(d, set()) for d in win]))
        prefetch([(s, periods[p]["end"]) for s in Uq] + [(s, periods[prev_q(*p)]["end"]) for s in Uq])
        cov = coverage(Uq, p)
        pre_ = [s for s in Uq if state(s, p, periods[p]["end"], {})["m"] is not False]
        prefetch([(s, T) for s in pre_] + [(s, T) for s in Uq])
        per_q[f"{p[0]}Q{p[1]}"] = {"T": T, "U": len(Uq), "coverage": cov}
        for s in Uq:
            st = state(s, p, T)
            units3.append({"s": s, "q": f"{p[0]}Q{p[1]}", "y": T[:4], "T": T, "m": st["m"], "src": st["src"], "new": st["new"],
                           "io": st["io"], "it": st["it"]})
        log(f"   ③ {p}: T {T} · الكون {len(Uq)} · التغطية {cov} · {int(time.time() - t0)}ث")
    bars, splits = {}, {}

    def fetch_sym(s):
        j = _poly(f"https://api.polygon.io/v2/aggs/ticker/{s}/range/1/day/2022-11-01/2026-03-31?adjusted=true&sort=asc&limit=50000", key) or {}
        b = [(dt.datetime.utcfromtimestamp(r["t"] / 1000).date().isoformat(), r.get("h"), r.get("c")) for r in j.get("results") or []]
        sp = _poly(f"https://api.polygon.io/v3/reference/splits?ticker={s}&limit=1000", key) or {}
        return s, b, [x.get("execution_date") for x in sp.get("results") or []]
    with ThreadPoolExecutor(12) as ex:
        for s, b, sp in ex.map(fetch_sym, sorted({u["s"] for u in units3 if u["m"] is not None})):
            bars[s], splits[s] = b, sp
    excl = {"بلا شموع": 0, "تقسيمٌ في النافذة": 0, "أقلُّ من النافذة": 0, "مجهول": 0}
    for u in units3:
        if u["m"] is None:
            excl["مجهول"] += 1
            continue
        b = bars.get(u["s"]) or []
        days = [x[0] for x in b]
        i0 = days.index(u["T"]) if u["T"] in days else None
        if i0 is None:
            excl["بلا شموع"] += 1
            u["m"] = None
            continue
        u["r5"] = (b[i0][2] / b[i0 - 5][2] - 1) if i0 >= 5 and b[i0 - 5][2] else None
        for n in HORIZONS:
            end = days[min(i0 + n, len(days) - 1)]
            sp_in = any(u["T"] < x <= end for x in splits.get(u["s"], []) if x)
            for lv in LEVELS:
                u[f"h{int(lv * 100)}_{n}"] = None if sp_in else outcome_hits(b, i0, n, lv)
    gov = "h50_20"
    years = {}
    for y in ("2023", "2024", "2025"):
        uy = [u for u in units3 if u["y"] == y and u["m"] is not None and u.get(gov) is not None and u.get("r5") is not None]
        ed = I.quintile_edges([u["r5"] for u in uy])
        bu3 = [(u["s"], "I" if u["m"] else "R", I.quintile_of(u["r5"], ed), 1 if u[gov] else 0) for u in uy]
        est3, (l3, h3) = I.boot_adj(bu3, seed=BOOT_SEED)
        nm3 = sum(1 for u in uy if u["m"])
        tab = {}
        for k in [f"h{int(lv * 100)}_{n}" for lv in LEVELS for n in HORIZONS]:
            ok_ = [u for u in units3 if u["y"] == y and u["m"] is not None and u.get(k) is not None]
            km3 = sum(1 for u in ok_ if u["m"] and u[k]); n_m = sum(1 for u in ok_ if u["m"])
            ku3 = sum(1 for u in ok_ if not u["m"] and u[k]); n_u = sum(1 for u in ok_ if not u["m"])
            tab[k] = (km3, n_m, ku3, n_u, I.wilson(km3, n_m), I.wilson(ku3, n_u))
        years[y] = {"n_m": nm3, "adj": (est3, l3, h3), "verdict": year_verdict(nm3, l3, h3), "tab": tab}
        log(f"③ {y}: مطابق {nm3} · المضبوط {est3} [{l3}، {h3}] ⟵ {years[y]['verdict']} · {tab[gov]}")
    res["three"] = {"per_q": per_q, "years": years, "weakest": weakest([v["verdict"] for v in years.values()]), "excl": excl}
    log(f"③ الحكم بالأضعف: {res['three']['weakest']}{tag} · المستبعَد {excl}")

    # ④ الفصل على مطابقي ③
    mus = [u for u in units3 if u["m"] is True and u.get(gov) is not None]
    sub_cache = {}

    def subm(s):
        if s not in sub_cache:
            cik = str(details(*s).get("cik") or "").lstrip("0")
            j = _sec_get(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json", contact) if cik.isdigit() else None
            rec = (json.loads(j) if j else {}).get("filings", {}).get("recent", {})
            sub_cache[s] = [{"form": f, "date": d, "items": it} for f, d, it in zip(rec.get("form", []), rec.get("filingDate", []), rec.get("items", []))]
        return sub_cache[s]
    for u in mus:
        y, q = int(u["q"][:4]), int(u["q"][-1])
        qs = dt.date(y, 3 * q - 2, 1).isoformat()
        fl_ = I.offering_flags(subm((u["s"], u["T"])), qs, u["T"])
        u["offer"] = bool(fl_["registered"] or fl_["placement_d"] or fl_["pipe_302"])
        p, pp = (y, q), prev_q(y, q)
        cs, _ = cusips_for(u["s"], p)
        cps, _ = cusips_for(u["s"], pp)
        a = hold[p][hold[p]["cusip"].isin(cs or [])].groupby("cik")["shares"].sum().to_dict() if p in hold else {}
        b = hold[pp][hold[pp]["cusip"].isin(cps or [])].groupby("cik")["shares"].sum().to_dict() if pp in hold else {}
        dlt = {c: a.get(c, 0) - b.get(c, 0) for c in set(a) | set(b)}
        sh_ = mm_share(dlt, names, mm)
        u["mm_led"] = None if sh_ is None else sh_ >= 0.5
    four = {}
    for k, f in (("بلا طرح", lambda u: u.get("offer") is False), ("بعد طرح", lambda u: u.get("offer") is True),
                 ("صنّاعُ سوق", lambda u: u.get("mm_led") is True), ("صناديق", lambda u: u.get("mm_led") is False)):
        g = [u for u in mus if f(u)]
        kk = sum(1 for u in g if u[gov])
        four[k] = (kk, len(g), I.wilson(kk, len(g)), "تُقرأ" if len(g) >= FLOOR4 else "لا تُقرأ")
    res["four"] = four
    log(f"④ {four}")
    res["elapsed_s"] = int(time.time() - t0)
    res["units3"] = units3
    with gzip.open(os.path.join(OUT, "bt.json.gz"), "wt", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, default=str)
    slim = {k: v for k, v in res.items() if k != "units3"}
    print("INSTBT_JSON " + json.dumps(slim, ensure_ascii=False, default=str), flush=True)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("check", "run"), default="check")
    a = ap.parse_args(argv)
    if not contract_ok():
        log("⛔ بصمةُ العقد تغيّرت — خروج 9")
        return CONTRACT_RC
    if a.mode == "check":
        log("✅ العقد مطابق")
        return 0
    key = (os.environ.get("POLYGON_API_KEY") or "").strip()
    contact = (os.environ.get("SEC_CONTACT") or "").strip()
    if not key or not contact:
        log("⛔ بلا مفتاح Polygon أو SEC_CONTACT")
        return KEY_RC
    return mode_run(key, contact)


if __name__ == "__main__":
    sys.exit(main())
