# AI Data Analysis Assistant

A CSV/Excel analysis application built with Python, Pandas, LangChain and Streamlit. It turns a natural-language question into a validated query plan, executes the plan locally and produces tables, charts and downloadable reports.

**Author:** Mert Nusret Sağlam

## Features

- CSV and XLSX loading with data-quality checks and parsing controls.
- Optional OpenAI-backed LangChain planner with Pydantic output validation.
- Local filtering, grouping, aggregation, sorting and row selection in Pandas.
- Matplotlib charts and CSV, JSON, PNG and HTML exports.
- API-free demo with six explicit question presets and artificial sales data.
- Thirteen automated tests, including Streamlit UI flow and a mocked HTTP integration with the real LangChain pipeline.

The model generates a plan rather than executable Python or SQL. Column names, question text and data types are sent to the API in LLM mode; raw dataset rows and computed results are not sent. Users review the plan before running it in the UI.

## Quick start on Windows

From the repository root:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe smoke_test.py
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Start in Demo mode with the bundled sample. Expected total revenue: **20,800**; Istanbul **8,000**, Ankara **6,500**, Izmir **6,300**.

For free-form questions, copy `.env.example` to `.env`, configure your own API key locally and select LLM mode. API calls may incur charges. Never commit `.env` or a real API key.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Scope

Supported operations are explicitly constrained. This version does not perform forecasting, joins, derived-column calculations or arbitrary code execution. A valid plan may still misunderstand a question; inspect its columns, filters and operation before accepting the result. The demo uses fixed presets and does not run a language model.

No LLM accuracy benchmark is claimed. The integration test uses a controlled HTTP response rather than a paid live model call. See [README_TR.md](README_TR.md) for detailed Turkish instructions and [VALIDATION.md](VALIDATION.md) for test scope.
