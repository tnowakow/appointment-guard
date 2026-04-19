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

<!-- NEW LESSONS GO BELOW THIS LINE -->
