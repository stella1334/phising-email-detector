import time
import asyncio
from typing import List
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from loguru import logger

# Import configurations and schemas
from config import settings
from utils.logging_config import setup_logging
from schemas.request_schemas import EmailAnalysisRequest, BulkAnalysisRequest
from schemas.response_schemas import (
    PhishingAnalysisResponse, BulkAnalysisResponse, HealthResponse, ErrorResponse
)

# Import models
from models.email_parser import EmailParser
from models.deterministic_checker import DeterministicChecker
from models.gemini_analyzer import GeminiAnalyzer
from models.risk_scorer import RiskScorer
from utils.html_processor import HTMLProcessor

# Global instances
email_parser = None
deterministic_checker = None
gemini_analyzer = None
risk_scorer = None
html_processor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting Bank Phishing Detector service...")
    
    global email_parser, deterministic_checker, gemini_analyzer, risk_scorer, html_processor
    
    # Initialize components
    email_parser = EmailParser()
    deterministic_checker = DeterministicChecker()
    gemini_analyzer = GeminiAnalyzer()
    risk_scorer = RiskScorer()
    html_processor = HTMLProcessor()
    
    logger.info("Service components initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Bank Phishing Detector service...")

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description=settings.app_description,
    lifespan=lifespan
)

# Setup logging
setup_logging()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="InternalServerError",
            message="An internal server error occurred",
            details={"exception_type": type(exc).__name__}
        ).dict()
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTPException",
            message=str(exc.detail)
        ).dict()
    )

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Test Gemini connectivity
        gemini_connected, gemini_status = gemini_analyzer.test_connection()
        
        return HealthResponse(
            status="healthy",
            version=settings.app_version,
            gemini_api_status=gemini_status
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

# Main analysis endpoint
@app.post("/analyze", response_model=PhishingAnalysisResponse)
async def analyze_email(request: EmailAnalysisRequest):
    """Analyze a single email for phishing indicators"""
    start_time = time.time()
    
    try:
        logger.info(f"Starting email analysis for sender: {request.sender_email}")
        
        # Stage 1: Parse email and extract metadata
        email_metadata, html_body, text_body = email_parser.parse_raw_email(request.raw_email)
        
        # Override metadata if provided in request
        if request.sender_email:
            email_metadata.sender = request.sender_email
        if request.subject:
            email_metadata.subject = request.subject
        
        # Get clean body text for analysis
        body_for_analysis = email_parser.get_body_for_analysis(html_body, text_body)
        
        # Stage 1: Deterministic checks
        logger.info("Performing deterministic checks...")
        metadata_dict = email_metadata.dict()
        deterministic_checks, suspicious_indicators = deterministic_checker.perform_checks(
            metadata_dict, body_for_analysis
        )
        
        # Stage 2: Gemini semantic analysis
        logger.info("Performing Gemini semantic analysis...")
        gemini_analysis = gemini_analyzer.analyze_email(
            metadata_dict, body_for_analysis, suspicious_indicators
        )
        
        # Apply context adjustments if provided
        if request.additional_context:
            context = request.additional_context.copy()
            context['email_content'] = body_for_analysis
            
            # Adjust Gemini score based on context
            original_score = gemini_analysis.phishing_likelihood
            adjusted_score = risk_scorer.adjust_score_for_context(original_score, context)
            
            if adjusted_score != original_score:
                gemini_analysis.phishing_likelihood = adjusted_score
                gemini_analysis.reasoning += f" (Score adjusted from {original_score:.1f} to {adjusted_score:.1f} based on context)"
        
        # Stage 3: Generate annotated HTML if we have HTML content
        annotated_html = None
        if html_body:
            # Convert indicators to dict format for HTML processor
            indicator_dicts = [
                {
                    'type': ind.type.value,
                    'value': ind.value,
                    'reason': ind.reason,
                    'confidence': ind.confidence
                }
                for ind in suspicious_indicators
            ]
            annotated_html = html_processor.annotate_suspicious_content(
                html_body, indicator_dicts
            )
        
        # Stage 3: Calculate final risk and build response
        processing_time = (time.time() - start_time) * 1000
        
        response = risk_scorer.build_response(
            email_metadata=email_metadata,
            deterministic_checks=deterministic_checks,
            gemini_analysis=gemini_analysis,
            suspicious_indicators=suspicious_indicators,
            annotated_html=annotated_html,
            clean_text=body_for_analysis,
            processing_time_ms=processing_time
        )
        
        logger.info(
            f"Analysis completed in {processing_time:.1f}ms. "
            f"Risk score: {response.risk_score}, Level: {response.risk_level}"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error during email analysis: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Analysis failed: {str(e)}"
        )

# Bulk analysis endpoint
@app.post("/analyze/bulk", response_model=BulkAnalysisResponse)
async def analyze_emails_bulk(request: BulkAnalysisRequest):
    """Analyze multiple emails for phishing indicators"""
    start_time = time.time()
    
    try:
        logger.info(f"Starting bulk analysis for {len(request.emails)} emails")
        
        # Process emails concurrently (but with some limits to avoid overwhelming)
        semaphore = asyncio.Semaphore(5)  # Limit concurrent processing
        
        async def analyze_single_email(email_request: EmailAnalysisRequest):
            async with semaphore:
                try:
                    # Convert to synchronous call (since our analyzers are sync)
                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(
                        None, 
                        lambda: analyze_email_sync(email_request)
                    )
                    return response
                except Exception as e:
                    logger.error(f"Error analyzing email in bulk: {e}")
                    # Return error response for this email
                    return create_error_response(str(e))
        
        # Process all emails
        tasks = [analyze_single_email(email_req) for email_req in request.emails]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and create proper responses
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Exception in bulk analysis for email {i}: {result}")
                valid_results.append(create_error_response(str(result)))
            else:
                valid_results.append(result)
        
        # Generate summary
        processing_time = (time.time() - start_time) * 1000
        summary = risk_scorer.get_risk_summary(valid_results)
        
        bulk_response = BulkAnalysisResponse(
            results=valid_results,
            summary=summary,
            total_processing_time_ms=processing_time
        )
        
        logger.info(
            f"Bulk analysis completed in {processing_time:.1f}ms. "
            f"Processed {len(valid_results)} emails"
        )
        
        return bulk_response
        
    except Exception as e:
        logger.error(f"Error during bulk analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Bulk analysis failed: {str(e)}"
        )

def analyze_email_sync(request: EmailAnalysisRequest) -> PhishingAnalysisResponse:
    """Synchronous version of email analysis for use in async context"""
    start_time = time.time()
    
    # Parse email and extract metadata
    email_metadata, html_body, text_body = email_parser.parse_raw_email(request.raw_email)
    
    # Override metadata if provided
    if request.sender_email:
        email_metadata.sender = request.sender_email
    if request.subject:
        email_metadata.subject = request.subject
    
    # Get clean body text
    body_for_analysis = email_parser.get_body_for_analysis(html_body, text_body)
    
    # Deterministic checks
    metadata_dict = email_metadata.dict()
    deterministic_checks, suspicious_indicators = deterministic_checker.perform_checks(
        metadata_dict, body_for_analysis
    )
    
    # Gemini analysis
    gemini_analysis = gemini_analyzer.analyze_email(
        metadata_dict, body_for_analysis, suspicious_indicators
    )
    
    # Context adjustments
    if request.additional_context:
        context = request.additional_context.copy()
        context['email_content'] = body_for_analysis
        
        original_score = gemini_analysis.phishing_likelihood
        adjusted_score = risk_scorer.adjust_score_for_context(original_score, context)
        
        if adjusted_score != original_score:
            gemini_analysis.phishing_likelihood = adjusted_score
    
    # Generate annotated HTML
    annotated_html = None
    if html_body:
        indicator_dicts = [
            {
                'type': ind.type.value,
                'value': ind.value,
                'reason': ind.reason,
                'confidence': ind.confidence
            }
            for ind in suspicious_indicators
        ]
        annotated_html = html_processor.annotate_suspicious_content(
            html_body, indicator_dicts
        )
    
    # Build final response
    processing_time = (time.time() - start_time) * 1000
    
    return risk_scorer.build_response(
        email_metadata=email_metadata,
        deterministic_checks=deterministic_checks,
        gemini_analysis=gemini_analysis,
        suspicious_indicators=suspicious_indicators,
        annotated_html=annotated_html,
        clean_text=body_for_analysis,
        processing_time_ms=processing_time
    )

def create_error_response(error_message: str) -> PhishingAnalysisResponse:
    """Create a minimal error response for failed analyses"""
    from schemas.response_schemas import EmailMetadata, DeterministicChecks, GeminiAnalysis, RiskLevel
    
    return PhishingAnalysisResponse(
        risk_score=50.0,
        risk_level=RiskLevel.MEDIUM,
        is_phishing=False,
        email_metadata=EmailMetadata(),
        deterministic_checks=DeterministicChecks(score=50.0),
        gemini_analysis=GeminiAnalysis(
            phishing_likelihood=50.0,
            reasoning=f"Analysis failed: {error_message}",
            key_concerns=["Analysis error"],
            linguistic_patterns=[],
            model_confidence=0.0
        ),
        suspicious_indicators=[],
        processing_time_ms=0.0
    )

# Additional utility endpoints
@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": settings.app_title,
        "version": settings.app_version,
        "description": settings.app_description,
        "endpoints": {
            "analyze": "/analyze",
            "bulk_analyze": "/analyze/bulk",
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/status")
async def get_status():
    """Get detailed service status"""
    try:
        gemini_connected, gemini_status = gemini_analyzer.test_connection()
        
        return {
            "service_status": "operational",
            "components": {
                "email_parser": "operational",
                "deterministic_checker": "operational",
                "gemini_analyzer": "operational" if gemini_connected else "degraded",
                "risk_scorer": "operational",
                "html_processor": "operational"
            },
            "gemini_api": {
                "connected": gemini_connected,
                "status": gemini_status
            },
            "configuration": {
                "deterministic_weight": settings.deterministic_weight,
                "gemini_weight": settings.gemini_weight,
                "high_risk_threshold": settings.high_risk_threshold,
                "medium_risk_threshold": settings.medium_risk_threshold
            }
        }
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return {
            "service_status": "degraded",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server on {settings.host}:{settings.port}")
    uvicorn.run(
        "app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
