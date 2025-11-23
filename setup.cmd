@echo off
REM Quick start script for Financial Document Extraction PoC

echo ====================================
echo Financial Document Extraction PoC
echo ====================================
echo.

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10 or higher.
    exit /b 1
)

echo [1/5] Creating virtual environment...
if not exist venv (
    python -m venv venv
    echo Virtual environment created.
) else (
    echo Virtual environment already exists.
)

echo.
echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [3/5] Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo [4/5] Setting up configuration...
if not exist .env (
    copy .env.example .env
    echo Created .env file. Please edit it with your API keys.
    echo.
    echo IMPORTANT: You must set OPENAI_API_KEY in .env before running!
    echo.
    pause
) else (
    echo .env file already exists.
)

echo.
echo [5/5] Creating data directories...
if not exist data\uploads mkdir data\uploads
if not exist data\processed mkdir data\processed
if not exist data\vectordb mkdir data\vectordb

echo.
echo ====================================
echo Setup Complete!
echo ====================================
echo.
echo To start the API server, run:
echo   python api.py
echo.
echo To run the pipeline directly, run:
echo   python poc_pipeline.py
echo.
echo To run tests:
echo   pytest tests/ -v
echo.
echo API will be available at: http://localhost:8000
echo API documentation: http://localhost:8000/docs
echo.
pause
