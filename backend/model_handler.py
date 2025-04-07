# model_handler.py
import requests
import os
from google import genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Gemini API with key from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Ollama API endpoint
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
DEFAULT_OLLAMA_MODEL = os.getenv("DEFAULT_OLLAMA_MODEL", "mistral-nemo:latest")

class ModelHandler:
    def __init__(self):
        # Configure available models
        self.models = {
            "gemini-1.5-pro": {
                "type": "gemini",
                "name": "gemini-1.5-pro", 
                "description": "Google Gemini 1.5 Pro"
            },
            "gemini-1.5-flash": {
                "type": "gemini",
                "name": "gemini-1.5-flash", 
                "description": "Google Gemini 1.5 Flash (Faster)"
            },
            "local": {
                "type": "ollama",
                "name": DEFAULT_OLLAMA_MODEL,
                "description": f"Local Ollama ({DEFAULT_OLLAMA_MODEL})"
            }
        }
        
    def get_available_models(self):
        """Return a list of available models."""
        return self.models
    
    async def generate_response(self, model_id, prompt, function_schemas=None):
        """Generate a response from the selected model."""
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not available")
            
        model_info = self.models[model_id]
        model_type = model_info["type"]
        
        if model_type == "gemini":
            return await self._generate_with_gemini(model_info["name"], prompt, function_schemas)
        elif model_type == "ollama":
            return self._generate_with_ollama(model_info["name"], prompt)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
    
    async def _generate_with_gemini(self, model_name, prompt, function_schemas=None):
        """Generate a response using Google Gemini API."""
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set in environment variables")
        
        try:
            # Create a model instance
            model = genai.GenerativeModel(model_name)
            
            # If function schemas provided, set up function calling
            if function_schemas:
                tools = [
                    {
                        "function_declarations": [
                            {
                                "name": schema["name"],
                                "description": schema["description"],
                                "parameters": schema["parameters"]
                            } for schema in function_schemas.values()
                        ]
                    }
                ]
                response = await model.generate_content_async(
                    prompt,
                    generation_config={"temperature": 0.7},
                    tools=tools
                )
            else:
                response = await model.generate_content_async(
                    prompt,
                    generation_config={"temperature": 0.7}
                )
            
            # Check for function calls in the response
            function_calls = []
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and candidate.content.parts:
                        for part in candidate.content.parts:
                            if hasattr(part, 'function_call'):
                                function_calls.append({
                                    "function": part.function_call.name,
                                    "arguments": part.function_call.args
                                })
            
            # Extract the text response
            text_response = response.text
            
            return {
                "response": text_response,
                "function_calls": function_calls,
                "raw_response": response
            }
            
        except Exception as e:
            raise Exception(f"Error generating content with Gemini: {str(e)}")
    
    def _generate_with_ollama(self, model_name, prompt):
        """Generate a response using Ollama API."""
        try:
            response = requests.post(
                OLLAMA_API_URL,
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Error from Ollama API: {response.text}")
                
            response_data = response.json()
            ai_response = response_data.get('response', 'No response generated')
            
            # Ollama doesn't have native function calling, so we'll parse it later
            return {
                "response": ai_response,
                "function_calls": [],
                "raw_response": response_data
            }
            
        except Exception as e:
            raise Exception(f"Error generating content with Ollama: {str(e)}")