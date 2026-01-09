import discord
from discord import app_commands
from datetime import datetime
from typing import Optional
from log_helper import add_log
import json
import os
from datetime import datetime

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

    @app_commands.command(name="accept", description="Accept an appeal and undo an action on the main server")
    @app_commands.describe(user_id="The ID of the user to act upon", reason="Optional reason for the action")
    async def accept(self, interaction: discord.Interaction, user_id: str, reason: Optional[str] = None):
        # Present a dropdown to choose which action to undo on the configured main server
        if not interaction.user.guild_permissions.manage_guild and not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("You lack permissions to perform moderation actions.", ephemeral=True)
            return

        class ActionSelect(discord.ui.Select):
            def __init__(self, target_user_id: str, target_reason: Optional[str], bot):
                options = [
                    discord.SelectOption(label="Unban", value="unban", description="Remove a ban for the user"),
                    discord.SelectOption(label="Untimeout", value="untimeout", description="Remove timeout from the user"),
                    discord.SelectOption(label="Unkick", value="unkick", description="Record that a kick was overturned"),
                ]
                super().__init__(placeholder="Select action to perform...", min_values=1, max_values=1, options=options)
                self.target_user_id = target_user_id
                self.target_reason = target_reason or "Appeal accepted"
                self.bot = bot

            async def callback(self, select_interaction: discord.Interaction):
                # Load config to find main_server
                try:
                    cfg_path = os.path.join(os.getcwd(), 'config.json')
                    if not os.path.exists(cfg_path):
                        await select_interaction.response.send_message("Config file not found.", ephemeral=True)
                        return
                    with open(cfg_path, 'r', encoding='utf-8') as f:
                        cfg = json.load(f)
                    main_server_id = cfg.get('main_server')
                    if not main_server_id:
                        await select_interaction.response.send_message("Main server not configured in config.json.", ephemeral=True)
                        return

                    guild = self.bot.get_guild(int(main_server_id))
                    if not guild:
                        await select_interaction.response.send_message(f"Bot is not a member of the main server ({main_server_id}).", ephemeral=True)
                        return

                    action = self.values[0]
                    uid = int(self.target_user_id)

                    if action == 'unban':
                        try:
                            user = await self.bot.fetch_user(uid)
                            await guild.unban(user, reason=self.target_reason)
                            add_log({
                                "type": "unban",
                                "user_id": str(uid),
                                "reason": self.target_reason,
                                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                            })
                            await select_interaction.response.send_message(f"Unbanned <@{uid}> in the main server.", ephemeral=True)
                        except discord.NotFound:
                            await select_interaction.response.send_message("User or ban not found.", ephemeral=True)
                        except discord.Forbidden:
                            await select_interaction.response.send_message("Bot lacks permission to unban in the main server.", ephemeral=True)
                        except Exception as e:
                            await select_interaction.response.send_message(f"Error unbanning: {e}", ephemeral=True)

                    elif action == 'untimeout':
                        try:
                            member = guild.get_member(uid)
                            if not member:
                                try:
                                    member = await guild.fetch_member(uid)
                                except Exception:
                                    member = None

                            if not member:
                                await select_interaction.response.send_message(f"Could not find member {uid} in the main server.", ephemeral=True)
                                return

                            await member.timeout(None, reason=self.target_reason)
                            add_log({
                                "type": "untimeout",
                                "user_id": str(uid),
                                "reason": self.target_reason,
                                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                            })
                            await select_interaction.response.send_message(f"Removed timeout from <@{uid}> in the main server.", ephemeral=True)
                        except discord.Forbidden:
                            await select_interaction.response.send_message("Bot lacks permission to remove timeout in the main server.", ephemeral=True)
                        except Exception as e:
                            await select_interaction.response.send_message(f"Error removing timeout: {e}", ephemeral=True)

                    elif action == 'unkick':
                        # Cannot directly "unkick" a user; mark the appeal as accepted for the record
                        add_log({
                            "type": "unkick",
                            "user_id": str(uid),
                            "reason": self.target_reason,
                            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        await select_interaction.response.send_message(f"Recorded overturn of kick for <@{uid}>. User may need to rejoin manually.", ephemeral=True)

                    else:
                        await select_interaction.response.send_message(f"Unknown action: {action}", ephemeral=True)

                except Exception as e:
                    await select_interaction.response.send_message(f"Error performing action: {e}", ephemeral=True)

        class ActionView(discord.ui.View):
            def __init__(self, target_user_id: str, target_reason: Optional[str], bot):
                super().__init__(timeout=300)
                self.add_item(ActionSelect(target_user_id, target_reason, bot))

        view = ActionView(user_id, reason, self.bot)
        await interaction.response.send_message(f"Choose action to perform on <@{user_id}> in the main server:", view=view, ephemeral=True)

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