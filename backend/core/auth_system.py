import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String, Boolean, DateTime, Float, select, update, Text
from .database import Base, AsyncDatabase
from config import DATABASE_URL

# ── Farmer Model ──────────────────────────────────────────────────

class Farmer(Base):
    __tablename__ = "farmers"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    farmer_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(20))
    password_hash: Mapped[str] = mapped_column(Text)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Metadata
    location: Mapped[str] = mapped_column(Text, nullable=True) 
    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)
    farm_size: Mapped[float] = mapped_column(Float, nullable=True) # In hectares
    language: Mapped[str] = mapped_column(String(10), default="en")

# ── Auth System Class ───────────────────────────────────────────

class AuthSystem:
    def __init__(self, db: AsyncDatabase):
        self.db = db

    async def register_farmer(self, farmer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new farmer"""
        async with self.db.session_factory() as session:
            # Check if email exists
            stmt = select(Farmer).where(Farmer.email == farmer_data["email"])
            result = await session.execute(stmt)
            if result.scalars().first():
                raise Exception("Email already registered")
                
            new_farmer = Farmer(
                farmer_id=f"F_{int(datetime.utcnow().timestamp())}",
                name=farmer_data["name"],
                email=farmer_data["email"],
                phone=farmer_data["phone"],
                password_hash=farmer_data["password"], 
                location=farmer_data.get("location"),
                latitude=farmer_data.get("latitude"),
                longitude=farmer_data.get("longitude"),
                farm_size=farmer_data.get("farm_size"),
                language=farmer_data.get("language", "en")
            )
            session.add(new_farmer)
            await session.commit()
            return {
                "status": "success",
                "farmer_id": new_farmer.farmer_id,
                "name": new_farmer.name
            }

    async def login_farmer(self, identifier: str, password: str) -> Dict[str, Any]:
        """Verify login credentials (email or farmer_id)"""
        async with self.db.session_factory() as session:
            # Check by email or farmer_id (case-insensitive)
            from sqlalchemy import or_, func
            stmt = select(Farmer).where(or_(
                func.lower(Farmer.email) == identifier.lower(),
                func.lower(Farmer.farmer_id) == identifier.lower()
            ))
            result = await session.execute(stmt)
            farmer = result.scalars().first()
            
            if not farmer or farmer.password_hash != password:
                return {"status": "failed", "message": "Invalid email/ID or password"}
                
            return {
                "status": "success",
                "farmer_id": farmer.farmer_id,
                "name": farmer.name,
                "email": farmer.email
            }

    async def get_farmer_profile(self, farmer_id: str) -> Optional[Dict[str, Any]]:
        """Get farmer details"""
        async with self.db.session_factory() as session:
            stmt = select(Farmer).where(Farmer.farmer_id == farmer_id)
            result = await session.execute(stmt)
            farmer = result.scalars().first()
            if not farmer:
                return None
            return {
                "farmer_id": farmer.farmer_id,
                "name": farmer.name,
                "email": farmer.email,
                "phone": farmer.phone,
                "language": farmer.language,
                "location": farmer.location,
                "latitude": farmer.latitude,
                "longitude": farmer.longitude,
                "farm_size": farmer.farm_size
            }
