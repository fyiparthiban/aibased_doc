from backend_service.milestone1.app import load_documents, DOCUMENTS_DIR, DATA_DIR
print('DOCUMENTS_DIR:', DOCUMENTS_DIR)
print('DOCUMENTS_DIR exists:', DOCUMENTS_DIR.exists())
print('DATA_DIR:', DATA_DIR)
print('DATA_DIR exists:', DATA_DIR.exists())
docs = load_documents()
print('Loaded docs:', len(docs))
print('Sample sources:', [getattr(d, 'metadata', {}).get('source', 'no source') for d in docs[:5]])
