# AI Interview Agent (Rooman Technologies)

Lightweight, production-oriented interview agent scaffold using Streamlit, LangChain, and a pluggable model/provider interface (OpenAI, Anthropic/Claude). This repo provides a minimal but runnable demo suitable for deployment to Streamlit Community Cloud.

Features
- Streamlit UI for creating interview sessions and interacting with a candidate
- Question generation module (mock + hooks for LangChain/OpenAI/Anthropic)
- Simple evaluation module (heuristic + LLM hooks)
- Local storage and PDF/JSON export
- Config / prompts ready for extension

Getting started
1. Create a Python 3.10+ environment and install requirements

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Optionally set API keys for OpenAI or Anthropic in environment variables

```powershell
$env:OPENAI_API_KEY = "sk-..."
$env:ANTHROPIC_API_KEY = "..."
```

3. Run the Streamlit app locally

```powershell
streamlit run app.py
```

Deployment
- Streamlit Community Cloud works well: push this repository, configure secret env vars for API keys (OPENAI_API_KEY / ANTHROPIC_API_KEY) in the app settings and deploy.

Extending the project
- Replace mock implementations in `agent/question_bank.py` and `agent/evaluator.py` with LangChain + LLM calls for higher quality generation and scoring.
- Add ChromaDB / Pinecone integration (RAG) in `agent/question_bank.py`.
- Swap storage for Supabase or Google Sheets by implementing adapters in `utils/storage.py`.

License
MIT
