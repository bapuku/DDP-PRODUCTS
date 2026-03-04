# API v1
from fastapi import APIRouter

from app.api.v1 import dpp, compliance, workflow, battery_passport, auth, dpp_sector, lifecycle, ml, human_review, agents_registry, system_assistant, connectors, blockchain

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(lifecycle.router, prefix="/dpp", tags=["dpp-lifecycle"])
router.include_router(dpp.router, prefix="/dpp", tags=["dpp"])
router.include_router(battery_passport.router, prefix="/dpp/battery", tags=["battery-passport"])
router.include_router(dpp_sector.router, prefix="/dpp/sector", tags=["dpp-sector"])
router.include_router(compliance.router, prefix="/compliance", tags=["compliance"])
router.include_router(workflow.router, prefix="/workflow", tags=["workflow"])
router.include_router(human_review.router, prefix="/human-review", tags=["human-review"])
router.include_router(ml.router, prefix="/ml", tags=["ml"])
router.include_router(agents_registry.router, prefix="/agents", tags=["agents-registry"])
router.include_router(system_assistant.router, prefix="/assistant", tags=["system-assistant"])
router.include_router(connectors.router, prefix="/connectors", tags=["connectors"])
router.include_router(blockchain.router, prefix="/blockchain", tags=["blockchain"])
