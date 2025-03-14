import google.generativeai as genai
import os
import json
import logging
import re
from file_manager import move_file

def generate_llm_prompt(command, image_data_string):
    return f"You are an expert image organizer with access to vision capabilities. Analyze the following command: '{command}'. Analyze the following images:\\n{image_data_string}\\nProvide instructions on how to organize the images into folders based on their content. The response should include a JSON object with the following format:\\n\\n{{\\n  \"folders\": [\\n    {{\\n      \"name\": \"folder_name\",\\n      \"images\": [\"image1.jpg\", \"image2.jpg\"]\\n    }}\\n  ]\\n}}\\n\\nEach object in the 'folders' array should have a 'name' key representing the folder name and an 'images' key representing an array of the actual image filenames (including their extensions) to be moved to that folder. The code should create the folders if they don't exist. Do not use hardcoded paths. Use the 'move_file' function defined in the 'file_manager' module to move the files. Use os.path.join to construct file paths. Ensure the generated JSON is valid and does not contain syntax errors. The 'file_manager' module contains the function 'move_file(source, destination)' which moves a file from the source path to the destination path. The current working directory is '{os.getcwd()}'. Return ONLY a JSON object."

def organize_images_gemini(gemini_api_key, uploaded_images, selected_directory, command, ui):
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
    ui.progress_text.append(f"Prompt sent to Gemini with image data.")

    response = client.generate_content(contents)
    analysis = response.text
    logging.info(f"Gemini LLM Analysis: {analysis}")
    ui.progress_text.append(f"Gemini LLM Analysis: {analysis}")
    print(f"Gemini LLM Analysis: {analysis}")

    # Parse the JSON object and execute the instructions
    try:
        logging.info("Attempting to parse JSON from Gemini response")
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
        ui.progress_text.append(f"Error executing LLM instructions: {e}")
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
                ui.progress_text.append(f"Moved {image_name} to {folder_name}")
            except Exception as e:
                ui.progress_text.append(f"Error moving file: {e}")

    ui.progress_text.append("Image organization complete.")