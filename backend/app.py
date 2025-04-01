from flask import Flask, request, jsonify, session
from flask_cors import CORS
import requests
import json
import uuid
from datetime import datetime
from db_manager import DatabaseManager
from prompts import get_system_prompt
import traceback

app = Flask(__name__)
CORS(app, supports_credentials=True)  # Enable CORS with credentials support
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure random key

# Initialize database
db = DatabaseManager()

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
        
        # Format message history and add system prompt
        system_prompt = get_system_prompt(game_state)
        formatted_messages = format_messages(message_history, user_message, system_prompt, character)
        
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
        
        # Save assistant message to database
        db.save_message(session_id, "assistant", ai_response)
        
        # Check if we need to transition game state
        # This is a simple rule-based approach - could be made more sophisticated
        if game_state == "character_creation" and "ready to begin the adventure" in ai_response.lower():
            db.update_game_state(session_id, "adventure")
            game_state = "adventure"
        elif game_state == "adventure" and any(combat_phrase in ai_response.lower() for combat_phrase in 
                                            ["roll for initiative", "combat begins", "enter combat"]):
            db.update_game_state(session_id, "combat")
            game_state = "combat"
        elif game_state == "combat" and any(end_phrase in ai_response.lower() for end_phrase in 
                                          ["combat ends", "fight is over", "defeated all"]):
            db.update_game_state(session_id, "adventure")
            game_state = "adventure"
        
        # Check the response for potential character updates
        if game_state == "character_creation":
            extract_character_info(ai_response, user_message, session_id)
        
        return jsonify({
            "response": ai_response,
            "session_id": session_id,
            "game_state": game_state
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

def format_messages(history, current_message, system_prompt, character=None):
    """Format the conversation history and current message for Ollama."""
    # Start with the system prompt
    formatted_prompt = system_prompt + "\n\n"
    
    # Add character information if available
    if character:
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

def extract_character_info(ai_response, user_message, session_id):
    """
    Extract character information from the conversation.
    This is a simple rule-based extraction - could be enhanced with NLP or function calling.
    """
    # Get existing character data or create new
    character = db.get_character(session_id) or {}
    
    # Check for common character attributes in the user message
    # Name
    if "my name is" in user_message.lower() or "name:" in user_message.lower():
        for line in user_message.split("\n"):
            if "my name is" in line.lower():
                character['name'] = line.lower().split("my name is")[1].strip()
                break
            elif "name:" in line.lower():
                character['name'] = line.lower().split("name:")[1].strip()
                break
    
    # Race
    for race in ["human", "elf", "dwarf", "halfling", "gnome", "half-elf", "half-orc", "tiefling", "dragonborn"]:
        if f"i am a {race}" in user_message.lower() or f"i'm a {race}" in user_message.lower() or f"race: {race}" in user_message.lower():
            character['race'] = race
            break
    
    # Class
    for char_class in ["fighter", "wizard", "rogue", "cleric", "ranger", "paladin", "barbarian", "bard", "druid", "monk", "sorcerer", "warlock"]:
        if f"i am a {char_class}" in user_message.lower() or f"i'm a {char_class}" in user_message.lower() or f"class: {char_class}" in user_message.lower():
            character['class'] = char_class
            break
    
    # Background
    if "background:" in user_message.lower():
        for line in user_message.split("\n"):
            if "background:" in line.lower():
                character['background'] = line.split("background:")[1].strip()
                break
    
    # Only save if we extracted something
    if any(key in character for key in ['name', 'race', 'class', 'background']):
        db.save_character(session_id, character)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)