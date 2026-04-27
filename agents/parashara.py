"""
Parashara Expert Agent (y₁) - Classical Vedic Aspects
Implements traditional aspect rules from Parashara system.
"""

from typing import Dict, List, Tuple


# Zodiac signs in order (Whole Sign system)
ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# Element associations for each sign
SIGN_ELEMENTS = {
    "Aries": "Fire", "Leo": "Fire", "Sagittarius": "Fire",
    "Taurus": "Earth", "Virgo": "Earth", "Capricorn": "Earth",
    "Gemini": "Air", "Libra": "Air", "Aquarius": "Air",
    "Cancer": "Water", "Scorpio": "Water", "Pisces": "Water"
}

# Special aspect rules for each planet (in addition to 7th house aspect)
SPECIAL_ASPECTS = {
    "Mars": [4, 7, 8],
    "Jupiter": [5, 7, 9],
    "Saturn": [3, 7, 10],
    "Sun": [7],
    "Moon": [7],
    "Mercury": [7],
    "Venus": [7],
    "Rahu": [7],
    "Ketu": [7]
}


def get_house_from_longitude(longitude: float) -> int:
    """
    Calculate house/sign number from sidereal longitude using Whole Sign system.
    
    Args:
        longitude: Sidereal longitude in degrees (0-360)
    
    Returns:
        House number (1-12), where 1 = Aries, 2 = Taurus, etc.
    """
    # Normalize to 0-360 range
    longitude = longitude % 360
    
    # Each sign/house is exactly 30 degrees in Whole Sign system
    house_num = int(longitude / 30) + 1
    
    # Handle edge case at exactly 360 degrees
    if house_num > 12:
        house_num = 1
    
    return house_num


def get_sign_name(house_num: int) -> str:
    """
    Get zodiac sign name from house number.
    
    Args:
        house_num: House number (1-12)
    
    Returns:
        Zodiac sign name
    """
    return ZODIAC_SIGNS[(house_num - 1) % 12]


def calculate_aspect_houses(planet_house: int, aspect_positions: List[int]) -> List[int]:
    """
    Calculate which houses a planet aspects from its position.
    
    Args:
        planet_house: House number where planet is located (1-12)
        aspect_positions: List of aspect positions (e.g., [4, 7, 8] for Mars)
    
    Returns:
        List of house numbers that are aspected
    """
    aspected_houses = []
    
    for aspect_offset in aspect_positions:
        # Calculate target house (circular, 1-12)
        target_house = ((planet_house - 1 + aspect_offset) % 12) + 1
        aspected_houses.append(target_house)
    
    return aspected_houses


def calculate_aspects(planet_positions: Dict[str, Dict]) -> List[str]:
    """
    Calculate all Vedic aspects between planets using Parashara rules.
    
    Uses Whole Sign House system where each sign = 30 degrees = 1 house.
    
    Aspect rules:
    - Mars: aspects 4th, 7th, and 8th houses from itself
    - Jupiter: aspects 5th, 7th, and 9th houses from itself
    - Saturn: aspects 3rd, 7th, and 10th houses from itself
    - All other planets: aspect 7th house only
    
    Args:
        planet_positions: Dictionary from EphemerisEngine.calculate_planets()
                         or calculate_chart(), containing longitude data
    
    Returns:
        List of aspect description strings, e.g.:
        ['Mars (Aries) aspects Venus (Cancer)', ...]
    """
    aspects = []
    
    # First, determine house position for each planet
    planet_houses = {}
    for planet_name, planet_data in planet_positions.items():
        longitude = planet_data.get("longitude")
        if longitude is not None:
            house_num = get_house_from_longitude(longitude)
            sign_name = get_sign_name(house_num)
            planet_houses[planet_name] = {
                "house": house_num,
                "sign": sign_name,
                "longitude": longitude
            }
    
    # Calculate aspects for each planet
    for aspecting_planet, aspecting_data in planet_houses.items():
        aspecting_house = aspecting_data["house"]
        aspecting_sign = aspecting_data["sign"]
        
        # Get aspect positions for this planet
        aspect_positions = SPECIAL_ASPECTS.get(aspecting_planet, [7])
        
        # Calculate which houses are aspected
        aspected_houses = calculate_aspect_houses(aspecting_house, aspect_positions)
        
        # Check if any other planet is in the aspected houses
        for aspected_planet, aspected_data in planet_houses.items():
            # Don't aspect itself
            if aspected_planet == aspecting_planet:
                continue
            
            aspected_house = aspected_data["house"]
            aspected_sign = aspected_data["sign"]
            
            # Check if this planet is in one of the aspected houses
            if aspected_house in aspected_houses:
                # Determine aspect type based on house distance
                house_distance = (aspected_house - aspecting_house) % 12
                if house_distance == 0:
                    house_distance = 12
                
                aspect_type = f"{house_distance}th house"
                
                aspect_desc = (
                    f"{aspecting_planet} ({aspecting_sign}) aspects "
                    f"{aspected_planet} ({aspected_sign}) [{aspect_type}]"
                )
                aspects.append(aspect_desc)
    
    return aspects


