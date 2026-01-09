from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from app.core.data_access import DATA_DIR
from app.core.models import UserProfile


CONDITIONS_FILE = DATA_DIR / "conditions.json"


@dataclass
class Condition:
    id: str
    name: str
    group: str
    sessions_per_week_max: Optional[int] = None
    cardio_level: Optional[str] = None
    notes: str = ""

    @staticmethod
    def from_dict(data: dict) -> "Condition":
        return Condition(
            id=data["id"],
            name=data.get("name", ""),
            group=data.get("group", "other"),
            sessions_per_week_max=data.get("sessions_per_week_max"),
            cardio_level=data.get("cardio_level"),
            notes=data.get("notes", ""),
        )


_conditions_by_id: Dict[str, Condition] | None = None


def _load_conditions() -> Dict[str, Condition]:
    global _conditions_by_id

    if _conditions_by_id is not None:
        return _conditions_by_id

    if not CONDITIONS_FILE.exists():
        _conditions_by_id = {}
        return _conditions_by_id

    with CONDITIONS_FILE.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    result: Dict[str, Condition] = {}
    for item in raw:
        try:
            cond = Condition.from_dict(item)
        except Exception:  # noqa: BLE001
            continue
        result[cond.id] = cond

    _conditions_by_id = result
    return _conditions_by_id


def _known_condition_ids() -> Set[str]:
    return set(_load_conditions().keys())


def extract_condition_ids(health_issues: List[str]) -> Set[str]:
    """Возвращает подмножество health_issues, которое совпадает с id заболеваний.

    Остальные элементы списка профиля считаются произвольными тегами
    (например, старые значения "суставы", "спина" и т.п.).
    """

    known = _known_condition_ids()
    return {item for item in health_issues if item in known}


def get_sessions_limit_for_profile(profile: UserProfile) -> Optional[int]:
    """Возвращает максимальное рекомендуемое число занятий в неделю
    с учётом всех указанных у пользователя заболеваний.

    Берётся минимальное значение sessions_per_week_max по всем заболеваниям.
    """

    cond_ids = extract_condition_ids(profile.health_issues)
    if not cond_ids:
        return None

    conditions = _load_conditions()
    limits: List[int] = []
    for cid in cond_ids:
        cond = conditions.get(cid)
        if cond and cond.sessions_per_week_max is not None:
            limits.append(int(cond.sessions_per_week_max))

    if not limits:
        return None

    return min(limits)


def get_risk_tags_for_profile(profile: UserProfile) -> Set[str]:
    """Строит набор тегов риска на основе заболеваний и свободных пометок профиля.

    Эти теги используются для сопоставления с полем Exercise.contraindications.
    Поддерживает как новые коды заболеваний из conditions.json, так и старые
    текстовые значения ("сердце", "суставы", ...).
    """

    tags: Set[str] = set()
    raw = set(profile.health_issues)

    # Все неизвестные строки сохраняем как есть (совместимость со старыми профилями)
    known_ids = _known_condition_ids()
    for item in raw:
        if item not in known_ids:
            tags.add(item)

    conditions = _load_conditions()
    for cid in extract_condition_ids(profile.health_issues):
        cond = conditions.get(cid)
        if cond is None:
            continue

        group = cond.group
        # Общие групповые теги
        if group == "cardio":
            tags.add("сердце")
        elif group == "joint":
            tags.add("суставы")
        elif group == "spine":
            tags.add("спина")
        elif group == "metabolic":
            # более конкретные теги см. ниже
            pass

        # Более точные теги по конкретным диагнозам
        if cid == "joint_knee_arthrosis":
            tags.update({"колени", "суставы"})
        elif cid == "joint_hip_arthrosis":
            tags.update({"тазобедренные", "суставы"})
        elif cid == "joint_shoulder_impingement":
            tags.update({"плечи", "суставы"})
        elif cid == "joint_elbow_wrist_pain":
            tags.update({"локти", "запястья", "суставы"})
        elif cid == "spine_lumbar_pain":
            tags.update({"поясница", "спина"})
        elif cid == "spine_cervical_pain":
            tags.update({"шея", "спина"})
        elif cid == "metabolic_obesity":
            tags.add("ожирение")
        elif cid == "metabolic_diabetes_type2":
            tags.add("диабет")
        elif cid == "resp_asthma_mild":
            tags.add("астма")
        elif cid == "other_pregnancy":
            tags.add("беременность")
        elif cid == "other_post_surgery_general":
            tags.add("после операции")

    return tags
