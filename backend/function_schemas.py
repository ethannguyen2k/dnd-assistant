# Schema definitions for function calling
FUNCTION_SCHEMAS = {
    "update_character": {
        "name": "update_character",
        "description": "Update or add character information",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Character name"
                },
                "race": {
                    "type": "string",
                    "description": "Character race (e.g., Human, Elf, Dwarf)"
                },
                "class": {
                    "type": "string",
                    "description": "Character class (e.g., Fighter, Wizard, Rogue)"
                },
                "background": {
                    "type": "string",
                    "description": "Character's background story or profession"
                },
                "strength": {
                    "type": "integer",
                    "description": "Strength attribute (typically 1-20)"
                },
                "dexterity": {
                    "type": "integer",
                    "description": "Dexterity attribute (typically 1-20)"
                },
                "constitution": {
                    "type": "integer",
                    "description": "Constitution attribute (typically 1-20)"
                },
                "intelligence": {
                    "type": "integer",
                    "description": "Intelligence attribute (typically 1-20)"
                },
                "wisdom": {
                    "type": "integer",
                    "description": "Wisdom attribute (typically 1-20)"
                },
                "charisma": {
                    "type": "integer",
                    "description": "Charisma attribute (typically 1-20)"
                },
                "hp": {
                    "type": "integer",
                    "description": "Maximum hit points"
                },
                "currentHp": {
                    "type": "integer",
                    "description": "Current hit points"
                },
                "level": {
                    "type": "integer",
                    "description": "Character level"
                },
                "inventory": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "List of items in character's inventory"
                }
            },
            "required": []
        }
    },
    "add_world_location": {
        "name": "add_world_location",
        "description": "Add a location to the game world",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the location"
                },
                "description": {
                    "type": "string",
                    "description": "Detailed description of the location"
                },
                "type": {
                    "type": "string",
                    "description": "Type of location (e.g., town, dungeon, forest)"
                },
                "notable_npcs": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "Notable NPCs present at this location"
                },
                "points_of_interest": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "Notable features or landmarks at this location"
                }
            },
            "required": ["name", "description", "type"]
        }
    },
    "add_npc": {
        "name": "add_npc",
        "description": "Add an NPC to the game world",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the NPC"
                },
                "description": {
                    "type": "string",
                    "description": "Physical description and notable features"
                },
                "personality": {
                    "type": "string",
                    "description": "Personality traits and behavior"
                },
                "role": {
                    "type": "string",
                    "description": "Role in the story or community (e.g., shopkeeper, villain, quest giver)"
                },
                "location": {
                    "type": "string",
                    "description": "Current location of the NPC"
                },
                "motivation": {
                    "type": "string",
                    "description": "What drives this character, what they want"
                }
            },
            "required": ["name", "description"]
        }
    },
    "update_quest": {
        "name": "update_quest",
        "description": "Create or update a quest in the game",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Title of the quest"
                },
                "description": {
                    "type": "string",
                    "description": "Description of the quest objectives"
                },
                "status": {
                    "type": "string",
                    "enum": ["not_started", "in_progress", "completed", "failed"],
                    "description": "Current status of the quest"
                },
                "giver": {
                    "type": "string",
                    "description": "NPC who gave the quest"
                },
                "location": {
                    "type": "string",
                    "description": "Location associated with the quest"
                },
                "reward": {
                    "type": "string",
                    "description": "Reward for completing the quest"
                }
            },
            "required": ["title", "description", "status"]
        }
    },
    "update_combat_state": {
        "name": "update_combat_state",
        "description": "Update the state of combat",
        "parameters": {
            "type": "object",
            "properties": {
                "is_in_combat": {
                    "type": "boolean",
                    "description": "Whether combat is currently active"
                },
                "initiative_order": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name of combatant"
                            },
                            "initiative": {
                                "type": "integer",
                                "description": "Initiative roll result"
                            },
                            "is_player": {
                                "type": "boolean",
                                "description": "Whether this is a player character"
                            }
                        }
                    },
                    "description": "Order of turns in combat"
                },
                "current_combatant": {
                    "type": "string",
                    "description": "Name of the combatant whose turn it currently is"
                },
                "round": {
                    "type": "integer",
                    "description": "Current round of combat"
                }
            },
            "required": ["is_in_combat"]
        }
    }
}