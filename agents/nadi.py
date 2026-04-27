"""
Nadi & State Expert Agents (y₂, y₃)
Structural analysis including elemental groupings and special planetary states.
"""

from typing import Dict, List, Set


# Element associations for zodiac signs (from parashara_expert)
SIGN_ELEMENTS = {
    "Aries": "Fire", "Leo": "Fire", "Sagittarius": "Fire",
    "Taurus": "Earth", "Virgo": "Earth", "Capricorn": "Earth",
    "Gemini": "Air", "Libra": "Air", "Aquarius": "Air",
    "Cancer": "Water", "Scorpio": "Water", "Pisces": "Water"
}

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# Gandanta zones - critical junctions between water and fire signs
# These are the last degrees of water signs and first degrees of fire signs
GANDANTA_ZONES = [
    # Pisces-Aries junction (end of Revati, start of Ashwini)
    {"start": 356.4, "end": 360.0, "from_sign": "Pisces", "to_sign": "Aries"},
    {"start": 0.0, "end": 3.6, "from_sign": "Pisces", "to_sign": "Aries"},
    
    # Cancer-Leo junction (end of Ashlesha, start of Magha)
    {"start": 116.4, "end": 120.0, "from_sign": "Cancer", "to_sign": "Leo"},
    {"start": 120.0, "end": 123.6, "from_sign": "Cancer", "to_sign": "Leo"},
    
    # Scorpio-Sagittarius junction (end of Jyeshtha, start of Mula)
    {"start": 236.4, "end": 240.0, "from_sign": "Scorpio", "to_sign": "Sagittarius"},
    {"start": 240.0, "end": 243.6, "from_sign": "Scorpio", "to_sign": "Sagittarius"},
]


def get_sign_from_longitude(longitude: float) -> str:
    """
    Get zodiac sign name from sidereal longitude.
    
    Args:
        longitude: Sidereal longitude in degrees (0-360)
    
    Returns:
        Zodiac sign name
    """
    longitude = longitude % 360
    sign_index = int(longitude / 30)
    return ZODIAC_SIGNS[sign_index]


def get_element_from_longitude(longitude: float) -> str:
    """
    Get element (Fire/Earth/Air/Water) from sidereal longitude.
    
    Args:
        longitude: Sidereal longitude in degrees (0-360)
    
    Returns:
        Element name
    """
    sign = get_sign_from_longitude(longitude)
    return SIGN_ELEMENTS[sign]


def analyze_nadi_links(planet_positions: Dict[str, Dict]) -> Dict[str, List[List[str]]]:
    """
    Analyze Nadi links - planets grouped by elemental trines.
    
    Planets in the same element (Fire/Earth/Air/Water) are considered
    "linked" and have natural affinity/resonance with each other.
    
    Args:
        planet_positions: Dictionary from EphemerisEngine containing planet data
    
    Returns:
        Dictionary with:
        - 'element_groups': List of planet groups by element
        - 'linked_pairs': List of planet pairs in same element
    """
    # Group planets by element
    element_groups = {
        "Fire": [],
        "Earth": [],
        "Air": [],
        "Water": []
    }
    
    for planet_name, planet_data in planet_positions.items():
        longitude = planet_data.get("longitude")
        if longitude is not None:
            element = get_element_from_longitude(longitude)
            sign = get_sign_from_longitude(longitude)
            element_groups[element].append({
                "planet": planet_name,
                "sign": sign,
                "longitude": longitude
            })
    
    # Find linked groups (elements with 2+ planets)
    linked_groups = []
    for element, planets in element_groups.items():
        if len(planets) >= 2:
            planet_names = [p["planet"] for p in planets]
            linked_groups.append({
                "element": element,
                "planets": planet_names,
                "count": len(planet_names)
            })
    
    # Find all planet pairs in same element
    linked_pairs = []
    for element, planets in element_groups.items():
        if len(planets) >= 2:
            # Generate all pairs
            for i in range(len(planets)):
                for j in range(i + 1, len(planets)):
                    linked_pairs.append({
                        "planet1": planets[i]["planet"],
                        "planet2": planets[j]["planet"],
                        "element": element,
                        "sign1": planets[i]["sign"],
                        "sign2": planets[j]["sign"]
                    })
    
    return {
        "element_groups": linked_groups,
        "linked_pairs": linked_pairs,
        "full_distribution": {
            element: [p["planet"] for p in planets]
            for element, planets in element_groups.items()
        }
    }


