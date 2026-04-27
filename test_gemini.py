"""
Quick Gemini API Setup and Test Script
Run this to verify your Gemini API key works.
"""

import os
from pathlib import Path

# Load .env file
from dotenv import load_dotenv
load_dotenv()

def test_gemini_api():
    """Test if Gemini API key is configured and working."""
    
    print("=" * 70)
    print("GEMINI API CONFIGURATION TEST")
    print("=" * 70)
    
    # Check for API key
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("\n❌ No Gemini API key found!")
        print("\nTo fix this:")
        print("1. Get your free API key from: https://aistudio.google.com/apikey")
        print("2. Open the .env file in this directory")
        print("3. Replace 'your-gemini-api-key-here' with your actual key:")
        print("   GOOGLE_API_KEY=AIzaSy...")
        print("4. Save the file and run this script again")
        return False
    
    if api_key == "your-gemini-api-key-here":
        print("\n⚠️  API key not updated yet!")
        print("\nYou need to:")
        print("1. Open the .env file")
        print("2. Replace 'your-gemini-api-key-here' with your real Gemini API key")
        print("3. Save and run again")
        return False
    
    print(f"\n✓ Found API key: {api_key[:20]}...")
    
    # Test the API
    print("\nTesting Gemini API connection...")
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.7,
            google_api_key=api_key
        )
        
        # Simple test query
        response = llm.invoke("Say 'Hello from Gemini!' in exactly 3 words.")
        
        print("✓ API connection successful!")
        print(f"\nTest response: {response.content}")
        print("\n" + "=" * 70)
        print("✅ GEMINI IS READY!")
        print("=" * 70)
        print("\nYou can now run the full analysis:")
        print("python main.py --date 2025-12-15 --time 12:00 --lat 28.6139 --lon 77.2090")
        print("\nIt will automatically use Gemini for AI synthesis!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ API test failed: {e}")
        print("\nPossible issues:")
        print("- Invalid API key")
        print("- Network connection problem")
        print("- API quota exceeded")
        return False


if __name__ == "__main__":
    test_gemini_api()
