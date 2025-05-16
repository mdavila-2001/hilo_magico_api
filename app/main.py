# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importar routers
from app.api.v1.routes import users

app = FastAPI(title="Hilo Mágico API", version="1.0.0")

# CORS – permití conexión desde frontend Astro o localhost
origins = [
    "http://localhost:3000",  # Astro local
    "http://127.0.0.1:3000",
    "*"  # (opcional para pruebas, restringir en producción)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ruta raíz
@app.get("/")
def root():
    return {"message": "✨ Bienvenido a Hilo Mágico API ✂️"}

# Incluir rutas del módulo usuario
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
