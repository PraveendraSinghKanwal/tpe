from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_db
from app.core.security.okta_auth import get_current_user, require_scope
from app.features.tpe.schemas import (
    SurveyInput,
    SurveyAnalysisResponse,
    SurveyStatusResponse,
    ErrorResponse
)
from app.features.tpe.controller import SurveyAnalysisController
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/survey-analysis", tags=["Survey Analysis"])


@router.post(
    "/analyze",
    response_model=SurveyAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Analyze survey data using AI",
    description="Submit survey data for AI-powered analysis. The system will categorize questions, analyze responses, and provide insights about strengths and weaknesses in each category."
)
async def analyze_survey(
    survey_data: SurveyInput,
    current_user: Dict[str, Any] = Depends(require_scope("survey:analyze")),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Analyze survey data using AI.
    
    This endpoint:
    1. Accepts survey data with questions and answers
    2. Restructures the data for LLM processing
    3. Sends data to AI model for analysis
    4. Returns categorized insights and recommendations
    
    - **survey_data**: Survey information including questions, answers, and metadata
    - **Authentication**: Requires valid Okta JWT token with 'survey:analyze' scope
    """
    try:
        controller = SurveyAnalysisController(db)
        result = await controller.analyze_survey(survey_data, current_user["sub"])
        
        logger.info(
            "Survey analysis endpoint called successfully",
            user_id=current_user["sub"],
            survey_title=survey_data.title
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Unexpected error in analyze_survey endpoint",
            error=str(e),
            user_id=current_user["sub"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred during survey analysis"
        )


@router.get(
    "/{survey_id}",
    response_model=SurveyAnalysisResponse,
    summary="Get survey analysis results",
    description="Retrieve the analysis results for a specific survey. The survey must be in 'completed' status."
)
async def get_survey_analysis(
    survey_id: int,
    current_user: Dict[str, Any] = Depends(require_scope("survey:read")),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get survey analysis results.
    
    - **survey_id**: ID of the survey to retrieve
    - **Authentication**: Requires valid Okta JWT token with 'survey:read' scope
    - **Returns**: Complete analysis results if survey is completed
    """
    try:
        controller = SurveyAnalysisController(db)
        result = await controller.get_survey_analysis(survey_id, current_user["sub"])
        
        logger.info(
            "Survey analysis retrieved successfully",
            survey_id=survey_id,
            user_id=current_user["sub"]
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Unexpected error in get_survey_analysis endpoint",
            error=str(e),
            survey_id=survey_id,
            user_id=current_user["sub"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving analysis"
        )


@router.get(
    "/{survey_id}/status",
    response_model=SurveyStatusResponse,
    summary="Get survey processing status",
    description="Check the current status of a survey analysis (pending, processing, completed, or failed)."
)
async def get_survey_status(
    survey_id: int,
    current_user: Dict[str, Any] = Depends(require_scope("survey:read")),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get survey processing status.
    
    - **survey_id**: ID of the survey to check
    - **Authentication**: Requires valid Okta JWT token with 'survey:read' scope
    - **Returns**: Current status and progress information
    """
    try:
        controller = SurveyAnalysisController(db)
        result = await controller.get_survey_status(survey_id, current_user["sub"])
        
        logger.info(
            "Survey status retrieved successfully",
            survey_id=survey_id,
            user_id=current_user["sub"],
            status=result.status
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Unexpected error in get_survey_status endpoint",
            error=str(e),
            survey_id=survey_id,
            user_id=current_user["sub"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving status"
        )


@router.get(
    "/",
    response_model=List[Dict[str, Any]],
    summary="Get user's surveys",
    description="Retrieve a list of all surveys for the authenticated user with pagination support."
)
async def get_user_surveys(
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of surveys to return"),
    offset: int = Query(default=0, ge=0, description="Number of surveys to skip"),
    current_user: Dict[str, Any] = Depends(require_scope("survey:read")),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get user's surveys.
    
    - **limit**: Maximum number of surveys to return (1-1000)
    - **offset**: Number of surveys to skip for pagination
    - **Authentication**: Requires valid Okta JWT token with 'survey:read' scope
    - **Returns**: List of survey summaries
    """
    try:
        controller = SurveyAnalysisController(db)
        result = await controller.get_user_surveys(current_user["sub"], limit, offset)
        
        logger.info(
            "User surveys retrieved successfully",
            user_id=current_user["sub"],
            count=len(result),
            limit=limit,
            offset=offset
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Unexpected error in get_user_surveys endpoint",
            error=str(e),
            user_id=current_user["sub"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving surveys"
        )


@router.delete(
    "/{survey_id}",
    response_model=Dict[str, str],
    summary="Delete survey",
    description="Delete a survey and all its associated data. This action cannot be undone."
)
async def delete_survey(
    survey_id: int,
    current_user: Dict[str, Any] = Depends(require_scope("survey:delete")),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete survey.
    
    - **survey_id**: ID of the survey to delete
    - **Authentication**: Requires valid Okta JWT token with 'survey:delete' scope
    - **Returns**: Success message
    - **Warning**: This action permanently deletes the survey and all related data
    """
    try:
        controller = SurveyAnalysisController(db)
        result = await controller.delete_survey(survey_id, current_user["sub"])
        
        logger.info(
            "Survey deleted successfully",
            survey_id=survey_id,
            user_id=current_user["sub"]
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Unexpected error in delete_survey endpoint",
            error=str(e),
            survey_id=survey_id,
            user_id=current_user["sub"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while deleting survey"
        )
