"""
Smart Farming Agentic AI System — Main Backend Server
=====================================================
FastAPI Application Entry Point
Consolidated Version: PostgreSQL + Async + Full Agent Suite + AI Vision
"""
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
import random
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from both .env files
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Import configuration
from config import API_CONFIG

# Import all agents
from agents.lead_agent import LeadAgent
from agents.soil_agent import SoilAgent
from agents.weather_collector_agent import WeatherCollectorAgent
from agents.weather_forecast_agent import WeatherForecastAgent
from agents.water_management_agent import WaterManagementAgent
from agents.fertilizer_agent import FertilizerAgent
from agents.disease_detection_agent import DiseaseDetectionAgent
from agents.yield_prediction_agent import YieldPredictionAgent
from agents.market_forecast_agent import MarketForecastAgent
from agents.market_integration_agent import MarketIntegrationAgent
from agents.govt_scheme_agent import GovtSchemeAgent
from agents.blockchain_agent import BlockchainAgent
from agents.sustainability_agent import SustainabilityAgent
from agents.drone_satellite_agent import DroneSatelliteAgent
from agents.climate_risk_agent import ClimateRiskAgent
from agents.voice_assistant_agent import VoiceAssistantAgent
from agents.speech_recognition_agent import SpeechRecognitionAgent

# Core components
from core.database import AsyncDatabase
from core.auth_system import AuthSystem

# Initialize FastAPI
app = FastAPI(
    title="Smart Farming AI System",
    description="Consolidated Agentic AI System for Precision Agriculture",
    version="2.2.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
db = AsyncDatabase(API_CONFIG["database_url"])
auth_system = AuthSystem(db)
lead_agent = LeadAgent(db)

# Initialize specialized agents
market_forecast_agent = MarketForecastAgent(api_key=API_CONFIG.get('data_gov_api_key'))
weather_collector_agent = WeatherCollectorAgent(api_key=API_CONFIG.get('openweather_api_key'))
weather_forecast_agent = WeatherForecastAgent(api_key=API_CONFIG.get('openweather_api_key'))

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

class CropRequest(BaseModel):
    crop_type: str
    variety: Optional[str] = None
    planted_date: Optional[str] = None
    area_hectares: float = 1.0
    status: str = "growing"

class CropStatusUpdate(BaseModel):
    status: str

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

class LoginRequest(BaseModel):
    email: Optional[str] = None
    farmer_id: Optional[str] = None
    password: str

# ── Lifecycle Events ────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    print("🌾 Initializing Smart Farming AI System...")
    await db.init_db()
    print("✅ Database initialized")

# ── Health & System Status ──────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Smart Farming AI System",
        "version": "2.2.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/system_status")
async def system_status():
    return {
        "status": "online",
        "apis": {
            "market": bool(API_CONFIG.get('data_gov_api_key')),
            "weather": bool(API_CONFIG.get('openweather_api_key')),
            "grok_vision": bool(API_CONFIG.get('grok_api_key')),
            "ollama": lead_agent.llm.is_available
        },
        "database": API_CONFIG["database_url"].split(":")[0]
    }

# ── Authentication ──────────────────────────────────────────────────

