# Chatrio Backend

Asynchronous FastAPI backend for Chatrio AI WhatsApp Order & Support SaaS.

## Getting Started

1. Create virtual environment:
   ```bash
   uv venv
   ```
2. Install dependencies:
   ```bash
   uv pip install -e ".[dev]"
   ```
3. Run tests:
   ```bash
   .venv\Scripts\pytest -v
   ```
4. Start development server:
   ```bash
   .venv\Scripts\uvicorn app.main:app --reload
   ```
