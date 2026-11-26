"""Ingest Markdown policy files through LlamaIndex into persistent ChromaDB."""
import chromadb
from llama_index.core import SimpleDirectoryReader
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

from opspilot.config import get_settings


def ingest() -> int:
    settings = get_settings()
    settings.chroma_path.mkdir(parents=True, exist_ok=True)
    if not settings.knowledge_dir.exists():
        raise FileNotFoundError(f"Knowledge directory not found: {settings.knowledge_dir}")
    documents = SimpleDirectoryReader(
        input_dir=str(settings.knowledge_dir),
        recursive=True,
        required_exts=[".md", ".txt"],
    ).load_data()
    if not documents:
        raise RuntimeError("No .md or .txt files were found in the knowledge directory.")

    client = chromadb.PersistentClient(path=str(settings.chroma_path))
    try:
        client.delete_collection("opspilot_policies")
    except Exception:
        pass
    collection = client.get_or_create_collection("opspilot_policies")
    vector_store = ChromaVectorStore(chroma_collection=collection)
    embed_model = HuggingFaceEmbedding(model_name=settings.embedding_model, device="cpu")
    pipeline = IngestionPipeline(
        transformations=[
            SentenceSplitter(chunk_size=450, chunk_overlap=70),
            embed_model,
        ],
        vector_store=vector_store,
    )
    nodes = pipeline.run(documents=documents, show_progress=True)
    print(f"Ingested {len(documents)} document(s) into {len(nodes)} nodes.")
    print(f"Chroma collection: opspilot_policies | path: {settings.chroma_path}")
    return len(nodes)


if __name__ == "__main__":
    ingest()
