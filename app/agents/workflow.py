from app.agents.data_capture import DataCaptureAgent
from app.agents.report import ReportAgent
from app.agents.analysis import AnalysisAgent
from app.models.schemas import AnalysisReport

# Initialize Agents
data_capture_agent = DataCaptureAgent()
analysis_agent = AnalysisAgent()
report_agent = ReportAgent()
# Simple Async Workflow Pipeline
async def process_video_analysis_workflow(image_base64: str, audio_base64: str, timestamp: str) -> AnalysisReport:
    """Process video analysis workflow through all agents"""
    # Step 1: Capture and process data
    captured_data = await data_capture_agent.capture_and_process(
        image_base64,
        audio_base64,
        timestamp
    )
    # Step 2: Analyze and prioritize
    analysis_result = await analysis_agent.analyze_and_prioritize(captured_data)
    # Step 3: Generate and send report
    analysis_report = await report_agent.generate_and_send_report(
        analysis_result,
        captured_data
    )
    return analysis_report