from fastapi.responses import FileResponse
from fastapi import Request
import os

frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")

async def serve_static(request: Request):
    """Serve static files from frontend directory"""
    path = request.url.path
    
    # Remove leading slash
    if path.startswith('/'):
        path = path[1:]
    
    # Default to index.html
    if not path or path == '/':
        file_path = os.path.join(frontend_path, "index.html")
    else:
        file_path = os.path.join(frontend_path, path)
    
    # Security: ensure file is within frontend directory
    file_path = os.path.normpath(file_path)
    if not file_path.startswith(os.path.normpath(frontend_path)):
        return {"error": "Forbidden"}, 403
    
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    else:
        # For SPA routing, return index.html
        index_path = os.path.join(frontend_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"error": "Not found"}, 404
