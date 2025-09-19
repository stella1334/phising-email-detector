import email
import re
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from email.message import EmailMessage
from email.policy import default
import base64
from loguru import logger
from schemas.response_schemas import EmailMetadata
from utils.validators import URLValidator, EmailValidator
from utils.html_processor import HTMLProcessor

class EmailParser:
    """Email parsing and metadata extraction"""
    
    def __init__(self):
        self.html_processor = HTMLProcessor()
        self.url_validator = URLValidator()
        self.email_validator = EmailValidator()
    
    def parse_raw_email(self, raw_email: str) -> Tuple[EmailMetadata, str, str]:
        """Parse raw email and extract metadata
        
        Args:
            raw_email: Raw email content with headers
            
        Returns:
            Tuple of (metadata, html_body, text_body)
        """
        try:
            # Parse email
            msg = email.message_from_string(raw_email, policy=default)
            
            # Extract basic metadata
            metadata = EmailMetadata(
                sender=self._extract_email_address(msg.get('From', '')),
                reply_to=self._extract_email_address(msg.get('Reply-To', '')),
                subject=msg.get('Subject', ''),
                message_id=msg.get('Message-ID', ''),
                return_path=msg.get('Return-Path', ''),
                received_spf=msg.get('Received-SPF', ''),
                authentication_results=msg.get('Authentication-Results', '')
            )
            
            # Parse date
            date_str = msg.get('Date', '')
            if date_str:
                try:
                    metadata.received_date = email.utils.parsedate_to_datetime(date_str)
                except Exception as e:
                    logger.warning(f"Could not parse date '{date_str}': {e}")
            
            # Extract body content
            html_body, text_body = self._extract_body_content(msg)
            
            # Extract links from both HTML and text
            if html_body:
                _, html_links = self.html_processor.extract_text_and_links(html_body)
                metadata.links.extend(html_links)
            
            if text_body:
                text_links = self.url_validator.extract_urls(text_body)
                metadata.links.extend(text_links)
            
            # Remove duplicate links
            metadata.links = list(set(metadata.links))
            
            # Extract attachment information
            metadata.attachments = self._extract_attachments(msg)
            
            logger.info(f"Parsed email from {metadata.sender} with {len(metadata.links)} links and {len(metadata.attachments)} attachments")
            
            return metadata, html_body or '', text_body or ''
            
        except Exception as e:
            logger.error(f"Error parsing raw email: {e}")
            # Try to extract minimal information
            metadata = self._fallback_parse(raw_email)
            return metadata, '', raw_email
    
    def _extract_email_address(self, header_value: str) -> Optional[str]:
        """Extract email address from header value"""
        if not header_value:
            return None
        
        try:
            # Use email.utils to properly parse
            name, addr = email.utils.parseaddr(header_value)
            if addr:
                is_valid, normalized = self.email_validator.validate_email_address(addr)
                return normalized if is_valid else addr
            return None
        except Exception:
            # Fallback regex
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            match = re.search(email_pattern, header_value)
            return match.group(0) if match else None
    
    def _extract_body_content(self, msg: EmailMessage) -> Tuple[Optional[str], Optional[str]]:
        """Extract HTML and text body content
        
        Returns:
            Tuple of (html_body, text_body)
        """
        html_body = None
        text_body = None
        
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = part.get('Content-Disposition', '')
                    
                    # Skip attachments
                    if 'attachment' in content_disposition:
                        continue
                    
                    if content_type == 'text/html':
                        html_body = self._decode_content(part)
                    elif content_type == 'text/plain':
                        text_body = self._decode_content(part)
            else:
                # Single part message
                content_type = msg.get_content_type()
                if content_type == 'text/html':
                    html_body = self._decode_content(msg)
                elif content_type == 'text/plain':
                    text_body = self._decode_content(msg)
                else:
                    # Try to get content anyway
                    content = self._decode_content(msg)
                    if content:
                        if '<html' in content.lower() or '<body' in content.lower():
                            html_body = content
                        else:
                            text_body = content
            
            return html_body, text_body
            
        except Exception as e:
            logger.error(f"Error extracting body content: {e}")
            return None, None
    
    def _decode_content(self, part: EmailMessage) -> Optional[str]:
        """Decode email part content"""
        try:
            content = part.get_content()
            if isinstance(content, str):
                return content
            elif isinstance(content, bytes):
                # Try different encodings
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        return content.decode(encoding)
                    except UnicodeDecodeError:
                        continue
                # If all fail, decode with errors='ignore'
                return content.decode('utf-8', errors='ignore')
            return str(content)
        except Exception as e:
            logger.warning(f"Error decoding content: {e}")
            return None
    
    def _extract_attachments(self, msg: EmailMessage) -> List[str]:
        """Extract attachment filenames"""
        attachments = []
        
        try:
            for part in msg.walk():
                content_disposition = part.get('Content-Disposition', '')
                if 'attachment' in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        attachments.append(filename)
                    else:
                        # Try to get filename from Content-Disposition header
                        disposition_params = part.get_params(header='Content-Disposition')
                        if disposition_params:
                            for param_name, param_value in disposition_params:
                                if param_name.lower() == 'filename':
                                    attachments.append(param_value)
                                    break
                        else:
                            attachments.append('unnamed_attachment')
            
            return attachments
            
        except Exception as e:
            logger.warning(f"Error extracting attachments: {e}")
            return []
    
    def _fallback_parse(self, raw_email: str) -> EmailMetadata:
        """Fallback parsing when standard email parsing fails"""
        metadata = EmailMetadata()
        
        try:
            lines = raw_email.split('\n')
            
            # Extract basic headers with regex
            for line in lines:
                line = line.strip()
                if line.lower().startswith('from:'):
                    metadata.sender = self._extract_email_address(line[5:].strip())
                elif line.lower().startswith('reply-to:'):
                    metadata.reply_to = self._extract_email_address(line[9:].strip())
                elif line.lower().startswith('subject:'):
                    metadata.subject = line[8:].strip()
                elif line.lower().startswith('message-id:'):
                    metadata.message_id = line[11:].strip()
            
            # Extract links from entire content
            metadata.links = self.url_validator.extract_urls(raw_email)
            
            logger.warning("Used fallback parsing for malformed email")
            
        except Exception as e:
            logger.error(f"Fallback parsing also failed: {e}")
        
        return metadata
    
    def extract_header_analysis_data(self, metadata: EmailMetadata) -> Dict[str, Any]:
        """Extract data for header-based analysis"""
        analysis_data = {
            'has_sender': metadata.sender is not None,
            'has_reply_to': metadata.reply_to is not None,
            'sender_reply_to_match': False,
            'has_message_id': metadata.message_id is not None,
            'has_return_path': metadata.return_path is not None,
            'has_received_spf': metadata.received_spf is not None,
            'has_auth_results': metadata.authentication_results is not None,
            'link_count': len(metadata.links),
            'attachment_count': len(metadata.attachments),
            'suspicious_attachments': []
        }
        
        try:
            # Check if sender and reply-to match
            if metadata.sender and metadata.reply_to:
                analysis_data['sender_reply_to_match'] = (
                    metadata.sender.lower() == metadata.reply_to.lower()
                )
            
            # Check for suspicious attachment types
            suspicious_extensions = {
                '.exe', '.scr', '.bat', '.cmd', '.com', '.pif', '.jar', 
                '.zip', '.rar', '.7z', '.js', '.vbs', '.ps1'
            }
            
            for attachment in metadata.attachments:
                for ext in suspicious_extensions:
                    if attachment.lower().endswith(ext):
                        analysis_data['suspicious_attachments'].append({
                            'filename': attachment,
                            'extension': ext,
                            'reason': f'Potentially dangerous file type: {ext}'
                        })
                        break
            
        except Exception as e:
            logger.error(f"Error in header analysis: {e}")
        
        return analysis_data
    
    def get_body_for_analysis(self, html_body: str, text_body: str) -> str:
        """Get the best body content for analysis"""
        if html_body:
            # Extract clean text from HTML for analysis
            clean_text = self.html_processor.clean_html(html_body)
            return clean_text
        elif text_body:
            return text_body
        else:
            return ""
