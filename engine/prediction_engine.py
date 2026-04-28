"""
Prediction Engine — Pre-computes all reasoning / evidence chains before LLM synthesis.

Design principle:
  The LLM is a PROSE WRITER, not a reasoner.
  All Vedic logic happens here in Python — house assignments, functional lordships,
  yoga detection, domain evidence chains, confidence scoring, dasha analysis.
  The LLM receives structured facts and writes natural language.

Architecture:
  PredictionEngine.compute_brief(mathematical_data, logical_analysis, birth_datetime)
    → full PredictionBrief dict consumed by orchestrator section prompts
"""

from datetime import datetime
from typing import Dict, List, Any, Optional

# ─── Zodiac constants ─────────────────────────────────────────────────────────

SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

SIGN_RULERS: Dict[str, str] = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
    "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
    "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}

PLANET_EXALTATIONS: Dict[str, str] = {
    "Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn",
    "Mercury": "Virgo", "Jupiter": "Cancer", "Venus": "Pisces",
    "Saturn": "Libra", "Rahu": "Gemini", "Ketu": "Sagittarius",
}

PLANET_DEBILITATIONS: Dict[str, str] = {
    "Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer",
    "Mercury": "Pisces", "Jupiter": "Capricorn", "Venus": "Virgo",
    "Saturn": "Aries", "Rahu": "Sagittarius", "Ketu": "Gemini",
}

PLANET_OWN_SIGNS: Dict[str, List[str]] = {
    "Sun": ["Leo"], "Moon": ["Cancer"], "Mars": ["Aries", "Scorpio"],
    "Mercury": ["Gemini", "Virgo"], "Jupiter": ["Sagittarius", "Pisces"],
    "Venus": ["Taurus", "Libra"], "Saturn": ["Capricorn", "Aquarius"],
    "Rahu": [], "Ketu": [],
}

# Natural benefics / malefics (independent of lagna)
NATURAL_BENEFICS = {"Jupiter", "Venus", "Moon", "Mercury"}  # Mercury mixed
NATURAL_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}

HOUSE_MEANINGS: Dict[int, str] = {
    1: "self, body, personality, vitality",
    2: "wealth, family, speech, food",
    3: "courage, siblings, short travel, communication",
    4: "mother, home, emotional security, property",
    5: "creativity, children, intelligence, romance",
    6: "enemies, debts, disease, service",
    7: "marriage, partnerships, public relations",
    8: "longevity, transformation, inheritance, research",
    9: "dharma, father, luck, higher philosophy",
    10: "career, status, authority, public reputation",
    11: "gains, income, ambitions, social network",
    12: "losses, foreign lands, liberation, seclusion",
}

PLANET_NATURE: Dict[str, str] = {
    "Sun": "authority, confidence, vitality, leadership, father",
    "Moon": "mind, emotions, mother, comfort, intuition, memory",
    "Mars": "energy, courage, drive, conflict, action, property",
    "Mercury": "intellect, communication, commerce, analysis, skill",
    "Jupiter": "wisdom, expansion, dharma, children, guru, abundance",
    "Venus": "relationships, beauty, creativity, wealth, pleasure",
    "Saturn": "discipline, karma, delay, hard work, service, longevity",
    "Rahu": "ambition, foreign, technology, illusion, karmic desire",
    "Ketu": "spirituality, detachment, past karma, research, liberation",
}

PLANET_PHASE_TYPE: Dict[str, str] = {
    "Jupiter": "expansion and growth",
    "Venus": "prosperity and relationships",
    "Mercury": "intellectual development and communication",
    "Moon": "emotional sensitivity and family focus",
    "Sun": "authority building and confidence",
    "Mars": "action, initiative and effort",
    "Saturn": "karmic consolidation and discipline",
    "Rahu": "ambition, disruption and unconventional experiences",
    "Ketu": "inner work, detachment and spiritual insight",
}

DOMAIN_PLANETS: Dict[str, List[str]] = {
    "career":        ["Sun", "Saturn", "Mercury", "Mars", "Jupiter"],
    "wealth":        ["Jupiter", "Venus", "Mercury", "Moon"],
    "relationships": ["Venus", "Jupiter", "Moon", "Mars"],
    "health":        ["Sun", "Mars", "Saturn", "Moon"],
    "spirituality":  ["Jupiter", "Ketu", "Saturn", "Moon"],
    "education":     ["Mercury", "Jupiter", "Moon"],
    "family":        ["Moon", "Venus", "Mars", "Jupiter"],
    "travel":        ["Rahu", "Jupiter", "Saturn", "Moon"],
}

