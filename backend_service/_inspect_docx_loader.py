try:
    import langchain_community.document_loaders as dl
    print('has Docx2txtLoader', hasattr(dl, 'Docx2txtLoader'))
    print('has UnstructuredWordDocumentLoader', hasattr(dl, 'UnstructuredWordDocumentLoader'))
    if hasattr(dl, 'Docx2txtLoader'):
        print('Docx2txtLoader', dl.Docx2txtLoader)
    if hasattr(dl, 'UnstructuredWordDocumentLoader'):
        print('UnstructuredWordDocumentLoader', dl.UnstructuredWordDocumentLoader)
except Exception as e:
    print('import failed', type(e).__name__, e)
