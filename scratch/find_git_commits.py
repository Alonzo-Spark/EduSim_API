import subprocess

result = subprocess.run(
    ["git", "log", "--all", "--name-only", "--oneline"],
    cwd=r"c:\EduSim_frontend",
    capture_output=True,
    text=True,
    encoding="utf-8"
)

lines = result.stdout.splitlines()
current_commit = ""
for line in lines:
    if line and not line.startswith(" ") and not "/" in line.split(" ")[0]:
        current_commit = line
    if "AssistedModePanel" in line or "assistedModeStore" in line:
        print(f"Found in commit: {current_commit} -> {line}")
