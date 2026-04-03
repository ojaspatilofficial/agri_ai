"""
Authentication System
Handles user registration, login, and session management
"""
import hashlib
import secrets
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class AuthenticationSystem:
    """Secure authentication with password hashing"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Get absolute path to database directory
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_dir = os.path.join(os.path.dirname(backend_dir), 'database')
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, 'farming_system.db')
        self.db_path = db_path
        self._init_users_table()
    
    def _init_users_table(self):
        """Create users table if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                farmer_id TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                language TEXT DEFAULT 'en',
                created_at TEXT NOT NULL,
                last_login TEXT,
                is_active INTEGER DEFAULT 1
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                farmer_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (farmer_id) REFERENCES users(farmer_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _hash_password(self, password: str, salt: str = None) -> tuple:
        """Hash password with salt using SHA-256"""
        if salt is None:
            salt = secrets.token_hex(32)
        
        # Combine password and salt
        password_salt = f"{password}{salt}".encode('utf-8')
        
        # Hash using SHA-256
        password_hash = hashlib.sha256(password_salt).hexdigest()
        
        return password_hash, salt
    
    def register_user(self, farmer_id: str, password: str, name: str, 
                     email: str = None, phone: str = None, language: str = "en") -> Dict[str, Any]:
        """
        Register a new user
        
        Args:
            farmer_id: Unique farmer ID (e.g., FARM001)
            password: User password (min 6 characters)
            name: User's full name
            email: Optional email
            phone: Optional phone number
            language: Preferred language (en/hi/mr)
        
        Returns:
            Dict with success status and message
        """
        try:
            # Validation
            if not farmer_id or not password or not name:
                return {
                    "success": False,
                    "error": "Farmer ID, password, and name are required"
                }
            
            # Check password strength
            if len(password) < 6:
                return {
                    "success": False,
                    "error": "Password must be at least 6 characters long"
                }
            
            # Normalize farmer_id
            farmer_id = farmer_id.upper().strip()
            
            # Check if user already exists
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT farmer_id FROM users WHERE farmer_id = ?", (farmer_id,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                conn.close()
                return {
                    "success": False,
                    "error": f"User with Farmer ID '{farmer_id}' already exists"
                }
            
            # Hash password
            password_hash, salt = self._hash_password(password)
            
            # Insert new user
            cursor.execute("""
                INSERT INTO users (farmer_id, password_hash, salt, name, email, phone, language, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                farmer_id,
                password_hash,
                salt,
                name,
                email,
                phone,
                language,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "message": f"User '{farmer_id}' registered successfully",
                "farmer_id": farmer_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Registration failed: {str(e)}"
            }
    
    def login_user(self, farmer_id: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user login
        
        Args:
            farmer_id: Farmer ID
            password: User password
        
        Returns:
            Dict with success status, session_id, and user data
        """
        try:
            if not farmer_id or not password:
                return {
                    "success": False,
                    "error": "Farmer ID and password are required"
                }
            
            farmer_id = farmer_id.upper().strip()
            
            # Get user from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT farmer_id, password_hash, salt, name, email, phone, language, is_active
                FROM users
                WHERE farmer_id = ?
            """, (farmer_id,))
            
            user = cursor.fetchone()
            
            if not user:
                conn.close()
                return {
                    "success": False,
                    "error": "Invalid Farmer ID or password"
                }
            
            (stored_id, stored_hash, salt, name, email, phone, language, is_active) = user
            
            # Check if account is active
            if not is_active:
                conn.close()
                return {
                    "success": False,
                    "error": "Account is deactivated. Contact support."
                }
            
            # Verify password
            password_hash, _ = self._hash_password(password, salt)
            
            if password_hash != stored_hash:
                conn.close()
                return {
                    "success": False,
                    "error": "Invalid Farmer ID or password"
                }
            
            # Create session
            session_id = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(days=7)  # 7 day session
            
            cursor.execute("""
                INSERT INTO sessions (session_id, farmer_id, created_at, expires_at)
                VALUES (?, ?, ?, ?)
            """, (
                session_id,
                farmer_id,
                datetime.now().isoformat(),
                expires_at.isoformat()
            ))
            
            # Update last login
            cursor.execute("""
                UPDATE users
                SET last_login = ?
                WHERE farmer_id = ?
            """, (datetime.now().isoformat(), farmer_id))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "message": "Login successful",
                "session_id": session_id,
                "user": {
                    "farmer_id": farmer_id,
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "language": language
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Login failed: {str(e)}"
            }
    
    def verify_session(self, session_id: str) -> Dict[str, Any]:
        """
        Verify if session is valid
        
        Args:
            session_id: Session token
        
        Returns:
            Dict with validity status and user data
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT s.farmer_id, s.expires_at, u.name, u.email, u.phone, u.language
                FROM sessions s
                JOIN users u ON s.farmer_id = u.farmer_id
                WHERE s.session_id = ? AND s.is_active = 1
            """, (session_id,))
            
            session = cursor.fetchone()
            conn.close()
            
            if not session:
                return {
                    "valid": False,
                    "error": "Invalid session"
                }
            
            (farmer_id, expires_at, name, email, phone, language) = session
            
            # Check if session expired
            if datetime.fromisoformat(expires_at) < datetime.now():
                return {
                    "valid": False,
                    "error": "Session expired. Please login again."
                }
            
            return {
                "valid": True,
                "user": {
                    "farmer_id": farmer_id,
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "language": language
                }
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Session verification failed: {str(e)}"
            }
    
    def logout_user(self, session_id: str) -> Dict[str, Any]:
        """
        Logout user by invalidating session
        
        Args:
            session_id: Session token
        
        Returns:
            Dict with success status
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE sessions
                SET is_active = 0
                WHERE session_id = ?
            """, (session_id,))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "message": "Logged out successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Logout failed: {str(e)}"
            }
    
    def change_password(self, farmer_id: str, old_password: str, new_password: str) -> Dict[str, Any]:
        """
        Change user password
        
        Args:
            farmer_id: Farmer ID
            old_password: Current password
            new_password: New password
        
        Returns:
            Dict with success status
        """
        try:
            # Verify old password
            login_result = self.login_user(farmer_id, old_password)
            if not login_result["success"]:
                return {
                    "success": False,
                    "error": "Current password is incorrect"
                }
            
            # Validate new password
            if len(new_password) < 6:
                return {
                    "success": False,
                    "error": "New password must be at least 6 characters long"
                }
            
            # Hash new password
            password_hash, salt = self._hash_password(new_password)
            
            # Update password
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users
                SET password_hash = ?, salt = ?
                WHERE farmer_id = ?
            """, (password_hash, salt, farmer_id.upper()))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "message": "Password changed successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Password change failed: {str(e)}"
            }
    
    def get_all_users(self) -> list:
        """Get list of all registered users (for admin)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT farmer_id, name, email, phone, language, created_at, last_login, is_active
                FROM users
                ORDER BY created_at DESC
            """)
            
            users = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "farmer_id": u[0],
                    "name": u[1],
                    "email": u[2],
                    "phone": u[3],
                    "language": u[4],
                    "created_at": u[5],
                    "last_login": u[6],
                    "is_active": bool(u[7])
                }
                for u in users
            ]
            
        except Exception as e:
            return []


# Example usage
if __name__ == "__main__":
    auth = AuthenticationSystem()
    
    # Test registration
    print("=== Testing Registration ===")
    result = auth.register_user(
        farmer_id="FARM001",
        password="secure123",
        name="Ravi Kumar",
        email="ravi@example.com",
        phone="+919876543210",
        language="hi"
    )
    print(result)
    
    # Test login
    print("\n=== Testing Login ===")
    result = auth.login_user("FARM001", "secure123")
    print(result)
    
    if result["success"]:
        session_id = result["session_id"]
        
        # Test session verification
        print("\n=== Testing Session Verification ===")
        result = auth.verify_session(session_id)
        print(result)
        
        # Test logout
        print("\n=== Testing Logout ===")
        result = auth.logout_user(session_id)
        print(result)
