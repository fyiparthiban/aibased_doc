$root = Get-Location
$apiContent = @'
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask.logging import create_logger
from werkzeug.exceptions import HTTPException

from milestone1.app import (
    load_documents,
    split_documents,
    clean_metadata,
    create_vector_store,
    cleanup,
)
from milestone2.rag_pipeline import (
    initialize_vector_store,
    initialize_llm,
    build_rag_chain,
    query_rag,
    DEFAULT_CHROMA_DB_DIR,
)

ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / '.env')

app = Flask(__name__)
logger = create_logger(app)
logger.setLevel('INFO')

vector_store = None
llm = None
rag_chain = None
chat_history = []


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{name}' is missing. "
            f"Please add it to {ROOT_DIR / '.env'}."
        )
    return value


def initialize_rag_system() -> None:
    global vector_store, llm, rag_chain

    try:
        vector_store = initialize_vector_store()
        llm = initialize_llm()
        rag_chain = build_rag_chain(vector_store, llm)
        logger.info('RAG system initialized successfully')
    except FileNotFoundError as e:
        logger.warning('ChromaDB initialization skipped: %s', e)
        vector_store = llm = rag_chain = None
    except EnvironmentError as e:
        logger.error('Environment configuration error: %s', e)
        vector_store = llm = rag_chain = None
    except Exception:
        logger.exception('Failed to initialize RAG system')
        vector_store = llm = rag_chain = None


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
    return jsonify({
        'status': 'healthy',
        'vector_store': vector_store is not None,
        'llm': llm is not None,
        'rag_chain': rag_chain is not None,
        'chroma_db_path': str(DEFAULT_CHROMA_DB_DIR),
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
        return jsonify({'error': 'Service Unavailable', 'message': 'RAG system is not initialized.'}), 503

    try:
        result = query_rag(rag_chain, question.strip())
        chat_entry = {
            'question': question.strip(),
            'answer': result['answer'],
            'sources': result['sources'],
        }
        chat_history.append(chat_entry)
        return jsonify(result)
    except Exception as e:
        logger.exception('Query failed')
        return jsonify({'error': 'Query Error', 'message': str(e)}), 500


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


if __name__ == '__main__':
    initialize_rag_system()
    app.run(host='0.0.0.0', port=8001)
'@
Set-Content -Path .\api.py -Value $apiContent -Encoding utf8

$m1 = @'
import os
import shutil
from pathlib import Path
from langchain_groq import ChatGroq
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
CHROMA_DB_DIR = BASE_DIR / 'chroma_db'
COLLECTION_NAME = 'milestone1_collection'
EMBEDDING_MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'


def cleanup():
    '''
    Deletes the existing chroma_db folder if it exists.
    Handles locked files gracefully.
    '''
    if CHROMA_DB_DIR.exists():
        try:
            def handle_remove_error(func, path, exc_info):
                import stat
                if not os.access(path, os.W_OK):
                    os.chmod(path, stat.S_IWUSR | stat.S_IRUSR)
                    func(path)
                else:
                    raise

            shutil.rmtree(CHROMA_DB_DIR, onerror=handle_remove_error)
            print(f'Cleanup: Deleted existing {CHROMA_DB_DIR} directory.')
        except PermissionError as e:
            print(f'Warning: Could not delete {CHROMA_DB_DIR} - {e}')
            print('This may be due to the database being in use. Skipping cleanup.')


def initialize_chat_model():
    '''
    Initializes the ChatGroq model.
    '''
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        raise EnvironmentError('GROQ_API_KEY is required in the root .env file.')

    model = ChatGroq(model='l-3.1-8b-instantlama', api_key=api_key)
    print('ChatGroq model initialized.')
    return model


def load_documents():
    '''
    Loads PDF and TXT documents from milestone1/data.
    '''
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        print(f'Created {DATA_DIR}. Please place your files here.')
        return []

    print(f'Loading documents from {DATA_DIR}...')
    documents = []

    try:
        pdf_loader = DirectoryLoader(str(DATA_DIR), glob='**/*.pdf', loader_cls=PyPDFLoader)
        documents.extend(pdf_loader.load())
    except Exception as e:
        print(f'Error loading PDFs: {e}')

    try:
        txt_loader = DirectoryLoader(str(DATA_DIR), glob='**/*.txt', loader_cls=TextLoader)
        documents.extend(txt_loader.load())
    except Exception as e:
        print(f'Error loading TXTs: {e}')

    print(f'Total documents loaded: {len(documents)}')
    return documents


def split_documents(documents):
    '''
    Splits documents into manageable chunks.
    '''
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    print(f'Created {len(chunks)} chunks.')
    return chunks


def clean_metadata(chunks):
    '''
    Cleans metadata for Chroma compatibility.
    '''
    for chunk in chunks:
        new_metadata = {}
        for k, v in chunk.metadata.items():
            if isinstance(v, (str, int, float, bool)):
                new_metadata[k] = v
            else:
                new_metadata[k] = str(v)
        chunk.metadata = new_metadata
    return chunks


def create_vector_store(chunks):
    '''
    Creates vector embeddings and stores them in Chroma.
    '''
    if not chunks:
        print('No chunks to process.')
        return

    print('Initializing Embeddings...')
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME, model_kwargs={'device': 'cpu'})

    print(f'Creating Chroma Vector Store in {CHROMA_DB_DIR}...')
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(CHROMA_DB_DIR),
        collection_name=COLLECTION_NAME,
    )
    print('Vector Store created successfully.')


