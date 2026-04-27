"""
Main Orchestrator - Astrological Hybrid Agent
Entry point for the complete astrological analysis system.

This orchestrates the Mixture of Experts architecture:
- Math Layer: EphemerisEngine (precise calculations)
- Logic Layer: Expert agents (rule-based analysis)
- Knowledge Layer: RAG system (domain knowledge)
- Synthesis Layer: LLM (interpretation)
"""

import os
import sys
from datetime import datetime
from pathlib import Path
import logging
import argparse

from pydantic import ValidationError
from dotenv import load_dotenv

from synthesizer import AstrologicalOrchestrator, BirthData

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def initialize_llm(model: str = "auto", temperature: float = 0.7):
    """
    Initialize the LLM for synthesis.
    Auto-detects available API keys: Google Gemini > OpenAI > Anthropic
    
    Args:
        model: Model name (e.g., 'gemini-1.5-flash', 'gpt-4', 'claude-3-sonnet') or 'auto'
        temperature: Temperature for generation
    
    Returns:
        LangChain LLM instance or None if initialization fails
    """
    # Auto-detect available API keys
    if model == "auto":
        if os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"):
            model = "gemini-2.5-flash"
            logger.info("Auto-detected: Using Google Gemini")
        elif os.getenv("OPENAI_API_KEY"):
            model = "gpt-4o-mini"
            logger.info("Auto-detected: Using OpenAI")
        elif os.getenv("ANTHROPIC_API_KEY"):
            model = "claude-3-sonnet-20240229"
            logger.info("Auto-detected: Using Anthropic Claude")
        else:
            logger.warning("No API key found. Set one of:")
            logger.warning("  - GOOGLE_API_KEY or GEMINI_API_KEY (Gemini - Free tier available)")
            logger.warning("  - OPENAI_API_KEY (GPT models)")
            logger.warning("  - ANTHROPIC_API_KEY (Claude models)")
            return None
    
    # Initialize Gemini
    if model.startswith("gemini"):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.warning("GOOGLE_API_KEY or GEMINI_API_KEY not found")
                return None
            
            llm = ChatGoogleGenerativeAI(
                model=model,
                temperature=temperature,
                google_api_key=api_key
            )
            
            logger.info(f"✓ Initialized Google Gemini ({model}) with temperature {temperature}")
            return llm
            
        except ImportError:
            logger.warning("langchain-google-genai not installed")
            logger.warning("Install with: pip install langchain-google-genai")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            return None
    
    # Initialize OpenAI
    elif model.startswith("gpt"):
        try:
            from langchain_openai import ChatOpenAI
            
            if not os.getenv("OPENAI_API_KEY"):
                logger.warning("OPENAI_API_KEY not found in environment")
                return None
            
            llm = ChatOpenAI(
                model=model,
                temperature=temperature
            )
            
            logger.info(f"✓ Initialized OpenAI ({model}) with temperature {temperature}")
            return llm
            
        except ImportError:
            logger.warning("langchain-openai not installed")
            logger.warning("Install with: pip install langchain-openai")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
            return None
    
    # Initialize Anthropic
    elif model.startswith("claude"):
        try:
            from langchain_anthropic import ChatAnthropic
            
            if not os.getenv("ANTHROPIC_API_KEY"):
                logger.warning("ANTHROPIC_API_KEY not found in environment")
                return None
            
            llm = ChatAnthropic(
                model=model,
                temperature=temperature
            )
            
            logger.info(f"✓ Initialized Anthropic Claude ({model}) with temperature {temperature}")
            return llm
            
        except ImportError:
            logger.warning("langchain-anthropic not installed")
            logger.warning("Install with: pip install langchain-anthropic")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic: {e}")
            return None
    
    else:
        logger.error(f"Unknown model: {model}")
        logger.info("Supported models: gemini-1.5-flash, gpt-4o-mini, claude-3-sonnet-20240229")
        return None


