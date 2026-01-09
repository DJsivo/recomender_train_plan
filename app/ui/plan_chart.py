from __future__ import annotations

from typing import List

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from app.core.data_access import load_training_plan
from app.core.models import TrainingPlan


class PlanChartView(QWidget):
    """Вкладка с графиком количества тренировок по неделям."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_plan: TrainingPlan | None = None
        self._init_ui()
        self.refresh_from_plan()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.info_label = QLabel(
            "График показывает, сколько тренировок запланировано на каждую неделю.",
            self,
        )
        self.info_label.setWordWrap(True)

        self.figure = Figure(figsize=(5, 3))
        self.canvas = FigureCanvas(self.figure)

        self.refresh_button = QPushButton("Обновить график", self)
        self.refresh_button.clicked.connect(self.refresh_from_plan)

        self.status_label = QLabel("", self)
        self.status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        layout.addWidget(self.info_label)
        layout.addWidget(self.canvas)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.status_label)

    def set_plan(self, plan: TrainingPlan) -> None:
        """Принимает новый план и обновляет график."""

        self._current_plan = plan
        self._draw_chart()

    def refresh_from_plan(self) -> None:
        """Загружает последний сохранённый план из файла и обновляет график."""

        plan = load_training_plan()
        if plan is None:
            self._current_plan = None
            self._clear_chart("План ещё не сгенерирован.")
            return

        self._current_plan = plan
        self._draw_chart()
        self.status_label.setText("График обновлён по текущему плану тренировок.")

    def _clear_chart(self, message: str | None = None) -> None:
        ax = self.figure.gca()
        ax.clear()
        ax.set_title("Нет данных для отображения")
        ax.set_xlabel("")
        ax.set_ylabel("")
        self.canvas.draw()
        if message:
            self.status_label.setText(message)

    def _draw_chart(self) -> None:
        if self._current_plan is None:
            self._clear_chart("План ещё не сгенерирован.")
            return

        weeks = list(range(1, self._current_plan.total_weeks + 1))
        counts: List[int] = []
        for w in weeks:
            count = sum(1 for s in self._current_plan.sessions if s.week_index == w)
            counts.append(count)

        if not weeks:
            self._clear_chart("План пуст.")
            return

        ax = self.figure.gca()
        ax.clear()
        ax.bar(weeks, counts, color="#4A90E2")
        ax.set_xlabel("Неделя программы")
        ax.set_ylabel("Количество тренировок")
        ax.set_title("Тренировки по неделям")
        ax.set_xticks(weeks)
        self.canvas.draw()

        self.status_label.setText(
            f"Всего недель: {self._current_plan.total_weeks}, тренировок в неделю: {self._current_plan.sessions_per_week}."
        )
