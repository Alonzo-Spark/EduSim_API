import os

files = [
    r"c:\EduSim_frontend\src\sandbox\components\AssistedModePanel.tsx",
    r"c:\EduSim_frontend\src\store\assistedModeStore.ts",
    r"c:\EduSim_frontend\src\sandbox\components\ObjectiveTracker.tsx",
    r"c:\EduSim_frontend\src\sandbox\components\SmartHintSystem.tsx",
    r"c:\EduSim_frontend\src\sandbox\components\SimulationAnalyzer.tsx",
    r"c:\EduSim_frontend\src\sandbox\components\ChallengePanel.tsx",
]

for f in files:
    print(f"{f} exists: {os.path.exists(f)}")
