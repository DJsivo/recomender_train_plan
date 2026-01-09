from __future__ import annotations

from typing import Dict, List

from app.core.conditions import get_risk_tags_for_profile, get_sessions_limit_for_profile
from app.core.exercise_ml import rank_exercises_for_goal
from app.core.models import Exercise, PlannedExercise, TrainingPlan, TrainingSession, UserProfile


def _rule_based_sessions_per_week(profile: UserProfile) -> int:
    score = 3

    if profile.activity_level == "low":
        score -= 1
    elif profile.activity_level == "high":
        score += 1

    if profile.goal in {"muscle_gain", "endurance"}:
        score += 1
    elif profile.goal in {"back_health", "general_health"}:
        score -= 0

    if "сердце" in profile.health_issues or "суставы" in profile.health_issues:
        score -= 1

    if profile.experience_level == "beginner":
        score -= 0.5
    elif profile.experience_level == "advanced":
        score += 0.5

    score = int(round(score))
    return max(1, min(5, score))


def _rule_based_total_weeks(profile: UserProfile) -> int:
    """Выбирает длительность программы в неделях по цели.

    На первом этапе используем фиксированные значения, как в ТЗ:

    - weight_loss  -> 8 недель
    - muscle_gain  -> 12 недель
    - endurance    -> 8 недель
    - maintenance  -> 6 недель
    - остальные цели (в т.ч. back_health/general_health) -> 6 недель
    """

    if profile.goal == "weight_loss":
        return 8
    if profile.goal == "muscle_gain":
        return 12
    if profile.goal == "endurance":
        return 8
    if profile.goal == "maintenance":
        return 6

    return 6


def recommend_sessions_per_week(profile: UserProfile) -> int:
    base = _rule_based_sessions_per_week(profile)

    value = base

    if hasattr(profile, "max_sessions_per_week") and profile.max_sessions_per_week:
        value = min(value, int(profile.max_sessions_per_week))

    cond_limit = get_sessions_limit_for_profile(profile)
    if cond_limit is not None:
        value = min(value, cond_limit)

    return max(1, min(7, value))


def recommend_total_weeks(profile: UserProfile) -> int:
    return _rule_based_total_weeks(profile)


def _difficulty_score(level: str) -> int:
    if level == "beginner":
        return 1
    if level == "intermediate":
        return 2
    return 3


def _select_allowed_exercises(profile: UserProfile, exercises: List[Exercise]) -> List[Exercise]:
    result: List[Exercise] = []
    exp_score = _difficulty_score(profile.experience_level)
    risk_tags = get_risk_tags_for_profile(profile)

    user_eq = {e.lower() for e in profile.available_equipment}

    for ex in exercises:
        if profile.preferred_location == "home" and "home" not in ex.locations:
            continue
        if profile.preferred_location == "gym" and "gym" not in ex.locations:
            continue

        # Фильтр по оборудованию: не предлагаем упражнения, для которых
        # требуется инвентарь, которого у пользователя нет.
        ex_eq = {e.lower() for e in ex.equipment}

        if profile.preferred_location == "home":
            # Дома оставляем либо упражнения с собственным весом, либо такие,
            # для которых у пользователя явно указан инвентарь.
            if ex_eq and (not user_eq or not ex_eq.intersection(user_eq)):
                continue
        else:
            # В зале / без предпочтений всё равно не даём упражнения, где
            # требуется инвентарь, которого нет в available_equipment, если
            # пользователь вообще заполнил этот список.
            if ex_eq and user_eq and not ex_eq.intersection(user_eq):
                continue

        if _difficulty_score(ex.difficulty) > exp_score + 1:
            continue

        if risk_tags.intersection(ex.contraindications):
            continue

        result.append(ex)

    return result


def _pick_exercises(
    all_ex: List[Exercise],
    exercise_type: str,
    muscle_keyword: str | None,
    max_items: int,
    goal: str | None,
    used_global: set[str] | None = None,
) -> List[Exercise]:
    """Выбирает упражнения заданного типа/мышечной группы.

    1) Фильтрует по типу и ключевому слову мышечной группы.
    2) При наличии used_global старается сначала использовать упражнения,
       которые ещё не встречались в плане.
    3) Если задана goal, передаёт управление ML-ранжированию, которое
       выбирает до max_items упражнений по TF-IDF-релевантности.
       Количество упражнений при этом может быть меньше max_items,
       если остальные слишком далеки по смыслу от цели.
    """

    filtered: List[Exercise] = []
    for ex in all_ex:
        if ex.exercise_type != exercise_type:
            continue
        if muscle_keyword is not None:
            if not any(muscle_keyword in mg for mg in ex.muscle_groups):
                continue
        filtered.append(ex)

    if not filtered:
        return []

    # Стараемся не повторять уже использованные упражнения, если есть запас
    if used_global:
        unused = [ex for ex in filtered if ex.id not in used_global]
        if unused:
            filtered = unused

    if goal:
        # ML сам выбирает до max_items наиболее релевантных упражнений
        return rank_exercises_for_goal(goal, filtered, max_items=max_items)

    filtered.sort(key=lambda e: e.id)
    return filtered[:max_items]