def get_planet_relationships(planet_positions: Dict[str, Dict]) -> Dict[str, List[str]]:
    """
    Build a structured relationship map showing which planets aspect which.
    
    Args:
        planet_positions: Dictionary from EphemerisEngine containing planet data
    
    Returns:
        Dictionary mapping each planet to list of planets it aspects
    """
    relationships = {planet: [] for planet in planet_positions.keys()}
    
    # Get house positions
    planet_houses = {}
    for planet_name, planet_data in planet_positions.items():
        longitude = planet_data.get("longitude")
        if longitude is not None:
            house_num = get_house_from_longitude(longitude)
            planet_houses[planet_name] = house_num
    
    # Build relationships
    for aspecting_planet, aspecting_house in planet_houses.items():
        aspect_positions = SPECIAL_ASPECTS.get(aspecting_planet, [7])
        aspected_houses = calculate_aspect_houses(aspecting_house, aspect_positions)
        
        for aspected_planet, aspected_house in planet_houses.items():
            if aspected_planet != aspecting_planet and aspected_house in aspected_houses:
                relationships[aspecting_planet].append(aspected_planet)
    
    return relationships


def check_vargottama(d1_sign_index: int, d9_sign_index: int) -> bool:
    """
    Check if a planet is Vargottama (Supreme Strength).
    
    Vargottama occurs when a planet occupies the same sign in both
    the Birth Chart (D1) and Navamsa Chart (D9). This is considered
    one of the most powerful placements in Vedic astrology, indicating
    the planet's energy is pure, strong, and manifests powerfully.
    
    Args:
        d1_sign_index: Sign index in birth chart (0-11)
        d9_sign_index: Sign index in navamsa chart (0-11)
    
    Returns:
        True if Vargottama, False otherwise
    """
    return d1_sign_index == d9_sign_index


def analyze_divisional_strength(planet_positions: Dict[str, Dict], 
                                navamsa_data: Dict[str, Dict]) -> Dict:
    """
    Analyze planetary strength using Navamsa (D9) divisional chart.
    
    The Navamsa is called the "fruit" of the birth chart - it shows
    the inner potential and manifestation strength of planets.
    
    Args:
        planet_positions: D1 (birth chart) positions from EphemerisEngine
        navamsa_data: D9 positions calculated for each planet
    
    Returns:
        Dictionary with divisional strength analysis including:
        - vargottama_planets: List of supremely strong planets
        - d9_placements: Navamsa sign for each planet
        - strength_summary: Overall strength assessment
    """
    vargottama_planets = []
    d9_placements = {}
    strength_notes = []
    
    for planet_name, d9_info in navamsa_data.items():
        d1_sign = d9_info.get("d1_sign")
        d9_sign = d9_info.get("d9_sign")
        is_vargottama = d9_info.get("vargottama", False)
        
        d9_placements[planet_name] = {
            "d1_sign": d1_sign,
            "d9_sign": d9_sign,
            "vargottama": is_vargottama
        }
        
        if is_vargottama:
            vargottama_planets.append(planet_name)
            strength_notes.append(
                f"{planet_name} is VARGOTTAMA ({d1_sign}=D9): Supreme strength, "
                f"pure expression, powerful manifestation"
            )
    
    # Additional strength indicators
    for planet_name, d9_info in navamsa_data.items():
        if planet_name not in vargottama_planets:
            d9_sign = d9_info.get("d9_sign")
            
            # Check for exaltation in D9 (simplified - can be expanded)
            exaltation_signs = {
                "Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn",
                "Mercury": "Virgo", "Jupiter": "Cancer", "Venus": "Pisces",
                "Saturn": "Libra", "Rahu": "Taurus", "Ketu": "Scorpio"
            }
            
            if exaltation_signs.get(planet_name) == d9_sign:
                strength_notes.append(
                    f"{planet_name} is exalted in D9 ({d9_sign}): "
                    f"Strong manifestation potential"
                )
    
    summary = {
        "vargottama_count": len(vargottama_planets),
        "vargottama_planets": vargottama_planets,
        "interpretation": (
            "Exceptional chart" if len(vargottama_planets) >= 3 else
            "Strong foundation" if len(vargottama_planets) >= 1 else
            "Standard strength distribution"
        )
    }
    
    return {
        "vargottama_planets": vargottama_planets,
        "d9_placements": d9_placements,
        "strength_notes": strength_notes,
        "summary": summary
    }
