@echo off
REM Prerequisite Checker and Setup Helper

echo ========================================
echo Financial Document Extraction PoC
echo Prerequisite Checker
echo ========================================
echo.

REM Check Python
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [X] Python NOT FOUND
    echo.
    echo Please install Python 3.10 or higher:
    echo 1. Download from: https://www.python.org/downloads/
    echo 2. During installation, CHECK "Add Python to PATH"
    echo 3. Restart this script after installation
    echo.
    pause
    exit /b 1
) else (
    python --version
    echo [✓] Python is installed
)

echo.
echo [2/4] Checking pip...
pip --version >nul 2>&1
if errorlevel 1 (
    echo [X] pip NOT FOUND
    echo.
    echo Installing pip...
    python -m ensurepip --upgrade
) else (
    pip --version
    echo [✓] pip is installed
)

echo.
echo [3/4] Checking Tesseract OCR...
set TESSERACT_PATH="C:\Program Files\Tesseract-OCR\tesseract.exe"
if exist %TESSERACT_PATH% (
    %TESSERACT_PATH% --version 2>nul | findstr /C:"tesseract" >nul
    if errorlevel 1 (
        echo [!] Tesseract found but cannot get version
    ) else (
        echo [✓] Tesseract is installed
    )
) else (
    echo [X] Tesseract NOT FOUND at standard location
    echo.
    echo Please install Tesseract OCR:
    echo 1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
    echo 2. Or direct link: https://digi.bib.uni-mannheim.de/tesseract/
    echo 3. Install to default location: C:\Program Files\Tesseract-OCR
    echo 4. Update .env file with TESSERACT_PATH if installed elsewhere
    echo.
    echo You can continue setup, but OCR will not work without Tesseract.
    echo.
    set /p CONTINUE="Continue anyway? (y/n): "
    if /i not "%CONTINUE%"=="y" exit /b 1
)

echo.
echo [4/4] Checking OpenAI API Key configuration...
if exist .env (
    findstr /C:"OPENAI_API_KEY=" .env >nul
    if errorlevel 1 (
        echo [!] .env exists but OPENAI_API_KEY not configured
    ) else (
        findstr /C:"OPENAI_API_KEY=your_openai_api_key_here" .env >nul
        if errorlevel 1 (
            echo [✓] OPENAI_API_KEY appears to be configured
        ) else (
            echo [!] OPENAI_API_KEY needs to be updated with real key
        )
    )
) else (
    echo [!] .env file not found (will be created during setup)
)

echo.
echo ========================================
echo Prerequisite Check Summary
echo ========================================
echo.
echo Next Steps:
echo.

if not exist venv (
    echo 1. Run setup.cmd to create virtual environment and install dependencies
) else (
    echo 1. Virtual environment already exists
    echo 2. Activate it: venv\Scripts\activate
    echo 3. Install/update dependencies: pip install -r requirements.txt
)

echo.
echo REQUIRED BEFORE RUNNING:
echo - Get OpenAI API key from: https://platform.openai.com/api-keys
echo - Update .env file with your API key
echo - Ensure Tesseract is installed for OCR functionality
echo.
echo For detailed instructions, see: PREREQUISITES.md
echo.
pause
