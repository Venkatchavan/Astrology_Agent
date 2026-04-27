"""
Numerology Expert Agent - Phase 5
=================================
Interprets numerology numbers and provides tags for cross-verification with astrology.
"""

from datetime import datetime
from typing import Dict, List


class NumerologyExpert:
    """
    Expert agent for numerological interpretation.
    Provides detailed meanings and checks harmony with astrological indicators.
    """
    
    def __init__(self):
        """Initialize the numerology expert."""
        # Expanded interpretations for each number
        self.interpretations = {
            1: {
                "archetype": "The Leader",
                "planet": "Sun",
                "element": "Fire",
                "keywords": ["Independent", "Pioneer", "Ambitious", "Original", "Confident"],
                "strengths": ["Natural leadership", "Initiative", "Courage", "Innovation"],
                "challenges": ["Egotism", "Dominance", "Impatience", "Stubbornness"],
                "career": ["Entrepreneur", "Executive", "Inventor", "Solo Professional"],
                "spiritual": "Learning to balance self-assertion with cooperation"
            },
            2: {
                "archetype": "The Diplomat",
                "planet": "Moon",
                "element": "Water",
                "keywords": ["Sensitive", "Cooperative", "Intuitive", "Peaceful", "Supportive"],
                "strengths": ["Partnership skills", "Empathy", "Mediation", "Harmony"],
                "challenges": ["Over-sensitivity", "Indecision", "Dependency", "Shyness"],
                "career": ["Counselor", "Team Player", "Diplomat", "Caregiver"],
                "spiritual": "Learning to trust inner voice while supporting others"
            },
            3: {
                "archetype": "The Creative Communicator",
                "planet": "Jupiter",
                "element": "Fire",
                "keywords": ["Expressive", "Optimistic", "Social", "Artistic", "Joyful"],
                "strengths": ["Communication", "Creativity", "Enthusiasm", "Inspiration"],
                "challenges": ["Scattered energy", "Superficiality", "Gossip", "Extravagance"],
                "career": ["Artist", "Writer", "Speaker", "Entertainer", "Teacher"],
                "spiritual": "Learning to focus creative energy and speak truth"
            },
            4: {
                "archetype": "The Builder",
                "planet": "Rahu/Uranus",
                "element": "Earth",
                "keywords": ["Practical", "Organized", "Disciplined", "Loyal", "Systematic"],
                "strengths": ["Hard work", "Reliability", "Structure", "Endurance"],
                "challenges": ["Rigidity", "Limitation", "Resistance to change", "Dullness"],
                "career": ["Architect", "Engineer", "Manager", "Accountant", "Planner"],
                "spiritual": "Learning to build lasting foundations while embracing change"
            },
            5: {
                "archetype": "The Freedom Seeker",
                "planet": "Mercury",
                "element": "Air",
                "keywords": ["Versatile", "Adventurous", "Curious", "Dynamic", "Resourceful"],
                "strengths": ["Adaptability", "Quick thinking", "Communication", "Freedom"],
                "challenges": ["Restlessness", "Impulsiveness", "Irresponsibility", "Excess"],
                "career": ["Traveler", "Sales", "Media", "Marketing", "Entertainer"],
                "spiritual": "Learning to balance freedom with commitment"
            },
            6: {
                "archetype": "The Nurturer",
                "planet": "Venus",
                "element": "Earth",
                "keywords": ["Responsible", "Caring", "Harmonious", "Artistic", "Family-oriented"],
                "strengths": ["Service", "Compassion", "Balance", "Aesthetics"],
                "challenges": ["Martyrdom", "Interference", "Perfectionism", "Worry"],
                "career": ["Healer", "Teacher", "Counselor", "Artist", "Home-maker"],
                "spiritual": "Learning to serve without sacrificing self"
            },
            7: {
                "archetype": "The Seeker",
                "planet": "Ketu/Neptune",
                "element": "Water",
                "keywords": ["Analytical", "Spiritual", "Introspective", "Wise", "Reserved"],
                "strengths": ["Deep thinking", "Research", "Intuition", "Perfection"],
                "challenges": ["Isolation", "Skepticism", "Aloofness", "Criticism"],
                "career": ["Researcher", "Analyst", "Philosopher", "Scientist", "Mystic"],
                "spiritual": "Learning to share wisdom while honoring inner truth"
            },
            8: {
                "archetype": "The Authority",
                "planet": "Saturn",
                "element": "Earth",
                "keywords": ["Powerful", "Ambitious", "Authoritative", "Material", "Executive"],
                "strengths": ["Business acumen", "Organization", "Achievement", "Power"],
                "challenges": ["Materialism", "Workaholism", "Control", "Ruthlessness"],
                "career": ["CEO", "Banker", "Judge", "Politician", "Manager"],
                "spiritual": "Learning to balance material success with spiritual values"
            },
            9: {
                "archetype": "The Humanitarian",
                "planet": "Mars",
                "element": "Fire",
                "keywords": ["Compassionate", "Idealistic", "Generous", "Artistic", "Universal"],
                "strengths": ["Humanitarianism", "Wisdom", "Completion", "Tolerance"],
                "challenges": ["Martyrdom", "Emotional turmoil", "Impracticality", "Loss"],
                "career": ["Humanitarian", "Artist", "Healer", "Teacher", "Philanthropist"],
                "spiritual": "Learning to let go and embrace universal love"
            },
            11: {
                "archetype": "The Intuitive Visionary",
                "planet": "Moon/Uranus",
                "element": "Air",
                "keywords": ["Intuitive", "Inspirational", "Idealistic", "Sensitive", "Illuminating"],
                "strengths": ["Psychic ability", "Vision", "Inspiration", "Enlightenment"],
                "challenges": ["Nervous energy", "Impracticality", "Fanaticism", "Delusion"],
                "career": ["Spiritual teacher", "Inventor", "Artist", "Psychic", "Visionary"],
                "spiritual": "Master Number: Channeling higher consciousness to uplift humanity"
            },
            22: {
                "archetype": "The Master Builder",
                "planet": "Saturn/Master",
                "element": "Earth",
                "keywords": ["Masterful", "Practical visionary", "Large-scale", "Powerful", "Transformative"],
                "strengths": ["Manifestation", "Grand vision", "Practical spirituality", "Impact"],
                "challenges": ["Overwhelming responsibility", "Self-doubt", "Pressure", "Burnout"],
                "career": ["World leader", "Architect of change", "Master builder", "Visionary CEO"],
                "spiritual": "Master Number: Building dreams into physical reality on grand scale"
            },
            33: {
                "archetype": "The Master Teacher",
                "planet": "Jupiter/Master",
                "element": "Fire",
                "keywords": ["Compassionate", "Healing", "Teaching", "Selfless", "Nurturing"],
                "strengths": ["Universal love", "Healing ability", "Teaching", "Service"],
                "challenges": ["Martyrdom", "Over-giving", "Emotional burden", "Self-neglect"],
                "career": ["Spiritual teacher", "Healer", "Guru", "Humanitarian leader"],
                "spiritual": "Master Number: Embodying Christ consciousness, healing through love"
            }
        }
    
    def interpret_number(self, number: int, number_type: str) -> Dict:
        """
        Get detailed interpretation for a specific number.
        
        Args:
            number: Numerology number (1-9, 11, 22, 33)
            number_type: Type of number ("life_path", "destiny", "attitude")
            
        Returns:
            Dictionary with interpretation details
        """
        base_interpretation = self.interpretations.get(number, {})
        
        # Context-specific additions
        context = {}
        if number_type == "life_path":
            context = {
                "context": "Core Life Purpose",
                "focus": "This number reveals your fundamental life mission and lessons"
            }
        elif number_type == "destiny":
            context = {
                "context": "Soul Expression",
                "focus": "This number shows how your soul desires to express in the world"
            }
        elif number_type == "attitude":
            context = {
                "context": "Outward Personality",
                "focus": "This number reveals how others perceive you initially"
            }
        
        return {**base_interpretation, **context}
    
    def generate_profile_tags(self, numerology_profile: Dict) -> Dict:
        """
        Generate interpretive tags from numerology profile.
        Used for cross-verification with astrology.
        
        Args:
            numerology_profile: Result from NumerologyEngine.analyze_full_profile()
            
        Returns:
            Dictionary with interpretive tags
        """
        life_path = numerology_profile["life_path"]["number"]
        destiny = numerology_profile["destiny"]["number"]
        attitude = numerology_profile["attitude"]["number"]
        
        tags = {
            "life_path": {
                "number": life_path,
                "ruler": numerology_profile["life_path"]["ruler"],
                "meaning": numerology_profile["life_path"]["meaning"],
                "archetype": self.interpretations.get(life_path, {}).get("archetype", "Unknown"),
                "element": self.interpretations.get(life_path, {}).get("element", "Unknown")
            },
            "destiny": {
                "number": destiny,
                "ruler": numerology_profile["destiny"]["ruler"],
                "meaning": numerology_profile["destiny"]["meaning"],
                "archetype": self.interpretations.get(destiny, {}).get("archetype", "Unknown"),
                "element": self.interpretations.get(destiny, {}).get("element", "Unknown")
            },
            "attitude": {
                "number": attitude,
                "ruler": numerology_profile["attitude"]["ruler"],
                "meaning": numerology_profile["attitude"]["meaning"],
                "archetype": self.interpretations.get(attitude, {}).get("archetype", "Unknown"),
                "element": self.interpretations.get(attitude, {}).get("element", "Unknown")
            },
            "synthesis": self._synthesize_numbers(life_path, destiny, attitude)
        }
        
        return tags
    
    def _synthesize_numbers(self, life_path: int, destiny: int, attitude: int) -> Dict:
        """
        Synthesize the three main numbers into overall pattern.
        
        Args:
            life_path: Life Path number
            destiny: Destiny number
            attitude: Attitude number
            
        Returns:
            Synthesis dictionary
        """
        all_numbers = [life_path, destiny, attitude]
        
        # Check for master numbers
        master_present = any(n in [11, 22, 33] for n in all_numbers)
        
        # Get dominant elements
        elements = []
        for num in all_numbers:
            elem = self.interpretations.get(num, {}).get("element")
            if elem:
                elements.append(elem)
        
        element_counts = {}
        for elem in elements:
            element_counts[elem] = element_counts.get(elem, 0) + 1
        
        dominant_element = max(element_counts, key=element_counts.get) if element_counts else "Balanced"
        
        # Pattern analysis
        patterns = []
        if life_path == destiny == attitude:
            patterns.append("Triple Emphasis: Extremely focused life purpose")
        elif life_path == destiny:
            patterns.append("Life Path = Destiny: Inner and outer alignment")
        elif life_path == attitude:
            patterns.append("Life Path = Attitude: Authentic presentation")
        elif destiny == attitude:
            patterns.append("Destiny = Attitude: Soul expression matches persona")
        
        if master_present:
            patterns.append("Master Number Present: Higher spiritual calling")
        
        # Numerical relationships
        if abs(life_path - destiny) == 1:
            patterns.append("Sequential Numbers: Progressive development")
        
        return {
            "dominant_element": dominant_element,
            "master_number_present": master_present,
            "patterns": patterns,
            "overall_theme": self._get_overall_theme(all_numbers, dominant_element)
        }
    
    def _get_overall_theme(self, numbers: List[int], dominant_element: str) -> str:
        """
        Determine overall life theme from number combination.
        
        Args:
            numbers: List of main numbers
            dominant_element: Dominant element
            
        Returns:
            Overall theme description
        """
        avg = sum(numbers) / len(numbers)
        
        themes = {
            "Fire": "Dynamic action and creative expression",
            "Earth": "Practical manifestation and material mastery",
            "Air": "Intellectual exploration and communication",
            "Water": "Emotional depth and intuitive wisdom",
            "Balanced": "Versatile integration of multiple paths"
        }
        
        element_theme = themes.get(dominant_element, "Multi-faceted development")
        
        # Add intensity indicator
        if avg <= 3:
            return f"Early Stage: {element_theme} with foundational focus"
        elif avg <= 6:
            return f"Middle Stage: {element_theme} with balanced development"
        else:
            return f"Advanced Stage: {element_theme} with spiritual emphasis"
    
    def check_harmony_with_astrology(self, numerology_tags: Dict, 
                                    astrological_indicators: Dict) -> Dict:
        """
        Check for harmony between numerology and astrology.
        Doubles confidence score when both systems agree.
        
        Args:
            numerology_tags: Tags from generate_profile_tags()
            astrological_indicators: Dict with keys like "sun_ruler", "dominant_element", etc.
            
        Returns:
            Harmony analysis with confidence multiplier
        """
        harmony_points = []
        confidence_boost = 0.0
        
        # Check planetary ruler matches
        num_rulers = [
            numerology_tags["life_path"]["ruler"],
            numerology_tags["destiny"]["ruler"],
            numerology_tags["attitude"]["ruler"]
        ]
        
        astro_sun_ruler = astrological_indicators.get("sun_ruler")
        astro_moon_ruler = astrological_indicators.get("moon_ruler")
        astro_ascendant_ruler = astrological_indicators.get("ascendant_ruler")
        
        if astro_sun_ruler and any(astro_sun_ruler in ruler for ruler in num_rulers):
            harmony_points.append(f"Sun ruler {astro_sun_ruler} matches numerology")
            confidence_boost += 0.5
        
        if astro_moon_ruler and any(astro_moon_ruler in ruler for ruler in num_rulers):
            harmony_points.append(f"Moon ruler {astro_moon_ruler} matches numerology")
            confidence_boost += 0.3
        
        if astro_ascendant_ruler and any(astro_ascendant_ruler in ruler for ruler in num_rulers):
            harmony_points.append(f"Ascendant ruler {astro_ascendant_ruler} matches numerology")
            confidence_boost += 0.3
        
        # Check element matches
        num_dominant_element = numerology_tags["synthesis"]["dominant_element"]
        astro_dominant_element = astrological_indicators.get("dominant_element")
        
        if astro_dominant_element and num_dominant_element == astro_dominant_element:
            harmony_points.append(f"Element {num_dominant_element} matches in both systems")
            confidence_boost += 0.4
        
        # Check archetype matches
        life_path_archetype = numerology_tags["life_path"]["archetype"]
        astro_archetype = astrological_indicators.get("sun_archetype")
        
        # Simple keyword matching for archetypes
        if astro_archetype:
            keywords = ["Leader", "Diplomat", "Creative", "Builder", "Freedom", 
                       "Nurturer", "Seeker", "Authority", "Humanitarian"]
            for keyword in keywords:
                if keyword in life_path_archetype and keyword in astro_archetype:
                    harmony_points.append(f"Archetype '{keyword}' present in both systems")
                    confidence_boost += 0.5
                    break
        
        # Calculate final multiplier (minimum 1.0, can go up to 3.0+)
        confidence_multiplier = 1.0 + confidence_boost
        
        verdict = "Strong Harmony" if len(harmony_points) >= 2 else \
                 "Moderate Harmony" if len(harmony_points) == 1 else \
                 "Divergent Paths (Both Valid)"
        
        return {
            "harmony_points": harmony_points,
            "harmony_count": len(harmony_points),
            "confidence_multiplier": round(confidence_multiplier, 2),
            "verdict": verdict,
            "interpretation": self._interpret_harmony_level(len(harmony_points))
        }
    
    def _interpret_harmony_level(self, harmony_count: int) -> str:
        """
        Interpret the level of harmony between systems.
        
        Args:
            harmony_count: Number of harmony points found
            
        Returns:
            Interpretation string
        """
        if harmony_count >= 3:
            return "Exceptional alignment. Astrology and numerology powerfully reinforce the same life themes. This indicates a highly focused incarnation with clear purpose."
        elif harmony_count == 2:
            return "Strong alignment. Both systems point to similar life lessons and qualities. The core message is consistent across modalities."
        elif harmony_count == 1:
            return "Moderate alignment. Some shared themes exist, but each system reveals different facets of the soul's journey."
        else:
            return "Divergent paths. This indicates a multi-dimensional soul with diverse lessons. Each system reveals a different aspect of your complexity."
