# Installation Notes - CAM Feature

## ✅ Issue Resolved

### Problem:
Backend server failed to start with error:
```
ModuleNotFoundError: No module named 'markdown'
```

### Solution:
Installed the `markdown` package:
```bash
pip install markdown
```

### Status:
✅ **RESOLVED** - Backend should now start successfully

---

## Required Packages (Already Installed)

### Core Packages:
- ✅ `fastapi` - Web framework
- ✅ `sqlalchemy` - Database ORM
- ✅ `openai` - AI analysis
- ✅ `markdown` - HTML conversion (for export)

### Optional Export Packages:
- ⏭️ `weasyprint` - PDF generation (optional)
- ⏭️ `python-docx` - Word generation (optional)

---

## Installation Status

### Backend Core: ✅ Complete
```bash
cd backend
pip install -r requirements.txt
```

All required packages are now in `requirements.txt`:
- fastapi, uvicorn, sqlalchemy
- openai, langchain
- markdown (newly added)
- And all other dependencies

### Frontend: ✅ Complete
```bash
cd frontend
npm install
```

All required packages installed:
- react, react-dom
- react-markdown (for CAM display)
- framer-motion, lucide-react
- And all other dependencies

---

## Optional: Export Functionality

If you want to enable PDF and Word export, run:

```bash
cd backend
source venv/bin/activate
./install_export_packages.sh
```

This installs:
- `weasyprint` - For PDF export
- `python-docx` - For Word export
- `markdown` - For HTML conversion

**Note:** These are optional. CAM generation works without them. You'll just see a helpful error message if you try to export without these packages.

---

## Starting the Servers

### Backend:
```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload
```

**Expected Output:**
```
INFO:     Will watch for changes in these directories: ['/path/to/backend']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Frontend:
```bash
cd frontend
npm run dev
```

**Expected Output:**
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
➜  press h + enter to show help
```

---

## Verification

### Backend is Running:
```bash
curl http://localhost:8000/health
```

Should return: `{"status":"healthy"}`

### Frontend is Running:
Open browser: `http://localhost:5173`

Should show the login page

---

## Troubleshooting

### Issue: "No module named 'markdown'"
**Solution:** Already fixed! Package is now in requirements.txt

### Issue: "No module named 'weasyprint'"
**Solution:** This is expected if you haven't installed export packages. Either:
1. Install packages: `./install_export_packages.sh`
2. Or ignore - CAM generation works without export

### Issue: "No module named 'python-docx'"
**Solution:** Same as above - optional package for Word export

### Issue: Port 8000 already in use
**Solution:** 
```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9
# Or use a different port
uvicorn app.main:app --reload --port 8001
```

### Issue: Port 5173 already in use
**Solution:**
```bash
# Kill the process
lsof -ti:5173 | xargs kill -9
# Or Vite will automatically use next available port
```

---

## Package Versions

### Backend (Python 3.10+):
- fastapi: 0.109.0
- sqlalchemy: 2.0.25
- openai: 1.10.0
- markdown: 3.10.2 ⭐ NEW
- weasyprint: 61.2 (optional)
- python-docx: 1.1.0 (optional)

### Frontend (Node 18+):
- react: 18.x
- react-markdown: latest
- framer-motion: latest
- vite: 5.x

---

## Next Steps

1. ✅ Backend packages installed
2. ✅ Frontend packages installed
3. ✅ Markdown package added
4. ⏭️ Start backend server
5. ⏭️ Start frontend server
6. ⏭️ Test CAM generation

---

## Quick Commands

```bash
# Install all backend packages
cd backend && pip install -r requirements.txt

# Install optional export packages
cd backend && ./install_export_packages.sh

# Start backend
cd backend && python -m uvicorn app.main:app --reload

# Start frontend
cd frontend && npm run dev

# Test CAM API
curl -X POST "http://localhost:8000/api/v1/applications/{APP_ID}/cam-simple"
```

---

**Status:** ✅ All required packages installed and ready to go!
