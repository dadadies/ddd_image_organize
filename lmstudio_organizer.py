import lmstudio as lms
import os
import json
import logging
import re
from file_manager import move_file
from PIL import Image
import io
from typing import List

# Define the schema using lms.BaseModel
class Folder(lms.BaseModel):
    name: str
    images: List[str]

class ImageOrganizationSchema(lms.BaseModel):
    folders: List[Folder]

# Load the 0.json schema
try:
    with open('0.json', 'r') as f:
        JSON_SCHEMA = json.load(f)
except FileNotFoundError:
    logging.error("0.json not found. Please ensure it's in the same directory.")
    JSON_SCHEMA = {}
except json.JSONDecodeError as e:
    logging.error(f"Error decoding 0.json: {e}")
    JSON_SCHEMA = {}

def generate_llm_prompt(command, filename):
    return f"""You are an expert image organizer with access to vision capabilities. 
 Analyze the following command: '{command}'. 
 Provide instructions on how to organize the image '{filename}' into folders based on its content. 
 The response should be a JSON object with the following format:

{{
  "folders": [
    {{
      "name": "folder_name",
      "images": ["{filename}"]
    }}
  ]
}}

Each object in the 'folders' array should have a 'name' key representing the folder name and an 'images' key representing an array containing ONLY the filename '{filename}' (including its extension) to be moved to that folder. 
Include only the filename of the image being processed in the 'images' array.
Return ONLY a JSON object.
"""

def parse_json_response(content: str):
    """
    Attempt to extract and parse JSON from an LLM response.
    Returns the parsed JSON dictionary or raises an Exception.
    """
    logging.info("Attempting to parse JSON from LLM response.")
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in LLM response")

    json_string = match.group(0)

    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        logging.warning(f"Initial JSON parsing failed: {e}")
        # Try some basic cleanup and reattempt
        try:
            cleaned = json_string.replace('\\"', '"').replace("\\n", "").replace("'", '"')
            return json.loads(cleaned)
        except json.JSONDecodeError as e2:
            logging.error(f"Failed to parse JSON after cleanup: {e2}")
            logging.debug(f"Problematic JSON: {json_string}")
            raise

def organize_images_lmstudio(uploaded_images, selected_directory, command, ui):
    try:
        try:
            loaded_models = lms.list_loaded_models()
            if loaded_models:
                model_name = loaded_models[0].identifier
                model = lms.llm(model_name)
            else:
                ui.progress_text.append("Error: No models are loaded in LM Studio. Please load a model and try again.")
                return
        except Exception as e:
            ui.progress_text.append(f"Error getting active model from LM Studio: {e}. Please ensure LM Studio is running and a model is loaded.")
            return

        for image in uploaded_images:
            image_path = os.path.join(selected_directory, image['filename'])
            logging.debug(f"Processing image: {image_path}")
            try:
                image_handle = lms.prepare_image(image_path)
                logging.debug(f"Prepared image handle: {image_handle}")
            except Exception as e:
                ui.progress_text.append(f"Error preparing image {image['filename']}: {e}")
                logging.error(f"Error preparing image {image['filename']}: {e}")
                continue

            full_prompt = generate_llm_prompt(command, image['filename'])
            logging.debug(f"Full prompt sent to LLM: {full_prompt}")

            chat = lms.Chat()
            chat.add_user_message(full_prompt, images=[image_handle])

            try:
                analysis = model.respond(chat)
                ui.progress_text.append(f"Raw LLM response: {analysis.content}")
                logging.debug(f"Raw LLM response: {analysis.content}")
            except Exception as e:
                ui.progress_text.append(f"Error generating response for {image['filename']}: {e}")
                logging.error(f"Error generating response for {image['filename']}: {e}", exc_info=True)
                continue

            # Default instructions in case parsing fails
            instructions = {}

            try:
                instructions = parse_json_response(analysis.content)
                logging.info(f"LLM JSON parsed successfully: {instructions}")
            except Exception as e:
                ui.progress_text.append(f"Error parsing LLM response for {image['filename']}: {e}")
                logging.error(f"Error parsing LLM response: {e}", exc_info=True)
                continue

            if 'folders' not in instructions:
                ui.progress_text.append(f"Warning: LLM response for {image['filename']} did not contain 'folders' key.")
                logging.warning(f"LLM response for {image['filename']} did not contain 'folders' key. Raw response: {analysis.content}")
                continue

            folders_to_create = instructions['folders']
            if not folders_to_create:
                ui.progress_text.append(f"Warning: No folders suggested for {image['filename']}.")
                logging.warning(f"No folders suggested for {image['filename']}. Raw response: {analysis.content}")
                continue

            try:
                for folder_info in folders_to_create:
                    folder_name = folder_info['name']
                    folder_path = os.path.join(selected_directory, folder_name)

                    if not os.path.exists(folder_path):
                        os.makedirs(folder_path)
                        logging.debug(f"Created folder: {folder_path}")

                    for image_name in folder_info['images']:
                        if image_name.startswith("images/"):
                            image_name = image_name[7:]
                        source_path = os.path.join(selected_directory, image_name)
                        destination_path = os.path.join(folder_path, image_name)

                        try:
                            move_file(source_path, destination_path)
                            ui.progress_text.append(f"Moved {image_name} to {folder_name}")
                            logging.debug(f"Moved {image_name} to {folder_path}")
                        except Exception as e:
                            ui.progress_text.append(f"Error moving file {image_name}: {e}")
                            logging.error(f"Error moving file {image_name}: {e}", exc_info=True)
            except Exception as e:
                ui.progress_text.append(f"Error processing folders for {image['filename']}: {e}")
                logging.error(f"Error processing folders for {image['filename']}: {e}", exc_info=True)
                continue

        ui.progress_text.append("Image organization complete.")

    except Exception as e:
        ui.progress_text.append(f"Fatal error during image organization: {e}")
        logging.error(f"Fatal error in organize_images_lmstudio: {e}", exc_info=True)
