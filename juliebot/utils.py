import discord
import datetime
from typing import Optional
import logging

async def send_warning_message(user: discord.Member, time_left: str, phase: int) -> None:
    """Send a warning message to a user with exact specified format"""
    embed = discord.Embed(
        title="⚠️ TimeBomb Warning",
        description=f"You have {time_left} remaining!",
        color=discord.Color.yellow()
    )
    
    try:
        await user.send(embed=embed)
        logging.info(f"Warning sent to {user.id} for phase {phase} - {time_left} remaining")
    except discord.Forbidden:
        logging.warning(f"Could not send warning to {user.id}")

async def handle_bomb_failure(guild: discord.Guild, user_id: int, phase: int) -> None:
    """Handle when a user fails a TimeBomb"""
    member = guild.get_member(user_id)
    if not member:
        return
        
    role_id = CONFIG["roles"]["first_jail"] if phase == 1 else CONFIG["roles"]["second_jail"]
    jail_role = guild.get_role(role_id)
    
    if not jail_role:
        return
        
    try:
        await member.add_roles(jail_role)
        
        embed = discord.Embed(
            title="⚠️ Challenge Failed",
            description=(
                "You've been placed in jail for not completing the requirements in time. "
                "Contact an admin to discuss your next steps."
            ),
            color=discord.Color.red()
        )
        
        await member.send(embed=embed)
    except discord.Forbidden:
        pass

def format_time_remaining(end_time: datetime.datetime) -> Optional[str]:
    """Format the remaining time in a human-readable format"""
    now = datetime.datetime.utcnow()
    if end_time < now:
        return None
        
    remaining = end_time - now
    days = remaining.days
    hours = remaining.seconds // 3600
    minutes = (remaining.seconds % 3600) // 60
    
    if days > 0:
        return f"{days}d {hours}h"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m" 

async def check_and_send_warnings(bot, user_id: str, data: dict) -> None:
    """Check and send time-based warnings"""
    current_time = datetime.datetime.utcnow()
    warnings_sent = data.get("warnings_sent", {})
    guild = bot.get_guild(bot.CONFIG["guild_id"])
    member = guild.get_member(int(user_id))
    
    if not member:
        return

    # First TimeBomb warnings (3-day bomb)
    if "first_bomb_end" in data and not data.get("first_bomb_failed", False):
        end_time = datetime.datetime.fromisoformat(data["first_bomb_end"])
        remaining = end_time - current_time
        hours_left = remaining.total_seconds() / 3600

        # 24 hour warning
        if 23 <= hours_left <= 25 and "first_24h" not in warnings_sent:
            embed = discord.Embed(
                title="⚠️ First Challenge - 24 Hours Remaining",
                description=(
                    "You have 24 hours left to complete your first challenge!\n\n"
                    "Requirements:\n"
                    "1️⃣ Create an Instagram account following our course rules\n"
                    "2️⃣ Verify your account by opening a ticket\n"
                    "3️⃣ Introduce yourself in general chat\n\n"
                    "⚠️ If you don't complete these in time, you'll be moved to jail!"
                ),
                color=discord.Color.yellow()
            )
            try:
                await member.send(embed=embed)
                warnings_sent["first_24h"] = current_time.isoformat()
                logging.info(f"24h warning sent to {user_id} for phase 1")
            except discord.Forbidden:
                logging.warning(f"Could not send 24h warning to {user_id}")

        # 12 hour warning
        elif 11 <= hours_left <= 13 and "first_12h" not in warnings_sent:
            embed = discord.Embed(
                title="⚠️ First Challenge - 12 Hours Remaining",
                description=(
                    "⚠️ URGENT: Only 12 hours left to complete your first challenge!\n\n"
                    "Requirements:\n"
                    "1️⃣ Create an Instagram account following our course rules\n"
                    "2️⃣ Verify your account by opening a ticket\n"
                    "3️⃣ Introduce yourself in general chat\n\n"
                    "⚠️ Time is running out! Contact an admin if you need help!"
                ),
                color=discord.Color.orange()
            )
            try:
                await member.send(embed=embed)
                warnings_sent["first_12h"] = current_time.isoformat()
                logging.info(f"12h warning sent to {user_id} for phase 1")
            except discord.Forbidden:
                logging.warning(f"Could not send 12h warning to {user_id}")

    # Second TimeBomb warnings (14-day bomb)
    if data.get("second_bomb_active", False) and not data.get("second_bomb_failed", False):
        end_time = datetime.datetime.fromisoformat(data["second_bomb_end"])
        remaining = end_time - current_time
        days_left = remaining.days

        # 7 day warning
        if 6.5 <= days_left <= 7.5 and "second_7d" not in warnings_sent:
            embed = discord.Embed(
                title="⚠️ Second Challenge - 7 Days Remaining",
                description=(
                    "You have 7 days left to complete your second challenge!\n\n"
                    "Requirements:\n"
                    "1️⃣ Get three posts approved\n"
                    "2️⃣ Send at least 10 messages in general chat\n"
                    "3️⃣ Spend at least 30 minutes in voice calls\n\n"
                    "💡 Use /timer to check your progress!"
                ),
                color=discord.Color.yellow()
            )
            try:
                await member.send(embed=embed)
                warnings_sent["second_7d"] = current_time.isoformat()
                logging.info(f"7d warning sent to {user_id} for phase 2")
            except discord.Forbidden:
                logging.warning(f"Could not send 7d warning to {user_id}")

        # 3 day warning
        elif 2.5 <= days_left <= 3.5 and "second_3d" not in warnings_sent:
            embed = discord.Embed(
                title="⚠️ Second Challenge - 3 Days Remaining",
                description=(
                    "⚠️ Only 3 days left to complete your second challenge!\n\n"
                    "Requirements:\n"
                    "1️⃣ Get three posts approved\n"
                    "2️⃣ Send at least 10 messages in general chat\n"
                    "3️⃣ Spend at least 30 minutes in voice calls\n\n"
                    "⚠️ Make sure to complete everything in time!"
                ),
                color=discord.Color.orange()
            )
            try:
                await member.send(embed=embed)
                warnings_sent["second_3d"] = current_time.isoformat()
                logging.info(f"3d warning sent to {user_id} for phase 2")
            except discord.Forbidden:
                logging.warning(f"Could not send 3d warning to {user_id}")

        # 24 hour warning
        elif 23 <= (remaining.total_seconds() / 3600) <= 25 and "second_24h" not in warnings_sent:
            embed = discord.Embed(
                title="⚠️ Second Challenge - 24 Hours Remaining",
                description=(
                    "⚠️ URGENT: Only 24 hours left to complete your second challenge!\n\n"
                    "Requirements:\n"
                    "1️⃣ Get three posts approved\n"
                    "2️⃣ Send at least 10 messages in general chat\n"
                    "3️⃣ Spend at least 30 minutes in voice calls\n\n"
                    "⚠️ Contact an admin immediately if you need help!"
                ),
                color=discord.Color.red()
            )
            try:
                await member.send(embed=embed)
                warnings_sent["second_24h"] = current_time.isoformat()
                logging.info(f"24h warning sent to {user_id} for phase 2")
            except discord.Forbidden:
                logging.warning(f"Could not send 24h warning to {user_id}")

    data["warnings_sent"] = warnings_sent
    bot.save_user_data()

