#!/bin/bash

# Simple test script for the Bank Phishing Detector API

set -e

API_BASE="http://localhost:8000"

echo "Testing Bank Phishing Detector API..."
echo "======================================"

# Test health endpoint
echo "1. Testing health endpoint..."
response=$(curl -s "$API_BASE/health")
if echo "$response" | grep -q '"status":"healthy"'; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    echo "Response: $response"
    exit 1
fi

# Test status endpoint
echo "\n2. Testing status endpoint..."
response=$(curl -s "$API_BASE/status")
if echo "$response" | grep -q '"service_status"'; then
    echo "✅ Status check passed"
else
    echo "❌ Status check failed"
    echo "Response: $response"
fi

# Test legitimate email analysis
echo "\n3. Testing legitimate email analysis..."
legitimate_email=$(cat examples/sample_emails/legitimate_bank_email.txt | sed 's/"/\\"/g' | tr '\n' '\\n')
payload=$(cat <<EOF
{
  "raw_email": "$legitimate_email"
}
EOF
)

response=$(curl -s -X POST "$API_BASE/analyze" \
  -H "Content-Type: application/json" \
  -d "$payload")

if echo "$response" | grep -q '"risk_score"'; then
    risk_score=$(echo "$response" | grep -o '"risk_score":[0-9.]*' | cut -d':' -f2)
    echo "✅ Legitimate email analysis completed (Risk Score: $risk_score)"
else
    echo "❌ Legitimate email analysis failed"
    echo "Response: $response"
fi

# Test phishing email analysis
echo "\n4. Testing phishing email analysis..."
phishing_email=$(cat examples/sample_emails/phishing_email.txt | sed 's/"/\\"/g' | tr '\n' '\\n')
payload=$(cat <<EOF
{
  "raw_email": "$phishing_email"
}
EOF
)

response=$(curl -s -X POST "$API_BASE/analyze" \
  -H "Content-Type: application/json" \
  -d "$payload")

if echo "$response" | grep -q '"risk_score"'; then
    risk_score=$(echo "$response" | grep -o '"risk_score":[0-9.]*' | cut -d':' -f2)
    is_phishing=$(echo "$response" | grep -o '"is_phishing":[^,]*' | cut -d':' -f2)
    echo "✅ Phishing email analysis completed (Risk Score: $risk_score, Is Phishing: $is_phishing)"
else
    echo "❌ Phishing email analysis failed"
    echo "Response: $response"
fi

echo "\n✅ All tests completed!"
echo "\nFor detailed API documentation, visit: $API_BASE/docs"
