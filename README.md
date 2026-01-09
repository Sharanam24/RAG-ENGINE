# RAG Automation Project

A full-stack RAG (Retrieval-Augmented Generation) automation system with a modern web interface, thread management, and deployment configuration.

## Features

- 🤖 **RAG-powered AI responses** using LangChain and ChromaDB
- 💬 **Thread-based conversations** with persistent storage
- 🎨 **Modern web interface** with real-time chat
- 🗄️ **SQLite database** for thread and message storage
- 🐳 **Docker support** for easy deployment
- 🌐 **Production-ready** with Nginx configuration

## Project Structure

```
PROJECT/
├── backend/
│   ├── main.py           # FastAPI application
│   ├── rag_engine.py     # RAG implementation
│   └── requirements.txt  # Python dependencies
├── frontend/
│   ├── index.html        # Main HTML file
│   ├── styles.css        # Styling
│   └── app.js            # Frontend logic
├── Dockerfile            # Container configuration
├── docker-compose.yml    # Development setup
├── docker-compose.prod.yml  # Production setup
├── nginx.conf            # Nginx configuration
└── README.md             # This file
```

## Prerequisites

- Python 3.11+
- Docker and Docker Compose (for containerized deployment)
- Ollama (optional, for local LLM) or OpenAI API key

## Setup Instructions

### Option 1: Local Development

**Windows:**
1. **Run the startup script:**
   ```cmd
   start.bat
   ```
   This will automatically set up the virtual environment, install dependencies, and start the server.

**Linux/Mac:**
1. **Run the startup script:**
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

**Manual Setup:**
1. **Install Python dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Run the backend:**
   ```bash
   python main.py
   ```
   The application will be available at `http://localhost:8000` (frontend and API)

3. **Access the application:**
   - Open your browser and go to `http://localhost:8000`
   - The frontend is automatically served by the FastAPI backend

### Option 2: Docker Deployment

1. **Build and run:**
   ```bash
   docker-compose up -d
   ```

2. **Access the application:**
   - Frontend: `http://localhost:8000`
   - API docs: `http://localhost:8000/docs`

### Option 3: Production Deployment with Domain

1. **Update domain in nginx.conf:**
   ```nginx
   server_name your-domain.com www.your-domain.com;
   ```

2. **Deploy with production compose:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **SSL Certificate (Let's Encrypt):**
   ```bash
   # Install certbot
   docker run -it --rm -v ./ssl:/etc/letsencrypt certbot/certbot certonly --standalone -d your-domain.com
   ```

4. **Update nginx.conf for SSL:**
   ```nginx
   listen 443 ssl;
   ssl_certificate /etc/nginx/ssl/fullchain.pem;
   ssl_certificate_key /etc/nginx/ssl/privkey.pem;
   ```

## Configuration

### RAG Engine Setup

The RAG engine uses:
- **Embeddings**: HuggingFace `sentence-transformers/all-MiniLM-L6-v2`
- **Vector Store**: ChromaDB (persisted in `chroma_db/`)
- **LLM**: Ollama (default) or can be configured for OpenAI

**Note**: On first run, the system will download the embedding model (~80MB). This may take a few minutes.

### Using OpenAI instead of Ollama

Edit `backend/rag_engine.py`:

```python
from langchain.llms import OpenAI

self.llm = OpenAI(openai_api_key="your-api-key")
```

### Adding Custom Documents

You can add documents to the RAG system by modifying `rag_engine.py` or creating an API endpoint to upload documents.

## API Endpoints

- `GET /api/threads` - Get all conversation threads
- `GET /api/threads/{thread_id}` - Get a specific thread with messages
- `POST /api/chat` - Send a message and get RAG response
- `DELETE /api/threads/{thread_id}` - Delete a thread

## Environment Variables

Create a `.env` file for configuration:

```env
OPENAI_API_KEY=your-key-here
OLLAMA_BASE_URL=http://localhost:11434
```

## Troubleshooting

1. **Ollama not found**: 
   - Install Ollama from https://ollama.ai
   - Or switch to OpenAI in `rag_engine.py`
   - The system will work without Ollama but with limited functionality

2. **Port conflicts**: Change ports in `docker-compose.yml` or update the port in `main.py`

3. **Database errors**: Delete `threads.db` in the backend directory to reset (development only)

4. **Model download issues**: The first run downloads the embedding model. Ensure you have internet connection and ~500MB free space

5. **Windows path issues**: If you encounter path issues, ensure you're running from the project root directory

## License

MIT License - feel free to use and modify as needed.

## Support

For issues or questions, please check the API documentation at `/docs` when the server is running.
