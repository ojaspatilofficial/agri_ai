"""
Authentication System — Async SQLAlchemy + PostgreSQL
=====================================================
Replaces raw sqlite3. Uses shared PostgreSQL database with
Farmer and Session ORM models.
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.db_models import Farmer, Session
from core.db_session import get_db_context


class AuthenticationSystem:
    """Async authentication with password hashing — PostgreSQL backed."""

    # ── Password Hashing ───────────────────────────────────────────

    @staticmethod
    def _hash_password(password: str, salt: str = None) -> tuple:
        """Hash password with salt using SHA-256."""
        if salt is None:
            salt = secrets.token_hex(32)
        password_salt = f"{password}{salt}".encode("utf-8")
        password_hash = hashlib.sha256(password_salt).hexdigest()
        return password_hash, salt

    # ── Register ───────────────────────────────────────────────────

    async def register_user(
        self, farmer_id: str, password: str, name: str,
        email: str = None, phone: str = None, language: str = "en",
        session: AsyncSession = None,
    ) -> Dict[str, Any]:
        """Register a new user."""
        async def _do(s: AsyncSession):
            if not farmer_id or not password or not name:
                return {"success": False, "error": "Farmer ID, password, and name are required"}
            if len(password) < 6:
                return {"success": False, "error": "Password must be at least 6 characters long"}

            fid = farmer_id.upper().strip()

            # Check if already exists
            stmt = select(Farmer).where(Farmer.farmer_id == fid)
            result = await s.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                return {"success": False, "error": f"User with Farmer ID '{fid}' already exists"}

            password_hash, salt = self._hash_password(password)

            farmer = Farmer(
                farmer_id=fid,
                password_hash=password_hash,
                salt=salt,
                name=name,
                email=email,
                phone=phone,
                language=language,
            )
            s.add(farmer)
            await s.flush()

            return {
                "success": True,
                "message": f"User '{fid}' registered successfully",
                "farmer_id": fid,
            }

        try:
            if session:
                return await _do(session)
            async with get_db_context() as s:
                return await _do(s)
        except Exception as e:
            return {"success": False, "error": f"Registration failed: {str(e)}"}

    # ── Login ──────────────────────────────────────────────────────

    async def login_user(
        self, farmer_id: str, password: str,
        session: AsyncSession = None,
    ) -> Dict[str, Any]:
        """Authenticate user login, creates a session."""
        async def _do(s: AsyncSession):
            if not farmer_id or not password:
                return {"success": False, "error": "Farmer ID and password are required"}

            fid = farmer_id.upper().strip()

            stmt = select(Farmer).where(Farmer.farmer_id == fid)
            result = await s.execute(stmt)
            farmer = result.scalar_one_or_none()

            if not farmer:
                return {"success": False, "error": "Invalid Farmer ID or password"}
            if not farmer.is_active:
                return {"success": False, "error": "Account is deactivated. Contact support."}

            password_hash, _ = self._hash_password(password, farmer.salt)
            if password_hash != farmer.password_hash:
                return {"success": False, "error": "Invalid Farmer ID or password"}

            # Create session
            session_token = secrets.token_urlsafe(32)
            now = datetime.now(timezone.utc)
            expires = now + timedelta(days=7)

            sess = Session(
                farmer_id=farmer.id,
                session_token=session_token,
                created_at=now,
                expires_at=expires,
            )
            s.add(sess)

            # Update last login
            farmer.updated_at = now
            await s.flush()

            return {
                "success": True,
                "message": "Login successful",
                "session_id": session_token,
                "user": {
                    "farmer_id": farmer.farmer_id,
                    "name": farmer.name,
                    "email": farmer.email,
                    "phone": farmer.phone,
                    "language": farmer.language,
                },
            }

        try:
            if session:
                return await _do(session)
            async with get_db_context() as s:
                return await _do(s)
        except Exception as e:
            return {"success": False, "error": f"Login failed: {str(e)}"}

    # ── Verify Session ─────────────────────────────────────────────

    async def verify_session(
        self, session_id: str, session: AsyncSession = None
    ) -> Dict[str, Any]:
        """Verify if session is valid."""
        async def _do(s: AsyncSession):
            stmt = (
                select(Session, Farmer)
                .join(Farmer, Session.farmer_id == Farmer.id)
                .where(
                    Session.session_token == session_id,
                    Session.is_active == True,
                )
            )
            result = await s.execute(stmt)
            row = result.first()

            if not row:
                return {"valid": False, "error": "Invalid session"}

            sess_obj, farmer = row
            now = datetime.now(timezone.utc)
            expires = sess_obj.expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)

            if expires < now:
                return {"valid": False, "error": "Session expired. Please login again."}

            return {
                "valid": True,
                "user": {
                    "farmer_id": farmer.farmer_id,
                    "name": farmer.name,
                    "email": farmer.email,
                    "phone": farmer.phone,
                    "language": farmer.language,
                },
            }

        try:
            if session:
                return await _do(session)
            async with get_db_context() as s:
                return await _do(s)
        except Exception as e:
            return {"valid": False, "error": f"Session verification failed: {str(e)}"}

    # ── Logout ─────────────────────────────────────────────────────

    async def logout_user(
        self, session_id: str, session: AsyncSession = None
    ) -> Dict[str, Any]:
        """Logout user by invalidating session."""
        async def _do(s: AsyncSession):
            stmt = (
                update(Session)
                .where(Session.session_token == session_id)
                .values(is_active=False)
            )
            await s.execute(stmt)
            return {"success": True, "message": "Logged out successfully"}

        try:
            if session:
                return await _do(session)
            async with get_db_context() as s:
                return await _do(s)
        except Exception as e:
            return {"success": False, "error": f"Logout failed: {str(e)}"}

    # ── Change Password ────────────────────────────────────────────

    async def change_password(
        self, farmer_id: str, old_password: str, new_password: str,
        session: AsyncSession = None,
    ) -> Dict[str, Any]:
        """Change user password."""
        async def _do(s: AsyncSession):
            # Verify old password
            fid = farmer_id.upper().strip()
            stmt = select(Farmer).where(Farmer.farmer_id == fid)
            result = await s.execute(stmt)
            farmer = result.scalar_one_or_none()

            if not farmer:
                return {"success": False, "error": "User not found"}

            old_hash, _ = self._hash_password(old_password, farmer.salt)
            if old_hash != farmer.password_hash:
                return {"success": False, "error": "Current password is incorrect"}

            if len(new_password) < 6:
                return {"success": False, "error": "New password must be at least 6 characters long"}

            new_hash, new_salt = self._hash_password(new_password)
            farmer.password_hash = new_hash
            farmer.salt = new_salt
            await s.flush()

            return {"success": True, "message": "Password changed successfully"}

        try:
            if session:
                return await _do(session)
            async with get_db_context() as s:
                return await _do(s)
        except Exception as e:
            return {"success": False, "error": f"Password change failed: {str(e)}"}

    # ── Admin ──────────────────────────────────────────────────────

    async def get_all_users(self, session: AsyncSession = None) -> list:
        """Get list of all registered users (for admin)."""
        async def _do(s: AsyncSession):
            stmt = select(Farmer).order_by(Farmer.created_at.desc())
            result = await s.execute(stmt)
            farmers = result.scalars().all()
            return [
                {
                    "farmer_id": f.farmer_id,
                    "name": f.name,
                    "email": f.email,
                    "phone": f.phone,
                    "language": f.language,
                    "created_at": f.created_at.isoformat() if f.created_at else None,
                    "last_login": f.updated_at.isoformat() if f.updated_at else None,
                    "is_active": f.is_active,
                }
                for f in farmers
            ]

        try:
            if session:
                return await _do(session)
            async with get_db_context() as s:
                return await _do(s)
        except Exception:
            return []
