// main.go
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"html/template"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"strings"

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
	tmpl         = template.Must(template.ParseFiles("template.html"))
	apiGatewayURL string
	listenPort    string
)

func init() {
	err := godotenv.Load()
	if err != nil {
		log.Fatal("Error loading .env file")
	}
	apiGatewayURL = os.Getenv("API_GATEWAY_URL")
	listenPort = os.Getenv("PORT")
	if listenPort == "" {
		listenPort = "8080"
	}
}

func main() {
	http.HandleFunc("/", handleIndex)
	http.HandleFunc("/add", handleAdd)
	http.HandleFunc("/update", handleUpdate)
	http.HandleFunc("/delete", handleDelete)
	fmt.Println("Server started at :" + listenPort)
	http.ListenAndServe(":"+listenPort, nil)
}

func handleIndex(w http.ResponseWriter, r *http.Request) {
	resp, err := http.Get(apiGatewayURL + "/tasks")
	if err != nil {
		http.Error(w, "Failed to fetch tasks", http.StatusInternalServerError)
		return
	}
	defer resp.Body.Close()
	body, _ := ioutil.ReadAll(resp.Body)

	var tasks []Task
	json.Unmarshal(body, &tasks)

	tmpl.Execute(w, tasks)
}

func handleAdd(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Redirect(w, r, "/", http.StatusSeeOther)
		return
	}
	task := Task{
		Title:       r.FormValue("title"),
		Description: r.FormValue("description"),
		DueDate:     r.FormValue("due_date"),
		Priority:    r.FormValue("priority"),
	}
	data, _ := json.Marshal(task)
	http.Post(apiGatewayURL+"/tasks", "application/json", bytes.NewBuffer(data))
	http.Redirect(w, r, "/", http.StatusSeeOther)
}

func handleUpdate(w http.ResponseWriter, r *http.Request) {
	id := r.FormValue("id")
	task := Task{
		ID:          stringToInt(id),
		Title:       r.FormValue("title"),
		Description: r.FormValue("description"),
		DueDate:     r.FormValue("due_date"),
		Priority:    r.FormValue("priority"),
		Completed:   r.FormValue("completed") == "on",
	}
	data, _ := json.Marshal(task)
	req, _ := http.NewRequest(http.MethodPut, apiGatewayURL+"/tasks/"+id, bytes.NewBuffer(data))
	req.Header.Set("Content-Type", "application/json")
	http.DefaultClient.Do(req)
	http.Redirect(w, r, "/", http.StatusSeeOther)
}

func handleDelete(w http.ResponseWriter, r *http.Request) {
	id := r.URL.Query().Get("id")
	req, _ := http.NewRequest(http.MethodDelete, apiGatewayURL+"/tasks/"+id, nil)
	http.DefaultClient.Do(req)
	http.Redirect(w, r, "/", http.StatusSeeOther)
}

func stringToInt(s string) int {
	i := 0
	fmt.Sscanf(s, "%d", &i)
	return i
}
