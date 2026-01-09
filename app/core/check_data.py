from __future__ import annotations

from app.core.data_access import load_exercises


def main() -> None:
    exercises = load_exercises()
    print(f"Загружено упражнений: {len(exercises)}")
    print("Первые 5 упражнений:")
    for ex in exercises[:5]:
        muscles = ", ".join(ex.muscle_groups)
        print(f"- {ex.name} ({muscles})")


if __name__ == "__main__":
    main()
