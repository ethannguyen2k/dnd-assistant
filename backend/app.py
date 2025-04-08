from flask import Flask, request, jsonify, session
from flask_cors import CORS
import requests
import json
import uuid
from datetime import datetime
import traceback
import logging
from db_manager import DatabaseManager
from prompts import get_system_prompt
from function_handler import FunctionHandler
from function_schemas import FUNCTION_SCHEMAS
import os
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Log to console
    ]
)
logger = logging.getLogger('dnd_gm_assistant')

app = Flask(__name__)
CORS(app, supports_credentials=True)  # Enable CORS with credentials support
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure random key

# Initialize database and function handler
db = DatabaseManager()
function_handler = FunctionHandler(db)

# Ollama API endpoint - adjust if Ollama is running on a different host
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# Gemini API endpoint and key 
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")  # Set this as an environment variable

@app.route('/session', methods=['POST'])
def create_session():
    """Create a new game session."""
    session_id = db.create_session()
    logger.info(f"Created new session: {session_id}")
    return jsonify({"session_id": session_id})

@app.route('/models', methods=['GET'])
def get_models():
    """Get available models."""
    models = {
        'local': {
            'id': 'local',
            'description': 'Local (Mistral)',
            'capabilities': ['text']
        }
    }
    
    # Only add Gemini if API key is set
    if GEMINI_API_KEY:
        models['gemini'] = {
            'id': 'gemini',
            'description': 'Google Gemini',
            'capabilities': ['text']
        }
    
    logger.info(f"Available models: {', '.join(models.keys())}")
    return jsonify(models)

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        session_id = data.get('session_id', '')
        model_id = data.get('model_id', 'local')  # Default to local model
        
        logger.info(f"Chat request - Session: {session_id}, Model: {model_id}")
        logger.info(f"User message: {user_message[:50]}{'...' if len(user_message) > 50 else ''}")
        
        # If no session_id provided, create a new one
        if not session_id:
            session_id = db.create_session()
            logger.info(f"Created new session: {session_id}")
        else:
            # Update last active timestamp
            db.update_session_activity(session_id)
        
        # Get current game state
        game_state = db.get_game_state(session_id) or "character_creation"
        logger.info(f"Current game state: {game_state}")
        
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
        
        # Choose the model endpoint based on model_id
        if model_id == 'gemini' and GEMINI_API_KEY:
            logger.info("Using Google Gemini model for generation")
            ai_response = call_gemini_api(formatted_messages)
        else:
            logger.info("Using local Ollama model for generation")
            # Default to local Ollama model
            ai_response = call_ollama_api(formatted_messages)
        
        # Process function calls in the response
        cleaned_response, function_results = function_handler.parse_and_execute_functions(ai_response, session_id)
        cleaned_response = re.sub(r'```function.*?```', '', cleaned_response, flags=re.DOTALL)
        cleaned_response = re.sub(r'function\s+\w+\s*\(.*?\)', '', cleaned_response, flags=re.DOTALL)

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
        if game_state == "character_creation" and character and character.get('name') and 'ready to begin' in ai_response.lower():
            db.update_game_state(session_id, "adventure")
            game_state = "adventure"
        
        # Get updated character data
        character = db.get_character(session_id)
        
        logger.info(f"Response generated - Length: {len(cleaned_response)} chars")
        if function_results:
            logger.info(f"Functions executed: {[result.get('function') for result in function_results if result.get('success')]}")
        
        return jsonify({
            "response": cleaned_response,
            "session_id": session_id,
            "game_state": game_state,
            "function_calls": function_results,
            "character": character
        })
    
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

def call_ollama_api(formatted_messages):
    """Call the Ollama API with the formatted messages."""
    logger.info("Sending request to Ollama API")
    start_time = datetime.now()
    
    response = requests.post(
        OLLAMA_API_URL,
        json={
            "model": "mistral-nemo:latest",  # Replace with your preferred model
            "prompt": formatted_messages,
            "stream": False
        }
    )
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    logger.info(f"Ollama API response received in {duration:.2f} seconds")
    
    if response.status_code != 200:
        logger.error(f"Ollama API error: {response.status_code} - {response.text}")
        raise Exception(f"Error from Ollama API: {response.text}")
    
    response_data = response.json()
    return response_data.get('response', 'No response generated')

def call_gemini_api(formatted_messages):
    """Call the Google Gemini API with the formatted messages."""
    if not GEMINI_API_KEY:
        logger.error("Gemini API key not set")
        raise Exception("Gemini API key not set")
    
    logger.info("Sending request to Google Gemini API")
    start_time = datetime.now()
    
    # Prepare the request for Gemini API
    prompt_data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": formatted_messages
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 2048
        }
    }
    
    response = requests.post(
        f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
        json=prompt_data
    )
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    logger.info(f"Gemini API response received in {duration:.2f} seconds")
    
    if response.status_code != 200:
        logger.error(f"Gemini API error: {response.status_code} - {response.text}")
        raise Exception(f"Error from Gemini API: {response.text}")
    
    response_data = response.json()
    
    # Extract the response text from Gemini's response structure
    try:
        return response_data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        logger.error("Unexpected response structure from Gemini API")
        logger.error(f"Response: {json.dumps(response_data)}")
        raise Exception("Unexpected response structure from Gemini API")

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
    """Format the conversation history and current message for the LLM."""
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
    logger.info("Starting D&D Game Master Assistant server...")
    logger.info(f"Local Ollama API URL: {OLLAMA_API_URL}")
    logger.info(f"Gemini API available: {bool(GEMINI_API_KEY)}")
    app.run(debug=True, host='0.0.0.0', port=5000)