# Deployment Guide for Render

This guide will help you deploy PDF Buddy to Render.

## ✅ Current Configuration

This project is now configured to use:
- **Google Gemini 2.0 Flash Exp** (or 1.5 Pro) for AI features
- **MongoDB Cloud (Atlas)** or Render's MongoDB service for database

## ⚠️ Important Considerations

### 1. **Google Gemini API**
The project uses Google Gemini API for AI features. You'll need:
1. Get a Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Set it as `GEMINI_API_KEY` environment variable
3. Optionally set `GEMINI_MODEL` to specify the model (default: `gemini-2.0-flash-exp`)

**Available Models:**
- `gemini-2.0-flash-exp` (Latest, recommended)
- `gemini-1.5-pro` (More capable, slower)
- `gemini-pro` (Fallback)

### 2. **MongoDB**
You can use either:
- **MongoDB Atlas (Cloud)** - Recommended for production
- **Render's MongoDB service** - Easy setup, good for development

**For MongoDB Atlas:**
1. Create a free cluster at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a database user
3. Whitelist Render's IP addresses (or use 0.0.0.0/0 for development)
4. Get the connection string
5. Set it as `MONGODB_URI` environment variable

**For Render MongoDB:**
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "MongoDB"
3. Choose a name (e.g., `pdf-buddy-db`)
4. Select a plan (Free tier available)
5. Click "Create Database"
6. Copy the **Internal Connection String** (for same region) or **External Connection String**

### 3. **File Storage**
Render's disk storage is ephemeral. For production, consider:
- **AWS S3** or **Cloudflare R2** for file storage
- Or use Render's disk storage (files will be lost on redeploy)

## 🚀 Deployment Steps

### Step 1: Prepare Your Repository
1. Push your code to GitHub/GitLab/Bitbucket
2. Make sure all files are committed

### Step 2: Get Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the API key (you'll need this for Step 4)

### Step 3: Set Up MongoDB
**Option A: MongoDB Atlas (Recommended)**
1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a free account and cluster
3. Create a database user (Database Access → Add New Database User)
4. Whitelist IP addresses (Network Access → Add IP Address → Allow Access from Anywhere for development)
5. Click "Connect" → "Connect your application"
6. Copy the connection string (replace `<password>` with your password)

**Option B: Render MongoDB**
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "MongoDB"
3. Choose a name (e.g., `pdf-buddy-db`)
4. Select a plan (Free tier available)
5. Click "Create Database"
6. Copy the **Internal Connection String** (for same region) or **External Connection String**

### Step 4: Deploy Web Service
1. Go to Render Dashboard
2. Click "New +" → "Web Service"
3. Connect your repository
4. Configure:
   - **Name**: `pdf-buddy` (or your choice)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Choose based on your needs (Free tier available)

### Step 5: Set Environment Variables
In your Render service settings, add these environment variables:

```
SECRET_KEY=<generate a random secret key>
MONGODB_URI=<your MongoDB connection string from Step 3>
GEMINI_API_KEY=<your Gemini API key from Step 2>
GEMINI_MODEL=gemini-2.0-flash-exp
FLASK_ENV=production
PORT=10000
```

**Generate SECRET_KEY:**
```python
import secrets
print(secrets.token_hex(32))
```

**Example MONGODB_URI format:**
```
mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
```

**Note:** The code is already configured to use Gemini API - no code changes needed!

## 🔧 Alternative: Manual Deployment (Without render.yaml)

If you prefer manual setup:

1. **Create Web Service** on Render
2. **Build Command**: `pip install -r requirements.txt`
3. **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
4. **Environment Variables**: Set manually in Render dashboard

## 📊 Resource Requirements

- **Free Tier**: Limited resources, good for testing
- **Starter Plan ($7/month)**: Better for production
- **Standard Plan ($25/month)**: Recommended for production with heavy usage

## 🐛 Troubleshooting

### Build Fails
- Check Python version compatibility
- Ensure all dependencies are in `requirements.txt`
- Check build logs for specific errors

### MongoDB Connection Error
- Verify `MONGODB_URI` is set correctly
- Use Internal Connection String if database is in same region
- Check MongoDB service is running

### Gemini API Errors
- Verify `GEMINI_API_KEY` is set correctly
- Check API quota/limits in Google AI Studio
- Ensure the model name is correct (check available models)
- Check API key permissions

### File Upload Issues
- Render's disk is ephemeral - consider cloud storage
- Check file size limits
- Verify upload directory permissions

## 📚 Additional Resources

- [Render Documentation](https://render.com/docs)
- [Render Python Guide](https://render.com/docs/deploy-flask)
- [MongoDB on Render](https://render.com/docs/databases)

## ✅ Checklist

- [ ] Code pushed to Git repository
- [ ] Gemini API key obtained from Google AI Studio
- [ ] MongoDB Atlas cluster created (or Render MongoDB)
- [ ] MongoDB connection string obtained
- [ ] Web service created on Render
- [ ] Environment variables set (SECRET_KEY, MONGODB_URI, GEMINI_API_KEY)
- [ ] Test deployment
- [ ] Monitor logs for errors
- [ ] Test PDF upload and summarization

---

**Note**: The code is already configured to use Google Gemini API and MongoDB Cloud. Just set the environment variables and deploy!

