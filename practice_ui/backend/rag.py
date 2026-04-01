"""
RAG Backend Implementation
Handles document processing, embeddings, vector storage, and retrieval
Now connects to the FastAPI backend service
"""

import os
import sys
import time
import subprocess
import requests
from typing import List, Dict, Any, Optional
from pathlib import Path

_LOCAL_BACKEND_PROCESS = None
_LOCAL_BACKEND_STARTED = False


def _normalize_api_url(api_url: str) -> str:
    api_url = api_url.strip().rstrip('/')
    if api_url.startswith("http://0.0.0.0"):
        api_url = api_url.replace("0.0.0.0", "127.0.0.1")
    return api_url


def _start_local_backend_service() -> bool:
    global _LOCAL_BACKEND_PROCESS, _LOCAL_BACKEND_STARTED
    if _LOCAL_BACKEND_STARTED:
        return _LOCAL_BACKEND_PROCESS is not None

    backend_script = Path(__file__).resolve().parents[2] / "backend_service" / "api.py"
    if not backend_script.exists():
        return False

    env = os.environ.copy()
    env.setdefault("BACKEND_PORT", "8003")
    try:
        _LOCAL_BACKEND_PROCESS = subprocess.Popen(
            [sys.executable, str(backend_script)],
            cwd=str(backend_script.parent),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as exc:
        print(f"Warning: Failed to start local backend service: {exc}")
        _LOCAL_BACKEND_STARTED = True
        return False

    _LOCAL_BACKEND_STARTED = True
    for _ in range(20):
        try:
            response = requests.get("http://127.0.0.1:8003/health", timeout=1)
            if response.status_code == 200:
                print("Successfully started local backend service on http://127.0.0.1:8003")
                return True
        except requests.exceptions.RequestException:
            time.sleep(0.5)

    print("Warning: Local backend service did not become available on port 8003")
    return False


def _get_default_api_base_url() -> str:
    env_url = os.getenv("RAG_API_URL")
    if env_url:
        return _normalize_api_url(env_url.strip())
    return "http://127.0.0.1:8003"


def _find_working_api_base_url() -> str:
    candidates = []
    env_url = os.getenv("RAG_API_URL")
    if not env_url and _start_local_backend_service():
        return "http://127.0.0.1:8003"
    if env_url:
        normalized = _normalize_api_url(env_url.strip())
        candidates.append(normalized)
        if normalized.startswith("http://127.0.0.1"):
            candidates.append(normalized.replace("127.0.0.1", "localhost", 1))
        elif normalized.startswith("http://localhost"):
            candidates.append(normalized.replace("localhost", "127.0.0.1", 1))

    candidates.extend([
            "http://127.0.0.1:8003",
            "http://127.0.0.1:8001",
            "http://127.0.0.1:8002",
            "http://127.0.0.1:8000",
            "http://localhost:8003",
            "http://localhost:8001",
            "http://localhost:8002",
            "http://localhost:8000",
        ])
    seen = set()
    filtered = []
    for url in candidates:
        if url not in seen:
            seen.add(url)
            filtered.append(url)
    candidates = filtered

    for url in candidates:
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                print(f"Successfully connected to RAG backend API on {url}")
                return url
            print(f"Warning: Backend API at {url} returned status {response.status_code}")
        except requests.exceptions.RequestException:
            print(f"Warning: Could not connect to backend API on {url}")

    if _start_local_backend_service():
        try:
            response = requests.get("http://127.0.0.1:8003/health", timeout=5)
            if response.status_code == 200:
                print("Successfully connected to local backend API on http://127.0.0.1:8003")
                return "http://127.0.0.1:8003"
        except requests.exceptions.RequestException:
            print("Warning: Could not connect to local backend API on http://127.0.0.1:8003")

    fallback = candidates[0] if candidates else "http://127.0.0.1:8001"
    print(f"Warning: Could not connect to RAG backend API. Using fallback URL {fallback}")
    return fallback


DEFAULT_API_BASE_URL = _get_default_api_base_url()
"""Default backend API base URL, configurable with RAG_API_URL."""


class RAGBackend:
    """RAG Backend for document processing and Q&A - API Client"""

    def __init__(self, api_base_url: str = DEFAULT_API_BASE_URL):
        self.api_base_url = api_base_url
        self.documents_path = Path("documents")
        self._connected = False

    def _ensure_connected(self):
        if not self._connected:
            self.api_base_url = self._find_working_api_url(self.api_base_url)
            self._connected = True

    def _find_working_api_url(self, api_base_url: str) -> str:
        try:
            response = requests.get(f"{api_base_url}/health", timeout=5)
            if response.status_code == 200:
                print(f"Successfully connected to RAG backend API on {api_base_url}")
                return api_base_url
            print(f"Warning: Backend API at {api_base_url} returned status {response.status_code}")
        except requests.exceptions.RequestException:
            print(f"Warning: Could not connect to backend API on {api_base_url}")

        fallback_candidates = ["http://localhost:8001", "http://localhost:8002", "http://localhost:8000"]
        for fallback_url in fallback_candidates:
            if fallback_url == api_base_url:
                continue
            try:
                response = requests.get(f"{fallback_url}/health", timeout=5)
                if response.status_code == 200:
                    print(f"Successfully connected to RAG backend API on {fallback_url}")
                    return fallback_url
                print(f"Warning: Backend API at {fallback_url} returned status {response.status_code}")
            except requests.exceptions.RequestException:
                print(f"Warning: Could not connect to backend API on {fallback_url}")

        print(f"Warning: Falling back to configured API URL {api_base_url}")
        return api_base_url

    def _test_connection(self):
        """Test connection to the backend API"""
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=5)
            if response.status_code == 200:
                print("Successfully connected to RAG backend API")
            else:
                print(f"Warning: Backend API returned status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Warning: Could not connect to backend API: {e}")
            print(f"Make sure the backend API is running on {self.api_base_url}")

    def load_documents(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """Load documents from file paths - now handled by API"""
        # This method is kept for compatibility but documents are uploaded via API
        return []

    def process_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process documents: chunking and preprocessing - now handled by API"""
        return documents

    def create_vectorstore(self, documents: List[Dict[str, Any]]):
        """Create or update vector store with documents - now handled by API"""
        pass  # Vector store creation is handled by the API

    def ask_question(self, question: str, chat_history: List[Dict] = None) -> Dict[str, Any]:
        """Ask a question and get an answer with sources"""
        self._ensure_connected()
        try:
            response = requests.post(
                f"{self.api_base_url}/query",
                json={"question": question},
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                sources = result.get("sources", [])
                if not isinstance(sources, list):
                    sources = [sources] if sources else []
                normalized_sources = []
                for source in sources:
                    if isinstance(source, dict):
                        normalized_sources.append(
                            f"{source.get('source', 'Unknown')} (Page {source.get('page', 'N/A')}): {source.get('snippet', '')}"
                        )
                    else:
                        normalized_sources.append(str(source))
                return {
                    "answer": result.get("answer", "No answer received"),
                    "sources": normalized_sources
                }
            else:
                return {
                    "answer": f"Error: Backend API returned status {response.status_code}",
                    "sources": []
                }

        except requests.exceptions.RequestException as e:
            return {
                "answer": f"Error connecting to backend API: {str(e)}",
                "sources": []
            }

    def upload_documents(self, file_paths: List[str]) -> Dict[str, Any]:
        """Upload documents to the backend API"""
        self._ensure_connected()
        print(f"DEBUG: upload_documents called with {len(file_paths)} file paths")
        files = []
        try:
            for file_path in file_paths:
                print(f"DEBUG: Checking file: {file_path}")
                if os.path.exists(file_path):
                    print(f"DEBUG: File exists: {file_path}")
                    files.append(('files', open(file_path, 'rb')))
                else:
                    print(f"DEBUG: File does not exist: {file_path}")

            if not files:
                print("DEBUG: No valid files found")
                return {"success": False, "message": "No valid files found"}

            print(f"DEBUG: Sending {len(files)} files to backend API")
            response = requests.post(
                f"{self.api_base_url}/upload-documents",
                files=files,
                timeout=60
            )

            print(f"DEBUG: Backend response status: {response.status_code}")
            print(f"DEBUG: Backend response text: {response.text}")

            if response.status_code == 200:
                result = response.json()
                return {"success": True, "message": result.get("message", "Upload successful")}
            else:
                return {
                    "success": False,
                    "message": f"Upload failed: {response.text}"
                }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"Error uploading documents: {str(e)}. Make sure the backend API is running on {self.api_base_url}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error uploading documents: {str(e)}"
            }
        finally:
            for _, file_obj in files:
                try:
                    file_obj.close()
                except Exception:
                    pass

    def get_chat_history(self) -> List[Dict[str, Any]]:
        """Get chat history from the backend"""
        self._ensure_connected()
        try:
            response = requests.get(f"{self.api_base_url}/history", timeout=10)
            if response.status_code == 200:
                result = response.json()
                return result.get("history", [])
            else:
                print(f"Warning: Could not get history, status {response.status_code}")
                return []
        except requests.exceptions.RequestException as e:
            print(f"Warning: Could not connect to get history: {e}")
            return []

    def reset_vectorstore(self):
        """Reset the vectorstore via API"""
        self._ensure_connected()
        try:
            response = requests.post(f"{self.api_base_url}/reset", timeout=30)
            if response.status_code == 200:
                print("Vector store reset successfully")
            else:
                print(f"Warning: Reset failed with status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Warning: Could not reset vector store: {e}")

    def get_document_count(self) -> int:
        """Get the number of documents in the vectorstore - approximated"""
        self._ensure_connected()
        # Since we can't directly query the count, we'll return an estimate
        # based on whether the system is initialized
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=5)
            if response.status_code == 200:
                health = response.json()
                return 1 if health.get("vector_store") else 0
            return 0
        except:
            return 0

    def reset(self):
        """Reset the vectorstore (alias for reset_vectorstore)"""
        self.reset_vectorstore()

    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        return {
            "document_count": self.get_document_count(),
            "status": "ready"
        }


# Singleton instance for frontend state access
rag_backend = RAGBackend()