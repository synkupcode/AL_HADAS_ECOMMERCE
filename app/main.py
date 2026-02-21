from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.items import router as items_router
from app.api.orders import router as orders_router
from app.api.customers import router as customers_router

app = FastAPI(title="AL HADAS Ecommerce Middleware")

# CORS Configuration
allow_origins = settings.ALLOWED_ORIGINS or ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(items_router)
app.include_router(orders_router)
app.include_router(customers_router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "message": "AL HADAS Ecommerce middleware is running",
    }