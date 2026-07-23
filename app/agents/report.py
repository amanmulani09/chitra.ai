# Agent 3: Report Generation and Communication Agent
from datetime import datetime

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.config import FROM_EMAIL, RECIPIENT_EMAIL, SENDGRID_API_KEY, logger
from app.models.schemas import AnalysisReport, AnalysisResult, CapturedData


class ReportAgent:
    def __init__(self):
        self.name = "ReportAgent"
    def generate_html_report(self, analysis: AnalysisResult, captured_data: CapturedData, session_id: str = "Unknown") -> str:
        """Generate comprehensive HTML report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Priority color coding
        priority_colors = {
            "low": "#4caf50",
            "medium": "#ff9800",
            "high": "#f44336",
            "critical": "#d32f2f"
        }
        priority_color = priority_colors.get(analysis.priority_level, "#757575")
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f5f5f5; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
                .priority-badge {{
                    background-color: {priority_color};
                    color: white;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }}
                .section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #2196f3; background-color: #f9f9f9; }}
                .urgent {{ border-left-color: #f44336; background-color: #ffebee; }}
                .finding {{ margin: 10px 0; padding: 10px; background-color: white; border-radius: 4px; }}
                .confidence {{ font-size: 0.9em; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎥 AI Video Analysis Report</h1>
                <p><strong>Session ID:</strong> {session_id}</p>
                <p><strong>Generated:</strong> {timestamp}</p>
                <p><strong>Priority Level:</strong> <span class="priority-badge">{analysis.priority_level.upper()}</span></p>
                <p><strong>Score:</strong> {analysis.score}/10</p>
                <p><strong>Confidence:</strong> <span class="confidence">{analysis.confidence_score:.1%}</span></p>
            </div>
            <div class="section {'urgent' if analysis.score >= 7 else ''}">
                <h2>🔍 Visual Analysis</h2>
                <div class="finding"><strong>Appearance:</strong> {analysis.visual_findings.get('appearance', 'N/A')}</div>
                <div class="finding"><strong>Behavior Patterns:</strong> {analysis.visual_findings.get('behavior_patterns', 'N/A')}</div>
                <div class="finding"><strong>Movement:</strong> {analysis.visual_findings.get('movement', 'N/A')}</div>
                <div class="finding"><strong>General State:</strong> {analysis.visual_findings.get('general_state', 'N/A')}</div>
                <div class="finding"><strong>Expressions:</strong> {analysis.visual_findings.get('expressions', 'N/A')}</div>
            </div>
            <div class="section">
                <h2>🎤 Audio Analysis</h2>
                <div class="finding"><strong>Transcription:</strong> "{captured_data.audio_transcription}"</div>
                <div class="finding"><strong>Key Topics:</strong> {', '.join(analysis.audio_analysis.get('key_topics', []))}</div>
                <div class="finding"><strong>Sentiment:</strong> {analysis.audio_analysis.get('sentiment', 'N/A')}</div>
                <div class="finding"><strong>Temporal Info:</strong> {analysis.audio_analysis.get('temporal_info', 'N/A')}</div>
                <div class="finding"><strong>Context:</strong> {analysis.audio_analysis.get('context', 'N/A')}</div>
                <div class="finding"><strong>Voice Notes:</strong> {analysis.audio_analysis.get('voice_notes', 'N/A')}</div>
            </div>
            <div class="section {'urgent' if analysis.assessment == 'high' else ''}">
                <h2>⚠️ Assessment</h2>
                <div class="finding">
                    <strong>Overall Assessment:</strong>
                    <span style="color: {'red' if analysis.assessment == 'high' else 'orange' if analysis.assessment == 'moderate' else 'green'}">
                        {analysis.assessment.upper()}
                    </span>
                </div>
            </div>
            <div class="section">
                <h2>📋 Recommendations</h2>
                <ul>
                    {''.join(f'<li>{action}</li>' for action in analysis.recommendations)}
                </ul>
            </div>
            <div class="section">
                <h2>📝 Summary</h2>
                <p>{analysis.summary}</p>
            </div>
            <div class="section">
                <h2>📊 Technical Details</h2>
                <div class="finding"><strong>Capture Quality:</strong> {captured_data.capture_quality}</div>
                <div class="finding"><strong>Analysis Timestamp:</strong> {captured_data.timestamp}</div>
                <div class="finding"><strong>Model Confidence:</strong> {analysis.confidence_score:.1%}</div>
            </div>
            <hr style="margin: 30px 0;">
            <p style="font-size: 0.9em; color: #666;">
                <em>🤖 This report was generated by an AI video analysis system using OpenAI GPT-4 Vision and Whisper transcription.</em>
            </p>
        </body>
        </html>
        """
        return html_content
    
    async def send_report(self, analysis: AnalysisResult, captured_data: CapturedData, session_id: str = "Unknown") -> bool:
        """Send report via SendGrid"""
        try:
            if not SENDGRID_API_KEY or not RECIPIENT_EMAIL:
                logger.warning("SendGrid API key or recipient email not configured")
                return False
            html_content = self.generate_html_report(analysis, captured_data, session_id)
            # Subject line with priority indicators
            subject_prefix = "🚨 CRITICAL" if analysis.priority_level == "critical" else \
                           "⚠️ HIGH PRIORITY" if analysis.priority_level == "high" else \
                           "📋 MEDIUM PRIORITY" if analysis.priority_level == "medium" else \
                           "ℹ️ LOW PRIORITY"
            subject = f"{subject_prefix} - AI Video Analysis Alert - Score {analysis.score}/10"
            message = Mail(
                from_email=FROM_EMAIL,
                to_emails=RECIPIENT_EMAIL,
                subject=subject,
                html_content=html_content
            )
            sg = SendGridAPIClient(api_key=SENDGRID_API_KEY)
            response = sg.send(message)
            success = response.status_code == 202
            if success:
                logger.info(f"Report sent successfully for {session_id}")
            else:
                logger.error(f"Failed to send report: {response.status_code}")
            return success
        except Exception as e:
            logger.error(f"Email sending error: {str(e)}")
            return False
        

    async def generate_and_send_report(self, analysis_result: AnalysisResult, captured_data: CapturedData) -> AnalysisReport:
        """Main report generation and sending function"""
        logger.info("Starting report generation and communication")
        session_id = "Session-" + datetime.now().strftime("%Y%m%d-%H%M%S")
        # Always send email
        email_sent = await self.send_report(
            analysis_result,
            captured_data,
            session_id
        )
        # Create analysis report
        analysis_report = AnalysisReport(
            session_id=session_id,
            analysis=analysis_result,
            captured_data=captured_data,
            report_generated_at=datetime.now().isoformat(),
            email_sent=email_sent
        )
        logger.info(f"Report generation completed - Email sent: {email_sent}")
        return analysis_report