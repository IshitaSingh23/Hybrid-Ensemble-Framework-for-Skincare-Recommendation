#!/usr/bin/env python3
"""Build Matrix -> Transformer -> Bayesian handoff artifacts.

Run from the up-skin project folder:

    source venv/bin/activate
    python viraj/scripts/build_handoff_artifacts.py

The script writes generated artifacts under artifacts/, which is ignored by git.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.neighbors import NearestNeighbors


REVIEW_FILES = [
    "reviews_0-250.csv",
    "reviews_250-500.csv",
    "reviews_500-750.csv",
    "reviews_750-1250.csv",
    "reviews_1250-end.csv",
]


@dataclass
class RunConfig:
    data_dir: str = "Datasets"
    artifact_dir: str = "artifacts"
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    min_user_ratings: int = 10
    min_product_ratings: int = 20
    random_state: int = 42
    mf_factors: int = 20
    mf_lr: float = 0.01
    mf_reg: float = 0.05
    mf_epochs: int = 42
    hybrid_alpha: float = 0.7
    liked_rating_threshold: float = 4.0
    top_k_values: tuple[int, ...] = (5, 10, 20)
    neighbor_count: int = 10


class BiasedMatrixFactorization:
    """Small explicit-feedback matrix factorization model matching Ishita's notebook."""

    def __init__(
        self,
        n_users: int,
        n_items: int,
        n_factors: int = 20,
        lr: float = 0.01,
        reg: float = 0.05,
        n_epochs: int = 42,
        random_state: int = 42,
    ) -> None:
        self.n_users = n_users
        self.n_items = n_items
        self.n_factors = n_factors
        self.lr = lr
        self.reg = reg
        self.n_epochs = n_epochs
        self.random_state = random_state

    def fit(self, train_array: np.ndarray, val_array: np.ndarray | None = None) -> "BiasedMatrixFactorization":
        rng = np.random.default_rng(self.random_state)
        self.mu = float(np.mean(train_array[:, 2]))
        self.bu = np.zeros(self.n_users)
        self.bi = np.zeros(self.n_items)
        self.P = 0.1 * rng.normal(size=(self.n_users, self.n_factors))
        self.Q = 0.1 * rng.normal(size=(self.n_items, self.n_factors))
        self.train_history_: list[float] = []
        self.val_history_: list[float] = []

        for epoch in range(1, self.n_epochs + 1):
            shuffled = train_array.copy()
            rng.shuffle(shuffled)

            for u_raw, i_raw, r_raw in shuffled:
                u = int(u_raw)
                i = int(i_raw)
                r = float(r_raw)

                pred = self.mu + self.bu[u] + self.bi[i] + np.dot(self.P[u], self.Q[i])
                err = r - pred

                self.bu[u] += self.lr * (err - self.reg * self.bu[u])
                self.bi[i] += self.lr * (err - self.reg * self.bi[i])

                p_old = self.P[u].copy()
                q_old = self.Q[i].copy()
                self.P[u] += self.lr * (err * q_old - self.reg * p_old)
                self.Q[i] += self.lr * (err * p_old - self.reg * q_old)

            train_pred = self.predict_many(train_array[:, 0], train_array[:, 1])
            train_rmse = rmse(train_array[:, 2], train_pred)
            self.train_history_.append(train_rmse)

            if val_array is not None and len(val_array) > 0:
                val_pred = self.predict_many(val_array[:, 0], val_array[:, 1])
                self.val_history_.append(rmse(val_array[:, 2], val_pred))

            if epoch == 1 or epoch % 5 == 0 or epoch == self.n_epochs:
                if self.val_history_:
                    print(
                        f"Epoch {epoch:02d} | Train RMSE: {self.train_history_[-1]:.4f} "
                        f"| Val RMSE: {self.val_history_[-1]:.4f}"
                    )
                else:
                    print(f"Epoch {epoch:02d} | Train RMSE: {self.train_history_[-1]:.4f}")

        return self

    def predict_many(self, users: Iterable[int], items: Iterable[int]) -> np.ndarray:
        users = np.asarray(users, dtype=int)
        items = np.asarray(items, dtype=int)
        preds = self.mu + self.bu[users] + self.bi[items] + np.sum(self.P[users] * self.Q[items], axis=1)
        return np.clip(preds, 1, 5)

    def predict_user_all(self, user_idx: int) -> np.ndarray:
        preds = self.mu + self.bu[user_idx] + self.bi + self.Q @ self.P[user_idx]
        return np.clip(preds, 1, 5)


