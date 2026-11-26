"""LlamaIndex + Chroma retriever used as a tool by the LangChain agent."""
from functools import lru_cache

from opspilot.config import get_settings
from opspilot.logging_config import get_logger

logger = get_logger("opspilot.rag")


@lru_cache(maxsize=1)
def get_policy_retriever():
    """Load a persistent LlamaIndex vector index and return its retriever."""
    import chromadb
    from llama_index.core import VectorStoreIndex
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from llama_index.vector_stores.chroma import ChromaVectorStore

    settings = get_settings()
    settings.chroma_path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(settings.chroma_path))
    collection = client.get_or_create_collection("opspilot_policies")
    if collection.count() == 0:
        raise RuntimeError("The policy index is empty. Run: python -m opspilot.rag.ingest")
    embed_model = HuggingFaceEmbedding(model_name=settings.embedding_model, device="cpu")
    vector_store = ChromaVectorStore(chroma_collection=collection)
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store, embed_model=embed_model)
    return index.as_retriever(similarity_top_k=settings.top_k)


def retrieve_policy_evidence(query: str) -> str:
    """Return top-k policy passages with filename metadata for grounded answers."""
    query = (query or "").strip()
    if not query:
        return "Query is empty."
    try:
        retriever = get_policy_retriever()
        nodes = retriever.retrieve(query)
    except Exception as exc:
        logger.exception("Policy retrieval failed")
        return f"Policy retrieval is unavailable: {type(exc).__name__}. Do not answer policy questions from guesswork."
    if not nodes:
        return "No relevant policy passages were retrieved. State that the available knowledge base did not provide an answer."
    blocks = []
    for i, item in enumerate(nodes, start=1):
        node = item.node
        metadata = node.metadata or {}
        source = metadata.get("file_name") or metadata.get("file_path") or "unknown policy file"
        score = getattr(item, "score", None)
        excerpt = node.get_content().strip()
        blocks.append(f"[Policy evidence {i} | source: {source} | score: {score}]\n{excerpt}")
    return "\n\n".join(blocks)
