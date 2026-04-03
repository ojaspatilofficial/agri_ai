"""
Database Manager — Async SQLAlchemy + PostgreSQL
================================================
Replaces the old raw-sqlite3 Database class.
Every method is now async and uses the ORM models.
Maintains the same public API so existing agents/endpoints work.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy import select, update, delete, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from core.db_models import (
    Farmer, Field, CropCycle, SensorReading,
    AgentRecommendation, ActionLog, AgentMemoryLog,
    ExternalApiCache, LlmConversationHistory,
)
from core.db_session import get_db_context


class Database:
    """
    Async database manager.
    All public methods are async — callers must await them.
    Accepts an optional AsyncSession; if not provided, creates its own.
    """

    # ── Sensor Data ────────────────────────────────────────────────

    async def store_sensor_data(
        self, sensor_readings: List[Dict[str, Any]], session: AsyncSession = None
    ):
        """Store sensor data in database."""
        async def _do(s: AsyncSession):
            for reading in sensor_readings:
                field_id = reading.get("field_id")
                # Legacy compat: if farm_id is passed instead of field_id,
                # look up the default field for that farmer
                if not field_id and reading.get("farm_id"):
                    field_id = await self._resolve_field_id(s, reading["farm_id"])
                if not field_id:
                    continue

                reading_time = reading.get("timestamp", datetime.now())
                if isinstance(reading_time, str):
                    try:
                        reading_time = datetime.fromisoformat(reading_time.replace('Z', '+00:00'))
                    except ValueError:
                        reading_time = datetime.now()

                obj = SensorReading(
                    field_id=field_id,
                    reading_time=reading_time,
                    soil_moisture=reading.get("soil_moisture"),
                    soil_ph=reading.get("soil_ph"),
                    soil_temperature=reading.get("soil_temperature"),
                    air_temperature=reading.get("air_temperature"),
                    humidity=reading.get("humidity"),
                    rainfall=reading.get("rainfall"),
                    light_intensity=reading.get("light_intensity"),
                    npk_nitrogen=reading.get("npk_nitrogen"),
                    npk_phosphorus=reading.get("npk_phosphorus"),
                    npk_potassium=reading.get("npk_potassium"),
                    source=reading.get("source", "simulator"),
                )
                s.add(obj)

        if session:
            await _do(session)
        else:
            async with get_db_context() as s:
                await _do(s)

    async def get_latest_sensor_data(
        self, farm_id: str, limit: int = 10, session: AsyncSession = None
    ) -> List[Dict[str, Any]]:
        """Get latest sensor readings for a farm."""
        async def _do(s: AsyncSession):
            field_id = await self._resolve_field_id(s, farm_id)
            if not field_id:
                return []
            stmt = (
                select(SensorReading)
                .where(SensorReading.field_id == field_id)
                .order_by(desc(SensorReading.reading_time))
                .limit(limit)
            )
            result = await s.execute(stmt)
            rows = result.scalars().all()
            return [self._sensor_to_dict(r, farm_id) for r in rows]

        if session:
            return await _do(session)
        async with get_db_context() as s:
            return await _do(s)

    # ── Recommendations ────────────────────────────────────────────

    async def store_recommendation(
        self, farm_id: str, agent_name: str,
        rec_type: str, rec_text: str, priority: str = "medium",
        context_snapshot: dict = None, llm_source: str = "rule_based",
        session: AsyncSession = None,
    ):
        """Store agent recommendation."""
        async def _do(s: AsyncSession):
            field_id = await self._resolve_field_id(s, farm_id)
            if not field_id:
                return
            crop_cycle_id = await self._get_active_crop_cycle_id(s, field_id)
            obj = AgentRecommendation(
                field_id=field_id,
                crop_cycle_id=crop_cycle_id,
                agent_name=agent_name,
                recommendation_type=rec_type,
                recommendation_text=rec_text,
                priority=priority,
                context_snapshot=context_snapshot or {},
                llm_source=llm_source,
            )
            s.add(obj)

        if session:
            await _do(session)
        else:
            async with get_db_context() as s:
                await _do(s)

    async def get_recommendations(
        self, farm_id: str, status: str = "pending", limit: int = 20,
        session: AsyncSession = None,
    ) -> List[Dict[str, Any]]:
        """Get recommendations."""
        async def _do(s: AsyncSession):
            field_id = await self._resolve_field_id(s, farm_id)
            if not field_id:
                return []
            stmt = (
                select(AgentRecommendation)
                .where(
                    AgentRecommendation.field_id == field_id,
                    AgentRecommendation.status == status,
                )
                .order_by(desc(AgentRecommendation.created_at))
                .limit(limit)
            )
            result = await s.execute(stmt)
            rows = result.scalars().all()
            return [self._rec_to_dict(r, farm_id) for r in rows]

        if session:
            return await _do(session)
        async with get_db_context() as s:
            return await _do(s)

    # ── Actions Log ────────────────────────────────────────────────

    async def log_action(
        self, farm_id: str, action_type: str,
        action_details: str, green_tokens: int = 0,
        session: AsyncSession = None,
    ):
        """Log farming action."""
        async def _do(s: AsyncSession):
            field_id = await self._resolve_field_id(s, farm_id)
            if not field_id:
                return
            obj = ActionLog(
                field_id=field_id,
                action_type=action_type,
                action_details=action_details,
                green_tokens_earned=green_tokens,
            )
            s.add(obj)

        if session:
            await _do(session)
        else:
            async with get_db_context() as s:
                await _do(s)

    async def get_actions_log(
        self, farm_id: str, limit: int = 50,
        session: AsyncSession = None,
    ) -> List[Dict[str, Any]]:
        """Get actions log."""
        async def _do(s: AsyncSession):
            field_id = await self._resolve_field_id(s, farm_id)
            if not field_id:
                return []
            stmt = (
                select(ActionLog)
                .where(ActionLog.field_id == field_id)
                .order_by(desc(ActionLog.created_at))
                .limit(limit)
            )
            result = await s.execute(stmt)
            rows = result.scalars().all()
            return [
                {
                    "id": str(r.id),
                    "farm_id": farm_id,
                    "timestamp": r.created_at.isoformat() if r.created_at else None,
                    "action_type": r.action_type,
                    "action_details": r.action_details,
                    "green_tokens_earned": r.green_tokens_earned,
                }
                for r in rows
            ]

        if session:
            return await _do(session)
        async with get_db_context() as s:
            return await _do(s)

    async def get_action_by_id(
        self, action_id: str, session: AsyncSession = None
    ) -> Optional[Dict[str, Any]]:
        """Get specific action by ID."""
        async def _do(s: AsyncSession):
            try:
                uid = UUID(action_id) if isinstance(action_id, str) else action_id
            except ValueError:
                return None
            stmt = select(ActionLog).where(ActionLog.id == uid)
            result = await s.execute(stmt)
            r = result.scalar_one_or_none()
            if not r:
                return None
            return {
                "id": str(r.id),
                "timestamp": r.created_at.isoformat() if r.created_at else None,
                "action_type": r.action_type,
                "action_details": r.action_details,
                "green_tokens_earned": r.green_tokens_earned,
            }

        if session:
            return await _do(session)
        async with get_db_context() as s:
            return await _do(s)

    async def delete_action(self, action_id: str, session: AsyncSession = None):
        """Delete action from log."""
        async def _do(s: AsyncSession):
            try:
                uid = UUID(action_id) if isinstance(action_id, str) else action_id
            except ValueError:
                return
            stmt = delete(ActionLog).where(ActionLog.id == uid)
            await s.execute(stmt)

        if session:
            await _do(session)
        else:
            async with get_db_context() as s:
                await _do(s)

    # ── Crops ──────────────────────────────────────────────────────

    async def add_crop(
        self, farm_id: str, crop_type: str, planted_date: str,
        expected_harvest_date: str, area_hectares: float,
        status: str = "active", session: AsyncSession = None,
    ) -> str:
        """Add new crop cycle. Returns crop_cycle id."""
        async def _do(s: AsyncSession):
            field_id = await self._resolve_field_id(s, farm_id)
            if not field_id:
                return None
            from datetime import date as d
            obj = CropCycle(
                field_id=field_id,
                crop_name=crop_type,
                planted_date=d.fromisoformat(planted_date) if isinstance(planted_date, str) else planted_date,
                expected_harvest_date=d.fromisoformat(expected_harvest_date) if isinstance(expected_harvest_date, str) else expected_harvest_date,
                status=status,
            )
            s.add(obj)
            await s.flush()
            return str(obj.id)

        if session:
            return await _do(session)
        async with get_db_context() as s:
            return await _do(s)

    async def get_crops(
        self, farm_id: str, status: str = None,
        session: AsyncSession = None,
    ) -> List[Dict[str, Any]]:
        """Get all crops for a farm."""
        async def _do(s: AsyncSession):
            field_id = await self._resolve_field_id(s, farm_id)
            if not field_id:
                return []
            stmt = select(CropCycle).where(CropCycle.field_id == field_id)
            if status:
                stmt = stmt.where(CropCycle.status == status)
            stmt = stmt.order_by(desc(CropCycle.planted_date))
            result = await s.execute(stmt)
            rows = result.scalars().all()
            return [
                {
                    "id": str(r.id),
                    "farm_id": farm_id,
                    "crop_type": r.crop_name,
                    "planted_date": r.planted_date.isoformat() if r.planted_date else None,
                    "expected_harvest_date": r.expected_harvest_date.isoformat() if r.expected_harvest_date else None,
                    "area_hectares": None,  # stored on field now
                    "status": r.status,
                    "growth_stage": r.growth_stage,
                }
                for r in rows
            ]

        if session:
            return await _do(session)
        async with get_db_context() as s:
            return await _do(s)

    async def update_crop_status(
        self, crop_id: str, status: str, session: AsyncSession = None
    ):
        """Update crop status."""
        async def _do(s: AsyncSession):
            try:
                uid = UUID(crop_id) if isinstance(crop_id, str) else crop_id
            except ValueError:
                return
            stmt = (
                update(CropCycle)
                .where(CropCycle.id == uid)
                .values(status=status, updated_at=func.now())
            )
            await s.execute(stmt)

        if session:
            await _do(session)
        else:
            async with get_db_context() as s:
                await _do(s)

    async def delete_crop(self, crop_id: str, session: AsyncSession = None):
        """Delete crop."""
        async def _do(s: AsyncSession):
            try:
                uid = UUID(crop_id) if isinstance(crop_id, str) else crop_id
            except ValueError:
                return
            stmt = delete(CropCycle).where(CropCycle.id == uid)
            await s.execute(stmt)

        if session:
            await _do(session)
        else:
            async with get_db_context() as s:
                await _do(s)

    # ── Agent Memory Logs ──────────────────────────────────────────

    async def store_agent_memory(
        self, farm_id: str, agent_name: str, action: str,
        input_context: dict, output_result: dict,
        summary: str = None, session: AsyncSession = None,
    ):
        """Persist an agent's run to memory."""
        async def _do(s: AsyncSession):
            field_id = await self._resolve_field_id(s, farm_id)
            if not field_id:
                return
            crop_cycle_id = await self._get_active_crop_cycle_id(s, field_id)
            obj = AgentMemoryLog(
                field_id=field_id,
                crop_cycle_id=crop_cycle_id,
                agent_name=agent_name,
                action=action,
                input_context=input_context,
                output_result=output_result,
                summary=summary,
            )
            s.add(obj)

        if session:
            await _do(session)
        else:
            async with get_db_context() as s:
                await _do(s)

    async def get_agent_memory(
        self, farm_id: str, agent_name: str = None, limit: int = 10,
        session: AsyncSession = None,
    ) -> List[Dict[str, Any]]:
        """Get past agent memory logs."""
        async def _do(s: AsyncSession):
            field_id = await self._resolve_field_id(s, farm_id)
            if not field_id:
                return []
            stmt = select(AgentMemoryLog).where(AgentMemoryLog.field_id == field_id)
            if agent_name:
                stmt = stmt.where(AgentMemoryLog.agent_name == agent_name)
            stmt = stmt.order_by(desc(AgentMemoryLog.created_at)).limit(limit)
            result = await s.execute(stmt)
            rows = result.scalars().all()
            return [
                {
                    "id": str(r.id),
                    "agent_name": r.agent_name,
                    "action": r.action,
                    "summary": r.summary,
                    "input_context": r.input_context,
                    "output_result": r.output_result,
                    "timestamp": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ]

        if session:
            return await _do(session)
        async with get_db_context() as s:
            return await _do(s)

    # ── External API Cache ─────────────────────────────────────────

    async def cache_api_response(
        self, source: str, endpoint: str, location: str,
        response_payload: dict, ttl_seconds: int = 1800,
        farm_id: str = None, session: AsyncSession = None,
    ):
        """Cache an external API response."""
        async def _do(s: AsyncSession):
            field_id = None
            if farm_id:
                field_id = await self._resolve_field_id(s, farm_id)
            obj = ExternalApiCache(
                field_id=field_id,
                source=source,
                endpoint=endpoint,
                location=location,
                response_payload=response_payload,
                ttl_seconds=ttl_seconds,
            )
            s.add(obj)

        if session:
            await _do(session)
        else:
            async with get_db_context() as s:
                await _do(s)

    async def get_cached_api_response(
        self, source: str, endpoint: str, location: str,
        max_age_seconds: int = 1800, session: AsyncSession = None,
    ) -> Optional[Dict[str, Any]]:
        """Get a cached API response if still valid."""
        async def _do(s: AsyncSession):
            from datetime import timedelta
            cutoff = datetime.utcnow() - timedelta(seconds=max_age_seconds)
            stmt = (
                select(ExternalApiCache)
                .where(
                    ExternalApiCache.source == source,
                    ExternalApiCache.endpoint == endpoint,
                    ExternalApiCache.location == location,
                    ExternalApiCache.fetched_at >= cutoff,
                )
                .order_by(desc(ExternalApiCache.fetched_at))
                .limit(1)
            )
            result = await s.execute(stmt)
            row = result.scalar_one_or_none()
            if not row:
                return None
            return row.response_payload

        if session:
            return await _do(session)
        async with get_db_context() as s:
            return await _do(s)

    # ── LLM Conversation History ───────────────────────────────────

    async def store_llm_conversation(
        self, farm_id: str, prompt_sent: str, response_received: str,
        model_used: str = "mistral:latest", context_used: dict = None,
        latency_ms: float = None, session: AsyncSession = None,
    ):
        """Log an LLM interaction."""
        async def _do(s: AsyncSession):
            field_id = await self._resolve_field_id(s, farm_id)
            if not field_id:
                return
            obj = LlmConversationHistory(
                field_id=field_id,
                prompt_sent=prompt_sent,
                response_received=response_received,
                model_used=model_used,
                context_used=context_used or {},
                latency_ms=latency_ms,
            )
            s.add(obj)

        if session:
            await _do(session)
        else:
            async with get_db_context() as s:
                await _do(s)

    # ── Field / Farmer Helpers ─────────────────────────────────────

    async def ensure_default_field(
        self, farm_id: str, session: AsyncSession = None
    ) -> str:
        """
        Ensure a default field exists for a legacy farm_id (e.g., FARM001).
        Creates a dummy farmer + field if they don't exist.
        Returns the field UUID as a string.
        """
        async def _do(s: AsyncSession):
            # Check if farmer exists
            stmt = select(Farmer).where(Farmer.farmer_id == farm_id.upper())
            result = await s.execute(stmt)
            farmer = result.scalar_one_or_none()

            if not farmer:
                farmer = Farmer(
                    farmer_id=farm_id.upper(),
                    password_hash="legacy",
                    salt="legacy",
                    name=f"Farmer {farm_id}",
                )
                s.add(farmer)
                await s.flush()

            # Check if default field exists
            stmt2 = select(Field).where(Field.farmer_id == farmer.id)
            result2 = await s.execute(stmt2)
            field = result2.scalar_one_or_none()

            if not field:
                field = Field(
                    farmer_id=farmer.id,
                    field_name=f"Default Field ({farm_id})",
                    area_hectares=2.0,
                    location_name="Default",
                )
                s.add(field)
                await s.flush()

            return field.id

        if session:
            return await _do(session)
        async with get_db_context() as s:
            return await _do(s)

    # ── Internal Helpers ───────────────────────────────────────────

    async def _resolve_field_id(self, s: AsyncSession, farm_id: str) -> Optional[UUID]:
        """
        Resolve a legacy farm_id string (e.g., FARM001) to the UUID of its
        default field. Auto-creates farmer+field if they don't exist.
        """
        # Check if it's already a UUID
        if isinstance(farm_id, UUID):
            return farm_id
        try:
            return UUID(farm_id)
        except (ValueError, AttributeError):
            pass

        # Look up farmer by farmer_id
        stmt = select(Farmer).where(Farmer.farmer_id == farm_id.upper())
        result = await s.execute(stmt)
        farmer = result.scalar_one_or_none()

        if not farmer:
            # Auto-create for legacy compatibility
            farmer = Farmer(
                farmer_id=farm_id.upper(),
                password_hash="legacy",
                salt="legacy",
                name=f"Farmer {farm_id}",
            )
            s.add(farmer)
            await s.flush()

        # Get first field
        stmt2 = select(Field).where(Field.farmer_id == farmer.id).limit(1)
        result2 = await s.execute(stmt2)
        field = result2.scalar_one_or_none()

        if not field:
            field = Field(
                farmer_id=farmer.id,
                field_name=f"Default Field ({farm_id})",
                area_hectares=2.0,
                location_name="Default",
            )
            s.add(field)
            await s.flush()

        return field.id

    async def _get_active_crop_cycle_id(
        self, s: AsyncSession, field_id: UUID
    ) -> Optional[UUID]:
        """Get the active crop cycle for a field, if any."""
        stmt = (
            select(CropCycle.id)
            .where(CropCycle.field_id == field_id, CropCycle.status == "active")
            .order_by(desc(CropCycle.planted_date))
            .limit(1)
        )
        result = await s.execute(stmt)
        row = result.scalar_one_or_none()
        return row

    # ── Serialization Helpers ──────────────────────────────────────

    @staticmethod
    def _sensor_to_dict(r: SensorReading, farm_id: str) -> Dict[str, Any]:
        return {
            "id": str(r.id),
            "farm_id": farm_id,
            "timestamp": r.reading_time.isoformat() if r.reading_time else None,
            "soil_moisture": r.soil_moisture,
            "soil_ph": r.soil_ph,
            "soil_temperature": r.soil_temperature,
            "air_temperature": r.air_temperature,
            "humidity": r.humidity,
            "rainfall": r.rainfall,
            "light_intensity": r.light_intensity,
            "npk_nitrogen": r.npk_nitrogen,
            "npk_phosphorus": r.npk_phosphorus,
            "npk_potassium": r.npk_potassium,
        }

    @staticmethod
    def _rec_to_dict(r: AgentRecommendation, farm_id: str) -> Dict[str, Any]:
        return {
            "id": str(r.id),
            "farm_id": farm_id,
            "timestamp": r.created_at.isoformat() if r.created_at else None,
            "agent_name": r.agent_name,
            "recommendation_type": r.recommendation_type,
            "recommendation_text": r.recommendation_text,
            "priority": r.priority,
            "status": r.status,
            "llm_source": r.llm_source,
        }
