#!/usr/bin/env python3
"""Recover one explicitly bounded outage without touching production state."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import os
import sys
import time

import requests

os.environ.setdefault("SCREENER_MODE", "PROBE")

import Super_stock as bot
import operator_entry_live as live
import probe_common as probe


MAX_OPERATOR_LOOKUPS = 80
WORKERS = min(8, int(bot.LIQ_WORKERS))
OPERATOR_LOOKUPS = 0


def parse_utc(name):
    value = os.environ.get(name, "").strip()
    if not value:
        raise ValueError(f"{name} is required")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"{name} must include its UTC timezone")
    return parsed.astimezone(timezone.utc)


def minute_bars(symbol, day, key):
    endpoint = (f"https://api.polygon.io/v2/aggs/ticker/{symbol.upper()}"
                f"/range/1/minute/{day}/{day}")
    for attempt in range(3):
        try:
            response = requests.get(
                endpoint,
                headers={"Authorization": f"Bearer {key}"},
                params={"adjusted": "true", "sort": "asc", "limit": 50_000},
                timeout=20,
            )
            if response.status_code == 429 and attempt < 2:
                time.sleep(attempt + 1)
                continue
            if response.status_code != 200:
                return symbol, None, f"HTTP {response.status_code}"
            results = (response.json() or {}).get("results") or []
            bars = [
                {"o": bar.get("o"), "h": bar.get("h"), "l": bar.get("l"),
                 "c": bar.get("c"), "v": bar.get("v"), "t": bar.get("t"),
                 "vw": bar.get("vw")}
                for bar in results
                if bar.get("l") is not None and bar.get("c") is not None
            ]
            return symbol, bars, None
        except requests.RequestException as exc:
            if attempt == 2:
                return symbol, None, type(exc).__name__
            time.sleep(attempt + 1)
    return symbol, None, "retry limit"


def historical_operator(symbol, start_ms, close_ms, key):
    global OPERATOR_LOOKUPS
    OPERATOR_LOOKUPS += 1
    if OPERATOR_LOOKUPS > MAX_OPERATOR_LOOKUPS:
        raise RuntimeError("historical operator-request safety cap exceeded")
    try:
        response = requests.get(
            f"https://api.polygon.io/v3/trades/{symbol.upper()}",
            headers={"Authorization": f"Bearer {key}"},
            params={
                "timestamp.gte": int(start_ms) * 1_000_000,
                "timestamp.lt": int(close_ms) * 1_000_000,
                "limit": min(int(bot.LIQ_OPERATOR_TRADES), 50_000),
                "order": "desc",
            },
            timeout=30,
        )
        if response.status_code != 200:
            return None
        trades = (response.json() or {}).get("results") or []
        ordered = [(trade.get("price"), trade.get("size"))
                   for trade in reversed(trades)
                   if trade.get("price") and trade.get("size")]
        return bot._operator_blocks(ordered, bot.CONFIG["OPERATOR_MIN_SHARES"])
    except requests.RequestException:
        return None


def replay(symbol, bars, start_ms, end_ms, key, day):
    state = {}
    recovered = []
    previous_close = None
    previous_close_checked = False
    window = int(bot.LIQ_WINDOW_MIN)

    for count in range(3, len(bars) + 1):
        closed_ms = int(bars[count - 2]["t"]) + 60_000
        if closed_ms > end_ms:
            break

        events, next_state = bot.liq_stage_events(
            bars[max(0, count - window):count], state
        )
        state = next_state
        if not events:
            continue

        operator = None
        if any(event.get("stage") != "Px" for event in events):
            operator = historical_operator(symbol, start_ms, closed_ms, key)
            if operator is not None and not operator.get("has_operator"):
                events = [event for event in events if event.get("stage") == "Px"]
                if not events:
                    state = {}
                    continue

        if not previous_close_checked:
            previous_close = bot.polygon_prev_close(symbol, day)
            previous_close_checked = True

        for event in events:
            event["operator"] = operator
            if previous_close:
                event["prev_close"] = previous_close
            if event.get("stage") == "M5" and isinstance(event.get("k2"), dict):
                event["k2"]["j1"], event["k2"]["j1_top"] = bot._event_j1(event)

            event_close_ms = int(event.get("last_ms") or 0) + 60_000
            if start_ms <= event_close_ms <= end_ms:
                recovered.append(event)

    return recovered


def previously_delivered(symbol, event, state, day):
    current = state.get(bot.LIQ_STATE_PREFIX + symbol)
    if not isinstance(current, dict) or current.get("date") != day:
        return False
    if int(current.get("anchor_ms") or 0) != int(event.get("anchor_ms") or 0):
        return False
    stage = str(event.get("stage") or "")
    if stage == "Px":
        return int(current.get("pulse_ms") or 0) >= int(event.get("last_ms") or 0)
    return stage in (current.get("sent") or [])


def main():
    start = parse_utc("RECOVERY_START_UTC")
    end = parse_utc("RECOVERY_END_UTC")
    now = datetime.now(timezone.utc)
    if end <= start or end > now or (end - start).total_seconds() > 7_200:
        raise ValueError("recovery interval must be historical and at most two hours")

    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key or not bot.TELEGRAM_TOKEN or not bot.TELEGRAM_CHAT:
        raise RuntimeError("required market-data or Telegram configuration is missing")

    day = start.date().isoformat()
    if end.date().isoformat() != day:
        raise ValueError("recovery interval cannot cross UTC dates")
    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)

    witness, witness_bars, witness_error = minute_bars("AAPL", day, key)
    if witness_error or not witness_bars:
        raise RuntimeError(f"market-data witness {witness} unavailable: {witness_error}")

    _limited, _cut, _state, universe = live._load_universe()
    watchlist = dict(live._WL)
    by_symbol = {row["symbol"].upper(): row for row in universe if row.get("symbol")}
    if not by_symbol:
        raise RuntimeError("production monitoring universe is empty")

    print(f"INTERVAL_UTC={start.isoformat()}..{end.isoformat()}", flush=True)
    print(f"UNIVERSE={len(by_symbol)} WITNESS_BARS={len(witness_bars)}", flush=True)

    fetched = {}
    failures = []
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        results = executor.map(
            lambda symbol: minute_bars(symbol, day, key), sorted(by_symbol)
        )
        for symbol, bars, error in results:
            if error:
                failures.append((symbol, error))
            else:
                fetched[symbol] = bars

    print(f"FETCHED={len(fetched)} FAILED={len(failures)}", flush=True)
    if probe.coverage_bad(len(fetched), len(by_symbol), probe.MAX_MISS_FRAC):
        raise RuntimeError(f"market-data coverage insufficient: {failures[:8]}")

    candidates = []
    for symbol in sorted(fetched):
        bars = fetched[symbol]
        if len(bars) < 3:
            continue
        events = replay(symbol, bars, start_ms, end_ms, key, day)
        if events:
            candidates.append((by_symbol[symbol], events))

    config = bot.load_alert_filter()
    filtered, muted = bot.apply_alert_filter(candidates, config, watchlist)
    latest = live._fetch_state([bot.OP_ENTRY_STATE_FILE])
    state = latest.get(bot.OP_ENTRY_STATE_FILE)
    if not isinstance(state, dict):
        state = bot.load_op_entry_state()

    deliverable = []
    duplicates = 0
    for row, events in filtered:
        remaining = []
        for event in events:
            if previously_delivered(row["symbol"].upper(), event, state, day):
                duplicates += 1
            else:
                remaining.append(event)
        if remaining:
            deliverable.append((row, remaining))

    total = sum(len(events) for _row, events in deliverable)
    print(
        f"CANDIDATE_SYMBOLS={len(candidates)} FILTERED={len(muted)} "
        f"DUPLICATES={duplicates} DELIVERABLE_SYMBOLS={len(deliverable)} "
        f"DELIVERABLE_EVENTS={total} OPERATOR_LOOKUPS={OPERATOR_LOOKUPS}",
        flush=True,
    )
    for row, events in deliverable:
        stages = ",".join(str(event.get("stage")) for event in events)
        print(f"RECOVERED={row['symbol']} STAGES={stages}", flush=True)

    if not deliverable:
        print("DELIVERY=NOT_NEEDED", flush=True)
        return 0

    from zoneinfo import ZoneInfo

    ny = ZoneInfo("America/New_York")
    start_ny = start.astimezone(ny).strftime("%H:%M")
    end_ny = end.astimezone(ny).strftime("%H:%M")
    header = (
        f"<b>⏪ استدراك التنبيهات الفائتة {start_ny}–{end_ny} نيويورك</b>\n"
        "⚠️ الأحداث والأسعار تاريخية؛ ليست إشارة دخول حالية.\n\n"
    )
    message = header + bot.build_liq_stage_alert(
        deliverable, now_ms=int(time.time() * 1000)
    )
    if not bot.send_telegram(message):
        raise RuntimeError("Telegram delivery was not confirmed")
    print(f"DELIVERY=CONFIRMED EVENTS={total} SYMBOLS={len(deliverable)}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"RECOVERY_ERROR={type(exc).__name__}: {exc}", flush=True)
        sys.exit(1)
