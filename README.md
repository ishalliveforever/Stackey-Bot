# Stackey Bot

Stackey Bot is an open-source Discord bot that integrates with Yours Wallet and provides XP tracking, leveling, and rewards in the form of BitcoinSV (BSV) satoshis. The bot uses Flask for web service integration and SQLite for local database storage. 

## Features

- **XP Tracking:** Tracks users' XP based on message content.
- **Level Calculation:** Calculates user levels based on XP.
- **BSV Rewards:** Sends satoshis to users upon leveling up.
- **Flask Webhooks:** Integrates with web services to handle level-up notifications.
- **Discord Commands:** Provides a command to display current XP and level.

## Prerequisites

- Python 3.7+
- Discord Account and Server
- BitcoinSV Wallet
- Yours Wallet
- `.env` file with necessary environment variables

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/ishalliveforever/stackey-bot.git
   cd stackey-bot
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Create and configure `.env` file:**

   ```plaintext
   DISCORD_TOKEN=your_discord_bot_token
   WALLET_PRIVATE_KEY=your_bsv_wallet_private_key
   ```

4. **Run the bot:**

   ```bash
   python bot.py
   ```

## Usage

### Discord Commands

- **!xp:** Displays your current XP, level, and XP needed for the next level.

### Webhooks

- **/notify_level_up:** Endpoint to notify the bot of a user's level-up event. Expects a JSON payload with `user_id` and `channel_id`.

## Code Overview

### bot.py

```python
import os
import requests
import logging
import discord
import sqlite3
import threading
import math
from discord.ext import commands
from flask import Flask, request
from dotenv import load_dotenv
from bsvlib import Wallet

# Flask app initialization
app = Flask(__name__)

@app.route('/')
def home():
    return "Hello, Flask is running!"

# Logging configuration
logging.basicConfig(level=logging.INFO)

# SQLite database setup
conn = sqlite3.connect('xp_database.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS user_xp (user_id INTEGER PRIMARY KEY, xp INTEGER DEFAULT 0)''')
conn.commit()

# Function definitions (get_user_xp, update_user_xp, calculate_level, etc.)

# Load environment variables
load_dotenv()

# Retrieve bot token and wallet private key
bot_token = os.getenv('DISCORD_TOKEN')
private_key_wif = os.getenv('WALLET_PRIVATE_KEY')

# Discord bot setup
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Discord command to display XP
@bot.command(name='xp', help='Displays your current XP.')
async def show_xp(ctx):
    # Command implementation

# Event handler for new messages
@bot.event
async def on_message(message):
    # Event implementation

# Fetch BSV address function
def fetch_user_address(username):
    # Function implementation

# Send satoshis function
def send_sats(private_key_wif, to_address, amount_sats):
    # Function implementation

# Send level-up message function
async def send_level_up_message(channel, user, xp, level, address):
    # Function implementation

# Flask endpoint for level-up notifications
@app.route('/notify_level_up', methods=['POST'])
def notify_level_up():
    # Endpoint implementation

# Run Flask app in a separate thread
def run_flask_app():
    app.run(host='0.0.0.0', port=5002)

# Main function to start bot and Flask app
if __name__ == '__main__':
    threading.Thread(target=run_flask_app).start()
    bot.run(bot_token)
```

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Create a new Pull Request

## Donate
## BSV Address: 1AehJyGHnPXMZ2zg4wdBjaowdLTebysFus 
## BCH: qrxx9gycn3rrp6pd29p84ez2cceqc93gl5zdvttrjw 
## BTC Address: bc1q5dc49up9k8ne90xn4n6edxd908n8het9maxwhu 
## Doge: DJ1pkmDwdLS94ZSEJdVJoq2MHprDfjaUpZ 
## Sol: 9HmpAhDoicGehmGhbbN5kmhsd5uZGm2DEDt68cGiUseJ