def rmse(y_true: Iterable[float], y_pred: Iterable[float]) -> float:
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def mae(y_true: Iterable[float], y_pred: Iterable[float]) -> float:
    return float(mean_absolute_error(y_true, y_pred))


def parse_args() -> RunConfig:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="Datasets")
    parser.add_argument("--artifact-dir", default="artifacts")
    parser.add_argument("--model-name", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--min-user-ratings", type=int, default=10)
    parser.add_argument("--min-product-ratings", type=int, default=20)
    parser.add_argument("--mf-epochs", type=int, default=42)
    parser.add_argument("--mf-factors", type=int, default=20)
    parser.add_argument("--hybrid-alpha", type=float, default=0.7)
    args = parser.parse_args()
    return RunConfig(
        data_dir=args.data_dir,
        artifact_dir=args.artifact_dir,
        model_name=args.model_name,
        min_user_ratings=args.min_user_ratings,
        min_product_ratings=args.min_product_ratings,
        mf_epochs=args.mf_epochs,
        mf_factors=args.mf_factors,
        hybrid_alpha=args.hybrid_alpha,
    )


def ensure_inputs(data_dir: Path) -> None:
    missing = [data_dir / name for name in ["product_info.csv", *REVIEW_FILES] if not (data_dir / name).exists()]
    if missing:
        raise FileNotFoundError("Missing required Kaggle CSVs: " + ", ".join(str(path) for path in missing))


def parse_listish(value: object) -> str:
    if isinstance(value, list):
        return ", ".join(str(x) for x in value if pd.notna(x))
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.startswith("[") and text.endswith("]"):
        try:
            parsed = ast.literal_eval(text)
            if isinstance(parsed, list):
                return ", ".join(str(x) for x in parsed if pd.notna(x))
        except (SyntaxError, ValueError):
            pass
    return text


def clean_text(value: object) -> str:
    text = parse_listish(value)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def build_product_text(row: pd.Series) -> str:
    parts = [
        f"Product: {clean_text(row.get('product_name'))}",
        f"Brand: {clean_text(row.get('brand_name'))}",
        f"Category: {clean_text(row.get('secondary_category'))} {clean_text(row.get('tertiary_category'))}",
        f"Highlights: {clean_text(row.get('highlights'))}",
        f"Ingredients: {clean_text(row.get('ingredients'))}",
    ]
    return " | ".join(part for part in parts if part and not part.endswith(": "))


def load_products(data_dir: Path) -> pd.DataFrame:
    df_products = pd.read_csv(data_dir / "product_info.csv")
    df_products = df_products.rename(columns={"rating": "avg_product_rating", "reviews": "num_reviews"})
    df_products = df_products[df_products["primary_category"] == "Skincare"].copy()
    df_products["product_id"] = df_products["product_id"].astype(str)
    df_products = df_products.drop_duplicates(subset=["product_id"]).reset_index(drop=True)

    for col in ["product_name", "brand_name", "secondary_category", "tertiary_category", "highlights", "ingredients"]:
        df_products[col] = df_products[col].apply(clean_text)
    df_products["product_text"] = df_products.apply(build_product_text, axis=1)
    return df_products


def load_interactions(data_dir: Path, skincare_product_ids: set[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    frames = []
    usecols = ["author_id", "product_id", "rating", "skin_type", "skin_tone", "eye_color", "hair_color"]
    for name in REVIEW_FILES:
        frame = pd.read_csv(data_dir / name, usecols=usecols, dtype={"author_id": "string", "product_id": "string"})
        frames.append(frame)

    reviews = pd.concat(frames, ignore_index=True)
    reviews["author_id"] = reviews["author_id"].astype(str)
    reviews["product_id"] = reviews["product_id"].astype(str)
    reviews["rating"] = pd.to_numeric(reviews["rating"], errors="coerce")
    reviews = reviews.dropna(subset=["author_id", "product_id", "rating"])
    reviews = reviews[reviews["product_id"].isin(skincare_product_ids)].copy()

    profile_cols = ["skin_type", "skin_tone", "eye_color", "hair_color"]
    user_profile = (
        reviews.groupby("author_id")[profile_cols]
        .agg(lambda values: values.dropna().mode().iloc[0] if len(values.dropna()) else np.nan)
        .reset_index()
    )

    interactions = (
        reviews.groupby(["author_id", "product_id"], as_index=False)["rating"]
        .mean()
        .sort_values(["author_id", "product_id"])
        .reset_index(drop=True)
    )
    return interactions, user_profile


def make_split(
    interactions: pd.DataFrame,
    min_user_ratings: int,
    min_product_ratings: int,
    random_state: int,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int | float]]:
    df_cf = interactions.copy()
    filter_iterations = 0
    while True:
        before_rows = len(df_cf)
        user_counts = df_cf["author_id"].value_counts()
        product_counts = df_cf["product_id"].value_counts()
        active_users = user_counts[user_counts >= min_user_ratings].index
        active_products = product_counts[product_counts >= min_product_ratings].index
        df_cf = df_cf[
            df_cf["author_id"].isin(active_users) & df_cf["product_id"].isin(active_products)
        ].copy()
        filter_iterations += 1
        if len(df_cf) == before_rows:
            break

    matrix_users = int(df_cf["author_id"].nunique())
    matrix_products = int(df_cf["product_id"].nunique())
    observed = int(len(df_cf))
    total_cells = matrix_users * matrix_products
    missing_pct = 100 * (total_cells - observed) / total_cells

    test_df = df_cf.groupby("author_id", group_keys=False).sample(n=1, random_state=random_state)
    train_df = df_cf.drop(index=test_df.index).copy()
    train_users = set(train_df["author_id"])
    train_products = set(train_df["product_id"])
    test_df = test_df[
        test_df["author_id"].isin(train_users) & test_df["product_id"].isin(train_products)
    ].copy()

    report = {
        "filtered_interactions": observed,
        "filtered_users": matrix_users,
        "filtered_products": matrix_products,
        "filter_iterations": filter_iterations,
        "matrix_total_cells": int(total_cells),
        "matrix_missing_pct": float(missing_pct),
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
        "train_users": int(train_df["author_id"].nunique()),
        "test_users": int(test_df["author_id"].nunique()),
        "min_train_ratings_per_user": int(train_df.groupby("author_id").size().min()),
        "cold_start_test_rows_removed": int(matrix_users - len(test_df)),
    }
    return train_df.reset_index(drop=True), test_df.reset_index(drop=True), report


def build_mappings(train_df: pd.DataFrame) -> tuple[dict[str, int], dict[str, int], np.ndarray, np.ndarray]:
    user_ids = np.sort(train_df["author_id"].unique())
    item_ids = np.sort(train_df["product_id"].unique())
    user_to_idx = {user_id: idx for idx, user_id in enumerate(user_ids)}
    item_to_idx = {item_id: idx for idx, item_id in enumerate(item_ids)}
    return user_to_idx, item_to_idx, user_ids, item_ids


def to_indexed_array(df: pd.DataFrame, user_to_idx: dict[str, int], item_to_idx: dict[str, int]) -> np.ndarray:
    mapped = pd.DataFrame(
        {
            "user_idx": df["author_id"].map(user_to_idx),
            "item_idx": df["product_id"].map(item_to_idx),
            "rating": df["rating"],
        }
    ).dropna()
    return mapped[["user_idx", "item_idx", "rating"]].to_numpy(dtype=float)


def baseline_predictions(train_df: pd.DataFrame, test_df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, dict[str, float]]]:
    global_mean = float(train_df["rating"].mean())
    user_mean = train_df.groupby("author_id")["rating"].mean()
    item_mean = train_df.groupby("product_id")["rating"].mean()

    out = test_df.rename(columns={"rating": "true_rating"}).copy()
    out["global_mean_score"] = global_mean
    out["user_item_score"] = [
        np.clip(global_mean + (user_mean.get(u, global_mean) - global_mean) + (item_mean.get(p, global_mean) - global_mean), 1, 5)
        for u, p in zip(out["author_id"], out["product_id"])
    ]

    metrics = {
        "global_mean": {
            "rmse": rmse(out["true_rating"], out["global_mean_score"]),
            "mae": mae(out["true_rating"], out["global_mean_score"]),
        },
        "user_item_baseline": {
            "rmse": rmse(out["true_rating"], out["user_item_score"]),
            "mae": mae(out["true_rating"], out["user_item_score"]),
        },
    }
    return out, metrics


def encode_products(
    df_products: pd.DataFrame,
    model_name: str,
    transformer_dir: Path,
    force: bool = False,
) -> np.ndarray:
    transformer_dir.mkdir(parents=True, exist_ok=True)
    embedding_path = transformer_dir / "product_embeddings.npz"
    catalog_path = transformer_dir / "product_catalog.csv"

    if embedding_path.exists() and not force:
        saved = np.load(embedding_path, allow_pickle=True)
        saved_ids = saved["product_ids"].astype(str).tolist()
        current_ids = df_products["product_id"].astype(str).tolist()
        if saved_ids == current_ids:
            print("Reusing existing transformer embeddings.")
            return saved["embeddings"].astype(np.float32)

    model = SentenceTransformer(model_name)
    embeddings = model.encode(
        df_products["product_text"].tolist(),
        batch_size=64,
        show_progress_bar=True,
        normalize_embeddings=True,
    )
    embeddings = np.asarray(embeddings, dtype=np.float32)
    np.savez_compressed(embedding_path, product_ids=df_products["product_id"].to_numpy(), embeddings=embeddings)
    df_products.drop(columns=["product_text"]).to_csv(catalog_path, index=False)
    (transformer_dir / "embedding_model.txt").write_text(model_name + "\n")
    return embeddings


def save_neighbors(
    df_products: pd.DataFrame,
    embeddings: np.ndarray,
    transformer_dir: Path,
    neighbor_count: int,
) -> pd.DataFrame:
    nn = NearestNeighbors(metric="cosine", algorithm="brute")
    nn.fit(embeddings)
    distances, indices = nn.kneighbors(embeddings, n_neighbors=neighbor_count + 1)

    rows = []
    product_ids = df_products["product_id"].to_numpy()
    for product_idx, product_id in enumerate(product_ids):
        for rank, (distance, neighbor_idx) in enumerate(zip(distances[product_idx], indices[product_idx]), start=0):
            neighbor_id = product_ids[neighbor_idx]
            if neighbor_id == product_id:
                continue
            neighbor = df_products.iloc[neighbor_idx]
            rows.append(
                {
                    "product_id": product_id,
                    "neighbor_product_id": neighbor_id,
                    "rank": rank,
                    "similarity": 1 - float(distance),
                    "neighbor_product_name": neighbor["product_name"],
                    "neighbor_brand_name": neighbor["brand_name"],
                    "neighbor_secondary_category": neighbor["secondary_category"],
                    "neighbor_tertiary_category": neighbor["tertiary_category"],
                }
            )
    neighbors = pd.DataFrame(rows).sort_values(["product_id", "rank"])
    neighbors.to_csv(transformer_dir / "product_neighbors.csv", index=False)
    return neighbors


def make_user_history(train_df: pd.DataFrame, liked_threshold: float) -> pd.DataFrame:
    grouped = train_df.sort_values(["author_id", "product_id"]).groupby("author_id")
    history = grouped.agg(
        user_rating_count=("rating", "size"),
        mean_user_rating=("rating", "mean"),
        rated_product_ids=("product_id", lambda values: "|".join(values.astype(str))),
    ).reset_index()
    liked = (
        train_df[train_df["rating"] >= liked_threshold]
        .sort_values(["author_id", "product_id"])
        .groupby("author_id")["product_id"]
        .agg(lambda values: "|".join(values.astype(str)))
        .rename("liked_product_ids")
        .reset_index()
    )
    return history.merge(liked, on="author_id", how="left").fillna({"liked_product_ids": ""})


def user_content_profiles(
    train_df: pd.DataFrame,
    product_id_to_embedding_idx: dict[str, int],
    embeddings: np.ndarray,
    liked_threshold: float,
) -> dict[str, np.ndarray]:
    profiles = {}
    for user_id, user_rows in train_df.groupby("author_id"):
        liked_rows = user_rows[user_rows["rating"] >= liked_threshold]
        source_rows = liked_rows if len(liked_rows) else user_rows
        indices = [product_id_to_embedding_idx[p] for p in source_rows["product_id"] if p in product_id_to_embedding_idx]
        if not indices:
            continue
        profile = embeddings[indices].mean(axis=0)
        norm = np.linalg.norm(profile)
        if norm > 0:
            profile = profile / norm
        profiles[user_id] = profile.astype(np.float32)
    return profiles


def cosine_to_rating_scale(scores: np.ndarray) -> np.ndarray:
    return 1 + 4 * np.clip(scores, 0, 1)


def prediction_feature_table(
    test_predictions: pd.DataFrame,
    train_df: pd.DataFrame,
    df_products: pd.DataFrame,
    user_profiles_df: pd.DataFrame,
    product_id_to_embedding_idx: dict[str, int],
    embeddings: np.ndarray,
    profiles: dict[str, np.ndarray],
    alpha: float,
) -> pd.DataFrame:
    rows = []
    for row in test_predictions.itertuples(index=False):
        profile = profiles.get(row.author_id)
        product_idx = product_id_to_embedding_idx.get(row.product_id)
        content_score = np.nan
        if profile is not None and product_idx is not None:
            content_score = float(embeddings[product_idx] @ profile)
        content_rating_score = float(cosine_to_rating_scale(np.array([content_score]))[0]) if not np.isnan(content_score) else np.nan
        hybrid_score = (
            alpha * row.mf_score + (1 - alpha) * content_rating_score
            if not np.isnan(content_rating_score)
            else row.mf_score
        )
        rows.append(
            {
                "author_id": row.author_id,
                "product_id": row.product_id,
                "true_rating": row.true_rating,
                "mf_score": row.mf_score,
                "content_score": content_score,
                "content_rating_score": content_rating_score,
                "hybrid_score": hybrid_score,
                "mf_content_gap": abs(row.mf_score - content_rating_score) if not np.isnan(content_rating_score) else np.nan,
            }
        )

    features = pd.DataFrame(rows)
    user_stats = train_df.groupby("author_id")["rating"].agg(user_rating_count="size", mean_user_rating="mean").reset_index()
    product_stats = train_df.groupby("product_id")["rating"].agg(train_product_rating_count="size", mean_train_product_rating="mean").reset_index()
    product_meta_cols = [
        "product_id",
        "product_name",
        "brand_name",
        "secondary_category",
        "tertiary_category",
        "price_usd",
        "avg_product_rating",
        "num_reviews",
    ]
    features = features.merge(user_stats, on="author_id", how="left")
    features = features.merge(product_stats, on="product_id", how="left")
    features = features.merge(df_products[product_meta_cols], on="product_id", how="left")
    features = features.merge(user_profiles_df, on="author_id", how="left")
    return features


def hit_rate_at_k(
    test_df: pd.DataFrame,
    train_user_items: dict[str, set[str]],
    item_ids: np.ndarray,
    item_to_idx: dict[str, int],
    mf_model: BiasedMatrixFactorization,
    user_to_idx: dict[str, int],
    content_profiles: dict[str, np.ndarray],
    product_embeddings_for_items: np.ndarray,
    product_ids_for_items: np.ndarray,
    alpha: float,
    k_values: tuple[int, ...],
) -> dict[str, dict[str, float]]:
    metrics = {
        "mf": {f"hit_rate_at_{k}": np.nan for k in k_values},
        "content": {f"hit_rate_at_{k}": np.nan for k in k_values},
        "hybrid": {f"hit_rate_at_{k}": np.nan for k in k_values},
    }
    hits = {model_name: {k: 0 for k in k_values} for model_name in metrics}
    totals = {model_name: 0 for model_name in metrics}

    item_ids_list = item_ids.tolist()
    item_index_lookup = {product_id: idx for idx, product_id in enumerate(product_ids_for_items)}

    for row in test_df.itertuples(index=False):
        user_id = row.author_id
        true_item = row.product_id
        if user_id not in user_to_idx or true_item not in item_to_idx:
            continue

        already_rated = train_user_items.get(user_id, set())
        candidate_mask = np.array([product_id not in already_rated for product_id in item_ids_list], dtype=bool)
        candidate_ids = item_ids[candidate_mask]
        if len(candidate_ids) == 0:
            continue

        mf_scores_all = mf_model.predict_user_all(user_to_idx[user_id])
        mf_scores = mf_scores_all[candidate_mask]

        content_profile = content_profiles.get(user_id)
        content_scores = None
        hybrid_scores = None
        if content_profile is not None:
            item_embedding_indices = np.array([item_index_lookup[pid] for pid in candidate_ids])
            content_scores = product_embeddings_for_items[item_embedding_indices] @ content_profile
            content_rating_scores = cosine_to_rating_scale(content_scores)
            hybrid_scores = alpha * mf_scores + (1 - alpha) * content_rating_scores

        for model_name, scores in [("mf", mf_scores), ("content", content_scores), ("hybrid", hybrid_scores)]:
            if scores is None:
                continue
            totals[model_name] += 1
            ranked_ids = candidate_ids[np.argsort(-scores)]
            for k in k_values:
                hits[model_name][k] += int(true_item in set(ranked_ids[:k]))

    for model_name in metrics:
        for k in k_values:
            total = totals[model_name]
            metrics[model_name][f"hit_rate_at_{k}"] = float(hits[model_name][k] / total) if total else np.nan
        metrics[model_name]["evaluated_users"] = int(totals[model_name])
    return metrics


def qualitative_checks(df_products: pd.DataFrame, neighbors: pd.DataFrame, out_path: Path) -> pd.DataFrame:
    checks = []
    for label, term in [
        ("moisturizer", "moisturizer"),
        ("acne", "acne"),
        ("sunscreen_spf", "spf"),
        ("sensitive_skin", "sensitive"),
    ]:
        candidates = df_products[df_products["product_text"].str.contains(term, case=False, regex=False, na=False)]
        if candidates.empty:
            continue
        query = candidates.iloc[0]
        query_neighbors = neighbors[neighbors["product_id"] == query["product_id"]].head(5).copy()
        query_neighbors.insert(0, "query_type", label)
        query_neighbors.insert(1, "query_product_name", query["product_name"])
        checks.append(query_neighbors)
    out = pd.concat(checks, ignore_index=True) if checks else pd.DataFrame()
    out.to_csv(out_path, index=False)
    return out


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def main() -> None:
    config = parse_args()
    data_dir = Path(config.data_dir)
    artifact_dir = Path(config.artifact_dir)
    matrix_dir = artifact_dir / "matrix"
    transformer_dir = artifact_dir / "transformer"
    handoff_dir = artifact_dir / "handoff"
    for directory in [matrix_dir, transformer_dir, handoff_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    ensure_inputs(data_dir)
    write_json(artifact_dir / "run_config.json", asdict(config))

    print("Loading skincare products and reviews...")
    df_products = load_products(data_dir)
    interactions, user_profile = load_interactions(data_dir, set(df_products["product_id"]))
    train_df, test_df, split_report = make_split(
        interactions,
        config.min_user_ratings,
        config.min_product_ratings,
        config.random_state,
    )
    user_to_idx, item_to_idx, user_ids, item_ids = build_mappings(train_df)
    train_array = to_indexed_array(train_df, user_to_idx, item_to_idx)
    test_array = to_indexed_array(test_df, user_to_idx, item_to_idx)

    print("Filtered matrix:", split_report)
    sanity = {
        "no_missing_train_indices": bool(not np.isnan(train_array[:, :2]).any()),
        "no_missing_test_indices": bool(not np.isnan(test_array[:, :2]).any()),
        "train_user_count_matches_mapping": bool(train_df["author_id"].nunique() == len(user_to_idx)),
        "min_train_ratings_per_user": split_report["min_train_ratings_per_user"],
    }
    write_json(matrix_dir / "split_sanity.json", sanity)

    train_df.to_csv(matrix_dir / "train_df.csv", index=False)
    test_df.to_csv(matrix_dir / "test_df.csv", index=False)
    df_products.drop(columns=["product_text"]).to_csv(matrix_dir / "skincare_products.csv", index=False)
    user_history = make_user_history(train_df, config.liked_rating_threshold)
    user_history.to_csv(matrix_dir / "user_history.csv", index=False)

    baseline_test, metric_payload = baseline_predictions(train_df, test_df)

    print("Training Matrix Factorization...")
    mf_model = BiasedMatrixFactorization(
        n_users=len(user_ids),
        n_items=len(item_ids),
        n_factors=config.mf_factors,
        lr=config.mf_lr,
        reg=config.mf_reg,
        n_epochs=config.mf_epochs,
        random_state=config.random_state,
    ).fit(train_array, val_array=test_array)

    mf_scores = mf_model.predict_many(test_array[:, 0], test_array[:, 1])
    baseline_test["mf_score"] = mf_scores
    metric_payload["biased_mf"] = {
        "rmse": rmse(baseline_test["true_rating"], baseline_test["mf_score"]),
        "mae": mae(baseline_test["true_rating"], baseline_test["mf_score"]),
    }
    metric_payload["split_report"] = split_report
    metric_payload["mf_train_history"] = mf_model.train_history_
    metric_payload["mf_val_history"] = mf_model.val_history_
    baseline_test[["author_id", "product_id", "true_rating", "mf_score"]].to_csv(
        matrix_dir / "mf_predictions_test.csv",
        index=False,
    )

    print("Encoding transformer product text...")
    embeddings = encode_products(df_products, config.model_name, transformer_dir)
    product_id_to_embedding_idx = {pid: idx for idx, pid in enumerate(df_products["product_id"].to_numpy())}
    neighbors = save_neighbors(df_products, embeddings, transformer_dir, config.neighbor_count)
    qualitative_checks(df_products, neighbors, transformer_dir / "qualitative_checks.csv")

    train_user_items = train_df.groupby("author_id")["product_id"].apply(set).to_dict()
    profiles = user_content_profiles(
        train_df,
        product_id_to_embedding_idx,
        embeddings,
        config.liked_rating_threshold,
    )

    feature_table = prediction_feature_table(
        baseline_test[["author_id", "product_id", "true_rating", "mf_score"]],
        train_df,
        df_products,
        user_profile,
        product_id_to_embedding_idx,
        embeddings,
        profiles,
        config.hybrid_alpha,
    )
    feature_table.to_csv(handoff_dir / "bayesian_handoff_features.csv", index=False)

    hybrid_eval = feature_table.dropna(subset=["content_rating_score"]).copy()
    metric_payload["content_only"] = {
        "rmse": rmse(hybrid_eval["true_rating"], hybrid_eval["content_rating_score"]),
        "mae": mae(hybrid_eval["true_rating"], hybrid_eval["content_rating_score"]),
        "evaluated_rows": int(len(hybrid_eval)),
    }
    metric_payload["hybrid"] = {
        "rmse": rmse(hybrid_eval["true_rating"], hybrid_eval["hybrid_score"]),
        "mae": mae(hybrid_eval["true_rating"], hybrid_eval["hybrid_score"]),
        "alpha": config.hybrid_alpha,
        "evaluated_rows": int(len(hybrid_eval)),
    }

    item_embedding_indices = np.array([product_id_to_embedding_idx[pid] for pid in item_ids])
    rank_metrics = hit_rate_at_k(
        test_df,
        train_user_items,
        item_ids,
        item_to_idx,
        mf_model,
        user_to_idx,
        profiles,
        embeddings[item_embedding_indices],
        item_ids,
        config.hybrid_alpha,
        config.top_k_values,
    )
    metric_payload["ranking"] = rank_metrics
    metric_payload["decision_gate"] = {
        "hybrid_beats_mf_hit_rate_at_10": bool(
            rank_metrics["hybrid"]["hit_rate_at_10"] > rank_metrics["mf"]["hit_rate_at_10"]
        ),
        "hybrid_beats_mf_rmse": bool(metric_payload["hybrid"]["rmse"] < metric_payload["biased_mf"]["rmse"]),
    }

    write_json(matrix_dir / "metrics.json", metric_payload)
    write_json(handoff_dir / "hybrid_metrics.json", metric_payload)
    print("Wrote artifacts to", artifact_dir)
    print(json.dumps(metric_payload["decision_gate"], indent=2))


if __name__ == "__main__":
    main()
