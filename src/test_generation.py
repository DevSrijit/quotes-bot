import os
import sys
from dotenv import load_dotenv
from quote_generator import QuoteGenerator
from image_generator import ImageGenerator

def main():
    # Load environment variables
    load_dotenv()

    # Check for purge argument
    if len(sys.argv) > 1 and sys.argv[1] == '--purge':
        history_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'history', 'chat_history.pkl')
        if os.path.exists(history_file):
            os.remove(history_file)
            print("Chat history purged successfully!")
        else:
            print("No chat history found to purge.")
        return

    print("1. Testing quote generation...\n")
    quote_gen = QuoteGenerator()
    quote_data = quote_gen.get_quote()
    
    if quote_data:
        print("Quote generated successfully!")
        print(f"Quote: {quote_data['quote']}")
        print(f"Author: {quote_data['author']}")
        print(f"Instagram Description: {quote_data['instagram_description']}\n")
        
        print("2. Testing image generation...\n")
        image_gen = ImageGenerator()
        try:
            image_path = image_gen.create_quote_image(quote_data['quote'], quote_data['author'])
            print(f"Image generated successfully at: {image_path}")
            print("Please check the generated image to verify the design.")
        except Exception as e:
            print(f"Failed to generate image: {e}")
            return
    else:
        print("Failed to generate quote.")

if __name__ == "__main__":
    main()
