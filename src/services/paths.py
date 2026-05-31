from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class ProjectPaths:
    root: Path = ROOT_DIR
    raw_data: Path = ROOT_DIR / "data" / "raw"
    reference_data: Path = ROOT_DIR / "data" / "reference"
    artifacts: Path = ROOT_DIR / "artifacts"
    rules_artifacts: Path = ROOT_DIR / "artifacts" / "rules"
    ml_artifacts: Path = ROOT_DIR / "artifacts" / "ml"

    @property
    def fraud_report(self) -> Path:
        return self.rules_artifacts / "fraud_report.csv"

    @property
    def dashboard_json(self) -> Path:
        return self.rules_artifacts / "dashboard_data.json"

    @property
    def labels(self) -> Path:
        return self.ml_artifacts / "card_labels.csv"

    @property
    def features(self) -> Path:
        return self.ml_artifacts / "features.csv"

    @property
    def model(self) -> Path:
        return self.ml_artifacts / "discovery_model.pkl"


PATHS = ProjectPaths()


def ensure_artifact_dirs(paths: ProjectPaths = PATHS) -> None:
    paths.rules_artifacts.mkdir(parents=True, exist_ok=True)
    paths.ml_artifacts.mkdir(parents=True, exist_ok=True)
