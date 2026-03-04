from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Rate Limiting (from separate module — NO circular import)
from app.core.rate_limiter import limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.site_control import SiteControl

from app.api.items import router as items_router
from app.api.orders import router as orders_router
from app.api.customers import router as customers_router
from app.api.contact import router as contact_router
from app.api.auth import router as auth_router
from app.api.profile import router as profile_router
from app.api import order_history
# -------------------------------------------------
# Create FastAPI App
# -------------------------------------------------

app = FastAPI(title="AL HADAS Ecommerce Middleware")


# -------------------------------------------------
# Rate Limiter Setup
# -------------------------------------------------

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please try again later."},
    )


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
    allow_origins=settings.ALLOWED_ORIGINS if settings.ALLOWED_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------
# Store Status Endpoint
# -------------------------------------------------

from fastapi import APIRouter

status_router = APIRouter()

@status_router.get("/store-status")
def store_status():
    return {
        "visibility": SiteControl.get_store_visibility()
    }

app.include_router(status_router)


# -------------------------------------------------
# Include Routers
# -------------------------------------------------

app.include_router(items_router)
app.include_router(orders_router)
app.include_router(customers_router)
app.include_router(contact_router)
app.include_router(auth_router)
app.include_router(profile_router, prefix="/api")
app.include_router(order_history.router, prefix="/api")

# -------------------------------------------------
# Health Check
# -------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "message": "AL HADAS Ecommerce middleware is running",
    }
