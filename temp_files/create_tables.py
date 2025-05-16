import sys
sys.path.append('.')

from app.db.session import engine
from app.models import user
from app.db.session import Base

print("🔧 Creando tablas en la base de datos...")
Base.metadata.create_all(bind=engine)
print("✅ Tablas creadas correctamente.")