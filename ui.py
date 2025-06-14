# ui.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox, QFileDialog, QListWidget, QListWidgetItem
import os
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPixmap, QIcon

class UI(QWidget):
    organize_clicked = pyqtSignal(str)
    upload_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.llm_choice = QComboBox()
        self.llm_choice.addItem("OpenAI")
        self.llm_choice.addItem("Local")
        self.llm_choice.addItem("Google Gemini")
        self.llm_choice.addItem("LM Studio")
        self.llm_choice.addItem("Ollama")
        layout.addWidget(self.llm_choice)

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter API Key")
        layout.addWidget(self.api_key_input)

        self.local_llm_model_path_input = QLineEdit()
        self.local_llm_model_path_input.setPlaceholderText("Enter Local LLM Model Path")
        layout.addWidget(self.local_llm_model_path_input)
        self.local_llm_model_path = ""
        self.local_llm_model_path_input.textChanged.connect(self.on_local_llm_model_path_changed)

        self.directory_button = QPushButton("Select Directory")
        self.directory_button.clicked.connect(self.on_directory_clicked)
        layout.addWidget(self.directory_button)
        self.selected_directory = ""

        self.image_list = QListWidget()
        layout.addWidget(self.image_list)

        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter Prompt")
        layout.addWidget(self.command_input)

        self.upload_button = QPushButton("Upload Images")
        self.upload_button.clicked.connect(self.on_upload_clicked)
        layout.addWidget(self.upload_button)

        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        layout.addWidget(self.progress_text)

        self.organize_button = QPushButton("Organize")
        self.organize_button.clicked.connect(self.on_organize_clicked)
        layout.addWidget(self.organize_button)
        self.setLayout(layout)

    def print_to_terminal(self, text):
        print(text)
        self.progress_text.append(text)

    def on_local_llm_model_path_changed(self, text):
        self.local_llm_model_path = text

    def on_upload_clicked(self):
        self.uploaded_images = []
        for index in range(self.image_list.count()):
            item = self.image_list.item(index)
            filename = item.text()
            filepath = os.path.join(self.selected_directory, filename)
            try:
                with open(filepath, "rb") as f:
                    image_data = f.read()
                    self.uploaded_images.append({"filename": filename, "data": image_data})
                self.print_to_terminal(f"Uploaded {filename}")
            except Exception as e:
                self.print_to_terminal(f"Error uploading {filename}: {e}")
        self.upload_clicked.emit()

    def on_organize_clicked(self):
        command = self.command_input.text()
        self.print_to_terminal(f"Organizing images with command: {command}")
        self.organize_clicked.emit(command)

    def on_directory_clicked(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.selected_directory = directory
            self.print_to_terminal(f"Selected directory: {directory}")
            self.load_images()

    def load_images(self):
        self.image_list.clear()
        if self.selected_directory:
            for filename in os.listdir(self.selected_directory):
                if filename.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
                    item = QListWidgetItem()
                    item.setText(filename)
                    # Load image thumbnail
                    pixmap = QPixmap(os.path.join(self.selected_directory, filename))
                    pixmap = pixmap.scaledToWidth(100)
                    icon = QIcon(pixmap)
                    item.setIcon(icon)
                    self.image_list.addItem(item)
