from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow


def main() -> None:
    app = QApplication([])

    # Явно задаём читаемый базовый размер шрифта для всего приложения,
    # чтобы избежать ситуаций с микроскопическим текстом.
    font = app.font()
    font.setPointSize(11)
    app.setFont(font)

    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
