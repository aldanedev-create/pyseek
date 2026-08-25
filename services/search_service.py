from database import repositories
from services.ranking_service import highlight, normalize_query


def search(query: str, limit: int = 20, domain: str = "") -> dict:
    normalized = normalize_query(query)
    if not normalized:
        return {"query": "", "results": [], "total": 0}
    results = repositories.search_documents(normalized, limit=limit, domain=domain)
    for result in results:
        result["snippet"] = highlight(result.pop("body_text", ""), normalized)
        if result.get("fetched_at") and hasattr(result["fetched_at"], "isoformat"):
            result["fetched_at"] = result["fetched_at"].isoformat()
    return {"query": normalized, "results": results, "total": len(results)}
