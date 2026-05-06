from __future__ import annotations

import math
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from .artifacts import read_json, resolve_project_root
from .model import ModelBundle, load_model_bundle
from .schemas import RecommendationFilters


def _clean_string(value: object, default: str = "Unknown") -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return default
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return default
    return text


def _split_ids(value: object) -> list[str]:
    text = "" if value is None or (isinstance(value, float) and math.isnan(value)) else str(value)
    return [part for part in text.split("|") if part]


def _safe_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(out):
        return None
    return out


def _category(row: pd.Series) -> str:
    secondary = _clean_string(row.get("secondary_category"))
    tertiary = _clean_string(row.get("tertiary_category"))
    return f"{secondary} / {tertiary}"


@dataclass(frozen=True)
class Profile:
    author_id: str | None
    source_product_ids: list[str]
    already_seen_product_ids: set[str]
    user_rating_count: int
    mean_user_rating: float
    profile_product_count: int
    liked_product_count: int
    mean_train_rating: float
    profile_vector: np.ndarray


class RecommendationService:
    def __init__(self, project_root: Path | None = None, model_bundle: ModelBundle | None = None) -> None:
        self.project_root = project_root or resolve_project_root()
        self.bundle = model_bundle or load_model_bundle(self.project_root)
        self.artifact_dir = self.project_root / "artifacts"
        self.run_config = read_json(self.artifact_dir / "run_config.json")
        self.matrix_metadata = self._load_matrix_metadata()
        self.hybrid_alpha = float(self.run_config.get("hybrid_alpha", 0.7))
        self.mc_samples = int(os.getenv("UPSKIN_MC_SAMPLES", self.bundle.model_config.get("mc_samples", 100)))

        self.product_catalog = self._load_product_catalog()
        self.product_ids = self.product_catalog["product_id"].astype(str).to_numpy()
        self.product_id_to_index = {product_id: idx for idx, product_id in enumerate(self.product_ids)}
        self.product_embeddings = self._load_product_embeddings()
        self.product_pca = self._build_product_pca_frame()
        self.user_history = self._load_user_history()
        self.train_df = self._load_train_df()
        self.global_mean_rating = float(self.train_df["rating"].mean())
        self.product_rating_mean = self.train_df.groupby("product_id")["rating"].mean()
        self.product_rating_count = self.train_df.groupby("product_id")["rating"].size()
        self.filter_report = self.bundle.best_run.summary.get("filter_report", {})

    def _load_product_catalog(self) -> pd.DataFrame:
        path = self.artifact_dir / "transformer" / "product_catalog.csv"
        df = pd.read_csv(path, dtype={"product_id": "string"}).copy()
        df["product_id"] = df["product_id"].astype(str)
        for col in ["product_name", "brand_name", "secondary_category", "tertiary_category", "ingredients", "highlights"]:
            if col in df.columns:
                df[col] = df[col].map(_clean_string)
        return df.drop_duplicates(subset=["product_id"]).reset_index(drop=True)

    def _load_product_embeddings(self) -> np.ndarray:
        path = self.artifact_dir / "transformer" / "product_embeddings.npz"
        data = np.load(path, allow_pickle=True)
        embedding_ids = data["product_ids"].astype(str)
        if not np.array_equal(embedding_ids, self.product_ids):
            raise ValueError("Product embedding IDs do not align with product_catalog.csv")
        return np.asarray(data["embeddings"], dtype=np.float32)

    def _build_product_pca_frame(self) -> pd.DataFrame:
        reduced = self.bundle.embedding_pca.transform(self.product_embeddings)
        columns = self.bundle.feature_schema["reduced_embedding_columns"]
        return pd.DataFrame(reduced, columns=columns).assign(product_id=self.product_ids)

    def _load_user_history(self) -> pd.DataFrame:
        path = self.artifact_dir / "matrix" / "user_history.csv"
        df = pd.read_csv(path, dtype={"author_id": "string"}).copy()
        df["author_id"] = df["author_id"].astype(str)
        return df

    def _load_train_df(self) -> pd.DataFrame:
        path = self.artifact_dir / "matrix" / "train_df.csv"
        df = pd.read_csv(path, dtype={"author_id": "string", "product_id": "string"}).copy()
        df["author_id"] = df["author_id"].astype(str)
        df["product_id"] = df["product_id"].astype(str)
        return df

    def _load_matrix_metadata(self) -> dict:
        """Return matrix-score metadata for the selected model run."""
        step1_config_path = self.bundle.best_run.run_dir / "step1_matrix_ensemble" / "run_config.json"
        if step1_config_path.exists():
            metadata = read_json(step1_config_path)
        else:
            metadata = {}

        feature_columns = set(self.bundle.feature_schema.get("feature_columns", []))
        if not metadata.get("canonical_matrix_model"):
            metadata["canonical_matrix_model"] = (
                "ridge_ensemble" if "ridge_ensemble_score" in feature_columns else "matrix_factorization"
            )
        if not metadata.get("mf_score_semantics"):
            metadata["mf_score_semantics"] = (
                "ridge_ensemble_matrix_completion_score"
                if metadata["canonical_matrix_model"] == "ridge_ensemble"
                else "matrix_factorization_score"
            )
        return metadata

    def health(self) -> dict:
        return {
            "status": "ok",
            "run_id": self.bundle.best_run.run_id,
            "canonical_matrix_model": self.matrix_metadata.get("canonical_matrix_model"),
            "mf_score_semantics": self.matrix_metadata.get("mf_score_semantics"),
            "best_model_rmse": self.bundle.best_run.test_bnn_rmse,
            "model_type": self.bundle.model_config.get("model_type"),
            "product_count": int(len(self.product_catalog)),
            "demo_user_count": int(len(self.user_history)),
            "uses_mf_proxy": self.bundle.uses_mf_proxy,
            "mf_proxy_note": self.bundle.mf_proxy_note,
        }

    def metrics(self) -> dict:
        summary = self.bundle.best_run.summary
        best_model = summary.get("best_model", {})
        uncertainty = summary.get("uncertainty", {})
        return {
            "run_id": self.bundle.best_run.run_id,
            "canonical_matrix_model": self.matrix_metadata.get("canonical_matrix_model"),
            "mf_score_semantics": self.matrix_metadata.get("mf_score_semantics"),
            "best_model": best_model,
            "uncertainty": uncertainty,
            "all_metrics": {
                "test_decision_report": self.bundle.all_metrics.get("test_decision_report", {}),
                "calibration_report": self.bundle.all_metrics.get("calibration_report", {}),
                "confidence_bucket_summary": self.bundle.all_metrics.get("confidence_bucket_summary", []),
            },
            "uses_mf_proxy": self.bundle.uses_mf_proxy,
            "mf_proxy_note": self.bundle.mf_proxy_note,
            "stale_notes_file": str(self.project_root / "stale.md"),
        }

    def demo_users(self, limit: int = 25) -> list[dict]:
        df = self.user_history.sort_values(["user_rating_count", "author_id"], ascending=[False, True]).head(limit)
        users = []
        for row in df.itertuples(index=False):
            liked_ids = _split_ids(getattr(row, "liked_product_ids", ""))
            rated_ids = _split_ids(getattr(row, "rated_product_ids", ""))
            users.append(
                {
                    "author_id": str(row.author_id),
                    "user_rating_count": int(row.user_rating_count),
                    "mean_user_rating": float(row.mean_user_rating),
                    "liked_product_count": len(liked_ids),
                    "rated_product_count": len(rated_ids),
                    "liked_product_ids": liked_ids[:10],
                }
            )
        return users

    def search_products(self, query: str = "", limit: int = 20) -> list[dict]:
        q = query.strip().lower()
        df = self.product_catalog.copy()
        if q:
            haystack = (
                df["product_name"].fillna("")
                + " "
                + df["brand_name"].fillna("")
                + " "
                + df["secondary_category"].fillna("")
                + " "
                + df["tertiary_category"].fillna("")
            ).str.lower()
            df = df[haystack.str.contains(q, regex=False, na=False)].copy()
        else:
            df = df.sort_values(["loves_count", "avg_product_rating"], ascending=[False, False])

        return [self._product_search_payload(row) for _, row in df.head(limit).iterrows()]

    def _product_search_payload(self, row: pd.Series) -> dict:
        return {
            "product_id": str(row["product_id"]),
            "product_name": _clean_string(row.get("product_name"), "Unnamed Product"),
            "brand_name": _clean_string(row.get("brand_name")),
            "category": _category(row),
            "price_usd": _safe_float(row.get("price_usd")),
            "avg_product_rating": _safe_float(row.get("avg_product_rating")),
            "loves_count": int(row["loves_count"]) if pd.notna(row.get("loves_count")) else None,
        }

    def recommend_for_demo_user(self, author_id: str, top_n: int = 10) -> dict:
        user_rows = self.user_history[self.user_history["author_id"] == str(author_id)]
        if user_rows.empty:
            raise KeyError(f"Unknown demo user: {author_id}")
        row = user_rows.iloc[0]
        liked_ids = _split_ids(row.get("liked_product_ids"))
        rated_ids = _split_ids(row.get("rated_product_ids"))
        source_ids = liked_ids or rated_ids
        profile = self._build_profile(
            author_id=str(author_id),
            source_product_ids=source_ids,
            already_seen_product_ids=set(rated_ids),
            user_rating_count=int(row["user_rating_count"]),
            mean_user_rating=float(row["mean_user_rating"]),
            profile_product_count=len(rated_ids),
            liked_product_count=len(liked_ids),
            mean_train_rating=float(row["mean_user_rating"]),
        )
        return self._recommend(profile, top_n=top_n, filters=RecommendationFilters())

    def recommend_for_custom(
        self,
        liked_product_ids: Iterable[str],
        top_n: int = 10,
        filters: RecommendationFilters | None = None,
    ) -> dict:
        source_ids = [str(product_id) for product_id in liked_product_ids]
        known_source_ids = [product_id for product_id in source_ids if product_id in self.product_id_to_index]
        if not known_source_ids:
            raise ValueError("None of the liked_product_ids exist in the product catalog.")

        source_stats = []
        for product_id in known_source_ids:
            if product_id in self.product_rating_mean.index:
                source_stats.append(float(self.product_rating_mean.loc[product_id]))
            else:
                row = self.product_catalog[self.product_catalog["product_id"] == product_id].iloc[0]
                avg_rating = _safe_float(row.get("avg_product_rating"))
                if avg_rating is not None:
                    source_stats.append(avg_rating)
        inferred_mean = float(np.mean(source_stats)) if source_stats else self.global_mean_rating

        profile = self._build_profile(
            author_id=None,
            source_product_ids=known_source_ids,
            already_seen_product_ids=set(known_source_ids),
            user_rating_count=len(known_source_ids),
            mean_user_rating=inferred_mean,
            profile_product_count=len(known_source_ids),
            liked_product_count=len(known_source_ids),
            mean_train_rating=inferred_mean,
        )
        return self._recommend(profile, top_n=top_n, filters=filters or RecommendationFilters())

    def _build_profile(
        self,
        author_id: str | None,
        source_product_ids: list[str],
        already_seen_product_ids: set[str],
        user_rating_count: int,
        mean_user_rating: float,
        profile_product_count: int,
        liked_product_count: int,
        mean_train_rating: float,
    ) -> Profile:
        indices = [self.product_id_to_index[pid] for pid in source_product_ids if pid in self.product_id_to_index]
        if not indices:
            raise ValueError("Profile has no products with available embeddings.")

        profile_vector = self.product_embeddings[indices].mean(axis=0)
        norm = np.linalg.norm(profile_vector)
        if norm > 0:
            profile_vector = profile_vector / norm

        return Profile(
            author_id=author_id,
            source_product_ids=source_product_ids,
            already_seen_product_ids=already_seen_product_ids,
            user_rating_count=user_rating_count,
            mean_user_rating=mean_user_rating,
            profile_product_count=profile_product_count,
            liked_product_count=liked_product_count,
            mean_train_rating=mean_train_rating,
            profile_vector=profile_vector.astype(np.float32),
        )

    def _recommend(self, profile: Profile, top_n: int, filters: RecommendationFilters) -> dict:
        candidates = self._candidate_features(profile, filters)
        if candidates.empty:
            recommendations: list[dict] = []
        else:
            mc = self.bundle.predict_mc(candidates, mc_samples=self.mc_samples)
            scored = candidates.copy()
            scored["predicted_score"] = mc["mean"]
            scored["uncertainty"] = mc["std"]
            scored["predicted_lower_95"] = mc["lower_95"]
            scored["predicted_upper_95"] = mc["upper_95"]
            scored["risk_adjusted_score"] = np.clip(scored["predicted_score"] - 0.5 * scored["uncertainty"], 1, 5)
            scored["confidence_bucket"] = [
                self.bundle.confidence_bucket(value) for value in scored["uncertainty"]
            ]
            ranked = scored.sort_values(
                ["risk_adjusted_score", "predicted_score", "avg_product_rating", "loves_count"],
                ascending=[False, False, False, False],
            ).head(top_n)
            recommendations = [self._recommendation_payload(row) for _, row in ranked.iterrows()]

        return {
            "run_id": self.bundle.best_run.run_id,
            "best_model_rmse": self.bundle.best_run.test_bnn_rmse,
            "uses_mf_proxy": self.bundle.uses_mf_proxy,
            "mf_proxy_note": self.bundle.mf_proxy_note,
            "recommendations": recommendations,
        }

    def _candidate_features(self, profile: Profile, filters: RecommendationFilters) -> pd.DataFrame:
        df = self.product_catalog.copy()
        excluded = set(profile.already_seen_product_ids) | {str(pid) for pid in filters.exclude_product_ids}
        if excluded:
            df = df[~df["product_id"].isin(excluded)].copy()

        if filters.secondary_categories:
            allowed = {category.strip() for category in filters.secondary_categories if category.strip()}
            df = df[df["secondary_category"].isin(allowed)].copy()

        if filters.max_price_usd is not None:
            df = df[pd.to_numeric(df["price_usd"], errors="coerce") <= filters.max_price_usd].copy()

        if not filters.include_out_of_stock and "out_of_stock" in df.columns:
            df = df[pd.to_numeric(df["out_of_stock"], errors="coerce").fillna(0).astype(int) == 0].copy()

        excluded_secondary = set(self.filter_report.get("excluded_secondary_categories", []))
        if excluded_secondary:
            df = df[~df["secondary_category"].isin(excluded_secondary)].copy()

        excluded_tertiary = set(self.filter_report.get("excluded_tertiary_categories", []))
        if excluded_tertiary:
            df = df[~df["tertiary_category"].isin(excluded_tertiary)].copy()

        if df.empty:
            return df

        content_scores = self.product_embeddings[df.index.to_numpy()] @ profile.profile_vector
        df["content_score"] = content_scores
        df["content_rating_score"] = 1 + 4 * np.clip(df["content_score"], 0, 1)

        product_means = df["product_id"].map(self.product_rating_mean).fillna(df["avg_product_rating"]).fillna(self.global_mean_rating)
        df["mf_score"] = np.clip(
            self.global_mean_rating
            + (profile.mean_user_rating - self.global_mean_rating)
            + (product_means - self.global_mean_rating),
            1,
            5,
        )
        df["hybrid_score"] = self.hybrid_alpha * df["mf_score"] + (1 - self.hybrid_alpha) * df["content_rating_score"]
        df["mf_content_gap"] = (df["mf_score"] - df["content_rating_score"]).abs()

        df["baseline_score"] = np.clip(profile.mean_user_rating, 1, 5)
        df["legacy_mf_score"] = df["mf_score"]
        df["item_knn_score"] = df["mf_score"]
        df["metadata_content_score"] = df["content_rating_score"]
        df["ridge_ensemble_score"] = df["mf_score"]
        df["gb_ensemble_score"] = df["mf_score"]
        df["rf_ensemble_score"] = df["mf_score"]
        df["product_rating_count"] = df["product_id"].map(self.product_rating_count).fillna(0).astype(int)
        df["product_avg_rating"] = product_means

        component_cols = [
            "baseline_score",
            "legacy_mf_score",
            "item_knn_score",
            "metadata_content_score",
        ]
        df["pred_mean"] = df[component_cols].mean(axis=1)
        df["pred_std"] = df[component_cols].std(axis=1).fillna(0)
        df["pred_min"] = df[component_cols].min(axis=1)
        df["pred_max"] = df[component_cols].max(axis=1)
        df["pred_range"] = df["pred_max"] - df["pred_min"]
        df["component_score_mean"] = df["pred_mean"]
        df["component_score_std"] = df["pred_std"]
        df["component_score_range"] = df["pred_range"]

        df["user_rating_count"] = profile.user_rating_count
        df["mean_user_rating"] = profile.mean_user_rating
        df["profile_product_count"] = profile.profile_product_count
        df["liked_product_count"] = profile.liked_product_count
        df["mean_train_rating"] = profile.mean_train_rating

        for col in ["price_usd", "avg_product_rating", "num_reviews", "loves_count"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["log1p_price_usd"] = np.log1p(df["price_usd"].clip(lower=0))
        df["log1p_num_reviews"] = np.log1p(df["num_reviews"].clip(lower=0))
        df["log1p_loves_count"] = np.log1p(df["loves_count"].clip(lower=0))
        df["has_liked_history"] = int(profile.liked_product_count > 0)
        df["user_history_strength"] = np.log1p(profile.user_rating_count)
        df["profile_history_strength"] = np.log1p(profile.profile_product_count)

        top_brands = set(self.bundle.feature_schema.get("top_brands", []))
        df["brand_name_grouped"] = np.where(df["brand_name"].isin(top_brands), df["brand_name"], "Other Brand")
        df["secondary_category"] = df["secondary_category"].map(_clean_string)
        df["tertiary_category"] = df["tertiary_category"].map(_clean_string)

        df = df.merge(self.product_pca, on="product_id", how="left", validate="one_to_one")
        return df.reset_index(drop=True)

    def _recommendation_payload(self, row: pd.Series) -> dict:
        return {
            "product_id": str(row["product_id"]),
            "product_name": _clean_string(row.get("product_name"), "Unnamed Product"),
            "brand_name": _clean_string(row.get("brand_name")),
            "category": _category(row),
            "predicted_score": round(float(row["predicted_score"]), 4),
            "risk_adjusted_score": round(float(row["risk_adjusted_score"]), 4),
            "uncertainty": round(float(row["uncertainty"]), 4),
            "confidence_bucket": str(row["confidence_bucket"]),
            "predicted_interval": {
                "lower": round(float(row["predicted_lower_95"]), 4),
                "upper": round(float(row["predicted_upper_95"]), 4),
                "level": "calibrated_95",
            },
            "explanation": self._explain(row),
        }

    def _explain(self, row: pd.Series) -> str:
        confidence_phrase = {
            "high_confidence": "high confidence",
            "medium_confidence": "moderate confidence",
            "low_confidence": "lower confidence",
        }.get(str(row["confidence_bucket"]), "measured confidence")
        signals = self._ingredient_signals(row)
        signal_text = f" It also shows ingredient/content signals for {signals}." if signals else ""
        return (
            f"Recommended as a {_clean_string(row.get('tertiary_category'))} product with {confidence_phrase} "
            f"because its product text is similar to the selected liked products.{signal_text} "
            f"Predicted score: {float(row['predicted_score']):.2f}; uncertainty: {float(row['uncertainty']):.3f}."
        )

    def _ingredient_signals(self, row: pd.Series) -> str:
        text = f"{row.get('ingredients', '')} {row.get('highlights', '')}".lower()
        groups = {
            "hydration": ["hyaluronic", "glycerin", "squalane", "aloe"],
            "barrier support": ["ceramide", "peptide", "niacinamide", "panthenol"],
            "brightening": ["vitamin c", "ascorbic", "licorice", "niacinamide"],
            "acne/oil control": ["salicylic", "bha", "tea tree"],
            "soothing": ["oat", "cica", "centella", "allantoin"],
            "exfoliation": ["lactic acid", "glycolic", "aha", "papain"],
        }
        found = []
        for label, terms in groups.items():
            matched = [term for term in terms if term in text]
            if matched:
                found.append(f"{label} ({', '.join(matched[:2])})")
        return "; ".join(found[:3])


@lru_cache(maxsize=1)
def get_service() -> RecommendationService:
    return RecommendationService()
