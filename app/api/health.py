from fastapi import APIRouter

# FastAPI Endpoints


router = APIRouter()

@router.router("/health")
async def health_check():
    """Enhanced health check endpoint"""
    services_status = {
        "openai": "configured" if OPENAI_API_KEY else "not configured",
        "sendgrid": "configured" if SENDGRID_API_KEY else "not configured",
        "agents": {
            "data_capture": "active",
            "analysis": "active",
            "report": "active"
        }
    }
    # Test OpenAI connection
    try:
        if OPENAI_API_KEY:
            test_response = await openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            services_status["openai"] = "connected"
    except Exception as e:
        services_status["openai"] = f"error: {str(e)}"
    return {
        "status": "healthy",
        "services": services_status,
        "workflow": "multi-agent system operational",
        "version": "2.0.0"
    }