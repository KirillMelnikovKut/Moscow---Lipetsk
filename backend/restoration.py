"""Fill missing numeric measurements by interpolating along trip distance."""

from __future__ import annotations

from bisect import bisect_left
import math

from backend.errors import DataError


def restore_missing_values(
    rows: list[dict[str, str]],
    fields: tuple[str, ...],
    coordinate_field: str = "distance",
) -> list[dict[str, str]]:
    """Return copied rows with blank numeric fields interpolated by distance.

    Interior gaps use linear interpolation. Leading and trailing gaps take the
    nearest available value. Row identifiers and timestamps are not changed.
    """
    if not rows:
        return rows

    restored = [row.copy() for row in rows]
    for field in fields:
        missing = [index for index, row in enumerate(restored) if _blank(row.get(field))]
        if not missing:
            continue

        known = [index for index, row in enumerate(restored) if not _blank(row.get(field))]
        if not known:
            raise DataError(f"Невозможно восстановить {field}: нет исходных значений")

        known_values = {
            index: _finite_number(restored[index].get(field), field)
            for index in known
        }
        for index in missing:
            position = bisect_left(known, index)
            left = known[position - 1] if position else None
            right = known[position] if position < len(known) else None
            if left is None:
                value = known_values[right]
            elif right is None:
                value = known_values[left]
            else:
                x0 = _finite_number(restored[left].get(coordinate_field), coordinate_field)
                x1 = _finite_number(restored[right].get(coordinate_field), coordinate_field)
                x = _finite_number(restored[index].get(coordinate_field), coordinate_field)
                ratio = (x - x0) / (x1 - x0) if x1 != x0 else (index - left) / (right - left)
                value = known_values[left] + (known_values[right] - known_values[left]) * ratio
            restored[index][field] = str(round(value, 3))

    return restored


def _blank(value: str | None) -> bool:
    return value is None or value.strip() == ""


def _finite_number(value: str | None, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise DataError(f"Невозможно восстановить {field}: неверное числовое значение") from exc
    if not math.isfinite(number):
        raise DataError(f"Невозможно восстановить {field}: значение должно быть конечным числом")
    return number
