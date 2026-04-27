"""
Quick Start Script - Run this first to verify your setup
"""

import sys
from pathlib import Path


def check_dependencies():
    """Check if all required packages are installed."""
    required = [
        ('swisseph', 'Swiss Ephemeris'),
        ('pandas', 'Pandas'),
        ('chromadb', 'ChromaDB'),
        ('langchain', 'LangChain'),
        ('pydantic', 'Pydantic'),
    ]
    
    missing = []
    for module, name in required:
        try:
            __import__(module)
            print(f"✓ {name}")
        except ImportError:
            print(f"✗ {name} - MISSING")
            missing.append(module)
    
    return missing


def check_data_files():
    """Check if data files exist."""
    data_dir = Path("data")
    required_files = [
        "nakshatra_longitudes_27.csv",
        "nakshatra_padas_108.csv",
        "nakshatra_rulers.csv"
    ]
    
    missing = []
    for filename in required_files:
        filepath = data_dir / filename
        if filepath.exists():
            print(f"✓ {filename}")
        else:
            print(f"✗ {filename} - MISSING")
            missing.append(filename)
    
    return missing


def check_structure():
    """Check project structure."""
    required_dirs = [
        "engine",
        "agents",
        "synthesizer",
        "knowledge",
        "data",
        "docs"
    ]
    
    missing = []
    for dirname in required_dirs:
        dirpath = Path(dirname)
        if dirpath.exists():
            print(f"✓ {dirname}/")
        else:
            print(f"✗ {dirname}/ - MISSING")
            missing.append(dirname)
    
    return missing


def main():
    """Run all checks."""
    print("=" * 70)
    print("ASTROLOGICAL HYBRID AGENT - SETUP CHECK")
    print("=" * 70)
    
    # Check dependencies
    print("\n1. Checking Dependencies:")
    print("-" * 70)
    missing_deps = check_dependencies()
    
    # Check data files
    print("\n2. Checking Data Files:")
    print("-" * 70)
    missing_data = check_data_files()
    
    # Check structure
    print("\n3. Checking Project Structure:")
    print("-" * 70)
    missing_dirs = check_structure()
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    all_good = True
    
    if missing_deps:
        print(f"\n✗ Missing dependencies: {', '.join(missing_deps)}")
        print("   Install with: pip install -r requirements.txt")
        all_good = False
    
    if missing_data:
        print(f"\n✗ Missing data files: {', '.join(missing_data)}")
        all_good = False
    
    if missing_dirs:
        print(f"\n✗ Missing directories: {', '.join(missing_dirs)}")
        all_good = False
    
    if all_good:
        print("\n✅ All checks passed! System is ready.")
        print("\nNext steps:")
        print("  1. Run tests: python test_ephemeris.py")
        print("  2. Try example: python example_complete.py")
        print("  3. Run analysis: python main.py --date 2025-12-15 --time 12:00 --lat 28.6139 --lon 77.2090 --no-llm")
        print("\nOptional:")
        print("  • Set OPENAI_API_KEY for LLM synthesis")
        print("  • Add PDFs to docs/ for knowledge base")
        print("  • Run: python ingest_knowledge.py --docs-dir docs")
    else:
        print("\n⚠️  Some components are missing. Please fix the issues above.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
