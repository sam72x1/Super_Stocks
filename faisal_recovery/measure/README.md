# faisal_recovery/measure — how every Phase A input was measured

These scripts are the **measurement record** of PHASE A (2026-10-08). They ran once in the session container, against sources that
CI cannot reach (this session's transcript and uploads, the scratchpad, GitHub API listings, Actions logs, a full git mirror). Their
output is frozen in `../data/phase_a_inputs.json` and `../data/artifact_probe_result.json`; `../phase_a.py` builds every Phase A
artifact from those two files, and `python3 faisal_recovery/phase_a.py --check` re-derives the artifacts and the seal from them.

| script | measures |
|---|---|
| `tr_extract.py` | every base64 image block of the session transcript (0-based line · message · tool · path · SHA256) |
| `hashimg.py` | SHA256 · dHash · pHash · size of a list of image files |
| `blob_scan.py` | every blob of a full mirror: image/PDF/archive magic bytes + embedded base64 image signatures |
| `prep_inputs.py` | writes `phase_a_inputs.json` (transcript · uploads · scratchpad · git mirror · GitHub text) |
| `prep_more.py` | adds repository renders · Telegram accounting · sessions, and writes `artifact_probe_result.json` (transcribed from the `APROBE` lines of runner probe 37713107882) |

`../artifact_probe.py` is the runner-side artifact probe (its temporary workflow was removed before merge).
Paths inside the scripts are the session's own; they are a record, not a CI step.
