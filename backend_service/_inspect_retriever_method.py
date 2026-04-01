import inspect
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

emb = HuggingFaceEmbeddings(model='sentence-transformers/all-MiniLM-L6-v2')
vec = Chroma(collection_name='milestone1_collection', embedding_function=emb, persist_directory='backend_service/milestone1/chroma_db')
ret = vec.as_retriever()
print('type', type(ret))
method = getattr(ret, '_get_relevant_documents', None)
print('method', method)
print('signature', inspect.signature(method))
print('has_run_manager', 'run_manager' in inspect.signature(method).parameters)
