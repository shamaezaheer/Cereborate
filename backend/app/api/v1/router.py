from fastapi import APIRouter

from app.api.v1.auth import router as auth_router

router = APIRouter()

router.include_router(auth_router)

# Phase 2+ routers will be added here:
# from app.api.v1.planning import router as planning_router
# from app.api.v1.ideas import router as ideas_router
# from app.api.v1.components import router as components_router
# from app.api.v1.budget import router as budget_router
# from app.api.v1.links import router as links_router
# from app.api.v1.dependencies import router as dependencies_router
# from app.api.v1.consistency import router as consistency_router
# from app.api.v1.shareability import router as shareability_router
# from app.api.v1.team import router as team_router
