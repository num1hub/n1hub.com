#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SQL_DIR="${REPO_ROOT}/infra/sql"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Run database migrations for N1Hub v0.1.

Options:
    -d, --database-url URL    PostgreSQL connection string (required)
    -n, --dry-run            Show what would be executed without running
    -h, --help               Show this help message

Environment Variables:
    DATABASE_URL             PostgreSQL connection string (alternative to -d)

Examples:
    $0 --database-url postgresql://user:pass@localhost:5432/n1hub
    DATABASE_URL=postgresql://... $0
    $0 --dry-run --database-url postgresql://...
EOF
    exit 1
}

DRY_RUN=false
DATABASE_URL="${DATABASE_URL:-}"

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--database-url)
            DATABASE_URL="$2"
            shift 2
            ;;
        -n|--dry-run)
            DRY_RUN=true
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

if [[ -z "$DATABASE_URL" ]]; then
    echo -e "${RED}Error: DATABASE_URL is required${NC}" >&2
    echo "Use -d/--database-url or set DATABASE_URL environment variable"
    exit 1
fi

# Migration files in order
mapfile -t MIGRATIONS < <(find "$SQL_DIR" -maxdepth 1 -type f -name '[0-9][0-9][0-9][0-9]_*.sql' -print | sort)

if [[ ${#MIGRATIONS[@]} -eq 0 ]]; then
    echo -e "${RED}Error: no migration files found in ${SQL_DIR}${NC}" >&2
    exit 1
fi

echo -e "${GREEN}>>> N1Hub Database Migration Runner${NC}"
echo "Database: ${DATABASE_URL%%@*}@***"
echo ""

if [[ "$DRY_RUN" == "true" ]]; then
    echo -e "${YELLOW}[DRY RUN] Would execute the following migrations:${NC}"
    for migration_path in "${MIGRATIONS[@]}"; do
        migration_file="$(basename "$migration_path")"
        if [[ -f "$migration_path" ]]; then
            echo "  - $migration_file"
        else
            echo -e "  ${RED}- $migration_file (NOT FOUND)${NC}"
        fi
    done
    exit 0
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
    echo "Please check your DATABASE_URL and ensure the database is accessible"
    exit 1
fi
echo -e "${GREEN}✓ Database connection successful${NC}"
echo ""

# Run migrations
SUCCESS_COUNT=0
FAILED_MIGRATIONS=()

for migration_path in "${MIGRATIONS[@]}"; do
    migration_file="$(basename "$migration_path")"

    if [[ ! -f "$migration_path" ]]; then
        echo -e "${RED}✗ Migration file not found: $migration_file${NC}"
        FAILED_MIGRATIONS+=("$migration_file")
        continue
    fi

    echo -e "${YELLOW}Running migration: $migration_file${NC}"

    if psql "$DATABASE_URL" -f "$migration_path" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Migration completed: $migration_file${NC}"
        ((SUCCESS_COUNT++))
    else
        echo -e "${RED}✗ Migration failed: $migration_file${NC}"
        FAILED_MIGRATIONS+=("$migration_file")
        # Show error details
        psql "$DATABASE_URL" -f "$migration_path" 2>&1 | tail -5
    fi
    echo ""
done

# Summary
echo "=========================================="
if [[ ${#FAILED_MIGRATIONS[@]} -eq 0 ]]; then
    echo -e "${GREEN}✓ All migrations completed successfully${NC}"
    echo "Total migrations: ${#MIGRATIONS[@]}"
    exit 0
else
    echo -e "${RED}✗ Some migrations failed${NC}"
    echo "Successful: $SUCCESS_COUNT / ${#MIGRATIONS[@]}"
    echo "Failed migrations:"
    for failed in "${FAILED_MIGRATIONS[@]}"; do
        echo "  - $failed"
    done
    exit 1
fi