def run_analysis(
    dt: datetime,
    lat: float,
    lon: float,
    location_name: str = None,
    name: str = None,
    use_llm: bool = True,
    use_rag: bool = True,
    output_file: str = None
):
    """
    Run complete astrological analysis.
    
    Args:
        dt: Birth datetime (IST - Indian Standard Time)
        lat: Latitude
        lon: Longitude
        location_name: Name of birth place
        name: Person's name
        use_llm: Whether to use LLM for synthesis
        use_rag: Whether to use RAG for knowledge retrieval
        output_file: Optional file to save output
    """
    logger.info("=" * 70)
    logger.info("ASTROLOGICAL HYBRID AGENT - Analysis Starting")
    logger.info("=" * 70)
    
    # Initialize LLM
    llm = None
    if use_llm:
        llm = initialize_llm()
        if llm is None:
            logger.warning("Proceeding without LLM - will output fact sheet only")
    
    # Initialize orchestrator
    logger.info("\nInitializing orchestrator...")
    orchestrator = AstrologicalOrchestrator(
        llm=llm,
        data_dir="data",
        docs_dir="docs",
        use_rag=use_rag
    )
    
    # Create birth data
    birth_data = BirthData(
        datetime=dt,
        latitude=lat,
        longitude=lon,
        location_name=location_name,
        name=name
    )
    
    # Display input
    logger.info("\n" + "=" * 70)
    logger.info("BIRTH DATA")
    logger.info("=" * 70)
    if name:
        logger.info(f"Name:     {name}")
    
    logger.info(f"Date/Time: {dt.strftime('%Y-%m-%d %H:%M')} IST")
    logger.info(f"Location:  {lat}°N, {lon}°E")
    if location_name:
        logger.info(f"Place:     {location_name}")
    
    # Run analysis
    logger.info("\n" + "=" * 70)
    logger.info("RUNNING ANALYSIS")
    logger.info("=" * 70)
    
    reading = orchestrator.analyze_chart(birth_data)
    
    # Display results
    logger.info("\n" + "=" * 70)
    logger.info("FACT SHEET")
    logger.info("=" * 70)
    print("\n" + reading.fact_sheet)
    
    logger.info("\n" + "=" * 70)
    logger.info("SYNTHESIS")
    logger.info("=" * 70)
    print("\n" + reading.synthesis)
    
    # Save to file if requested
    if output_file:
        logger.info(f"\nSaving output to {output_file}...")
        
        output = []
        output.append("=" * 70)
        output.append("ASTROLOGICAL READING")
        output.append("=" * 70)
        
        if name:
            output.append(f"\nName: {name}")
        output.append(f"Birth: {dt.strftime('%Y-%m-%d %H:%M')} IST")
        output.append(f"Location: {lat}°N, {lon}°E")
        if location_name:
            output.append(f"Place: {location_name}")
        
        output.append("\n" + reading.fact_sheet)
        output.append("\n" + "=" * 70)
        output.append("INTERPRETATION")
        output.append("=" * 70)
        output.append("\n" + reading.synthesis)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output))
        
        logger.info(f"✓ Saved to {output_file}")
    
    logger.info("\n" + "=" * 70)
    logger.info("ANALYSIS COMPLETE")
    logger.info("=" * 70)
    
    return reading


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Astrological Hybrid Agent - Vedic Chart Analysis (IST-Based)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples (ALL inputs and calculations in IST - Indian Standard Time):
  # Basic analysis
  python main.py --date "2025-12-15" --time "12:00" --lat 28.6139 --lon 77.2090
  
  # Full analysis with details
  python main.py --date "1990-05-15" --time "14:30" --lat 19.0760 --lon 72.8777 \\
                 --name "John Doe" --location "Mumbai" --output reading.txt
  
  # India Independence (midnight IST)
  python main.py --date "1947-08-15" --time "00:00" --lat 28.6139 --lon 77.2090 \\
                 --name "India Independence" --location "New Delhi"
  
  # Without LLM (fact sheet only, faster)
  python main.py --date "2025-12-15" --time "12:00" --lat 28.6139 --lon 77.2090 \\
                 --no-llm
  
  # Save output to file
  python main.py --date "1995-07-10" --time "08:15" --lat 12.9716 --lon 77.5946 \\
                 --name "Personal Chart" --location "Bengaluru" --output my_chart.txt
        """
    )
    
    # Required arguments
    parser.add_argument(
        '--date',
        required=True,
        help='Birth date in YYYY-MM-DD format'
    )
    parser.add_argument(
        '--time',
        required=True,
        help='Birth time in HH:MM format (24-hour, Indian Standard Time)'
    )
    parser.add_argument(
        '--lat',
        type=float,
        required=True,
        help='Latitude (decimal degrees)'
    )
    parser.add_argument(
        '--lon',
        type=float,
        required=True,
        help='Longitude (decimal degrees)'
    )
    
    # Optional arguments
    parser.add_argument(
        '--name',
        help='Person\'s name'
    )
    parser.add_argument(
        '--location',
        help='Birth location name'
    )
    parser.add_argument(
        '--output',
        help='Output file to save reading'
    )
    parser.add_argument(
        '--no-llm',
        action='store_true',
        help='Disable LLM synthesis (show fact sheet only)'
    )
    parser.add_argument(
        '--no-rag',
        action='store_true',
        help='Disable RAG knowledge retrieval'
    )
    
    args = parser.parse_args()
    
    # Parse datetime
    try:
        date_parts = args.date.split('-')
        time_parts = args.time.split(':')
        
        # Parse IST time (Indian Standard Time)
        # All calculations use IST directly
        dt = datetime(
            int(date_parts[0]),
            int(date_parts[1]),
            int(date_parts[2]),
            int(time_parts[0]),
            int(time_parts[1])
        )
        
        logger.info(f"Birth time (IST): {dt.strftime('%Y-%m-%d %H:%M')}")
            
    except (ValueError, IndexError) as e:
        logger.error(f"Invalid date/time format: {e}")
        logger.error("Use: --date YYYY-MM-DD --time HH:MM (Indian Standard Time)")
        sys.exit(1)
    
    # Run analysis
    try:
        run_analysis(
            dt=dt,
            lat=args.lat,
            lon=args.lon,
            location_name=args.location,
            name=args.name,
            use_llm=not args.no_llm,
            use_rag=not args.no_rag,
            output_file=args.output
        )
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
