from __future__ import annotations

import hashlib
import io
import zipfile
from pathlib import Path

import pandas as pd


SUPPORTED_PATTERNS = ("*.csv", "*.xlsx", "*.xls", "*.xltx", "*.cell", "*.zip")
DATE_FORMAT = "%d.%m.%Y %H:%M:%S"


def sha1(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def list_input_files(data_dir: Path | str) -> list[Path]:
    data_dir = Path(data_dir)
    if not data_dir.exists():
        raise FileNotFoundError(f"Папка с данными не найдена: {data_dir}")

    files: list[Path] = []
    for pattern in SUPPORTED_PATTERNS:
        files.extend(data_dir.glob(pattern))

    unique_files = []
    seen_hashes = set()
    for path in sorted(files):
        if path.name.startswith("."):
            continue
        file_hash = sha1(path)
        if file_hash in seen_hashes:
            continue
        seen_hashes.add(file_hash)
        unique_files.append(path)

    if not unique_files:
        raise FileNotFoundError(f"В папке {data_dir} нет поддерживаемых файлов")
    return unique_files


def read_csv_file(path: Path) -> pd.DataFrame:
    encodings = ("cp1251", "utf-8-sig", "utf-8", "latin1")
    separators = (";", ",", "\t", "|")
    for separator in separators:
        for encoding in encodings:
            try:
                frame = pd.read_csv(path, sep=separator, encoding=encoding, dtype=str)
            except Exception:
                continue
            if len(frame.columns) > 1:
                return frame
    raise ValueError(f"Не удалось прочитать CSV: {path.name}")


def read_excel_file(path: Path) -> pd.DataFrame:
    return pd.read_excel(path, dtype=str)


def read_zip_file(path: Path) -> pd.DataFrame:
    frames = []
    with zipfile.ZipFile(path, "r") as archive:
        for inner_name in archive.namelist():
            if "__MACOSX" in inner_name or Path(inner_name).name.startswith("."):
                continue
            suffix = Path(inner_name).suffix.lower()
            try:
                with archive.open(inner_name) as file:
                    if suffix == ".csv":
                        text = file.read().decode("utf-8-sig", errors="replace")
                        frames.append(pd.read_csv(io.StringIO(text), sep=";", dtype=str))
                    elif suffix in {".xlsx", ".xls"}:
                        frames.append(pd.read_excel(file, dtype=str))
            except Exception:
                continue
    if not frames:
        raise ValueError(f"В ZIP-архиве не найдено CSV/XLSX файлов: {path.name}")
    return pd.concat(frames, ignore_index=True)


def read_any_file(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return read_csv_file(path)
    if suffix in {".xlsx", ".xls", ".xltx", ".cell"}:
        return read_excel_file(path)
    if suffix == ".zip":
        return read_zip_file(path)
    raise ValueError(f"Неподдерживаемый формат: {path.name}")


def normalize_transactions(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    data.columns = [str(column).strip().upper() for column in data.columns]
    if "DATE" in data.columns:
        data = data[data["DATE"].astype(str).str.upper() != "DATE"].copy()

    for column in data.columns:
        if data[column].dtype == object:
            data[column] = data[column].astype(str).str.strip()

    required = {"DATE", "CARD", "TRM_ID"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Не хватает обязательных колонок: {', '.join(sorted(missing))}")

    data["datetime"] = pd.to_datetime(data["DATE"], format=DATE_FORMAT, errors="coerce")
    data = data.dropna(subset=["datetime", "CARD", "TRM_ID"]).copy()
    data["date"] = data["datetime"].dt.date
    data["hour"] = data["datetime"].dt.hour
    data["minute"] = data["datetime"].dt.minute
    data["second"] = data["datetime"].dt.second
    data["time_sec"] = data["datetime"].dt.floor("s")
    data["weekday"] = data["datetime"].dt.dayofweek

    for column in ("CARD", "TRM_ID", "ROUTE_NUM", "CAT", "CAT_TYPE", "TRC_ID"):
        if column in data.columns:
            data[column] = data[column].astype(str).str.strip()
            data.loc[data[column].isin(["", "nan", "None", "<NA>"]), column] = pd.NA

    if "CAT" in data.columns:
        data["CAT_NUM"] = pd.to_numeric(data["CAT"], errors="coerce")
    else:
        data["CAT_NUM"] = pd.NA

    if "SUMM" in data.columns:
        data["SUMM_NUM"] = pd.to_numeric(data["SUMM"], errors="coerce")
    else:
        data["SUMM_NUM"] = pd.NA

    if "VEHICLE" in data.columns:
        data["VEHICLE"] = data["VEHICLE"].fillna("")

    return data


def remove_near_duplicates(data: pd.DataFrame) -> pd.DataFrame:
    if not {"CARD", "TRM_ID", "datetime"}.issubset(data.columns):
        return data.drop_duplicates().copy()

    clean = data.drop_duplicates().sort_values(["CARD", "TRM_ID", "datetime"]).copy()
    duplicate_flag = (
        clean["CARD"].eq(clean["CARD"].shift(1))
        & clean["TRM_ID"].eq(clean["TRM_ID"].shift(1))
        & ((clean["datetime"] - clean["datetime"].shift(1)).dt.total_seconds().abs() <= 2)
    )
    return clean.loc[~duplicate_flag].copy()


def load_transactions(data_dir: Path | str) -> pd.DataFrame:
    frames = []
    for path in list_input_files(data_dir):
        frame = read_any_file(path)
        frames.append(frame)
    data = pd.concat(frames, ignore_index=True)
    data = normalize_transactions(data)
    data = remove_near_duplicates(data)
    return data.reset_index(drop=True)
