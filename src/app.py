"""SPORTZBOT version 2 web app: answers from live Wikipedia with cited sources.

Run a local model first, either
    ollama pull llama3.2 && ollama serve                      (SPORTZBOT_LLM_URL=http://127.0.0.1:11434, the default)
or
    llama-server -m Llama-3.2-3B-Instruct-Q4_K_M.gguf --port 8080   (SPORTZBOT_LLM_URL=http://127.0.0.1:8080)
then
    uvicorn app:app --app-dir src --port 8000
"""

import os
import re
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from sportzbot.llm import LlamaServer
from sportzbot.systems import answer_v2
from sportzbot.wiki import Wikipedia

STATIC = Path(__file__).parent / "static"
llm = LlamaServer(os.environ.get("SPORTZBOT_LLM_URL", "http://127.0.0.1:11434"), model=os.environ.get("SPORTZBOT_MODEL", "llama3.2"))
wiki = Wikipedia(cache_dir=Path(os.environ.get("SPORTZBOT_CACHE", Path.home() / ".cache" / "sportzbot")))

app = FastAPI(title="SPORTZBOT API")


class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
def chat(request: ChatRequest):
    question = request.message.strip()[:500]
    try:
        r = answer_v2(llm, wiki, question)
    except Exception as e:
        return {"response": f"Something went wrong: {type(e).__name__}", "sources": [], "status": "error"}
    cited = {int(n) for n in re.findall(r"\[(\d+)\]", r["answer"])}
    sources = [{"n": s["n"], "title": s["title"], "section": s["section"], "url": s["url"]} for s in r["sources"] if s["n"] in cited]
    return {"response": r["answer"], "sources": sources, "status": "ok"}


@app.get("/health")
def health():
    return {"status": "online", "llm": llm.url, "model": llm.model}


@app.get("/")
def root():
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")