PLANET_ACTIVATED_AREAS: Dict[str, List[str]] = {
    "Sun":     ["career", "authority", "father", "health"],
    "Moon":    ["mind", "family", "mother", "emotions", "home"],
    "Mars":    ["energy", "property", "siblings", "ambition", "conflict"],
    "Mercury": ["intellect", "business", "communication", "education"],
    "Jupiter": ["wisdom", "wealth", "children", "religion", "expansion"],
    "Venus":   ["relationships", "marriage", "creativity", "wealth"],
    "Saturn":  ["career", "discipline", "karma", "delays", "service"],
    "Rahu":    ["ambition", "foreign", "technology", "unconventional"],
    "Ketu":    ["spirituality", "past karma", "detachment", "research"],
}


# ─── Helper functions ─────────────────────────────────────────────────────────

def _confidence_from_count(supporting: int, total: int) -> str:
    if total == 0:
        return "Low"
    ratio = supporting / total
    if ratio >= 0.7:
        return "High"
    if ratio >= 0.4:
        return "Medium"
    return "Low"


def _infer_activated_areas(md: str, ad: str) -> List[str]:
    areas = set(PLANET_ACTIVATED_AREAS.get(md, []) + PLANET_ACTIVATED_AREAS.get(ad, []))
    return list(areas)[:5]


def _dasha_timing_for_domain(domain: str, dasha_timeline: dict) -> str:
    current = dasha_timeline.get("current", {})
    md = current.get("mahadasha", "")
    ad = current.get("antardasha", "")
    md_end = current.get("end_date", "")
    relevant = DOMAIN_PLANETS.get(domain, [])
    if md in relevant or ad in relevant:
        return f"Directly activated — {md}/{ad} until {md_end}"
    return f"Not primary focus — current {md}/{ad} period"


# ─── Main class ───────────────────────────────────────────────────────────────

