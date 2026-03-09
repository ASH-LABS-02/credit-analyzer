# CAM Testing Checklist

Use this checklist to verify the CAM implementation is working correctly.

## Pre-Testing Setup

### ✅ Backend Setup
- [ ] Backend virtual environment activated
- [ ] Backend server running on port 8000
- [ ] No errors in backend terminal
- [ ] Database file exists: `backend/intellicredit.db`

### ✅ Frontend Setup
- [ ] Frontend dependencies installed (`npm install`)
- [ ] Frontend server running (usually port 5173)
- [ ] No errors in frontend terminal
- [ ] Browser can access `http://localhost:5173`

### ✅ Test Data
- [ ] At least one application exists
- [ ] Application has documents uploaded
- [ ] Analysis has been completed for the application
- [ ] Analysis status is "complete"

## CAM Generation Testing

### ✅ Basic Generation
- [ ] Navigate to application detail page
- [ ] Click "CAM" tab
- [ ] Loading spinner appears
- [ ] CAM generates within 3 seconds
- [ ] No errors in browser console
- [ ] No errors in backend terminal

### ✅ Content Verification

#### Section 1: Executive Summary
- [ ] Section header visible
- [ ] Company overview present
- [ ] Key financial highlights table displays
- [ ] Table has 6 rows (Revenue, Profit, Margin, Growth, Current Ratio, Debt-to-Equity)
- [ ] All values are numbers (not "undefined" or "null")
- [ ] Credit recommendation present
- [ ] Recommendation is one of: APPROVE, APPROVE WITH CONDITIONS, REVIEW REQUIRED, REJECT

#### Section 2: Borrower Information
- [ ] Section header visible
- [ ] Company profile present
- [ ] Credit history table displays
- [ ] Credit score shown (0-100)
- [ ] Risk classification shown (Low/Medium/High Risk)

#### Section 3: Loan Proposal
- [ ] Section header visible
- [ ] Facility details table displays
- [ ] Loan amount matches application
- [ ] Loan purpose matches application
- [ ] End-use of funds section present

#### Section 4: Financial Analysis
- [ ] Section header visible
- [ ] Historical performance table displays
- [ ] Revenue values present for each year
- [ ] Profit values present for each year
- [ ] Profit margins calculated correctly
- [ ] Growth analysis table displays
- [ ] Revenue growth percentages shown
- [ ] Profit growth percentages shown
- [ ] Key financial ratios table displays
- [ ] Current ratio shown with assessment
- [ ] Debt-to-equity shown with assessment
- [ ] Profit margin shown with assessment
- [ ] Liquidity position analysis present
- [ ] Leverage analysis present
- [ ] Cash flow assessment present

#### Section 5: Risk Assessment
- [ ] Section header visible
- [ ] Overall risk rating table displays
- [ ] Credit score shown (0-100)
- [ ] Risk classification shown
- [ ] Probability of default shown
- [ ] Risk factor analysis present
- [ ] At least 3 risk factors analyzed
- [ ] Each risk factor has:
  - [ ] Score (0-100)
  - [ ] Assessment text
  - [ ] Explanation paragraph
- [ ] Key strengths section present
- [ ] At least 1 strength listed
- [ ] Areas of concern section present
- [ ] Risk mitigation measures listed (5 items)

#### Section 6: Credit Recommendation
- [ ] Section header visible
- [ ] Final recommendation clearly stated
- [ ] Rationale section present
- [ ] Rationale explains the decision
- [ ] Proposed terms table displays
- [ ] Loan amount shown
- [ ] Interest rate guidance shown
- [ ] Margin percentage shown
- [ ] Conditions precedent listed
- [ ] Monitoring requirements present
- [ ] Monitoring frequency specified

#### Section 7: Compliance
- [ ] Section header visible
- [ ] KYC compliance checklist present
- [ ] Regulatory compliance checklist present

#### Section 8: Conclusion
- [ ] Section header visible
- [ ] Summary paragraph present
- [ ] Approval hierarchy table displays
- [ ] Document classification shown
- [ ] Version number shown
- [ ] Last updated date shown

### ✅ Formatting Verification
- [ ] All tables have visible borders
- [ ] Table headers are bold
- [ ] H1 headers are large and bold
- [ ] H2 headers are medium and bold
- [ ] H3 headers are smaller and bold
- [ ] Horizontal rules (---) display as lines
- [ ] Bold text (**text**) displays correctly
- [ ] Bullet points display correctly
- [ ] Numbered lists display correctly

### ✅ Data Accuracy
- [ ] Company name matches application
- [ ] Loan amount matches application (₹ symbol present)
- [ ] Loan purpose matches application
- [ ] Application date is correct
- [ ] Credit score matches analysis (0-100)
- [ ] Risk rating matches risk score:
  - [ ] 70-100 = Low Risk
  - [ ] 50-69 = Medium Risk
  - [ ] 0-49 = High Risk
- [ ] Recommendation matches risk score:
  - [ ] ≥70 = APPROVE
  - [ ] 50-69 = APPROVE WITH CONDITIONS
  - [ ] 30-49 = REVIEW REQUIRED
  - [ ] <30 = REJECT
- [ ] Financial metrics match analysis results
- [ ] Growth rates calculated correctly

## Export Testing (Optional)

### ✅ Without Export Packages
- [ ] Click "Export PDF" button
- [ ] Error message appears: "requires 'weasyprint' package"
- [ ] Error message is clear and helpful
- [ ] Click "Export Word" button
- [ ] Error message appears: "requires 'python-docx' package"
- [ ] Error message is clear and helpful

