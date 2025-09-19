import re
from typing import List, Dict, Optional, Tuple
from bs4 import BeautifulSoup, Tag
import html2text
from loguru import logger
from utils.validators import URLValidator

class HTMLProcessor:
    """HTML processing and annotation utilities"""
    
    def __init__(self):
        self.h = html2text.HTML2Text()
        self.h.ignore_links = False
        self.h.ignore_images = False
        self.h.body_width = 0  # Don't wrap lines
    
    def extract_text_and_links(self, html_content: str) -> Tuple[str, List[str]]:
        """Extract clean text and all links from HTML
        
        Returns:
            Tuple of (clean_text, links_list)
        """
        try:
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract links
            links = []
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                if href and not href.startswith('#'):
                    links.append(href)
            
            # Also extract from other elements
            for element in soup.find_all(['img', 'iframe', 'embed'], src=True):
                src = element['src']
                if src and not src.startswith('#'):
                    links.append(src)
            
            # Extract clean text
            clean_text = self.h.handle(html_content)
            
            # Also extract URLs from text content
            text_urls = URLValidator.extract_urls(clean_text)
            links.extend(text_urls)
            
            # Remove duplicates
            links = list(set(links))
            
            return clean_text, links
            
        except Exception as e:
            logger.error(f"Error extracting text and links: {e}")
            # Fallback to regex extraction
            text_urls = URLValidator.extract_urls(html_content)
            return html_content, text_urls
    
    def annotate_suspicious_content(self, html_content: str, 
                                   suspicious_indicators: List[Dict]) -> str:
        """Annotate HTML content with suspicious indicators highlighted
        
        Args:
            html_content: Original HTML content
            suspicious_indicators: List of suspicious indicators to highlight
            
        Returns:
            Annotated HTML with suspicious content highlighted
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Add CSS for highlighting
            style_tag = soup.new_tag('style')
            style_tag.string = """
            .phishing-highlight-critical { 
                background-color: #ff6b6b !important; 
                border: 2px solid #e74c3c !important; 
                padding: 2px !important;
                border-radius: 3px !important;
            }
            .phishing-highlight-high { 
                background-color: #ffa726 !important; 
                border: 1px solid #ff9800 !important; 
                padding: 1px !important;
                border-radius: 2px !important;
            }
            .phishing-highlight-medium { 
                background-color: #ffeb3b !important; 
                border: 1px solid #fbc02d !important; 
                padding: 1px !important;
                border-radius: 2px !important;
            }
            .phishing-tooltip {
                position: relative;
                cursor: help;
            }
            .phishing-tooltip::after {
                content: attr(data-reason);
                position: absolute;
                bottom: 100%;
                left: 50%;
                transform: translateX(-50%);
                background-color: #333;
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 12px;
                white-space: nowrap;
                visibility: hidden;
                opacity: 0;
                transition: opacity 0.2s;
                z-index: 1000;
            }
            .phishing-tooltip:hover::after {
                visibility: visible;
                opacity: 1;
            }
            """
            if soup.head:
                soup.head.append(style_tag)
            else:
                soup.insert(0, style_tag)
            
            # Group indicators by type for efficient processing
            url_indicators = [ind for ind in suspicious_indicators if ind.get('type') == 'url']
            content_indicators = [ind for ind in suspicious_indicators if ind.get('type') == 'content']
            email_indicators = [ind for ind in suspicious_indicators if ind.get('type') == 'email']
            
            # Highlight URLs
            for indicator in url_indicators:
                url = indicator['value']
                reason = indicator['reason']
                confidence = indicator.get('confidence', 0.5)
                
                css_class = self._get_highlight_class(confidence)
                
                # Find and highlight URL in href attributes
                for a_tag in soup.find_all('a', href=True):
                    if url in a_tag['href']:
                        a_tag['class'] = a_tag.get('class', []) + [css_class, 'phishing-tooltip']
                        a_tag['data-reason'] = f"Suspicious URL: {reason}"
                
                # Also highlight in text content
                self._highlight_text_pattern(soup, url, css_class, f"Suspicious URL: {reason}")
            
            # Highlight email addresses
            for indicator in email_indicators:
                email = indicator['value']
                reason = indicator['reason']
                confidence = indicator.get('confidence', 0.5)
                
                css_class = self._get_highlight_class(confidence)
                self._highlight_text_pattern(soup, email, css_class, f"Suspicious email: {reason}")
            
            # Highlight suspicious content patterns
            for indicator in content_indicators:
                pattern = indicator['value']
                reason = indicator['reason']
                confidence = indicator.get('confidence', 0.5)
                
                css_class = self._get_highlight_class(confidence)
                self._highlight_text_pattern(soup, pattern, css_class, f"Suspicious content: {reason}")
            
            return str(soup)
            
        except Exception as e:
            logger.error(f"Error annotating HTML content: {e}")
            return html_content  # Return original if annotation fails
    
    def _get_highlight_class(self, confidence: float) -> str:
        """Get CSS class based on confidence level"""
        if confidence >= 0.8:
            return 'phishing-highlight-critical'
        elif confidence >= 0.6:
            return 'phishing-highlight-high'
        else:
            return 'phishing-highlight-medium'
    
    def _highlight_text_pattern(self, soup: BeautifulSoup, pattern: str, 
                               css_class: str, reason: str):
        """Highlight text pattern in soup with given CSS class"""
        try:
            # Find all text nodes containing the pattern
            for element in soup.find_all(text=True):
                if pattern.lower() in element.lower():
                    parent = element.parent
                    if parent and parent.name not in ['script', 'style', 'meta']:
                        # Replace text with highlighted version
                        highlighted_text = re.sub(
                            re.escape(pattern), 
                            f'<span class="{css_class} phishing-tooltip" data-reason="{reason}">{pattern}</span>',
                            element,
                            flags=re.IGNORECASE
                        )
                        
                        if highlighted_text != element:
                            new_soup = BeautifulSoup(highlighted_text, 'html.parser')
                            element.replace_with(new_soup)
                            
        except Exception as e:
            logger.warning(f"Error highlighting pattern '{pattern}': {e}")
    
    def extract_suspicious_phrases(self, text: str) -> List[Tuple[str, float, str]]:
        """Extract suspicious phrases from text
        
        Returns:
            List of (phrase, confidence, reason) tuples
        """
        suspicious_phrases = []
        
        # Define suspicious patterns with confidence scores
        patterns = {
            r'urgent[ly]?\s+(action|response|verification|update)': (
                0.8, "Urgency manipulation tactic"
            ),
            r'verify\s+(your\s+)?(account|identity|information)': (
                0.7, "Verification request (common phishing tactic)"
            ),
            r'suspend(ed)?\s+(your\s+)?account': (
                0.9, "Account suspension threat"
            ),
            r'click\s+(here|below|now|immediately)': (
                0.6, "Immediate action request"
            ),
            r'confirm\s+(your\s+)?(identity|details|information)': (
                0.7, "Information confirmation request"
            ),
            r'update\s+(your\s+)?(payment|billing|card)': (
                0.8, "Payment information update request"
            ),
            r'limited\s+time\s+(offer|deal)': (
                0.5, "Limited time pressure"
            ),
            r'act\s+(now|immediately|fast|quickly)': (
                0.6, "Pressure to act quickly"
            ),
            r'security\s+(alert|warning|notice)': (
                0.7, "Security alert (potential false alarm)"
            ),
            r'dear\s+(customer|client|user)': (
                0.4, "Generic greeting (legitimate emails usually use names)"
            ),
            r'\$[0-9,]+\s*(million|billion|dollars?)': (
                0.9, "Large money offer (likely scam)"
            ),
            r'congratulations.*?(won|winner|prize)': (
                0.9, "Prize/lottery scam"
            )
        }
        
        try:
            for pattern, (confidence, reason) in patterns.items():
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    phrase = match.group(0)
                    suspicious_phrases.append((phrase, confidence, reason))
            
            return suspicious_phrases
            
        except Exception as e:
            logger.error(f"Error extracting suspicious phrases: {e}")
            return []
    
    def clean_html(self, html_content: str) -> str:
        """Clean HTML content for analysis"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text and clean it
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            logger.error(f"Error cleaning HTML: {e}")
            return html_content
