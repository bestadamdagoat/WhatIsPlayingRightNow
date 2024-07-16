from models import Base, engine

# Create all tables in the engine. This is equivalent to "Create Table" statements in raw SQL.
Base.metadata.create_all(engine)

print("Database initialized with tables.")
