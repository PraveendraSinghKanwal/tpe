from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.db.base import Base


class Survey(Base):
    """Survey model to store survey metadata."""
    
    __tablename__ = "surveys"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(String(255), nullable=False, index=True)  # Okta user ID
    status = Column(String(50), default="pending", index=True)  # pending, processing, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    questions = relationship("SurveyQuestion", back_populates="survey", cascade="all, delete-orphan")
    analysis_results = relationship("SurveyAnalysis", back_populates="survey", cascade="all, delete-orphan")


class SurveyQuestion(Base):
    """Survey question model."""
    
    __tablename__ = "survey_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=False)  # multiple_choice, text, rating, etc.
    category = Column(String(100), nullable=False, index=True)
    weight = Column(Float, default=1.0)
    options = Column(JSON, nullable=True)  # For multiple choice questions
    order_index = Column(Integer, default=0)
    
    # Relationships
    survey = relationship("Survey", back_populates="questions")
    answers = relationship("SurveyAnswer", back_populates="question", cascade="all, delete-orphan")


class SurveyAnswer(Base):
    """User's answer to a survey question."""
    
    __tablename__ = "survey_answers"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("survey_questions.id"), nullable=False)
    survey_id = Column(Integer, ForeignKey("surveys.id"), nullable=False)
    user_id = Column(String(255), nullable=False, index=True)
    selected_answer = Column(Text, nullable=False)
    answer_weight = Column(Float, default=1.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    question = relationship("SurveyQuestion", back_populates="answers")


class SurveyAnalysis(Base):
    """Analysis results for a survey."""
    
    __tablename__ = "survey_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    strengths = Column(JSON, nullable=True)  # List of strengths identified
    weaknesses = Column(JSON, nullable=True)  # List of weaknesses identified
    recommendations = Column(JSON, nullable=True)  # List of recommendations
    category_score = Column(Float, nullable=True)  # Numerical score for the category
    analysis_summary = Column(Text, nullable=False)
    llm_model_used = Column(String(100), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    processing_time = Column(Float, nullable=True)  # in seconds
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    survey = relationship("Survey", back_populates="analysis_results")
