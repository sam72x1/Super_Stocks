"""T-FSWEEP mutation round: each mutation must make `fsweep.py --guards` fail cleanly (no crash). Restores the file in finally.
Bytecode is never written and the module's __pycache__ is cleared before each run (stale-bytecode lesson, same-length mutations)."""
import glob
import os
import subprocess
import sys

WT = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
P = os.path.join(WT, "fm_forensics/fsweep/fsweep.py")
M = [
    ("m1 the boundary instant excluded", "        if n and r.get(\"status\") in NEW_STATUSES and str(r.get(\"collected_utc\") or \"\") >= boundary:",
     "        if n and r.get(\"status\") in NEW_STATUSES and str(r.get(\"collected_utc\") or \"\") > boundary:"),
    ("m2 duplicates are new images", "NEW_STATUSES = (\"saved\", \"saved_from_pending\")", "NEW_STATUSES = (\"saved\", \"saved_from_pending\", \"dup\")"),
    ("m3 zero is a number", "math.isfinite(v) and v > 0)", "math.isfinite(v) and v >= 0)"),
    ("m4 sweep fields allowed on NONE", "        if any(p.get(f) is not None for f in SWEEP_FIELDS):", "        if False:"),
    ("m5 no row hash check", "        if r.get(\"row_hash\") != row_hash(r):", "        if False:"),
    ("m6 no chain check", "        if r.get(\"prev\") != prev:", "        if False:"),
    ("m7 an image triaged twice", "            if n in seen:", "            if False:"),
    ("m8 the file sha ignored", "            if file_sha is not None and file_sha(n) != m.get(\"sha256\"):", "            if False:"),
    ("m9 triaged before collected allowed", "            if str(r.get(\"triaged_utc\") or \"\") < str(m.get(\"collected_utc\") or \"~\"):", "            if False:"),
    ("m10 corrections after the analysis", "            if result_len is not None and r.get(\"seq\", 0) > result_len:", "            if False:"),
    ("m11 corrections ignored", "        elif r.get(\"row\") == \"CORRECTION\" and r.get(\"image\") in out:", "        elif False:"),
    ("m12 any author counts", "    if e.get(\"author\") != \"FAISAL\":", "    if False:"),
    ("m13 seven days is stale", "    if (col - _parse_post(e[\"post_date\"]).date()).days > FRESH_DAYS:",
     "    if (col - _parse_post(e[\"post_date\"]).date()).days >= FRESH_DAYS:"),
    ("m14 first by triage order", "    for e in sorted(ok, key=lambda e: (_parse_post(e[\"post_date\"]), e[\"seq\"])):",
     "    for e in sorted(ok, key=lambda e: (e[\"seq\"],)):"),
    ("m15 16:00 is before the close", "    if \"T\" in post_date and (p.hour, p.minute) >= CLOSE_ET:", "    if \"T\" in post_date and (p.hour, p.minute) > CLOSE_ET:"),
    ("m16 a date-only post reads its day", "    return p.date() - dt.timedelta(days=1)\n", "    return p.date()\n"),
    ("m17 no floor at the deadline", "        return \"RUN\" if n_units >= FLOOR_N else \"NO_MEASURE\"", "        return \"RUN\""),
    ("m18 13 % is a collapse", "    return (\"COLLAPSE\" if float(d[\"depth\"]) > COLLAPSE_PCT else", "    return (\"COLLAPSE\" if float(d[\"depth\"]) >= COLLAPSE_PCT else"),
    ("m19 base resets (production sweep)", "    d = depth_fn(pc_fn, df, k, lead=LEAD, sweep=FREE_SWEEP)", "    d = depth_fn(pc_fn, df, k, lead=LEAD, sweep=None)"),
    ("m20 no sweep is unknown", "        return (\"NO_SWEEP\", d) if d.get(\"why\") == \"no_sweep_in_window\" else",
     "        return (\"NO_SWEEP\", d) if d.get(\"why\") == \"no_sweep_in_windoW\" else"),
    ("m21 jumps ignored", "    if jumps_fn(df, k):\n        return \"UNKNOWN:jump\", None", "    if False:\n        return \"UNKNOWN:jump\", None"),
    ("m22 60 bars are enough", "    if df is None or k < SPAN:", "    if df is None or k < MIN_BARS:"),
    ("m23 verdict on reading B alone", "    if wa and wb and wa[0] > 0.5 and wb[0] > 0.5:", "    if wa and wb and wb[0] > 0.5:"),
    ("m24 no floor in the verdict", "    if a[\"n\"] < FLOOR_N:\n        return \"NO-MEASURE\"", "    if False:\n        return \"NO-MEASURE\""),
    ("m25 reading A drops no-sweep", "    det_a = sum(1 for c in classes if c in (\"COLLAPSE\", \"NO_COLLAPSE\", \"NO_SWEEP\"))",
     "    det_a = sum(1 for c in classes if c in (\"COLLAPSE\", \"NO_COLLAPSE\"))"),
    ("m26 stated % from the prices first", "    if e.get(\"sweep_pct\") is not None:\n        return float(e[\"sweep_pct\"])",
     "    if False:\n        return float(e[\"sweep_pct\"])"),
    ("m27 band exclusive", "\"in_band\": sum(1 for x in v if SW_LO <= x <= SW_HI)}", "\"in_band\": sum(1 for x in v if SW_LO < x < SW_HI)}"),
    ("m28 a snapshot fetched on t' counts", "        if fdate > cut.isoformat() and", "        if fdate >= cut.isoformat() and"),
    ("m29 the latest snapshot", "    for fdate, name, blob in sorted(snaps, key=lambda s: (s[0], s[1])):",
     "    for fdate, name, blob in sorted(snaps, key=lambda s: (s[0], s[1]), reverse=True):"),
    ("m30 main never read", "    blob = (read or (lambda: _main_blob(PREREG)))()\n    got = hashlib.sha256(blob).hexdigest() if blob is not None else None",
     "    blob = None\n    got = PREREG_SHA256"),
    ("m31 triage without the merge gate", "def cmd_triage(a):\n    check_merged()", "def cmd_triage(a):\n    pass"),
    ("m32 analysis without the pins", "        check_pins(S, FD)\n", ""),
    ("m33 status reads the measure", "    eff = effective(rows)\n    dec = {}", "    eff = effective(rows)\n    dec = {}\n    _ = _mods"),
    ("m34 no pre-append verification", "    errs = verify_rows(rows + [row], imgs, _file_sha)\n    if errs:\n        print(\"⛔ the new row would break the ledger:\"",
     "    errs = []\n    if errs:\n        print(\"⛔ the new row would break the ledger:\""),
    ("m35 correction after the analysis accepted", "    if res is not None:\n        print(\"⛔ no correction after the analysis",
     "    if False:\n        print(\"⛔ no correction after the analysis"),
    ("m37 a snapshot on the last t' is ready", "    return any(s[0] > last for s in snaps)", "    return any(s[0] >= last for s in snaps)"),
    ("m38 the verdict without bars", "        if not bars_ready(snaps, u):", "        if False:"),
    ("m36 triage twice accepted", "    if any(r.get(\"row\") == \"TRIAGE\" and r.get(\"image\") == a.image for r in rows):",
     "    if False:"),
]
orig = open(P, encoding="utf-8").read()
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")


