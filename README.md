# Science Quotes Instagram Bot

An automated Instagram bot that generates and shares daily science and technology quotes with aesthetic designs.

## Setup on Hetzner (Shared Server)

### Prerequisites
- Python 3.8+
- Docker (should be available on the shared server)
- Access to a user-level directory

### Installation
1. Clone the repository to your home directory:
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

3. Create required directories:
```bash
mkdir -p ~/quotes-bot/logs
```

4. Start the bot:
```bash
docker-compose up -d
```

### Monitoring
- Health checks run on localhost:8000 (not publicly accessible)
- Email alerts sent via Resend API for:
  - Service downtime
  - Service recovery
  - Critical errors

### Logs
- Application logs are stored in `~/quotes-bot/logs/`
- View Docker logs:
```bash
docker-compose logs -f
```

### Testing
Run a test post:
```bash
docker-compose run --rm bot python src/main.py --test
```

### Maintenance
- The bot uses session persistence to avoid frequent Instagram logins
- Automatic restart on failure
- Health monitoring with email alerts
- Posts only between 9 AM and 11 PM IST

### Stopping the Bot
```bash
docker-compose down
```

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
