from typing import Dict, Any, List


class SurveyAnalysisPrompts:
    """Predefined prompts for survey analysis using LLM."""
    
    @staticmethod
    def get_system_prompt() -> str:
        """Get the system prompt for survey analysis."""
        return """You are an expert performance analyst specializing in survey data analysis. 
Your task is to analyze survey responses and provide insights about the respondent's strengths and weaknesses across different categories.

Key responsibilities:
1. Analyze survey questions and answers objectively
2. Identify patterns in responses
3. Categorize findings by question categories
4. Provide actionable insights and recommendations
5. Maintain a professional and constructive tone

Analysis guidelines:
- Focus on behavioral and performance patterns
- Consider question weights and answer weights
- Provide specific, actionable feedback
- Balance strengths and areas for improvement
- Use evidence from the survey responses to support conclusions

Output format:
- Provide analysis in JSON format
- Include strengths, weaknesses, and recommendations for each category
- Provide an overall summary
- Be specific and actionable in recommendations"""

    @staticmethod
    def get_analysis_prompt(survey_data: Dict[str, Any]) -> str:
        """Get the analysis prompt with survey data."""
        return f"""Please analyze the following survey data and provide a comprehensive performance analysis.

Survey Information:
- Title: {survey_data.get('title', 'N/A')}
- Description: {survey_data.get('description', 'N/A')}
- Total Questions: {len(survey_data.get('questions', []))}

Analysis Requirements:
1. Group questions by their categories
2. For each category, analyze the responses considering:
   - Question weights
   - Answer weights
   - Response patterns
   - Performance indicators

3. For each category, provide:
   - List of strengths (what the person is doing well)
   - List of weaknesses (areas for improvement)
   - Specific recommendations for enhancement
   - A numerical score (0-100) for the category
   - Detailed analysis summary

4. Provide an overall summary that:
   - Highlights key findings across all categories
   - Identifies the strongest and weakest areas
   - Offers prioritized improvement suggestions

Please format your response as valid JSON with the following structure:
{{
  "categories": [
    {{
      "category": "category_name",
      "strengths": ["strength1", "strength2"],
      "weaknesses": ["weakness1", "weakness2"],
      "recommendations": ["rec1", "rec2"],
      "category_score": 85.5,
      "analysis_summary": "Detailed analysis of this category..."
    }}
  ],
  "overall_summary": "Comprehensive summary across all categories...",
  "key_insights": ["insight1", "insight2"],
  "priority_areas": ["priority1", "priority2"]
}}

Survey Data:
{survey_data}"""

    @staticmethod
    def get_category_specific_prompt(category: str, questions: List[Dict[str, Any]]) -> str:
        """Get a category-specific analysis prompt."""
        return f"""Focus your analysis on the '{category}' category.

Category Questions:
{questions}

For this specific category, please analyze:
1. What patterns emerge from the responses?
2. What does the respondent do well in this area?
3. What areas need improvement?
4. What specific actions would help enhance performance in this category?

Consider:
- Question weights and their significance
- Answer weights and their implications
- Response consistency and quality
- Industry best practices for this category

Provide a focused analysis for the '{category}' category only."""

    @staticmethod
    def get_followup_prompt(initial_analysis: str, specific_question: str) -> str:
        """Get a follow-up prompt for additional analysis."""
        return f"""Based on the initial analysis provided below, please address this specific question:

Initial Analysis:
{initial_analysis}

Specific Question:
{specific_question}

Please provide a focused response that builds upon the initial analysis and addresses the specific question asked."""
