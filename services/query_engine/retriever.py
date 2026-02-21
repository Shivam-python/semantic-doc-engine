from typing import List, Dict, Any
from core.vector_db import get_qdrant_client
from config.settings import settings

class Retriever:
    """
    Handles searching in Qdrant vector database.
    """
    
    def __init__(self, collection_name: str = None):
        self.client = get_qdrant_client()
        self.collection_name = collection_name or settings.COLLECTION_NAME

    async def search(self, query_vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Queries Qdrant for matching vectors and returns the associated payloads.
        """
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            with_payload=True,
            with_vectors=False
        )
        
        formatted_results = []
        for res in results:
            formatted_results.append({
                "text": res.payload.get("content", ""),
                "metadata": res.payload.get("metadata", {}),
                "score": res.score,
                "id": res.id
            })
            
        return formatted_results

retriever = Retriever()
