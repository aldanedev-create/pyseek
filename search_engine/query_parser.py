from services.ranking_service import normalize_query


def parse(query: str) -> dict:
    value = normalize_query(query)
    return {"raw": query or "", "text": value, "terms": value.split()}
