"""
Main Orchestrator - Astrological Hybrid Agent
Entry point for the complete astrological analysis system.

Architecture (Mixture of Experts + H-RAG + Ollama):
- Math Layer:      EphemerisEngine (Skyfield/NASA JPL, IST input)
- Logic Layer:     Expert agents (Parashara, Nadi, Numerology)
- Knowledge Layer: H-RAG (Hierarchical RAG, ChromaDB, local embeddings)
- Synthesis Layer: Ollama LLM (fully local, no API key required)
"""

import os
import sys
import subprocess
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


def _list_ollama_models() -> list:
    """Return names of locally available Ollama models."""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True, text=True, timeout=6
        )
        lines = result.stdout.strip().split('\n')
        # Skip header row, grab the model name (first column)
        return [
            line.split()[0]
            for line in lines[1:]
            if line.strip() and line.split()
        ]
    except Exception:
        return []


def initialize_llm(model: str = "auto", temperature: float = 0.7):
    """
    Initialize a fully local Ollama LLM for synthesis.

    Ollama must be running (it starts automatically on macOS).
    To pull a model: ollama pull llama3.2

    Args:
        model: Ollama model name, or 'auto' to pick the best available.
        temperature: Sampling temperature (0.0 – 1.0).

    Returns:
        LangChain ChatOllama instance, or None on failure.
    """
    available = _list_ollama_models()

    if not available:
        logger.error(
            "No Ollama models found. Pull one first:\n"
            "  ollama pull llama3.2\n"
            "Then re-run the analysis."
        )
        return None

    # Auto-select: prefer quality models for long-form generation
    PREFERRED = ["llama3.2", "llama3.1", "mistral", "gemma3", "phi3", "qwen2.5"]

    if model == "auto":
        model = available[0]  # fallback
        for preferred in PREFERRED:
            for m in available:
                if preferred in m.lower():
                    model = m
                    break
            else:
                continue
            break

    if model not in available:
        logger.warning(
            f"Model '{model}' not found locally. Available: {available}\n"
            f"Falling back to: {available[0]}"
        )
        model = available[0]

    try:
        from langchain_ollama import ChatOllama
        llm = ChatOllama(model=model, temperature=temperature)
        logger.info(f"✓ Initialized Ollama LLM: {model} (temperature={temperature})")
        return llm
    except ImportError:
        logger.error("langchain-ollama not installed. Run: pip install langchain-ollama")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize Ollama ({model}): {e}")
        return None


