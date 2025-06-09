import json
import os
import pymysql

# --- Konfigurasi Database dari Environment Variables ---
DB_HOST     = os.environ.get('DB_HOST')
DB_USER     = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME     = os.environ.get('DB_NAME')
DB_PORT     = int(os.environ.get('DB_PORT', 3306))

def get_db_connection():
    try:
        return pymysql.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASSWORD,
            database=DB_NAME, port=DB_PORT,
            cursorclass=pymysql.cursors.DictCursor
        )
    except Exception as e:
        print(f"DB connection error: {e}")
        raise

def initialize_db():
    conn = get_db_connection()
    try:
        with conn.cursor() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    due_date DATE,
                    priority VARCHAR(50),
                    completed BOOLEAN DEFAULT FALSE
                );
            """)
            c.execute("SELECT COUNT(*) AS cnt FROM tasks;")
            if c.fetchone()['cnt'] == 0:
                dummy = [
                    ("Belajar GoLang","Selesai tutorial","2025-06-15","High",False),
                    ("Laporan Bulanan","Data penjualan Q2","2025-06-20","High",False),
                ]
                c.executemany(
                    "INSERT INTO tasks (title,description,due_date,priority,completed) VALUES (%s,%s,%s,%s,%s);",
                    dummy
                )
                conn.commit()
    finally:
        conn.close()

def get_all_tasks():
    conn = get_db_connection()
    try:
        with conn.cursor() as c:
            c.execute("SELECT * FROM tasks ORDER BY id DESC;")
            tasks = c.fetchall()
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(tasks, default=str)
        }
    finally:
        conn.close()

def create_task(body):
    data = json.loads(body)
    if not data.get('title'):
        return {'statusCode':400,'headers':{'Content-Type':'application/json','Access-Control-Allow-Origin':'*'},'body':json.dumps({'message':'Title is required'})}
    conn = get_db_connection()
    try:
        with conn.cursor() as c:
            c.execute(
                "INSERT INTO tasks (title,description,due_date,priority,completed) VALUES (%s,%s,%s,%s,%s);",
                (data['title'], data.get('description'), data.get('due_date'), data.get('priority'), data.get('completed', False))
            )
            conn.commit()
            new_id = c.lastrowid
        return {
            'statusCode': 201,
            'headers': {'Content-Type':'application/json','Access-Control-Allow-Origin':'*'},
            'body': json.dumps({'id': new_id})
        }
    finally:
        conn.close()

def update_task(task_id, body):
    data = json.loads(body)
    conn = get_db_connection()
    try:
        with conn.cursor() as c:
            c.execute("SELECT * FROM tasks WHERE id=%s;", (task_id,))
            existing = c.fetchone()
            if not existing:
                return {'statusCode':404,'headers':{'Content-Type':'application/json','Access-Control-Allow-Origin':'*'},'body':json.dumps({'message':'Not found'})}
            # fill fields
            title       = data.get('title', existing['title'])
            description = data.get('description', existing['description'])
            due_date    = data.get('due_date', str(existing['due_date']))
            priority    = data.get('priority', existing['priority'])
            completed   = data.get('completed', existing['completed'])
            c.execute(
                "UPDATE tasks SET title=%s,description=%s,due_date=%s,priority=%s,completed=%s WHERE id=%s;",
                (title, description, due_date, priority, completed, task_id)
            )
            conn.commit()
        return {'statusCode':200,'headers':{'Content-Type':'application/json','Access-Control-Allow-Origin':'*'},'body':json.dumps({'message':'OK'})}
    finally:
        conn.close()

def delete_task(task_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as c:
            c.execute("DELETE FROM tasks WHERE id=%s;", (task_id,))
            conn.commit()
            if c.rowcount == 0:
                return {'statusCode':404,'headers':{'Content-Type':'application/json','Access-Control-Allow-Origin':'*'},'body':json.dumps({'message':'Not found'})}
        return {'statusCode':204,'headers':{'Content-Type':'application/json','Access-Control-Allow-Origin':'*'},'body':''}
    finally:
        conn.close()

def lambda_handler(event, context):
    # event['path'] bisa mengandung stage prefix => ambil bagian sesudah domain
    path = event.get('rawPath') or event.get('path') or ''
    method = event.get('httpMethod')
    body   = event.get('body') or ''
    initialize_db()

    parts = [p for p in path.split('/') if p]
    # /tasks
    if len(parts) == 1 and parts[0] == 'tasks':
        if method == 'GET':
            return get_all_tasks()
        if method == 'POST':
            return create_task(body)
    # /tasks/{id}
    if len(parts) == 2 and parts[0] == 'tasks':
        try:
            tid = int(parts[1])
        except:
            return {'statusCode':400,'headers':{'Content-Type':'application/json','Access-Control-Allow-Origin':'*'},'body':json.dumps({'message':'Invalid ID'})}
        if method == 'PUT':
            return update_task(tid, body)
        if method == 'DELETE':
            return delete_task(tid)
    # CORS preflight
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': ''
        }
    return {'statusCode':404,'headers':{'Content-Type':'application/json','Access-Control-Allow-Origin':'*'},'body':json.dumps({'message':'Not Found'})}
