import sys
sys.path.append('c:/edu-sample')
try:
    import utils.prompts
    print('Import successful')
    # Test the functions
    context = utils.prompts.build_context(['test chunk'], 'test question')
    prompt = utils.prompts.get_prompt('test context', 'test question')
    print('Functions work correctly')
except Exception as e:
    print(f'Error: {e}')