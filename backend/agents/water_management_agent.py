"""
💧 WATER MANAGEMENT AGENT
Smart irrigation scheduling and water optimization
"""

from typing import Dict, Any
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)


class WaterManagementAgent:
    # Constants (no magic numbers)
    MOISTURE_THRESHOLD = 40
    BASE_DURATION = 20  # minutes
    FLOW_RATE = 50  # liters per minute

    def __init__(self, database):
        self.db = database
        self.name = "Water Management Agent"

    def calculate_irrigation_need(
        self,
        sensor_data: Dict[str, Any],
        weather_forecast: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate irrigation requirements based on soil moisture, weather, and evaporation
        """

        result = {
            "agent": self.name,
            "timestamp": datetime.now().isoformat(),
            "should_irrigate": False,
            "duration_minutes": 0,
            "water_volume_liters": 0,
            "reason": "",
            "recommendations": []
        }

        try:
            # Sensor readings
            soil_moisture = sensor_data.get("soil_moisture", 50)
            air_temperature = sensor_data.get("air_temperature", 25)
            humidity = sensor_data.get("humidity", 60)

            # Weather forecast
            summary = weather_forecast.get("summary", {})
            rain_expected = summary.get("rain_expected", False)
            rain_probability = summary.get("avg_rain_probability", 0)

            # Decision logic
            if rain_expected and rain_probability > 60:
                result["reason"] = f"Rain expected ({rain_probability}% probability) - irrigation postponed"
                result["recommendations"].append("Monitor soil moisture after rainfall")

            elif soil_moisture < self.MOISTURE_THRESHOLD:
                result["should_irrigate"] = True

                moisture_deficit = self.MOISTURE_THRESHOLD - soil_moisture
                duration = self.BASE_DURATION + (moisture_deficit * 2)

                result["duration_minutes"] = int(duration)
                result["water_volume_liters"] = int(duration * self.FLOW_RATE)
                result["reason"] = f"Soil moisture low ({soil_moisture}%) - irrigation required"

                evap_risk = self._calculate_evaporation_risk(air_temperature, humidity)
                result["evaporation_risk"] = evap_risk

                if evap_risk == "high":
                    result["recommendations"].append(
                        "⏰ Irrigate early morning or evening to reduce evaporation"
                    )

                result["recommendations"].append(
                    f"💧 Apply {result['water_volume_liters']} liters over {result['duration_minutes']} minutes"
                )

            else:
                result["reason"] = f"Soil moisture adequate ({soil_moisture}%)"
                result["recommendations"].append("✓ No irrigation needed - monitor daily")

            # Schedule
            result["optimal_schedule"] = self._generate_irrigation_schedule()

            return result

        except Exception as e:
            logging.error(f"Error in calculate_irrigation_need: {e}")
            result["status"] = "error"
            result["error"] = str(e)
            return result

    def _calculate_evaporation_risk(self, temperature: float, humidity: float) -> str:
        """Calculate evaporation risk level"""

        if temperature > 35 and humidity < 40:
            return "high"
        elif temperature > 30 and humidity < 50:
            return "medium"
        return "low"

    def _generate_irrigation_schedule(self) -> Dict[str, Any]:
        """Generate week-long irrigation schedule"""

        schedule = {
            "next_7_days": [],
            "total_water_needed": 0,
            "frequency": "every_2_days"
        }

        days = ["Monday", "Wednesday", "Friday", "Sunday"]

        for day in days:
            schedule["next_7_days"].append({
                "day": day,
                "recommended_time": "06:00 AM",
                "duration_minutes": 30,
                "water_liters": 1500
            })

        schedule["total_water_needed"] = len(days) * 1500

        return schedule