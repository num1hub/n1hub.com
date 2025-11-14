#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Verify database migrations have been applied correctly.

Options:
    -d, --database-url URL    PostgreSQL connection string (required)
    -h, --help               Show this help message

Environment Variables:
    DATABASE_URL             PostgreSQL connection string (alternative to -d)

Examples:
    $0 --database-url postgresql://user:pass@localhost:5432/n1hub
    DATABASE_URL=postgresql://... $0
EOF
    exit 1
}

DATABASE_URL="${DATABASE_URL:-}"

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--database-url)
            DATABASE_URL="$2"
            shift 2
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

if [[ -z "$DATABASE_URL" ]]; then
    echo -e "${RED}Error: DATABASE_URL is required${NC}" >&2
    echo "Use -d/--database-url or set DATABASE_URL environment variable"
    exit 1
fi

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo -e "${RED}Error: psql command not found. Please install PostgreSQL client tools.${NC}" >&2
    exit 1
fi

# Test database connection
echo "Testing database connection..."
if ! psql "$DATABASE_URL" -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${RED}Error: Failed to connect to database${NC}" >&2
    exit 1
fi
echo -e "${GREEN}✓ Database connection successful${NC}"
echo ""

# Required tables (from all migrations)
REQUIRED_TABLES=(
    "capsules"
    "capsule_vectors"
    "links"
    "jobs"
    "artifacts"
    "query_logs"
    "validation_runs"
    "link_suggestions"
    "audit_logs"
)

# Required extensions
REQUIRED_EXTENSIONS=(
    "uuid-ossp"
    "vector"
)

# Check extensions
echo "Checking PostgreSQL extensions..."
MISSING_EXTENSIONS=()
for ext in "${REQUIRED_EXTENSIONS[@]}"; do
    if psql "$DATABASE_URL" -tAc "SELECT 1 FROM pg_extension WHERE extname='$ext';" | grep -q 1; then
        echo -e "${GREEN}✓ Extension installed: $ext${NC}"
    else
        echo -e "${RED}✗ Extension missing: $ext${NC}"
        MISSING_EXTENSIONS+=("$ext")
    fi
done
echo ""

# Check tables
echo "Checking required tables..."
MISSING_TABLES=()
for table in "${REQUIRED_TABLES[@]}"; do
    if psql "$DATABASE_URL" -tAc "SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$table';" | grep -q 1; then
        # Get row count for verification
        row_count=$(psql "$DATABASE_URL" -tAc "SELECT COUNT(*) FROM $table;" 2>/dev/null || echo "0")
        echo -e "${GREEN}✓ Table exists: $table (rows: $row_count)${NC}"
    else
        echo -e "${RED}✗ Table missing: $table${NC}"
        MISSING_TABLES+=("$table")
    fi
done
echo ""

# Check indexes (critical ones)
echo "Checking critical indexes..."
CRITICAL_INDEXES=(
    "idx_capsule_vectors_capsule_id"
    "idx_links_src"
    "idx_links_dst"
    "idx_query_logs_query_hash"
    "idx_audit_logs_capsule_id"
)

MISSING_INDEXES=()
for idx in "${CRITICAL_INDEXES[@]}"; do
    if psql "$DATABASE_URL" -tAc "SELECT 1 FROM pg_indexes WHERE indexname='$idx';" | grep -q 1; then
        echo -e "${GREEN}✓ Index exists: $idx${NC}"
    else
        echo -e "${YELLOW}⚠ Index missing: $idx (may be created automatically)${NC}"
        MISSING_INDEXES+=("$idx")
    fi
done
echo ""

# Summary
echo "=========================================="
ISSUES=0

if [[ ${#MISSING_EXTENSIONS[@]} -gt 0 ]]; then
    echo -e "${RED}✗ Missing extensions:${NC}"
    for ext in "${MISSING_EXTENSIONS[@]}"; do
        echo "  - $ext"
    done
    ISSUES=$((ISSUES + ${#MISSING_EXTENSIONS[@]}))
fi

if [[ ${#MISSING_TABLES[@]} -gt 0 ]]; then
    echo -e "${RED}✗ Missing tables:${NC}"
    for table in "${MISSING_TABLES[@]}"; do
        echo "  - $table"
    done
    ISSUES=$((ISSUES + ${#MISSING_TABLES[@]}))
fi

# Check vector dimension from migration 0004
echo "Checking capsule vector dimension..."
VECTOR_TYPE=$(psql "$DATABASE_URL" -tAc "SELECT format_type(atttypid, atttypmod) FROM pg_attribute WHERE attrelid = 'capsule_vectors'::regclass AND attname = 'embedding';")
if [[ "${VECTOR_TYPE//[[:space:]]/}" != "vector(384)" ]]; then
    echo -e "${RED}✗ Unexpected embedding column type: ${VECTOR_TYPE}${NC}"
    ISSUES=$((ISSUES + 1))
else
    echo -e "${GREEN}✓ Embedding column matches vector(384)${NC}"
fi
echo ""

if [[ $ISSUES -eq 0 ]]; then
    echo -e "${GREEN}✓ All migrations verified successfully${NC}"
    echo "Required tables: ${#REQUIRED_TABLES[@]}"
    echo "Required extensions: ${#REQUIRED_EXTENSIONS[@]}"
    exit 0
else
    echo -e "${RED}✗ Migration verification failed${NC}"
    echo "Total issues found: $ISSUES"
    echo ""
    echo "Run migrations with: ./scripts/migrate.sh --database-url $DATABASE_URL"
    exit 1
fi
