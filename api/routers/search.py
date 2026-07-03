"""
Search API endpoint.
"""

from fastapi import APIRouter, Query

from api.dependencies import get_recommendation_service

router = APIRouter(tags=["Search"])


@router.get("/search")
def search(
    q: str = Query(..., min_length=1, description="Search query"),
    max_results: int = Query(10, ge=1, le=50),
):
    """Fuzzy movie search — substring match + difflib fallback."""
    svc = get_recommendation_service()
    results = svc.search(q, max_results=max_results)
    return {"results": results, "query": q, "count": len(results)}
