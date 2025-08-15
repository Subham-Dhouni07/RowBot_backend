import sqlite3

def execute_sql(query):
    try:
        conn = sqlite3.connect("database/mcp_data.db")
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        return {"result": [dict(zip(columns, row)) for row in rows]}
    except Exception as e:
        return {"error": str(e)}
