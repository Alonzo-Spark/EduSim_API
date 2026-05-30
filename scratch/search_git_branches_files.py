import subprocess

result = subprocess.run(
    ["git", "branch", "-a"],
    cwd=r"c:\model_eval\EduSim_frontend",
    capture_output=True,
    text=True,
    encoding="utf-8"
)

branches = [b.strip().replace("* ", "") for b in result.stdout.splitlines() if b.strip()]

for branch in branches:
    # Clean branch name
    b_name = branch.split(" -> ")[0]
    res_files = subprocess.run(
        ["git", "ls-tree", "-r", b_name, "--name-only"],
        cwd=r"c:\model_eval\EduSim_frontend",
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    if "AssistedModePanel" in res_files.stdout:
        print(f"Branch {b_name} CONTAINS AssistedModePanel.tsx!")
