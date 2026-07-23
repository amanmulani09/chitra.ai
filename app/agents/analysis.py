# Agent 2: Analysis and Priority Assessment Agent
import json
from typing import Any, Dict

from app.config import logger, openai_client
from app.models.schemas import CapturedData, AnalysisResult


class AnalysisAgent:
    def __init__(self):
        self.name = "AnalysisAgent"
        self.model = "gpt-4o"  # Best model for vision + text analysis
    def get_analysis_prompt(self, transcription: str) -> str:
        return f"""
            You are an AI assistant analyzing visual and audio data.
            TRANSCRIBED SPEECH: "{transcription}"
            Analyze the provided image and transcribed speech comprehensively:
            VISUAL ASSESSMENT:
            - Appearance and presentation
            - Visible conditions or characteristics
            - Movement and behavior patterns
            - General demeanor and state
            - Expressions and non-verbal cues
            AUDIO ASSESSMENT:
            - Key topics and themes discussed
            - Sentiment and tone
            - Temporal information (when, how long)
            - Context and background information
            - Voice characteristics and quality
            ASSESSMENT AND SCORING:
            - Score (1-10, where 10 is highest priority)
            - Priority level (low/medium/high/critical)
            - Overall assessment (low/moderate/high)
            Provide your analysis in this exact JSON format:
            {{
            "visual_findings": {{
                "appearance": "detailed description",
                "behavior_patterns": "detailed assessment",
                "movement": "detailed evaluation",
                "general_state": "comprehensive description",
                "expressions": "non-verbal indicators"
            }},
            "audio_analysis": {{
                "key_topics": ["list of main topics"],
                "sentiment": "sentiment and tone analysis",
                "temporal_info": "timing and duration details",
                "context": "contextual information",
                "voice_notes": "observations about speech patterns"
            }},
            "assessment": "low/moderate/high",
            "priority_level": "low/medium/high/critical",
            "score": 1-10,
            "recommendations": ["specific recommendations"],
            "summary": "concise summary integrating visual and audio findings",
            "confidence_score": 0.0-1.0,
            "flags": ["list any concerning findings requiring attention"]
            }}
            Be thorough and objective in your assessment.
            """
    async def analyze_with_openai(self, image_base64: str, transcription: str) -> Dict[str, Any]:
        """Analyze data using OpenAI GPT-4 Vision"""
        try:
            # Prepare the image for OpenAI API
            base64_data = image_base64
            if 'data:image' not in base64_data:
                base64_data = f"data:image/jpeg;base64,{image_base64}"

            response = await openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": self.get_analysis_prompt(transcription)
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": base64_data,
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1500,
                temperature=0.2
            )

            # Parse JSON response
            content = response.choices[0].message.content

            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            analysis_dict = json.loads(content)
            return analysis_dict

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            raise ValueError(f"Failed to parse AI response: {str(e)}")
        except Exception as e:
            logger.error(f"Analysis error: {str(e)}")
            raise ValueError(f"Analysis failed: {str(e)}")
        
    async def analyze_and_prioritize(self, captured_data: CapturedData) -> AnalysisResult:
        """Main analysis and prioritization function"""
        logger.info("Starting health analysis and prioritization")
        # Perform OpenAI analysis
        analysis_data = await self.analyze_with_openai(
            captured_data.image_data,
            captured_data.audio_transcription
        )
        # Create analysis result
        analysis_result = AnalysisResult(
            visual_findings=analysis_data.get("visual_findings", {}),
            audio_analysis=analysis_data.get("audio_analysis", {}),
            assessment=analysis_data.get("assessment", "moderate"),
            priority_level=analysis_data.get("priority_level", "medium"),
            score=analysis_data.get("score", 5),
            recommendations=analysis_data.get("recommendations", []),
            summary=analysis_data.get("summary", "Analysis completed"),
            confidence_score=analysis_data.get("confidence_score", 0.8)
        )
        logger.info(f"Analysis completed - Priority: {analysis_result.priority_level}, Score: {analysis_result.score}")
        return analysis_result