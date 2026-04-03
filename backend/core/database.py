"""
Database Manager - SQLite + JSON Hybrid Storage
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

class Database:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Get absolute path to database directory
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_dir = os.path.join(os.path.dirname(backend_dir), 'database')
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, 'farming_data.db')
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Sensor Data Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                soil_moisture REAL,
                soil_ph REAL,
                soil_temperature REAL,
                air_temperature REAL,
                humidity REAL,
                rainfall REAL,
                light_intensity REAL,
                npk_nitrogen REAL,
                npk_phosphorus REAL,
                npk_potassium REAL
            )
        """)
        
        # Agent Recommendations Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                recommendation_type TEXT,
                recommendation_text TEXT,
                priority TEXT,
                status TEXT DEFAULT 'pending'
            )
        """)
        
        # Crop Data Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crops (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_id TEXT NOT NULL,
                crop_type TEXT NOT NULL,
                planted_date TEXT,
                expected_harvest_date TEXT,
                area_hectares REAL,
                status TEXT DEFAULT 'growing'
            )
        """)
        
        # Actions Log Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS actions_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                action_type TEXT NOT NULL,
                action_details TEXT,
                green_tokens_earned INTEGER DEFAULT 0
            )
        """)
        
        conn.commit()
        conn.close()
    
    def store_sensor_data(self, sensor_readings: List[Dict[str, Any]]):
        """Store sensor data in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for reading in sensor_readings:
            cursor.execute("""
                INSERT INTO sensor_data (
                    farm_id, timestamp, soil_moisture, soil_ph, soil_temperature,
                    air_temperature, humidity, rainfall, light_intensity,
                    npk_nitrogen, npk_phosphorus, npk_potassium
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                reading.get('farm_id'),
                reading.get('timestamp'),
                reading.get('soil_moisture'),
                reading.get('soil_ph'),
                reading.get('soil_temperature'),
                reading.get('air_temperature'),
                reading.get('humidity'),
                reading.get('rainfall'),
                reading.get('light_intensity'),
                reading.get('npk_nitrogen'),
                reading.get('npk_phosphorus'),
                reading.get('npk_potassium')
            ))
        
        conn.commit()
        conn.close()
    
    def get_latest_sensor_data(self, farm_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get latest sensor readings"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM sensor_data 
            WHERE farm_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (farm_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def store_recommendation(self, farm_id: str, agent_name: str, 
                            rec_type: str, rec_text: str, priority: str = "medium"):
        """Store agent recommendation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO recommendations (
                farm_id, timestamp, agent_name, recommendation_type,
                recommendation_text, priority
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            farm_id,
            datetime.now().isoformat(),
            agent_name,
            rec_type,
            rec_text,
            priority
        ))
        
        conn.commit()
        conn.close()
    
    def get_recommendations(self, farm_id: str, status: str = "pending", 
                           limit: int = 20) -> List[Dict[str, Any]]:
        """Get recommendations"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM recommendations 
            WHERE farm_id = ? AND status = ?
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (farm_id, status, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def log_action(self, farm_id: str, action_type: str, 
                   action_details: str, green_tokens: int = 0):
        """Log farming action"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO actions_log (
                farm_id, timestamp, action_type, action_details, green_tokens_earned
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            farm_id,
            datetime.now().isoformat(),
            action_type,
            action_details,
            green_tokens
        ))
        
        conn.commit()
        conn.close()
    
    def get_actions_log(self, farm_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get actions log"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM actions_log 
            WHERE farm_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (farm_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def add_crop(self, farm_id: str, crop_type: str, planted_date: str,
                 expected_harvest_date: str, area_hectares: float, status: str = "growing"):
        """Add new crop"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO crops (
                farm_id, crop_type, planted_date, expected_harvest_date, 
                area_hectares, status
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (farm_id, crop_type, planted_date, expected_harvest_date, area_hectares, status))
        
        conn.commit()
        crop_id = cursor.lastrowid
        conn.close()
        return crop_id
    
    def get_crops(self, farm_id: str, status: str = None) -> List[Dict[str, Any]]:
        """Get all crops for a farm"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if status:
            cursor.execute("""
                SELECT * FROM crops 
                WHERE farm_id = ? AND status = ?
                ORDER BY planted_date DESC
            """, (farm_id, status))
        else:
            cursor.execute("""
                SELECT * FROM crops 
                WHERE farm_id = ?
                ORDER BY planted_date DESC
            """, (farm_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_crop_status(self, crop_id: int, status: str):
        """Update crop status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE crops 
            SET status = ?
            WHERE id = ?
        """, (status, crop_id))
        
        conn.commit()
        conn.close()
    
    def delete_crop(self, crop_id: int):
        """Delete crop"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM crops WHERE id = ?", (crop_id,))
        
        conn.commit()
        conn.close()
    
    def get_action_by_id(self, action_id: int) -> Dict[str, Any]:
        """Get specific action by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM actions_log WHERE id = ?", (action_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def delete_action(self, action_id: int):
        """Delete action from log"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM actions_log WHERE id = ?", (action_id,))
        
        conn.commit()
        conn.close()
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute custom SQL query"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
