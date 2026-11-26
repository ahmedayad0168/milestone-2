"""Local Gradio entry point for OpsPilot."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import gradio as gr
from opspilot.database.db import initialize_database
from opspilot.agent import run_agent


def respond(message: str, history: list[dict] | None):
    """Gradio ChatInterface callback; history is session-scoped."""
    return run_agent(message, history or [])


def build_demo():
    return gr.ChatInterface(
        fn=respond,
        title="OpsPilot | Business Operations Agent",
        description=(
            "Ask about sales, inventory, customer orders, and company policies. "
            "Demo data only — restock requests are drafts, not purchases."
        ),
        examples=[
            "Summarize sales from 2026-10-01 to 2026-10-31.",
            "Which products need replenishment?",
            "What is our return policy for an opened product?",
            "Show the top 5 products by revenue in November 2026.",
        ],
        chatbot=gr.Chatbot(height=560, layout="bubble"),
        textbox=gr.Textbox(
            placeholder="Ask OpsPilot about your business operations...",
            lines=2,
            max_lines=5,
        ),
        show_progress="minimal",
    )


if __name__ == "__main__":
    initialize_database()
    demo = build_demo()
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)
