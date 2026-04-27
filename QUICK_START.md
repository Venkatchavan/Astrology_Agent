# ⚡ Quick Start Guide

**Get up and running with the Astrology Hybrid Agent in 5 minutes!**

---

## 🎯 What You'll Get

- **7-Section Fact Sheet**: Planetary positions, aspects, Dasha, D9, numerology
- **AI Reading**: 3,000-5,000 word comprehensive astrological analysis
- **Processing Time**: ~15-30 seconds per chart

---

## 📋 Prerequisites

✅ Python 3.13.2 (or 3.10+)  
✅ Internet connection (for Gemini API)  
✅ Windows/Linux/Mac  

---

## 🚀 Installation (3 Steps)

### Step 1: Setup Virtual Environment

```bash
# Navigate to project folder
cd G:\Hobby_projects\Astrology_Hybrid_Agent

# Activate virtual environment
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
```

### Step 2: Verify Dependencies (Already Installed)

```bash
# Check if packages are installed
python -c "import langchain_google_genai; print('✓ Gemini')"
python -c "import chromadb; print('✓ ChromaDB')"
python -c "import sentence_transformers; print('✓ Embeddings')"
```

If any fail, install:
```bash
pip install langchain-google-genai==4.0.0
pip install langchain-huggingface==1.2.0
pip install sentence-transformers==5.2.0
pip install chromadb==1.3.7
pip install python-dotenv
pip install pydantic
```

### Step 3: Verify API Key (Already Configured)

```bash
# Check .env file
Get-Content .env | Select-String "GOOGLE_API_KEY"

# Expected output:
# GOOGLE_API_KEY=your-google-api-key-here
```

✅ **API Key is already configured and ready!**

---

## 🎬 Run Your First Chart (30 seconds)

### Example 1: India Independence Chart

```bash
python main.py --date 1947-08-15 --time 00:00 --lat 28.6139 --lon 77.2090 --name "India Independence" --location "New Delhi"
```

**Expected Output**:
```
=== ASTROLOGICAL ANALYSIS ===
Date: 1947-08-15 00:00:00 UTC
Location: New Delhi (28.6139°N, 77.2090°E)

SECTION 1: PLANETARY POSITIONS (Sidereal/Lahiri)
Sun    : Gemini 28.39° | Punarvasu | Pada 3 | Ruler: Jupiter
Moon   : Taurus  2.06° | Krittika  | Pada 2 | Ruler: Sun
...

[7 sections + 3,000-word AI synthesis]
```

### Example 2: Your Personal Chart

```bash
python main.py --date YYYY-MM-DD --time HH:MM --lat YOUR_LAT --lon YOUR_LON --name "Your Name" --location "Your City"
```

**Replace**:
- `YYYY-MM-DD`: Your birth date (e.g., 1990-05-15)
- `HH:MM`: Your birth time in 24-hour format UTC (e.g., 14:30)
- `YOUR_LAT`: Your latitude (e.g., 19.0760 for Mumbai)
- `YOUR_LON`: Your longitude (e.g., 72.8777 for Mumbai)

---

## 🛠️ Command Options

### Required Arguments

```bash
--date      Birth date (YYYY-MM-DD format)
--time      Birth time (HH:MM, 24-hour UTC)
--lat       Latitude (decimal degrees)
--lon       Longitude (decimal degrees)
```

### Optional Arguments

```bash
--name      Person's name (enables numerology Section 7)
--location  Location name (display only, e.g., "Mumbai")
--no-llm    Skip AI synthesis (fact sheet only, faster)
```

---

## 🌍 Major City Coordinates

Use these for quick testing:

| City | Latitude | Longitude | Example |
|------|----------|-----------|---------|
| New Delhi | 28.6139 | 77.2090 | `--lat 28.6139 --lon 77.2090` |
| Mumbai | 19.0760 | 72.8777 | `--lat 19.0760 --lon 72.8777` |
| Bengaluru | 12.9716 | 77.5946 | `--lat 12.9716 --lon 77.5946` |
| Kolkata | 22.5726 | 88.3639 | `--lat 22.5726 --lon 88.3639` |
| Chennai | 13.0827 | 80.2707 | `--lat 13.0827 --lon 80.2707` |
| London | 51.5074 | -0.1278 | `--lat 51.5074 --lon -0.1278` |
| New York | 40.7128 | -74.0060 | `--lat 40.7128 --lon -74.0060` |
| Los Angeles | 34.0522 | -118.2437 | `--lat 34.0522 --lon -118.2437` |

---

## 📖 Understanding the Output

### 7-Section Fact Sheet

**Section 1: Planetary Positions**
- 9 planets with zodiac sign, degrees, nakshatra, pada, ruler

**Section 2: Vedic Aspects**
- Classical aspect relationships between planets

**Section 3: Structural Analysis**
- Dominant element, retrograde planets, special states

**Section 4: Key Relationships**
- Elemental pairs and supportive connections

**Section 5: Vimshottari Dasha**
- 120-year cycle, current period, birth balance

**Section 6: Navamsa (D9)**
- Divisional chart, Vargottama planets (supreme strength)

**Section 7: Numerology** (if name provided)
- Life Path, Destiny, Attitude numbers
- Harmony score with astrology (1.0x - 2.0x)

### AI Synthesis (with LLM)

**Narrative Sections**:
1. Core Personality & Emotional Nature
2. Strengths, Talents & Natural Gifts
3. Challenges & Growth Opportunities
4. Life Themes & Purpose
5. Timing Analysis (Dasha interpretation)
6. D9 & Numerology Integration

**Length**: 3,000-5,000 words  
**Processing Time**: 15-30 seconds

---

## ⚡ Quick Commands Cheatsheet

