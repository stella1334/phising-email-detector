import re
import dns.resolver
from typing import List, Dict, Any, Tuple, Optional
from loguru import logger
from schemas.response_schemas import DeterministicChecks, SuspiciousIndicator, IndicatorType
from utils.validators import URLValidator, EmailValidator, DomainValidator
from utils.html_processor import HTMLProcessor

class DeterministicChecker:
    """Deterministic phishing detection checks"""
    
    def __init__(self):
        self.url_validator = URLValidator()
        self.email_validator = EmailValidator()
        self.domain_validator = DomainValidator()
        self.html_processor = HTMLProcessor()
    
    def perform_checks(self, metadata: Dict[str, Any], body_text: str) -> Tuple[DeterministicChecks, List[SuspiciousIndicator]]:
        """Perform all deterministic checks
        
        Args:
            metadata: Email metadata dictionary
            body_text: Email body text content
            
        Returns:
            Tuple of (deterministic_checks, suspicious_indicators)
        """
        indicators = []
        
        try:
            # Perform individual checks
            spf_result = self._check_spf(metadata)
            dkim_result = self._check_dkim(metadata)
            dmarc_result = self._check_dmarc(metadata)
            
            # Check sender reputation
            sender_rep = self._check_sender_reputation(metadata.get('sender'))
            
            # Analyze URLs
            url_indicators = self._analyze_urls(metadata.get('links', []))
            indicators.extend(url_indicators)
            
            # Analyze attachments
            attachment_indicators = self._analyze_attachments(metadata.get('attachments', []))
            indicators.extend(attachment_indicators)
            
            # Analyze email addresses
            email_indicators = self._analyze_email_addresses(metadata)
            indicators.extend(email_indicators)
            
            # Analyze content patterns
            content_indicators = self._analyze_content_patterns(body_text)
            indicators.extend(content_indicators)
            
            # Analyze headers
            header_indicators = self._analyze_headers(metadata)
            indicators.extend(header_indicators)
            
            # Calculate overall deterministic score
            score = self._calculate_deterministic_score(
                spf_result, dkim_result, dmarc_result, sender_rep, indicators
            )
            
            # Create deterministic checks result
            checks = DeterministicChecks(
                spf_pass=spf_result,
                dkim_pass=dkim_result,
                dmarc_pass=dmarc_result,
                sender_reputation=sender_rep,
                suspicious_urls_count=len([i for i in indicators if i.type == IndicatorType.URL]),
                suspicious_attachments_count=len([i for i in indicators if i.type == IndicatorType.ATTACHMENT]),
                score=score
            )
            
            logger.info(f"Deterministic checks completed. Score: {score}, Indicators: {len(indicators)}")
            return checks, indicators
            
        except Exception as e:
            logger.error(f"Error performing deterministic checks: {e}")
            # Return minimal result
            return DeterministicChecks(score=50.0), []
    
    def _check_spf(self, metadata: Dict[str, Any]) -> Optional[bool]:
        """Check SPF record validation"""
        try:
            spf_header = metadata.get('received_spf', '')
            if not spf_header:
                return None
            
            # Parse SPF result from header
            spf_lower = spf_header.lower()
            if 'pass' in spf_lower:
                return True
            elif any(word in spf_lower for word in ['fail', 'softfail', 'hardfail']):
                return False
            else:
                return None  # Neutral or unknown
                
        except Exception as e:
            logger.warning(f"Error checking SPF: {e}")
            return None
    
    def _check_dkim(self, metadata: Dict[str, Any]) -> Optional[bool]:
        """Check DKIM signature validation"""
        try:
            auth_results = metadata.get('authentication_results', '')
            if not auth_results:
                return None
            
            # Look for DKIM results in authentication results
            auth_lower = auth_results.lower()
            if 'dkim=pass' in auth_lower:
                return True
            elif 'dkim=fail' in auth_lower or 'dkim=none' in auth_lower:
                return False
            else:
                return None
                
        except Exception as e:
            logger.warning(f"Error checking DKIM: {e}")
            return None
    
    def _check_dmarc(self, metadata: Dict[str, Any]) -> Optional[bool]:
        """Check DMARC policy validation"""
        try:
            auth_results = metadata.get('authentication_results', '')
            if not auth_results:
                return None
            
            # Look for DMARC results in authentication results
            auth_lower = auth_results.lower()
            if 'dmarc=pass' in auth_lower:
                return True
            elif 'dmarc=fail' in auth_lower:
                return False
            else:
                return None
                
        except Exception as e:
            logger.warning(f"Error checking DMARC: {e}")
            return None
    
    def _check_sender_reputation(self, sender: Optional[str]) -> Optional[float]:
        """Check sender domain reputation"""
        if not sender:
            return None
        
        try:
            domain = self.email_validator.extract_domain(sender)
            if not domain:
                return None
            
            score, factors = self.domain_validator.analyze_domain_reputation(domain)
            logger.debug(f"Sender reputation for {domain}: {score} ({factors})")
            return score
            
        except Exception as e:
            logger.warning(f"Error checking sender reputation: {e}")
            return None
    
    def _analyze_urls(self, links: List[str]) -> List[SuspiciousIndicator]:
        """Analyze URLs for suspicious patterns"""
        indicators = []
        
        try:
            for url in links:
                is_suspicious, confidence, reasons = self.url_validator.analyze_url(url)
                
                if is_suspicious:
                    indicators.append(SuspiciousIndicator(
                        type=IndicatorType.URL,
                        value=url,
                        reason='; '.join(reasons),
                        confidence=confidence,
                        location="email_body"
                    ))
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error analyzing URLs: {e}")
            return []
    
    def _analyze_attachments(self, attachments: List[str]) -> List[SuspiciousIndicator]:
        """Analyze attachments for suspicious patterns"""
        indicators = []
        
        try:
            suspicious_extensions = {
                '.exe': 0.9,
                '.scr': 0.9,
                '.bat': 0.8,
                '.cmd': 0.8,
                '.com': 0.8,
                '.pif': 0.9,
                '.jar': 0.7,
                '.js': 0.6,
                '.vbs': 0.8,
                '.ps1': 0.7,
                '.zip': 0.4,
                '.rar': 0.4,
                '.7z': 0.4
            }
            
            for attachment in attachments:
                filename_lower = attachment.lower()
                
                # Check dangerous extensions
                for ext, confidence in suspicious_extensions.items():
                    if filename_lower.endswith(ext):
                        indicators.append(SuspiciousIndicator(
                            type=IndicatorType.ATTACHMENT,
                            value=attachment,
                            reason=f"Potentially dangerous file type: {ext}",
                            confidence=confidence,
                            location="attachment"
                        ))
                        break
                
                # Check for double extensions
                if re.search(r'\.[a-z]{2,4}\.[a-z]{2,4}$', filename_lower):
                    indicators.append(SuspiciousIndicator(
                        type=IndicatorType.ATTACHMENT,
                        value=attachment,
                        reason="Suspicious double extension",
                        confidence=0.7,
                        location="attachment"
                    ))
                
                # Check for very long filenames (obfuscation attempt)
                if len(attachment) > 100:
                    indicators.append(SuspiciousIndicator(
                        type=IndicatorType.ATTACHMENT,
                        value=attachment[:50] + "...",
                        reason="Unusually long filename (potential obfuscation)",
                        confidence=0.5,
                        location="attachment"
                    ))
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error analyzing attachments: {e}")
            return []
    
    def _analyze_email_addresses(self, metadata: Dict[str, Any]) -> List[SuspiciousIndicator]:
        """Analyze email addresses for suspicious patterns"""
        indicators = []
        
        try:
            # Check sender
            sender = metadata.get('sender')
            if sender:
                is_suspicious, confidence, reasons = self.email_validator.is_suspicious_email(sender)
                if is_suspicious:
                    indicators.append(SuspiciousIndicator(
                        type=IndicatorType.EMAIL,
                        value=sender,
                        reason='; '.join(reasons),
                        confidence=confidence,
                        location="sender"
                    ))
            
            # Check reply-to
            reply_to = metadata.get('reply_to')
            if reply_to and reply_to != sender:
                is_suspicious, confidence, reasons = self.email_validator.is_suspicious_email(reply_to)
                if is_suspicious:
                    indicators.append(SuspiciousIndicator(
                        type=IndicatorType.EMAIL,
                        value=reply_to,
                        reason='; '.join(reasons),
                        confidence=confidence,
                        location="reply_to"
                    ))
                
                # Check if sender and reply-to domains differ significantly
                sender_domain = self.email_validator.extract_domain(sender) if sender else None
                reply_domain = self.email_validator.extract_domain(reply_to)
                
                if sender_domain and reply_domain and sender_domain != reply_domain:
                    indicators.append(SuspiciousIndicator(
                        type=IndicatorType.EMAIL,
                        value=f"Sender: {sender}, Reply-to: {reply_to}",
                        reason="Sender and reply-to domains differ",
                        confidence=0.6,
                        location="headers"
                    ))
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error analyzing email addresses: {e}")
            return []
    
    def _analyze_content_patterns(self, body_text: str) -> List[SuspiciousIndicator]:
        """Analyze content for suspicious patterns"""
        indicators = []
        
        try:
            # Extract suspicious phrases
            suspicious_phrases = self.html_processor.extract_suspicious_phrases(body_text)
            
            for phrase, confidence, reason in suspicious_phrases:
                indicators.append(SuspiciousIndicator(
                    type=IndicatorType.CONTENT,
                    value=phrase,
                    reason=reason,
                    confidence=confidence,
                    location="email_body"
                ))
            
            # Check for common phishing patterns
            phishing_patterns = {
                r'\bbank[^a-z]*(?:account|statement|alert)': (0.7, "Banking-related content"),
                r'\b(?:paypal|venmo|zelle)[^a-z]*(?:account|payment)': (0.8, "Payment service reference"),
                r'\b(?:social\s+security|ssn|tax\s+refund)': (0.9, "Government/tax-related content"),
                r'\b(?:credit\s+card|debit\s+card)[^a-z]*(?:expir|suspend|block)': (0.8, "Credit card threat"),
                r'\b(?:amazon|apple|microsoft|google)[^a-z]*(?:account|subscription)': (0.6, "Tech company impersonation"),
                r'\$[0-9,]+(?:\.[0-9]{2})?.*(?:refund|reward|prize|lottery)': (0.9, "Money offer"),
                r'\b(?:fbi|irs|federal|government)\b': (0.8, "Government agency impersonation")
            }
            
            for pattern, (confidence, reason) in phishing_patterns.items():
                matches = re.finditer(pattern, body_text, re.IGNORECASE)
                for match in matches:
                    indicators.append(SuspiciousIndicator(
                        type=IndicatorType.CONTENT,
                        value=match.group(0),
                        reason=reason,
                        confidence=confidence,
                        location="email_body"
                    ))
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error analyzing content patterns: {e}")
            return []
    
    def _analyze_headers(self, metadata: Dict[str, Any]) -> List[SuspiciousIndicator]:
        """Analyze email headers for suspicious patterns"""
        indicators = []
        
        try:
            # Check for missing important headers
            if not metadata.get('message_id'):
                indicators.append(SuspiciousIndicator(
                    type=IndicatorType.HEADER,
                    value="Missing Message-ID",
                    reason="Missing Message-ID header (unusual for legitimate emails)",
                    confidence=0.4,
                    location="headers"
                ))
            
            # Check for suspicious subject patterns
            subject = metadata.get('subject', '')
            if subject:
                suspicious_subject_patterns = [
                    (r'\bURGENT\b', 0.6, "Urgent subject line"),
                    (r'\bIMMEDIATE\b', 0.6, "Immediate action subject"),
                    (r'^(?:RE:|FW:)\s*$', 0.7, "Empty reply/forward subject"),
                    (r'[!]{3,}', 0.5, "Excessive exclamation marks"),
                    (r'\$[0-9,]+', 0.7, "Money amount in subject"),
                    (r'\b(?:suspended|locked|blocked)\b', 0.8, "Account threat in subject")
                ]
                
                for pattern, confidence, reason in suspicious_subject_patterns:
                    if re.search(pattern, subject, re.IGNORECASE):
                        indicators.append(SuspiciousIndicator(
                            type=IndicatorType.HEADER,
                            value=subject,
                            reason=reason,
                            confidence=confidence,
                            location="subject"
                        ))
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error analyzing headers: {e}")
            return []
    
    def _calculate_deterministic_score(self, spf_pass: Optional[bool], dkim_pass: Optional[bool], 
                                     dmarc_pass: Optional[bool], sender_reputation: Optional[float],
                                     indicators: List[SuspiciousIndicator]) -> float:
        """Calculate overall deterministic score"""
        try:
            score = 50.0  # Start with neutral score
            
            # Authentication checks (30% weight)
            auth_weight = 30.0
            auth_penalties = 0
            auth_checks = 0
            
            if spf_pass is not None:
                auth_checks += 1
                if not spf_pass:
                    auth_penalties += 1
            
            if dkim_pass is not None:
                auth_checks += 1
                if not dkim_pass:
                    auth_penalties += 1
            
            if dmarc_pass is not None:
                auth_checks += 1
                if not dmarc_pass:
                    auth_penalties += 1
            
            if auth_checks > 0:
                auth_score = (auth_checks - auth_penalties) / auth_checks
                score += (auth_score - 0.5) * auth_weight
            
            # Sender reputation (20% weight)
            if sender_reputation is not None:
                rep_weight = 20.0
                score += (sender_reputation - 0.5) * rep_weight
            
            # Suspicious indicators (50% weight)
            if indicators:
                indicator_penalty = 0
                for indicator in indicators:
                    # Weight by confidence and type
                    type_weights = {
                        IndicatorType.URL: 1.0,
                        IndicatorType.EMAIL: 0.8,
                        IndicatorType.ATTACHMENT: 1.2,
                        IndicatorType.CONTENT: 0.7,
                        IndicatorType.HEADER: 0.5
                    }
                    
                    weight = type_weights.get(indicator.type, 0.7)
                    penalty = indicator.confidence * weight * 10
                    indicator_penalty += penalty
                
                # Cap the penalty
                indicator_penalty = min(indicator_penalty, 40.0)
                score += indicator_penalty
            
            # Ensure score is within bounds
            score = max(0.0, min(100.0, score))
            
            return round(score, 1)
            
        except Exception as e:
            logger.error(f"Error calculating deterministic score: {e}")
            return 50.0
