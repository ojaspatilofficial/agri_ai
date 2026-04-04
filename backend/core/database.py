import os
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Float, DateTime, Text, ForeignKey, select, desc, JSON
from pathlib import Path

# ── Base Model ──────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass

# ── Models ─────────────────────────────────────────────────────────

class SensorReading(Base):
    __tablename__ = "sensor_readings"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    farm_id: Mapped[str] = mapped_column(String(50), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    # Soil Data
    soil_moisture: Mapped[float] = mapped_column(Float)
    soil_temperature: Mapped[float] = mapped_column(Float)
    soil_ph: Mapped[float] = mapped_column(Float)
    
    # Nutrients
    npk_nitrogen: Mapped[float] = mapped_column(Float)
    npk_phosphorus: Mapped[float] = mapped_column(Float)
    npk_potassium: Mapped[float] = mapped_column(Float)
    
    # Environment
    humidity: Mapped[float] = mapped_column(Float)
    air_temperature: Mapped[float] = mapped_column(Float)
    rainfall: Mapped[float] = mapped_column(Float, nullable=True)
    light_intensity: Mapped[float] = mapped_column(Float, nullable=True)

class AgentRecommendation(Base):
    __tablename__ = "agent_recommendations"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    farm_id: Mapped[str] = mapped_column(String(50), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    agent_name: Mapped[str] = mapped_column(String(100))
    recommendation_type: Mapped[str] = mapped_column(String(50)) # irrigation, fertilizer, pest, harvest
    recommendation_text: Mapped[Text] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(20)) # critical, high, medium, low
    status: Mapped[str] = mapped_column(String(20), default="pending") # pending, applied, dismissed
    
    llm_source: Mapped[str] = mapped_column(String(100), nullable=True) # e.g. "mistral:latest"
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)

class LLMConversation(Base):
    __tablename__ = "llm_conversation_history"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    farm_id: Mapped[str] = mapped_column(String(50), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    prompt_sent: Mapped[Text] = mapped_column(Text)
    response_received: Mapped[Text] = mapped_column(Text)
    model_used: Mapped[str] = mapped_column(String(100))
    metadata_used: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=True)

class Crop(Base):
    __tablename__ = "crops"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    farm_id: Mapped[str] = mapped_column(String(50), index=True)
    crop_type: Mapped[str] = mapped_column(String(100))
    variety: Mapped[str] = mapped_column(String(100), nullable=True)
    planted_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expected_harvest: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    area_hectares: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(50), default="growing") # growing, ready, harvested
    yield_estimate: Mapped[float] = mapped_column(Float, nullable=True)

# ── Database Class ──────────────────────────────────────────────────

