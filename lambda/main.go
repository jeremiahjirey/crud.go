// main.go
package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"strconv"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
	_ "github.com/go-sql-driver/mysql"
	"github.com/joho/godotenv"
)

type Task struct {
	ID          int    `json:"id"`
	Title       string `json:"title"`
	Description string `json:"description"`
	DueDate     string `json:"due_date"`
	Priority    string `json:"priority"`
	Completed   bool   `json:"completed"`
}

var db *sql.DB

func init() {
	_ = godotenv.Load()
	dsn := fmt.Sprintf("%s:%s@tcp(%s:%s)/%s",
		os.Getenv("DB_USER"),
		os.Getenv("DB_PASS"),
		os.Getenv("DB_HOST"),
		os.Getenv("DB_PORT"),
		os.Getenv("DB_NAME"),
	)
	var err error
	db, err = sql.Open("mysql", dsn)
	if err != nil {
		panic(err)
	}
}

func handler(ctx context.Context, req events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
	switch req.HTTPMethod {
	case "GET":
		return handleGet(req)
	case "POST":
		return handlePost(req)
	case "PUT":
		return handlePut(req)
	case "DELETE":
		return handleDelete(req)
	default:
		return events.APIGatewayProxyResponse{StatusCode: 405}, nil
	}
}

func handleGet(req events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
	rows, err := db.Query("SELECT id, title, description, due_date, priority, completed FROM tasks")
	if err != nil {
		return serverError(err)
	}
	defer rows.Close()

	tasks := []Task{}
	for rows.Next() {
		t := Task{}
		var completed int
		_ = rows.Scan(&t.ID, &t.Title, &t.Description, &t.DueDate, &t.Priority, &completed)
		t.Completed = completed == 1
		tasks = append(tasks, t)
	}

	resp, _ := json.Marshal(tasks)
	return events.APIGatewayProxyResponse{StatusCode: 200, Body: string(resp)}, nil
}

func handlePost(req events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
	t := Task{}
	_ = json.Unmarshal([]byte(req.Body), &t)
	_, err := db.Exec("INSERT INTO tasks (title, description, due_date, priority, completed) VALUES (?, ?, ?, ?, 0)", t.Title, t.Description, t.DueDate, t.Priority)
	if err != nil {
		return serverError(err)
	}
	return events.APIGatewayProxyResponse{StatusCode: 201}, nil
}

func handlePut(req events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
	id, _ := strconv.Atoi(req.PathParameters["id"])
	t := Task{}
	_ = json.Unmarshal([]byte(req.Body), &t)
	completed := 0
	if t.Completed {
		completed = 1
	}
	_, err := db.Exec("UPDATE tasks SET title=?, description=?, due_date=?, priority=?, completed=? WHERE id=?",
		t.Title, t.Description, t.DueDate, t.Priority, completed, id)
	if err != nil {
		return serverError(err)
	}
	return events.APIGatewayProxyResponse{StatusCode: 200}, nil
}

func handleDelete(req events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
	id, _ := strconv.Atoi(req.PathParameters["id"])
	_, err := db.Exec("DELETE FROM tasks WHERE id=?", id)
	if err != nil {
		return serverError(err)
	}
	return events.APIGatewayProxyResponse{StatusCode: 200}, nil
}

func serverError(err error) (events.APIGatewayProxyResponse, error) {
	return events.APIGatewayProxyResponse{StatusCode: 500, Body: err.Error()}, nil
}

func main() {
	lambda.Start(handler)
}
