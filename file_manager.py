# file_manager.py
import os
import shutil

def move_file(src, dest):
    try:
        shutil.move(src, dest)
        return True
    except Exception as e:
        print(f"Error moving file: {e}")
        return False

def copy_file(src, dest):
    try:
        shutil.copy(src, dest)
        return True
    except Exception as e:
        print(f"Error copying file: {e}")
        return False

def delete_file(path):
    try:
        os.remove(path)
        return True
    except Exception as e:
        print(f"Error deleting file: {e}")
        return False