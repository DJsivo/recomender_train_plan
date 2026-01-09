from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from app.core.models import Exercise, TrainingPlan, UserProfile


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

EXERCISES_FILE = DATA_DIR / "exercises.json"
USER_PROFILE_FILE = DATA_DIR / "user_profile.json"
TRAINING_PLAN_FILE = DATA_DIR / "training_plan.json"


def load_exercises() -> List[Exercise]:
    """Загружает каталог упражнений из JSON-файла."""

    if not EXERCISES_FILE.exists():
        raise FileNotFoundError(
            f"Файл с упражнениями не найден: {EXERCISES_FILE}. "
            f"Убедитесь, что exercises.json находится в папке data."
        )

    with EXERCISES_FILE.open("r", encoding="utf-8") as f:
        raw_list = json.load(f)

    return [Exercise.from_dict(item) for item in raw_list]


def save_user_profile(profile: UserProfile) -> None:
    """Сохраняет профиль пользователя в JSON-файл."""

    with USER_PROFILE_FILE.open("w", encoding="utf-8") as f:
        json.dump(profile.to_dict(), f, ensure_ascii=False, indent=2)


def load_user_profile() -> Optional[UserProfile]:
    """Загружает профиль пользователя, если он сохранён.

    Возвращает None, если файл отсутствует.
    """

    if not USER_PROFILE_FILE.exists():
        return None

    with USER_PROFILE_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return UserProfile.from_dict(data)


def save_training_plan(plan: TrainingPlan) -> None:
    """Сохраняет план тренировок в JSON-файл."""

    with TRAINING_PLAN_FILE.open("w", encoding="utf-8") as f:
        json.dump(plan.to_dict(), f, ensure_ascii=False, indent=2)


def load_training_plan() -> Optional[TrainingPlan]:
    """Загружает план тренировок, если он сохранён.

    Возвращает None, если файл отсутствует.
    """

    if not TRAINING_PLAN_FILE.exists():
        return None

    with TRAINING_PLAN_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return TrainingPlan.from_dict(data)
