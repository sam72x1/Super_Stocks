"""Faisal condition atlas — renders the result reports from the JSON files (every number comes from data/):
CONDITION_STRENGTH_RESULTS.md · CANDLE_PATTERN_STUDY.md · READY_CLASSIFICATION_SPEC.md ·
HISTORICAL_CLASSIFICATION_RESULTS.md · CHART_CASEBOOK.md. (FINAL_FINDINGS.md is written by hand from these.)
Run from the repo root:  python3 faisal_engine/readynow/condition_atlas/ca_report.py   (--check compares)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ca_atlas as A                                                      # noqa: E402

DATA = os.path.join(HERE, "data")
W = ("validation", "holdout")
CANDLE_DEFS = {
    "K01_HAMMER": "the bot's «مطرقة»: body ≤ 0.4 range, lower wick ≥ 2 body, upper wick ≤ max(0.5 body, 0.1 range)",
    "K01_HAMMER_3": "a hammer on any of the last 3 sessions",
    "K02_RED_HAMMER": "hammer with close < open («شمعة حمرا = صعود قصير الامد», IMG_0569)",
    "K03_INV_HAMMER": "the bot's «مطرقة مقلوبة»: body ≤ 0.4 range, upper wick ≥ 2 body, small lower wick",
    "K03_INV_HAMMER_3": "an inverted hammer on any of the last 3 sessions",
    "K04_DOJI": "body ≤ 0.10 × range (DOJI_BODY_MAX)",
    "K04b_DOJI_SUPPORT": "the bot's «دوجي عند الدعم»: doji with the low within 3% of the 30-session low",
    "K05_ENGULF": "the bot's «ابتلاع صاعد»: red then green, open ≤ previous close, close ≥ previous open, larger body",
    "K05_ENGULF_3": "a bullish engulfing on any of the last 3 sessions",
    "K06_MSTAR": "the bot's «نجمة الصباح»: big red (body ≥ 0.4 range), small body (≤ 0.5 of the first) not above "
                 "its close, green closing above the first body's midpoint",
    "K06b_DOJI_THEN_ENGULF": "doji (T−1 or T−2) or morning star (T−1), then a bullish engulfing (TG_58382, third party)",
    "K07_HARAMI": "previous red with body ≥ 0.4 range; today green inside the previous body, body ≤ 0.6 previous",
    "K08_WICK_BOUNCE": "long lower wick (≥ 0.5 range and ≥ 2 body) at the 25-session low in the last 3 sessions, close "
                       "≥ 1.05 × that low (TG_57874)",
    "K08b_LONGWICK": "long lower wick today (≥ 0.5 range and ≥ 2 body)",
    "K09_HANGMAN": "hammer shape with the close within 3% of the 20-session high (the bot's _hanging_man)",
    "K10_SHOOT": "inverted-hammer shape with the close within 3% of the 20-session high",
    "K11_INSIDE": "high ≤ previous high and low ≥ previous low",
    "K11_SPIN": "body ≤ 0.3 range, both wicks ≥ body, not a doji",
    "K11_PIERCING": "the bot's «اختراق صاعد»: red then green opening below the red close, closing above its midpoint",
    "K11_MARUBOZU": "the bot's «ماروبوزو أخضر»: green body ≥ 0.9 range, range ≥ 2% of the close",
    "K11_SOLDIERS": "the bot's «ثلاثة جنود بيض»",
    "B20_CANDLE_AT_SUPPORT": "any of hammer, inverted hammer, doji at support, engulfing, piercing, morning star, long "
                             "lower wick in the last 3 sessions ∧ within 15% of the 25-session low",
}


def j(name):
    return json.load(open(os.path.join(DATA, name), encoding="utf-8"))


def ci(x):
    return f"[{x[0]}, {x[1]}]" if x else "—"


def pp(x):
    return f'{x["rule_minus_pp"]:+.2f} {ci(x["rule_minus_pp_ci"])}' if x and x.get("rule_minus_pp") is not None else "—"


def _name(flag):
    for a in A.ATLAS:
        if a["flag"] and flag.startswith(a["flag"].split("_")[0]):
            return a["en"]
    return ""


def strength_rows(s, names):
    L = ["| flag | flags / session | prevalence POS · NEG | lift [95%] | Bonferroni | matched [95%] | events captured "
         "(exclusion cost) | − DROP_k pp | − VOLAT_k pp | halves lift | at support · oversold |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for n in names:
        v = s[n]
        cx = v["context"]
        c1 = cx["at_support"]["lift"] if cx.get("at_support") else "—"
        c2 = cx["oversold"]["lift"] if cx.get("oversold") else "—"
        L.append(f'| {n} | {v["flags_per_session"]} | {v["prev_pos"]} · {v["prev_neg"]} | {v["lift"]} {ci(v["lift_ci"])} '
                 f'| {ci(v["lift_ci_bonferroni"])} | {v["matched"]["ratio"]} {ci(v["matched"]["ci"])} | '
                 f'{v["events_captured"]}/{v["events_eligible"]} ({v["exclusion_cost_events"]}) | {pp(v["DROP_k"])} | '
                 f'{pp(v["VOLAT_k"])} | {" · ".join(str(h["lift"]) for h in v["halves"])} | {c1} · {c2} |')
    return L


def y26_rows(f, names):
    L = ["| flag | validation lift [95%] | prevalence POS · NEG | holdout lift [95%] | prevalence POS · NEG |",
         "|---|---|---|---|---|"]
    for n in names:
        a, b = f["validation"]["conditions"][n], f["holdout"]["conditions"][n]
        L.append(f'| {n} | {a["lift"]} {ci(a["lift_ci"])} | {a["prev_pos"]} · {a["prev_neg"]} | {b["lift"]} '
                 f'{ci(b["lift_ci"])} | {b["prev_pos"]} · {b["prev_neg"]} |')
    return L


STRUCT = ("B05_HOLD3", "B05b_HOLD5", "B06_TEST15", "B07_RETEST", "B08_SWEEP", "B23_CYCLE3", "B04_PEAK_AGE30",
          "B09_TIGHT_NEAR_LOW", "B12_GAP10", "B11_MACD_X9", "B13_EMA_X5", "B14_KVO_UP", "B16_WR_TURN", "B17_UPDN_VOL",
          "B18_TOUCHES")


def _lo1(x):
    return bool(x["lift_ci"] and x["lift_ci"][0] > 1)


def one26(f, names):
    return [n for n in names if sum(_lo1(f[w]["conditions"][n]) for w in W) == 1]


def both26(f, names):
    return [n for n in names if all(_lo1(f[w]["conditions"][n]) for w in W)]


def stable(s, f):
    """Flags whose lift lower bound is above 1 in development and in both 2026 windows."""
    out = []
    for n, v in s.items():
        ok = (v["lift_ci"] and v["lift_ci"][0] > 1 and all(
            f[w]["conditions"][n]["lift_ci"] and f[w]["conditions"][n]["lift_ci"][0] > 1 for w in W))
        if ok:
            out.append(n)
    return out


WALL = ("development", "validation", "holdout")


def _surv(rc, n):
    """Windows where the same-session matched ratio keeps a lower bound above 1 (RECONCILIATION_ADDENDUM.md R2)."""
    return [w for w in WALL if rc["R2"][w][n]["matched_ci95"] and rc["R2"][w][n]["matched_ci95"][0] > 1]


def _mtx(rc, n):
    return ", ".join(f'{rc["R2"][w][n]["matched_ratio"]} {ci(rc["R2"][w][n]["matched_ci95"])}' for w in WALL)


def _dpp(x):
    return f"{x[0]:+.2f} {ci(x[1])}"


def strength_md():
    sd, f, sec, rc = j("strength_dev.json"), j("final.json"), j("sec_dev.json"), j("reconcile.json")
    s = sd["strength"]
    non_k = [n for n in s if not n.startswith("K") and n != "B20_CANDLE_AT_SUPPORT"]
    st = stable(s, f)
    L = ["# Condition strength — every atlas condition against the onset 7–10 sessions later", "",
         f'Population: the READY NOW pivot-days (identity M1–M3 from bars ≤ T; seeds and HUBC excluded). Target POS710 = a '
         f'clean corrected onset (start of the final +70% leg) 7–10 sessions after T. Development '
         f'{sd["window"][0]} → {sd["window"][1]}: {sd["rows"]:,} rows, {sd["evaluable"]:,} evaluable, base '
         f'{sd["base_rate"]:.2%}, {sd["eligible_events"]} eligible events. Generated by `ca_report.py` from '
         f'`data/strength_dev.json`, `data/final.json`, `data/sec_dev.json`.', "",
         "**Five separate quantities** (never merged): *prevalence* (share of POS710 rows and of NEG rows that satisfy "
         "the flag) · *association* (lift = precision ÷ window base, ticker-cluster CI; Bonferroni over the "
         f'{sd["flags_tested"]} flags) · *discrimination against look-alikes* (matched ratio: same session, price bucket, '
         "volume, volatility and dollar-volume percentiles within 0.10) · *equal-burden ranking value* (precision of the "
         "flag minus the 5-session-drop and the volatility rankings that flag as many rows per session, pp) · "
         "*timing* (the lead profile below). Exclusion cost = eligible events the flag never marks in T−10…T−7, i.e. "
         "lost if the flag were required.", "",
         "## 1. Development (2025-05-01 → 12-31) — validity, technical, invalidation and timing flags", ""]
    L += strength_rows(s, non_k)
    L += ["", "## 2. The same flags in 2026 (descriptive; the windows were read by earlier studies)", ""]
    L += y26_rows(f, non_k)
    L += ["", "## 3. Lead profile — share of rows flagged k sessions before a clean onset", "",
          "«far» = rows with no onset within the next 10 sessions (the labels record the next onset only within 10 "
          "sessions, so k = 11…20 is not available).", "",
          "| flag | far | T−10 | T−9 | T−8 | T−7 | T−6 | T−5 | T−4 | T−3 | T−2 | T−1 |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for n in ("B01_RSI30", "B01b_RSI33", "B02_RSI27_10", "A03_ANNUAL_LOW", "A05_SPLIT120", "T01_DIP_LOW", "B10_VOL5_3",
              "B03_BELOW3", "B19b_NEAR15", "B08_SWEEP", "I02_RSI40", "I03_BOOM5", "I04_GROUP_PROXY"):
        lp = s[n]["lead_profile"]
        L.append(f'| {n} | {lp["far"][1]} | ' + " | ".join(str(lp[str(k)][1]) for k in range(10, 0, -1)) + " |")
    L += ["", "## 4. Share count and offering — SEC subset (descriptive only)", "",
          f'{sec["note"]}: {sec["rows_covered"]:,} development rows, {sec["symbols_covered"]} symbols, '
          f'{sec["pos_covered"]} POS710 rows; share count known on {sec["rows_with_share_count"]:,} rows.', "",
          "| flag | flagged | prevalence POS · NEG | lift [95%] |", "|---|---|---|---|"]
    for n, v in sec["flags"].items():
        L.append(f'| {n} | {v["flagged"]:,} | {v["prev_pos"]} · {v["prev_neg"]} | {v["lift"]} {ci(v["lift_ci"])} |')
    L += ["", "## 5. Reading", "",
          "- **Flags with a lift lower bound above 1 in development and in both 2026 windows:** "
          + (", ".join(st) if st else "none") + ".",
          f'- **RSI oversold is the most consistent raw association among Faisal\'s readiness conditions, not a signal '
          f'beyond volatility.** RSI < 30: development {s["B01_RSI30"]["lift"]} {ci(s["B01_RSI30"]["lift_ci"])}, validation '
          f'{f["validation"]["conditions"]["B01_RSI30"]["lift"]}, holdout {f["holdout"]["conditions"]["B01_RSI30"]["lift"]} '
          f'(the flags with a lift lower bound above 1 in all three periods: '
          f'{", ".join(rc["R7"]["R7a_lift_lower_above_1_all_three"])}). '
          f'Matched on session, price, volume and volatility its ratio is {_mtx(rc, "B01_RSI30")} (development, '
          f'validation, holdout: lower bound above 1 in {", ".join(_surv(rc, "B01_RSI30")) or "none"}). At equal burden '
          f'it does not beat the drop or volatility rankings in any window ({pp(s["B01_RSI30"]["DROP_k"])} · '
          f'{pp(s["B01_RSI30"]["VOLAT_k"])} pp in development; RECONCILIATION_ADDENDUM.md §2, §4). Inside the '
          f'oversold context its lift is {s["B01_RSI30"]["context"]["oversold"]["lift"]}, as expected. Its prevalence '
          f'rises toward the onset ({s["B01_RSI30"]["lead_profile"]["10"][1]} at T−10, '
          f'{s["B01_RSI30"]["lead_profile"]["1"][1]} at T−1, {s["B01_RSI30"]["lead_profile"]["far"][1]} far): oversold '
          "marks proximity, but most exploders are not oversold at T−10…T−7.",
          f'- **«مستحيل يصعد اذا RSI بمناطق 40» is not supported as a rule.** RSI ≥ 40 has prevalence '
          f'{s["I02_RSI40"]["prev_pos"]} among POS710 rows in development (lift {s["I02_RSI40"]["lift"]}): about half '
          "of the legs started with RSI at 40 or above 7–10 sessions earlier. Lower odds, not impossibility.",
          "- **Faisal's invalidation states: an association, not a forecast and not an entry signal.** The "
          "group-candle proxy (I04, a daily stand-in for his 4-hour «group» candle) has lift "
          + ", ".join(f'{rc["R1"][w]["lift"]} {ci(rc["R1"][w]["lift_ci95"])}' for w in WALL)
          + f' (development, validation, holdout). Matched on volatility its ratio is {_mtx(rc, "I04_GROUP_PROXY")} '
          f'(lower bound above 1 in {", ".join(_surv(rc, "I04_GROUP_PROXY")) or "none"} only); it never beats the '
          "volatility or drop ranking at equal burden; its prevalence is flat from T−10 to T−1 and about three times "
          f'higher after a recent episode. Chasing (I01) and the within-a-week explosion (I03) have development lifts '
          f'{s["I01_CHASE"]["lift"]} and {s["I03_BOOM5"]["lift"]} (matched {s["I01_CHASE"]["matched"]["ratio"]} and '
          f'{s["I03_BOOM5"]["matched"]["ratio"]}). For Faisal these are exclusion states — groups make the candles '
          "unreadable and the operator may press the stock (IMG_0488, IMG_0316) — about entry risk («مايدخل الان»), "
          "not about whether another leg comes. As exclusion rules they would remove some exploders, but they do not "
          "mark the stocks most likely to start one (RECONCILIATION_ADDENDUM.md §1–§2).",
          f'- **The cycle and structure conditions do not separate on daily bars:** {", ".join(STRUCT)} — development '
          f'lifts {min(s[n]["lift"] for n in STRUCT)}–{max(s[n]["lift"] for n in STRUCT)}; with a 2026 lower bound '
          f'above 1 in one window only: {", ".join(one26(f, STRUCT)) or "none"}; in both: '
          f'{", ".join(both26(f, STRUCT)) or "none"}. The EMA 9/26 cross is below 1 in development '
          f'({s["B13_EMA_X5"]["lift"]} {ci(s["B13_EMA_X5"]["lift_ci"])}).',
          f'- **Lower bound above 1 in both 2026 windows but not in development:** '
          f'{", ".join(n for n in both26(f, list(s)) if not (s[n]["lift_ci"] and s[n]["lift_ci"][0] > 1)) or "none"} '
          "— a 2026 regime (volume bursts, quiet oscillation, recent splits, hot stocks) that development did not "
          "show; descriptive, since these windows were read before.",
          f'- **Split recency (A05)** was {s["A05_SPLIT120"]["lift"]} {ci(s["A05_SPLIT120"]["lift_ci"])} in '
          f'development and above 1 with confidence in both 2026 windows '
          f'({f["validation"]["conditions"]["A05_SPLIT120"]["lift"]}, {f["holdout"]["conditions"]["A05_SPLIT120"]["lift"]}). '
          "Unstable across periods; the 2026 rise matches the app's split-cycle universe, but it is not a confirmed "
          "separator.",
          "- **Share count < 2 M shows no association in the SEC subset;** a recent final prospectus points the way "
          "Faisal says (lower odds) without significance. The subset is biased and small, so neither is a finding "
          "about the population.", ""]
    return "\n".join(L) + "\n"


def candle_md():
    sd, f = j("strength_dev.json"), j("final.json")
    s = sd["strength"]
    ks = [n for n in s if n.startswith("K")] + ["B20_CANDLE_AT_SUPPORT"]
    L = ["# Candle pattern study", "",
         "**What is new here and what is not.** T-CANDLE (2026-08-27, archive line 7108) measured six reversal "
         "candles as trade selectors in the pressure channel (R expectancy) and failed 0/6; that axis stays closed and "
         "its verdict is unchanged. This study asks a different question on a different population: does a "
         "candle on a pivot-day mark a +70% leg starting 7–10 sessions later? It is descriptive and does not "
         "reopen T-CANDLE. The 4-hour frame, which Faisal uses for most candle readings (IMG_0569, TG_1865), is not "
         "archived, so every candle here is daily.", "",
         "## 1. Definitions (no incomplete or future candle: the candle at T is the completed daily bar of T)", "",
         "| flag | definition | source |", "|---|---|---|"]
    for n in ks:
        src = next((", ".join(a["src"][:2]) + " · " + a["author"] for a in A.ATLAS
                    if a["flag"] and n.startswith(a["flag"][:3])), "standard")
        L.append(f"| {n} | {CANDLE_DEFS.get(n, '')} | {src} |")
    L += ["", f'## 2. Development (2025-05-01 → 12-31; base {sd["base_rate"]:.2%}, {sd["eligible_events"]} events)', ""]
    L += strength_rows(s, ks)
    L += ["", "## 3. 2026 (descriptive)", ""]
    L += y26_rows(f, ks)
    hm = s["K01_HAMMER"]
    L += ["", "## 4. Lead profile of the hammer", "",
          "| flag | far | T−10 | T−9 | T−8 | T−7 | T−6 | T−5 | T−4 | T−3 | T−2 | T−1 |", "|---|---|---|---|---|---|---|---|---|---|---|---|",
          f'| K01_HAMMER | {hm["lead_profile"]["far"][1]} | ' + " | ".join(
              str(hm["lead_profile"][str(k)][1]) for k in range(10, 0, -1)) + " |", "",
          "## 5. Reading", "",
          f'- **Alone:** no candle separates. Hammer {hm["lift"]} {ci(hm["lift_ci"])}, inverted hammer '
          f'{s["K03_INV_HAMMER"]["lift"]}, bullish engulfing {s["K05_ENGULF"]["lift"]}, morning star '
          f'{s["K06_MSTAR"]["lift"]}, harami {s["K07_HARAMI"]["lift"]} {ci(s["K07_HARAMI"]["lift_ci"])} (below 1). '
          "Every candle ranks below the drop and volatility rankings at equal burden.",
          f'- **In context:** the hammer at the support has lift {hm["context"]["at_support"]["lift"]} and '
          f'{hm["context"]["oversold"]["lift"]} when the stock is oversold. A positive candle at the support (the app\'s '
          f'condition) is {s["B20_CANDLE_AT_SUPPORT"]["lift"]} {ci(s["B20_CANDLE_AT_SUPPORT"]["lift_ci"])}.',
          f'- **Composite:** the third-party rule «doji or morning star must be followed by an engulfing» is '
          f'{s["K06b_DOJI_THEN_ENGULF"]["lift"]} {ci(s["K06b_DOJI_THEN_ENGULF"]["lift_ci"])}.',
          f'- **2026:** one candle has a lower bound above 1 in one window (long lower wick then +5%, validation '
          f'{f["validation"]["conditions"]["K08_WICK_BOUNCE"]["lift"]} '
          f'{ci(f["validation"]["conditions"]["K08_WICK_BOUNCE"]["lift_ci"])}). It is not in the other window '
          f'({f["holdout"]["conditions"]["K08_WICK_BOUNCE"]["lift"]}) or in development ({s["K08_WICK_BOUNCE"]["lift"]}). '
          "With 22 candle flags, one such hit is expected by chance.",
          "- The hanging man and the shooting star almost never occur on pivot-days (they need a close near the "
          "20-session high), so they cannot be judged here.",
          "- **Conclusion:** on daily bars, Faisal's candles are confirmations a trader reads at a prepared moment, as "
          "T-CANDLE concluded. They carry no measurable information about a +70% leg 7–10 sessions ahead.", ""]
    return "\n".join(L) + "\n"


def spec_md():
    fz, md = j("model_frozen.json"), j("model_dev.json")
    L = ["# READY classification — specification (research candidate; NOT validated)", "",
         "Status: frozen on development and checked once on 2026 (`CA_PROTOCOL.md`). **Sealed verdict: "
         + j("verdict.json")["verdict"] + " · " + j("verdict.json")["classification"] + "** "
         "(HISTORICAL_CLASSIFICATION_RESULTS.md). Not a production rule; nothing here changes the bot.", "",
         "## Three separate questions, three axes", "",
         "- **A · Is it a valid pivot?** The population already passes the identity (M1–M3: prior spike, drop band, "
         "price). Axis A grades validity with 9 flags (spike ≥ 100%, drop ≥ 50%, near the annual low, no rise in "
         "20 sessions, reverse split ≤ 120 days, not risen > 20% after the split, ÷2 band, split ≥ 3 times, no group "
         "candle). Float, borrow, offering and news are UNKNOWN for history (always reported as such).",
         "- **B · How strong is its technical readiness?** Technical flags and candles.",
         "- **C · How close is it to a +70% leg?** Every flag, including invalidation and timing.", "",
         "Each axis is a ridge logistic regression on binary flags (intercept unpenalised). The penalty λ is chosen by "
         "the development test-half AUC (train 2025-05 → 09, test 10 → 12), then the model is refitted on the whole "
         f'development window. Chosen λ: A {md["chosen"]["A"]}, B {md["chosen"]["B"]}, C {md["chosen"]["C"]}. Nothing '
         "is mandatory except not being invalidated; a missing auxiliary condition contributes 0, so a pivot with "
         "high readiness is not dropped for one absent condition.", "",
         "## Classes (per session; k = the rows the tool's technical part flags that session)", "",
         "| class | rule |", "|---|---|",
         "| INVALIDATED | chasing (more than 40% above the 25-session low, or more than 30% in 5 sessions), exploded "
         "within 5 sessions, or a daily group-candle proxy in the last 10 sessions |",
         "| READY_1 | top k of the valid pivot-days by C |", "| READY_2 | the next k |", "| READY_3 | the next 2k |",
         "| WATCH | the rest with B at or above the session median |", "| NOT_READY | the rest |", "",
         "**The numerals are score ranks, not grades.** READY_1–3 are bands of the C score inside a session (top k, next "
         "k, next 2k). The sealed check found the classes NOT_GRADED, and no fine difference between them holds in 2026 "
         "(RECONCILIATION_ADDENDUM.md §4): read them as a review order, not as levels of readiness.", "",
         "Per-stock row (`data/ready_rows_2026.csv.gz` for READY_1–3 in 2026; the casebook for every case): class, "
         "the three axis probabilities, the flags that hold, top contributors (largest positive coefficient × flag), "
         "blockers (negative), and confidence = «partial»: daily bars only; float, borrow, offering, groups and "
         "operator UNKNOWN.", "",
         "## Frozen coefficients (largest by absolute value)", ""]
    for ax in ("A", "B", "C"):
        v = fz[ax]
        pairs = sorted(zip(v["features"], v["w"][1:]), key=lambda p: -abs(p[1]))[:12]
        L += [f'**Axis {ax}** (λ {v["lam"]}, intercept {v["w"][0]}): '
              + " · ".join(f"{n} {w:+.4f}" for n, w in pairs), ""]
    L += ["## Comparison set (all at the same per-session burden k)", "",
          "TC_TECH · CAPIT_TC · DROP_k · VOLAT_k · VOL_k · COUNT_k (number of Faisal's 11 counted conditions) · APPW_k "
          "(the app's weighted screen TG_58420: support with failed breaks 12, entry near the support 8, averages 8, "
          "daily RSI 23–27 12, MACD improving 10, positive candle at the support 8, selling weakens 7, room above 5; "
          "daily proxies) · W_k (= READY_1) · W_k without invalidation · B_k · A_k.", ""]
    return "\n".join(L) + "\n"


def cmp_table(c, names):
    L = ["| ranking | flags / session | precision [95%] | lift [95%] | FPR | events (recall) | − TC_TECH pp | − CAPIT_TC "
         "pp | − DROP_k pp | − VOLAT_k pp |", "|---|---|---|---|---|---|---|---|---|---|"]
    for n in names:
        if n not in c:
            continue
        x = c[n]

        def d(ref):
            y = x.get("minus_" + ref)
            return f'{y["pp"]:+.2f} {ci(y["ci95"])}' if y and y.get("pp") is not None else "—"
        L.append(f'| {n} | {x["flags_per_session"]} | {x["precision"]:.2%} {ci(x["precision_ci95"])} | {x["lift"]} '
                 f'{ci(x["lift_ci"])} | {x["fpr"]} | {x["events_captured"]}/{x["events_eligible"]} ({x["recall"]}) | '
                 f'{d("TC_TECH")} | {d("CAPIT_TC")} | {d("DROP_k")} | {d("VOLAT_k")} |')
    return L


def class_table(c):
    L = ["| class | rows | per session | precision [95%] | events touched |", "|---|---|---|---|---|"]
    for k in ("READY_1", "READY_2", "READY_3", "WATCH", "NOT_READY", "INVALIDATED"):
        x = c[k]
        L.append(f'| {k} | {x["rows"]:,} | {x["per_session"]} | {x["precision"]:.2%} {ci(x["precision_ci95"])} | '
                 f'{x["events_touched"]} |')
    return L


def results_md():
    md, f, v, rc = j("model_dev.json"), j("final.json"), j("verdict.json"), j("reconcile.json")
    names = ("W_k", "W_k_noinval", "B_k", "A_k", "COUNT_k", "APPW_k", "TC_TECH", "CAPIT_TC", "DROP_k", "VOLAT_k",
             "VOL_k")
    L = ["# Historical classification results", "",
         "Sealed check (`CA_PROTOCOL.md`, SHA-256 pinned in `ca_final.py`; run once 2026-10-11 22:30–22:32 UTC). "
         "Exploratory: the 2026 windows were read by earlier studies. Generated by `ca_report.py` from "
         "`data/model_dev.json`, `data/final.json` and `data/verdict.json`.", "",
         f'## 1. Verdict: **{v["verdict"]}** · classes **{v["classification"]}**', "",
         "| rule | result |", "|---|---|",
         f'| V1 W_k beats the tool (pooled lower > 0 and each window > 0) | {v["V1_beats_tool"]} |',
         f'| V2 beats the drop and the volatility rankings | {v["V2_beats_drop_and_volatility"]} |',
         f'| V3 beats CAPIT_TC | {v["V3_beats_CAPIT_TC"]} |',
         f'| V4 weights beat counting | {v["V4_weights_beat_count"]} |',
         f'| V5 graded classes (monotone in both windows, READY_1 lift lower > 1) | {v["V5_graded_classes"]} |', "",
         "Pooled (validation + holdout, ticker-cluster CI):", "", "| ranking | − reference | pp [95%] |", "|---|---|---|"]
    for n in ("W_k", "COUNT_k", "APPW_k"):
        for ref, x in f["pooled"][n].items():
            L.append(f'| {n} | {ref} | {x["pp"]:+.2f} {ci(x["ci95"])} |')
    L += ["", f'## 2. Development test half ({md["test"][0]} → {md["test"][1]}; models fitted on the training half)', ""]
    L += cmp_table(md["test_half_compare"], names)
    L += [""] + class_table(md["test_half_classes"])
    for w in W:
        x = f[w]
        L += ["", f'## 3. {w.capitalize()} {x["window"][0]} → {x["window"][1]} — {x["rows"]:,} rows, base '
                  f'{x["base_rate"]:.2%}, {x["eligible_events"]} events · AUC: C {x["auc_C"]}, volatility '
                  f'{x["auc_volatility"]}, 5-session drop {x["auc_drop"]}', ""]
        L += cmp_table(x["compare"], names)
        L += [""] + class_table(x["classes"])
    L += ["", "## 4. Predictions written before the run", "", "| prediction | outcome |", "|---|---|"]
    pv = f["pooled"]
    q = [("Q1 V1 fails", not v["V1_beats_tool"]), ("Q2 V2 fails", not v["V2_beats_drop_and_volatility"]),
         ("Q3 V3 fails", not v["V3_beats_CAPIT_TC"]), ("Q4 V5 fails", not v["V5_graded_classes"]),
         ("Q5 COUNT_k and APPW_k do not beat TC_TECH",
          not (pv["COUNT_k"]["TC_TECH"]["ci95"][0] > 0) and not (pv["APPW_k"]["TC_TECH"]["ci95"][0] > 0)),
         ("Q6 RSI < 33 lift above 1 in both windows",
          all(f[w]["conditions"]["B01b_RSI33"]["lift"] > 1 for w in W)),
         ("Q7 no candle flag with lift lower > 1 in both windows",
          not any(all(f[w]["conditions"][n]["lift_ci"] and f[w]["conditions"][n]["lift_ci"][0] > 1 for w in W)
                  for n in f["validation"]["conditions"] if n.startswith("K"))),
         ("Q8 group-candle proxy lift ≥ 1 in both windows",
          all(f[w]["conditions"]["I04_GROUP_PROXY"]["lift"] >= 1 for w in W))]
    for name, ok in q:
        L.append(f"| {name} | {'came true' if ok else 'did not come true'} |")
    L += ["", "## 5. Reading", "",
          f'- The atlas classifier (W_k) does not beat the tool\'s technical part (pooled '
          f'{pv["W_k"]["TC_TECH"]["pp"]:+.2f} pp {ci(pv["W_k"]["TC_TECH"]["ci95"])}). It is below the 5-session-drop '
          f'ranking ({pv["W_k"]["DROP_k"]["pp"]:+.2f} {ci(pv["W_k"]["DROP_k"]["ci95"])}) and below CAPIT_TC '
          f'({pv["W_k"]["CAPIT_TC"]["pp"]:+.2f} {ci(pv["W_k"]["CAPIT_TC"]["ci95"])}). Its AUC is under volatility '
          "alone in both windows.",
          "- Weighting does not beat counting (V4), and neither beats the tool. The app's weighted screen (daily "
          "proxies) was above the tool in validation and below it in the holdout.",
          "- The classes are not graded. Precision READY_1 · READY_2 · READY_3 · WATCH · NOT_READY · INVALIDATED: "
          + " — ".join(f'{w} ' + " · ".join(f'{f[w]["classes"][k]["precision"]:.2%}' for k in
                                             ("READY_1", "READY_2", "READY_3", "WATCH", "NOT_READY", "INVALIDATED"))
                       for w in W)
          + ". With ticker-cluster intervals (RECONCILIATION_ADDENDUM.md §4) no fine difference holds in 2026: "
          f'READY_1 − READY_2 pooled {_dpp(rc["R6"]["pooled_2026"]["diff_pp"]["READY_1-READY_2"])}, READY_2 − READY_3 '
          f'{_dpp(rc["R6"]["pooled_2026"]["diff_pp"]["READY_2-READY_3"])} pp. The coarse READY(1–3) − WATCH is '
          f'{_dpp(rc["R6"]["pooled_2026"]["diff_pp"]["READY-WATCH"])} and INVALIDATED − READY_1 '
          f'{_dpp(rc["R6"]["pooled_2026"]["diff_pp"]["INVALIDATED-READY_1"])}: invalidated pivot-days start a leg about '
          "as often as READY ones, because the invalidation states mark volatile stocks. READY_1–3 are score-rank "
          "bands, not grades.",
          "- The bottleneck is the information in daily bars, not the weighting scheme: the ceiling model (all daily "
          "features with interactions, READY_DISCOVERY) also showed nothing beyond volatility.", ""]
    return "\n".join(L) + "\n"


def casebook_md():
    cb, rc = j("casebook.json"), j("reconcile.json")

    def ev_line(c):
        dd = c["dates"]
        return (f'| {c.get("sym", "")} | {dd["trough"]} | {dd["onset"]} | {dd["first_intraday_+70"]} | '
                f'{dd["q_+70_close_or_jump"]} | {dd["d1"]} | {dd["peak_close_gain_pct"]}% · '
                f'{dd["peak_intraday_gain_pct"]}% | {dd["kind"]} |')

    def tl_lines(c):
        out = []
        for t in c["timeline"]:
            fl = [x for x in t["flags"] if not x.startswith("K")][:9]
            kk = [x for x in t["flags"] if x.startswith("K")]
            out.append(f'| {t["T"]} {t["date"]} | RSI {t["rsi"]} · dist {t["dist"]}% · bounce {t["bounce"]}% · r5 '
                       f'{t["r5"]}% · range20 {t["range20"]}% · v1x {t["v1x"]} | {", ".join(fl)}{" …" if len(fl) == 9 else ""} '
                       f'| {", ".join(kk) or "—"} | {"yes" if t["invalidated"] else "no"} | '
                       f'{t.get("A")} · {t.get("B")} · {t.get("C")} | {", ".join(t.get("C_top", []))} | '
                       f'{", ".join(t.get("C_blockers", []))} | {t.get("would_be_class", "—")} |')
        return out

    head = ["| symbol | trough | ONSET | first intraday +70% | +70% close / jump | D1 | peak close · intraday | kind |",
            "|---|---|---|---|---|---|---|---|"]
    th = ["| day | values | flags (non-candle) | candles | invalidated | A · B · C | C top | C blockers | class |",
          "|---|---|---|---|---|---|---|---|---|"]
    L = ["# Chart casebook", "",
         "Generated by `ca_report.py` from `data/casebook.json` (`ca_casebook.py all`, after the sealed run). Dates "
         "are kept apart: ONSET = start of the final +70% leg; «first intraday +70%» = first session whose high is "
         "70% above the trough close; «+70% close / jump» = Q; D1 = the detector's first detection. Values and flags "
         "are computed from bars ≤ each day; A · B · C are the frozen axis probabilities; «class» is the class the day "
         "received (cases) or would have received inside its session (seeds and HUBC, which never entered a "
         "statistic).", "", "## 1. Seeds (DLXY · RETO · DKI · SXTC) and HUBC", ""]
    for sym, eps in cb["seeds_and_hubc"].items():
        L += [f"### {sym}" + (" — reported separately and never counted as a completed success of any rule (instruction); its "
                                    "daily-close episodes are listed as the detector sees them" if sym == "HUBC" else ""), ""] + head
        for e in eps:
            L.append(ev_line(dict(e, sym=sym)))
        for e in eps:
            L += ["", f'**{sym} · onset {e["dates"]["onset"]}** (T−10 … T−7)', ""] + th + tl_lines(e)
        L.append("")
    for w in ("development", "validation", "holdout"):
        c = cb[w]
        L += [f"## {w.capitalize()} — largest captured (READY_1–3) and largest missed events", ""]
        for kind in ("captured", "missed"):
            L += [f"### {kind}", ""] + head + [ev_line(x) for x in c[kind]] + [""]
            for x in c[kind][:3]:
                L += [f'**{x["sym"]} · onset {x["dates"]["onset"]}**', ""] + th + tl_lines(x) + [""]
        iv = c["invalidation_events"]
        L += [f'**Invalidation and the events of this window:** of {iv["eligible"]} eligible events, '
              f'{iv["all_pos_rows_invalidated"]} were in one of Faisal\'s three invalidation states (chasing, exploded '
              f'within 5 sessions, group-candle proxy) on every pivot-day of T−10…T−7 — '
              f'{rc["R5"][w]["all_invalidated_by_component_all_days"]["I04_GROUP_PROXY"]} of them with the group-candle '
              f'proxy on every day — ({iv["any_pos_row_invalidated"]} on at least one); such events cannot be READY by '
              f'construction. Of the 20 largest by peak gain, {iv["top20_by_peak_all_invalidated"]} were invalidated '
              "throughout (RECONCILIATION_ADDENDUM.md §3).", ""]
        L += ["### Same-session matched inactive controls (on each case's first POS710 day)", "",
              "| for | control | date | class | count | flags |", "|---|---|---|---|---|---|"]
        for x in c["controls"]:
            L.append(f'| {x["for"]} | {x["sym"]} | {x["date"]} | {x["class"]} | {x["count_score"]} | '
                     f'{", ".join(x["flags"][:10])} |')
        L += ["", "### Pivot-days with most of Faisal's counted conditions that did not explode", "",
              "| symbol | date | count of 11 | held | missing | class |", "|---|---|---|---|---|---|"]
        for x in c["partial_no_explosion"]:
            L.append(f'| {x["sym"]} | {x["date"]} | {x["count_score"]} | {", ".join(x["flags"])} | '
                     f'{", ".join(x["missing"])} | {x["class"]} |')
        L.append("")
    return "\n".join(L) + "\n"


def main(check=False):
    out = {"CONDITION_STRENGTH_RESULTS.md": strength_md(), "CANDLE_PATTERN_STUDY.md": candle_md(),
           "READY_CLASSIFICATION_SPEC.md": spec_md(), "HISTORICAL_CLASSIFICATION_RESULTS.md": results_md(),
           "CHART_CASEBOOK.md": casebook_md()}
    bad = []
    for name, txt in out.items():
        path = os.path.join(HERE, name)
        if check:
            if not os.path.exists(path) or open(path, encoding="utf-8").read() != txt:
                bad.append(name)
        else:
            open(path, "w", encoding="utf-8").write(txt)
    return bad


if __name__ == "__main__":
    if "--check" in sys.argv:
        b = main(True)
        print("❌ differs: " + ", ".join(b) if b else "✅ reports match")
        sys.exit(1 if b else 0)
    main()
    print("written")
