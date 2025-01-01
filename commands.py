from discord import app_commands
from discord.ext import commands
import discord
import datetime
import logging
import utils

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="timer")
    async def timer(self, interaction: discord.Interaction):
        """Shows remaining time for your active bombs"""
        user_id = str(interaction.user.id)
        if user_id not in self.bot.user_data:
            await interaction.response.send_message("You don't have any active TimeBombs.", ephemeral=True)
            return

        data = self.bot.user_data[user_id]
        embed = discord.Embed(title="Your TimeBomb Status", color=discord.Color.blue())

        if "first_bomb_end" in data:
            end_time = datetime.datetime.fromisoformat(data["first_bomb_end"])
            remaining = end_time - datetime.datetime.utcnow()
            if remaining.total_seconds() > 0:
                embed.add_field(
                    name="First TimeBomb",
                    value=f"Time remaining: {remaining.days}d {remaining.seconds//3600}h {(remaining.seconds//60)%60}m"
                )

        if data.get("second_bomb_active", False):
            end_time = datetime.datetime.fromisoformat(data["second_bomb_end"])
            remaining = end_time - datetime.datetime.utcnow()
            if remaining.total_seconds() > 0:
                embed.add_field(
                    name="Second TimeBomb",
                    value=f"Time remaining: {remaining.days}d {remaining.seconds//3600}h {(remaining.seconds//60)%60}m"
                )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="alltimer")
    @app_commands.default_permissions(administrator=True)
    async def alltimer(self, interaction: discord.Interaction):
        """Shows all active timers"""
        current_time = datetime.datetime.utcnow()
        all_users = list(self.bot.user_data.items())
        
        if not all_users:
            await interaction.response.send_message("No active timers.", ephemeral=True)
            return
            
        # Split into chunks of 25 users
        chunk_size = 25
        chunks = [all_users[i:i + chunk_size] for i in range(0, len(all_users), chunk_size)]
        
        for i, chunk in enumerate(chunks):
            embed = discord.Embed(
                title=f"All Active TimeBombs (Page {i+1}/{len(chunks)})", 
                color=discord.Color.blue()
            )
            
            for user_id, data in chunk:
                user = interaction.guild.get_member(int(user_id))
                if not user:
                    continue

                status = []
                if "first_bomb_end" in data:
                    end_time = datetime.datetime.fromisoformat(data["first_bomb_end"])
                    remaining = end_time - current_time
                    if remaining.total_seconds() > 0:
                        status.append(f"First: {remaining.days}d {remaining.seconds//3600}h")

                if data.get("second_bomb_active", False):
                    end_time = datetime.datetime.fromisoformat(data["second_bomb_end"])
                    remaining = end_time - current_time
                    if remaining.total_seconds() > 0:
                        status.append(f"Second: {remaining.days}d {remaining.seconds//3600}h")

                if status:
                    embed.add_field(
                        name=user.display_name, 
                        value=" | ".join(status), 
                        inline=False
                    )
            
            if i == 0:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="synctimer")
    @app_commands.default_permissions(administrator=True)
    async def synctimer(self, interaction: discord.Interaction):
        """Sync all timers and clean up invalid entries"""
        await interaction.response.defer(ephemeral=True)
        
        before_count = len(self.bot.user_data)
        current_time = datetime.datetime.utcnow()
        
        # Get relevant roles
        first_target = interaction.guild.get_role(self.bot.CONFIG["roles"]["first_success"])
        starter_role = interaction.guild.get_role(1198697252374462564)
        
        # Check all members - NO DMs
        for member in interaction.guild.members:
            if member.bot:
                continue
                
            user_id = str(member.id)
            member_roles = member.roles
            
            # Scenario 1: No roles or starter role - give first timer
            if not member_roles or starter_role in member_roles:
                end_time = current_time + datetime.timedelta(days=3)
                self.bot.user_data[user_id] = {
                    "join_date": current_time.isoformat(),
                    "first_bomb_end": end_time.isoformat(),
                    "warnings_sent": {},
                    "second_bomb_active": False
                }
                
            # Scenario 2: Has first target role - give second timer
            elif first_target in member_roles:
                # Initialize user data if it doesn't exist
                if user_id not in self.bot.user_data:
                    self.bot.user_data[user_id] = {
                        "join_date": current_time.isoformat(),
                        "warnings_sent": {},
                    }
                
                end_time = current_time + datetime.timedelta(days=14)
                self.bot.user_data[user_id].update({
                    "second_bomb_active": True,
                    "second_bomb_end": end_time.isoformat(),
                })
        
        self.bot.save_user_data()
        after_count = len(self.bot.user_data)
        
        await interaction.followup.send(
            f"Timer sync complete. Total users with timers: {after_count} (Change: {after_count - before_count})",
            ephemeral=True
        )

    @app_commands.command(name="removetimer")
    @app_commands.default_permissions(administrator=True)
    async def removetimer(self, interaction: discord.Interaction, user: discord.Member, bomb_number: int):
        """Remove a specific timer from a user"""
        if bomb_number not in [1, 2]:
            await interaction.response.send_message(
                "Bomb number must be 1 or 2",
                ephemeral=True
            )
            return

        user_id = str(user.id)
        if user_id not in self.bot.user_data:
            await interaction.response.send_message(
                f"No timer found for {user.display_name}",
                ephemeral=True
            )
            return

        if bomb_number == 1:
            if "first_bomb_end" in self.bot.user_data[user_id]:
                del self.bot.user_data[user_id]["first_bomb_end"]
                if "first_bomb_failed" in self.bot.user_data[user_id]:
                    del self.bot.user_data[user_id]["first_bomb_failed"]
        else:
            if self.bot.user_data[user_id].get("second_bomb_active", False):
                self.bot.user_data[user_id]["second_bomb_active"] = False
                if "second_bomb_end" in self.bot.user_data[user_id]:
                    del self.bot.user_data[user_id]["second_bomb_end"]
                if "second_bomb_failed" in self.bot.user_data[user_id]:
                    del self.bot.user_data[user_id]["second_bomb_failed"]

        self.bot.save_user_data()
        
        await interaction.response.send_message(
            f"Removed bomb {bomb_number} from {user.display_name}",
            ephemeral=True
        )

    @app_commands.command(name="resetserver")
    @app_commands.default_permissions(administrator=True)
    async def resetserver(self, interaction: discord.Interaction):
        """Reset all timers and start fresh for the entire server"""
        await interaction.response.defer(ephemeral=True)
        
        before_count = len(self.bot.user_data)
        current_time = datetime.datetime.utcnow()
        
        self.bot.user_data.clear()
        
        # Get relevant roles
        first_target = interaction.guild.get_role(self.bot.CONFIG["roles"]["first_success"])
        starter_role = interaction.guild.get_role(1198697252374462564)
        
        # Process all members - NO DMs
        for member in interaction.guild.members:
            if member.bot:
                continue
                
            user_id = str(member.id)
            member_roles = member.roles
            
            if not member_roles or starter_role in member_roles:
                end_time = current_time + datetime.timedelta(days=3)
                self.bot.user_data[user_id] = {
                    "join_date": current_time.isoformat(),
                    "first_bomb_end": end_time.isoformat(),
                    "warnings_sent": {},
                    "second_bomb_active": False
                }
                
            elif first_target in member_roles:
                end_time = current_time + datetime.timedelta(days=14)
                self.bot.user_data[user_id] = {
                    "join_date": current_time.isoformat(),
                    "second_bomb_active": True,
                    "second_bomb_end": end_time.isoformat(),
                    "warnings_sent": {}
                }
        
        self.bot.save_user_data()
        after_count = len(self.bot.user_data)
        
        await interaction.followup.send(
            f"Server reset complete! All timers have been reset.\n"
            f"Total users with new timers: {after_count}\n"
            f"Previous users with timers: {before_count}",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(AdminCommands(bot)) 