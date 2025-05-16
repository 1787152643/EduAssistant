# tests2/test_users.py
from locust import HttpUser, task, between, TaskSet
import random
import json
import time
import config
import string

class AuthenticationUser(HttpUser):
    """User class for testing authentication functionality"""
    wait_time = between(1, 3)
    
    @task(3)
    def login_test(self):
        # Test login with valid credentials
        credentials = random.choice(config.TEST_CREDENTIALS)
        with self.client.post("/login", data=credentials, catch_response=True) as response:
            if response.status_code in [200, 302]:
                response.success()
            else:
                response.failure(f"Login failed with status {response.status_code}")
    
    @task(1)
    def register_test(self):
        # Test registration with unique credentials
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        new_user = {
            "username": f"test_user_{random_suffix}",
            "password": "123456",
            "email": f"test_{random_suffix}@example.com",
            "name": f"Test User {random_suffix}"
        }
        
        with self.client.post("/register", data=new_user, catch_response=True) as response:
            if response.status_code in [200, 302]:
                response.success()
            else:
                response.failure(f"Registration failed with status {response.status_code}")

class CourseUser(HttpUser):
    """User class for testing course functionality"""
    wait_time = between(3, 7)
    
    def on_start(self):
        # Login first
        self.client.post("/login", data=random.choice(config.TEST_CREDENTIALS))
    
    @task(5)
    def view_courses(self):
        # Test course listing
        with self.client.get("/course/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Course listing failed with status {response.status_code}")
    
    @task(3)
    def view_course_details(self):
        # Test course detail views
        course_id = random.randint(1, 5)
        with self.client.get(f"/course/{course_id}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Course detail view failed with status {response.status_code}")
    
    @task(1)
    def enroll_course(self):
        # Test enrollment process
        course_id = random.randint(1, 5)
        with self.client.post(f"/course/{course_id}/enroll", data={}, catch_response=True) as response:
            if response.status_code in [200, 302]:
                response.success()
            else:
                response.failure(f"Course enrollment failed with status {response.status_code}")

class AssignmentUser(HttpUser):
    """User class for testing assignment functionality"""
    wait_time = between(5, 10)
    
    def on_start(self):
        # Login first
        self.client.post("/login", data=random.choice(config.TEST_CREDENTIALS))
    
    @task(3)
    def view_assignments(self):
        # View assignments for a course
        course_id = random.randint(1, 5)
        with self.client.get(f"/course/{course_id}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Viewing assignments failed with status {response.status_code}")
    
    @task(1)
    def submit_assignment(self):
        # Submit an assignment
        assignment_id = random.randint(1, 10)
        submission_data = {
            "content": f"This is a test submission for assignment {assignment_id}."
        }
        
        with self.client.post(f"/course/assignment/{assignment_id}/submit", 
                            data=submission_data, catch_response=True) as response:
            if response.status_code in [200, 302]:
                response.success()
            else:
                response.failure(f"Assignment submission failed with status {response.status_code}")

class KnowledgeBaseUser(HttpUser):
    """User class for testing knowledge base search"""
    wait_time = between(2, 5)
    
    def on_start(self):
        # Login first
        self.client.post("/login", data=random.choice(config.TEST_CREDENTIALS))
    
    @task
    def search_knowledge_base(self):
        # Test search functionality with different queries
        queries = [
            "machine learning",
            "database design",
            "programming basics",
            "algorithms"
        ]
        
        query = random.choice(queries)
        with self.client.get(f"/search/?q={query}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Knowledge base search failed with status {response.status_code}")

class AnalyticsUser(HttpUser):
    """User class for testing analytics functionality"""
    wait_time = between(5, 15)
    
    def on_start(self):
        # Login with appropriate credentials based on role
        is_teacher = random.choice([True, False])
        if is_teacher:
            self.is_teacher = True
            self.client.post("/login", data={"username": "prof_zhang", "password": "123456"})
        else:
            self.is_teacher = False
            self.client.post("/login", data={"username": "student001", "password": "123456"})
    
    @task
    def view_analytics(self):
        if self.is_teacher:
            # Teacher viewing course analytics
            course_id = random.randint(1, 5)
            with self.client.get(f"/analytics/course/{course_id}", catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Course analytics failed with status {response.status_code}")
        else:
            # Student viewing personal analytics
            with self.client.get("/analytics/", catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Personal analytics failed with status {response.status_code}")