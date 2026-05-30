import os

path = r"C:\Users\Aswini\.gemini\antigravity-ide\brain\6ab269ab-138f-46d6-9684-75731f582dca"
print(f"Exists: {os.path.exists(path)}")
if os.path.exists(path):
    print("Files in brain dir:")
    try:
        for root, dirs, files in os.walk(path):
            for file in files:
                print(os.path.relpath(os.path.join(root, file), path))
    except Exception as e:
        print(e)
