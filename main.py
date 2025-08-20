from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from typing import Optional, List
from collections import defaultdict, deque
import asyncio, time, hashlib

from database import DBase
from compilers.cpp import CppCompiler
from compilers.python import PythonCompiler
from compilers.javascript import JavaScriptCompiler

app = FastAPI()
db = DBase("compilehub.db")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Компиляторы
compilers = {
    "cpp": CppCompiler(),
    "python": PythonCompiler(),
    "javascript": JavaScriptCompiler(),
}

# Очередь задач компиляции
compilation_queue = asyncio.Queue(maxsize=100)
compilation_results = {}

# Rate limiting
rate_limit_storage = defaultdict(lambda: {"count": 0, "reset_time": time.time() + 60})
MAX_REQUESTS_PER_MINUTE = 30

# Метрики
metrics = {
    "total_compilations": 0,
    "failed_compilations": 0,
    "avg_compilation_time": 0,
    "compilation_times": deque(maxlen=100),
    "active_users": set(),
}

# Модели Pydantic
class UserRegister(BaseModel):
    email: str
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class FileItem(BaseModel):
    id: int
    name: str
    type: str  # "file" или "folder"
    size: str
    modified: str
    folder: Optional[int] = None
    code: Optional[str] = None
    code_lang: Optional[str] = None

class MoveFileRequest(BaseModel):
    folderId: Optional[int]

class MigrateFilesRequest(BaseModel):
    userId: str
    files: List[FileItem]

# Rate limiting
def check_rate_limit(client_ip: str):
    current_time = time.time()
    limits = rate_limit_storage[client_ip]
    
    if current_time >= limits["reset_time"]:
        limits["count"] = 0
        limits["reset_time"] = current_time + 60
    
    if limits["count"] >= MAX_REQUESTS_PER_MINUTE:
        return False
    
    limits["count"] += 1
    return True

# Worker для обработки компиляций
async def compilation_worker():
    while True:
        try:
            task = await compilation_queue.get()
            task_id = task["id"]
            code = task["code"]
            language = task["language"]
            input_data = task.get("input", "")
            
            start_time = time.time()
            
            compiler = compilers.get(language, compilers["cpp"])
            result = await compiler.compile_and_run(code, input_data)
            
            execution_time = time.time() - start_time
            
            # Обновление метрик
            metrics["total_compilations"] += 1
            if not result["success"]:
                metrics["failed_compilations"] += 1
            metrics["compilation_times"].append(execution_time)
            metrics["avg_compilation_time"] = sum(metrics["compilation_times"]) / len(metrics["compilation_times"])
            
            result["executionTime"] = execution_time
            compilation_results[task_id] = result
            
        except Exception as e:
            print(f"Worker error: {e}")
            compilation_results[task_id] = {
                "success": False,
                "error": str(e)
            }

@app.on_event("startup")
async def startup_event():
    db.init_db()
    asyncio.create_task(compilation_worker())

# Auth endpoints
@app.post("/api/auth/register")
async def register(user: UserRegister):
    existing = db.get_user_by_username(user.username)
    if existing:
        raise HTTPException(400, "Username already taken")
    
    existing_email = db.get_user_by_email(user.email)
    if existing_email:
        raise HTTPException(400, "Email already registered")
    
    password_hash = hashlib.sha256(user.password.encode()).hexdigest()
    user_id = db.create_user(user.email, user.username, password_hash)
    
    return {"message": "Successfully signed up, please login", "success": True}

@app.post("/api/auth/login")
async def login(user: UserLogin):
    db_user = db.get_user_by_username(user.username)
    if not db_user:
        raise HTTPException(401, "Invalid credentials")
    
    password_hash = hashlib.sha256(user.password.encode()).hexdigest()
    if db_user["password"] != password_hash:
        raise HTTPException(401, "Invalid credentials")
    
    metrics["active_users"].add(db_user["id"])
    
    return {
        "id": str(db_user["id"]),
        "email": db_user["email"],
        "username": db_user["username"],
        "token": hashlib.sha256(f"{db_user['id']}{time.time()}".encode()).hexdigest(),
        "isGuest": False
    }

