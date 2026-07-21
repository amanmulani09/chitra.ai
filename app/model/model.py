from pydantic import BaseModel
from typing import Dict,Any,List

class VideoData(BaseModel):
    image_base64:str
    audio_transcription:str
    timestamp:str

class CapturedData(BaseModel):
    image_data:str
    audio_transcription:str
    timestamp:str
    capture_quality:str

class AnalysisResult(BaseModel):
    visual_findings: Dict[str, str]
    audio_analysis: Dict[str, Any]
    assessment: str
    priority_level: str
    score: int
    recommendations: List[str]
    summary: str
    confidence_score: float

class AnalysisReport(BaseModel):
    session_id: str
    analysis: AnalysisResult
    captured_data: CapturedData
    report_generated_at: str
    email_sent: bool