async def complete_first_phase(bot, member: discord.Member) -> None:
    """Handle completion of first phase"""
    user_id = str(member.id)
    if user_id not in bot.user_data:
        return

    # Add success role
    success_role = member.guild.get_role(bot.CONFIG["roles"]["first_success"])
    if success_role:
        await member.add_roles(success_role)
        await send_second_phase_message(member)

    # Start second phase
    end_time = datetime.datetime.utcnow() + datetime.timedelta(days=14)
    bot.user_data[user_id].update({
        "second_bomb_active": True,
        "second_bomb_end": end_time.isoformat()
    })
    bot.save_user_data()

    # Send success message and second phase instructions
    embed = discord.Embed(
        title="🚀 Second Challenge Activated!",
        description=(
            "You now have 14 days to complete:\n\n"
            "1️⃣ Get three posts approved\n"
            "2️⃣ Send at least 10 messages in general chat\n"
            "3️⃣ Spend at least 30 minutes in voice calls\n\n"
            "Use /timer to check your progress!"
        ),
        color=discord.Color.green()
    )
    
    try:
        await member.send(embed=embed)
    except discord.Forbidden:
        pass

    # Log the event
    log_channel = bot.get_channel(bot.CONFIG["log_channel"])
    if log_channel:
        log_embed = discord.Embed(
            title="First Phase Completed",
            description=f"{member.mention} has completed the first TimeBomb phase",
            color=discord.Color.green()
        )
        await log_channel.send(embed=log_embed)

async def complete_second_phase(bot, member: discord.Member) -> None:
    """Handle completion of second phase"""
    user_id = str(member.id)
    if user_id not in bot.user_data:
        return

    # Add final success role
    success_role = member.guild.get_role(bot.CONFIG["roles"]["second_success"])
    if success_role:
        await member.add_roles(success_role)

    # Send completion message
    embed = discord.Embed(
        title="🎉 Congratulations!",
        description="You've successfully completed all challenges! Welcome to the full community!",
        color=discord.Color.gold()
    )
    
    try:
        await member.send(embed=embed)
    except discord.Forbidden:
        pass

    # Log the event
    log_channel = bot.get_channel(bot.CONFIG["log_channel"])
    if log_channel:
        log_embed = discord.Embed(
            title="All Phases Completed",
            description=f"{member.mention} has completed all TimeBomb phases",
            color=discord.Color.gold()
        )
        await log_channel.send(embed=log_embed)

    # Clean up user data
    del bot.user_data[user_id]
    bot.save_user_data() 

