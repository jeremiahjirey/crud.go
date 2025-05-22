# DEPENDENCY
## Download 
```
go mod tidy
```

# INVOKE
## GET
```
{
  "httpMethod": "GET",
  "path": "/tasks"
}
```

## POST
```
{
  "httpMethod": "POST",
  "path": "/tasks",
  "body": "{\"title\":\"Belajar Golang\",\"description\":\"Pelajari dasar-dasar Golang\",\"due_date\":\"2025-06-01\",\"priority\":\"tinggi\"}"
}
```

## PUT
```
{
  "httpMethod": "PUT",
  "path": "/tasks/1",
  "pathParameters": {
    "id": "1"
  },
  "body": "{\"title\":\"Belajar Golang\",\"description\":\"Pelajari concurrency\",\"due_date\":\"2025-06-03\",\"priority\":\"tinggi\",\"completed\":true}"
}
```

## DELETE
```
{
  "httpMethod": "DELETE",
  "path": "/tasks/1",
  "pathParameters": {
    "id": "1"
  }
}
```

