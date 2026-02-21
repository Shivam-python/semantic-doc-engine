from core.vector_db import get_qdrant_client
from qdrant_client.models import PointStruct, VectorParams, Distance


qdrant_client = get_qdrant_client()


def get_query_points(vector, collection_name):
    search_result = qdrant_client.query_points(
        collection_name=collection_name,
        query=vector
    ).points
    return search_result


def similarity_search(query_vector, collection_name, limit=5):
    points = get_query_points(query_vector, collection_name)
    sorted_points = sorted(points, key=lambda x: x.score, reverse=True)
    search_results = {hit.score: hit.payload.get("content","") for hit in sorted_points[:limit]}
    return search_results


def create_collection_if_not_exists(collection_name, vector_size):
    try:
        if not qdrant_client.collection_exists(collection_name=collection_name):
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
    except Exception as e:
        print(f"Error creating collection '{collection_name}': {e}")


def upsert_points(collection_name, points, vector_size):
    create_collection_if_not_exists(collection_name, vector_size)
    try:
        operation_info = qdrant_client.upsert(
            collection_name=collection_name,
            wait=True,
            points=points
        )
        return operation_info.status
    except Exception as e:
        print(f"Error upserting points to collection '{collection_name}': {e}")
        return None