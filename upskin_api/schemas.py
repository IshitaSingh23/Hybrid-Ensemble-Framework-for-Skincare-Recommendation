from __future__ import annotations

from pydantic import BaseModel, Field


class RecommendationFilters(BaseModel):
    secondary_categories: list[str] = Field(default_factory=list)
    max_price_usd: float | None = Field(default=None, ge=0)
    exclude_product_ids: list[str] = Field(default_factory=list)
    include_out_of_stock: bool = False


class CustomRecommendationRequest(BaseModel):
    liked_product_ids: list[str] = Field(min_length=1)
    top_n: int = Field(default=10, ge=1, le=50)
    filters: RecommendationFilters = Field(default_factory=RecommendationFilters)


class ProductSearchItem(BaseModel):
    product_id: str
    product_name: str
    brand_name: str
    category: str
    price_usd: float | None = None
    avg_product_rating: float | None = None
    loves_count: int | None = None


class PredictedInterval(BaseModel):
    lower: float
    upper: float
    level: str = "calibrated_95"


class RecommendationItem(BaseModel):
    product_id: str
    product_name: str
    brand_name: str
    category: str
    predicted_score: float
    risk_adjusted_score: float
    uncertainty: float
    confidence_bucket: str
    predicted_interval: PredictedInterval
    explanation: str


class RecommendationResponse(BaseModel):
    run_id: str
    best_model_rmse: float
    uses_mf_proxy: bool
    mf_proxy_note: str
    recommendations: list[RecommendationItem]
