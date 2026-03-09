# Vercel Full-Stack Deployment Guide

## Overview

This guide deploys both frontend (React) and backend (FastAPI) on Vercel as a monorepo.

---

## Prerequisites

1. GitHub account with your code pushed
2. Vercel account (sign up at https://vercel.com)
3. OpenAI API key
4. (Optional) News API key

---

## Step-by-Step Deployment

### 1. Prepare Your Repository

Your code is already configured! The following files are set up:
- ✅ `vercel.json` - Vercel configuration
- ✅ `api/index.py` - Serverless function entry point
- ✅ `requirements.txt` - Python dependencies
- ✅ `.vercelignore` - Files to ignore during deployment

### 2. Deploy to Vercel

#### Option A: Using Vercel Dashboard (Recommended)

1. **Go to Vercel**
   - Visit https://vercel.com
   - Click "Sign Up" or "Login"
   - Connect with GitHub

2. **Import Project**
   - Click "Add New..." → "Project"
   - Select your `credit-analyzer` repository
   - Click "Import"

3. **Configure Project**
   - Framework Preset: **Other** (we have custom config)
   - Root Directory: **Leave as root** (monorepo setup)
   - Build Command: `cd frontend && npm install && npm run build`
   - Output Directory: `frontend/dist`
   - Install Command: `npm install --prefix frontend`

4. **Add Environment Variables**
   Click "Environment Variables" and add:

   ```
   OPENAI_API_KEY=sk-proj-your-key-here
   DATABASE_URL=sqlite:///./intellicredit.db
   FILE_STORAGE_ROOT=/tmp/storage
   JWT_SECRET_KEY=your-secure-random-key-minimum-32-chars
   JWT_ALGORITHM=HS256
   JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
   BACKEND_PORT=8000
   BACKEND_HOST=0.0.0.0
   CORS_ORIGINS=["*"]
   ENVIRONMENT=production
   RATE_LIMIT_PER_MINUTE=60
   MONITORING_CHECK_INTERVAL_HOURS=24
   NEWS_API_KEY=your-news-api-key-optional
   ```

   **Important Notes:**
   - Generate JWT_SECRET_KEY: `openssl rand -hex 32`
   - Set `FILE_STORAGE_ROOT=/tmp/storage` (Vercel uses /tmp for temporary files)
   - `CORS_ORIGINS=["*"]` allows all origins (or specify your domain)

5. **Deploy**
   - Click "Deploy"
   - Wait 2-5 minutes for deployment
   - Your app will be live at `https://your-project.vercel.app`

#### Option B: Using Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy
vercel

# Follow prompts:
# - Set up and deploy? Yes
# - Which scope? Your account
# - Link to existing project? No
# - Project name? credit-analyzer
# - Directory? ./
# - Override settings? No

# Deploy to production
vercel --prod
```

### 3. Configure Environment Variables (CLI Method)

```bash
# Add environment variables
vercel env add OPENAI_API_KEY
vercel env add DATABASE_URL
vercel env add JWT_SECRET_KEY
vercel env add NEWS_API_KEY

# Redeploy with new env vars
vercel --prod
```

---

## Project Structure for Vercel

```
credit-analyzer/
├── api/
│   └── index.py              # Serverless function entry (backend)
├── backend/
│   ├── app/                  # FastAPI application
│   └── requirements.txt      # Backend dependencies
├── frontend/
│   ├── src/                  # React source
│   ├── dist/                 # Build output (generated)
│   └── package.json
├── requirements.txt          # Root requirements (for Vercel)
├── vercel.json              # Vercel configuration
└── .vercelignore            # Files to ignore
```

---

## How It Works

### Backend (FastAPI → Serverless)
- FastAPI runs as Vercel serverless functions
- All `/api/*` routes go to `api/index.py`
- Python dependencies from `requirements.txt`
- Stateless (no persistent file storage)

### Frontend (React → Static)
- Built with Vite
- Served as static files from `frontend/dist`
- All routes fallback to `index.html` (SPA routing)

### Routing
- `/api/*` → Backend API
- `/docs` → API documentation
- `/health` → Health check
- `/*` → Frontend React app

---

## Testing Your Deployment

### 1. Check Backend API
Visit: `https://your-project.vercel.app/docs`
- Should show Swagger UI
- Test endpoints

### 2. Check Health Endpoint
Visit: `https://your-project.vercel.app/health`
- Should return: `{"status": "healthy"}`

### 3. Check Frontend
Visit: `https://your-project.vercel.app`
- Should show login page
- Try registering and logging in

### 4. Test Full Flow
1. Register a new account
2. Login
3. Upload a document
4. Check if analysis works

---

## Important Limitations on Vercel

### 1. **Serverless Function Timeout**
- Free tier: 10 seconds
- Pro tier: 60 seconds
- **Impact**: Long-running AI analysis may timeout
- **Solution**: Break into smaller chunks or upgrade to Pro

### 2. **No Persistent Storage**
- Files uploaded are stored in `/tmp` (temporary)
- **Impact**: Files deleted after function execution
- **Solution**: Use external storage (AWS S3, Cloudinary, etc.)

### 3. **Cold Starts**
- Functions may take 1-2 seconds to start if inactive
- **Impact**: First request may be slow
- **Solution**: Keep functions warm or upgrade to Pro

### 4. **Database**
- SQLite works but data is temporary
- **Impact**: Data lost on redeployment
- **Solution**: Use external database (PostgreSQL, MongoDB)

---

## Recommended Upgrades for Production

### 1. External Database
Use PostgreSQL (recommended):
- **Vercel Postgres**: Built-in, easy setup
- **Supabase**: Free tier, PostgreSQL + Auth
- **Neon**: Serverless PostgreSQL

Update `DATABASE_URL`:
```
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

### 2. File Storage
Use cloud storage:
- **Vercel Blob**: Built-in file storage
- **AWS S3**: Industry standard
- **Cloudinary**: Image/document hosting

### 3. Upgrade Vercel Plan
- **Pro Plan**: $20/month
  - 60s function timeout
  - More bandwidth
  - Better performance

---

## Troubleshooting

### Build Fails

**Error: "Module not found"**
```bash
# Check if all dependencies are in package.json
cd frontend && npm install
```

**Error: "Python module not found"**
```bash
# Check requirements.txt has all dependencies
pip install -r requirements.txt
```

### API Not Working

**Error: "CORS policy"**
- Check `CORS_ORIGINS` environment variable
- Should include your Vercel domain

**Error: "500 Internal Server Error"**
- Check Vercel function logs
- Go to Dashboard → Deployments → Function Logs

### Frontend Not Loading

**Blank page**
- Check browser console for errors
- Verify `VITE_API_URL` is empty (same domain)

**404 on refresh**
- Check `vercel.json` routes configuration
- Should fallback to `index.html`

---

## Monitoring & Logs

### View Logs
1. Go to Vercel Dashboard
2. Select your project
3. Click "Deployments"
4. Click on latest deployment
5. View "Function Logs" or "Build Logs"

### Real-time Logs (CLI)
```bash
vercel logs
```

---

## Custom Domain (Optional)

### Add Custom Domain
1. Go to Project Settings → Domains
2. Add your domain (e.g., `app.yourdomain.com`)
3. Update DNS records as instructed
4. Wait for SSL certificate (automatic)

### Update Environment Variables
After adding domain, update:
```
CORS_ORIGINS=["https://app.yourdomain.com"]
```

---

## Continuous Deployment

### Automatic Deployments
- Push to `main` branch → Auto-deploy to production
- Push to other branches → Preview deployments
- Pull requests → Preview deployments

### Manual Deployment
```bash
vercel --prod
```

---

## Cost Estimate

### Free Tier (Hobby)
- ✅ Unlimited deployments
- ✅ 100GB bandwidth/month
- ✅ Serverless functions (10s timeout)
- ✅ Automatic HTTPS
- ⚠️ Limited for production use

### Pro Tier ($20/month)
- ✅ Everything in Free
- ✅ 60s function timeout
- ✅ 1TB bandwidth
- ✅ Team collaboration
- ✅ Better for production

---

## Security Checklist

- ✅ Environment variables set (not in code)
- ✅ JWT_SECRET_KEY is strong (32+ chars)
- ✅ CORS configured properly
- ✅ HTTPS enabled (automatic)
- ✅ API keys rotated regularly
- ✅ Rate limiting enabled

---

## Next Steps After Deployment

1. ✅ Test all features thoroughly
2. ✅ Set up external database (if needed)
3. ✅ Configure file storage (if needed)
4. ✅ Add custom domain (optional)
5. ✅ Set up monitoring/alerts
6. ✅ Upgrade to Pro (if needed)

---

## Support & Resources

- **Vercel Docs**: https://vercel.com/docs
- **Vercel Support**: https://vercel.com/support
- **Community**: https://github.com/vercel/vercel/discussions

---

## Quick Commands Reference

```bash
# Deploy to production
vercel --prod

# View logs
vercel logs

# List deployments
vercel ls

# Remove deployment
vercel rm [deployment-url]

# Add environment variable
vercel env add [NAME]

# Pull environment variables
vercel env pull
```

---

## Summary

Your Intelli-Credit platform is now deployed on Vercel! 🎉

- **Frontend**: Static React app
- **Backend**: Serverless FastAPI functions
- **URL**: `https://your-project.vercel.app`
- **API Docs**: `https://your-project.vercel.app/docs`

For production use, consider:
1. External database (PostgreSQL)
2. Cloud file storage (S3/Blob)
3. Vercel Pro plan ($20/month)
