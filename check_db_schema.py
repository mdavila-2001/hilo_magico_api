import asyncio
import asyncpg
from app.core.config import settings

async def check_database_schema():
    print("🔍 Analizando esquema de la base de datos...")
    
    # Ajustar la URL para asyncpg
    db_url = settings.DATABASE_URL.replace('+asyncpg', '')
    
    try:
        # Conectarse a la base de datos
        conn = await asyncpg.connect(dsn=db_url)
        print("✅ Conexión exitosa con PostgreSQL!")
        
        # Obtener información de la tabla users
        print("\n📋 Estructura de la tabla 'users':")
        columns = await conn.fetch('''
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'users'
            ORDER BY ordinal_position
        ''')
        
        if columns:
            print("\n   Nombre Columna   |   Tipo de Dato   | ¿Nulo? |           Valor por Defecto")
            print("-" * 80)
            for col in columns:
                col_name = col['column_name'].ljust(18)
                col_type = col['data_type'].ljust(16)
                nullable = "Sí" if col['is_nullable'] == 'YES' else "No"
                default = str(col['column_default'])[:30] + '...' if col['column_default'] else 'NULL'
                print(f"   {col_name} | {col_type} | {nullable.ljust(6)} | {default}")
        else:
            print("   No se encontró la tabla 'users' en la base de datos.")
        
        # Contar usuarios
        user_count = await conn.fetchval('SELECT COUNT(*) FROM users')
        print(f"\n👥 Total de usuarios en la base de datos: {user_count}")
        
        # Mostrar primeros 5 usuarios (si existen)
        if user_count > 0:
            print("\n👤 Primeros 5 usuarios:")
            users = await conn.fetch('SELECT id, email, created_at FROM users LIMIT 5')
            for i, user in enumerate(users, 1):
                print(f"   {i}. ID: {user['id']}, Email: {user['email']}, Creado: {user['created_at']}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        if 'conn' in locals():
            await conn.close()
            print("\n🔌 Conexión cerrada correctamente")

if __name__ == "__main__":
    asyncio.run(check_database_schema())
