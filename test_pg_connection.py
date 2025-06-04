import asyncio
import asyncpg
from app.core.config import settings

async def test_connection():
    print("🔍 Probando conexión directa con asyncpg...")
    
    # Extraer los componentes de la URL
    db_url = settings.DATABASE_URL
    print(f"URL de conexión original: {db_url}")
    
    # Ajustar la URL para asyncpg (eliminar el +asyncpg si existe)
    db_url = db_url.replace('+asyncpg', '')
    print(f"URL ajustada para asyncpg: {db_url}")
    
    try:
        # Conectarse a la base de datos con un timeout corto
        print("\n🔌 Intentando conectar a la base de datos...")
        conn = await asyncio.wait_for(asyncpg.connect(dsn=db_url), timeout=10.0)
        print("✅ Conexión exitosa con PostgreSQL!")
        
        # Obtener versión de PostgreSQL
        version = await conn.fetchval('SELECT version()')
        print(f"📊 {version}")
        
        # Listar tablas
        tables = await conn.fetch('''
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY table_schema, table_name
        ''')
        
        if tables:
            print("\n📋 Tablas en la base de datos:")
            for table in tables:
                print(f"   - {table['table_schema']}.{table['table_name']}")
        else:
            print("\nℹ️ No se encontraron tablas en la base de datos.")
            
    except asyncio.TimeoutError:
        print("\n⌛ Error: Tiempo de espera agotado al intentar conectar a la base de datos")
        print("   - Verifica tu conexión a internet")
        print("   - Asegúrate de que la base de datos esté en línea")
        return
    except asyncpg.InvalidPasswordError:
        print("\n🔑 Error: Usuario o contraseña incorrectos")
        return
    except asyncpg.PostgresError as e:
        print(f"\n❌ Error de PostgreSQL: {e}")
        return
    except Exception as e:
        print(f"\n❌ Error al conectar a la base de datos: {e}")
        print("\n🔧 Posibles soluciones:")
        print("1. Verifica que la URL de conexión en .env sea correcta")
        print("2. Asegúrate de que la base de datos esté en línea y accesible")
        print("3. Verifica que el usuario y contraseña sean correctos")
        print("4. Comprueba que tu conexión a internet sea estable")
        print("5. Si usas una VPN, asegúrate de que permite conexiones a la base de datos")
    finally:
        if 'conn' in locals():
            await conn.close()
            print("\n🔌 Conexión cerrada correctamente")

if __name__ == "__main__":
    asyncio.run(test_connection())
