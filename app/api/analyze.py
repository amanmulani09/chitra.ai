from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.agents.workflow import process_video_analysis_workflow
from app.config import logger, templates
from app.models.schemas import VideoData

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request, "index.html")
@router.post("/analyze")
async def analyze_video_data(data: VideoData):
    """Main endpoint for video data analysis using multi-agent workflow"""
    try:
        logger.info("Starting multi-agent video analysis workflow")
        # Run the workflow pipeline
        analysis_report = await process_video_analysis_workflow(
            data.image_base64,
            data.audio_transcription,
            data.timestamp
        )
        # Return comprehensive response
        return {
            "analysis": analysis_report.analysis.model_dump(),
            "transcription": analysis_report.captured_data.audio_transcription,
            "email_sent": analysis_report.email_sent,
            "timestamp": analysis_report.report_generated_at,
            "session_id": analysis_report.session_id,
            "workflow_status": "completed",
            "priority_level": analysis_report.analysis.priority_level,
            "score": analysis_report.analysis.score
        }
    except Exception as e:
        logger.error(f"Workflow error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis workflow failed: {str(e)}")