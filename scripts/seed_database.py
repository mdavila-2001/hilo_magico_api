"""
Script unificado para poblar la base de datos con datos de prueba.

Este script incluye la creación de:
- Usuarios con diferentes roles
- Tiendas
- Productos
"""
import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4

# Agregar el directorio raíz al path para poder importar los módulos de la aplicación
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

# Configurar variables de entorno
from dotenv import load_dotenv
load_dotenv()

# Importaciones de SQLAlchemy
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

# Importar modelos
from app.models.user import User
from app.models.store import Store
from app.models.product import Product

# Importar utilidades
from app.db.session import AsyncSessionLocal, engine
from app.core.security import get_password_hash
from app.schemas.user import UserRole

# Configurar logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==============================================
# Funciones auxiliares
# ==============================================

async def create_user(db: AsyncSession, user_data: Dict[str, Any]) -> User:
    """
    Crea un nuevo usuario en la base de datos.
    """
    try:
        # Verificar si el usuario ya existe
        result = await db.execute(select(User).where(User.email == user_data["email"]))
        existing_user = result.scalars().first()
        
        if existing_user:
            logger.info(f"⚠️  Usuario {user_data['email']} ya existe, omitiendo...")
            return existing_user
        
        # Crear el usuario
        user = User(
            email=user_data["email"],
            hashed_password=get_password_hash(user_data["password"]),
            first_name=user_data.get("first_name", ""),
            last_name=user_data.get("last_name", ""),
            is_active=user_data.get("is_active", True),
            role=user_data.get("role", UserRole.USER),
            created_at=datetime.utcnow()
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"✅ Usuario creado: {user.email} (ID: {user.id})")
        return user
        
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error al crear usuario {user_data['email']}: {str(e)}")
        raise

async def create_store(db: AsyncSession, store_data: Dict[str, Any]) -> Store:
    """
    Crea una nueva tienda en la base de datos.
    """
    try:
        store = Store(
            id=store_data.get("id", uuid4()),
            name=store_data["name"],
            description=store_data.get("description", ""),
            address=store_data.get("address", ""),
            phone=store_data.get("phone", ""),
            email=store_data.get("email", ""),
            is_active=store_data.get("is_active", True),
            created_at=datetime.utcnow()
        )
        
        db.add(store)
        await db.commit()
        await db.refresh(store)
        
        logger.info(f"🏪 Tienda creada: {store.name} (ID: {store.id})")
        return store
        
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error al crear tienda {store_data.get('name')}: {str(e)}")
        raise

async def create_product(db: AsyncSession, product_data: Dict[str, Any]) -> Product:
    """
    Crea un nuevo producto en la base de datos.
    """
    try:
        product = Product(
            id=product_data.get("id", uuid4()),
            name=product_data["name"],
            description=product_data.get("description", ""),
            price=product_data["price"],
            stock=product_data.get("stock", 0),
            is_active=product_data.get("is_active", True),
            store_id=product_data["store_id"],
            created_at=datetime.utcnow()
        )
        
        db.add(product)
        await db.commit()
        await db.refresh(product)
        
        logger.info(f"📦 Producto creado: {product.name} (SKU: {product.sku}, ID: {product.id})")
        return product
        
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error al crear producto {product_data.get('name')}: {str(e)}")
        raise

# ==============================================
# Datos de prueba
# ==============================================

# Usuarios de prueba
USERS = [
    {
        "email": "admin@hilomagico.com",
        "password": "admin123",
        "first_name": "Admin",
        "middle_name": "del",
        "last_name": "Sistema",
        "role": UserRole.ADMIN,
        "is_active": True
    },
    {
        "email": "dueno@hilomagico.com",
        "password": "dueno123",
        "first_name": "Dueño",
        "last_name": "Tienda",
        "role": UserRole.OWNER,
        "is_active": True
    },
    {
        "email": "vendedor@hilomagico.com",
        "password": "vendedor123",
        "first_name": "Vendedor",
        "last_name": "Tienda",
        "role": UserRole.SELLER,
        "is_active": True
    },
    {
        "email": "cliente@hilomagico.com",
        "password": "cliente123",
        "first_name": "Cliente",
        "last_name": "Final",
        "role": UserRole.CUSTOMER,
        "is_active": True
    }
]

