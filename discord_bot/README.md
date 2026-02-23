# punsVC Discord Bot

Enable voice synthesis directly in Discord using punsVC. Generate TTS audio with custom voice profiles from slash commands.

## Features

- 🎤 Generate TTS with any voice profile via Discord commands
- 🔗 Link your Discord account to a voice profile
- 📋 List all available voices
- ⚡ Fast audio generation and delivery
- 🔒 Optional API key authentication

## Quick Start

### 1. Create a Discord Application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name (e.g., "punsVC")
3. Go to the "Bot" section and click "Add Bot"
4. Copy the bot token

### 2. Configure Bot Permissions

In Discord Developer Portal:
1. Go to OAuth2 → URL Generator
2. Select scopes: `bot`, `applications.commands`
3. Select permissions:
   - Read Messages/View Channels
   - Send Messages
   - Embed Links
   - Attach Files
4. Copy the generated URL and open it to invite the bot to your server

### 3. Set Up the Bot

```bash
# Clone the repository (if not already done)
cd /path/to/punsvc

# Create environment file
cp .env.discord.example .env.discord

# Edit .env.discord and add your Discord bot token
nano .env.discord
```

### 4. Install Dependencies

```bash
cd discord_bot
pip install -r requirements.txt
```

### 5. Start the Bot

Make sure your punsVC backend is running first:

```bash
# Terminal 1: Start punsVC backend
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2: Start Discord bot
cd discord_bot
python bot.py
```

### 6. Verify Bot is Running

You should see in the Discord bot terminal:
```
✅ Bot logged in as punsVC#xxxx
📡 Connected to punsVC backend at http://localhost:8000
✅ Synced X command(s)
```

## Commands

### `/generate text: language:`

Generate TTS audio from text.

**Parameters:**
- `text` (required): Text to synthesize (max 5000 characters)
- `voice` (optional): Voice profile ID. If not specified, uses your linked profile
- `language` (optional): Language code - `en` (English) or `zh` (Chinese). Default: `en`

**Example:**
```
/generate text:"Hello, this is a test" voice:profile-123 language:en
```

### `/voices`

List all available voice profiles on the server.

### `/connect voice:`

Link your Discord account to a voice profile. This makes it your default voice for future generations.

**Parameters:**
- `voice` (required): Voice profile ID (get from `/voices`)

**Example:**
```
/connect voice:profile-123
```

### `/myvoice`

Show your currently linked voice profile.

### `/disconnect`

Unlink your Discord account from your current voice profile.

## Configuration

The bot reads configuration from `.env.discord`:

```env
# Required
DISCORD_TOKEN=your_bot_token

# Optional (defaults to http://localhost:8000)
PUNSVC_API_BASE=http://localhost:8000

# Optional (for future authentication)
PUNSVC_API_KEY=your_api_key
```

## Deployment

### Docker

```bash
docker run -d \
  --name punsvc-discord-bot \
  -e DISCORD_TOKEN=your_token \
  -e PUNSVC_API_BASE=http://host.docker.internal:8000 \
  punsvc-discord-bot
```

### Docker Compose

```yaml
services:
  discord-bot:
    build: ./discord_bot
    environment:
      DISCORD_TOKEN: ${DISCORD_TOKEN}
      PUNSVC_API_BASE: http://backend:8000
    depends_on:
      - backend
```

### System Service (Linux/macOS)

Create `/etc/systemd/system/punsvc-discord-bot.service`:

```ini
[Unit]
Description=punsVC Discord Bot
After=network.target

[Service]
Type=simple
User=punsvc
WorkingDirectory=/opt/punsvc
ExecStart=/usr/bin/python3 discord_bot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable punsvc-discord-bot
sudo systemctl start punsvc-discord-bot
```

## Troubleshooting

### Bot doesn't appear in Discord server
- Make sure bot is invited with correct permissions
- Check that bot token in `.env.discord` is correct

### "Failed to connect to backend"
- Make sure punsVC backend is running on the URL specified in `.env.discord`
- Check firewall settings allow connection

### Commands not appearing
- Reload Discord client (Ctrl+R on Windows/Linux, Cmd+R on macOS)
- Wait a few moments after starting bot for commands to sync
- Check console for sync errors

### Audio generation fails
- Make sure punsVC backend is running and not overloaded
- Check that the voice profile ID is correct
- Check language setting (only `en` and `zh` supported)

## Development

### Install dev dependencies

```bash
pip install -r requirements.txt
# Optional: install dev tools
pip install black flake8 mypy
```

### Run with debug logging

Edit `bot.py` and change logging level:
```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO
    ...
)
```

### Code style

```bash
black discord_bot/
flake8 discord_bot/
```

## Architecture

```
Discord Server
    ↓ (slash command)
Discord Bot (discord_bot/bot.py)
    ↓ (HTTP request)
punsVC Backend API (/discord/generate)
    ↓ (uses)
punsVC TTS Model
    ↓ (streams audio)
Discord Bot
    ↓ (uploads file)
Discord Channel
```

## API Endpoints Used

The Discord bot uses these punsVC backend endpoints:

- `POST /discord/register` - Link Discord user to profile
- `GET /discord/user/{discord_id}` - Get user's linked profile
- `DELETE /discord/user/{discord_id}` - Unlink user
- `POST /discord/generate` - Generate TTS
- `GET /profiles` - List profiles
- `GET /profiles/{id}` - Get profile details
- `GET /audio/{generation_id}` - Download generated audio

## Security

- Bot runs separately from main punsVC application
- API tokens are environment variables (not in code)
- Optional API key authentication for backend (future)
- Discord user IDs are stored in database for profile linking

## Support

For issues, questions, or feature requests, please open an issue on GitHub.
