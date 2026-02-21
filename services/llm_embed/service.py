import google.generativeai as genai 
from config.settings import settings


genai.configure(api_key=settings.GEMINI_API_KEY)


def get_gemini_embedding(text: str, task_type="retrieval_document"):
    """
    Generates an embedding for the given text using Gemini.
    """
    model = settings.EMBEDDING_MODEL
    
    result = genai.embed_content(
        model=model,
        content=text,
        task_type=task_type
    )
    return result['embedding']