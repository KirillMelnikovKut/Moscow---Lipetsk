"""Validation and normalization for route and telemetry CSV projections."""

from __future__ import annotations

import math

from backend.data_io import csv_rows
from backend.errors import DataError


def number(row: dict[str, str], key: str, row_number: int, filename: str) -> float:
    try:
        value = float(row[key])
    except (KeyError, TypeError, ValueError) as exc:
        raise DataError(f"{filename}: неверное значение {key} в строке {row_number}") from exc
    if not math.isfinite(value):
        raise DataError(f"{filename}: {key} в строке {row_number} должно быть конечным числом")
    return value


def integer(row: dict[str, str], key: str, row_number: int, filename: str) -> int:
    value = number(row, key, row_number, filename)
    if not value.is_integer() or value < 0:
        raise DataError(f"{filename}: {key} в строке {row_number} должен быть неотрицательным целым")
    return int(value)


def optional_number(row: dict[str, str], key: str, row_number: int, filename: str) -> float | None:
    if key not in row or row[key] in (None, ""):
        return None
    return number(row, key, row_number, filename)


def estimate_engine_rpm(speed_kmh: float) -> float:
    """Estimate engine speed if RPM is missing (0.31 m wheel, 5th gear, 3.9 final drive)."""
    wheel_rpm = (max(0.0, speed_kmh) / 3.6) / (2 * math.pi * 0.31) * 60
    return round(max(800.0, wheel_rpm * 0.82 * 3.9), 0)


def parse_terrain(content: bytes) -> dict:
    filename = "terrain.csv"
    required = {"point_id", "latitude", "longitude", "altitude", "slope", "distance"}
    rows = csv_rows(content, required, filename)
    if len(rows) < 2:
        raise DataError(f"{filename}: для линии маршрута нужны минимум две точки")

    points = []
    seen_ids: set[int] = set()
    previous_distance = -1.0
    for row_number, row in enumerate(rows, start=2):
        point_id = integer(row, "point_id", row_number, filename)
        latitude = number(row, "latitude", row_number, filename)
        longitude = number(row, "longitude", row_number, filename)
        altitude = number(row, "altitude", row_number, filename)
        slope = number(row, "slope", row_number, filename)
        distance = number(row, "distance", row_number, filename)
        bearing = optional_number(row, "bearing", row_number, filename)

        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            raise DataError(f"{filename}: координаты вне диапазона в строке {row_number}")
        if point_id in seen_ids or distance <= previous_distance:
            raise DataError(f"{filename}: повторный point_id или непоследовательное расстояние в строке {row_number}")
        if bearing is not None and not 0 <= bearing < 360:
            raise DataError(f"{filename}: bearing вне диапазона в строке {row_number}")

        seen_ids.add(point_id)
        previous_distance = distance
        points.append({"id": point_id, "lat": latitude, "lon": longitude, "altitude": altitude,
                       "slope": slope, "distance": distance, "bearing": bearing})

    return {"points": points, "stats": {
        "count": len(points), "distance_km": round(points[-1]["distance"] / 1000, 3),
        "altitude_min": min(point["altitude"] for point in points),
        "altitude_max": max(point["altitude"] for point in points),
    }}


def parse_telemetry(content: bytes) -> dict:
    filename = "telemetry.csv"
    required = {"point_id", "distance", "elapsed_seconds", "speed", "vehicle_mass", "cargo_mass"}
    rows = csv_rows(content, required, filename)
    points = []
    seen_ids: set[int] = set()
    previous_distance = -1.0
    previous_elapsed = -1.0

    for row_number, row in enumerate(rows, start=2):
        point_id = integer(row, "point_id", row_number, filename)
        distance = number(row, "distance", row_number, filename)
        elapsed = number(row, "elapsed_seconds", row_number, filename)
        speed = number(row, "speed", row_number, filename)
        vehicle_mass = number(row, "vehicle_mass", row_number, filename)
        cargo_mass = number(row, "cargo_mass", row_number, filename)
        if point_id in seen_ids or distance <= previous_distance or elapsed < previous_elapsed:
            raise DataError(f"{filename}: неверный порядок строк в строке {row_number}")
        if speed < 0 or vehicle_mass <= 0 or cargo_mass < 0 or elapsed < 0:
            raise DataError(f"{filename}: отрицательная скорость, время или масса в строке {row_number}")

        seen_ids.add(point_id)
        previous_distance, previous_elapsed = distance, elapsed
        measured_rpm = optional_number(row, "engine_rpm", row_number, filename)
        points.append({
            "id": point_id, "distance": distance, "elapsed": elapsed, "speed": speed,
            "vehicle_mass": vehicle_mass, "cargo_mass": cargo_mass,
            "total_mass": vehicle_mass + cargo_mass, "timestamp": row.get("timestamp") or None,
            "engine_rpm": measured_rpm if measured_rpm is not None else estimate_engine_rpm(speed),
            "engine_rpm_estimated": measured_rpm is None,
            "throttle": optional_number(row, "throttle", row_number, filename),
            "brake": optional_number(row, "brake", row_number, filename),
            "acceleration": optional_number(row, "acceleration", row_number, filename),
        })

    return {"points": points, "stats": {
        "count": len(points), "duration_seconds": points[-1]["elapsed"],
        "max_speed": max(point["speed"] for point in points),
    }}