@app.post("/auth/register")
async def register(request: RegisterRequest):
    try:
        return await auth_system.register_farmer(request.dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/login")
async def login(request: LoginRequest):
    identifier = request.email or request.farmer_id
    if not identifier:
        raise HTTPException(status_code=400, detail="Email or Farmer ID is required")
    
    result = await auth_system.login_farmer(identifier, request.password)
    if result["status"] == "failed":
        raise HTTPException(status_code=401, detail=result["message"])
    return result

@app.get("/profile")
async def get_profile(farm_id: str = "FARM001"):
    profile = await auth_system.get_farmer_profile(farm_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return profile

# ── Crop Management ──────────────────────────────────────────────

@app.get("/crops")
async def get_crops(farm_id: str = "FARM001"):
    crops = await db.get_crops(farm_id)
    return {"crops": crops}

@app.post("/crops")
async def add_crop(request: CropRequest, farm_id: str = "FARM001"):
    try:
        data = request.dict()
        data["farm_id"] = farm_id
        crop_id = await db.store_crop(data)
        return {"status": "success", "crop_id": crop_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/crops/{crop_id}/status")
async def update_crop_status(crop_id: int, request: CropStatusUpdate):
    await db.update_crop_status(crop_id, request.status)
    return {"status": "success"}

@app.delete("/crops/{crop_id}")
async def delete_crop(crop_id: int):
    await db.delete_crop(crop_id)
    return {"status": "success"}

# ── Core Agentic Workflows ──────────────────────────────────────────

@app.post("/run_agents")
async def run_agents(farm_id: str = "FARM001"):
    """Orchestrate all agents for a specific farm"""
    try:
        # 1. Collect late sensor data
        readings = await db.get_latest_readings(farm_id)
        if not readings:
            return {"status": "no_data", "message": "No sensor data found for this farm"}
            
        # 2. Run lead agent orchestration
        result = await lead_agent.orchestrate_all_agents(farm_id)
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
            "air_temperature": 25.0 + random.uniform(-5, 5)
        }
        data.append(reading)
    
    await db.store_sensor_data(data)
    return {"status": "success", "count": len(data)}

# ── Specialized Feature Endpoints ───────────────────────────────────

@app.get("/get_weather")
async def get_weather(location: str = "Delhi"):
    return weather_collector_agent.collect_weather(location)

@app.get("/get_forecast")
async def get_forecast(location: str = "Delhi", hours: int = 24):
    return weather_forecast_agent.predict_weather(location, hours)

@app.get("/get_market_forecast")
async def get_market_forecast(crop: str = "wheat"):
    return market_forecast_agent.forecast_prices(crop)

@app.post("/predict_yield")
async def predict_yield(request: YieldPredictionRequest):
    yield_agent = YieldPredictionAgent(db)
    return yield_agent.predict_yield(request.crop_type, request.area_hectares, request.soil_quality)

@app.post("/detect_disease")
async def detect_disease(request: DiseaseDetectionRequest):
    disease_agent = DiseaseDetectionAgent()
    return disease_agent.detect_disease(request.crop_type, request.symptoms)

@app.post("/detect_disease_image")
async def detect_disease_from_image(request: ImageDiseaseRequest):
    """AI-powered crop disease detection from base64 image data"""
    try:
        disease_agent = DiseaseDetectionAgent()
        # Note: If no implementation exists in the current branch for AI vision, 
        # this will fall back to legacy if possible or error gracefully.
        if hasattr(disease_agent, 'analyze_image_from_base64'):
             return disease_agent.analyze_image_from_base64(request.image_base64, request.crop_type)
        return {"status": "error", "message": "AI Vision model not available in this instance"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/detect_disease_image_upload")
async def detect_disease_upload(
    file: UploadFile = File(...),
    crop_type: str = Form("wheat")
):
    """Disease detection via direct file upload"""
    try:
        file_bytes = await file.read()
        image_b64 = base64.b64encode(file_bytes).decode('utf-8')
        mime_type = file.content_type or "image/jpeg"
        image_b64 = f"data:{mime_type};base64,{image_b64}"
        
        disease_agent = DiseaseDetectionAgent()
        if hasattr(disease_agent, 'analyze_image_from_base64'):
            return disease_agent.analyze_image_from_base64(image_b64, crop_type)
        return {"status": "error", "message": "AI Vision model not available"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_govt_schemes")
async def get_govt_schemes(state: str = "all", crop_type: str = "all"):
    govt_agent = GovtSchemeAgent()
    return govt_agent.get_applicable_schemes(state, crop_type)

@app.get("/blockchain_log")
async def blockchain_log(limit: int = 50):
    blockchain_agent = BlockchainAgent()
    return blockchain_agent.get_recent_logs(limit)

@app.get("/climate_risk")
async def get_climate_risk(location: str = "Delhi", days: int = 30):
    climate_agent = ClimateRiskAgent()
    return climate_agent.assess_risk(location, days)

@app.get("/drone_satellite_analysis")
async def drone_analysis(farm_id: str = "FARM001", lat: float = None, lon: float = None):
    drone_agent = DroneSatelliteAgent()
    return drone_agent.analyze_farm(farm_id, latitude=lat, longitude=lon)

# ── Voice & Accessibility ───────────────────────────────────────────

@app.post("/voice_command")
async def voice_command(request: VoiceCommandRequest):
    """LLM-powered voice command with full farm context."""
    voice_agent = VoiceAssistantAgent(db)
    farm_id = request.farm_id or "FARM001"

    # ── Gather farm context for the LLM ──────────────────────────────
    farmer_profile = None
    sensor_data = None
    crops = []
    recent_recommendations = []

    try:
        farmer_profile = await auth_system.get_farmer_profile(farm_id)
    except Exception as e:
        print(f"⚠️ Could not fetch farmer profile: {e}")

    try:
        readings = await db.get_latest_readings(farm_id, limit=1)
        if readings:
            sensor_data = readings[0]
    except Exception as e:
        print(f"⚠️ Could not fetch sensor data: {e}")

    try:
        crops = await db.get_crops(farm_id)
    except Exception as e:
        print(f"⚠️ Could not fetch crops: {e}")

    try:
        recent_recommendations = await db.get_recommendations(farm_id, limit=5)
    except Exception as e:
        print(f"⚠️ Could not fetch recommendations: {e}")

    return voice_agent.process_command(
        text=request.text,
        language=request.language,
        farmer_profile=farmer_profile,
        sensor_data=sensor_data,
        crops=crops,
        recent_recommendations=recent_recommendations,
    )

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
    blockchain = BlockchainAgent().get_stats()
    
    return {
        "farm_id": farm_id,
        "sensors": sensors[0] if sensors else None,
        "recommendations": recs,
        "blockchain": blockchain,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/realtime_recommendations")
async def realtime_recommendations(farm_id: str = "FARM001"):
    """Return real-time alerts derived from the latest sensor readings"""
    sensors = await db.get_latest_readings(farm_id, limit=1)
    alerts = []
    if sensors:
        s = sensors[0]
        if s.get("soil_moisture", 50) < 25:
            alerts.append({
                "title": "🚨 Low Soil Moisture",
                "message": f"Soil moisture is critically low at {s['soil_moisture']:.1f}%.",
                "action": "Irrigate immediately to prevent crop stress.",
                "priority": "critical"
            })
        if s.get("air_temperature", 25) > 38:
            alerts.append({
                "title": "🔥 High Temperature Alert",
                "message": f"Air temperature is {s['air_temperature']:.1f}°C — above stress threshold.",
                "action": "Increase irrigation frequency and provide shade if possible.",
                "priority": "critical"
            })
        if s.get("soil_ph", 6.5) < 5.5 or s.get("soil_ph", 6.5) > 8.0:
            alerts.append({
                "title": "⚠️ Soil pH Out of Range",
                "message": f"Soil pH is {s['soil_ph']:.1f} — outside the optimal 5.5–8.0 range.",
                "action": "Apply lime to raise pH or sulfur to lower it.",
                "priority": "high"
            })
        if s.get("npk_nitrogen", 150) < 100:
            alerts.append({
                "title": "🌱 Low Nitrogen Levels",
                "message": f"Nitrogen is {s['npk_nitrogen']:.0f} mg/kg — below optimal.",
                "action": "Apply nitrogen-rich fertilizer in the next irrigation cycle.",
                "priority": "high"
            })
    if not alerts:
        alerts.append({
            "title": "✅ All Systems Optimal",
            "message": "No critical alerts detected for your farm.",
            "action": "Continue regular monitoring.",
            "priority": "low"
        })
    return {"recommendations": alerts, "farm_id": farm_id, "timestamp": datetime.utcnow().isoformat()}

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
            "air_temperature": 28.0 + random.uniform(-2, 2)
        }
        await db.store_sensor_data([data])
        return {"status": "success", "scenario": "Low Moisture", "message": "Critical low moisture simulated!"}
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
            "air_temperature": 42.0 + random.uniform(-2, 2)
        }
        await db.store_sensor_data([data])
        return {"status": "success", "scenario": "High Temperature", "message": "Extreme heat stress simulated!"}
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
            "air_temperature": 24.0 + random.uniform(-2, 2)
        }
        await db.store_sensor_data([data])
        return {"status": "success", "scenario": "Optimal", "message": "Ideal conditions simulated!"}
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
            "air_temperature": 45.0 + random.uniform(-2, 2)
        }
        await db.store_sensor_data([data])
        return {"status": "success", "scenario": "Multi-Factor Emergency", "message": "Multiple critical alerts simulated!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
