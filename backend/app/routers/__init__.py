"""
Routers da API
"""

from .licenses import router as licenses_router
from .admin import router as admin_router
from .auth import router as auth_router
from .payments import router as payments_router
from .user_dashboard import router as user_dashboard_router
from .economic_indexes import router as economic_indexes_router
from .notifications import router as notifications_router
from .jobs import router as jobs_router

__all__ = [
    "licenses_router",
    "admin_router",
    "auth_router",
    "payments_router",
    "user_dashboard_router",
    "economic_indexes_router",
    "notifications_router",
    "jobs_router",
]

