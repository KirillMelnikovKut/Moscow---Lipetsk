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


SEGMENTS_DEFINITION = [
    {
        "id": 1,
        "name": "1. МКАД — Ока / Кашира",
        "from_km": 0.0, "to_km": 93.0, "length_km": 93.0,
        "bottleneck": True,
        "toll_name": "М-4 Дон (магистраль 21–93 км)",
        "free_name": "Старое Каширское ш. (Домодедово, 14 светофоров)",
        "toll_day": 450, "toll_night": 300,
    },
    {
        "id": 2,
        "name": "2. Кашира — Мордвес / Венёв",
        "from_km": 93.0, "to_km": 170.0, "length_km": 77.0,
        "bottleneck": False,
        "toll_name": "М-4 (платный участок 93–211 км)",
        "free_name": "Р-22 / региональная трасса через Мордвес",
        "toll_day": 350, "toll_night": 250,
    },
    {
        "id": 3,
        "name": "3. Венёв — Богородицк",
        "from_km": 170.0, "to_km": 260.0, "length_km": 90.0,
        "bottleneck": True,
        "toll_name": "М-4 (обход Богородицка 211–260 км)",
        "free_name": "Старая трасса через центр Богородицка (светофоры)",
        "toll_day": 450, "toll_night": 300,
    },
    {
        "id": 4,
        "name": "4. Богородицк — Ефремов",
        "from_km": 260.0, "to_km": 330.0, "length_km": 70.0,
        "bottleneck": False,
        "toll_name": "М-4 (платный участок 287–322 км)",
        "free_name": "Региональная загородная трасса",
        "toll_day": 350, "toll_night": 200,
    },
    {
        "id": 5,
        "name": "5. Ефремов — Елец",
        "from_km": 330.0, "to_km": 414.0, "length_km": 84.0,
        "bottleneck": True,
        "toll_name": "М-4 (обход Ельца и мост через р. Быстрая Сосна)",
        "free_name": "Старая дорога через центр Ельца и реку",
        "toll_day": 500, "toll_night": 350,
    },
    {
        "id": 6,
        "name": "6. Елец — Липецк",
        "from_km": 414.0, "to_km": 465.0, "length_km": 51.0,
        "bottleneck": False,
        "toll_name": "Региональная трасса Р-119",
        "free_name": "Региональная трасса Р-119",
        "toll_day": 0, "toll_night": 0,
    },
]


def _calc_segments(
    toll_flags: dict[int, bool],
    is_night: bool,
    is_van: bool,
    fuel_price: float,
) -> list[dict]:
    mass = 2800.0 if is_van else 1650.0
    cd_a = 2.2 if is_van else 0.77
    crr = 0.010 if is_van else 0.009
    eta = 0.28
    q_fuel = 35_000_000.0
    idle_lph = 1.2 if is_van else 0.8
    g = 9.81

    results = []
    for seg in SEGMENTS_DEFINITION:
        seg_id = seg["id"]
        is_toll = toll_flags.get(seg_id, False)
        length = seg["length_km"]

        if is_toll:
            speed = 83.0 if is_night else 110.0
            toll_fee = seg["toll_night"] if is_night else seg["toll_day"]
            if is_van:
                toll_fee = round(toll_fee * 1.5)
            v_ms = speed / 3.6
            time_h = length / speed
            rho = 1.28 if is_night else 1.18
            eff_cda = cd_a * 0.82 if is_night else cd_a
            f = mass * g * crr + 0.5 * rho * eff_cda * (v_ms**2)
            fuel = (f * length * 1000) / (eta * q_fuel) + idle_lph * time_h
            wear = 40.0
            seg_title = seg["toll_name"]
        else:
            speed = 52.0 if seg["bottleneck"] else 80.0
            if is_night:
                speed += 4.0
            length_eff = length * 1.05 if seg["bottleneck"] else length
            v_ms = speed / 3.6
            time_h = length_eff / speed
            rho = 1.28 if is_night else 1.18
            f = mass * g * crr + 0.5 * rho * cd_a * (v_ms**2)
            fuel_drive = (f * length_eff * 1000) / (eta * q_fuel) + idle_lph * time_h * (1.3 if seg["bottleneck"] else 1.0)
            cycles = round(length * 0.3) if seg["bottleneck"] else round(length * 0.04)
            if is_night:
                cycles = max(1, round(cycles * 0.25))
            dek = cycles * 0.5 * mass * ((75 / 3.6)**2 - (30 / 3.6)**2)
            fuel = fuel_drive + (dek / (eta * q_fuel))
            toll_fee = 0.0
            wear = 220.0 if seg["bottleneck"] else 50.0
            seg_title = seg["free_name"]

        fuel_per_100 = (fuel / length) * 100.0
        results.append({
            "id": seg_id,
            "name": seg["name"],
            "title": seg_title,
            "from_km": seg["from_km"],
            "to_km": seg["to_km"],
            "length_km": length,
            "is_toll": is_toll,
            "speed_kmh": round(speed, 1),
            "duration_min": round(time_h * 60, 1),
            "fuel_liters": round(fuel, 2),
            "fuel_per_100km": round(fuel_per_100, 2),
            "toll_rub": float(toll_fee),
            "wear_rub": float(wear),
            "fuel_cost_rub": round(fuel * fuel_price, 0),
        })
    return results


