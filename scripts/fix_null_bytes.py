import os
import sys

def clean_file(file_path):
    print(f"Cleaning {file_path}")
    with open(file_path, "rb") as f:
        content = f.read()
    
    if b"\x00" in content:
        print(f"Null bytes found in {file_path}, cleaning...")
        content = content.replace(b"\x00", b"")
        with open(file_path, "wb") as f:
            f.write(content)
        print(f"File cleaned: {file_path}")
        return True
    else:
        print(f"No null bytes found in {file_path}")
        return False

def scan_directory(directory):
    cleaned_files = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                if clean_file(file_path):
                    cleaned_files += 1
    print(f"Cleaned {cleaned_files} files in total")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = sys.argv[1]
        if os.path.isfile(path):
            clean_file(path)
        elif os.path.isdir(path):
            scan_directory(path)
        else:
            print(f"Path not found: {path}")
    else:
        scan_directory("cofoundai") 