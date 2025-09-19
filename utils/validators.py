import re
import validators
from typing import List, Tuple, Optional
from urllib.parse import urlparse, unquote
from email_validator import validate_email, EmailNotValidError
from loguru import logger

class URLValidator:
    """URL validation and analysis utilities"""
    
    # Suspicious TLDs commonly used in phishing
    SUSPICIOUS_TLDS = {
        '.tk', '.ml', '.ga', '.cf', '.top', '.click', '.download', '.stream',
        '.science', '.racing', '.review', '.date', '.faith', '.cricket'
    }
    
    # Suspicious URL patterns
    SUSPICIOUS_PATTERNS = [
        r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}',  # IP addresses
        r'bit\.ly|tinyurl|short|url\.org|goo\.gl|t\.co',  # URL shorteners
        r'[a-z0-9]+-[a-z0-9]+-[a-z0-9]+\.[a-z]{2,}',  # Suspicious hyphens
        r'[0-9]{4,}\.[a-z]{2,}',  # Numbers in domain
        r'[a-z]+[0-9]+[a-z]+\.[a-z]{2,}',  # Mixed alphanumeric
        r'secure[^a-z]|verify[^a-z]|update[^a-z]|confirm[^a-z]',  # Phishing keywords
    ]
    
    # Banking and financial domains (whitelist)
    LEGITIMATE_DOMAINS = {
        'chase.com', 'bankofamerica.com', 'wellsfargo.com', 'citi.com',
        'usbank.com', 'pnc.com', 'capitalone.com', 'td.com', 'regions.com',
        'suntrust.com', 'ally.com', 'americanexpress.com', 'discover.com',
        'paypal.com', 'venmo.com', 'zelle.com'
    }
    
    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """Extract all URLs from text"""
        try:
            # Pattern to match URLs
            url_pattern = re.compile(
                r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            )
            
            urls = url_pattern.findall(text)
            
            # Also look for URLs without protocol
            domain_pattern = re.compile(
                r'(?:^|[\s,;])([a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.)+[a-zA-Z]{2,}(?:[/?][^\s]*)?',
                re.MULTILINE
            )
            
            domain_urls = domain_pattern.findall(text)
            for url in domain_urls:
                if url.strip() and not url.startswith('http'):
                    urls.append(f'http://{url.strip()}')
            
            return list(set(urls))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error extracting URLs: {e}")
            return []
    
    @staticmethod
    def analyze_url(url: str) -> Tuple[bool, float, List[str]]:
        """Analyze a URL for phishing indicators
        
        Returns:
            Tuple of (is_suspicious, confidence_score, reasons)
        """
        try:
            reasons = []
            confidence = 0.0
            
            # Basic URL validation
            if not validators.url(url):
                return True, 0.9, ["Invalid URL format"]
            
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            path = parsed.path.lower()
            
            # Check if domain is in whitelist
            for legitimate in URLValidator.LEGITIMATE_DOMAINS:
                if domain.endswith(legitimate):
                    return False, 0.1, ["Legitimate domain"]
            
            # Check suspicious TLDs
            for tld in URLValidator.SUSPICIOUS_TLDS:
                if domain.endswith(tld):
                    confidence += 0.3
                    reasons.append(f"Suspicious TLD: {tld}")
            
            # Check suspicious patterns
            for pattern in URLValidator.SUSPICIOUS_PATTERNS:
                if re.search(pattern, url, re.IGNORECASE):
                    confidence += 0.25
                    reasons.append(f"Suspicious pattern detected")
            
            # Check for homograph attacks (similar looking domains)
            if URLValidator._check_homograph_attack(domain):
                confidence += 0.4
                reasons.append("Potential homograph attack")
            
            # Check URL length (very long URLs can be suspicious)
            if len(url) > 150:
                confidence += 0.2
                reasons.append("Unusually long URL")
            
            # Check for excessive subdomains
            subdomain_count = domain.count('.')
            if subdomain_count > 3:
                confidence += 0.3
                reasons.append(f"Excessive subdomains ({subdomain_count})")
            
            # Check for suspicious path patterns
            if re.search(r'(login|signin|verify|update|confirm|secure)', path):
                confidence += 0.2
                reasons.append("Suspicious path keywords")
            
            # Normalize confidence score
            confidence = min(confidence, 1.0)
            is_suspicious = confidence > 0.3
            
            return is_suspicious, confidence, reasons
            
        except Exception as e:
            logger.error(f"Error analyzing URL {url}: {e}")
            return True, 0.8, [f"Analysis error: {str(e)}"]
    
    @staticmethod
    def _check_homograph_attack(domain: str) -> bool:
        """Check for potential homograph attacks"""
        # Simple homograph detection - could be expanded
        suspicious_chars = ['а', 'е', 'о', 'р', 'с', 'х', 'у']  # Cyrillic lookalikes
        return any(char in domain for char in suspicious_chars)

