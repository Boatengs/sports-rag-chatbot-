"""Question sets with known answers.

simpleqa_sports: every question in OpenAI's SimpleQA test set (MIT licence) whose topic is Sports.
wikidata_recent: "Who won the <event>?" for sports events that ended in 2024 or 2025, with the
winner taken from Wikidata's "winner" property (P1346). Only events with exactly one winner
statement and no qualifiers on it are kept, so the answer is not ambiguous.
"""

from __future__ import annotations

import argparse
import ast
import io
import json
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

SIMPLEQA_URL = "https://openaipublic.blob.core.windows.net/simple-evals/simple_qa_test_set.csv"
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
USER_AGENT = "sportzbot-benchmark/2.0 (https://github.com/Boatengs/sports-rag-chatbot-)"

RECENT_QUERY = """
SELECT ?event ?eventLabel ?winner ?winnerLabel ?sportLabel ?date WHERE {
  VALUES ?dateProp { wdt:P585 wdt:P582 }
  ?event ?dateProp ?date .
  FILTER(?date >= "2024-01-01T00:00:00Z"^^xsd:dateTime && ?date < "2026-01-01T00:00:00Z"^^xsd:dateTime)
  ?event wdt:P1346 ?winner ; wdt:P641 ?sport .
  ?event rdfs:label ?eventLabel . FILTER(LANG(?eventLabel) = "en")
  ?winner rdfs:label ?winnerLabel . FILTER(LANG(?winnerLabel) = "en")
  OPTIONAL { ?sport rdfs:label ?sportLabel . FILTER(LANG(?sportLabel) = "en") }
}
"""
WIKIDATA_API = "https://www.wikidata.org/w/api.php"


def _get(url: str, accept: str | None = None) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **({"Accept": accept} if accept else {})})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504) or attempt == 4:
                raise
            time.sleep(30 * (attempt + 1))
    raise RuntimeError("unreachable")


def winner_statements(qids: list[str]) -> dict[str, list[dict]]:
    """P1346 statements of each item, with rank and qualifiers, from the Wikidata API."""
    out: dict[str, list[dict]] = {}
    for i in range(0, len(qids), 50):
        url = WIKIDATA_API + "?" + urllib.parse.urlencode({"action": "wbgetentities", "ids": "|".join(qids[i : i + 50]), "props": "claims", "format": "json"})
        ents = json.loads(_get(url))["entities"]
        for q, e in ents.items():
            out[q] = [
                {"winner": c["mainsnak"].get("datavalue", {}).get("value", {}).get("id"), "rank": c["rank"], "qualifiers": list(c.get("qualifiers", {}))}
                for c in e.get("claims", {}).get("P1346", [])
            ]
        time.sleep(0.5)
    return out


def simpleqa_sports() -> list[dict]:
    import pandas as pd

    df = pd.read_csv(io.BytesIO(_get(SIMPLEQA_URL)))
    rows = []
    for i, r in df.iterrows():
        meta = ast.literal_eval(r["metadata"])
        if meta.get("topic") == "Sports":
            rows.append(
                {
                    "id": f"simpleqa_{i}",
                    "set": "simpleqa_sports",
                    "question": r["problem"],
                    "answer": str(r["answer"]),
                    "answer_type": meta.get("answer_type"),
                    "source_urls": meta.get("urls", []),
                }
            )
    return rows


def _is_label(text: str) -> bool:
    # Wikidata falls back to the Q id when an item has no English label
    return bool(text) and not (text[0] == "Q" and text[1:].isdigit())


def wikidata_recent(n: int, per_sport: int, seed: int, today: date) -> tuple[list[dict], dict]:
    url = WIKIDATA_SPARQL + "?" + urllib.parse.urlencode({"query": RECENT_QUERY, "format": "json"})
    bindings = json.loads(_get(url, "application/sparql-results+json"))["results"]["bindings"]
    by_event: dict[str, dict] = {}
    winners: dict[str, set] = defaultdict(set)
    for b in bindings:
        ev = b["event"]["value"].rsplit("/", 1)[1]
        winners[ev].add(b["winner"]["value"])
        d = b["date"]["value"][:10]
        prev = by_event.get(ev)
        if prev is None or d > prev["date"]:
            by_event[ev] = {
                "event": ev,
                "event_label": b["eventLabel"]["value"],
                "winner": b["winner"]["value"].rsplit("/", 1)[1],
                "winner_label": b["winnerLabel"]["value"],
                "sport": b.get("sportLabel", {}).get("value", ""),
                "date": d,
            }
    stats = Counter()
    stats["events_from_query"] = len(by_event)
    claims = winner_statements(sorted(by_event))
    kept = []
    for ev, r in by_event.items():
        st = [c for c in claims.get(ev, []) if c["rank"] != "deprecated"]
        if len(winners[ev]) != 1 or len(st) != 1:
            stats["more_than_one_winner"] += 1
            continue
        if st[0]["qualifiers"]:
            stats["winner_has_qualifiers"] += 1
            continue
        if not (_is_label(r["event_label"]) and _is_label(r["winner_label"])):
            stats["no_english_label"] += 1
            continue
        if r["date"] > today.isoformat():
            stats["not_finished"] += 1
            continue
        if r["winner_label"].lower() in r["event_label"].lower():
            stats["answer_in_question"] += 1
            continue
        kept.append(r)
    stats["candidates"] = len(kept)
    rng = random.Random(seed)
    kept.sort(key=lambda r: r["event"])
    rng.shuffle(kept)
    per: Counter = Counter()
    chosen = []
    for r in kept:
        if per[r["sport"]] >= per_sport:
            continue
        per[r["sport"]] += 1
        chosen.append(r)
        if len(chosen) == n:
            break
    rows = [
        {
            "id": f"wikidata_{r['event']}",
            "set": "wikidata_recent",
            "question": f"Who won the {r['event_label']}?",
            "answer": r["winner_label"],
            "answer_type": "Winner",
            "source_urls": [f"https://www.wikidata.org/wiki/{r['event']}"],
            "sport": r["sport"],
            "date": r["date"],
            "wikidata_winner": r["winner"],
        }
        for r in chosen
    ]
    stats["chosen"] = len(rows)
    stats["sports"] = len({r["sport"] for r in rows})
    return rows, dict(stats)


def write_jsonl(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("data/questions"))
    ap.add_argument("--n-recent", type=int, default=300)
    ap.add_argument("--per-sport", type=int, default=25)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    today = date.today()
    sq = simpleqa_sports()
    write_jsonl(sq, a.out / "simpleqa_sports.jsonl")
    wd, stats = wikidata_recent(a.n_recent, a.per_sport, a.seed, today)
    write_jsonl(wd, a.out / "wikidata_recent.jsonl")
    info = {
        "built_on": today.isoformat(),
        "simpleqa_sports": len(sq),
        "wikidata_recent": stats,
        "wikidata_sports": Counter(r["sport"] for r in wd).most_common(),
    }
    (a.out / "build.json").write_text(json.dumps(info, indent=1))
    print(json.dumps(info, indent=1))


if __name__ == "__main__":
    main()
