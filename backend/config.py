"""Application paths and the shared combined-dataset schema."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data/real"
FRONTEND_DIST = ROOT / "frontend/dist"

FULL_DATA = Path(os.environ.get("ROUTE_FULL_DATA_CSV", DATA_DIR / "full_data.csv"))
MISSING_DATA = Path(os.environ.get("ROUTE_MISSING_DATA_CSV", DATA_DIR / "missing_data.csv"))
RESTORED_DATA = Path(os.environ.get("ROUTE_RESTORED_DATA_CSV", DATA_DIR / "restored_data.csv"))

DATA_FIELDS = (
    "point_id", "timestamp", "elapsed_seconds", "distance", "latitude", "longitude",
    "altitude", "slope", "bearing", "speed", "vehicle_mass", "cargo_mass",
    "total_mass", "engine_rpm", "throttle", "brake", "acceleration",
)
TERRAIN_FIELDS = (
    "point_id", "timestamp", "latitude", "longitude", "altitude", "slope", "distance", "bearing",
)
TELEMETRY_FIELDS = (
    "point_id", "timestamp", "elapsed_seconds", "distance", "speed", "vehicle_mass",
    "cargo_mass", "total_mass", "engine_rpm", "throttle", "brake", "acceleration",
)
DATA_VALUE_FIELDS = tuple(field for field in DATA_FIELDS if field not in {
    "point_id", "timestamp", "elapsed_seconds", "distance",
})