def clear():
    for f in glob.glob(os.path.join(WT, "fm_forensics/fsweep/__pycache__/fsweep*")):
        os.remove(f)


res = []
try:
    for name, a, b in M:
        if orig.count(a) != 1:
            print("⛔ anchor count", orig.count(a), name)
            res.append(False)
            continue
        open(P, "w", encoding="utf-8").write(orig.replace(a, b, 1))
        clear()
        r = subprocess.run([sys.executable, "-B", P, "--guards"], cwd=WT, capture_output=True, text=True, timeout=300, env=env)
        fails = [ln[2:].split(" ")[0] for ln in r.stdout.splitlines() if ln.startswith("❌")]
        tb = "Traceback" in r.stdout + r.stderr
        ok = r.returncode != 0 and bool(fails) and not tb
        res.append(ok)
        print(("FELL " if ok else "SURVIVED/CRASH ") + name, "rc", r.returncode, "tb", tb, fails[:3], flush=True)
finally:
    open(P, "w", encoding="utf-8").write(orig)
    clear()
r = subprocess.run([sys.executable, "-B", P, "--guards"], cwd=WT, capture_output=True, text=True, env=env)
print(f"fell {sum(res)}/{len(M)} · restored rc", r.returncode)
sys.exit(0 if all(res) and r.returncode == 0 else 1)
