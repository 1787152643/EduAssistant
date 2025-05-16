#!/bin/bash
# tests2/run_tests.sh

# Create results directory
mkdir -p test_results

# Set server URL
SERVER_URL="http://124.71.46.184:5000"

# Run authentication tests
echo "Running authentication tests..."
locust -f eduassistant_tests.py --host=$SERVER_URL --only-summary \
  --headless --users=30 --spawn-rate=10 --run-time=3m \
  --csv=test_results/authentication

# Run course tests
echo "Running course management tests..."
locust -f eduassistant_tests.py --host=$SERVER_URL --only-summary \
  --headless --users=25 --spawn-rate=5 --run-time=3m \
  --csv=test_results/courses

# Run assignment tests
echo "Running assignment tests..."
locust -f eduassistant_tests.py --host=$SERVER_URL --only-summary \
  --headless --users=20 --spawn-rate=5 --run-time=3m \
  --csv=test_results/assignments

# Run knowledge base tests
echo "Running knowledge base tests..."
locust -f eduassistant_tests.py --host=$SERVER_URL --only-summary \
  --headless --users=15 --spawn-rate=5 --run-time=3m \
  --csv=test_results/knowledge_base

# Run analytics tests
echo "Running analytics tests..."
locust -f eduassistant_tests.py --host=$SERVER_URL --only-summary \
  --headless --users=15 --spawn-rate=5 --run-time=3m \
  --csv=test_results/analytics

# Run combined tests
echo "Running combined system tests..."
locust -f eduassistant_tests.py --host=$SERVER_URL --only-summary \
  --headless --users=50 --spawn-rate=10 --run-time=5m \
  --csv=test_results/combined

# Run quick scalability test
echo "Running scalability tests..."
for users in 20 50 100
do
    echo "Testing with $users users..."
    spawn_rate=$((users / 10))
    if [ $spawn_rate -lt 1 ]; then spawn_rate=1; fi
    
    locust -f eduassistant_tests.py --host=$SERVER_URL --only-summary \
      --headless --users=$users --spawn-rate=$spawn_rate --run-time=2m \
      --csv=test_results/scalability_users_$users
      
    # Wait between tests
    sleep 5
done

# Analyze results
echo "Analyzing test results..."
python analyze_results.py

echo "Testing complete! Report available in the test_results/report directory."