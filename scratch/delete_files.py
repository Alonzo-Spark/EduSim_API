import os

files_to_delete = [
    r"c:\model_eval\EduSim_frontend\src\sandbox\components\AssistedModePanel.tsx",
    r"c:\model_eval\EduSim_frontend\src\store\assistedModeStore.ts",
    r"c:\model_eval\EduSim_frontend\src\sandbox\components\ObjectiveTracker.tsx",
    r"c:\model_eval\EduSim_frontend\src\sandbox\components\SmartHintSystem.tsx",
    r"c:\model_eval\EduSim_frontend\src\sandbox\components\SimulationAnalyzer.tsx",
    r"c:\model_eval\EduSim_frontend\src\sandbox\components\ChallengePanel.tsx",
    r"c:\model_eval\EduSim_frontend\implementation_plan.md",
    r"c:\model_eval\EduSim_API\app\src\modules\challenge\models.py",
    r"c:\model_eval\EduSim_API\app\src\modules\challenge\generator.py",
    r"c:\model_eval\EduSim_API\app\src\modules\challenge\evaluator.py",
    r"c:\model_eval\EduSim_API\app\src\api\challenge_router.py",
]

for f in files_to_delete:
    if os.path.exists(f):
        try:
            os.remove(f)
            print(f"Deleted: {f}")
        except Exception as e:
            print(f"Error deleting {f}: {e}")
