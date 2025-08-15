from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect
import pandas as pd
import sqlite3
import io
import json
from tools.gemini_agent import prompt_to_sql
from tools.db_executor import execute_sql
from tabulate import tabulate
from fastapi.responses import JSONResponse
import os


app = FastAPI()

# Always use a single fixed table name
FIXED_TABLE_NAME = "Table1"
uploaded_columns = []

def map_dtype(dtype):
    if pd.api.types.is_integer_dtype(dtype):
        return "INTEGER"
    elif pd.api.types.is_float_dtype(dtype):
        return "REAL"
    else:
        return "TEXT"

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    global uploaded_columns

    try:
        if not (file.filename.endswith(".csv") or file.filename.endswith((".xls", ".xlsx"))):
            return JSONResponse(status_code=400, content={"error": "Only CSV or Excel files allowed"})

        contents = await file.read()

        try:
            if file.filename.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(contents))
            else:
                df = pd.read_excel(io.BytesIO(contents))
        except Exception as e:
            return JSONResponse(status_code=400, content={"error": f"Error reading file: {str(e)}"})

        if df.empty:
            return JSONResponse(status_code=400, content={"error": "Uploaded file is empty"})

        # Ensure database folder exists
        os.makedirs("database", exist_ok=True)

        conn = sqlite3.connect("database/mcp_data.db")
        cur = conn.cursor()

        # Drop the fixed table if exists
        cur.execute(f'DROP TABLE IF EXISTS "{FIXED_TABLE_NAME}"')

        # Create table dynamically
        columns_with_types = []
        for col in df.columns:
            dtype = map_dtype(df[col].dtype)
            columns_with_types.append(f'"{col}" {dtype}')

        create_table_sql = f'CREATE TABLE "{FIXED_TABLE_NAME}" ({", ".join(columns_with_types)})'
        cur.execute(create_table_sql)

        # Insert rows
        placeholders = ", ".join(["?"] * len(df.columns))
        insert_sql = f'INSERT INTO "{FIXED_TABLE_NAME}" ({", ".join([f"""\"{col}\"""" for col in df.columns])}) VALUES ({placeholders})'

        data = []
        for row in df.itertuples(index=False, name=None):
            data.append(tuple(None if pd.isna(x) else x for x in row))

        cur.executemany(insert_sql, data)
        conn.commit()
        conn.close()

        # Update global columns
        uploaded_columns = list(df.columns)

        return JSONResponse(content={"message": f"Uploaded {len(df)} rows into table '{FIXED_TABLE_NAME}'"})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Internal server error: {str(e)}"})

def format_sql(sql_query):
    if sql_query.startswith("```"):
        sql_query = sql_query.strip("```").strip()
        if sql_query.lower().startswith("sql"):
            sql_query = sql_query[3:].strip()
    return sql_query

def print_result(result):
    rows = result.get('result', [])
    if rows and isinstance(rows, list):
        table = tabulate(rows, headers="keys", tablefmt='grid')
        print(table)
    else:
        print("No data found")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    global uploaded_columns

    try:
        while True:
            data = await websocket.receive_text()
            mcp = json.loads(data)

            if mcp.get("command") == "chat_to_sql":
                user_prompt = mcp.get("message", "")

                if not uploaded_columns:
                    await websocket.send_text(json.dumps({"error": "No uploaded table available. Please upload a file first."}))
                    continue

                # Always generate SQL for fixed table
                sql = prompt_to_sql(user_prompt, FIXED_TABLE_NAME, uploaded_columns)
                sql = format_sql(sql)
                print(f"Generated SQL:\n{sql}")

                result = execute_sql(sql)
                print_result(result)

                await websocket.send_text(json.dumps({
                    "sql_query": sql,
                    "data": result
                }))
            else:
                await websocket.send_text(json.dumps({"error": "Unknown command"}))

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        await websocket.send_text(json.dumps({"error": f"Internal server error: {str(e)}"}))