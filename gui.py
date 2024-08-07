import sys
import os
import tempfile
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QLineEdit, QPushButton, QComboBox, QProgressBar
from PyQt6.QtCore import QThread, pyqtSignal

from trophy_generator import edit_blender_texts_and_export_scene
from prusaslicer import slice_stl
from gcode_sender import MarlinPrinter

class WorkerThread(QThread):
    update_progress = pyqtSignal(int, str)
    update_send_progress = pyqtSignal(float)
    finished = pyqtSignal(bool, str)

    def __init__(self, initials, port):
        super().__init__()
        self.initials = initials
        self.port = port

    def run(self):
        try:
            # Step 1: Generate STL
            self.update_progress.emit(0, "Generating STL...")
            blend_file = "trophy-python.blend"
            stl_path = tempfile.mktemp(suffix='.stl')
            success, message = edit_blender_texts_and_export_scene(
                'blender', blend_file, {"initials": self.initials}, stl_path
            )
            if not success:
                self.finished.emit(False, f"Failed to generate STL: {message}")
                return

            # Step 2: Slice STL
            self.update_progress.emit(33, "Slicing STL...")
            config_path = "config.ini"
            gcode_path = slice_stl(stl_path, config_path)

            # Step 3: Send G-code to printer
            self.update_progress.emit(66, "Sending to printer...")
            printer = MarlinPrinter(self.port)
            if printer.send_gcode_to_sd(gcode_path, progress_callback=self.update_send_progress.emit):
                self.finished.emit(True, "Trophy successfully sent to printer!")
            else:
                self.finished.emit(False, "Failed to send G-code to printer")

        except Exception as e:
            self.finished.emit(False, f"An error occurred: {str(e)}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Trophy Printer")
        self.setGeometry(100, 100, 400, 250)

        layout = QVBoxLayout()

        # Printer selection
        self.printer_combo = QComboBox()
        self.scan_printers()
        layout.addWidget(QLabel("Select Printer:"))
        layout.addWidget(self.printer_combo)

        # Initials input
        initials_layout = QHBoxLayout()
        initials_layout.addWidget(QLabel("Initials:"))
        self.initials_input = QLineEdit()
        self.initials_input.setMaxLength(3)
        initials_layout.addWidget(self.initials_input)
        layout.addLayout(initials_layout)

        # Go button
        self.go_button = QPushButton("Go")
        self.go_button.clicked.connect(self.start_process)
        layout.addWidget(self.go_button)

        # Overall progress bar
        self.overall_progress_bar = QProgressBar()
        layout.addWidget(QLabel("Overall Progress:"))
        layout.addWidget(self.overall_progress_bar)

        # File sending progress bar
        self.send_progress_bar = QProgressBar()
        layout.addWidget(QLabel("File Sending Progress:"))
        layout.addWidget(self.send_progress_bar)

        # Status label
        self.status_label = QLabel()
        layout.addWidget(self.status_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def scan_printers(self):
        # This is a placeholder. You'll need to implement actual printer scanning logic.
        self.printer_combo.addItems(["COM1", "COM2", "COM3", "/dev/ttyACM0"])

    def start_process(self):
        initials = self.initials_input.text().upper()
        if not initials:
            self.status_label.setText("Please enter initials")
            return

        port = self.printer_combo.currentText()
        self.worker = WorkerThread(initials, port)
        self.worker.update_progress.connect(self.update_progress)
        self.worker.update_send_progress.connect(self.update_send_progress)
        self.worker.finished.connect(self.process_finished)
        self.worker.start()

        self.go_button.setEnabled(False)
        self.overall_progress_bar.setValue(0)
        self.send_progress_bar.setValue(0)

    def update_progress(self, value, message):
        self.overall_progress_bar.setValue(value)
        self.status_label.setText(message)

    def update_send_progress(self, value):
        self.send_progress_bar.setValue(int(value))

    def process_finished(self, success, message):
        self.status_label.setText(message)
        self.overall_progress_bar.setValue(100 if success else 0)
        self.send_progress_bar.setValue(100 if success else 0)
        self.go_button.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())