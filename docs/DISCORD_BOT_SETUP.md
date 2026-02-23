# Discord Bot Integration Setup Guide

Complete guide for setting up the punsVC Discord bot.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Creating a Discord Application](#creating-a-discord-application)
4. [Inviting the Bot to Your Server](#inviting-the-bot-to-your-server)
5. [Running the Discord Bot](#running-the-discord-bot)
6. [Using Discord Commands](#using-discord-commands)
7. [Advanced Configuration](#advanced-configuration)
8. [Deployment Options](#deployment-options)

## Overview

The punsVC Discord Bot allows you to generate voice synthesis audio directly within Discord using your custom voice profiles.

**Key Features:**
- Slash commands for easy interaction
- Link Discord accounts to voice profiles
- Generate TTS with custom voices
- Share audio files directly in Discord
- Works alongside standalone punsVC app

## Prerequisites

### Requirements

1. **punsVC Backend Running** - The bot connects to your local/remote punsVC server
2. **Python 3.9+** - To run the bot
3. **Discord Server** - Where you want to use the bot
4. **Discord Developer Account** - Free, required to create the bot application

### Already have punsVC installed?

If you've already installed punsVC, you have everything needed except the Discord bot dependencies.

## Creating a Discord Application

### Step 1: Go to Discord Developer Portal

1. Visit [https://discord.com/developers/applications](https://discord.com/developers/applications)
2. Sign in with your Discord account
3. Click "New Application" button in the top right

### Step 2: Name Your Application

1. Enter a name (e.g., "punsVC", "VoiceBot")
2. Click "Create"

### Step 3: Create a Bot User

1. In the left sidebar, click "Bot"
2. Click "Add Bot"
3. You now have a bot instance!

### Step 4: Copy Your Bot Token

1. Under the bot name, click "Copy" next to the token
2. **Keep this token secret!** Anyone with this token can control your bot.
3. Save it somewhere safe for now

### Step 5: Configure Bot Intents

1. Scroll down to "Privileged Gateway Intents"
2. Enable:
   - ✅ **Message Content Intent** (needed for text processing)
3. Click "Save Changes"

## Inviting the Bot to Your Server

### Step 1: Generate Invite URL

1. In Discord Developer Portal, go to OAuth2 → URL Generator
2. Select these scopes:
   - ✅ `bot`
   - ✅ `applications.commands` (for slash commands)
3. Select these permissions:
   - ✅ Send Messages
   - ✅ Embed Links (for rich formatting)
   - ✅ Attach Files (for audio files)
   - ✅ Read Messages/View Channels
4. Copy the generated URL

### Step 2: Invite to Your Server

1. Open the generated URL in your browser
2. Select the Discord server from the dropdown
3. Click "Authorize"
4. Complete the CAPTCHA if prompted

### Step 3: Verify Bot is in Your Server

1. Go back to your Discord server
2. You should see the bot appear in the member list
3. Check that it has the correct permissions

## Running the Discord Bot

### Option 1: Manual Installation (Recommended for Testing)

#### 1. Install Dependencies

```bash
cd /path/to/punsvc
cd discord_bot
pip install -r requirements.txt
```

#### 2. Create Configuration File

```bash
# From the repo root
cp .env.discord.example .env.discord
```

#### 3. Edit Configuration

```bash
nano .env.discord
```

Add your Discord bot token:

```env
DISCORD_TOKEN=your_actual_bot_token_here
PUNSVC_API_BASE=http://localhost:8000
```

#### 4. Start the Bot

First, make sure punsVC backend is running:

```bash
# Terminal 1: Backend
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Then in another terminal:

```bash
# Terminal 2: Discord Bot
cd discord_bot
python bot.py
```

You should see:
```
✅ Bot logged in as punsVC#xxxx
📡 Connected to punsVC backend at http://localhost:8000
✅ Synced X command(s)
```

### Option 2: Docker

Create `.env.discord`:

```bash
cp .env.discord.example .env.discord
# Edit with your token
nano .env.discord
```

Run with Docker:

```bash
docker build -f discord_bot/Dockerfile -t punsvc-discord-bot .
docker run -d \
  --name punsvc-discord-bot \
  --env-file .env.discord \
  -e PUNSVC_API_BASE=http://host.docker.internal:8000 \
  punsvc-discord-bot
```

### Option 3: Docker Compose

Add to your docker-compose.yml:

```yaml
discord-bot:
  build:
    context: .
    dockerfile: discord_bot/Dockerfile
  environment:
    DISCORD_TOKEN: ${DISCORD_TOKEN}
    PUNSVC_API_BASE: http://backend:8000
  depends_on:
    - backend
  restart: unless-stopped
```

Then:

```bash
docker-compose up discord-bot
```

## Using Discord Commands

Once the bot is running and synced, use these commands in your Discord server:

### Generate Audio

```
/generate text:"Hello world" voice:profile-id language:en
```

**Parameters:**
- `text` - Text to synthesize (max 5000 chars)
- `voice` - Voice profile ID (optional, uses linked profile if omitted)
- `language` - `en` or `zh` (default: en)

### List Voices

```
/voices
```

Shows all available voice profiles.

### Link Your Voice

```
/connect voice:profile-id
```

Links your Discord account to a voice profile. After this, you can omit the `voice` parameter in `/generate`.

### Check Your Voice

```
/myvoice
```

Shows your currently linked voice profile.

### Unlink Your Voice

```
/disconnect
```

Removes your voice profile link.

## Advanced Configuration

### Remote punsVC Server

If your punsVC backend is on a different machine:

```env
DISCORD_TOKEN=your_token
PUNSVC_API_BASE=http://192.168.1.100:8000
```

### API Key Authentication (Optional)

If you set up API key authentication on your backend:

```env
DISCORD_TOKEN=your_token
PUNSVC_API_BASE=http://localhost:8000
PUNSVC_API_KEY=your_api_key
```

### Custom Bot Name/Icon

In Discord Developer Portal:
1. Go to Application Info
2. Edit the name and icon
3. Save

### Rate Limiting

The bot will queue generations if multiple users request simultaneously. This is normal behavior - the backend processes them in order.

## Deployment Options

### Production Deployment (Linux Server)

#### 1. Create System User

```bash
sudo useradd -m -d /opt/punsvc punsvc
sudo mkdir -p /opt/punsvc
sudo chown -R punsvc:punsvc /opt/punsvc
```

#### 2. Copy Application

```bash
cd /opt/punsvc
# Copy punsVC files
```

#### 3. Create Systemd Service

Create `/etc/systemd/system/punsvc-discord-bot.service`:

```ini
[Unit]
Description=punsVC Discord Bot
After=network.target punsvc-backend.service
Requires=punsvc-backend.service

[Service]
Type=simple
User=punsvc
WorkingDirectory=/opt/punsvc
ExecStart=/usr/bin/python3 /opt/punsvc/discord_bot/bot.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

Environment="PATH=/opt/punsvc/venv/bin"

[Install]
WantedBy=multi-user.target
```

#### 4. Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable punsvc-discord-bot
sudo systemctl start punsvc-discord-bot
sudo systemctl status punsvc-discord-bot
```

#### 5. View Logs

```bash
journalctl -u punsvc-discord-bot -f
```

### Cloud Hosting (Heroku, Railway, Replit)

1. Add your repo to the service
2. Create `.env` with `DISCORD_TOKEN` and `PUNSVC_API_BASE`
3. Create `Procfile`:
   ```
   discord-bot: python discord_bot/bot.py
   ```
4. Deploy

### Keep Bot Running

Use process managers:

**pm2** (Node.js-based, works with any process):

```bash
npm install -g pm2
pm2 start "python discord_bot/bot.py" --name punsvc-bot
pm2 save
pm2 startup
```

**supervisor** (Linux):

```bash
sudo apt install supervisor
```

Create `/etc/supervisor/conf.d/punsvc-bot.conf`:

```ini
[program:punsvc-bot]
command=/usr/bin/python3 /opt/punsvc/discord_bot/bot.py
directory=/opt/punsvc
user=punsvc
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/punsvc-bot.log
```

Then:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start punsvc-bot
```

## Troubleshooting

### Bot not appearing in server

**Cause:** Bot not properly invited or permissions missing

**Fix:**
1. Check that you used the correct invite URL
2. Verify bot has these permissions in server settings:
   - Send Messages
   - Embed Links
   - Attach Files
3. Reinvite the bot

### Commands not showing

**Cause:** Command sync failed or cache issue

**Fix:**
1. Restart the bot
2. Reload Discord (Ctrl+R / Cmd+R)
3. Wait 30 seconds
4. Check console for sync errors

### "Failed to connect to backend"

**Cause:** Backend not running or wrong URL

**Fix:**
1. Make sure punsVC backend is running:
   ```bash
   curl http://localhost:8000/
   ```
2. Check `.env.discord` has correct `PUNSVC_API_BASE`
3. If using Docker, use `http://host.docker.internal:8000`

### "Generation failed"

**Cause:** Backend error or invalid profile

**Fix:**
1. Verify the profile ID is correct: `/voices`
2. Check backend logs for errors
3. Make sure the backend isn't overloaded

### "No voice profile linked"

**Cause:** Haven't linked account yet or wrong profile

**Fix:**
1. Run `/voices` to list available profiles
2. Run `/connect voice:profile-id` to link one
3. Run `/myvoice` to confirm

### Bot logs in then exits

**Cause:** Authentication error

**Fix:**
1. Verify `DISCORD_TOKEN` is correct (copy from DevPortal again)
2. Make sure bot user exists (check DevPortal Bot page)
3. Check for typos in `.env.discord`

## Getting Help

### Documentation
- [Discord.py Documentation](https://discordpy.readthedocs.io/)
- [Discord Developer Docs](https://discord.com/developers/docs)
- Main [punsVC README](../README.md)

### Common Issues
- Check logs: `python bot.py` shows errors in console
- Verify backend: `curl http://localhost:8000/health`
- Test profile access: `/voices` command should list profiles

### Report Issues
- Open a GitHub issue with:
  - Error messages from bot logs
  - Your `.env.discord` (without token)
  - Steps to reproduce
