"""Expose LlamaIndex retrieval as a standard LangChain tool."""
from langchain_core.tools import tool
from opspilot.rag.index import retrieve_policy_evidence
from opspilot.logging_config import get_logger

logger = get_logger("opspilot.rag.tool")


@tool
def search_company_policies(query: str) -> str:
    """Search internal company policy documents for returns, shipping, purchasing, stock handling, or customer privacy. Use this before answering policy questions."""
    logger.info("tool_call name=search_company_policies query_chars=%d", len(query or ""))
    return retrieve_policy_evidence(query)
