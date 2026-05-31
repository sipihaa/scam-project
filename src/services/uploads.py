from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Iterable

from src.services.paths import ProjectPaths


def _safe_filename(name: str) -> str:
    path_name = Path(name).name
    safe = "".join(char if char.isalnum() or char in " ._-" else "_" for char in path_name)
    return safe.strip() or "uploaded.csv"


def create_uploaded_workspace(uploaded_files: Iterable[object]) -> tuple[ProjectPaths, list[str]]:
    root = Path(tempfile.mkdtemp(prefix="transport_fraud_upload_"))
    raw_dir = root / "raw"
    artifacts_dir = root / "artifacts"
    rules_dir = artifacts_dir / "rules"
    ml_dir = artifacts_dir / "ml"
    raw_dir.mkdir(parents=True, exist_ok=True)
    rules_dir.mkdir(parents=True, exist_ok=True)
    ml_dir.mkdir(parents=True, exist_ok=True)

    saved_names: list[str] = []
    used_names: set[str] = set()
    for index, uploaded_file in enumerate(uploaded_files, start=1):
        original_name = getattr(uploaded_file, "name", f"uploaded_{index}.csv")
        safe_name = _safe_filename(original_name)
        if safe_name in used_names:
            stem = Path(safe_name).stem
            suffix = Path(safe_name).suffix or ".csv"
            safe_name = f"{stem}_{index}{suffix}"
        used_names.add(safe_name)

        target = raw_dir / safe_name
        target.write_bytes(uploaded_file.getbuffer())
        saved_names.append(safe_name)

    paths = ProjectPaths(
        root=root,
        raw_data=raw_dir,
        reference_data=root / "reference",
        artifacts=artifacts_dir,
        rules_artifacts=rules_dir,
        ml_artifacts=ml_dir,
    )
    return paths, saved_names
