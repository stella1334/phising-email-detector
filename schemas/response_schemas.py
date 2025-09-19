from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class IndicatorType(str, Enum):
    URL = "url"
    EMAIL = "email"
    DOMAIN = "domain"
    CONTENT = "content"
    HEADER = "header"
    ATTACHMENT = "attachment"

class SuspiciousIndicator(BaseModel):
    """Individual suspicious indicator found in the email"""
    
    type: IndicatorType = Field(..., description="Type of indicator")
    value: str = Field(..., description="The suspicious value (URL, email, text, etc.)")
    reason: str = Field(..., description="Why this is considered suspicious")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for this indicator")
    location: Optional[str] = Field(None, description="Where in the email this was found")

class DeterministicChecks(BaseModel):
    """Results from deterministic security checks"""
    
    spf_pass: Optional[bool] = Field(None, description="SPF record validation result")
    dkim_pass: Optional[bool] = Field(None, description="DKIM signature validation result")
    dmarc_pass: Optional[bool] = Field(None, description="DMARC policy validation result")
    sender_reputation: Optional[float] = Field(None, ge=0.0, le=1.0, description="Sender reputation score")
    suspicious_urls_count: int = Field(0, description="Number of suspicious URLs found")
    suspicious_attachments_count: int = Field(0, description="Number of suspicious attachments found")
    score: float = Field(..., ge=0.0, le=100.0, description="Overall deterministic score")

class GeminiAnalysis(BaseModel):
    """Results from Gemini AI analysis"""
    
    phishing_likelihood: float = Field(..., ge=0.0, le=100.0, description="Phishing likelihood score from Gemini")
    reasoning: str = Field(..., description="Gemini's reasoning for the score")
    key_concerns: List[str] = Field(default_factory=list, description="Key concerns identified by Gemini")
    linguistic_patterns: List[str] = Field(default_factory=list, description="Suspicious linguistic patterns")
    model_confidence: float = Field(..., ge=0.0, le=1.0, description="Model's confidence in its assessment")

class EmailMetadata(BaseModel):
    """Parsed email metadata"""
    
    sender: Optional[str] = Field(None, description="Sender email address")
    reply_to: Optional[str] = Field(None, description="Reply-to email address")
    subject: Optional[str] = Field(None, description="Email subject")
    received_date: Optional[datetime] = Field(None, description="Email received date")
    message_id: Optional[str] = Field(None, description="Email message ID")
    return_path: Optional[str] = Field(None, description="Return path")
    received_spf: Optional[str] = Field(None, description="Received SPF header")
    authentication_results: Optional[str] = Field(None, description="Authentication results header")
    links: List[str] = Field(default_factory=list, description="Extracted links")
    attachments: List[str] = Field(default_factory=list, description="Attachment names")

class PhishingAnalysisResponse(BaseModel):
    """Complete phishing analysis response"""
    
    # Core Results
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Final risk score (0-100)")
    risk_level: RiskLevel = Field(..., description="Risk level classification")
    is_phishing: bool = Field(..., description="Binary phishing determination")
    
    # Detailed Analysis
    email_metadata: EmailMetadata = Field(..., description="Parsed email metadata")
    deterministic_checks: DeterministicChecks = Field(..., description="Deterministic check results")
    gemini_analysis: GeminiAnalysis = Field(..., description="Gemini AI analysis results")
    suspicious_indicators: List[SuspiciousIndicator] = Field(default_factory=list, description="All suspicious indicators found")
    
    # Processed Content
    annotated_body_html: Optional[str] = Field(None, description="HTML body with suspicious content highlighted")
    clean_body_text: Optional[str] = Field(None, description="Clean text version of email body")
    
    # Analysis Metadata
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When analysis was performed")
    processing_time_ms: Optional[float] = Field(None, description="Total processing time in milliseconds")
    version: str = Field("1.0.0", description="Analysis engine version")
    
    class Config:
        schema_extra = {
            "example": {
                "risk_score": 85.5,
                "risk_level": "high",
                "is_phishing": True,
                "email_metadata": {
                    "sender": "phisher@suspicious-domain.com",
                    "subject": "URGENT: Verify Your Account",
                    "links": ["http://suspicious-site.com/verify"]
                },
                "deterministic_checks": {
                    "spf_pass": False,
                    "dkim_pass": False,
                    "suspicious_urls_count": 1,
                    "score": 75.0
                },
                "gemini_analysis": {
                    "phishing_likelihood": 90.0,
                    "reasoning": "Email contains urgent language, requests credentials, and has suspicious sender",
                    "key_concerns": ["Urgent language", "Credential request", "Suspicious domain"],
                    "model_confidence": 0.95
                },
                "suspicious_indicators": [
                    {
                        "type": "url",
                        "value": "http://suspicious-site.com/verify",
                        "reason": "Domain not associated with legitimate bank",
                        "confidence": 0.9
                    }
                ],
                "is_phishing": True
            }
        }

class BulkAnalysisResponse(BaseModel):
    """Response for bulk email analysis"""
    
    results: List[PhishingAnalysisResponse] = Field(..., description="Analysis results for each email")
    summary: Dict[str, Any] = Field(..., description="Summary statistics")
    total_processing_time_ms: float = Field(..., description="Total processing time for all emails")
    
class HealthResponse(BaseModel):
    """Health check response"""
    
    status: str = Field("healthy", description="Service status")
    version: str = Field("1.0.0", description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    gemini_api_status: str = Field(..., description="Gemini API connectivity status")
    
class ErrorResponse(BaseModel):
    """Error response schema"""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