def run_analysis(
    dt: datetime,
    lat: float,
    lon: float,
    location_name: str = None,
    name: str = None,
    use_llm: bool = True,
    use_rag: bool = True,
    output_file: str = None,
    model: str = "auto"
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
        llm = initialize_llm(model=model)
        if llm is None:
            logger.warning("Proceeding without LLM - will output fact sheet only")
    
    # Initialize orchestrator
    logger.info("\nInitializing orchestrator...")
    orchestrator = AstrologicalOrchestrator(
        llm=llm,
        data_dir="data",
        docs_dir="data/pdfs",
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
    
    # ── Auto-save to output/<name>_<date>_<time>.md ──────────────────────────
    _save_markdown(
        reading=reading,
        dt=dt,
        lat=lat,
        lon=lon,
        name=name,
        location_name=location_name,
        override_path=output_file,
    )

    logger.info("\n" + "=" * 70)
    logger.info("ANALYSIS COMPLETE")
    logger.info("=" * 70)
    
    return reading


def _generate_south_indian_chart(mathematical_data, name=None):
    """
    Generate a South Indian (square grid, fixed signs) Rasi chart in ASCII art.
    Planets are placed in their respective sign houses.

    South Indian layout (signs fixed, anti-clockwise from top-left):
        Pisces  | Aries  | Taurus | Gemini
        Aquarius|  [center merged]  | Cancer
        Capric. |  [center merged]  | Leo
        Sagitt. | Scorpio| Libra  | Virgo
    """
    W  = 13          # content width per cell
    CW = 2 * W + 1   # merged center content width = 27

    SIGN_NAMES = [
        "Aries", "Taurus", "Gemini", "Cancer",
        "Leo", "Virgo", "Libra", "Scorpio",
        "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    ]
    PLANET_ABBR = {
        "Sun": "Su", "Moon": "Mo", "Mercury": "Me",
        "Venus": "Ve", "Mars": "Ma", "Jupiter": "Ju",
        "Saturn": "Sa", "Rahu": "Ra", "Ketu": "Ke",
    }

    # Ascendant (Lagna) sign index
    asc_data     = mathematical_data.get('_ascendant')
    asc_sign_idx = int(asc_data['longitude'] / 30) % 12 if asc_data else None

    # Group planets by sign index (0=Aries … 11=Pisces)
    sign_planets: dict = {i: [] for i in range(12)}
    for planet, data in mathematical_data.items():
        if planet.startswith('_'):
            continue
        lon      = data.get('longitude', 0)
        sign_idx = int(lon / 30) % 12
        retro    = "(R)" if data.get('retrograde', False) else ""
        abbr     = PLANET_ABBR.get(planet, planet[:2])
        sign_planets[sign_idx].append(f"{abbr}{retro}")

    def cell(sign_idx):
        """2-line cell: [sign name (◈ if lagna), planet list]."""
        sign    = SIGN_NAMES[sign_idx]
        is_lagna = (sign_idx == asc_sign_idx)
        # Mark lagna sign name with ◈
        if is_lagna:
            label = (sign[:W - 2] + " ◈").center(W)
        else:
            label = sign[:W].center(W)
        planets = " ".join(sign_planets[sign_idx])
        if is_lagna and planets:
            planets = "Asc " + planets
        elif is_lagna:
            planets = "Asc"
        if len(planets) > W:
            planets = planets[:W - 1] + "\u2026"   # ellipsis if overflow
        return [label, planets.center(W)]

    # ── Border templates (all exactly 57 chars wide) ─────────────────────
    top         = "\u250c" + ("\u2500" * W + "\u252c") * 3 + "\u2500" * W + "\u2510"
    sep_full    = "\u251c" + ("\u2500" * W + "\u253c") * 3 + "\u2500" * W + "\u2524"
    sep_merge_t = "\u251c" + "\u2500" * W + "\u253c" + "\u2500" * CW + "\u253c" + "\u2500" * W + "\u2524"
    sep_merge_m = "\u251c" + "\u2500" * W + "\u2524" + " " * CW + "\u251c" + "\u2500" * W + "\u2524"
    sep_merge_b = "\u251c" + "\u2500" * W + "\u253c" + "\u2500" * W + "\u252c" + "\u2500" * W + "\u253c" + "\u2500" * W + "\u2524"
    bot         = "\u2514" + ("\u2500" * W + "\u2534") * 3 + "\u2500" * W + "\u2518"

    def row4(signs):
        """Two content lines for a 4-cell row."""
        cells = [cell(s) for s in signs]
        return [
            "\u2502" + "\u2502".join(c[0] for c in cells) + "\u2502",
            "\u2502" + "\u2502".join(c[1] for c in cells) + "\u2502",
        ]

    # ── Center section content ────────────────────────────────────────────
    title1 = "SOUTH INDIAN RASI".center(CW)
    title2 = (name or "Birth Chart").center(CW)
    blank  = " " * CW

    aq = cell(10)   # Aquarius  — row 2, col 1
    ca = cell(3)    # Cancer    — row 2, col 4
    cp = cell(9)    # Capricorn — row 3, col 1
    le = cell(4)    # Leo       — row 3, col 4

    chart = []
    chart.append(top)
    chart.extend(row4([11, 0, 1, 2]))        # Pisces | Aries | Taurus | Gemini
    chart.append(sep_merge_t)
    chart.append("\u2502" + aq[0] + "\u2502" + title1 + "\u2502" + ca[0] + "\u2502")
    chart.append("\u2502" + aq[1] + "\u2502" + title2 + "\u2502" + ca[1] + "\u2502")
    chart.append(sep_merge_m)
    chart.append("\u2502" + cp[0] + "\u2502" + blank   + "\u2502" + le[0] + "\u2502")
    chart.append("\u2502" + cp[1] + "\u2502" + blank   + "\u2502" + le[1] + "\u2502")
    chart.append(sep_merge_b)
    chart.extend(row4([8, 7, 6, 5]))         # Sagittarius | Scorpio | Libra | Virgo
    chart.append(bot)

    return "\n".join(chart)


def _save_markdown(reading, dt, lat, lon, name, location_name, override_path=None):
    """
    Always save a rich Markdown report to output/<slug>_<YYYYMMDD>_<HHMM>.md.
    If override_path is given, save there instead (but still as .md).
    """
    import re as _re
    from datetime import datetime as _dt
    from pathlib import Path as _Path

    # Build filename slug
    name_slug = _re.sub(r'[^a-zA-Z0-9]+', '_', (name or "chart")).strip('_').lower()
    timestamp = dt.strftime("%Y%m%d_%H%M")

    if override_path:
        out_path = _Path(override_path)
        if not out_path.suffix:
            out_path = out_path.with_suffix('.md')
    else:
        out_dir = _Path("output")
        out_dir.mkdir(exist_ok=True)
        out_path = out_dir / f"{name_slug}_{timestamp}.md"

    # ── Build Markdown ─────────────────────────────────────────────────────
    generated_at = _dt.now().strftime("%Y-%m-%d %H:%M")
    display_name = name or "—"
    display_place = location_name or "—"

    # South Indian Rasi chart diagram
    rasi_chart = _generate_south_indian_chart(reading.mathematical_data, name=display_name)

    lines = [
        f"# Vedic Astrological Reading — {display_name}",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| **Name** | {display_name} |",
        f"| **Date & Time (IST)** | {dt.strftime('%Y-%m-%d %H:%M')} |",
        f"| **Latitude / Longitude** | {lat}°N, {lon}°E |",
        f"| **Birth Place** | {display_place} |",
        f"| **Generated** | {generated_at} |",
        "",
        "---",
        "",
        "## Rasi Chart (South Indian Style)",
        "",
        "```",
        rasi_chart,
        "```",
        "",
        "---",
        "",
        "## Chart Data",
        "",
        "```",
        reading.fact_sheet.strip(),
        "```",
        "",
        "---",
        "",
        "## Interpretation",
        "",
        reading.synthesis.strip(),
        "",
        "---",
        "",
        "*Generated by Astrology Agent — H-RAG + Ollama (llama3.2) — Fully Local, No API Key*",
    ]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info(f"✓ Markdown saved → {out_path}")
    return out_path


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Astrological Hybrid Agent — Vedic Chart Analysis (H-RAG + Ollama, IST-Based)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Fully LOCAL — no API keys required. Uses Ollama for LLM synthesis.

Prerequisites:
  ollama pull llama3.2          # (one-time, ~2 GB)
  python ingest_knowledge.py    # ingest PDF books into H-RAG (optional)

Examples (ALL times in IST — Indian Standard Time):
  # Basic analysis (auto-selects best available Ollama model)
  python main.py --date "2025-12-15" --time "12:00" --lat 28.6139 --lon 77.2090

  # Full analysis with name + location + file output
  python main.py --date "1990-05-15" --time "14:30" --lat 19.0760 --lon 72.8777 \\
                 --name "Arjun Sharma" --location "Mumbai" --output reading.txt

  # Choose a specific Ollama model
  python main.py --date "1990-05-15" --time "14:30" --lat 13.0827 --lon 80.2707 \\
                 --name "Test User" --location "Chennai" --model llama3.2

  # Fact sheet only (no LLM, fastest)
  python main.py --date "2025-12-15" --time "12:00" --lat 28.6139 --lon 77.2090 \\
                 --no-llm

  # Skip RAG (useful when no PDFs ingested yet)
  python main.py --date "1990-05-15" --time "14:30" --lat 13.0827 --lon 80.2707 \\
                 --name "Test User" --location "Chennai" --no-rag

  # List available Ollama models
  ollama list
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
    parser.add_argument(
        '--model',
        default='auto',
        help='Ollama model name to use (default: auto-selects best available). '
             'Examples: llama3.2, llama3.1, mistral. Run "ollama list" to see options.'
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
            output_file=args.output,
            model=args.model
        )
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
