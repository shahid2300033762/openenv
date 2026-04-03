# Hugging Face Spaces Deployment Guide

## Overview
This guide will help you successfully deploy the OpenEnv Workflow Evaluation Environment to Hugging Face Spaces.

## Prerequisites
- Hugging Face account with write access
- Git installed locally
- Docker installed (for local testing)

## Quick Start (Recommended)

### Step 1: Create a Hugging Face Space
1. Go to [https://huggingface.co/spaces](https://huggingface.co/spaces)
2. Click "Create new Space"
3. Fill in details:
   - **Space name**: `openenv-workflow-eval` (or your preferred name)
   - **License**: MIT
   - **SDK**: Docker
   - **Visibility**: Public
4. Click "Create Space"

### Step 2: Clone the Space Repository
```bash
git clone https://huggingface.co/spaces/YOUR_USERNAME/openenv-workflow-eval
cd openenv-workflow-eval
```

### Step 3: Copy Project Files
```bash
# From the openenv-workflow repository, copy all files
# Make sure these critical files are present:
# - Dockerfile (optimized for HF Spaces)
# - requirements-prod.txt
# - .dockerignore
# - server/app.py
# - models.py
# - All task environments
# - openenv.yaml
```

### Step 4: Push to Hugging Face
```bash
git add .
git commit -m "Deploy OpenEnv to Hugging Face Spaces"
git push
```

The Space will automatically build and deploy! Check the "Logs" tab for build status.

## Local Testing (Before Deployment)

### Test 1: Validate the Environment
```bash
python main.py --validate
# Expected output: "OK All validation checks passed!"
```

### Test 2: Start the Server Locally
```bash
# Option A: Using uvicorn directly
uvicorn server.app:app --reload --port 7860

# Option B: Using Docker (if you have Docker running)
docker build -t openenv-workflow .
docker run -p 7860:7860 openenv-workflow
```

### Test 3: Test the API Endpoints
In another terminal:
```bash
# Health check
curl http://localhost:7860/health

# Create a session
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_name": "email_triage", "index": 0}'

# View API documentation
# Visit: http://localhost:7860/docs
```

## Troubleshooting

### Issue: Docker Build Hangs or Takes Forever
**Solution**: This is often due to pip dependency resolution. The new `requirements-prod.txt` fixes this by:
- Pinning exact package versions (prevents version conflict loops)
- Using only production dependencies (excludes dev/test packages)
- Increasing pip timeout to 100 seconds

**To rebuild**:
```bash
# Clear Docker cache
docker system prune -a

# Rebuild
docker build --no-cache -t openenv-workflow .
```

### Issue: "ModuleNotFoundError" When Building
**Solution**: Ensure all files are in the repository:
- `models.py` in root
- `server/` directory with `app.py`
- `tasks/` directory with all task environments
- `grading/` directory if used
- All `__init__.py` files present

### Issue: Port 7860 Already in Use
**Solution**: Use a different port
```bash
uvicorn server.app:app --host 0.0.0.0 --port 8080
```

### Issue: API Returns 404 for Health Check
**Solution**: Ensure server is running and check the endpoint format:
```bash
# Correct format (note: no trailing slash)
curl http://localhost:7860/health

# Not: http://localhost:7860/health/
```

## After Deployment

### Monitor the Space
1. Go to your Space on Hugging Face
2. Check "Logs" for any runtime errors
3. Test the `/health` endpoint
4. Use the interactive API docs at `/docs`

### Common Endpoints
- `GET /health` - Health check
- `POST /reset` - Start new session
  ```json
  {
    "task_name": "email_triage|data_cleaning|code_review|incident_response",
    "index": 0
  }
  ```
- `POST /step` - Execute action
  ```json
  {
    "session_id": "session-uuid",
    "action": { "type": "...", "value": "..." }
  }
  ```
- `GET /state/{session_id}` - Get session state
- `GET /docs` - Interactive API documentation

## Performance Notes

### Build Time
- First build: ~2-3 minutes
- Subsequent builds: ~1-2 minutes (with caching)

### Runtime
- Server startup: <5 seconds
- First API call (reset): <1 second
- Subsequent steps: <500ms

### Resource Requirements
- Memory: ~500MB (minimal)
- CPU: Minimal (no GPU needed)
- Disk: ~1GB for dependencies

## File Structure for Deployment

Required files in your Space repository:
```
/
├── Dockerfile                 # Container configuration
├── requirements-prod.txt      # Production dependencies
├── .dockerignore             # Files to exclude from container
├── server/
│   └── app.py               # FastAPI server
├── models.py                # Data models
├── openenv.yaml             # Task definitions
├── tasks/                   # Task environments
│   ├── email_triage/
│   ├── data_cleaning/
│   ├── code_review/
│   └── incident_response/
├── grading/                 # Grading utilities
├── __init__.py
└── README_HF_SPACE.md       # This file
```

## Advanced Configuration

### Custom Domain
After deployment, you can add a custom domain:
1. Go to Space Settings
2. Add custom domain
3. Update your DNS records

### Rate Limiting
The Space has built-in rate limiting. For high-traffic scenarios, contact Hugging Face support.

### Secrets Management
For sensitive environment variables:
1. Go to Space Settings → Secrets
2. Add variables like `HF_TOKEN`, `API_KEY`
3. They'll be injected at runtime (not in code)

## Success Checklist

- [ ] Space created on Hugging Face
- [ ] Repository cloned locally
- [ ] All project files copied to Space repo
- [ ] `git push` successful
- [ ] Space logs show "Build successful"
- [ ] `/health` endpoint returns 200 OK
- [ ] `/docs` endpoint shows interactive API
- [ ] Can create sessions via `/reset`

## Support & Issues

For issues:
1. Check the Space "Logs" tab
2. Run `python main.py --validate` locally
3. Check Docker build locally: `docker build -t openenv-workflow .`
4. Review this guide's troubleshooting section

## Next Steps

Once deployed:
1. Share your Space URL with users
2. Use the `/docs` endpoint for API documentation
3. Monitor Space activity in the Hub dashboard
4. Update README with your Space URL

---

**Happy deploying!** 🚀
