# Implementation status

The project is a runnable local starter, not a verified production deployment.

Verified in the build environment: Python syntax, the standard-library business-layer tests, the agent helper tests (history trimming, Gemini block flattening, error mapping), the LangChain tool wrappers, and construction of the Gemini chat model and agent graph with a dummy key.

Not executed in the build environment (requires your own key / network): live Gemini calls and the first-run download of the BGE embedding model. Run `python scripts/check_gemini.py` after configuring `.env` to verify your key.
