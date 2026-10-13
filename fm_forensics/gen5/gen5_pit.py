"""GEN5 — float and available-to-borrow as the bot knew them at decision time (research only).

For decision session t the source is the newest git snapshot committed before the open of the next
session (13:30 UTC; every date here is in daylight time) — what the bot had stored when it decided.
Unknown stays None (never zero). Sources, in order:
  float     : near_watch.json (float with float_date ≤ t) · weekly_watchlist.json stocks · hunter_watchlist.json ·
              company_cache.json
  available : ctb_log.jsonl rows dated ≤ t · weekly_watchlist.json stocks (shares_available) · hunter_watchlist.json
Reads git history of `origin/main` only (`git show <commit>:<file>`). No network.
"""
import bisect
import datetime as dt
import json
import subprocess

REF = "origin/main"
FILES = ("near_watch.json", "weekly_watchlist.json", "hunter_watchlist.json", "company_cache.json", "ctb_log.jsonl")


def _git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=False).stdout


def commits(path):
    """[(commit_time_utc, sha)] oldest first."""
    out = []
    for line in _git("log", REF, "--format=%H %cI", "--", path).splitlines():
        h, t = line.split()
        out.append((dt.datetime.fromisoformat(t).astimezone(dt.timezone.utc), h))
    return sorted(out)


def _num(x):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return x if x == x and x > 0 else None


def _avail(x):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return x if x == x and x >= 0 else None


def _rows(path, blob):
    try:
        d = json.loads(blob)
    except Exception:                                            # noqa: BLE001
        return {}
    out = {}
    if path == "near_watch.json" and isinstance(d, dict):
        for s, v in d.items():
            if isinstance(v, dict):
                out[s] = {"float": _num(v.get("float")), "float_date": v.get("float_date")}
    elif path in ("weekly_watchlist.json", "hunter_watchlist.json") and isinstance(d, dict):
        for v in (d.get("stocks") or []):
            if isinstance(v, dict) and v.get("symbol"):
                out[v["symbol"]] = {"float": _num(v.get("float")),
                                    "avail": _avail(v.get("shares_available", v.get("avail")))}
    elif path == "company_cache.json" and isinstance(d, dict):
        for s, v in d.items():
            if isinstance(v, dict):
                out[s] = {"float": _num(v.get("float"))}
    return out


class PIT:
    def __init__(self, dates, next_session):
        """dates: decision sessions (ISO) · next_session: {t: next trading session ISO}."""
        self.cut = {t: dt.datetime.fromisoformat(next_session[t]).replace(hour=13, minute=30, tzinfo=dt.timezone.utc)
                    for t in dates}
        self.snap = {}                                    # (file, t) -> rows
        for path in FILES[:4]:
            cs = commits(path)
            times = [c[0] for c in cs]
            cache = {}
            for t, cut in self.cut.items():
                k = bisect.bisect_right(times, cut) - 1   # newest commit at or before the cut
                if k < 0:
                    self.snap[(path, t)] = {}
                    continue
                h = cs[k][1]
                if h not in cache:
                    cache[h] = _rows(path, _git("show", f"{h}:{path}"))
                self.snap[(path, t)] = cache[h]
        self.ctb = {}                                     # symbol -> [(date, avail)]
        blob = _git("show", f"{REF}:ctb_log.jsonl")
        for line in blob.splitlines():
            try:
                r = json.loads(line)
            except Exception:                                    # noqa: BLE001
                continue
            a = _avail(r.get("shares_available"))
            if r.get("symbol") and r.get("date") and a is not None:
                self.ctb.setdefault(r["symbol"], []).append((r["date"], a))
        for v in self.ctb.values():
            v.sort()

    def float_at(self, sym, t):
        nw = self.snap.get(("near_watch.json", t), {}).get(sym) or {}
        if nw.get("float") and (nw.get("float_date") or "9999") <= t:
            return nw["float"], "near_watch"
        for path in ("weekly_watchlist.json", "hunter_watchlist.json", "company_cache.json"):
            v = (self.snap.get((path, t), {}).get(sym) or {}).get("float")
            if v:
                return v, path.split(".")[0]
        return None, None

    def avail_at(self, sym, t):
        rows = [a for d, a in self.ctb.get(sym, []) if d <= t]
        if rows:
            return rows[-1], "ctb_log"
        for path in ("weekly_watchlist.json", "hunter_watchlist.json"):
            v = (self.snap.get((path, t), {}).get(sym) or {}).get("avail")
            if v is not None:
                return v, path.split(".")[0]
        return None, None
