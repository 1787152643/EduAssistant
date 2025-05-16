@echo off
setlocal EnableDelayedExpansion

REM Create directory for results
mkdir concurrency_test_results

REM Server configuration
set SERVER_IP=124.71.46.184
set SERVER_PORT=5000

REM Message complexity to test with
set MESSAGE_TYPE=simple

REM UPDATED: Progressive user counts with wider range
set USER_COUNTS=5 10 20 30 50 75 100 150 200 300 500

echo Running concurrency tests against %SERVER_IP% with progressively increasing users...
echo Message type: %MESSAGE_TYPE%

for %%u in (%USER_COUNTS%) do (
    echo.
    echo =============================================
    echo Testing with %%u concurrent users...
    echo =============================================
    
    REM Calculate spawn rate and test duration based on user count
    set SPAWN_RATE=5
    set TEST_DURATION=1m
    
    if %%u GTR 50 set SPAWN_RATE=10
    if %%u GTR 200 set SPAWN_RATE=20
    
    if %%u GTR 50 set TEST_DURATION=2m
    if %%u GTR 200 set TEST_DURATION=3m
    
    echo Spawn rate: !SPAWN_RATE! users/sec, Test duration: !TEST_DURATION!
    
    REM Run the test
    locust -f concurrency_test.py --host=http://%SERVER_IP%:%SERVER_PORT% --users=%%u --spawn-rate=!SPAWN_RATE! --run-time=!TEST_DURATION! --headless --only-summary --csv=concurrency_test_results/users_%%u
    
    REM Calculate wait time - longer for larger tests
    set WAIT_TIME=15
    if %%u GTR 100 set WAIT_TIME=30
    if %%u GTR 300 set WAIT_TIME=60
    
    echo Waiting !WAIT_TIME! seconds for system to stabilize...
    timeout /t !WAIT_TIME! /nobreak > nul
)

echo All concurrency tests completed!