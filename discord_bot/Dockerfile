FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY discord_bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY discord_bot/ .

# Run bot
CMD ["python", "bot.py"]
