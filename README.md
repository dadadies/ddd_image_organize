# ddd_image_organize

A Windows 11 image organizer application that uses LLMs (OpenAI, Google Gemini, or local models) to automatically categorize images into folders based on what is depicted in the images.

![alt text](image.png)

## Features

*   Upload images
*   Select a directory to organize images into
*   Choose between OpenAI, Google Gemini, or a local LLM for image categorization
*   Automatically categorize images into folders based on their content

## Usage

1.  Clone the repository.
2.  Install the required dependencies (e.g., `pip install -r requirements.txt`).
3.  Run the application (`python main.py`).
4.  Upload images using the "Upload Images" button.
5.  Select a directory to organize the images into.
6.  Choose an LLM (OpenAI, Google Gemini, or Local).
    If using LM Studio, provide the `0.json` file to help it provide a structured JSON output.
7.  If using OpenAI or Google Gemini, enter your API key.
8.  Click the "Organize Images" button.

## Dependencies

*   PyQt5
*   requests
*   openai
*   google.generativeai
*   llama\_cpp (for local LLM)

## License

[MIT](https://opensource.org/licenses/MIT)

## Future Goals

*   Improve compatibility with local and online LLMs/APIs.
*   Enhance accuracy in image identification and folder placement.
    The current LLM is not accurate in identifying images. This is an area that needs further development.
    This project is being shared on GitHub to encourage contributions to improve this aspect of the project.
*   Implement a configuration/preference system.