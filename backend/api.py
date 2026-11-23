"""HTTP routes for health, route data, vehicle telemetry, and analysis."""

from fastapi import APIRouter, HTTPException

from backend.errors import DataError
from backend.services import (
    analysis_payload,
    dataset_comparison_payload,
    dataset_status,
    route_optimization_payload,
    route_payload,
    telemetry_payload,
)

router = APIRouter(prefix="/api")


def _unprocessable(exc: DataError | ValueError) -> HTTPException:
    return HTTPException(status_code=422, detail=str(exc))


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/status")
def status() -> dict:
    return dataset_status()


@router.get("/route")
def route() -> dict:
    try:
        return route_payload()
    except DataError as exc:
        raise _unprocessable(exc) from exc


@router.get("/telemetry")
def telemetry() -> dict:
    try:
        return telemetry_payload()
    except DataError as exc:
        raise _unprocessable(exc) from exc


@router.get("/analysis")
def analysis() -> dict:
    try:
        return analysis_payload()
    except (DataError, ValueError) as exc:
        raise _unprocessable(exc) from exc


@router.get("/datasets")
def datasets() -> dict:
    try:
        return dataset_comparison_payload()
    except DataError as exc:
        raise _unprocessable(exc) from exc


@router.get("/optimization")
def optimization(
    fuel_price: float = 68.0,
    value_of_time: float = 600.0,
    vehicle_type: str = "car",
) -> dict:
    try:
        return route_optimization_payload(
            fuel_price=fuel_price,
            value_of_time=value_of_time,
            vehicle_type=vehicle_type,
        )
    except Exception as exc:
        raise _unprocessable(ValueError(str(exc))) from exc
