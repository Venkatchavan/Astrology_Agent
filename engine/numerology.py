"""
Numerology Engine - Phase 5
===========================
Calculates numerological values using both Pythagorean and Chaldean systems.
Provides Life Path, Destiny, and Attitude numbers for cross-verification with astrology.
"""

import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple


class NumerologyEngine:
    """
    Numerology calculation engine supporting:
    - Pythagorean system: Life Path, Attitude Number
    - Chaldean system: Destiny Number (name analysis)
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize the numerology engine.
        
        Args:
            data_dir: Path to directory containing numerology CSV files
        """
        self.data_dir = Path(data_dir)
        self.pythagorean_map = self._load_letter_values("numerology_pythagorean.csv")
        self.chaldean_map = self._load_letter_values("numerology_chaldean.csv")
        
        # Master numbers that should not be reduced
        self.master_numbers = {11, 22, 33}
        
        # Planetary rulers for each number
        self.number_rulers = {
            1: "Sun",
            2: "Moon",
            3: "Jupiter",
            4: "Rahu",
            5: "Mercury",
            6: "Venus",
            7: "Ketu",
            8: "Saturn",
            9: "Mars",
            11: "Moon/Uranus",  # Master Number
            22: "Saturn/Master Builder",  # Master Number
            33: "Jupiter/Master Teacher"  # Master Number
        }
        
        # Archetypal meanings
        self.number_meanings = {
            1: "Leader/Independent/Sun",
            2: "Partner/Diplomat/Moon",
            3: "Creator/Communicator/Jupiter",
            4: "Builder/Organizer/Rahu",
            5: "Freedom/Change/Mercury",
            6: "Nurturer/Harmonizer/Venus",
            7: "Seeker/Analyst/Ketu",
            8: "Authority/Power/Saturn",
            9: "Humanitarian/Completion/Mars",
            11: "Intuitive/Visionary/Master",
            22: "Master Builder/Manifestor",
            33: "Master Teacher/Healer"
        }
    
    def _load_letter_values(self, filename: str) -> Dict[str, int]:
        """
        Load letter-to-number mapping from CSV.
        
        Args:
            filename: Name of CSV file
            
        Returns:
            Dictionary mapping letters to numeric values
        """
        mapping = {}
        filepath = self.data_dir / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"Numerology data file not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                letter = row['letter'].upper()
                value = int(row['value'])
                mapping[letter] = value
        
        return mapping
    
    def _reduce_to_single_digit(self, number: int, keep_master: bool = True) -> int:
        """
        Reduce a number to single digit, optionally preserving master numbers.
        
        Args:
            number: Number to reduce
            keep_master: If True, preserve master numbers (11, 22, 33)
            
        Returns:
            Reduced number
        """
        if keep_master and number in self.master_numbers:
            return number
        
        while number > 9:
            if keep_master and number in self.master_numbers:
                return number
            number = sum(int(digit) for digit in str(number))
        
        return number
    
    def calculate_life_path(self, birth_date: datetime) -> Tuple[int, Dict]:
        """
        Calculate Life Path Number (Pythagorean system).
        This is the most important number - represents life purpose and core lessons.
        
        Method: Reduce day, month, year separately, then add and reduce.
        This preserves master numbers better than summing all digits at once.
        
        Args:
            birth_date: Date of birth
            
        Returns:
            Tuple of (life_path_number, details_dict)
        """
        day = birth_date.day
        month = birth_date.month
        year = birth_date.year
        
        # Reduce each component
        day_reduced = self._reduce_to_single_digit(day)
        month_reduced = self._reduce_to_single_digit(month)
        year_reduced = self._reduce_to_single_digit(year)
        
        # Add and reduce final
        total = day_reduced + month_reduced + year_reduced
        life_path = self._reduce_to_single_digit(total)
        
        details = {
            "number": life_path,
            "ruler": self.number_rulers.get(life_path, "Unknown"),
            "meaning": self.number_meanings.get(life_path, "Unknown"),
            "calculation": f"{day}→{day_reduced} + {month}→{month_reduced} + {year}→{year_reduced} = {total}→{life_path}"
        }
        
        return life_path, details
    
    def calculate_attitude_number(self, birth_date: datetime) -> Tuple[int, Dict]:
        """
        Calculate Attitude Number (Pythagorean system).
        Represents outward personality and how others perceive you.
        
        Method: Day + Month only
        
        Args:
            birth_date: Date of birth
            
        Returns:
            Tuple of (attitude_number, details_dict)
        """
        day = birth_date.day
        month = birth_date.month
        
        total = day + month
        attitude = self._reduce_to_single_digit(total)
        
        details = {
            "number": attitude,
            "ruler": self.number_rulers.get(attitude, "Unknown"),
            "meaning": self.number_meanings.get(attitude, "Unknown"),
            "calculation": f"{day} + {month} = {total}→{attitude}"
        }
        
        return attitude, details
    
    def calculate_destiny_number(self, full_name: str, system: str = "chaldean") -> Tuple[int, Dict]:
        """
        Calculate Destiny Number from name.
        Chaldean system is more mystical and accurate for names.
        
        Args:
            full_name: Full birth name
            system: "chaldean" or "pythagorean"
            
        Returns:
            Tuple of (destiny_number, details_dict)
        """
        # Select appropriate mapping
        mapping = self.chaldean_map if system == "chaldean" else self.pythagorean_map
        
        # Clean name: uppercase, remove non-letters
        clean_name = ''.join(c.upper() for c in full_name if c.isalpha())
        
        # Calculate total
        letter_values = []
        total = 0
        for letter in clean_name:
            value = mapping.get(letter, 0)
            letter_values.append(f"{letter}={value}")
            total += value
        
        # Reduce to single digit
        destiny = self._reduce_to_single_digit(total)
        
        details = {
            "number": destiny,
            "ruler": self.number_rulers.get(destiny, "Unknown"),
            "meaning": self.number_meanings.get(destiny, "Unknown"),
            "system": system.capitalize(),
            "name": full_name,
            "clean_name": clean_name,
            "calculation": f"{' + '.join(letter_values[:10])}{'...' if len(letter_values) > 10 else ''} = {total}→{destiny}"
        }
        
        return destiny, details
    
    def analyze_full_profile(self, birth_date: datetime, full_name: str) -> Dict:
        """
        Generate complete numerology profile.
        
        Args:
            birth_date: Date of birth
            full_name: Full birth name
            
        Returns:
            Dictionary with all numerology calculations
        """
        life_path_num, life_path_details = self.calculate_life_path(birth_date)
        attitude_num, attitude_details = self.calculate_attitude_number(birth_date)
        destiny_num, destiny_details = self.calculate_destiny_number(full_name, "chaldean")
        
        profile = {
            "life_path": life_path_details,
            "attitude": attitude_details,
            "destiny": destiny_details,
            "summary": {
                "core_numbers": [life_path_num, destiny_num, attitude_num],
                "dominant_rulers": self._get_dominant_rulers([life_path_num, destiny_num, attitude_num]),
                "alignment_strength": self._calculate_alignment(life_path_num, destiny_num, attitude_num)
            }
        }
        
        return profile
    
    def _get_dominant_rulers(self, numbers: list) -> list:
        """
        Identify which planetary rulers appear most frequently.
        
        Args:
            numbers: List of numerology numbers
            
        Returns:
            List of dominant planetary rulers
        """
        ruler_count = {}
        for num in numbers:
            ruler = self.number_rulers.get(num, "Unknown")
            # Handle master number compound rulers
            rulers = ruler.split('/')
            for r in rulers:
                r = r.strip()
                ruler_count[r] = ruler_count.get(r, 0) + 1
        
        # Get rulers that appear more than once
        dominant = [ruler for ruler, count in ruler_count.items() if count > 1]
        return dominant if dominant else list(ruler_count.keys())
    
    def _calculate_alignment(self, life_path: int, destiny: int, attitude: int) -> str:
        """
        Calculate how well aligned the numbers are.
        
        Args:
            life_path: Life Path number
            destiny: Destiny number
            attitude: Attitude number
            
        Returns:
            Alignment strength description
        """
        # All three same = perfect
        if life_path == destiny == attitude:
            return "Perfect (All Same)"
        
        # Any two same = strong
        if life_path == destiny or life_path == attitude or destiny == attitude:
            return "Strong (Two Match)"
        
        # Check if rulers match
        rulers = [self.number_rulers.get(n, "") for n in [life_path, destiny, attitude]]
        if len(set(rulers)) < 3:
            return "Moderate (Rulers Align)"
        
        return "Diverse (Varied Influences)"
    
    def check_astrological_harmony(self, numerology_profile: Dict, sun_sign: str, 
                                   ascendant_sign: str = None) -> Dict:
        """
        Check harmony between numerology and astrology.
        Used to boost confidence when both systems agree.
        
        Args:
            numerology_profile: Result from analyze_full_profile()
            sun_sign: Astrological sun sign
            ascendant_sign: Optional ascendant/rising sign
            
        Returns:
            Dictionary with harmony analysis
        """
        # Map signs to ruling planets
        sign_rulers = {
            "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
            "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
            "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
            "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
        }
        
        sun_ruler = sign_rulers.get(sun_sign, "Unknown")
        ascendant_ruler = sign_rulers.get(ascendant_sign, "Unknown") if ascendant_sign else None
        
        # Get numerology rulers
        num_rulers = numerology_profile["summary"]["dominant_rulers"]
        
        # Check matches
        matches = []
        if sun_ruler in num_rulers:
            matches.append(f"Sun ({sun_sign}) matches numerology ruler {sun_ruler}")
        if ascendant_ruler and ascendant_ruler in num_rulers:
            matches.append(f"Ascendant ({ascendant_sign}) matches numerology ruler {ascendant_ruler}")
        
        harmony_score = len(matches)
        confidence_multiplier = 1.0 + (harmony_score * 0.5)  # 1.5x for 1 match, 2.0x for 2 matches
        
        return {
            "harmony_score": harmony_score,
            "matches": matches,
            "confidence_multiplier": confidence_multiplier,
            "verdict": "Strong Harmony" if harmony_score >= 1 else "Divergent Paths"
        }
