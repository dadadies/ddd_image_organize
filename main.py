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
import google.generativeai as genai
import os
import json
import io

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
                openai.api_key = api_key

                image_data_string = ""
                for i, image in enumerate(uploaded_images):
                    image_data_string += f"Image {i+1}: Filename: {image['filename']}, Data: {image['data'][:100]}...\n"

                prompt = generate_llm_prompt(command, image_data_string)
                self.ui.progress_text.append(f"Prompt sent to OpenAI: {prompt}")

                response = openai.chat.completions.create(
                    model="text-davinci-003",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=350
                )
                analysis = response.choices[0].message.content.strip()
                logging.info(f"OpenAI LLM Analysis: {analysis}")
                self.ui.progress_text.append(f"OpenAI LLM Analysis: {analysis}")

                # Parse the JSON object and execute the instructions
                try:
                    logging.info("Attempting to parse JSON from OpenAI response")
                    import json
                    import re
                    # Find the JSON object within the response
                    match = re.search(r"\{.*\}", analysis, re.DOTALL)
                    if match:
                        json_string = match.group(0)
                        try:
                            instructions = json.loads(json_string)
                        except json.JSONDecodeError as e:
                            logging.error(f"JSONDecodeError: {e}")
                            logging.error(f"Failed to parse JSON: {json_string}")
                            raise
                    else:
                        raise ValueError("No JSON object found in LLM response")

                    for folder in instructions['folders']:
                        folder_name = folder['name']
                        folder_path = os.path.join(selected_directory, folder_name)
                        if not os.path.exists(folder_path):
                            os.makedirs(folder_path)

                        for image_name in folder['images']:
                            if image_name.startswith("images/"):
                                image_name = image_name[7:]
                            source_path = os.path.join(selected_directory, image_name)
                            destination_path = os.path.join(folder_path, image_name)
                            move_file(source_path, destination_path)
                            self.ui.progress_text.append(f"Moved {image_name} to {folder_name}")

                    self.ui.progress_text.append("Image organization complete.")

                except Exception as e:
                    error_message = str(e)
                    self.ui.progress_text.append(f"Error executing LLM instructions: {error_message}")

            elif llm_choice == "Google Gemini":
                gemini_api_key = self.ui.api_key_input.text()
                if gemini_api_key == "":
                    gemini_api_key = ""
                genai.configure(api_key=gemini_api_key)

                client = genai.GenerativeModel('gemini-2.0-flash')

                contents = []
                image_names = [image['filename'] for image in uploaded_images]
                image_data_string = ""
                for i, image in enumerate(uploaded_images):
                    image_data_string += f"Image {i+1}: Filename: {image['filename']}, Data: {image['data'][:100]}...\n"
                prompt = generate_llm_prompt(command, image_data_string)
                contents.append(prompt)

                for i, image in enumerate(uploaded_images):
                    image_data = image['data']
                    filename = image['filename']
                    mime_type = "image/jpeg"  # Default MIME type
                    if filename.lower().endswith(".png"):
                        mime_type = "image/png"
                    elif filename.lower().endswith(".webp"):
                        mime_type = "image/webp"
                    contents.append({
                        "mime_type": mime_type,
                        "data": image_data
                    })
                self.ui.progress_text.append(f"Prompt sent to Gemini with image data.")

                response = client.generate_content(contents)
                analysis = response.text
                logging.info(f"Gemini LLM Analysis: {analysis}")
                self.ui.progress_text.append(f"Gemini LLM Analysis: {analysis}")
                print(f"Gemini LLM Analysis: {analysis}")

                # Parse the JSON object and execute the instructions
                try:
                    logging.info("Attempting to parse JSON from Gemini response")
                    import json
                    import re
                    # Find the JSON object within the response
                    match = re.search(r"\{.*\}", analysis, re.DOTALL)
                    if match:
                        json_string = match.group(0)
                        # Fix JSON format
                        json_string = json_string.replace('""', '","').replace('\\n', '').replace('" "', '","')
                        try:
                            instructions = json.loads(json_string)
                            logging.info(f"Gemini JSON parsed successfully: {instructions}")
                        except json.JSONDecodeError as e:
                            logging.warning(f"JSONDecodeError: {e}")
                            logging.warning(f"Failed to parse JSON with standard json.loads, attempting alternative parsing...")
                            try:
                                # Attempt to fix common JSON errors and parse again
                                json_string = json_string.replace('""', '","').replace('\\n', '').replace('" "', '","')
                                instructions = json.loads(json_string)
                                logging.info("Successfully parsed JSON with alternative parsing.")
                            except json.JSONDecodeError as e2:
                                logging.error(f"JSONDecodeError: {e2}")
                                logging.error(f"Failed to parse JSON: {json_string}")
                            raise
                    else:
                        raise ValueError("No JSON object found in LLM response")

                except Exception as e:
                    self.ui.progress_text.append(f"Error executing LLM instructions: {e}")
                    return

                for folder in instructions['folders']:
                    folder_name = folder['name']
                    folder_path = os.path.join(selected_directory, folder_name)
                    if not os.path.exists(folder_path):
                        os.makedirs(folder_path)
                    for image_name in folder['images']:
                        if image_name.startswith("images/"):
                            image_name = image_name[7:]
                        source_path = os.path.join(selected_directory, image_name)
                        destination_path = os.path.join(folder_path, image_name)
                        try:
                            move_file(source_path, destination_path)
                            self.ui.progress_text.append(f"Moved {image_name} to {folder_name}")
                        except Exception as e:
                            self.ui.progress_text.append(f"Error moving file: {e}")

                self.ui.progress_text.append("Image organization complete.")

            elif llm_choice == "LM Studio":
                import requests
                try:
                    # Prepare the prompt
                    image_data_string = ""
                    for i, image in enumerate(uploaded_images):
                        image_data_string += f"Image {i+1}: Filename: {image['filename']}, Data: {image['data'][:100]}...\n"

                    prompt = generate_llm_prompt(command, image_data_string)
                    self.ui.progress_text.append(f"Prompt sent to LM Studio: {prompt}")

                    # Make the API call to LM Studio
                    url = "http://127.0.0.1:1234/v1/chat/completions"
                    headers = {"Content-Type": "application/json"}
                    data = {
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 350
                    }
                    try:
                        response = requests.post(url, headers=headers, json=data)
                        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                    except requests.exceptions.RequestException as e:
                        self.ui.progress_text.append(f"Error connecting to LM Studio: {e}")
                        return

                    try:
                        analysis = response.json()["choices"][0]["message"]["content"].strip()
                    except (KeyError, json.JSONDecodeError) as e:
                        self.ui.progress_text.append(f"Error parsing LM Studio response: {e}")
                        return

                    logging.info(f"LM Studio LLM Analysis: {analysis}")
                    self.ui.progress_text.append(f"LM Studio LLM Analysis: {analysis}")

                    # Parse the JSON object and execute the instructions
                    try:
                        logging.info("Attempting to parse JSON from LM Studio response")
                        import json
                        import re
                        # Find the JSON object within the response
                        match = re.search(r"\{.*\}", analysis, re.DOTALL)
                        if match:
                            json_string = match.group(0)
                            try:
                                instructions = json.loads(json_string)
                                logging.info(f"LM Studio JSON parsed successfully: {instructions}")
                            except json.JSONDecodeError as e:
                                logging.error(f"JSONDecodeError: {e}")
                                logging.error(f"Failed to parse JSON: {json_string}")
                                self.ui.progress_text.append(f"Error parsing JSON: {e}")
                                return
                        else:
                            self.ui.progress_text.append("No JSON object found in LLM response")
                            return

                        for folder in instructions['folders']:
                            folder_name = folder['name']
                            folder_path = os.path.join(selected_directory, folder_name)
                            if not os.path.exists(folder_path):
                                os.makedirs(folder_path)

                            for image_name in folder['images']:
                                # Remove "images/" prefix from image_name if it exists
                                if image_name.startswith("images/"):
                                    image_name = image_name[7:]
                                source_path = os.path.join(selected_directory, image_name)
                                destination_path = os.path.join(folder_path, image_name)
                                move_file(source_path, destination_path)
                                self.ui.progress_text.append(f"Moved {image_name} to {folder_name}")

                        self.ui.progress_text.append("Image organization complete.")

                    except Exception as e:
                        self.ui.progress_text.append(f"Error executing LLM instructions: {e}")
                        return
                        import re
                        # Find the JSON object within the response
                        match = re.search(r"\{.*\}", analysis, re.DOTALL)
                        if match:
                            json_string = match.group(0)
                            try:
                                instructions = json.loads(json_string)
                                logging.info(f"Local LLM JSON parsed successfully: {instructions}")
                            except json.JSONDecodeError as e:
                                logging.error(f"JSONDecodeError: {e}")
                                logging.error(f"Failed to parse JSON: {json_string}")
                                raise
                        else:
                            raise ValueError("No JSON object found in LLM response")

                        for folder in instructions['folders']:
                            folder_name = folder['name']
                            folder_path = os.path.join(selected_directory, folder_name)
                            if not os.path.exists(folder_path):
                                os.makedirs(folder_path)

                            for image_name in folder['images']:
                                # Remove "images/" prefix from image_name if it exists
                                if image_name.startswith("images/"):
                                    image_name = image_name[7:]
                                source_path = os.path.join(selected_directory, image_name)
                                destination_path = os.path.join(folder_path, image_name)
                                move_file(source_path, destination_path)
                                self.ui.progress_text.append(f"Moved {image_name} to {folder_name}")

                        self.ui.progress_text.append("Image organization complete.")

                    except Exception as e:
                        self.ui.progress_text.append(f"Error executing LLM instructions: {e}")
                        return
                        import json
                        import re
                        # Find the JSON object within the response
                        match = re.search(r"\{.*\}", analysis, re.DOTALL)
                        if match:
                            json_string = match.group(0)
                            try:
                                instructions = json.loads(json_string)
                            except json.JSONDecodeError as e:
                                logging.warning(f"JSONDecodeError: {e}")
                                logging.warning(f"Failed to parse JSON with standard json.loads, attempting alternative parsing...")
                                try:
                                    # Attempt to fix common JSON errors and parse again
                                    json_string = json_string.replace('""', '","').replace('\\n', '').replace('" "', '","')
                                    instructions = json.loads(json_string)
                                    logging.info("Successfully parsed JSON with alternative parsing.")
                                except json.JSONDecodeError as e2:
                                    logging.error(f"JSONDecodeError: {e2}")
                                    logging.error(f"Failed to parse JSON: {json_string}")
                                    raise
                        else:
                            raise ValueError("No JSON object found in LLM response")

                    except Exception as e:
                        self.ui.progress_text.append(f"Error executing LLM instructions: {e}")
                        return
                        import json
                        import re
                        # Find the JSON object within the response
                        match = re.search(r"\{.*\}", analysis, re.DOTALL)
                        if match:
                            json_string = match.group(0)
                            try:
                                instructions = json.loads(json_string)
                            except json.JSONDecodeError as e:
                                logging.error(f"JSONDecodeError: {e}")
                                logging.error(f"Failed to parse JSON: {json_string}")
                                raise
                        else:
                            raise ValueError("No JSON object found in LLM response")

                    except Exception as e:
                        self.ui.progress_text.append(f"Error executing LLM instructions: {e}")
                        return

                    for folder in instructions['folders']:
                        folder_name = folder['name']
                        folder_path = os.path.join(selected_directory, folder_name)
                        if not os.path.exists(folder_path):
                            os.makedirs(folder_path)

                        for image_name in folder['images']:
                            # Remove "images/" prefix from image_name if it exists
                            if image_name.startswith("images/"):
                                image_name = image_name[7:]
                            source_path = os.path.join(selected_directory, image_name)
                            destination_path = os.path.join(folder_path, image_name)
                            move_file(source_path, destination_path)
                            self.ui.progress_text.append(f"Moved {image_name} to {folder_name}")

                    self.ui.progress_text.append("Image organization complete.")

                except Exception as e:
                    self.ui.progress_text.append(f"Error: {e}")
                return
            elif llm_choice == "Local":
                try:
                    from llama_cpp import Llama

                    # Load the local LLM model
                    model_path = self.ui.local_llm_model_path
                    if not os.path.exists(model_path):
                        self.ui.progress_text.append(f"Error: Local LLM model not found at {model_path}")
                        return

                    llm = Llama(model_path=model_path, n_threads=4)

                    image_data_string = ""
                    for i, image in enumerate(uploaded_images):
                        image_data_string += f"Image {i+1}: Filename: {image['filename']}, Data: {image['data'][:100]}...\n"
    
                    prompt = generate_llm_prompt(command, image_data_string)
                    self.ui.progress_text.append(f"Prompt sent to Local LLM: {prompt}")

                    response = llm(prompt, max_tokens=350, stop=["\\n"], echo=False)
                    analysis = response["choices"][0]["text"].strip()
                    logging.info(f"Local LLM Analysis: {analysis}")
                    self.ui.progress_text.append(f"Local LLM Analysis: {analysis}")

                    # Parse the JSON object and execute the instructions
                    try:
                        logging.info("Attempting to parse JSON from Local LLM response")
                        import json
                        import re
                        # Find the JSON object within the response
                        match = re.search(r"\{.*\}", analysis, re.DOTALL)
                        if match:
                            json_string = match.group(0)
                            try:
                                instructions = json.loads(json_string)
                            except json.JSONDecodeError as e:
                                logging.error(f"JSONDecodeError: {e}")
                                logging.error(f"Failed to parse JSON: {json_string}")
                                raise
                        else:
                            raise ValueError("No JSON object found in LLM response")

                    except Exception as e:
                        self.ui.progress_text.append(f"Error executing LLM instructions: {e}")
                        return

                    for folder in instructions['folders']:
                        folder_name = folder['name']
                        folder_path = os.path.join(selected_directory, folder_name)
                        if not os.path.exists(folder_path):
                            os.makedirs(folder_path)

                        for image_name in folder['images']:
                            # Remove "images/" prefix from image_name if it exists
                            if image_name.startswith("images/"):
                                image_name = image_name[7:]
                            source_path = os.path.join(selected_directory, image_name)
                            destination_path = os.path.join(folder_path, image_name)
                            move_file(source_path, destination_path)
                            self.ui.progress_text.append(f"Moved {image_name} to {folder_name}")

                    self.ui.progress_text.append("Image organization complete.")

                except Exception as e:
                    self.ui.progress_text.append(f"Error: {e}")
                return

        except Exception as e:
            self.ui.progress_text.append(f"Error: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
