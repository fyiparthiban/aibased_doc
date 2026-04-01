import os
from pathlib import Path
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

ROOT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT_DIR.parent

def _load_env_file(env_path: Path, override: bool = False) -> None:
    if load_dotenv is not None:
        load_dotenv(env_path, override=override)
        return
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if override or key not in os.environ:
            os.environ[key] = value

for env_file in (
    ROOT_DIR / '.env',
    ROOT_DIR / 'milestone1' / '.env',
    ROOT_DIR / 'milestone2' / '.env',
):
    _load_env_file(env_file, override=True)

import groq
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask.logging import create_logger
from werkzeug.exceptions import HTTPException
from werkzeug.utils import secure_filename

from milestone1.app import (
    load_documents,
    split_documents,
    clean_metadata,
    create_vector_store,
    cleanup,
    DATA_DIR,
)
from milestone2.rag_pipeline import (
    initialize_vector_store,
    initialize_llm,
    build_rag_chain,
    query_rag,
    get_default_chroma_db_dir,
)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
logger = create_logger(app)
logger.setLevel('INFO')

vector_store = None
llm = None
rag_chain = None
chat_history = []


def get_required_env(name: str) -> str:
    value = os.getenv(name, '')
    if not value.strip():
        raise EnvironmentError(
            f"Required environment variable '{name}' is missing or empty. "
            f"Please add it to {ROOT_DIR / '.env'}."
        )
    return value.strip()


def validate_required_envs() -> None:
    missing = [name for name in ('GROQ_API_KEY',) if not os.getenv(name, '').strip()]
    if missing:
        raise EnvironmentError(
            f"Required environment variables are missing or empty: {', '.join(missing)}. "
            f"Please add them to {ROOT_DIR / '.env'}."
        )


def initialize_rag_system() -> None:
    global vector_store, llm, rag_chain

    vector_store = None
    llm = None
    rag_chain = None

    try:
        vector_store = initialize_vector_store()
    except FileNotFoundError as e:
        logger.warning('ChromaDB not found: %s', e)
        vector_store = None
    except Exception:
        logger.exception('Failed to load Chroma vector store')
        vector_store = None

    if vector_store is None:
        logger.info('No existing vector store found, rebuilding from documents...')
        try:
            build_document_index()
            vector_store = initialize_vector_store()
        except Exception:
            logger.exception('Failed to build vector store from documents')
            vector_store = None

    if vector_store is None:
        logger.warning('RAG system initialization aborted because vector store is unavailable')
        return

    try:
        llm = initialize_llm()
        rag_chain = build_rag_chain(vector_store, llm)
        logger.info('RAG system initialized successfully')
    except Exception:
        logger.exception('Failed to initialize RAG system')
        vector_store = llm = rag_chain = None


def build_document_index() -> None:
    cleanup()
    documents = load_documents()
    if not documents:
        raise ValueError(
            'No valid PDF, TXT, MD, or DOCX documents were found in the project documents directories.'
        )

    chunks = split_documents(documents)
    chunks = clean_metadata(chunks)
    create_vector_store(chunks)


@app.errorhandler(HTTPException)
def handle_http_exception(error: HTTPException):
    response = jsonify({
        'error': error.name,
        'message': error.description,
    })
    response.status_code = error.code
    return response


@app.errorhandler(Exception)
def handle_exception(error: Exception):
    logger.exception('Unhandled exception')
    return jsonify({
        'error': 'Internal Server Error',
        'message': str(error),
    }), 500


@app.route('/', methods=['GET'])
def root():
    return jsonify({'message': 'RAG Chatbot API', 'status': 'running'})


@app.route('/health', methods=['GET'])
def health_check():
    chroma_path = get_default_chroma_db_dir()
    return jsonify({
        'status': 'healthy',
        'groq_api_key_present': bool(os.getenv('GROQ_API_KEY', '').strip()),
        'vector_store': vector_store is not None,
        'llm': llm is not None,
        'rag_chain': rag_chain is not None,
        'chroma_db_path': str(chroma_path),
    })


