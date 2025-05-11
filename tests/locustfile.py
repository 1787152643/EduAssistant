import json
import random
import time
import os
import datetime
from locust import HttpUser, task, between, tag, events
from locust.exception import StopUser
import statistics
import csv
from collections import defaultdict

# Test Configuration
CONFIG = {
    "host": "http://localhost:5000",
    "users": 10,          # Number of concurrent users
    "spawn_rate": 2,      # Users started per second
    "run_time": "10m",    # Test duration
    "output_dir": "locust_results",  # Directory to store results
    "test_name": f"ai_chat_test_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
    "simple_weight": 3,   # Task weight for simple messages
    "medium_weight": 2,   # Task weight for medium messages  
    "complex_weight": 1,  # Task weight for complex messages
    "wait_time_min": 5,   # Minimum wait time between tasks (seconds)
    "wait_time_max": 15,  # Maximum wait time between tasks (seconds)
    "chats_per_user": 5,  # Number of chat sessions to create per user
}

# Ensure output directory exists
os.makedirs(CONFIG["output_dir"], exist_ok=True)

# Global data for custom metrics tracking
response_data = defaultdict(list)
message_counts = defaultdict(int)
message_data = []  # Store individual message data for detailed analysis

class ChatUser(HttpUser):
    # Wait between configured seconds between tasks
    wait_time = between(CONFIG["wait_time_min"], CONFIG["wait_time_max"])
    
    # Store user state
    user_id = None
    username = None
    chat_ids = []
    
    def on_start(self):
        """Log in user when test starts"""
        self.login()
        self.create_test_chats()
    
    def login(self):
        """Log in to the application"""
        # Randomly select from test users
        test_users = [
            {"username": "student001", "password": "123456"},
            {"username": "student002", "password": "123456"},
            {"username": "student003", "password": "123456"}
        ]
        user_credentials = random.choice(test_users)
        
        # Login to the application
        response = self.client.post("/login", data=user_credentials)
        
        if response.status_code != 200:
            print(f"Login failed for {user_credentials['username']}")
            raise StopUser()
        
        self.username = user_credentials["username"]
        print(f"User {self.username} logged in successfully")
    
    def create_test_chats(self):
        """Create chat sessions for testing"""
        # Create configured number of chat sessions per user
        for _ in range(CONFIG["chats_per_user"]):
            response = self.client.post("/ai-assistant/chats", json={})
            if response.status_code == 200:
                chat_id = response.json().get("id")
                self.chat_ids.append(chat_id)
                print(f"User {self.username} created chat {chat_id}")
            else:
                print(f"Failed to create chat: {response.text}")
        
        if not self.chat_ids:
            print("No chat sessions created, stopping user")
            raise StopUser()
    
    @tag('send_message')
    @task(CONFIG["simple_weight"])
    def send_simple_message(self):
        """Send a simple message to a random chat"""
        self.check_and_renew_session()
        if not self.chat_ids:
            return
            
        chat_id = random.choice(self.chat_ids)
        simple_messages = [
            "What is machine learning?",
            "Explain object-oriented programming",
            "What are arrays in programming?",
            "Define artificial intelligence",
            "What is a database?",
            "How does the internet work?",
            "What is an algorithm?",
            "Define the term 'variable' in programming"
        ]
        
        message = random.choice(simple_messages)
        self._send_message(chat_id, message, "simple")
    
    @tag('send_message')
    @task(CONFIG["medium_weight"])
    def send_medium_message(self):
        """Send a medium complexity message to a random chat"""
        self.check_and_renew_session()
        if not self.chat_ids:
            return
            
        chat_id = random.choice(self.chat_ids)
        medium_messages = [
            "Compare supervised and unsupervised learning with examples of each",
            "Explain the differences between SQL and NoSQL databases. What are the use cases for each?",
            "What are the principles of clean code? Give me some examples of how to write maintainable code",
            "How do HTTP requests work? Explain the different request methods",
            "Explain the concept of inheritance in object-oriented programming with a practical example"
        ]
        
        message = random.choice(medium_messages)
        self._send_message(chat_id, message, "medium")
    
    @tag('send_message')
    @task(CONFIG["complex_weight"])
    def send_complex_message(self):
        """Send a complex message to a random chat"""
        self.check_and_renew_session()
        if not self.chat_ids:
            return
            
        chat_id = random.choice(self.chat_ids)
        complex_messages = [
            "I'm developing an educational app that needs to track student progress across various skills. What would be the best database schema design for this? Consider scalability and performance.",
            "Can you explain how neural networks work in depth? Include explanations of backpropagation, activation functions, and how different layer types affect learning capabilities.",
            "I need help designing a distributed system for a university that can handle course registration, grade tracking, and student performance analytics. What architecture would you recommend?"
        ]
        
        message = random.choice(complex_messages)
        self._send_message(chat_id, message, "complex")
    
    def _send_message(self, chat_id, message, complexity):
        """Helper method to send a message and record metrics"""
        payload = {"message": message}
        
        # Record custom start time to measure actual response time including network delays
        start_time = time.time()
        request_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with self.client.post(
            f"/ai-assistant/chats/{chat_id}/messages",
            json=payload,
            catch_response=True,
            name=f"Send {complexity} message"
        ) as response:
            duration = time.time() - start_time
            message_counts[complexity] += 1
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    response_content = result.get('ai_message', {}).get('content', '')
                    response_length = len(response_content)
                    
                    # Mark as success
                    response.success()
                    
                    # Store metrics for later analysis
                    response_data[complexity].append({
                        'duration': duration,
                        'length': response_length
                    })
                    
                    # Add detailed record
                    message_data.append({
                        'timestamp': request_time,
                        'user': self.username,
                        'chat_id': chat_id,
                        'complexity': complexity,
                        'message_length': len(message),
                        'response_length': response_length,
                        'duration': duration,
                        'status_code': response.status_code
                    })
                    
                    # Log the result
                    print(f"Chat {chat_id}: Got {complexity} response of length {response_length} in {duration:.2f}s")
                    
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 401:
                response.failure("Authentication failed")
                raise StopUser()
            else:
                response.failure(f"Request failed with status code: {response.status_code}")
                
                # Still record the attempt
                message_data.append({
                    'timestamp': request_time,
                    'user': self.username,
                    'chat_id': chat_id,
                    'complexity': complexity,
                    'message_length': len(message),
                    'response_length': None,
                    'duration': duration,
                    'status_code': response.status_code
                })

    def check_and_renew_session(self):
        """Periodically check if session is still valid and renew if needed"""
        # Check if chats exist by making a lightweight request
        response = self.client.get("/ai-assistant/chats")
        
        # If unauthorized or no chats found, re-login
        if response.status_code in [401, 403] or (response.status_code == 200 and len(response.json()) == 0):
            print(f"Renewing session for {self.username}")
            self.login()
            
            # Re-create chats if needed
            if not self.chat_ids or len(self.chat_ids) < CONFIG["chats_per_user"]:
                print(f"Re-creating chats for {self.username}")
                self.create_test_chats()

