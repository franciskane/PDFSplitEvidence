import sys
import os
import re
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QFileDialog, QLabel, QVBoxLayout, QWidget, QProgressBar, QMessageBox, QSizePolicy, QSpacerItem, QHBoxLayout)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QDropEvent, QDragEnterEvent
from pdf_drawer import compile_pdf  # Import the updated compile_pdf function

def get_version():
    """Read the version number from the version file."""
    version_file = 'version.txt'
    if os.path.exists(version_file):
        with open(version_file, 'r') as file:
            return file.read().strip()
    return "Unknown"

def increment_version():
    """Increment the version number in the version file."""
    version_file = 'version.txt'
    if os.path.exists(version_file):
        with open(version_file, 'r') as file:
            version = file.read().strip()
        version_parts = version.split('.')
        if len(version_parts) == 3:
            major, minor, patch = version_parts
            patch = str(int(patch) + 1)
            new_version = f"{major}.{minor}.{patch}"
        else:
            new_version = "1.0.1"  # Default to 1.0.1 if format is unexpected

        with open(version_file, 'w') as file:
            file.write(new_version)
    else:
        with open(version_file, 'w') as file:
            file.write("1.0.0")

class WorkerThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, pdf_paths):
        super().__init__()
        self.pdf_paths = pdf_paths

    def run(self):
        try:
            # Create the output directory if it doesn't exist
            output_dir = 'split'
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            for pdf_path in self.pdf_paths:
                self.process_pdf(pdf_path)
                self.progress.emit(f"Processed {os.path.basename(pdf_path)}")
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

    def process_pdf(self, pdf_path):
        def sanitize_filename(filename):
            return re.sub(r'[\/:*?"<>|]', '_', filename)  # Replace invalid characters with '_'

        base_filename = os.path.splitext(os.path.basename(pdf_path))[0]
        sanitized_filename = sanitize_filename(base_filename)
        output_pdf_path = os.path.join('split', f"{sanitized_filename}.pdf")
        compile_pdf(pdf_path, output_pdf_path)

class PDFAnalyzerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        increment_version()  # Increment version when the application starts
        self.setWindowTitle("Split Evidence")
        self.setGeometry(100, 100, 400, 300)

        # Initialize GUI elements
        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Create a horizontal layout for buttons
        button_layout = QHBoxLayout()

        self.upload_button = QPushButton("Upload PDFs")
        self.upload_button.clicked.connect(self.upload_pdfs)
        self.upload_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button_layout.addWidget(self.upload_button)

        self.start_button = QPushButton("Start Analysis")
        self.start_button.clicked.connect(self.start_analysis)
        self.start_button.setEnabled(False)
        self.start_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button_layout.addWidget(self.start_button)

        self.layout.addLayout(button_layout)

        # Add a spacer item to push the progress bar and status label to the top
        self.layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.progress = QProgressBar()
        self.progress.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.layout.addWidget(self.progress)

        self.status_label = QLabel(f"Status: Waiting for PDFs... (Version: {get_version()})")
        self.status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.layout.addWidget(self.status_label)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close_app)
        self.close_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.layout.addWidget(self.close_button)

        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        file_paths = [url.toLocalFile() for url in event.mimeData().urls()]
        self.handle_file_paths(file_paths)

    def upload_pdfs(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Select PDF Files", "", "PDF files (*.pdf)")
        self.handle_file_paths(file_paths)

    def handle_file_paths(self, file_paths):
        if len(file_paths) > 250:
            QMessageBox.warning(self, "Warning", "Only the first 250 files will be processed.")
            file_paths = file_paths[:250]

        if file_paths:
            self.pdf_paths = file_paths
            self.status_label.setText(f"Status: {len(self.pdf_paths)} PDFs Loaded (Version: {get_version()})")
            self.start_button.setEnabled(True)

    def start_analysis(self):
        if not hasattr(self, 'pdf_paths'):
            QMessageBox.critical(self, "Error", "No PDFs uploaded!")
            return

        self.status_label.setText("Status: Analyzing...")
        self.progress.setRange(0, 0)  # Indeterminate mode
        self.thread = WorkerThread(self.pdf_paths)
        self.thread.progress.connect(self.update_status)
        self.thread.finished.connect(self.analysis_complete)
        self.thread.error.connect(self.show_error)
        self.thread.start()

    def update_status(self, message):
        self.status_label.setText(f"Status: {message} (Version: {get_version()})")

    def analysis_complete(self):
        self.status_label.setText("Status: Analysis Complete")
        QMessageBox.information(self, "Success", "PDF analysis complete!")
        self.progress.setRange(0, 1)
        self.start_button.setEnabled(False)

    def show_error(self, message):
        self.status_label.setText(f"Status: Error processing files")
        QMessageBox.critical(self, "Error", f"An error occurred: {message}")

    def close_app(self):
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PDFAnalyzerApp()
    window.show()
    sys.exit(app.exec_())
