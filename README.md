#  SPORTZBOT — AI Sports Analytics Chatbot

A full-stack RAG-powered sports analytics chatbot with a Slack-style dashboard interface. Ask anything about football, basketball, NFL, cricket, tennis, Formula 1 and more — powered by Llama 3.2 running fully locally.

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-Latest-orange)](https://langchain.com)
[![Llama](https://img.shields.io/badge/Llama-3.2-purple)](https://ollama.com)

---

##  Live Demo

> Run locally — see setup instructions below.
> Zero API costs · Fully local · No internet required after setup

---

##  Interface

- **Slack-style dashboard** with sidebar navigation
- **Dark / Light mode** toggle with preference saved
- **Channel switching** — football, basketball, NFL, cricket, tennis, F1
- **Quick Questions** sidebar for instant demos
- **Typing indicator** for real-time feedback
- **Responsive chat** with timestamps

---

##  Architecture

---

##  Knowledge Base

| Domain | Coverage |
|--------|----------|
|  Football | World Cup history, UCL, Premier League, Messi vs Ronaldo |
|  Basketball | NBA 2024, Paris Olympics, FIBA |
|  NFL | Super Bowl history, Patrick Mahomes era |
|  Cricket | T20 World Cup 2024, IPL, Test cricket |
|  Tennis | Grand Slams, ATP/WTA rankings 2024 |
|  Formula 1 | Verstappen, Hamilton, Ferrari 2024 |
|  Latest News | Ballon d'Or 2024, Mbappe to Real Madrid, Euro 2024 |

**10 documents · 57 knowledge chunks · All indexed in ChromaDB**

---

##  Quick Start

**Prerequisites:** Python 3.11+, [Ollama](https://ollama.com)

```bash
# 1. Clone the repo
git clone https://github.com/Boatengs/sports-rag-chatbot.git
cd sports-rag-chatbot

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install langchain langchain-community langchain-chroma \
            langchain-ollama langchain-text-splitters \
            chromadb sentence-transformers fastapi \
            uvicorn python-multipart ollama

# 4. Pull Llama 3.2
ollama pull llama3.2

# 5. Build the vector store
python3 - << 'PYEOF'
import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma

docs_path = "documents"
db_path   = "chroma_db"

loader    = DirectoryLoader(docs_path, glob="**/*.txt", loader_cls=TextLoader)
documents = loader.load()
splitter  = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks    = splitter.split_documents(documents)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2", model_kwargs={"device": "cpu"})
vectorstore = Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=db_path)
print(f" Vector store ready with {vectorstore._collection.count()} chunks!")
PYEOF

# 6. Start the server
cd src
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Open **http://localhost:8000** 

---

##  Tech Stack

| Layer | Technology |
|-------|-----------|
| **LLM** | Llama 3.2 via Ollama (fully local) |
| **RAG Framework** | LangChain |
| **Vector Store** | ChromaDB |
| **Embeddings** | HuggingFace all-MiniLM-L6-v2 |
| **Backend** | FastAPI + Uvicorn |
| **Frontend** | Vanilla HTML / CSS / JavaScript |
| **Retrieval** | MMR (Maximum Marginal Relevance) |

---

##  Key Technical Decisions

**Why RAG over pure LLM prompting?**
Llama 3.2's training cutoff means it lacks 2024-25 sports data. RAG grounds every answer in our curated knowledge base, eliminating hallucination on recent events like the 2024 Ballon d'Or winner or Mbappe's transfer.

**Why MMR retrieval?**
Maximum Marginal Relevance retrieves diverse chunks rather than the top-6 most similar. This prevents the model from seeing redundant context and improves answer quality across multi-topic questions.

**Why FastAPI + Vanilla JS over Gradio?**
Gradio's rendering flash and limited CSS control made it unsuitable for a portfolio-quality UI. FastAPI serves the RAG pipeline as a clean REST API, giving full control over the frontend design.

**Why Llama 3.2 locally via Ollama?**
Zero API costs, no rate limits, full privacy, and no internet dependency after initial setup — making this deployable anywhere.

---

##  Known Limitations

- Knowledge base is static — requires manual updates for new sports events
- Response time depends on local hardware (M3 Mac: ~5-10 seconds per answer)
- Knowledge limited to documents in the `/documents` folder
- Very specific statistical queries may miss if not in the knowledge base

---

##  Key Learnings

- RAG dramatically improves LLM accuracy on domain-specific recent knowledge
- MMR retrieval outperforms simple similarity search for diverse questions
- Prompt engineering is critical — forcing context-only answers prevents hallucination
- Building a custom frontend gives far more portfolio impact than default Gradio UI

---

##  Project Structure
---

##  Links

- [Project 1 — Sentiment Analyzer](https://github.com/Boatengs/sentiment-analyzer)
- [My Portfolio](#)
- [LinkedIn](#)
