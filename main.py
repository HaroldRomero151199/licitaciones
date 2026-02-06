from fastapi import FastAPI
from app.routes import router as api_router
from app.api.mercadopublico import router as mp_real_router
from app.config import logger

app = FastAPI(title="Mercado Público Search API")

# Include the routes
app.include_router(api_router)
app.include_router(mp_real_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