### ✅ With Export Packages Installed
- [ ] Export packages installed (`./backend/install_export_packages.sh`)
- [ ] Backend server restarted
- [ ] Click "Export PDF" button
- [ ] PDF file downloads
- [ ] Filename format: `CAM_CompanyName_YYYYMMDD_HHMMSS.pdf`
- [ ] Open PDF file
- [ ] PDF has proper formatting
- [ ] All sections visible in PDF
- [ ] Tables display correctly in PDF
- [ ] Click "Export Word" button
- [ ] DOCX file downloads
- [ ] Filename format: `CAM_CompanyName_YYYYMMDD_HHMMSS.docx`
- [ ] Open Word file
- [ ] Word doc has proper formatting
- [ ] All sections visible in Word
- [ ] Tables display correctly in Word

## UI/UX Testing

### ✅ Loading States
- [ ] Loading spinner shows during generation
- [ ] Loading text is clear: "Generating Credit Appraisal Memo..."
- [ ] Loading state prevents multiple clicks
- [ ] Export buttons show loading state when clicked

### ✅ Error Handling
- [ ] If analysis not complete, error message shows
- [ ] Error message is clear and actionable
- [ ] Retry button appears on error
- [ ] Retry button works correctly
- [ ] Error state is visually distinct (red background)

### ✅ Success States
- [ ] Success message shows after generation
- [ ] Timestamp displays: "Generated on [date/time]"
- [ ] Green checkmark icon appears
- [ ] CAM content is clearly visible

### ✅ Interactions
- [ ] Regenerate button works
- [ ] Regenerate updates the timestamp
- [ ] Export buttons are clearly labeled
- [ ] Export buttons have appropriate icons
- [ ] All buttons have hover effects
- [ ] Disabled states are visually clear

### ✅ Responsive Design
- [ ] CAM displays correctly on desktop (1920x1080)
- [ ] CAM displays correctly on laptop (1366x768)
- [ ] CAM displays correctly on tablet (768x1024)
- [ ] Tables are scrollable on small screens
- [ ] Text is readable at all sizes

## Performance Testing

### ✅ Speed
- [ ] CAM generates in < 3 seconds
- [ ] No lag when scrolling through CAM
- [ ] Export completes in < 5 seconds
- [ ] Page remains responsive during generation

### ✅ Resource Usage
- [ ] Browser memory usage is reasonable
- [ ] No memory leaks (check DevTools)
- [ ] Backend CPU usage is reasonable
- [ ] No excessive database queries

## Edge Cases

### ✅ Missing Data
- [ ] CAM generates even with missing revenue data
- [ ] Tables show "No data" when data is missing
- [ ] No JavaScript errors with missing data
- [ ] Graceful degradation of content

### ✅ Large Data
- [ ] CAM handles 10+ years of financial data
- [ ] CAM handles long company names
- [ ] CAM handles large loan amounts (₹1,00,00,000+)
- [ ] Export works with large CAMs

### ✅ Special Characters
- [ ] Company names with special characters display correctly
- [ ] Currency symbols (₹) display correctly
- [ ] Percentages (%) display correctly
- [ ] Decimal numbers display correctly

## Browser Compatibility

### ✅ Chrome
- [ ] CAM displays correctly
- [ ] Export works
- [ ] No console errors

### ✅ Firefox
- [ ] CAM displays correctly
- [ ] Export works
- [ ] No console errors

### ✅ Safari (if available)
- [ ] CAM displays correctly
- [ ] Export works
- [ ] No console errors

### ✅ Edge (if available)
- [ ] CAM displays correctly
- [ ] Export works
- [ ] No console errors

## Final Verification

### ✅ Documentation
- [ ] README updated with CAM feature
- [ ] API documentation includes CAM endpoints
- [ ] User guide includes CAM instructions

### ✅ Code Quality
- [ ] No syntax errors in backend
- [ ] No TypeScript errors in frontend
- [ ] No linting errors
- [ ] Code is properly commented

### ✅ Security
- [ ] Authentication required to access CAM
- [ ] No sensitive data exposed in logs
- [ ] No SQL injection vulnerabilities
- [ ] No XSS vulnerabilities

## Sign-Off

### Testing Completed By:
- Name: ___________________________
- Date: ___________________________
- Signature: ___________________________

### Issues Found:
```
Issue #1: _______________________________________________________
Severity: [ ] Critical  [ ] High  [ ] Medium  [ ] Low
Status: [ ] Open  [ ] Fixed  [ ] Won't Fix

Issue #2: _______________________________________________________
Severity: [ ] Critical  [ ] High  [ ] Medium  [ ] Low
Status: [ ] Open  [ ] Fixed  [ ] Won't Fix

Issue #3: _______________________________________________________
Severity: [ ] Critical  [ ] High  [ ] Medium  [ ] Low
Status: [ ] Open  [ ] Fixed  [ ] Won't Fix
```

### Overall Assessment:
- [ ] ✅ PASS - Ready for production
- [ ] ⚠️ PASS WITH ISSUES - Minor issues, can deploy
- [ ] ❌ FAIL - Critical issues, cannot deploy

### Notes:
```
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
```

---

**Total Checklist Items:** 150+  
**Estimated Testing Time:** 30-45 minutes  
**Recommended Testers:** 2-3 people
