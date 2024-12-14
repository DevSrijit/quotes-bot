import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import noise
from colorthief import ColorThief
import cv2
from typing import Tuple, List
import random
import textwrap
import requests
from pathlib import Path
from scipy.ndimage import gaussian_filter
import logging

# Configure root logger with proper format for systemd/journalctl
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Get logger for this module
logger = logging.getLogger(__name__)

class ImageGenerator:
    def __init__(self):
        self.WIDTH = 1080
        self.HEIGHT = 1080
        self.SIDE_PADDING = 130
        self.FONT_SIZE = 55
        self.LINE_BREAK = 55  # Line break height between quote and author
        self.LINE_SPACING = 20  # Adding new line spacing between quote lines
        
        # Create fonts directory in the project root
        self.fonts_dir = Path(os.path.dirname(os.path.dirname(__file__))) / "fonts"
        self.fonts_dir.mkdir(exist_ok=True)
        
        self.font_path = self.fonts_dir / "PlayfairDisplay-Regular.ttf"
        
        # Download font if not exists
        if not self.font_path.exists():
            logger.info("Downloading Playfair Display font...")
            font_url = "https://cloud-bi14k3e70-hack-club-bot.vercel.app/0playfairdisplay-regular.ttf"
            response = requests.get(font_url)
            if response.status_code == 200:
                self.font_path.write_bytes(response.content)
                logger.info("Font downloaded successfully!")
            else:
                logger.error("Failed to download font!")
                raise Exception("Failed to download font!")

    def generate_blobby_gradient(self) -> Image.Image:
        logger.debug("Generating blobby gradient background...")
        # Create base image
        img = np.zeros((self.HEIGHT, self.WIDTH, 3), dtype=np.float32)
        
        # Generate 5 distinct but harmonious colors
        base_color = np.random.randint(0, 255, 3) / 255.0
        colors = [
            np.random.randint(0, 255, 3) / 255.0,  # Completely random first color
            np.random.randint(0, 255, 3) / 255.0,  # Completely random second color
            np.random.randint(0, 255, 3) / 255.0,  # Third color
            np.random.randint(0, 255, 3) / 255.0,  # Fourth color
            #np.random.randint(0, 255, 3) / 255.0,  # Fifth color
        ]
        
        # Generate smoother Perlin noise with larger scale
        scale = 6.0  # Larger scale for fewer, bigger blobs
        octaves = 2  # Slightly more detail
        persistence = 0.5
        lacunarity = 2.0
        
        # Generate multiple noise layers for color mixing
        bases = []
        for i in range(len(colors)):
            base = np.zeros((self.HEIGHT, self.WIDTH))
            for y in range(self.HEIGHT):
                for x in range(self.WIDTH):
                    noise_val = noise.pnoise2(x/self.WIDTH * scale + i*5, 
                                           y/self.HEIGHT * scale + i*5, 
                                           octaves=octaves,
                                           persistence=persistence,
                                           lacunarity=lacunarity,
                                           repeatx=self.WIDTH,
                                           repeaty=self.HEIGHT)
                    base[y][x] = noise_val
            
            # Normalize to 0-1
            base = (base - base.min()) / (base.max() - base.min())
            # Apply gaussian blur for smooth transitions
            base = gaussian_filter(base, sigma=30)  # Reduced blur
            bases.append(base)
        
        # Normalize all bases to sum to 1 at each pixel
        bases = np.array(bases)
        bases_sum = np.sum(bases, axis=0)
        bases = bases / bases_sum[np.newaxis, :, :]
        
        # Mix colors using the normalized bases
        for i in range(3):  # RGB channels
            for j in range(len(colors)):
                img[:,:,i] += colors[j][i] * bases[j]
        
        # Add slightly more noticeable grain
        grain = np.random.normal(0, 0.035, img.shape)  # Increased grain
        img = np.clip(img + grain, 0, 1)
        
        # Convert to uint8
        img = (img * 255).astype(np.uint8)
        
        return Image.fromarray(img)

    def get_contrast_color(self, background: Image.Image) -> Tuple[int, int, int]:
        # Convert to numpy array for easier processing
        img_array = np.array(background)
        
        # Calculate average color of the center region
        center_region = img_array[self.HEIGHT//3:2*self.HEIGHT//3, 
                                self.WIDTH//3:2*self.WIDTH//3]
        avg_color = np.mean(center_region, axis=(0, 1))
        
        # Calculate perceived brightness
        brightness = (0.299 * avg_color[0] + 0.587 * avg_color[1] + 0.114 * avg_color[2])
        
        # Choose white or black based on background brightness
        if brightness > 128:
            return (0, 0, 0)  # Black for light backgrounds
        else:
            return (255, 255, 255)  # White for dark backgrounds

    def create_quote_image(self, quote: str, author: str) -> str:
        # Ensure quote has quotes and period
        if not quote.startswith('"'):
            quote = f'"{quote}'
        if not quote.endswith('"'):
            quote = f'{quote}"'
        if not quote.endswith('."'):
            quote = quote[:-1] + '."'
            
        # Ensure author ends with period
        if not author.endswith('.'):
            author = f"~ {author}."

        # Create background
        background = self.generate_blobby_gradient()
        draw = ImageDraw.Draw(background)
        
        # Get contrasting text color
        text_color = self.get_contrast_color(background)
        
        # Load font
        font = ImageFont.truetype(str(self.font_path), self.FONT_SIZE)
        
        # Wrap text
        quote_lines = textwrap.wrap(quote, width=30)
        
        # Calculate maximum line width
        max_line_width = max(font.getbbox(line)[2] - font.getbbox(line)[0] for line in quote_lines)
        right_padding = self.WIDTH - (self.SIDE_PADDING + max_line_width)
        
        # Calculate heights
        line_heights = [font.getbbox(line)[3] - font.getbbox(line)[1] for line in quote_lines]
        quote_height = sum(line_heights) + self.LINE_SPACING * (len(quote_lines) - 1)
        author_height = font.getbbox(author)[3] - font.getbbox(author)[1]
        total_height = quote_height + self.LINE_BREAK + author_height
        
        # Calculate starting y position to center text block vertically
        current_y = (self.HEIGHT - total_height) // 2
        
        # Draw quote
        for line in quote_lines:
            bbox = font.getbbox(line)
            draw.text((self.SIDE_PADDING, current_y), line, 
                    fill=text_color, font=font)
            current_y += (bbox[3] - bbox[1]) + self.LINE_SPACING  # Add spacing after each line
        
        # Add line break
        current_y += self.LINE_BREAK - (bbox[3] - bbox[1]) // 2
        
        # Draw author
        draw.text((self.SIDE_PADDING, current_y), author, 
                fill=text_color, font=font)
        
        # Log calculated right padding for debugging
        print(f"Calculated right padding: {right_padding}")
        
        # Save image
        output_path = f"output_{random.randint(1000, 9999)}.png"
        background.save(output_path, "PNG", quality=95)
        return output_path
