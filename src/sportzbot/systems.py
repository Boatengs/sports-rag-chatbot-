"""The three systems compared in the benchmark, all on the same generator model.

closed_book  the model answers from memory, with an instruction to say it does not know.
v1           version 1 as shipped: the 10 curated documents, 500 character chunks with 50 overlap,
             all-MiniLM-L6-v2 embeddings, MMR retrieval (k 6, fetch_k 12, lambda 0.5) and the
             version 1 prompt from src/app.py, at temperature 0.2.
v2           live Wikipedia: a short search query written by the model plus the question itself,
             up to 5 pages, passages ranked by a bi-encoder then a cross-encoder, the top 6 passed
             to a prompt that allows only answers found in the passages, with citations.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

import numpy as np

from .llm import LlamaServer
from .wiki import Passage, Wikipedia

ROOT = Path(__file__).resolve().parents[2]
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
DONT_KNOW = "I don't know based on the sources I found."

V1_PROMPT = """You are SPORTZBOT — the world's most knowledgeable and enthusiastic sports analytics AI expert. You have deep expertise in football, basketball, NFL, cricket, tennis, Formula 1, MLB, NHL and all major sports worldwide.

RULES:
1. Use the context below as your PRIMARY source of facts and statistics
2. You MAY expand on the context with your general sports knowledge to give richer, more detailed answers
3. Always be detailed, specific and cite real statistics, scores, dates and records
4. Be energetic and passionate — you LOVE sports
5. Use relevant emojis naturally
6. If something is completely outside your knowledge say: "I don't have enough data on that one!"
7. Never give one-line answers — always explain and elaborate

Context:
{context}

Question: {question}

Detailed Answer:"""

CLOSED_PROMPT = """Answer the question in one short sentence. If you are not sure of the answer, reply exactly: I don't know.

Question: {question}"""

QUERY_PROMPT = """Write a short Wikipedia search query (2 to 6 words) that would find the article answering this question. Reply with the query only.

Question: {question}"""

V2_PROMPT = (
    """You answer sports questions using only the numbered Wikipedia passages below.

Rules:
- Answer in one or two sentences, starting with the answer itself.
- Use only facts stated in the passages. Do not add anything from memory.
- Cite the passages you used like [1] or [2][3].
- If the passages do not state the answer, reply exactly: """
    + DONT_KNOW
    + """

Passages:
{passages}

Question: {question}

