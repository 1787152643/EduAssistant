# tests2/config.py
# EduAssistant Testing Configuration

# Server configuration
SERVER_URL = "http://124.71.46.184:5000"

# Results directory
RESULTS_DIR = "test_results"

# Test user credentials
TEST_CREDENTIALS = [
    {"username": "student001", "password": "123456"},
    {"username": "student002", "password": "123456"},
    {"username": "student003", "password": "123456"}
]

# Test parameters for each component
# Authentication testing
AUTH_USERS = 30
AUTH_DURATION = "3m"

# Course management testing
COURSE_USERS = 25
COURSE_DURATION = "3m"

# Assignment testing
ASSIGNMENT_USERS = 20
ASSIGNMENT_DURATION = "3m"

# Knowledge base testing
KB_USERS = 15
KB_DURATION = "3m"

# Analytics testing
ANALYTICS_USERS = 15
ANALYTICS_DURATION = "3m"

# Combined testing
COMBINED_USERS = 50
COMBINED_DURATION = "5m"

# User distribution for combined test (relative weights)
USER_DISTRIBUTION = {
    "authentication": 1,   # 10%
    "courses": 3,          # 30%
    "assignments": 3,      # 30%
    "knowledge_base": 2,   # 20%
    "analytics": 1,        # 10%
}

# Progressive user counts for scalability testing
SCALABILITY_USER_COUNTS = [5, 10, 20, 50, 100, 200]