```bash
# Full analysis (with AI)
python main.py --date 1947-08-15 --time 00:00 --lat 28.6139 --lon 77.2090 --name "India"

# Fact sheet only (no AI, faster)
python main.py --date 1947-08-15 --time 00:00 --lat 28.6139 --lon 77.2090 --no-llm

# Without numerology (no name)
python main.py --date 1947-08-15 --time 00:00 --lat 28.6139 --lon 77.2090

# Save to file
python main.py --date 1947-08-15 --time 00:00 --lat 28.6139 --lon 77.2090 > reading.txt
```

---

## 🧪 Test the System

### Test 1: Verify Installation

```bash
python test_gemini.py
```

**Expected**: Connection to Gemini API successful

### Test 2: Test Numerology + D9

```bash
python test_phase5_6.py
```

**Expected**: Numerology calculations and Vargottama detection working

### Test 3: Validate Dasha

```bash
python validate_dasha.py
```

**Expected**: Dasha dates accurate to ±1 day

---

## 🚨 Troubleshooting

### Problem: "No module named 'langchain_google_genai'"

**Solution**:
```bash
pip install langchain-google-genai==4.0.0
```

### Problem: "API key not found"

**Solution**:
```bash
# Check .env file exists and contains:
GOOGLE_API_KEY=your-google-api-key-here
```

### Problem: "ChromaDB error"

**Solution**:
```bash
# Delete and recreate database
Remove-Item -Recurse -Force data\chroma_db
python -c "from agents.rag_retriever import get_rag_retriever; get_rag_retriever()"
```

### Problem: "Slow AI synthesis"

**Causes**:
- Normal: First request initializes embeddings (~10s)
- Network: Check internet connection
- API: Gemini free tier rate limits (60 req/min)

**Solutions**:
- Use `--no-llm` for fact sheet only (instant)
- Wait 1 second between requests
- Upgrade to Gemini paid tier

---

## 📚 Learn More

**Complete Documentation**: [DOCUMENTATION.md](DOCUMENTATION.md) (25,000 words)

**Key Topics**:
- [System Architecture](DOCUMENTATION.md#-system-architecture)
- [Implementation Phases](PHASES_SUMMARY.md)
- [Data Sources](DATA_SOURCES.md)
- [All Features](README.md#-features)

**Quick Links**:
- Architecture Diagram: [README.md](README.md#%EF%B8%8F-architecture-ascii)
- Usage Examples: [README.md](README.md#-usage-examples)
- Performance Metrics: [DOCUMENTATION.md](DOCUMENTATION.md#-performance-metrics)

---

## 🎓 Example Commands for Different Use Cases

### Personal Birth Chart
```bash
python main.py --date 1995-07-10 --time 14:30 --lat 12.9716 --lon 77.5946 --name "John Doe" --location "Bengaluru"
```

### Historical Event Analysis
```bash
python main.py --date 1969-07-20 --time 20:17 --lat 0.6745 --lon 23.4731 --name "Moon Landing" --location "Sea of Tranquility"
```

### Quick Fact Sheet (No AI)
```bash
python main.py --date 2000-01-01 --time 00:00 --lat 40.7128 --lon -74.0060 --no-llm
```

### Company/Organization Chart
```bash
python main.py --date 2004-02-04 --time 18:00 --lat 42.3656 --lon -71.1040 --name "Facebook" --location "Cambridge"
```

---

## 💡 Pro Tips

**Tip 1: Time Zone Conversion**
- System uses UTC time
- Convert local time to UTC before input
- Example: IST (UTC+5:30) 12:00 → UTC 06:30

**Tip 2: Coordinate Precision**
- More decimal places = more precise
- Good: 28.6139 (4 decimals, ~11m precision)
- Better: 28.613889 (6 decimals, ~0.1m precision)

**Tip 3: Name for Numerology**
- Include full name for accurate Destiny number
- Example: "India Independence" (both words)
- Omit for anonymous charts

**Tip 4: Batch Processing**
```bash
# Create a script for multiple charts
for name in person1 person2 person3; do
  python main.py --date ... --time ... --lat ... --lon ... --name $name > ${name}_reading.txt
done
```

**Tip 5: Fact Sheet Only (Fast Mode)**
- Use `--no-llm` when you need quick data
- Processing: <1 second vs 15-30 seconds
- Perfect for batch analysis or data extraction

---

## 🎯 Success Checklist

- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip list | Select-String "langchain|chromadb"`)
- [ ] API key verified (`.env` contains `GOOGLE_API_KEY`)
- [ ] Test command executed successfully
- [ ] Output shows all 7 sections + AI synthesis

**If all checked** ✅ → You're ready to use the system!

---

## 🚀 Next Steps

1. **Run your own birth chart** using the template above
2. **Read the documentation** to understand deeper features
3. **Explore test scripts** to see validation examples
4. **Check [DOCUMENTATION.md](DOCUMENTATION.md)** for advanced usage

---

## 📞 Getting Help

**If stuck**:
1. Check [DOCUMENTATION.md](DOCUMENTATION.md) first
2. Review error messages carefully
3. Run test scripts to isolate issues
4. Check `.env` file for API key
5. Verify internet connection (for Gemini API)

**Common Issues**: See Troubleshooting section above

---

**Last Updated**: December 15, 2025  
**System Version**: 1.0.0  
**Status**: ✅ Production Ready

---

**Ready to begin?** Run this command now:

```bash
python main.py --date 1947-08-15 --time 00:00 --lat 28.6139 --lon 77.2090 --name "India Independence" --location "New Delhi"
```

**Expected time**: 15-30 seconds  
**Expected output**: 7-section fact sheet + 3,000-word AI reading

🌟 **Enjoy exploring Vedic astrology with AI!** 🌟
