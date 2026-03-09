# Deployment Guide - Intelli-Credit Platform

## Overview

This guide covers deploying the full-stack application:
- **Frontend (React)** → Vercel
- **Backend (FastAPI)** → Railway (recommended) or Render

---

## Part 1: Deploy Backend to Railway

### Why Railway?
- Easy Python/FastAPI deployment
- Free tier available ($5 credit/month)
- Automatic HTTPS
- Environment variables management
- PostgreSQL database option

### Steps:

1. **Sign up for Railway**
   - Go to https://railway.app
   - Sign up with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `credit-analyzer` repository
   - Select the `backend` folder as root directory

3. **Configure Build Settings**
   - Railway should auto-detect Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

4. **Add Environment Variables**
   Go to Variables tab and add:
   ```
   OPENAI_API_KEY=your_openai_key
   DATABASE_URL=sqlite:///./intellicredit.db
   FILE_STORAGE_ROOT=./storage
   JWT_SECRET_KEY=your-secure-random-key-here
   JWT_ALGORITHM=HS256
   JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
   BACKEND_PORT=8000
   BACKEND_HOST=0.0.0.0
   CORS_ORIGINS=["https://your-frontend-url.vercel.app"]
   ENVIRONMENT=production
   RATE_LIMIT_PER_MINUTE=60
   MONITORING_CHECK_INTERVAL_HOURS=24
   NEWS_API_KEY=your_news_api_key (optional)
   ```

5. **Deploy**
   - Click "Deploy"
   - Wait for deployment to complete
   - Copy your backend URL (e.g., `https://credit-analyzer-production.up.railway.app`)

6. **Update CORS**
   - After getting your Vercel frontend URL, update `CORS_ORIGINS` in Railway

---

## Part 2: Deploy Frontend to Vercel

### Steps:

1. **Update Frontend Environment**
   - Edit `frontend/.env.production`
   - Replace `VITE_API_URL` with your Railway backend URL:
   ```
   VITE_API_URL=https://your-backend-url.railway.app
   ```

2. **Commit Changes**
   ```bash
   git add .
   git commit -m "Add deployment configs"
   git push origin main
   ```

3. **Deploy to Vercel**
   - Go to https://vercel.com
   - Sign up/login with GitHub
   - Click "Add New Project"
   - Import your `credit-analyzer` repository

4. **Configure Project**
   - Framework Preset: Vite
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Install Command: `npm install`

5. **Add Environment Variables**
   In Vercel project settings → Environment Variables:
   ```
   VITE_API_URL=https://your-backend-url.railway.app
   ```

6. **Deploy**
   - Click "Deploy"
   - Wait for deployment
   - Your frontend will be live at `https://your-project.vercel.app`

7. **Update Backend CORS**
   - Go back to Railway
   - Update `CORS_ORIGINS` with your Vercel URL:
   ```
   CORS_ORIGINS=["https://your-project.vercel.app"]
   ```

---

## Alternative: Deploy Backend to Render

If you prefer Render over Railway:

1. **Sign up at https://render.com**

2. **Create New Web Service**
   - Connect GitHub repository
   - Select `backend` folder
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

3. **Add Environment Variables** (same as Railway)

4. **Deploy** and copy the URL

---

## Post-Deployment Checklist

### Backend
- ✅ Backend is accessible at your Railway/Render URL
- ✅ Test API: `https://your-backend-url/docs` (Swagger UI)
- ✅ Health check: `https://your-backend-url/health`
- ✅ Environment variables are set
- ✅ CORS is configured with frontend URL

### Frontend
- ✅ Frontend is accessible at Vercel URL
- ✅ Can access login page
- ✅ API calls work (check browser console)
- ✅ Environment variables are set

### Testing
1. Open your Vercel URL
2. Try to register a new account
3. Login with credentials
4. Upload a document
5. Check if analysis works

---

## Troubleshooting

### CORS Errors
- Make sure `CORS_ORIGINS` in backend includes your Vercel URL
- Format: `["https://your-app.vercel.app"]` (with quotes and brackets)

### API Connection Failed
- Check `VITE_API_URL` in Vercel environment variables
- Make sure backend is running on Railway/Render
- Check backend logs for errors

### Build Failures

**Frontend:**
- Check Node.js version (should be 18+)
- Verify all dependencies are in `package.json`
- Check build logs in Vercel

**Backend:**
- Check Python version (should be 3.10+)
- Verify `requirements.txt` is complete
- Check Railway/Render logs

### Database Issues
- For production, consider upgrading to PostgreSQL
- Railway offers managed PostgreSQL
- Update `DATABASE_URL` accordingly

---

## Monitoring & Maintenance

### Logs
- **Railway**: Dashboard → Deployments → Logs
- **Vercel**: Dashboard → Deployments → Function Logs

### Updates
- Push to `main` branch triggers auto-deployment on both platforms
- Monitor deployment status in respective dashboards

### Scaling
- **Railway**: Upgrade plan for more resources
- **Vercel**: Automatic scaling for frontend

---

## Cost Estimates

### Free Tier
- **Vercel**: Unlimited deployments, 100GB bandwidth
- **Railway**: $5 credit/month (enough for small apps)
- **Render**: 750 hours/month free

### Paid Plans (if needed)
- **Vercel Pro**: $20/month
- **Railway**: Pay as you go (~$5-20/month)
- **Render**: $7/month for starter

---

## Security Notes

1. **Never commit `.env` files** - Already in `.gitignore`
2. **Use strong JWT secrets** - Generate with: `openssl rand -hex 32`
3. **Enable HTTPS only** - Both platforms provide this automatically
4. **Rotate API keys regularly**
5. **Monitor usage** - Set up alerts for unusual activity

---

## Next Steps

1. Deploy backend to Railway
2. Get backend URL
3. Update frontend `.env.production`
4. Deploy frontend to Vercel
5. Update backend CORS with Vercel URL
6. Test the application
7. Set up custom domain (optional)

---

## Support

- Railway Docs: https://docs.railway.app
- Vercel Docs: https://vercel.com/docs
- Render Docs: https://render.com/docs

For issues, check the logs first, then refer to platform documentation.