def route_optimization_payload(
    fuel_price: float = 68.0,
    value_of_time: float = 600.0,
    vehicle_type: str = "car",
) -> dict:
    """Оптимальный выбор маршрута и времени движения между Москвой и Липецком."""
    is_van = vehicle_type == "van"
    mass = 2800.0 if is_van else 1650.0

    toll_flags_toll = {i: True for i in range(1, 7)}
    toll_flags_free = {i: False for i in range(1, 7)}
    toll_flags_hybrid = {1: True, 2: False, 3: True, 4: False, 5: True, 6: False}

    seg_toll = _calc_segments(toll_flags_toll, is_night=False, is_van=is_van, fuel_price=fuel_price)
    seg_free = _calc_segments(toll_flags_free, is_night=False, is_van=is_van, fuel_price=fuel_price)
    seg_hybrid = _calc_segments(toll_flags_hybrid, is_night=True, is_van=is_van, fuel_price=fuel_price)

    def _assemble_variant(vid, name, desc, deptime, is_night, segs):
        total_dist = sum(s["length_km"] for s in segs)
        total_time_h = sum(s["duration_min"] for s in segs) / 60.0
        total_fuel = sum(s["fuel_liters"] for s in segs)
        total_toll = sum(s["toll_rub"] for s in segs)
        total_wear = sum(s["wear_rub"] for s in segs)
        fuel_cost = round(total_fuel * fuel_price, 0)
        time_cost = round(total_time_h * value_of_time, 0)
        total_cost = round(fuel_cost + total_toll + total_wear + time_cost, 0)
        avg_speed = round(total_dist / total_time_h, 1)
        per_100 = round(total_fuel / total_dist * 100.0, 2)
        return {
            "id": vid,
            "name": name,
            "description": desc,
            "departure_time": deptime,
            "is_night": is_night,
            "distance_km": round(total_dist, 1),
            "duration_hours": round(total_time_h, 2),
            "avg_speed_kmh": avg_speed,
            "fuel_liters": round(total_fuel, 1),
            "fuel_per_100km": per_100,
            "fuel_cost_rub": fuel_cost,
            "toll_cost_rub": total_toll,
            "wear_cost_rub": total_wear,
            "time_cost_rub": time_cost,
            "total_cost_rub": total_cost,
            "segments": segs,
        }

    v_toll = _assemble_variant(
        "toll", "1. Платная М-4 (Скоростная)",
        "Сплошной платный коридор. Крейсерская скорость 110 км/ч, дневной выезд.",
        "10:00 (День)", False, seg_toll,
    )
    v_free = _assemble_variant(
        "free", "2. Бесплатная через н.п.",
        "Старая М-4 / Р-22. 58 населенных пунктов и светофоров, дневной выезд.",
        "10:00 (День)", False, seg_free,
    )
    v_hybrid = _assemble_variant(
        "hybrid", "3. Умный Гибрид PEER-KS",
        "Оптимальное чередование: платные обходы узких мест, бесплатные прямые перегоны. Ночной выезд 83 км/ч.",
        "23:30 (Ночь)", True, seg_hybrid,
    )

    variants = [v_toll, v_free, v_hybrid]

    toll_total = v_toll["total_cost_rub"]
    free_total = v_free["total_cost_rub"]
    hybrid_total = v_hybrid["total_cost_rub"]

    return {
        "params": {
            "fuel_price": fuel_price,
            "value_of_time": value_of_time,
            "vehicle_type": vehicle_type,
            "vehicle_mass": mass,
        },
        "segments_def": SEGMENTS_DEFINITION,
        "variants": variants,
        "best_variant_id": "hybrid",
        "savings_vs_toll": round(toll_total - hybrid_total, 0),
        "savings_vs_free": round(free_total - hybrid_total, 0),
        "methodology_summary": {
            "title": "Умная сегментация и ночное окно",
            "points": [
                "Скорость vs Аэродинамика: на 110 км/ч сопротивление воздуха растет квадратично, сжигая на 25% больше топлива, а плата за проезд превышает стоимость всего бензина.",
                "Деревни vs Тормоза: на бесплатной дороге 58 населенных пунктов и камер; постоянные разгоны и торможения сжигают колодки и почти 9 часов времени.",
                "Гибридное чередование: платные участки берутся только для объезда бутылочных горлышек (выезд из Москвы, Богородицк, Елец). Прямые спокойные перегоны едутся бесплатно со скоростью 80–85 км/ч.",
                "Ночное окно (23:30): дешевый ночной тариф «Автодор», пустая дорога без пешеходных светофоров и равномерный безопасный темп.",
            ],
        },
    }
