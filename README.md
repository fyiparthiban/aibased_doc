# RAG Chatbot UI

A modern web application for document-based question answering using Retrieval-Augmented Generation (RAG) with Groq API and Hugging Face embeddings.

## Features

- **Document Upload**: Upload PDF, TXT, MD, and DOCX files
- **Intelligent Q&A**: Ask questions about your documents with AI-powered responses
- **Chat History**: Maintain conversation context across sessions
- **Modern UI**: Built with Reflex for a responsive, beautiful interface
- **Backend API**: Separate Flask API service for document processing and embeddings
- **Vector Search**: ChromaDB for efficient document retrieval
- **Multiple Embeddings**: Support for Hugging Face sentence transformers

## Architecture

- **Frontend**: Reflex web application
- **Backend**: Flask REST API
- **Embeddings**: Hugging Face Transformers
- **LLM**: Groq API (Llama models)
- **Vector Store**: ChromaDB
- **Deployment**: Fly.io

## Prerequisites

- Python 3.11+
- Groq API key
- Optional: Hugging Face token for higher rate limits

## Local Development Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd practice_ui
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
cd backend_service
pip install -r requirements.txt
cd ..
```

### 3. Set up environment variables

Create `.env` files in the root and `backend_service/` directories:

**Root `.env`:**

```env
# Not needed for local development
```

**backend_service/.env:**

```env
GROQ_API_KEY=your_groq_api_key_here
HUGGINGFACEHUB_API_TOKEN=your_huggingface_token_here  # Optional
```

### 4. Run the backend service

```bash
cd backend_service
python api.py
```

The backend will start on `http://localhost:8003`

### 5. Run the frontend (in a new terminal)

```bash
reflex run
```

The frontend will start on `http://localhost:3000`

## Deployment

### Backend Deployment

The backend is deployed separately. You can deploy it to Fly.io or any cloud service:

1. Create a Fly.io app
2. Set environment variables in Fly.io dashboard
3. Deploy using `fly deploy` from the `backend_service` directory

### Frontend Deployment

The frontend is deployed using Reflex Cloud:

```bash
reflex cloud deploy
```

Set the `RAG_API_URL` environment variable in the Reflex dashboard to point to your deployed backend.

## Usage

1. Open the web application
2. Upload documents using the upload page
3. Ask questions about your documents in the chat interface
4. View chat history and manage conversations

## API Endpoints

- `GET /health` - Health check
- `POST /query` - Ask questions
- `POST /upload-documents` - Upload documents
- `GET /history` - Get chat history
- `DELETE /history` - Clear chat history
- `POST /reset` - Reset the system
- `POST /reload-documents` - Reload documents from disk

## Configuration

- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (configurable)
- **LLM**: Groq Llama models
- **Vector Store**: ChromaDB with cosine similarity
- **Chunk Size**: Configurable in backend code

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## License

MIT License - see LICENSE file for details
