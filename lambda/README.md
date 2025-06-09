## CREATE LAYER
- create python folder
```
mkdir python
```
- create virtual environment
```
python3 -m venv venv
```
atau
```
python -m venv venv
```
- Activcate virtual environment folder
On Linux/macOS
```
source venv/bin/activate
```
On Windows (PowerShell)
```
.\venv\Scripts\activate
```
- Install pymysql
```
pip install pymysql -t python/
```
- Compress the python folder containing pymysql
```
zip -r layer.zip python/
```

# 📝 AWS Lambda Task API (Python Backend)

## 🔧 Supported Endpoints

| Method | Path           | Description              |
|--------|----------------|--------------------------|
| GET    | `/tasks`       | Get all tasks            |
| GET    | `/tasks/{id}`  | Get task by ID           |
| POST   | `/tasks`       | Create a new task        |
| PUT    | `/tasks/{id}`  | Update a task by ID      |
| DELETE | `/tasks/{id}`  | Delete a task by ID      |

---

## 📥 Environment Variables

Set these in your Lambda function:

```bash
DB_HOST=<your-mysql-host>
DB_USER=<your-mysql-user>
DB_PASSWORD=<your-mysql-password>
DB_NAME=todoapp
DB_PORT=3306
```

---

## 🚀 Lambda Test Events

### 📌 1. Get all tasks

```json
{
  "httpMethod": "GET",
  "path": "/tasks"
}
```

### 📌 2. Get task by ID

```json
{
  "httpMethod": "GET",
  "path": "/tasks/1"
}
```

### 📌 3. Create task

```json
{
  "httpMethod": "POST",
  "path": "/tasks",
  "body": "{\"title\": \"Ngoding GoLang\", \"description\": \"Belajar struct dan interface\", \"due_date\": \"2025-06-30\", \"priority\": \"Medium\", \"completed\": false}"
}
```

### 📌 4. Update task

```json
{
  "httpMethod": "PUT",
  "path": "/tasks/1",
  "body": "{\"title\": \"Ngoding GoLang Updated\", \"description\": \"Revisi belajar Go\", \"priority\": \"High\", \"completed\": true}"
}
```

### 📌 5. Delete task

```json
{
  "httpMethod": "DELETE",
  "path": "/tasks/1"
}
```

---

## 📫 Postman Examples

### ✅ Headers (for all requests)
```
Content-Type: application/json
```

### 🔍 1. GET All Tasks

- **Method**: GET  
- **URL**: `https://<your-api-url>/tasks`

### 🔍 2. GET Task by ID

- **Method**: GET  
- **URL**: `https://<your-api-url>/tasks/1`

### 📝 3. POST Create Task

- **Method**: POST  
- **URL**: `https://<your-api-url>/tasks`  
- **Body (JSON)**:
```json
{
  "title": "Ngoding GoLang",
  "description": "Belajar struct dan interface",
  "due_date": "2025-06-30",
  "priority": "Medium",
  "completed": false
}
```

### ✏️ 4. PUT Update Task

- **Method**: PUT  
- **URL**: `https://<your-api-url>/tasks/1`  
- **Body (JSON)**:
```json
{
  "title": "Ngoding GoLang Updated",
  "description": "Revisi belajar Go",
  "priority": "High",
  "completed": true
}
```

### ❌ 5. DELETE Task

- **Method**: DELETE  
- **URL**: `https://<your-api-url>/tasks/1`

---

## 📎 Notes

- Replace `<your-api-url>` with your actual endpoint from API Gateway or ALB.
- `due_date` must be in format `YYYY-MM-DD`.
- `completed` should be `true` or `false`.