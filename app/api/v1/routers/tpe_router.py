from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status
import json
import time

from app.integrations.langchain_client import langchain_client
from app.features.tpe.prompts import SurveyAnalysisPrompts
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/survey-analysis", tags=["Survey Analysis"])


def restructure_data(survey_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Custom function to restructure survey data for LLM processing.
    
    Args:
        survey_data: Raw survey data from the request
        
    Returns:
        Restructured data ready for LLM analysis
    """
    # Extract basic survey info
    title = survey_data.get("title", "")
    description = survey_data.get("description", "")
    
    # Extract questions
    questions = []
    for question in survey_data.get("questions", []):
        question_data = {
            "question_text": question.get("question_text", ""),
            "question_type": question.get("question_type", ""),
            "category": question.get("category", ""),
            "weight": question.get("weight", 1.0),
            "options": []
        }
        
        # Add options if they exist
        for option in question.get("options", []):
            option_data = {
                "value": option.get("value", ""),
                "label": option.get("label", ""),
                "weight": option.get("weight", 1.0)
            }
            question_data["options"].append(option_data)
        
        questions.append(question_data)
    
    # Extract answers
    answers = []
    for answer in survey_data.get("answers", []):
        answer_data = {
            "question_text": answer.get("question_text", ""),
            "selected_answer": answer.get("selected_answer", ""),
            "answer_weight": answer.get("answer_weight", 1.0),
            "category": answer.get("category", "")
        }
        answers.append(answer_data)
    
    return {
        "title": title,
        "description": description,
        "questions": questions,
        "answers": answers
    }


@router.post(
    "/process",
    status_code=status.HTTP_200_OK,
    summary="Process survey data and get category analysis",
    description="Submit survey data for AI-powered analysis. The system will categorize questions, analyze responses, and provide insights about strengths and weaknesses in each category."
)
async def process_survey_data(survey_data: Dict[str, Any]):
    """
    Process survey data and return category analysis.
    
    This endpoint:
    1. Accepts survey data with questions and answers
    2. Restructures the data for LLM processing
    3. Sends data to AI model for analysis
    4. Returns categorized insights and recommendations
    
    - **survey_data**: Survey information including questions, answers, and metadata
    """
    start_time = time.time()
    
    try:
        logger.info(
            "Survey processing started",
            survey_title=survey_data.get("title", ""),
            questions_count=len(survey_data.get("questions", [])),
            answers_count=len(survey_data.get("answers", []))
        )
        
        # Restructure survey data for LLM processing
        restructured_data = restructure_data(survey_data)
        
        # Get prompts
        system_prompt = SurveyAnalysisPrompts.get_system_prompt()
        analysis_prompt = SurveyAnalysisPrompts.get_analysis_prompt(restructured_data)
        
        # Send to LLM for analysis
        llm_response = await langchain_client.get_completion_with_retry(
            system_prompt=system_prompt,
            user_prompt=analysis_prompt,
            endpoint="survey_process"
        )
        
        # Parse LLM response
        try:
            analysis_result = json.loads(llm_response["content"])
        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM response as JSON", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to parse AI analysis response"
            )
        
        processing_time = time.time() - start_time
        
        # Prepare response
        response = {
            "status": "completed",
            "categories_analyzed": len(analysis_result.get("categories", [])),
            "category_summaries": analysis_result.get("categories", []),
            "overall_summary": analysis_result.get("overall_summary", ""),
            "processing_time": processing_time,
            "llm_model_used": llm_response.get("model", "unknown")
        }
        
        logger.info(
            "Survey processing completed successfully",
            survey_title=survey_data.get("title", ""),
            categories_analyzed=len(analysis_result.get("categories", [])),
            processing_time=processing_time
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(
            "Unexpected error in process_survey_data endpoint",
            error=str(e),
            processing_time=processing_time
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred during survey processing"
        )
