import openai
import os
import json
import logging
import io
import base64
from PIL import Image
from file_manager import move_file

def organize_images_ollama(uploaded_images, selected_directory, ui):
    try:
        # Point to the local server
        client = openai.OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

        # Iterate through each uploaded image
        for image in uploaded_images:
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that can analyze images and provide instructions on how to organize them into folders.",
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Analyze the image and return a single word directory that you would place it in to organize it. Do NOT output any special characters like '*'s."},
                    ],
                }
            ]

            image_data = image['data']
            filename = image['filename']
            
            # Convert image to JPEG
            try:
                img = Image.open(io.BytesIO(image_data))
                img_io = io.BytesIO()
                img.convert('RGB').save(img_io, 'JPEG', quality=90)
                image_data = img_io.getvalue()
                mime_type = "image/jpeg"
            except Exception as e:
                ui.progress_text.append(f"Error converting image to JPEG: {e}")
                continue

            base64_image = base64.b64encode(image_data).decode("utf-8")
            messages[1]["content"].append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{base64_image}"
                },
            })

            ui.progress_text.append(f"Sending request to Ollama for image: {filename}")

            completion = client.chat.completions.create(
                model="llama3.2-vision:latest",
                messages=messages,
                max_tokens=-1,
                stream=False,
                timeout=600,  # Increased timeout to 600 seconds (10 minutes)
            )

            analysis = completion.choices[0].message.content.strip()
            logging.info(f"Ollama LLM Analysis for {filename}: {analysis}")
            ui.progress_text.append(f"Ollama LLM Analysis for {filename}: {analysis}")

            # Create folder and move image
            folder_name = analysis.strip()  # Use the analysis as the folder name
            folder_path = os.path.join(selected_directory, folder_name)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            source_path = os.path.join(selected_directory, filename)
            destination_path = os.path.join(folder_path, filename)
            move_file(source_path, destination_path)
            ui.progress_text.append(f"Moved {filename} to {folder_name}")

        ui.progress_text.append("Image organization complete.")

    except Exception as e:
        ui.progress_text.append(f"Error: {e}")
    return