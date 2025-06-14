import openai
import os
import json
import logging
import re
from file_manager import move_file

def generate_llm_prompt(command, image_data_string):
    return f"You are an expert image organizer with access to vision capabilities. Analyze the following command: '{command}'. Analyze the following images:\\n{image_data_string}\\nProvide instructions on how to organize the images into folders based on their content. The response should include a JSON object with the following format:\\n\\n{{\\n  \"folders\": [\\n    {{\\n      \"name\": \"folder_name\",\\n      \"images\": [\"image1.jpg\", \"image2.jpg\"]\\n    }}\\n  ]\\n}}\\n\\nEach object in the 'folders' array should have a 'name' key representing the folder name and an 'images' key representing an array of the actual image filenames (including their extensions) to be moved to that folder. The code should create the folders if they don't exist. Do not use hardcoded paths. Use the 'move_file' function defined in the 'file_manager' module to move the files. Use os.path.join to construct file paths. Ensure the generated JSON is valid and does not contain syntax errors. The 'file_manager' module contains the function 'move_file(source, destination)' which moves a file from the source path to the destination path. The current working directory is '{os.getcwd()}'. Return ONLY a JSON object."

def organize_images_openai(api_key, uploaded_images, selected_directory, command, ui):
    openai.api_key = api_key

    image_data_string = ""
    for i, image in enumerate(uploaded_images):
        image_data_string += f"Image {i+1}: Filename: {image['filename']}, Data: {image['data'][:100]}...\n"

    prompt = generate_llm_prompt(command, image_data_string)
    ui.progress_text.append(f"Prompt sent to OpenAI: {prompt}")

    response = openai.chat.completions.create(
        model="text-davinci-003",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=6000
    )
    analysis = response.choices[0].message.content.strip()
    logging.info(f"OpenAI LLM Analysis: {analysis}")
    ui.progress_text.append(f"OpenAI LLM Analysis: {analysis}")

    # Parse the JSON object and execute the instructions
    try:
        logging.info("Attempting to parse JSON from OpenAI response")
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
                ui.progress_text.append(f"Moved {image_name} to {folder_name}")

        ui.progress_text.append("Image organization complete.")

    except Exception as e:
        error_message = str(e)
        ui.progress_text.append(f"Error executing LLM instructions: {error_message}")