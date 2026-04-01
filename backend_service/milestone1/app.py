import os
import shutil
from pathlib import Path
from langchain_groq import ChatGroq
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader, TextLoader
try:
    from langchain_community.document_loaders import Docx2txtLoader
except ImportError:
    Docx2txtLoader = None
try:
    from langchain_community.document_loaders import UnstructuredWordDocumentLoader
except ImportError:
    UnstructuredWordDocumentLoader = None
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[1]
DOCUMENTS_DIR = PROJECT_ROOT / 'documents'
DATA_DIR = BASE_DIR / 'data'
CHROMA_DB_DIR = BASE_DIR / 'chroma_db'
COLLECTION_NAME = 'milestone1_collection'
EMBEDDING_MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'


def get_huggingface_token() -> str | None:
    for name in ('HUGGINGFACEHUB_API_TOKEN', 'HF_TOKEN', 'HUGGINGFACE_API_KEY'):
        value = os.getenv(name, '').strip()
        if value:
            return value
    return None


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

    model = ChatGroq(model='llama-3.1-8b-instant', api_key=api_key)
    print('ChatGroq model initialized.')
    return model


def load_documents():
    '''
    Loads PDF, TXT, MD, and DOCX documents from the project root `documents/` folder and from milestone1/data.
    '''
    # Ensure both directories exist, but prefer the root documents folder if present.
    if not DOCUMENTS_DIR.exists():
        DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
        print(f'Created root documents directory {DOCUMENTS_DIR}. Place your files there.')

    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        print(f'Created milestone1 data directory {DATA_DIR}.')

    search_dirs = [DOCUMENTS_DIR, DATA_DIR]
    documents = []

    for source_dir in search_dirs:
        print(f'Loading documents from {source_dir}...')
        try:
            pdf_loader = DirectoryLoader(str(source_dir), glob='**/*.pdf', loader_cls=PyPDFLoader)
            documents.extend(pdf_loader.load())
        except Exception as e:
            print(f'Error loading PDFs from {source_dir}: {e}')

        try:
            txt_loader = DirectoryLoader(str(source_dir), glob='**/*.txt', loader_cls=TextLoader)
            documents.extend(txt_loader.load())
        except Exception as e:
            print(f'Error loading TXTs from {source_dir}: {e}')

        try:
            md_loader = DirectoryLoader(str(source_dir), glob='**/*.md', loader_cls=TextLoader)
            documents.extend(md_loader.load())
        except Exception as e:
            print(f'Error loading MDs from {source_dir}: {e}')

        if Docx2txtLoader is not None:
            try:
                docx_loader = DirectoryLoader(str(source_dir), glob='**/*.docx', loader_cls=Docx2txtLoader)
                documents.extend(docx_loader.load())
            except Exception as e:
                print(f'Error loading DOCX from {source_dir} with Docx2txtLoader: {e}')
        elif UnstructuredWordDocumentLoader is not None:
            try:
                docx_loader = DirectoryLoader(str(source_dir), glob='**/*.docx', loader_cls=UnstructuredWordDocumentLoader)
                documents.extend(docx_loader.load())
            except Exception as e:
                print(f'Error loading DOCX from {source_dir} with UnstructuredWordDocumentLoader: {e}')
        else:
            print('DOCX support is not available: install docx2txt or unstructured to enable .docx uploads.')

    # Remove duplicate documents loaded from multiple source directories
    unique_documents = []
    seen_sources = set()
    for doc in documents:
        source = getattr(doc, 'metadata', {}).get('source', None)
        if source is None:
            source = getattr(doc, 'source', None)
        if isinstance(source, str):
            normalized_source = str(Path(source).resolve()) if source else source
        else:
            normalized_source = str(source)
        if normalized_source in seen_sources:
            continue
        seen_sources.add(normalized_source)
        unique_documents.append(doc)

    print(f'Total documents loaded: {len(unique_documents)}')
    return unique_documents


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
    hf_token = get_huggingface_token()
    if hf_token:
        os.environ['HUGGINGFACEHUB_API_TOKEN'] = hf_token
        print('Using Hugging Face token from environment.')
    embeddings = HuggingFaceEmbeddings(model=EMBEDDING_MODEL_NAME, model_kwargs={'device': 'cpu'})

    print(f'Creating Chroma Vector Store in {CHROMA_DB_DIR}...')
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(CHROMA_DB_DIR),
        collection_name=COLLECTION_NAME,
    )
    if hasattr(vector_store, 'persist'):
        try:
            vector_store.persist()
            print('Vector store persisted successfully.')
        except Exception as e:
            print(f'Warning: Failed to persist Chroma vector store: {e}')
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
        print("No documents found. Please add files to the project root 'documents/' folder or 'backend_service/milestone1/data'.")


if __name__ == '__main__':
    main()
