from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class BestRun:
    project_root: Path
    run_id: str
    run_dir: Path
    test_bnn_rmse: float
    summary: dict

    @property
    def step4_dir(self) -> Path:
        return self.run_dir / "step4_features"

    @property
    def step5_dir(self) -> Path:
        return self.run_dir / "step5_bnn"


def find_project_root(start: Path | None = None) -> Path:
    """Find the project root by walking upward until version results exist."""
    current = (start or Path.cwd()).resolve()

    for candidate in [current, *current.parents]:
        if (candidate / "artifacts" / "versions" / "results_log.csv").exists():
            return candidate

    raise FileNotFoundError(
        "Could not find artifacts/versions/results_log.csv from "
        f"{current}. Run from the up-skin project or set UPSKIN_PROJECT_ROOT."
    )


def resolve_project_root() -> Path:
    """Resolve project root from env-compatible cwd discovery."""
    import os

    configured = os.getenv("UPSKIN_PROJECT_ROOT")
    if configured:
        root = Path(configured).expanduser().resolve()
        if not (root / "artifacts" / "versions" / "results_log.csv").exists():
            raise FileNotFoundError(
                "UPSKIN_PROJECT_ROOT does not contain artifacts/versions/results_log.csv: "
                f"{root}"
            )
        return root

    return find_project_root()


def resolve_best_run(project_root: Path | None = None) -> BestRun:
    """Pick the saved model version with the lowest test BNN RMSE."""
    root = project_root or resolve_project_root()
    results_path = root / "artifacts" / "versions" / "results_log.csv"
    results = pd.read_csv(results_path)

    required = {"run_id", "test_bnn_rmse"}
    missing = required - set(results.columns)
    if missing:
        raise ValueError(f"Missing required columns in {results_path}: {sorted(missing)}")

    results["test_bnn_rmse"] = pd.to_numeric(results["test_bnn_rmse"], errors="coerce")
    scored = results.dropna(subset=["test_bnn_rmse"]).sort_values("test_bnn_rmse")
    if scored.empty:
        raise ValueError(f"No usable test_bnn_rmse values found in {results_path}")

    row = scored.iloc[0]
    run_id = str(row["run_id"])
    run_dir = root / "artifacts" / "versions" / run_id
    summary_path = run_dir / "final_pipeline_summary.json"
    if not summary_path.exists():
        raise FileNotFoundError(f"Best run summary not found: {summary_path}")

    return BestRun(
        project_root=root,
        run_id=run_id,
        run_dir=run_dir,
        test_bnn_rmse=float(row["test_bnn_rmse"]),
        summary=json.loads(summary_path.read_text()),
    )


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())
