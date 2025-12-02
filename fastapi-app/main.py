from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import json
import os
import logging
import time
import threading
from multiprocessing import Queue
from os import getenv
from fastapi import Request
from prometheus_fastapi_instrumentator import Instrumentator
from logging_loki import LokiQueueHandler


app = FastAPI()

# Prometheus 메트릭스 엔드포인트 (/metrics)
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# Loki 로그 핸들러 설정
loki_endpoint = getenv("LOKI_ENDPOINT", "http://loki:3100/loki/api/v1/push")
loki_logs_handler = LokiQueueHandler(
    Queue(-1),
    url=loki_endpoint,
    tags={"application": "fastapi"},
    version="1",
)

# Custom access logger (ignore Uvicorn's default logging)
custom_logger = logging.getLogger("custom.access")
custom_logger.setLevel(logging.INFO)
custom_logger.propagate = False  # 중복 로깅 방지

# Add Loki handler
custom_logger.addHandler(loki_logs_handler)

# 로그 핸들러가 제대로 초기화되었는지 확인
logging.info(f"Loki endpoint configured: {loki_endpoint}")

async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time  # Compute response time

    # 클라이언트 IP와 포트 정보 추출
    client_host = request.client.host if request.client else "unknown"
    client_port = request.client.port if request.client else 0
    
    # 로그 메시지 형식: IP:PORT - "METHOD PATH HTTP/VERSION" STATUS DURATIONs
    log_message = (
        f'{client_host}:{client_port} - "{request.method} {request.url.path} HTTP/1.1" {response.status_code} {duration:.3f}s'
    )

    # 로그 전송
    try:
        custom_logger.info(log_message)
    except Exception as e:
        # 로그 전송 실패 시에도 앱이 계속 작동하도록 예외 처리
        logging.error(f"Failed to send log to Loki: {e}")

    return response

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    return await log_requests(request, call_next)

# To-Do 항목 모델
class TodoItem(BaseModel):
    id: int
    title: str
    description: str
    completed: bool
    due_date: str | None = None

# JSON 파일 경로
TODO_FILE = "todo.json"

# JSON 파일에서 To-Do 항목 로드
def load_todos():
    if os.path.exists(TODO_FILE):
        with open(TODO_FILE, "r") as file:
            return json.load(file)
    return []

# JSON 파일에 To-Do 항목 저장
def save_todos(todos):
    with open(TODO_FILE, "w") as file:
        json.dump(todos, file, indent=4)

# To-Do 목록 조회
@app.get("/todos", response_model=list[TodoItem])
def get_todos():
    return load_todos()

# 신규 To-Do 항목 추가
@app.post("/todos", response_model=TodoItem)
def create_todo(todo: TodoItem):
    todos = load_todos()
    todos.append(todo.dict())
    save_todos(todos)
    return todo

# To-Do 항목 수정
@app.put("/todos/{todo_id}", response_model=TodoItem)
def update_todo(todo_id: int, updated_todo: TodoItem):
    todos = load_todos()
    for todo in todos:
        if todo["id"] == todo_id:
            todo.update(updated_todo.dict())
            save_todos(todos)
            return updated_todo
    raise HTTPException(status_code=404, detail="To-Do item not found")

# To-Do 항목 삭제
@app.delete("/todos/{todo_id}", response_model=dict)
def delete_todo(todo_id: int):
    todos = load_todos()
    todos = [todo for todo in todos if todo["id"] != todo_id]
    save_todos(todos)
    return {"message": "To-Do item deleted"}

# HTML 파일 서빙
@app.get("/", response_class=HTMLResponse)
def read_root():
    with open("templates/index.html", "r") as file:
        content = file.read()
    return HTMLResponse(content=content)