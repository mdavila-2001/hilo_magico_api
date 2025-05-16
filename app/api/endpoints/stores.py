from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.api.deps import get_db
from app.schemas.store import Store, StoreCreate, StoreUpdate
from app.services import store_service

router = APIRouter()

@router.post("/", response_model=Store)
def create_store(store: StoreCreate, db: Session = Depends(get_db)):
    return store_service.create_store(db=db, store=store)

@router.get("/{store_id}", response_model=Store)
def read_store(store_id: UUID, db: Session = Depends(get_db)):
    db_store = store_service.get_store(db, store_id=store_id)
    if db_store is None:
        raise HTTPException(status_code=404, detail="Tienda no encontrada")
    return db_store

@router.get("/", response_model=List[Store])
def read_stores(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    stores = store_service.get_all_stores(db, skip=skip, limit=limit)
    return stores

@router.put("/{store_id}", response_model=Store)
def update_store(store_id: UUID, store: StoreUpdate, db: Session = Depends(get_db)):
    db_store = store_service.update_store(db, store_id=store_id, store_data=store)
    if db_store is None:
        raise HTTPException(status_code=404, detail="Tienda no encontrada")
    return db_store

@router.delete("/{store_id}", response_model=Store)
def delete_store(store_id: UUID, db: Session = Depends(get_db)):
    db_store = store_service.delete_store(db, store_id=store_id)
    if db_store is None:
        raise HTTPException(status_code=404, detail="Tienda no encontrada")
    return db_store