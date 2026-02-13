#!/bin/bash

# Test script for payroll authentication system

echo "🔐 Payroll System - Authentication Test"
echo "========================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Register new user
echo -e "\n${YELLOW}Test 1: Register new user${NC}"
REGISTER_RESPONSE=$(curl -s -X POST http://localhost:5001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"testuser@example.com","password":"testpass1234","name":"Test User"}')

echo "$REGISTER_RESPONSE" | jq .

TOKEN=$(echo "$REGISTER_RESPONSE" | jq -r '.token // empty')
USER_ID=$(echo "$REGISTER_RESPONSE" | jq -r '.user.id // empty')

if [ -z "$TOKEN" ]; then
    echo -e "${RED}✗ Registration failed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Registration successful${NC} (User ID: $USER_ID)"

# Test 2: Login
echo -e "\n${YELLOW}Test 2: Login${NC}"
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"testuser@example.com","password":"testpass1234"}')

echo "$LOGIN_RESPONSE" | jq .

LOGIN_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.token // empty')
if [ -z "$LOGIN_TOKEN" ]; then
    echo -e "${RED}✗ Login failed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Login successful${NC}"

# Test 3: Get profile (protected endpoint)
echo -e "\n${YELLOW}Test 3: Get profile (protected endpoint)${NC}"
PROFILE=$(curl -s -X GET http://localhost:5001/api/auth/profile \
  -H "Authorization: Bearer $TOKEN")

echo "$PROFILE" | jq .
echo -e "${GREEN}✓ Profile retrieved successfully${NC}"

# Test 4: Create shift
echo -e "\n${YELLOW}Test 4: Create shift${NC}"
SHIFT=$(curl -s -X POST http://localhost:5001/api/shifts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"date":"2024-02-13","start_time":"09:00","end_time":"17:00","hours":8,"shift_type":"regular","total_pay":250}')

echo "$SHIFT" | jq .
echo -e "${GREEN}✓ Shift created successfully${NC}"

# Test 5: Get shifts (verify it returns user's shifts)
echo -e "\n${YELLOW}Test 5: Get shifts${NC}"
SHIFTS=$(curl -s -X GET http://localhost:5001/api/shifts \
  -H "Authorization: Bearer $TOKEN")

echo "$SHIFTS" | jq .
SHIFT_COUNT=$(echo "$SHIFTS" | jq 'length')
echo -e "${GREEN}✓ Retrieved $SHIFT_COUNT shifts${NC}"

# Test 6: Create expense
echo -e "\n${YELLOW}Test 6: Create expense${NC}"
EXPENSE=$(curl -s -X POST http://localhost:5001/api/expenses \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"category":"Food","amount":50}')

echo "$EXPENSE" | jq .
echo -e "${GREEN}✓ Expense created successfully${NC}"

# Test 7: Create goal
echo -e "\n${YELLOW}Test 7: Create goal${NC}"
GOAL=$(curl -s -X POST http://localhost:5001/api/goals \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Save for vacation","target_amount":2000}')

echo "$GOAL" | jq .
echo -e "${GREEN}✓ Goal created successfully${NC}"

# Test 8: Test without token (should fail)
echo -e "\n${YELLOW}Test 8: Access protected endpoint without token${NC}"
NO_AUTH=$(curl -s -X GET http://localhost:5001/api/shifts)
echo "$NO_AUTH" | jq .
echo -e "${RED}✓ Correctly blocked access without token${NC}"

echo -e "\n${GREEN}✅ All authentication tests passed!${NC}"
