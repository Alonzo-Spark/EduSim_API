import os

path = r"c:\EduSim_frontend"
print(f"Exists: {os.path.exists(path)}")
if os.path.exists(path):
    print("Files in c:\\EduSim_frontend:")
    try:
        print(os.listdir(path))
    except Exception as e:
        print(e)
