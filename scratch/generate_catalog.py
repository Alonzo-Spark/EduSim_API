import os
import json

base_dir = '/home/rithvik/EduSim_frontend/EduSim_frontend/public/assets'
catalog = {}

for root, dirs, files in os.walk(base_dir):
    for file in files:
        if file.endswith(('.png', '.jpg', '.svg')):
            # Get relative path from assets/
            rel_path = os.path.relpath(os.path.join(root, file), base_dir)
            category = rel_path.split(os.sep)[0]
            
            if category not in catalog:
                catalog[category] = []
            
            # Use the filename (without extension) as a potential search term, 
            # but we need the full path for the renderer.
            # We'll store the full web path.
            asset_id = os.path.splitext(file)[0]
            catalog[category].append({
                "id": asset_id,
                "path": f"/assets/{rel_path}"
            })

with open('/home/rithvik/EduSim/data/asset_catalog.json', 'w') as f:
    json.dump(catalog, f, indent=2)

print(f"Generated catalog with {sum(len(v) for v in catalog.values())} assets across {len(catalog)} categories.")
