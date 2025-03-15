# main.py
import requests
import sys
import os
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow

logging.basicConfig(filename='image_organizer.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
from ui import UI
from folder_manager import create_folder, delete_folder, rename_folder
from file_manager import move_file, copy_file, delete_file
import openai
import os
import json
import io
import base64
from PIL import Image
import google.generativeai as genai
from openai_organizer import organize_images_openai
from gemini_organizer import organize_images_gemini
from lmstudio_organizer import organize_images_lmstudio
from ollama_organizer import organize_images_ollama

def generate_llm_prompt(command, image_data_string):
    return f"You are an expert image organizer with access to vision capabilities. Analyze the following command: '{command}'. Analyze the following images:\\n{image_data_string}\\nProvide instructions on how to organize the images into folders based on their content. The response should include a JSON object with the following format:\\n\\n{{\\n  \"folders\": [\\n    {{\\n      \"name\": \"folder_name\",\\n      \"images\": [\"image1.jpg\", \"image2.jpg\"]\\n    }}\\n  ]\\n}}\\n\\nEach object in the 'folders' array should have a 'name' key representing the folder name and an 'images' key representing an array of the actual image filenames (including their extensions) to be moved to that folder. The code should create the folders if they don't exist. Do not use hardcoded paths. Use the 'move_file' function defined in the 'file_manager' module to move the files. Use os.path.join to construct file paths. Ensure the generated JSON is valid and does not contain syntax errors. The 'file_manager' module contains the function 'move_file(source, destination)' which moves a file from the source path to the destination path. The current working directory is '{os.getcwd()}'. Return ONLY a JSON object."

def get_image_files(directory):
    image_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
                image_files.append(os.path.join(root, file))
    return image_files

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Organizer")
        self.ui = UI()
        self.setCentralWidget(self.ui)
        self.ui.organize_clicked.connect(self.organize_images)
        self.ui.upload_button.clicked.connect(self.upload_images)
        self.uploaded_images = []

    def upload_images(self):
        self.ui.progress_text.append("Uploading images...")
        self.uploaded_images = self.ui.uploaded_images
        self.ui.progress_text.append(f"Uploaded {len(self.uploaded_images)} images.")

    def organize_images(self, command):
        self.ui.progress_text.append(f"Organizing images with command: {command}")
        uploaded_images = self.uploaded_images
        selected_directory = self.ui.selected_directory
        if not selected_directory:
            self.ui.progress_text.append("Error: No directory selected.")
            return

        uploaded_images = self.uploaded_images
        if not uploaded_images:
            self.ui.progress_text.append("Error: No images uploaded.")
            return

        try:
            llm_choice = self.ui.llm_choice.currentText()
            api_key = self.ui.api_key_input.text()

            if llm_choice == "OpenAI":
                organize_images_openai(api_key, uploaded_images, selected_directory, command, self.ui)

            elif llm_choice == "Google Gemini":
                gemini_api_key = self.ui.api_key_input.text()
                organize_images_gemini(gemini_api_key, uploaded_images, selected_directory, command, self.ui)

            elif llm_choice == "LM Studio":
                organize_images_lmstudio(uploaded_images, selected_directory, command, self.ui)
            
            elif llm_choice == "Ollama":
                organize_images_ollama(uploaded_images, selected_directory, self.ui)

        except Exception as e:
            self.ui.progress_text.append(f"Error: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())