class PredictionEngine:
    """
    Pre-computes all Vedic logic and assembles structured evidence briefs.
    Called by the orchestrator after the math + logic layers are done.
    The output (PredictionBrief) feeds directly into section-specific LLM prompts.
    """

    def __init__(self, ephemeris_engine, dasha_engine):
        self.engine = ephemeris_engine
        self.dasha_engine = dasha_engine

    # ─── Public API ──────────────────────────────────────────────────────────

    def compute_brief(
        self,
        mathematical_data: Dict[str, Any],
        logical_analysis: Dict[str, Any],
        birth_datetime: datetime,
    ) -> Dict[str, Any]:
        """
        Main entry point.  Runs once per chart, takes ~50 ms.
        Returns a fully structured PredictionBrief dict used by all 14 sections.
        """
        asc_data = mathematical_data.get("_ascendant", {})
        lagna_sign = asc_data.get("sign", "Aries")
        lagna_idx = SIGN_NAMES.index(lagna_sign) if lagna_sign in SIGN_NAMES else 0
        lagna_lord = SIGN_RULERS[lagna_sign]

        houses = self._compute_houses(lagna_idx)
        planet_houses = self._compute_planet_houses(mathematical_data, lagna_idx)
        lordships = self._compute_lordships(lagna_idx)
        planet_strengths = self._compute_planet_strengths(mathematical_data)
        yogas = self._detect_yogas(mathematical_data, planet_houses, lordships)
        dasha_timeline = self._compute_dasha_timeline(mathematical_data, birth_datetime)
        domains = self._compute_domain_briefs(
            mathematical_data, planet_houses, lordships, planet_strengths, dasha_timeline
        )
        life_phase = self._compute_life_phase(dasha_timeline)
        top_themes = self._compute_top_themes(domains, yogas, dasha_timeline)

        return {
            "lagna": lagna_sign,
            "lagna_idx": lagna_idx,
            "lagna_lord": lagna_lord,
            "lagna_nakshatra": asc_data.get("nakshatra", {}),
            "lagna_degree": round(asc_data.get("degree", 0.0), 2),
            "houses": houses,
            "planet_houses": planet_houses,
            "lordships": lordships,
            "planet_strengths": planet_strengths,
            "yogas": yogas,
            "domains": domains,
            "dasha_timeline": dasha_timeline,
            "life_phase": life_phase,
            "top_themes": top_themes,
        }

    # ─── House system ─────────────────────────────────────────────────────────

    def _compute_houses(self, lagna_idx: int) -> Dict[int, str]:
        """Returns {house_number: sign_name} for all 12 houses."""
        return {h: SIGN_NAMES[(lagna_idx + h - 1) % 12] for h in range(1, 13)}

    def _compute_planet_houses(self, mathematical_data: dict, lagna_idx: int) -> Dict[str, int]:
        """Returns {planet_name: house_number} for all planets."""
        result: Dict[str, int] = {}
        for planet, data in mathematical_data.items():
            if planet.startswith("_"):
                continue
            sign_idx = int(data["longitude"] / 30) % 12
            house = ((sign_idx - lagna_idx) % 12) + 1
            result[planet] = house
        result["Ascendant"] = 1
        return result

    def _compute_lordships(self, lagna_idx: int) -> Dict[str, List[int]]:
        """Returns {planet: [house numbers it rules]} for this lagna."""
        lordships: Dict[str, List[int]] = {}
        for h in range(1, 13):
            sign = SIGN_NAMES[(lagna_idx + h - 1) % 12]
            lord = SIGN_RULERS[sign]
            lordships.setdefault(lord, []).append(h)
        return lordships

    # ─── Planet strength ──────────────────────────────────────────────────────

    def _compute_planet_strengths(self, mathematical_data: dict) -> Dict[str, Dict]:
        navamsa_data = mathematical_data.get("_navamsa", {})
        strengths: Dict[str, Dict] = {}

        for planet, data in mathematical_data.items():
            if planet.startswith("_"):
                continue
            lon = data.get("longitude", 0)
            sign = self.engine.get_sign_name(lon)
            deg_in_sign = lon % 30
            status_list: List[str] = []

            if PLANET_EXALTATIONS.get(planet) == sign:
                status_list.append("Exalted")
            if PLANET_DEBILITATIONS.get(planet) == sign:
                status_list.append("Debilitated")
            if sign in PLANET_OWN_SIGNS.get(planet, []):
                status_list.append("Own Sign")
            d9 = navamsa_data.get(planet, {})
            if d9.get("vargottama"):
                status_list.append("Vargottama")
            if data.get("retrograde"):
                status_list.append("Retrograde")
            if deg_in_sign < 1.0 or deg_in_sign > 29.0:
                status_list.append("Gandanta")

            if any(s in ("Exalted", "Own Sign", "Vargottama") for s in status_list):
                overall = "Strong"
            elif "Debilitated" in status_list:
                overall = "Weakened"
            else:
                overall = "Neutral"

            strengths[planet] = {
                "sign": sign,
                "degree": round(deg_in_sign, 2),
                "status_list": status_list,
                "overall": overall,
                "retrograde": data.get("retrograde", False),
                "d9_sign": d9.get("d9_sign", ""),
                "vargottama": d9.get("vargottama", False),
            }
        return strengths

    # ─── Yoga detection ───────────────────────────────────────────────────────

    def _detect_yogas(
        self,
        mathematical_data: dict,
        planet_houses: Dict[str, int],
        lordships: Dict[str, List[int]],
    ) -> List[Dict]:
        yogas: List[Dict] = []
        navamsa_data = mathematical_data.get("_navamsa", {})

        # 1. Vargottama yoga
        for planet, d9 in navamsa_data.items():
            if d9.get("vargottama"):
                yogas.append({
                    "name": f"{planet} Vargottama",
                    "type": "Strength",
                    "description": (
                        f"{planet} occupies the same sign in D1 and D9 — "
                        "pure, undiluted planetary energy; supreme strength in its domain"
                    ),
                    "planets": [planet],
                    "confidence": "High",
                })

        # 2. Gaja Kesari — Jupiter in kendra from Moon
        moon_h = planet_houses.get("Moon", 0)
        jup_h = planet_houses.get("Jupiter", 0)
        if moon_h and jup_h:
            diff = (jup_h - moon_h) % 12
            if diff in (0, 3, 6, 9):
                yogas.append({
                    "name": "Gaja Kesari Yoga",
                    "type": "Benefic",
                    "description": (
                        "Jupiter in angular position from Moon — intelligence, fame, "
                        "nobility, leadership ability, and protection in life"
                    ),
                    "planets": ["Jupiter", "Moon"],
                    "confidence": "High" if diff in (0, 6) else "Medium",
                })

        # 3. Raj yoga — planet ruling both trikona (1,5,9) and kendra (1,4,7,10)
        for planet, houses in lordships.items():
            rules_trikona = any(h in (1, 5, 9) for h in houses)
            rules_kendra = any(h in (1, 4, 7, 10) for h in houses)
            if rules_trikona and rules_kendra:
                yogas.append({
                    "name": f"Raj Yoga ({planet})",
                    "type": "Power",
                    "description": (
                        f"{planet} rules houses {houses} — both a trikona and a kendra, "
                        "creating natural authority, success, and social recognition"
                    ),
                    "planets": [planet],
                    "confidence": "Medium",
                })

        # 4. Kemadruma — Moon with no planets in 2nd and 12th houses from it
        if moon_h:
            adj_houses = {(moon_h % 12) + 1, ((moon_h - 2) % 12) + 1}
            planets_near = {
                p for p, h in planet_houses.items()
                if h in adj_houses and p not in ("Rahu", "Ketu", "Ascendant")
            }
            if not planets_near:
                yogas.append({
                    "name": "Kemadruma Yoga",
                    "type": "Challenge",
                    "description": (
                        "Moon has no planets in adjacent houses — tendency toward emotional "
                        "solitude, self-reliance, and periods of isolation or introspection"
                    ),
                    "planets": ["Moon"],
                    "confidence": "Medium",
                })

        # 5. Budha-Aditya — Sun and Mercury in same house
        sun_h = planet_houses.get("Sun", 0)
        mer_h = planet_houses.get("Mercury", 0)
        if sun_h and mer_h and sun_h == mer_h:
            yogas.append({
                "name": "Budha-Aditya Yoga",
                "type": "Intelligence",
                "description": (
                    "Sun and Mercury conjunct — exceptional intellect, sharp communication, "
                    "leadership through intelligence; strong for writing, analysis, and strategy"
                ),
                "planets": ["Sun", "Mercury"],
                "confidence": "High",
            })

        # 6. Venus-Jupiter strong relationship
        ven_h = planet_houses.get("Venus", 0)
        if ven_h and jup_h:
            diff = (ven_h - jup_h) % 12
            if diff in (0, 6):
                yogas.append({
                    "name": "Lakshmi-Guru Connection",
                    "type": "Prosperity",
                    "description": (
                        "Venus and Jupiter in strong mutual relationship — wealth, aesthetic sense, "
                        "wisdom in relationships, and blessings in marriage and finances"
                    ),
                    "planets": ["Venus", "Jupiter"],
                    "confidence": "Medium",
                })

        # 7. Retrograde planet in own/exaltation sign
        for planet in ("Jupiter", "Saturn", "Mars"):
            data = mathematical_data.get(planet, {})
            if data.get("retrograde"):
                sign = self.engine.get_sign_name(data.get("longitude", 0))
                if (
                    sign in PLANET_OWN_SIGNS.get(planet, [])
                    or PLANET_EXALTATIONS.get(planet) == sign
                ):
                    yogas.append({
                        "name": f"Retrograde {planet} in Power",
                        "type": "Karmic",
                        "description": (
                            f"Retrograde {planet} in own/exalted sign — intensified, internalized "
                            "energy; deep karmic theme requiring conscious effort; eventual mastery"
                        ),
                        "planets": [planet],
                        "confidence": "High",
                    })

        # 8. Dhana yoga — 2nd/11th lords related
        lagna_idx = 0  # default, will use lordship keys
        # Find 2nd and 11th lords
        lord_2 = SIGN_RULERS[SIGN_NAMES[(list(lordships.keys())[0:1] and 0) % 12]]  # fallback
        for p, hs in lordships.items():
            if 2 in hs:
                lord_2_planet = p
            if 11 in hs:
                lord_11_planet = p

        if "lord_2_planet" in dir() and "lord_11_planet" in dir():
            h2 = planet_houses.get(lord_2_planet, 0)
            h11 = planet_houses.get(lord_11_planet, 0)
            if h2 and h11 and (h2 == h11 or {h2, h11} & {2, 11, 5, 9, 1}):
                yogas.append({
                    "name": "Dhana Yoga",
                    "type": "Wealth",
                    "description": (
                        f"2nd lord ({lord_2_planet}) and 11th lord ({lord_11_planet}) "
                        "in favourable relationship — wealth accumulation, financial gains"
                    ),
                    "planets": [lord_2_planet, lord_11_planet],
                    "confidence": "Medium",
                })

        return yogas

    # ─── Domain briefs ────────────────────────────────────────────────────────

    def _compute_domain_briefs(
        self,
        mathematical_data: dict,
        planet_houses: Dict[str, int],
        lordships: Dict[str, List[int]],
        planet_strengths: Dict[str, Dict],
        dasha_timeline: dict,
    ) -> Dict[str, Dict]:
        """Build structured evidence brief for each life domain."""
        navamsa_data = mathematical_data.get("_navamsa", {})

        def pinfo(planet: str) -> Dict:
            """Compact info dict for one planet."""
            data = mathematical_data.get(planet, {})
            if not data:
                return {"sign": "?", "degree": 0, "house": "?", "overall": "Neutral", "status": []}
            sign = self.engine.get_sign_name(data.get("longitude", 0))
            ps = planet_strengths.get(planet, {})
            return {
                "sign": sign,
                "degree": round(data.get("longitude", 0) % 30, 2),
                "house": planet_houses.get(planet, "?"),
                "overall": ps.get("overall", "Neutral"),
                "status": ps.get("status_list", []),
                "retrograde": data.get("retrograde", False),
                "d9_sign": navamsa_data.get(planet, {}).get("d9_sign", ""),
                "vargottama": navamsa_data.get(planet, {}).get("vargottama", False),
            }

        def build(items: List[Dict]) -> tuple:
            """Return (items, confidence_str) from a list of {point, supports} dicts."""
            n_support = sum(1 for i in items if i.get("supports"))
            conf = _confidence_from_count(n_support, len(items))
            return items, conf

        # Resolve lagna index from lordships to find house signs
        # lordships maps planet → [houses], so we can derive house signs
        # Houses 1..12 were assigned by _compute_houses(lagna_idx)
        # We need lagna_idx here — derive it from any planet's position
        # Use Sun as reference: sign_idx = int(sun_lon/30), house = planet_houses[Sun]
        # lagna_idx = (sign_idx - house + 1 + 12) % 12
        sun_data = mathematical_data.get("Sun", {})
        sun_sign_idx = int(sun_data.get("longitude", 0) / 30) % 12 if sun_data else 0
        sun_house = planet_houses.get("Sun", 1)
        lagna_idx = (sun_sign_idx - sun_house + 1 + 12) % 12

        def house_sign(h: int) -> str:
            return SIGN_NAMES[(lagna_idx + h - 1) % 12]

        def house_lord(h: int) -> str:
            return SIGN_RULERS[house_sign(h)]

        # Collect planet info objects once
        pi = {p: pinfo(p) for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]}

        domains: Dict[str, Dict] = {}

        # ── CAREER (10th house) ──────────────────────────────────────────────
        hs10 = house_sign(10)
        hl10 = house_lord(10)
        items, conf = build([
            {"point": f"10th house is {hs10}", "supports": True},
            {"point": f"10th lord {hl10} in house {pi[hl10]['house']} ({pi[hl10]['sign']})",
             "supports": pi[hl10]["overall"] in ("Strong", "Neutral")},
            {"point": f"Sun (authority) in H{pi['Sun']['house']} ({pi['Sun']['sign']}) — {pi['Sun']['overall']}",
             "supports": pi["Sun"]["overall"] != "Weakened"},
            {"point": f"Saturn (work ethic/karma) in H{pi['Saturn']['house']} — {pi['Saturn']['overall']}",
             "supports": True},
            {"point": f"Mercury (intellect/business) in H{pi['Mercury']['house']} — {pi['Mercury']['overall']}",
             "supports": pi["Mercury"]["overall"] != "Weakened"},
        ] + ([
            {"point": f"10th lord {hl10} Vargottama in D9 — exceptionally strong career promise",
             "supports": True}
        ] if navamsa_data.get(hl10, {}).get("vargottama") else []))
        domains["career"] = {
            "house_sign": hs10, "house_lord": hl10,
            "house_lord_placement": f"H{pi[hl10]['house']} ({pi[hl10]['sign']})",
            "house_lord_status": pi[hl10]["status"],
            "supporting": items, "confidence": conf,
            "dasha_relevance": _dasha_timing_for_domain("career", dasha_timeline),
            "key_planets": {k: pi[k] for k in ["Sun", "Saturn", "Mercury", "Mars"]},
        }

        # ── EDUCATION / INTELLIGENCE (5th + 9th) ────────────────────────────
        hs5 = house_sign(5);  hl5 = house_lord(5)
        hs9 = house_sign(9);  hl9 = house_lord(9)
        items, conf = build([
            {"point": f"5th house (intelligence/creativity): {hs5}, lord {hl5} in H{pi[hl5]['house']}",
             "supports": pi[hl5]["overall"] in ("Strong", "Neutral")},
            {"point": f"9th house (higher education/philosophy): {hs9}, lord {hl9} in H{pi[hl9]['house']}",
             "supports": True},
            {"point": f"Mercury (intellect) in H{pi['Mercury']['house']} ({pi['Mercury']['sign']}) — {pi['Mercury']['overall']}",
             "supports": pi["Mercury"]["overall"] != "Weakened"},
            {"point": f"Jupiter (wisdom/knowledge) in H{pi['Jupiter']['house']} — {pi['Jupiter']['overall']}",
             "supports": pi["Jupiter"]["overall"] != "Weakened"},
        ])
        domains["education"] = {
            "5th_sign": hs5, "5th_lord": hl5,
            "9th_sign": hs9, "9th_lord": hl9,
            "supporting": items, "confidence": conf,
            "dasha_relevance": _dasha_timing_for_domain("education", dasha_timeline),
            "key_planets": {k: pi[k] for k in ["Mercury", "Jupiter", "Moon"]},
        }

        # ── WEALTH (2nd + 11th) ──────────────────────────────────────────────
        hs2 = house_sign(2);   hl2 = house_lord(2)
        hs11 = house_sign(11); hl11 = house_lord(11)
        items, conf = build([
            {"point": f"2nd house (accumulated wealth): {hs2}, lord {hl2} in H{pi[hl2]['house']}",
             "supports": pi[hl2]["overall"] in ("Strong", "Neutral")},
            {"point": f"11th house (income/gains): {hs11}, lord {hl11} in H{pi[hl11]['house']}",
             "supports": pi[hl11]["overall"] in ("Strong", "Neutral")},
            {"point": f"Jupiter (natural karaka for wealth) in H{pi['Jupiter']['house']} — {pi['Jupiter']['overall']}",
             "supports": pi["Jupiter"]["overall"] != "Weakened"},
            {"point": f"Venus in H{pi['Venus']['house']} ({pi['Venus']['sign']}) — {pi['Venus']['overall']}",
             "supports": pi["Venus"]["overall"] != "Weakened"},
        ])
        domains["wealth"] = {
            "2nd_sign": hs2, "2nd_lord": hl2,
            "11th_sign": hs11, "11th_lord": hl11,
            "supporting": items, "confidence": conf,
            "dasha_relevance": _dasha_timing_for_domain("wealth", dasha_timeline),
            "key_planets": {k: pi[k] for k in ["Jupiter", "Venus", "Mercury"]},
        }

        # ── RELATIONSHIPS / MARRIAGE (7th + 5th + Venus) ────────────────────
        hs7 = house_sign(7);  hl7 = house_lord(7)
        d9_venus = navamsa_data.get("Venus", {})
        items, conf = build([
            {"point": f"7th house (marriage/partnerships): {hs7}, lord {hl7} in H{pi[hl7]['house']} ({pi[hl7]['sign']})",
             "supports": pi[hl7]["overall"] in ("Strong", "Neutral")},
            {"point": f"5th house (romance): {hs5}, lord {hl5} in H{pi[hl5]['house']}",
             "supports": pi[hl5]["overall"] in ("Strong", "Neutral")},
            {"point": f"Venus (love/attraction) in H{pi['Venus']['house']} ({pi['Venus']['sign']}) — {pi['Venus']['overall']}",
             "supports": pi["Venus"]["overall"] != "Weakened"},
            {"point": f"Jupiter (marriage blessing) in H{pi['Jupiter']['house']} — {pi['Jupiter']['overall']}",
             "supports": True},
            {"point": f"Moon (emotional bond) in H{pi['Moon']['house']} ({pi['Moon']['sign']}) — {pi['Moon']['overall']}",
             "supports": pi["Moon"]["overall"] != "Weakened"},
        ] + ([
            {"point": f"Venus exalted in D9 (Pisces) — very strong marriage promise", "supports": True}
        ] if d9_venus.get("d9_sign") == "Pisces" else []) + ([
            {"point": f"Venus Vargottama in D9 — consistent relationship strength across charts", "supports": True}
        ] if d9_venus.get("vargottama") else []))
        domains["relationships"] = {
            "7th_sign": hs7, "7th_lord": hl7,
            "5th_sign": hs5, "5th_lord": hl5,
            "7th_lord_status": pi[hl7]["status"],
            "supporting": items, "confidence": conf,
            "dasha_relevance": _dasha_timing_for_domain("relationships", dasha_timeline),
            "key_planets": {k: pi[k] for k in ["Venus", "Jupiter", "Moon", "Mars", "Rahu"]},
        }

        # ── FAMILY / HOME (4th) ──────────────────────────────────────────────
        hs4 = house_sign(4);  hl4 = house_lord(4)
        items, conf = build([
            {"point": f"4th house (home/mother/roots): {hs4}, lord {hl4} in H{pi[hl4]['house']}",
             "supports": pi[hl4]["overall"] in ("Strong", "Neutral")},
            {"point": f"Moon (mother/emotional security) in H{pi['Moon']['house']} ({pi['Moon']['sign']}) — {pi['Moon']['overall']}",
             "supports": pi["Moon"]["overall"] != "Weakened"},
            {"point": f"Venus (domestic happiness) in H{pi['Venus']['house']} — {pi['Venus']['overall']}",
             "supports": pi["Venus"]["overall"] != "Weakened"},
        ])
        domains["family"] = {
            "4th_sign": hs4, "4th_lord": hl4,
            "supporting": items, "confidence": conf,
            "dasha_relevance": _dasha_timing_for_domain("family", dasha_timeline),
            "key_planets": {k: pi[k] for k in ["Moon", "Venus", "Mars"]},
        }

        # ── HEALTH (1st + 6th) ───────────────────────────────────────────────
        lagna_sign = SIGN_NAMES[lagna_idx]
        ll = SIGN_RULERS[lagna_sign]  # lagna lord
        hs6 = house_sign(6);  hl6 = house_lord(6)
        items, conf = build([
            {"point": f"Lagna ({lagna_sign}), lagna lord {ll} in H{pi[ll]['house']} ({pi[ll]['sign']}) — {pi[ll]['overall']}",
             "supports": pi[ll]["overall"] != "Weakened"},
            {"point": f"6th house (disease/challenges): {hs6}, lord {hl6} in H{pi[hl6]['house']}",
             "supports": planet_houses.get(hl6, 0) not in (1, 5, 9)},
            {"point": f"Sun (vitality) in H{pi['Sun']['house']} — {pi['Sun']['overall']}",
             "supports": pi["Sun"]["overall"] != "Weakened"},
            {"point": f"Moon (mental health) in H{pi['Moon']['house']} — {pi['Moon']['overall']}",
             "supports": pi["Moon"]["overall"] != "Weakened"},
            {"point": f"Mars (energy/stamina) in H{pi['Mars']['house']} — {pi['Mars']['overall']}",
             "supports": True},
        ])
        domains["health"] = {
            "lagna_lord": ll, "lagna_lord_info": pi[ll],
            "6th_sign": hs6, "6th_lord": hl6,
            "supporting": items, "confidence": conf,
            "dasha_relevance": _dasha_timing_for_domain("health", dasha_timeline),
            "key_planets": {k: pi[k] for k in ["Sun", "Moon", "Mars", "Saturn"]},
        }

        # ── SPIRITUALITY / DHARMA (9th + 12th + Ketu) ───────────────────────
        hs12 = house_sign(12); hl12 = house_lord(12)
        items, conf = build([
            {"point": f"9th house (dharma/luck/guru): {hs9}, lord {hl9} in H{pi[hl9]['house']} — {pi[hl9]['overall']}",
             "supports": True},
            {"point": f"12th house (liberation/seclusion): {hs12}, lord {hl12} in H{pi[hl12]['house']}",
             "supports": True},
            {"point": f"Jupiter (guru/wisdom) in H{pi['Jupiter']['house']} — {pi['Jupiter']['overall']}",
             "supports": pi["Jupiter"]["overall"] != "Weakened"},
            {"point": f"Ketu (past karma/spiritual liberation) in H{pi['Ketu']['house']} ({pi['Ketu']['sign']})",
             "supports": True},
        ])
        domains["spirituality"] = {
            "9th_sign": hs9, "9th_lord": hl9,
            "12th_sign": hs12, "12th_lord": hl12,
            "supporting": items, "confidence": conf,
            "dasha_relevance": _dasha_timing_for_domain("spirituality", dasha_timeline),
            "key_planets": {k: pi[k] for k in ["Jupiter", "Ketu", "Saturn"]},
        }

        # ── FOREIGN TRAVEL / RELOCATION (12th + 9th + Rahu) ─────────────────
        items, conf = build([
            {"point": f"12th house (foreign lands): {hs12}, lord {hl12} in H{pi[hl12]['house']}",
             "supports": True},
            {"point": f"Rahu (foreign/unconventional) in H{pi['Rahu']['house']} ({pi['Rahu']['sign']})",
             "supports": planet_houses.get("Rahu", 0) in (7, 8, 9, 12, 3)},
            {"point": f"9th house (long journeys): {hs9}, lord {hl9} in H{pi[hl9]['house']}",
             "supports": True},
            {"point": f"Moon (overseas relocation) in H{pi['Moon']['house']}",
             "supports": planet_houses.get("Moon", 0) in (3, 9, 12)},
        ])
        domains["travel"] = {
            "12th_sign": hs12, "12th_lord": hl12,
            "9th_sign": hs9,
            "supporting": items, "confidence": conf,
            "dasha_relevance": _dasha_timing_for_domain("travel", dasha_timeline),
            "key_planets": {k: pi[k] for k in ["Rahu", "Jupiter", "Saturn"]},
        }

        return domains

    # ─── Dasha timeline ───────────────────────────────────────────────────────

    def _compute_dasha_timeline(
        self, mathematical_data: dict, birth_datetime: datetime
    ) -> Dict[str, Any]:
        moon_lon = mathematical_data["Moon"]["longitude"]
        balance = self.dasha_engine.calculate_dasha_balance(moon_lon, birth_datetime)
        schedule = self.dasha_engine.generate_mahadasha_schedule(balance, years_to_generate=80)

        now = datetime.now()
        current = self.dasha_engine.get_current_dasha(moon_lon, birth_datetime, now)

        # Antardasha schedule for the current mahadasha
        md = current.get("mahadasha", "")
        antardashas: List[Dict] = []
        if md and md != "Unknown":
            entry = next(
                (s for s in schedule if s["lord"] == md),
                None,
            )
            if entry:
                antardashas = self.dasha_engine.generate_antardashas(md, entry["start"])

        # Next 3 upcoming mahadashas
        upcoming: List[Dict] = []
        found = False
        for s in schedule:
            if s["lord"] == md and not found:
                found = True
                continue
            if found:
                upcoming.append(s)
            if len(upcoming) >= 3:
                break

        return {
            "birth_balance": balance,
            "schedule": schedule[:10],
            "current": current,
            "antardashas": antardashas,
            "upcoming_mds": upcoming,
        }

    # ─── Life phase ───────────────────────────────────────────────────────────

    def _compute_life_phase(self, dasha_timeline: Dict) -> Dict:
        current = dasha_timeline.get("current", {})
        md = current.get("mahadasha", "")
        ad = current.get("antardasha", "")
        return {
            "mahadasha": md,
            "antardasha": ad,
            "md_nature": PLANET_NATURE.get(md, ""),
            "ad_nature": PLANET_NATURE.get(ad, ""),
            "phase_type": PLANET_PHASE_TYPE.get(md, "transition"),
            "md_end": current.get("end_date", ""),
            "ad_end": current.get("end_date", ""),
            "activated_areas": _infer_activated_areas(md, ad),
        }

    # ─── Top themes ───────────────────────────────────────────────────────────

    def _compute_top_themes(
        self,
        domains: Dict,
        yogas: List[Dict],
        dasha_timeline: Dict,
    ) -> List[Dict]:
        LABELS = {
            "career": "Career & Professional Growth",
            "wealth": "Wealth & Financial Prosperity",
            "relationships": "Relationships & Marriage",
            "health": "Vitality & Physical Wellbeing",
            "spirituality": "Spiritual Growth & Dharma",
            "education": "Intelligence & Education",
            "family": "Family & Emotional Security",
            "travel": "Foreign Connections & Travel",
        }
        SORT = {"High": 3, "Medium": 2, "Low": 1}
        themes: List[Dict] = []

        for key, label in LABELS.items():
            d = domains.get(key, {})
            conf = d.get("confidence", "Low")
            evidence = [e["point"] for e in d.get("supporting", []) if e.get("supports")]
            themes.append({
                "theme": label,
                "strength": conf,
                "evidence": evidence[:2] if evidence else ["No dominant indicators"],
                "timing": _dasha_timing_for_domain(key, dasha_timeline),
                "_sort": SORT.get(conf, 0),
            })

        # High-confidence yogas also become themes
        for yoga in yogas:
            if yoga.get("confidence") == "High":
                themes.append({
                    "theme": yoga["name"],
                    "strength": "High",
                    "evidence": [yoga["description"]],
                    "timing": "Lifetime — inherent chart quality",
                    "_sort": 3,
                })

        themes.sort(key=lambda x: -x["_sort"])
        # Remove internal sort key before returning
        for t in themes:
            t.pop("_sort", None)
        return themes[:7]
