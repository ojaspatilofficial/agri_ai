"""
📍 LIVE MANDI PRICE AGENT
Provides real-time nearby mandi (market) prices and insights.
"""
from typing import Dict, Any, List
import random
from datetime import datetime
import math

class LiveMandiAgent:
    def __init__(self):
        self.name = "Live Mandi Agent"
        
        # Base realistic prices per quintal (100 kg) for different crops
        self.base_prices = {
            "wheat": 2275,
            "rice": 2183,
            "cotton": 6620,
            "sugarcane": 315,
            "maize": 2090,
            "soybean": 4600,
            "tomato": 1500,
            "potato": 1200,
            "onion": 1800
        }
        
        # Simulated Mandi locations around a base region (e.g., Pune/Maharashtra bounds)
        self.mandi_db = [
            {"id": "m1", "name": "Pune APMC", "base_distance": 15, "premium": 1.05},
            {"id": "m2", "name": "Lasalgaon Mandi", "base_distance": 120, "premium": 0.95},
            {"id": "m3", "name": "Nashik APMC", "base_distance": 90, "premium": 0.98},
            {"id": "m4", "name": "Baramati Krishi Bazar", "base_distance": 45, "premium": 1.02},
            {"id": "m5", "name": "Solapur Mandi", "base_distance": 180, "premium": 0.90},
        ]
        
    def _calculate_trend(self) -> str:
        """Simulate a simple market trend."""
        trends = ["up", "down", "stable"]
        # Probabilities: 40% up, 30% down, 30% stable
        return random.choices(trends, weights=[40, 30, 30], k=1)[0]
        
    def _calculate_price_change(self) -> float:
        """Simulate price percentage change compared to yesterday."""
        return round(random.uniform(-5.0, 5.0), 2)

    def get_mandi_prices(self, crop: str, lat: float = None, lon: float = None) -> Dict[str, Any]:
        """
        Fetch real-time prices for a specific crop across nearby mandis.
        In a real-world scenario, this would call eNAM or data.gov.in API.
        """
        crop_lower = crop.lower()
        base_price = self.base_prices.get(crop_lower, 2000)  # Default metric if crop not found
        
        results = []
        for mandi in self.mandi_db:
            # Vary the distance slightly to simulate actual user location differences
            # If lat/lon are not provided, we just give randomized distances based on defaults
            distance_variance = random.uniform(0.8, 1.2)
            distance = round(mandi["base_distance"] * distance_variance, 1)
            
            # Premium logic: Closer, more demand mandis might offer slightly better or worse prices
            daily_fluctuation = random.uniform(0.95, 1.05)
            current_price = int(base_price * mandi["premium"] * daily_fluctuation)
            
            trend = self._calculate_trend()
            price_change = self._calculate_price_change()
            if trend == "up":
                price_change = abs(price_change)
            elif trend == "down":
                price_change = -abs(price_change)
            else:
                price_change = 0.0
                
            results.append({
                "mandi_id": mandi["id"],
                "mandi_name": mandi["name"],
                "distance_km": distance,
                "price_per_quintal": current_price,
                "currency": "INR",
                "trend": trend,
                "price_change_pct": price_change,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
        # Sort by best price (highest first)
        results = sorted(results, key=lambda x: x["price_per_quintal"], reverse=True)
        
        # Calculate best recommendation
        best_mandi = results[0]
        
        # Very simple transport cost heuristic: ₹15 per km per quintal avg rough estimate
        for r in results:
            r["est_transport_cost_per_q"] = round(r["distance_km"] * 15, 2)
            r["net_profit_per_q"] = r["price_per_quintal"] - r["est_transport_cost_per_q"]
            
        # Re-sort by best net profit
        results = sorted(results, key=lambda x: x["net_profit_per_q"], reverse=True)
        best_net_mandi = results[0]

        return {
            "agent": self.name,
            "crop": crop,
            "timestamp": datetime.now().isoformat(),
            "best_price_mandi": best_mandi["mandi_name"],
            "best_net_profit_mandi": best_net_mandi["mandi_name"],
            "mandis": results,
            "insight": f"Selling at {best_net_mandi['mandi_name']} yields the highest net profit after transport costs."
        }