def _sets_reps_for_strength(experience_level: str) -> tuple[int, int]:
    if experience_level == "beginner":
        return 2, 12
    if experience_level == "intermediate":
        return 3, 10
    return 4, 8


def _duration_for_cardio_seconds(experience_level: str) -> int:
    if experience_level == "beginner":
        return 8 * 60
    if experience_level == "intermediate":
        return 12 * 60
    return 18 * 60


def _exercise_priority(ex: Exercise) -> int:
    name = (ex.name or "").lower()

    if "squat" in name:
        return 0
    if "deadlift" in name:
        return 1
    if "bench press" in name:
        return 2
    if "bench" in name and "press" in name:
        return 3
    if "row" in name or "pulldown" in name or "pull-up" in name or "pull up" in name:
        return 4
    if "lunge" in name or "step-up" in name or "step up" in name:
        return 5

    if ex.exercise_type == "strength":
        return 10
    if ex.exercise_type == "cardio":
        return 20
    return 30


def _build_session_title(profile: UserProfile, index_within_week: int) -> str:
    base = {
        "weight_loss": "Похудение",
        "muscle_gain": "Набор массы",
        "maintenance": "Поддержание формы",
        "endurance": "Выносливость",
        "back_health": "Спина",
        "general_health": "Общее здоровье",
    }.get(profile.goal, "Тренировка")
    return f"{base} — день {index_within_week}"


