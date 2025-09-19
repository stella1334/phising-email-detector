import json
import google.generativeai as genai
from typing import Dict, Any, Optional, Tuple
from loguru import logger
from config import settings
from schemas.response_schemas import GeminiAnalysis

class GeminiAnalyzer:
    """Google Gemini API integration for semantic phishing analysis"""
    
    def __init__(self):
        self.model = None
        self.initialized = False
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """Initialize Gemini API client"""
        try:
            if not settings.gemini_api_key:
                logger.warning("Gemini API key not provided. Semantic analysis will be unavailable.")
                return
            
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel(settings.gemini_model)
            self.initialized = True
            logger.info(f"Initialized Gemini model: {settings.gemini_model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini API: {e}")
            self.initialized = False
    
    def analyze_email(self, metadata: Dict[str, Any], body_text: str, 
                     deterministic_indicators: list) -> GeminiAnalysis:
        """Analyze email content using Gemini for phishing detection
        
        Args:
            metadata: Email metadata dictionary
            body_text: Clean email body text
            deterministic_indicators: List of deterministic indicators found
            
        Returns:
            GeminiAnalysis object with results
        """
        if not self.initialized:
            logger.warning("Gemini not initialized. Returning default analysis.")
            return self._get_default_analysis()
        
        try:
            # Prepare the analysis prompt
            prompt = self._build_analysis_prompt(metadata, body_text, deterministic_indicators)
            
            # Call Gemini API
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=settings.gemini_temperature,
                    max_output_tokens=settings.gemini_max_tokens,
                    response_mime_type="application/json",
                )
            )
            
            # Parse response
            result = self._parse_gemini_response(response.text)
            
            logger.info(f"Gemini analysis completed. Phishing likelihood: {result.phishing_likelihood}%")
            return result
            
        except Exception as e:
            logger.error(f"Error during Gemini analysis: {e}")
            return self._get_fallback_analysis(deterministic_indicators)
    
    def _build_analysis_prompt(self, metadata: Dict[str, Any], body_text: str, 
                              deterministic_indicators: list) -> str:
        """Build comprehensive analysis prompt for Gemini"""
        
        # Prepare email information
        email_info = {
            "sender": metadata.get('sender', 'Unknown'),
            "reply_to": metadata.get('reply_to'),
            "subject": metadata.get('subject', 'No subject'),
            "links": metadata.get('links', []),
            "attachments": metadata.get('attachments', []),
            "body_text": body_text[:2000] if body_text else "No body content"  # Limit length
        }
        
        # Summarize deterministic findings
        deterministic_summary = []
        for indicator in deterministic_indicators:
            deterministic_summary.append({
                "type": indicator.type if hasattr(indicator, 'type') else "unknown",
                "value": indicator.value if hasattr(indicator, 'value') else str(indicator),
                "reason": indicator.reason if hasattr(indicator, 'reason') else "No reason",
                "confidence": indicator.confidence if hasattr(indicator, 'confidence') else 0.5
            })
        
        prompt = f"""
You are an expert cybersecurity analyst specializing in email phishing detection. Analyze the following email for phishing characteristics and provide a comprehensive assessment.

**EMAIL INFORMATION:**
```json
{json.dumps(email_info, indent=2)}
```

**DETERMINISTIC ANALYSIS FINDINGS:**
```json
{json.dumps(deterministic_summary, indent=2)}
```

**ANALYSIS REQUIREMENTS:**

Evaluate this email for phishing indicators across multiple dimensions:

1. **Sender Analysis**: Assess sender legitimacy, domain reputation, and email authentication
2. **Content Analysis**: Look for social engineering tactics, urgency manipulation, credential harvesting attempts
3. **Linguistic Patterns**: Identify suspicious language patterns, grammar issues, or psychological manipulation
4. **URL Analysis**: Evaluate any links for legitimacy and potential redirects
5. **Context Analysis**: Consider if this appears to be targeting banking/financial information

**SCORING RUBRIC (0-100):**
- 0-20: Legitimate email, no phishing indicators
- 21-40: Low risk, minor suspicious elements
- 41-60: Medium risk, several concerning factors
- 61-80: High risk, strong phishing indicators
- 81-100: Critical risk, almost certainly phishing

**RESPONSE FORMAT:**
Provide your analysis in the following JSON format:

```json
{
  "phishing_likelihood": <score_0_to_100>,
  "reasoning": "<detailed_explanation_of_score>",
  "key_concerns": ["<concern_1>", "<concern_2>", "<concern_3>"],
  "linguistic_patterns": ["<pattern_1>", "<pattern_2>"],
  "model_confidence": <confidence_0_to_1>
}
```

**IMPORTANT GUIDELINES:**
- Be thorough but concise in your reasoning
- Focus on banking/financial phishing specifically
- Consider the deterministic findings but make your own independent assessment
- Provide specific examples from the email content when possible
- Be conservative with legitimate banking communications
- Pay special attention to urgency tactics and credential requests

Provide your analysis now:
"""
        
        return prompt
    
    def _parse_gemini_response(self, response_text: str) -> GeminiAnalysis:
        """Parse Gemini API response into GeminiAnalysis object"""
        try:
            # Clean the response text (remove markdown formatting if present)
            cleaned_text = response_text.strip()
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]
            
            # Parse JSON
            response_data = json.loads(cleaned_text)
            
            # Validate and extract fields
            phishing_likelihood = float(response_data.get('phishing_likelihood', 50.0))
            phishing_likelihood = max(0.0, min(100.0, phishing_likelihood))  # Clamp to 0-100
            
            reasoning = str(response_data.get('reasoning', 'No reasoning provided'))
            
            key_concerns = response_data.get('key_concerns', [])
            if not isinstance(key_concerns, list):
                key_concerns = []
            
            linguistic_patterns = response_data.get('linguistic_patterns', [])
            if not isinstance(linguistic_patterns, list):
                linguistic_patterns = []
            
            model_confidence = float(response_data.get('model_confidence', 0.5))
            model_confidence = max(0.0, min(1.0, model_confidence))  # Clamp to 0-1
            
            return GeminiAnalysis(
                phishing_likelihood=phishing_likelihood,
                reasoning=reasoning,
                key_concerns=key_concerns,
                linguistic_patterns=linguistic_patterns,
                model_confidence=model_confidence
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini JSON response: {e}")
            logger.debug(f"Raw response: {response_text}")
            return self._extract_fallback_from_text(response_text)
        
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}")
            return self._get_default_analysis()
    
    def _extract_fallback_from_text(self, response_text: str) -> GeminiAnalysis:
        """Extract information from non-JSON response text"""
        try:
            # Try to extract score using regex
            import re
            
            score_match = re.search(r'(?:score|likelihood|risk).*?([0-9]{1,3})', response_text, re.IGNORECASE)
            phishing_likelihood = 50.0
            if score_match:
                phishing_likelihood = float(score_match.group(1))
                phishing_likelihood = max(0.0, min(100.0, phishing_likelihood))
            
            # Extract key phrases
            key_concerns = []
            concern_patterns = [
                r'urgent[^.]*\.?',
                r'suspicious[^.]*\.?',
                r'phishing[^.]*\.?',
                r'credential[^.]*\.?',
                r'malicious[^.]*\.?'
            ]
            
            for pattern in concern_patterns:
                matches = re.findall(pattern, response_text, re.IGNORECASE)
                key_concerns.extend(matches[:2])  # Limit to 2 per pattern
            
            return GeminiAnalysis(
                phishing_likelihood=phishing_likelihood,
                reasoning=response_text[:500] + "..." if len(response_text) > 500 else response_text,
                key_concerns=key_concerns[:5],  # Limit to 5 concerns
                linguistic_patterns=[],
                model_confidence=0.3  # Low confidence for fallback parsing
            )
            
        except Exception as e:
            logger.error(f"Error in fallback text extraction: {e}")
            return self._get_default_analysis()
    
    def _get_fallback_analysis(self, deterministic_indicators: list) -> GeminiAnalysis:
        """Generate fallback analysis when Gemini fails"""
        try:
            # Base score on deterministic indicators
            score = 50.0
            concerns = []
            
            if deterministic_indicators:
                high_confidence_indicators = [
                    ind for ind in deterministic_indicators 
                    if hasattr(ind, 'confidence') and ind.confidence > 0.7
                ]
                
                if high_confidence_indicators:
                    score = min(80.0, 50.0 + len(high_confidence_indicators) * 10)
                    concerns = [f"Deterministic indicator: {ind.reason}" 
                               for ind in high_confidence_indicators[:3]]
            
            return GeminiAnalysis(
                phishing_likelihood=score,
                reasoning="Analysis based on deterministic indicators only (Gemini unavailable)",
                key_concerns=concerns,
                linguistic_patterns=[],
                model_confidence=0.4
            )
            
        except Exception as e:
            logger.error(f"Error generating fallback analysis: {e}")
            return self._get_default_analysis()
    
    def _get_default_analysis(self) -> GeminiAnalysis:
        """Get default analysis when all else fails"""
        return GeminiAnalysis(
            phishing_likelihood=50.0,
            reasoning="Unable to perform semantic analysis (Gemini unavailable)",
            key_concerns=["Analysis incomplete"],
            linguistic_patterns=[],
            model_confidence=0.1
        )
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test Gemini API connectivity
        
        Returns:
            Tuple of (is_connected, status_message)
        """
        if not self.initialized:
            return False, "Gemini API not initialized"
        
        try:
            # Test with a simple prompt
            test_response = self.model.generate_content(
                "Respond with 'OK' to confirm API connectivity.",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=10
                )
            )
            
            if test_response and test_response.text:
                return True, "Gemini API connected successfully"
            else:
                return False, "Gemini API response empty"
                
        except Exception as e:
            logger.error(f"Gemini connectivity test failed: {e}")
            return False, f"Gemini API error: {str(e)}"
