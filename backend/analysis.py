"""Reproducible terrain ML experiment and illustrative vehicle energy model."""

from __future__ import annotations

from bisect import bisect_left
from math import sqrt

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.neighbors import KNeighborsRegressor


RHO = 1.225
CD_A = 0.77
CRR = 0.008
GRAVITY = 9.81
EFFICIENCY = 0.30
FUEL_ENERGY = 35_000_000
IDLE_LPH = 0.8


def terrain_experiment(points: list[dict]) -> dict:
    """Hide deterministic rows, fit KNN to visible elevation, and score held-out rows."""
    if len(points) < 20:
        raise ValueError("Для эксперимента восстановления нужны минимум 20 точек маршрута")
    distances = np.array([p["distance"] for p in points], dtype=float)
    heights = np.array([p["altitude"] for p in points], dtype=float)
    missing = np.zeros(len(points), dtype=bool)
    missing[7:-7:9] = True
    gap_width = max(3, min(35, len(points) // 150))
    for fraction in (0.22, 0.51, 0.76):
        center = int(fraction * len(points))
        missing[center:center + gap_width] = True
    missing[:2] = False
    missing[-2:] = False
    visible = ~missing
    x_visible = distances[visible]
    y_visible = heights[visible]
    model = KNeighborsRegressor(n_neighbors=min(8, len(x_visible)), weights="distance")
    model.fit(x_visible.reshape(-1, 1), y_visible)
    predicted = model.predict(distances.reshape(-1, 1))
    linear = np.interp(distances, x_visible, y_visible)
    reconstructed = heights.copy()
    reconstructed[missing] = predicted[missing]
    ahead_distance = np.minimum(distances + 200.0, distances[-1])
    forecast_heights = model.predict(ahead_distance.reshape(-1, 1))
    span = np.maximum(1.0, ahead_distance - distances)
    forecast_slope = np.clip((forecast_heights - predicted) / span * 100, -12, 12)
    forecast_slope[-1] = 0.0
    held_truth = heights[missing]
    metrics = {
        "removed_count": int(missing.sum()),
        "total_count": len(points),
        "ml_mae_m": round(float(mean_absolute_error(held_truth, predicted[missing])), 3),
        "ml_rmse_m": round(float(sqrt(mean_squared_error(held_truth, predicted[missing]))), 3),
        "linear_mae_m": round(float(mean_absolute_error(held_truth, linear[missing])), 3),
        "linear_rmse_m": round(float(sqrt(mean_squared_error(held_truth, linear[missing]))), 3),
        "model": "KNeighborsRegressor, 8 соседей, веса 1/расстояние",
    }
    return {
        "missing_ids": [points[i]["id"] for i in np.flatnonzero(missing)],
        "reconstructed_altitude": reconstructed.round(3).tolist(),
        "comparison": [{"id": points[i]["id"], "distance": float(distances[i]),
                        "actual_altitude": float(heights[i]),
                        "reconstructed_altitude": float(predicted[i]) if missing[i] else None,
                        "linear_altitude": float(linear[i]) if missing[i] else None,
                        "was_removed": bool(missing[i])} for i in range(len(points))],
        "predicted_slope": forecast_slope.round(3).tolist(),
        "metrics": metrics,
    }


def fuel_trace(distances: list[float], speeds_kmh: list[float], elapsed: list[float],
               masses: list[float], slopes: list[float]) -> list[float]:
    """Integrate fuel using road load and positive wheel power; no regeneration."""
    result = [0.0]
    for i in range(1, len(distances)):
        ds = distances[i] - distances[i - 1]
        dt = elapsed[i] - elapsed[i - 1]
        if ds <= 0 or dt <= 0:
            result.append(result[-1])
            continue
        v0, v1 = speeds_kmh[i - 1] / 3.6, speeds_kmh[i] / 3.6
        v = (v0 + v1) / 2
        mass = (masses[i - 1] + masses[i]) / 2
        slope = (slopes[i - 1] + slopes[i]) / 2
        acceleration = (v1 * v1 - v0 * v0) / (2 * ds)
        force = mass * GRAVITY * CRR + mass * GRAVITY * slope / 100
        force += 0.5 * RHO * CD_A * v * v + mass * acceleration
        liters = max(0.0, force * ds) / (EFFICIENCY * FUEL_ENERGY)
        liters += IDLE_LPH * dt / 3600
        result.append(result[-1] + liters)
    return result


def candidate_trip(distances: list[float], baseline: list[float], slopes_ahead: list[float],
                   actual_slopes: list[float], masses: list[float], cap: float) -> dict:
    speeds = [min(speed, max(25.0, cap - 2.5 * max(0.0, grade)))
              for speed, grade in zip(baseline, slopes_ahead)]
    squared = [(speed / 3.6) ** 2 for speed in speeds]
    for i in range(len(squared) - 2, -1, -1):
        squared[i] = min(squared[i], squared[i + 1] + 4.0 * (distances[i + 1] - distances[i]))
    for i in range(1, len(squared)):
        squared[i] = min(squared[i], squared[i - 1] + 2.4 * (distances[i] - distances[i - 1]))
    speeds = [sqrt(max(0.0, value)) * 3.6 for value in squared]
    elapsed = [0.0]
    for i in range(1, len(distances)):
        denominator = max(1.0, (speeds[i - 1] + speeds[i]) / 3.6)
        elapsed.append(elapsed[-1] + 2 * (distances[i] - distances[i - 1]) / denominator)
    fuel = fuel_trace(distances, speeds, elapsed, masses, actual_slopes)
    return {"cap_kmh": cap, "duration_seconds": elapsed[-1], "fuel_liters": fuel[-1],
            "speeds": speeds, "fuel_trace": fuel}


def analyze(terrain: list[dict], telemetry: list[dict]) -> dict:
    experiment = terrain_experiment(terrain)
    terrain_dist = [p["distance"] for p in terrain]
    terrain_ids = {p["id"]: i for i, p in enumerate(terrain)}
    indices = []
    for row in telemetry:
        if row["id"] in terrain_ids:
            indices.append(terrain_ids[row["id"]])
        else:
            position = bisect_left(terrain_dist, row["distance"])
            indices.append(min(position, len(terrain) - 1))
    distance = [p["distance"] for p in telemetry]
    elapsed = [p["elapsed"] for p in telemetry]
    speed = [p["speed"] for p in telemetry]
    mass = [p["total_mass"] for p in telemetry]
    slope = [terrain[i]["slope"] for i in indices]
    forecast = [experiment["predicted_slope"][i] for i in indices]
    baseline_fuel = fuel_trace(distance, speed, elapsed, mass, slope)
    baseline_duration = elapsed[-1] - elapsed[0]
    candidates = [candidate_trip(distance, speed, forecast, slope, mass, cap) for cap in (65, 70, 75, 80, 85, 90)]
    feasible = [c for c in candidates if c["duration_seconds"] <= baseline_duration * 1.10]
    chosen = min(feasible, key=lambda c: c["fuel_liters"]) if feasible else min(candidates, key=lambda c: c["duration_seconds"])
    return {
        "experiment": experiment,
        "fuel_by_telemetry": [round(v, 4) for v in baseline_fuel],
        "optimal_speed_by_telemetry": [round(v, 2) for v in chosen["speeds"]],
        "baseline": {"duration_seconds": round(baseline_duration, 1), "fuel_liters": round(baseline_fuel[-1], 2)},
        "optimal": {"duration_seconds": round(chosen["duration_seconds"], 1),
                    "fuel_liters": round(chosen["fuel_liters"], 2), "cap_kmh": chosen["cap_kmh"]},
        "method": {"fuel": "F=(Crr*m*g)+(m*g*slope/100)+(rho*CdA*v²/2)+(m*a); L=max(0,F*ds)/(eta*35 MJ/L)+1 L/h*dt",
                   "speed": "Выбор минимума расчётного топлива среди ограничений 65–90 км/ч при времени ≤ 110% исходного"},
    }
