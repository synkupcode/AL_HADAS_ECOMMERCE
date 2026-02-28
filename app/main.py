from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

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
# Store Freeze Middleware (Production Grade)
# -------------------------------------------------

class StoreFreezeMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request, call_next):

        # Always allow health endpoint
        if request.url.path == "/health":
            return await call_next(request)

        # Check ERP store visibility
        visibility = SiteControl.get_store_visibility()

        if visibility in ["Maintenance", "Disable"]:

            message = (
                "Site is under maintenance."
                if visibility == "Maintenance"
                else "System is currently unavailable."
            )

            return JSONResponse(
                status_code=503,
                content={"detail": message},
            )

        return await call_next(request)


# -------------------------------------------------
# Add Middleware (IMPORTANT ORDER)
# -------------------------------------------------

app.add_middleware(StoreFreezeMiddleware)

allow_origins = settings.ALLOWED_ORIGINS or ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------
# Include Routers
# -------------------------------------------------

app.include_router(items_router)
app.include_router(orders_router)
app.include_router(customers_router)


# -------------------------------------------------
# Health Check Endpoint
# -------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "message": "AL HADAS Ecommerce middleware is running",
    }
