import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta, timezone
from typing import Optional
from log_helper import add_log
import json
import os

class BanModal(discord.ui.Modal, title="Ban User"):
    user_id = discord.ui.TextInput(label="User ID", placeholder="User ID here", required=True)
    reason = discord.ui.TextInput(label="Reason", style=discord.TextStyle.paragraph, required=False)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id_val = self.user_id.value.strip()
            user = discord.Object(id=int(user_id_val))
            await interaction.guild.ban(user, reason=self.reason.value or "No reason given")
            add_log({
                "type": "ban",
                "user_id": user_id_val,
                "reason": self.reason.value or "No reason given",
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            })
            await interaction.response.send_message(f"Successfully banned user {user_id_val}.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Invalid User ID.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error: {e}", ephemeral=True)

class KickModal(discord.ui.Modal, title="Kick User"):
    user_id = discord.ui.TextInput(label="User ID", placeholder="User ID here", required=True)
    reason = discord.ui.TextInput(label="Reason", style=discord.TextStyle.paragraph, required=False)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id_val = self.user_id.value.strip()
            member = interaction.guild.get_member(int(user_id_val))
            if not member:
                try:
                    member = await interaction.guild.fetch_member(int(user_id_val))
                except:
                    member = None

            if member:
                await member.kick(reason=self.reason.value or "No reason given")
                add_log({
                    "type": "kick",
                    "user_id": user_id_val,
                    "reason": self.reason.value or "No reason given",
                    "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                })
                await interaction.response.send_message(f"Successfully kicked user {member.name}.", ephemeral=True)
            else:
                await interaction.response.send_message("Member not found in this server.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Invalid User ID.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error: {e}", ephemeral=True)

class TimeoutModal(discord.ui.Modal, title="Timeout User"):
    user_id = discord.ui.TextInput(label="User ID", placeholder="User ID here", required=True)
    minutes = discord.ui.TextInput(label="Duration (Minutes)", placeholder="60", required=True)
    reason = discord.ui.TextInput(label="Reason", style=discord.TextStyle.paragraph, required=False)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id_val = self.user_id.value.strip()
            member = interaction.guild.get_member(int(user_id_val))
            if not member:
                try:
                    member = await interaction.guild.fetch_member(int(user_id_val))
                except:
                    member = None

            if member:
                duration = timedelta(minutes=int(self.minutes.value))
                await member.timeout(duration, reason=self.reason.value or "No reason given")
                add_log({
                    "type": "timeout",
                    "user_id": user_id_val,
                    "reason": self.reason.value or f"Timed out for {self.minutes.value} minutes",
                    "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                })
                await interaction.response.send_message(f"Successfully timed out user {member.name} for {self.minutes.value}m.", ephemeral=True)
            else:
                await interaction.response.send_message("Member not found in this server.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Invalid User ID or Minutes.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error: {e}", ephemeral=True)

class AcceptModal(discord.ui.Modal, title='Accept Appeal'):
    user_id = discord.ui.TextInput(label='User ID', placeholder='User ID to act upon', required=True)
    reason = discord.ui.TextInput(label='Reason', style=discord.TextStyle.paragraph, required=False)

    def __init__(self, action_type: str, bot):
        super().__init__()
        self.action_type = action_type
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id_val = self.user_id.value.strip()
            uid = int(user_id_val)

            cfg_path = 'config.json'
            if os.path.exists(cfg_path):
                with open(cfg_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
            else:
                await interaction.response.send_message("Config file not found.", ephemeral=True)
                return

            main_server_id = cfg.get('main_server')
            if not main_server_id:
                await interaction.response.send_message("Main server ID not configured in config.json.", ephemeral=True)
                return

            guild = self.bot.get_guild(int(main_server_id))
            if not guild:
                try:
                    guild = await self.bot.fetch_guild(int(main_server_id))
                except:
                    guild = None

            if not guild:
                await interaction.response.send_message(f"Bot is not a member of the main server ({main_server_id}).", ephemeral=True)
                return

            user_mention = f"<@{uid}>"
            target_reason = self.reason.value or "Appeal accepted"

            if self.action_type == 'unban':
                try:
                    user = await self.bot.fetch_user(uid)
                    await guild.unban(user, reason=target_reason)
                    action_msg = f"Appeal Accepted. Unbanned {user_mention} in the main server."
                except discord.NotFound:
                    await interaction.response.send_message("User or ban not found.", ephemeral=True)
                    return
            elif self.action_type == 'untimeout':
                member = guild.get_member(uid)
                if not member:
                    try:
                        member = await guild.fetch_member(uid)
                    except Exception:
                        member = None
                if member:
                    await member.timeout(None, reason=target_reason)
                    action_msg = f"Appeal Accepted. Removed timeout from {user_mention} in the main server."
                else:
                    await interaction.response.send_message(f"Could not find member {uid} in the main server.", ephemeral=True)
                    return
            elif self.action_type == 'unkick':
                action_msg = f"Appeal Accepted. Kick overturned for {user_mention}. User may need to rejoin via invite."
            else:
                await interaction.response.send_message(f"Unknown action: {self.action_type}", ephemeral=True)
                return

            add_log({
                "type": self.action_type,
                "user_id": str(uid),
                "reason": target_reason,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            })
            await interaction.response.send_message(action_msg, ephemeral=False)

        except ValueError:
            await interaction.response.send_message("Invalid User ID.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("Bot lacks permissions to perform this action in the main server.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error performing action: {e}", ephemeral=True)

class ActionSelect(discord.ui.Select):
    def __init__(self, bot):
        options = [
            discord.SelectOption(label="Unban", value="unban", description="Remove a ban for the user"),
            discord.SelectOption(label="Untimeout", value="untimeout", description="Remove timeout from the user"),
            discord.SelectOption(label="Unkick", value="unkick", description="Record that a kick was overturned"),
        ]
        super().__init__(placeholder="Select action to perform...", min_values=1, max_values=1, options=options)
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(AcceptModal(self.values[0], self.bot))

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ban", description="Ban a user via a modal")
    @app_commands.default_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction):
        await interaction.response.send_modal(BanModal())

    @app_commands.command(name="kick", description="Kick a user via a modal")
    @app_commands.default_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction):
        await interaction.response.send_modal(KickModal())

    @app_commands.command(name="timeout", description="Timeout a user via a modal")
    @app_commands.default_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TimeoutModal())

    @app_commands.command(name="accept", description="Accept an appeal and undo an action")
    @app_commands.default_permissions(manage_guild=True)
    async def accept(self, interaction: discord.Interaction):
        view = discord.ui.View(timeout=300)
        view.add_item(ActionSelect(self.bot))
        await interaction.response.send_message("Select the action to undo:", view=view, ephemeral=True)

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
