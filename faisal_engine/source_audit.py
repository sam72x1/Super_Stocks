# -*- coding: utf-8 -*-
"""تدقيقُ استعادة المصادر (SOURCE_RECOVERY_AUDIT) — أرقامٌ من الملفّات لا باليد ⟵ out/source_audit.json. قراءةٌ فقط."""
import collections
import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.environ.get("FE_OUT") or os.path.join(HERE, "out")


def _inv():
    inv = json.load(open(os.path.join(ROOT, "faisal_method_v41", "corpus_audit", "MASTER_CORPUS_INVENTORY.json"), encoding="utf-8"))
    return inv["rows"] if isinstance(inv, dict) and "rows" in inv else inv


def main():
    corpus = json.load(open(os.path.join(ROOT, "faisal_method_v3", "image_corpus.json"), encoding="utf-8"))
    rows = _inv()
    vp = [json.loads(l) for l in open(os.path.join(ROOT, "faisal_method_v4", "data", "visual_pass_v4.jsonl"), encoding="utf-8") if l.strip()]
    tl = list(csv.DictReader(open(os.path.join(ROOT, "fm_forensics", "phase3", "FAISAL_TIMELINE.csv"), encoding="utf-8")))
    ex = json.load(open(os.path.join(ROOT, "faisal_method_v41", "corpus_audit", "research_queue_ex.json"), encoding="utf-8")) if os.path.exists(os.path.join(ROOT, "faisal_method_v41", "corpus_audit", "research_queue_ex.json")) else None
    src = collections.Counter(str(r.get("SOURCE")).split(" · ")[1] if " · " in str(r.get("SOURCE")) else str(r.get("SOURCE")) for r in rows)
    status = collections.Counter(str(r.get("ANALYSIS_STATUS")) for r in rows)
    author = collections.Counter(str(r.get("AUTHOR")) for r in rows)
    f_rows = [r for r in tl if r["IS_FAISAL"] == "1"]
    by_type = {t: sorted({r["TICKER"] for r in f_rows if r["EVIDENCE_TYPE"] == t}) for t in sorted({r["EVIDENCE_TYPE"] for r in f_rows})}
    dated = [r for r in f_rows if len(r["DATE"]) == 10 and r["OBSERVATION_CLASS"] in ("FOCUS", "WATCH", "READY", "ENTRY")]
    wa = sorted({t for r in rows for t in (r.get("TICKER") or []) if "WA_" in str(r.get("IMAGE_ID"))}) if rows else []
    ex_tickers = sorted({r["TICKER"] for r in dated} - set(wa) - {"UNK", ""})
    out = {
        "corpus": {"image_corpus_images": len(corpus["images"]) if isinstance(corpus, dict) and "images" in corpus else len(corpus),
                   "inventory_files": len(rows), "inventory_units": len({r.get("UNIT_ID") for r in rows}),
                   "visual_pass_v4_units": len(vp), "inventory_status": dict(status), "inventory_source_channel": dict(src), "inventory_author": dict(author),
                   "high_info": sum(1 for r in rows if r.get("HIGH_INFO") is True),
                   "partially_analyzed": sum(1 for r in rows if str(r.get("ANALYSIS_STATUS")).startswith("PARTIALLY"))},
        "sources": [
            {"id": "S-REPO-IMG", "name": "faisal_images/ + faisal_batches/ + chart_cards (repo)", "status": "ACCESSIBLE · INSPECTED (eye pass 609/609 units · inventory 769 files)"},
            {"id": "S-TG-BOT", "name": "Telegram bot updates (telegram_collect.py · scheduled)", "status": "ACCESSIBLE · collector pulls only what is sent to the bot; 2026-10-09 pull = 0"},
            {"id": "S-TG-CHANNEL", "name": "Faisal's Telegram channel history (pre-bot)", "status": "UNAVAILABLE (no API access; only images the owner forwarded)"},
            {"id": "S-X", "name": "X (@kisar_) posts", "status": "UNAVAILABLE live (blocked from runners); 70 X images present in corpus via owner forwards"},
            {"id": "S-WA", "name": "WhatsApp cases", "status": "ACCESSIBLE only as 2 forwarded images (NUWE · SXTC); chat export UNAVAILABLE"},
            {"id": "S-APP", "name": "Faisal's app screenshots", "status": "ACCESSIBLE · 8 images (V3) · 1 dated WATCH unit (VEEE)"},
            {"id": "S-GIT", "name": "git history of state files (weekly_watchlist · company_cache · near_watch)", "status": "ACCESSIBLE · used by Phase 5 (S01/S02) for bot-era floats/borrow only"},
            {"id": "S-SEC", "name": "SEC EDGAR submissions (fm_forensics/data/sec_2026-10-08.json.gz · 234/238 ok)", "status": "ACCESSIBLE · dated filings · used for offering validity"},
            {"id": "S-BARS", "name": "TradingView daily bars frozen 2026-10-08 (232/238 symbols · from 2025-01-01)", "status": "ACCESSIBLE · split-adjusted · 6 symbols without bars"},
            {"id": "S-PDF", "name": "منهج فيصل.pdf + Elliott guide + audio transcript", "status": "ACCESSIBLE locally · NOT PUSHED (public repo) · tagged faisal_adopted"},
            {"id": "S-SESSIONS", "name": "earlier Claude sessions / artifacts (Phase A probe)", "status": "INSPECTED by Phase A: NEW_TO_CORPUS 0 of 9,930 records"},
        ],
        "owner_examples_outside_whatsapp": {"dated_decision_units": len(dated), "dated_tickers": len({r["TICKER"] for r in dated}),
                                            "whatsapp_tickers": wa, "non_whatsapp_dated_tickers": ex_tickers, "by_evidence_type": by_type,
                                            "no_bars": sorted({r["TICKER"] for r in dated if r["TICKER"] in ("ATPC", "LABT", "MI", "UNK")})},
        "duplicates": dict(collections.Counter(("UNIQUE" if "UNIQUE" in str(r.get("DUPLICATE_STATUS")) else "DUPLICATE/DERIVATIVE") for r in rows)),
        "research_queue_ex": (len(ex) if isinstance(ex, list) else (len(ex.get("items", ex)) if isinstance(ex, dict) else None)),
        "unresolved": ["Faisal channel history before the bot (not retrievable)", "X live timeline (blocked)", "WhatsApp chat text (only 2 images)",
                       "10 chat images cited in Phase 3 (not recovered)", "float/borrow/short dated before bot logs (no source)"],
    }
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(os.path.join(OUT, "source_audit.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out["corpus"], ensure_ascii=False)[:600]); print(out["owner_examples_outside_whatsapp"])


if __name__ == "__main__":
    main()
