# Deploy Appointment Guard - Quick Start Guide

## Status: ✅ Code Ready, ⚠️ Needs Railway Setup

The code is **100% complete and tested**. Just need to connect GitHub repo to Railway.

---

## Option A: New Project (Recommended - Fastest)

### Step 1: Create New Railway Project
1. Go to https://railway.app/new/import
2. Click "Import a Repository"
3. Select `tnowakow/appointment-guard`
4. Click "Deploy Now"

### Step 2: Add Environment Variables
In the Railway dashboard, go to **Variables** tab and add:

```bash
# Supabase (already created)
SUPABASE_URL=https://jmkwrxtxfkvydjmlrmya.supabase.co
SUPABASE_ANON_KEY=<paste_your_supabase_anon_key_here>

# Twilio (get from https://www.twilio.com/console)
TWILIO_ACCOUNT_SID=<your_twilio_account_sid>
TWILIO_AUTH_TOKEN=<your_twilio_auth_token>
TWILIO_PHONE_NUMBER=+1xxxxxxxxxx  # Your Twilio phone number

# Optional: Telegram for alerts
TELEGRAM_BOT_TOKEN=<your_bot_token>
TELEGRAM_CHAT_ID=<your_chat_id>
```

### Step 3: Wait for Deployment
- Railway will auto-deploy within 2-3 minutes
- Watch the "Deployments" tab for progress

### Step 4: Verify Health Check
Once deployed, get your project URL from the dashboard and run:

```bash
curl https://<your-project-name>.up.railway.app/health
# Expected: {"status":"healthy","version":"1.0.0"}
```

---

## Option B: Use Existing Project (If You Have Access)

### Step 1: Open Existing Project
Go to: https://railway.app/project/fda2073b-d325-4734-8dd6-20deb81eb585

### Step 2: Connect GitHub Repository
1. Go to **Settings** → **GitHub** tab
2. Click "Connect a Repository" or "Add GitHub App"
3. Select `tnowakow/appointment-guard`
4. Enable auto-deploy on main branch

### Step 3: Add Environment Variables
Same as Option A, Step 2

### Step 4: Verify Deployment
Same as Option A, Step 4

---

## What Happens Next

Once connected:
1. Railway automatically builds your app using Nixpacks (Python 3.11)
2. Installs dependencies from `requirements.txt`
3. Starts the server using `Procfile`: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Exposes your app at `<project-name>.up.railway.app`

**Auto-deploy:** Every push to `main` branch will trigger a new deployment!

---

## Troubleshooting

### "Application not found" (404)
- App hasn't been deployed yet - wait 2-3 minutes after connecting repo
- Check Deployments tab for build logs

### Import errors in logs
- Shouldn't happen - code is tested and working locally
- If it does, check that all dependencies are in `requirements.txt`

### Health endpoint not responding
- Wait for deployment to complete (green checkmark)
- Verify environment variables are set correctly
- Check service logs in Railway dashboard

---

## Local Testing (Before Deploying)

```bash
cd /Users/tomnow/.openclaw/workspace/dev-team/projects/appointment-guard/backend

# Test imports
python3 -c "from main import app; print('✅ Imports work')"

# Run server locally
uvicorn main:app --host 127.0.0.1 --port 8001

# Test health endpoint
curl http://localhost:8001/health
# Expected: {"status":"healthy","version":"1.0.0"}
```

---

## Need Help?

- Railway Docs: https://docs.railway.app
- GitHub Repo: https://github.com/tnowakow/appointment-guard
- Local docs: `README.md` in backend folder