def is_in_gandanta(longitude: float) -> Dict[str, any]:
    """
    Check if a longitude is in Gandanta zone (water-fire junction).
    
    Gandanta represents critical transitional zones that are considered
    challenging or transformative in Vedic astrology.
    
    Args:
        longitude: Sidereal longitude in degrees (0-360)
    
    Returns:
        Dictionary with 'in_gandanta' boolean and details if True
    """
    longitude = longitude % 360
    
    for zone in GANDANTA_ZONES:
        start = zone["start"]
        end = zone["end"]
        
        # Handle wrap-around at 360/0 degrees
        if start > end:  # Crosses 360/0 boundary
            if longitude >= start or longitude <= end:
                return {
                    "in_gandanta": True,
                    "from_sign": zone["from_sign"],
                    "to_sign": zone["to_sign"],
                    "longitude": longitude,
                    "zone": f"{zone['from_sign']}-{zone['to_sign']}"
                }
        else:
            if start <= longitude <= end:
                return {
                    "in_gandanta": True,
                    "from_sign": zone["from_sign"],
                    "to_sign": zone["to_sign"],
                    "longitude": longitude,
                    "zone": f"{zone['from_sign']}-{zone['to_sign']}"
                }
    
    return {"in_gandanta": False}


def analyze_special_states(planet_positions: Dict[str, Dict]) -> Dict[str, List[Dict]]:
    """
    Identify special planetary states (retrograde, gandanta, etc.).
    
    Args:
        planet_positions: Dictionary from EphemerisEngine containing planet data
    
    Returns:
        Dictionary containing:
        - 'retrograde_planets': List of retrograde planets with details
        - 'gandanta_planets': List of planets in Gandanta zones
        - 'special_states': Combined list of all special states
    """
    retrograde_planets = []
    gandanta_planets = []
    special_states = []
    
    for planet_name, planet_data in planet_positions.items():
        longitude = planet_data.get("longitude")
        is_retrograde = planet_data.get("retrograde", False)
        speed = planet_data.get("speed", 0)
        
        if longitude is None:
            continue
        
        sign = get_sign_from_longitude(longitude)
        
        # Check retrograde state
        if is_retrograde:
            retro_info = {
                "planet": planet_name,
                "sign": sign,
                "longitude": longitude,
                "speed": speed,
                "state": "Retrograde"
            }
            retrograde_planets.append(retro_info)
            special_states.append(retro_info)
        
        # Check Gandanta state
        gandanta_check = is_in_gandanta(longitude)
        if gandanta_check["in_gandanta"]:
            gandanta_info = {
                "planet": planet_name,
                "sign": sign,
                "longitude": longitude,
                "state": "Gandanta",
                "zone": gandanta_check["zone"],
                "from_sign": gandanta_check["from_sign"],
                "to_sign": gandanta_check["to_sign"]
            }
            gandanta_planets.append(gandanta_info)
            special_states.append(gandanta_info)
    
    return {
        "retrograde_planets": retrograde_planets,
        "gandanta_planets": gandanta_planets,
        "special_states": special_states,
        "counts": {
            "retrograde": len(retrograde_planets),
            "gandanta": len(gandanta_planets),
            "total_special": len(special_states)
        }
    }


def perform_structural_analysis(planet_positions: Dict[str, Dict]) -> Dict:
    """
    Perform complete structural analysis combining Nadi and State experts.
    
    This is the main function that combines elemental groupings (Nadi)
    with special planetary states to provide comprehensive structural insight.
    
    Args:
        planet_positions: Dictionary from EphemerisEngine containing planet data
    
    Returns:
        Comprehensive structural analysis JSON object
    """
    # Analyze Nadi links (elemental groupings)
    nadi_analysis = analyze_nadi_links(planet_positions)
    
    # Analyze special states
    state_analysis = analyze_special_states(planet_positions)
    
    # Combine into comprehensive structural analysis
    structural_analysis = {
        "nadi_analysis": {
            "element_groups": nadi_analysis["element_groups"],
            "linked_pairs": nadi_analysis["linked_pairs"],
            "distribution": nadi_analysis["full_distribution"]
        },
        "state_analysis": {
            "retrograde_planets": state_analysis["retrograde_planets"],
            "gandanta_planets": state_analysis["gandanta_planets"],
            "special_states": state_analysis["special_states"],
            "counts": state_analysis["counts"]
        },
        "summary": {
            "total_element_groups": len(nadi_analysis["element_groups"]),
            "total_linked_pairs": len(nadi_analysis["linked_pairs"]),
            "total_retrograde": state_analysis["counts"]["retrograde"],
            "total_gandanta": state_analysis["counts"]["gandanta"],
            "total_special": state_analysis["counts"]["total_special"],
            "dominant_element": max(
                nadi_analysis["full_distribution"].items(),
                key=lambda x: len(x[1])
            )[0] if any(nadi_analysis["full_distribution"].values()) else None
        }
    }
    
    return structural_analysis
