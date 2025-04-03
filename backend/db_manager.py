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
        
        # Create locations table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            location_id TEXT PRIMARY KEY,
            session_id TEXT,
            name TEXT,
            description TEXT,
            type TEXT,
            details TEXT,
            created_at TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        )
        ''')
        # details TEXT,  # JSON string of additional details
        
        # Create NPCs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS npcs (
            npc_id TEXT PRIMARY KEY,
            session_id TEXT,
            name TEXT,
            description TEXT,
            role TEXT,
            details TEXT,
            location_id TEXT,
            created_at TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id),
            FOREIGN KEY (location_id) REFERENCES locations (location_id)
        )
        ''')
        # details TEXT,  # JSON string of additional details
        
        # Create quests table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS quests (
            quest_id TEXT PRIMARY KEY,
            session_id TEXT,
            title TEXT,
            description TEXT,
            status TEXT,
            details TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        )
        ''')
        # details TEXT,  # JSON string of additional details
        
        # Create combat_state table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS combat_state (
            combat_id TEXT PRIMARY KEY,
            session_id TEXT,
            is_in_combat BOOLEAN,
            initiative_order TEXT,
            current_combatant TEXT,
            round INTEGER,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        )
        ''')
        # initiative_order TEXT,  # JSON string of initiative order
        
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
        
        # Create a copy of character_data to avoid modifying the original
        stats_data = character_data.copy()
        
        # Remove fields that are stored separately
        for field in ['name', 'race', 'class', 'background']:
            if field in stats_data:
                del stats_data[field]
        
        # Handle inventory separately
        inventory = stats_data.pop('inventory', [])
        
        # Store remaining data as JSON
        stats = json.dumps(stats_data)
        inventory_json = json.dumps(inventory)
        
        if result:
            # Update existing character
            cursor.execute('''
            UPDATE characters 
            SET name = ?, race = ?, class = ?, background = ?, stats = ?, inventory = ?
            WHERE character_id = ?
            ''', (name, race, character_class, background, stats, inventory_json, character_id))
        else:
            # Insert new character
            cursor.execute('''
            INSERT INTO characters 
            (character_id, session_id, name, race, class, background, stats, inventory, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (character_id, session_id, name, race, character_class, background, stats, 
                 inventory_json, now))
        
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
    
    # New methods for world building
    
    def add_location(self, session_id, location_data):
        """Add a new location to the game world."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        location_id = str(uuid.uuid4())
        now = datetime.now()
        
        name = location_data.get('name', '')
        description = location_data.get('description', '')
        location_type = location_data.get('type', '')
        
        # Store additional details as JSON
        details_data = location_data.copy()
        for field in ['name', 'description', 'type']:
            if field in details_data:
                del details_data[field]
        
        details = json.dumps(details_data)
        
        cursor.execute('''
        INSERT INTO locations
        (location_id, session_id, name, description, type, details, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (location_id, session_id, name, description, location_type, details, now))
        
        conn.commit()
        conn.close()
        
        return location_id
    
    def get_locations(self, session_id):
        """Get all locations for a session."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT location_id, name, description, type, details
        FROM locations WHERE session_id = ?
        ''', (session_id,))
        
        locations = []
        for row in cursor.fetchall():
            location = {
                'id': row['location_id'],
                'name': row['name'],
                'description': row['description'],
                'type': row['type']
            }
            # Add details from JSON
            details = json.loads(row['details']) if row['details'] else {}
            location.update(details)
            locations.append(location)
        
        conn.close()
        return locations
    
    def add_npc(self, session_id, npc_data):
        """Add a new NPC to the game world."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        npc_id = str(uuid.uuid4())
        now = datetime.now()
        
        name = npc_data.get('name', '')
        description = npc_data.get('description', '')
        role = npc_data.get('role', '')
        location_name = npc_data.get('location', '')
        
        # Get location ID if provided
        location_id = None
        if location_name:
            cursor.execute('SELECT location_id FROM locations WHERE name = ? AND session_id = ?', 
                          (location_name, session_id))
            location_result = cursor.fetchone()
            if location_result:
                location_id = location_result['location_id']
        
        # Store additional details as JSON
        details_data = npc_data.copy()
        for field in ['name', 'description', 'role', 'location']:
            if field in details_data:
                del details_data[field]
        
        details = json.dumps(details_data)
        
        cursor.execute('''
        INSERT INTO npcs
        (npc_id, session_id, name, description, role, details, location_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (npc_id, session_id, name, description, role, details, location_id, now))
        
        conn.commit()
        conn.close()
        
        return npc_id
    
    def get_npcs(self, session_id, location_id=None):
        """Get NPCs for a session, optionally filtered by location."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if location_id:
            cursor.execute('''
            SELECT npc_id, name, description, role, details
            FROM npcs WHERE session_id = ? AND location_id = ?
            ''', (session_id, location_id))
        else:
            cursor.execute('''
            SELECT npc_id, name, description, role, details, location_id
            FROM npcs WHERE session_id = ?
            ''', (session_id,))
        
        npcs = []
        for row in cursor.fetchall():
            npc = {
                'id': row['npc_id'],
                'name': row['name'],
                'description': row['description'],
                'role': row['role']
            }
            # Add details from JSON
            details = json.loads(row['details']) if row['details'] else {}
            npc.update(details)
            
            # Add location name if available
            if 'location_id' in row and row['location_id']:
                cursor.execute('SELECT name FROM locations WHERE location_id = ?', (row['location_id'],))
                location_result = cursor.fetchone()
                if location_result:
                    npc['location'] = location_result['name']
            
            npcs.append(npc)
        
        conn.close()
        return npcs
    
    def update_quest(self, session_id, quest_data):
        """Create or update a quest."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        title = quest_data.get('title', '')
        now = datetime.now()
        
        # Check if quest already exists
        cursor.execute('SELECT quest_id FROM quests WHERE title = ? AND session_id = ?', 
                      (title, session_id))
        result = cursor.fetchone()
        
        if result:
            quest_id = result['quest_id']
            # Update existing quest
            description = quest_data.get('description', '')
            status = quest_data.get('status', 'not_started')
            
            # Store additional details as JSON
            details_data = quest_data.copy()
            for field in ['title', 'description', 'status']:
                if field in details_data:
                    del details_data[field]
            
            details = json.dumps(details_data)
            
            cursor.execute('''
            UPDATE quests 
            SET description = ?, status = ?, details = ?, updated_at = ?
            WHERE quest_id = ?
            ''', (description, status, details, now, quest_id))
        else:
            # Create new quest
            quest_id = str(uuid.uuid4())
            description = quest_data.get('description', '')
            status = quest_data.get('status', 'not_started')
            
            # Store additional details as JSON
            details_data = quest_data.copy()
            for field in ['title', 'description', 'status']:
                if field in details_data:
                    del details_data[field]
            
            details = json.dumps(details_data)
            
            cursor.execute('''
            INSERT INTO quests
            (quest_id, session_id, title, description, status, details, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (quest_id, session_id, title, description, status, details, now, now))
        
        conn.commit()
        conn.close()
        
        return quest_id
    
    def get_quests(self, session_id, status=None):
        """Get quests for a session, optionally filtered by status."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute('''
            SELECT quest_id, title, description, status, details
            FROM quests WHERE session_id = ? AND status = ?
            ''', (session_id, status))
        else:
            cursor.execute('''
            SELECT quest_id, title, description, status, details
            FROM quests WHERE session_id = ?
            ''', (session_id,))
        
        quests = []
        for row in cursor.fetchall():
            quest = {
                'id': row['quest_id'],
                'title': row['title'],
                'description': row['description'],
                'status': row['status']
            }
            # Add details from JSON
            details = json.loads(row['details']) if row['details'] else {}
            quest.update(details)
            quests.append(quest)
        
        conn.close()
        return quests
    
    def update_combat_state(self, session_id, combat_data):
        """Update the combat state for a session."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now()
        is_in_combat = combat_data.get('is_in_combat', False)
        
        # Check if combat state already exists
        cursor.execute('SELECT combat_id FROM combat_state WHERE session_id = ?', (session_id,))
        result = cursor.fetchone()
        
        # Convert initiative order to JSON
        initiative_order = json.dumps(combat_data.get('initiative_order', []))
        current_combatant = combat_data.get('current_combatant', '')
        round_num = combat_data.get('round', 1)
        
        if result:
            combat_id = result['combat_id']
            # Update existing combat state
            cursor.execute('''
            UPDATE combat_state 
            SET is_in_combat = ?, initiative_order = ?, current_combatant = ?, 
                round = ?, updated_at = ?
            WHERE combat_id = ?
            ''', (is_in_combat, initiative_order, current_combatant, round_num, now, combat_id))
        else:
            # Create new combat state
            combat_id = str(uuid.uuid4())
            cursor.execute('''
            INSERT INTO combat_state
            (combat_id, session_id, is_in_combat, initiative_order, current_combatant, 
             round, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (combat_id, session_id, is_in_combat, initiative_order, current_combatant, 
                 round_num, now, now))
        
        conn.commit()
        conn.close()
        
        return combat_id
    
    def get_combat_state(self, session_id):
        """Get the current combat state for a session."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT combat_id, is_in_combat, initiative_order, current_combatant, round
        FROM combat_state WHERE session_id = ?
        ''', (session_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return {'is_in_combat': False}
        
        combat_state = {
            'id': result['combat_id'],
            'is_in_combat': bool(result['is_in_combat']),
            'current_combatant': result['current_combatant'],
            'round': result['round']
        }
        
        # Parse initiative order from JSON
        if result['initiative_order']:
            combat_state['initiative_order'] = json.loads(result['initiative_order'])
        else:
            combat_state['initiative_order'] = []
        
        return combat_state