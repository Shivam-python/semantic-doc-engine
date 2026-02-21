from core.vector_db import get_qdrant_client

qdrnt_client = get_qdrant_client()


def get_query_points(vector, collection_name):
    search_result = qdrnt_client.query_points(
        collection_name=collection_name,
        query=vector
    ).points
    return search_result


def similarity_search(query_vector, collection_name, limit=5):
    points = get_query_points(query_vector, collection_name)
    sorted_points = sorted(points, key=lambda x: x.score, reverse=True)
    search_results = {hit.score: hit.payload.get("content","") for hit in sorted_points[:limit]}
    return search_results