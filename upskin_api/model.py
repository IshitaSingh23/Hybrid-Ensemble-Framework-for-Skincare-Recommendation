from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
from torch import nn

from .artifacts import BestRun, read_json, resolve_best_run


class MCDropoutBNN(nn.Module):
    def __init__(
        self,
        input_dim: int,
        hidden_1: int = 128,
        hidden_2: int = 64,
        dropout_rate: float = 0.2,
    ) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_1),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_1, hidden_2),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_2, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        raw_output = self.network(x)
        return 1.0 + 4.0 * torch.sigmoid(raw_output)


@dataclass
class ModelBundle:
    best_run: BestRun
    model: MCDropoutBNN
    preprocessor: object
    embedding_pca: object
    feature_schema: dict
    model_config: dict
    all_metrics: dict
    device: torch.device

    @property
    def uses_mf_proxy(self) -> bool:
        return bool(self.best_run.summary.get("uses_mf_proxy", True))

    @property
    def mf_proxy_note(self) -> str:
        return str(
            self.best_run.summary.get(
                "mf_proxy_note",
                self.best_run.summary.get(
                    "known_limitation",
                    "Full candidate-level MF scores were not exported; the API uses a user/product mean proxy.",
                ),
            )
        )

    @property
    def calibration_multiplier(self) -> float:
        report = self.all_metrics.get("calibration_report", {})
        return float(report.get("uncertainty_interval_multiplier", 1.96))

    @property
    def low_uncertainty_threshold(self) -> float:
        report = self.all_metrics.get("calibration_report", {})
        return float(report.get("validation_low_uncertainty_threshold", 0.06267690658569336))

    @property
    def high_uncertainty_threshold(self) -> float:
        report = self.all_metrics.get("calibration_report", {})
        return float(report.get("validation_high_uncertainty_threshold", 0.10898177077372868))

    def confidence_bucket(self, uncertainty: float) -> str:
        if uncertainty <= self.low_uncertainty_threshold:
            return "high_confidence"
        if uncertainty <= self.high_uncertainty_threshold:
            return "medium_confidence"
        return "low_confidence"

    def transform_features(self, features: pd.DataFrame) -> np.ndarray:
        feature_columns = self.feature_schema["feature_columns"]
        missing = [col for col in feature_columns if col not in features.columns]
        if missing:
            raise ValueError(f"Missing model feature columns: {missing}")
        X = self.preprocessor.transform(features[feature_columns])
        return np.asarray(X, dtype=np.float32)

    def predict_mc(self, features: pd.DataFrame, mc_samples: int, batch_size: int = 512) -> dict[str, np.ndarray]:
        X = self.transform_features(features)
        self.model.train()
        samples: list[np.ndarray] = []

        with torch.no_grad():
            for _ in range(mc_samples):
                predictions: list[np.ndarray] = []
                for start in range(0, len(X), batch_size):
                    batch = torch.tensor(
                        X[start : start + batch_size],
                        dtype=torch.float32,
                        device=self.device,
                    )
                    preds = self.model(batch).detach().cpu().numpy().ravel()
                    predictions.append(preds)
                samples.append(np.concatenate(predictions))

        self.model.eval()
        sample_matrix = np.vstack(samples)
        mean = np.clip(sample_matrix.mean(axis=0), 1, 5)
        std = sample_matrix.std(axis=0)
        half_width = std * self.calibration_multiplier

        return {
            "mean": mean,
            "std": std,
            "lower_95": np.clip(mean - half_width, 1, 5),
            "upper_95": np.clip(mean + half_width, 1, 5),
        }


def load_model_bundle(project_root: Path | None = None) -> ModelBundle:
    best_run = resolve_best_run(project_root)
    step4_dir = best_run.step4_dir
    step5_dir = best_run.step5_dir

    checkpoint_path = step5_dir / "mc_dropout_bnn_model.pt"
    preprocessor_path = step5_dir / "preprocessor.joblib"
    model_config_path = step5_dir / "model_config.json"
    all_metrics_path = step5_dir / "all_metrics.json"
    feature_schema_path = step4_dir / "feature_schema.json"
    embedding_pca_path = step4_dir / "embedding_pca.joblib"

    required_paths = [
        checkpoint_path,
        preprocessor_path,
        model_config_path,
        all_metrics_path,
        feature_schema_path,
        embedding_pca_path,
    ]
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required model artifacts: " + ", ".join(missing))

    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    model_config = read_json(model_config_path)
    feature_schema = read_json(feature_schema_path)

    model = MCDropoutBNN(
        input_dim=int(model_config["input_dim"]),
        hidden_1=int(model_config.get("hidden_1", 128)),
        hidden_2=int(model_config.get("hidden_2", 64)),
        dropout_rate=float(model_config.get("dropout_rate", 0.2)),
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    return ModelBundle(
        best_run=best_run,
        model=model,
        preprocessor=joblib.load(preprocessor_path),
        embedding_pca=joblib.load(embedding_pca_path),
        feature_schema=feature_schema,
        model_config=model_config,
        all_metrics=read_json(all_metrics_path),
        device=torch.device("cpu"),
    )
