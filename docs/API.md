# Bank Phishing Detector API Documentation

## Overview

The Bank Phishing Detector provides RESTful endpoints for analyzing emails to detect phishing attempts. The service combines deterministic rule-based analysis with Google Gemini AI for comprehensive threat detection.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. In production, implement appropriate authentication mechanisms.

## Endpoints

### Health Check

#### GET /health

Returns the health status of the service.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-09-19T07:15:47.123456Z",
  "gemini_api_status": "Gemini API connected successfully"
}
```

### Service Status

#### GET /status

Returns detailed status of all service components.

**Response:**
```json
{
  "service_status": "operational",
  "components": {
    "email_parser": "operational",
    "deterministic_checker": "operational",
    "gemini_analyzer": "operational",
    "risk_scorer": "operational",
    "html_processor": "operational"
  },
  "gemini_api": {
    "connected": true,
    "status": "Gemini API connected successfully"
  },
  "configuration": {
    "deterministic_weight": 0.6,
    "gemini_weight": 0.4,
    "high_risk_threshold": 70.0,
    "medium_risk_threshold": 40.0
  }
}
```

### Analyze Single Email

#### POST /analyze

Analyzes a single email for phishing indicators.

**Request Body:**
```json
{
  "raw_email": "From: sender@example.com\nTo: recipient@bank.com\nSubject: Urgent Account Verification\n\nDear customer, click here to verify...",
  "sender_email": "sender@example.com",
  "subject": "Urgent Account Verification",
  "additional_context": {
    "user_bank": "Example Bank",
    "user_account_type": "checking"
  }
}
```

**Parameters:**
- `raw_email` (required): Complete raw email content including headers
- `sender_email` (optional): Override sender email if different from headers
- `subject` (optional): Override subject if different from headers
- `additional_context` (optional): Additional context for analysis

**Response:**
```json
{
  "risk_score": 85.5,
  "risk_level": "high",
  "is_phishing": true,
  "email_metadata": {
    "sender": "phisher@suspicious-domain.com",
    "reply_to": null,
    "subject": "URGENT: Verify Your Account",
    "received_date": "2025-09-19T07:15:47Z",
    "message_id": "<123456@suspicious-domain.com>",
    "return_path": "phisher@suspicious-domain.com",
    "received_spf": "fail",
    "authentication_results": "dkim=fail",
    "links": ["http://suspicious-site.com/verify"],
    "attachments": []
  },
  "deterministic_checks": {
    "spf_pass": false,
    "dkim_pass": false,
    "dmarc_pass": null,
    "sender_reputation": 0.2,
    "suspicious_urls_count": 1,
    "suspicious_attachments_count": 0,
    "score": 75.0
  },
  "gemini_analysis": {
    "phishing_likelihood": 90.0,
    "reasoning": "Email contains urgent language, requests credentials, and has suspicious sender",
    "key_concerns": [
      "Urgent language manipulation",
      "Credential harvesting attempt",
      "Suspicious domain"
    ],
    "linguistic_patterns": [
      "Pressure tactics",
      "Generic greeting"
    ],
    "model_confidence": 0.95
  },
  "suspicious_indicators": [
    {
      "type": "url",
      "value": "http://suspicious-site.com/verify",
      "reason": "Domain not associated with legitimate bank",
      "confidence": 0.9,
      "location": "email_body"
    },
    {
      "type": "content",
      "value": "URGENT",
      "reason": "Urgent language manipulation tactic",
      "confidence": 0.8,
      "location": "subject"
    }
  ],
  "annotated_body_html": "<html>...(highlighted suspicious content)...</html>",
  "clean_body_text": "Dear customer, click here to verify your account...",
  "analysis_timestamp": "2025-09-19T07:15:47.123456Z",
  "processing_time_ms": 1250.5,
  "version": "1.0.0"
}
```

### Bulk Email Analysis

#### POST /analyze/bulk

Analyzes multiple emails concurrently.

**Request Body:**
```json
{
  "emails": [
    {
      "raw_email": "From: phisher@evil.com\nSubject: URGENT\n\nClick here now!",
      "additional_context": {"priority": "high"}
    },
    {
      "raw_email": "From: legitimate@bank.com\nSubject: Monthly Statement\n\nYour statement is ready."
    }
  ]
}
```

**Parameters:**
- `emails` (required): Array of email analysis requests (max 50)

**Response:**
```json
{
  "results": [
    {
      "risk_score": 85.5,
      "risk_level": "high",
      "is_phishing": true,
      // ... (same structure as single analysis)
    },
    {
      "risk_score": 15.0,
      "risk_level": "low",
      "is_phishing": false,
      // ... (same structure as single analysis)
    }
  ],
  "summary": {
    "total_emails": 2,
    "phishing_detected": 1,
    "phishing_rate": 50.0,
    "risk_level_distribution": {
      "critical": 0,
      "high": 1,
      "medium": 0,
      "low": 1
    },
    "score_statistics": {
      "average": 50.25,
      "maximum": 85.5,
      "minimum": 15.0
    },
    "indicator_summary": {
      "url": 3,
      "content": 2,
      "email": 1
    },
    "high_risk_emails": [
      {
        "sender": "phisher@evil.com",
        "subject": "URGENT",
        "risk_score": 85.5,
        "risk_level": "high"
      }
    ]
  },
  "total_processing_time_ms": 2501.2
}
```

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "error": "ValidationError",
  "message": "Invalid email format",
  "details": {
    "field": "raw_email",
    "issue": "Missing required headers"
  },
  "timestamp": "2025-09-19T07:15:47.123456Z"
}
```

### HTTP Status Codes

- `200 OK`: Successful analysis
- `400 Bad Request`: Invalid request format
- `422 Unprocessable Entity`: Validation errors
- `500 Internal Server Error`: Service error
- `503 Service Unavailable`: Service degraded

## Rate Limiting

Consider implementing rate limiting in production:
- Recommended: 100 requests per minute per IP
- Bulk endpoints: 10 requests per minute per IP

## Data Types

### Risk Levels
- `low`: Score 0-39
- `medium`: Score 40-69  
- `high`: Score 70-89
- `critical`: Score 90-100

### Indicator Types
- `url`: Suspicious URLs
- `email`: Suspicious email addresses
- `domain`: Suspicious domains
- `content`: Suspicious content patterns
- `header`: Suspicious email headers
- `attachment`: Suspicious attachments

## Integration Examples

### Python
```python
import requests

response = requests.post('http://localhost:8000/analyze', json={
    'raw_email': raw_email_content
})

analysis = response.json()
if analysis['is_phishing']:
    print(f"PHISHING DETECTED! Risk: {analysis['risk_score']}")
```

### cURL
```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "raw_email": "From: test@example.com\nSubject: Test\n\nBody content"
  }'
```

## Interactive Documentation

Visit `/docs` for interactive API documentation (Swagger UI) or `/redoc` for alternative documentation format.
