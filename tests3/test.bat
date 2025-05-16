@echo off
setlocal EnableDelayedExpansion

:: EduAssistant API Testing Script
:: Usage: test_api.bat [session_cookie]

:: Configuration
set BASE_URL=http://124.71.46.184:5000
set REQUESTS=1000
set CONCURRENCY=100
set RESULTS_DIR=api_test_results
set DATE_TIME=%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set DATE_TIME=%DATE_TIME: =0%
set RESULTS_DIR=%RESULTS_DIR%\%DATE_TIME%

:: Check if session cookie is provided
if "%~1"=="" (
    echo Please provide a session cookie.
    echo Usage: test_api.bat [session_cookie]
    exit /b 1
)
set SESSION=%~1

:: Create results directory
mkdir "%RESULTS_DIR%"
echo Testing started at %TIME% > "%RESULTS_DIR%\summary.txt"
echo Base URL: %BASE_URL% >> "%RESULTS_DIR%\summary.txt"
echo Requests: %REQUESTS% >> "%RESULTS_DIR%\summary.txt"
echo Concurrency: %CONCURRENCY% >> "%RESULTS_DIR%\summary.txt"
echo. >> "%RESULTS_DIR%\summary.txt"

:: Create login test data
echo username=prof_zhang^&password=123456 > temp_login_data.txt

echo Running API tests...

:: Authentication Tests
echo Testing Authentication APIs...
echo ---------------------------- >> "%RESULTS_DIR%\summary.txt"
echo Authentication Tests >> "%RESULTS_DIR%\summary.txt"
echo ---------------------------- >> "%RESULTS_DIR%\summary.txt"

echo Testing login endpoint...
ab -n %REQUESTS% -c %CONCURRENCY% -p temp_login_data.txt -T "application/x-www-form-urlencoded" %BASE_URL%/login > "%RESULTS_DIR%\login_results.txt"
for /f "tokens=*" %%a in ('findstr /C:"Requests per second" "%RESULTS_DIR%\login_results.txt"') do (
    echo Login: %%a >> "%RESULTS_DIR%\summary.txt"
)

:: Course Tests
echo Testing Course APIs...
echo. >> "%RESULTS_DIR%\summary.txt"
echo ---------------------------- >> "%RESULTS_DIR%\summary.txt"
echo Course Tests >> "%RESULTS_DIR%\summary.txt"
echo ---------------------------- >> "%RESULTS_DIR%\summary.txt"

echo Testing course listing...
ab -n %REQUESTS% -c %CONCURRENCY% -C "session=%SESSION%" %BASE_URL%/course/ > "%RESULTS_DIR%\course_list_results.txt"
for /f "tokens=*" %%a in ('findstr /C:"Requests per second" "%RESULTS_DIR%\course_list_results.txt"') do (
    echo Course List: %%a >> "%RESULTS_DIR%\summary.txt"
)

echo Testing course view...
ab -n %REQUESTS% -c %CONCURRENCY% -C "session=%SESSION%" %BASE_URL%/course/1 > "%RESULTS_DIR%\course_view_results.txt"
for /f "tokens=*" %%a in ('findstr /C:"Requests per second" "%RESULTS_DIR%\course_view_results.txt"') do (
    echo Course View: %%a >> "%RESULTS_DIR%\summary.txt"
)

:: Assignment Tests
echo Testing Assignment APIs...
echo. >> "%RESULTS_DIR%\summary.txt"
echo ---------------------------- >> "%RESULTS_DIR%\summary.txt"
echo Assignment Tests >> "%RESULTS_DIR%\summary.txt"
echo ---------------------------- >> "%RESULTS_DIR%\summary.txt"

echo Testing assignment view...
ab -n %REQUESTS% -c %CONCURRENCY% -C "session=%SESSION%" %BASE_URL%/course/assignment/1 > "%RESULTS_DIR%\assignment_view_results.txt"
for /f "tokens=*" %%a in ('findstr /C:"Requests per second" "%RESULTS_DIR%\assignment_view_results.txt"') do (
    echo Assignment View: %%a >> "%RESULTS_DIR%\summary.txt"
)

:: Search Tests
echo Testing Search APIs...
echo. >> "%RESULTS_DIR%\summary.txt"
echo ---------------------------- >> "%RESULTS_DIR%\summary.txt"
echo Search Tests >> "%RESULTS_DIR%\summary.txt"
echo ---------------------------- >> "%RESULTS_DIR%\summary.txt"

echo Testing search API...
ab -n %REQUESTS% -c %CONCURRENCY% -C "session=%SESSION%" "%BASE_URL%/search/api/search?q=python&limit=5" > "%RESULTS_DIR%\search_results.txt"
for /f "tokens=*" %%a in ('findstr /C:"Requests per second" "%RESULTS_DIR%\search_results.txt"') do (
    echo Search API: %%a >> "%RESULTS_DIR%\summary.txt"
)

:: Analytics Tests
echo Testing Analytics APIs...
echo. >> "%RESULTS_DIR%\summary.txt"
echo ---------------------------- >> "%RESULTS_DIR%\summary.txt"
echo Analytics Tests >> "%RESULTS_DIR%\summary.txt"
echo ---------------------------- >> "%RESULTS_DIR%\summary.txt"

echo Testing student analytics...
ab -n %REQUESTS% -c %CONCURRENCY% -C "session=%SESSION%" %BASE_URL%/analytics/student/1 > "%RESULTS_DIR%\student_analytics_results.txt"
for /f "tokens=*" %%a in ('findstr /C:"Requests per second" "%RESULTS_DIR%\student_analytics_results.txt"') do (
    echo Student Analytics: %%a >> "%RESULTS_DIR%\summary.txt"
)

echo Testing course analytics...
ab -n %REQUESTS% -c %CONCURRENCY% -C "session=%SESSION%" %BASE_URL%/analytics/course/1 > "%RESULTS_DIR%\course_analytics_results.txt"
for /f "tokens=*" %%a in ('findstr /C:"Requests per second" "%RESULTS_DIR%\course_analytics_results.txt"') do (
    echo Course Analytics: %%a >> "%RESULTS_DIR%\summary.txt"
)

:: Stress Testing
echo Running stress tests with higher concurrency...
set STRESS_CONCURRENCY=25

echo. >> "%RESULTS_DIR%\summary.txt"
echo ---------------------------- >> "%RESULTS_DIR%\summary.txt"
echo Stress Tests (Concurrency=%STRESS_CONCURRENCY%) >> "%RESULTS_DIR%\summary.txt"
echo ---------------------------- >> "%RESULTS_DIR%\summary.txt"

echo Stress testing course listing...
ab -n %REQUESTS% -c %STRESS_CONCURRENCY% -C "session=%SESSION%" %BASE_URL%/course/ > "%RESULTS_DIR%\stress_course_list_results.txt"
for /f "tokens=*" %%a in ('findstr /C:"Requests per second" "%RESULTS_DIR%\stress_course_list_results.txt"') do (
    echo Stress Course List: %%a >> "%RESULTS_DIR%\summary.txt"
)

:: Clean up
del temp_login_data.txt

echo Testing completed at %TIME% >> "%RESULTS_DIR%\summary.txt"
echo Results saved to %RESULTS_DIR%
echo Summary available in %RESULTS_DIR%\summary.txt