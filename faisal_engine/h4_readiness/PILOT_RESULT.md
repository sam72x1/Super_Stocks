# T-H4b pilot — result: **stopped at PG0, zero requests sent**

> 2026-10-12 · the owner authorized reopening T-H4 for research and a Massive pilot of at most 29 requests
> («أوافق على إعادة فتح T-H4 للبحث فقط، وأوافق على تجربة Massive الأولية بحد أقصى 29 طلب API»).
> The protocol is `PROTOCOL.md`; its seal `PROTOCOL.sha256` still verifies (`sha256sum -c` OK).

| gate | result | evidence |
|---|---|---|
| PG0 key and host | **FAIL — key not readable by this session** | `POLYGON_API_KEY` and `MASSIVE_API_KEY` are both absent from the session environment. Names only were checked; no value was printed. A secret added in the environment settings reaches a **new** session, not a running one. Host reachability was not probed. |
| PG1 access | not run | the protocol stops at the first failed gate |
| PG2 history depth | not run | — |
| PG3 extended hours | not run | — |
| PG4 30-minute alignment / 4H grid | not run | — |
| PG5 daily parity within 1% | not run | — |
| PG6 report-only checks | not run | — |

## Totals

- Requests sent: **0 of 29**.
- Data received: none.
- Pilot features computed: none.
- The protocol is unchanged, nothing is committed, and `fwd/` was not touched.

## Blocking fact for the next attempt

A new session starts in a fresh clone of the repository. Every untracked file of this study would therefore be absent
there: `PROTOCOL.md`, `SIZING.md`, `h4p_sizing.py`, the ALERTS100 study and the rest. Running the pilot in a new session
needs one of two things:

- these files pushed to the branch first, which needs the owner's permission; or
- the files recreated, which would not carry the same sealed bytes by construction.
