from scalepad_v2 import get_templates

templates = get_templates()

print()

for t in templates["data"]:

    print(t["title"])
    print("Slug :", t["slug"])
    print("ID   :", t["id"])
    print("Updated:", t["record_updated_at"])
    print("-" * 60)
