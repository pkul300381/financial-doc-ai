# 🚀 SETUP INSTRUCTIONS - READ FIRST

## ⚠️ CURRENT STATUS: Python Not Installed

Your system needs Python installed before you can run this PoC. Follow these steps:

---

## 📋 Quick Setup Guide

### STEP 1: Install Python 3.10+ (REQUIRED)

**Recommended Method** - Official Python Installer:

1. **Download Python**:
   - Go to: https://www.python.org/downloads/
   - Click "Download Python 3.11.x" (or latest 3.10+)

2. **Install Python**:
   - Run the downloaded installer
   - ✅ **CRITICAL**: Check ☑ "Add Python to PATH" at the bottom
   - Click "Install Now"
   - Wait for installation to complete

3. **Verify Installation**:
   ```cmd
   python --version
   ```
   Should show: `Python 3.10.x` or higher

---

### STEP 2: Install Tesseract OCR (REQUIRED)

1. **Download Tesseract**:
   - Go to: https://github.com/UB-Mannheim/tesseract/wiki
   - Download: `tesseract-ocr-w64-setup-5.3.x.exe` (latest version)
   - Direct link: https://digi.bib.uni-mannheim.de/tesseract/

2. **Install Tesseract**:
   - Run the installer
   - Install to default location: `C:\Program Files\Tesseract-OCR`
   - Complete installation

3. **Verify Installation**:
   ```cmd
   "C:\Program Files\Tesseract-OCR\tesseract.exe" --version
   ```

---

### STEP 3: Get OpenAI API Key (REQUIRED)

1. **Create OpenAI Account**:
   - Go to: https://platform.openai.com/signup
   - Sign up or log in

2. **Create API Key**:
   - Go to: https://platform.openai.com/api-keys
   - Click "Create new secret key"
   - Name it (e.g., "Financial PoC")
   - Copy the key (starts with `sk-`)
   - **SAVE IT** - you can't see it again!

3. **Billing Setup** (if new account):
   - Go to: https://platform.openai.com/account/billing
   - Add payment method
   - Set spending limit (recommend $10-20 for testing)

**Cost Estimate**: ~$0.50-$2.00 per document processed

---

### STEP 4: Run Setup Script

After installing Python and Tesseract:

```cmd
cd d:\MySpace\Learning\Financial-poc
.\check-prerequisites.cmd
```

This will verify all prerequisites are installed.

Then run:

```cmd
.\setup.cmd
```

This will:
- Create virtual environment
- Install all Python dependencies (~10 minutes)
- Create `.env` configuration file
- Set up data directories

---

### STEP 5: Configure Environment

Edit the `.env` file and add your OpenAI API key:

```cmd
notepad .env
```

Update this line:
```
OPENAI_API_KEY=sk-your_actual_api_key_here
```

And verify Tesseract path (default should work):
```
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
```

---

### STEP 6: Test Installation

```cmd
REM Activate virtual environment
venv\Scripts\activate

REM Run tests
pytest tests/ -v --tb=short

REM If tests pass, start the API
python api.py
```

**Success!** API should start at: http://localhost:8000

---

## 🎯 Quick Reference

### Required Downloads:
1. **Python 3.10+**: https://www.python.org/downloads/
2. **Tesseract OCR**: https://github.com/UB-Mannheim/tesseract/wiki
3. **OpenAI API Key**: https://platform.openai.com/api-keys

### Commands:
```cmd
REM Check prerequisites
.\check-prerequisites.cmd

REM Run setup
.\setup.cmd

REM Activate environment
venv\Scripts\activate

REM Start API
python api.py

REM Run tests
pytest tests/ -v
```

### Access Points After Setup:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics

---

## 🐛 Common Issues

### "python is not recognized"
**Cause**: Python not in PATH  
**Solution**: 
1. Reinstall Python and check "Add Python to PATH"
2. OR manually add to PATH (see PREREQUISITES.md)
3. Restart command prompt

### "No module named 'fastapi'"
**Cause**: Dependencies not installed  
**Solution**: 
```cmd
venv\Scripts\activate
pip install -r requirements.txt
```

### "Tesseract is not installed"
**Cause**: Tesseract not found  
**Solution**: 
1. Install Tesseract
2. Update `.env` with correct path

### OpenAI Rate Limits
**Cause**: Too many requests  
**Solution**: 
1. Wait a minute and retry
2. Check your API usage: https://platform.openai.com/usage
3. Increase rate limits in OpenAI dashboard

---

## 📞 Getting Help

1. **Check Full Guide**: See `PREREQUISITES.md` for detailed troubleshooting
2. **Review Logs**: Check terminal output for specific errors
3. **Test Components**: Run `pytest tests/ -v` to identify failing parts
4. **Check Documentation**: Review files in `docs/` folder

---

## ⏱️ Time Estimate

- Python installation: 5 minutes
- Tesseract installation: 5 minutes  
- OpenAI account setup: 5 minutes
- Dependency installation: 10-15 minutes
- Configuration: 5 minutes

**Total**: ~30-40 minutes

---

## ✅ Success Criteria

You're ready when:
- ✅ `python --version` shows 3.10+
- ✅ Tesseract is installed and accessible
- ✅ OpenAI API key is configured in `.env`
- ✅ `pytest tests/ -v` passes (or most tests pass)
- ✅ `python api.py` starts without errors
- ✅ http://localhost:8000/health returns `{"status": "healthy"}`

---

## 🎉 What's Next?

After successful setup:

1. **Try the API**:
   - Open http://localhost:8000/docs
   - Try the upload endpoint
   - Test queries

2. **Process a Document**:
   ```python
   from poc_pipeline import DocumentPipeline
   pipeline = DocumentPipeline()
   extraction = pipeline.process_document("path/to/invoice.pdf")
   ```

3. **Explore Examples**:
   - Check `docs/EXAMPLES.md` for JSON schemas
   - Review `docs/API.md` for all endpoints
   - See `docs/ARCHITECTURE.md` for system design

---

**Ready to start?** Follow Steps 1-6 above in order!
