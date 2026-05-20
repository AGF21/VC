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
PUNSVC_API_URL = "http://localhost:17493"
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Connected voice profile per user
connected_voices = {}  # {user_id: profile_id}

# Emotion variants for regeneration
EMOTIONS = ["neutral", "happy", "sad", "angry", "excited", "calm"]


class EmotionButton(discord.ui.View):
    def __init__(self, profile_id: str, text: str):
        super().__init__()
        self.profile_id = profile_id
        self.text = text

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
                    "instruct": f"Speak with a {emotion} tone and emotion",
                    "model_type": "qwen",
                    "model_size": "1.7B"
                }
                async with session.post(f"{PUNSVC_API_URL}/generate", json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        embed = discord.Embed(
                            title="🎙️ Generated Speech",
                            description=f"Emotion: {emotion.capitalize()}",
                            color=discord.Color.blue()
                        )
                        embed.add_field(name="Text", value=self.text[:1024], inline=False)
                        embed.set_footer(text=f"Duration: {data['duration']:.2f}s")
                        await interaction.followup.send(
                            embed=embed,
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


@bot.tree.command(name="connect", description="Connect to a voice profile")
@app_commands.describe(profile_id="The voice profile ID to connect to")
async def connect(interaction: discord.Interaction, profile_id: str):
    await interaction.response.defer()

    try:
        async with aiohttp.ClientSession() as session:
            # Verify the profile exists
            async with session.get(f"{PUNSVC_API_URL}/profiles/{profile_id}") as resp:
                if resp.status == 200:
                    profile = await resp.json()
                    connected_voices[interaction.user.id] = profile_id
                    embed = discord.Embed(
                        title="✅ Connected to Voice Profile",
                        description=f"**{profile.get('name', 'Unknown')}**",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="Profile ID", value=profile_id, inline=True)
                    embed.add_field(name="Language", value=profile.get('language', 'Unknown'), inline=True)
                    await interaction.followup.send(embed=embed)
                else:
                    await interaction.followup.send(f"❌ Voice profile not found: {profile_id}")
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")


@bot.tree.command(name="generate", description="Generate speech with the connected voice")
@app_commands.describe(text="The text to generate speech from")
async def generate(interaction: discord.Interaction, text: str):
    await interaction.response.defer()

    user_id = interaction.user.id
    if user_id not in connected_voices:
        await interaction.followup.send("❌ No voice profile connected. Use `/connect <profile_id>` first!", ephemeral=True)
        return

    profile_id = connected_voices[user_id]

    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "profile_id": profile_id,
                "text": text,
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
                    embed.set_footer(text=f"Duration: {data['duration']:.2f}s")

                    # Send message with emotion buttons
                    view = EmotionButton(profile_id, text)
                    await interaction.followup.send(
                        embed=embed,
                        view=view
                    )
                else:
                    await interaction.followup.send(f"❌ Generation failed: {resp.status}")
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")


@bot.tree.command(name="disconnect", description="Disconnect from the current voice profile")
async def disconnect(interaction: discord.Interaction):
    user_id = interaction.user.id

    if user_id not in connected_voices:
        await interaction.response.send_message("❌ No voice profile connected!", ephemeral=True)
        return

    profile_id = connected_voices.pop(user_id)
    await interaction.response.send_message(f"✅ Disconnected from voice profile (ID: {profile_id})")


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
