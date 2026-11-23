"""Turn graded answers into results/<tag>/RESULTS.md and summary.json.

For each system and question set: the share of answers graded correct, incorrect and not attempted,
accuracy when the system did answer, and SimpleQA's F1 (harmonic mean of correct and accuracy when
answering). 95% intervals come from 2,000 bootstrap resamples of questions.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

SYSTEMS = ["closed_book", "v1", "v2"]
SETS = ["simpleqa_sports", "wikidata_recent"]
NAMES = {"closed_book": "Llama 3.2 3B alone", "v1": "Version 1 (curated documents)", "v2": "Version 2 (live Wikipedia)"}


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", text)).strip()


def answer_in_sources(gold: str, sources: list[dict]) -> bool:
    g = norm(gold)
    return bool(g) and any(g in norm(s.get("text", "")) for s in sources)


def load(d: Path) -> pd.DataFrame:
    ans, grd = [], []
    for f in sorted(d.glob("answers_*.jsonl")):
        ans += [json.loads(x) for x in f.read_text().splitlines() if x.strip()]
    for f in sorted(d.glob("graded_*.jsonl")):
        grd += [json.loads(x) for x in f.read_text().splitlines() if x.strip()]
    a = pd.DataFrame(ans)
    g = pd.DataFrame(grd)[["id", "system", "grade"]]
    df = a.merge(g, on=["id", "system"], how="left")
    df["answer_in_sources"] = [answer_in_sources(gl, s or []) for gl, s in zip(df["gold"], df["sources"], strict=True)]
    return df


def rates(grades: np.ndarray) -> dict:
    c = float(np.mean(grades == "CORRECT"))
    i = float(np.mean(grades == "INCORRECT"))
    att = c + i
    acc = c / att if att else 0.0
    f1 = 2 * acc * c / (acc + c) if (acc + c) else 0.0
    return {"correct": c, "incorrect": i, "not_attempted": 1 - att, "accuracy_when_answered": acc, "f1": f1}


def bootstrap(grades: np.ndarray, n: int = 2000, seed: int = 42) -> dict:
    rng = np.random.default_rng(seed)
    draws = [rates(grades[rng.integers(0, len(grades), len(grades))]) for _ in range(n)]
    return {k: [float(np.percentile([d[k] for d in draws], 2.5)), float(np.percentile([d[k] for d in draws], 97.5))] for k in draws[0]}


def summarise(df: pd.DataFrame) -> dict:
    out: dict = {"systems": {}}
    for s in SYSTEMS:
        for st in SETS + ["all"]:
            d = df[(df.system == s) & ((df.set == st) | (st == "all"))]
            if d.empty:
                continue
            g = d["grade"].fillna("NOT_ATTEMPTED").to_numpy()
            r = rates(g)
            out["systems"].setdefault(s, {})[st] = {
                "n": int(len(d)),
                **r,
                "ci": bootstrap(g),
                "errors": int(d["error"].notna().sum()),
                "ungraded": int(d["grade"].isna().sum()),
                "median_seconds": float(d["seconds"].median()),
                "answer_in_sources": float(d["answer_in_sources"].mean()) if s != "closed_book" else None,
            }
    v2 = df[df.system == "v2"]
    if not v2.empty:
        ins = v2[v2.answer_in_sources]
        outs = v2[~v2.answer_in_sources]
        out["v2_by_retrieval"] = {
            "answer_in_sources": {"n": int(len(ins)), **rates(ins["grade"].fillna("NOT_ATTEMPTED").to_numpy())} if len(ins) else None,
            "answer_not_in_sources": {"n": int(len(outs)), **rates(outs["grade"].fillna("NOT_ATTEMPTED").to_numpy())} if len(outs) else None,
        }
    return out


def pct(x: float) -> str:
    return f"{100 * x:.1f}"


def write_markdown(summary: dict, d: Path) -> None:
    L = ["# SPORTZBOT benchmark results", "", "Share of questions, in %. Brackets are 95% bootstrap intervals.", ""]
    for st, title in [
        ("simpleqa_sports", "SimpleQA, sports questions"),
        ("wikidata_recent", "Winners of sports events in 2024 and 2025 (Wikidata)"),
        ("all", "Both sets together"),
    ]:
        L += [
            f"## {title}",
            "",
            "| System | Questions | Correct | Incorrect | Not attempted | Accuracy when it answered | F1 |",
            "|---|---|---|---|---|---|---|",
        ]
        for s in SYSTEMS:
            r = summary["systems"].get(s, {}).get(st)
            if not r:
                continue
            ci = r["ci"]
            L.append(
                f"| {NAMES[s]} | {r['n']} | {pct(r['correct'])} ({pct(ci['correct'][0])} to {pct(ci['correct'][1])}) | {pct(r['incorrect'])} ({pct(ci['incorrect'][0])} to {pct(ci['incorrect'][1])}) "
                f"| {pct(r['not_attempted'])} | {pct(r['accuracy_when_answered'])} ({pct(ci['accuracy_when_answered'][0])} to {pct(ci['accuracy_when_answered'][1])}) | {pct(r['f1'])} |"
            )
        L.append("")
    L += [
        "## Retrieval and speed",
        "",
        "| System | Set | Gold answer appears word for word in the sources (%) | Median seconds per question | Errors | Ungraded |",
        "|---|---|---|---|---|---|",
    ]
    for s in SYSTEMS:
        for st in SETS:
            r = summary["systems"].get(s, {}).get(st)
            if r:
                ais = "" if r["answer_in_sources"] is None else pct(r["answer_in_sources"])
                L.append(f"| {NAMES[s]} | {st} | {ais} | {r['median_seconds']:.1f} | {r['errors']} | {r['ungraded']} |")
    vb = summary.get("v2_by_retrieval")
    if vb:
        L += [
            "",
            "## Version 2, split by whether the gold answer was in the retrieved passages",
            "",
            "| Retrieved passages | Questions | Correct | Incorrect | Not attempted |",
            "|---|---|---|---|---|",
        ]
        for k, label in [("answer_in_sources", "contain the gold answer"), ("answer_not_in_sources", "do not contain it word for word")]:
            r = vb.get(k)
            if r:
                L.append(f"| {label} | {r['n']} | {pct(r['correct'])} | {pct(r['incorrect'])} | {pct(r['not_attempted'])} |")
    (d / "RESULTS.md").write_text("\n".join(L) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", type=Path, required=True)
    a = ap.parse_args()
    df = load(a.dir)
    s = summarise(df)
    (a.dir / "summary.json").write_text(json.dumps(s, indent=1))
    write_markdown(s, a.dir)
    print((a.dir / "RESULTS.md").read_text())


if __name__ == "__main__":
    main()
