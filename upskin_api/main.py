from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .recommender import get_service
from .schemas import CustomRecommendationRequest, ProductSearchItem, RecommendationResponse


app = FastAPI(
    title="Up Skin Recommendation API",
    version="0.1.0",
    description="Model-backed handoff API for uncertainty-aware skincare recommendations.",
)

default_origins = ",".join(
    [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://up-skin.onrender.com",
        "https://up-skin.vercel.app",
    ]
)
cors_origins = [
    origin.strip()
    for origin in os.getenv("UPSKIN_CORS_ORIGINS", default_origins).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health() -> dict:
    return get_service().health()


@app.get("/model/metrics")
def model_metrics() -> dict:
    return get_service().metrics()


@app.get("/demo-users")
def demo_users(limit: int = Query(default=25, ge=1, le=100)) -> list[dict]:
    return get_service().demo_users(limit=limit)


@app.get("/products/search", response_model=list[ProductSearchItem])
def products_search(
    q: str = Query(default=""),
    limit: int = Query(default=20, ge=1, le=50),
) -> list[dict]:
    return get_service().search_products(query=q, limit=limit)


@app.get("/recommendations/{author_id}", response_model=RecommendationResponse)
def recommendations_for_author(
    author_id: str,
    top_n: int = Query(default=10, ge=1, le=50),
) -> dict:
    try:
        return get_service().recommend_for_demo_user(author_id=author_id, top_n=top_n)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/recommendations/custom", response_model=RecommendationResponse)
def custom_recommendations(payload: CustomRecommendationRequest) -> dict:
    try:
        return get_service().recommend_for_custom(
            liked_product_ids=payload.liked_product_ids,
            top_n=payload.top_n,
            filters=payload.filters,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
