"""Use cases that combine stored files with parsers and analysis algorithms."""

from __future__ import annotations

from functools import lru_cache

from backend.analysis import analyze
from backend.config import (
    DATA_VALUE_FIELDS,
    FULL_DATA,
    MISSING_DATA,
    RESTORED_DATA,
    TELEMETRY_FIELDS,
    TERRAIN_FIELDS,
)
from backend.data_io import file_status, projected_csv, read_dataset_rows
from backend.errors import DataError
from backend.parsers import parse_telemetry, parse_terrain
from backend.restoration import restore_missing_values


def dataset_status() -> dict:
    restored_status = file_status(RESTORED_DATA)
    return {
        "terrain": restored_status,
        "telemetry": restored_status,
        "full": file_status(FULL_DATA),
        "missing": file_status(MISSING_DATA),
        "restored": restored_status,
    }


def route_payload() -> dict:
    rows, version = read_dataset_rows(RESTORED_DATA)
    rows = restore_missing_values(rows, DATA_VALUE_FIELDS)
    parsed = parse_terrain(projected_csv(rows, TERRAIN_FIELDS))
    return {"version": version, **parsed}


def telemetry_payload() -> dict:
    restored, version = read_dataset_rows(RESTORED_DATA)
    restored = restore_missing_values(restored, DATA_VALUE_FIELDS)
    missing, _ = read_dataset_rows(MISSING_DATA)
    _validate_matching_rows(restored, missing)

    parsed = parse_telemetry(projected_csv(restored, TELEMETRY_FIELDS))
    for point, masked_row in zip(parsed["points"], missing):
        point["engine_rpm_estimated"] = (
            masked_row.get("engine_rpm", "") == "" or point["engine_rpm_estimated"]
        )
    return {"version": version, **parsed}


def dataset_comparison_payload() -> dict:
    full, full_version = read_dataset_rows(FULL_DATA)
    missing, missing_version = read_dataset_rows(MISSING_DATA)
    restored, restored_version = read_dataset_rows(RESTORED_DATA)
    _validate_matching_rows(full, missing)
    _validate_matching_rows(full, restored)

    differences = []
    field_counts = {field: 0 for field in DATA_VALUE_FIELDS}
    field_errors: dict[str, list[float]] = {field: [] for field in DATA_VALUE_FIELDS}
    for original, masked, fixed in zip(full, missing, restored):
        for field in DATA_VALUE_FIELDS:
            if masked.get(field, "") != "":
                continue
            try:
                delta = float(fixed[field]) - float(original[field])
            except (KeyError, TypeError, ValueError):
                delta = None
            differences.append({
                "point_id": original["point_id"], "distance": original["distance"],
                "field": field, "real": original.get(field, ""), "missing": "",
                "restored": fixed.get(field, ""), "delta": delta,
            })
            field_counts[field] += 1
            if delta is not None:
                field_errors[field].append(delta)

    field_metrics = {
        field: {
            "mae": sum(abs(value) for value in errors) / len(errors),
            "rmse": (sum(value * value for value in errors) / len(errors)) ** 0.5,
            "count": len(errors),
        }
        for field, errors in field_errors.items() if errors
    }
    return {
        "full_version": full_version, "missing_version": missing_version,
        "restored_version": restored_version, "row_count": len(full),
        "masked_count": len(differences), "field_counts": field_counts,
        "field_metrics": field_metrics, "differences": differences,
    }


def _validate_matching_rows(reference: list[dict[str, str]], candidate: list[dict[str, str]]) -> None:
    if len(reference) != len(candidate):
        raise DataError("Три файла должны содержать одинаковое число строк")
    for index, (expected, actual) in enumerate(zip(reference, candidate), start=2):
        if expected.get("point_id") != actual.get("point_id"):
            raise DataError(f"Несовпадающий point_id в строке {index}")


@lru_cache(maxsize=2)
def _analyze_projected_files(terrain_csv: bytes, telemetry_csv: bytes) -> dict:
    return analyze(parse_terrain(terrain_csv)["points"], parse_telemetry(telemetry_csv)["points"])


def analysis_payload() -> dict:
    rows, version = read_dataset_rows(RESTORED_DATA)
    rows = restore_missing_values(rows, DATA_VALUE_FIELDS)
    terrain_csv = projected_csv(rows, TERRAIN_FIELDS)
    telemetry_csv = projected_csv(rows, TELEMETRY_FIELDS)
    result = _analyze_projected_files(terrain_csv, telemetry_csv)
    return {"terrain_version": version, "telemetry_version": version, **result}
