from tools.gemini_agent import prompt_to_sql
from tools.db_executor import execute_sql

async def handle_message(websocket, path):
    async for message in websocket:
        try:
            import json
            mcp = json.loads(message)
            if mcp.get("command") == "chat_to_sql":
                user_prompt = mcp["message"]
                sql = prompt_to_sql(user_prompt)
                result = execute_sql(sql)
                await websocket.send(json.dumps({
                    "sql_query": sql,
                    "data": result
                }))
        except Exception as e:
            await websocket.send(json.dumps({"error": str(e)}))
