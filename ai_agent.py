import os

from dotenv import load_dotenv
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from sqlalchemy.exc import SQLAlchemyError

from db_config import get_database_url


load_dotenv()


def build_agent():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Set GOOGLE_API_KEY in your environment or .env file.")

    database = SQLDatabase.from_uri(get_database_url())
    llm = ChatGoogleGenerativeAI(
        model=os.getenv("GOOGLE_MODEL", "gemini-2.5-flash"),
        temperature=0,
        google_api_key=api_key,
    )

    return create_sql_agent(llm=llm, db=database, verbose=True)


def ask_question(question: str) -> str:
    agent = build_agent()
    response = agent.invoke({"input": question})

    if isinstance(response, dict):
        return str(response.get("output", response))

    return str(response)


def main() -> None:
    question = "How many customers do we have in total?"
    try:
        answer = ask_question(question)
        print(answer)
    except SQLAlchemyError as exc:
        print("Could not build the agent because the MySQL connection failed.")
        print("Check MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, and MYSQL_DATABASE.")
        print(f"Details: {exc}")
    except Exception as exc:
        print(f"AI agent failed: {exc}")


if __name__ == "__main__":
    main()