# folder_manager.py
import os

def create_folder(path):
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating folder: {e}")
        return False

def delete_folder(path):
    try:
        os.rmdir(path)
        return True
    except Exception as e:
        print(f"Error deleting folder: {e}")
        return False

def rename_folder(old_path, new_path):
    try:
        os.rename(old_path, new_path)
        return True
    except Exception as e:
        print(f"Error renaming folder: {e}")
        return False