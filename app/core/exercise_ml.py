from __future__ import annotations

from typing import List

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from app.core.models import Exercise


_GOAL_QUERIES = {
    "weight_loss": "похудение жир кардио ходьба бег низкая ударная нагрузка cardio fat loss walking running low impact",
    "muscle_gain": "мышечная масса сила присед жим тяга hypertrophy strength muscle squat press row deadlift",
    "maintenance": "поддержание формы общее здоровье силовые кардио mobility general fitness strength cardio mobility",
    "endurance": "выносливость длительное кардио бег велосипед эллипс endurance running cycling long cardio",
    "back_health": "спина поясница реабилитация ЛФК стабилизация кора rehab back pain core stability mobility",
    "general_health": "общее здоровье ходьба умеренное кардио лёгкие силовые mobility general health walking light cardio",
}

_DEFAULT_QUERY = (
    "общее здоровье фитнес кардио силовые ходьба упражнения general health fitness cardio strength"
)


def _build_corpus(exercises: List[Exercise]) -> List[str]:
    docs: List[str] = []
    for ex in exercises:
        parts: List[str] = []
        parts.append(ex.name)
        if ex.description:
            parts.append(ex.description)
        parts.extend(ex.muscle_groups)
        parts.extend(ex.equipment)
        parts.append(ex.exercise_type)
        docs.append(" ".join(str(p) for p in parts if p))
    return docs


def rank_exercises_for_goal(
    goal: str,
    exercises: List[Exercise],
    max_items: int | None = None,
) -> List[Exercise]:
    """Возвращает упражнения, отсортированные по уместности под указанную цель.

    Реализация простого content-based recommender на базе TF-IDF по описаниям
    и атрибутам упражнений.

    Если max_items не указан, функция просто возвращает все упражнения
    в порядке убывания релевантности. Если max_items задан, количество
    упражнений подбирается динамически: берутся лучшие по score упражнения
    до тех пор, пока их оценка не падает слишком сильно относительно
    максимальной (порог по доле от max score), но не более max_items.
    """

    if len(exercises) <= 1:
        return exercises

    docs = _build_corpus(exercises)
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(docs)

    query = _GOAL_QUERIES.get(goal, _DEFAULT_QUERY)
    q_vec = vectorizer.transform([query])

    scores = (X @ q_vec.T).toarray().ravel()
    order = np.argsort(-scores)

    # Если нет ограничения по количеству, просто возвращаем сортированный список
    if max_items is None:
        return [exercises[int(i)] for i in order]

    max_items = max(1, int(max_items))

    # Просто берём top-N самых релевантных упражнений.
    # ML отвечает за порядок, правила — за верхний лимит по количеству.
    return [exercises[int(i)] for i in order[:max_items]]
