#!/usr/bin/env python3
"""Quick test script for curriculum search endpoints."""

import sys
sys.path.insert(0, ".")

from app.src.modules.tutor import service as tutor_service

print("=" * 60)
print("Testing Curriculum Search System")
print("=" * 60)

# Test 1: Flatten curriculum
print("\n[1] Testing curriculum flattening...")
try:
    entries = tutor_service._flatten_curriculum()
    print(f"✓ Flattened {len(entries)} curriculum entries")
    print(f"  Sample entry: {entries[0] if entries else 'None'}")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Search for "projectile"
print("\n[2] Testing search_curriculum('projectile')...")
try:
    results = tutor_service.search_curriculum("projectile")
    print(f"✓ Found {len(results)} results")
    for i, r in enumerate(results[:3]):
        print(f"  {i+1}. {r.get('display')} (type: {r.get('type')})")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Search for "newton"
print("\n[3] Testing search_curriculum('newton')...")
try:
    results = tutor_service.search_curriculum("newton")
    print(f"✓ Found {len(results)} results")
    for i, r in enumerate(results[:3]):
        print(f"  {i+1}. {r.get('display')} (type: {r.get('type')})")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Autocomplete for "proje"
print("\n[4] Testing autocomplete_curriculum('proje')...")
try:
    suggestions = tutor_service.autocomplete_curriculum("proje")
    print(f"✓ Found {len(suggestions)} suggestions")
    for i, s in enumerate(suggestions[:5]):
        print(f"  {i+1}. {s.get('topic')} ({s.get('subject')} • {s.get('class_name')})")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Autocomplete for "kinema"
print("\n[5] Testing autocomplete_curriculum('kinema')...")
try:
    suggestions = tutor_service.autocomplete_curriculum("kinema")
    print(f"✓ Found {len(suggestions)} suggestions")
    for i, s in enumerate(suggestions[:5]):
        print(f"  {i+1}. {s.get('topic')} ({s.get('subject')} • {s.get('class_name')})")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Get topic content
print("\n[6] Testing get_topic_content(physics, Class 11, Kinematics, Projectile motion)...")
try:
    content = tutor_service.get_topic_content("physics", "Class 11", "Kinematics", "Projectile motion")
    if "error" in content:
        print(f"✗ Error: {content['error']}")
    else:
        print(f"✓ Retrieved topic content")
        print(f"  Topic: {content.get('topic')}")
        print(f"  Subject: {content.get('subject')}")
        print(f"  Chapter: {content.get('chapter')}")
        print(f"  Related concepts: {content.get('related_concepts')}")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 7: Case-insensitive search
print("\n[7] Testing case-insensitive get_topic_content(Physics, class 11, kinematics, projectile motion)...")
try:
    content = tutor_service.get_topic_content("Physics", "class 11", "kinematics", "projectile motion")
    if "error" in content:
        print(f"✗ Error: {content['error']}")
    else:
        print(f"✓ Retrieved topic content (case-insensitive)")
        print(f"  Topic: {content.get('topic')}")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("All tests completed!")
print("=" * 60)
