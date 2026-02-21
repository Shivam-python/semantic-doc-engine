from typing import List, Dict, Any
from .llm import llm_service
from .retriever import retriever

class QueryEngine:
    """
    Orchestrates the RAG flow:
    1. String -> LLM (Embedding)
    2. Embedding -> Qdrant (Search)
    3. Results -> LLM (Generation)
    4. Return Final Answer
    """

    async def query(self, question: str) -> Dict[str, Any]:
        # 1. Get embedding for the question
        query_vector = await llm_service.get_embeddings(question)
        
        # 2. Retrieve relevant chunks from Qdrant
        matches = await retriever.search(query_vector)
        
        if not matches:
            return {
                "answer": "I couldn't find any relevant information in the documents.",
                "citations": [],
                "confidence": 0.0
            }

        # 3. Prepare context for LLM
        context_parts = []
        citations = []
        for i, match in enumerate(matches):
            citation_label = f"Source {i+1}"
            context_parts.append(f"[{citation_label}]: {match['text']}")
            citations.append({
                "label": citation_label,
                "id": match['id'],
                "metadata": match['metadata']
            })
            
        context_str = "\n\n".join(context_parts)
        
        # 4. Generate final answer
        answer = await llm_service.generate_answer(question, context_str)
        
        # Calculate a simple confidence score
        confidence = matches[0]["score"] if matches else 0.0
        
        return {
            "answer": answer,
            "citations": citations,
            "confidence": confidence
        }

engine = QueryEngine()
