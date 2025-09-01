from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.tpe.schemas import (
    SurveyInput,
    SurveyAnalysisResponse,
    SurveyStatusResponse,
    ErrorResponse
)
from app.features.tpe.services import SurveyAnalysisService
from app.features.tpe.repository import SurveyRepository
from app.core.logging import get_logger

logger = get_logger(__name__)


class SurveyAnalysisController:
    """Controller layer for survey analysis operations."""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.repository = SurveyRepository(db_session)
        self.service = SurveyAnalysisService()
    
    async def analyze_survey(
        self,
        survey_data: SurveyInput,
        user_id: str
    ) -> SurveyAnalysisResponse:
        """
        Analyze survey data and return results.
        
        Args:
            survey_data: Input survey data
            user_id: Authenticated user ID
            
        Returns:
            Survey analysis response
        """
        try:
            logger.info("Starting survey analysis", user_id=user_id)
            
            # Step 1: Create survey in database
            survey = await self.repository.create_survey(survey_data, user_id)
            
            # Step 2: Update status to processing
            await self.repository.update_survey_status(survey.id, "processing", user_id)
            
            try:
                # Step 3: Process survey analysis
                analysis_result = await self.service.process_survey_analysis(survey_data)
                
                # Step 4: Store analysis results
                await self.repository.create_analysis_results(survey.id, analysis_result)
                
                # Step 5: Update status to completed
                await self.repository.update_survey_status(survey.id, "completed", user_id)
                
                # Step 6: Format and return response
                response = self.service.format_analysis_response(survey.id, analysis_result)
                
                logger.info(
                    "Survey analysis completed successfully",
                    survey_id=survey.id,
                    user_id=user_id
                )
                
                return response
                
            except Exception as e:
                # Update status to failed
                await self.repository.update_survey_status(survey.id, "failed", user_id)
                logger.error(
                    "Survey analysis failed",
                    survey_id=survey.id,
                    user_id=user_id,
                    error=str(e)
                )
                raise
                
        except Exception as e:
            logger.error("Survey analysis controller error", error=str(e), user_id=user_id)
            if "LLM analysis result validation failed" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="AI analysis failed to generate valid results. Please try again."
                )
            elif "Could not extract valid JSON" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="AI analysis generated invalid response format. Please try again."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Survey analysis failed. Please try again later."
                )
    
    async def get_survey_analysis(
        self,
        survey_id: int,
        user_id: str
    ) -> SurveyAnalysisResponse:
        """
        Get existing survey analysis results.
        
        Args:
            survey_id: Survey ID
            user_id: Authenticated user ID
            
        Returns:
            Survey analysis response
        """
        try:
            # Get survey and analysis results
            survey = await self.repository.get_survey_by_id(survey_id, user_id)
            if not survey:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Survey not found"
                )
            
            if survey.status != "completed":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Survey analysis is not complete. Current status: {survey.status}"
                )
            
            # Get analysis results
            analysis_results = await self.repository.get_analysis_results(survey_id, user_id)
            if not analysis_results:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Analysis results not found"
                )
            
            # Format response
            category_analyses = []
            for analysis in analysis_results:
                from app.features.tpe.schemas import CategoryAnalysis
                category_analysis = CategoryAnalysis(
                    category=analysis.category,
                    strengths=analysis.strengths or [],
                    weaknesses=analysis.weaknesses or [],
                    recommendations=analysis.recommendations or [],
                    category_score=analysis.category_score,
                    analysis_summary=analysis.analysis_summary
                )
                category_analyses.append(category_analysis)
            
            response = SurveyAnalysisResponse(
                survey_id=survey_id,
                status=survey.status,
                categories_analyzed=len(category_analyses),
                category_analyses=category_analyses,
                overall_summary="",  # Would need to be stored separately or calculated
                processing_time=0.0,  # Would need to be stored separately
                llm_model_used=analysis_results[0].llm_model_used or "",
                tokens_used=analysis_results[0].tokens_used or 0,
                created_at=analysis_results[0].created_at
            )
            
            logger.info("Survey analysis retrieved", survey_id=survey_id, user_id=user_id)
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get survey analysis", error=str(e), survey_id=survey_id, user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve survey analysis"
            )
    
    async def get_survey_status(
        self,
        survey_id: int,
        user_id: str
    ) -> SurveyStatusResponse:
        """
        Get survey processing status.
        
        Args:
            survey_id: Survey ID
            user_id: Authenticated user ID
            
        Returns:
            Survey status response
        """
        try:
            survey = await self.repository.get_survey_by_id(survey_id, user_id)
            if not survey:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Survey not found"
                )
            
            # Calculate progress based on status
            progress = None
            if survey.status == "completed":
                progress = 100.0
            elif survey.status == "processing":
                progress = 50.0
            elif survey.status == "pending":
                progress = 0.0
            elif survey.status == "failed":
                progress = 0.0
            
            response = SurveyStatusResponse(
                survey_id=survey_id,
                status=survey.status,
                progress=progress,
                estimated_completion=None,  # Could be calculated based on queue position
                message=self._get_status_message(survey.status)
            )
            
            logger.info("Survey status retrieved", survey_id=survey_id, user_id=user_id, status=survey.status)
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get survey status", error=str(e), survey_id=survey_id, user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve survey status"
            )
    
    async def get_user_surveys(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get all surveys for a user.
        
        Args:
            user_id: Authenticated user ID
            limit: Maximum number of surveys to return
            offset: Number of surveys to skip
            
        Returns:
            List of survey summaries
        """
        try:
            surveys = await self.repository.get_surveys_by_user(user_id, limit, offset)
            
            survey_summaries = []
            for survey in surveys:
                summary = {
                    "id": survey.id,
                    "title": survey.title,
                    "description": survey.description,
                    "status": survey.status,
                    "created_at": survey.created_at,
                    "updated_at": survey.updated_at
                }
                survey_summaries.append(summary)
            
            logger.info("User surveys retrieved", user_id=user_id, count=len(survey_summaries))
            return survey_summaries
            
        except Exception as e:
            logger.error("Failed to get user surveys", error=str(e), user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve user surveys"
            )
    
    async def delete_survey(
        self,
        survey_id: int,
        user_id: str
    ) -> Dict[str, str]:
        """
        Delete a survey and all related data.
        
        Args:
            survey_id: Survey ID
            user_id: Authenticated user ID
            
        Returns:
            Success message
        """
        try:
            deleted = await self.repository.delete_survey(survey_id, user_id)
            if not deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Survey not found"
                )
            
            logger.info("Survey deleted", survey_id=survey_id, user_id=user_id)
            return {"message": "Survey deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to delete survey", error=str(e), survey_id=survey_id, user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete survey"
            )
    
    def _get_status_message(self, status: str) -> str:
        """Get human-readable status message."""
        status_messages = {
            "pending": "Survey is queued for analysis",
            "processing": "Survey is being analyzed by AI",
            "completed": "Survey analysis is complete",
            "failed": "Survey analysis failed"
        }
        return status_messages.get(status, "Unknown status")
