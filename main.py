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
    Render and save the full 14-section Vedic Astrology Prediction Report.
    If override_path is given, save there; otherwise output/<slug>_<YYYYMMDD>_<HHMM>.md
    """
    import re as _re
    from datetime import datetime as _dt
    from pathlib import Path as _Path

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

    generated_at = _dt.now().strftime("%Y-%m-%d %H:%M")
    display_name = name or "—"
    display_place = location_name or "—"

    b = reading.prediction_brief or {}
    sec = reading.report_sections or {}
    md_data = reading.mathematical_data

    # ── Helper: section text or placeholder ──────────────────────────────────
    def S(key: str, fallback: str = "") -> str:
        return sec.get(key, fallback).strip() if sec.get(key) else fallback

    # ── Rasi chart ────────────────────────────────────────────────────────────
    rasi_chart = _generate_south_indian_chart(md_data, name=display_name)

    # ── Planetary position table ──────────────────────────────────────────────
    PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    navamsa = md_data.get("_navamsa", {})
    asc = md_data.get("_ascendant", {})
    ps = b.get("planet_strengths", {})
    ph = b.get("planet_houses", {})
    lordships = b.get("lordships", {})

    def _planet_rows() -> str:
        rows = []
        for planet in PLANETS:
            data = md_data.get(planet, {})
            if not data:
                continue
            nak = data.get("nakshatra", {})
            pstrength = ps.get(planet, {})
            sign = pstrength.get("sign", "?")
            deg = pstrength.get("degree", 0)
            nname = nak.get("nakshatra_name", "?")
            pada = nak.get("pada", "?")
            retro = "Yes" if data.get("retrograde") else "No"
            func_role = "/".join(f"H{h}" for h in lordships.get(planet, [])) or "—"
            status = ", ".join(pstrength.get("status_list", [])) or "—"
            d9_sign = navamsa.get(planet, {}).get("d9_sign", "?")
            rows.append(
                f"| {planet} | {sign} | {deg:.2f}° | {nname} | {pada} "
                f"| {retro} | {func_role} | {status} | {d9_sign} |"
            )
        return "\n".join(rows)

    # ── Core anchors table ────────────────────────────────────────────────────
    def _anchor_rows() -> str:
        rows = []
        if asc:
            nak = asc.get("nakshatra", {})
            lagna_lord = b.get("lagna_lord", "?")
            rows.append(
                f"| Ascendant / Lagna | {asc.get('sign', '?')} {asc.get('degree', 0):.2f}° "
                f"| {nak.get('nakshatra_name', '?')} / Pada {nak.get('pada', '?')} "
                f"| {lagna_lord} | Very High |"
            )
        moon = md_data.get("Moon", {})
        if moon:
            moon_nak = moon.get("nakshatra", {})
            moon_sign = ps.get("Moon", {}).get("sign", "?")
            moon_deg = ps.get("Moon", {}).get("degree", 0)
            rows.append(
                f"| Moon | {moon_sign} {moon_deg:.2f}° "
                f"| {moon_nak.get('nakshatra_name', '?')} / Pada {moon_nak.get('pada', '?')} "
                f"| {moon_nak.get('ruler', '?')} | Very High |"
            )
        sun = md_data.get("Sun", {})
        if sun:
            sun_nak = sun.get("nakshatra", {})
            sun_sign = ps.get("Sun", {}).get("sign", "?")
            sun_deg = ps.get("Sun", {}).get("degree", 0)
            rows.append(
                f"| Sun | {sun_sign} {sun_deg:.2f}° "
                f"| {sun_nak.get('nakshatra_name', '?')} / Pada {sun_nak.get('pada', '?')} "
                f"| {sun_nak.get('ruler', '?')} | High |"
            )
        lp = b.get("life_phase", {})
        md_lord = lp.get("mahadasha", "?")
        if md_lord and md_lord in ps:
            md_ps = ps[md_lord]
            rows.append(
                f"| Current Dasha Lord | {md_lord} in {md_ps.get('sign', '?')} (H{ph.get(md_lord, '?')}) "
                f"| — | — | Very High |"
            )
        return "\n".join(rows)

    # ── Dasha overview table ──────────────────────────────────────────────────
    def _dasha_overview() -> str:
        dt_data = b.get("dasha_timeline", {})
        current = dt_data.get("current", {})
        md_lord = current.get("mahadasha", "?")
        ad_lord = current.get("antardasha", "?")
        ad_end = current.get("end_date", "?")
        schedule = dt_data.get("schedule", [])
        md_entry = next((s for s in schedule if s.get("lord") == md_lord), {})
        md_start = md_entry.get("start")
        md_end = md_entry.get("end")
        md_start_s = md_start.strftime("%Y-%m-%d") if hasattr(md_start, "strftime") else "?"
        md_end_s = md_end.strftime("%Y-%m-%d") if hasattr(md_end, "strftime") else "?"
        activated = ', '.join(b.get('life_phase', {}).get('activated_areas', [])[:3])
        rows = [
            f"| Mahadasha | {md_lord} | {md_start_s} | {md_end_s} | {activated} |",
            f"| Antardasha | {ad_lord} | — | {ad_end} | Sub-period themes |",
        ]
        return "\n".join(rows)

    # ── Antardasha schedule ───────────────────────────────────────────────────
    def _antardasha_rows() -> str:
        ads = b.get("dasha_timeline", {}).get("antardashas", [])
        rows = []
        for entry in ads:
            sub = entry.get("sub_lord", "?")
            s = entry["start"].strftime("%Y-%m-%d") if hasattr(entry.get("start"), "strftime") else "?"
            e = entry["end"].strftime("%Y-%m-%d") if hasattr(entry.get("end"), "strftime") else "?"
            rows.append(f"| {sub} | {s} | {e} |")
        return "\n".join(rows)

    # ── Upcoming mahadashas ───────────────────────────────────────────────────
    def _upcoming_md_rows() -> str:
        from engine.prediction_engine import PLANET_PHASE_TYPE
        rows = []
        for m in b.get("dasha_timeline", {}).get("upcoming_mds", []):
            lord = m.get("lord", "?")
            s = m["start"].strftime("%Y-%m-%d") if hasattr(m.get("start"), "strftime") else "?"
            e = m["end"].strftime("%Y-%m-%d") if hasattr(m.get("end"), "strftime") else "?"
            nature = PLANET_PHASE_TYPE.get(lord, "transition")
            rows.append(f"| {lord} | {s} | {e} | {nature} |")
        return "\n".join(rows)

    # ── Top themes table ──────────────────────────────────────────────────────
    def _top_themes_rows() -> str:
        rows = []
        for i, t in enumerate(b.get("top_themes", []), 1):
            evidence = t.get("evidence", ["—"])
            ev1 = (evidence[0][:80] if evidence else "—")
            timing = t.get("timing", "—")[:60]
            rows.append(f"| {i} | {t['theme']} | {t['strength']} | {ev1} | {timing} |")
        return "\n".join(rows)

    # ── Yoga table ────────────────────────────────────────────────────────────
    def _yoga_rows() -> str:
        rows = [
            f"| {y['name']} | {y['type']} | {y['description'][:90]} "
            f"| {', '.join(y['planets'])} | {y['confidence']} |"
            for y in b.get("yogas", [])
        ]
        return "\n".join(rows) or "| — | — | No significant yogas detected | — | — |"

    # ── Domain evidence list ──────────────────────────────────────────────────
    def _domain_evidence(domain: str) -> str:
        d = b.get("domains", {}).get(domain, {})
        rows = [
            f"- {'✓' if item.get('supports') else '✗'} {item['point']}"
            for item in d.get("supporting", [])
        ]
        rows.append(f"- **Confidence:** {d.get('confidence', '?')} | {d.get('dasha_relevance', '?')}")
        return "\n".join(rows)

    # ── D9 Navamsa table ──────────────────────────────────────────────────────
    def _d9_rows() -> str:
        rows = []
        for planet in PLANETS:
            d9 = navamsa.get(planet, {})
            d1_sign = ps.get(planet, {}).get("sign", "?")
            d9_sign = d9.get("d9_sign", "?")
            varg = "Yes ⭐" if d9.get("vargottama") else "No"
            rows.append(f"| {planet} | {d1_sign} | {d9_sign} | {varg} |")
        return "\n".join(rows)

    # ── H-RAG evidence table ──────────────────────────────────────────────────
    def _hrag_rows() -> str:
        rows = [
            f"| {r.get('metadata', {}).get('source', 'H-RAG context')} "
            f"| {r.get('content', '')[:100].replace('|', '—').replace(chr(10), ' ')}… | — | Retrieved |"
            for r in reading.rag_context[:8]
        ]
        return "\n".join(rows) or "| — | No H-RAG context retrieved | — | — |"

    # ── High-confidence predictions ───────────────────────────────────────────
    def _high_conf_rows() -> str:
        rows = []
        for domain, d in b.get("domains", {}).items():
            if d.get("confidence") == "High":
                sup = [e["point"] for e in d.get("supporting", []) if e.get("supports")]
                ev = (sup + ["—", "—", "—"])[:3]
                label = domain.replace("_", " ").title()
                rows.append(
                    f"| Strong {label} indication | {ev[0][:60]} | {ev[1][:60]} | {ev[2][:60]} | High |"
                )
        return "\n".join(rows) or "| — | — | — | — | High |"

    # ── Low-confidence predictions ────────────────────────────────────────────
    def _low_conf_rows() -> str:
        rows = [
            f"| {d.replace('_', ' ').title()} breakthrough | Insufficient dominant indicators "
            f"| Stronger planetary support or dasha activation needed |"
            for d, data in b.get("domains", {}).items()
            if data.get("confidence") == "Low"
        ]
        return "\n".join(rows) or "| — | All domains have Medium or High indicators | — |"

    # ── Nakshatra signature table ─────────────────────────────────────────────
    def _nakshatra_rows() -> str:
        rows = []
        for anchor_name, planet_key in [
            ("Moon Nakshatra", "Moon"),
            ("Lagna Nakshatra", None),
            ("Sun Nakshatra", "Sun"),
        ]:
            if planet_key:
                nak = md_data.get(planet_key, {}).get("nakshatra", {})
            else:
                nak = asc.get("nakshatra", {}) if asc else {}
            nname = nak.get("nakshatra_name", "?")
            rows.append(f"| {anchor_name} | {nname} | — | — | — |")
        return "\n".join(rows)

    # ─── Assemble Markdown ────────────────────────────────────────────────────
    lp = b.get("life_phase", {})
    md_lord = lp.get("mahadasha", "?")
    ad_lord = lp.get("antardasha", "?")
    lagna = b.get("lagna", "?")
    lagna_lord = b.get("lagna_lord", "?")

    lines = [
        f"# Vedic Astrology Prediction Report — {display_name}",
        "",
        "---",
        "",
        "## 0. Report Metadata",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Name | {display_name} |",
        f"| Date of Birth | {dt.strftime('%Y-%m-%d')} |",
        f"| Time of Birth | {dt.strftime('%H:%M')} IST |",
        f"| Birth Place | {display_place} |",
        f"| Latitude / Longitude | {lat}°N, {lon}°E |",
        "| Ayanamsa | Lahiri |",
        "| Chart System | Sidereal Vedic |",
        f"| Generated At | {generated_at} |",
        "| Engine | Astrology_Agent: Skyfield/JPL + Parashara + Vimshottari + H-RAG + Ollama |",
        "",
        "---",
        "",
        "## 1. Important Disclaimer",
        "",
        (
            "This report is an interpretive Vedic astrology reading based on chart calculations, "
            "classical rule-based reasoning, and retrieved knowledge from classical texts "
            "(Brihat Parashara Hora Shastra and other Vedic references). It should not be treated "
            "as medical, legal, financial, or life-critical advice. All predictions are expressed "
            "as tendencies, timing windows, and symbolic indicators — not guaranteed outcomes. "
            "Free will and conscious effort shape every result."
        ),
        "",
        "---",
        "",
        "## 2. Executive Prediction Summary",
        "",
        "### 2.1 Top 7 Life Themes",
        "",
        "| Rank | Theme | Strength | Main Evidence | Dasha Relevance |",
        "|---|---|---:|---|---|",
        _top_themes_rows(),
        "",
        "### 2.2 One-Paragraph Summary & 2.3 Current Phase",
        "",
        S("executive_summary", "_No LLM summary available — see Section 3 for chart data._"),
        "",
        "---",
        "",
        "## 3. Calculation Audit",
        "",
        "### 3.1 Core Chart Anchors",
        "",
        "| Anchor | Placement | Nakshatra / Pada | Ruler | Interpretation Weight |",
        "|---|---|---|---|---|",
        _anchor_rows(),
        "",
        "### 3.2 Planetary Position Table",
        "",
        "| Planet | Sign | Degree | Nakshatra | Pada | Retro | Functional Role | Status | D9 Sign |",
        "|---|---|---:|---|---:|---|---|---|---|",
        _planet_rows(),
        "",
        "---",
        "",
        "## 4. Chart Foundation",
        "",
        "### 4.1 Lagna-Based Personality",
        "",
        S("lagna_personality", f"_Lagna: {lagna} | Lagna Lord: {lagna_lord} — LLM not available._"),
        "",
        f"**Evidence:** Lagna {lagna}, Lagna lord {lagna_lord} in "
        f"House {ph.get(lagna_lord, '?')} "
        f"({ps.get(lagna_lord, {}).get('sign', '?')}), "
        f"{ps.get(lagna_lord, {}).get('overall', '?')}",
        "",
        "### 4.2 Moon-Based Mind and Emotional Pattern",
        "",
        S("moon_mind", "_Moon mind section — LLM not available._"),
        "",
        "### 4.3 Sun-Based Identity and Authority",
        "",
        S("sun_identity", "_Sun identity section — LLM not available._"),
        "",
        "### 4.4 Nakshatra Signature",
        "",
        "| Key Nakshatra | Point | Weight | Core Trait | Shadow Trait |",
        "|---|---|---|---|---|",
        _nakshatra_rows(),
        "",
        "---",
        "",
        "## 5. Strengths, Talents, and Natural Advantages",
        "",
        "### 5.1 Strongest Planets & Yogas",
        "",
        "| Yoga / Planet | Type | Description | Planets | Confidence |",
        "|---|---|---|---|---|",
        _yoga_rows(),
        "",
        "### 5.2 Natural Talents",
        "",
        S("strengths", "_Strengths section — LLM not available._"),
        "",
        "### 5.3 D9 / Navamsa Confirmation",
        "",
        "| Planet | D1 Sign | D9 Sign | Vargottama? |",
        "|---|---|---|---|",
        _d9_rows(),
        "",
        "---",
        "",
        "## 6. Challenges, Weaknesses, and Growth Areas",
        "",
        "### 6.1 Difficult Planetary Conditions",
        "",
        "| Issue | Planet/House | Status | Growth Advice |",
        "|---|---|---|---|",
    ]

    # 6.1 weakness rows
    from engine.prediction_engine import PLANET_NATURE as _PN
    weak_rows = []
    for planet, pdata in ps.items():
        if pdata.get("overall") == "Weakened" or "Gandanta" in pdata.get("status_list", []):
            issue = "Debilitated" if "Debilitated" in pdata.get("status_list", []) else "Gandanta"
            weak_rows.append(
                f"| {issue} | {planet} in H{ph.get(planet, '?')} ({pdata.get('sign', '?')}) "
                f"| {pdata.get('overall', '?')} | Work consciously with {planet}'s themes |"
            )
    lines.extend(weak_rows or ["| — | No debilitated planets | — | — |"])

    lines += [
        "",
        "### 6.2 Psychological Shadow Pattern",
        "",
        S("challenges", "_Challenges section — LLM not available._"),
        "",
        "---",
        "",
        "## 7. Domain-Wise Predictions",
        "",
        "---",
        "",
        "### 7.1 Career and Professional Growth",
        "",
        S("career", "_Career section — LLM not available._"),
        "",
        "**Evidence Chain:**",
        "",
        _domain_evidence("career"),
        "",
        "---",
        "",
        "### 7.2 Education, Intelligence, and Learning",
        "",
        "**Evidence Chain:**",
        "",
        _domain_evidence("education"),
        "",
        "---",
        "",
        "### 7.3 Wealth, Finance, and Assets",
        "",
        S("wealth", "_Wealth section — LLM not available._"),
        "",
        "**Evidence Chain:**",
        "",
        _domain_evidence("wealth"),
        "",
        "---",
        "",
        "### 7.4 Relationships, Marriage, and Partnership",
        "",
        S("relationships", "_Relationships section — LLM not available._"),
        "",
        "**Evidence Chain:**",
        "",
        _domain_evidence("relationships"),
        "",
        "---",
        "",
        "### 7.5 Family, Home, and Emotional Security",
        "### 7.6 Health, Energy, and Lifestyle",
        "### 7.7 Spirituality, Dharma, and Inner Development",
        "### 7.8 Foreign Travel, Relocation, and Long-Distance Opportunities",
        "",
        S("family_health_spirit", "_Sections 7.5–7.8 — LLM not available._"),
        "",
        "---",
        "",
        "## 8. Timing Engine",
        "",
        "### 8.1 Vimshottari Dasha Overview",
        "",
        "| Level | Lord | Start | End | Activated Themes |",
        "|---|---|---|---|---|",
        _dasha_overview(),
        "",
        "**Full Antardasha Schedule (Current Mahadasha):**",
        "",
        "| Antardasha Lord | Start | End |",
        "|---|---|---|",
        _antardasha_rows(),
        "",
        "### 8.2 Current Period Interpretation",
        "",
        S("dasha_interpretation", "_Dasha interpretation — LLM not available._"),
        "",
        "### 8.3 Upcoming Mahadashas",
        "",
        "| Lord | Start | End | Phase Nature |",
        "|---|---|---|---|",
        _upcoming_md_rows(),
        "",
        "---",
        "",
        "## 9. High-Confidence Predictions",
        "",
        "| Prediction | Evidence 1 | Evidence 2 | Evidence 3 | Confidence |",
        "|---|---|---|---|---|",
        _high_conf_rows(),
        "",
        "---",
        "",
        "## 10. Low-Confidence or Conditional Predictions",
        "",
        "| Possible Outcome | Why Uncertain | What Would Strengthen It |",
        "|---|---|---|",
        _low_conf_rows(),
        "",
        "---",
        "",
        "## 11. Classical Text / H-RAG Evidence",
        "",
        "| Source | Retrieved Principle | Applied To | Interpretation |",
        "|---|---|---|---|",
        _hrag_rows(),
        "",
        "---",
        "",
        "## 12. Remedies and Practical Guidance",
        "",
        "### 12.1 Behavioural Remedies",
        "",
        "| Issue | Behavioural Remedy | Reason |",
        "|---|---|---|",
    ]

    remedy_rows = []
    for planet, pdata in ps.items():
        if pdata.get("overall") == "Weakened":
            remedy_rows.append(
                f"| {planet} weakness | Honour {planet}'s significations: "
                f"{_PN.get(planet, 'its domain')} | Counteracts debilitation |"
            )
        if pdata.get("retrograde"):
            remedy_rows.append(
                f"| {planet} retrograde | Reflect before acting in {planet}'s domain; "
                f"avoid impulsiveness | Retrograde energy rewards patience |"
            )
    lines.extend(remedy_rows or ["| — | No specific remedies identified | — |"])

    lines += [
        "",
        "### 12.2 Practical Action Plan",
        "",
        "**Next 30 Days:**",
        f"- Focus on areas activated by current {ad_lord} Antardasha",
        f"- Strengthen {lagna_lord} (Lagna lord) through consistent daily practice",
        "",
        "**Next 90 Days:**",
        f"- Build momentum in domains where {md_lord} Mahadasha is supportive",
        "- Address any Weakened planet's domain through disciplined effort",
        "",
        "**Next 1 Year:**",
        "- Review career and relationship timing windows from Section 8",
        "- Re-evaluate at the next Antardasha transition",
        "",
        "---",
        "",
        "## 13. Final Verdict",
        "",
        S("final_verdict", "_Final verdict — LLM not available. See Section 2 for top themes._"),
        "",
        "---",
        "",
        "## 14. Appendix",
        "",
        "### 14.1 Rasi Chart (South Indian Style)",
        "",
        "```",
        rasi_chart,
        "```",
        "",
        "### 14.2 Raw Fact Sheet",
        "",
        "```",
        reading.fact_sheet.strip(),
        "```",
        "",
        "---",
        "",
        "*Generated by Astrology Agent — Skyfield/JPL + H-RAG + Ollama — Fully Local*",
    ]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info(f"✓ Report saved → {out_path}")
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
