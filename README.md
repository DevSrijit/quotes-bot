# Quotes Bot

An automated Instagram bot that posts aesthetic science quotes with beautiful gradient backgrounds.

## Features

- Generates unique science quotes using Google's Gemini 1.5 Pro API
- Creates beautiful gradient backgrounds with grain effect
- Dynamic text color selection for optimal readability
- Automated posting with randomized schedules
- Configurable posting frequency
- Smart token management to prevent API limits

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with the following variables:
```env
GEMINI_API_KEY=your_gemini_api_key
INSTAGRAM_ACCESS_TOKEN=your_instagram_graph_api_token
FACEBOOK_PAGE_ID=your_facebook_page_id
INSTAGRAM_ACCOUNT_ID=your_instagram_business_account_id
POSTS_PER_DAY=1  # or any number you prefer
RESEND_API_KEY=your_resend_api_key
MONITORING_EMAIL=your@email.com
```

3. Run the bot:
```bash
python src/main.py
```

## Running the Application

### Setup
1. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables in `.env`:
```
GEMINI_API_KEY=your_gemini_api_key
INSTAGRAM_ACCESS_TOKEN=your_instagram_graph_api_token
FACEBOOK_PAGE_ID=your_facebook_page_id
INSTAGRAM_ACCOUNT_ID=your_instagram_business_account_id
POSTS_PER_DAY=1
RESEND_API_KEY=your_resend_api_key
MONITORING_EMAIL=your@email.com
```

### Testing Quote and Image Generation
```bash
# Activate virtual environment (if not already activated)
source venv/bin/activate

# Run test script
cd src
python test_generation.py
```

### Purging Chat History
If you want to clear the Gemini chat history (useful when quotes start repeating):
```bash
cd src
python test_generation.py --purge
```

### Running Instagram Bot
1. First, test the connection:
```bash
cd src
python main.py --test
```

2. Run the bot in production mode:
```bash
# Run in background with logging
nohup python main.py > ../logs/instagram_bot.log 2>&1 &

# Or run in foreground
python main.py
```

3. Monitor the logs:
```bash
tail -f logs/instagram_bot.log
```

### Stopping the Bot
```bash
# Find the process
ps aux | grep "python main.py"

# Kill the process
kill <process_id>
```

### Common Issues
1. If quotes start repeating: Run `python test_generation.py --purge` to clear chat history
2. If Instagram login fails: Wait 24 hours before trying again (Instagram rate limiting)
3. If image generation fails: Check if font download is working properly

## Monitoring and Service Management

### Email Monitoring
The bot includes email-based monitoring using the Resend API. To enable monitoring:

1. Add these variables to your `.env`:
```env
RESEND_API_KEY=your_resend_api_key
MONITORING_EMAIL=your@email.com
```

The monitoring system will send emails for:
- Service startup
- Error notifications (rate limited to 1 per hour)
- Service recovery notifications

## Running as a System Service on Linux

To run this application as a system service that starts on boot and automatically restarts:

1. Copy the service file to systemd:
```bash
sudo cp quotable-science.service /etc/systemd/system/
```

2. Reload systemd daemon:
```bash
sudo systemctl daemon-reload
```

3. Enable the service to start on boot:
```bash
sudo systemctl enable quotable-science
```

4. Start the service:
```bash
sudo systemctl start quotable-science
```

You can check the status of the service using:
```bash
sudo systemctl status quotable-science
```

View logs:
```bash
# View application logs
sudo tail -f /var/log/quotable-science.log

# View error logs
sudo tail -f /var/log/quotable-science.error.log
```

## Project Structure

- `src/main.py`: Main script that orchestrates the entire process
- `src/quote_generator.py`: Handles quote generation using Gemini API
- `src/image_generator.py`: Creates beautiful gradient images with quotes
- `src/instagram_poster.py`: Handles Instagram posting

## Design Specifications

- Image Size: 1080x1080 pixels
- Font: Playfair Display
- Font Size: 55px
- Side Padding: 130px
- Background: Dynamic grainy gradient
- Text Color: Automatically selected for optimal contrast

## Image Generation Parameters

The `ImageGenerator` class uses several parameters that can be tuned to customize the image output:

### Image Dimensions
- `WIDTH`, `HEIGHT`: 1080x1080 pixels (Instagram square format)
- `PADDING`: 130 pixels (space between text and image edge)

### Typography
- `FONT_SIZE`: 55 pixels
- `LINE_SPACING`: 55 pixels (space between quote and author)
- Font: Playfair Display (downloaded dynamically)

### Gradient Generation
- `scale`: 4.0 (controls size of blob patterns - higher = larger blobs)
- `octaves`: 2 (number of noise layers - higher = more detail)
- `persistence`: 0.5 (how much each octave contributes)
- `lacunarity`: 2.0 (how frequency increases with each octave)
- `sigma`: 30 (gaussian blur intensity - higher = smoother transitions)
- `grain`: 0.015 (noise intensity - higher = more grainy texture)

### Color Generation
- Uses 3 random colors for rich, varied gradients
- Colors are mixed using normalized Perlin noise bases
- Each color gets its own noise layer offset by 5 units
- Colors are blended smoothly using gaussian blur
- Final image includes subtle grain effect for texture

### Text Formatting
- Quotes are wrapped in quotation marks
- Authors are prefixed with "~" and end with a period
- Text color adapts to background brightness
- Text is center-aligned both horizontally and vertically

### Fine-tuning Tips
1. For larger, smoother blobs:
   - Increase `scale`
   - Decrease `octaves`
   - Increase `sigma`

2. For more detailed, intricate patterns:
   - Decrease `scale`
   - Increase `octaves`
   - Decrease `sigma`

3. For color variation:
   - Modify the color generation logic in `generate_blobby_gradient()`
   - Adjust the offset between noise layers (currently 5)

4. For texture:
   - Adjust `grain` value (0.01-0.02 recommended range)
   - Modify gaussian blur `sigma` (20-50 recommended range)

## Dependencies

- google-generativeai: For quote generation
- Pillow: Image processing
- numpy: Numerical operations
- instabot: Instagram API interaction
- python-dotenv: Environment variable management
- noise: Perlin noise for grain effect
- colorthief: Color analysis
- apscheduler: Scheduling posts

## Note

This bot uses the Instagram API through instabot. Be aware that Instagram's API policies may change, and excessive automation might lead to account restrictions. Use responsibly and consider Instagram's terms of service.
