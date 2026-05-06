from __future__ import annotations

import os

os.environ.setdefault("UPSKIN_MC_SAMPLES", "3")

from fastapi.testclient import TestClient

from upskin_api.main import app
from upskin_api.recommender import get_service


client = TestClient(app)


def test_model_bundle_loads_best_run() -> None:
    service = get_service()
    health = service.health()
    assert health["status"] == "ok"
    assert health["run_id"]
    assert health["best_model_rmse"] > 0
    assert health["uses_mf_proxy"] is True


def test_demo_user_recommendation_call() -> None:
    demo_users = client.get("/demo-users?limit=1").json()
    assert demo_users
    author_id = demo_users[0]["author_id"]

    response = client.get(f"/recommendations/{author_id}?top_n=3")
    assert response.status_code == 200
    payload = response.json()
    assert payload["uses_mf_proxy"] is True
    assert len(payload["recommendations"]) == 3
    item = payload["recommendations"][0]
    for key in [
        "product_id",
        "product_name",
        "brand_name",
        "category",
        "predicted_score",
        "risk_adjusted_score",
        "uncertainty",
        "confidence_bucket",
        "predicted_interval",
        "explanation",
    ]:
        assert key in item
    assert 1 <= item["predicted_score"] <= 5
    assert item["predicted_interval"]["lower"] <= item["predicted_interval"]["upper"]


def test_custom_liked_products_recommendation_call() -> None:
    search = client.get("/products/search?q=farmacy&limit=3")
    assert search.status_code == 200
    products = search.json()
    assert products
    liked_ids = [product["product_id"] for product in products[:2]]

    response = client.post(
        "/recommendations/custom",
        json={"liked_product_ids": liked_ids, "top_n": 3, "filters": {"include_out_of_stock": False}},
    )
    assert response.status_code == 200
    payload = response.json()
    returned_ids = {item["product_id"] for item in payload["recommendations"]}
    assert returned_ids
    assert not returned_ids.intersection(liked_ids)


def test_no_already_seen_products_for_demo_user() -> None:
    service = get_service()
    demo_user = service.demo_users(limit=1)[0]
    author_id = demo_user["author_id"]
    seen = set(
        service.user_history.loc[
            service.user_history["author_id"] == author_id,
            "rated_product_ids",
        ].iloc[0].split("|")
    )

    payload = service.recommend_for_demo_user(author_id=author_id, top_n=10)
    returned_ids = {item["product_id"] for item in payload["recommendations"]}
    assert not returned_ids.intersection(seen)


def test_can_force_latest_ridge_run(monkeypatch) -> None:
    get_service.cache_clear()
    monkeypatch.setenv("UPSKIN_MODEL_RUN_ID", "v002")
    try:
        service = get_service()
        health = service.health()
        assert health["run_id"] == "v002"
        assert health["canonical_matrix_model"] == "ridge_ensemble"
        assert health["mf_score_semantics"] == "ridge_ensemble_matrix_completion_score"

        demo_user = service.demo_users(limit=1)[0]
        payload = service.recommend_for_demo_user(author_id=demo_user["author_id"], top_n=3)
        assert payload["run_id"] == "v002"
        assert len(payload["recommendations"]) == 3
    finally:
        get_service.cache_clear()
