<div align="center">

# 🔍 NovelVerified.AI

**AI-Powered Novel Claim Verification System**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-55%20passed-brightgreen.svg)](#testing)

*Verify character backstory claims against actual novel text using RAG + LLM*

*Supports both **Claude API** and **Local LLM** (Ollama)*

</div>

---

## 📖 Overview

NovelVerified.AI is an intelligent system that determines whether **character backstory claims** about literary works are **supported** or **contradicted** by the actual text of the novels.

### Example

> **Claim:** "Edmond Dantes was imprisoned for fourteen years"  
> **Novel:** *The Count of Monte Cristo*  
> **Verdict:** ✅ **SUPPORTED** (confidence: 0.95)

---

## ✨ Features

- 🤖 **7-Agent Pipeline** - Modular architecture from ingestion to results
- 🔎 **Semantic Search** - FAISS vector index with sentence-transformers
- 🧠 **Flexible LLM Backend** - Claude API or **local Ollama** (runs on your GPU!)
- 📊 **Modern Dashboard** - React + Tailwind UI for exploring results
- 🔄 **Resumable Processing** - Continue from where you left off
- 📝 **Detailed Dossiers** - Human-readable Markdown reports per claim
- ✅ **Comprehensive Tests** - 55+ pytest tests with mocked APIs

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         DATA SOURCES                            │
├──────────────────────┬──────────────────────────────────────────┤
│   novels/*.txt       │       train.csv / test.csv              │
└──────────┬───────────┴──────────────────┬───────────────────────┘
           │                              │
           ▼                              ▼
┌──────────────────────┐       ┌──────────────────────┐
│   Ingestion Agent    │       │    Claim Parser      │
│   (chunk novels)     │       │    (parse CSV)       │
└──────────┬───────────┘       └──────────┬───────────┘
           │                              │
           ▼                              │
┌──────────────────────┐                  │
│   Embedding Agent    │                  │
│   (FAISS index)      │                  │
└──────────┬───────────┘                  │
           │                              │
           ▼                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Retriever Agent                            │
│              (find relevant passages per claim)                 │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Reasoning Agent                            │
│                    (Claude API verdicts)                        │
└──────────┬───────────────────────────────────────┬──────────────┘
           │                                       │
           ▼                                       ▼
┌──────────────────────┐             ┌────────────────────────────┐
│   Dossier Writer     │             │   Results Aggregator       │
│   (Markdown reports) │             │   (CSV output)             │
└──────────────────────┘             └────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- **Option A:** [Anthropic API key](https://console.anthropic.com/) (cloud)
- **Option B:** [Ollama](https://ollama.com/) (local, free)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/NovelVerified.AI.git
cd NovelVerified.AI

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Run the Pipeline

```bash
# Full pipeline with Claude API
python run_all.py

# Full pipeline with LOCAL LLM (no API needed!)
python run_all.py --local

# Test mode (limited claims)
python run_all.py --test-mode

# Skip LLM calls (use cached verdicts)
python run_all.py --skip-reasoning

# Start from specific stage
python run_all.py --start-from reasoning
```

### 🏠 Local LLM Setup (Ollama)

Run entirely on your machine with no API costs:

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull a model (choose based on your GPU VRAM)
ollama pull phi3:mini          # 4GB VRAM - fast
ollama pull mistral:7b-instruct-q4_0  # 5GB VRAM - better quality
ollama pull llama3.2:3b        # 3GB VRAM - lightweight

# 3. Run the pipeline locally
python run_all.py --local
```

| Model | VRAM Required | Speed |
|-------|---------------|-------|
| phi3:mini | ~4GB | ~2-3 sec/claim |
| mistral:7b-q4 | ~5GB | ~4-5 sec/claim |
| llama3.2:3b | ~3GB | ~2 sec/claim |

### Start the Dashboard

```bash
# Terminal 1: Start Flask API
python flask_api/app.py

# Terminal 2: Start React frontend
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 to view the dashboard.

---

## 📁 Project Structure

```
NovelVerified.AI/
├── agents/                  # Pipeline agents
│   ├── ingestion_agent.py   # Chunk novels into segments
│   ├── embedding_agent.py   # Create FAISS vector index
│   ├── claim_parser.py      # Parse claims from CSV
│   ├── retriever_agent.py   # Find relevant passages
│   ├── reasoning_agent.py       # Claude API verification
│   ├── reasoning_agent_local.py # Local Ollama verification
│   ├── dossier_writer.py        # Generate Markdown reports
│   ├── results_aggregator.py    # Compile final CSV
│   └── utils.py                 # Shared utilities
├── data/
│   ├── novels/              # Source novel .txt files
│   ├── train.csv            # Training claims (with labels)
│   └── test.csv             # Test claims
├── flask_api/
│   └── app.py               # REST API server
├── frontend/                # React + Vite + Tailwind dashboard
├── tests/                   # Pytest test suite
├── run_all.py               # Pipeline orchestrator
├── requirements.txt         # Python dependencies
└── .env.example             # Environment template
```

### Generated Directories

| Directory | Contents |
|-----------|----------|
| `chunks/` | Chunked novel text (JSONL) |
| `index/` | FAISS index + metadata |
| `claims/` | Parsed claims (JSONL) |
| `evidence/` | Retrieved passages per claim |
| `verdicts/` | Claude API verdicts (JSON) |
| `dossiers/` | Human-readable reports (Markdown) |
| `output/` | Final results.csv |

---

## 🔧 Configuration

Edit `.env` to configure:

```env
# Option A: Claude API
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4-20250514

# Option B: Local Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=phi3:mini

# Flask server
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
FLASK_DEBUG=true
```

---

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=agents --cov=flask_api

# Run specific test file
python -m pytest tests/test_reasoning_agent.py -v

# Run only unit tests
python -m pytest tests/ -v -m unit
```

Current status: **55 tests passing** ✅

---

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/results` | GET | All verification results |
| `/api/dossier/<id>` | GET | Markdown dossier for claim |
| `/api/verdict/<id>` | GET | Raw verdict JSON |
| `/api/evidence/<id>` | GET | Retrieved evidence |
| `/api/stats` | GET | Summary statistics |
| `/api/books` | GET | List of books |
| `/api/characters` | GET | List of characters |
| `/download/results.csv` | GET | Download results file |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Anthropic Claude](https://www.anthropic.com/) - Cloud AI reasoning
- [Ollama](https://ollama.com/) - Local LLM runtime
- [Sentence Transformers](https://www.sbert.net/) - Embeddings
- [FAISS](https://github.com/facebookresearch/faiss) - Vector search
- Classic novels from [Project Gutenberg](https://www.gutenberg.org/)

---

<div align="center">

**Built with ❤️ for literary AI research**

</div>
