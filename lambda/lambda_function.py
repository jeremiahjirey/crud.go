import json
import os
import pymysql
from datetime import datetime

# --- Konfigurasi Database dari Environment Variables ---
DB_HOST = os.environ.get('DB_HOST')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME = os.environ.get('DB_NAME')
DB_PORT = int(os.environ.get('DB_PORT', 3306)) # Default ke 3306 jika tidak diset

# --- Fungsi untuk Koneksi Database ---
def get_db_connection():
    """Membuka koneksi ke database MySQL."""
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT, 
            cursorclass=pymysql.cursors.DictCursor # Mengembalikan hasil sebagai dictionary
        )
        print("Successfully connected to the database.")
        return conn
    except Exception as e:
        print(f"ERROR: Could not connect to database: {e}")
        raise e

# --- Fungsi untuk Inisialisasi Tabel dan Data Dummy ---
def initialize_db():
    """Membuat tabel 'tasks' jika belum ada dan mengisi data dummy."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Buat tabel tasks
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS tasks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                due_date DATE,
                priority VARCHAR(50),
                completed BOOLEAN DEFAULT FALSE
            );
            """
            cursor.execute(create_table_sql)
            print("Table 'tasks' checked/created.")

            # Periksa apakah tabel kosong, jika ya, isi data dummy
            cursor.execute("SELECT COUNT(*) FROM tasks;")
            result = cursor.fetchone()
            if result['COUNT(*)'] == 0:
                print("Table 'tasks' is empty. Inserting dummy data...")
                dummy_tasks = [
                    ("Belajar GoLang", "Selesaikan tutorial web Go", "2025-06-15", "High", False),
                    ("Buat Laporan Bulanan", "Kumpulkan data penjualan Q2", "2025-06-20", "High", False),
                    ("Olahraga Pagi", "Lari 5km di taman", "2025-06-05", "Medium", True),
                    ("Baca Buku 'Clean Code'", "Selesaikan bab 3 dan 4", "2025-06-30", "Low", False),
                    ("Rapat Tim", "Persiapan presentasi proyek baru", "2025-06-10", "High", False)
                ]
                insert_sql = """
                INSERT INTO tasks (title, description, due_date, priority, completed)
                VALUES (%s, %s, %s, %s, %s);
                """
                cursor.executemany(insert_sql, dummy_tasks)
                conn.commit()
                print("Dummy data inserted successfully.")
            else:
                print("Table 'tasks' already contains data. Skipping dummy data insertion.")
    except Exception as e:
        print(f"ERROR: Database initialization failed: {e}")
        raise e
    finally:
        if conn:
            conn.close()

# --- Fungsi Handler untuk Operasi CRUD ---

