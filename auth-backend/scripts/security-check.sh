#!/bin/bash
# Security Check Script
# Runs security scans locally before committing

set -e

echo "🔒 Running Security Scans..."
echo ""

# Colors
GREEN='\033[0.32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if in virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Warning: Not in virtual environment. Activating...${NC}"
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo -e "${RED}Error: venv not found. Run: python -m venv venv${NC}"
        exit 1
    fi
fi

# Install security tools if not present
echo "📦 Checking security tools..."
pip install safety bandit --quiet

echo ""
echo "=" echo "1️⃣  Running Safety (Dependency Vulnerabilities)"
echo "================================================"
safety check --json > safety-report.json || true
safety check || echo -e "${YELLOW}⚠️  Some vulnerabilities found${NC}"

echo ""
echo "================================================"
echo "2️⃣  Running Bandit (Security Linter)"
echo "================================================"
bandit -r app/ core/ infra/ -ll -f screen || echo -e "${YELLOW}⚠️  Some security issues found${NC}"

echo ""
echo "================================================"
echo "3️⃣  Checking for Hardcoded Secrets"
echo "================================================"

# Check for common secrets patterns
if grep -r "password.*=.*['\"].*['\"]" app/ core/ infra/ --include="*.py" | grep -v "field_validator\|Field\|BaseModel"; then
    echo -e "${RED}❌ Potential hardcoded passwords found${NC}"
else
    echo -e "${GREEN}✅ No hardcoded passwords found${NC}"
fi

if grep -r "api_key.*=.*['\"].*['\"]" app/ core/ infra/ --include="*.py" | grep -v "os.getenv\|settings"; then
    echo -e "${RED}❌ Potential hardcoded API keys found${NC}"
else
    echo -e "${GREEN}✅ No hardcoded API keys found${NC}"
fi

if grep -r "secret.*=.*['\"].*['\"]" app/ core/ infra/ --include="*.py" | grep -v "os.getenv\|settings\|SecretStr"; then
    echo -e "${RED}❌ Potential hardcoded secrets found${NC}"
else
    echo -e "${GREEN}✅ No hardcoded secrets found${NC}"
fi

echo ""
echo "================================================"
echo "4️⃣  Checking Environment Variables"
echo "================================================"

if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found${NC}"
else
    echo -e "${GREEN}✅ .env file exists${NC}"
    
    # Check for required variables
    required_vars=("JWT_SECRET" "DATABASE_URL" "REDIS_HOST")
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" .env; then
            echo -e "${GREEN}✅ $var is set${NC}"
        else
            echo -e "${RED}❌ $var is missing${NC}"
        fi
    done
fi

echo ""
echo "================================================"
echo "📊 Summary"
echo "================================================"
echo "Reports generated:"
echo "  - safety-report.json"
echo ""
echo -e "${GREEN}✅ Security scan complete!${NC}"
echo ""
echo "To fix issues:"
echo "  1. Update vulnerable dependencies: pip install --upgrade <package>"
echo "  2. Review bandit findings and fix high/medium issues"
echo "  3. Remove any hardcoded secrets"
echo ""