async def send_jail_message(member: discord.Member, phase: int) -> None:
    """Send jail notification to user"""
    message = (
        "⚠️ First Challenge Failed\n"
        "You've been placed in jail for not completing the requirements in time. "
        "Contact an admin to discuss your next steps."
    ) if phase == 1 else (
        "⚠️ Second Challenge Failed\n"
        "You've been placed in jail for not completing the advanced requirements in time. "
        "Contact an admin to discuss your next steps."
    )
    
    embed = discord.Embed(
        title="TimeBomb Failed",
        description=message,
        color=discord.Color.red()
    )
    
    try:
        await member.send(embed=embed)
    except discord.Forbidden:
        pass

async def send_release_message(member: discord.Member) -> None:
    """Send jail release message to user"""
    embed = discord.Embed(
        title="🔓 Released from Jail",
        description="You've been given another chance. Make sure to complete the requirements this time!",
        color=discord.Color.green()
    )
    
    try:
        await member.send(embed=embed)
    except discord.Forbidden:
        pass

async def handle_jail_release(bot, member: discord.Member, phase: int) -> None:
    """Handle releasing a user from jail"""
    # Remove jail role
    jail_role = member.guild.get_role(
        bot.CONFIG["roles"]["first_jail"] if phase == 1 else bot.CONFIG["roles"]["second_jail"]
    )
    if jail_role and jail_role in member.roles:
        await member.remove_roles(jail_role)
    
    # Reset timer
    user_id = str(member.id)
    current_time = datetime.datetime.utcnow()
    
    if phase == 1:
        end_time = current_time + datetime.timedelta(days=3)
        bot.user_data[user_id] = {
            "join_date": current_time.isoformat(),
            "first_bomb_end": end_time.isoformat(),
            "warnings_sent": {},
            "second_bomb_active": False
        }
    else:
        end_time = current_time + datetime.timedelta(days=14)
        bot.user_data[user_id].update({
            "second_bomb_end": end_time.isoformat(),
            "second_bomb_failed": False
        })
    
    bot.save_user_data()
    
    # Send release message
    await send_release_message(member)
    
    # Log the release
    log_channel = bot.get_channel(bot.CONFIG["log_channel"])
    if log_channel:
        log_embed = discord.Embed(
            title="User Released from Jail",
            description=f"{member.mention} has been released from phase {phase} jail",
            color=discord.Color.green()
        )
        await log_channel.send(embed=log_embed) 

async def send_second_phase_message(user: discord.Member) -> None:
    """Send second phase activation message with exact specified format"""
    embed = discord.Embed(
        title="🚀 Second Challenge Activated!",
        description=(
            "You now have 14 days to complete:\n\n"
            "1️⃣ Get three posts approved\n"
            "2️⃣ Send at least 10 messages in general chat\n"
            "3️⃣ Spend at least 30 minutes in voice calls\n\n"
            "Use /timer to check your progress!"
        ),
        color=discord.Color.blue()
    )
    
    try:
        await user.send(embed=embed)
        logging.info(f"Second phase message sent to {user.id}")
    except discord.Forbidden:
        logging.warning(f"Could not send second phase message to {user.id}")

async def send_completion_message(user: discord.Member) -> None:
    """Send final completion message with exact specified format"""
    embed = discord.Embed(
        title="🎉 Congratulations!",
        description="You've successfully completed all challenges! Welcome to the full community!",
        color=discord.Color.gold()
    )
    
    try:
        await user.send(embed=embed)
        logging.info(f"Completion message sent to {user.id}")
    except discord.Forbidden:
        logging.warning(f"Could not send completion message to {user.id}") 

async def send_welcome_message(member: discord.Member, start_time: datetime.datetime) -> None:
    """Send welcome message to new member"""
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
    embed.set_footer(text=f"Time started: {start_time.strftime('%Y-%m-%d %H:%M')} UTC")
    
    try:
        await member.send(embed=embed)
        logging.info(f"Welcome message sent to {member.id}")
    except discord.Forbidden:
        logging.warning(f"Could not send welcome message to {member.id}")

