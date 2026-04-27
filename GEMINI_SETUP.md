# 🚀 Gemini API Setup Guide

## Quick Start (3 Easy Steps)

### Step 1: Get Your Free Gemini API Key

1. Go to **https://aistudio.google.com/apikey**
2. Click "Create API Key"
3. Copy the key (looks like: `AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXX`)

### Step 2: Add Key to .env File

Open the `.env` file in this directory and replace:

```bash
GOOGLE_API_KEY=your-gemini-api-key-here
```

With your actual key:

```bash
GOOGLE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXX
```

**Save the file!**

### Step 3: Test It

Run the test script:

```powershell
.venv\Scripts\python.exe test_gemini.py
```

You should see:
```
✅ GEMINI IS READY!
```

---

## Run Your First AI-Powered Analysis

```powershell
.venv\Scripts\python.exe main.py `
  --date 2025-12-15 `
  --time 12:00 `
  --lat 28.6139 `
  --lon 77.2090 `
  --location "New Delhi" `
  --name "Sample Chart"
```

**Notice**: No `--no-llm` flag! The system will automatically:
1. Detect your Gemini API key
2. Calculate planetary positions
3. Run expert agents
4. Retrieve knowledge from RAG
5. **Generate AI interpretation using Gemini!**

---

## What You Get

### Without LLM (Before)
```
FACT SHEET ONLY:
✓ Planetary positions
✓ Aspects calculated
✓ Element analysis
✓ Knowledge chunks retrieved
```

### With Gemini (Now!)
```
FACT SHEET + AI SYNTHESIS:
✓ All calculations above
✓ Meaningful interpretation in natural language
✓ Context from knowledge base integrated
✓ Personalized reading combining all layers
```

---

## Example Output with Gemini

```
ASTROLOGICAL READING
======================================================================

The chart for December 15, 2025, at noon in New Delhi reveals a 
dominant Fire element with Mars, Mercury, Saturn, and Ketu positioned 
in fire signs. This suggests a dynamic, action-oriented personality 
with strong initiative.

The Moon in Ashlesha nakshatra (ruled by Mercury) at 109.27° indicates 
deep emotional intelligence and intuitive understanding. As Ashlesha 
represents the coiled serpent, there's potential for psychological 
penetration and interest in occult sciences...

[Multiple paragraphs of coherent interpretation]

The retrograde positions of Rahu and Ketu suggest internal spiritual 
development rather than external expression. Past life karma may be 
requiring resolution through...

[Continues with detailed analysis]
```

---

## Why Gemini?

✅ **Free Tier**: Generous free quota for personal use  
✅ **Fast**: Quick response times  
✅ **Quality**: Google's latest AI model  
✅ **Easy**: Simple API key setup  
✅ **No Credit Card**: Free tier doesn't require payment  

Compare to:
- OpenAI GPT: Requires payment, $$$
- Anthropic Claude: Requires payment, $$$
- Local Ollama: Free but slow on CPU

---

## Troubleshooting

### "No API key found"
- Make sure you edited `.env` file
- Check for typos in `GOOGLE_API_KEY=`
- File must be named exactly `.env` (with the dot)

### "API test failed"
- Verify your key at https://aistudio.google.com/apikey
- Check if key is enabled
- Try generating a new key

### "API quota exceeded"
- Gemini free tier has daily limits
- Wait 24 hours or upgrade to paid tier
- Monitor usage at Google AI Studio

### Still not working?
Run without LLM to verify other layers work:
```powershell
.venv\Scripts\python.exe main.py `
  --date 2025-12-15 `
  --time 12:00 `
  --lat 28.6139 `
  --lon 77.2090 `
  --no-llm
```

---

## Advanced: Using Different Models

The system now supports auto-detection of any API key:

```python
# Priority order (checks in this sequence):
1. GOOGLE_API_KEY     → Uses Gemini (gemini-1.5-flash)
2. OPENAI_API_KEY     → Uses GPT (gpt-4o-mini)
3. ANTHROPIC_API_KEY  → Uses Claude (claude-3-sonnet)
```

To force a specific model:
```powershell
# Use Gemini Pro instead of Flash
.venv\Scripts\python.exe main.py ... --llm-model gemini-1.5-pro

# Use GPT-4 (if you have OpenAI key)
.venv\Scripts\python.exe main.py ... --llm-model gpt-4o

# Use Claude (if you have Anthropic key)
.venv\Scripts\python.exe main.py ... --llm-model claude-3-sonnet-20240229
```

---

## Next Steps

1. **Test Gemini**: Run `test_gemini.py`
2. **Run Analysis**: Use the command above
3. **Explore**: Try different birth charts
4. **Expand Knowledge**: Add more PDFs to `data/pdfs/`
5. **Share**: Generate readings for friends/family

---

*Updated: December 15, 2025*  
*Gemini Integration: Complete* ✅
