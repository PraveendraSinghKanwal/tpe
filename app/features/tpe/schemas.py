from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class QuestionOption(BaseModel):
    """Schema for question options in multiple choice questions."""
    value: str = Field(..., description="Option value")
    label: str = Field(..., description="Option label")
    weight: float = Field(default=1.0, description="Option weight")


class SurveyQuestionInput(BaseModel):
    """Input schema for survey questions."""
    question_text: str = Field(..., description="Question text", min_length=1)
    question_type: str = Field(..., description="Question type (multiple_choice, text, rating)")
    category: str = Field(..., description="Question category", min_length=1)
    weight: float = Field(default=1.0, description="Question weight", ge=0.0)
    options: Optional[List[QuestionOption]] = Field(None, description="Options for multiple choice questions")
    order_index: int = Field(default=0, description="Question order")
    
    @validator('options')
    def validate_options(cls, v, values):
        if values.get('question_type') == 'multiple_choice' and not v:
            raise ValueError("Options are required for multiple choice questions")
        return v


class SurveyAnswerInput(BaseModel):
    """Input schema for survey answers."""
    question_id: int = Field(..., description="Question ID")
    selected_answer: str = Field(..., description="Selected answer", min_length=1)
    answer_weight: float = Field(default=1.0, description="Answer weight", ge=0.0)


class SurveyInput(BaseModel):
    """Input schema for survey analysis request."""
    title: str = Field(..., description="Survey title", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Survey description")
    questions: List[SurveyQuestionInput] = Field(..., description="Survey questions", min_items=1)
    answers: List[SurveyAnswerInput] = Field(..., description="User answers", min_items=1)
    
    @validator('answers')
    def validate_answers_match_questions(cls, v, values):
        if 'questions' in values:
            question_ids = {q.get('question_id') for q in values['questions']}
            answer_question_ids = {a.get('question_id') for a in v}
            
            if not answer_question_ids.issubset(question_ids):
                raise ValueError("All answers must correspond to existing questions")
            
            if len(v) != len(values['questions']):
                raise ValueError("Number of answers must match number of questions")
        
        return v


class CategoryAnalysis(BaseModel):
    """Schema for category analysis results."""
    category: str = Field(..., description="Question category")
    strengths: List[str] = Field(..., description="Identified strengths")
    weaknesses: List[str] = Field(..., description="Identified weaknesses")
    recommendations: List[str] = Field(..., description="Recommendations for improvement")
    category_score: Optional[float] = Field(None, description="Numerical score for the category")
    analysis_summary: str = Field(..., description="Detailed analysis summary")


class SurveyAnalysisResponse(BaseModel):
    """Response schema for survey analysis."""
    survey_id: int = Field(..., description="Survey ID")
    status: str = Field(..., description="Analysis status")
    categories_analyzed: int = Field(..., description="Number of categories analyzed")
    category_analyses: List[CategoryAnalysis] = Field(..., description="Analysis results by category")
    overall_summary: str = Field(..., description="Overall analysis summary")
    processing_time: float = Field(..., description="Total processing time in seconds")
    llm_model_used: str = Field(..., description="LLM model used for analysis")
    tokens_used: int = Field(..., description="Total tokens used")
    created_at: datetime = Field(..., description="Analysis completion timestamp")


class SurveyStatusResponse(BaseModel):
    """Response schema for survey status."""
    survey_id: int = Field(..., description="Survey ID")
    status: str = Field(..., description="Current status")
    progress: Optional[float] = Field(None, description="Progress percentage (0-100)")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    message: Optional[str] = Field(None, description="Status message")


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
