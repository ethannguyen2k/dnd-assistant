# function_handler.py
import json
import re
import random
from datetime import datetime

class FunctionHandler:
    def __init__(self, db_manager, vector_db_manager=None):
        self.db = db_manager
        self.vector_db = vector_db_manager  # Add vector DB manager
    
    def parse_and_execute_functions(self, ai_response, session_id):
        """Parse the AI response for function calls and execute them."""
        # Extract all function calls using regex pattern
        # Original pattern for backward compatibility
        function_pattern = r'```function\s+(\w+)\s*\((.*?)\)\s*```'
        function_calls = re.findall(function_pattern, ai_response, re.DOTALL)
        
        # Alternative pattern without code blocks
        alt_function_pattern = r'function\s+(\w+)\s*\((.*?)\)'
        function_calls.extend(re.findall(alt_function_pattern, ai_response, re.DOTALL))
        
        results = []
        
        for func_name, func_args_str in function_calls:
            # Try to parse arguments as JSON, fallback to simpler parsing if it fails
            try:
                func_args = json.loads(func_args_str)
            except json.JSONDecodeError:
                # Simple parsing for key-value pairs: key: value format
                func_args = {}
                for line in func_args_str.split('\n'):
                    line = line.strip()
                    if ':' in line:
                        key, value = line.split(':', 1)
                        func_args[key.strip()] = value.strip()
            
            # Execute the function if it exists
            result = self._execute_function(func_name, func_args, session_id)
            results.append(result)
        
        # Return the cleaned response and function results
        cleaned_response = re.sub(function_pattern, '', ai_response)
        cleaned_response = re.sub(alt_function_pattern, '', cleaned_response)
        return cleaned_response, results
    
    def _execute_function(self, func_name, args, session_id):
        """Execute a function with the given name and arguments."""
        func_mapping = {
            'update_character': self._update_character,
            'add_world_location': self._add_world_location,
            'add_npc': self._add_npc,
            'update_quest': self._update_quest,
            'update_combat_state': self._update_combat_state,
            'start_adventure': self._handle_adventure_start,
        }
        
        if func_name in func_mapping:
            return func_mapping[func_name](args, session_id)
        else:
            return {
                'error': f"Unknown function: {func_name}"
            }
    
    def _update_character(self, args, session_id):
        """Update character information."""
        try:
            character_id = self.db.save_character(session_id, args)
            
            # Also store in vector DB if available
            if self.vector_db:
                vector_character_id = self.vector_db.add_character_memory(session_id, args)
            
            return {
                'success': True,
                'function': 'update_character',
                'character_id': character_id
            }
        except Exception as e:
            return {
                'success': False,
                'function': 'update_character',
                'error': str(e)
            }
    
    def _add_world_location(self, args, session_id):
        """Add a location to the game world."""
        try:
            location_id = self.db.add_location(session_id, args)
            
            # Also store in vector DB if available
            if self.vector_db:
                vector_location_id = self.vector_db.add_location_memory(session_id, args)
            
            return {
                'success': True,
                'function': 'add_world_location',
                'location_id': location_id,
                'location_name': args.get('name', '')
            }
        except Exception as e:
            return {
                'success': False,
                'function': 'add_world_location',
                'error': str(e)
            }
    
    def _add_npc(self, args, session_id):
        """Add an NPC to the game world."""
        try:
            npc_id = self.db.add_npc(session_id, args)
            
            # Also store in vector DB if available
            if self.vector_db:
                vector_npc_id = self.vector_db.add_npc_memory(session_id, args)
            
            return {
                'success': True,
                'function': 'add_npc',
                'npc_id': npc_id,
                'npc_name': args.get('name', '')
            }
        except Exception as e:
            return {
                'success': False,
                'function': 'add_npc',
                'error': str(e)
            }
    
    def _update_quest(self, args, session_id):
        """Create or update a quest."""
        try:
            quest_id = self.db.update_quest(session_id, args)
            
            # Also store in vector DB if available
            if self.vector_db:
                vector_quest_id = self.vector_db.add_quest_memory(session_id, args)
            
            return {
                'success': True,
                'function': 'update_quest',
                'quest_id': quest_id,
                'quest_title': args.get('title', '')
            }
        except Exception as e:
            return {
                'success': False,
                'function': 'update_quest',
                'error': str(e)
            }
        
    def _update_combat_state(self, args, session_id):
        """Update the combat state."""
        try:
            combat_id = self.db.update_combat_state(session_id, args)
            
            # If combat is starting, update game state
            if args.get('is_in_combat', False):
                self.db.update_game_state(session_id, "combat")
            else:
                # If combat is ending, return to adventure mode
                self.db.update_game_state(session_id, "adventure")
            
            return {
                'success': True,
                'function': 'update_combat_state',
                'combat_id': combat_id,
                'is_in_combat': args.get('is_in_combat', False)
            }
        except Exception as e:
            return {
                'success': False,
                'function': 'update_combat_state',
                'error': str(e)
            }
        
    def _handle_adventure_start(self, args, session_id):
        """Update game state to adventure when character creation is complete."""
        self.db.update_game_state(session_id, "adventure")
        return {
            'success': True,
            'function': 'start_adventure',
            'message': 'Transitioned to adventure mode'
        }