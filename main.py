from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router as api_router
from app.api.mercadopublico import router as mp_real_router
from app.api.admin import router as admin_router
from app.config import logger

app = FastAPI(title="Mercado Público Search API")

# 1. Define los orígenes permitidos
origins = [
    "http://localhost:3000",  # Tu app de Angular
    "http://127.0.0.1:3000",
]

# 2. Agrega el middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # Permite el origen de tu frontend
    allow_credentials=True,
    allow_methods=["*"],              # Permite todos los métodos (GET, POST, etc.)
    allow_headers=["*"],              # Permite todos los headers
)

# Include the routes
app.include_router(api_router)
app.include_router(mp_real_router)
app.include_router(admin_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
