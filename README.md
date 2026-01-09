# Please note, this is nothing but a passion project! Updates can be made in a few hours, a few days, or even a few years!


## Discord Moderation Bot with Appeal System

A comprehensive Discord moderation bot featuring automated logging, appeal system, and web dashboard for managing moderation actions.

### Features

- **Automated Logging**: All moderation actions (ban, kick, timeout) are automatically logged
- **Web Dashboard**: Manage custom commands and view moderation logs through a web interface
- **Appeal System**: Users can submit appeals for moderation actions with a dedicated workflow
- **Multi-Server Support**: Separate servers for main moderation and appeal handling
- **Dynamic Commands**: Create and manage custom slash commands through the web interface
- **Thread-Based Appeals**: Automatic creation of private threads for appeal discussions

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
- You shouldn't use the `/mod <command>` commands. They are the commands which are ran by the `/accept` command.
> See `Mod commands` in issues tab.
- `/ban`, `/kick`, `/timeout` are the commands you need.

#### Custom Commands
Custom commands can be managed through the web dashboard at `http://<your_local_ip>:5000`.

### Web Dashboard

The web dashboard provides several interfaces:

- **Dashboard** (`/`): Create and manage custom slash commands (requires login)
- **Logs** (`/logs`): View all moderation logs (public access)
- **Appeals** (`/appeals`): View and manage pending appeals (requires login)

## Appeal Process Flow

1. **Moderation Action**: A user is banned, kicked, or timed out
2. **Log Creation**: The action is automatically logged
3. **Appeal Submission**: User visits `/logs` and clicks "Appeal" on their log entry
4. **Appeal Review**: Moderators check `/appeals` to see pending appeals
5. **Case Opening**: Moderator clicks "Open Case" to create a private thread
6. **Resolution**: Moderator uses `/mod accept` command to resolve the appeal

> This process is still non-functional, but more headway has been made.


### File Structure

- `bot.py`: Main bot application with both Discord bot and Flask web server
- `moderation.py`: Moderation commands implementation
- `log_helper.py`: Functions for managing moderation logs
- `config.json`: Bot configuration (tokens, IDs, custom commands)
- `passwd.json`: Web dashboard password
- `logs.json`: Stored moderation logs
- `appeals.json`: Pending appeals
- All HTML files share names with their .json counterparts.

### Security

- The web dashboard and appeals page is password-protected
- Moderation commands require appropriate Discord permissions (Untested, proceed with caution.)

### Contributing

Feel free to submit issues and enhancement requests. Pull requests are welcome!

### License

This project is licensed under the MIT License - see the LICENSE file for details.
