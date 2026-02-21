import google.generativeai as genai
from typing import List, Dict, Any
from config.settings import settings

from services.llm_embed.service import get_gemini_embedding

class LLMService:
    """
    Handles communication with the LLM service for embeddings and completions.
    """
    
    def __init__(self):
        # Note: genai is configured in services.llm_embed.service
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    async def get_embeddings(self, text: str) -> List[float]:
        """
        Transforms a string into a numerical vector embedding using Gemini.
        """
        return get_gemini_embedding(text)

    async def generate_answer(self, question: str, context: str) -> str:
        """
        Generates a final answer using Gemini based on retrieved context.
        """
        prompt = f"""
        Use the following pieces of retrieved context to answer the question. 
        If you don't know the answer, just say that you don't know, don't try to make up an answer.
        
        Context:
        {context}
        
        Question: {question}
        
        Answer concisely and cite the sources if provided in the context.
        """
        response = self.model.generate_content(prompt)
        return response.text

llm_service = LLMService()
