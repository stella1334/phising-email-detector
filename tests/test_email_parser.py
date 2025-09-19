import pytest
from models.email_parser import EmailParser
from schemas.response_schemas import EmailMetadata

class TestEmailParser:
    def setup_method(self):
        self.parser = EmailParser()
    
    def test_parse_simple_email(self):
        raw_email = """From: sender@example.com
To: recipient@bank.com
Subject: Test Email
Message-ID: <12345@example.com>

This is a test email body."""
        
        metadata, html_body, text_body = self.parser.parse_raw_email(raw_email)
        
        assert isinstance(metadata, EmailMetadata)
        assert metadata.sender == "sender@example.com"
        assert metadata.subject == "Test Email"
        assert metadata.message_id == "<12345@example.com>"
        assert text_body == "This is a test email body."
    
    def test_extract_email_address(self):
        # Test various email formats
        test_cases = [
            ("John Doe <john@example.com>", "john@example.com"),
            ("jane@example.com", "jane@example.com"),
            ("<admin@bank.com>", "admin@bank.com"),
            ("", None),
            ("Invalid email", None)
        ]
        
        for header_value, expected in test_cases:
            result = self.parser._extract_email_address(header_value)
            assert result == expected
    
    def test_fallback_parse(self):
        # Test with malformed email
        raw_email = "This is not a proper email format"
        metadata, html_body, text_body = self.parser.parse_raw_email(raw_email)
        
        assert isinstance(metadata, EmailMetadata)
        # Should return original content as text_body
        assert text_body == raw_email
