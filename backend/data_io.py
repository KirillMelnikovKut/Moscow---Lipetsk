"""Small file and CSV primitives shared by parsers and API services."""

from __future__ import annotations

import csv
import hashlib
import io
from pathlib import Path

from backend.config import DATA_FIELDS
from backend.errors import DataError


def read_file(path: Path) -> tuple[bytes, str]:
    try:
        content = path.read_bytes()
    except FileNotFoundError as exc:
        raise DataError(f"Файл не найден: {path.name}") from exc
    if not content:
        raise DataError(f"Файл пуст: {path.name}")
    return content, hashlib.sha256(content).hexdigest()[:16]


def file_status(path: Path) -> dict:
    try:
        content, version = read_file(path)
    except DataError as exc:
        return {"available": False, "version": None, "error": str(exc)}
    return {"available": True, "version": version, "bytes": len(content)}


def csv_rows(content: bytes, required: set[str], filename: str) -> list[dict[str, str]]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise DataError(f"{filename}: требуется кодировка UTF-8") from exc
    reader = csv.DictReader(io.StringIO(text))
    fields = set(reader.fieldnames or [])
    missing = required - fields
    if missing:
        raise DataError(f"{filename}: отсутствуют поля {', '.join(sorted(missing))}")
    rows = list(reader)
    if not rows:
        raise DataError(f"{filename}: нет строк данных")
    return rows


def read_dataset_rows(path: Path) -> tuple[list[dict[str, str]], str]:
    content, version = read_file(path)
    return csv_rows(content, set(DATA_FIELDS), path.name), version


def projected_csv(rows: list[dict[str, str]], fields: tuple[str, ...]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    writer.writerows({field: row.get(field, "") for field in fields} for row in rows)
    return output.getvalue().encode("utf-8")
