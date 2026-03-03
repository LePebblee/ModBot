import discord
from discord import app_commands
from datetime import datetime
from typing import Optional
from log_helper import add_log
import json
import os

async def perform_accept_action(bot, guild, user_id: str, action: str, reason: str):
    uid = int(user_id)
    if action == 'unban':
        user = await bot.fetch_user(uid)
        await guild.unban(user, reason=reason)
        log_type = "unban"
    elif action == 'unkick':
        # Overturn kick (record-only)
        log_type = "unkick"
    else:
        raise ValueError(f"Unknown action: {action}")

    add_log({
        "type": log_type,
        "user_id": str(uid),
        "reason": reason,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    })

@app_commands.command(name="accept", description="Accept an appeal and undo an action on the main server")
@app_commands.describe(user_id="The ID of the user to act upon", reason="Optional reason for the action")
async def accept_command(interaction: discord.Interaction, user_id: str, reason: Optional[str] = None):
    if not interaction.user.guild_permissions.manage_guild and not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("You lack permissions to perform moderation actions.", ephemeral=True)
        return

    class ActionSelect(discord.ui.Select):
        def __init__(self, target_user_id: str, target_reason: Optional[str], bot):
            options = [
                discord.SelectOption(label="Unban", value="unban", description="Remove a ban for the user"),
                discord.SelectOption(label="Unkick", value="unkick", description="Record that a kick was overturned"),
            ]
            super().__init__(placeholder="Select action to perform...", min_values=1, max_values=1, options=options)
            self.target_user_id = target_user_id
            self.target_reason = target_reason or "Appeal accepted"
            self.bot = bot

        async def callback(self, select_interaction: discord.Interaction):
            try:
                cfg_path = os.path.join(os.getcwd(), 'config.json')
                with open(cfg_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                main_server_id = cfg.get('main_server')
                if not main_server_id:
                    await select_interaction.response.send_message("Main server not configured.", ephemeral=True)
                    return

                guild = self.bot.get_guild(int(main_server_id))
                if not guild:
                    await select_interaction.response.send_message("Bot is not in the main server.", ephemeral=True)
                    return

                action = self.values[0]
                await perform_accept_action(self.bot, guild, self.target_user_id, action, self.target_reason)

                await select_interaction.response.send_message(f"Successfully performed {action} on <@{self.target_user_id}>.", ephemeral=True)

            except Exception as e:
                await select_interaction.response.send_message(f"Error: {e}", ephemeral=True)

    class ActionView(discord.ui.View):
        def __init__(self, target_user_id: str, target_reason: Optional[str], bot):
            super().__init__(timeout=300)
            self.add_item(ActionSelect(target_user_id, target_reason, bot))

    view = ActionView(user_id, reason, interaction.client)
    await interaction.response.send_message(f"Choose action to perform on <@{user_id}>:", view=view, ephemeral=True)

async def notify_user_of_appeal(bot, user_id: str, invite_link: str):
    try:
        user = await bot.fetch_user(int(user_id))
        embed = discord.Embed(
            title="Appeal Case Opened",
            description=f"Your appeal case has been opened. To proceed, please join our dedicated appeal server using the link below.\n\n**Invite Link:** {invite_link}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Instructions", value="Once you join the server, you will be automatically added to your private appeal thread. Please wait for a moderator to contact you there.")
        await user.send(embed=embed)
    except Exception as e:
        import logging
        logging.error(f"Failed to send DM to user {user_id}: {e}")
