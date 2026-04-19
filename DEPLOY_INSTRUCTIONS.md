# 🚀 Deployment Instructions for AppointmentGuard

## Current Status
- ✅ GitHub repo is ready: `tnowakow/appointment-guard`
- ✅ Railway project exists: "AppointmentGuard" 
- ❌ Service not yet created in Railway
- ❌ Environment variables not configured

## Quick Deploy (2 minutes)

### Option 1: Via Railway Web UI (Recommended)

1. Go to https://railway.app/dashboard/projects/AppointmentGuard
2. Click **"New"** → **"Provision from GitHub repo"**
3. Select repository: `tnowakow/appointment-guard`
4. Wait for deployment to complete (~2 minutes)
5. Add environment variables in the **"Variables"** tab:
   ```
   TWILIO_ACCOUNT_SID=<your_twilio_sid>
   TWILIO_AUTH_TOKEN=<your_twilio_token>
   TWILIO_PHONE_NUMBER=+13135461280
   SUPABASE_URL=https://jmkwrxtxfkvydjmlrmya.supabase.co
   SUPABASE_ANON_KEY=<from .env file>
   ```

### Option 2: Via Railway CLI (if you have it installed)

```bash
cd /Users/tomnow/.openclaw/workspace/dev-team/projects/appointment-guard/backend
railway login
railway link --project AppointmentGuard
railway add --service backend --repo https://github.com/tnowakow/appointment-guard
# Then add environment variables via Railway dashboard
```

## Verify Deployment

Once deployed, test the health endpoint:
```bash
curl https://appointment-guard.up.railway.app/health
```

Expected response:
```json
{"status": "healthy", "service": "appointment-guard"}
```

## Notes
- The project name on Railway is "AppointmentGuard" (capital A, capital G)
- Railway will auto-deploy on future pushes to main branch once connected
