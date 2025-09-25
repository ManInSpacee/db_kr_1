import sys
import logging
from PyQt5 import uic
from PyQt5.QtWidgets import (QApplication, QMainWindow, QDialog, QLabel, QVBoxLayout,
                             QLineEdit, QPushButton, QFormLayout, QMessageBox, QComboBox,
                             QTextEdit, QWidget, QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QSpinBox, QCheckBox, QDateTimeEdit)
from PyQt5.QtCore import Qt, QDateTime
import os
import db  # наш модуль db.py
import datetime

# Настройка логирования
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "app.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger("app")

class InsertDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Вставить данные")
        self.setModal(True)  # модальное окно
        self.resize(420, 300)

        form = QFormLayout()

        self.experiment_name = QLineEdit()
        form.addRow("Experiment name:", self.experiment_name)

        self.experiment_desc = QTextEdit()
        self.experiment_desc.setFixedHeight(60)
        form.addRow("Description:", self.experiment_desc)

        # attack types — пользователь вводит через запятую, либо выбрать
        self.attack_types_input = QLineEdit()
        self.attack_types_input.setPlaceholderText("UDP_FLOOD,SYN_FLOOD")
        form.addRow("Attack types (CSV):", self.attack_types_input)

        self.source_ips_input = QLineEdit()
        self.source_ips_input.setPlaceholderText("192.0.2.1,198.51.100.2")
        form.addRow("Source IPs (CSV):", self.source_ips_input)

        self.packet_rate = QSpinBox()
        self.packet_rate.setRange(1, 100000000)
        self.packet_rate.setValue(1000)
        form.addRow("Packet rate (>0):", self.packet_rate)

        self.severity = QComboBox()
        self.severity.addItems(["LOW", "MEDIUM", "HIGH"])
        form.addRow("Severity:", self.severity)

        self.detected = QCheckBox("Detected by model")
        form.addRow(self.detected)

        btn_box = QHBoxLayout()
        btn_insert = QPushButton("Добавить")
        btn_cancel = QPushButton("Отмена")
        btn_box.addWidget(btn_insert)
        btn_box.addWidget(btn_cancel)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(btn_box)
        self.setLayout(layout)

        btn_insert.clicked.connect(self.on_insert)
        btn_cancel.clicked.connect(self.reject)

    def on_insert(self):
        name = self.experiment_name.text().strip()
        desc = self.experiment_desc.toPlainText().strip()
        attack_csv = self.attack_types_input.text().strip()
        ips_csv = self.source_ips_input.text().strip()
        packet_rate = int(self.packet_rate.value())
        severity = self.severity.currentText()
        detected = bool(self.detected.isChecked())

        if not name:
            QMessageBox.warning(self, "Ошибка", "Имя эксперимента обязательно (NOT NULL).")
            return

        # Преобразуем CSV в списки
        attack_types = [s.strip() for s in attack_csv.split(",") if s.strip()]
        source_ips = [s.strip() for s in ips_csv.split(",") if s.strip()]

        try:
            exp_id, run_id = db.insert_experiment_and_run(
                experiment_name=name,
                experiment_description=desc,
                attack_types_list=attack_types,
                source_ip_list=source_ips,
                packet_rate=packet_rate,
                severity=severity,
                detected=detected
            )
            QMessageBox.information(self, "Успех", f"Вставлено: experiment_id={exp_id}, run_id={run_id}")
            self.accept()
        except Exception as e:
            logger.exception("Ошибка при вставке данных")
            QMessageBox.critical(self, "Ошибка при вставке", str(e))

class ShowDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Показать данные")
        self.resize(800, 400)
        self.setModal(False)  # немодальное окно

        v = QVBoxLayout()

        # Фильтры
        filter_layout = QHBoxLayout()
        self.filter_attack = QLineEdit()
        self.filter_attack.setPlaceholderText("Например: SYN_FLOOD")
        self.filter_packet_min = QSpinBox()
        self.filter_packet_min.setRange(0, 100000000)
        self.filter_packet_min.setValue(0)
        self.filter_since = QDateTimeEdit(QDateTime.currentDateTime().addDays(-7))
        self.filter_since.setCalendarPopup(True)
        btn_apply = QPushButton("Применить фильтр")
        filter_layout.addWidget(QLabel("Attack type:"))
        filter_layout.addWidget(self.filter_attack)
        filter_layout.addWidget(QLabel("Min packet rate:"))
        filter_layout.addWidget(self.filter_packet_min)
        filter_layout.addWidget(QLabel("Since:"))
        filter_layout.addWidget(self.filter_since)
        filter_layout.addWidget(btn_apply)

        v.addLayout(filter_layout)

        # Таблица
        self.table = QTableWidget()
        v.addWidget(self.table)

        self.setLayout(v)

        btn_apply.clicked.connect(self.load_data)
        self.load_data()

    def load_data(self):
        # Получаем значения фильтров
        attack_type = self.filter_attack.text().strip() or None
        min_rate = self.filter_packet_min.value()
        if min_rate <= 0:
            min_rate = None
        since_qt = self.filter_since.dateTime().toPyDateTime() if self.filter_since.dateTime() else None

        # Если все фильтры пустые/0, покажем все данные
        try:
            rows = db.query_runs(
                filter_attack_type=attack_type,
                since=since_qt,
                min_packet_rate=min_rate
            )
            self.table.setRowCount(len(rows))
            self.table.setColumnCount(8)
            self.table.setHorizontalHeaderLabels([
                "Run ID", "Experiment", "Attack Types", "Source IPs",
                "Packet Rate", "Severity", "Detected", "Run Time"
            ])

            for i, row in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(str(row['run_id'])))
                self.table.setItem(i, 1, QTableWidgetItem(str(row['experiment_name'])))
                self.table.setItem(i, 2, QTableWidgetItem(','.join(row['attack_types'])))
                self.table.setItem(i, 3, QTableWidgetItem(','.join(row['source_ips'])))
                self.table.setItem(i, 4, QTableWidgetItem(str(row['packet_rate'])))
                self.table.setItem(i, 5, QTableWidgetItem(row['severity']))
                self.table.setItem(i, 6, QTableWidgetItem(str(row['detected'])))
                self.table.setItem(i, 7, QTableWidgetItem(str(row['run_time'])))
        except Exception as e:
            print("Ошибка при загрузке данных:", e)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/main_window.ui", self)

        # подключение кнопок (имена объектов должны совпадать с main_window.ui)
        self.main_button_create.clicked.connect(self.create_schema)
        self.main_button_insert.clicked.connect(self.open_insert_dialog)
        self.main_button_show.clicked.connect(self.open_show_dialog)

    def create_schema(self):
        try:
            with open("schema.sql", "r", encoding="utf-8") as f:
                sql_text = f.read()
            db.execute_script(sql_text)
            self.main_label_notification.setText("Схема и таблицы созданы")
            logger.info("Schema created by user action")
        except Exception as e:
            logger.exception("Error creating schema")
            QMessageBox.critical(self, "Ошибка создания схемы", str(e))
            self.main_label_notification.setText("Ошибка при создании схемы")

    def open_insert_dialog(self):
        dialog = InsertDialog(self)
        dialog.exec()  # модальное

    def open_show_dialog(self):
        dialog = ShowDialog(self)
        dialog.show()  # немодальное

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
