# Lessons Learned - Dev Team

## Lesson 1: Railway Deployment Requires Valid Authentication (Token or GitHub Integration)
**Date:** 2026-04-19  
**Project:** appointment-guard  
**Symptom:** Health endpoint returns 404 "Application not found" despite code being ready and pushed to GitHub. GitHub Actions failing with "Unauthorized" error at "Link to existing project" step.

**Root Cause:** 
1. Railway project exists (ID: fda2073b-d325-4734-8dd6-20deb81eb585) but has no deployment connected
2. GitHub Actions workflow uses `RAILWAY_TOKEN` secret which is expired/invalid
3. Cannot deploy programmatically without valid authentication

**Fix:** 
1. Added `pyproject.toml` for proper Nixpacks Python package detection (commit 86279f0)
2. Documented that manual Railway dashboard connection is required OR GitHub secret needs updating
3. Code is ready; deployment will auto-trigger once authentication is resolved

**Resolution Options:**
- **Option A (Recommended):** Connect GitHub repo via Railway dashboard at https://railway.app/project/fda2073b-d325-4734-8dd6-20deb81eb585/settings/github
- **Option B:** Generate new Railway token at https://railway.app/account/security and update `RAILWAY_TOKEN` secret in GitHub repo settings

**Prevention:** For future Railway deployments:
- Always connect GitHub repo via Railway dashboard first (more reliable than CLI tokens)
- Add `pyproject.toml` for Python projects to ensure Nixpacks detects the framework correctly  
- Verify Procfile exists with proper start command before deployment
- Test imports locally: `python3 -c "from main import app"`
- If using GitHub Actions, verify RAILWAY_TOKEN secret is valid before relying on it
---

## Lesson 2: Code Works Locally But Deployment Blocked by Auth (Not Import Errors)
**Date:** 2026-04-19  
**Project:** appointment-guard  
**Symptom:** Cron job reported "ModuleNotFoundError or import issues" but actual investigation showed code is fully functional locally.

**Root Cause:** 
- Health endpoint returns 404 because app **hasn't been deployed yet**, not because of code errors
- Local testing confirms: `uvicorn main:app` starts successfully, health check returns `{"status":"healthy","version":"1.0.0"}`
- All imports work: `from risk_scoring import NoShowRiskAgent`, `from intervention_agent import PatientInterventionAgent`
- The real blocker is Railway authentication, not code issues

**Fix:** 
- Verified locally with full server test:
  ```bash
  cd backend && uvicorn main:app --host 127.0.0.1 --port 8765 &
  curl http://127.0.0.1:8765/health  # Returns 200 OK
  pkill -f "uvicorn main:app"
  ```
- No code changes needed - deployment only requires Railway auth resolution

**Prevention:** 
- When troubleshooting deployment issues, always test locally first before assuming code errors
- Distinguish between "not deployed" (404) vs "deployed but broken" (500/other errors)
- Cron job error messages should be more specific about what was actually found
---

## Lesson 3: Railway CLI Login Requires Browser Interaction (Cannot Automate)
**Date:** 2026-04-19  
**Project:** appointment-guard  
**Symptom:** Attempted to fix deployment by running `railway login` but CLI requires browser interaction or valid token.

**Root Cause:** 
- Railway CLI authentication cannot be done in non-interactive mode
- `railway login --browserless` fails with "Cannot login in non-interactive mode"
- Existing RAILWAY_TOKEN is expired/invalid and needs regeneration via web interface

**Fix Attempted:**
```bash
railway login  # Prompts for browser open - cannot automate
railway login --browserless  # Fails: requires interactive mode
```

**Actual Resolution Path:**
The only way to resolve this is manual intervention:
1. Tom must access https://railway.app/login via browser
2. Either regenerate token at https://railway.app/account/security OR connect GitHub repo directly in project settings
3. Once connected, Railway auto-deploys from main branch

**Prevention:** 
- For future deployments, prefer Railway's native GitHub integration over CLI tokens (more stable)
- If using tokens, document expiration and set reminder to refresh before deployment deadlines
- Consider alternative deployment methods (Vercel, Render, Fly.io) that may have better programmatic auth
---

## Lesson 4: Cron Job Error Messages Can Be Misleading - Always Verify Root Cause
**Date:** 2026-04-19  
**Project:** appointment-guard  
**Symptom:** Overnight monitor cron job reported "ModuleNotFoundError or import issues" as the current error.

**Root Cause:** 
- The error message was a generic description, not an actual observed error
- Real issue: Railway token invalid → no deployment possible → health endpoint returns 404
- No ModuleNotFoundError exists in the code - all imports work perfectly locally

**Investigation Steps Taken:**
1. Checked Railway logs via CLI (failed due to auth)
2. Checked GitHub Actions workflow runs (confirmed "Unauthorized" error)
3. Tested local imports: `python3 -c "from main import app"` ✅ Success
4. Verified health endpoint: returns 404 because app not deployed, not because of code errors

**Fix:** 
- Updated DEPLOYMENT_STATUS.md with accurate status
- Documented that code is 100% ready and working locally
- Clarified that only manual Railway dashboard connection is needed

**Prevention:** 
- Cron job descriptions should include actual error messages from logs, not assumptions
- Always verify the real error before attempting fixes
- Distinguish between deployment infrastructure issues vs. application code issues
---

## Lesson 5: Health Check 404 Means No Deployment, Not Code Error
**Date:** 2026-04-19  
**Project:** appointment-guard  
**Symptom:** `curl https://appointment-guard-production.up.railway.app/health` returns `{"status":"error","code":404,"message":"Application not found"}`

**Root Cause:** 
The Railway project exists but has no service deployed. A 404 from Railway means:
- The project URL is valid (Railway recognizes it)
- But no deployment/service is running at that URL
- This is NOT a code error - the app simply doesn't exist on Railway yet

**Verification:**
```bash
# Check if project exists but has no deployment
curl -sI "https://appointment-guard-production.up.railway.app/health"
# Returns: HTTP/2 404 with x-railway-cdn-edge header

# This confirms Railway is responding, just no app deployed
```

**Fix:** 
Create a new deployment via Railway dashboard:
1. Go to https://railway.app/new/import
2. Select GitHub repo: `tnowakow/appointment-guard`
3. Add environment variables (Twilio + Supabase)
4. Wait 2-3 minutes for auto-deployment
5. Verify with health check returning HTTP 200

**Prevention:** 
- When troubleshooting, distinguish between:
  - **404 Not Found**: App not deployed yet (infrastructure issue)
  - **500 Internal Server Error**: App deployed but has runtime errors (code issue)
  - **Connection refused/timeout**: Wrong URL or Railway project doesn't exist
- Always check HTTP status code, not just response body
- Test locally first: `uvicorn main:app` should start without errors before deployment
---

<!-- NEW LESSONS GO BELOW THIS LINE -->
