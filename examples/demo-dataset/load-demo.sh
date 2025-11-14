#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCS_DIR="${SCRIPT_DIR}/documents"
API_URL="${API_URL:-http://127.0.0.1:8000}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}>>> Loading N1Hub v0.1 Demo Dataset${NC}"
echo "API URL: $API_URL"
echo ""

# Check if API is available
if ! curl -s "${API_URL}/healthz" > /dev/null 2>&1; then
    echo -e "${YELLOW}Warning: API not available at ${API_URL}${NC}"
    echo "Please start the backend first: npm run dev:stack:unix"
    exit 1
fi

# Function to upload a document
upload_document() {
    local file_path="$1"
    local title=$(head -n 1 "$file_path" | sed 's/^Title: //')
    local content=$(tail -n +2 "$file_path")
    
    # Extract tags from filename (remove .txt, split by -)
    local basename=$(basename "$file_path" .txt)
    local tags=$(echo "$basename" | tr '-' ' ' | tr '[:upper:]' '[:lower:]')
    local tag_array=$(echo "$tags" | awk '{for(i=1;i<=NF;i++) printf "\"%s\"%s", $i, (i<NF?", ":"")}')
    
    echo -e "${YELLOW}Uploading: $title${NC}"
    
    local response=$(curl -s -X POST "${API_URL}/ingest" \
        -H "Content-Type: application/json" \
        -d "{
            \"title\": \"$title\",
            \"content\": $(echo "$content" | jq -Rs .),
            \"tags\": [$tag_array],
            \"include_in_rag\": true
        }")
    
    local job_id=$(echo "$response" | jq -r '.job_id // empty')
    
    if [ -z "$job_id" ] || [ "$job_id" = "null" ]; then
        echo -e "  ${YELLOW}⚠ Upload may have failed${NC}"
        echo "  Response: $response"
    else
        echo -e "  ${GREEN}✓ Job created: $job_id${NC}"
    fi
    
    echo ""
}

# Upload all documents
if [ ! -d "$DOCS_DIR" ]; then
    echo "Documents directory not found: $DOCS_DIR"
    exit 1
fi

echo "Found documents:"
ls -1 "$DOCS_DIR"/*.txt 2>/dev/null | while read -r file; do
    echo "  - $(basename "$file")"
done
echo ""

# Upload each document
for file in "$DOCS_DIR"/*.txt; do
    if [ -f "$file" ]; then
        upload_document "$file"
        sleep 1  # Rate limiting consideration
    fi
done

echo -e "${GREEN}>>> Demo dataset loading complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Check job status: curl ${API_URL}/jobs"
echo "  2. Wait for jobs to complete (check /inbox)"
echo "  3. List capsules: curl ${API_URL}/capsules"
echo "  4. Try example queries from queries.md"
