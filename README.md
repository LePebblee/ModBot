# Please note, this is nothing but a passion project! Updates can be made in a few hours, a few days, or even a few years!


## Discord Moderation Bot with Appeal System

A comprehensive Discord moderation bot featuring automated logging, appeal system, and web dashboard for managing moderation actions.

### Features

- **Automated Logging**: Moderation actions (ban, kick) are automatically logged for the appeal system.
- **Pre-action Notifications**: Users receive a DM with an explanation and appeal server invite link before being banned or kicked.
- **Enhanced Appeal Dashboard**: Moderators can manage appeals through a dedicated "Appeal Case" page, allowing them to Accept or Deny appeals directly from the web.
- **Web Dashboard**: Manage custom commands and view moderation logs through a web interface.
- **Appeal System**: Users can submit appeals for moderation actions with a dedicated workflow.
- **Multi-Server Support**: Separate servers for main moderation and appeal handling.
- **Dynamic Commands**: Create and manage custom slash commands through the web interface.
- **Thread-Based Appeals**: Automatic creation of private threads for appeal discussions.

### Prerequisites

- Python 3.8+
- Discord Bot Token with appropriate permissions
- Two Discord servers (main server and appeal server)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```


### Configuration examples

### config.json
Update the `config.json` file with your specific values:

```json
{
    "token": "YOUR_DISCORD_BOT_TOKEN",
    "log_channel_id": "LOG_CHANNEL_ID",
    "main_server": "MAIN_SERVER_ID",
    "app_server": "APPEAL_SERVER_ID",
    "app_channel_id": "APPEAL_CHANNEL_ID",
    "application_invite_link": "https://discord.gg/YOUR_INVITE_LINK",
    "custom_commands": {
        ...
    }
}
```
> Note: Use Discord's python library for commands, even in the Web UI. Plain text will *not* work.


### passwd.json
Set a secure password for the web dashboard:

```json
{
    "password": "YOUR_PASSWORD"
}
```

### Required Bot Permissions

Make sure your bot has the following permissions:
- View Channels
- Send Messages
- Manage Messages
- Embed Links
- Read Message History
- Mention Everyone
- Use External Emojis
- Ban Members
- Kick Members
- Manage Threads
- Create Public Threads
- Send Messages in Threads
- Moderate Members (for timeouts)

- You can use Administrator to bypass all of this, but it is NOT reccomended for anything other than testing.

### Usage

### Starting the Bot

```bash
python bot.py
```

The bot will start and begin listening for commands, while also launching the web dashboard on `http://<your_local_ip>:5000`.

### Available Commands

#### Moderation Commands
- `/ban`, `/kick`, `/timeout`: Core moderation actions. `/ban` and `/kick` notify the user via DM and create an appealable log.
- `/accept`: Top-level command for moderators to manually resolve an appeal by overturning a ban or kick. (Also used on Appeal Case [See Web Dashboard -> Appeal Case on this readme file.])

#### Custom Commands
Custom commands can be managed through the web dashboard at `http://<your_local_ip>:5000`.

### Web Dashboard

The web dashboard provides several interfaces:

- **Dashboard** (`/`): Create and manage custom slash commands (requires login).
- **Logs** (`/logs`): View all moderation logs (public access).
- **Appeals** (`/appeals`): View pending appeals (requires login).
- **Appeal Case** (`/appeal_case/<user_id>/<log_id>`): Manage a specific appeal case with options to Accept or Deny.

## Appeal Process Flow

1. **Moderation Action**: A user is banned or kicked via Discord command.
2. **User Notification**: The user receives a DM with an invite to the appeals server.
3. **Log Creation**: The action is automatically logged in the system.
4. **Appeal Submission**: User visits `/logs`, finds their entry, and clicks "Appeal".
5. **Case Opening**: Moderator checks `/appeals` and clicks "Open Case" to create a private Discord thread and access the management page.
6. **Resolution**: Moderator uses the web dashboard to **Accept** (unban/unkick) or **Deny** (notifying the user in the thread) the appeal.

### File Structure

- `bot.py`: Main bot application with both Discord bot and Flask web server
- `moderation.py`: Implementation of the `/accept` command and core appeal actions
- `log_helper.py`: Functions for managing moderation logs
- `config.json`: Bot configuration (tokens, IDs, custom commands)
- `passwd.json`: Web dashboard password
- `logs.json`: Stored moderation logs
- `appeals.json`: Pending appeals and thread tracking
- `appeal_case.html`: Dashboard template for managing individual appeals
- `appeals.html`, `dashboard.html`, `logs.html`, `login.html`: Web dashboard templates

### Security

- The web dashboard and appeals management pages are password-protected.
> Default configs use HTTP, not HTTPS. Proceed with caution.
- Moderation commands include explicit permission checks (e.g., `ban_members`) to ensure security.
> Untested. Proceed with caution.

### Todo:
- Rewrite with human-only code (Currently, Jules is partially used) [Likely not happening soon because life exists]
- Clean the code in general (It is currently very messy and unoptimized, with files required for functions being in a dedicated file even though they could be a single line in `config.json` [*cough cough* ***passwd.json*** *cough*])
- Make the edit button in the Web UI dashboard actually work
- Remove "Generate with Qwen" block on the Web UI dashboard (It does not work, even with the qwen-coder cli. Don't try.)

### Contributing

Feel free to submit issues and enhancement requests. Pull requests are welcome!

### License

This project is licensed under the MIT License - see the LICENSE file for details.
