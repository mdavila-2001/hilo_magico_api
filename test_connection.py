from sqlalchemy import text, inspect
from app.db.session import SessionLocal
from app.models.user import User

try:
    db = SessionLocal()
    # Verificar la conexión
    db.execute(text("SELECT 1"))
    print("✅ Conexión exitosa con Neon PostgreSQL\n")

    # Mostrar las tablas existentes
    inspector = inspect(db.get_bind())
    schemas = inspector.get_schema_names()
    
    print("📋 Tablas existentes en la base de datos:")
    for schema in schemas:
        if schema != "information_schema":
            tables = inspector.get_table_names(schema=schema)
            for table in tables:
                print(f"   - {schema}.{table}")
    
    # Intentar obtener algunos usuarios
    print("\n👥 Usuarios registrados:")
    users = db.query(User).all()
    if users:
        for user in users:
            print(f"   - {user.full_name} ({user.email}) - Rol: {user.role}")
    else:
        print("   No hay usuarios registrados aún.")

except Exception as e:
    print("❌ Error:", e)
finally:
    db.close()