@app.post("/api/auth/logout")
async def logout():
    return {"message": "Logged out successfully"}

@app.get("/api/files")
async def get_files(userId: str):
    user_files = db.get_user_files(int(userId))
    items = []
    
    for file in user_files:
        item = {
            "id": file["id"],
            "name": file["name"],
            "type": file["type"],
            "size": file["size"],
            "modified": file["modified"],
        }
        if file["type"] == "file":
            item["folder"] = file["folder_id"]
        items.append(item)
    
    return items

@app.delete("/api/files/{file_id}")
async def delete_file(file_id: int):
    db.delete_file(file_id)
    return {"message": "File deleted"}

@app.patch("/api/files/{file_id}/move")
async def move_file(file_id: int, request: MoveFileRequest):
    db.update_file_folder(file_id, request.folderId)
    return {"message": "File moved"}

@app.post("/api/files/migrate")
async def migrate_files(request: MigrateFilesRequest):
    for file in request.files:
        db.create_file(
            user_id=int(request.userId),
            name=file.name,
            file_type=file.type,
            size=file.size,
            folder_id=file.folder,
            code=file.code,
            code_lang=file.code_lang
        )
    return {"message": "Files migrated"}

# Compilation endpoints
@app.get("/api/code")
async def get_code(fileId: int):
    file = db.get_file_by_id(fileId)
    if not file:
        raise HTTPException(404, "File not found")
    return file.get("code", "")

class CompileRequest(BaseModel):
    code: str
    language: Optional[str] = None
    input: Optional[str] = None

@app.post("/api/compile/")
async def compile_code_post(request: Request, compile_req: CompileRequest):
    client_ip = request.client.host
    
    if not check_rate_limit(client_ip):
        raise HTTPException(429, "Rate limit exceeded")
    
    code = compile_req.code
    input_data = compile_req.input or ""
    
    # Определение языка
    language = compile_req.language
    if not language:
        if "#include" in code:
            language = "cpp"
        elif "print(" in code or "def " in code or "import " in code:
            language = "python"
        elif "console.log" in code or "function" in code or "const " in code:
            language = "javascript"
        else:
            language = "cpp"
    
    task_id = hashlib.sha256(f"{code}{time.time()}".encode()).hexdigest()[:16]
    
    await compilation_queue.put({
        "id": task_id,
        "code": code,
        "language": language,
        "input": input_data
    })
    
    # Ждём результат (max 10 секунд)
    for _ in range(100):
        if task_id in compilation_results:
            result = compilation_results.pop(task_id)
            return result
        await asyncio.sleep(0.1)
    
    return {
        "success": False,
        "error": "Compilation timeout"
    }

@app.get("/api/compile/")
async def compile_code(request: Request, code: str, input: Optional[str] = None):
    client_ip = request.client.host
    
    if not check_rate_limit(client_ip):
        raise HTTPException(429, "Rate limit exceeded")
    
    # Определение языка по расширению или синтаксису
    language = "cpp"  # по умолчанию
    if "print(" in code or "def " in code or "import " in code:
        language = "python"
    elif "console.log" in code or "function" in code:
        language = "javascript"
    
    task_id = hashlib.sha256(f"{code}{time.time()}".encode()).hexdigest()[:16]
    
    await compilation_queue.put({
        "id": task_id,
        "code": code,
        "language": language,
        "input": input or ""
    })
    
    # Ждём результат (max 10 секунд)
    for _ in range(100):
        if task_id in compilation_results:
            result = compilation_results.pop(task_id)
            return result
        await asyncio.sleep(0.1)
    
    return {
        "success": False,
        "error": "Compilation timeout"
    }

# Metrics endpoint
@app.get("/api/metrics")
async def get_metrics():
    return {
        "total_compilations": metrics["total_compilations"],
        "failed_compilations": metrics["failed_compilations"],
        "success_rate": ((metrics["total_compilations"] - metrics["failed_compilations"]) / max(metrics["total_compilations"], 1)) * 100,
        "avg_compilation_time": round(metrics["avg_compilation_time"], 3),
        "active_users": len(metrics["active_users"]),
        "queue_size": compilation_queue.qsize()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.3.29", port=9999)