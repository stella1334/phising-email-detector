# Bank Phishing Detector Plugin

A production-ready phishing detection service that combines deterministic rule-based analysis with Google Gemini AI for semantic evaluation of bank-related emails.

## Features

### Core Capabilities
- **Multi-stage Analysis**: Combines deterministic checks with AI-powered semantic analysis
- **Email Parsing**: Full email parsing with header, body, and attachment analysis
- **Authentication Validation**: SPF, DKIM, and DMARC verification
- **URL Analysis**: Comprehensive link analysis with threat detection
- **Content Analysis**: Pattern matching for phishing indicators
- **AI Integration**: Google Gemini API for advanced semantic analysis
- **Risk Scoring**: Weighted scoring system with configurable thresholds
- **HTML Annotation**: Visual highlighting of suspicious content
- **Bulk Processing**: Analyze multiple emails concurrently

### Technical Features
- **RESTful API**: FastAPI-based HTTP service
- **Async Processing**: Concurrent email analysis
- **Configurable Weights**: Adjustable scoring algorithms
- **Comprehensive Logging**: Structured logging with Loguru
- **Error Handling**: Graceful degradation and error recovery
- **Health Monitoring**: Service health and status endpoints
- **Docker Support**: Containerized deployment

## Architecture

The system follows a three-stage analysis pipeline:

### Stage 1: Preprocessing
- Parse raw email headers and body
- Extract sender, subject, links, attachments
- Perform deterministic security checks (SPF/DKIM/DMARC)
- Apply regex-based suspicious pattern detection
- Generate feature vector with confidence weights

### Stage 2: LLM Analysis
- Send structured prompt to Google Gemini
- Evaluate phishing likelihood (0-100 score)
- Extract key concerns and reasoning
- Identify linguistic manipulation patterns

### Stage 3: Aggregation
- Combine deterministic and Gemini scores
- Apply configurable weights (default: 60% deterministic, 40% Gemini)
- Generate risk classification (low/medium/high/critical)
- Produce annotated HTML with highlighted threats
- Return comprehensive analysis response

## Installation

### Prerequisites
- Python 3.9+
- Google Gemini API key
- Docker (optional)

### Local Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd bank_phishing_detector
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your Gemini API key and other settings
```

4. Run the service:
```bash
python app.py
```

### Docker Deployment

```bash
# Build image
docker build -t bank-phishing-detector .

# Run container
docker run -p 8000:8000 --env-file .env bank-phishing-detector
```

### Docker Compose

```bash
docker-compose up -d
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|----------|
| `PHISHING_DETECTOR_GEMINI_API_KEY` | Google Gemini API key | Required |
| `PHISHING_DETECTOR_HOST` | Server host | `0.0.0.0` |
| `PHISHING_DETECTOR_PORT` | Server port | `8000` |
| `PHISHING_DETECTOR_DETERMINISTIC_WEIGHT` | Weight for deterministic score | `0.6` |
| `PHISHING_DETECTOR_GEMINI_WEIGHT` | Weight for Gemini score | `0.4` |
| `PHISHING_DETECTOR_HIGH_RISK_THRESHOLD` | High risk threshold | `70.0` |
| `PHISHING_DETECTOR_MEDIUM_RISK_THRESHOLD` | Medium risk threshold | `40.0` |

### Risk Scoring

The final risk score is calculated as:
```
final_score = (deterministic_score × deterministic_weight) + (gemini_score × gemini_weight)
```

Risk levels:
- **Critical** (90-100): Almost certainly phishing
- **High** (70-89): Strong phishing indicators
- **Medium** (40-69): Some suspicious elements
- **Low** (0-39): Likely legitimate

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=models --cov=utils --cov=schemas

# Run specific test file
pytest tests/test_email_parser.py
```

## Monitoring

### Health Checks
- `GET /health` - Basic health status
- `GET /status` - Detailed component status

### Logging
- Structured JSON logging
- Configurable log levels
- File rotation for production
- Request/response tracking

## Security Considerations

- API rate limiting recommended
- Input validation on all endpoints
- Sensitive data sanitization in logs
- Network security for Gemini API calls
- Regular security updates

## Performance

- Single email analysis: ~500-2000ms
- Bulk processing: Up to 5 concurrent analyses
- Memory usage: ~100-200MB baseline
- Scalable with load balancer

## Limitations

- Requires Google Gemini API access
- Limited to 50 emails per bulk request
- Processing time depends on email size and complexity
- Network dependency for AI analysis

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
