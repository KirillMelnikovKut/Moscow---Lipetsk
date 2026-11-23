"""
Интеллектуальная система оптимального выбора маршрутов и времени движения:
Методика умной сегментации и ночного окна (Smart Segmentation & Night Window)
Маршрут: Москва — Липецк (~465 км)
Сравнение для двух типов ТС: Легковой автомобиль (1650 кг) и Фургон (2800 кг).
"""

from backend.services import route_optimization_payload


def print_comparison_table(vehicle_type: str, title: str):
    data = route_optimization_payload(vehicle_type=vehicle_type)
    routes = data["variants"]
    print(f"\n>>> {title}")
    print("=" * 115)
    print(f"{'Метрика / Показатель':<38} | {'1. Платная М-4 (110 км/ч)':<24} | {'2. Бесплатная (н.п.)':<22} | {'3. Умный Гибрид':<22}")
    print("=" * 115)
    rows = [
        ("Время выезда", [r["departure_time"] for r in routes]),
        ("Дистанция (км)", [f"{r['distance_km']:.1f} км" for r in routes]),
        ("Время в пути (ч:мин)", [f"{int(r['duration_hours'])}ч {int((r['duration_hours'] % 1)*60):02d}м" for r in routes]),
        ("Средняя скорость (км/ч)", [f"{r['avg_speed_kmh']:.1f} км/ч" for r in routes]),
        ("РАСХОД ТОПЛИВА НА 100 КМ", [f"{r['fuel_per_100km']:.2f} л/100км" for r in routes]),
        ("РАСХОД ТОПЛИВА НА ВСЮ ДОРОГУ", [f"{r['fuel_liters']:.1f} л" for r in routes]),
        ("Затраты на топливо (руб)", [f"{int(r['fuel_cost_rub']):,} ₽" for r in routes]),
        ("Оплата платных дорог (руб)", [f"{int(r['toll_cost_rub']):,} ₽" for r in routes]),
        ("Амортизация и износ (руб)", [f"{int(r['wear_cost_rub']):,} ₽" for r in routes]),
        ("Стоимость времени VoT (руб)", [f"{int(r['time_cost_rub']):,} ₽" for r in routes]),
        ("-" * 38, ["-" * 24, "-" * 22, "-" * 22]),
        ("ИТОГОВАЯ СТОИМОСТЬ TCO (руб)", [f"{int(r['total_cost_rub']):,} ₽" for r in routes]),
    ]
    for label, vals in rows:
        print(f"{label:<38} | {vals[0]:<24} | {vals[1]:<22} | {vals[2]:<22}")
    print("=" * 115)
    print(f"Экономия Гибрида: к платке {int(data['savings_vs_toll']):,} ₽ | к бесплатной {int(data['savings_vs_free']):,} ₽")


if __name__ == "__main__":
    print_comparison_table("car", "ЛЕГКОВОЙ АВТОМОБИЛЬ (1650 кг, Cd*A = 0.77 м²)")
    print_comparison_table("van", "КОММЕРЧЕСКИЙ ФУРГОН / ГАЗель (2800 кг, Cd*A = 2.2 м²)")
