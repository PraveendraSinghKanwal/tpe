import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.features.survey_analysis.schemas import SurveyInput, CategoryAnalysis, SurveyAnalysisResponse
from app.features.survey_analysis.prompts import SurveyAnalysisPrompts
from app.integrations.langchain_client import langchain_client
from app.core.logging import get_logger
from app.config import settings

logger = get_logger(__name__)


class SurveyAnalysisService:
    """Service layer for survey analysis business logic."""
    
    def __init__(self):
        self.prompts = SurveyAnalysisPrompts()
    
    def restructure_survey_data(self, survey_data: SurveyInput) -> Dict[str, Any]:
        """
        Restructure survey data for LLM analysis.
        
        Args:
            survey_data: Input survey data
            
        Returns:
            Restructured data optimized for LLM processing
        """
        try:
            # Group questions by category
            categories = {}
            for question in survey_data.questions:
                category = question.category
                if category not in categories:
                    categories[category] = []
                
                # Find corresponding answer
                answer = next(
                    (a for a in survey_data.answers if a.question_id == question.order_index),
                    None
                )
                
                if answer:
                    categories[category].append({
                        "question": question.question_text,
                        "question_type": question.question_type,
                        "question_weight": question.weight,
                        "selected_answer": answer.selected_answer,
                        "answer_weight": answer.answer_weight,
                        "options": question.options.dict() if question.options else None
                    })
            
            # Create restructured data
            restructured_data = {
                "title": survey_data.title,
                "description": survey_data.description,
                "total_questions": len(survey_data.questions),
                "categories": categories,
                "analysis_request": {
                    "focus_areas": list(categories.keys()),
                    "total_categories": len(categories)
                }
            }
            
            logger.info("Survey data restructured", categories_count=len(categories))
            return restructured_data
            
        except Exception as e:
            logger.error("Failed to restructure survey data", error=str(e))
            raise
    
    async def analyze_survey_with_llm(self, restructured_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze survey data using LLM.
        
        Args:
            restructured_data: Restructured survey data
            
        Returns:
            LLM analysis results
        """
        try:
            start_time = time.time()
            
            # Get prompts
            system_prompt = self.prompts.get_system_prompt()
            analysis_prompt = self.prompts.get_analysis_prompt(restructured_data)
            
            # Get LLM completion
            llm_response = await langchain_client.get_completion_with_retry(
                system_prompt=system_prompt,
                user_prompt=analysis_prompt,
                endpoint="survey_analysis"
            )
            
            # Parse LLM response
            try:
                analysis_result = json.loads(llm_response["content"])
            except json.JSONDecodeError as e:
                logger.error("Failed to parse LLM response as JSON", error=str(e))
                # Try to extract JSON from the response
                content = llm_response["content"]
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_content = content[start_idx:end_idx]
                    analysis_result = json.loads(json_content)
                else:
                    raise ValueError("Could not extract valid JSON from LLM response")
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Add metadata
            analysis_result.update({
                "llm_model_used": settings.openai_model,
                "tokens_used": llm_response.get("total_tokens", 0),
                "processing_time": processing_time,
                "analysis_timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(
                "Survey analysis completed",
                processing_time=processing_time,
                tokens_used=llm_response.get("total_tokens", 0),
                categories_count=len(analysis_result.get("categories", []))
            )
            
            return analysis_result
            
        except Exception as e:
            logger.error("Failed to analyze survey with LLM", error=str(e))
            raise
    
    def validate_analysis_result(self, analysis_result: Dict[str, Any]) -> bool:
        """
        Validate LLM analysis result structure.
        
        Args:
            analysis_result: Analysis result from LLM
            
        Returns:
            True if valid, False otherwise
        """
        try:
            required_fields = ["categories", "overall_summary"]
            
            # Check required fields
            for field in required_fields:
                if field not in analysis_result:
                    logger.error(f"Missing required field in analysis result: {field}")
                    return False
            
            # Validate categories structure
            categories = analysis_result.get("categories", [])
            if not isinstance(categories, list) or len(categories) == 0:
                logger.error("Invalid categories structure in analysis result")
                return False
            
            # Validate each category
            for category in categories:
                if not isinstance(category, dict):
                    logger.error("Invalid category structure in analysis result")
                    return False
                
                required_category_fields = ["category", "analysis_summary"]
                for field in required_category_fields:
                    if field not in category:
                        logger.error(f"Missing required field in category: {field}")
                        return False
            
            logger.info("Analysis result validation successful")
            return True
            
        except Exception as e:
            logger.error("Failed to validate analysis result", error=str(e))
            return False
    
    def format_analysis_response(
        self,
        survey_id: int,
        analysis_result: Dict[str, Any]
    ) -> SurveyAnalysisResponse:
        """
        Format analysis result into response schema.
        
        Args:
            survey_id: Survey ID
            analysis_result: Analysis result from LLM
            
        Returns:
            Formatted response
        """
        try:
            # Extract category analyses
            category_analyses = []
            for category_data in analysis_result.get("categories", []):
                category_analysis = CategoryAnalysis(
                    category=category_data["category"],
                    strengths=category_data.get("strengths", []),
                    weaknesses=category_data.get("weaknesses", []),
                    recommendations=category_data.get("recommendations", []),
                    category_score=category_data.get("category_score"),
                    analysis_summary=category_data["analysis_summary"]
                )
                category_analyses.append(category_analysis)
            
            # Create response
            response = SurveyAnalysisResponse(
                survey_id=survey_id,
                status="completed",
                categories_analyzed=len(category_analyses),
                category_analyses=category_analyses,
                overall_summary=analysis_result.get("overall_summary", ""),
                processing_time=analysis_result.get("processing_time", 0.0),
                llm_model_used=analysis_result.get("llm_model_used", ""),
                tokens_used=analysis_result.get("tokens_used", 0),
                created_at=datetime.utcnow()
            )
            
            logger.info("Analysis response formatted successfully", survey_id=survey_id)
            return response
            
        except Exception as e:
            logger.error("Failed to format analysis response", error=str(e), survey_id=survey_id)
            raise
    
    async def process_survey_analysis(self, survey_data: SurveyInput) -> Dict[str, Any]:
        """
        Complete survey analysis process.
        
        Args:
            survey_data: Input survey data
            
        Returns:
            Complete analysis results
        """
        try:
            logger.info("Starting survey analysis process")
            
            # Step 1: Restructure data
            restructured_data = self.restructure_survey_data(survey_data)
            
            # Step 2: Analyze with LLM
            analysis_result = await self.analyze_survey_with_llm(restructured_data)
            
            # Step 3: Validate result
            if not self.validate_analysis_result(analysis_result):
                raise ValueError("LLM analysis result validation failed")
            
            logger.info("Survey analysis process completed successfully")
            return analysis_result
            
        except Exception as e:
            logger.error("Survey analysis process failed", error=str(e))
            raise
