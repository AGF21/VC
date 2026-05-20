import os
import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Configuration
PUNSVC_API_URL = "http://localhost:8000"
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
VOICE_CLIENT = None

# Emotion variants for regeneration
EMOTIONS = ["neutral", "happy", "sad", "angry", "excited", "calm"]


class EmotionButton(discord.ui.View):
    def __init__(self, profile_id: str, text: str, language: str = "en"):
        super().__init__()
        self.profile_id = profile_id
        self.text = text
        self.language = language

    @discord.ui.button(label="😊 Happy", style=discord.ButtonStyle.primary)
    async def happy_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.regenerate(interaction, "happy")

    @discord.ui.button(label="😢 Sad", style=discord.ButtonStyle.primary)
    async def sad_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.regenerate(interaction, "sad")

    @discord.ui.button(label="😠 Angry", style=discord.ButtonStyle.primary)
    async def angry_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.regenerate(interaction, "angry")

    @discord.ui.button(label="🤩 Excited", style=discord.ButtonStyle.primary)
    async def excited_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.regenerate(interaction, "excited")

    async def regenerate(self, interaction: discord.Interaction, emotion: str):
        await interaction.response.defer()
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "profile_id": self.profile_id,
                    "text": self.text,
                    "language": self.language,
                    "instruct": f"Speak with a {emotion} tone and emotion",
                    "model_type": "qwen",
                    "model_size": "1.7B"
                }
                async with session.post(f"{PUNSVC_API_URL}/generate", json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        audio_url = f"{PUNSVC_API_URL}/audio/{data['id']}.wav"
                        embed = discord.Embed(
                            title="🎙️ Generated Speech",
                            description=f"Emotion: {emotion.capitalize()}",
                            color=discord.Color.blue()
                        )
                        embed.add_field(name="Text", value=self.text[:1024], inline=False)
                        embed.set_footer(text=f"Duration: {data['duration']:.2f}s")
                        await interaction.followup.send(
                            embed=embed,
                            file=discord.File(audio_url, filename="speech.wav"),
                            view=self
                        )
                    else:
                        await interaction.followup.send(f"❌ Generation failed: {resp.status}")
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}")


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    print(f"🤖 Bot logged in as {bot.user}")


@bot.tree.command(name="connect", description="Connect the bot to your voice channel")
async def connect(interaction: discord.Interaction):
    global VOICE_CLIENT

    if not interaction.user.voice:
        await interaction.response.send_message("❌ You need to be in a voice channel!", ephemeral=True)
        return

    try:
        VOICE_CLIENT = await interaction.user.voice.channel.connect()
        await interaction.response.send_message(f"✅ Connected to {interaction.user.voice.channel.mention}")
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to connect: {str(e)}", ephemeral=True)


@bot.tree.command(name="generate", description="Generate speech from a voice profile")
@app_commands.describe(
    text="The text to generate speech from",
    profile_id="The voice profile ID",
    language="Language code (en, zh, etc.)"
)
async def generate(interaction: discord.Interaction, text: str, profile_id: str, language: str = "en"):
    await interaction.response.defer()

    if not VOICE_CLIENT or not VOICE_CLIENT.is_connected():
        await interaction.followup.send("❌ Bot is not connected to a voice channel. Use /connect first!", ephemeral=True)
        return

    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "profile_id": profile_id,
                "text": text,
                "language": language,
                "model_type": "qwen",
                "model_size": "1.7B"
            }
            async with session.post(f"{PUNSVC_API_URL}/generate", json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()

                    # Create embed with speech info
                    embed = discord.Embed(
                        title="🎙️ Generated Speech",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="Text", value=text[:1024], inline=False)
                    embed.add_field(name="Profile ID", value=profile_id, inline=True)
                    embed.add_field(name="Language", value=language, inline=True)
                    embed.set_footer(text=f"Duration: {data['duration']:.2f}s")

                    # Send message with emotion buttons
                    view = EmotionButton(profile_id, text, language)
                    await interaction.followup.send(
                        embed=embed,
                        view=view
                    )

                    # Play audio in voice channel
                    audio_source = discord.FFmpegPCMAudio(f"{PUNSVC_API_URL}/audio/{data['id']}.wav")
                    if not VOICE_CLIENT.is_playing():
                        VOICE_CLIENT.play(audio_source)
                else:
                    await interaction.followup.send(f"❌ Generation failed: {resp.status}")
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")


@bot.tree.command(name="disconnect", description="Disconnect the bot from the voice channel")
async def disconnect(interaction: discord.Interaction):
    global VOICE_CLIENT

    if not VOICE_CLIENT or not VOICE_CLIENT.is_connected():
        await interaction.response.send_message("❌ Bot is not connected to a voice channel!", ephemeral=True)
        return

    await VOICE_CLIENT.disconnect()
    VOICE_CLIENT = None
    await interaction.response.send_message("✅ Disconnected from voice channel")


@bot.tree.command(name="voices", description="List all available voices")
async def voices(interaction: discord.Interaction):
    await interaction.response.defer()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{PUNSVC_API_URL}/profiles") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data:
                        embed = discord.Embed(
                            title="🎤 Available Voices",
                            color=discord.Color.blue()
                        )
                        for profile in data[:15]:
                            embed.add_field(
                                name=f"{profile.get('name', 'Unknown')} ({profile['id']})",
                                value=f"Language: {profile.get('language', 'Unknown')}",
                                inline=False
                            )
                        if len(data) > 15:
                            embed.set_footer(text=f"Showing 15 of {len(data)} voices")
                        await interaction.followup.send(embed=embed)
                    else:
                        await interaction.followup.send("❌ No voices found!")
                else:
                    await interaction.followup.send(f"❌ Failed to fetch voices: {resp.status}")
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")


@bot.tree.command(name="profiles", description="List available voice profiles")
async def profiles(interaction: discord.Interaction):
    await interaction.response.defer()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{PUNSVC_API_URL}/profiles") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data:
                        embed = discord.Embed(
                            title="🎤 Available Voice Profiles",
                            color=discord.Color.blue()
                        )
                        for profile in data[:10]:  # Show first 10 profiles
                            embed.add_field(
                                name=f"ID: {profile['id']}",
                                value=f"Name: {profile.get('name', 'Unknown')}\nLanguage: {profile.get('language', 'Unknown')}",
                                inline=False
                            )
                        if len(data) > 10:
                            embed.set_footer(text=f"Showing 10 of {len(data)} profiles")
                        await interaction.followup.send(embed=embed)
                    else:
                        await interaction.followup.send("❌ No voice profiles found!")
                else:
                    await interaction.followup.send(f"❌ Failed to fetch profiles: {resp.status}")
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ DISCORD_BOT_TOKEN not set in environment variables!")
        exit(1)

    bot.run(DISCORD_TOKEN)
