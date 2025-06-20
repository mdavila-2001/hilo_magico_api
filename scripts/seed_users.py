"""
Script para poblar la base de datos con usuarios de prueba.

Este script crea varios usuarios con diferentes roles para propósitos de desarrollo y pruebas.
"""
import sys
import uuid
from datetime import datetime
from typing import List, Dict, Any

# Agregar el directorio raíz al path para poder importar los módulos de la aplicación
sys.path.insert(0, str('c:/NUR/Semestre III/Comercio Electrónico/hilo_magico_api'))

import asyncio
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal, engine
from app.core.security import get_password_hash
from app.models.user import User

async def create_user(db: AsyncSession, user_data: Dict[str, Any]) -> User:
    """
    Crea un nuevo usuario en la base de datos.
    
    Args:
        db: Sesión de base de datos asíncrona
        user_data: Diccionario con los datos del usuario
        
    Returns:
        User: El usuario creado
    """
    try:
        # Verificar si el usuario ya existe
        result = await db.execute(select(User).where(User.email == user_data["email"]))
        existing_user = result.scalars().first()
        
        if existing_user:
            print(f"⚠️  El usuario con email {user_data['email']} ya existe")
            return existing_user
        
        # Obtener el rol como entero (por defecto 0=USER)
        role = int(user_data.get("role", 0))
        
        # Crear el nuevo usuario
        user = User(
            email=user_data["email"],
            first_name=user_data["first_name"],
            middle_name=user_data.get("middle_name"),
            last_name=user_data["last_name"],
            mother_last_name=user_data.get("mother_last_name"),
            hashed_password=get_password_hash(user_data["password"]),
            is_active=user_data.get("is_active", True),
            is_superuser=user_data.get("is_superuser", False),
            role=role
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        print(f"✅ Usuario creado: {user_data['email']} (Rol: {role})")
        return user
        
    except Exception as e:
        await db.rollback()
        print(f"❌ Error al crear usuario {user_data.get('email', 'unknown')}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def seed_users():
    """Función principal para poblar la base de datos con usuarios de prueba."""
    print("🚀 Iniciando seed de usuarios...")
    
    # Datos de los usuarios a crear
    # Códigos de rol: 0=USER, 1=ADMIN, 2=OWNER, 3=SELLER, 4=CUSTOMER
    users_data = [
        {
            "email": "admin@hilomagico.com",
            "first_name": "Admin",
            "last_name": "Sistema",
            "password": "admin123",
            "role": 1,  # 1=ADMIN
            "is_superuser": True,
            "is_active": True
        },
        {
            "email": "vendedor1@hilomagico.com",
            "first_name": "Ana",
            "middle_name": "María",
            "last_name": "Pérez",
            "mother_last_name": "González",
            "password": "vendedor123",
            "role": 3,  # 3=SELLER
            "is_active": True
        },
        {
            "email": "dueno1@hilomagico.com",
            "first_name": "Carlos",
            "last_name": "López",
            "password": "dueno123",
            "role": 2,  # 2=OWNER
            "is_active": True
        },
        {
            "email": "cliente1@hilomagico.com",
            "first_name": "Laura",
            "middle_name": "Isabel",
            "last_name": "Martínez",
            "mother_last_name": "Sánchez",
            "password": "cliente123",
            "role": 4,  # 4=CUSTOMER
            "is_active": True
        },
        {
            "email": "usuario1@hilomagico.com",
            "first_name": "Juan",
            "last_name": "Gómez",
            "password": "usuario123",
            "role": 0,  # 0=USER
            "is_active": True
        }
    ]
    
    # Obtener la sesión de la base de datos
    print("🔌 Conectando a la base de datos...")
    db = AsyncSessionLocal()
    
    try:
        # Verificar si la tabla de usuarios existe
        print("🔍 Verificando tabla de usuarios...")
        result = await db.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'development' AND table_name = 'users')")
        )
        table_exists = result.scalar()
        
        if not table_exists:
            print("❌ La tabla 'users' no existe en el esquema 'development'")
            print("   Por favor, ejecute primero el script create_tables.py")
            return 0
            
        # Crear cada usuario
        created_count = 0
        print(f"\n📝 Intentando crear {len(users_data)} usuarios...")
        
        for i, user_data in enumerate(users_data, 1):
            print(f"\n🔧 Procesando usuario {i}/{len(users_data)}: {user_data['email']}")
            try:
                user = await create_user(db, user_data)
                if user:
                    created_count += 1
                    print(f"✅ Usuario {i} creado exitosamente")
                else:
                    print(f"⚠️  No se pudo crear el usuario {i}")
            except Exception as e:
                print(f"❌ Error al crear usuario {i}: {str(e)}")
                import traceback
                traceback.print_exc()
        
        print(f"\n🎉 Se crearon {created_count} de {len(users_data)} usuarios exitosamente!")
        return created_count
        
    except Exception as e:
        print(f"\n❌ Error al crear usuarios: {str(e)}")
        await db.rollback()
    finally:
        await db.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(seed_users())
