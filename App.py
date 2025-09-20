from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QLabel, QVBoxLayout

class InsertDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Вставить govno")
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Форма для penis"))
        self.setLayout(layout)


class ShowDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Показать данные")
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Таблица данных"))
        self.setLayout(layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("main_window.ui", self)


        self.main_button_create.clicked.connect(self.create_schema)
        self.main_button_insert.clicked.connect(self.open_insert_dialog)
        self.main_button_show.clicked.connect(self.open_show_dialog)

    def create_schema(self):
        self.main_label_notification.setText("Схема и таблицы созданы")

    def open_insert_dialog(self):
        dialog = InsertDialog()
        dialog.exec()

    def open_show_dialog(self):
        dialog = InsertDialog()
        dialog.exec()


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
