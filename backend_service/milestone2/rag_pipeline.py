import os
from pathlib import Path
from typing import Any

from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_default_chroma_db_dir() -> Path:
    return Path(os.getenv('CHROMA_DB_DIR') or PROJECT_ROOT / 'milestone1' / 'chroma_db')


def get_collection_name() -> str:
    return os.getenv('CHROMA_COLLECTION_NAME', 'milestone1_collection')


def get_embedding_model_name() -> str:
    return os.getenv('EMBEDDING_MODEL_NAME', 'sentence-transformers/all-MiniLM-L6-v2')


def get_huggingface_token() -> str | None:
    for name in ('HUGGINGFACEHUB_API_TOKEN', 'HF_TOKEN', 'HUGGINGFACE_API_KEY'):
        value = os.getenv(name, '').strip()
        if value:
            return value
    return None


class RAGChain:
    def __init__(self, retriever: Any, llm: ChatGroq):
        self.retriever = retriever
        self.llm = llm

    def invoke(self, query: str) -> dict:
        if hasattr(self.retriever, 'get_relevant_documents'):
            documents = self.retriever.get_relevant_documents(query)
        elif hasattr(self.retriever, '_get_relevant_documents'):
            documents = self.retriever._get_relevant_documents(query, run_manager=None)
        else:
            raise AttributeError(
                'Retriever does not support get_relevant_documents or _get_relevant_documents.'
            )
        context = format_docs(documents)
        prompt = build_prompt(query, context)

        llm_response = self.llm.invoke(prompt)
        answer = getattr(llm_response, 'content', None)
        if answer is None:
            answer = str(llm_response)

        return {'answer': answer, 'context': documents}


def build_prompt(query: str, context: str) -> str:
    if not context:
        context = 'No context was retrieved from the document store.'

    return (
        'You are a helpful assistant. Answer the user question using only the provided document context. '
        'If the answer is not contained in the context, say that you do not know. Keep the answer concise and factual.\n\n'
        'Context:\n'
        f'{context}\n\n'
        'Question:\n'
        f'{query}\n'
    )


def format_docs(docs: list) -> str:
    return '\n\n'.join(getattr(doc, 'page_content', '') for doc in docs if getattr(doc, 'page_content', None))


def initialize_vector_store(persist_directory: Path | str | None = None):
    chroma_dir = Path(persist_directory) if persist_directory else get_default_chroma_db_dir()

    if not chroma_dir.exists():
        raise FileNotFoundError(
            f'ChromaDB directory not found at {chroma_dir}. '
            'Please run milestone1 pipeline or upload documents first.'
        )

    embedding_model_name = get_embedding_model_name()
    collection_name = get_collection_name()

    print(f'Loading embeddings ({embedding_model_name})...')
    hf_token = get_huggingface_token()
    if hf_token:
        os.environ['HUGGINGFACEHUB_API_TOKEN'] = hf_token
        print('Using Hugging Face token from environment.')

    embeddings = HuggingFaceEmbeddings(model=embedding_model_name, model_kwargs={'device': 'cpu'})

    print(f'Loading Chroma Vector Store from {chroma_dir}...')
    vector_store = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=str(chroma_dir),
    )
    return vector_store


def initialize_llm(api_key: str | None = None):
    api_key = api_key or os.getenv('GROQ_API_KEY')

    if not api_key:
        raise EnvironmentError(
            'GROQ_API_KEY is required in backend_service/.env and must be a valid Groq API key.'
        )

    print('Initializing ChatGroq LLM...')
    llm = ChatGroq(model='llama-3.1-8b-instant', api_key=api_key, temperature=0.3)
    return llm


def build_rag_chain(vector_store, llm):
    print('Building Retrieval QA Chain...')
    retriever = vector_store.as_retriever(search_kwargs={'k': 3})
    return RAGChain(retriever, llm)


def query_rag(rag_chain, query: str):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('Query must be a non-empty string.')

    response = rag_chain.invoke(query.strip())
    answer = response.get('answer', 'No answer generated.')
    context_docs = response.get('context', []) or []

    sources = []
    sources_seen = set()
    for doc in context_docs:
        metadata = getattr(doc, 'metadata', {}) or {}
        if isinstance(metadata, dict):
            source = metadata.get('source', 'Unknown')
            page = metadata.get('page', 'N/A')
        else:
            source = getattr(metadata, 'source', 'Unknown')
            page = getattr(metadata, 'page', 'N/A')

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