@app.route('/query', methods=['POST'])
def query_documents():
    global rag_chain, chat_history

    if not request.is_json:
        return jsonify({'error': 'Bad Request', 'message': 'Request body must be JSON.'}), 400

    payload = request.get_json(silent=True)
    if not payload or not isinstance(payload, dict):
        return jsonify({'error': 'Bad Request', 'message': 'Invalid JSON payload.'}), 400

    question = payload.get('question')
    if not isinstance(question, str) or not question.strip():
        return jsonify({'error': 'Bad Request', 'message': "The 'question' field is required."}), 400

    if not rag_chain:
        return jsonify({
            'error': 'Service Unavailable',
            'message': (
                'RAG system is not initialized. Ensure GROQ_API_KEY is set in root .env, '
                'the ChromaDB directory exists at milestone1/chroma_db, and restart the backend.'
            )
        }), 503

    try:
        result = query_rag(rag_chain, question.strip())
        chat_entry = {
            'question': question.strip(),
            'answer': result['answer'],
            'sources': result['sources'],
        }
        chat_history.append(chat_entry)
        return jsonify(result)
    except groq.AuthenticationError as e:
        logger.exception('Query failed due to Groq authentication error')
        return jsonify({
            'error': 'Authentication Error',
            'message': (
                'Invalid or expired GROQ_API_KEY. Please verify your Groq API key in backend_service/.env, milestone1/.env, or milestone2/.env and restart the backend.'
            ),
            'details': str(e),
        }), 401
    except Exception as e:
        logger.exception('Query failed')
        return jsonify({'error': 'Query Error', 'message': str(e)}), 500


@app.route('/upload-documents', methods=['POST'])
def upload_documents():
    global rag_chain, vector_store, llm, chat_history

    uploaded_files = request.files.getlist('files')
    if not uploaded_files:
        return jsonify({'error': 'Bad Request', 'message': "No files were uploaded. Use the 'files' field."}), 400

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    project_documents_dir = PROJECT_ROOT / 'documents'
    project_documents_dir.mkdir(parents=True, exist_ok=True)

    saved_files = []
    for uploaded_file in uploaded_files:
        filename = secure_filename(uploaded_file.filename)
        if not filename:
            continue

        file_bytes = uploaded_file.read()
        if not file_bytes:
            continue

        root_filepath = project_documents_dir / filename
        with open(root_filepath, 'wb') as out_file:
            out_file.write(file_bytes)
        saved_files.append(str(root_filepath))

    if not saved_files:
        return jsonify({'error': 'Bad Request', 'message': 'Uploaded files must have valid filenames.'}), 400

    try:
        build_document_index()
        initialize_rag_system()

        if not rag_chain:
            raise RuntimeError('Failed to initialize RAG system after uploading documents.')

        chat_history = []
        return jsonify({'message': 'Documents uploaded and RAG system initialized successfully.'})
    except Exception as e:
        logger.exception('Upload failed')
        return jsonify({'error': 'Upload Failed', 'message': str(e)}), 500


@app.route('/history', methods=['GET'])
def get_history():
    return jsonify({'history': chat_history})


@app.route('/history', methods=['DELETE'])
def clear_history():
    global chat_history
    chat_history = []
    return jsonify({'message': 'Chat history cleared.'})


@app.route('/reset', methods=['POST'])
def reset_system():
    global vector_store, llm, rag_chain, chat_history

    cleanup()
    chat_history = []
    initialize_rag_system()

    if not rag_chain:
        return jsonify({'message': 'System reset, but RAG system is not initialized.'}), 500

    return jsonify({'message': 'System reset successfully.'})


@app.route('/reload-documents', methods=['POST'])
def reload_documents():
    global rag_chain, vector_store, llm, chat_history

    try:
        build_document_index()
        initialize_rag_system()

        if not rag_chain:
            raise RuntimeError('Failed to initialize RAG system after reloading documents.')

        chat_history = []
        return jsonify({'message': 'Documents reloaded and RAG system initialized successfully.'})
    except ValueError as e:
        return jsonify({'error': 'No Documents', 'message': str(e)}), 400
    except Exception as e:
        logger.exception('Document reload failed')
        return jsonify({'error': 'Reload Failed', 'message': str(e)}), 500


@app.before_request
def ensure_rag_initialized():
    global rag_chain
    if rag_chain is None:
        initialize_rag_system()


if __name__ == '__main__':
    validate_required_envs()
    initialize_rag_system()
    port = int(os.getenv('BACKEND_PORT', '8003'))
    app.run(host='0.0.0.0', port=port)
