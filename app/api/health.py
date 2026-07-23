from fastapi import APIRouter

from app.config import OPENAI_API_KEY, SENDGRID_API_KEY

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check. Cheap and dependency-free so load balancers can poll it
    often — it does not make any billed API calls."""
    return {
        "status": "healthy",
        "services": {
            "openai": "configured" if OPENAI_API_KEY else "not_configured",
            "sendgrid": "configured" if SENDGRID_API_KEY else "not_configured",
        },
    }
