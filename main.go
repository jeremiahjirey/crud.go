package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"html/template"
	"net/http"
	"os"
	"strconv"

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

var (
	tmpl          *template.Template
	apiGatewayURL string
	listenPort    string
)

func init() {
	_ = godotenv.Load()
	apiGatewayURL = os.Getenv("API_GATEWAY_URL")
	if apiGatewayURL == "" {
		fmt.Println("ERROR: API_GATEWAY_URL is not set")
		os.Exit(1)
	}
	listenPort = os.Getenv("PORT")
	if listenPort == "" {
		listenPort = "8080"
	}
	tmpl = template.Must(template.ParseFiles("template.html"))
}

func main() {
	http.HandleFunc("/", handleIndex)
	http.HandleFunc("/healthz", handleHealthz) // ✅ health check endpoint
	http.HandleFunc("/create", handleCreate)
	http.HandleFunc("/update", handleUpdate)
	http.HandleFunc("/delete", handleDelete)
	fmt.Println("Server listening on :" + listenPort)
	http.ListenAndServe(":"+listenPort, nil)
}

func handleHealthz(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	w.Write([]byte("OK"))
}

func handleIndex(w http.ResponseWriter, r *http.Request) {
	resp, err := http.Get(apiGatewayURL + "/tasks")
	if err != nil {
		http.Error(w, "Failed to fetch tasks: "+err.Error(), http.StatusInternalServerError)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		var errObj map[string]interface{}
		json.NewDecoder(resp.Body).Decode(&errObj)
		http.Error(w, fmt.Sprintf("Backend error (%d): %v", resp.StatusCode, errObj), resp.StatusCode)
		return
	}

	var tasks []Task
	if err := json.NewDecoder(resp.Body).Decode(&tasks); err != nil {
		http.Error(w, "Invalid task data: "+err.Error(), http.StatusInternalServerError)
		return
	}
	tmpl.Execute(w, tasks)
}

func handleCreate(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Redirect(w, r, "/", http.StatusSeeOther)
		return
	}
	r.ParseForm()
	task := map[string]interface{}{
		"title":       r.FormValue("title"),
		"description": r.FormValue("description"),
		"due_date":    r.FormValue("due_date"),
		"priority":    r.FormValue("priority"),
	}
	postJSON("/tasks", task)
	http.Redirect(w, r, "/", http.StatusSeeOther)
}

func handleUpdate(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Redirect(w, r, "/", http.StatusSeeOther)
		return
	}
	r.ParseForm()
	id := r.FormValue("id")
	parsedID := parseInt(id)
	task := map[string]interface{}{
		"title":       r.FormValue("title"),
		"description": r.FormValue("description"),
		"due_date":    r.FormValue("due_date"),
		"priority":    r.FormValue("priority"),
		"completed":   r.FormValue("completed") == "on",
	}
	putJSON("/tasks/"+strconv.Itoa(parsedID), task)
	http.Redirect(w, r, "/", http.StatusSeeOther)
}

func handleDelete(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Redirect(w, r, "/", http.StatusSeeOther)
		return
	}
	id := r.FormValue("id")
	req, _ := http.NewRequest(http.MethodDelete, apiGatewayURL+"/tasks/"+id, nil)
	http.DefaultClient.Do(req)
	http.Redirect(w, r, "/", http.StatusSeeOther)
}

func postJSON(path string, data interface{}) {
	buf := new(bytes.Buffer)
	json.NewEncoder(buf).Encode(data)
	http.Post(apiGatewayURL+path, "application/json", buf)
}

func putJSON(path string, data interface{}) {
	buf := new(bytes.Buffer)
	json.NewEncoder(buf).Encode(data)
	req, _ := http.NewRequest(http.MethodPut, apiGatewayURL+path, buf)
	req.Header.Set("Content-Type", "application/json")
	http.DefaultClient.Do(req)
}

func parseInt(s string) int {
	if n, err := strconv.Atoi(s); err == nil {
		return n
	}
	return 0
}
