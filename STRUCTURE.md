# Project Structure

```
bank_phishing_detector/
├── app.py                          # Main FastAPI application
├── config.py                       # Configuration management
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
├── Makefile                        # Development and deployment commands
├── Dockerfile                      # Docker container configuration
├── docker-compose.yml              # Multi-container setup
├── nginx.conf                      # Nginx reverse proxy configuration
├── .gitignore                      # Git ignore patterns
├── README.md                       # Main documentation
│
├── models/                         # Core business logic
│   ├── __init__.py
│   ├── email_parser.py              # Email parsing and metadata extraction
│   ├── deterministic_checker.py     # Rule-based phishing detection
│   ├── gemini_analyzer.py           # Google Gemini API integration
│   └── risk_scorer.py               # Risk scoring and final decision
│
├── schemas/                        # Data models and API schemas
│   ├── __init__.py
│   ├── request_schemas.py           # API request schemas
│   └── response_schemas.py          # API response schemas
│
├── utils/                          # Utility functions
│   ├── __init__.py
│   ├── validators.py                # URL, email, and domain validation
│   ├── html_processor.py            # HTML processing and annotation
│   └── logging_config.py            # Logging configuration
│
├── tests/                          # Test suite
│   ├── __init__.py
│   ├── test_api.py                  # API endpoint tests
│   ├── test_email_parser.py         # Email parser tests
│   └── test_deterministic_checker.py # Deterministic checker tests
│
├── docs/                           # Documentation
│   └── API.md                       # Detailed API documentation
│
├── examples/                       # Sample data and usage examples
│   └── sample_emails/
│       ├── legitimate_bank_email.txt    # Sample legitimate email
│       └── phishing_email.txt           # Sample phishing email
│
└── test_api.sh                     # API testing script
```

## Component Overview

### Core Application (`app.py`)
- FastAPI web application
- API endpoint definitions
- Request/response handling
- Error handling and middleware
- Health checks and monitoring

### Models Package

#### Email Parser (`models/email_parser.py`)
- Raw email parsing with headers and body extraction
- Metadata extraction (sender, subject, links, attachments)
- HTML and text content processing
- Fallback parsing for malformed emails

#### Deterministic Checker (`models/deterministic_checker.py`)
- SPF/DKIM/DMARC validation
- URL pattern analysis
- Attachment security checks
- Content pattern matching
- Header analysis

#### Gemini Analyzer (`models/gemini_analyzer.py`)
- Google Gemini API integration
- Semantic content analysis
- Phishing likelihood scoring
- Error handling and fallback analysis

#### Risk Scorer (`models/risk_scorer.py`)
- Final risk score calculation
- Risk level classification
- Response building
- Bulk analysis summary generation

### Utilities Package

#### Validators (`utils/validators.py`)
- URL validation and analysis
- Email address validation
- Domain reputation checking
- Suspicious pattern detection

#### HTML Processor (`utils/html_processor.py`)
- HTML content extraction
- Suspicious content annotation
- Text cleaning and processing
- Visual highlighting for web display

#### Logging Config (`utils/logging_config.py`)
- Structured logging setup
- Log formatting and rotation
- Development vs production logging

### Schemas Package

#### Request Schemas (`schemas/request_schemas.py`)
- API request validation
- Input data models
- Bulk request handling

#### Response Schemas (`schemas/response_schemas.py`)
- API response structures
- Risk assessment models
- Error response formats

## Architecture Patterns

### Three-Stage Pipeline
1. **Preprocessing**: Email parsing and deterministic analysis
2. **AI Analysis**: Semantic evaluation with Gemini
3. **Aggregation**: Score combination and response generation

### Design Principles
- **Separation of Concerns**: Each component has a single responsibility
- **Dependency Injection**: Components are loosely coupled
- **Error Resilience**: Graceful degradation when services fail
- **Configurability**: Adjustable weights and thresholds
- **Observability**: Comprehensive logging and monitoring

### Security Considerations
- Input validation on all endpoints
- Rate limiting (via nginx)
- SSL/TLS encryption
- No sensitive data in logs
- Secure API key management

### Performance Features
- Async request handling
- Concurrent bulk processing
- Efficient HTML parsing
- Connection pooling for external APIs
- Caching where appropriate

### Production Readiness
- Docker containerization
- Health checks and monitoring
- Structured logging
- Configuration management
- Graceful shutdown handling
- Error tracking and alerting
