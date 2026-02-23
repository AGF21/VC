# Changelog

All notable changes to punsVC will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-02-23

### Added

#### Discord Bot Integration
- **Discord Bot Service** - Standalone Python-based Discord bot for punsVC integration
- **Slash Commands** - Five new Discord slash commands for TTS generation:
  - `/generate` - Generate speech from text with custom voices
  - `/voices` - List all available voice profiles
  - `/connect` - Link Discord account to a voice profile
  - `/myvoice` - Show current linked voice profile
  - `/disconnect` - Unlink Discord account from voice profile
- **Discord User Linking** - Store and manage Discord user to voice profile associations
- **Audio Streaming** - Stream generated audio files directly to Discord channels

#### Backend API
- **Discord Endpoints**:
  - `POST /discord/register` - Register Discord user and link to profile
  - `GET /discord/user/{discord_id}` - Get Discord user's linked profile
  - `DELETE /discord/user/{discord_id}` - Unlink Discord user
  - `POST /discord/generate` - Generate TTS from Discord request
- **Discord User Database Table** - Store Discord user mappings

#### Documentation
- **Discord Setup Guide** - Comprehensive guide for creating and configuring Discord bot (`docs/DISCORD_BOT_SETUP.md`)
- **Discord Bot README** - Full documentation for running and deploying the bot (`discord_bot/README.md`)
- **Updated Main README** - Added Discord integration section with quick-start instructions

#### Deployment
- **Docker Support** - Dockerfile and Docker Compose configuration for Discord bot
- **Systemd Service** - Example systemd service file for Linux deployments
- **Process Manager Support** - PM2 and supervisor configurations

### Changed

- **Database Schema** - Added `discord_users` table for user mappings
- **API Models** - Added Pydantic models for Discord integration (`DiscordUserRegister`, `DiscordUserResponse`, `DiscordGenerateRequest`, `DiscordGenerateResponse`)
- **Main README** - Enhanced with Discord integration section
- **Feature List** - Added Discord Bot to flexible deployment options

### Technical Details

- Discord Bot built with `discord.py` (2.3.2)
- Async HTTP client using `aiohttp` for API communication
- Environment variable configuration with `.env` files
- Optional API key authentication support (for future use)
- Isolated service architecture (doesn't affect core application)

### Notes

- **No breaking changes** - Core punsVC application remains unchanged
- **Completely optional** - Discord bot is an independent add-on service
- **Backwards compatible** - Existing API, desktop app, and web version unaffected
- **Language support** - Discord bot currently supports English and Chinese (en/zh) languages

## [0.1.13] - 2026-02-21

### Added

- Story timeline improvements
- Enhanced audio preview controls

## [0.1.0] - 2026-01-25

### Added

#### Core Features
- **Voice Cloning** - Clone voices from audio samples using Qwen3-TTS (1.7B and 0.6B models)
- **Voice Profile Management** - Create, edit, and organize voice profiles with multiple samples
- **Speech Generation** - Generate high-quality speech from text using cloned voices
- **Generation History** - Track all generations with search and filtering capabilities
- **Audio Transcription** - Automatic transcription powered by Whisper
- **In-App Recording** - Record audio samples directly in the app with waveform visualization

#### Desktop App
- **Tauri Desktop App** - Native desktop application for macOS, Windows, and Linux
- **Local Server Mode** - Embedded Python server runs automatically
- **Remote Server Mode** - Connect to a remote punsVC server on your network
- **Auto-Updates** - Automatic update notifications and installation

#### API
- **REST API** - Full REST API for voice synthesis and profile management
- **OpenAPI Documentation** - Interactive API docs at `/docs` endpoint
- **Type-Safe Client** - Auto-generated TypeScript client from OpenAPI schema

#### Technical
- **Voice Prompt Caching** - Fast regeneration with cached voice prompts
- **Multi-Sample Support** - Combine multiple audio samples for better voice quality
- **GPU/CPU/MPS Support** - Automatic device detection and optimization
- **Model Management** - Lazy loading and VRAM management
- **SQLite Database** - Local data persistence

### Technical Details

- Built with Tauri v2 (Rust + React)
- FastAPI backend with async Python
- TypeScript frontend with React Query and Zustand
- Qwen3-TTS for voice cloning
- Whisper for transcription

### Platform Support

- macOS (Apple Silicon and Intel)
- Windows
- Linux (AppImage)

---

## [Unreleased]

### Fixed
- Audio export failing when Tauri save dialog returns object instead of string path

### Added
- **Makefile** - Comprehensive development workflow automation with commands for setup, development, building, testing, and code quality checks
  - Includes Python version detection and compatibility warnings
  - Self-documenting help system with `make help`
  - Colored output for better readability
  - Supports parallel development server execution

### Changed
- **README** - Added Makefile reference and updated Quick Start with Makefile-based setup instructions alongside manual setup

---

## [Unreleased - Planned]

### Planned
- Real-time streaming synthesis
- Conversation mode with multiple speakers
- Voice effects (pitch shift, reverb, M3GAN-style)
- Timeline-based audio editor
- Additional voice models (XTTS, Bark)
- Voice design from text descriptions
- Project system for saving sessions
- Plugin architecture

---

[0.1.0]: https://github.com/jamiepine/voicebox/releases/tag/v0.1.0
