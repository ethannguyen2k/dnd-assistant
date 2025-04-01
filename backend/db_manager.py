# db_manager.py
import sqlite3
import json
import uuid
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="game_data.db"):
        self.db_path = db_path
        self.setup_database()
    
    def get_connection(self):
        """Create and return a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access rows as dictionaries
        return conn
    
    def setup_database(self):
        """Create necessary tables if they don't exist."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create sessions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            created_at TIMESTAMP,
            last_active TIMESTAMP,
            game_state TEXT DEFAULT 'character_creation'
        )
        ''')
        
        # Create characters table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS characters (
            character_id TEXT PRIMARY KEY,
            session_id TEXT,
            name TEXT,
            race TEXT,
            class TEXT,
            background TEXT,
            stats TEXT,
            inventory TEXT,
            created_at TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        )
        ''')
        # stats TEXT,  # JSON string of all character stats
        # inventory TEXT,  # JSON string of inventory items
        
        # Create messages history table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            message_id TEXT PRIMARY KEY,
            session_id TEXT,
            role TEXT,
            content TEXT,
            timestamp TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        )
        ''')
        # role TEXT,  # 'user' or 'assistant'
        
        conn.commit()
        conn.close()
    
    def create_session(self):
        """Create a new game session and return the session ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        session_id = str(uuid.uuid4())
        now = datetime.now()
        
        cursor.execute(
            'INSERT INTO sessions (session_id, created_at, last_active) VALUES (?, ?, ?)',
            (session_id, now, now)
        )
        
        conn.commit()
        conn.close()
        
        return session_id
    
    def update_session_activity(self, session_id):
        """Update the last_active timestamp for a session."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE sessions SET last_active = ? WHERE session_id = ?',
            (datetime.now(), session_id)
        )
        
        conn.commit()
        conn.close()
    
    def update_game_state(self, session_id, game_state):
        """Update the game state for a session."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE sessions SET game_state = ? WHERE session_id = ?',
            (game_state, session_id)
        )
        
        conn.commit()
        conn.close()
    
    def get_game_state(self, session_id):
        """Get the current game state for a session."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT game_state FROM sessions WHERE session_id = ?', (session_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return result['game_state']
        return None
    
    def save_character(self, session_id, character_data):
        """Save or update character information."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if character already exists for this session
        cursor.execute('SELECT character_id FROM characters WHERE session_id = ?', (session_id,))
        result = cursor.fetchone()
        
        character_id = result['character_id'] if result else str(uuid.uuid4())
        now = datetime.now()
        
        # Extract specific fields, store the rest as JSON
        name = character_data.get('name', '')
        race = character_data.get('race', '')
        character_class = character_data.get('class', '')
        background = character_data.get('background', '')
        
        # Remove fields that are stored separately
        for field in ['name', 'race', 'class', 'background']:
            if field in character_data:
                del character_data[field]
        
        # Store remaining data as JSON
        stats = json.dumps(character_data)
        
        if result:
            # Update existing character
            cursor.execute('''
            UPDATE characters 
            SET name = ?, race = ?, class = ?, background = ?, stats = ?
            WHERE character_id = ?
            ''', (name, race, character_class, background, stats, character_id))
        else:
            # Insert new character
            cursor.execute('''
            INSERT INTO characters 
            (character_id, session_id, name, race, class, background, stats, inventory, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (character_id, session_id, name, race, character_class, background, stats, 
                 json.dumps([]), now))
        
        conn.commit()
        conn.close()
        
        return character_id
    
    def get_character(self, session_id):
        """Get character information for a session."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT name, race, class, background, stats, inventory
        FROM characters WHERE session_id = ?
        ''', (session_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return None
        
        # Combine specific fields with JSON data
        character = {
            'name': result['name'],
            'race': result['race'],
            'class': result['class'],
            'background': result['background'],
        }
        
        # Add stats from JSON
        stats = json.loads(result['stats']) if result['stats'] else {}
        character.update(stats)
        
        # Add inventory
        character['inventory'] = json.loads(result['inventory']) if result['inventory'] else []
        
        return character
    
    def save_message(self, session_id, role, content):
        """Save a message to the history."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        message_id = str(uuid.uuid4())
        now = datetime.now()
        
        cursor.execute(
            'INSERT INTO messages (message_id, session_id, role, content, timestamp) VALUES (?, ?, ?, ?, ?)',
            (message_id, session_id, role, content, now)
        )
        
        conn.commit()
        conn.close()
        
        return message_id
    
    def get_messages(self, session_id, limit=20):
        """Get recent messages for a session."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT role, content FROM messages 
        WHERE session_id = ? 
        ORDER BY timestamp ASC
        LIMIT ?
        ''', (session_id, limit))
        
        messages = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return messages