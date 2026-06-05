@echo off
SETLOCAL Enabledelayedexpansion
cls
echo =======================================================================
echo 🚀 STARTING INTEGRATED PIPELINE DEPLOYMENT GATEWAY
echo =======================================================================
echo.

:: Step 1: Force system environment variables to process UTF-8 text encoding parameters inside Windows CMD
set PYTHONIOENCODING=utf-8

echo [Step 1/3] Running Infrastructure Validation Tests...
python test_infra.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 🛑 [DEPLOYMENT CRASHED]: test_infra.py validation suite rejected your code.
    echo Action required: Fix breaks or syntax parameters before deployment pass.
    exit /b %ERRORLEVEL%
)

echo.
echo =======================================================================
echo [Step 2/3] Verification passed. Packaging and staging git tracking layers...
echo =======================================================================
git add .

:: Prompt the user for an authentic commit message natively inside CMD
echo.
set /p commit_msg="Enter your deployment commit tracking message: "
if "!commit_msg!"=="" (
    set commit_msg="feat: optimize autonomous multi-agent data verification pipelines"
)

git commit -m "!commit_msg!"

echo.
echo =======================================================================
echo [Step 3/3] Shipping verified code base to main origin repository...
echo =======================================================================
git push origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo 🏆 [DEPLOYMENT SUCCESSFUL]: All components verified and deployed cleanly to your repository!
) else (
    echo.
    echo ❌ [DEPLOYMENT ERROR]: Git tracking push failed. Verify remote connection parameters.
)

pause
