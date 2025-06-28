import asyncio
from datetime import datetime
from uuid import uuid4
import json

from app.db.session import SessionLocal
from app.models.product import Product
from app.models.store import Store
from app.models.user import User
from app.schemas.user import UserRole

async def seed_products():
    async with SessionLocal() as db:
        # Crear tiendas de prueba
        stores = [
            Store(
                id=uuid4(),
                name="Hilo Mágico",
                description="Tienda principal en el centro de la ciudad",
                address="Calle Principal 123",
                phone="62160217",
                email="hilo.magico.scz@gmail.com",
                is_active=True,
                created_at=datetime.now()
            ),
            Store(
                id=uuid4(),
                name="Tienda Sur",
                description="Tienda en la zona sur de la ciudad",
                address="Avenida Sur 456",
                phone="555-5678",
                email="tienda.sur@hilomagico.com",
                is_active=True,
                created_at=datetime.now()
            )
        ]
        
        # Crear productos para la Tienda Centro
        products_centro = [
            Product(
                id=uuid4(),
                name="Hilo Blanco",
                description="Hilo de algodón 100% blanco",
                price=15.0,
                stock=100,
                is_active=True,
                store_id=stores[0].id,
                created_at=datetime.now()
            ),
            Product(
                id=uuid4(),
                name="Hilo Rojo",
                description="Hilo de algodón 100% rojo",
                price=15.0,
                stock=80,
                is_active=True,
                store_id=stores[0].id,
                created_at=datetime.now()
            ),
            Product(
                id=uuid4(),
                name="Agua de Tejido",
                description="Agua para tejido de alta calidad",
                price=25.0,
                stock=50,
                is_active=True,
                store_id=stores[0].id,
                created_at=datetime.now()
            )
        ]
        
        # Crear productos para la Tienda Sur
        products_sur = [
            Product(
                id=uuid4(),
                name="Hilo Azul Marino",
                description="Hilo de algodón 100% azul marino",
                price=15.0,
                stock=90,
                is_active=True,
                store_id=stores[1].id,
                created_at=datetime.now()
            ),
            Product(
                id=uuid4(),
                name="Hilo Verde Esmeralda",
                description="Hilo de algodón 100% verde esmeralda",
                price=15.0,
                stock=70,
                is_active=True,
                store_id=stores[1].id,
                created_at=datetime.now()
            ),
            Product(
                id=uuid4(),
                name="Agua de Tejido Premium",
                description="Agua para tejido de alta calidad con ingredientes especiales",
                price=35.0,
                stock=40,
                is_active=True,
                store_id=stores[1].id,
                created_at=datetime.now()
            )
        ]
        
        # Agregar tiendas a la base de datos
        for store in stores:
            db.add(store)
        await db.commit()
        
        # Agregar productos a la base de datos
        for product in products_centro + products_sur:
            db.add(product)
        await db.commit()
        
        print("\nDatos de prueba creados exitosamente!")
        print("\nTiendas creadas:")
        for store in stores:
            print(f"- {store.name} (ID: {store.id})")
        
        print("\nProductos en Tienda Centro:")
        for product in products_centro:
            print(f"- {product.name} (ID: {product.id}, Precio: ${product.price}, Stock: {product.stock})")
        
        print("\nProductos en Tienda Sur:")
        for product in products_sur:
            print(f"- {product.name} (ID: {product.id}, Precio: ${product.price}, Stock: {product.stock})")

if __name__ == "__main__":
    asyncio.run(seed_products())
