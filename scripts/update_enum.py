"""
Script para actualizar el enum userrole en la base de datos.
"""
import sys
import asyncio
from pathlib import Path
from sqlalchemy import text

# Agregar el directorio raíz al path para que Python pueda encontrar los módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import engine

async def update_userrole_enum():
    """Actualiza el enum userrole en la base de datos."""
    async with engine.begin() as conn:
        # 1. Verificar si el tipo enum existe
        result = await conn.execute(text(
            """
            SELECT t.typname, e.enumlabel 
            FROM pg_type t 
            JOIN pg_enum e ON t.oid = e.enumtypid
            WHERE t.typname = 'userrole';
            """
        ))
        
        current_values = {row[1] for row in result.fetchall()}
        expected_values = {'admin', 'user', 'seller', 'owner', 'customer'}
        
        print("Valores actuales del enum:", current_values)
        print("Valores esperados:", expected_values)
        
        # 2. Agregar valores faltantes
        for value in expected_values - current_values:
            print(f"Agregando valor faltante: {value}")
            try:
                await conn.execute(text(f"ALTER TYPE userrole ADD VALUE IF NOT EXISTS '{value}'"))
                print(f"✅ Valor '{value}' agregado exitosamente")
            except Exception as e:
                print(f"⚠️ Error al agregar valor '{value}': {e}")
        
        await conn.commit()

if __name__ == "__main__":
    print("🔄 Actualizando enum userrole...")
    asyncio.run(update_userrole_enum())
    print("✅ Proceso completado")