# Event handlers for custom reporting
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Handler called when the test is starting"""
    print(f"Test started at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Configuration: {json.dumps(CONFIG, indent=2)}")
    
    # Create report directory
    os.makedirs(os.path.join(CONFIG["output_dir"], CONFIG["test_name"]), exist_ok=True)
    
    # Save configuration
    with open(os.path.join(CONFIG["output_dir"], CONFIG["test_name"], "config.json"), "w") as f:
        json.dump(CONFIG, f, indent=2)

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Generate comprehensive report when test ends"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_path = os.path.join(CONFIG["output_dir"], CONFIG["test_name"])
    
    # Create report file
    report_file = os.path.join(report_path, "report.txt")
    detailed_csv = os.path.join(report_path, "detailed_results.csv")
    summary_csv = os.path.join(report_path, "summary.csv")
    
    # Generate summary statistics for each complexity level
    summary_stats = {}
    for complexity, data in response_data.items():
        if not data:
            continue
            
        durations = [item['duration'] for item in data]
        lengths = [item['length'] for item in data]
        
        stats = {
            'count': len(data),
            'avg_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'p95_duration': sorted(durations)[int(len(durations) * 0.95)] if len(durations) >= 20 else None,
            'avg_length': sum(lengths) / len(lengths),
            'min_length': min(lengths),
            'max_length': max(lengths)
        }
        
        if len(durations) >= 2:
            stats['stdev_duration'] = statistics.stdev(durations)
        
        summary_stats[complexity] = stats
    
    # Write detailed CSV file
    if message_data:
        with open(detailed_csv, 'w', newline='') as csvfile:
            fieldnames = message_data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in message_data:
                writer.writerow(row)
    
    # Write summary CSV file
    with open(summary_csv, 'w', newline='') as csvfile:
        fieldnames = ['complexity', 'count', 'avg_duration', 'min_duration', 'max_duration', 
                     'p95_duration', 'stdev_duration', 'avg_length', 'min_length', 'max_length']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for complexity, stats in summary_stats.items():
            row = {'complexity': complexity}
            row.update(stats)
            writer.writerow(row)
    
    # Generate text report
    with open(report_file, 'w') as f:
        f.write(f"AI Chat Interface Concurrency Test Report\n")
        f.write(f"======================================\n\n")
        f.write(f"Test completed at: {now}\n")
        f.write(f"Test duration: {CONFIG['run_time']}\n")
        f.write(f"Number of users: {CONFIG['users']}\n")
        f.write(f"Spawn rate: {CONFIG['spawn_rate']} users/second\n\n")
        
        f.write(f"Summary Statistics\n")
        f.write(f"-----------------\n\n")
        
        for complexity in ['simple', 'medium', 'complex']:
            if complexity in summary_stats:
                stats = summary_stats[complexity]
                f.write(f"{complexity.upper()} Messages ({stats['count']} requests):\n")
                f.write(f"  Response Time:\n")
                f.write(f"    Average: {stats['avg_duration']:.2f} seconds\n")
                f.write(f"    Min: {stats['min_duration']:.2f} seconds\n")
                f.write(f"    Max: {stats['max_duration']:.2f} seconds\n")
                if stats.get('p95_duration'):
                    f.write(f"    95th percentile: {stats['p95_duration']:.2f} seconds\n")
                if stats.get('stdev_duration'):
                    f.write(f"    Standard deviation: {stats['stdev_duration']:.2f} seconds\n")
                
                f.write(f"  Response Length:\n")
                f.write(f"    Average: {stats['avg_length']:.0f} characters\n")
                f.write(f"    Min: {stats['min_length']} characters\n")
                f.write(f"    Max: {stats['max_length']} characters\n\n")
        
        # Total statistics
        total_requests = sum(len(data) for data in response_data.values())
        all_durations = [item['duration'] for items in response_data.values() for item in items]
        
        if all_durations:
            avg_overall_duration = sum(all_durations) / len(all_durations)
            f.write(f"Overall Statistics:\n")
            f.write(f"  Total requests: {total_requests}\n")
            f.write(f"  Average response time: {avg_overall_duration:.2f} seconds\n\n")
        
        f.write(f"Test Configuration:\n")
        f.write(f"------------------\n")
        for key, value in CONFIG.items():
            f.write(f"  {key}: {value}\n")
        
        f.write(f"\nNote: Detailed results available in CSV format at {detailed_csv}\n")
    
    print(f"\n\nTest completed at {now}")
    print(f"Report saved to {report_file}")
    print(f"Detailed data saved to {detailed_csv}")
    print(f"Summary data saved to {summary_csv}")

# Running instructions:
# locust -f locustfile.py --host=http://localhost:5000 --users=1 --spawn-rate=2 --run-time=10m --headless --only-summary --csv=locust_results/baseline
