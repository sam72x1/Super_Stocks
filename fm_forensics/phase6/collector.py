"""🔎🧭⑥ PHASE 6 — Workstream A: prospective, point-in-time collector for Faisal-mentioned tickers.

Research-only (no production decision, no Telegram, no production state file, no threshold). It reuses the
repository's existing provider integrations (Yahoo `Ticker.info`/`splits`, TradingView screener, ChartExchange
borrow page, SEC submissions + XBRL `dei`, Nasdaq split calendar) through **injected fetchers** so the suite runs
offline. Every observation is written once to an append-only, hash-chained JSONL ledger with an explicit status;
missing is never zero and a current value is never relabelled as historical.

Categories (mission §A):
  CAT 1  POINT_IN_TIME   — value captured by us at `collected_utc`; the provider gives no as-of ⇒ as-of = collection.
  CAT 2  HISTORICAL      — value with a provider-supplied, verifiable as-of/event timestamp (`source_asof`).
  CAT 3  CURRENT_ONLY    — assigned **at use time** by `evidence_class(record, T)`: a record whose as-of is after the
                           reference date T cannot describe T (it is "current only" relative to T).
  CAT 4  UNAVAILABLE     — status UNKNOWN / FAILED / NOT_ATTEMPTED (value is the literal string "UNKNOWN").
Only CAT 1–2 records with as-of ≤ T count as historical evidence for T.
"""
import csv
import datetime as dt
import gzip
import hashlib
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
os.chdir(ROOT)                           # the catalog envelope (`envelope_p100.json`) is loaded relative to cwd
DATA = os.path.join(HERE, "data")
OUT = os.environ.get("P6_OUT") or os.path.join(HERE, "out")
LEDGER_PATH = os.path.join(DATA, "PHASE6_LEDGER.jsonl")
MENTIONS_PATH = os.path.join(DATA, "PHASE6_MENTIONS.csv")
RAW_DIR = os.environ.get("P6_RAW_DIR") or os.path.join(HERE, "raw")
GENESIS = "0" * 64
UNKNOWN = "UNKNOWN"
FIELDS = ("public_float", "shares_outstanding", "short_interest", "borrow_available", "borrow_fee",
          "sec_filing", "reverse_split", "identity")
SHARE_COUNT_FIELDS = ("public_float", "shares_outstanding", "short_interest", "borrow_available")
STATUS = ("OK", "UNKNOWN", "FAILED", "NOT_ATTEMPTED")
CE_QUOTA = 48            # ChartExchange returns a shell page after ≈50 requests per runner (ctb_harvest measurement)
STALE_ASOF_DAYS = 45     # short-interest as-of older than this at collection ⇒ quality flag (not a rejection)
PACE_S = float(os.environ.get("P6_PACE_S") or 0.4)
ANCHORS = ("DKI", "SXTC", "HUBC")


# ---------------------------------------------------------------- helpers
def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()


