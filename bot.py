import discord
from discord.ext import commands, tasks
import json
import datetime
import logging
import os
from dotenv import load_dotenv
import utils  # Make sure to import utils

# Load token
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Setup logging
logging.basicConfig(level=logging.INFO)

class TimeBombBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.guilds = True
        
        super().__init__(
            command_prefix='/',
            intents=intents
        )
        
        # Initialize data storage
        self.user_data = {}
        self.CONFIG = {}
    
    def load_config(self):
        try:
            with open('config.json', 'r') as f:
                self.CONFIG = json.load(f)
            print("Configuration loaded successfully")
        except Exception as e:
            print(f"Error loading config: {e}")
            raise SystemExit("Could not load configuration!")

    def load_user_data(self):
        """Load user data from single persistent file"""
        data_file = "/data/persistent_user_data.json"
        
        try:
            # Try loading from persistent storage
            with open(data_file, 'r') as f:
                self.user_data = json.load(f)
            print(f"User data loaded successfully from {data_file}")
        except FileNotFoundError:
            print("No existing data found, starting fresh")
            self.user_data = {}
        except Exception as e:
            print(f"Error loading data: {e}")
            self.user_data = {}

    def save_user_data(self):
        """Save user data to single persistent file"""
        # Ensure data directory exists
        os.makedirs("/data", exist_ok=True)
        
        # Use a single, consistent filename
        data_file = "/data/persistent_user_data.json"
        
        try:
            # Save to persistent storage
            with open(data_file, 'w') as f:
                json.dump(self.user_data, f, indent=4)
            print(f"User data saved successfully to {data_file}")
        except Exception as e:
            print(f"Error saving to persistent storage: {e}")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Handle new member joins"""
        if member.bot:
            return

        # Set up initial timer
        current_time = datetime.datetime.utcnow()
        end_time = current_time + datetime.timedelta(days=3)
        
        # Store user data
        self.user_data[str(member.id)] = {
            "join_date": current_time.isoformat(),
            "first_bomb_end": end_time.isoformat(),
            "warnings_sent": {},
            "second_bomb_active": False
        }
        self.save_user_data()

        # Send welcome message
        embed = discord.Embed(
            title="🎯 Welcome to Your First TimeBomb!",
            description=(
                "Welcome to our community! You're now on your first TimeBomb challenge.\n\n"
                "⏰ You have 3 days to complete these requirements:\n\n"
                "1️⃣ Create an Instagram account following our course rules\n"
                "2️⃣ Verify your account by opening a ticket\n"
                "3️⃣ Introduce yourself in general chat\n\n"
                "💡 Use /timer to check your remaining time!\n\n"
                "⚠️ Important: Failing to complete these requirements within 3 days "
                "will result in being moved to jail until requirements are met."
            ),
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Time started: {current_time.strftime('%Y-%m-%d %H:%M')} UTC")

        try:
            await member.send(embed=embed)
            logging.info(f"Welcome message sent to {member.id}")
        except discord.Forbidden:
            logging.warning(f"Could not send welcome message to {member.id}")

        # Log the join
        log_channel = self.get_channel(self.CONFIG["log_channel"])
        if log_channel:
            await log_channel.send(f"New member {member.mention} started their TimeBomb journey!")

    @tasks.loop(hours=8)
    async def check_timers(self):
        """Check timers every 8 hours"""
        try:
            current_time = datetime.datetime.utcnow()
            guild = self.get_guild(self.CONFIG["guild_id"])
            if not guild:
                return

            for user_id, data in self.user_data.items():
                # Check warnings
                await utils.check_and_send_warnings(self, user_id, data)

                # Check first phase
                if "first_bomb_end" in data and not data.get("first_bomb_failed", False):
                    end_time = datetime.datetime.fromisoformat(data["first_bomb_end"])
                    if current_time > end_time:
                        await utils.handle_bomb_failure(guild, int(user_id), 1)
                        data["first_bomb_failed"] = True

                # Check second phase
                if data.get("second_bomb_active", False) and not data.get("second_bomb_failed", False):
                    end_time = datetime.datetime.fromisoformat(data["second_bomb_end"])
                    if current_time > end_time:
                        await utils.handle_bomb_failure(guild, int(user_id), 2)
                        data["second_bomb_failed"] = True

            self.save_user_data()

        except Exception as e:
            logging.error(f"Error in timer check: {e}")

    async def setup_hook(self):
        print("Bot is setting up...")
        self.load_config()
        self.load_user_data()
        
        # Start timer check loop
        self.check_timers.start()
        
        # Load extensions
        await self.load_extension('commands')
        print("Commands loaded")
        
        # Sync commands with Discord
        print("Syncing commands...")
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} commands")
        except Exception as e:
            print(f"Error syncing commands: {e}")
        
        print("Setup complete!")

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Handle role changes"""
        if before.roles != after.roles:
            # Find which role was added
            added_roles = set(after.roles) - set(before.roles)
            for role in added_roles:
                if role.id in [
                    self.CONFIG["roles"]["first_success"],
                    self.CONFIG["roles"]["second_success"],
                    self.CONFIG["roles"]["first_jail"],
                    self.CONFIG["roles"]["second_jail"]
                ]:
                    await utils.handle_role_change(after, role)

bot = TimeBombBot()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print('Syncing commands...')
    try:
        await bot.tree.sync()
        print('Commands synced!')
    except Exception as e:
        print(f"Error syncing commands: {e}")
    print('Bot is ready!')

if __name__ == "__main__":
    bot.run(TOKEN) 