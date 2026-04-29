from functools import lru_cache

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError

from ai_agent import ask_question
from db_config import get_database_url


ENGINE = create_engine(get_database_url())
JOINED_FROM = """
FROM billing b
JOIN contracts c ON c.customerID = b.customerID
JOIN internet_services i ON i.customerID = b.customerID
JOIN customers cu ON cu.customerID = b.customerID
JOIN phone_services p ON p.customerID = b.customerID
"""


class StatCard(BaseModel):
    label: str
    value: float | int
    suffix: str = ""


class CategoryStat(BaseModel):
    label: str
    customers: int
    churn_rate: float
    avg_monthly_charges: float | None = None


class DashboardStats(BaseModel):
    cards: list[StatCard]
    internet_service: list[CategoryStat]
    contract: list[CategoryStat]
    tenure_band: list[CategoryStat]
    top_risk_segment: str


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    output: str


def _fetch_one(query: str) -> dict:
    with ENGINE.connect() as connection:
        row = connection.execute(text(query)).mappings().first()
        return dict(row) if row else {}


def _fetch_all(query: str) -> list[dict]:
    with ENGINE.connect() as connection:
        rows = connection.execute(text(query)).mappings().all()
        return [dict(row) for row in rows]


@lru_cache(maxsize=1)
def _validate_schema() -> None:
    inspector = inspect(ENGINE)
    required_tables = ["billing", "contracts", "customers", "internet_services", "phone_services"]
    missing_tables = [table for table in required_tables if table not in inspector.get_table_names()]
    if missing_tables:
        raise RuntimeError(f"Missing expected tables: {', '.join(missing_tables)}")


def _category_query(group_expression: str) -> str:
    return f"""
    SELECT
        COALESCE({group_expression}, 'Unknown') AS label,
        COUNT(*) AS customers,
        AVG(CASE WHEN b.Churn = 'Yes' THEN 1 ELSE 0 END) AS churn_rate,
        AVG(b.MonthlyCharges) AS avg_monthly_charges
    {JOINED_FROM}
    GROUP BY label
    ORDER BY churn_rate DESC, customers DESC
    """


def _tenure_band_query() -> str:
    return """
    SELECT
        CASE
            WHEN b.tenure < 12 THEN 'Under 12 months'
            WHEN b.tenure < 24 THEN '12-23 months'
            WHEN b.tenure < 36 THEN '24-35 months'
            ELSE '36+ months'
        END AS label,
        COUNT(*) AS customers,
        AVG(CASE WHEN b.Churn = 'Yes' THEN 1 ELSE 0 END) AS churn_rate,
        AVG(b.MonthlyCharges) AS avg_monthly_charges
    FROM billing b
    JOIN contracts c ON c.customerID = b.customerID
    JOIN internet_services i ON i.customerID = b.customerID
    JOIN customers cu ON cu.customerID = b.customerID
    JOIN phone_services p ON p.customerID = b.customerID
    GROUP BY label
    ORDER BY MIN(b.tenure)
    """


def get_dashboard_stats() -> DashboardStats:
    _validate_schema()

    summary = _fetch_one(
        f"""
        SELECT
            COUNT(DISTINCT b.customerID) AS total_customers,
            AVG(CASE WHEN b.Churn = 'Yes' THEN 1 ELSE 0 END) AS churn_rate,
            AVG(b.MonthlyCharges) AS avg_monthly_charges,
            AVG(b.tenure) AS avg_tenure
        {JOINED_FROM}
        """
    )
    internet_service_rows = _fetch_all(_category_query("i.InternetService"))
    contract_rows = _fetch_all(_category_query("c.Contract"))
    tenure_rows = _fetch_all(_tenure_band_query())

    top_risk_segment = "No segment found"
    combined_segments = internet_service_rows + contract_rows + tenure_rows
    if combined_segments:
        worst_segment = max(combined_segments, key=lambda row: row["churn_rate"])
        top_risk_segment = f"{worst_segment['label']} ({worst_segment['churn_rate']:.1%} churn)"

    return DashboardStats(
        cards=[
            StatCard(label="Total customers", value=int(summary.get("total_customers", 0))),
            StatCard(label="Churn rate", value=float(summary.get("churn_rate", 0.0)) * 100, suffix="%"),
            StatCard(label="Avg monthly charges", value=float(summary.get("avg_monthly_charges", 0.0)), suffix="$"),
            StatCard(label="Avg tenure", value=float(summary.get("avg_tenure", 0.0)), suffix=" months"),
        ],
        internet_service=[CategoryStat(**row) for row in internet_service_rows],
        contract=[CategoryStat(**row) for row in contract_rows],
        tenure_band=[CategoryStat(**row) for row in tenure_rows],
        top_risk_segment=top_risk_segment,
    )


app = FastAPI(title="Telco Churn Chat API", version="1.0.0")

# GitHub Pages is served from a different origin, so CORS is required.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/stats", response_model=DashboardStats)
def stats() -> DashboardStats:
    try:
        return get_dashboard_stats()
    except (SQLAlchemyError, RuntimeError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        answer = ask_question(question)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ChatResponse(output=answer)
