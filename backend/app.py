from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Ollama API endpoint - adjust if Ollama is running on a different host
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# Define the game master system prompt
SYSTEM_PROMPT = """
You are a Dungeon Master for a Dungeons & Dragons adventure. Your role is to:
- Create an immersive fantasy world with rich descriptions
- Control NPCs and monsters, giving them unique personalities and behaviors
- Manage combat encounters with appropriate challenge levels
- Adapt the story based on player choices
- Provide fair and consistent rule interpretations
- Create memorable moments and exciting adventures

Always respond in character as a knowledgeable and creative Game Master. Describe scenes vividly and make the world feel alive and reactive to player actions.
"""

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        message_history = data.get('history', [])
        
        # Format message history and add system prompt
        formatted_messages = format_messages(message_history, user_message)
        
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
        
        return jsonify({"response": ai_response})
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

def format_messages(history, current_message):
    """Format the conversation history and current message for Ollama."""
    # Start with the system prompt
    formatted_prompt = SYSTEM_PROMPT + "\n\n"
    
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