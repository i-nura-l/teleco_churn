# Telco Churn MySQL + Groq SQL Agent

This project connects VS Code Python code directly to MySQL and then uses a LangChain SQL agent powered by Groq to answer questions from the live database.

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

For a notebook workflow, open `teleco_churn_qna.ipynb` and run the question cell there.

## Run the local chat API

Start the API server:

```bash
uvicorn chat_api:app --reload
```

API endpoints:

- `GET /health`
- `POST /chat` with JSON body: `{ "question": "your question" }`

## GitHub Pages chat UI

The `docs/` folder contains a static dashboard-plus-chat frontend that can be deployed to GitHub Pages.

1. Push this repository to GitHub.
2. In repository settings, enable Pages and set source to `Deploy from branch`.
3. Choose branch `main` and folder `/docs`.
4. Open the published Pages URL.
5. Set `API Base URL` in the UI to your deployed API endpoint.

Important: GitHub Pages can only host static files, so the Python API must run somewhere else (for example Render, Railway, Fly.io, Azure, or your own server).

The frontend uses `GET /health`, `GET /stats`, and `POST /chat` from `chat_api.py`.

## Environment variables

- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`
- `GROQ_API_KEY`
- `GROQ_MODEL`