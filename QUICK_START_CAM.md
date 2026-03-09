# Quick Start Guide - CAM Feature

## 🚀 Get Started in 3 Steps

### Step 1: Start the Servers

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # or: . venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Step 2: Navigate to CAM

1. Open browser: `http://localhost:5173`
2. Login with your credentials
3. Go to any application with completed analysis
4. Click the **"CAM"** tab

### Step 3: View & Export

- CAM will auto-generate (2-3 seconds)
- Click **"Export PDF"** or **"Export Word"** to download

---

## 📋 What You'll See

### CAM Sections:
1. **Executive Summary** - Overview and key highlights
2. **Borrower Information** - Company profile and credit history
3. **Loan Proposal** - Facility details and terms
4. **Financial Analysis** - Revenue, profit, ratios, trends
5. **Risk Assessment** - Risk factors, strengths, concerns
6. **Credit Recommendation** - Final decision and terms
7. **Compliance** - Regulatory requirements
8. **Conclusion** - Summary and approval hierarchy

### All Data is Real:
- ✅ Revenue from uploaded documents
- ✅ Profit from uploaded documents
- ✅ Growth rates calculated from data
- ✅ Financial ratios from analysis
- ✅ Risk scores from AI assessment
- ✅ Recommendations based on scoring

---

## 🔧 Optional: Enable Export

To enable PDF and Word export:

```bash
cd backend
source venv/bin/activate
./install_export_packages.sh
# Restart backend server
```

---

## ✅ Success Indicators

You'll know it's working when:
- ✅ CAM tab shows loading spinner
- ✅ CAM content appears within 3 seconds
- ✅ All 8 sections are visible
- ✅ Tables have borders and data
- ✅ Company name and loan amount are correct
- ✅ Financial data matches analysis

---

## ❌ Troubleshooting

### CAM Not Generating?
- Ensure analysis is complete first
- Check backend terminal for errors
- Verify application exists

### Export Not Working?
- Install export packages (see above)
- Restart backend server
- Check backend terminal for errors

### Data Missing?
- Run analysis first: Click "Analyze" button
- Wait for analysis to complete
- Then generate CAM

---

## 📞 Need Help?

Check these files:
- `CAM_TESTING_GUIDE.md` - Detailed testing instructions
- `CAM_IMPLEMENTATION_COMPLETE.md` - Full implementation details
- `FINAL_CAM_SUMMARY.md` - Complete summary

---

## 🎯 Test Application

Use this application ID for testing:
```
6f636cf7-fab9-438d-8c22-0754d44d6ed9
```

Direct API test:
```bash
curl -X POST "http://localhost:8000/api/v1/applications/6f636cf7-fab9-438d-8c22-0754d44d6ed9/cam-simple"
```

---

**That's it! You're ready to generate professional CAMs! 🎉**
