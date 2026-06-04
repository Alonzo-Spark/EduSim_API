import os
from sqlalchemy import create_engine, inspect

DATABASE_URL = "postgresql://postgres:Rith439@localhost:5432/edusim"
engine = create_engine(DATABASE_URL)
inspector = inspect(engine)

for table_name in ['classes', 'subjects', 'chapters', 'topics', 'curriculum_classes', 'curriculum_subjects']:
    if inspector.has_table(table_name):
        print(f"Table: {table_name}")
        for col in inspector.get_columns(table_name):
            print(f"  {col['name']} ({col['type']})")
    else:
        print(f"Table: {table_name} NOT FOUND")
