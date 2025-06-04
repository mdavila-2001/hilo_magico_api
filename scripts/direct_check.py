import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_database():
    """Check database connection and structure using psycopg2"""
    logger.info("🚀 Starting direct database check...")
    
    # Parse the database URL
    db_url = settings.DATABASE_URL
    logger.info(f"🔗 Database URL: {db_url}")
    
    # Extract connection parameters from URL
    # Format: postgresql+asyncpg://user:password@host:port/dbname
    db_url = db_url.replace('postgresql+asyncpg://', '')
    user_pass, host_port_db = db_url.split('@')
    user, password = user_pass.split(':')
    host_port, dbname = host_port_db.split('/')
    
    if ':' in host_port:
        host, port = host_port.split(':')
    else:
        host = host_port
        port = '5432'  # Default PostgreSQL port
    
    conn = None
    try:
        # Connect to PostgreSQL
        logger.info(f"🔌 Connecting to {host}:{port}/{dbname} as {user}...")
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
            cursor_factory=RealDictCursor
        )
        
        # Set autocommit to True
        conn.autocommit = True
        
        # Create a cursor
        cur = conn.cursor()
        
        # Get database version
        cur.execute("SELECT version()")
        db_version = cur.fetchone()['version']
        logger.info(f"📊 Database version: {db_version}")
        
        # List schemas
        cur.execute("SELECT schema_name FROM information_schema.schemata ORDER BY schema_name")
        schemas = [row['schema_name'] for row in cur.fetchall()]
        logger.info(f"📂 Available schemas: {', '.join(schemas)}")
        
        # Check if development schema exists
        if 'development' in schemas:
            logger.info("🔍 Checking 'development' schema...")
            
            # List tables in development schema
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'development'
                ORDER BY table_name
            """)
            tables = [row['table_name'] for row in cur.fetchall()]
            logger.info(f"📊 Tables in 'development' schema: {', '.join(tables) if tables else 'None'}")
            
            # Check users table
            if 'users' in tables:
                logger.info("\n🔍 Checking 'users' table structure...")
                cur.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_schema = 'development' 
                    AND table_name = 'users'
                    ORDER BY ordinal_position
                """)
                
                logger.info("\n📋 'users' table columns:")
                logger.info("-" * 80)
                logger.info(f"{'Column':<25} | {'Type':<20} | {'Nullable':<10} | {'Default'}")
                logger.info("-" * 80)
                
                for col in cur.fetchall():
                    logger.info(
                        f"{col['column_name']:<25} | "
                        f"{col['data_type']:<20} | "
                        f"{'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL':<10} | "
                        f"{col['column_default'] or 'NULL'}"
                    )
                
                # Check for sample data
                try:
                    cur.execute("SELECT COUNT(*) FROM development.users")
                    count = cur.fetchone()['count']
                    logger.info(f"\n📊 Total users in database: {count}")
                    
                    if count > 0:
                        cur.execute("SELECT * FROM development.users LIMIT 1")
                        user = cur.fetchone()
                        logger.info("\n👤 Sample user:")
                        for key, value in user.items():
                            logger.info(f"- {key}: {value}")
                except Exception as e:
                    logger.warning(f"⚠️  Could not fetch users: {str(e)}")
        
        # Test a simple query
        try:
            cur.execute("SELECT 1 AS test_value")
            result = cur.fetchone()['test_value']
            logger.info(f"\n✅ Simple query test: SELECT 1 = {result}")
        except Exception as e:
            logger.error(f"❌ Simple query failed: {str(e)}")
        
        logger.info("\n✅ Database check completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Database check failed: {str(e)}", exc_info=True)
        return False
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            logger.info("🔌 Database connection closed")
    
    return True

if __name__ == "__main__":
    check_database()
