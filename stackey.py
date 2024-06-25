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

# Initialize the Flask app
app = Flask(__name__)

@app.route('/')
def home():
    # Default route to verify Flask is running
    return "Hello, Flask is running!"

# Set up basic configuration for logging
logging.basicConfig(level=logging.INFO)

# Initialize the SQLite database and create the user_xp table if it doesn't exist
conn = sqlite3.connect('xp_database.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS user_xp (user_id INTEGER PRIMARY KEY, xp INTEGER DEFAULT 0)''')
conn.commit()

# Function to fetch the user's XP from the database
def get_user_xp(user_id):
    logging.info(f"Fetching XP for user ID: {user_id}")
    c.execute("SELECT xp FROM user_xp WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    if result:
        logging.info(f"Found XP: {result[0]} for user ID: {user_id}")
        return result[0]
    else:
        logging.info(f"No XP record found for user ID: {user_id}")
        return 0

# Function to update the user's XP in the database
def update_user_xp(user_id, xp):
    logging.info(f"Updating XP for user ID: {user_id} to {xp}")
    c.execute("INSERT OR REPLACE INTO user_xp (user_id, xp) VALUES (?, ?)", (user_id, xp))
    conn.commit()

# Function to calculate the user's level based on XP
def calculate_level(xp):
    logging.info(f"Calculating level for XP: {xp}")
    k = 15
    level = int(math.sqrt(xp / k))
    logging.info(f"Calculated level: {level} for XP: {xp}")
    return level

# Function to calculate the XP required for the next level
def calculate_next_level_xp(level):
    logging.info(f"Calculating XP for the next level from level: {level}")
    k = 15
    next_level = level + 1
    next_level_xp = int(k * next_level**2)
    logging.info(f"XP required for next level {next_level}: {next_level_xp}")
    return next_level_xp

# Function to check if the user has leveled up
def check_level_up(current_level, new_level):
    logging.info(f"Checking level up: current level {current_level}, new level {new_level}")
    return new_level > current_level

# Load environment variables from a .env file
logging.info("Loading environment variables")
load_dotenv()

# Retrieve the bot token and wallet private key from environment variables
bot_token = os.getenv('DISCORD_TOKEN')
private_key_wif = os.getenv('WALLET_PRIVATE_KEY')
logging.info(f"Bot token loaded: {bool(bot_token)}")
logging.info(f"Private key loaded: {bool(private_key_wif)}")

# Define intents for the Discord bot
intents = discord.Intents.default()
intents.messages = True  # To receive messages
intents.guilds = True    # Access to guild events
intents.message_content = True  # Required to access message content under new API rules

# Initialize the Discord bot
bot = commands.Bot(command_prefix='!', intents=intents)

# Command to display the user's current XP
@bot.command(name='xp', help='Displays your current XP.')
async def show_xp(ctx):
    user_id = ctx.author.id
    xp = get_user_xp(user_id)
    level = calculate_level(xp)
    next_level_xp = calculate_next_level_xp(level)
    xp_to_next_level = next_level_xp - xp
    embed = discord.Embed(title="XP Progress", color=discord.Color.blue())
    embed.add_field(name="Current XP", value=f"{xp}", inline=False)
    embed.add_field(name="Level", value=f"{level}", inline=False)
    embed.add_field(name="XP to Next Level", value=f"{xp_to_next_level}", inline=False)
    logging.info(f"Sending XP progress embed to user ID: {user_id}")
    await ctx.send(embed=embed)

# Event handler for new messages
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Check if the message is the !xp command
    if message.content.startswith('!xp'):
        await bot.process_commands(message)
        return

    # Calculate and update the user's XP based on the message length
    words = message.content.split()
    if len(words) <= 1:
        return
    
    user_id = message.author.id
    current_xp = get_user_xp(user_id)
    new_xp = current_xp + len(words)
    current_level = calculate_level(current_xp)
    new_level = calculate_level(new_xp)
    update_user_xp(user_id, new_xp)

    logging.info(f"User {message.author} (ID: {user_id}) XP updated to {new_xp} and leveled up to {new_level}")

    # Check if the user has leveled up and send a level-up message if they have
    if check_level_up(current_level, new_level):
        channel = message.channel
        user_address = fetch_user_address(message.author.name)
        if user_address:
            logging.info(f"User address found: {user_address}")
            await send_level_up_message(channel, message.author, new_xp, new_level, user_address)
        else:
            logging.error(f"No address found for user {message.author.name}")

    await bot.process_commands(message)

# Function to fetch the user's BitcoinSV address from a web service
def fetch_user_address(username):
    logging.info(f"Fetching BSV address for username: {username}")
    try:
        response = requests.get('https://1satsociety.com/show_users')
        response.raise_for_status()
        users = response.text.split('<br>')
        for user in users:
            if user.startswith(f"Username: {username}, BSV Address:"):
                address_info = user.split(", BSV Address: ")[1].split(",")[0]
                if address_info != "Not set":
                    logging.info(f"Address retrieved for username {username}: {address_info}")
                    return address_info
        logging.info(f"No address found for username {username}")
    except requests.RequestException as e:
        logging.error(f"Failed to retrieve user addresses: {e}")
    return None

# Function to send satoshis (BSV) using bsvlib
def send_sats(private_key_wif, to_address, amount_sats):
    logging.info(f"Preparing to send {amount_sats} sats to {to_address}")
    try:
        outputs = [(to_address, amount_sats)]
        wallet = Wallet([private_key_wif])
        tx = wallet.create_transaction(outputs=outputs)
        result = tx.broadcast()
        logging.info(f"Transaction successful: {result}")
        return result.data
    except Exception as e:
        logging.error(f"Failed to send transaction: {str(e)}")
        return None

# Function to send a level-up message to the user
async def send_level_up_message(channel, user, xp, level, address):
    try:
        logging.info(f"Preparing to send level up message to {user.name} in channel {channel.name}")

        amount_sats = level * 218  # Set the amount of satoshis to send for leveling up
        tx_id = send_sats(private_key_wif, address, amount_sats)

        if tx_id:
            next_level_xp = calculate_next_level_xp(level)
            xp_to_next_level = next_level_xp - xp
            embed = discord.Embed(title="🚨Amazing Fren Alert!🚨", color=discord.Color.orange())
            embed.add_field(name="Congratulations!", value=f"{user.mention}, you have leveled up to level {level}!", inline=False)
            embed.add_field(name="Reward", value=f"{amount_sats} sats have been sent to you.", inline=False)
            embed.add_field(name="Transaction ID", value=f"{tx_id}", inline=False)
            embed.add_field(name="XP to Next Level", value=f"{xp_to_next_level} XP", inline=False)
        else:
            embed = discord.Embed(title="Level Up!", color=discord.Color.red())
            embed.add_field(name="Congratulations!", value=f"{user.mention}, you have leveled up to level {level}!", inline=False)
            embed.add_field(name="Reward", value="However, there was an issue sending your reward.", inline=False)

        await channel.send(embed=embed)
        logging.info(f"Message successfully sent to {user.name} in channel {channel.name}")
    except Exception as e:
        logging.error(f"Failed to send level up message to {user.name} in channel {channel.name}: {e}")

# Endpoint to handle level-up notifications from external services
@app.route('/notify_level_up', methods=['POST'])
def notify_level_up():
    data = request.json
    user_id = int(data['user_id'])
    channel_id = int(data['channel_id'])
    logging.info(f"Received level up notification for user {user_id} in channel {channel_id}")

    # Find the channel by ID
    channel = bot.get_channel(channel_id)
    user = bot.get_user(user_id)

    if not channel:
        logging.error(f"Channel with ID {channel_id} not found")
        return "Channel not found", 404
    if not user:
        logging.error(f"User with ID {user_id} not found")
        return "User not found", 404

    user_address = fetch_user_address(user.name)
    if user_address:
        logging.info(f"Sending level up message to user {user.name} in channel {channel.name}")
        bot.loop.create_task(send_level_up_message(channel, user, get_user_xp(user_id), user_address))
        return "Notification sent", 200
    logging.error(f"User address for {user.name} not found")
    return "User address not found", 404

# Function to run the Flask app in a separate thread
def run_flask_app():
    logging.info("Starting Flask app")
    app.run(host='0.0.0.0', port=5002)

# Main function to start the bot and Flask app
if __name__ == '__main__':
    logging.info("Starting bot and Flask app")
    threading.Thread(target=run_flask_app).start()
    bot.run(bot_token)
