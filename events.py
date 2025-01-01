import discord
from discord.ext import commands
import datetime
import logging

class EventHandlers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Handle new member joins"""
        if member.guild.id != self.bot.CONFIG["guild_id"]:
            return

        # Set up first bomb timer
        end_time = datetime.datetime.utcnow() + datetime.timedelta(days=3)
        
        # Store user data
        self.bot.user_data[str(member.id)] = {
            "join_date": datetime.datetime.utcnow().isoformat(),
            "first_bomb_end": end_time.isoformat(),
            "warnings_sent": {},
            "second_bomb_active": False
        }
        self.bot.save_user_data()

        # Send welcome message
        welcome_embed = discord.Embed(
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
        welcome_embed.set_footer(text=f"Time started: {datetime.datetime.utcnow()} UTC")

        try:
            await member.send(embed=welcome_embed)
            
            # Log the event
            log_channel = self.bot.get_channel(self.bot.CONFIG["log_channel"])
            if log_channel:
                log_embed = discord.Embed(
                    title="TimeBomb Assigned",
                    description=f"First TimeBomb assigned to {member.mention}",
                    color=discord.Color.blue()
                )
                log_embed.add_field(name="End Time", value=end_time.strftime("%Y-%m-%d %H:%M UTC"))
                await log_channel.send(embed=log_embed)
                
            logging.info(f"First TimeBomb assigned to user {member.id}")
            
        except discord.Forbidden:
            logging.warning(f"Could not send welcome message to user {member.id}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Handle member leaves"""
        if member.guild.id != self.bot.CONFIG["guild_id"]:
            return

        if str(member.id) in self.bot.user_data:
            # Log the event
            log_channel = self.bot.get_channel(self.bot.CONFIG["log_channel"])
            if log_channel:
                log_embed = discord.Embed(
                    title="Member Left During TimeBomb",
                    description=f"{member.mention} left the server during their TimeBomb period",
                    color=discord.Color.red()
                )
                await log_channel.send(embed=log_embed)
                
            logging.info(f"User {member.id} left during TimeBomb period")
            
            # Clean up user data
            del self.bot.user_data[str(member.id)]
            self.bot.save_user_data()

async def setup(bot):
    await bot.add_cog(EventHandlers(bot)) 