"""
Smart Farming Agentic AI System — Main Backend Server
=====================================================
FastAPI Application Entry Point
Consolidated Version: PostgreSQL + Async + Full Agent Suite + AI Vision
"""

# ── Mock broken opentelemetry dependency ──────────────────────────
import sys
from unittest.mock import MagicMock

sys.modules["opentelemetry"] = MagicMock()
sys.modules["opentelemetry.api"] = MagicMock()
sys.modules["opentelemetry.sdk"] = MagicMock()
sys.modules["opentelemetry.sdk._logs"] = MagicMock()
sys.modules["opentelemetry.sdk._logs._internal"] = MagicMock()

from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uvicorn
import json
import io
import os
import base64
import logging
import random
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from both .env files
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

logger = logging.getLogger(__name__)

# Import configuration
from config import API_CONFIG

# LangGraph modules (Agentic AI System)
from graph import run_farm_analysis, get_supervisor

# Core components
from core.database import AsyncDatabase
from core.auth_system import AuthSystem

# Keep voice assistant as separate UI layer
from agents.voice_assistant_agent import VoiceAssistantAgent

# FastAPI will be initialized later with lifespan

# Initialize components
db = AsyncDatabase(API_CONFIG["database_url"])
auth_system = AuthSystem(db)

# Initialize LangGraph supervisor (main agentic brain)
supervisor = get_supervisor()

# Initialize voice assistant
voice_agent = VoiceAssistantAgent(db)


# ── Request Models ──────────────────────────────────────────────────


class SensorDataRequest(BaseModel):
    farm_id: str = "FARM001"
    duration_minutes: int = 1


class VoiceCommandRequest(BaseModel):
    text: str
    language: str = "en"
    farm_id: str = "FARM001"


class SpeechRecognitionRequest(BaseModel):
    audio_base64: str
    language: str = "en"


class DiseaseDetectionRequest(BaseModel):
    image_data: Optional[str] = None
    crop_type: str = "wheat"
    symptoms: List[str] = []


class ImageDiseaseRequest(BaseModel):
    image_base64: str
    crop_type: str = "wheat"


class YieldPredictionRequest(BaseModel):
    crop_type: str
    area_hectares: float
    soil_quality: str = "medium"


class AgentQueryRequest(BaseModel):
    farm_id: str = "FARM001"
    query: str = "Analyze my farm and give recommendations"
    location: str = "Pune"
    crop_type: str = "wheat"


class ChatMessageRequest(BaseModel):
    message: str
    farm_id: str = "FARM001"
    history: List[Dict[str, str]] = []


class CropRequest(BaseModel):
    crop_type: str
    variety: Optional[str] = None
    planted_date: Optional[str] = None
    area_hectares: float = 1.0
    status: str = "growing"
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class CropStatusUpdate(BaseModel):
    status: str


class CopilotRequest(BaseModel):
    message: str
    farm_id: str = "FARM001"


class RegisterRequest(BaseModel):
    name: str
    email: str
    phone: str
    password: str
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    farm_size: Optional[float] = None
    language: str = "en"
    soil_type: Optional[str] = None
    irrigation_source: Optional[str] = None
    is_organic: Optional[bool] = False


class FarmDetailsRequest(BaseModel):
    total_land_area_acres: Optional[float] = None
    number_of_crops: Optional[int] = None
    crops_names: Optional[str] = None
    sowing_date: Optional[str] = None
    sowed_land_area_acres: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class LoginRequest(BaseModel):
    email: Optional[str] = None
    farmer_id: Optional[str] = None
    password: str


# ── Lifecycle Events ────────────────────────────────────────────────


from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    print("Initializing Smart Farming AI System...")
    await db.init_db()
    print("Database initialized")
    yield


app = FastAPI(
    title="AgroBrain OS - Agentic AI Farming System",
    description="LangGraph-powered Autonomous AI Agent for Precision Agriculture",
    version="3.0.0",
    lifespan=lifespan,
)


# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/run_agents")
async def run_agents(farm_id: str = "FARM001"):
    """Run all AI agents for a farm"""
    try:
        from graph import run_farm_analysis

        result = await run_farm_analysis(
            farm_id=farm_id,
            location="Pune",
            crop_type="wheat",
            user_query="Run full farm analysis",
        )

        return {
            "status": "success",
            "message": "All AI agents executed successfully",
            "data": result.get("data", {}),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/api/agent/run")
async def run_langgraph_agent(request: AgentQueryRequest):
    """Run full LangGraph autonomous workflow"""
    try:
        from graph import run_farm_analysis

        result = await run_farm_analysis(
            farm_id=request.farm_id,
            location=request.location,
            crop_type=request.crop_type,
            user_query=request.query,
        )

        # Save the recommendation to the database so the dashboard can fetch it
        if result.get("status") == "success" and result.get("data", {}).get(
            "final_advice"
        ):
            advice = result["data"]["final_advice"]
            await db.store_recommendation(
                {
                    "farm_id": request.farm_id,
                    "agent_name": "AgroBrain Auto Agent",
                    "recommendation_type": "farm_analysis",
                    "recommendation_text": advice,
                    "priority": result["data"].get("confidence", "high"),
                    "llm_source": "langgraph-supervisor",
                }
            )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agent/chat")
async def chat_with_agent(request: ChatMessageRequest):
    """
    Chat with the autonomous agent using natural language.
    Uses Groq LLM with tool access for intelligent responses.
    """
    try:
        from graph import get_supervisor

        supervisor = get_supervisor()

        if not supervisor.is_available:
            return {
                "status": "error",
                "response": "AI agent unavailable. Please configure GROQ_API_KEY.",
            }

        result = await supervisor.chat(message=request.message, history=request.history)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agent/query")
async def query_agent(request: AgentQueryRequest):
    """
    Query the agent with a specific question.
    Returns autonomous analysis using tools.
    """
    try:
        from graph import get_supervisor

        supervisor = get_supervisor()

        if not supervisor.is_available:
            return {
                "status": "error",
                "response": "Agent unavailable. Check GROQ_API_KEY.",
            }

        result = await supervisor.run_autonomous(
            user_query=request.query, farm_id=request.farm_id
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/simulate_sensors")
async def simulate_sensors(request: SensorDataRequest):
    """Generate mock sensor data for testing"""
    import random

    data = []
    for _ in range(request.duration_minutes):
        reading = {
            "farm_id": request.farm_id,
            "soil_moisture": 35.0 + random.uniform(-5, 5),
            "soil_temperature": 22.0 + random.uniform(-2, 2),
            "soil_ph": 6.5 + random.uniform(-0.5, 0.5),
            "npk_nitrogen": 150 + random.uniform(-20, 20),
            "npk_phosphorus": 45 + random.uniform(-5, 5),
            "npk_potassium": 180 + random.uniform(-20, 20),
            "humidity": 60.0 + random.uniform(-10, 10),
            "air_temperature": 25.0 + random.uniform(-5, 5),
        }
        data.append(reading)

    await db.store_sensor_data(data)
    return {"status": "success", "count": len(data)}


# ── Sensor Data Endpoints ───────────────────────────────────────────


@app.get("/sensors/{farm_id}")
async def get_sensors(farm_id: str, limit: int = 10):
    """Get sensor data for a farm"""
    try:
        readings = await db.get_latest_readings(farm_id, limit=limit)
        return {"farm_id": farm_id, "sensors": readings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Crop Management ─────────────────────────────────────────────────


class CropRequest(BaseModel):
    crop_type: str
    variety: Optional[str] = None
    planted_date: Optional[str] = None
    area_hectares: float = 1.0
    status: str = "growing"
    latitude: Optional[float] = None
    longitude: Optional[float] = None


@app.post("/crops")
async def add_crop(request: CropRequest, farm_id: str = "FARM001"):
    """Add a new crop"""
    try:
        data = request.dict()
        data["farm_id"] = farm_id
        crop_id = await db.store_crop(data)
        return {"status": "success", "crop_id": crop_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/crops")
async def get_crops(farm_id: str = "FARM001", status: Optional[str] = None):
    """Get all crops for a farm"""
    try:
        crops = await db.get_crops(farm_id)
        if status and status != "all":
            crops = [c for c in crops if c.get("status") == status]
        return {"farm_id": farm_id, "crops": crops}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/crops/{crop_id}/status")
async def update_crop_status(crop_id: int, status: str):
    try:
        await db.update_crop_status(crop_id, status)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/crops/{crop_id}")
async def update_crop(crop_id: int, request_data: Dict[str, Any]):
    try:
        await db.update_crop(crop_id, request_data)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/crops/{crop_id}")
async def delete_crop(crop_id: int):
    try:
        await db.delete_crop(crop_id)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Profile Endpoints ───────────────────────────────────────────────


class FarmDetailsRequest(BaseModel):
    farm_size: Optional[float] = None
    total_land_area_acres: Optional[float] = None
    number_of_crops: Optional[int] = None
    crops_names: Optional[str] = None
    sowing_date: Optional[str] = None
    sowed_land_area_acres: Optional[float] = None
    soil_type: Optional[str] = None
    irrigation_source: Optional[str] = None
    is_organic: Optional[bool] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


@app.get("/profile")
async def get_profile(farm_id: str = "FARM001"):
    """Get farmer profile"""
    profile = await auth_system.get_farmer_profile(farm_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return profile


@app.put("/profile/farm_details")
async def update_farm_details(request: FarmDetailsRequest, farm_id: str = "FARM001"):
    """Update farm details"""
    try:
        result = await auth_system.update_farm_details(farm_id, request.dict())
        if not result:
            raise HTTPException(status_code=404, detail="Farmer not found")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "success", "count": len(data)}


# ── Auth Endpoints ───────────────────────────────────────────────────


class LoginRequest(BaseModel):
    email: Optional[str] = None
    farmer_id: Optional[str] = None
    phone: Optional[str] = None
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: str
    phone: str
    password: str
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    farm_size: Optional[float] = None
    language: str = "en"
    soil_type: Optional[str] = None
    irrigation_source: Optional[str] = None
    is_organic: Optional[bool] = False


@app.post("/auth/login")
async def login(request: LoginRequest):
    identifier = request.email or request.farmer_id
    if not identifier:
        raise HTTPException(status_code=400, detail="Email or Farmer ID is required")

    result = await auth_system.login_farmer(identifier, request.password)
    if result["status"] == "failed":
        raise HTTPException(status_code=401, detail=result["message"])
    return result


@app.post("/auth/register")
async def register(request: RegisterRequest):
    try:
        farmer_id = await auth_system.register_farmer(
            name=request.name,
            email=request.email,
            phone=request.phone,
            password=request.password,
            location=request.location,
            latitude=request.latitude,
            longitude=request.longitude,
            farm_size=request.farm_size,
            language=request.language,
            soil_type=request.soil_type,
            irrigation_source=request.irrigation_source,
            is_organic=request.is_organic,
        )
        return {"status": "success", "farmer_id": farmer_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Specialized Feature Endpoints ───────────────────────────────────


@app.get("/get_weather")
async def get_weather(location: str = "Delhi"):
    from graph.tools import get_current_weather

    res = await get_current_weather.ainvoke(location)
    data = res.get("data", {})
    return {
        "location": location,
        "data_source": "OpenWeather API"
        if res.get("status") == "success"
        else "Simulated due to Error",
        "current": data
        if res.get("status") == "success"
        else {
            "temperature": 0,
            "humidity": 0,
            "wind_speed": 0,
            "cloud_cover": 0,
            "pressure": 0,
            "visibility": 0,
        },
    }


@app.get("/get_forecast")
async def get_forecast(location: str = "Delhi", hours: int = 24):
    from graph.tools import get_weather_forecast

    res = await get_weather_forecast.ainvoke({"location": location, "hours": hours})
    data = res.get("data", {})
    summary = data.get("summary", {})
    
    # Correct mapping for frontend
    formatted_summary = {
        "avg_temperature": round((summary.get("temp_min", 0) + summary.get("temp_max", 0)) / 2, 1),
        "max_temperature": summary.get("temp_max", 0),
        "max_rain_probability": data.get("avg_rain_probability", 0),
        "rain_expected": data.get("rain_expected", False)
    }

    return {
        "data_source": "OpenWeather API"
        if res.get("status") == "success"
        else "Simulated due to Error",
        "summary": formatted_summary,
        "risk_score": {"level": data.get("risk", "low"), "factors": []},
        "hourly_forecast": data.get("hourly_forecast", []),
        "recommendations": [
            "Monitor soil moisture" if data.get("rain_expected") else "Normal conditions",
            "Prepare for possible irrigation" if not data.get("rain_expected") else "Rain predicted"
        ],
    }


@app.get("/get_weather_advisory")
async def get_weather_advisory(location: str = "Pune", farm_id: str = "FARM001"):
    """
    Fetches 4-day weather forecast using LangGraph weather tool.
    """
    from graph.tools import get_weather_forecast

    forecast = await get_weather_forecast.ainvoke({"location": location, "hours": 96})
    return forecast

    # 2. Build per-day summaries from the 3-hour slots
    daily_summaries = {}
    for slot in forecast_raw.get("hourly_forecast", []):
        try:
            day_key = slot["time"][:10]  # "YYYY-MM-DD"
            if day_key not in daily_summaries:
                daily_summaries[day_key] = {
                    "date": day_key,
                    "temps": [],
                    "rain_probs": [],
                    "conditions": [],
                    "humidity": [],
                    "wind_speeds": [],
                }
            d = daily_summaries[day_key]
            d["temps"].append(slot.get("temperature", 0))
            d["rain_probs"].append(slot.get("rain_probability", 0))
            d["conditions"].append(slot.get("conditions", ""))
            d["humidity"].append(slot.get("humidity", 0))
            d["wind_speeds"].append(slot.get("wind_speed", 0))
        except Exception:
            continue

    # Collapse to 4 days max, compute day-level stats
    days = []
    for day_key in sorted(daily_summaries.keys())[:4]:
        d = daily_summaries[day_key]
        dominant_condition = (
            max(set(d["conditions"]), key=d["conditions"].count)
            if d["conditions"]
            else "Clear"
        )
        days.append(
            {
                "date": day_key,
                "max_temp": round(max(d["temps"]), 1) if d["temps"] else 0,
                "min_temp": round(min(d["temps"]), 1) if d["temps"] else 0,
                "avg_temp": round(sum(d["temps"]) / len(d["temps"]), 1)
                if d["temps"]
                else 0,
                "max_rain_prob": round(max(d["rain_probs"]), 1)
                if d["rain_probs"]
                else 0,
                "avg_humidity": round(sum(d["humidity"]) / len(d["humidity"]), 1)
                if d["humidity"]
                else 0,
                "avg_wind_speed": round(
                    sum(d["wind_speeds"]) / len(d["wind_speeds"]), 1
                )
                if d["wind_speeds"]
                else 0,
                "dominant_condition": dominant_condition,
                "rain_expected": max(d["rain_probs"]) > 50
                if d["rain_probs"]
                else False,
            }
        )

    if not days:
        return {
            "location": location,
            "daily_forecast": [],
            "advisory": "Weather forecast unavailable. Please configure your OpenWeather API key.",
            "risk_level": "unknown",
            "error": forecast_raw.get("error", "No forecast data"),
        }

    # 3. Get optional farm context to personalise advice (Using Smoothing for stability)
    sensor_ctx = {}
    try:
        readings = await db.get_latest_readings(farm_id, limit=10)
        if readings:
            m = sum([r.get("soil_moisture", 0) for r in readings]) / len(readings)
            p = sum([r.get("soil_ph", 7) for r in readings]) / len(readings)
            n = sum([r.get("npk_nitrogen", 0) for r in readings]) / len(readings)

            sensor_ctx = {
                "soil_moisture": round(m, 2),
                "soil_ph": round(p, 2),
                "npk_nitrogen": round(n, 2),
            }
    except Exception:
        pass

    crop_ctx = {}
    try:
        crops = await db.get_crops(farm_id)
        if crops:
            crop_ctx = {
                "crop_type": crops[0].get("crop_type", "unknown"),
                "status": crops[0].get("status", "growing"),
            }
    except Exception:
        pass

    # 4. Call Groq LLM for AI advisory — fully grounded in the real forecast data
    groq_client = (
        lead_agent.llm.groq_client
        if getattr(lead_agent.llm, "_groq_available", False)
        else None
    )

    advisory_text = None
    advisory_structured = None

    if groq_client:
        days_json = _json.dumps(days, indent=2)
        sensor_note = (
            f"Farm sensor context: {_json.dumps(sensor_ctx)}" if sensor_ctx else ""
        )
        crop_note = f"Current crop: {crop_ctx}" if crop_ctx else ""

        prompt = f"""You are an expert agricultural AI advisor.
Below is the REAL 4-day weather forecast for {location}.
{sensor_note}
{crop_note}

FORECAST DATA (do not ignore these numbers):
{days_json}

Based ONLY on this data, generate a JSON response in this exact schema:
{{
  "overall_outlook": "<1-2 sentence summary of the next 4 days weather>",
  "risk_level": "<low|medium|high|critical>",
  "risk_reason": "<specific reason tied to the forecast numbers>",
  "daily_advice": [
    {{
      "date": "<YYYY-MM-DD>",
      "condition_emoji": "<one weather emoji>",
      "key_advice": "<1 concrete farming action for this specific day>",
      "do": "<what to do>",
      "avoid": "<what NOT to do>"
    }}
  ],
  "critical_alerts": ["<alert if any dangerous conditions exist, else empty list>"],
  "best_farming_window": "<which day(s) are best for field operations and why>",
  "irrigation_recommendation": "<specific irrigation advice based on rain probability and temp>",
  "pesticide_spray_window": "<best window for spraying pesticides based on wind/rain forecast>"
}}

Return ONLY valid JSON. Do not add markdown or explanation."""

        try:
            response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=900,
            )
            raw = response.choices[0].message.content.strip()
            # Strip any markdown fences
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            advisory_structured = _json.loads(raw)
        except Exception as e:
            advisory_text = f"AI advisory temporarily unavailable: {str(e)}"

    # Fallback if Groq is not available or parsing failed
    if advisory_structured is None:
        has_rain = any(d["rain_expected"] for d in days)
        max_temp_overall = max(d["max_temp"] for d in days) if days else 0
        advisory_structured = {
            "overall_outlook": f"{'Rainy' if has_rain else 'Dry'} conditions expected over the next {len(days)} days with temperatures reaching {max_temp_overall}°C.",
            "risk_level": "high"
            if has_rain and max_temp_overall > 36
            else ("medium" if has_rain else "low"),
            "risk_reason": "Heavy rain probability detected"
            if has_rain
            else "Dry and warm conditions",
            "daily_advice": [
                {
                    "date": d["date"],
                    "condition_emoji": "🌧️" if d["rain_expected"] else "☀️",
                    "key_advice": "Postpone field operations, prepare drainage"
                    if d["rain_expected"]
                    else "Good day for field operations",
                    "do": "Drain fields, cover storage"
                    if d["rain_expected"]
                    else "Irrigate, spray, plough",
                    "avoid": "Spraying pesticides, ploughing"
                    if d["rain_expected"]
                    else "Over-irrigation",
                }
                for d in days
            ],
            "critical_alerts": ["⛈️ Rain expected — postpone fertilizer application"]
            if has_rain
            else [],
            "best_farming_window": next(
                (d["date"] for d in days if not d["rain_expected"]),
                days[0]["date"] if days else "N/A",
            ),
            "irrigation_recommendation": "Skip irrigation — rain expected"
            if has_rain
            else f"Irrigate — no rain forecast, temperatures up to {max_temp_overall}°C",
            "pesticide_spray_window": next(
                (
                    d["date"]
                    for d in days
                    if not d["rain_expected"] and d["avg_wind_speed"] < 15
                ),
                "Avoid spraying — check conditions",
            ),
        }

    return {
        "location": location,
        "farm_id": farm_id,
        "generated_at": datetime.utcnow().isoformat(),
        "daily_forecast": days,
        "ai_advisory": advisory_structured,
        "data_source": forecast_raw.get("data_source", "OpenWeather API"),
    }


@app.get("/get_market_forecast")
async def get_market_forecast(crop: str = "wheat"):
    from ml.market_predictor import predict_market_prices

    result = predict_market_prices(crop, days=30)
    return result


@app.get("/api/marketplace")
async def get_marketplace(state: Optional[str] = None):
    """Fetch ML-powered market prices"""
    from ml.market_predictor import predict_market_prices

    result = predict_market_prices("wheat", days=30)
    return result


@app.post("/predict_yield")
async def predict_yield(request: YieldPredictionRequest):
    from graph.tools import predict_yield as yield_tool

    sensor_data = {
        "soil_moisture": request.soil_quality * 50 if request.soil_quality else 45,
        "air_temperature": 25,
        "npk_nitrogen": 45,
        "npk_phosphorus": 30,
        "npk_potassium": 40,
    }
    result = await yield_tool.ainvoke(
        {"crop_type": request.crop_type, "sensor_data": sensor_data}
    )
    return result


@app.post("/detect_disease")
async def detect_disease(request: DiseaseDetectionRequest):
    from graph.tools import detect_disease as disease_tool

    result = await disease_tool.ainvoke(
        {
            "crop_type": request.crop_type,
            "symptoms": request.symptoms,
            "image_data": request.image_data,
        }
    )
    return result


@app.post("/detect_disease_image")
async def detect_disease_from_image(request: ImageDiseaseRequest):
    """AI-powered crop disease detection from base64 image data"""
    from graph.tools import detect_disease as disease_tool

    result = await disease_tool.ainvoke(
        {"crop_type": request.crop_type, "image_data": request.image_base64}
    )
    return result


@app.post("/detect_disease_image_upload")
async def detect_disease_upload(
    file: UploadFile = File(...), crop_type: str = Form("wheat")
):
    """Disease detection via direct file upload"""
    try:
        file_bytes = await file.read()
        image_b64 = base64.b64encode(file_bytes).decode("utf-8")
        mime_type = file.content_type or "image/jpeg"
        image_b64 = f"data:{mime_type};base64,{image_b64}"

        disease_agent = DiseaseDetectionAgent()
        result = disease_agent.analyze_image_from_base64(image_b64, crop_type)
        if result and isinstance(result, dict) and result.get("error"):
            return result
        return result
    except Exception as e:
        error_msg = str(e).lower()
        if "image" in error_msg and "not support" in error_msg:
            return {
                "error": "This model does not support image input. Please use a vision-enabled model."
            }
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get_govt_schemes")
async def get_govt_schemes(state: str = "all", crop_type: str = "all"):
    """Government schemes - deprecated, integrated into LangGraph"""
    return {
        "status": "deprecated",
        "message": "Govt schemes now available via LangGraph agent",
        "schemes": [
            {"name": "PM-KISAN", "benefit": "₹6000/year"},
            {"name": "PMFBY", "benefit": "Crop insurance"},
            {"name": "KCC", "benefit": "Low-interest credit"},
        ],
    }


@app.get("/blockchain_log")
async def blockchain_log(limit: int = 50):
    """Blockchain logs - deprecated"""
    return {"status": "deprecated", "message": "Green token system deprecated in v3.0"}


@app.get("/climate_risk")
async def get_climate_risk(location: str = "Delhi", days: int = 30):
    from graph.tools import assess_climate_risk

    return await assess_climate_risk.ainvoke(location)


@app.get("/drone_satellite_analysis")
async def drone_analysis(
    farm_id: str = "FARM001", lat: float = None, lon: float = None
):
    """Drone/Satellite - deprecated, use LangGraph workflow"""
    return {
        "status": "deprecated",
        "message": "Drone analysis integrated into LangGraph workflow",
    }


@app.get("/farm_analytics")
async def get_farm_analytics(farm_id: str = "FARM001", crop_type: Optional[str] = None):
    """Farm analytics - now via LangGraph workflow"""
    from graph import run_farm_analysis

    result = await run_farm_analysis(farm_id=farm_id, crop_type=crop_type or "wheat")
    return result


@app.get("/agrobrain_os_data")
async def get_agrobrain_os_data(
    farm_id: str = "FARM001", crop_type: Optional[str] = None
):
    """Returns the true AgroBrain OS LLM payload via LangGraph"""
    from graph import run_farm_analysis

    result = await run_farm_analysis(farm_id=farm_id, crop_type=crop_type or "wheat")
    return result


@app.post("/copilot_chat")
async def copilot_chat(request: CopilotRequest):
    """Processes messages to the Farm Copilot via LangGraph"""
    import traceback

    try:
        from graph import get_supervisor

        supervisor = get_supervisor()
        if supervisor is None:
            return {
                "reply": "AI agent is initializing. Please try again.",
                "error": True,
            }

        if not supervisor.is_available:
            return {
                "reply": "AI agent is not available. Please check API configuration."
            }

        # Use run_autonomous for better results
        result = await supervisor.run_autonomous(request.message, request.farm_id)
        return {"reply": result.get("response", "No response")}
    except Exception as e:
        traceback.print_exc()
        return {"reply": f"Error: {str(e)}", "error": True}


# ── Voice & Accessibility ───────────────────────────────────────────


@app.post("/voice_command")
async def voice_command(request: VoiceCommandRequest):
    """LLM-powered voice command via LangGraph"""
    import traceback

    try:
        from graph import get_supervisor

        supervisor = get_supervisor()
        if supervisor is None:
            return {
                "reply": "AI agent is initializing. Please try again.",
                "error": True,
            }

        if not supervisor.is_available:
            return {"reply": "AI agent not available", "error": True}

        result = await supervisor.run_autonomous(
            request.text, request.farm_id or "FARM001"
        )
        return {"reply": result.get("response", "No response")}
    except Exception as e:
        traceback.print_exc()
        return {"reply": f"Error: {str(e)}", "error": True}


@app.post("/text_to_speech")
async def text_to_speech(text: str, language: str = "en"):
    from gtts import gTTS

    lang_map = {"en": "en", "hi": "hi", "mr": "mr"}
    tts = gTTS(text=text, lang=lang_map.get(language, "en"))
    audio_buffer = io.BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)
    return StreamingResponse(audio_buffer, media_type="audio/mpeg")


# ── Dashboard & Analytics ───────────────────────────────────────────


@app.get("/dashboard")
async def get_dashboard(farm_id: str = "FARM001"):
    sensors = await db.get_latest_readings(farm_id, limit=1)
    recs = await db.get_recommendations(farm_id, limit=5)
    return {
        "farm_id": farm_id,
        "sensors": sensors[0] if sensors else None,
        "recommendations": recs,
        "blockchain": {"status": "deprecated"},
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/realtime_recommendations")
async def realtime_recommendations(farm_id: str = "FARM001"):
    """Return real-time alerts derived from the latest sensor readings"""
    sensors = await db.get_latest_readings(farm_id, limit=1)
    alerts = []
    if sensors:
        s = sensors[0]
        if s.get("soil_moisture", 50) < 25:
            alerts.append(
                {
                    "title": "🚨 Low Soil Moisture",
                    "message": f"Soil moisture is critically low at {s['soil_moisture']:.1f}%.",
                    "action": "Irrigate immediately to prevent crop stress.",
                    "priority": "critical",
                }
            )
        if s.get("air_temperature", 25) > 38:
            alerts.append(
                {
                    "title": "🔥 High Temperature Alert",
                    "message": f"Air temperature is {s['air_temperature']:.1f}°C — above stress threshold.",
                    "action": "Increase irrigation frequency and provide shade if possible.",
                    "priority": "critical",
                }
            )
        if s.get("soil_ph", 6.5) < 5.5 or s.get("soil_ph", 6.5) > 8.0:
            alerts.append(
                {
                    "title": "⚠️ Soil pH Out of Range",
                    "message": f"Soil pH is {s['soil_ph']:.1f} — outside the optimal 5.5–8.0 range.",
                    "action": "Apply lime to raise pH or sulfur to lower it.",
                    "priority": "high",
                }
            )
        if s.get("npk_nitrogen", 150) < 100:
            alerts.append(
                {
                    "title": "🌱 Low Nitrogen Levels",
                    "message": f"Nitrogen is {s['npk_nitrogen']:.0f} mg/kg — below optimal.",
                    "action": "Apply nitrogen-rich fertilizer in the next irrigation cycle.",
                    "priority": "high",
                }
            )
    if not alerts:
        alerts.append(
            {
                "title": "✅ All Systems Optimal",
                "message": "No critical alerts detected for your farm.",
                "action": "Continue regular monitoring.",
                "priority": "low",
            }
        )
    return {
        "recommendations": alerts,
        "farm_id": farm_id,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ── Test Scenarios ──────────────────────────────────────────────────


@app.post("/test/scenario/low_moisture")
async def scenario_low_moisture(farm_id: str = "FARM001"):
    try:
        data = {
            "farm_id": farm_id,
            "soil_moisture": 15.0 + random.uniform(-2, 2),
            "soil_temperature": 24.0 + random.uniform(-1, 1),
            "soil_ph": 6.8 + random.uniform(-0.1, 0.1),
            "npk_nitrogen": 180 + random.uniform(-10, 10),
            "npk_phosphorus": 45 + random.uniform(-5, 5),
            "npk_potassium": 210 + random.uniform(-10, 10),
            "humidity": 45.0 + random.uniform(-5, 5),
            "air_temperature": 28.0 + random.uniform(-2, 2),
        }
        await db.store_sensor_data([data])
        return {
            "status": "success",
            "scenario": "Low Moisture",
            "message": "Critical low moisture simulated!",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/test/scenario/high_temperature")
async def scenario_high_temp(farm_id: str = "FARM001"):
    try:
        data = {
            "farm_id": farm_id,
            "soil_moisture": 45.0 + random.uniform(-2, 2),
            "soil_temperature": 32.0 + random.uniform(-1, 1),
            "soil_ph": 6.8 + random.uniform(-0.1, 0.1),
            "npk_nitrogen": 180 + random.uniform(-10, 10),
            "npk_phosphorus": 45 + random.uniform(-5, 5),
            "npk_potassium": 210 + random.uniform(-10, 10),
            "humidity": 30.0 + random.uniform(-5, 5),
            "air_temperature": 42.0 + random.uniform(-2, 2),
        }
        await db.store_sensor_data([data])
        return {
            "status": "success",
            "scenario": "High Temperature",
            "message": "Extreme heat stress simulated!",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/test/scenario/optimal")
async def scenario_optimal(farm_id: str = "FARM001"):
    try:
        data = {
            "farm_id": farm_id,
            "soil_moisture": 55.0 + random.uniform(-2, 2),
            "soil_temperature": 22.0 + random.uniform(-1, 1),
            "soil_ph": 6.8 + random.uniform(-0.1, 0.1),
            "npk_nitrogen": 220 + random.uniform(-10, 10),
            "npk_phosphorus": 55 + random.uniform(-5, 5),
            "npk_potassium": 240 + random.uniform(-10, 10),
            "humidity": 65.0 + random.uniform(-5, 5),
            "air_temperature": 24.0 + random.uniform(-2, 2),
        }
        await db.store_sensor_data([data])
        return {
            "status": "success",
            "scenario": "Optimal",
            "message": "Ideal conditions simulated!",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/test/scenario/multiple_issues")
async def scenario_multiple(farm_id: str = "FARM001"):
    try:
        data = {
            "farm_id": farm_id,
            "soil_moisture": 12.0 + random.uniform(-2, 2),
            "soil_temperature": 35.0 + random.uniform(-1, 1),
            "soil_ph": 5.2 + random.uniform(-0.1, 0.1),
            "npk_nitrogen": 80 + random.uniform(-10, 10),
            "npk_phosphorus": 15 + random.uniform(-5, 5),
            "npk_potassium": 90 + random.uniform(-10, 10),
            "humidity": 25.0 + random.uniform(-5, 5),
            "air_temperature": 45.0 + random.uniform(-2, 2),
        }
        await db.store_sensor_data([data])
        return {
            "status": "success",
            "scenario": "Multi-Factor Emergency",
            "message": "Multiple critical alerts simulated!",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Actions Log ─────────────────────────────────────────────────────────────


class ActionLogSubmitResponse(BaseModel):
    """Not used as input — purely for documentation."""

    pass


@app.post("/actions_log/submit")
async def submit_action_log(
    farm_id: str = Form(...),
    action_type: str = Form(...),
    action_details: str = Form(""),
    green_tokens: int = Form(0),
    image: Optional[UploadFile] = File(None),
    provided_lat: Optional[float] = Form(None),
    provided_lon: Optional[float] = Form(None),
):
    """
    Submit a farming action with optional proof image.
    Runs EXIF geo-verification against the farm's stored GPS profile.
    Verification states: L0_SUBMITTED → L1_IMAGE_UPLOADED → L2_GEO_VERIFIED → L3_ADMIN_REVIEW
                        or verification_failed (with reason)
    """
    from core.geo_verifier import verify_geo

    # Validate inputs
    farm_id = farm_id.strip().upper()
    if not action_type:
        raise HTTPException(status_code=400, detail="action_type is required")
    if green_tokens < 0:
        raise HTTPException(status_code=400, detail="green_tokens must be >= 0")

    # Geo verification defaults
    geo_result = None
    verification_level = "L0_SUBMITTED"
    verification_status = "submitted"
    verification_reason = "No proof image uploaded"
    geo_match_passed = False
    proof_lat = None
    proof_lon = None
    distance_meters = None
    allowed_radius_m = None
    farm_lat = None
    farm_lon = None
    image_metadata = None

    if image is not None:
        image_bytes = await image.read()
        image_metadata = {
            "filename": image.filename,
            "content_type": image.content_type,
        }
        logger.info(
            "[ACTION_LOG] Image received: filename=%r, content_type=%r, size=%d bytes",
            image.filename, image.content_type, len(image_bytes),
        )

        # Look up farm GPS profile
        farm_profile = await db.get_farm_profile(farm_id)
        if farm_profile:
            farm_lat = farm_profile.get("latitude")
            farm_lon = farm_profile.get("longitude")
            allowed_radius_m = farm_profile.get("verification_radius_meters", 600.0)
        else:
            # Fallback: try auth system farmer profile
            try:
                farmer = await auth_system.get_farmer_profile(farm_id)
                if farmer:
                    farm_lat = farmer.get("latitude")
                    farm_lon = farmer.get("longitude")
                    # farm_size is stored in acres in the Farmer model
                    farm_size_acres = float(
                        farmer.get("farm_size")
                        or farmer.get("total_land_area_acres")
                        or 1.0
                    )
                    # Convert acres → m², then derive circle radius, add 500m practical buffer
                    import math as _math

                    farm_radius_m = _math.sqrt(farm_size_acres * 4047 / _math.pi)
                    allowed_radius_m = round(
                        farm_radius_m + 500.0, 0
                    )  # geometric radius + 500m margin
            except Exception:
                pass
            if not allowed_radius_m:
                allowed_radius_m = 600.0

        # Run geo-verification
        geo_result = verify_geo(image_bytes, farm_lat, farm_lon, allowed_radius_m)

        # Override with real-time Browser Coordinates if provided (Actual Live Geolocation)
        if provided_lat is not None and provided_lon is not None:
            proof_lat = provided_lat
            proof_lon = provided_lon
            # Recalculate distance based on the live coordinates
            from core.geo_verifier import haversine

            if farm_lat is not None and farm_lon is not None:
                distance_meters = haversine(proof_lat, proof_lon, farm_lat, farm_lon)
            else:
                distance_meters = 0.0

            # Update geo_result to be based on the actual live coordinates
            geo_result["proof_latitude"] = proof_lat
            geo_result["proof_longitude"] = proof_lon
            geo_result["distance_meters"] = distance_meters
            geo_result["passed"] = distance_meters <= allowed_radius_m
            geo_result["verification_level"] = (
                "L2_GEO_VERIFIED" if geo_result["passed"] else "verification_failed"
            )
            geo_result["reason"] = f"Live GPS: {distance_meters:.1f}m from farm"
        else:
            proof_lat = geo_result.get("proof_latitude")
            proof_lon = geo_result.get("proof_longitude")
            distance_meters = geo_result.get("distance_meters")

        verification_reason = geo_result.get("reason", "")
        image_metadata["exif_datetime"] = geo_result["exif"].get("datetime")
        image_metadata["exif_device"] = (
            f"{geo_result['exif'].get('make', '')} {geo_result['exif'].get('model', '')}".strip()
        )
        image_metadata["has_gps"] = geo_result["exif"].get("has_gps", False) or (
            provided_lat is not None
        )
        logger.info(
            "[ACTION_LOG] Image metadata extracted: exif_datetime=%r, exif_device=%r, has_gps=%s",
            image_metadata["exif_datetime"],
            image_metadata["exif_device"],
            image_metadata["has_gps"],
        )
        logger.info(
            "[ACTION_LOG] Geo-verification result: passed=%s, level=%r, reason=%r",
            geo_result["passed"],
            geo_result.get("verification_level"),
            verification_reason,
        )

        if geo_result["passed"]:
            verification_level = "L2_GEO_VERIFIED"
            verification_status = "geo_verified"
            token_request_status = "awaiting_admin_review"
            geo_match_passed = True
        else:
            verification_level = geo_result.get(
                "verification_level", "verification_failed"
            )
            # If coordinates were missing entirely, status=geo_failed, otherwise detail the level
            verification_status = (
                "geo_failed"
                if not (geo_result["exif"].get("has_gps") or provided_lat)
                else "geo_radius_exceeded"
            )
            token_request_status = (
                "pending"  # Manual review / Video verification needed
            )
            geo_match_passed = False
    else:
        verification_level = "L0_SUBMITTED"
        verification_status = "submitted"
        token_request_status = "pending"

    payload = {
        "farm_id": farm_id,
        "action_type": action_type,
        "action_details": action_details,
        "requested_green_tokens": green_tokens,
        "green_tokens_earned": 0,  # Only minted after L5_APPROVED
        "token_request_status": token_request_status,
        "verification_status": verification_status,
        "verification_level": verification_level,
        "verification_reason": verification_reason,
        "geo_match_passed": geo_match_passed,
        "farm_size_match_passed": True,
        "distance_meters": distance_meters,
        "allowed_radius_meters": allowed_radius_m,
        "proof_latitude": proof_lat,
        "proof_longitude": proof_lon,
        "farm_latitude": farm_lat,
        "farm_longitude": farm_lon,
        "image_metadata": image_metadata,
        "video_verification_required": False,
        "video_verification_status": "not_required",
    }

    # Geo-verified → move to admin queue
    if geo_match_passed:
        payload["token_request_status"] = "awaiting_admin_review"

    saved = await db.log_action(payload)
    return {
        "status": "success",
        "action_id": saved["id"],
        "verification_level": verification_level,
        "verification_status": verification_status,
        "geo_passed": geo_match_passed,
        "verification_reason": verification_reason,
        "proof_latitude": proof_lat,
        "proof_longitude": proof_lon,
        "distance_meters": distance_meters,
        "farm_latitude": farm_lat,
        "farm_longitude": farm_lon,
        "exif": geo_result["exif"] if geo_result else None,
    }


@app.get("/actions_log")
async def get_actions_log(farm_id: str = "FARM001", limit: int = 100):
    """Get all actions for a farm."""
    actions = await db.list_actions(farm_id=farm_id, limit=limit)
    total_tokens = sum(int(a.get("green_tokens_earned") or 0) for a in actions)
    return {
        "actions": actions,
        "total_green_tokens": total_tokens,
        "total_actions": len(actions),
    }


@app.delete("/actions_log/{action_id}")
async def delete_action_log(action_id: int):
    """Delete an action log entry."""
    deleted = await db.delete_action(action_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Action not found")
    return {"status": "success", "deleted_id": action_id}


# ── Admin Auth ────────────────────────────────────────────────────────────────

ADMIN_SUPER_SECRET = os.getenv("ADMIN_SUPER_SECRET", "agri_admin_secret_2026")


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminRegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "admin"
    super_secret: str  # must match env var


def _verify_admin_token(x_admin_token: Optional[str] = None) -> Dict[str, Any]:
    """Simple shared-token admin auth guard."""
    import hashlib

    if not x_admin_token:
        raise HTTPException(status_code=401, detail="X-Admin-Token header required")
    # Token format: sha256(username:password)  — set on login
    return {"token": x_admin_token}


from fastapi import Header


async def require_admin(x_admin_token: Optional[str] = Header(None)):
    """Depend on this to protect admin routes."""
    if not x_admin_token:
        raise HTTPException(
            status_code=401,
            detail="Admin authentication required (X-Admin-Token header)",
        )
    # Verify token exists in DB by checking hash lookup
    # Token is sha256(username + ":" + password_hash) created at login
    # We trust it here; a real system would use JWT
    return x_admin_token


@app.post("/admin/login")
async def admin_login(request: AdminLoginRequest):
    """Admin login — returns X-Admin-Token to use in subsequent requests."""
    import hashlib

    admin = await db.get_admin_by_username(request.username)
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    expected_hash = hashlib.sha256(request.password.encode()).hexdigest()
    if admin["password_hash"] != expected_hash:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    # Token = sha256(username:password_hash) — deterministic session token
    token = hashlib.sha256(
        f"{request.username}:{admin['password_hash']}".encode()
    ).hexdigest()
    return {
        "status": "success",
        "admin_token": token,
        "username": admin["username"],
        "role": admin["role"],
    }


@app.post("/admin/register")
async def admin_register(request: AdminRegisterRequest):
    """Create a new admin account (requires ADMIN_SUPER_SECRET)."""
    if request.super_secret != ADMIN_SUPER_SECRET:
        raise HTTPException(status_code=403, detail="Invalid super secret")
    if not request.username or len(request.password) < 6:
        raise HTTPException(
            status_code=400, detail="Username required, password must be >= 6 chars"
        )
    try:
        admin = await db.create_admin(request.username, request.password, request.role)
        return {"status": "success", "admin": admin}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not create admin: {str(e)}")


# ── Admin Verification Queue ───────────────────────────────────────────────────


@app.get("/admin/queue")
async def admin_queue(
    status: str = "all", limit: int = 200, admin_token: str = Depends(require_admin)
):
    """Fetch the verification queue with optional status filter."""
    actions = await db.list_pending_actions(limit=limit, status_filter=status)
    return {"actions": actions, "count": len(actions), "filter": status}


class AdminReviewRequest(BaseModel):
    reviewer: str
    notes: Optional[str] = None


@app.post("/admin/approve/{action_id}")
async def admin_approve(
    action_id: int,
    request: AdminReviewRequest,
    admin_token: str = Depends(require_admin),
):
    """Approve a token request - deprecated blockchain system"""
    action = await db.get_action(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    return {
        "status": "approved",
        "message": "Token system deprecated in v3.0",
        "action_id": action_id,
    }


@app.post("/admin/reject/{action_id}")
async def admin_reject(
    action_id: int,
    request: AdminReviewRequest,
    admin_token: str = Depends(require_admin),
):
    """Reject a token request."""
    action = await db.get_action(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    updates = {
        "token_request_status": "rejected",
        "verification_level": "L5_REJECTED",
        "verification_status": "rejected",
        "green_tokens_earned": 0,
        "admin_reviewer": request.reviewer,
        "admin_review_notes": request.notes,
    }
    result = await db.update_action(action_id, updates)
    return {"status": "rejected", "action": result}


class ScheduleCallRequest(BaseModel):
    phone: str
    scheduled_at: str  # ISO datetime string
    notes: Optional[str] = None


@app.post("/admin/schedule_call/{action_id}")
async def admin_schedule_call(
    action_id: int,
    request: ScheduleCallRequest,
    admin_token: str = Depends(require_admin),
):
    """Schedule a WhatsApp video verification call."""
    action = await db.get_action(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    # Validate phone
    phone = request.phone.strip()
    if not phone or len(phone) < 7:
        raise HTTPException(status_code=400, detail="Valid phone number required")

    try:
        # Handle 'Z' suffix from JavaScript toISOString()
        iso_str = request.scheduled_at.replace("Z", "+00:00")
        scheduled_dt = datetime.fromisoformat(iso_str)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail=f"scheduled_at must be valid ISO datetime (e.g. 2026-04-10T14:00:00). Recieved: {request.scheduled_at}",
        )

    updates = {
        "token_request_status": "awaiting_video_verification",
        "verification_level": "L4_VIDEO_PENDING",
        "video_verification_required": True,
        "video_verification_status": "scheduled",
        "video_call_scheduled_at": scheduled_dt,
        "verification_phone": phone,
        "admin_review_notes": request.notes,
    }
    result = await db.update_action(action_id, updates)
    return {
        "status": "call_scheduled",
        "phone": phone,
        "scheduled_at": scheduled_dt.isoformat(),
        "action": result,
    }


class CompleteCallRequest(BaseModel):
    call_status: str  # "completed" | "failed"
    notes: Optional[str] = None


@app.post("/admin/complete_call/{action_id}")
async def admin_complete_call(
    action_id: int,
    request: CompleteCallRequest,
    admin_token: str = Depends(require_admin),
):
    """Mark a video verification call as completed or failed."""
    action = await db.get_action(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    if request.call_status not in ("completed", "failed"):
        raise HTTPException(
            status_code=400, detail="call_status must be 'completed' or 'failed'"
        )

    if request.call_status == "completed":
        updates = {
            "video_verification_status": "completed",
            "video_verified_at": datetime.utcnow(),
            "verification_level": "L4_VIDEO_VERIFIED",
            "token_request_status": "awaiting_admin_review",  # back for final approval
            "admin_review_notes": request.notes,
        }
    else:
        updates = {
            "video_verification_status": "failed",
            "video_verified_at": datetime.utcnow(),
            "verification_level": "L5_REJECTED",
            "token_request_status": "rejected",
            "verification_status": "rejected",
            "admin_review_notes": request.notes,
        }

    result = await db.update_action(action_id, updates)
    return {"status": f"call_{request.call_status}", "action": result}


# ── Admin Farmers & Stats ─────────────────────────────────────────────────────


@app.get("/admin/farmers")
async def admin_farmers(admin_token: str = Depends(require_admin)):
    """List all farmers with their farm geo profiles."""
    try:
        farmers = await db.get_all_farmers_with_profiles()
    except Exception as e:
        # Fallback: return farm profiles only
        farmers = await db.list_farm_profiles()
    return {"farmers": farmers, "count": len(farmers)}


@app.get("/admin/stats")
async def admin_stats(admin_token: str = Depends(require_admin)):
    """Aggregated stats for admin dashboard."""
    return await db.get_verification_stats()


# ── Admin Farm Profile CRUD ───────────────────────────────────────────────────


class FarmProfileRequest(BaseModel):
    farm_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    area_hectares: Optional[float] = None
    verification_radius_meters: Optional[float] = None
    is_active: Optional[bool] = True


@app.get("/admin/farm_profile/{farm_id}")
async def get_farm_profile(farm_id: str, admin_token: str = Depends(require_admin)):
    profile = await db.get_farm_profile(farm_id.upper())
    if not profile:
        raise HTTPException(status_code=404, detail="Farm profile not found")
    return profile


@app.put("/admin/farm_profile/{farm_id}")
async def upsert_farm_profile(
    farm_id: str, request: FarmProfileRequest, admin_token: str = Depends(require_admin)
):
    """Create or update a farm's GPS geo-verification profile."""
    # Validate geo inputs
    payload = request.dict(exclude_none=True)
    if "latitude" in payload and not (-90 <= payload["latitude"] <= 90):
        raise HTTPException(
            status_code=400, detail="latitude must be between -90 and 90"
        )
    if "longitude" in payload and not (-180 <= payload["longitude"] <= 180):
        raise HTTPException(
            status_code=400, detail="longitude must be between -180 and 180"
        )
    if "area_hectares" in payload and payload["area_hectares"] < 0:
        raise HTTPException(status_code=400, detail="area_hectares must be >= 0")
    if (
        "verification_radius_meters" in payload
        and payload["verification_radius_meters"] < 10
    ):
        raise HTTPException(
            status_code=400, detail="verification_radius_meters must be >= 10"
        )

    result = await db.upsert_farm_profile(farm_id.upper(), payload)
    return {"status": "updated", "profile": result}


@app.get("/admin/farm_profiles")
async def list_farm_profiles(admin_token: str = Depends(require_admin)):
    """List all registered farm profiles."""
    profiles = await db.list_farm_profiles()
    return {"profiles": profiles, "count": len(profiles)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