class AsyncDatabase:
    def __init__(self, database_url: str):
        # Handle SQLite for local development
        if database_url.startswith("sqlite"):
            self.engine = create_async_engine(database_url)
        else:
            self.engine = create_async_engine(database_url, pool_pre_ping=True)
            
        self.session_factory = async_sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

    async def init_db(self):
        """Create tables if they don't exist"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def store_sensor_data(self, readings: List[Dict[str, Any]]):
        """Store new sensor readings"""
        async with self.session_factory() as session:
            for r in readings:
                reading = SensorReading(
                    farm_id=r.get("farm_id", "default_farm"),
                    soil_moisture=r.get("soil_moisture", 0.0),
                    soil_temperature=r.get("soil_temperature", 0.0),
                    soil_ph=r.get("soil_ph", 7.0),
                    npk_nitrogen=r.get("npk_nitrogen", 0.0),
                    npk_phosphorus=r.get("npk_phosphorus", 0.0),
                    npk_potassium=r.get("npk_potassium", 0.0),
                    humidity=r.get("humidity", 0.0),
                    air_temperature=r.get("air_temperature", 0.0),
                    rainfall=r.get("rainfall"),
                    light_intensity=r.get("light_intensity")
                )
                session.add(reading)
            await session.commit()

    async def get_latest_readings(self, farm_id: str, limit: int = 1) -> List[Dict[str, Any]]:
        """Get latest sensor readings for a farm"""
        async with self.session_factory() as session:
            query = select(SensorReading).where(SensorReading.farm_id == farm_id).order_by(desc(SensorReading.timestamp)).limit(limit)
            result = await session.execute(query)
            readings = result.scalars().all()
            return [
                {
                    "timestamp": r.timestamp.isoformat(),
                    "soil_moisture": r.soil_moisture,
                    "soil_temperature": r.soil_temperature,
                    "soil_ph": r.soil_ph,
                    "npk_nitrogen": r.npk_nitrogen,
                    "npk_phosphorus": r.npk_phosphorus,
                    "npk_potassium": r.npk_potassium,
                    "humidity": r.humidity,
                    "air_temperature": r.air_temperature,
                    "rainfall": r.rainfall,
                    "light_intensity": r.light_intensity
                } for r in readings
            ]

    async def store_recommendation(self, rec: Dict[str, Any]):
        """Store a new AI recommendation"""
        async with self.session_factory() as session:
            recommendation = AgentRecommendation(
                farm_id=rec.get("farm_id", "default_farm"),
                agent_name=rec.get("agent_name", "Unknown"),
                recommendation_type=rec.get("recommendation_type", "general"),
                recommendation_text=rec.get("recommendation_text", ""),
                priority=rec.get("priority", "medium"),
                llm_source=rec.get("llm_source"),
                metadata_json=rec.get("metadata", {})
            )
            session.add(recommendation)
            await session.commit()

    async def get_recommendations(self, farm_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent recommendations"""
        async with self.session_factory() as session:
            query = select(AgentRecommendation).where(AgentRecommendation.farm_id == farm_id).order_by(desc(AgentRecommendation.created_at)).limit(limit)
            result = await session.execute(query)
            recs = result.scalars().all()
            return [
                {
                    "id": r.id,
                    "timestamp": r.created_at.isoformat(),
                    "agent_name": r.agent_name,
                    "recommendation_type": r.recommendation_type,
                    "recommendation_text": r.recommendation_text,
                    "priority": r.priority,
                    "status": r.status
                } for r in recs
            ]

    async def store_llm_conversation(self, farm_id: str, prompt_sent: str, response_received: str, model_used: str, context_used: Dict[str, Any], latency_ms: float = None):
        """Log LLM conversation for audit/history"""
        async with self.session_factory() as session:
            conv = LLMConversation(
                farm_id=farm_id,
                prompt_sent=prompt_sent,
                response_received=response_received,
                model_used=model_used,
                context_used=context_used,
                latency_ms=latency_ms
            )
            session.add(conv)
            await session.commit()

    # ── Crop Management ──────────────────────────────────────────────

    async def store_crop(self, crop_data: Dict[str, Any]):
        """Store a new crop record"""
        async with self.session_factory() as session:
            crop = Crop(
                farm_id=crop_data.get("farm_id"),
                crop_type=crop_data.get("crop_type"),
                variety=crop_data.get("variety"),
                planted_date=datetime.fromisoformat(crop_data["planted_date"]) if "planted_date" in crop_data else datetime.utcnow(),
                area_hectares=float(crop_data.get("area_hectares", 1.0)),
                status=crop_data.get("status", "growing")
            )
            session.add(crop)
            await session.commit()
            return crop.id

    async def get_crops(self, farm_id: str) -> List[Dict[str, Any]]:
        """Get all crops for a farm"""
        async with self.session_factory() as session:
            stmt = select(Crop).where(Crop.farm_id == farm_id).order_by(desc(Crop.planted_date))
            result = await session.execute(stmt)
            crops = result.scalars().all()
            return [
                {
                    "id": c.id,
                    "crop_type": c.crop_type,
                    "variety": c.variety,
                    "planted_date": c.planted_date.isoformat(),
                    "expected_harvest": c.expected_harvest.isoformat() if c.expected_harvest else None,
                    "area_hectares": c.area_hectares,
                    "status": c.status,
                    "yield_estimate": c.yield_estimate
                } for c in crops
            ]

    async def update_crop_status(self, crop_id: int, status: str):
        """Update the status of a specific crop"""
        async with self.session_factory() as session:
            stmt = update(Crop).where(Crop.id == crop_id).values(status=status)
            await session.execute(stmt)
            await session.commit()

    async def delete_crop(self, crop_id: int):
        """Delete a crop record"""
        async with self.session_factory() as session:
            from sqlalchemy import delete
            stmt = delete(Crop).where(Crop.id == crop_id)
            await session.execute(stmt)
            await session.commit()
