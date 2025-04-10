# Import submodules for easier access
from worker.llm.gemini_client import get_gemini_response
from worker.llm.text_processing import extract_text_from_document, chunk_text
from worker.llm.embedding import generate_embeddings, cosine_similarity