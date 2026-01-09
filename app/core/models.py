from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class UserProfile:
    """Модель профиля пользователя.

    Значения полей подобраны так, чтобы их было удобно сериализовать в JSON
    и использовать как признаки для ML-модели.
    """

    gender: str  # "male" / "female"
    age: int
    weight_kg: float
    height_cm: Optional[float]
    activity_level: str  # "low" / "medium" / "high"
    goal: str  # "weight_loss" / "muscle_gain" / "maintenance" / "endurance" / "back_health" / "general_health"
    experience_level: str  # "beginner" / "intermediate" / "advanced"
    preferred_location: str  # "home" / "gym" / "no_preference"
    available_equipment: List[str] = field(default_factory=list)
    health_issues: List[str] = field(default_factory=list)  # например: "суставы", "спина", "сердце", "ожирение"
    max_sessions_per_week: int = 3

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "UserProfile":
        return UserProfile(**data)


@dataclass
class Exercise:
    """Описание одного упражнения из каталога."""

    id: str
    name: str
    muscle_groups: List[str]
    equipment: List[str]
    difficulty: str  # "beginner" / "intermediate" / "advanced"
    exercise_type: str  # "strength" / "cardio" / "mobility" / "rehab"
    locations: List[str]  # где можно выполнять: ["home", "gym"]
    contraindications: List[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Exercise":
        return Exercise(**data)


@dataclass
class PlannedExercise:
    """Упражнение внутри конкретной тренировки (с подходами/повторами/временем)."""

    exercise_id: str
    sets: int
    reps: Optional[int] = None
    duration_seconds: Optional[int] = None
    comment: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "PlannedExercise":
        return PlannedExercise(**data)


@dataclass
class TrainingSession:
    """Отдельная тренировка в рамках плана."""

    week_index: int
    day_index: int
    title: str
    exercises: List[PlannedExercise] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "week_index": self.week_index,
            "day_index": self.day_index,
            "title": self.title,
            "exercises": [e.to_dict() for e in self.exercises],
        }

    @staticmethod
    def from_dict(data: dict) -> "TrainingSession":
        exercises = [PlannedExercise.from_dict(e) for e in data.get("exercises", [])]
        return TrainingSession(
            week_index=data["week_index"],
            day_index=data["day_index"],
            title=data["title"],
            exercises=exercises,
        )


@dataclass
class TrainingPlan:
    """Полный план тренировок на несколько недель."""

    goal: str
    sessions_per_week: int
    total_weeks: int
    sessions: List[TrainingSession] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "goal": self.goal,
            "sessions_per_week": self.sessions_per_week,
            "total_weeks": self.total_weeks,
            "sessions": [s.to_dict() for s in self.sessions],
        }

    @staticmethod
    def from_dict(data: dict) -> "TrainingPlan":
        sessions = [TrainingSession.from_dict(s) for s in data.get("sessions", [])]
        return TrainingPlan(
            goal=data["goal"],
            sessions_per_week=data["sessions_per_week"],
            total_weeks=data["total_weeks"],
            sessions=sessions,
        )
