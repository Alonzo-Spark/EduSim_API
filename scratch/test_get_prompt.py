import sys
sys.path.append('c:/EduSim/EduSim_API/app/src')
from modules.legacy_rag.generator import get_tutor_prompt
print(get_tutor_prompt('Sample context', 'What is energy?', fallback_mode=True))
