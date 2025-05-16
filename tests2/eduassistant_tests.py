# tests2/eduassistant_tests.py
from locust import HttpUser, task, between, events
import json
import random
import time
import os
from test_users import AuthenticationUser, CourseUser, AssignmentUser, KnowledgeBaseUser, AnalyticsUser
import config

# Create results directory if it doesn't exist
os.makedirs(config.RESULTS_DIR, exist_ok=True)

# Define test stages
TEST_STAGES = [
    {"name": "authentication", "user_class": AuthenticationUser, 
     "weight": 1, "users": config.AUTH_USERS, "duration": config.AUTH_DURATION},
    {"name": "courses", "user_class": CourseUser, 
     "weight": 1, "users": config.COURSE_USERS, "duration": config.COURSE_DURATION},
    {"name": "assignments", "user_class": AssignmentUser, 
     "weight": 1, "users": config.ASSIGNMENT_USERS, "duration": config.ASSIGNMENT_DURATION},
    {"name": "knowledge_base", "user_class": KnowledgeBaseUser, 
     "weight": 1, "users": config.KB_USERS, "duration": config.KB_DURATION},
    {"name": "analytics", "user_class": AnalyticsUser, 
     "weight": 1, "users": config.ANALYTICS_USERS, "duration": config.ANALYTICS_DURATION},
    {"name": "combined", "user_class": [AuthenticationUser, CourseUser, AssignmentUser, 
                                       KnowledgeBaseUser, AnalyticsUser], 
     "weight": [1, 3, 3, 2, 1], "users": config.COMBINED_USERS, "duration": config.COMBINED_DURATION}
]

# Store start time as a global variable
test_start_time = None

# Record start time of test
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    global test_start_time
    test_start_time = time.time()
    print(f"Test started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Log test configuration
    with open(os.path.join(config.RESULTS_DIR, "test_config.json"), "w") as f:
        json.dump({
            "server": config.SERVER_URL,
            "stages": [{"name": stage["name"], "users": stage["users"], "duration": stage["duration"]} 
                      for stage in TEST_STAGES],
            "start_time": time.strftime('%Y-%m-%d %H:%M:%S')
        }, f, indent=2)

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    global test_start_time
    print(f"Test completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total run time: {time.time() - test_start_time:.2f} seconds")