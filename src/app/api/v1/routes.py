from fastapi import APIRouter

from app.api.v1.master_data import router as master_data_router
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.subjects import router as subjects_router
from app.api.v1.topics import router as topics_router
from app.api.v1.notes import router as notes_router
from app.api.v1.materials import router as materials_router
from app.api.v1.snippets import router as snippets_router
from app.api.v1.health import router as health_router

router = APIRouter()


# Include health routes
router.include_router(health_router)

# Include master data routes
router.include_router(master_data_router)

# Include auth routes
router.include_router(auth_router)

# Include users routes
router.include_router(users_router)

# Include subjects routes
router.include_router(subjects_router)

# Include topics routes
router.include_router(topics_router)

# Include notes routes
router.include_router(notes_router)

# Include materials routes
router.include_router(materials_router)

# Include snippets routes
router.include_router(snippets_router)
