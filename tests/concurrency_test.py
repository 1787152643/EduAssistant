import json
import random
import time
import datetime
import os
from locust import HttpUser, task, events, between
from locust.exception import StopUser
import statistics
import csv

# Test Configuration
CONFIG = {
    "host": "http://124.71.46.184:5000",
    "message_type": "simple",  # Use 'simple', 'medium', or 'complex'
    "output_dir": "concurrency_results",
    "test_name": f"concurrency_test_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
}

# Ensure output directory exists
os.makedirs(os.path.join(CONFIG["output_dir"], CONFIG["test_name"]), exist_ok=True)

# Message data storage
results = []

class SingleMessageUser(HttpUser):
    """User that logs in, creates a chat, sends one message, then stops"""
    wait_time = between(0.5, 2)  # Small randomized wait to avoid exact simultaneous requests
    
    def on_start(self):
        """Login, create a chat, send a message, then stop"""
        try:
            # Login
            self.login()
            
            # Create chat
            chat_id = self.create_chat()
            if not chat_id:
                raise StopUser()
                
            # Send message and stop
            self.send_message(chat_id)
            
            # Stop the user after sending one message
            raise StopUser()
            
        except Exception as e:
            print(f"Error in user workflow: {e}")
            raise StopUser()
    
    def login(self):
        """Log in with test credentials"""
        # Create unique username by appending a timestamp and random value
        unique_suffix = f"{int(time.time())}_{random.randint(1000, 9999)}"
        self.username = f"test_user_{unique_suffix}"
        password = "123456"
        
        # For the test, use existing test accounts if available
        test_users = [
            {"username": "student001", "password": "123456"},
            {"username": "student002", "password": "123456"},
            {"username": "student003", "password": "123456"}
        ]
        
        # Pick a random test user if available, otherwise use unique username
        if test_users:
            credentials = random.choice(test_users)
        else:
            credentials = {"username": self.username, "password": password}
        
        self.username = credentials["username"]
        
        # Login
        with self.client.post("/login", data=credentials, catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Login failed with status {response.status_code}")
                raise Exception(f"Login failed for {self.username}")
            response.success()
            print(f"User {self.username} logged in")
    
    def create_chat(self):
        """Create a new chat session"""
        with self.client.post("/ai-assistant/chats", json={}, catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Chat creation failed with status {response.status_code}")
                return None
            
            chat_id = response.json().get("id")
            if not chat_id:
                response.failure("No chat ID in response")
                return None
                
            response.success()
            print(f"Created chat {chat_id} for {self.username}")
            return chat_id
    
    def send_message(self, chat_id):
        """Send a single message to the chat"""
        # Select message based on configuration
        message = self.get_message_by_type(CONFIG["message_type"])
        
        start_time = time.time()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with self.client.post(
            f"/ai-assistant/chats/{chat_id}/messages",
            json={"message": message},
            catch_response=True,
            name=f"Send {CONFIG['message_type']} message"
        ) as response:
            duration = time.time() - start_time
            
            result = {
                "timestamp": timestamp,
                "user": self.username,
                "chat_id": chat_id,
                "message_type": CONFIG["message_type"],
                "message_length": len(message),
                "duration": duration,
                "status_code": response.status_code
            }
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    ai_message = response_data.get('ai_message', {})
                    response_content = ai_message.get('content', '')
                    result["response_length"] = len(response_content)
                    response.success()
                    print(f"Chat {chat_id}: Got response of length {len(response_content)} in {duration:.2f}s")
                except Exception as e:
                    result["error"] = str(e)
                    response.failure(f"Error processing response: {e}")
            else:
                result["error"] = response.text[:100]  # Truncate long error messages
                response.failure(f"Request failed with status code: {response.status_code}")
            
            # Store result
            results.append(result)
    
    def get_message_by_type(self, message_type):
        """Get a message of the specified complexity"""
        if message_type == "simple":
            messages = [
                "What is machine learning?",
                "Explain object-oriented programming",
                "What are arrays in programming?",
                "Define artificial intelligence"
            ]
        elif message_type == "medium":
            messages = [
                "Compare supervised and unsupervised learning with examples of each",
                "Explain the differences between SQL and NoSQL databases. What are the use cases for each?",
                "What are the principles of clean code? Give me some examples of how to write maintainable code"
            ]
        else:  # complex
            messages = [
                "I'm developing an educational app that needs to track student progress across various skills. What would be the best database schema design for this? Consider scalability and performance.",
                "Can you explain how neural networks work in depth? Include explanations of backpropagation, activation functions, and how different layer types affect learning capabilities."
            ]
        
        return random.choice(messages)

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Handler called when the test is starting"""
    print(f"Concurrency test started at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Configuration: {CONFIG}")
    
    # Save configuration
    config_file = os.path.join(CONFIG["output_dir"], CONFIG["test_name"], "config.json")
    with open(config_file, "w") as f:
        json.dump(CONFIG, f, indent=2)

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Generate report when test ends"""
    print("\nGenerating test report...")
    report_path = os.path.join(CONFIG["output_dir"], CONFIG["test_name"])
    
    # Save detailed results
    results_file = os.path.join(report_path, "results.csv")
    if results:
        with open(results_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    
    # Generate summary
    total_requests = len(results)
    successful_requests = sum(1 for r in results if r.get("status_code") == 200)
    
    if total_requests > 0:
        success_rate = (successful_requests / total_requests) * 100
        
        # Calculate response time statistics for successful requests
        durations = [r["duration"] for r in results if r.get("status_code") == 200]
        
        if durations:
            avg_duration = sum(durations) / len(durations)
            min_duration = min(durations)
            max_duration = max(durations)
            
            # Calculate percentiles if we have enough data
            if len(durations) >= 10:
                sorted_durations = sorted(durations)
                p50 = sorted_durations[len(sorted_durations) // 2]
                p90 = sorted_durations[int(len(sorted_durations) * 0.9)]
                p95 = sorted_durations[int(len(sorted_durations) * 0.95)]
                p99 = sorted_durations[int(len(sorted_durations) * 0.99)]
            else:
                p50 = p90 = p95 = p99 = "Not enough data"
                
            if len(durations) >= 2:
                stdev = statistics.stdev(durations)
            else:
                stdev = "Not enough data"
        else:
            avg_duration = min_duration = max_duration = p50 = p90 = p95 = p99 = stdev = "No successful requests"
    else:
        success_rate = 0
        avg_duration = min_duration = max_duration = p50 = p90 = p95 = p99 = stdev = "No requests"
    
    # Create summary report
    summary_file = os.path.join(report_path, "summary.txt")
    with open(summary_file, "w") as f:
        f.write(f"Concurrency Test Summary\n")
        f.write(f"======================\n\n")
        f.write(f"Test completed at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Message type: {CONFIG['message_type']}\n")
        f.write(f"Number of users: {environment.runner.user_count}\n\n")
        
        f.write(f"Results:\n")
        f.write(f"  Total requests: {total_requests}\n")
        f.write(f"  Successful requests: {successful_requests}\n")
        f.write(f"  Success rate: {success_rate:.2f}%\n\n")
        
        f.write(f"Response Time (successful requests):\n")
        f.write(f"  Average: {avg_duration if isinstance(avg_duration, str) else f'{avg_duration:.2f} seconds'}\n")
        f.write(f"  Minimum: {min_duration if isinstance(min_duration, str) else f'{min_duration:.2f} seconds'}\n")
        f.write(f"  Maximum: {max_duration if isinstance(max_duration, str) else f'{max_duration:.2f} seconds'}\n")
        f.write(f"  Median (P50): {p50 if isinstance(p50, str) else f'{p50:.2f} seconds'}\n")
        f.write(f"  P90: {p90 if isinstance(p90, str) else f'{p90:.2f} seconds'}\n")
        f.write(f"  P95: {p95 if isinstance(p95, str) else f'{p95:.2f} seconds'}\n")
        f.write(f"  P99: {p99 if isinstance(p99, str) else f'{p99:.2f} seconds'}\n")
        f.write(f"  Standard Deviation: {stdev if isinstance(stdev, str) else f'{stdev:.2f} seconds'}\n")
    
    print(f"Report saved to {summary_file}")
    print(f"Detailed results saved to {results_file}")