def main():
    print('--- Starting Milestone 1 Pipeline ---')
    cleanup()
    initialize_chat_model()
    docs = load_documents()
    if docs:
        chunks = split_documents(docs)
        chunks = clean_metadata(chunks)
        create_vector_store(chunks)
        print('--- Pipeline Completed ---')
    else:
        print("No documents found. Please add files to 'milestone1/data'.")


if __name__ == '__main__':
    main()
'@
Set-Content -Path .\milestone1\app.py -Value $m1 -Encoding utf8

$m2 = @'
import os
from pathlib import Path
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CHROMA_DB_DIR = Path(os.getenv('CHROMA_DB_DIR', PROJECT_ROOT / 'milestone1' / 'chroma_db'))
COLLECTION_NAME = os.getenv('CHROMA_COLLECTION_NAME', 'milestone1_collection')
EMBEDDING_MODEL_NAME = os.getenv('EMBEDDING_MODEL_NAME', 'sentence-transformers/all-MiniLM-L6-v2')


def initialize_vector_store(persist_directory: Path | str | None = None):
    chroma_dir = Path(persist_directory) if persist_directory else DEFAULT_CHROMA_DB_DIR

    if not chroma_dir.exists():
        raise FileNotFoundError(
            f'ChromaDB directory not found at {chroma_dir}. '
            'Please run milestone1 pipeline or upload documents first.'
        )

    print(f'Loading embeddings ({EMBEDDING_MODEL_NAME})...')
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME, model_kwargs={'device': 'cpu'})

    print(f'Loading Chroma Vector Store from {chroma_dir}...')
    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(chroma_dir),
    )
    return vector_store


def initialize_llm(api_key: str | None = None):
    api_key = api_key or os.getenv('GROQ_API_KEY')

    if not api_key:
        raise EnvironmentError('GROQ_API_KEY is required in the root .env file.')

    print('Initializing ChatGroq LLM...')
    llm = ChatGroq(model='llama-3.1-8b-instant', api_key=api_key, temperature=0.3)
    return llm


def format_docs(docs):
    return '\n\n'.join(doc.page_content for doc in docs)


def build_rag_chain(vector_store, llm):
    print('Building Retrieval QA Chain...')
    retriever = vector_store.as_retriever(search_kwargs={'k': 3})

    system_prompt = (
        'You are an assistant for question-answering tasks. '
        'Use the following pieces of retrieved context to answer the question. '
        'If you don\'t know the answer, say that you don\'t know. '
        'Use three sentences maximum and keep the answer concise.'
        '\n\nContext:'
        '\n{context}'
    )
    prompt = ChatPromptTemplate.from_messages([
        ('system', system_prompt),
        ('human', '{input}'),
    ])

    rag_chain_from_docs = (
        RunnablePassthrough.assign(context=(lambda x: format_docs(x['context'])))
        | prompt
        | llm
        | StrOutputParser()
    )

    rag_chain_with_source = RunnableParallel(
        {'context': retriever, 'input': RunnablePassthrough()}
    ).assign(answer=rag_chain_from_docs)

    return rag_chain_with_source


def query_rag(rag_chain, query: str):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('Query must be a non-empty string.')

    response = rag_chain.invoke(query.strip())
    answer = response.get('answer', 'No answer generated.')
    context_docs = response.get('context', []) or []

    sources = []
    sources_seen = set()
    for doc in context_docs:
        source = getattr(doc.metadata, 'get', doc.metadata.get)('source', 'Unknown') if hasattr(doc, 'metadata') else 'Unknown'
        page = getattr(doc.metadata, 'get', doc.metadata.get)('page', 'N/A') if hasattr(doc, 'metadata') else 'N/A'
        cite_key = f'{source} (Page: {page})'
        if cite_key not in sources_seen:
            sources_seen.add(cite_key)
            source_basename = Path(source).name if source and source != 'Unknown' else source
            sources.append({
                'source': source_basename,
                'page': page,
                'snippet': getattr(doc, 'page_content', '')[:200],
            })

    return {
        'answer': answer,
        'sources': sources,
    }
'@
Set-Content -Path .\milestone2\rag_pipeline.py -Value $m2 -Encoding utf8
Write-Output 'Files written successfully.'