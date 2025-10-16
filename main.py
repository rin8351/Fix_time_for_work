import sys
import json
import time
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon
import datetime

class TimeManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon('ico.png'))
        # Оставляем только кнопку закрытия
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)  
        self.is_working = False
        self.is_day_active = False
        self.start_time = None
        self.sessions = []
        self.is_compact = False  # Добавляем переменную для отслеживания компактного режима
        self.load_sessions()
        with open("styles.qss", "r") as file:
            self.setStyleSheet(file.read())

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)  # Обновление каждую секунду
        self.timer_start = None

        self.initUI()

    def update_style(self):
        if not self.is_day_active:
            self.setStyleSheet("background-color: #d3d3d3;")  # Серый фон
        elif self.is_working:
            self.setStyleSheet("background-color: #f5b7b1;")  # Красный фон
        else:
            self.setStyleSheet("background-color: #a3e4a3;")  # Зеленый фон

    def initUI(self):
        self.setWindowTitle("Time")
        self.setGeometry(100, 100, 200, 250)

        self.layout = QVBoxLayout()

        self.label = QLabel("Нажмите 'Начать рабочий день'", self)
        self.layout.addWidget(self.label)

        # Добавляем новый лейбл для счетчика
        self.timer_label = QLabel("00:00", self)
        self.layout.addWidget(self.timer_label)

        self.day_button = QPushButton("Начать рабочий день", self)
        self.day_button.clicked.connect(self.toggle_workday)
        self.layout.addWidget(self.day_button)

        self.button = QPushButton("Начать работу", self)
        self.button.clicked.connect(self.toggle_timer)
        self.button.setVisible(False)
        self.layout.addWidget(self.button)

        self.stats_button = QPushButton("Показать статистику", self)
        self.stats_button.clicked.connect(self.show_statistics)
        self.layout.addWidget(self.stats_button)
        if not self.is_day_active:
            self.stats_button.setVisible(False)
        else:
            self.stats_button.setVisible(True)

        self.on_top_button = QPushButton("Поверх всех окон", self)
        self.on_top_button.clicked.connect(self.toggle_on_top)
        self.layout.addWidget(self.on_top_button)

        # Добавляем кнопку "Уменьшить"
        self.compact_button = QPushButton("Уменьшить", self)
        self.compact_button.clicked.connect(self.toggle_compact)
        self.layout.addWidget(self.compact_button)

        # Создаем элементы для компактного режима
        self.compact_layout = QVBoxLayout()
        
        # Верхняя строка с временем и кнопками
        self.compact_top_layout = QHBoxLayout()
        
        self.compact_timer_label = QLabel("00:00", self)
        self.compact_timer_label.setAlignment(Qt.AlignCenter)
        self.compact_top_layout.addWidget(self.compact_timer_label)
        
        # Маленькая кнопка для смены режима (квадратик)
        self.compact_toggle_button = QPushButton("●", self)
        self.compact_toggle_button.setFixedSize(25, 25)
        self.compact_toggle_button.clicked.connect(self.toggle_timer)
        self.compact_top_layout.addWidget(self.compact_toggle_button)
        
        # Маленькая кнопка для увеличения окна
        self.expand_button = QPushButton("↑", self)
        self.expand_button.setFixedSize(25, 25)
        self.expand_button.clicked.connect(self.toggle_compact)
        self.compact_top_layout.addWidget(self.expand_button)
        
        # Нижняя строка с активностью
        self.compact_label = QLabel("Отдых", self)
        self.compact_label.setAlignment(Qt.AlignCenter)
        
        self.compact_layout.addLayout(self.compact_top_layout)
        self.compact_layout.addWidget(self.compact_label)
        
        # Создаем виджет для компактного режима
        self.compact_widget = QWidget()
        self.compact_widget.setLayout(self.compact_layout)
        self.layout.addWidget(self.compact_widget)
        self.compact_widget.setVisible(False)

        self.setLayout(self.layout)
        self.update_style()
        self.restore_last_state()

    def toggle_compact(self):
        """Переключение между обычным и компактным режимом"""
        self.is_compact = not self.is_compact
        
        if self.is_compact:
            # Скрываем все элементы обычного режима
            self.label.setVisible(False)
            self.timer_label.setVisible(False)
            self.day_button.setVisible(False)
            self.button.setVisible(False)
            self.stats_button.setVisible(False)
            self.on_top_button.setVisible(False)
            self.compact_button.setVisible(False)
            self.compact_label.setVisible(False)
            
            # Показываем элементы компактного режима
            self.compact_widget.setVisible(True)
            
            # Инициализируем компактный таймер
            if self.timer_start is not None and self.is_day_active:
                elapsed = int(time.time() - self.timer_start)
                hours = elapsed // 3600
                minutes = (elapsed % 3600) // 60
                time_text = f"{hours:02d}:{minutes:02d}"
                self.compact_timer_label.setText(time_text)
            
            # Изменяем размер окна на минимальный
            self.setFixedSize(150, 60)
        else:
            # Показываем все элементы обычного режима
            self.label.setVisible(True)
            self.timer_label.setVisible(True)
            self.day_button.setVisible(True)
            if self.is_day_active:
                self.button.setVisible(True)
            self.stats_button.setVisible(True)
            self.on_top_button.setVisible(True)
            self.compact_button.setVisible(True)
            
            # Скрываем элементы компактного режима
            self.compact_widget.setVisible(False)
            
            # Восстанавливаем обычный размер окна
            self.setMinimumSize(200, 250)
            self.setMaximumSize(16777215, 16777215)  # Убираем ограничения по максимальному размеру

    def toggle_workday(self):
        if self.is_day_active:
            self.day_button.setText("Начать рабочий день")
            self.label.setText("Нажмите 'Начать рабочий день'")
            self.button.setVisible(False)
            self.stats_button.setVisible(False)
            self.is_day_active = False
            self.save_sessions(clear=True)
        else:
            self.day_button.setText("Закончить рабочий день")
            self.label.setText("Рабочий день начался")
            self.button.setVisible(True)
            self.stats_button.setVisible(True)
            self.is_day_active = True
            self.save_sessions()
        
        
        # Сбрасываем компактный таймер если день не активен
        if not self.is_day_active:
            self.compact_timer_label.setText("00:00")
        
        self.update_style()

    def toggle_timer(self):
        current_time = time.time()
        # Сбрасываем счетчик
        self.timer_start = time.time()
        
        if self.is_working:
            self.sessions.append(("Работа", self.start_time, current_time))
            self.button.setText("Начать работу")
            self.label.setText("Режим: Отдых")
        else:
            if self.start_time is not None:
                self.sessions.append(("Отдых", self.start_time, current_time))
            self.button.setText("Закончить работу")
            self.label.setText("Режим: Работа")

        self.start_time = current_time
        self.is_working = not self.is_working
        
        # Сбрасываем компактный таймер при смене режима
        self.compact_timer_label.setText("00:00")
        
        self.save_sessions()
        self.update_style()

    def save_sessions(self, clear=False):
        data = {"day_active": self.is_day_active, "is_working": self.is_working, 
                "start_time": self.start_time, "sessions": self.sessions}
        if clear:
            data = {"day_active": False, "is_working": False, "start_time": None, "sessions": []}
        with open("sessions.json", "w") as file:
            json.dump(data, file)

    def load_sessions(self):
        try:
            with open("sessions.json", "r") as file:
                data = json.load(file)
                self.is_day_active = data.get("day_active", False)
                self.is_working = data.get("is_working", False)
                self.start_time = data.get("start_time", None)
                self.sessions = data.get("sessions", [])
        except FileNotFoundError:
            self.sessions = []
            self.is_day_active = False
            self.is_working = False
            self.start_time = None

    def restore_last_state(self):
        if self.is_day_active:
            self.day_button.setText("Закончить рабочий день")
            self.label.setText("Рабочий день начался")
            self.button.setVisible(True)
        
        if self.is_working and self.start_time is not None:
            self.button.setText("Закончить работу")
            self.label.setText("Режим: Работа")
        elif self.is_day_active:
            self.button.setText("Начать работу")
            self.label.setText("Режим: Отдых")
        
        # Инициализируем компактный таймер
        if self.timer_start is not None and self.is_day_active:
            elapsed = int(time.time() - self.timer_start)
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            time_text = f"{hours:02d}:{minutes:02d}"
            self.compact_timer_label.setText(time_text)

    def toggle_on_top(self):
        flags = self.windowFlags()
        if flags & Qt.WindowStaysOnTopHint:
            self.setWindowFlags(flags & ~Qt.WindowStaysOnTopHint)
            self.on_top_button.setText("Поверх всех окон")
        else:
            self.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
            self.on_top_button.setText("Обычный режим")
        self.show()

    def show_statistics(self):
        self.load_sessions()
        if not self.sessions:
            return
        times = []
        labels = []
        total_work = 0
        total_rest = 0
        
        for i, (mode, start, end) in enumerate(self.sessions):
            duration = (end - start) / 60  # Перевод в минуты
            times.append(duration)
            labels.append(str(i+1))  # Просто номер сессии без текста
            if "Работа" in mode:
                total_work += duration
            else:
                total_rest += duration

        # Создаем график
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # График сессий
        bars = ax.bar(labels, times, color=["blue" if "Работа" in self.sessions[i][0] else "red" for i in range(len(labels))])
        ax.set_ylabel("Длительность (мин)")
        
        # Добавляем настройку делений оси Y с шагом 5 минут
        y_max = max(times) + 5  # Максимальное значение + небольшой отступ
        ax.set_yticks(range(0, int(y_max), 5))  # Создаем деления с шагом 5
        
        # Добавляем значения над каждым столбцом
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}',
                    ha='center', va='bottom')
        
        ax.set_title("Статистика работы и отдыха")
        ax.tick_params(axis='x', rotation=45)

        work_time = 0
        rest_time = 0

        for period in self.sessions:
            activity = period[0]
            start_time = float(period[1])  # Преобразуем строку в число
            end_time = float(period[2])    # Преобразуем строку в число
            duration = end_time - start_time  # Время в секундах
            
            if activity == "Работа":
                work_time += duration
            elif activity == "Отдых":
                rest_time += duration
        
        # Добавляем текст с общим временем внизу графика
        work_time_formatted = str(datetime.timedelta(seconds=int(work_time)))
        rest_time_formatted = str(datetime.timedelta(seconds=int(rest_time)))
        summary_text = f'Работа - {work_time_formatted}, Отдых - {rest_time_formatted}'
        plt.figtext(0.5, 0.0, summary_text, ha='center', fontsize=14)
        
        plt.tight_layout()
        plt.show()

    def update_timer(self):
        if self.timer_start is not None and self.is_day_active:
            elapsed = int(time.time() - self.timer_start)
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            time_text = f"{hours:02d}:{minutes:02d}"
            self.timer_label.setText(time_text)
            # Обновляем время и в компактном режиме
            self.compact_timer_label.setText(time_text)
        else:
            # Если таймер не активен, показываем 00:00
            self.compact_timer_label.setText("00:00")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = TimeManager()
    ex.show()
    sys.exit(app.exec_())