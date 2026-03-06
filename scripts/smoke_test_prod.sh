#!/bin/bash
# Backend smoke test for production (teski-zj2gsg.fly.dev)
# Usage: ./smoke_test_prod.sh [BASE_URL]
# Captures all responses and status codes for STABILITY_REPORT.md

set -e
BASE_URL="${1:-https://teski-zj2gsg.fly.dev}"
TIMESTAMP=$(date +%s)
TEST_EMAIL="smoke-${TIMESTAMP}@teski-smoke.test"
TEST_PASSWORD="SmokeTest123!"

echo "=== Teski Backend Smoke Test ==="
echo "Base URL: $BASE_URL"
echo "Started: $(date -Iseconds)"
echo ""

# 1. Health check
echo "--- 1. GET /health ---"
HEALTH=$(curl -s -w "\n%{http_code}" "$BASE_URL/health")
HEALTH_BODY=$(echo "$HEALTH" | head -n -1)
HEALTH_CODE=$(echo "$HEALTH" | tail -n 1)
echo "Status: $HEALTH_CODE"
echo "Response: $HEALTH_BODY"
echo ""

# 2. CORS debug
echo "--- 2. GET /api/debug/cors ---"
CORS=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/debug/cors")
CORS_BODY=$(echo "$CORS" | head -n -1)
CORS_CODE=$(echo "$CORS" | tail -n 1)
echo "Status: $CORS_CODE"
echo "Response: $CORS_BODY"
echo ""

