import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_connection():
    """Test direct database connection using psycopg2"""
    # Parámetros de conexión (extraer del DATABASE_URL)
    db_url = "postgresql://hilo-magico_owner:npg_K0yfd4YAgxJG@ep-long-recipe-a8f4mr20-pooler.eastus2.azure.neon.tech:5432/hilo-magico"
    
    # Extraer parámetros de conexión
    # Formato: postgresql://user:password@host:port/dbname
    parts = db_url.split('//')[1].split('@')
    user_pass = parts[0].split(':')
    host_db = parts[1].split('/')
    
    conn_params = {
        'dbname': host_db[1],
        'user': user_pass[0],
        'password': user_pass[1],
        'host': host_db[0].split(':')[0],
        'port': host_db[0].split(':')[1] if ':' in host_db[0] else '5432',
        'sslmode': 'require',  # Necesario para Neon.tech
        'connect_timeout': 10
    }
    
    conn = None
    try:
        logger.info("🔌 Intentando conectar a la base de datos...")
        logger.info(f"Parámetros de conexión: host={conn_params['host']}, dbname={conn_params['dbname']}, user={conn_params['user']}")
        
        # Intentar conexión
        conn = psycopg2.connect(**conn_params)
        logger.info("✅ Conexión exitosa a la base de datos")
        
        # Crear cursor
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Obtener versión de PostgreSQL
            cur.execute("SELECT version()")
            db_version = cur.fetchone()['version']
            logger.info(f"📊 Versión de la base de datos: {db_version}")
            
            # Verificar esquemas
            cur.execute("SELECT schema_name FROM information_schema.schemata ORDER BY schema_name")
            schemas = [row['schema_name'] for row in cur.fetchall()]
            logger.info(f"📂 Esquemas disponibles: {', '.join(schemas)}")
            
            # Verificar tablas en el esquema development
            if 'development' in schemas:
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'development'
                    ORDER BY table_name
                """)
                tables = [row['table_name'] for row in cur.fetchall()]
                logger.info(f"📊 Tablas en 'development': {', '.join(tables) if tables else 'Ninguna'}")
                
                if 'users' in tables:
                    # Verificar estructura de la tabla users
                    cur.execute("""
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns 
                        WHERE table_schema = 'development' 
                        AND table_name = 'users'
                        ORDER BY ordinal_position
                    """)
                    
                    logger.info("\n📋 Estructura de la tabla 'users':")
                    logger.info("-" * 80)
                    logger.info(f"{'Columna':<25} | {'Tipo':<20} | ¿Nulo? | Valor por defecto")
                    logger.info("-" * 80)
                    
                    for col in cur.fetchall():
                        logger.info(
                            f"{col['column_name']:<25} | "
                            f"{col['data_type']:<20} | "
                            f"{'Sí' if col['is_nullable'] == 'YES' else 'No':<6} | "
                            f"{col['column_default'] or 'NULL'}"
                        )
                    
                    # Contar usuarios
                    cur.execute("SELECT COUNT(*) FROM development.users")
                    count = cur.fetchone()['count']
                    logger.info(f"\n👥 Total de usuarios: {count}")
                    
    except Exception as e:
        logger.error(f"❌ Error de conexión: {str(e)}", exc_info=True)
    finally:
        if conn:
            conn.close()
            logger.info("🔌 Conexión cerrada")

if __name__ == "__main__":
    test_connection()
