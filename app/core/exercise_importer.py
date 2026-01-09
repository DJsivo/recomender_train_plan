from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from app.core.data_access import DATA_DIR, EXERCISES_FILE
from app.core.models import Exercise


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FREE_EX_DB_FILE = PROJECT_ROOT / "datasets" / "exercises.json"


def _map_category_to_type(category: str) -> str:
    cat = category.lower()
    if cat in {"strength", "powerlifting", "strongman"}:
        return "strength"
    if cat in {"cardio"}:
        return "cardio"
    if cat in {"stretching", "yoga"}:
        return "mobility"
    if cat in {"plyometrics"}:
        # в контексте плана можно считать высокоинтенсивным кардио/силой
        return "cardio"
    return "strength"


def _map_level_to_difficulty(level: str) -> str:
    lvl = level.lower()
    if lvl in {"beginner", "novice"}:
        return "beginner"
    if lvl in {"intermediate"}:
        return "intermediate"
    return "advanced"


_MUSCLE_GROUP_MAP: Dict[str, str] = {
    "quadriceps": "ноги",
    "hamstrings": "ноги",
    "glutes": "ноги",
    "calves": "ноги",
    "adductors": "ноги",
    "abductors": "ноги",
    "chest": "грудь",
    "abdominals": "пресс",
    "lats": "спина",
    "lower_back": "спина",
    "middle_back": "спина",
    "neck": "спина",
    "shoulders": "плечи",
    "traps": "плечи",
    "biceps": "бицепс",
    "triceps": "трицепс",
    "forearms": "руки",
}


def _normalize_muscle_groups(raw: List[str]) -> List[str]:
    """Объединяет исходные (англ.) мышцы и русские агрегированные теги.

    Это нужно, чтобы фильтр по muscle_keyword ("ноги", "спина", "грудь", "пресс" и т.д.)
    в планировщике начал работать для упражнений из free-exercise-db.
    """

    result: List[str] = []
    for item in raw:
        name = str(item).strip().lower()
        if not name:
            continue
        # сохраняем оригинальное название мышц (для информации и ML)
        result.append(name)

        # добавляем агрегированный русский тег, если он известен
        ru = _MUSCLE_GROUP_MAP.get(name)
        if ru:
            result.append(ru)

    return result or ["прочее"]


def _infer_locations(equipment: str | None) -> List[str]:
    if not equipment:
        return ["home", "gym"]

    eq = equipment.lower()
    gym_only_keywords = [
        "machine",
        "smith",
        "cable",
        "lever",
        "sled",
        "hack squat",
    ]

    if any(k in eq for k in gym_only_keywords):
        return ["gym"]

    return ["home", "gym"]


def _import_from_free_ex_db(data: List[Dict[str, object]]) -> List[Exercise]:
    exercises: List[Exercise] = []

    for item in data:
        ex_id = str(item.get("id") or "").strip()
        name = str(item.get("name") or ex_id)
        if not ex_id:
            continue

        primary = item.get("primaryMuscles") or []
        secondary = item.get("secondaryMuscles") or []
        if not isinstance(primary, list):
            primary = [primary]
        if not isinstance(secondary, list):
            secondary = [secondary]
        raw_muscles = [str(m) for m in (primary + secondary) if str(m).strip()]
        muscle_groups = _normalize_muscle_groups(raw_muscles)

        equipment_str = str(item.get("equipment") or "").strip()
        equipment_list = [equipment_str] if equipment_str else []

        level = str(item.get("level") or "beginner")
        category = str(item.get("category") or "strength")

        instructions = item.get("instructions") or []
        if isinstance(instructions, list):
            description = " ".join(str(x).strip() for x in instructions if str(x).strip())
        else:
            description = str(instructions)

        exercise = Exercise(
            id=ex_id,
            name=name,
            muscle_groups=muscle_groups,
            equipment=equipment_list,
            difficulty=_map_level_to_difficulty(level),
            exercise_type=_map_category_to_type(category),
            locations=_infer_locations(equipment_str),
            contraindications=[],
            description=description,
        )
        exercises.append(exercise)

    return exercises


def import_exercises_from_free_db() -> None:
    if not FREE_EX_DB_FILE.exists():
        raise FileNotFoundError(
            f"Файл с упражнениями free-exercise-db не найден: {FREE_EX_DB_FILE}. "
            "Скачайте dist/exercises.json из репозитория yuhonas/free-exercise-db "
            "и сохраните его как datasets/exercises.json в корне проекта."
        )

    with FREE_EX_DB_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Ожидался список упражнений в free_exercise_db.json")

    imported = _import_from_free_ex_db(data)

    base: List[Exercise] = []
    if EXERCISES_FILE.exists():
        with EXERCISES_FILE.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        base = [Exercise.from_dict(item) for item in raw]

    by_id: Dict[str, Exercise] = {ex.id: ex for ex in base}
    added = 0
    for ex in imported:
        if ex.id in by_id:
            continue
        by_id[ex.id] = ex
        added += 1

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    all_ex = [e.to_dict() for e in by_id.values()]

    with EXERCISES_FILE.open("w", encoding="utf-8") as f:
        json.dump(all_ex, f, ensure_ascii=False, indent=2)

    print(f"Импортировано новых упражнений: {added}")
    print(f"Всего упражнений в каталоге: {len(all_ex)}")


def main() -> None:
    import_exercises_from_free_db()


if __name__ == "__main__":
    main()
