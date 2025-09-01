from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.features.tpe.models import Survey, SurveyQuestion, SurveyAnswer, SurveyAnalysis
from app.features.tpe.schemas import SurveyInput, CategoryAnalysis
from app.core.logging import get_logger

logger = get_logger(__name__)


class SurveyRepository:
    """Repository for survey-related database operations."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def create_survey(self, survey_data: SurveyInput, user_id: str) -> Survey:
        """Create a new survey with questions and answers."""
        try:
            # Create survey
            survey = Survey(
                title=survey_data.title,
                description=survey_data.description,
                user_id=user_id,
                status="pending"
            )
            self.db.add(survey)
            await self.db.flush()  # Get the survey ID
            
            # Create questions
            questions_map = {}
            for q_data in survey_data.questions:
                question = SurveyQuestion(
                    survey_id=survey.id,
                    question_text=q_data.question_text,
                    question_type=q_data.question_type,
                    category=q_data.category,
                    weight=q_data.weight,
                    options=q_data.options.dict() if q_data.options else None,
                    order_index=q_data.order_index
                )
                self.db.add(question)
                await self.db.flush()
                questions_map[q_data.order_index] = question
            
            # Create answers
            for a_data in survey_data.answers:
                # Find corresponding question
                question = next(
                    (q for q in questions_map.values() if q.order_index == a_data.question_id),
                    None
                )
                
                if question:
                    answer = SurveyAnswer(
                        question_id=question.id,
                        survey_id=survey.id,
                        user_id=user_id,
                        selected_answer=a_data.selected_answer,
                        answer_weight=a_data.answer_weight
                    )
                    self.db.add(answer)
            
            await self.db.commit()
            logger.info("Survey created successfully", survey_id=survey.id, user_id=user_id)
            return survey
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to create survey", error=str(e), user_id=user_id)
            raise
    
    async def get_survey_by_id(self, survey_id: int, user_id: str) -> Optional[Survey]:
        """Get survey by ID with all related data."""
        try:
            query = select(Survey).options(
                selectinload(Survey.questions),
                selectinload(Survey.analysis_results)
            ).where(
                Survey.id == survey_id,
                Survey.user_id == user_id
            )
            
            result = await self.db.execute(query)
            survey = result.scalar_one_or_none()
            
            if survey:
                logger.info("Survey retrieved", survey_id=survey_id, user_id=user_id)
            else:
                logger.warning("Survey not found", survey_id=survey_id, user_id=user_id)
            
            return survey
            
        except Exception as e:
            logger.error("Failed to retrieve survey", error=str(e), survey_id=survey_id)
            raise
    
    async def get_surveys_by_user(self, user_id: str, limit: int = 100, offset: int = 0) -> List[Survey]:
        """Get all surveys for a user with pagination."""
        try:
            query = select(Survey).where(
                Survey.user_id == user_id
            ).order_by(
                Survey.created_at.desc()
            ).limit(limit).offset(offset)
            
            result = await self.db.execute(query)
            surveys = result.scalars().all()
            
            logger.info("Surveys retrieved for user", user_id=user_id, count=len(surveys))
            return surveys
            
        except Exception as e:
            logger.error("Failed to retrieve surveys for user", error=str(e), user_id=user_id)
            raise
    
    async def update_survey_status(self, survey_id: int, status: str, user_id: str) -> bool:
        """Update survey status."""
        try:
            query = update(Survey).where(
                Survey.id == survey_id,
                Survey.user_id == user_id
            ).values(
                status=status,
                updated_at=datetime.utcnow()
            )
            
            result = await self.db.execute(query)
            await self.db.commit()
            
            updated = result.rowcount > 0
            if updated:
                logger.info("Survey status updated", survey_id=survey_id, status=status, user_id=user_id)
            else:
                logger.warning("Survey not found for status update", survey_id=survey_id, user_id=user_id)
            
            return updated
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to update survey status", error=str(e), survey_id=survey_id)
            raise
    
    async def create_analysis_results(self, survey_id: int, analysis_data: Dict[str, Any]) -> List[SurveyAnalysis]:
        """Create analysis results for a survey."""
        try:
            analysis_results = []
            
            for category_data in analysis_data.get("categories", []):
                analysis = SurveyAnalysis(
                    survey_id=survey_id,
                    category=category_data["category"],
                    strengths=category_data.get("strengths", []),
                    weaknesses=category_data.get("weaknesses", []),
                    recommendations=category_data.get("recommendations", []),
                    category_score=category_data.get("category_score"),
                    analysis_summary=category_data["analysis_summary"],
                    llm_model_used=analysis_data.get("llm_model_used"),
                    tokens_used=analysis_data.get("tokens_used"),
                    processing_time=analysis_data.get("processing_time")
                )
                self.db.add(analysis)
                analysis_results.append(analysis)
            
            await self.db.commit()
            logger.info("Analysis results created", survey_id=survey_id, categories_count=len(analysis_results))
            return analysis_results
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to create analysis results", error=str(e), survey_id=survey_id)
            raise
    
    async def get_analysis_results(self, survey_id: int, user_id: str) -> Optional[List[SurveyAnalysis]]:
        """Get analysis results for a survey."""
        try:
            # First verify the survey belongs to the user
            survey = await self.get_survey_by_id(survey_id, user_id)
            if not survey:
                return None
            
            query = select(SurveyAnalysis).where(
                SurveyAnalysis.survey_id == survey_id
            ).order_by(SurveyAnalysis.category)
            
            result = await self.db.execute(query)
            analyses = result.scalars().all()
            
            logger.info("Analysis results retrieved", survey_id=survey_id, count=len(analyses))
            return analyses
            
        except Exception as e:
            logger.error("Failed to retrieve analysis results", error=str(e), survey_id=survey_id)
            raise
    
    async def delete_survey(self, survey_id: int, user_id: str) -> bool:
        """Delete a survey and all related data."""
        try:
            # First verify the survey belongs to the user
            survey = await self.get_survey_by_id(survey_id, user_id)
            if not survey:
                return False
            
            # Delete survey (cascade will handle related data)
            await self.db.delete(survey)
            await self.db.commit()
            
            logger.info("Survey deleted", survey_id=survey_id, user_id=user_id)
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to delete survey", error=str(e), survey_id=survey_id)
            raise
