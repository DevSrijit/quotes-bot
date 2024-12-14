import os
import json
import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import content
from typing import Dict, List
from dotenv import load_dotenv
import pickle
from pathlib import Path
from db_sync import DatabaseSync
import logging
import re

# Get module logger
logger = logging.getLogger(__name__)

load_dotenv()

class QuoteGenerator:
    def __init__(self):
        logger.info("Initializing QuoteGenerator...")
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.generation_config = {
            "temperature": 0.75,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_schema": content.Schema(
                type=content.Type.OBJECT,
                enum=[],
                required=["quote", "author", "instagram_description"],
                properties={
                    "quote": content.Schema(
                        type=content.Type.STRING,
                        description="A thought-provoking quote related to science, engineering, physics, mathematics, chemistry or related fields.",
                    ),
                    "author": content.Schema(
                        type=content.Type.STRING,
                        description="The author of the quote.",
                    ),
                    "instagram_description": content.Schema(
                        type=content.Type.STRING,
                        description="An engaging description to make the quote relatable, inspiring, and impactful. Includes hashtags, a call to action, and aesthetic vibes.",
                    ),
                },
            ),
            "response_mime_type": "application/json",
        }
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=self.generation_config,
        )
        
        # Create a directory to store chat history
        self.history_dir = Path(os.path.dirname(os.path.dirname(__file__))) / "history"
        self.history_dir.mkdir(exist_ok=True)
        self.history_file = self.history_dir / "chat_history.pkl"
        
        # Initialize database sync
        self.db_sync = DatabaseSync()
        
        # Load existing chat history if it exists
        if self.history_file.exists():
            try:
                with open(self.history_file, 'rb') as f:
                    self.chat_history = pickle.load(f)
            except:
                self.chat_history = []
        else:
            self.chat_history = []
            
        self.initialize_chat()

    def initialize_chat(self):
        self.chat_session = self.model.start_chat(history=self.chat_history)
        
    def save_history(self):
        with open(self.history_file, 'wb') as f:
            pickle.dump(self.chat_history, f)
        
        # Sync with Supabase
        self.db_sync.sync_databases()
        
    def get_quote(self) -> Dict:
        """Generate a quote using Gemini API"""
        prompt = """You are managing an Instagram account that posts daily, aesthetic, and thought-provoking science-related quotes.        
        Your goal is to create content that both inspires and educates, while optimizing for maximum reach and engagement. 
        Select powerful quotes from the realms of science, computer science, physics, chemistry, or engineering—without diluting 
        their depth or complexity to suit general audience comprehension. Let the gravity and intellectual rigor of the quotes shine through.
        Try not to post things that do not align with your audience's interests. Grandeur, sophistication, and satisfaction 
        are the hallmarks of a well-crafted quote.

        For each quote, craft a compelling Instagram description that breaks down its essence in an engaging and relatable manner, 
        encouraging the audience to interact and reflect. Use best practices for Instagram, such as relevant hashtags, analogies, 
        and calls to action, to enhance visibility and connection with the audience. Do not repeat a quote that has been provided 
        in the chat history, if provided so. Using the chat history, try not to create an author bias on the quotes,
        feel free to use infinite quotes from a single author, BUT do not use quotes from the SAME author more than once in 3 generations to
        keep your content fresh and engaging.
        
        Important: DO NOT include citations/references/links in your response. Only provide the quote, author, and Instagram description 
        in the requested JSON format. Including anything else will lead to breaking the API constraints. STRICTLY follow the Structured Output Schema provided."""
        
        strict_prompt = "Generate ONLY a JSON object with these exact fields: quote, author, and instagram_description. No citations or references. Do not include hashtags."

        predefined_hashtags = [
            "#sciencequotes", "#sciencefictionquotes", "#quotesscience", "#quotesaboutscience",
            "#datasciencequotes", "#astronomy", "#womeninstem",
            "#cosmology", "#spacescience", "#quoteslife", "#quotedaily",
            "#sciencefictionbooks", "#scienceworld",
            "#chemistryfacts", "#scifiquotes", "#science", "#physics", "#universe", "#space",
            "#cosmos", "#fact", "#engineering", "#didyouknow", "#technology", "#quotesdaily",
            "#quotestagram", "#quotes", "#quotesaboutlife", "#quotesoflife", "#nasa",
            "#knowledge", "#biology", "#factz", "#chemistry", "#education",
            "#tech", "#astrophysics", "#physicsquotes", "#sciencefacts",
            "#technologicalquotes", "#techquotes", "#sciencelife",
            "#einsteinquotes", "#scienceofmind", "#coding", "#computerscience"
        ]

        try:
            logger.info("Requesting quote from Gemini API...")
            response = self.chat_session.send_message(prompt)
            
            # Check if response has citations
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'finish_reason') and candidate.finish_reason == 'RECITATION':
                    # If we got a citation, try again with a more strict prompt
                    response = self.chat_session.send_message(strict_prompt)
            
            # Get the actual text content
            content = response.text if hasattr(response, 'text') else response.parts[0].text
            
            # Remove existing hashtags
            content = re.sub(r'#\w+', '', content)
            
            # Append top 30 predefined hashtags
            hashtags = ' '.join(predefined_hashtags[:30])
            content += f" {hashtags}"
            
            # Clean the response - remove any markdown formatting or extra content
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            # Try to extract just the JSON part if there's extra text
            try:
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    content = content[start_idx:end_idx]
            except:
                pass
            
            quote_data = json.loads(content)
            
            # Validate the required fields
            required_fields = ['quote', 'author', 'instagram_description']
            if not all(field in quote_data for field in required_fields):
                raise ValueError("Missing required fields in response")
            
            # Update chat history
            self.chat_history.extend([
                {"role": "user", "parts": [prompt]},
                {"role": "model", "parts": [response.text]}
            ])
            
            # Save updated history
            self.save_history()
            
            # Check token count and reset if needed
            if len(str(self.chat_history)) > 800000:  # Conservative limit
                self.chat_history = []
                self.initialize_chat()
                self.save_history()
            
            logger.debug(f"Raw response: {response}")
            return quote_data
            
        except Exception as e:
            logger.error(f"Error generating quote: {e}")
            return None