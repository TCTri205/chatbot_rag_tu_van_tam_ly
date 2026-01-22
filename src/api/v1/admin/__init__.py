"""
Admin API routers initialization.
"""
from fastapi import APIRouter
from src.api.v1.admin import stats, config, knowledge, users

router = APIRouter()

# Register sub-routers
router.include_router(stats.router, prefix="/stats", tags=["Admin Stats"])
router.include_router(config.router, prefix="/config", tags=["Admin Config"])
router.include_router(knowledge.router, prefix="/knowledge", tags=["Admin Knowledge"])
router.include_router(users.router, prefix="/users", tags=["Admin Users"])
