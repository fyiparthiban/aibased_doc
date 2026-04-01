"""
RAG State Management
Handles chat state, file uploads, and backend integration
"""

import reflex as rx
from typing import List, Dict, Any, Optional, TypedDict
from pathlib import Path
import shutil
import os

from ..backend.rag import rag_backend


class HistoryEntry(TypedDict):
    question: str
    answer: str
    sources: List[str]


class ChatState(rx.State):
    """Main state for RAG Chatbot application"""

    # Chat related state
    question: str = ""
    history: List[HistoryEntry] = []
    is_loading: bool = False

    # Upload related state
    uploaded_files: List[Dict[str, Any]] = []
    pending_upload_paths: List[str] = []
    upload_progress: str = ""

    # System state
    is_initialized: bool = False

    def set_question(self, question: str):
        """Set the current question"""
        self.question = question

    def ask(self):
        """Process question and get answer from RAG backend"""
        if not self.question.strip():
            return

        self.is_loading = True

        try:
            # Get answer from RAG backend (now via API)
            result = rag_backend.ask_question(self.question, self.history)
            sources = result.get("sources", [])
            if not isinstance(sources, list):
                sources = [sources] if sources else []
            sources = self._normalize_sources(sources)

            # Create new history entry
            new_entry = {
                "question": self.question,
                "answer": result.get("answer", "No answer received"),
                "sources": sources
            }

            # Update history (create new list for reactivity)
            self.history = self.history + [new_entry]

            # Clear question
            self.question = ""

        except Exception as e:
            # Handle errors
            error_entry = {
                "question": self.question,
                "answer": f"Error: {str(e)}",
                "sources": []
            }
            self.history = self.history + [error_entry]
            self.question = ""

        finally:
            self.is_loading = False

    async def handle_upload(self, files: List[rx.UploadFile]):
        """Handle file uploads locally and stage for backend processing"""
        if not files:
            print("DEBUG: No files provided to handle_upload")
            self.upload_progress = "No files selected."
            return

        print(f"DEBUG: Received {len(files)} files for upload")

        try:
            # Create documents directory if it doesn't exist
            docs_path = Path("documents")
            docs_path.mkdir(exist_ok=True)

            uploaded_paths = []

            for file in files:
                # Save file to documents directory
                file_path = docs_path / file.filename

                # Read file content (properly await async read)
                try:
                    # Try async read first (Reflex UploadFile)
                    content = await file.read()
                except TypeError:
                    # Fallback to sync read if not async
                    content = file.read()

                # Ensure we have bytes
                if isinstance(content, str):
                    content = content.encode('utf-8')
                elif not isinstance(content, (bytes, bytearray)):
                    raise ValueError(f'Invalid file content type: {type(content)}')

                # Write to disk
                with open(file_path, "wb") as f:
                    f.write(content)

                uploaded_paths.append(str(file_path))

                # Update uploaded files list
                self.uploaded_files = self.uploaded_files + [{
                    "filename": file.filename,
                    "path": str(file_path),
                    "size": len(content)
                }]

            # Store pending upload paths but do not send yet; user clicks button
            self.pending_upload_paths = uploaded_paths
            if self.pending_upload_paths:
                self.upload_progress = f"{len(self.pending_upload_paths)} files ready to upload. Click Upload button."
            else:
                self.upload_progress = "No valid documents selected."

        except Exception as e:
            self.upload_progress = f"Error staging files for upload: {str(e)}"

    def upload_pending_files(self):
        """Send staged files to backend API using the upload button"""
        if not self.pending_upload_paths:
            self.upload_progress = "No files staged for upload. Add files first."
            return

        self.upload_progress = "Uploading documents to backend..."
        upload_result = rag_backend.upload_documents(self.pending_upload_paths)

        if upload_result.get("success"):
            self.upload_progress = upload_result.get("message", "Upload successful")
            self.is_initialized = True
            self.pending_upload_paths = []
            self.load_history()
            self.upload_progress = "Upload succeeded. Redirecting to chat..."
            return rx.redirect("/chat")

        self.upload_progress = f"Upload failed: {upload_result.get('message', 'unknown error')}"

    def load_history(self):
        """Load chat history from the backend API"""
        try:
            api_history = rag_backend.get_chat_history()
            normalized_history = []
            for item in api_history:
                sources = item.get("sources", []) if isinstance(item, dict) else []
                if not isinstance(sources, list):
                    sources = [sources]
                normalized_history.append({
                    "question": item.get("question", "") if isinstance(item, dict) else "",
                    "answer": item.get("answer", "") if isinstance(item, dict) else "",
                    "sources": self._normalize_sources(sources)
                })
            self.history = normalized_history
            # Mark documents available if the backend has a loaded vector store.
            self.is_initialized = rag_backend.get_document_count() > 0
        except Exception as e:
            print(f"Warning: Could not load history from API: {e}")
            # Keep existing history if API fails

    def reset_session(self):
        """Reset the entire session"""
        # Clear local history
        self.history = []

        # Clear uploaded files
        self.uploaded_files = []

        # Clear upload progress
        self.upload_progress = ""

        # Reset RAG backend
        rag_backend.reset()

        # Reset initialization flag
        self.is_initialized = False

        # Clear documents directory
        self._clear_documents_directory()

    def _clear_documents_directory(self):
        """Clear the documents directory"""
        try:
            docs_path = Path("documents")
            if docs_path.exists():
                shutil.rmtree(docs_path)
                docs_path.mkdir(exist_ok=True)
        except Exception as e:
            print(f"Error clearing documents directory: {e}")

    def _normalize_sources(self, sources: List[Any]) -> List[str]:
        normalized_sources: List[str] = []
        for source in sources:
            if isinstance(source, dict):
                src = source.get("source", "Unknown")
                page = source.get("page", "N/A")
                snippet = source.get("snippet", "")
                normalized_sources.append(f"{src} (Page {page}): {snippet}")
            else:
                normalized_sources.append(str(source))
        return normalized_sources

    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        return rag_backend.get_stats()

    @rx.var
    def upload_successful(self) -> bool:
        """Determine whether the upload progress indicates success."""
        return "success" in self.upload_progress.lower()

    @rx.var
    def has_documents(self) -> bool:
        """Check if documents are uploaded and processed"""
        return self.is_initialized or len(self.uploaded_files) > 0

    @rx.var
    def history_count(self) -> int:
        """Get number of chat exchanges"""
        return len(self.history)