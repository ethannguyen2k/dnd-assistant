from flask import Flask, request, jsonify, session
from flask_cors import CORS
import requests
import json
import uuid
from datetime import datetime
import traceback
from db_manager import DatabaseManager
from prompts import get_system_prompt
from function_handler import FunctionHandler
from function_schemas import FUNCTION_SCHEMAS

app = Flask(__name__)
CORS(app, supports_credentials=True)  # Enable CORS with credentials support
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure random key

# Initialize database and function handler
db = DatabaseManager()
function_handler = FunctionHandler(db)

# Ollama API endpoint - adjust if Ollama is running on a different host
OLLAMA_API_URL = "http://localhost:11434/api/generate"

@app.route('/session', methods=['POST'])
def create_session():
    """Create a new game session."""
    session_id = db.create_session()
    return jsonify({"session_id": session_id})

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        session_id = data.get('session_id', '')
        
        # If no session_id provided, create a new one
        if not session_id:
            session_id = db.create_session()
        else:
            # Update last active timestamp
            db.update_session_activity(session_id)
        
        # Get current game state
        game_state = db.get_game_state(session_id) or "character_creation"
        
        # Get message history from database
        message_history = db.get_messages(session_id)
        
        # Save user message to database
        db.save_message(session_id, "user", user_message)
        
        # Get character information if available
        character = db.get_character(session_id)
        
        # Get world information if available
        locations = db.get_locations(session_id)
        npcs = db.get_npcs(session_id)
        quests = db.get_quests(session_id)
        combat_state = db.get_combat_state(session_id)
        
        # Format message history and add system prompt
        system_prompt = get_system_prompt(game_state)
        formatted_messages = format_messages(
            message_history, 
            user_message, 
            system_prompt, 
            character, 
            locations, 
            npcs, 
            quests, 
            combat_state
        )
        
        # Call Ollama API
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": "mistral-nemo:latest",  # Replace with your preferred model
                "prompt": formatted_messages,
                "stream": False
            }
        )
        
        if response.status_code != 200:
            return jsonify({
                "error": "Error from Ollama API",
                "details": response.text
            }), 500
        
        response_data = response.json()
        ai_response = response_data.get('response', 'No response generated')
        
        # Process function calls in the response
        cleaned_response, function_results = function_handler.parse_and_execute_functions(ai_response, session_id)
        
        # Check if the model is trying to speak for the player
        if "Player:" in cleaned_response:
            # Truncate at the point where the model speaks for the player
            cleaned_response = cleaned_response.split("Player:")[0]
            # Add a reminder
            cleaned_response += "\n\n[Waiting for your input...]"
        
        # Save cleaned assistant message to database
        db.save_message(session_id, "assistant", cleaned_response)
        
        # Get current game state after function calls
        game_state = db.get_game_state(session_id)
        
        # Get updated character data
        character = db.get_character(session_id)
        
        return jsonify({
            "response": cleaned_response,
            "session_id": session_id,
            "game_state": game_state,
            "function_calls": function_results,
            "character": character
        })
    
    except Exception as e:
        print(f"Error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/character', methods=['GET'])
def get_character():
    """Get character information for a session."""
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({"error": "Session ID required"}), 400
    
    character = db.get_character(session_id)
    if not character:
        return jsonify({"error": "Character not found"}), 404
    
    return jsonify(character)

@app.route('/character', methods=['POST'])
def update_character():
    """Update character information."""
    data = request.json
    session_id = data.get('session_id')
    character_data = data.get('character', {})
    
    if not session_id:
        return jsonify({"error": "Session ID required"}), 400
    
    character_id = db.save_character(session_id, character_data)
    return jsonify({"character_id": character_id})

@app.route('/world', methods=['GET'])
def get_world_info():
    """Get world information for a session."""
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({"error": "Session ID required"}), 400
    
    locations = db.get_locations(session_id)
    npcs = db.get_npcs(session_id)
    quests = db.get_quests(session_id)
    
    return jsonify({
        "locations": locations,
        "npcs": npcs,
        "quests": quests
    })

def format_messages(history, current_message, system_prompt, character=None, 
                   locations=None, npcs=None, quests=None, combat_state=None):
    """Format the conversation history and current message for Ollama."""
    # Start with the system prompt
    formatted_prompt = system_prompt + "\n\n"
    
    # Add character information if available
    if character and character.get('name'):
        formatted_prompt += "PLAYER CHARACTER:\n"
        for key, value in character.items():
            if key != 'inventory':  # Handle inventory separately
                formatted_prompt += f"{key.capitalize()}: {value}\n"
        
        # Add inventory if it exists
        if 'inventory' in character and character['inventory']:
            formatted_prompt += "Inventory:\n"
            for item in character['inventory']:
                formatted_prompt += f"- {item}\n"
        
        formatted_prompt += "\n"
    
    # Add world information if available
    if locations and len(locations) > 0:
        formatted_prompt += "KNOWN LOCATIONS:\n"
        for loc in locations[:5]:  # Limit to 5 to keep context manageable
            formatted_prompt += f"- {loc['name']}: {loc['type']} - {loc['description'][:100]}...\n"
        formatted_prompt += "\n"
    
    if npcs and len(npcs) > 0:
        formatted_prompt += "KNOWN NPCs:\n"
        for npc in npcs[:5]:  # Limit to 5
            formatted_prompt += f"- {npc['name']}: {npc['role']} - {npc['description'][:100]}...\n"
        formatted_prompt += "\n"
    
    if quests and len(quests) > 0:
        formatted_prompt += "ACTIVE QUESTS:\n"
        for quest in [q for q in quests if q['status'] in ['not_started', 'in_progress']][:3]:
            formatted_prompt += f"- {quest['title']} ({quest['status']}): {quest['description'][:100]}...\n"
        formatted_prompt += "\n"
    
    # Add combat state if in combat
    if combat_state and combat_state.get('is_in_combat'):
        formatted_prompt += "CURRENT COMBAT STATE:\n"
        formatted_prompt += f"Round: {combat_state.get('round', 1)}\n"
        formatted_prompt += f"Current turn: {combat_state.get('current_combatant', 'Unknown')}\n"
        
        if 'initiative_order' in combat_state and combat_state['initiative_order']:
            formatted_prompt += "Initiative order:\n"
            for combatant in combat_state['initiative_order']:
                formatted_prompt += f"- {combatant.get('name', 'Unknown')}: {combatant.get('initiative', 0)}\n"
        
        formatted_prompt += "\n"
    
    # Add conversation history
    for message in history:
        role = message.get('role', '')
        content = message.get('content', '')
        
        if role == 'user':
            formatted_prompt += f"Player: {content}\n"
        elif role == 'assistant':
            formatted_prompt += f"Game Master: {content}\n"
    
    # Add the current message
    formatted_prompt += f"Player: {current_message}\n"
    formatted_prompt += "Game Master:"
    
    return formatted_prompt

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)