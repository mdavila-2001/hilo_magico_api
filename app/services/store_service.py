from sqlalchemy.orm import Session
from app.models.store import Store
from app.schemas.store import StoreCreate, StoreUpdate

def create_store(db: Session, store: StoreCreate):
    db_store = Store(
        name=store.name,
        city=store.city,
        address=store.address,
        phone=store.phone,
        is_active=store.is_active
    )
    db.add(db_store)
    db.commit()
    db.refresh(db_store)
    return db_store

def get_store(db: Session, store_id: int):
    return db.query(Store).filter(Store.id == store_id).first()

def get_all_stores(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Store).offset(skip).limit(limit).all()

def update_store(db: Session, store_id: int, store_data: StoreUpdate):
    store = get_store(db, store_id)
    if not store:
        return None

    if store_data.name is not None:
        store.name = store_data.name
    if store_data.city is not None:
        store.city = store_data.city
    if store_data.address is not None:
        store.address = store_data.address
    if store_data.phone is not None:
        store.phone = store_data.phone
    if store_data.is_active is not None:
        store.is_active = store_data.is_active

    db.commit()
    db.refresh(store)
    return store

def delete_store(db: Session, store_id: UUID):
    store = get_store(db, store_id)
    if not store:
        return None
    db.delete(store)
    db.commit()
    return store