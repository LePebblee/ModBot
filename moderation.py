import discord
from discord import app_commands
from datetime import datetime
from typing import Optional
from log_helper import add_log

INVITE_LINK = "YOUR_APPEAL_SERVER_INVITE_LINK_HERE"

class Moderation(app_commands.Group):
    def __init__(self, bot):
        super().__init__(name="mod", description="Moderation commands")
        self.bot = bot

    @app_commands.command(name="ban", description="Ban a user and log the action")
    @app_commands.describe(user_id="The ID of the user to ban", reason="Reason for the ban")
    async def ban(self, interaction: discord.Interaction, user_id: str, reason: Optional[str] = "No reason given"):
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("You lack permissions to ban members.", ephemeral=True)
            return

        try:
            user_obj = await self.bot.fetch_user(int(user_id))
            await interaction.guild.ban(user_obj, reason=reason)
            
            add_log({
                "type": "ban",
                "user_id": user_id,
                "reason": reason,
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            await interaction.response.send_message(f"Successfully banned <@{user_id}>.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error: {e}", ephemeral=True)

    @app_commands.command(name="kick", description="Kick a user and log the action")
    @app_commands.describe(user_id="The ID of the user to kick", reason="Reason for the kick")
    async def kick(self, interaction: discord.Interaction, user_id: str, reason: Optional[str] = "No reason given"):
        if not interaction.user.guild_permissions.kick_members:
            await interaction.response.send_message("You lack permissions to kick members.", ephemeral=True)
            return

        try:
            guild = interaction.guild
            member = await guild.fetch_member(int(user_id))
            await member.kick(reason=reason)

            add_log({
                "type": "kick",
                "user_id": user_id,
                "reason": reason,
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            })

            await interaction.response.send_message(f"Successfully kicked <@{user_id}>.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error: {e}", ephemeral=True)

async def notify_user_of_appeal(bot, user_id: str):
    try:
        user = await bot.fetch_user(int(user_id))
        embed = discord.Embed(
            title="Appeal Case Opened",
            description=f"Your appeal case has been opened. To proceed, please join our dedicated appeal server using the link below.\n\n**Invite Link:** {INVITE_LINK}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Instructions", value="Once you join the server, you will be automatically added to your private appeal thread. Please wait for a moderator to contact you there.")
        await user.send(embed=embed)
    except Exception:
        pass