# Tiendas de prueba
STORES = [
    {
        "id": uuid4(),
        "name": "Hilo Mágico Centro",
        "description": "Tienda principal en el centro de la ciudad",
        "address": "Calle Principal 123",
        "phone": "555-1234",
        "email": "centro@hilomagico.com",
        "is_active": True
    },
    {
        "id": uuid4(),
        "name": "Hilo Mágico Sur",
        "description": "Sucursal en la zona sur",
        "address": "Avenida Sur 456",
        "phone": "555-5678",
        "email": "sur@hilomagico.com",
        "is_active": True
    }
]

# Productos de prueba
PRODUCTS = [
    # Productos para la primera tienda
    {
        "id": uuid4(),
        "name": "Hilo Algodón Blanco",
        "description": "Hilo de algodón 100% blanco, ideal para todo tipo de costura",
        "price": 15.0,
        "stock": 100,
        "is_active": True,
        "store_id": None  # Se actualizará en el script
    },
    {
        "id": uuid4(),
        "name": "Hilo Algodón Rojo",
        "description": "Hilo de algodón 100% rojo, color intenso y duradero",
        "price": 15.0,
        "stock": 80,
        "is_active": True,
        "store_id": None
    },
    {
        "id": uuid4(),
        "name": "Agua de Tejido",
        "description": "Agua especial para planchar tejidos, deja un aroma fresco",
        "price": 25.0,
        "stock": 50,
        "is_active": True,
        "store_id": None
    },
    # Productos para la segunda tienda
    {
        "id": uuid4(),
        "name": "Hilo Algodón Azul Marino",
        "description": "Hilo de algodón 100% azul marino, color clásico y elegante",
        "price": 15.0,
        "stock": 90,
        "is_active": True,
        "store_id": None
    },
    {
        "id": uuid4(),
        "name": "Hilo Algodón Verde Esmeralda",
        "description": "Hilo de algodón 100% verde esmeralda, color vibrante",
        "price": 15.0,
        "stock": 70,
        "is_active": True,
        "store_id": None
    },
    {
        "id": uuid4(),
        "name": "Agua de Tejido Premium",
        "description": "Agua para planchar tejidos con suavizante y aroma a lavanda",
        "price": 35.0,
        "stock": 40,
        "is_active": True,
        "store_id": None
    }
]

# ==============================================
# Función principal
# ==============================================

async def seed_database():
    """
    Función principal para poblar la base de datos con datos de prueba.
    """
    print("\n🚀 Iniciando la carga de datos de prueba...")
    
    async with AsyncSessionLocal() as db:
        try:
            # Crear usuarios
            print("\n👥 Creando usuarios...")
            users = []
            for user_data in USERS:
                user = await create_user(db, user_data)
                users.append(user)
            
            # Crear tiendas
            print("\n🏪 Creando tiendas...")
            stores = []
            for store_data in STORES:
                store = await create_store(db, store_data)
                stores.append(store)
            
            # Asignar store_id a los productos
            half = len(PRODUCTS) // 2
            for i, product_data in enumerate(PRODUCTS):
                product_data["store_id"] = stores[0].id if i < half else stores[1].id
            
            # Crear productos (comentado temporalmente)
            # print("\n📦 Creando productos...")
            # for product_data in PRODUCTS:
            #     await create_product(db, product_data)
            
            await db.commit()
            print("\n✅ ¡Base de datos poblada exitosamente!")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error al poblar la base de datos: {str(e)}")
            raise

if __name__ == "__main__":
    asyncio.run(seed_database())