def generate_training_plan(profile: UserProfile, exercises: List[Exercise]) -> TrainingPlan:
    sessions_per_week = recommend_sessions_per_week(profile)
    total_weeks = recommend_total_weeks(profile)

    allowed = _select_allowed_exercises(profile, exercises)

    sessions: List[TrainingSession] = []
    used_global: set[str] = set()
    sets_default, reps_default = _sets_reps_for_strength(profile.experience_level)
    cardio_base = _duration_for_cardio_seconds(profile.experience_level)

    for w in range(1, total_weeks + 1):
        # Простая прогрессия: цикл из 4 недель
        # недели 2-3: лёгкое увеличение нагрузки, неделя 4: облегчённая
        cycle_week = (w - 1) % 4 + 1

        main_sets = sets_default
        main_reps = reps_default
        cardio_duration = cardio_base

        if cycle_week in {2, 3}:
            # Чуть увеличиваем объём: +1 повтор, немного больше кардио
            main_reps = reps_default + 1
            cardio_duration = int(cardio_base * 1.1)
        elif cycle_week == 4:
            # Облегчённая неделя
            main_reps = max(reps_default - 1, max(6, reps_default - 2))
            cardio_duration = int(cardio_base * 0.9)

        for d in range(1, sessions_per_week + 1):
            planned_exercises: List[PlannedExercise] = []

            # --- Разминка отключена: пользователь выполняет суставную разминку по своему усмотрению ---
            warmup_ex: List[Exercise] = []

            # --- Основная часть: зависит от цели ---
            main_ex: List[Exercise] = []
            if profile.goal == "muscle_gain":
                # Классический трёхдневный цикл для массы c явным разделением
                # на основную и дополнительную мышечные группы.
                # День 1: основная — грудь (4 упражнения), доп. — плечи (1–2 упражнения)
                # День 2: основная — ноги (4 упражнения), доп. — пресс (1–2 упражнения)
                # День 3: основная — спина (4 упражнения), доп. — бицепс (1–2 упражнения)
                day_in_cycle = (d - 1) % 3 + 1
                if day_in_cycle == 1:
                    chest = _pick_exercises(allowed, "strength", "грудь", 4, profile.goal, used_global)
                    shoulders = _pick_exercises(allowed, "strength", "плечи", 2, profile.goal, used_global)
                    main_ex = chest + shoulders
                elif day_in_cycle == 2:
                    legs = _pick_exercises(allowed, "strength", "ноги", 4, profile.goal, used_global)
                    core = _pick_exercises(allowed, "strength", "пресс", 2, profile.goal, used_global)
                    main_ex = legs + core
                else:
                    back = _pick_exercises(allowed, "strength", "спина", 4, profile.goal, used_global)
                    biceps = _pick_exercises(allowed, "strength", "бицепс", 2, profile.goal, used_global)
                    main_ex = back + biceps
            elif profile.goal == "back_health":
                # Реабилитация спины: ЛФК + мобилити
                rehab = _pick_exercises(allowed, "rehab", None, 4, profile.goal, used_global)
                mobility = _pick_exercises(allowed, "mobility", None, 3, profile.goal, used_global)
                main_ex = rehab + mobility
            elif profile.goal == "endurance":
                # Выносливость: интервальное кардио + умеренные силовые на ноги
                cardio = _pick_exercises(allowed, "cardio", None, 4, profile.goal, used_global)
                strength = _pick_exercises(allowed, "strength", "ноги", 2, profile.goal, used_global)
                main_ex = cardio + strength
            elif profile.goal == "weight_loss":
                # Похудение: круговая тренировка 6–8 упражнений
                circuit_strength = _pick_exercises(allowed, "strength", None, 5, profile.goal, used_global)
                circuit_cardio = _pick_exercises(allowed, "cardio", None, 3, profile.goal, used_global)
                main_ex = circuit_strength + circuit_cardio
            else:
                # Поддержание/общее здоровье: баланс силовых, кардио и мобилити
                strength = _pick_exercises(allowed, "strength", None, 3, profile.goal, used_global)
                cardio = _pick_exercises(allowed, "cardio", None, 2, profile.goal, used_global)
                mobility = _pick_exercises(allowed, "mobility", None, 2, profile.goal, used_global)
                main_ex = strength + cardio + mobility

            # Если по конкретным группам мышц упражнений оказалось мало,
            # добираем общий силовой блок, чтобы основная часть не была из 1–2 упражнений.
            # Для набора массы целимся в 4 упражнения на основную мышцу и
            # 1–2 на дополнительную, поэтому минимальный объём чуть выше.
            if profile.goal == "muscle_gain":
                min_main = 5
            elif profile.goal == "weight_loss":
                min_main = 6
            elif profile.goal == "endurance":
                min_main = 4
            else:
                min_main = 3

            if len(main_ex) < min_main:
                extra = _pick_exercises(
                    allowed,
                    "strength",
                    None,
                    min_main - len(main_ex),
                    profile.goal,
                    used_global,
                )
                main_ex.extend(extra)

            if main_ex:
                main_ex.sort(key=_exercise_priority)

            # --- Заминка отключена: по текущему ТЗ отдельного блока заминки нет ---
            cooldown_ex: List[Exercise] = []

            # Исключаем локальные дубли в пределах сессии
            used_ids_session = set()

            # Блок разминки не заполняется упражнениями, см. комментарий выше

            # Блок основной части
            for ex in main_ex:
                if ex.id in used_ids_session:
                    continue
                used_ids_session.add(ex.id)
                used_global.add(ex.id)

                if ex.exercise_type == "cardio":
                    planned_exercises.append(
                        PlannedExercise(
                            exercise_id=ex.id,
                            sets=1,
                            reps=None,
                            duration_seconds=cardio_duration,
                            comment="Основной блок: интервальное или ровное кардио, контролируйте дыхание.",
                        )
                    )
                elif ex.exercise_type in {"mobility", "rehab"}:
                    planned_exercises.append(
                        PlannedExercise(
                            exercise_id=ex.id,
                            sets=2,
                            reps=10,
                            duration_seconds=None,
                            comment="Основной блок: реабилитация/мобилити, движения плавные, без рывков.",
                        )
                    )
                else:
                    planned_exercises.append(
                        PlannedExercise(
                            exercise_id=ex.id,
                            sets=main_sets,
                            reps=main_reps,
                            duration_seconds=None,
                            comment="Основной блок: силовая часть, техника и небольшой запас по усилию.",
                        )
                    )

            # Блок заминки
            for ex in cooldown_ex:
                if ex.id in used_ids_session:
                    continue
                used_ids_session.add(ex.id)
                used_global.add(ex.id)

                planned_exercises.append(
                    PlannedExercise(
                        exercise_id=ex.id,
                        sets=1,
                        reps=10,
                        duration_seconds=None,
                        comment="Заминка/растяжка: мягкие статические позиции без сильной боли.",
                    )
                )

            title = _build_session_title(profile, d)
            session = TrainingSession(
                week_index=w,
                day_index=d,
                title=title,
                exercises=planned_exercises,
            )
            sessions.append(session)

    plan = TrainingPlan(
        goal=profile.goal,
        sessions_per_week=sessions_per_week,
        total_weeks=total_weeks,
        sessions=sessions,
    )
    return plan
