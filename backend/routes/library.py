# routes/library.py
from fastapi import APIRouter, Query
from ..services.crawl_whitelist import crawl_domain
from ..services.search_docs import search_docs

router = APIRouter(prefix="/api/library", tags=["library"])

@router.post("/crawl")
async def crawl(domain:str, start_url:str, topic:str):
    stored = await crawl_domain([start_url], topic)
    return {"stored": stored, "domain": domain}

@router.get("/search")
def lib_search(q:str = Query(..., min_length=3), topic:str|None=None, limit:int=5):
    results = search_docs(q, topic, limit)
    return {"results": results}
