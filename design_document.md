# Image Organization Software Design Document

## 1. Introduction

A Windows 11 software application with a UI that allow the user to provide images to a large language model (LLM) with vision capabilities, either online or local, to analyze the images and detail how to organize the images into appropriate folders based on what what is depicted in the images, and return a Json structure with the final files and the folders. The program will use this infirmation to perform the task.

## 3. Tools Used

*   **Python:** The primary programming language for developing the software.
*   **PyQt or Tkinter:** A UI framework for creating the graphical user interface.
*   **OpenAI API or similar:** An LLM API for natural language processing and vision capabilities.
*   **OpenCV or Pillow:** An image processing library for handling image manipulation.
*   **PyInstaller:** A tool for packaging the software into an executable file for Windows 11.

## 3. System Architecture

The software will consist of the following components:

*   **User Interface (UI):** A graphical interface for users to interact with the software, input commands, and view image organization progress.
*   **Natural Language Processing (NLP) Module:** Integrates with an LLM to process user commands and extract relevant information for image organization.
*   **Vision Module:** Uses the LLM's vision capabilities to analyze image content and identify objects, scenes, and other relevant features.
*   **Image Processing Module:** Handles image loading, resizing, and format conversion.
*   **Folder Management Module:** Creates, deletes, and renames folders based on the LLM's analysis and user commands.
*   **File Management Module:** Moves, copies, and deletes image files based on the LLM's analysis and user commands.
*   **Configuration Module:** Stores user preferences, API keys, and other configuration settings.

## 6. Development Process

### 4.0. LLM Compatibility

The software should be compatible with both online and local LLMs.

*   **Online LLMs:** Utilize cloud-based LLM services like OpenAI API. Requires an internet connection and API key.
*   **Local LLMs:** Support running LLMs locally on the user's machine. Requires sufficient hardware resources and a compatible LLM implementation (e.g., llama.cpp). eg: LM Studio.

The software should allow users to choose their preferred LLM and configure the necessary settings.

## 7. Future Goals

*   Improve compatibility with local and online LLMs/APIs.
*   Enhance accuracy in image identification and folder placement.
    The current LLM is not always accurate in identifying images and placing them in the appropriate folders. This is an area that needs further development.
*   Implement a configuration/preference system.