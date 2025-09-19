from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator
from enum import Enum

class EmailAnalysisRequest(BaseModel):
    """Request schema for email analysis"""
    
    raw_email: str = Field(..., description="Raw email content with headers")
    sender_email: Optional[str] = Field(None, description="Sender email address (optional, will be extracted if not provided)")
    subject: Optional[str] = Field(None, description="Email subject (optional, will be extracted if not provided)")
    additional_context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context for analysis")
    
    class Config:
        schema_extra = {
            "example": {
                "raw_email": "From: sender@example.com\nTo: recipient@bank.com\nSubject: Urgent Account Verification\n\nDear customer, click here to verify...",
                "sender_email": "sender@example.com",
                "subject": "Urgent Account Verification",
                "additional_context": {
                    "user_bank": "Example Bank",
                    "user_account_type": "checking"
                }
            }
        }

class BulkAnalysisRequest(BaseModel):
    """Request schema for bulk email analysis"""
    
    emails: List[EmailAnalysisRequest] = Field(..., min_items=1, max_items=50, description="List of emails to analyze")
    
    class Config:
        schema_extra = {
            "example": {
                "emails": [
                    {
                        "raw_email": "From: phisher@evil.com\nSubject: URGENT\n\nClick here now!",
                        "additional_context": {"priority": "high"}
                    }
                ]
            }
        }