def utc_now_iso(now=None) -> str:
    now = now or dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        raise ValueError("naive datetime refused: collection timestamps must be tz-aware UTC")
    return now.astimezone(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_ts(s):
    """ISO timestamp ⟶ tz-aware UTC datetime · None if unparseable. Naive strings are **refused** (None), never assumed UTC."""
    if not s or s == UNKNOWN:
        return None
    try:
        t = dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None
    if t.tzinfo is None:
        return None
    return t.astimezone(dt.timezone.utc)


def _num(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if f != f:                      # NaN is not a value
        return None
    return f


def store_raw(payload, raw_dir=None) -> str:
    """Raw provider response ⟶ gz file named by its sha256 (content-addressed) · returns the sha."""
    raw_dir = raw_dir or RAW_DIR
    sha = _sha(payload)
    try:
        os.makedirs(raw_dir, exist_ok=True)
        p = os.path.join(raw_dir, sha + ".json.gz")
        if not os.path.exists(p):
            with gzip.open(p, "wt", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, default=str)
    except OSError:
        pass
    return sha


# ---------------------------------------------------------------- ledger
class Ledger:
    """Append-only, hash-chained JSONL. `prev_sha256` links rows; `sha256` covers the row without itself."""

    def __init__(self, path):
        self.path = path
        self.rows = []
        self.keys = set()
        if os.path.exists(path):
            for line in open(path, encoding="utf-8"):
                line = line.strip()
                if line:
                    r = json.loads(line)
                    self.rows.append(r)
                    self.keys.add(r["obs_key"])

    @property
    def last_sha(self):
        return self.rows[-1]["sha256"] if self.rows else GENESIS

    def has(self, obs_key) -> bool:
        return obs_key in self.keys

    def append(self, rec: dict) -> bool:
        """True if appended · False if the obs_key already exists (idempotent)."""
        if rec["obs_key"] in self.keys:
            return False
        rec = dict(rec)
        rec["seq"] = len(self.rows) + 1
        rec["prev_sha256"] = self.last_sha
        rec["sha256"] = _sha({k: v for k, v in rec.items() if k != "sha256"})
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
        self.rows.append(rec)
        self.keys.add(rec["obs_key"])
        return True

    def verify(self) -> list:
        """Chain + schema problems (empty list = sound)."""
        bad, prev = [], GENESIS
        for i, r in enumerate(self.rows, 1):
            if r.get("seq") != i:
                bad.append(f"seq {r.get('seq')} != {i}")
            if r.get("prev_sha256") != prev:
                bad.append(f"seq {i}: prev_sha256 mismatch")
            if _sha({k: v for k, v in r.items() if k != "sha256"}) != r.get("sha256"):
                bad.append(f"seq {i}: sha256 mismatch")
            bad.extend(f"seq {i}: {m}" for m in schema_problems(r))
            prev = r.get("sha256")
        return bad


def schema_problems(r: dict) -> list:
    p = []
    for k in ("obs_key", "run_id", "collected_utc", "ticker", "field", "value", "units", "source", "source_asof",
              "asof_basis", "category", "status", "failure_reason", "raw_sha256", "split_frame", "security_id"):
        if k not in r:
            p.append(f"missing {k}")
    if p:
        return p
    if r["field"] not in FIELDS:
        p.append(f"field {r['field']}")
    if r["status"] not in STATUS:
        p.append(f"status {r['status']}")
    if r["status"] != "OK" and (r["value"] != UNKNOWN or r["category"] != 4):
        p.append("non-OK row must carry value=UNKNOWN and category=4")
    if r["status"] == "OK" and r["value"] == UNKNOWN:
        p.append("OK row with UNKNOWN value")
    if r["status"] == "OK" and r["field"] in SHARE_COUNT_FIELDS and _num(r["value"]) is None:
        p.append("share-count field must be numeric when OK")
    if r["status"] == "OK" and r["field"] in SHARE_COUNT_FIELDS and _num(r["value"]) == 0 and r["units"] != "shares_zero_reported":
        p.append("zero share count must be explicitly marked as provider-reported zero")
    if parse_ts(r["collected_utc"]) is None:
        p.append("collected_utc not tz-aware ISO")
    if r["asof_basis"] not in ("PROVIDER", "COLLECTION", "UNKNOWN"):
        p.append("asof_basis")
    if r["category"] not in (1, 2, 4):
        p.append("category at capture must be 1, 2 or 4 (3 is assigned at use time)")
    if r["category"] == 2 and r["asof_basis"] != "PROVIDER":
        p.append("CAT 2 requires provider as-of")
    if r["category"] == 1 and r["asof_basis"] != "COLLECTION":
        p.append("CAT 1 requires collection as-of")
    return p


def evidence_class(rec: dict, ref_date: str) -> int:
    """Class of `rec` as evidence about reference date T (ISO date, New York session day):
    1/2 if OK and as-of ≤ T (date granularity) · 3 if OK but as-of after T (current-only relative to T) · 4 otherwise."""
    if rec.get("status") != "OK":
        return 4
    asof = str(rec.get("source_asof") or "")[:10]
    if not asof or asof == UNKNOWN:
        return 4
    return int(rec["category"]) if asof <= ref_date else 3


def comparable(a: dict, b: dict) -> bool:
    """Two share-count observations are comparable only in the same split frame (no silent cross-split comparison)."""
    return a.get("split_frame") == b.get("split_frame") and a.get("field") == b.get("field")


# ---------------------------------------------------------------- mentions
def _read_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_mentions(root=ROOT) -> list:
    """Deterministic registry of Faisal mentions from the repository's dated sources (no network).
    One row per (evidence_id, original_ticker); duplicate posts collapse on that key."""
    rows = {}

    def put(ev, tick, date, ts, tz, prec, author, is_f, src, canon=None):
        tick = (tick or "").strip().upper()
        if not tick or not ev:
            return
        k = (ev, tick)
        if k in rows:
            return
        rows[k] = dict(mention_id=f"{ev}|{tick}", evidence_id=ev, original_ticker=tick,
                       canonical_ticker=(canon or tick).strip().upper(), post_date=date or UNKNOWN,
                       post_timestamp=ts or UNKNOWN, post_tz=tz or UNKNOWN, ts_precision=prec, author=author or UNKNOWN,
                       is_faisal=int(bool(is_f)), source=src)

    p = os.path.join(root, "fm_forensics", "phase5", "PHASE5_COHORT_MANIFEST.csv")
    if os.path.exists(p):
        for r in _read_csv(p):
            put(r["EVIDENCE_ID"], r["TICKER_AT_DECISION"], r["DECISION_DATE"], None, "America/New_York",
                "DATE" if r.get("DATE_AMBIGUOUS") == "0" else "DATE_AMBIGUOUS", "F", 1, "phase5_cohort", r["SECURITY_ID"])
    p = os.path.join(root, "fm_forensics", "phase3", "FAISAL_TIMELINE.csv")
    if os.path.exists(p):
        for r in _read_csv(p):
            put(r["EVIDENCE_ID"], r["TICKER"], r["DATE"], None, "America/New_York", "DATE", r["AUTHOR"],
                r["IS_FAISAL"] in ("1", "True"), "phase3_timeline")
    base = os.path.join(root, "faisal_method_v41", "final_protocol", "intake")
    if os.path.isdir(base):
        for b in sorted(os.listdir(base)):
            ap = os.path.join(base, b, "annotations.json")
            if not os.path.exists(ap):
                continue
            d = json.load(open(ap, encoding="utf-8"))
            imgs = d.get("images") or {}
            items = imgs.items() if isinstance(imgs, dict) else enumerate(imgs)
            for img_id, a in items:
                if not isinstance(a, dict):
                    continue
                ts = a.get("post_timestamp_utc") or a.get("post_timestamp_visible")
                put(str(a.get("image_id") or img_id), a.get("symbol"), a.get("decision_date"), ts,
                    "UTC" if ts else "America/New_York", "TIMESTAMP" if ts else str(a.get("date_evidence_level") or "DATE"),
                    a.get("author"), a.get("faisal_author"), f"intake:{b}")
    p = os.path.join(root, "faisal_validation", "PROSPECTIVE_LEDGER.jsonl")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                ts = r.get("faisal_timestamp")
                put(f"{r.get('case_id') or 'PB'}#seq{r.get('seq')}", r.get("ticker"), (ts or "")[:10], ts, "UTC" if ts else UNKNOWN,
                    "TIMESTAMP" if ts else UNKNOWN, "F", 1, "prospective_ledger")
    out = sorted(rows.values(), key=lambda r: (r["canonical_ticker"], r["post_date"], r["evidence_id"]))
    return out


PLACEHOLDER_TICKERS = {"UNK", "UNKNOWN", ""}


def mention_tickers(mentions, faisal_only: bool = True) -> list:
    """Tickers to collect: Faisal-authored mentions only by default (third-party/EDU mentions stay in the registry but are not collected)."""
    return sorted({m["canonical_ticker"] for m in mentions
                   if m["canonical_ticker"] not in PLACEHOLDER_TICKERS and (m["is_faisal"] or not faisal_only)})


def write_mentions(mentions, path=MENTIONS_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    keys = list(mentions[0].keys()) if mentions else ["mention_id"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(mentions)


# ---------------------------------------------------------------- identity / split frame
def frozen_sec(root=ROOT) -> dict:
    p = os.path.join(root, "fm_forensics", "data", "sec_2026-10-08.json.gz")
    if not os.path.exists(p):
        return {}
    return json.load(gzip.open(p, "rt", encoding="utf-8")).get("symbols") or {}


def frozen_splits(root=ROOT) -> dict:
    d = os.path.join(root, "fm_forensics", "data")
    if not os.path.isdir(d):
        return {}
    files = sorted(f for f in os.listdir(d) if f.startswith("bars_"))
    if not files:
        return {}
    return json.load(gzip.open(os.path.join(d, files[-1]), "rt", encoding="utf-8")).get("splits") or {}


def split_frame(splits, obs_date: str) -> str:
    """Frame label = last reverse split (ratio < 1) with effective date ≤ obs_date · 'pre:none' if none known."""
    rs = sorted((d, float(r)) for d, r in (splits or []) if float(r) < 1.0 and d <= obs_date)
    return f"post:{rs[-1][0]}" if rs else "pre:none"


# ---------------------------------------------------------------- fetchers (default = production integrations)
def default_fetchers():
    import contextlib
    import io
    sys.path.insert(0, ROOT)
    with contextlib.redirect_stdout(io.StringIO()):
        import Super_stock as S                                   # noqa: E402
        import data_quality as DQ                                 # noqa: E402
        import tv_data as TV                                      # noqa: E402
    import requests

    def yahoo_info(sym):
        if S.yf is None:
            return None
        return S._fetch_info(S.yf.Ticker(sym)) or None

    def yahoo_splits(sym):
        s = S._fetch_splits(sym)
        if s is None:
            return None
        return [(str(d)[:10], float(v)) for d, v in s.items()]

    def tv_scan():
        return TV.scan(["name", "float_shares_outstanding"])

    def ce_borrow(sym):
        diag = {}
        out = S.ce_borrow_info(sym, diag=diag)
        return out, diag

    def sec_cik(sym):
        return (S.sec_cik_map() or {}).get(sym.upper())

    def sec_get(url):
        r = requests.get(url, headers=S.SEC_UA, timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"http:{r.status_code}")
        return r.json()

    def sec_submissions(cik):
        return sec_get(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json")

    def sec_dei(cik, concept):
        return sec_get(f"https://data.sec.gov/api/xbrl/companyconcept/CIK{int(cik):010d}/dei/{concept}.json")

    def nasdaq_calendar():
        cal, _stats = DQ.nasdaq_calendar()
        return cal

    return dict(yahoo_info=yahoo_info, yahoo_splits=yahoo_splits, tv_scan=tv_scan, ce_borrow=ce_borrow, sec_cik=sec_cik,
                sec_submissions=sec_submissions, sec_dei=sec_dei, nasdaq_calendar=nasdaq_calendar)


# ---------------------------------------------------------------- collection
class Collector:
    def __init__(self, ledger: Ledger, fetchers: dict, run_id: str, now=None, raw_dir=None, splits_known=None,
                 security_ids=None, pace_s=0.0, ce_quota=CE_QUOTA, log=print):
        self.L, self.F, self.run_id = ledger, fetchers, str(run_id)
        self.now = now or dt.datetime.now(dt.timezone.utc)
        self.collected = utc_now_iso(self.now)
        self.obs_date = self.collected[:10]
        self.raw_dir = raw_dir or RAW_DIR
        self.splits_known = dict(splits_known or {})
        self.security_ids = dict(security_ids or {})
        self.pace_s, self.ce_quota, self.ce_used = pace_s, ce_quota, 0
        self.log = log
        self.attempts = []                      # (ticker, field, source, status) — audit completeness
        self._tv = None

    # -- record factory ------------------------------------------------
    def _rec(self, ticker, field, source, event_id, value=UNKNOWN, units=UNKNOWN, source_asof=UNKNOWN, asof_basis="UNKNOWN",
             status="UNKNOWN", failure_reason="", raw_sha="", source_url="", original_ticker=None, extra=None):
        if status == "OK":
            category = 2 if asof_basis == "PROVIDER" else 1
        else:
            category, value, units = 4, UNKNOWN, UNKNOWN
        if status == "OK" and field in SHARE_COUNT_FIELDS:
            n = _num(value)
            if n is None:
                status, category, value, units, failure_reason = "UNKNOWN", 4, UNKNOWN, UNKNOWN, failure_reason or "non_numeric_value"
            elif n == 0:
                units = "shares_zero_reported"
        rec = dict(obs_key=_sha([ticker, field, source, event_id]), run_id=self.run_id, collected_utc=self.collected,
                   ticker=ticker, original_ticker=original_ticker or ticker, security_id=self.security_ids.get(ticker, UNKNOWN),
                   field=field, value=value, units=units, source=source, source_url=source_url, source_asof=source_asof,
                   asof_basis=asof_basis if status == "OK" else "UNKNOWN", category=category, status=status,
                   failure_reason=failure_reason or "", raw_sha256=raw_sha or "",
                   split_frame=split_frame(self.splits_known.get(ticker), str(source_asof)[:10] if status == "OK" and asof_basis == "PROVIDER" and str(source_asof)[:10] <= self.obs_date else self.obs_date))
        if extra:
            rec["extra"] = extra
        return rec

    def _emit(self, rec) -> bool:
        self.attempts.append((rec["ticker"], rec["field"], rec["source"], rec["status"]))
        return self.L.append(rec)

    def _call(self, name, *a):
        f = self.F.get(name)
        if f is None:
            return None, "fetcher_not_configured"
        try:
            if self.pace_s:
                time.sleep(self.pace_s)
            return f(*a), ""
        except Exception as e:                                   # noqa: BLE001
            return None, f"exc:{type(e).__name__}:{str(e)[:80]}"

    # -- per-field collectors ------------------------------------------
    def yahoo_block(self, t):
        info, err = self._call("yahoo_info", t)
        if info is None:
            for fld in ("public_float", "short_interest"):
                self._emit(self._rec(t, fld, "yahoo_info", self.obs_date, status="FAILED", failure_reason=err or "empty_response"))
            return
        sha = store_raw({"provider": "yahoo_info", "ticker": t, "collected_utc": self.collected, "payload": info}, self.raw_dir)
        fv = _num(info.get("floatShares"))
        if fv is None:
            self._emit(self._rec(t, "public_float", "yahoo_info", self.obs_date, status="UNKNOWN", failure_reason="provider_no_floatShares", raw_sha=sha))
        else:
            self._emit(self._rec(t, "public_float", "yahoo_info", self.obs_date, fv, "shares", self.collected, "COLLECTION", "OK", raw_sha=sha))
        so = _num(info.get("sharesOutstanding"))
        if so is not None:
            self._emit(self._rec(t, "shares_outstanding", "yahoo_info", self.obs_date, so, "shares", self.collected, "COLLECTION", "OK", raw_sha=sha))
        si = _num(info.get("sharesShort"))
        asof = info.get("dateShortInterest")
        if si is None:
            self._emit(self._rec(t, "short_interest", "yahoo_info", self.obs_date, status="UNKNOWN", failure_reason="provider_no_sharesShort", raw_sha=sha))
            return
        asof_iso = None
        if asof not in (None, ""):
            try:
                asof_iso = dt.datetime.fromtimestamp(int(asof), dt.timezone.utc).date().isoformat()
            except (TypeError, ValueError, OSError):
                asof_iso = str(asof)[:10] if len(str(asof)) >= 10 and str(asof)[4] == "-" else None
        if asof_iso:
            flags = []
            try:
                if (dt.date.fromisoformat(self.obs_date) - dt.date.fromisoformat(asof_iso)).days > STALE_ASOF_DAYS:
                    flags.append("STALE_ASOF")
            except ValueError:
                flags.append("ASOF_UNPARSEABLE")
            self._emit(self._rec(t, "short_interest", "yahoo_info", f"asof:{asof_iso}", si, "shares", asof_iso, "PROVIDER", "OK",
                                 raw_sha=sha, extra={"quality_flags": flags, "shortRatio": info.get("shortRatio")}))
        else:
            self._emit(self._rec(t, "short_interest", "yahoo_info", self.obs_date, si, "shares", self.collected, "COLLECTION", "OK",
                                 raw_sha=sha, extra={"quality_flags": ["NO_PROVIDER_ASOF"]}))

    def tv_block(self, t):
        if self._tv is None:
            scan, err = self._call("tv_scan")
            self._tv = (scan or {}, err or ("scan_failed" if scan is None else ""))
            if scan:
                store_raw({"provider": "tv_scan", "collected_utc": self.collected, "payload": scan}, self.raw_dir)
        scan, err = self._tv
        if not scan:
            self._emit(self._rec(t, "public_float", "tv_scan", self.obs_date, status="FAILED", failure_reason=err or "scan_failed"))
            return
        hit = None
        for ex in ("NASDAQ", "NYSE", "AMEX"):
            if f"{ex}:{t}" in scan:
                hit = scan[f"{ex}:{t}"]
                break
        if hit is None:
            self._emit(self._rec(t, "public_float", "tv_scan", self.obs_date, status="UNKNOWN", failure_reason="ticker_not_in_scan"))
            return
        fv = _num(hit.get("float_shares_outstanding"))
        if fv is None:
            self._emit(self._rec(t, "public_float", "tv_scan", self.obs_date, status="UNKNOWN", failure_reason="provider_no_float"))
        else:
            self._emit(self._rec(t, "public_float", "tv_scan", self.obs_date, fv, "shares", self.collected, "COLLECTION", "OK"))

    def borrow_block(self, t):
        if self.ce_used >= self.ce_quota:
            for fld in ("borrow_available", "borrow_fee"):
                self._emit(self._rec(t, fld, "chartexchange", self.obs_date, status="NOT_ATTEMPTED", failure_reason=f"quota:{self.ce_quota}"))
            return
        self.ce_used += 1
        res, err = self._call("ce_borrow", t)
        out, diag = (res if isinstance(res, tuple) else (res, {})) if res is not None else ({}, {"reason": err})
        url = f"https://chartexchange.com/symbol/nasdaq-{t.lower()}/borrow-fee/"
        if not out:
            why = (diag or {}).get("reason") or err or "empty"
            st = "FAILED" if why.startswith(("http", "exc", "parse:challenge", "parse:shell")) else "UNKNOWN"
            for fld in ("borrow_available", "borrow_fee"):
                self._emit(self._rec(t, fld, "chartexchange", self.obs_date, status=st, failure_reason=why, source_url=url))
            return
        sha = store_raw({"provider": "chartexchange", "ticker": t, "collected_utc": self.collected, "payload": out}, self.raw_dir)
        av = _num(out.get("shares_available"))
        if av is None:
            self._emit(self._rec(t, "borrow_available", "chartexchange", self.obs_date, status="UNKNOWN", failure_reason="provider_no_available", raw_sha=sha, source_url=url))
        else:
            self._emit(self._rec(t, "borrow_available", "chartexchange", self.obs_date, av, "shares", self.collected, "COLLECTION", "OK", raw_sha=sha, source_url=url))
        fee = _num(out.get("borrow_fee"))
        if fee is None:
            self._emit(self._rec(t, "borrow_fee", "chartexchange", self.obs_date, status="UNKNOWN", failure_reason="provider_no_fee", raw_sha=sha, source_url=url))
        else:
            self._emit(self._rec(t, "borrow_fee", "chartexchange", self.obs_date, fee, "pct_annual", self.collected, "COLLECTION", "OK", raw_sha=sha, source_url=url))

    def sec_block(self, t):
        cik, err = self._call("sec_cik", t)
        if not cik:
            self._emit(self._rec(t, "identity", "sec_cik_map", self.obs_date, status="FAILED" if err else "UNKNOWN", failure_reason=err or "ticker_not_in_cik_map"))
            self._emit(self._rec(t, "sec_filing", "sec_submissions", self.obs_date, status="NOT_ATTEMPTED", failure_reason="no_cik"))
            return
        self.security_ids.setdefault(t, f"CIK{int(cik):010d}")
        sub, err = self._call("sec_submissions", cik)
        if not sub:
            self._emit(self._rec(t, "identity", "sec_submissions", self.obs_date, status="FAILED", failure_reason=err or "empty"))
            self._emit(self._rec(t, "sec_filing", "sec_submissions", self.obs_date, status="FAILED", failure_reason=err or "empty"))
            return
        sha = store_raw({"provider": "sec_submissions", "cik": cik, "collected_utc": self.collected, "payload": sub}, self.raw_dir)
        ident = dict(cik=int(cik), name=sub.get("name"), tickers=sub.get("tickers") or [], exchanges=sub.get("exchanges") or [],
                     former_names=[{"name": x.get("name"), "from": x.get("from"), "to": x.get("to")} for x in (sub.get("formerNames") or [])])
        self._emit(self._rec(t, "identity", "sec_submissions", self.obs_date, json.dumps(ident, ensure_ascii=False, sort_keys=True), "json",
                             self.collected, "COLLECTION", "OK", raw_sha=sha,
                             extra={"ticker_listed_by_sec": t.upper() in [x.upper() for x in ident["tickers"]]}))
        rec = (sub.get("filings") or {}).get("recent") or {}
        forms, dates, acc, acct = rec.get("form") or [], rec.get("filingDate") or [], rec.get("accessionNumber") or [], rec.get("acceptanceDateTime") or []
        n = 0
        for i in range(min(len(forms), len(dates), len(acc))):
            a = acct[i] if i < len(acct) else ""
            n += int(self._emit(self._rec(t, "sec_filing", "sec_submissions", acc[i], json.dumps({"form": forms[i], "filingDate": dates[i], "accession": acc[i], "acceptance": a}, sort_keys=True),
                                          "json", (a or dates[i]), "PROVIDER", "OK", raw_sha=sha,
                                          source_url=f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc[i].replace('-', '')}/")))
        for concept, fld, units in (("EntityPublicFloat", "public_float", "USD"), ("EntityCommonStockSharesOutstanding", "shares_outstanding", "shares")):
            d, err = self._call("sec_dei", cik, concept)
            if not d:
                self._emit(self._rec(t, fld, f"sec_dei:{concept}", self.obs_date, status="FAILED" if err and not err.endswith("http:404") else "UNKNOWN", failure_reason=err or "no_concept"))
                continue
            sha2 = store_raw({"provider": f"sec_dei:{concept}", "cik": cik, "collected_utc": self.collected, "payload": d}, self.raw_dir)
            pts = []
            for u, arr in (d.get("units") or {}).items():
                for x in arr:
                    pts.append((x.get("end"), x.get("filed"), x.get("val"), x.get("accn"), u))
            for end, filed, val, accn, u in pts:
                ev = f"{accn}:{end}"
                if fld == "public_float":
                    self._emit(self._rec(t, fld, f"sec_dei:{concept}", ev, val, units, end or filed, "PROVIDER", "OK", raw_sha=sha2,
                                         extra={"filed": filed, "accession": accn, "note": "SEC public float is a dollar value, not a share count"}))
                else:
                    self._emit(self._rec(t, fld, f"sec_dei:{concept}", ev, val, units, end or filed, "PROVIDER", "OK", raw_sha=sha2, extra={"filed": filed, "accession": accn}))
        return n

    def splits_block(self, t, nasdaq_cal):
        sp, err = self._call("yahoo_splits", t)
        if sp is None:
            self._emit(self._rec(t, "reverse_split", "yahoo_splits", self.obs_date, status="FAILED", failure_reason=err or "empty"))
        else:
            sha = store_raw({"provider": "yahoo_splits", "ticker": t, "collected_utc": self.collected, "payload": sp}, self.raw_dir)
            seen = set()
            for d, r in sp:
                if float(r) >= 1.0:
                    continue
                key = (d[:10], round(float(r), 8))
                if key in seen:
                    continue
                seen.add(key)
                self.splits_known.setdefault(t, [])
                if [d[:10], float(r)] not in [[x[0], float(x[1])] for x in self.splits_known[t]]:
                    self.splits_known[t].append([d[:10], float(r)])
                self._emit(self._rec(t, "reverse_split", "yahoo_splits", f"{d[:10]}:{r}", json.dumps({"effective": d[:10], "ratio": float(r)}), "ratio",
                                     d[:10], "PROVIDER", "OK", raw_sha=sha))
            if not seen:
                self._emit(self._rec(t, "reverse_split", "yahoo_splits", self.obs_date, status="UNKNOWN", failure_reason="no_reverse_split_in_history"))
        if nasdaq_cal is None:
            self._emit(self._rec(t, "reverse_split", "nasdaq_calendar", self.obs_date, status="FAILED", failure_reason="calendar_unavailable"))
            return
        ev = nasdaq_cal.get(t) or []
        if not ev:
            self._emit(self._rec(t, "reverse_split", "nasdaq_calendar", self.obs_date, status="UNKNOWN", failure_reason="not_in_calendar_window"))
        for item in ev:
            d, r = item[0], item[1]
            ann = item[2] if len(item) > 2 else None
            self._emit(self._rec(t, "reverse_split", "nasdaq_calendar", f"{d}:{r}", json.dumps({"effective": d, "ratio": float(r), "announced": ann}), "ratio",
                                 d, "PROVIDER", "OK"))

    # -- run ---------------------------------------------------------------
    def run(self, tickers, resume=True):
        cal, cerr = self._call("nasdaq_calendar")
        if cal:
            store_raw({"provider": "nasdaq_calendar", "collected_utc": self.collected, "payload": cal}, self.raw_dir)
        done, skipped = [], []
        for t in tickers:
            t = t.upper()
            if resume and self.L.has(_sha([t, "public_float", "yahoo_info", self.obs_date])) and self.L.has(_sha([t, "identity", "sec_submissions", self.obs_date])):
                skipped.append(t)
                continue
            self.yahoo_block(t)
            self.tv_block(t)
            self.borrow_block(t)
            self.sec_block(t)
            self.splits_block(t, cal)
            done.append(t)
            self.log(f"  {t}: rows so far {len(self.L.rows)}")
        return dict(done=done, skipped=skipped, calendar_error=cerr, ce_used=self.ce_used)


def audit(ledger: Ledger, run_id: str) -> dict:
    """Completeness: every (ticker, field, source) attempted in `run_id` has a row with a status; counts by status/category."""
    rows = [r for r in ledger.rows if r["run_id"] == str(run_id)]
    by = {}
    for r in rows:
        by[r["status"]] = by.get(r["status"], 0) + 1
    cats = {}
    for r in rows:
        cats[r["category"]] = cats.get(r["category"], 0) + 1
    tick = sorted({r["ticker"] for r in rows})
    missing = []
    for t in tick:
        have = {(r["field"], r["source"].split(":")[0]) for r in rows if r["ticker"] == t}
        for need in (("public_float", "yahoo_info"), ("short_interest", "yahoo_info"), ("public_float", "tv_scan"),
                     ("borrow_available", "chartexchange"), ("identity", "sec_cik_map" if ("identity", "sec_cik_map") in have else "sec_submissions"),
                     ("reverse_split", "yahoo_splits"), ("reverse_split", "nasdaq_calendar")):
            if need not in have:
                missing.append((t,) + need)
    return dict(rows=len(rows), by_status=by, by_category={str(k): v for k, v in cats.items()}, tickers=len(tick), missing=missing,
                chain_problems=ledger.verify())


def coverage_report(ledger: Ledger, run_id: str, mentions=None) -> str:
    a = audit(ledger, run_id)
    lines = [f"# PHASE 6 — coverage for run `{run_id}`", "",
             f"rows {a['rows']} · tickers {a['tickers']} · by status {json.dumps(a['by_status'])} · by category {json.dumps(a['by_category'])}",
             f"audit gaps {len(a['missing'])} · chain problems {len(a['chain_problems'])}", ""]
    rows = [r for r in ledger.rows if r["run_id"] == str(run_id)]
    lines.append("| ticker | float yahoo | float TV | SI (as-of) | borrow avail | SEC id | filings | rev splits |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for t in sorted({r["ticker"] for r in rows}):
        def g(field, src):
            x = [r for r in rows if r["ticker"] == t and r["field"] == field and r["source"].startswith(src)]
            if not x:
                return "—"
            ok = [r for r in x if r["status"] == "OK"]
            if not ok:
                return f"{x[0]['status']}:{x[0]['failure_reason'][:24]}"
            r = ok[0]
            return f"{r['value']}" + (f" ({str(r['source_asof'])[:10]})" if r["asof_basis"] == "PROVIDER" else "")
        nf = len([r for r in rows if r["ticker"] == t and r["field"] == "sec_filing" and r["status"] == "OK"])
        ns = len([r for r in rows if r["ticker"] == t and r["field"] == "reverse_split" and r["status"] == "OK"])
        lines.append(f"| {t} | {g('public_float','yahoo_info')} | {g('public_float','tv_scan')} | {g('short_interest','yahoo_info')} | {g('borrow_available','chartexchange')} | {g('identity','sec')[:40]} | {nf} | {ns} |")
    if a["missing"]:
        lines += ["", "## audit gaps (attempted combos without a status row)"] + [f"- {m}" for m in a["missing"]]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- CLI
def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    mode = argv[0] if argv else "mentions"
    if mode == "mentions":
        m = build_mentions()
        write_mentions(m)
        print(f"mentions {len(m)} · tickers {len(mention_tickers(m))} → {MENTIONS_PATH}")
        return 0
    if mode == "verify":
        L = Ledger(LEDGER_PATH)
        bad = L.verify()
        print(f"ledger rows {len(L.rows)} · problems {len(bad)}")
        for b in bad[:20]:
            print("  ", b)
        return 1 if bad else 0
    if mode == "run":
        m = build_mentions()
        write_mentions(m)
        tickers = mention_tickers(m)
        sel = os.environ.get("P6_TICKERS")
        if sel:
            tickers = [t.strip().upper() for t in sel.split(",") if t.strip()]
        run_id = os.environ.get("GITHUB_RUN_ID") or utc_now_iso().replace(":", "")
        L = Ledger(LEDGER_PATH)
        sec = frozen_sec()
        ids = {t: f"CIK{int(v['cik']):010d}" for t, v in sec.items() if isinstance(v, dict) and v.get("cik")}
        C = Collector(L, default_fetchers(), run_id, splits_known=frozen_splits(), security_ids=ids, pace_s=PACE_S)
        res = C.run(tickers)
        a = audit(L, run_id)
        os.makedirs(OUT, exist_ok=True)
        rep = coverage_report(L, run_id, m)
        open(os.path.join(OUT, "PHASE6_COVERAGE_LAST.md"), "w", encoding="utf-8").write(rep)
        json.dump(dict(run_id=run_id, result=res, audit={k: v for k, v in a.items() if k != "missing"}, missing=a["missing"]),
                  open(os.path.join(OUT, "PHASE6_RUN_LAST.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
        print(rep)
        print(f"P6RUN run_id={run_id} done={len(res['done'])} skipped={len(res['skipped'])} rows={a['rows']} status={json.dumps(a['by_status'])} gaps={len(a['missing'])} chain={len(a['chain_problems'])}")
        return 1 if a["chain_problems"] else 0
    print("usage: collector.py mentions|run|verify")
    return 2


if __name__ == "__main__":
    sys.exit(main())
