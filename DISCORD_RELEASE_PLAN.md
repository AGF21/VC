# Discord Bot Integration Release Plan

**Version:** 0.2.0 (Minor release - new feature)
**Branch:** `claude/deployment-strategy-planning-WSPju`

## Overview

Add Discord bot integration as an **optional, standalone service** without modifying the core application. The Discord bot will:
- Allow users to generate TTS within Discord via slash commands
- Link Discord users to their punsVC voice profiles
- Stream generated audio directly to Discord channels

## Architecture

```
punsVC Core (unchanged)
├── Web app (unchanged)
├── Desktop app (unchanged)
└── Backend API (minimal changes)
    └── New Discord endpoints (optional feature)

Discord Bot Service (NEW)
├── discord_bot/ (new directory)
├── discord_bot/bot.py (main bot service)
├── discord_bot/requirements.txt
├── discord_bot/config.example.env
└── docker-compose.discord.yml (optional)
```

## Changes Required

### 1. Database Schema (Minimal)
Add new table for Discord user mappings:
```sql
discord_users (
  id,
  discord_user_id,
  discord_guild_id,
  punsvc_profile_id,
  created_at,
  updated_at
)
```

### 2. Backend API (New Endpoints)
- `POST /discord/register` - Link Discord user to profile
- `GET /discord/user/{discord_id}` - Get linked profile
- `DELETE /discord/user/{discord_id}` - Unlink user

### 3. Discord Bot Service (New)
- New Python service using `discord.py`
- Commands:
  - `/generate text:"..." voice:"voice-id"`
  - `/voices` - List available voices
  - `/myvoices` - Show linked voices
  - `/connect voice-id` - Link a voice profile

### 4. Documentation
- New `docs/DISCORD_BOT_SETUP.md`
- Update main README with Discord bot section
- Update `CONTRIBUTING.md` with bot development guidelines

### 5. Version Bump
- Bump from 0.1.13 → 0.2.0
- Add Discord bot to bumpversion config

## Implementation Steps

### Phase 1: Database & Backend (2-3 hours)
1. Add Discord user table migration
2. Create Discord user models in backend
3. Implement Discord API endpoints

### Phase 2: Discord Bot (4-5 hours)
1. Create bot service directory structure
2. Implement slash commands
3. Add error handling and rate limiting
4. Test with Discord sandbox/server

### Phase 3: Documentation & Release (1-2 hours)
1. Write Discord setup guide
2. Update README
3. Bump version
4. Create release notes
5. Commit and push

## Files to Create/Modify

### Create:
- `discord_bot/` (directory)
- `discord_bot/__init__.py`
- `discord_bot/bot.py`
- `discord_bot/commands/` (directory)
- `discord_bot/commands/generate.py`
- `discord_bot/commands/voices.py`
- `discord_bot/config.py`
- `discord_bot/requirements.txt`
- `discord_bot/README.md`
- `docs/DISCORD_BOT_SETUP.md`
- `.env.discord.example`
- `docker-compose.discord.yml`

### Modify:
- `backend/models.py` - Add DiscordUser model
- `backend/database.py` - Add Discord user table
- `backend/main.py` - Add Discord endpoints
- `README.md` - Add Discord bot section
- `.bumpversion.cfg` - Add discord_bot version tracking
- `package.json` - Add Discord bot info

## Key Design Decisions

✅ **Keep it separate** - Discord bot is a standalone service
✅ **No breaking changes** - Core app unaffected
✅ **Optional feature** - Users can skip Discord setup
✅ **Simple auth** - Use Discord user ID for initial MVP
✅ **Rate limiting** - Prevent abuse with per-user quotas

## Testing Strategy

1. Unit tests for Discord endpoints
2. Integration tests with test Discord server
3. Manual testing with bot commands
4. Load testing for concurrent users

## Deployment

### Option 1: Docker
```bash
docker-compose -f docker-compose.discord.yml up
```

### Option 2: Manual
```bash
cd discord_bot
pip install -r requirements.txt
python bot.py
```

### Option 3: System Service (systemd)
Create `discord-bot.service` for Linux deployments

## Rollback Plan

- Feature is completely isolated
- Simply don't deploy Discord bot service
- No database migration required for core app
- Can be enabled/disabled via config flag

## Success Criteria

✅ Discord bot responds to slash commands
✅ Users can link Discord ID to voice profile
✅ Audio generation works via Discord
✅ No errors in core application
✅ Documentation is clear and complete
✅ Release notes highlight new feature

---

**Next Steps:**
1. Create database migration for Discord users
2. Add Discord models and endpoints to backend
3. Create Discord bot service
4. Write documentation
5. Commit changes with clear commit messages
