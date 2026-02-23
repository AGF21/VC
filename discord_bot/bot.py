"""
punsVC Discord Bot - Main bot instance and command handlers.
Enables voice synthesis within Discord using punsVC backend.
"""

import os
import io
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from typing import Optional
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PUNSVC_API_BASE = os.getenv("PUNSVC_API_BASE", "http://localhost:17493")
PUNSVC_API_KEY = os.getenv("PUNSVC_API_KEY")  # Optional, for future auth

if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is required")


class PunsVCBot(commands.Cog):
    """punsVC Discord integration commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session: Optional[aiohttp.ClientSession] = None

    async def cog_load(self):
        """Initialize HTTP session when cog is loaded."""
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        """Close HTTP session when cog is unloaded."""
        if self.session:
            await self.session.close()

    async def _get_profile_name(self, profile_id: str) -> Optional[str]:
        """Get profile name from API."""
        try:
            async with self.session.get(
                f"{PUNSVC_API_BASE}/profiles/{profile_id}",
                headers=self._get_headers()
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("name")
        except Exception as e:
            logger.error(f"Error fetching profile name: {e}")
        return None

    async def _list_profiles(self) -> list:
        """Get all available profiles."""
        try:
            async with self.session.get(
                f"{PUNSVC_API_BASE}/profiles",
                headers=self._get_headers()
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception as e:
            logger.error(f"Error fetching profiles: {e}")
        return []

    def _get_headers(self) -> dict:
        """Get request headers with optional API key."""
        headers = {"Content-Type": "application/json"}
        if PUNSVC_API_KEY:
            headers["Authorization"] = f"Bearer {PUNSVC_API_KEY}"
        return headers

    @app_commands.command(name="generate", description="Generate speech with punsVC")
    @app_commands.describe(
        text="Text to synthesize",
        voice="Voice profile ID (or name)",
        language="Language (en or zh)",
        emotion="Emotion/style instruction (e.g., 'happy', 'sad', 'angry', 'professional')",
    )
    async def generate(
        self,
        interaction: discord.Interaction,
        text: str,
        voice: Optional[str] = None,
        language: str = "en",
        emotion: Optional[str] = None,
    ):
        """Generate TTS audio in Discord."""
        await interaction.response.defer()

        try:
            discord_user_id = str(interaction.user.id)

            # If voice not specified, try to use user's linked profile
            if not voice:
                async with self.session.get(
                    f"{PUNSVC_API_BASE}/discord/user/{discord_user_id}",
                    headers=self._get_headers()
                ) as resp:
                    if resp.status == 200:
                        user_data = await resp.json()
                        voice = user_data.get("profile_id")
                    else:
                        await interaction.followup.send(
                            "❌ No voice profile linked. Use `/connect <profile-id>` first, or specify a voice with `/generate text:... voice:...`"
                        )
                        return

            if not voice:
                await interaction.followup.send(
                    "❌ No voice specified and no linked profile found. Use `/voices` to list available voices."
                )
                return

            # Check text length
            if len(text) > 5000:
                await interaction.followup.send("❌ Text is too long (max 5000 characters)")
                return

            # Validate language
            if language not in ["en", "zh"]:
                await interaction.followup.send("❌ Unsupported language. Supported: en, zh")
                return

            # Generate audio via Discord endpoint
            payload = {
                "discord_user_id": discord_user_id,
                "text": text,
                "language": language,
            }
            if emotion:
                payload["instruct"] = emotion

            async with self.session.post(
                f"{PUNSVC_API_BASE}/discord/generate",
                json=payload,
                headers=self._get_headers()
            ) as resp:
                result = await resp.json()

                if not result.get("success"):
                    await interaction.followup.send(
                        f"❌ Generation failed: {result.get('message', 'Unknown error')}"
                    )
                    return

                # Download and send audio
                generation_id = result.get("generation_id")
                duration = result.get("duration", 0)

                async with self.session.get(
                    f"{PUNSVC_API_BASE}/audio/{generation_id}",
                    headers=self._get_headers()
                ) as audio_resp:
                    if audio_resp.status == 200:
                        audio_data = await audio_resp.read()

                        # Create Discord embed
                        profile_name = await self._get_profile_name(voice)
                        embed = discord.Embed(
                            title="🎤 TTS Generated",
                            description=f"**Voice:** {profile_name or voice}\n**Duration:** {duration:.1f}s",
                            color=discord.Color.blurple()
                        )
                        embed.add_field(name="Text", value=text[:256], inline=False)

                        # Send audio file
                        audio_file = discord.File(
                            io.BytesIO(audio_data),
                            filename=f"tts_{generation_id[:8]}.wav"
                        )
                        await interaction.followup.send(
                            embed=embed,
                            file=audio_file
                        )
                    else:
                        await interaction.followup.send(
                            "❌ Failed to download generated audio"
                        )

        except asyncio.TimeoutError:
            await interaction.followup.send("⏱️ Request timed out. The generation may have taken too long.")
        except Exception as e:
            logger.error(f"Error in generate command: {e}")
            await interaction.followup.send(f"❌ Error: {str(e)[:200]}")

    @app_commands.command(name="voices", description="List available voice profiles")
    async def voices(self, interaction: discord.Interaction):
        """List all available voice profiles."""
        await interaction.response.defer()

        try:
            profiles = await self._list_profiles()

            if not profiles:
                await interaction.followup.send("❌ No voice profiles available")
                return

            # Create embed with profiles
            embed = discord.Embed(
                title="🎤 Available Voices",
                color=discord.Color.blurple()
            )

            # Show first 25 profiles (Discord embed limit)
            for i, profile in enumerate(profiles[:25]):
                profile_id = profile.get("id", "unknown")
                name = profile.get("name", "Unknown")
                lang = profile.get("language", "en")

                embed.add_field(
                    name=name,
                    value=f"`{profile_id}`\nLanguage: {lang}",
                    inline=True
                )

            if len(profiles) > 25:
                embed.set_footer(text=f"... and {len(profiles) - 25} more")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in voices command: {e}")
            await interaction.followup.send(f"❌ Error: {str(e)[:200]}")

    @app_commands.command(name="connect", description="Link your Discord account to a voice profile")
    @app_commands.describe(voice="Voice profile ID to link")
    async def connect(self, interaction: discord.Interaction, voice: str):
        """Link user to a voice profile."""
        await interaction.response.defer()

        try:
            discord_user_id = str(interaction.user.id)

            # Verify profile exists
            async with self.session.get(
                f"{PUNSVC_API_BASE}/profiles/{voice}",
                headers=self._get_headers()
            ) as resp:
                if resp.status != 200:
                    await interaction.followup.send(
                        f"❌ Profile not found. Use `/voices` to list available profiles."
                    )
                    return
                profile = await resp.json()

            # Register user
            payload = {
                "discord_user_id": discord_user_id,
                "discord_guild_id": str(interaction.guild.id) if interaction.guild else None,
                "profile_id": voice,
            }

            async with self.session.post(
                f"{PUNSVC_API_BASE}/discord/register",
                json=payload,
                headers=self._get_headers()
            ) as resp:
                if resp.status in [200, 201]:
                    profile_name = profile.get("name", voice)
                    embed = discord.Embed(
                        title="✅ Voice Connected",
                        description=f"Your voice profile is now: **{profile_name}**",
                        color=discord.Color.green()
                    )
                    await interaction.followup.send(embed=embed)
                else:
                    await interaction.followup.send("❌ Failed to link voice profile")

        except Exception as e:
            logger.error(f"Error in connect command: {e}")
            await interaction.followup.send(f"❌ Error: {str(e)[:200]}")

    @app_commands.command(name="myvoice", description="See your linked voice profile")
    async def myvoice(self, interaction: discord.Interaction):
        """Show user's linked voice profile."""
        await interaction.response.defer()

        try:
            discord_user_id = str(interaction.user.id)

            async with self.session.get(
                f"{PUNSVC_API_BASE}/discord/user/{discord_user_id}",
                headers=self._get_headers()
            ) as resp:
                if resp.status == 200:
                    user_data = await resp.json()
                    profile_id = user_data.get("profile_id")

                    # Get profile details
                    profile_name = await self._get_profile_name(profile_id)

                    embed = discord.Embed(
                        title="🎤 Your Linked Voice",
                        color=discord.Color.blurple()
                    )
                    embed.add_field(name="Profile", value=profile_name or profile_id, inline=False)
                    embed.add_field(name="Profile ID", value=f"`{profile_id}`", inline=False)

                    await interaction.followup.send(embed=embed)
                else:
                    await interaction.followup.send(
                        "❌ No voice profile linked. Use `/connect <profile-id>` to link one."
                    )

        except Exception as e:
            logger.error(f"Error in myvoice command: {e}")
            await interaction.followup.send(f"❌ Error: {str(e)[:200]}")

    @app_commands.command(name="disconnect", description="Unlink your Discord account from voice profile")
    async def disconnect(self, interaction: discord.Interaction):
        """Unlink user from voice profile."""
        await interaction.response.defer()

        try:
            discord_user_id = str(interaction.user.id)

            async with self.session.delete(
                f"{PUNSVC_API_BASE}/discord/user/{discord_user_id}",
                headers=self._get_headers()
            ) as resp:
                if resp.status == 200:
                    embed = discord.Embed(
                        title="✅ Voice Disconnected",
                        description="Your voice profile has been unlinked.",
                        color=discord.Color.green()
                    )
                    await interaction.followup.send(embed=embed)
                else:
                    await interaction.followup.send("❌ Failed to unlink voice profile")

        except Exception as e:
            logger.error(f"Error in disconnect command: {e}")
            await interaction.followup.send(f"❌ Error: {str(e)[:200]}")


async def main():
    """Initialize and run the Discord bot."""
    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(command_prefix="/", intents=intents)

    @bot.event
    async def on_ready():
        """Bot ready event."""
        logger.info(f"✅ Bot logged in as {bot.user}")
        logger.info(f"📡 Connected to punsVC backend at {PUNSVC_API_BASE}")
        try:
            synced = await bot.tree.sync()
            logger.info(f"✅ Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

    @bot.event
    async def on_error(event, *args, **kwargs):
        """Error handler."""
        logger.error(f"Error in {event}", exc_info=True)

    # Load cog
    await bot.add_cog(PunsVCBot(bot))

    # Start bot
    async with bot:
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