def get_all_tasks():
    """Mengambil semua tugas dari database."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM tasks ORDER BY id DESC;")
            tasks = cursor.fetchall()
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*' # Penting untuk CORS
                },
                'body': json.dumps(tasks, default=str) # default=str untuk handle objek Date
            }
    except Exception as e:
        print(f"Error fetching tasks: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'message': 'Internal Server Error', 'error': str(e)})
        }
    finally:
        if conn:
            conn.close()

def create_task(body):
    """Membuat tugas baru di database."""
    conn = None
    try:
        data = json.loads(body)
        title = data.get('title')
        description = data.get('description')
        due_date = data.get('due_date')
        priority = data.get('priority')
        completed = data.get('completed', False) # Default to False

        if not title:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'message': 'Title is required'})
            }

        conn = get_db_connection()
        with conn.cursor() as cursor:
            insert_sql = """
            INSERT INTO tasks (title, description, due_date, priority, completed)
            VALUES (%s, %s, %s, %s, %s);
            """
            cursor.execute(insert_sql, (title, description, due_date, priority, completed))
            conn.commit()
            return {
                'statusCode': 201,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'message': 'Task created successfully', 'id': cursor.lastrowid})
            }
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'message': 'Invalid JSON format'})
        }
    except Exception as e:
        print(f"Error creating task: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'message': 'Internal Server Error', 'error': str(e)})
        }
    finally:
        if conn:
            conn.close()

def update_task(task_id, body):
    """Memperbarui tugas yang ada di database."""
    conn = None
    try:
        data = json.loads(body)
        # Ambil semua field, gunakan nilai yang ada jika tidak disediakan
        title = data.get('title')
        description = data.get('description')
        due_date = data.get('due_date')
        priority = data.get('priority')
        completed = data.get('completed')

        if not task_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'message': 'Task ID is required'})
            }

        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Ambil data task yang sudah ada untuk mengisi field yang tidak diupdate
            cursor.execute("SELECT * FROM tasks WHERE id = %s;", (task_id,))
            existing_task = cursor.fetchone()

            if not existing_task:
                return {
                    'statusCode': 404,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'message': 'Task not found'})
                }

            # Gunakan nilai dari body jika ada, jika tidak, gunakan nilai yang sudah ada
            title = title if title is not None else existing_task['title']
            description = description if description is not None else existing_task['description']
            due_date = due_date if due_date is not None else str(existing_task['due_date']) # Convert date object to string
            priority = priority if priority is not None else existing_task['priority']
            completed = completed if completed is not None else existing_task['completed']

            update_sql = """
            UPDATE tasks SET title = %s, description = %s, due_date = %s, priority = %s, completed = %s
            WHERE id = %s;
            """
            cursor.execute(update_sql, (title, description, due_date, priority, completed, task_id))
            conn.commit()

            if cursor.rowcount == 0:
                # Ini bisa terjadi jika ID tidak ditemukan, tapi sudah dihandle di atas
                # Atau jika tidak ada perubahan data
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'message': 'No changes made or task not found'})
                }
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'message': 'Task updated successfully'})
            }
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'message': 'Invalid JSON format'})
        }
    except Exception as e:
        print(f"Error updating task: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'message': 'Internal Server Error', 'error': str(e)})
        }
    finally:
        if conn:
            conn.close()

def delete_task(task_id):
    """Menghapus tugas dari database."""
    conn = None
    try:
        if not task_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'message': 'Task ID is required'})
            }

        conn = get_db_connection()
        with conn.cursor() as cursor:
            delete_sql = "DELETE FROM tasks WHERE id = %s;"
            cursor.execute(delete_sql, (task_id,))
            conn.commit()

            if cursor.rowcount == 0:
                return {
                    'statusCode': 404,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'message': 'Task not found'})
                }
            return {
                'statusCode': 204, # No Content for successful deletion
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': "" # No content for 204
            }
    except Exception as e:
        print(f"Error deleting task: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'message': 'Internal Server Error', 'error': str(e)})
        }
    finally:
        if conn:
            conn.close()

# --- Fungsi Utama Lambda Handler ---
def lambda_handler(event, context):
    """
    Fungsi utama handler Lambda untuk memproses permintaan API Gateway.
    """
    print(f"Received event: {json.dumps(event)}")

    http_method = event.get('httpMethod')
    path = event.get('path')
    body = event.get('body')
    path_parameters = event.get('pathParameters')

    # Inisialisasi database pada setiap invokasi (atau bisa di-cache jika koneksi persistent)
    # Untuk demo, ini cukup aman. Untuk produksi, pertimbangkan koneksi persistent.
    try:
        initialize_db()
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'message': 'Database initialization failed', 'error': str(e)})
        }

    # Routing berdasarkan HTTP Method dan Path
    if path == '/tasks':
        if http_method == 'GET':
            return get_all_tasks()
        elif http_method == 'POST':
            return create_task(body)
    elif path and path.startswith('/tasks/'):
        # Ekstrak ID dari path
        try:
            task_id = int(path_parameters.get('id'))
        except (ValueError, TypeError):
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'message': 'Invalid Task ID'})
            }

        if http_method == 'PUT':
            return update_task(task_id, body)
        elif http_method == 'DELETE':
            return delete_task(task_id)

    # Handle OPTIONS method for CORS preflight requests
    if http_method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
            },
            'body': ''
        }

    return {
        'statusCode': 404,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({'message': 'Not Found'})
    }