async def handle_role_change(member: discord.Member, role: discord.Role) -> None:
    """Handle role changes and send appropriate messages"""
    logging.info(f"Role change detected for {member.name} (ID: {member.id}): {role.name} (ID: {role.id})")
    
    # Get bot instance (fixed)
    bot = member.guild.me._state._get_client()
    
    # Log channel for monitoring
    log_channel = member.guild.get_channel(bot.CONFIG["log_channel"])
    user_id = str(member.id)
    
    # First Success Role (Target Role)
    if role.id == bot.CONFIG["roles"]["first_success"]:
        logging.info(f"Target role detected for {member.name}, updating timers and sending message")
        
        # Update timers
        current_time = datetime.datetime.utcnow()
        end_time = current_time + datetime.timedelta(days=14)
        
        if user_id in bot.user_data:
            # Remove first timer and start second timer
            if "first_bomb_end" in bot.user_data[user_id]:
                del bot.user_data[user_id]["first_bomb_end"]
            if "first_bomb_failed" in bot.user_data[user_id]:
                del bot.user_data[user_id]["first_bomb_failed"]
                
            bot.user_data[user_id].update({
                "second_bomb_active": True,
                "second_bomb_end": end_time.isoformat(),
                "warnings_sent": bot.user_data[user_id].get("warnings_sent", {})
            })
            bot.save_user_data()
            logging.info(f"Updated timers for {member.name}: Started second phase")
        
        # Send combined success/second phase message
        embed = discord.Embed(
            title="🎯 First Challenge Complete & Second Challenge Started!",
            description=(
                "🎉 Congratulations! You've completed the first challenge!\n\n"
                "🚀 Your second challenge has now begun:\n\n"
                "You have 14 days to complete:\n"
                "1️⃣ Get three posts approved\n"
                "2️⃣ Send at least 10 messages in general chat\n"
                "3️⃣ Spend at least 30 minutes in voice calls\n\n"
                "💡 Use /timer to check your remaining time!\n\n"
                "⚠️ Important: Failing to complete these requirements within 14 days "
                "will result in being moved to jail until requirements are met."
            ),
            color=discord.Color.green()
        )
        try:
            await member.send(embed=embed)
            if log_channel:
                await log_channel.send(f"✅ Successfully sent target role message to {member.mention}")
        except discord.Forbidden:
            if log_channel:
                await log_channel.send(f"❌ Could not send target role message to {member.mention} - DMs closed")
        except Exception as e:
            if log_channel:
                await log_channel.send(f"❌ Error sending target role message to {member.mention}: {str(e)}")
    
    # Second Success Role (Final Role)
    elif role.id == bot.CONFIG["roles"]["second_success"]:
        logging.info(f"Final success role detected for {member.name}, cleaning up timers")
        
        # Remove all timers and send congratulations
        if user_id in bot.user_data:
            del bot.user_data[user_id]  # Remove all timer data
            bot.save_user_data()
            logging.info(f"Removed all timers for {member.name}")
        
        # Send completion message
        embed = discord.Embed(
            title="🎉 Congratulations - All Challenges Complete!",
            description=(
                "You've successfully completed all challenges!\n"
                "Welcome to the full community! 🌟\n\n"
                "You are now a full member with access to all features."
            ),
            color=discord.Color.gold()
        )
        try:
            await member.send(embed=embed)
            if log_channel:
                await log_channel.send(f"✅ Successfully sent completion message to {member.mention}")
        except discord.Forbidden:
            if log_channel:
                await log_channel.send(f"❌ Could not send completion message to {member.mention} - DMs closed")
        except Exception as e:
            if log_channel:
                await log_channel.send(f"❌ Error sending completion message to {member.mention}: {str(e)}")
    
    # Jail Messages
    elif role.id in [bot.CONFIG["roles"]["first_jail"], bot.CONFIG["roles"]["second_jail"]]:
        is_first_jail = role.id == bot.CONFIG["roles"]["first_jail"]
        embed = discord.Embed(
            title=f"⚠️ {'First' if is_first_jail else 'Second'} Challenge Failed",
            description=(
                f"You've been placed in jail for not completing the {('first' if is_first_jail else 'second')} "
                "phase requirements in time.\n\n"
                "To get out of jail:\n"
                "1️⃣ Contact an admin\n"
                "2️⃣ Explain why you couldn't complete the tasks\n"
                "3️⃣ Show that you're ready to complete them\n\n"
                "An admin will review your case and may give you another chance."
            ),
            color=discord.Color.red()
        )
        try:
            await member.send(embed=embed)
            if log_channel:
                await log_channel.send(f"✅ Successfully sent jail message to {member.mention}")
        except discord.Forbidden:
            if log_channel:
                await log_channel.send(f"❌ Could not send jail message to {member.mention} - DMs closed")
        except Exception as e:
            if log_channel:
                await log_channel.send(f"❌ Error sending jail message to {member.mention}: {str(e)}") 