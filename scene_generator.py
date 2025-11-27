"""
D&D Scene Description Generator
Uses Google Gemini API to generate scene descriptions suitable for DM narration
"""
import logging
import os
from typing import Optional
from google import genai

from dotenv import load_dotenv



logger = logging.getLogger(__name__)

class SceneGenerator:
    """Scene description generator"""
    
    def __init__(self):
        # Get API key from environment variables
        load_dotenv()
        api_key = os.getenv('GEMINI_API_KEY')
        print(api_key)
        if not api_key:
            raise ValueError("Please set the GEMINI_API_KEY environment variable")
        
        # Configure client
        self.client = genai.Client(api_key=api_key)
        # Use Gemini Flash model
        self.model = "gemini-2.5-flash"
    
    async def generate_scene_description(
        self, 
        english_prompt: str, 
        length: int = 100,
        style: str = "descriptive"
    ) -> Optional[str]:
        """
        Generate scene description
        
        Args:
            english_prompt: English description prompt
            length: Target length (character count)
            style: Description style (supports any style keywords, e.g.: descriptive, mysterious, horror, romantic, humorous, etc.)
            
        Returns:
            Generated English scene description
        """
        try:
            # First try calling the real API
            try:
                # Build system prompt
                system_prompt = self._build_system_prompt(length, style)
                
                # Build complete prompt (Gemini doesn't need separate system and user messages)
                full_prompt = f"""
{system_prompt}

Please generate an English scene description suitable for DM narration based on the following English description:

{english_prompt}

Requirements:
- Approximately {length} characters
- Style: {style}
- Suitable for oral narration
- Create immersion
- Do not include specific game rules or numerical values
"""
                
                # Use Gemini API call
                completion = self.client.models.generate_content(
                    model=self.model,
                    contents=full_prompt
                )
                
                response = completion.text
                if response:
                    # Clean response, remove possible format markers
                    response = response.strip()
                    # Remove possible quotes
                    if response.startswith('"') and response.endswith('"'):
                        response = response[1:-1]
                    
                    logger.info(f"Scene description generated successfully, length: {len(response)} characters")
                    return response
                
            except Exception as api_error:
                logger.warning(f"API call failed, using demo mode: {api_error}")
                # If API call fails, return demo content
                return self._generate_demo_description(english_prompt, length, style)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to generate scene description: {e}")
            return None
    
    def _build_system_prompt(self, length: int, style: str) -> str:
        """Build system prompt"""
        # Detailed descriptions for predefined styles
        predefined_styles = {
            "descriptive": "Use rich adjectives and sensory descriptions to help players imagine vivid scenes",
            "dramatic": "Use dramatic language to enhance emotional impact and make scenes more engaging",
            "mysterious": "Create a mysterious atmosphere using subtle descriptions and hints to spark player curiosity",
            "tense": "Use urgent language and short sentences to create a tense and thrilling atmosphere",
            "horror": "Create a horror atmosphere using unsettling descriptions and hints to make players feel nervous and afraid",
            "romantic": "Use beautiful language and poetic descriptions to create a romantic and warm atmosphere",
            "humorous": "Use light and humorous language with interesting details and descriptions",
            "epic": "Use grand and magnificent language to showcase epic scenes and atmosphere",
            "cozy": "Use warm and friendly language to create a comfortable and safe atmosphere",
            "adventurous": "Use energetic language emphasizing the thrill of exploration and discovery"
        }
        
        # If it's a predefined style, use detailed description; otherwise use user input as style guidance
        if style in predefined_styles:
            style_instruction = predefined_styles[style]
        else:
            # Custom style, let AI flexibly adapt based on style keywords
            style_instruction = f"Adopt the characteristics of '{style}' style, adjusting language style, word choice, and atmosphere creation based on this style keyword"
        
        return f"""You are a professional Dungeons & Dragons (D&D) Dungeon Master (DM) assistant. Your task is to generate English scene descriptions suitable for DM narration based on English descriptions.

Requirements:
1. Text length should be around {length} characters (can vary by 20%)
2. Style: {style_instruction}
3. Language characteristics:
   - Conversational, suitable for reading aloud
   - Rich in imagery
   - Avoid overly formal expressions
   - Create immersion
4. Content characteristics:
   - Focus on environment, atmosphere, sensory experience
   - Do not include specific game mechanics or numerical values
   - Leave room for player actions
   - Suitable for fantasy settings

Please output the description text directly without any prefix or suffix."""
    
    def get_suggested_styles(self) -> list:
        """Get suggested description styles (users can also input custom styles)"""
        return ["descriptive", "dramatic", "mysterious", "tense", "horror", "romantic", "humorous", "epic", "cozy", "adventurous"]
    
    def _generate_demo_description(self, english_prompt: str, length: int, style: str) -> str:
        """Generate demo scene description (used when API is unavailable)"""
        # Generate appropriate demo content based on input
        demo_descriptions = {
            "descriptive": {
                "default": "Night falls upon this ancient forest, moonlight filtering through the dense canopy casting dappled silver light. In the distance, several mysterious blue-green glows flicker among the trees, as if elves are whispering in the shadows. The air is filled with the scent of damp earth and fresh grass, occasionally punctuated by the low growl of an unknown beast, instilling a sense of caution."
            },
            "dramatic": {
                "default": "Darkness swallows the forest like a tide! Eerie lights flicker deep within the woods, as if summoned from another world! Every ray of moonlight reveals an ominous portent, every whisper of wind could herald danger! Adventurers, do you have the courage to step into this cursed land?"
            },
            "mysterious": {
                "default": "The forest hides secrets unknown to mortals... Those flickering lights seem to hint at something, perhaps ancient magic, perhaps lost souls. Something seems to watch from the shadows of the trees, but when you look closely, nothing is there. This forest keeps its secrets, waiting for the brave to uncover the truth."
            },
            "tense": {
                "default": "Danger! Something moves in the tree shadows! Those eerie lights are getting closer, time is running out! You must decide immediately: advance or retreat? Every step could be a trap! Stay alert, prepare for battle!"
            },
            "horror": {
                "default": "A cold dread creeps up your spine... Unsettling sounds echo through the forest, as if some evil presence watches from the darkness. Withered branches creak in the wind like wailing voices, and unknown bones litter the ground. The air is thick with the stench of death, every step could lead into unknown terror."
            },
            "romantic": {
                "default": "Moonlight spills like liquid silver across the forest, draping this tranquil land in a dreamlike veil. A gentle breeze caresses the leaves, playing nature's nocturne. In the distance, a nightingale's song mingles with the babbling brook, weaving a beautiful serenade. Everything here seems so tender and romantic, like a fairyland from a poet's pen."
            },
            "humorous": {
                "default": "This forest has quite the 'personality' - the trees seem to strike various odd poses, as if competing in a 'best posture' contest. A squirrel sits perched on a branch, regarding you with a rather serious expression, as if to say 'another group of lost adventurers'. Even those mysterious lights seem playful, flickering on and off, as if playing hide-and-seek with you."
            },
            "epic": {
                "default": "Here, once stood the birthplace of ancient legends! Towering ancient trees have witnessed the rise and fall of countless heroes, every leaf bearing the memory of legends. Those lights flickering among the trees are echoes of ancient magic, telling of this land's former glory. Standing here, you can almost hear history's echo, feel destiny's call."
            },
            "cozy": {
                "default": "This forest feels like a warm home, ancient oaks spreading their sturdy arms to shelter all living things. The forest paths are covered in soft moss, comfortable and quiet underfoot. Small animals occasionally peek out from the bushes, regarding you with curious and friendly eyes. The air here is fresh and sweet, bringing a sense of peace and relaxation."
            },
            "adventurous": {
                "default": "Ahead, unknown adventures beckon! This forest is full of opportunities for exploration, every path could lead to unexpected discoveries. Those mysterious lights are like beacons guiding adventurers, leading brave hearts on journeys into the unknown. The air is thick with excitement, as if the entire world awaits your exploration and conquest."
            }
        }
        
        # Select appropriate demo description
        if style in demo_descriptions:
            base_desc = demo_descriptions[style]["default"]
        else:
            # Custom style, use generic description template
            base_desc = f"You step into a mysterious place filled with a '{style}' atmosphere. Based on your description of '{english_prompt}', every detail here embodies this unique style. The air is filled with a special essence, every corner of the environment tells an extraordinary story. This place awaits brave adventurers to explore and discover."
        
        # Adjust description based on target length
        if length < 80:
            # Short version, take first half
            sentences = base_desc.split(". ")
            result = ". ".join(sentences[:2]) + "."
        elif length > 150:
            # Long version, add more details
            additional_details = {
                "descriptive": " A gentle breeze carries news from afar.",
                "dramatic": " The wheels of fate are turning!",
                "mysterious": " Everything has its deeper meaning...",
                "tense": " Time is short, you must act now!",
                "horror": " An ominous premonition spreads through your heart...",
                "romantic": " Beautiful memories surface in this moment.",
                "humorous": " Looks like today will be an interesting day.",
                "epic": " Great legends are about to be written!",
                "cozy": " A warm feeling wells up in your heart.",
                "adventurous": " A new journey is about to begin!"
            }
            additional = additional_details.get(style, f" The '{style}' atmosphere grows ever stronger.")
            result = base_desc + additional
        else:
            result = base_desc
        
        # Add demo marker
        result = f"[Demo Mode] {result}"
        
        logger.info(f"Generated demo scene description, length: {len(result)} characters")
        return result

# Create global instance
scene_generator = SceneGenerator()