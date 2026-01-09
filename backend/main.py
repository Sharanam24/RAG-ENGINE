from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import uuid
from datetime import datetime
from rag_engine import RAGEngine
import os

app = FastAPI(title="RAG Automation API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG engine (non-blocking)
rag_engine = RAGEngine()
print("RAG Engine initialized (components loading in background)")

# Database setup
DB_PATH = "threads.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS threads (
            id TEXT PRIMARY KEY,
            title TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            thread_id TEXT,
            role TEXT,
            content TEXT,
            created_at TEXT,
            FOREIGN KEY (thread_id) REFERENCES threads(id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

class MessageRequest(BaseModel):
    prompt: str
    thread_id: Optional[str] = None

class Message(BaseModel):
    id: str
    role: str
    content: str
    created_at: str

class Thread(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: List[Message] = []

# API Routes (must be defined before catch-all routes)
@app.get("/api/threads")
async def get_threads():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, created_at, updated_at FROM threads ORDER BY updated_at DESC")
    threads = []
    for row in cursor.fetchall():
        threads.append({
            "id": row[0],
            "title": row[1] or "Untitled",
            "created_at": row[2],
            "updated_at": row[3]
        })
    conn.close()
    return {"threads": threads}

@app.get("/api/threads/{thread_id}")
async def get_thread(thread_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get thread info
    cursor.execute("SELECT id, title, created_at, updated_at FROM threads WHERE id = ?", (thread_id,))
    thread_row = cursor.fetchone()
    if not thread_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Get messages
    cursor.execute("SELECT id, role, content, created_at FROM messages WHERE thread_id = ? ORDER BY created_at", (thread_id,))
    messages = []
    for row in cursor.fetchall():
        messages.append({
            "id": row[0],
            "role": row[1],
            "content": row[2],
            "created_at": row[3]
        })
    
    conn.close()
    return {
        "id": thread_row[0],
        "title": thread_row[1] or "Untitled",
        "created_at": thread_row[2],
        "updated_at": thread_row[3],
        "messages": messages
    }

@app.post("/api/chat")
async def chat(request: MessageRequest):
    try:
        # Generate response using RAG
        response = await rag_engine.query(request.prompt)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        # Create or update thread
        if not request.thread_id:
            thread_id = str(uuid.uuid4())
            title = request.prompt[:50] + "..." if len(request.prompt) > 50 else request.prompt
            cursor.execute(
                "INSERT INTO threads (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (thread_id, title, now, now)
            )
        else:
            thread_id = request.thread_id
            cursor.execute("UPDATE threads SET updated_at = ? WHERE id = ?", (now, thread_id))
        
        # Save user message
        user_msg_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO messages (id, thread_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_msg_id, thread_id, "user", request.prompt, now)
        )
        
        # Save assistant response
        assistant_msg_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO messages (id, thread_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (assistant_msg_id, thread_id, "assistant", response, now)
        )
        
        conn.commit()
        conn.close()
        
        return {
            "thread_id": thread_id,
            "response": response,
            "message_id": assistant_msg_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/threads/{thread_id}")
async def delete_thread(thread_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE thread_id = ?", (thread_id,))
    cursor.execute("DELETE FROM threads WHERE id = ?", (thread_id,))
    conn.commit()
    conn.close()
    return {"message": "Thread deleted"}

# Serve frontend static files (after API routes)
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    # Serve static files (CSS, JS, etc.)
    static_path = frontend_path
    app.mount("/static", StaticFiles(directory=static_path), name="static")
    
    # Serve index.html at root
    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        from fastapi.responses import FileResponse
        index_path = os.path.join(frontend_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"message": "Frontend not found"}
    
    # Serve other frontend files (catch-all, but API routes are already defined above)
    @app.get("/{filename:path}", include_in_schema=False)
    async def serve_frontend_files(filename: str):
        # Skip API and docs routes
        if filename.startswith("api") or filename.startswith("docs") or filename == "openapi.json":
            from fastapi.responses import JSONResponse
            return JSONResponse({"error": "Not found"}, status_code=404)
        
        from fastapi.responses import FileResponse
        # Only serve known frontend files
        if filename in ["index.html", "styles.css", "app.js"]:
            file_path = os.path.join(frontend_path, filename)
            if os.path.exists(file_path):
                return FileResponse(file_path)
        return {"error": "Not found"}, 404

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

