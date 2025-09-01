# AI-Powered Backend Application

A robust, scalable, and maintainable AI-powered backend application built with Python FastAPI, designed to support multiple GenAI-related features with a focus on clean architecture principles and SOLID design patterns.

## 🏗️ Architecture Overview

The application follows a clean architecture pattern with clear separation of concerns:

- **API Layer**: FastAPI routers organized by feature/use-case
- **Controller Layer**: Orchestrates business logic and data access
- **Service Layer**: Contains business logic and LLM integration
- **Repository Layer**: Handles database operations
- **Models Layer**: SQLAlchemy ORM models and Pydantic schemas

### Key Design Principles

- **SOLID Principles**: Single Responsibility, Open-Closed, Liskov Substitution, Interface Segregation, Dependency Inversion
- **Clean Architecture**: Clear separation between layers
- **Modular Design**: Each feature is self-contained in its own directory
- **Async-First**: Built with async/await for high concurrency
- **Type Safety**: Full type hints and Pydantic validation

## 🚀 Features

### Current Features

1. **Survey Analysis** (`/api/v1/survey-analysis`)
   - AI-powered analysis of survey responses
   - Categorization of questions by category
   - Identification of strengths and weaknesses
   - Actionable recommendations for improvement
   - Integration with OpenAI GPT models via LangChain

### Planned Features

2. **Policy Analyzer** (`/api/v1/policy-analyzer`)
   - Document analysis and policy review
   - Compliance checking and risk assessment

3. **Chat Document** (`/api/v1/chat-document`)
   - Interactive document Q&A
   - Context-aware responses

## 🛠️ Technology Stack

- **Framework**: FastAPI (Python 3.8+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: Okta JWT integration
- **AI/ML**: LangChain with OpenAI integration
- **Monitoring**: Prometheus metrics and structured logging
- **Migrations**: Alembic
- **Testing**: pytest with async support

## 📋 Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- Okta developer account (for authentication)
- OpenAI API key

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd TPE
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Copy the environment template and configure your settings:

```bash
cp env.example .env
```

Edit `.env` with your configuration:

```env
# Database
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/ai_backend_db
DATABASE_URL_SYNC=postgresql://username:password@localhost:5432/ai_backend_db

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Okta
OKTA_ISSUER=https://your-domain.okta.com/oauth2/default
OKTA_CLIENT_ID=your_okta_client_id
OKTA_CLIENT_SECRET=your_okta_client_secret
OKTA_AUDIENCE=api://default

# Security
SECRET_KEY=your_secret_key_here
```

### 5. Database Setup

Create PostgreSQL database:

```sql
CREATE DATABASE ai_backend_db;
```

Run migrations:

```bash
alembic upgrade head
```

### 6. Start the Application

```bash
python -m app.main
```

The application will be available at `http://localhost:8000`

## 📚 API Documentation

Once the application is running, you can access:

- **Interactive API Docs**: `http://localhost:8000/docs` (Swagger UI)
- **Alternative API Docs**: `http://localhost:8000/redoc` (ReDoc)
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

## 🔐 Authentication

The application uses Okta for authentication. To access protected endpoints:

1. Obtain a JWT token from Okta
2. Include the token in the Authorization header:
   ```
   Authorization: Bearer <your_jwt_token>
   ```

### Required Scopes

- `survey:analyze` - Create and analyze surveys
- `survey:read` - Read survey data and results
- `survey:delete` - Delete surveys

## 📊 Survey Analysis Usage

### Example Request

```bash
curl -X POST "http://localhost:8000/api/v1/survey-analysis/analyze" \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Performance Assessment",
    "description": "Quarterly performance review",
    "questions": [
      {
        "question_text": "How would you rate your communication skills?",
        "question_type": "multiple_choice",
        "category": "Communication",
        "weight": 1.0,
        "options": [
          {"value": "1", "label": "Poor", "weight": 0.0},
          {"value": "2", "label": "Fair", "weight": 0.5},
          {"value": "3", "label": "Good", "weight": 1.0},
          {"value": "4", "label": "Excellent", "weight": 1.5}
        ],
        "order_index": 1
      }
    ],
    "answers": [
      {
        "question_id": 1,
        "selected_answer": "3",
        "answer_weight": 1.0
      }
    ]
  }'
```

### Example Response

```json
{
  "survey_id": 1,
  "status": "completed",
  "categories_analyzed": 1,
  "category_analyses": [
    {
      "category": "Communication",
      "strengths": ["Good communication skills demonstrated"],
      "weaknesses": ["Could improve in complex scenarios"],
      "recommendations": ["Practice active listening", "Seek feedback regularly"],
      "category_score": 75.0,
      "analysis_summary": "Strong foundation in communication with room for growth..."
    }
  ],
  "overall_summary": "Overall good performance with specific areas for improvement...",
  "processing_time": 2.5,
  "llm_model_used": "gpt-4",
  "tokens_used": 1250,
  "created_at": "2024-01-15T10:30:00Z"
}
```

## 🧪 Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=app --cov-report=html
```

## 📈 Monitoring

The application includes built-in monitoring:

- **Health Check**: `GET /health`
- **Metrics**: `GET /metrics` (Prometheus format)
- **Structured Logging**: JSON-formatted logs with correlation IDs

## 🔧 Development

### Code Quality

The project uses several tools for code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting

Format code:

```bash
black app/
isort app/
```

### Adding New Features

To add a new feature (e.g., `policy_analyzer`):

1. Create feature directory: `app/features/policy_analyzer/`
2. Add models, schemas, repository, service, and controller
3. Create router: `app/api/v1/routers/policy_analyzer_router.py`
4. Include router in main application
5. Add database models to migrations

### Database Migrations

Create a new migration:

```bash
alembic revision --autogenerate -m "Add new feature"
alembic upgrade head
```

## 🚀 Deployment

### Docker

Build the image:

```bash
docker build -t ai-backend .
```

Run the container:

```bash
docker run -p 8000:8000 --env-file .env ai-backend
```

### Production Considerations

- Set `DEBUG=false` in production
- Configure proper CORS origins
- Use environment-specific database URLs
- Set up proper logging and monitoring
- Configure rate limiting
- Use HTTPS in production

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the logs for detailed error information

## 🔮 Roadmap

- [ ] Policy Analyzer feature
- [ ] Chat Document feature
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Real-time notifications
- [ ] Advanced caching strategies
- [ ] Kubernetes deployment manifests
- [ ] CI/CD pipeline setup