class EmailValidator:
    """Email validation utilities"""
    
    @staticmethod
    def validate_email_address(email: str) -> Tuple[bool, Optional[str]]:
        """Validate email address format
        
        Returns:
            Tuple of (is_valid, normalized_email)
        """
        try:
            validated = validate_email(email)
            return True, validated.email
        except EmailNotValidError as e:
            logger.warning(f"Invalid email address {email}: {e}")
            return False, None
    
    @staticmethod
    def extract_domain(email: str) -> Optional[str]:
        """Extract domain from email address"""
        try:
            if '@' in email:
                return email.split('@')[1].lower()
            return None
        except Exception:
            return None
    
    @staticmethod
    def is_suspicious_email(email: str) -> Tuple[bool, float, List[str]]:
        """Analyze email address for suspicious patterns
        
        Returns:
            Tuple of (is_suspicious, confidence_score, reasons)
        """
        try:
            reasons = []
            confidence = 0.0
            
            # Basic validation
            is_valid, normalized = EmailValidator.validate_email_address(email)
            if not is_valid:
                return True, 0.9, ["Invalid email format"]
            
            domain = EmailValidator.extract_domain(normalized)
            if not domain:
                return True, 0.8, ["Cannot extract domain"]
            
            # Check for suspicious patterns
            local_part = normalized.split('@')[0]
            
            # Check for random-looking local parts
            if len(local_part) > 20 or re.search(r'^[a-z0-9]{15,}$', local_part):
                confidence += 0.3
                reasons.append("Suspicious local part pattern")
            
            # Check domain against URL validator
            dummy_url = f"http://{domain}"
            is_url_suspicious, url_confidence, url_reasons = URLValidator.analyze_url(dummy_url)
            
            if is_url_suspicious:
                confidence += url_confidence * 0.8
                reasons.extend([f"Domain: {reason}" for reason in url_reasons])
            
            # Check for free email providers (less trustworthy for banking)
            free_providers = {'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com'}
            if domain in free_providers:
                confidence += 0.1
                reasons.append("Free email provider")
            
            confidence = min(confidence, 1.0)
            is_suspicious = confidence > 0.3
            
            return is_suspicious, confidence, reasons
            
        except Exception as e:
            logger.error(f"Error analyzing email {email}: {e}")
            return True, 0.8, [f"Analysis error: {str(e)}"]

class DomainValidator:
    """Domain validation and reputation checking"""
    
    @staticmethod
    def is_legitimate_banking_domain(domain: str) -> bool:
        """Check if domain belongs to a legitimate bank"""
        return domain.lower() in URLValidator.LEGITIMATE_DOMAINS
    
    @staticmethod
    def analyze_domain_reputation(domain: str) -> Tuple[float, List[str]]:
        """Analyze domain reputation
        
        Returns:
            Tuple of (reputation_score, factors)
        """
        factors = []
        score = 0.5  # Neutral starting point
        
        try:
            # Check if it's a known legitimate domain
            if DomainValidator.is_legitimate_banking_domain(domain):
                score = 0.9
                factors.append("Known legitimate banking domain")
            
            # Check TLD reputation
            if any(domain.endswith(tld) for tld in URLValidator.SUSPICIOUS_TLDS):
                score -= 0.3
                factors.append("Suspicious TLD")
            
            # Check domain age (simplified - would use WHOIS in production)
            if re.search(r'[0-9]{4,}', domain):
                score -= 0.2
                factors.append("Contains suspicious numeric patterns")
            
            # Normalize score
            score = max(0.0, min(1.0, score))
            
            return score, factors
            
        except Exception as e:
            logger.error(f"Error analyzing domain reputation for {domain}: {e}")
            return 0.3, [f"Analysis error: {str(e)}"]