# 3. Exercise list
echo "--- 3. GET /api/ex/list ---"
EX_LIST=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/ex/list")
EX_LIST_BODY=$(echo "$EX_LIST" | head -n -1)
EX_LIST_CODE=$(echo "$EX_LIST" | tail -n 1)
echo "Status: $EX_LIST_CODE"
echo "Response: $EX_LIST_BODY"
FIRST_EX_ID=$(echo "$EX_LIST_BODY" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "First exercise ID: $FIRST_EX_ID"
echo ""

# 4. Exercise get (if we have an ID)
if [ -n "$FIRST_EX_ID" ]; then
  echo "--- 4. GET /api/ex/get?id=$FIRST_EX_ID ---"
  EX_GET=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/ex/get?id=$FIRST_EX_ID")
  EX_GET_BODY=$(echo "$EX_GET" | head -n -1)
  EX_GET_CODE=$(echo "$EX_GET" | tail -n 1)
  echo "Status: $EX_GET_CODE"
  echo "Response: $EX_GET_BODY"
else
  echo "--- 4. GET /api/ex/get (skipped - no exercises) ---"
  EX_GET_CODE="SKIP"
  EX_GET_BODY="No exercises in list"
fi
echo ""

# 5. Auth - Signup
echo "--- 5. POST /auth/signup ---"
SIGNUP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/auth/signup" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\",\"display_name\":\"Smoke Test\"}")
SIGNUP_BODY=$(echo "$SIGNUP" | head -n -1)
SIGNUP_CODE=$(echo "$SIGNUP" | tail -n 1)
echo "Status: $SIGNUP_CODE"
echo "Response: $SIGNUP_BODY"
TOKEN=$(echo "$SIGNUP_BODY" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
USER_ID=$(echo "$SIGNUP_BODY" | grep -o '"user_id":"[^"]*"' | cut -d'"' -f4)
echo "Token: ${TOKEN:0:20}..."
echo "User ID: $USER_ID"
echo ""

# 6. Onboarding status (requires auth)
echo "--- 6. GET /api/onboarding/status ---"
if [ -n "$TOKEN" ]; then
  ONBOARD_STATUS=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/onboarding/status" \
    -H "Authorization: Bearer $TOKEN")
  ONBOARD_STATUS_BODY=$(echo "$ONBOARD_STATUS" | head -n -1)
  ONBOARD_STATUS_CODE=$(echo "$ONBOARD_STATUS" | tail -n 1)
else
  ONBOARD_STATUS_CODE="SKIP"
  ONBOARD_STATUS_BODY="No token from signup"
fi
echo "Status: $ONBOARD_STATUS_CODE"
echo "Response: $ONBOARD_STATUS_BODY"
echo ""

# 7. Onboarding submit (requires auth)
echo "--- 7. POST /api/onboarding/submit ---"
if [ -n "$TOKEN" ]; then
  ONBOARD_SUBMIT=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/onboarding/submit" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"motivation_style":"mentor","difficulty_preference":"balanced","daily_minutes_target":15,"skipped":false}')
  ONBOARD_SUBMIT_BODY=$(echo "$ONBOARD_SUBMIT" | head -n -1)
  ONBOARD_SUBMIT_CODE=$(echo "$ONBOARD_SUBMIT" | tail -n 1)
else
  ONBOARD_SUBMIT_CODE="SKIP"
  ONBOARD_SUBMIT_BODY="No token"
fi
echo "Status: $ONBOARD_SUBMIT_CODE"
echo "Response: $ONBOARD_SUBMIT_BODY"
echo ""

# 8. Exercise submit (requires user_id, exercise_id, answer)
echo "--- 8. POST /api/ex/answer ---"
if [ -n "$USER_ID" ] && [ -n "$FIRST_EX_ID" ]; then
  EX_ANSWER=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/ex/answer" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "{\"user_id\":\"$USER_ID\",\"exercise_id\":\"$FIRST_EX_ID\",\"answer\":\"0\"}")
  EX_ANSWER_BODY=$(echo "$EX_ANSWER" | head -n -1)
  EX_ANSWER_CODE=$(echo "$EX_ANSWER" | tail -n 1)
else
  EX_ANSWER_CODE="SKIP"
  EX_ANSWER_BODY="Missing user_id or exercise_id"
fi
echo "Status: $EX_ANSWER_CODE"
echo "Response: $EX_ANSWER_BODY"
echo ""

# 9. Explanations - text-only (frontend uses /explanations/generate)
echo "--- 9. POST /explanations/generate (text) ---"
EXPLAIN=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/explanations/generate" \
  -H "Content-Type: application/json" \
  -d '{"text":"What is 2+2?","mode":"big_picture"}')
EXPLAIN_BODY=$(echo "$EXPLAIN" | head -n -1)
EXPLAIN_CODE=$(echo "$EXPLAIN" | tail -n 1)
echo "Status: $EXPLAIN_CODE"
echo "Response: $EXPLAIN_BODY"
echo ""

# 10. Explanations - exercise-based (if we have exercise)
if [ -n "$FIRST_EX_ID" ]; then
  echo "--- 10. POST /explanations/generate (exercise_id) ---"
  EXPLAIN_EX=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/explanations/generate" \
    -H "Content-Type: application/json" \
    -d "{\"exercise_id\":\"$FIRST_EX_ID\",\"user_answer\":\"0\"}")
  EXPLAIN_EX_BODY=$(echo "$EXPLAIN_EX" | head -n -1)
  EXPLAIN_EX_CODE=$(echo "$EXPLAIN_EX" | tail -n 1)
  echo "Status: $EXPLAIN_EX_CODE"
  echo "Response: $EXPLAIN_EX_BODY"
else
  echo "--- 10. POST /api/explanations/generate (exercise) - skipped ---"
  EXPLAIN_EX_CODE="SKIP"
fi
echo ""

# Summary
echo "=== Summary ==="
echo "Health: $HEALTH_CODE | CORS: $CORS_CODE | ExList: $EX_LIST_CODE | ExGet: $EX_GET_CODE"
echo "Signup: $SIGNUP_CODE | OnboardStatus: $ONBOARD_STATUS_CODE | OnboardSubmit: $ONBOARD_SUBMIT_CODE"
echo "ExAnswer: $EX_ANSWER_CODE | Explain: $EXPLAIN_CODE | ExplainEx: $EXPLAIN_EX_CODE"
echo ""
echo "Completed: $(date -Iseconds)"
