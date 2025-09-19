import pytest
from models.deterministic_checker import DeterministicChecker
from schemas.response_schemas import DeterministicChecks, SuspiciousIndicator

class TestDeterministicChecker:
    def setup_method(self):
        self.checker = DeterministicChecker()
    
    def test_check_spf_pass(self):
        metadata = {"received_spf": "pass (example.com: domain of sender@example.com designates 192.168.1.1 as permitted sender)"}
        result = self.checker._check_spf(metadata)
        assert result is True
    
    def test_check_spf_fail(self):
        metadata = {"received_spf": "fail (example.com: domain of sender@example.com does not designate 192.168.1.1 as permitted sender)"}
        result = self.checker._check_spf(metadata)
        assert result is False
    
    def test_analyze_suspicious_urls(self):
        links = [
            "http://bit.ly/suspicious",
            "https://192.168.1.1/login",
            "http://secure-bankofamerica.phishing.com/verify"
        ]
        
        indicators = self.checker._analyze_urls(links)
        
        assert len(indicators) > 0
        assert all(isinstance(ind, SuspiciousIndicator) for ind in indicators)
        assert any("shortener" in ind.reason.lower() or "ip address" in ind.reason.lower() for ind in indicators)
    
    def test_analyze_suspicious_attachments(self):
        attachments = ["document.exe", "invoice.pdf", "script.js"]
        
        indicators = self.checker._analyze_attachments(attachments)
        
        # Should flag .exe and .js files
        suspicious_files = [ind for ind in indicators if ind.value in ["document.exe", "script.js"]]
        assert len(suspicious_files) >= 2
    
    def test_content_pattern_analysis(self):
        body_text = "URGENT! Your account will be suspended. Click here to verify your identity immediately."
        
        indicators = self.checker._analyze_content_patterns(body_text)
        
        assert len(indicators) > 0
        # Should detect urgent language and verification request
        urgent_indicators = [ind for ind in indicators if "urgent" in ind.reason.lower()]
        assert len(urgent_indicators) > 0
