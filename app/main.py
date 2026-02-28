from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import APIRouter

from app.core.config import settings
from app.core.site_control import SiteControl

from app.api.items import router as items_router
from app.api.orders import router as orders_router
from app.api.customers import router as customers_router


# -------------------------------------------------
# Create FastAPI App
# -------------------------------------------------

app = FastAPI(title="AL HADAS Ecommerce Middleware")


# -------------------------------------------------
# Store Freeze Middleware (Backend Protection)
# -------------------------------------------------

class StoreFreezeMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request, call_next):

        # Always allow health check
        if request.url.path == "/health":
            return await call_next(request)

        # Check ERP Store Visibility
        visibility = SiteControl.get_store_visibility()

        # If not enabled → block backend APIs
        if visibility in ["Maintenance", "Disable"]:
            return JSONResponse(
                status_code=503,
                content={
                    "visibility": visibility,
                    "detail": "Store is currently unavailable."
                },
            )

        return await call_next(request)


# -------------------------------------------------
# Add Middleware (IMPORTANT ORDER)
# -------------------------------------------------

app.add_middleware(StoreFreezeMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------
# Store Status Endpoint (For Next.js UI Control)
# -------------------------------------------------

status_router = APIRouter()

@status_router.get("/store-status")
def store_status():
    return {
        "visibility": SiteControl.get_store_visibility()
    }

app.include_router(status_router)


# -------------------------------------------------
# Include Existing Routers
# -------------------------------------------------

app.include_router(items_router)
app.include_router(orders_router)
app.include_router(customers_router)


# -------------------------------------------------
# Health Check
# -------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "message": "AL HADAS Ecommerce middleware is running",
    }
