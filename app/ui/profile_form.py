from __future__ import annotations

from typing import Dict, List

from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.data_access import load_user_profile, save_user_profile
from app.core.models import UserProfile


class UserProfileForm(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_mappings()
        self._init_ui()
        self._load_existing_profile()

    def _init_mappings(self) -> None:
        self._gender_map: Dict[str, str] = {
            "Мужской": "male",
            "Женский": "female",
        }

        self._activity_map: Dict[str, str] = {
            "Низкий (сидячий образ жизни)": "low",
            "Средний (1-3 тренировки в неделю)": "medium",
            "Высокий (4+ тренировок, активная работа)": "high",
        }

        self._goal_map: Dict[str, str] = {
            "Похудение": "weight_loss",
            "Набор мышечной массы": "muscle_gain",
            "Поддержание формы": "maintenance",
            "Выносливость": "endurance",
            "Укрепление спины": "back_health",
            "Общее здоровье": "general_health",
        }

        self._experience_map: Dict[str, str] = {
            "Новичок": "beginner",
            "Продолжающий": "intermediate",
            "Продвинутый": "advanced",
        }

        self._location_map: Dict[str, str] = {
            "Дом": "home",
            "Спортзал": "gym",
            "Не важно": "no_preference",
        }

        self._health_issue_map: Dict[str, str] = {
            "Проблемы с суставами": "суставы",
            "Проблемы со спиной": "спина",
            "Сердечно-сосудистые": "сердце",
            "Ожирение / избыточный вес": "ожирение",
        }

        self._condition_issue_map: Dict[str, str] = {
            "ИБС / стенокардия": "cardio_ihd",
            "Гипертония (контролируемая)": "cardio_hypertension",
            "Нарушения ритма сердца": "cardio_arrhythmia",
            "ХСН (лёгкая)": "cardio_heart_failure_mild",
            "Артроз коленных суставов": "joint_knee_arthrosis",
            "Артроз тазобедренных суставов": "joint_hip_arthrosis",
            "Проблемы плечевого сустава": "joint_shoulder_impingement",
            "Боли в локтях/запястьях": "joint_elbow_wrist_pain",
            "Хроническая боль в пояснице": "spine_lumbar_pain",
            "Проблемы шейного отдела": "spine_cervical_pain",
            "После операций на позвоночнике": "spine_post_surgery",
            "Ожирение (медицинский диагноз)": "metabolic_obesity",
            "Сахарный диабет 2 типа": "metabolic_diabetes_type2",
            "Бронхиальная астма (лёгкая)": "resp_asthma_mild",
            "Беременность (без осложнений)": "other_pregnancy",
            "После больших операций": "other_post_surgery_general",
        }

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        personal_group = QGroupBox("Личные данные", self)
        personal_layout = QFormLayout(personal_group)

        self.gender_combo = QComboBox(personal_group)
        self.gender_combo.addItems(self._gender_map.keys())

        self.age_edit = QLineEdit(personal_group)
        self.age_edit.setPlaceholderText("полных лет")
        self.age_edit.setValidator(QIntValidator(1, 120, self))

        self.weight_edit = QLineEdit(personal_group)
        self.weight_edit.setPlaceholderText("кг")
        weight_validator = QDoubleValidator(1.0, 500.0, 1, self)
        weight_validator.setNotation(QDoubleValidator.StandardNotation)
        self.weight_edit.setValidator(weight_validator)

        self.height_edit = QLineEdit(personal_group)
        self.height_edit.setPlaceholderText("см (по желанию)")
        self.height_edit.setValidator(QIntValidator(100, 250, self))

        personal_layout.addRow("Пол:", self.gender_combo)
        personal_layout.addRow("Возраст:", self.age_edit)
        personal_layout.addRow("Вес:", self.weight_edit)
        personal_layout.addRow("Рост:", self.height_edit)

        activity_group = QGroupBox("Цели и активность", self)
        activity_layout = QFormLayout(activity_group)

        self.activity_combo = QComboBox(activity_group)
        self.activity_combo.addItems(self._activity_map.keys())

        self.goal_combo = QComboBox(activity_group)
        self.goal_combo.addItems(self._goal_map.keys())

        activity_layout.addRow("Уровень активности:", self.activity_combo)
        activity_layout.addRow("Цель тренировок:", self.goal_combo)

        self.sessions_per_week_spin = QSpinBox(activity_group)
        self.sessions_per_week_spin.setRange(1, 7)
        self.sessions_per_week_spin.setValue(3)
        activity_layout.addRow("Максимум тренировок в неделю:", self.sessions_per_week_spin)

        experience_group = QGroupBox("Опыт и формат тренировок", self)
        exp_layout = QFormLayout(experience_group)

        self.experience_combo = QComboBox(experience_group)
        self.experience_combo.addItems(self._experience_map.keys())

        self.location_combo = QComboBox(experience_group)
        self.location_combo.addItems(self._location_map.keys())

        equipment_widget = QWidget(experience_group)
        equipment_layout = QGridLayout(equipment_widget)
        self.equipment_checks: List[QCheckBox] = []
        equipment_labels = [
            "Коврик",
            "Гантели",
            "Турник",
            "Скакалка",
            "Степ / платформа",
            "Тренажёрный зал",
        ]
        for idx, label in enumerate(equipment_labels):
            cb = QCheckBox(label, equipment_widget)
            row = idx // 2
            col = idx % 2
            equipment_layout.addWidget(cb, row, col)
            self.equipment_checks.append(cb)

        exp_layout.addRow("Опыт тренировок:", self.experience_combo)
        exp_layout.addRow("Где планируете тренироваться:", self.location_combo)
        exp_layout.addRow(QLabel("Доступное оборудование:"), equipment_widget)

        health_group = QGroupBox("Здоровье и ограничения", self)
        health_layout = QVBoxLayout(health_group)

        scroll = QScrollArea(health_group)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        health_content = QWidget(scroll)
        health_content_layout = QVBoxLayout(health_content)
        health_content_layout.setContentsMargins(4, 4, 4, 4)
        health_content_layout.setSpacing(4)

        self.health_checks: List[QCheckBox] = []
        for label in self._health_issue_map.keys():
            cb = QCheckBox(label, health_content)
            self.health_checks.append(cb)
            health_content_layout.addWidget(cb)

        conditions_title = QLabel("Болезни и состояния (расширенный список):", health_content)
        health_content_layout.addWidget(conditions_title)

        self.condition_checks: List[QCheckBox] = []
        for label in self._condition_issue_map.keys():
            cb = QCheckBox(label, health_content)
            self.condition_checks.append(cb)
            health_content_layout.addWidget(cb)

        scroll.setWidget(health_content)
        health_layout.addWidget(scroll)

        # Блок "Другие ограничения" убран по ТЗ: используем только
        # стандартизированные чекбоксы и, при необходимости, медицинский слой.

        buttons_widget = QWidget(self)
        buttons_layout = QGridLayout(buttons_widget)

        self.save_button = QPushButton("Сохранить профиль", buttons_widget)
        self.save_button.clicked.connect(self._on_save_clicked)

        self.status_label = QLabel("", buttons_widget)
        self.status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        buttons_layout.addWidget(self.save_button, 0, 0)
        buttons_layout.addWidget(self.status_label, 0, 1)
        buttons_layout.setColumnStretch(1, 1)

        main_layout.addWidget(personal_group)
        main_layout.addWidget(activity_group)
        main_layout.addWidget(experience_group)
        main_layout.addWidget(health_group)
        main_layout.addWidget(buttons_widget)
        main_layout.addStretch()

    def _load_existing_profile(self) -> None:
        profile = load_user_profile()
        if profile is None:
            return
        self._fill_from_profile(profile)
        self.status_label.setText("Загружен сохранённый профиль пользователя.")

    def _fill_from_profile(self, profile: UserProfile) -> None:
        for label, code in self._gender_map.items():
            if code == profile.gender:
                self.gender_combo.setCurrentText(label)
                break

        self.age_edit.setText(str(profile.age))
        self.weight_edit.setText(str(profile.weight_kg))
        if profile.height_cm is not None:
            self.height_edit.setText(str(int(profile.height_cm)))

        for label, code in self._activity_map.items():
            if code == profile.activity_level:
                self.activity_combo.setCurrentText(label)
                break

        for label, code in self._goal_map.items():
            if code == profile.goal:
                self.goal_combo.setCurrentText(label)
                break

        for label, code in self._experience_map.items():
            if code == profile.experience_level:
                self.experience_combo.setCurrentText(label)
                break

        for label, code in self._location_map.items():
            if code == profile.preferred_location:
                self.location_combo.setCurrentText(label)
                break

        equipment_set = set(profile.available_equipment)
        for cb in self.equipment_checks:
            if cb.text() in equipment_set:
                cb.setChecked(True)

        issues_set = set(profile.health_issues)
        for cb in self.health_checks:
            code = self._health_issue_map[cb.text()]
            if code in issues_set:
                cb.setChecked(True)

        for cb in getattr(self, "condition_checks", []):
            code = self._condition_issue_map[cb.text()]
            if code in issues_set:
                cb.setChecked(True)

        if hasattr(profile, "max_sessions_per_week"):
            self.sessions_per_week_spin.setValue(max(1, min(7, int(profile.max_sessions_per_week))))

    def _collect_equipment(self) -> List[str]:
        return [cb.text() for cb in self.equipment_checks if cb.isChecked()]

    def _collect_health_issues(self) -> List[str]:
        issues: List[str] = []
        for cb in self.health_checks:
            if cb.isChecked():
                issues.append(self._health_issue_map[cb.text()])
        for cb in getattr(self, "condition_checks", []):
            if cb.isChecked():
                issues.append(self._condition_issue_map[cb.text()])
        return issues

    def _build_profile(self) -> UserProfile:
        gender_label = self.gender_combo.currentText()
        gender_code = self._gender_map.get(gender_label)
        if gender_code is None:
            raise ValueError("Выберите пол.")

        age_text = self.age_edit.text().strip()
        if not age_text:
            raise ValueError("Введите возраст в формате целого числа.")
        try:
            age = int(age_text)
        except ValueError as exc:  # noqa: PERF203
            raise ValueError("Введите возраст в формате целого числа.") from exc
        if age <= 0:
            raise ValueError("Возраст должен быть больше 0.")

        weight_text = self.weight_edit.text().strip()
        if not weight_text:
            raise ValueError("Введите вес в формате числа (кг).")
        try:
            weight = float(weight_text.replace(",", "."))
        except ValueError as exc:  # noqa: PERF203
            raise ValueError("Введите вес в формате числа (кг).") from exc
        if weight <= 0:
            raise ValueError("Вес должен быть больше 0 кг.")

        height_cm = None
        height_text = self.height_edit.text().strip()
        if height_text:
            try:
                height_val = int(height_text)
            except ValueError as exc:  # noqa: PERF203
                raise ValueError("Введите рост в формате целого числа (см).") from exc
            if height_val <= 0:
                raise ValueError("Рост должен быть больше 0 см.")
            height_cm = float(height_val)

        activity_label = self.activity_combo.currentText()
        activity_code = self._activity_map.get(activity_label)
        if activity_code is None:
            raise ValueError("Выберите уровень физической активности.")

        goal_label = self.goal_combo.currentText()
        goal_code = self._goal_map.get(goal_label)
        if goal_code is None:
            raise ValueError("Выберите цель тренировок.")

        experience_label = self.experience_combo.currentText()
        experience_code = self._experience_map.get(experience_label)
        if experience_code is None:
            raise ValueError("Выберите опыт тренировок.")

        location_label = self.location_combo.currentText()
        location_code = self._location_map.get(location_label)
        if location_code is None:
            raise ValueError("Выберите формат тренировок (дом/зал).")

        available_equipment = self._collect_equipment()
        health_issues = self._collect_health_issues()
        max_sessions_per_week = self.sessions_per_week_spin.value()

        return UserProfile(
            gender=gender_code,
            age=age,
            weight_kg=weight,
            height_cm=height_cm,
            activity_level=activity_code,
            goal=goal_code,
            experience_level=experience_code,
            preferred_location=location_code,
            available_equipment=available_equipment,
            health_issues=health_issues,
            max_sessions_per_week=max_sessions_per_week,
        )

    def _on_save_clicked(self) -> None:
        try:
            profile = self._build_profile()
        except ValueError as exc:
            QMessageBox.warning(self, "Ошибка ввода", str(exc))
            self.status_label.setText("")
            return

        save_user_profile(profile)
        self.status_label.setText("Профиль сохранён.")
        QMessageBox.information(self, "Профиль сохранён", "Данные профиля успешно сохранены.")
