import os
import json
import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import content
from typing import Dict, List
from dotenv import load_dotenv
import pickle
from pathlib import Path

load_dotenv()

class QuoteGenerator:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.generation_config = {
            "temperature": 1,
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
        
    def get_quote(self) -> Dict:
        prompt = """You are managing an Instagram account that posts daily, aesthetic, and thought-provoking science-related quotes.        
        Your goal is to create content that both inspires and educates, while optimizing for maximum reach and engagement. 
        Select powerful quotes from the realms of science, computer science, physics, chemistry, or engineering—without diluting 
        their depth or complexity to suit general audience comprehension. Let the gravity and intellectual rigor of the quotes shine through.

        For each quote, craft a compelling Instagram description that breaks down its essence in an engaging and relatable manner, 
        encouraging the audience to interact and reflect. Use best practices for Instagram, such as relevant hashtags, analogies, 
        and calls to action, to enhance visibility and connection with the audience. Do not repeat a quote that has been provided 
        in the chat history, if provided so.
        
        Important: Do not include citations or references in your response. Only provide the quote, author, and Instagram description 
        in the requested JSON format. Including anything else will lead to breaking the API constraints. STRICTLY follow the Structued Output Schema provided."""
        
        try:
            response = self.chat_session.send_message(prompt)
            quote_data = json.loads(response.text.strip('```json\n').strip('```'))
            
            # Update chat history
            self.chat_history.extend([
                {"role": "user", "parts": [prompt]},
                {"role": "model", "parts": [response.text]}
            ])
            
            # Save updated history
            self.save_history()
            
            # Check token count and reset if needed (approximate calculation)
            if len(str(self.chat_history)) > 800000:  # Conservative limit
                self.chat_history = []
                self.initialize_chat()
                self.save_history()
            
            return quote_data
            
        except Exception as e:
            print(f"Error generating quote: {e}")
            return None
