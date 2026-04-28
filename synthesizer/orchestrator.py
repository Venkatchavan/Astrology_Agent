"""
Astrological Orchestrator — H-RAG + Ollama Edition
=====================================================
Architecture (Mixture of Experts):
  1. Math Layer      — EphemerisEngine (Skyfield/NASA JPL, IST input)
  2. Logic Layer     — Expert agents (Parashara, Nadi, State, Numerology)
  3. Knowledge Layer — Hierarchical RAG (H-RAG) with local embeddings
  4. Synthesis Layer — Ollama LLM (fully local, no API key needed)
"""

from datetime import datetime as dt_module
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator
import logging

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Import our layers
from engine import EphemerisEngine, PredictionEngine
from agents import (
    calculate_aspects,
    get_planet_relationships,
    perform_structural_analysis,
    get_hrag_retriever,          # H-RAG (replaces flat RAG)
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BirthData(BaseModel):
    """Birth data input for chart calculation.

    IMPORTANT: datetime must be in IST (Indian Standard Time) as a naive datetime
    (no tzinfo). The system automatically converts to UTC internally for
    astronomical calculations.
    """
    datetime: dt_module = Field(description="Date and time of birth (IST - Indian Standard Time, naive datetime with no tzinfo)")
    latitude: float = Field(description="Latitude of birth place")
    longitude: float = Field(description="Longitude of birth place")
    location_name: Optional[str] = Field(default=None, description="Name of birth place")
    name: Optional[str] = Field(default=None, description="Person's name")

    @field_validator("datetime")
    @classmethod
    def enforce_ist_naive(cls, v: dt_module) -> dt_module:
        """Reject timezone-aware datetimes. Only naive IST datetimes are accepted."""
        if v.tzinfo is not None:
            raise ValueError(
                "datetime must be a naive IST datetime (no tzinfo). "
                "Do NOT pass UTC or any timezone-aware datetime. "
                "Enter the local IST birth time directly, e.g. datetime(1990, 5, 15, 14, 30)."
            )
        return v


class AstrologicalReading(BaseModel):
    """Complete astrological reading output."""
    birth_data: BirthData
    mathematical_data: Dict[str, Any]
    logical_analysis: Dict[str, Any]
    rag_context: List[Dict[str, Any]]
    synthesis: str
    fact_sheet: str
    prediction_brief: Optional[Dict[str, Any]] = Field(default=None)
    report_sections: Optional[Dict[str, str]] = Field(default=None)


class AstrologicalOrchestrator:
    """
    Master orchestrator that coordinates all layers of the astrological system.
    
    Architecture (Mixture of Experts):
    1. Math Layer (y_math): EphemerisEngine - precise astronomical calculations
    2. Logic Layer (y_1, y_2, y_3): Expert agents - rule-based analysis
    3. Knowledge Layer (RAG): Domain knowledge retrieval
    4. Synthesis Layer: LLM-based interpretation
    """
    
    def __init__(
        self,
        llm: Optional[Any] = None,
        data_dir: str = "data",
        docs_dir: str = "docs",
        use_rag: bool = True
    ):
        """
        Initialize the orchestrator.
        
        Args:
            llm: LangChain LLM instance (e.g., ChatOpenAI)
            data_dir: Directory containing nakshatra CSV files
            docs_dir: Directory containing PDF knowledge base
            use_rag: Whether to use RAG system for knowledge retrieval
        """
        # Initialize Math Layer (Skyfield/NASA JPL Ephemeris)
        logger.info("Initializing Math Layer (Skyfield/NASA JPL)...")
        self.engine = EphemerisEngine(data_dir=data_dir)
        
        # Initialize Dasha Engine
        from engine import DashaEngine, NumerologyEngine
        self.dasha_engine = DashaEngine()

        # Initialize Prediction Engine (pre-computes all reasoning for LLM sections)
        self.prediction_engine = PredictionEngine(self.engine, self.dasha_engine)

        # Initialize Numerology Engine
        self.numerology_engine = NumerologyEngine(data_dir=data_dir)
        
        # Initialize Numerology Expert
        from agents import NumerologyExpert
        self.numerology_expert = NumerologyExpert()
        
        # Initialize Knowledge Layer (H-RAG)
        self.use_rag = use_rag
        if use_rag:
            try:
                logger.info("Initializing Knowledge Layer (H-RAG)...")
                self.knowledge_base = get_hrag_retriever()
                kb_stats = self.knowledge_base.get_stats()
                logger.info(
                    f"H-RAG ready: {kb_stats['total_parents']} parents, "
                    f"{kb_stats['total_children']} children"
                )
            except Exception as e:
                logger.warning(f"H-RAG initialization failed: {e}. Proceeding without RAG.")
                self.use_rag = False
                self.knowledge_base = None
        else:
            self.knowledge_base = None
        
        # Initialize LLM
        self.llm = llm
        if llm is None:
            logger.warning("No LLM provided. Synthesis will return fact sheet only.")
        
        logger.info("Orchestrator initialized successfully")
    
    def _generate_fact_sheet(
        self,
        mathematical_data: Dict[str, Any],
        logical_analysis: Dict[str, Any]
    ) -> str:
        """
        Generate a structured fact sheet from mathematical and logical analysis.
        
        Args:
            mathematical_data: Output from EphemerisEngine
            logical_analysis: Output from expert agents
        
        Returns:
            Formatted fact sheet string
        """
        fact_sheet = []
        
        fact_sheet.append("=" * 70)
        fact_sheet.append("ASTROLOGICAL FACT SHEET")
        fact_sheet.append("=" * 70)
        
        # Section 1: Planetary Positions
        fact_sheet.append("\n1. PLANETARY POSITIONS (Sidereal/Lahiri)")
        fact_sheet.append("-" * 70)

        # Ascendant (Lagna) — first and most important entry
        asc = mathematical_data.get('_ascendant')
        if asc:
            nak = asc['nakshatra']
            fact_sheet.append(
                f"   {'Ascendant':12s}: {asc['sign']} {asc['degree']:5.2f}° | "
                f"{nak['nakshatra_name']:20s} | Pada {nak['pada']} | "
                f"Ruler: {nak['ruler']}  ◈ LAGNA"
            )
            fact_sheet.append("-" * 70)

        for planet, data in mathematical_data.items():
            # Skip internal metadata fields
            if planet.startswith('_'):
                continue
                
            nak = data['nakshatra']
            # Get sign name and degree within sign
            longitude = data['longitude']
            sign = self.engine.get_sign_name(longitude)
            degree_in_sign = longitude % 30
            retro = " (RETROGRADE)" if data['retrograde'] else ""
            fact_sheet.append(
                f"   {planet:12s}: {sign} {degree_in_sign:5.2f}° | "
                f"{nak['nakshatra_name']:20s} | Pada {nak['pada']} | "
                f"Ruler: {nak['ruler']}{retro}"
            )
        
        # Section 2: Vedic Aspects
        aspects = logical_analysis.get('aspects', [])
        fact_sheet.append(f"\n2. VEDIC ASPECTS (Parashara System)")
        fact_sheet.append("-" * 70)
        fact_sheet.append(f"   Total Aspects: {len(aspects)}")
        
        for aspect in aspects[:10]:  # Show first 10
            fact_sheet.append(f"   • {aspect}")
        
        if len(aspects) > 10:
            fact_sheet.append(f"   ... and {len(aspects) - 10} more aspects")
        
        # Section 3: Structural Analysis
        structural = logical_analysis.get('structural', {})
        summary = structural.get('summary', {})
        
        fact_sheet.append(f"\n3. STRUCTURAL ANALYSIS (Nadi & State)")
        fact_sheet.append("-" * 70)
        fact_sheet.append(f"   Dominant Element:      {summary.get('dominant_element', 'N/A')}")
        fact_sheet.append(f"   Element Groups (2+):   {summary.get('total_element_groups', 0)}")
        fact_sheet.append(f"   Linked Pairs:          {summary.get('total_linked_pairs', 0)}")
        fact_sheet.append(f"   Retrograde Planets:    {summary.get('total_retrograde', 0)}")
        fact_sheet.append(f"   Gandanta Planets:      {summary.get('total_gandanta', 0)}")
        
        # Element Distribution
        nadi = structural.get('nadi_analysis', {})
        distribution = nadi.get('distribution', {})
        
        if distribution:
            fact_sheet.append(f"\n   Element Distribution:")
            for element, planets in distribution.items():
                if planets:
                    fact_sheet.append(f"     {element:10s}: {', '.join(planets)}")
        
        # Special States
        state_analysis = structural.get('state_analysis', {})
        special_states = state_analysis.get('special_states', [])
        
        if special_states:
            fact_sheet.append(f"\n   Special Planetary States:")
            for state in special_states:
                fact_sheet.append(
                    f"     • {state['planet']} is {state['state']} "
                    f"at {state['longitude']:.2f}° in {state['sign']}"
                )
        
        # Section 4: Key Relationships
        fact_sheet.append(f"\n4. KEY RELATIONSHIPS")
        fact_sheet.append("-" * 70)
        
        # Show linked pairs
        linked_pairs = nadi.get('linked_pairs', [])
        if linked_pairs:
            fact_sheet.append(f"   Elemental Links:")
            for pair in linked_pairs[:5]:  # Show first 5
                fact_sheet.append(
                    f"     • {pair['planet1']} ({pair['sign1']}) ←→ "
                    f"{pair['planet2']} ({pair['sign2']}) [{pair['element']}]"
                )
        
        # Section 5: Vimshottari Dasha System
        fact_sheet.append(f"\n5. VIMSHOTTARI DASHA (120-Year Cycle)")
        fact_sheet.append("-" * 70)
        
        # Calculate Dasha from Moon position
        moon_data = mathematical_data.get('Moon', {})
        if moon_data:
            moon_lon = moon_data.get('longitude', 0)
            birth_date = mathematical_data.get('_birth_datetime')  # Will add this
            
            if birth_date:
                # Birth Balance
                balance = self.dasha_engine.calculate_dasha_balance(moon_lon, birth_date)
                fact_sheet.append(
                    f"   Birth Balance : {balance['ruler']} Mahadasha "
                    f"({balance['balance_str']} remaining)"
                )
                fact_sheet.append(f"   Balance Ends  : {balance['end_date'].strftime('%Y-%m-%d')}")
                
                # Current Operating Period
                from datetime import datetime
                current = self.dasha_engine.get_current_dasha(moon_lon, birth_date, datetime.now())
                fact_sheet.append(
                    f"   Current Period: {current['mahadasha']} Mahadasha / "
                    f"{current['antardasha']} Antardasha"
                )
                fact_sheet.append(f"   Period Ends   : {current['end_date']}")
                
                # Show next 3 Mahadashas
                schedule = self.dasha_engine.generate_mahadasha_schedule(balance, years_to_generate=50)
                fact_sheet.append(f"\n   Upcoming Mahadashas:")
                for md in schedule[:4]:  # Show first 4 periods
                    fact_sheet.append(
                        f"     • {md['lord']:8s} ({md['type']:7s}): "
                        f"{md['start'].strftime('%Y-%m-%d')} → {md['end'].strftime('%Y-%m-%d')}"
                    )
        
        # Section 6: Navamsa (D9) Divisional Chart
        navamsa_data = mathematical_data.get('_navamsa', {})
        if navamsa_data:
            fact_sheet.append(f"\n6. NAVAMSA (D9) - The Fruit of the Chart")
            fact_sheet.append("-" * 70)
            
            # Get divisional strength analysis
            divisional = logical_analysis.get('divisional_strength', {})
            summary = divisional.get('summary', {})
            
            fact_sheet.append(f"   Vargottama Count: {summary.get('vargottama_count', 0)}")
            vargottama_planets = summary.get('vargottama_planets', [])
            if vargottama_planets:
                fact_sheet.append(f"   Vargottama: {', '.join(vargottama_planets)} ⭐ SUPREME STRENGTH")
            fact_sheet.append(f"   Assessment: {summary.get('interpretation', 'N/A')}")
            
            fact_sheet.append(f"\n   D1 (Birth Chart) → D9 (Navamsa):")
            for planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']:
                if planet in navamsa_data:
                    d9 = navamsa_data[planet]
                    varg_mark = " ⭐" if d9['vargottama'] else ""
                    fact_sheet.append(
                        f"     {planet:10s}: {d9['d1_sign']:12s} → {d9['d9_sign']:12s}{varg_mark}"
                    )
            
            # Show strength notes
            strength_notes = divisional.get('strength_notes', [])
            if strength_notes:
                fact_sheet.append(f"\n   Strength Notes:")
                for note in strength_notes[:5]:  # Show first 5
                    fact_sheet.append(f"     • {note}")
        
        # Section 7: Numerology Cross-Verification
        numerology_data = mathematical_data.get('_numerology', {})
        if numerology_data:
            fact_sheet.append(f"\n7. NUMEROLOGY - Cross-Verification Layer")
            fact_sheet.append("-" * 70)
            
            profile = numerology_data['profile']
            tags = numerology_data['tags']
            harmony = numerology_data['harmony']
            
            # Core numbers
            lp = profile['life_path']
            dest = profile['destiny']
            att = profile['attitude']
            
            fact_sheet.append(f"   Life Path Number: {lp['number']} ({lp['meaning']})")
            fact_sheet.append(f"     Ruler: {lp['ruler']}, Archetype: {tags['life_path']['archetype']}")
            
            fact_sheet.append(f"\n   Destiny Number: {dest['number']} ({dest['meaning']})")
            fact_sheet.append(f"     Ruler: {dest['ruler']}, Archetype: {tags['destiny']['archetype']}")
            
            fact_sheet.append(f"\n   Attitude Number: {att['number']} ({att['meaning']})")
            fact_sheet.append(f"     Ruler: {att['ruler']}")
            
            # Synthesis
            syn = tags['synthesis']
            fact_sheet.append(f"\n   Synthesis:")
            fact_sheet.append(f"     Element: {syn['dominant_element']}, Theme: {syn['overall_theme']}")
            
            # Harmony check
            fact_sheet.append(f"\n   Astrology-Numerology Harmony:")
            fact_sheet.append(f"     Score: {harmony['harmony_count']}/3")
            fact_sheet.append(f"     Confidence Multiplier: {harmony['confidence_multiplier']}x")
            fact_sheet.append(f"     Verdict: {harmony['verdict']}")
            
            if harmony['harmony_points']:
                for point in harmony['harmony_points']:
                    fact_sheet.append(f"       ✓ {point}")
        
        fact_sheet.append("\n" + "=" * 70)
        
        return "\n".join(fact_sheet)
    
    def _get_sign_ruler(self, sign_name: str) -> str:
        """
        Get the planetary ruler for a zodiac sign.
        
        Args:
            sign_name: Name of zodiac sign
            
        Returns:
            Ruling planet name
        """
        sign_rulers = {
            "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
            "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
            "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
            "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
        }
        return sign_rulers.get(sign_name, "Unknown")
    
    def _query_knowledge_base(
        self,
        mathematical_data: Dict[str, Any],
        logical_analysis: Dict[str, Any],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Query the H-RAG knowledge base for relevant classical text passages.

        Builds targeted queries from chart features, then uses hierarchical
        retrieval: child vector search → ranked parent context chunks.
        """
        if not self.use_rag or self.knowledge_base is None:
            return []

        structural = logical_analysis.get('structural', {})
        queries: List[str] = []

        # 1. Moon nakshatra — most important for personality
        moon_nak = mathematical_data['Moon']['nakshatra']['nakshatra_name']
        queries.append(f"significance and interpretation of {moon_nak} nakshatra Moon")

        # 2. Retrograde planets
        retro_planets = structural.get('state_analysis', {}).get('retrograde_planets', [])
        if retro_planets:
            retro_names = [p['planet'] for p in retro_planets[:2]]
            queries.append(f"effects of retrograde {' and '.join(retro_names)} planet")

        # 3. Dominant element
        dominant_element = structural.get('summary', {}).get('dominant_element')
        if dominant_element:
            queries.append(f"{dominant_element} element dominance personality Vedic astrology")

        # 4. Key planetary aspects (Mars/Saturn/Jupiter are most significant)
        for aspect in logical_analysis.get('aspects', [])[:4]:
            if any(p in aspect for p in ('Mars', 'Saturn', 'Jupiter')):
                queries.append(f"Vedic astrology interpretation: {aspect}")
                break

        # 5. Dasha lord
        dasha_info = mathematical_data.get('_dasha_balance', {})
        if dasha_info.get('ruler'):
            queries.append(
                f"{dasha_info['ruler']} Mahadasha effects Vimshottari Vedic astrology"
            )

        # Execute hierarchical queries — H-RAG returns parent-level context
        all_results: List[Dict] = []
        seen_parents: set = set()

        for query in queries:
            try:
                hits = self.knowledge_base.search(query, top_k=2)
                for hit in hits:
                    content = hit['content']
                    if content not in seen_parents:
                        seen_parents.add(content)
                        all_results.append({
                            'query': query,
                            'content': content,
                            'metadata': hit.get('metadata', {}),
                            'child_hits': hit.get('child_hits', 1),
                        })
                if len(all_results) >= top_k:
                    break
            except Exception as e:
                logger.warning(f"H-RAG query failed for '{query}': {e}")
                continue

        return all_results[:top_k]
    
    def _create_synthesis_prompt(self) -> ChatPromptTemplate:
        """
        Synthesis prompt — tuned for local Ollama models.

        Ollama models (llama3.2 etc.) work best with:
        - Clear role definition up front
        - Explicit numbered sections
        - Concrete instruction to use provided data
        - Reasonable output length (they can be verbose)
        """
        system_message = (
            "You are an expert Vedic astrologer with deep knowledge of classical texts "
            "including Brihat Parashara Hora Shastra, Nadi astrology, nakshatras, "
            "planetary aspects, and yogas.\n\n"
            "Your task: synthesize the Mathematical Fact Sheet and Classical Text passages "
            "below into a clear, insightful Vedic astrological reading.\n\n"
            "RULES:\n"
            "1. Ground EVERY statement in actual data from the Fact Sheet (planets, "
            "nakshatras, degrees, aspects, dashas).\n"
            "2. Use Classical Text passages to deepen and validate interpretations.\n"
            "3. Apply Nadi rules for personality and character.\n"
            "4. Apply Parashara rules for life events and timing.\n"
            "5. Be specific — avoid generic astrology clichés.\n"
            "6. Keep a balanced tone: acknowledge both strengths and challenges.\n"
            "7. Target 800–1200 words total."
        )

        human_message = (
            "MATHEMATICAL FACT SHEET:\n{fact_sheet}\n\n"
            "CLASSICAL TEXT PASSAGES (H-RAG retrieved):\n{rag_context}\n\n"
            "Write a Vedic astrological reading with these five sections:\n\n"
            "## 1. Core Personality\n"
            "(Moon nakshatra, dominant element, psychological portrait)\n\n"
            "## 2. Strengths & Talents\n"
            "(Beneficial placements, vargottama planets, positive aspects)\n\n"
            "## 3. Challenges & Growth Areas\n"
            "(Retrograde planets, difficult aspects, areas needing attention)\n\n"
            "## 4. Key Life Themes\n"
            "(Major yogas, planetary pairs, life direction)\n\n"
            "## 5. Timing & Current Period\n"
            "(Current Mahadasha/Antardasha, what it activates, near-term outlook)\n\n"
            "Trace every point back to specific chart data."
        )

        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", human_message),
        ])

    # ─── Domain-specific H-RAG queries ───────────────────────────────────────

    def _query_knowledge_per_domain(
        self,
        prediction_brief: Dict[str, Any],
        mathematical_data: Dict[str, Any],
        logical_analysis: Dict[str, Any],
    ) -> Dict[str, str]:
        """
        Build targeted H-RAG context strings per domain.
        Returns {domain_key: context_text} for use in section prompts.
        """
        if not self.use_rag or self.knowledge_base is None:
            return {}

        brief = prediction_brief
        lagna = brief.get("lagna", "")
        lagna_lord = brief.get("lagna_lord", "")
        ph = brief.get("planet_houses", {})
        ps = brief.get("planet_strengths", {})

        def _moon_nak() -> str:
            return mathematical_data.get("Moon", {}).get("nakshatra", {}).get("nakshatra_name", "")

        def _query(q: str) -> str:
            try:
                hits = self.knowledge_base.search(q, top_k=2)
                parts = []
                for h in hits:
                    src = h.get("metadata", {}).get("source", "H-RAG")
                    parts.append(f"[{src}] {h['content']}")
                return "\n\n".join(parts)
            except Exception:
                return ""

        results: Dict[str, str] = {}

        results["personality"] = _query(
            f"{lagna} ascendant {lagna_lord} lord personality Vedic astrology"
        )
        results["moon"] = _query(
            f"{_moon_nak()} nakshatra Moon mind emotions Vedic astrology"
        )
        results["sun"] = _query(
            f"Sun in house {ph.get('Sun', '?')} identity authority Vedic astrology"
        )
        results["career"] = _query(
            f"10th house career {brief['domains']['career']['house_lord']} lord Vedic astrology profession"
        )
        results["wealth"] = _query(
            f"2nd 11th house wealth income gains Vedic astrology Jupiter Venus"
        )
        results["relationships"] = _query(
            f"7th house Venus marriage partner love {lagna} lagna Vedic astrology"
        )
        results["health"] = _query(
            f"lagna lord health vitality {lagna} Vedic astrology 6th house"
        )
        results["spirituality"] = _query(
            f"Ketu 9th 12th house spiritual liberation dharma Vedic astrology"
        )
        results["dasha"] = _query(
            f"{brief['life_phase']['mahadasha']} mahadasha effects Vimshottari period Vedic"
        )

        # Retrograde planets context
        retro = [p for p, d in ps.items() if d.get("retrograde")]
        if retro:
            results["retrograde"] = _query(
                f"retrograde {retro[0]} planet karmic effects Vedic astrology"
            )

        return results

    # ─── Section-by-section LLM synthesis ────────────────────────────────────

    def _generate_section(
        self,
        section_label: str,
        instructions: str,
        facts: str,
        hrag_context: str = "",
    ) -> str:
        """
        Call the LLM for one focused report section.
        Supplies pre-computed facts so the LLM only writes prose.
        """
        if self.llm is None:
            return ""

        system = (
            "You are an experienced Vedic astrology report writer. "
            "Write clearly, specifically, and practically. "
            "Use ONLY the chart facts provided — never invent placements or statistics. "
            "Do not use vague filler phrases. Every sentence must reference a specific chart indicator."
        )
        human = (
            f"## Section: {section_label}\n\n"
            f"### Chart Facts (use these exactly)\n{facts}\n\n"
            + (f"### Classical / Knowledge-Base Context\n{hrag_context}\n\n" if hrag_context else "")
            + f"### Instructions\n{instructions}"
        )

        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", system),
                ("human", human),
            ])
            chain = prompt | self.llm | StrOutputParser()
            return chain.invoke({}).strip()
        except Exception as e:
            logger.warning(f"Section '{section_label}' LLM call failed: {e}")
            return f"[Section generation failed: {e}]"

    def _generate_sections(
        self,
        prediction_brief: Dict[str, Any],
        domain_rag: Dict[str, str],
        birth_data: "BirthData",
        mathematical_data: Dict[str, Any],
    ) -> Dict[str, str]:
        """
        Generate all prose sections of the 14-section report.
        Returns {section_key: prose_text}.
        """
        b = prediction_brief
        lagna = b["lagna"]
        ll = b["lagna_lord"]
        lp = b["life_phase"]
        dt = b["dasha_timeline"]
        current = dt.get("current", {})
        md = current.get("mahadasha", "")
        ad = current.get("antardasha", "")

        def _brief_planet(planet: str) -> str:
            ps = b["planet_strengths"].get(planet, {})
            ph = b["planet_houses"].get(planet, "?")
            return (
                f"{planet}: {ps.get('sign', '?')} {ps.get('degree', 0):.1f}°, "
                f"House {ph}, {ps.get('overall', 'Neutral')}"
                + (f" ({', '.join(ps.get('status_list', []))})" if ps.get("status_list") else "")
            )

        def _domain_facts(domain: str) -> str:
            d = b["domains"].get(domain, {})
            lines = []
            for item in d.get("supporting", []):
                mark = "✓" if item.get("supports") else "✗"
                lines.append(f"{mark} {item['point']}")
            lines.append(f"Confidence: {d.get('confidence', '?')}")
            lines.append(f"Dasha Relevance: {d.get('dasha_relevance', '?')}")
            return "\n".join(lines)

        sections: Dict[str, str] = {}
        logger.info("Generating report sections with LLM...")

        # ── Executive Summary (2.2 + 2.3) ────────────────────────────────────
        top_themes_text = "\n".join(
            f"- {t['theme']} ({t['strength']}): {t['evidence'][0]}"
            for t in b["top_themes"]
        )
        facts_exec = (
            f"Lagna: {lagna} | Lagna Lord: {ll} ({b['planet_strengths'].get(ll, {}).get('overall', '?')})\n"
            f"Moon: {_brief_planet('Moon')}\n"
            f"Sun: {_brief_planet('Sun')}\n"
            f"Current Period: {md} Mahadasha / {ad} Antardasha (ends {current.get('end_date', '?')})\n"
            f"Phase nature: {lp['phase_type']}\n"
            f"Top themes:\n{top_themes_text}\n"
            f"Yogas: {', '.join(y['name'] for y in b['yogas'][:4]) or 'None detected'}"
        )
        sections["executive_summary"] = self._generate_section(
            "2.2–2.3 Executive Summary",
            (
                "Write a 150–220 word paragraph (section 2.2) summarising the native's personality, "
                "life direction, karmic themes, and near-term outlook. Be specific, not generic. "
                "Then write a Current Phase Verdict (section 2.3) as 3–5 bullet points covering: "
                "current dasha nature, most activated life areas, and best strategy."
            ),
            facts_exec,
            domain_rag.get("personality", "") + "\n\n" + domain_rag.get("moon", ""),
        )
        logger.info("  ✓ Executive summary")

        # ── Chart Foundation 4.1 Lagna ────────────────────────────────────────
        lagna_nak = b.get("lagna_nakshatra", {})
        facts_lagna = (
            f"Ascendant: {lagna} {b['lagna_degree']:.2f}° "
            f"({lagna_nak.get('nakshatra_name', '?')} Pada {lagna_nak.get('pada', '?')})\n"
            f"Lagna Lord: {ll} in House {b['planet_houses'].get(ll, '?')} "
            f"({b['planet_strengths'].get(ll, {}).get('sign', '?')}), "
            f"{b['planet_strengths'].get(ll, {}).get('overall', '?')}\n"
            f"Aspects on Lagna lord: see aspects list"
        )
        sections["lagna_personality"] = self._generate_section(
            "4.1 Lagna-Based Personality",
            (
                "Write 120–180 words explaining how this Ascendant sign, its nakshatra, and the "
                "condition of the Lagna lord shape the native's temperament, physical energy, "
                "decision-making style, social approach, and life orientation. Be specific to "
                "this exact sign — avoid generic descriptions."
            ),
            facts_lagna,
            domain_rag.get("personality", ""),
        )
        logger.info("  ✓ Lagna personality")

        # ── Chart Foundation 4.2 Moon ─────────────────────────────────────────
        moon_ps = b["planet_strengths"].get("Moon", {})
        moon_nak = mathematical_data.get("Moon", {}).get("nakshatra", {})
        facts_moon = (
            f"Moon: {moon_ps.get('sign', '?')} {moon_ps.get('degree', 0):.1f}°, "
            f"House {b['planet_houses'].get('Moon', '?')}\n"
            f"Moon Nakshatra: {moon_nak.get('nakshatra_name', '?')} Pada {moon_nak.get('pada', '?')}, "
            f"Ruler {moon_nak.get('ruler', '?')}\n"
            f"Moon Strength: {moon_ps.get('overall', 'Neutral')} "
            f"({', '.join(moon_ps.get('status_list', ['—']))})"
        )
        sections["moon_mind"] = self._generate_section(
            "4.2 Moon-Based Mind and Emotional Pattern",
            (
                "Write 120–150 words on this Moon's emotional nature, mental pattern, "
                "need for comfort/security, stress response, and relationship with intuition. "
                "Reference the specific Moon nakshatra and its meaning."
            ),
            facts_moon,
            domain_rag.get("moon", ""),
        )
        logger.info("  ✓ Moon mind")

        # ── Chart Foundation 4.3 Sun ──────────────────────────────────────────
        sun_ps = b["planet_strengths"].get("Sun", {})
        sun_nak = mathematical_data.get("Sun", {}).get("nakshatra", {})
        facts_sun = (
            f"Sun: {sun_ps.get('sign', '?')} {sun_ps.get('degree', 0):.1f}°, "
            f"House {b['planet_houses'].get('Sun', '?')}\n"
            f"Sun Nakshatra: {sun_nak.get('nakshatra_name', '?')} Pada {sun_nak.get('pada', '?')}\n"
            f"Sun Strength: {sun_ps.get('overall', 'Neutral')} "
            f"({', '.join(sun_ps.get('status_list', ['—']))})"
        )
        sections["sun_identity"] = self._generate_section(
            "4.3 Sun-Based Identity and Authority",
            (
                "Write 80–120 words on this Sun placement's effect on confidence, leadership "
                "style, relationship with authority/father, public identity, and ego development."
            ),
            facts_sun,
            domain_rag.get("sun", ""),
        )
        logger.info("  ✓ Sun identity")

        # ── Strengths (5.2 Talents) ───────────────────────────────────────────
        strong_planets = [
            p for p, d in b["planet_strengths"].items()
            if d.get("overall") == "Strong"
        ]
        vargottama = [p for p, d in b["planet_strengths"].items() if d.get("vargottama")]
        yogas_text = "\n".join(
            f"- {y['name']}: {y['description']}" for y in b["yogas"]
        ) or "None detected"
        facts_strengths = (
            f"Strong planets: {', '.join(strong_planets) or 'None'}\n"
            f"Vargottama (D1=D9): {', '.join(vargottama) or 'None'}\n"
            f"Yogas:\n{yogas_text}\n\n"
            + "\n".join(_brief_planet(p) for p in strong_planets[:4])
        )
        sections["strengths"] = self._generate_section(
            "5.2 Natural Talents",
            (
                "Write 2–4 talent cards in this format:\n"
                "### Talent N: [Name]\n"
                "- **Prediction:** [clear statement]\n"
                "- **Chart Evidence:** [planet/sign/house/yoga]\n"
                "- **How it manifests:** [real-world behaviour]\n"
                "- **Best use:** [career/life application]\n"
                "- **Confidence:** High / Medium / Low\n\n"
                "Base each talent on a strong planet, yoga, or vargottama listed in facts."
            ),
            facts_strengths,
            "",
        )
        logger.info("  ✓ Strengths")

        # ── Challenges (6.2 Shadow Pattern) ──────────────────────────────────
        weak_planets = [
            p for p, d in b["planet_strengths"].items()
            if d.get("overall") == "Weakened"
        ]
        retro_planets = [
            p for p, d in b["planet_strengths"].items()
            if d.get("retrograde")
        ]
        facts_challenges = (
            f"Weakened planets: {', '.join(weak_planets) or 'None'}\n"
            f"Retrograde planets: {', '.join(retro_planets) or 'None'}\n"
            + "\n".join(_brief_planet(p) for p in (weak_planets + retro_planets)[:4])
        )
        sections["challenges"] = self._generate_section(
            "6.2 Psychological Shadow Pattern",
            (
                "Write 100–150 words about this native's likely behavioural patterns to watch: "
                "emotional blocks, repeated friction, delay patterns, or overthinking. "
                "Base it on weak/retrograde planets only — do not fabricate challenges."
            ),
            facts_challenges,
            domain_rag.get("retrograde", ""),
        )
        logger.info("  ✓ Challenges")

        # ── Career (7.1) ──────────────────────────────────────────────────────
        sections["career"] = self._generate_section(
            "7.1 Career and Professional Growth",
            (
                "Write a career prediction covering: main career direction, suitable fields, "
                "leadership style, timing (from dasha), and a 2–3 sentence final verdict. "
                "Reference the 10th house, 10th lord, and Sun placement specifically."
            ),
            _domain_facts("career") + "\n\n" + "\n".join(
                _brief_planet(p) for p in ["Sun", "Saturn", "Mercury", "Mars"]
            ),
            domain_rag.get("career", ""),
        )
        logger.info("  ✓ Career")

        # ── Wealth (7.3) ──────────────────────────────────────────────────────
        sections["wealth"] = self._generate_section(
            "7.3 Wealth, Finance, and Assets",
            (
                "Write a wealth prediction covering: earning style, saving tendency, "
                "risk appetite, best wealth-building periods, and caution periods. "
                "Reference 2nd house, 11th house, Jupiter and Venus specifically."
            ),
            _domain_facts("wealth") + "\n\n" + "\n".join(
                _brief_planet(p) for p in ["Jupiter", "Venus", "Mercury"]
            ),
            domain_rag.get("wealth", ""),
        )
        logger.info("  ✓ Wealth")

        # ── Relationships (7.4) ───────────────────────────────────────────────
        sections["relationships"] = self._generate_section(
            "7.4 Relationships, Marriage, and Partnership",
            (
                "Write a relationship section covering: romantic personality, dating patterns, "
                "marriage potential (type and timing), spouse indications, and relationship "
                "challenges. Use the 7th house, 5th house, Venus, Jupiter, and Moon. "
                "Close with a 150–200 word final verdict on love and marriage. "
                "Do not predict divorce or widowhood — phrase any difficulties as "
                "'relationship stress requiring conscious work'."
            ),
            _domain_facts("relationships") + "\n\n" + "\n".join(
                _brief_planet(p) for p in ["Venus", "Jupiter", "Moon", "Mars", "Rahu"]
            ),
            domain_rag.get("relationships", ""),
        )
        logger.info("  ✓ Relationships")

        # ── Family + Health + Spirituality + Travel (7.5–7.8) ────────────────
        sections["family_health_spirit"] = self._generate_section(
            "7.5–7.8 Family, Health, Spirituality, Foreign Travel",
            (
                "Write four short sections (100–120 words each):\n"
                "### 7.5 Family and Home\n"
                "### 7.6 Health and Energy (no disease diagnosis — only vitality patterns)\n"
                "### 7.7 Spirituality and Inner Development\n"
                "### 7.8 Foreign Travel and Relocation\n"
                "Each section must reference its specific house and planets from the facts."
            ),
            "\n\n".join([
                "FAMILY:\n" + _domain_facts("family"),
                "HEALTH:\n" + _domain_facts("health"),
                "SPIRITUALITY:\n" + _domain_facts("spirituality"),
                "TRAVEL:\n" + _domain_facts("travel"),
            ]),
            domain_rag.get("spirituality", ""),
        )
        logger.info("  ✓ Family/Health/Spirituality/Travel")

        # ── Timing — Dasha Interpretation (8.2) ──────────────────────────────
        ad_schedule_text = ""
        for ad_entry in dt.get("antardashas", [])[:9]:
            sub = ad_entry.get("sub_lord", "?")
            s = ad_entry["start"].strftime("%Y-%m") if hasattr(ad_entry.get("start"), "strftime") else str(ad_entry.get("start", "?"))
            e = ad_entry["end"].strftime("%Y-%m") if hasattr(ad_entry.get("end"), "strftime") else str(ad_entry.get("end", "?"))
            ad_schedule_text += f"  {sub}: {s} → {e}\n"

        md_placement = _brief_planet(md) if md and md in b["planet_strengths"] else f"{md} (unknown placement)"
        facts_timing = (
            f"Current Mahadasha: {md} (ends approx {current.get('end_date', '?')})\n"
            f"Current Antardasha: {ad}\n"
            f"MD nature: {lp['md_nature']}\n"
            f"AD nature: {lp['ad_nature']}\n"
            f"MD planet placement: {md_placement}\n"
            f"Antardasha schedule:\n{ad_schedule_text}\n"
            f"Activated life areas: {', '.join(lp['activated_areas'])}"
        )
        sections["dasha_interpretation"] = self._generate_section(
            "8.2 Current Period Interpretation",
            (
                "Write a dasha interpretation covering:\n"
                "- What this Mahadasha activates for this native\n"
                "- Positive possibilities and challenges of this period\n"
                "- How the Antardasha modifies the Mahadasha tone\n"
                "- Practical advice for making the best use of this period\n"
                "Aim for 150–200 words total."
            ),
            facts_timing,
            domain_rag.get("dasha", ""),
        )
        logger.info("  ✓ Dasha interpretation")

        # ── Final Verdict (13) ────────────────────────────────────────────────
        theme_summary = "\n".join(
            f"- {t['theme']} ({t['strength']})" for t in b["top_themes"]
        )
        facts_verdict = (
            f"Lagna: {lagna} | Moon sign: {b['planet_strengths'].get('Moon', {}).get('sign', '?')}\n"
            f"Current period: {md}/{ad}\n"
            f"Top life themes:\n{theme_summary}\n"
            f"Strong planets: {', '.join(strong_planets) or 'None'}\n"
            f"Weak/challenged: {', '.join(weak_planets) or 'None'}"
        )
        sections["final_verdict"] = self._generate_section(
            "13 Final Verdict",
            (
                "Write a direct, grounded final reading in 250–350 words covering: "
                "the native's main life direction; what they should build; what they should "
                "consciously avoid; what period they are entering; and the most important "
                "practical advice. Do not be vague. Reference specific chart factors. "
                "End with one empowering sentence."
            ),
            facts_verdict,
            "",
        )
        logger.info("  ✓ Final verdict")

        logger.info(f"All {len(sections)} sections generated")
        return sections

    def analyze_chart(self, birth_data: BirthData) -> AstrologicalReading:
        """
        Perform complete astrological analysis using all layers.
        
        This is the main entry point that orchestrates:
        1. Mathematical calculations (EphemerisEngine)
        2. Rule-based analysis (Expert Agents)
        3. Knowledge retrieval (RAG)
        4. LLM synthesis
        
        Args:
            birth_data: Birth date, time, and location
        
        Returns:
            Complete astrological reading
        """
        logger.info("Starting chart analysis...")
        
        # STEP 1: Mathematical Layer
        logger.info("Step 1: Calculating planetary positions...")
        mathematical_data = self.engine.calculate_chart(
            birth_data.datetime,
            birth_data.latitude,
            birth_data.longitude
        )
        # Store birth datetime for Dasha calculations
        mathematical_data['_birth_datetime'] = birth_data.datetime
        logger.info(f"✓ Calculated positions for {len(mathematical_data) - 1} planets")
        
        # Calculate Ascendant (Lagna)
        logger.info("Step 1b: Calculating Ascendant (Lagna)...")
        asc_data = self.engine.calculate_ascendant(
            birth_data.datetime,
            birth_data.latitude,
            birth_data.longitude
        )
        mathematical_data['_ascendant'] = asc_data
        logger.info(f"✓ Ascendant (Lagna): {asc_data['sign']} {asc_data['degree']:.2f}°")

        # Calculate Navamsa (D9) for all planets
        logger.info("Step 1c: Calculating Navamsa (D9) divisional chart...")
        navamsa_data = {}
        for planet_name, planet_data in mathematical_data.items():
            if not planet_name.startswith('_'):
                longitude = planet_data["longitude"]
                navamsa_data[planet_name] = self.engine.calculate_navamsa(longitude)
        mathematical_data['_navamsa'] = navamsa_data
        
        vargottama_count = sum(1 for d9 in navamsa_data.values() if d9['vargottama'])
        logger.info(f"✓ D9 calculated: {vargottama_count} Vargottama planets")
        
        # Calculate Numerology if name provided
        if birth_data.name:
            logger.info("Step 1c: Calculating numerology profile...")
            numerology_profile = self.numerology_engine.analyze_full_profile(
                birth_data.datetime,
                birth_data.name
            )
            numerology_tags = self.numerology_expert.generate_profile_tags(numerology_profile)
            
            # Check harmony with astrology
            sun_sign = self.engine.get_sign_name(mathematical_data['Sun']['longitude'])
            moon_sign = self.engine.get_sign_name(mathematical_data['Moon']['longitude'])
            
            astro_indicators = {
                "sun_ruler": self._get_sign_ruler(sun_sign),
                "moon_ruler": self._get_sign_ruler(moon_sign),
                "dominant_element": navamsa_data['Sun']['element']  # Use D1 element from Sun
            }
            
            harmony = self.numerology_expert.check_harmony_with_astrology(
                numerology_tags, 
                astro_indicators
            )
            
            mathematical_data['_numerology'] = {
                "profile": numerology_profile,
                "tags": numerology_tags,
                "harmony": harmony
            }
            logger.info(f"✓ Numerology: Life Path {numerology_profile['life_path']['number']}, "
                       f"Harmony {harmony['confidence_multiplier']}x")
        
        # STEP 2: Logic Layer (run expert agents in parallel)
        logger.info("Step 2: Running expert agents...")
        
        # Filter out non-planet data for expert agents
        planet_data = {k: v for k, v in mathematical_data.items() if not k.startswith('_')}
        
        # Parashara Expert (y₁) - Aspects
        aspects = calculate_aspects(planet_data)
        logger.info(f"✓ Parashara: {len(aspects)} aspects calculated")
        
        # Parashara Expert - Divisional Strength (D9 analysis)
        from agents import analyze_divisional_strength
        divisional_strength = analyze_divisional_strength(planet_data, navamsa_data)
        logger.info(f"✓ Parashara D9: {divisional_strength['summary']['interpretation']}")
        
        # Nadi & State Experts (y₂, y₃) - Structural analysis
        structural = perform_structural_analysis(planet_data)
        logger.info(f"✓ Nadi: {structural['summary']['total_linked_pairs']} pairs linked")
        logger.info(f"✓ State: {structural['summary']['total_special']} special states found")

        # Pre-calculate dasha balance and store for H-RAG query use
        moon_lon = mathematical_data['Moon']['longitude']
        dasha_balance = self.dasha_engine.calculate_dasha_balance(moon_lon, birth_data.datetime)
        mathematical_data['_dasha_balance'] = dasha_balance
        
        # Combine logical analysis
        logical_analysis = {
            'aspects': aspects,
            'divisional_strength': divisional_strength,
            'structural': structural,
            'relationships': get_planet_relationships(planet_data)
        }

        # Generate Fact Sheet (used in Section 14 Appendix)
        fact_sheet = self._generate_fact_sheet(mathematical_data, logical_analysis)

        # STEP 2b: Prediction Engine — pre-compute all Vedic reasoning
        logger.info("Step 2b: Computing prediction brief (houses, lords, yogas, domains)...")
        prediction_brief = self.prediction_engine.compute_brief(
            mathematical_data, logical_analysis, birth_data.datetime
        )
        yogas_found = len(prediction_brief.get("yogas", []))
        logger.info(f"✓ Prediction brief: {yogas_found} yogas, "
                    f"{len(prediction_brief.get('domains', {}))} domains analysed")

        # STEP 3: Knowledge Layer — domain-specific H-RAG queries
        logger.info("Step 3: Querying H-RAG per domain...")
        rag_results = self._query_knowledge_base(mathematical_data, logical_analysis)
        domain_rag = self._query_knowledge_per_domain(
            prediction_brief, mathematical_data, logical_analysis
        )
        logger.info(f"✓ H-RAG: {len(rag_results)} general + {len(domain_rag)} domain contexts")

        # Format general RAG context for legacy fact sheet
        rag_context_text = "\n\n".join([
            f"[Source: {r['metadata'].get('source', 'Unknown')} | "
            f"Hits: {r.get('child_hits', '?')}]\n{r['content']}"
            for r in rag_results
        ]) if rag_results else "No classical text context retrieved."

        # STEP 4: Section-by-section LLM synthesis
        report_sections: Dict[str, str] = {}
        synthesis = ""

        if self.llm is not None:
            logger.info("Step 4: Generating 14-section report with LLM...")
            report_sections = self._generate_sections(
                prediction_brief, domain_rag, birth_data, mathematical_data
            )
            # Build legacy synthesis string for console output
            synthesis = "\n\n---\n\n".join(
                f"### {k.replace('_', ' ').title()}\n{v}"
                for k, v in report_sections.items()
                if v
            )
        else:
            logger.info("Step 4: No LLM — returning structured data only")
            synthesis = "[No LLM configured — structured data available in prediction_brief]"

        # Create final reading
        reading = AstrologicalReading(
            birth_data=birth_data,
            mathematical_data=mathematical_data,
            logical_analysis=logical_analysis,
            rag_context=rag_results,
            synthesis=synthesis,
            fact_sheet=fact_sheet,
            prediction_brief=prediction_brief,
            report_sections=report_sections,
        )

        logger.info("Chart analysis complete!")
        return reading
    
    def analyze_chart_simple(
        self,
        dt: dt_module,
        lat: float,
        lon: float,
        location_name: str = None,
        name: str = None
    ) -> AstrologicalReading:
        """
        Simplified interface for chart analysis.
        
        Args:
            dt: Birth datetime (UTC)
            lat: Latitude
            lon: Longitude
            location_name: Optional location name
            name: Optional person's name
        
        Returns:
            Complete astrological reading
        """
        birth_data = BirthData(
            datetime=dt,
            latitude=lat,
            longitude=lon,
            location_name=location_name,
            name=name
        )
        
        return self.analyze_chart(birth_data)
