# Lessons Learned - Dev Team

## Lesson 1: Railway Deployment Requires GitHub Integration (Not CLI Token)
**Date:** 2026-04-19  
**Project:** appointment-guard  
**Symptom:** Health endpoint returns 404 "Application not found" despite code being ready and pushed to GitHub  
**Root Cause:** Railway project was created but never connected to GitHub repository for auto-deployment. CLI token approach failed because token was invalid/expired.  
**Fix:** 
1. Added `pyproject.toml` for proper Nixpacks Python package detection
2. Documented that manual Railway dashboard connection is required (Settings → GitHub tab → Connect Repository)
3. Code is ready; deployment will auto-trigger once GitHub integration is configured in Railway dashboard

**Prevention:** For future Railway deployments:
- Always connect GitHub repo via Railway dashboard first (not CLI tokens)
- Add `pyproject.toml` for Python projects to ensure Nixpacks detects the framework correctly
- Verify Procfile exists with proper start command before deployment
- Test imports locally: `python3 -c "from main import app"`

---

<!-- NEW LESSONS GO BELOW THIS LINE -->
