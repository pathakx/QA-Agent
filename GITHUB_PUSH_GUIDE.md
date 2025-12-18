# 🚀 Push to GitHub - Step by Step Guide

## ⚠️ IMPORTANT - Before You Push

**Your `.env` file contains sensitive API keys!** 

I've updated `.gitignore` to exclude it, but let's verify:

```bash
# Check if .env will be ignored
git check-ignore .env
```

If it says `.env`, you're safe! ✅

---

## 📋 Prerequisites

1. **GitHub Account**: Sign up at [github.com](https://github.com) if you don't have one
2. **Git Installed**: Check with `git --version`
3. **GitHub Repository**: Create a new repo on GitHub

---

## 🎯 Step-by-Step Instructions

### Step 1: Initialize Git (if not already done)

```bash
cd b:\Project\qa-agent
git init
```

### Step 2: Check Git Status

```bash
git status
```

**Make sure `.env` is NOT listed!** If it is, STOP and fix `.gitignore` first.

### Step 3: Add All Files

```bash
git add .
```

### Step 4: Commit Your Changes

```bash
git commit -m "Initial commit: QA Agent with Groq and Pinecone"
```

### Step 5: Create a New Repository on GitHub

1. Go to [github.com](https://github.com)
2. Click the **"+"** icon (top right)
3. Select **"New repository"**
4. Name it: `qa-agent` (or your preferred name)
5. **Don't** initialize with README (we already have one)
6. Click **"Create repository"**

### Step 6: Link Your Local Repo to GitHub

Replace `YOUR_USERNAME` with your actual GitHub username:

```bash
git remote add origin https://github.com/YOUR_USERNAME/qa-agent.git
```

### Step 7: Push to GitHub

```bash
git branch -M main
git push -u origin main
```

**If prompted for credentials:**
- Username: Your GitHub username
- Password: Use a **Personal Access Token** (not your password)

---

## 🔑 Creating a Personal Access Token (PAT)

GitHub requires a token instead of password:

1. Go to GitHub → **Settings** → **Developer settings**
2. Click **Personal access tokens** → **Tokens (classic)**
3. Click **Generate new token** → **Generate new token (classic)**
4. Give it a name: `qa-agent-push`
5. Select scopes: Check **`repo`** (full control of private repositories)
6. Click **Generate token**
7. **Copy the token** (you won't see it again!)
8. Use this token as your password when pushing

---

## 🔄 Quick Commands Reference

### First Time Setup
```bash
cd b:\Project\qa-agent
git init
git add .
git commit -m "Initial commit: QA Agent with Groq and Pinecone"
git remote add origin https://github.com/YOUR_USERNAME/qa-agent.git
git branch -M main
git push -u origin main
```

### Future Updates
```bash
git add .
git commit -m "Your commit message here"
git push
```

---

## ✅ Verification Checklist

Before pushing, verify:

- [ ] `.env` file is in `.gitignore`
- [ ] Run `git status` - `.env` should NOT appear
- [ ] `venv/` folder is ignored
- [ ] `chroma_db/` folder is ignored
- [ ] `backend_error.log` is ignored
- [ ] No API keys in any committed files

---

## 🛡️ Security Best Practices

### ✅ DO:
- ✅ Keep `.env` in `.gitignore`
- ✅ Use `.env.example` for template (without real keys)
- ✅ Document required environment variables in README
- ✅ Use GitHub Secrets for deployment

### ❌ DON'T:
- ❌ Commit `.env` file
- ❌ Hardcode API keys in code
- ❌ Share your Personal Access Token
- ❌ Commit `venv/` or `chroma_db/`

---

## 📝 Your `.env.example` File

I've created `.env.example` for you. This is safe to commit:

```env
# Groq LLM Configuration
GROQ_API_KEY=your_groq_api_key_here

# Pinecone Vector Store Configuration
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=qa-agent-index
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1

# Backend URL
BACKEND_URL=http://localhost:8000
```

---

## 🔧 Troubleshooting

### "Permission denied" error
**Solution**: Use Personal Access Token instead of password

### ".env file is being tracked"
**Solution**: 
```bash
git rm --cached .env
git commit -m "Remove .env from tracking"
```

### "Remote already exists"
**Solution**:
```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/qa-agent.git
```

### "Failed to push"
**Solution**: Make sure you have write access to the repository

---

## 📦 What Gets Pushed

### ✅ Included:
- Source code (`backend/`, `frontend/`)
- Configuration files (`requirements.txt`, `.env.example`)
- Documentation (`README.md`)
- Test assets (`test_assets/`)
- `.gitignore`

### ❌ Excluded:
- `.env` (API keys)
- `venv/` (virtual environment)
- `chroma_db/` (database files)
- `__pycache__/` (Python cache)
- `*.log` (log files)
- `backend/data/docs/*` (uploaded documents)

---

## 🌐 After Pushing

Your repository will be at:
```
https://github.com/YOUR_USERNAME/qa-agent
```

### Share Your Project:
1. Add a good README with screenshots
2. Add topics/tags for discoverability
3. Consider adding a LICENSE file
4. Add GitHub Actions for CI/CD (optional)

---

## 🚀 Deploy to Render

After pushing to GitHub:

1. Go to [render.com](https://render.com)
2. Click **New** → **Web Service**
3. Connect your GitHub repository
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables (from `.env`)
6. Deploy!

---

## 📞 Need Help?

If you encounter issues:
1. Check git status: `git status`
2. Check remote: `git remote -v`
3. Check branch: `git branch`
4. View commit history: `git log --oneline`

---

## 🎉 Summary

**Commands to run:**
```bash
# 1. Initialize and commit
git init
git add .
git commit -m "Initial commit: QA Agent with Groq and Pinecone"

# 2. Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/qa-agent.git

# 3. Push
git branch -M main
git push -u origin main
```

**That's it!** Your code is now on GitHub! 🎊
