import discord
import json
import os
from log_helper import add_log

class AcceptModal(discord.ui.Modal, title="Accept Appeal"):
    user_id = discord.ui.TextInput(label="User ID", placeholder="User ID to act upon", required=True)
    reason = discord.ui.TextInput(label="Reason", style=discord.TextStyle.paragraph, required=False)

    def __init__(self, action_type: str):
        super().__init__()
        self.action_type = action_type

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Load config to get main server
            config_file = 'config.json'
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                await interaction.response.send_message("Config file not found.", ephemeral=True)
                return

            main_server_id = config.get('main_server')
            if not main_server_id:
                await interaction.response.send_message("Main server ID not configured in config.json.", ephemeral=True)
                return

            # Get the main server
            guild = client.get_guild(int(main_server_id))
            if not guild:
                await interaction.response.send_message(f"Could not find main server with ID {main_server_id}.", ephemeral=True)
                return

            user_obj = discord.Object(id=int(self.user_id.value))
            user_mention = f"<@{self.user_id.value}>"
            
            if self.action_type == "Unban":
                await guild.unban(user_obj, reason=self.reason.value)
                action_msg = f"Appeal Accepted. Unbanned {user_mention}."
            elif self.action_type == "Untimeout":
                # Get the member and remove timeout
                member = guild.get_member(int(self.user_id.value))
                if member:
                    await member.timeout(None, reason=self.reason.value)  # Remove timeout
                    action_msg = f"Appeal Accepted. Removed timeout from {user_mention}."
                else:
                    # If member not in cache, try to fetch
                    try:
                        member = await guild.fetch_member(int(self.user_id.value))
                        await member.timeout(None, reason=self.reason.value)
                        action_msg = f"Appeal Accepted. Removed timeout from {user_mention}."
                    except:
                        await interaction.response.send_message(f"Could not find member {self.user_id.value} in the server to remove timeout.", ephemeral=True)
                        return
            elif self.action_type == "Unkick":
                # For unkick, we can't directly "unkick" but we can send a message that the kick is overturned
                # Since kicked users are not in the server, we can't directly unkick them
                action_msg = f"Appeal Accepted. Kick overturned for {user_mention}. User may need to rejoin via invite."
            else:
                await interaction.response.send_message(f"Unknown action: {self.action_type}", ephemeral=True)
                return

            await interaction.response.send_message(action_msg, ephemeral=False)
            
        except discord.Forbidden:
            await interaction.response.send_message("Bot lacks permissions to perform this action.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error performing action: {e}", ephemeral=True)

class ActionTypeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)  # 5 minutes timeout

    @discord.ui.button(label="Unban", style=discord.ButtonStyle.danger, emoji="🔨")
    async def unban_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        modal = AcceptModal("Unban")
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Untimeout", style=discord.ButtonStyle.primary, emoji="⏰")
    async def untimeout_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        modal = AcceptModal("Untimeout")
        await interaction.response.send_message("Selecting Untimeout action...", ephemeral=True)
        await interaction.followup.send_modal(modal)

    @discord.ui.button(label="Unkick", style=discord.ButtonStyle.secondary, emoji="🚪")
    async def unkick_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        modal = AcceptModal("Unkick")
        await interaction.response.send_message("Selecting Unkick action...", ephemeral=True)
        await interaction.followup.send_modal(modal)

# Send the view with action buttons
await interaction.response.send_message("Select the action to undo:", view=ActionTypeView(), ephemeral=True)