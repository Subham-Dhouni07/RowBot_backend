import sqlite3

def setup_sample_db():
    conn = sqlite3.connect("database/mcp_data.db")
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            age INTEGER,
            city TEXT
        )
    ''')
    cur.executemany('INSERT INTO users (name, age, city) VALUES (?, ?, ?)', [
        ('Alice', 25, 'New York'),
        ('Subham', 23, 'Champawat'),
        ('Bob', 32, 'Delhi'),
        ('Carol', 40, 'London')
    ])
    conn.commit()
    conn.close()


if __name__ == "__main__":
    setup_sample_db()
