from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

print("⚡ Loading SPORTZBOT...")

# ── RAG Setup ──────────────────────────────────────────────────
db_path = os.path.expanduser("~/sports-rag-chatbot/chroma_db")

embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"}
)

vectorstore = Chroma(
    persist_directory=db_path,
    embedding_function=embeddings
)

retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 6, "fetch_k": 12}
)

llm = OllamaLLM(model="llama3.2", temperature=0.2)

prompt_template = """You are SPORTZBOT — a precise, expert sports analytics AI with deep knowledge of football, basketball, NFL, cricket, tennis, Formula 1, MLB, NHL and all major sports worldwide.

Guidelines:
- Be clear, precise and data-driven
- Lead with the key fact, then provide supporting context
- Use relevant emojis sparingly and professionally
- Always cite exact stats, scores, and dates when available
- If information is not in context say: "I don't have that in my knowledge base yet."

Context:
{context}

Question: {question}

Answer:"""

prompt = PromptTemplate(
    template=prompt_template,
    input_variables=["context", "question"]
)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

qa_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt | llm | StrOutputParser()
)

print("✅ RAG pipeline ready!")

# ── FastAPI ────────────────────────────────────────────────────
app = FastAPI(title="SPORTZBOT API")

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        response = qa_chain.invoke(request.message)
        return {"response": response, "status": "ok"}
    except Exception as e:
        return {"response": f"Error: {str(e)}", "status": "error"}

@app.get("/health")
async def health():
    return {
        "status": "online",
        "model": "llama3.2",
        "chunks": vectorstore._collection.count()
    }

@app.get("/")
async def root():
    static_path = os.path.expanduser("~/sports-rag-chatbot/src/static/index.html")
    return FileResponse(static_path)

# Mount static files last
static_dir = os.path.expanduser("~/sports-rag-chatbot/src/static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")