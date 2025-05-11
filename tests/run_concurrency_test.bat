@echo off
setlocal EnableDelayedExpansion

REM Create directory for results
mkdir concurrency_test_results

REM Message complexity to test with
set MESSAGE_TYPE=simple

REM Starting with a small number of users
set START_USERS=5
set MAX_USERS=50
set STEP=5

echo Running concurrency tests with gradually increasing users...
echo Message type: %MESSAGE_TYPE%

for /L %%u in (%START_USERS%, %STEP%, %MAX_USERS%) do (
    echo.
    echo =============================================
    echo Testing with %%u concurrent users...
    echo =============================================
    
    REM Run the test with current user count
    locust -f concurrency_test.py --host=http://localhost:5000 --users=%%u --spawn-rate=5 --run-time=1m --headless --only-summary --csv=concurrency_test_results/users_%%u
    
    REM Pause to let the system recover
    echo Waiting for system to stabilize...
    timeout /t 10 /nobreak > nul
)

echo All concurrency tests completed!