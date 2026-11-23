"""Answer a question set with one system, then grade the answers.

    python -m sportzbot.run answer --system v2 --questions data/questions/*.jsonl --shard 0 --n-shards 8 --out out
    python -m sportzbot.run grade --answers out/answers_v2_0.jsonl --out out

Answers are appended one line at a time, so a rerun picks up where it stopped.

The grader prompt is OpenAI's SimpleQA grader template, copied unchanged from
https://github.com/openai/simple-evals (MIT licence) into grader_template.txt.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

from .llm import LlamaServer
from .questions import read_jsonl

TEMPLATE = (Path(__file__).parent / "grader_template.txt").read_text()
LETTER = {"A": "CORRECT", "B": "INCORRECT", "C": "NOT_ATTEMPTED"}


def shard_rows(rows: list[dict], shard: int, n_shards: int) -> list[dict]:
    return rows[shard::n_shards]


def load_questions(paths: list[Path], limit: int | None, skip: int = 0) -> list[dict]:
    rows = []
    for p in paths:
        r = read_jsonl(p)[skip:]
        rows.extend(r[:limit] if limit else r)
    return rows


def done_ids(path: Path) -> set[str]:
    return {json.loads(line)["id"] for line in path.read_text().splitlines() if line.strip()} if path.exists() else set()


def answer(system: str, questions: list[dict], out: Path, llm: LlamaServer, cache: Path | None) -> None:
    from . import systems

    out.parent.mkdir(parents=True, exist_ok=True)
    seen = done_ids(out)
    if system == "v1":
        retriever = systems.V1Retriever()
    elif system == "v2":
        from .wiki import Wikipedia

        wiki = Wikipedia(cache_dir=cache)
    with out.open("a") as f:
        for i, q in enumerate(questions):
            if q["id"] in seen:
                continue
            t0 = time.time()
            try:
                if system == "closed_book":
                    r = systems.answer_closed_book(llm, q["question"])
                elif system == "v1":
                    r = systems.answer_v1(llm, retriever, q["question"])
                elif system == "v2":
                    r = systems.answer_v2(llm, wiki, q["question"])
                else:
                    raise ValueError(system)
                r["error"] = None
            except Exception as e:  # keep going; the error is recorded and counted in the report
                r = {"answer": "", "sources": [], "error": f"{type(e).__name__}: {e}"}
            r.update({"id": q["id"], "set": q["set"], "system": system, "question": q["question"], "gold": q["answer"], "seconds": round(time.time() - t0, 2)})
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            f.flush()
            print(f"{i + 1}/{len(questions)} {q['id']} {r['seconds']}s", flush=True)


def grade_one(llm: LlamaServer, question: str, gold: str, predicted: str) -> tuple[str, str]:
    prompt = TEMPLATE.replace("{question}", question).replace("{target}", gold).replace("{predicted_answer}", predicted)
    raw = llm.chat(prompt, temperature=0.0, max_tokens=4)["text"]
    m = re.search(r"(A|B|C)", raw)
    return LETTER[m.group(0)] if m else "NOT_ATTEMPTED", raw


def grade(answers: Path, out: Path, llm: LlamaServer) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    seen = done_ids(out)
    rows = read_jsonl(answers)
    with out.open("a") as f:
        for i, r in enumerate(rows):
            if r["id"] in seen:
                continue
            g, raw = grade_one(llm, r["question"], r["gold"], r["answer"])
            f.write(json.dumps({"id": r["id"], "system": r["system"], "grade": g, "grader_raw": raw}, ensure_ascii=False) + "\n")
            f.flush()
            print(f"{i + 1}/{len(rows)} {r['id']} {g}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("answer")
    a.add_argument("--system", required=True, choices=["closed_book", "v1", "v2"])
    a.add_argument("--questions", type=Path, nargs="+", required=True)
    a.add_argument("--shard", type=int, default=0)
    a.add_argument("--n-shards", type=int, default=1)
    a.add_argument("--limit", type=int, default=None, help="first N questions of each set, for a pilot")
    a.add_argument("--skip", type=int, default=0, help="leave out the first N questions of each set (the pilot questions used while building)")
    a.add_argument("--out", type=Path, required=True)
    a.add_argument("--cache", type=Path, default=None)
    a.add_argument("--llm", default="http://127.0.0.1:8080")
    g = sub.add_parser("grade")
    g.add_argument("--answers", type=Path, required=True)
    g.add_argument("--out", type=Path, required=True)
    g.add_argument("--llm", default="http://127.0.0.1:8080")
    args = ap.parse_args()
    llm = LlamaServer(args.llm)
    llm.wait()
    if args.cmd == "answer":
        qs = shard_rows(load_questions(args.questions, args.limit, args.skip), args.shard, args.n_shards)
        answer(args.system, qs, args.out / f"answers_{args.system}_{args.shard}.jsonl", llm, args.cache)
    else:
        grade(args.answers, args.out / args.answers.name.replace("answers_", "graded_"), llm)


if __name__ == "__main__":
    main()
