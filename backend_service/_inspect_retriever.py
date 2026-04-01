from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

emb = HuggingFaceEmbeddings(model='sentence-transformers/all-MiniLM-L6-v2')
vec = Chroma(collection_name='milestone1_collection', embedding_function=emb, persist_directory='backend_service/milestone1/chroma_db')
ret = vec.as_retriever()
print(type(ret))
print([m for m in dir(ret) if 'relevant' in m.lower() or 'retrieve' in m.lower()])
