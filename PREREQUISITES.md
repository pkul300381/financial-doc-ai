# Prerequisites Setup Guide

## ⚠️ Required Software

### 1. Python 3.10 or Higher

**Status**: ❌ Not Detected - INSTALL REQUIRED

**Installation Steps**:

#### Option A: Official Python Installer (Recommended)
1. Download Python 3.10+ from: https://www.python.org/downloads/
2. Run the installer
3. ✅ **IMPORTANT**: Check "Add Python to PATH" during installation
4. Click "Install Now"
5. Verify installation:
   ```cmd
   python --version
   ```

#### Option B: Microsoft Store
1. Open Microsoft Store
2. Search for "Python 3.10" or "Python 3.11"
3. Click Install
4. Verify installation:
   ```cmd
   python --version
   ```

#### Option C: Chocolatey (if you have it)
```cmd
choco install python --version=3.10.11
```

### 2. Tesseract OCR

**Status**: ❌ Not Checked - INSTALL REQUIRED

**Installation Steps**:

#### Windows:
1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Choose: `tesseract-ocr-w64-setup-5.3.x.exe` (latest version)
3. Run installer (default location: `C:\Program Files\Tesseract-OCR`)
4. Add to PATH or note installation path for `.env` configuration

**Quick Download Links**:
- Latest Tesseract: https://digi.bib.uni-mannheim.de/tesseract/

### 3. Git (for version control)

**Installation**:
1. Download from: https://git-scm.com/download/win
2. Run installer with default settings
3. Verify: `git --version`

### 4. Visual C++ Redistributable (for some Python packages)

**Installation**:
1. Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe
2. Run installer

---

## 🚀 Setup Steps (After Installing Python)

### Step 1: Create Virtual Environment
```cmd
cd d:\MySpace\Learning\Financial-poc
python -m venv venv
```

### Step 2: Activate Virtual Environment
```cmd
venv\Scripts\activate
```

### Step 3: Upgrade pip
```cmd
python -m pip install --upgrade pip
```

### Step 4: Install Dependencies
```cmd
pip install -r requirements.txt
```

**Note**: This may take 5-10 minutes. Some packages (like Prophet) compile C extensions.

### Step 5: Configure Environment
```cmd
copy .env.example .env
```

Edit `.env` file and set:
```
OPENAI_API_KEY=sk-your_actual_openai_api_key_here
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
```

### Step 6: Verify Setup
```cmd
python -c "import sys; print(f'Python {sys.version}')"
python -c "import fastapi; print('FastAPI installed')"
python -c "import pytesseract; print('Tesseract wrapper installed')"
```

---

## 🔑 API Keys Required

### OpenAI API Key (REQUIRED)

1. Go to: https://platform.openai.com/api-keys
2. Sign in or create account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)
5. Add to `.env` file:
   ```
   OPENAI_API_KEY=sk-your_actual_key_here
   ```

**Cost Estimate**: ~$0.50-$2.00 per document (depending on complexity)

---

## ✅ Verification Checklist

Run these commands to verify everything is installed:

```cmd
REM Check Python
python --version

REM Check pip
pip --version

REM Check Tesseract (after installation)
"C:\Program Files\Tesseract-OCR\tesseract.exe" --version

REM Check virtual environment
where python

REM List installed packages
pip list
```

Expected output:
```
Python 3.10.x or higher
pip 23.x or higher
tesseract 5.3.x or higher
Python path should show: d:\MySpace\Learning\Financial-poc\venv\...
```

---

## 🐛 Troubleshooting

### Issue: "python is not recognized"
**Solution**: Restart command prompt after Python installation or add Python to PATH manually:
1. Search "Environment Variables" in Windows
2. Edit "Path" in System Variables
3. Add: `C:\Users\<YourUser>\AppData\Local\Programs\Python\Python310`
4. Add: `C:\Users\<YourUser>\AppData\Local\Programs\Python\Python310\Scripts`

### Issue: "No module named 'pytesseract'"
**Solution**: Activate virtual environment first, then install:
```cmd
venv\Scripts\activate
pip install -r requirements.txt
```

### Issue: "Tesseract is not installed"
**Solution**: Install Tesseract and update `.env`:
```
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
```

### Issue: "Microsoft Visual C++ 14.0 is required"
**Solution**: Install Visual C++ redistributable:
https://aka.ms/vs/17/release/vc_redist.x64.exe

### Issue: Prophet installation fails
**Solution**: Try installing pre-built wheel:
```cmd
pip install prophet --no-cache-dir
```
Or install dependencies first:
```cmd
pip install pystan==2.19.1.1
pip install prophet
```

---

## 📦 Alternative: Docker Setup (No Local Python Needed)

If you prefer not to install Python locally:

### Prerequisites for Docker:
1. Install Docker Desktop: https://www.docker.com/products/docker-desktop/
2. Install WSL2 (Windows Subsystem for Linux) if on Windows

### Setup:
```cmd
REM Build Docker image
docker build -t financial-poc .

REM Run container
docker run -d -p 8000:8000 ^
  -e OPENAI_API_KEY=your_key_here ^
  --name financial-poc ^
  financial-poc

REM View logs
docker logs -f financial-poc
```

---

## 🎯 Quick Start (After Prerequisites)

```cmd
REM 1. Activate environment
venv\Scripts\activate

REM 2. Run tests to verify
pytest tests/ -v

REM 3. Start API server
python api.py

REM 4. Open browser to:
REM http://localhost:8000
REM http://localhost:8000/docs (Interactive API docs)
```

---

## 📞 Need Help?

- **Python Installation**: https://www.python.org/downloads/
- **Tesseract Installation**: https://github.com/UB-Mannheim/tesseract/wiki
- **OpenAI API**: https://platform.openai.com/docs/quickstart
- **Project Issues**: Check `docs/` folder for detailed guides

---

## ⏱️ Estimated Setup Time

- Python installation: 5 minutes
- Tesseract installation: 5 minutes
- Dependencies installation: 10-15 minutes
- Configuration: 5 minutes

**Total**: ~30 minutes
