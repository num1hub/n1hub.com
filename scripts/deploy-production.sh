#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Orchestrate production deployment for N1Hub v0.1.

Options:
    -d, --database-url URL    PostgreSQL connection string (required)
    -b, --backend-url URL      Backend API URL (for verification)
    -f, --frontend-url URL     Frontend URL (for verification)
    -s, --skip-migrations      Skip database migrations
    -v, --skip-validation      Skip environment validation
    -h, --help                 Show this help message

Environment Variables:
    DATABASE_URL               PostgreSQL connection string (alternative to -d)
    BACKEND_URL                Backend API URL (alternative to -b)
    FRONTEND_URL               Frontend URL (alternative to -f)

Examples:
    $0 --database-url postgresql://... --backend-url https://api.example.com
    DATABASE_URL=... BACKEND_URL=... $0
EOF
    exit 1
}

SKIP_MIGRATIONS=false
SKIP_VALIDATION=false
DATABASE_URL="${DATABASE_URL:-}"
BACKEND_URL="${BACKEND_URL:-}"
FRONTEND_URL="${FRONTEND_URL:-}"

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--database-url)
            DATABASE_URL="$2"
            shift 2
            ;;
        -b|--backend-url)
            BACKEND_URL="$2"
            shift 2
            ;;
        -f|--frontend-url)
            FRONTEND_URL="$2"
            shift 2
            ;;
        -s|--skip-migrations)
            SKIP_MIGRATIONS=true
            shift
            ;;
        -v|--skip-validation)
            SKIP_VALIDATION=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo -e "${RED}Error: Unknown option: $1${NC}" >&2
            usage
            ;;
    esac
done

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}N1Hub v0.1 Production Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Environment Validation
if [[ "$SKIP_VALIDATION" != "true" ]]; then
    echo -e "${YELLOW}Step 1: Validating environment...${NC}"
    if [[ -z "$DATABASE_URL" ]]; then
        echo -e "${RED}Error: DATABASE_URL is required${NC}" >&2
        exit 1
    fi
    
    # Validate backend environment
    python3 "${SCRIPT_DIR}/validate_env.py" --target backend 2>&1 | grep -q "Validation PASSED" || {
        echo -e "${RED}Backend environment validation failed${NC}" >&2
        exit 1
    }
    echo -e "${GREEN}✓ Environment validation passed${NC}"
    echo ""
else
    echo -e "${YELLOW}Skipping environment validation${NC}"
    echo ""
fi

# Step 2: Database Migrations
if [[ "$SKIP_MIGRATIONS" != "true" ]]; then
    echo -e "${YELLOW}Step 2: Running database migrations...${NC}"
    "${SCRIPT_DIR}/migrate.sh" --database-url "$DATABASE_URL" || {
        echo -e "${RED}Migration failed${NC}" >&2
        exit 1
    }
    echo ""
    
    # Verify migrations
    echo -e "${YELLOW}Step 3: Verifying migrations...${NC}"
    "${SCRIPT_DIR}/verify_migrations.sh" --database-url "$DATABASE_URL" || {
        echo -e "${RED}Migration verification failed${NC}" >&2
        exit 1
    }
    echo ""
else
    echo -e "${YELLOW}Skipping database migrations${NC}"
    echo ""
fi

# Step 4: Backend Health Check
if [[ -n "$BACKEND_URL" ]]; then
    echo -e "${YELLOW}Step 4: Checking backend health...${NC}"
    HEALTH_RESPONSE=$(curl -s "${BACKEND_URL}/healthz" || echo "")
    if [[ -z "$HEALTH_RESPONSE" ]]; then
        echo -e "${RED}✗ Backend health check failed (no response)${NC}"
        echo "  URL: ${BACKEND_URL}/healthz"
    elif echo "$HEALTH_RESPONSE" | grep -q '"status":"ok"'; then
        echo -e "${GREEN}✓ Backend is healthy${NC}"
    else
        echo -e "${YELLOW}⚠ Backend health check returned: $HEALTH_RESPONSE${NC}"
    fi
    echo ""
fi

# Step 5: Frontend Check
if [[ -n "$FRONTEND_URL" ]]; then
    echo -e "${YELLOW}Step 5: Checking frontend...${NC}"
    FRONTEND_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${FRONTEND_URL}" || echo "000")
    if [[ "$FRONTEND_RESPONSE" == "200" ]]; then
        echo -e "${GREEN}✓ Frontend is accessible${NC}"
    else
        echo -e "${YELLOW}⚠ Frontend returned HTTP $FRONTEND_RESPONSE${NC}"
    fi
    echo ""
fi

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Deployment orchestration complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Verify backend: curl ${BACKEND_URL:-<backend-url>}/healthz"
if [[ -n "$FRONTEND_URL" ]]; then
    echo "  2. Visit frontend: $FRONTEND_URL"
fi
echo "  3. Run end-to-end tests"
echo "  4. Monitor observability endpoints"
