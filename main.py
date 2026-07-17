import sys
import json
import time
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon
import datetime

ACTIVITY_WORK = "Work"
ACTIVITY_REST = "Rest"


def is_work_activity(activity):
    return activity == ACTIVITY_WORK


class TimeManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon('ico.png'))
        # Keep only the close button
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
        self.is_working = False
        self.is_day_active = False
        self.start_time = None
        self.sessions = []
        self.is_compact = False  # Track compact mode state
        self.load_sessions()
        with open("styles.qss", "r") as file:
            self.setStyleSheet(file.read())

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)  # Update every second
        self.timer_start = None

        self.initUI()

    def update_style(self):
        if not self.is_day_active:
            self.setStyleSheet("background-color: #d3d3d3;")  # Gray background
        elif self.is_working:
            self.setStyleSheet("background-color: #f5b7b1;")  # Red background
        else:
            self.setStyleSheet("background-color: #a3e4a3;")  # Green background

    def initUI(self):
        self.setWindowTitle("Time")
        self.setGeometry(100, 100, 200, 250)

        self.layout = QVBoxLayout()

        self.label = QLabel("Click 'Start working day'", self)
        self.layout.addWidget(self.label)

        # Timer counter label
        self.timer_label = QLabel("00:00", self)
        self.layout.addWidget(self.timer_label)

        self.day_button = QPushButton("Start working day", self)
        self.day_button.clicked.connect(self.toggle_workday)
        self.layout.addWidget(self.day_button)

        self.button = QPushButton("Start work", self)
        self.button.clicked.connect(self.toggle_timer)
        self.button.setVisible(False)
        self.layout.addWidget(self.button)

        self.stats_button = QPushButton("Show statistics", self)
        self.stats_button.clicked.connect(self.show_statistics)
        self.layout.addWidget(self.stats_button)
        if not self.is_day_active:
            self.stats_button.setVisible(False)
        else:
            self.stats_button.setVisible(True)

        self.on_top_button = QPushButton("Always on top", self)
        self.on_top_button.clicked.connect(self.toggle_on_top)
        self.layout.addWidget(self.on_top_button)

        # Minimize button
        self.compact_button = QPushButton("Minimize", self)
        self.compact_button.clicked.connect(self.toggle_compact)
        self.layout.addWidget(self.compact_button)

        # Compact mode widgets
        self.compact_layout = QVBoxLayout()

        # Top row with timer and buttons
        self.compact_top_layout = QHBoxLayout()

        self.compact_timer_label = QLabel("00:00", self)
        self.compact_timer_label.setAlignment(Qt.AlignCenter)
        self.compact_top_layout.addWidget(self.compact_timer_label)

        # Small mode toggle button (square)
        self.compact_toggle_button = QPushButton("●", self)
        self.compact_toggle_button.setFixedSize(25, 25)
        self.compact_toggle_button.clicked.connect(self.toggle_timer)
        self.compact_top_layout.addWidget(self.compact_toggle_button)

        # Small expand window button
        self.expand_button = QPushButton("↑", self)
        self.expand_button.setFixedSize(25, 25)
        self.expand_button.clicked.connect(self.toggle_compact)
        self.compact_top_layout.addWidget(self.expand_button)

        # Bottom row with activity label
        self.compact_label = QLabel("Rest", self)
        self.compact_label.setAlignment(Qt.AlignCenter)

        self.compact_layout.addLayout(self.compact_top_layout)
        self.compact_layout.addWidget(self.compact_label)

        # Compact mode container widget
        self.compact_widget = QWidget()
        self.compact_widget.setLayout(self.compact_layout)
        self.layout.addWidget(self.compact_widget)
        self.compact_widget.setVisible(False)

        self.setLayout(self.layout)
        self.update_style()
        self.restore_last_state()

    def toggle_compact(self):
        """Switch between normal and compact mode."""
        self.is_compact = not self.is_compact

        if self.is_compact:
            # Hide normal mode widgets
            self.label.setVisible(False)
            self.timer_label.setVisible(False)
            self.day_button.setVisible(False)
            self.button.setVisible(False)
            self.stats_button.setVisible(False)
            self.on_top_button.setVisible(False)
            self.compact_button.setVisible(False)
            self.compact_label.setVisible(False)

            # Show compact mode widgets
            self.compact_widget.setVisible(True)

            # Initialize compact timer
            if self.timer_start is not None and self.is_day_active:
                elapsed = int(time.time() - self.timer_start)
                hours = elapsed // 3600
                minutes = (elapsed % 3600) // 60
                time_text = f"{hours:02d}:{minutes:02d}"
                self.compact_timer_label.setText(time_text)

            # Shrink window to minimum size
            self.setFixedSize(150, 60)
        else:
            # Show normal mode widgets
            self.label.setVisible(True)
            self.timer_label.setVisible(True)
            self.day_button.setVisible(True)
            if self.is_day_active:
                self.button.setVisible(True)
            self.stats_button.setVisible(True)
            self.on_top_button.setVisible(True)
            self.compact_button.setVisible(True)

            # Hide compact mode widgets
            self.compact_widget.setVisible(False)

            # Restore normal window size
            self.setMinimumSize(200, 250)
            self.setMaximumSize(16777215, 16777215)  # Remove max size constraints

    def toggle_workday(self):
        if self.is_day_active:
            self.day_button.setText("Start working day")
            self.label.setText("Click 'Start working day'")
            self.button.setVisible(False)
            self.stats_button.setVisible(False)
            self.is_day_active = False
            self.save_sessions(clear=True)
        else:
            self.day_button.setText("End working day")
            self.label.setText("Working day started")
            self.button.setVisible(True)
            self.stats_button.setVisible(True)
            self.is_day_active = True
            self.save_sessions()

        # Reset compact timer when the day is inactive
        if not self.is_day_active:
            self.compact_timer_label.setText("00:00")

        self.update_style()

    def toggle_timer(self):
        current_time = time.time()
        # Reset counter
        self.timer_start = time.time()

        if self.is_working:
            self.sessions.append((ACTIVITY_WORK, self.start_time, current_time))
            self.button.setText("Start work")
            self.label.setText("Mode: Rest")
        else:
            if self.start_time is not None:
                self.sessions.append((ACTIVITY_REST, self.start_time, current_time))
            self.button.setText("End work")
            self.label.setText("Mode: Work")

        self.start_time = current_time
        self.is_working = not self.is_working

        # Reset compact timer on mode change
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
            self.day_button.setText("End working day")
            self.label.setText("Working day started")
            self.button.setVisible(True)

        if self.is_working and self.start_time is not None:
            self.button.setText("End work")
            self.label.setText("Mode: Work")
        elif self.is_day_active:
            self.button.setText("Start work")
            self.label.setText("Mode: Rest")

        # Initialize compact timer
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
            self.on_top_button.setText("Always on top")
        else:
            self.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
            self.on_top_button.setText("Normal mode")
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
            duration = (end - start) / 60  # Convert to minutes
            times.append(duration)
            labels.append(str(i + 1))  # Session number only
            if is_work_activity(mode):
                total_work += duration
            else:
                total_rest += duration

        # Build chart
        fig, ax = plt.subplots(figsize=(10, 6))

        # Session bars
        bars = ax.bar(
            labels,
            times,
            color=["blue" if is_work_activity(self.sessions[i][0]) else "red" for i in range(len(labels))],
        )
        ax.set_ylabel("Duration (min)")

        # Y-axis ticks every 5 minutes
        y_max = max(times) + 5  # Max value plus small padding
        ax.set_yticks(range(0, int(y_max), 5))

        # Value labels above each bar
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2.0, height,
                    f'{height:.1f}',
                    ha='center', va='bottom')

        ax.set_title("Work and rest statistics")
        ax.tick_params(axis='x', rotation=45)

        work_time = 0
        rest_time = 0

        for period in self.sessions:
            activity = period[0]
            start_time = float(period[1])  # Convert string to number
            end_time = float(period[2])
            duration = end_time - start_time  # Time in seconds

            if is_work_activity(activity):
                work_time += duration
            else:
                rest_time += duration

        # Total time summary below the chart
        work_time_formatted = str(datetime.timedelta(seconds=int(work_time)))
        rest_time_formatted = str(datetime.timedelta(seconds=int(rest_time)))
        summary_text = f'Work - {work_time_formatted}, Rest - {rest_time_formatted}'
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
            # Update compact mode timer too
            self.compact_timer_label.setText(time_text)
        else:
            # Show 00:00 when timer is inactive
            self.compact_timer_label.setText("00:00")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = TimeManager()
    ex.show()
    sys.exit(app.exec_())
