# VectorDBManager class for managing a vector database using ChromaDB and Sentence Transformers
# This class handles the addition and querying of various types of memories (conversations, characters, NPCs, locations, quests)
import os
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import uuid
import json
from datetime import datetime

class VectorDBManager:
    def __init__(self, db_directory="chroma_db"):
        """Initialize the vector database manager."""
        # Create the directory if it doesn't exist
        os.makedirs(db_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=db_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize the embedding model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # A lightweight, fast model
        
        # Initialize collections for different types of memories
        # Create collections if they don't exist, otherwise get existing ones
        self.conversation_collection = self._get_or_create_collection("conversations")
        self.character_collection = self._get_or_create_collection("characters")
        self.npc_collection = self._get_or_create_collection("npcs")
        self.location_collection = self._get_or_create_collection("locations")
        self.quest_collection = self._get_or_create_collection("quests")
        
    def _get_or_create_collection(self, name):
        """Get an existing collection or create a new one if it doesn't exist."""
        try:
            return self.client.get_collection(name=name)
        except:
            return self.client.create_collection(name=name)
    
    def _create_embedding(self, text):
        """Create embedding vector for the given text."""
        return self.model.encode(text).tolist()
    
    def add_conversation_memory(self, session_id, role, content, metadata=None):
        """Add a conversation message to the vector database."""
        if not metadata:
            metadata = {}
            
        # Add session_id and timestamp to metadata
        metadata.update({
            "session_id": session_id,
            "role": role,
            "timestamp": datetime.now().isoformat()
        })
        
        # Create a unique ID for this memory
        memory_id = str(uuid.uuid4())
        
        # Add the text and its embedding to the collection
        self.conversation_collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[memory_id]
        )
        
        return memory_id
    
    def add_character_memory(self, session_id, character_data):
        """Add character information to the vector database."""
        # Convert character data to a text description for embedding
        if "name" not in character_data:
            return None  # Skip if no name is present
            
        # Create a textual representation of the character
        text_representation = f"Character {character_data.get('name')}: "
        text_representation += f"a {character_data.get('race', 'unknown race')} "
        text_representation += f"{character_data.get('class', 'adventurer')}. "
        
        # Add additional attributes
        for key, value in character_data.items():
            if key not in ['name', 'race', 'class', 'inventory'] and value:
                text_representation += f"{key.capitalize()}: {value}. "
        
        # Add inventory if it exists
        if 'inventory' in character_data and character_data['inventory']:
            text_representation += "Inventory: " + ", ".join(character_data['inventory'])
        
        # Create a unique ID based on session_id + character name
        character_id = f"{session_id}_{character_data.get('name', 'unnamed')}"
        
        # Check if this character already exists in the collection
        existing_results = self.character_collection.get(
            ids=[character_id],
            include=["metadatas"]
        )
        
        # If character exists, update it
        if existing_results and len(existing_results['ids']) > 0:
            self.character_collection.update(
                documents=[text_representation],
                metadatas=[{"session_id": session_id, "data": json.dumps(character_data)}],
                ids=[character_id]
            )
        else:
            # Add the character to the collection
            self.character_collection.add(
                documents=[text_representation],
                metadatas=[{"session_id": session_id, "data": json.dumps(character_data)}],
                ids=[character_id]
            )
        
        return character_id
    
    def add_npc_memory(self, session_id, npc_data):
        """Add NPC information to the vector database."""
        if "name" not in npc_data:
            return None  # Skip if no name is present
            
        # Create a textual representation of the NPC
        text_representation = f"NPC {npc_data.get('name')}: "
        
        if 'description' in npc_data:
            text_representation += npc_data['description'] + " "
        
        if 'role' in npc_data:
            text_representation += f"Role: {npc_data['role']}. "
        
        if 'location' in npc_data:
            text_representation += f"Found in {npc_data['location']}. "
        
        if 'personality' in npc_data:
            text_representation += f"Personality: {npc_data['personality']}. "
        
        # Create a unique ID based on session_id + NPC name
        npc_id = f"{session_id}_{npc_data.get('name', 'unnamed')}"
        
        # Check if this NPC already exists in the collection
        existing_results = self.npc_collection.get(
            ids=[npc_id],
            include=["metadatas"]
        )
        
        # If NPC exists, update it
        if existing_results and len(existing_results['ids']) > 0:
            self.npc_collection.update(
                documents=[text_representation],
                metadatas=[{"session_id": session_id, "data": json.dumps(npc_data)}],
                ids=[npc_id]
            )
        else:
            # Add the NPC to the collection
            self.npc_collection.add(
                documents=[text_representation],
                metadatas=[{"session_id": session_id, "data": json.dumps(npc_data)}],
                ids=[npc_id]
            )
        
        return npc_id
    
    def add_location_memory(self, session_id, location_data):
        """Add location information to the vector database."""
        if "name" not in location_data:
            return None  # Skip if no name is present
            
        # Create a textual representation of the location
        text_representation = f"Location {location_data.get('name')}: "
        
        if 'description' in location_data:
            text_representation += location_data['description'] + " "
        
        if 'type' in location_data:
            text_representation += f"Type: {location_data['type']}. "
        
        if 'points_of_interest' in location_data and location_data['points_of_interest']:
            text_representation += "Points of interest: " + ", ".join(location_data['points_of_interest'])
        
        # Create a unique ID based on session_id + location name
        location_id = f"{session_id}_{location_data.get('name', 'unnamed')}"
        
        # Check if this location already exists in the collection
        existing_results = self.location_collection.get(
            ids=[location_id],
            include=["metadatas"]
        )
        
        # If location exists, update it
        if existing_results and len(existing_results['ids']) > 0:
            self.location_collection.update(
                documents=[text_representation],
                metadatas=[{"session_id": session_id, "data": json.dumps(location_data)}],
                ids=[location_id]
            )
        else:
            # Add the location to the collection
            self.location_collection.add(
                documents=[text_representation],
                metadatas=[{"session_id": session_id, "data": json.dumps(location_data)}],
                ids=[location_id]
            )
        
        return location_id
    
    def add_quest_memory(self, session_id, quest_data):
        """Add quest information to the vector database."""
        if "title" not in quest_data:
            return None  # Skip if no title is present
            
        # Create a textual representation of the quest
        text_representation = f"Quest: {quest_data.get('title')}. "
        
        if 'description' in quest_data:
            text_representation += quest_data['description'] + " "
        
        if 'status' in quest_data:
            text_representation += f"Status: {quest_data['status']}. "
        
        if 'giver' in quest_data:
            text_representation += f"Given by: {quest_data['giver']}. "
        
        if 'location' in quest_data:
            text_representation += f"Located in: {quest_data['location']}. "
        
        if 'reward' in quest_data:
            text_representation += f"Reward: {quest_data['reward']}. "
        
        # Create a unique ID based on session_id + quest title
        quest_id = f"{session_id}_{quest_data.get('title', 'unnamed')}"
        
        # Check if this quest already exists in the collection
        existing_results = self.quest_collection.get(
            ids=[quest_id],
            include=["metadatas"]
        )
        
        # If quest exists, update it
        if existing_results and len(existing_results['ids']) > 0:
            self.quest_collection.update(
                documents=[text_representation],
                metadatas=[{"session_id": session_id, "data": json.dumps(quest_data)}],
                ids=[quest_id]
            )
        else:
            # Add the quest to the collection
            self.quest_collection.add(
                documents=[text_representation],
                metadatas=[{"session_id": session_id, "data": json.dumps(quest_data)}],
                ids=[quest_id]
            )
        
        return quest_id
    
    def query_recent_conversations(self, session_id, query_text=None, limit=10):
        """
        Query the most recent conversations for a session.
        If query_text is provided, it will return the most relevant conversations.
        Otherwise, it will return the most recent conversations.
        """
        if query_text:
            # Search by semantic similarity if query text is provided
            results = self.conversation_collection.query(
                query_texts=[query_text],
                where={"session_id": session_id},
                n_results=limit,
                include=["documents", "metadatas"]
            )
        else:
            # Get the most recent conversations if no query text is provided
            # This requires querying all and then sorting by timestamp
            results = self.conversation_collection.get(
                where={"session_id": session_id},
                include=["documents", "metadatas"]
            )
            
            # Sort by timestamp (most recent first)
            if results and 'metadatas' in results and results['metadatas']:
                sorted_indices = sorted(
                    range(len(results['metadatas'])), 
                    key=lambda i: results['metadatas'][i].get('timestamp', ''),
                    reverse=True
                )
                
                # Reorder the results based on timestamp
                results['ids'] = [results['ids'][i] for i in sorted_indices][:limit]
                results['documents'] = [results['documents'][i] for i in sorted_indices][:limit]
                results['metadatas'] = [results['metadatas'][i] for i in sorted_indices][:limit]
        
        return results
    
    def query_by_context(self, session_id, context_text, limit=5):
        """Query all collections for information relevant to the given context."""
        relevant_info = {
            "characters": [],
            "npcs": [],
            "locations": [],
            "quests": [],
            "recent_conversations": []
        }
        
        # Query characters
        character_results = self.character_collection.query(
            query_texts=[context_text],
            where={"session_id": session_id},
            n_results=limit,
            include=["documents", "metadatas"]
        )
        
        if character_results and len(character_results.get('metadatas', [])) > 0:
            for metadata in character_results['metadatas']:
                if isinstance(metadata, dict) and 'data' in metadata:
                    try:
                        character_data = json.loads(metadata['data'])
                        relevant_info["characters"].append(character_data)
                    except:
                        pass
        
        # Query NPCs
        npc_results = self.npc_collection.query(
            query_texts=[context_text],
            where={"session_id": session_id},
            n_results=limit,
            include=["documents", "metadatas"]
        )
        
        if npc_results and len(npc_results.get('metadatas', [])) > 0:
            for metadata in npc_results['metadatas']:
                if isinstance(metadata, dict) and 'data' in metadata:
                    try:
                        npc_data = json.loads(metadata['data'])
                        relevant_info["npcs"].append(npc_data)
                    except:
                        pass
        
        # Query locations
        location_results = self.location_collection.query(
            query_texts=[context_text],
            where={"session_id": session_id},
            n_results=limit,
            include=["documents", "metadatas"]
        )
        
        if location_results and len(location_results.get('metadatas', [])) > 0:
            for metadata in location_results['metadatas']:
                if isinstance(metadata, dict) and 'data' in metadata:
                    try:
                        location_data = json.loads(metadata['data'])
                        relevant_info["locations"].append(location_data)
                    except:
                        pass
        
        # Query quests
        quest_results = self.quest_collection.query(
            query_texts=[context_text],
            where={"session_id": session_id},
            n_results=limit,
            include=["documents", "metadatas"]
        )
        
        if quest_results and len(quest_results.get('metadatas', [])) > 0:
            for metadata in quest_results['metadatas']:
                if isinstance(metadata, dict) and 'data' in metadata:
                    try:
                        quest_data = json.loads(metadata['data'])
                        relevant_info["quests"].append(quest_data)
                    except:
                        pass
        
        # Query recent conversations
        conversation_results = self.conversation_collection.query(
            query_texts=[context_text],
            where={"session_id": session_id},
            n_results=limit,
            include=["documents", "metadatas"]
        )
        
        if conversation_results and len(conversation_results.get('documents', [])) > 0:
            for i, document in enumerate(conversation_results['documents']):
                if i < len(conversation_results.get('metadatas', [])):
                    metadata = conversation_results['metadatas'][i]
                    if isinstance(metadata, dict):
                        relevant_info["recent_conversations"].append({
                            "content": document,
                            "role": metadata.get("role", "unknown"),
                            "timestamp": metadata.get("timestamp", "")
                        })
                    else:
                        # Handle case where metadata is not a dictionary
                        relevant_info["recent_conversations"].append({
                            "content": document,
                            "role": "unknown",
                            "timestamp": ""
                        })
        
        return relevant_info
    
    def generate_narrative_context(self, session_id, user_message, limit=3):
        """
        Generate a narrative context for the AI by querying relevant information
        from all collections based on the user's message.
        """
        context_results = self.query_by_context(session_id, user_message, limit)
        
        # Start building the context string
        context = "## Recent Context Information\n\n"
        
        # Add character information if available
        if context_results["characters"] and len(context_results["characters"]) > 0:
            character = context_results["characters"][0]  # Take the first (most relevant) character
            context += "### Character Information\n"
            context += f"Name: {character.get('name', 'Unknown')}\n"
            context += f"Race: {character.get('race', 'Unknown')}\n"
            context += f"Class: {character.get('class', 'Unknown')}\n"
            if 'background' in character and character['background']:
                context += f"Background: {character['background']}\n"
        
        # Add relevant NPC information
        if context_results["npcs"] and len(context_results["npcs"]) > 0:
            context += "\n### Relevant NPCs\n"
            for npc in context_results["npcs"]:
                context += f"- {npc.get('name', 'Unknown')}: "
                context += f"{npc.get('description', '')} "
                if 'role' in npc:
                    context += f"({npc['role']})"
                context += "\n"
        
        # Add relevant location information
        if context_results["locations"] and len(context_results["locations"]) > 0:
            context += "\n### Relevant Locations\n"
            for location in context_results["locations"]:
                context += f"- {location.get('name', 'Unknown')}: "
                context += f"{location.get('description', '')}\n"
        
        # Add relevant quest information
        if context_results["quests"] and len(context_results["quests"]) > 0:
            context += "\n### Relevant Quests\n"
            for quest in context_results["quests"]:
                context += f"- {quest.get('title', 'Unknown')}: "
                context += f"{quest.get('description', '')} "
                context += f"Status: {quest.get('status', 'unknown')}\n"
        
        # Add relevant conversation history
        if context_results["recent_conversations"] and len(context_results["recent_conversations"]) > 0:
            context += "\n### Recent Relevant Conversation\n"
            for conv in context_results["recent_conversations"]:
                role = "Player" if conv.get("role") == "user" else "Game Master"
                content = conv.get("content", "")
                if content:
                    context += f"{role}: {content}\n"
        
        return context