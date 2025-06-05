FROM golang:1.24.3

WORKDIR /app

COPY . .

RUN go mod init main.go 
RUN go mod tidy
RUN go build -o main

EXPOSE 8080
CMD ["./main"]