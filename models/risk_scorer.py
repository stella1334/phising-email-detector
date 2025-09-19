from typing import List, Tuple
from loguru import logger
from config import settings
from schemas.response_schemas import (
    RiskLevel, PhishingAnalysisResponse, DeterministicChecks, 
    GeminiAnalysis, SuspiciousIndicator, EmailMetadata
)
from datetime import datetime

class RiskScorer:
    """Risk scoring and final decision engine"""
    
    def __init__(self):
        self.deterministic_weight = settings.deterministic_weight
        self.gemini_weight = settings.gemini_weight
        self.high_risk_threshold = settings.high_risk_threshold
        self.medium_risk_threshold = settings.medium_risk_threshold
    
    def calculate_final_score(self, deterministic_checks: DeterministicChecks, 
                            gemini_analysis: GeminiAnalysis) -> Tuple[float, RiskLevel, bool]:
        """Calculate final risk score and classification
        
        Args:
            deterministic_checks: Results from deterministic analysis
            gemini_analysis: Results from Gemini semantic analysis
            
        Returns:
            Tuple of (final_score, risk_level, is_phishing)
        """
        try:
            # Calculate weighted score
            deterministic_score = deterministic_checks.score
            gemini_score = gemini_analysis.phishing_likelihood
            
            final_score = (
                (deterministic_score * self.deterministic_weight) + 
                (gemini_score * self.gemini_weight)
            )
            
            # Apply confidence adjustment
            confidence_factor = gemini_analysis.model_confidence
            if confidence_factor < 0.5:
                # If Gemini has low confidence, rely more on deterministic
                adjusted_weight = min(0.8, self.deterministic_weight + 0.2)
                final_score = (
                    (deterministic_score * adjusted_weight) + 
                    (gemini_score * (1.0 - adjusted_weight))
                )
            
            # Ensure score is within bounds
            final_score = max(0.0, min(100.0, final_score))
            
            # Determine risk level and phishing classification
            risk_level, is_phishing = self._classify_risk(final_score)
            
            logger.info(
                f"Final risk calculation - Deterministic: {deterministic_score:.1f}, "
                f"Gemini: {gemini_score:.1f}, Final: {final_score:.1f}, "
                f"Level: {risk_level}, Phishing: {is_phishing}"
            )
            
            return round(final_score, 1), risk_level, is_phishing
            
        except Exception as e:
            logger.error(f"Error calculating final score: {e}")
            # Fallback to deterministic score only
            score = deterministic_checks.score
            risk_level, is_phishing = self._classify_risk(score)
            return score, risk_level, is_phishing
    
    def _classify_risk(self, score: float) -> Tuple[RiskLevel, bool]:
        """Classify risk level based on score
        
        Args:
            score: Risk score (0-100)
            
        Returns:
            Tuple of (risk_level, is_phishing)
        """
        if score >= 90.0:
            return RiskLevel.CRITICAL, True
        elif score >= self.high_risk_threshold:
            return RiskLevel.HIGH, True
        elif score >= self.medium_risk_threshold:
            return RiskLevel.MEDIUM, False  # Medium risk is not classified as phishing
        else:
            return RiskLevel.LOW, False
    
    def build_response(self, email_metadata: EmailMetadata,
                      deterministic_checks: DeterministicChecks,
                      gemini_analysis: GeminiAnalysis,
                      suspicious_indicators: List[SuspiciousIndicator],
                      annotated_html: str = None,
                      clean_text: str = None,
                      processing_time_ms: float = None) -> PhishingAnalysisResponse:
        """Build comprehensive analysis response
        
        Args:
            email_metadata: Parsed email metadata
            deterministic_checks: Deterministic analysis results
            gemini_analysis: Gemini semantic analysis results
            suspicious_indicators: All suspicious indicators found
            annotated_html: HTML body with annotations (optional)
            clean_text: Clean text version of body (optional)
            processing_time_ms: Total processing time (optional)
            
        Returns:
            Complete PhishingAnalysisResponse
        """
        try:
            # Calculate final risk assessment
            final_score, risk_level, is_phishing = self.calculate_final_score(
                deterministic_checks, gemini_analysis
            )
            
            # Build response
            response = PhishingAnalysisResponse(
                risk_score=final_score,
                risk_level=risk_level,
                is_phishing=is_phishing,
                email_metadata=email_metadata,
                deterministic_checks=deterministic_checks,
                gemini_analysis=gemini_analysis,
                suspicious_indicators=suspicious_indicators,
                annotated_body_html=annotated_html,
                clean_body_text=clean_text,
                analysis_timestamp=datetime.utcnow(),
                processing_time_ms=processing_time_ms,
                version=settings.app_version
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error building response: {e}")
            raise
    
    def get_risk_summary(self, responses: List[PhishingAnalysisResponse]) -> dict:
        """Generate summary statistics for bulk analysis
        
        Args:
            responses: List of analysis responses
            
        Returns:
            Summary statistics dictionary
        """
        try:
            if not responses:
                return {}
            
            total_emails = len(responses)
            phishing_count = sum(1 for r in responses if r.is_phishing)
            
            risk_level_counts = {
                'critical': sum(1 for r in responses if r.risk_level == RiskLevel.CRITICAL),
                'high': sum(1 for r in responses if r.risk_level == RiskLevel.HIGH),
                'medium': sum(1 for r in responses if r.risk_level == RiskLevel.MEDIUM),
                'low': sum(1 for r in responses if r.risk_level == RiskLevel.LOW)
            }
            
            avg_score = sum(r.risk_score for r in responses) / total_emails
            max_score = max(r.risk_score for r in responses)
            min_score = min(r.risk_score for r in responses)
            
            # Top indicators
            all_indicators = []
            for response in responses:
                all_indicators.extend(response.suspicious_indicators)
            
            indicator_types = {}
            for indicator in all_indicators:
                indicator_type = indicator.type.value
                if indicator_type not in indicator_types:
                    indicator_types[indicator_type] = 0
                indicator_types[indicator_type] += 1
            
            return {
                'total_emails': total_emails,
                'phishing_detected': phishing_count,
                'phishing_rate': round(phishing_count / total_emails * 100, 1),
                'risk_level_distribution': risk_level_counts,
                'score_statistics': {
                    'average': round(avg_score, 1),
                    'maximum': max_score,
                    'minimum': min_score
                },
                'indicator_summary': indicator_types,
                'high_risk_emails': [
                    {
                        'sender': r.email_metadata.sender,
                        'subject': r.email_metadata.subject,
                        'risk_score': r.risk_score,
                        'risk_level': r.risk_level.value
                    }
                    for r in responses 
                    if r.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
                ]
            }
            
        except Exception as e:
            logger.error(f"Error generating risk summary: {e}")
            return {
                'total_emails': len(responses),
                'error': f"Summary generation failed: {str(e)}"
            }
    
    def adjust_score_for_context(self, base_score: float, context: dict) -> float:
        """Adjust score based on additional context
        
        Args:
            base_score: Initial calculated score
            context: Additional context information
            
        Returns:
            Adjusted score
        """
        try:
            adjusted_score = base_score
            
            # Adjust based on user's bank
            user_bank = context.get('user_bank', '').lower()
            if user_bank:
                # If email claims to be from user's bank, increase scrutiny
                email_content = context.get('email_content', '').lower()
                if user_bank in email_content:
                    # Potential targeted attack
                    adjusted_score += 5.0
            
            # Adjust based on time of day
            current_hour = datetime.utcnow().hour
            if current_hour < 6 or current_hour > 22:  # Outside business hours
                # Legitimate banks rarely send emails at odd hours
                adjusted_score += 3.0
            
            # Adjust based on account type
            account_type = context.get('user_account_type', '')
            if account_type == 'business' and 'personal' in context.get('email_content', '').lower():
                # Business account receiving personal banking emails
                adjusted_score += 5.0
            
            return max(0.0, min(100.0, adjusted_score))
            
        except Exception as e:
            logger.error(f"Error adjusting score for context: {e}")
            return base_score
