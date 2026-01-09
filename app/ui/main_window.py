from PySide6.QtWidgets import QMainWindow, QTabWidget

from app.ui.plan_view import TrainingPlanView
from app.ui.profile_form import UserProfileForm


class MainWindow(QMainWindow):
    """Главное окно приложения.

    На этом этапе содержит вкладку с формой профиля пользователя.
    В следующих этапах будут добавлены вкладки с планом тренировок
    и визуализацией графиков.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Рекомендательная система тренировок")
        self.setMinimumSize(900, 600)
        self.resize(1100, 750)
        self._init_ui()

    def _init_ui(self) -> None:
        tabs = QTabWidget(self)
        self.profile_tab = UserProfileForm(tabs)
        tabs.addTab(self.profile_tab, "Профиль")

        self.plan_tab = TrainingPlanView(tabs)
        tabs.addTab(self.plan_tab, "План тренировок")

        self.setCentralWidget(tabs)
