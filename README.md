# Telco Churn MySQL + AI Agent

This project connects VS Code Python code directly to MySQL and then uses a LangChain SQL agent to answer questions from the live database.

## Setup

1. Create a virtual environment in VS Code.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and fill in your values.
4. Make sure your MySQL database already exists and contains your Telco churn tables.
5. If your MySQL extension connects with `127.0.0.1`, use the same host in `.env` so Python matches the working connection.

## Test the MySQL connection

Run:

```bash
python database_test.py
```

If the connection is correct, you should see a success message plus the database name and MySQL version.

## Ask questions with the AI agent

Run:

```bash
python ai_agent.py
```

You can also import `ask_question()` in another script and pass your own natural-language question.

The sample question in `ai_agent.py` now uses a fast SQL path for common analytics questions, so it can answer directly from MySQL without consuming a Gemini request. Repeated questions are cached in `.ai_agent_cache.json`.

## Environment variables

- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`
- `GOOGLE_API_KEY`
- `GOOGLE_MODEL`