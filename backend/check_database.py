from sqlalchemy import inspect
from app.db.database import engine

inspector = inspect(engine)

tables = inspector.get_table_names()

print("\n========== DATABASE TABLES ==========\n")

for table in tables:
    print(f"✓ {table}")

print("\n========== FOREIGN KEY RELATIONSHIPS ==========\n")

for table in tables:
    foreign_keys = inspector.get_foreign_keys(table)

    for fk in foreign_keys:
        print(
            f"{table}.{fk['constrained_columns']} "
            f"-> {fk['referred_table']}.{fk['referred_columns']}"
        )

print("\n========== VERIFICATION COMPLETED ==========")