"""
Dasha Engine - Vimshottari Dasha System
Calculates the 120-year planetary period system used in Vedic astrology.
"""

from datetime import datetime, timedelta
from typing import Dict, List


class DashaEngine:
    """
    Calculates Vimshottari Dasha system (120-year cycle).
    Logic: Determines Dasha balance from Moon's Nakshatra position.
    """
    
    def __init__(self):
        # Standard Vimshottari Years
        self.dasha_periods = {
            "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
            "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17
        }
        # Cyclic Order: Ketu -> Venus -> ... -> Mercury -> Repeat
        self.dasha_order = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]

    def calculate_dasha_balance(self, moon_longitude_deg: float, birth_date: datetime) -> Dict:
        """
        Returns the starting Dasha and the balance remaining at birth.
        
        Args:
            moon_longitude_deg: Sidereal longitude of Moon (0-360)
            birth_date: Date and time of birth (UTC)
        
        Returns:
            Dictionary with ruler, balance string, end date, and remaining fraction
        """
        # 1. Nakshatra Geometry (13 deg 20 min = 13.3333 deg)
        nakshatra_span = 13 + (1/3)
        
        # 2. Position Calculation
        # How far is the moon into the zodiac?
        nakshatra_index_float = moon_longitude_deg / nakshatra_span
        nakshatra_index = int(nakshatra_index_float)  # 0 to 26
        
        # 3. Traversal within specific Nakshatra
        traversed_deg = moon_longitude_deg % nakshatra_span
        remaining_deg = nakshatra_span - traversed_deg
        fraction_remaining = remaining_deg / nakshatra_span
        
        # 4. Identify Ruler
        # Sequence repeats every 9 nakshatras (Ashwini=Ketu, Magha=Ketu, Mula=Ketu)
        ruler_index = nakshatra_index % 9
        ruler_name = self.dasha_order[ruler_index]
        full_years = self.dasha_periods[ruler_name]
        
        # 5. Calculate Balance Time
        balance_years_float = full_years * fraction_remaining
        
        # Helper to convert float years to Y/M/D
        b_years = int(balance_years_float)
        b_months = int((balance_years_float - b_years) * 12)
        b_days = int(((balance_years_float - b_years) * 12 - b_months) * 30.4375)  # More accurate month length
        
        # More precise date calculation using months
        total_days = balance_years_float * 365.2422  # Tropical year length
        end_date = birth_date + timedelta(days=total_days)
        
        return {
            "ruler": ruler_name,
            "balance_str": f"{b_years}y {b_months}m {b_days}d",
            "balance_years": balance_years_float,
            "start_date": birth_date,
            "end_date": end_date,
            "remaining_fraction": fraction_remaining
        }

    def generate_mahadasha_schedule(self, balance_obj: Dict, years_to_generate: int = 100) -> List[Dict]:
        """
        Generates the Mahadasha list starting from birth.
        
        Args:
            balance_obj: Result from calculate_dasha_balance()
            years_to_generate: How many years into future to calculate
        
        Returns:
            List of Mahadasha periods with lord, start, end dates
        """
        schedule = []
        current_date = balance_obj["end_date"]
        
        # 1. Add the first (Balance) Dasha
        schedule.append({
            "lord": balance_obj["ruler"],
            "start": balance_obj["start_date"],
            "end": balance_obj["end_date"],
            "type": "Balance"
        })
        
        # 2. Find index of current ruler to determine next
        start_index = self.dasha_order.index(balance_obj["ruler"])
        
        # 3. Loop for next Dashas
        loop_index = (start_index + 1) % 9
        years_covered = balance_obj["balance_years"]
        
        while years_covered < years_to_generate:
            lord = self.dasha_order[loop_index]
            years = self.dasha_periods[lord]
            
            end_date = current_date + timedelta(days=years * 365.2422)
            
            schedule.append({
                "lord": lord,
                "start": current_date,
                "end": end_date,
                "type": "Full"
            })
            
            # Prepare for next
            current_date = end_date
            years_covered += years
            loop_index = (loop_index + 1) % 9
            
        return schedule

    def generate_antardashas(self, mahadasha_lord: str, start_date: datetime) -> List[Dict]:
        """
        Calculates Antardashas (Sub-periods) for a given Mahadasha Lord.
        Rule: SubPeriod = (MajorYears * SubYears) / 120
        Order: Starts with the Mahadasha Lord and follows sequence.
        
        Args:
            mahadasha_lord: Name of the Mahadasha lord
            start_date: Start date of the Mahadasha
        
        Returns:
            List of Antardasha periods
        """
        sub_schedule = []
        current_date = start_date
        major_years = self.dasha_periods[mahadasha_lord]
        
        # Start sequence from the Mahadasha Lord
        start_index = self.dasha_order.index(mahadasha_lord)
        
        for i in range(9):
            sub_lord_idx = (start_index + i) % 9
            sub_lord = self.dasha_order[sub_lord_idx]
            sub_years_val = self.dasha_periods[sub_lord]
            
            # Formula: Years = (Major * Sub) / 120
            period_years = (major_years * sub_years_val) / 120.0
            
            end_date = current_date + timedelta(days=period_years * 365.2422)
            
            sub_schedule.append({
                "sub_lord": sub_lord,
                "start": current_date,
                "end": end_date
            })
            current_date = end_date
            
        return sub_schedule

    def get_current_dasha(self, moon_lon: float, birth_date: datetime, current_date: datetime = None) -> Dict:
        """
        Determines which Mahadasha and Antardasha is running RIGHT NOW.
        
        Args:
            moon_lon: Moon's longitude at birth
            birth_date: Date of birth
            current_date: Date to check (defaults to now)
        
        Returns:
            Dictionary with mahadasha, antardasha, and end date
        """
        if current_date is None:
            current_date = datetime.now()

        # 1. Start with Birth Balance
        balance = self.calculate_dasha_balance(moon_lon, birth_date)
        
        # If we are still in the first dasha
        running_date = balance["end_date"]
        current_lord_idx = self.dasha_order.index(balance["ruler"])
        
        if current_date < running_date:
            return self._calculate_antardasha(balance["ruler"], birth_date, running_date, current_date)

        # 2. Loop forward until we find the current time
        while running_date < current_date:
            current_lord_idx = (current_lord_idx + 1) % 9
            lord_name = self.dasha_order[current_lord_idx]
            years = self.dasha_periods[lord_name]
            
            start_date = running_date
            running_date = start_date + timedelta(days=years * 365.2422)
            
            if current_date <= running_date:
                # We found the Mahadasha! Now find Antardasha
                return self._calculate_antardasha(lord_name, start_date, running_date, current_date)
        
        return {"mahadasha": "Unknown", "antardasha": "Unknown", "end_date": "N/A"}

    def _calculate_antardasha(self, md_lord: str, md_start: datetime, md_end: datetime, target_date: datetime) -> Dict:
        """
        Internal: Finds the sub-period within a Mahadasha.
        
        Args:
            md_lord: Mahadasha lord
            md_start: Start of Mahadasha
            md_end: End of Mahadasha
            target_date: Date to find Antardasha for
        
        Returns:
            Dictionary with mahadasha, antardasha, and end date
        """
        md_years = self.dasha_periods[md_lord]
        
        # Antardashas always start with the Mahadasha Lord
        ad_start_idx = self.dasha_order.index(md_lord)
        running_date = md_start
        
        for i in range(9):
            ad_lord = self.dasha_order[(ad_start_idx + i) % 9]
            ad_years = self.dasha_periods[ad_lord]
            
            # Formula: (Major * Sub) / 120 = SubPeriod Length in Years
            sub_length_years = (md_years * ad_years) / 120.0
            sub_end = running_date + timedelta(days=sub_length_years * 365.25)
            
            if target_date <= sub_end:
                return {
                    "mahadasha": md_lord,
                    "antardasha": ad_lord,
                    "start_date": running_date.strftime("%Y-%m-%d"),
                    "end_date": sub_end.strftime("%Y-%m-%d")
                }
            
            running_date = sub_end
            
        return {
            "mahadasha": md_lord,
            "antardasha": "End",
            "start_date": md_start.strftime("%Y-%m-%d"),
            "end_date": "N/A"
        }
