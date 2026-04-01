# Document Ingestion and Indexing Pipeline (Milestone 1)

This project implements a document ingestion and indexing pipeline using LangChain, Chroma, and HuggingFace embeddings. It processes PDF and TXT files, chunks them, cleans metadata, and stores them in a local Chroma vector database.

## Project Structure

```
milestone1/
│
├── app.py              # Main application script
├── requirements.txt    # Project dependencies
├── .env                # Environment variables (API keys)
├── data/               # Place your PDF and TXT files here
└── chroma_db/          # Persistent vector store (auto-generated)
```

## Setup Instructions

1.  **Create a Virtual Environment** (Recommended):
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: You may need to install C++ build tools if you encounter errors with `chromadb` or `unstructured` on Windows.*

3.  **Configure Environment Variables**:
    - Open the `.env` file.
    - Replace `your_groq_api_key_here` with your actual Groq API Key.
    - Example: `GROQ_API_KEY=gsk_...`

4.  **Add Documents**:
    - Place your `.pdf` and `.txt` files inside the `data/` folder.

## How to Run

Execute the main script:

```bash
python app.py
```

## Execution Flow

The script will automatically:
1.  **Cleanup**: Delete any existing `chroma_db` to start fresh.
2.  **Initialize**: Setup the ChatGroq model (llama-3.1-8b-instant).
3.  **Load**: specific PDF and TXT files from `data/`.
4.  **Split**: Chunk text into 3000-character segments with 200 overlap.
5.  **Clean**: Remove incompatible metadata.
6.  **Embed**: Generate embeddings using `sentence-transformers/all-MiniLM-L6-v2` (running locally on CPU).
7.  **Store**: Save vectors to `chroma_db`.

## Testing

To verify the pipeline:
1.  Ensure `.env` has a valid key (or the script will warn but proceed with other steps).
2.  Put a sample PDF in `data/`.
3.  Run `python app.py`.
4.  Check the console output for:
    - "Starting fresh build..."
    - "Loaded X documents."
    - "Split X documents into Y chunks."
    - "Vector store created and persisted..."
    - "Milestone 1 Completed Successfully"
5.  Verify that the `chroma_db` folder has been created and populated.

## Troubleshooting / Common Errors

-   **`sqlite3` errors**: Chroma requires a newer version of SQLite. If you see this, try installing `pysqlite3-binary` and overriding the default sqlite3 import, or update your Python installation.
-   **`ModuleNotFoundError`**: Ensure you activated your virtual environment and installed all requirements.
-   **`GROQ_API_KEY not found`**: Make sure your `.env` file is in the `milestone1` directory and contains the key.
-   **Empty Data**: The script will complete but report "No documents loaded" if `data/` is empty.
