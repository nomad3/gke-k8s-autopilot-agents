#!/usr/bin/env bash
set -euo pipefail

# Simple smoke test for manual ingestion endpoints
# Requires backend running at http://localhost:3001 and a CSV file

BACKEND_URL="${BACKEND_URL:-http://localhost:3001}"
API="$BACKEND_URL/api"
TOKEN="${TOKEN:-}"
PRACTICE_ID="${PRACTICE_ID:-}"

if [[ -z "$TOKEN" || -z "$PRACTICE_ID" ]]; then
  echo "Usage: TOKEN=... PRACTICE_ID=... scripts/test-ingestion.sh"
  exit 1
fi

# Create a temp CSV
TMPCSV=$(mktemp /tmp/patients.XXXXXX.csv)
cat > "$TMPCSV" <<EOF
externalId,firstName,lastName,email,phone,dateOfBirth,gender,notes
E1001,John,Doe,john.doe@example.com,555-0101,1985-03-12,M,Imported via test
E1002,Jane,Smith,jane.smith@example.com,555-0102,1990-07-04,F,Imported via test
EOF

echo "Uploading CSV..."
JOB=$(curl -s -H "Authorization: Bearer $TOKEN" -F "practiceId=$PRACTICE_ID" -F "sourceSystem=manual" -F "dataset=patients" -F "file=@$TMPCSV" "$API/integrations/ingestion/upload" | jq -r '.job.id')
echo "Job: $JOB"

echo "Processing job..."
curl -s -H "Authorization: Bearer $TOKEN" -X POST "$API/integrations/ingestion/jobs/$JOB/process" | jq .

echo "Headers:"
curl -s -H "Authorization: Bearer $TOKEN" "$API/integrations/ingestion/jobs/$JOB/headers" | jq .

echo "Promoting to patients..."
curl -s -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"target":"patients","practiceId":"'$PRACTICE_ID'","sourceSystem":"manual","dataset":"patients","fieldMap":{"externalId":"externalId","firstName":"firstName","lastName":"lastName","email":"email","phone":"phone","dateOfBirth":"dateOfBirth","gender":"gender","notes":"notes"}}' \
  "$API/integrations/ingestion/jobs/$JOB/promote" | jq .

echo "Done."

