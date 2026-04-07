# ⭐ FOR RECRUITERS - How to Test the API

## 🎯 The Main Link to Share

**Share this HuggingFace Space link:**
```
https://huggingface.co/spaces/shahid21/openenv
```

## 📍 What Recruiters Will See

### On the HuggingFace Space Page:

At the top of the page, they'll see:

> ## 🎯 Quick Start - Interactive API Testing
> 
> **👉 [Click here to open Interactive API Documentation](https://shahid21-openenv.hf.space/docs) 👈**

### What Happens When They Click the Link:

They'll be taken to **Swagger UI** where they can:
- ✅ See all API endpoints with full documentation
- ✅ Click "Try it out" to test endpoints
- ✅ Execute real API calls
- ✅ See live responses with scores and feedback

## 🚀 Quick Demo Path (For Recruiters)

### Step 1: Open the Space
Visit: https://huggingface.co/spaces/shahid21/openenv

### Step 2: Click the Documentation Link
Click on: **"Click here to open Interactive API Documentation"**

### Step 3: Test POST /reset
1. Scroll to **POST /reset**
2. Click "Try it out"
3. Enter:
```json
{
  "task_name": "email_triage"
}
```
4. Click "Execute"
5. See the response with email content and instructions

### Step 4: Test POST /step
1. Copy the `session_id` from step 3
2. Scroll to **POST /step**
3. Click "Try it out"
4. Enter (replace the session_id):
```json
{
  "session_id": "PASTE_SESSION_ID_HERE",
  "action": {
    "action_type": "classify",
    "target": "email",
    "value": "complaint",
    "reasoning": "Customer frustrated about billing issue"
  }
}
```
5. Click "Execute"
6. See the reward score, feedback, and phase progression!

## 📊 What Makes This Impressive

When recruiters test the API, they'll see:

1. **Professional API Documentation** - Industry-standard Swagger UI
2. **Real-Time Responses** - Actual AI evaluation results
3. **Sophisticated Scoring** - Breakdown of correctness, reasoning, progress
4. **Multiple Tasks** - 4 different professional scenarios
5. **Production Deployment** - Live on HuggingFace with Docker
6. **Complete Workflow** - Multi-phase task progression

## 🔗 All Important Links

| Link | Purpose |
|------|---------|
| https://huggingface.co/spaces/shahid21/openenv | Main Space page (START HERE) |
| https://shahid21-openenv.hf.space/docs | Interactive API docs (Swagger UI) |
| https://shahid21-openenv.hf.space/redoc | Alternative docs (ReDoc) |
| https://github.com/shahid2300033762/openenv | Source code on GitHub |

## 💬 What to Say to Recruiters

**Email Template:**

```
Subject: AI Evaluation Environment - Live Demo

Hi [Recruiter Name],

I've built a production-grade AI evaluation environment that's deployed 
and ready to test interactively.

🔗 Live Demo: https://huggingface.co/spaces/shahid21/openenv

On the page, click the link that says "Interactive API Documentation" 
to access the Swagger UI where you can test the API with real-time 
responses.

Key Features:
• 4 realistic professional workflow tasks (Email Triage, Data Cleaning, 
  Code Review, Incident Response)
• Production FastAPI backend deployed on HuggingFace Spaces
• Sophisticated reward system with semantic evaluation
• 52 comprehensive tests with 85%+ coverage
• Full OpenAPI/Swagger documentation

Feel free to test any of the endpoints - they're fully functional!

Best regards,
[Your Name]
```

## ✅ Current Status

- ✅ README updated with prominent /docs links
- ✅ Deployed to HuggingFace Spaces
- ✅ Interactive Swagger UI accessible
- ✅ All API endpoints working
- ✅ Multiple tasks available for testing

**Status: Ready for recruiter review!** 🎉

---

## 🎥 Screen Recording Suggestion

If you want to create a demo video, show:

1. Opening the HuggingFace Space link
2. Clicking on "Interactive API Documentation"
3. Testing POST /reset with email_triage
4. Copying the session_id
5. Testing POST /step with a classify action
6. Showing the reward breakdown and feedback

This 2-minute demo will be very impressive!
