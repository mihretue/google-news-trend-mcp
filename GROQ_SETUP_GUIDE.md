# Groq Free API Setup Guide

## Why Groq?

- ✅ **Completely FREE** - No credit card required
- ✅ **Generous free tier** - 30 requests per minute
- ✅ **Fast inference** - Groq is known for speed
- ✅ **No quota issues** - Unlike OpenAI
- ✅ **Easy to use** - Drop-in replacement for OpenAI

## Step 1: Create Groq Account

1. Go to https://console.groq.com/keys
2. Click "Sign Up" (or "Sign In" if you have an account)
3. Create your account with email/password or Google/GitHub

## Step 2: Get Your API Key

1. After signing in, you'll see your API keys page
2. Click "Create API Key" or copy the existing key
3. Copy the key (starts with `gsk_`)

## Step 3: Update Your .env File

Edit `backend/.env` and replace:

```bash
GROQ_API_KEY=gsk_YOUR_GROQ_API_KEY_HERE
```

With your actual key:

```bash
GROQ_API_KEY=gsk_abc123def456...
```

## Step 4: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This will install `langchain-groq` which is now included.

## Step 5: Restart Backend

```bash
cd backend
py -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Step 6: Test

1. Go to http://localhost:3000
2. Sign up or login
3. Send a message
4. It should now work with Groq!

## Available Models

Groq offers several free models:

- `mixtral-8x7b-32768` (default) - Fast, good quality
- `llama2-70b-4096` - Larger model
- `gemma-7b-it` - Smaller, faster

To change the model, edit `backend/app/services/agent/react_agent.py` line 24:

```python
model_name="mixtral-8x7b-32768"  # Change this
```

## Rate Limits

- **Free tier**: 30 requests per minute
- **Tokens**: 6,000 tokens per minute

This is plenty for testing and development!

## Troubleshooting

### "Invalid API Key"
- Make sure you copied the key correctly
- Check it starts with `gsk_`
- Restart the backend after updating .env

### "Rate limit exceeded"
- Wait a minute and try again
- Free tier has 30 requests/minute limit
- This is normal for free tier

### "Model not found"
- Make sure you're using a valid Groq model name
- Check the model name in `react_agent.py`

## Switching Back to OpenAI

If you want to use OpenAI later:

1. Update `backend/.env` with your OpenAI key
2. Edit `backend/app/services/agent/react_agent.py`
3. Change line 18 from:
   ```python
   from langchain_groq import ChatGroq
   ```
   To:
   ```python
   from langchain_openai import ChatOpenAI
   ```
4. Change line 24-27 from:
   ```python
   self.llm = ChatGroq(
       temperature=0.7,
       model_name="mixtral-8x7b-32768",
       groq_api_key=settings.groq_api_key
   )
   ```
   To:
   ```python
   self.llm = ChatOpenAI(
       temperature=0.7,
       openai_api_key=settings.openai_api_key
   )
   ```

## More Info

- Groq Console: https://console.groq.com
- Groq Docs: https://console.groq.com/docs
- LangChain Groq: https://python.langchain.com/docs/integrations/llms/groq

---

**You're all set! Enjoy using Groq for free!** 🚀
