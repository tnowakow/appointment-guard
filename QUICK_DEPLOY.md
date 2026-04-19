# ⚡ Quick Deploy - 2 Minutes

## The Issue
Railway project doesn't exist yet. Railway CLI/API authentication isn't working with the token (might be expired or limited scope).

## Solution: Use GitHub Actions Workflow

### Step 1: Add RAILWAY_TOKEN Secret to GitHub (30 seconds)

1. Go to: https://github.com/tnowakow/appointment-guard/settings/secrets/actions
2. Click **"New repository secret"**
3. Name: `RAILWAY_TOKEN`  
4. Value: `00c9be57-884c-4fa6-97db-7bd53180025c`
5. Click **"Add secret"**

### Step 2: Trigger Deployment (10 seconds)

Go to: https://github.com/tnowakow/appointment-guard/actions/workflows/deploy-to-railway.yml

Click **"Run workflow"** → Select "main" branch → Click **"Run workflow"**

### Step 3: Wait & Verify (~2 minutes)

The workflow will create the Railway project and deploy automatically. Check logs at:
https://github.com/tnowakow/appointment-guard/actions

Once complete, test:
```bash
curl https://appointment-guard-production.up.railway.app/health
```

Expected: `{"status": "healthy", "service": "appointment-guard"}`

---

## Alternative: Manual Railway Setup (if GitHub Actions fails)

1. Go to https://railway.app/new
2. Click **"Deploy from GitHub repo"**
3. Select `tnowakow/appointment-guard`
4. Add env vars in Railway dashboard → Variables tab:
   ```bash
   TWILIO_ACCOUNT_SID=<your_twilio_sid>
   TWILIO_AUTH_TOKEN=<your_twilio_token>
   TWILIO_PHONE_NUMBER=<your_twilio_number>
   SUPABASE_URL=https://jmkwrxtxfkvydjmlrmya.supabase.co
   SUPABASE_ANON_KEY=<from .env file>
   ```

---

**Total time: 2-3 minutes max!**