Answer:"""
)


_encoders: dict = {}


def embedder():
    if "embed" not in _encoders:
        from sentence_transformers import SentenceTransformer

        _encoders["embed"] = SentenceTransformer(EMBED_MODEL, device="cpu")
    return _encoders["embed"]


def reranker():
    if "rerank" not in _encoders:
        from sentence_transformers import CrossEncoder

        _encoders["rerank"] = CrossEncoder(RERANK_MODEL, device="cpu")
    return _encoders["rerank"]


def mmr(query_vec: np.ndarray, doc_vecs: np.ndarray, k: int, lambda_mult: float = 0.5) -> list[int]:
    """Maximal marginal relevance as LangChain implements it (cosine similarity, lambda 0.5)."""

    def cos(a, b):
        a = a / np.linalg.norm(a, axis=-1, keepdims=True)
        b = b / np.linalg.norm(b, axis=-1, keepdims=True)
        return a @ b.T

    sim_q = cos(query_vec[None], doc_vecs)[0]
    chosen = [int(np.argmax(sim_q))]
    while len(chosen) < min(k, len(doc_vecs)):
        best, best_score = -1, -np.inf
        sim_chosen = cos(doc_vecs, doc_vecs[chosen])
        for i in range(len(doc_vecs)):
            if i in chosen:
                continue
            score = lambda_mult * sim_q[i] - (1 - lambda_mult) * sim_chosen[i].max()
            if score > best_score:
                best, best_score = i, score
        chosen.append(best)
    return chosen


class V1Retriever:
    def __init__(self, docs_dir: Path = ROOT / "documents"):
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        self.chunks: list[tuple[str, str]] = []
        for f in sorted(Path(docs_dir).glob("*.txt")):
            for c in splitter.split_text(f.read_text()):
                self.chunks.append((f.name, c))
        self.vecs = embedder().encode([c for _, c in self.chunks], batch_size=32)

    def __call__(self, question: str, k: int = 6, fetch_k: int = 12) -> list[tuple[str, str]]:
        q = embedder().encode([question])[0]
        sims = self.vecs @ q / (np.linalg.norm(self.vecs, axis=1) * np.linalg.norm(q))
        top = np.argsort(-sims)[:fetch_k]
        picked = mmr(q, self.vecs[top], k)
        return [self.chunks[top[i]] for i in picked]


def answer_closed_book(llm: LlamaServer, question: str) -> dict:
    r = llm.chat(CLOSED_PROMPT.format(question=question), temperature=0.0, max_tokens=96)
    return {"answer": r["text"], "llm_seconds": r["seconds"], "prompt_tokens": r["prompt_tokens"], "sources": []}


def answer_v1(llm: LlamaServer, retriever: V1Retriever, question: str) -> dict:
    t0 = time.time()
    chunks = retriever(question)
    context = "\n\n".join(c for _, c in chunks)
    r = llm.chat(V1_PROMPT.format(context=context, question=question), temperature=0.2, max_tokens=512)
    return {
        "answer": r["text"],
        "llm_seconds": r["seconds"],
        "retrieval_seconds": round(time.time() - t0 - r["seconds"], 2),
        "prompt_tokens": r["prompt_tokens"],
        "sources": [{"file": f, "text": c} for f, c in chunks],
    }


def clean_query(text: str) -> str:
    text = text.strip().splitlines()[0] if text.strip() else ""
    return re.sub(r'^(query:\s*)|["\']', "", text, flags=re.I).strip()[:120]


def retrieve_v2(llm: LlamaServer, wiki: Wikipedia, question: str, pages: int = 5, top: int = 6, prefilter: int = 40) -> dict:
    t0 = time.time()
    q = llm.chat(QUERY_PROMPT.format(question=question), temperature=0.0, max_tokens=24)
    query = clean_query(q["text"])
    titles: list[str] = []
    for search in (query, question):
        if not search:
            continue
        for t in wiki.search(search, limit=3):
            if t not in titles:
                titles.append(t)
    titles = titles[:pages]
    passages: list[Passage] = []
    for t in titles:
        passages.extend(wiki.page(t))
    fetched = time.time()
    ranked: list[tuple[Passage, float]] = []
    if passages:
        texts = [p.render() for p in passages]
        e = embedder()
        pv = e.encode(texts, batch_size=64)
        qv = e.encode([question])[0]
        sims = pv @ qv / (np.linalg.norm(pv, axis=1) * np.linalg.norm(qv) + 1e-9)
        cand = np.argsort(-sims)[:prefilter]
        scores = reranker().predict([(question, texts[i]) for i in cand], batch_size=32)
        order = np.argsort(-np.asarray(scores))[:top]
        ranked = [(passages[cand[i]], float(scores[i])) for i in order]
    return {
        "query": query,
        "titles": titles,
        "n_passages": len(passages),
        "ranked": ranked,
        "query_seconds": q["seconds"],
        "fetch_seconds": round(fetched - t0 - q["seconds"], 2),
        "rank_seconds": round(time.time() - fetched, 2),
    }


def answer_v2(llm: LlamaServer, wiki: Wikipedia, question: str) -> dict:
    ret = retrieve_v2(llm, wiki, question)
    ranked = ret.pop("ranked")
    if not ranked:
        return {"answer": DONT_KNOW, "llm_seconds": 0.0, "prompt_tokens": 0, "sources": [], **ret}
    block = "\n\n".join(f"[{i + 1}] {p.render()}" for i, (p, _) in enumerate(ranked))
    r = llm.chat(V2_PROMPT.format(passages=block, question=question), temperature=0.0, max_tokens=160)
    return {
        "answer": r["text"],
        "llm_seconds": r["seconds"],
        "prompt_tokens": r["prompt_tokens"],
        "sources": [
            {"n": i + 1, "title": p.title, "section": p.section, "revid": p.revid, "url": p.url, "score": round(s, 3), "text": p.text}
            for i, (p, s) in enumerate(ranked)
        ],
        **ret,
    }
