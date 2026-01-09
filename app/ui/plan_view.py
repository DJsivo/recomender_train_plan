from __future__ import annotations

from typing import Dict, List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.core.data_access import (
    load_exercises,
    load_training_plan,
    load_user_profile,
    save_training_plan,
)
from app.core.models import Exercise, TrainingPlan
from app.core.recommender import generate_training_plan


class TrainingPlanView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._exercises_index: Dict[str, Exercise] = {}
        self._current_plan: TrainingPlan | None = None
        self._init_ui()
        self._load_existing_plan()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        controls_widget = QWidget(self)
        controls_layout = QGridLayout(controls_widget)

        self.generate_button = QPushButton("Сгенерировать план", controls_widget)
        self.generate_button.clicked.connect(self._on_generate_clicked)

        self.week_combo = QComboBox(controls_widget)
        self.week_combo.currentIndexChanged.connect(self._on_week_changed)

        self.status_label = QLabel("", controls_widget)
        self.status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        controls_layout.addWidget(self.generate_button, 0, 0)
        controls_layout.addWidget(QLabel("Неделя:", controls_widget), 0, 1)
        controls_layout.addWidget(self.week_combo, 0, 2)
        controls_layout.addWidget(self.status_label, 1, 0, 1, 3)
        controls_layout.setColumnStretch(2, 1)

        self.table = QTableWidget(self)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["День", "Название тренировки", "Упражнения"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(True)
        self.table.setStyleSheet(
            "QTableWidget::item { padding: 6px; }"
        )

        main_layout.addWidget(controls_widget)
        main_layout.addWidget(self.table)

    def _load_existing_plan(self) -> None:
        try:
            exercises = load_exercises()
        except FileNotFoundError:
            self.status_label.setText("Каталог упражнений не найден.")
            return

        self._exercises_index = {ex.id: ex for ex in exercises}

        plan = load_training_plan()
        if plan is None:
            self.status_label.setText("План ещё не сгенерирован.")
            return

        self._set_plan(plan)
        self.status_label.setText("Загружен ранее сохранённый план тренировок.")

    # --- Вспомогательные функции форматирования ---

    def _format_exercise_name(self, ex: Exercise | None) -> str:
        """Возвращает человекочитаемое имя упражнения на русском.

        Для упражнений из free-exercise-db название часто на английском, поэтому
        используется простой набор правил по ключевым словам: мы подбираем
        русский эквивалент и добавляем исходное имя в скобках.
        """

        if ex is None:
            return "Неизвестное упражнение"

        name = ex.name or ""
        lower = name.lower()

        mapping = [
            ("squat", "Приседания"),
            ("deadlift", "Становая тяга"),
            ("romanian deadlift", "Румынская тяга"),
            ("good morning", "Наклоны 'Гуд морнинг'"),
            ("bench press", "Жим лёжа"),
            ("bench", "Жим"),
            ("overhead press", "Жим стоя"),
            ("shoulder press", "Жим на плечи"),
            ("push-up", "Отжимания"),
            ("push up", "Отжимания"),
            ("pull-up", "Подтягивания"),
            ("pull up", "Подтягивания"),
            ("chin-up", "Подтягивания обратным хватом"),
            ("chin up", "Подтягивания обратным хватом"),
            ("row", "Тяга на спину"),
            ("lat pulldown", "Тяга верхнего блока к груди"),
            ("pulldown", "Тяга верхнего блока"),
            ("face pull", "Тяга к лицу"),
            ("lunge", "Выпады"),
            ("leg press", "Жим ногами"),
            ("leg curl", "Сгибания ног"),
            ("leg extension", "Разгибания ног"),
            ("step-up", "Шаги на тумбу"),
            ("step up", "Шаги на тумбу"),
            ("plank", "Планка"),
            ("side plank", "Боковая планка"),
            ("crunch", "Скручивания"),
            ("sit-up", "Подъёмы туловища"),
            ("sit up", "Подъёмы туловища"),
            ("curl", "Сгибания"),
            ("hammer curl", "Сгибания молотком"),
            ("concentration curl", "Сгибания на бицепс сидя"),
            ("extension", "Разгибания"),
            ("tricep extension", "Разгибания на трицепс"),
            ("pushdown", "Жим вниз на блоке"),
            ("fly", "Разведения"),
            ("reverse fly", "Обратные разведения"),
            ("raise", "Подъёмы"),
            ("calf raise", "Подъёмы на икры"),
            ("walk", "Ходьба"),
            ("walking", "Ходьба"),
            ("run", "Бег"),
            ("running", "Бег"),
            ("jog", "Лёгкий бег"),
            ("bike", "Велотренажёр"),
            ("cycling", "Велотренажёр"),
            ("elliptical", "Орбитрек"),
            ("burpee", "Берпи"),
            ("swing", "Махи"),
            ("arm circles", "Круги руками"),
            ("cat-cow", "Упражнение 'Кошка-корова'"),
            ("cat cow", "Упражнение 'Кошка-корова'"),
            ("bench jump", "Прыжки с лавки"),
            ("medicine ball throw", "Бросок медболла"),
            ("backward medicine ball throw", "Бросок медболла назад"),
            ("linear 3-part start technique", "Стартовая техника из 3 фаз"),
            ("lateral cone hops", "Боковые прыжки через конусы"),
            ("hurdle hops", "Прыжки через барьеры"),
            ("front cone hops", "Прыжки вперёд через конусы"),
            ("supine chest throw", "Бросок мяча лёжа на спине"),
            ("pyramid", "Схема подходов 'Пирамида'"),
            ("calves-smr", "Самомассаж икроножных мышц роликом"),
            ("anterior tibialis-smr", "Самомассаж передней поверхности голени роликом"),
            ("frog hops", "Прыжки 'лягушкой'"),
            ("neck-smr", "Лёгкий массаж шеи"),
            ("ankle circles", "Круговые движения стопой"),
            ("standing hip flexors", "Растяжка сгибателей бедра стоя"),
            ("on-your-back quad stretch", "Растяжка квадрицепса лёжа на спине"),
            ("on your back quad stretch", "Растяжка квадрицепса лёжа на спине"),
            ("on your side quad stretch", "Растяжка квадрицепса лёжа на боку"),
            ("on-your-side quad stretch", "Растяжка квадрицепса лёжа на боку"),
            ("foot-smr", "Массаж стопы роликом"),
        ]

        for keyword, ru in mapping:
            if keyword in lower:
                # Показываем русское название и исходное в скобках для прозрачности
                return f"{ru} ({name})"

        # Если не нашли подходящего ключевого слова, возвращаем оригинальное имя
        return name

    def _format_session_exercises(self, week_index: int, day_index: int) -> List[str]:
        """Формирует многострочное описание упражнений для указанного дня.

        Разбивает упражнения на блоки:
        - Разминка
        - Основная часть
        - Заминка
        Использует комментарии, заданные генератором плана, чтобы определить блок.
        """

        if self._current_plan is None:
            return []

        sessions = [
            s
            for s in self._current_plan.sessions
            if s.week_index == week_index and s.day_index == day_index
        ]
        if not sessions:
            return []

        session = sessions[0]

        warmup_lines: List[str] = []
        main_lines: List[str] = []
        cooldown_lines: List[str] = []

        for pe in session.exercises:
            ex = self._exercises_index.get(pe.exercise_id)
            name = self._format_exercise_name(ex)

            if pe.duration_seconds:
                minutes = max(1, pe.duration_seconds // 60)
                base_text = f"{name}: ~{minutes} мин"
            elif pe.reps:
                base_text = f"{name}: {pe.sets}×{pe.reps} повторов"
            else:
                base_text = f"{name}: {pe.sets} подхода"

            comment = pe.comment or ""
            if "Разминка" in comment:
                warmup_lines.append(f"• {base_text}")
            elif "Заминка" in comment or "растяжка" in comment:
                cooldown_lines.append(f"• {base_text}")
            else:
                main_lines.append(f"• {base_text}")

        lines: List[str] = []

        # По ТЗ пользователь делает суставную разминку сам, конкретные
        # упражнения разминки в плане не перечисляются.
        lines.append("Суставная разминка (5–10 минут)")
        if main_lines:
            if lines:
                lines.append("")
            lines.append("Основная часть:")
            lines.extend(f"  {line}" for line in main_lines)
        if cooldown_lines:
            if lines:
                lines.append("")
            lines.append("Заминка:")
            lines.extend(f"  {line}" for line in cooldown_lines)

        return lines

    def _set_plan(self, plan: TrainingPlan) -> None:
        self._current_plan = plan
        self.week_combo.blockSignals(True)
        self.week_combo.clear()
        for w in range(1, plan.total_weeks + 1):
            self.week_combo.addItem(f"Неделя {w}", w)
        self.week_combo.blockSignals(False)

        if plan.total_weeks > 0:
            self.week_combo.setCurrentIndex(0)
            self._populate_table_for_week(1)

    def _populate_table_for_week(self, week_index: int) -> None:
        if self._current_plan is None:
            self.table.setRowCount(0)
            return

        sessions = [s for s in self._current_plan.sessions if s.week_index == week_index]
        sessions.sort(key=lambda s: s.day_index)

        self.table.setRowCount(len(sessions))

        for row, session in enumerate(sessions):
            day_item = QTableWidgetItem(f"День {session.day_index}")
            title_item = QTableWidgetItem(session.title)

            lines = self._format_session_exercises(week_index, session.day_index)
            exercises_item = QTableWidgetItem("\n".join(lines))
            exercises_item.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)

            self.table.setItem(row, 0, day_item)
            self.table.setItem(row, 1, title_item)
            self.table.setItem(row, 2, exercises_item)

        self.table.resizeRowsToContents()

    def _on_generate_clicked(self) -> None:
        profile = load_user_profile()
        if profile is None:
            QMessageBox.warning(self, "Профиль не найден", "Сначала заполните и сохраните профиль на вкладке 'Профиль'.")
            return

        try:
            exercises = load_exercises()
        except FileNotFoundError:
            QMessageBox.critical(self, "Ошибка", "Файл с упражнениями не найден (exercises.json).")
            return

        try:
            plan = generate_training_plan(profile, exercises)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Ошибка генерации", f"Не удалось сгенерировать план: {exc}")
            return

        save_training_plan(plan)
        self._set_plan(plan)
        self.status_label.setText("План тренировок сгенерирован и сохранён.")
        QMessageBox.information(self, "Готово", "План тренировок успешно сгенерирован.")

    def _on_week_changed(self, index: int) -> None:
        if index < 0:
            return
        week = self.week_combo.itemData(index)
        if not isinstance(week, int):
            return
        self._populate_table_for_week(week)
