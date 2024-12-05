# Quotable Science Bot

An automated Instagram bot that generates and shares daily science and technology quotes with aesthetic designs.

## Setup on Hetzner (Shared Server)

### Prerequisites
- Python 3.13
- Docker (should be available on the shared server)
- Access to a user-level directory

### Installation
1. Clone the repository:
```bash
cd ~
git clone https://github.com/devsrijit/quotes-bot.git
cd quotes-bot
```

2. Create environment file:
```bash
cp .env.example .env
nano .env  # Edit with your credentials
```

Required environment variables:
```
GEMINI_API_KEY=your_gemini_api_key
INSTAGRAM_USERNAME=your_instagram_username
INSTAGRAM_PASSWORD=your_instagram_password
POSTS_PER_DAY=2
RESEND_API_KEY=your_resend_api_key
MONITORING_EMAIL=your_monitoring_email
```

3. Run the setup script:
```bash
chmod +x setup.sh
./setup.sh
```

This will:
- Create a Python virtual environment
- Install all dependencies
- Create necessary directories
- Build and start the Docker container

### Monitoring
- Health checks run on localhost:4950
- Email alerts for service status changes
- Logs available in `./logs` directory

### Managing the Service

View logs:
```bash
docker compose logs -f
```

Stop the service:
```bash
docker compose down
```

Restart the service:
```bash
docker compose restart
```

Run a test post:
```bash
docker compose exec service python src/main.py --test
```

### Troubleshooting
If you encounter issues:
1. Check the logs: `docker compose logs -f`
2. Verify the virtual environment: `source venv/bin/activate && pip list`
3. Ensure all environment variables are set correctly
4. Check disk space and memory usage

## Features
- Dynamic quote generation using Google Gemini AI
- Beautiful image generation with multi-layered gradients
- Instagram posting via instagrapi
- Timezone-aware scheduling
- Error monitoring and alerts
- Health checks
- Docker containerization

## Support
For issues or questions, contact: mail@srijit.co
