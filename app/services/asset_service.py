import json
from pathlib import Path

_catalog = None

def load_asset_catalog() -> list[dict]:
    global _catalog
    if _catalog is None:
        catalog_path = Path("data/asset_catalog.json")
        if catalog_path.exists():
            with open(catalog_path) as f:
                data = json.load(f)
                _catalog = data.get("assets", [])
        else:
            # Fallback path if run from a different subfolder context
            alt_path = Path(__file__).parent.parent.parent / "data" / "asset_catalog.json"
            if alt_path.exists():
                with open(alt_path) as f:
                    data = json.load(f)
                    _catalog = data.get("assets", [])
            else:
                _catalog = []
    return _catalog

async def get_assets_for_topic(topic: str, subject: str) -> list[dict]:
    """Return assets relevant to a topic based on tags and topic matching."""
    catalog = load_asset_catalog()
    topic_lower = topic.lower().replace(" ", "_")
    subject_lower = subject.lower()

    matching = []
    for asset in catalog:
        asset_topics = [t.lower() for t in asset.get("topics", [])]
        asset_tags = [t.lower() for t in asset.get("tags", [])]
        asset_category = asset.get("category", "").lower()

        if (
            topic_lower in asset_topics
            or any(topic_lower in t for t in asset_topics)
            or subject_lower == asset_category
            or any(word in asset_tags for word in topic_lower.split("_"))
        ):
            matching.append(asset)

    # If no topic-specific assets, return generic ones for the subject
    if not matching:
        matching = [a for a in catalog if a.get("category", "").lower() == subject_lower]

    return matching[:8]  # cap at 8 assets per simulation
