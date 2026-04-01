from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

chroma_dir = Path('backend_service/milestone1/chroma_db')
print('exists', chroma_dir.exists())
emb = HuggingFaceEmbeddings(model='sentence-transformers/all-MiniLM-L6-v2', model_kwargs={'device':'cpu'})
vec = Chroma(collection_name='milestone1_collection', embedding_function=emb, persist_directory=str(chroma_dir))
print('vector store', type(vec))
ret = vec.as_retriever(search_kwargs={'k':3})
print('retriever type', type(ret))
print('has get_relevant_documents', hasattr(ret,'get_relevant_documents'))
print('has _get_relevant_documents', hasattr(ret,'_get_relevant_documents'))
print('dir filtered', [n for n in dir(ret) if 'relevant' in n.lower()])
try:
    docs = ret.get_relevant_documents('test')
    print('docs count', len(docs))
    print([getattr(d,'metadata',{}) for d in docs])
    print([getattr(d,'page_content','')[:120] for d in docs])
except Exception as e:
    print('get_relevant_documents failed', e)
try:
    docs2 = ret._get_relevant_documents('test', run_manager=None)
    print('docs2 count', len(docs2))
    print([getattr(d,'metadata',{}) for d in docs2])
    print([getattr(d,'page_content','')[:120] for d in docs2])
except Exception as e:
    print('_get_relevant_documents failed', e)
