import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()  # Load environment variables from .env

model = ChatGoogleGenerativeAI(
    model="models/gemini-2.5-pro",
    temperature=0.2,
    google_api_key=os.environ["GEMINI_API_KEY"]
)


def prompt_to_sql(user_prompt: str, table_name: str, columns: list[str]) -> str:
    columns_str = ", ".join(columns)
    prompt_template = ChatPromptTemplate.from_template(f"""
    Convert the following prompt into an SQL query (SQLite syntax only).
    Prompt: "{{user_input}}"
    Table: {table_name}({columns_str})

    Return only the SQL query.
    """)

    chain = prompt_template | model
    result = chain.invoke({"user_input": user_prompt})

    return result.content.strip().strip(';')


# print(prompt_to_sql("print all the data in the table"))