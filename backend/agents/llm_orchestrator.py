"""
LLM ORCHESTRATOR - Local LLM Integration with Mistral via Ollama
Falls back to rule-based resolution if LLM unavailable
"""

import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
import json


class LLMOrchestrator:
    """
    Local LLM orchestrator using Mistral via Ollama
    Falls back to rule-based resolution if LLM unavailable
    """

    def __init__(
        self, base_url: str = "http://localhost:11434", model: str = "mistral:latest"
    ):
        self.base_url = base_url
        self.model = "mistral:latest"
        self._available = None
        self._check_availability()

    def _check_availability(self):
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            self._available = response.status_code == 200
            if self._available:
                print(f"LLM Orchestrator: Mistral available at {self.base_url}")
            else:
                print(
                    f"LLM Orchestrator: Ollama not responding, using rule-based fallback"
                )
        except Exception as e:
            self._available = False
            print(f"LLM Orchestrator: Ollama not available, using rule-based fallback")

    @property
    def is_available(self) -> bool:
        self._check_availability()
        return self._available or False

    def generate_unified_advice(
        self, context: Dict[str, Any], use_llm: bool = True
    ) -> Dict[str, Any]:
        """
        Generate unified advice from all agent outputs
        Uses LLM if available and use_llm=True, otherwise rule-based
        """
        if use_llm and self.is_available:
            return self._generate_with_llm(context)
        else:
            return self._generate_rule_based(context)

    def _generate_with_llm(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Use Mistral LLM for unified reasoning"""
        prompt = self._build_llm_prompt(context)

        print("🧠 Sending data to local Mistral LLM via Ollama...")
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 256},
                },
                timeout=120,
            )

            if response.status_code == 200:
                result = response.json()
                print("✅ Mistral successfully generated multi-agent advice!")
                return {
                    "source": "llm",
                    "model": self.model,
                    "advice": result.get("response", "").strip(),
                    "confidence": "high",
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                print(f"⚠️ Ollama returned error status: {response.status_code}")
        except Exception as e:
            print(f"❌ LLM call failed. Falling back to rule-based. Error: {str(e)[:100]}")

        return self._generate_rule_based(context)

    def _build_llm_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for LLM"""
        return f"""<s>[INST] You are an agricultural expert AI. Analyze the following farm data from multiple AI agents and provide unified farming advice.

CONTEXT (Agent Context Bus - shared_context):
{json.dumps(context, indent=2)}

Based on this data:
1. Identify any conflicts between agent recommendations
2. Resolve conflicts logically using these rules:
   - If rain_in_24h == True -> Avoid fertilizer
   - If disease_alert == True -> Prioritize disease treatment
   - If both conflict -> Choose safest action for farmer

Output your final response exactly in the following format:
1. 📊 Agent Outputs Summary
(Briefly summarize what each agent suggested)
2. 🧠 Shared Context
(List the key context values used for decision making)
3. ⚖️ Conflict Resolution Explanation
(Explain how conflicts were resolved based on the rules)
4. ✅ Final Recommendation (clear, single decision)
(What the farmer should do NOW)
[/INST]"""

    def _generate_rule_based(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Rule-based fallback for unified advice"""
        advice_points = []
        priority = "normal"

        # Critical checks (highest priority)
        if (
            context.get("disease_alert")
            and context.get("risk_level") == "high"
        ):
            advice_points.append(
                "🚨 CRITICAL: Disease detected - prioritize treatment immediately"
            )
            priority = "critical"

        soil_moisture = context.get("soil_moisture", 0)
        if soil_moisture < 25 and soil_moisture > 0:
            advice_points.append(
                "🚨 CRITICAL: Soil moisture critically low - irrigate immediately"
            )
            priority = "critical"

        temperature = context.get("temperature", 0)
        if temperature > 42:
            advice_points.append(
                "🚨 CRITICAL: Extreme heat - increase water immediately"
            )
            priority = "critical"

        # High priority checks
        rain_in_24h = context.get("rain_in_24h", False)
        if rain_in_24h:
            advice_points.append(
                "⏸️ Rain expected in 24h - avoid fertilizer"
            )

        humidity = context.get("humidity", 0)
        disease_alert = context.get("disease_alert", False)
        if humidity > 85 and disease_alert:
            advice_points.append(
                "🌫️ High humidity + disease risk - spray only morning/evening"
            )

        # Medium priority
        fertilizer_advice = context.get("fertilizer_advice", "")
        disease_severity = context.get("risk_level", "none")

        if "recommended" in fertilizer_advice.lower() and not rain_in_24h:
            if disease_severity != "high":
                advice_points.append(
                    "🌱 Fertilizer recommended - apply according to schedule"
                )

        irrigation_needed = context.get("irrigation_needed", False)
        if irrigation_needed and not rain_in_24h:
            if soil_moisture < 80:
                duration = context.get("irrigation_duration", 30)
                advice_points.append(
                    f"💧 Irrigation needed - run for {duration} minutes"
                )

        # Good conditions check
        if (
            40 <= soil_moisture <= 70
            and 15 <= temperature <= 35
            and not context.get("disease_alert")
            and not rain_in_24h
        ):
            advice_points.append("✅ Conditions optimal - maintain current practices")

        final_recommendation = " | ".join(advice_points) if advice_points else "All systems normal"
        
        # Build structured response format as fallback
        formatted_advice = (
            "1. 📊 Agent Outputs Summary\n"
            f"- Weather: Rain expected = {context.get('rain_in_24h', False)}\n"
            f"- Disease: Alert = {context.get('disease_alert', False)}\n"
            f"- Fertilizer: {context.get('fertilizer_advice', 'No advice')}\n\n"
            "2. 🧠 Shared Context\n"
            + json.dumps(context, indent=2) + "\n\n"
            "3. ⚖️ Conflict Resolution Explanation\n"
            "Rule-based fallback applied. Prioritized disease treatment and/or postponed sensitive activities if raining.\n\n"
            "4. ✅ Final Recommendation\n"
            + final_recommendation
        )

        return {
            "source": "rule_based",
            "advice": formatted_advice,
            "priority": priority,
            "confidence": "medium",
            "timestamp": datetime.now().isoformat(),
            "rules_applied": self._get_applied_rules(context),
        }

    def _get_applied_rules(self, context: Dict[str, Any]) -> List[str]:
        """List which rules were applied"""
        rules = []

        if context.get("rain_in_24h", False):
            rules.append("rain_delay")
        if context.get("risk_level") == "high":
            rules.append("disease_priority")
        if context.get("temperature", 0) > 40:
            rules.append("heat_irrigation_timing")
        if context.get("soil_moisture", 0) > 80:
            rules.append("saturation_skip")
        if context.get("nitrogen", 0) > 250:
            rules.append("npk_excess_skip")

        return rules
