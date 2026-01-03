# DisCoder Discord Bot

A Discord bot with moderation capabilities, logging, and appeal management system.

## Features

- Custom slash commands with dynamic creation
- Moderation commands (ban, kick, timeout)
- Logging system for moderation actions
- Appeal management system
- Web dashboard for command management
- User appeal submission system

## Prerequisites

- Python 3.13 or higher
- Discord Bot Token (get from [Discord Developer Portal](https://discord.com/developers/applications))
- Required Python packages (see requirements.txt)
- Ollama (For use with /llm command only)

## Installation

1. Clone this repository:
   ```bash
   git clone (https://github.com/LePebblee/ModBot.git)
   cd <repository-dir>
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up configuration files:
   - Update `config.json` with your bot token and server/channel IDs
   - Update `passwd.json` with your admin password

## Configuration should look like:

### config.json
```json
{
    "token": "YOUR_BOT_TOKEN_HERE",
    "log_channel_id": "YOUR_LOG_CHANNEL_ID_HERE",
    "main_server": "YOUR_MAIN_SERVER_ID_HERE",
    "app_server": "application server (PLANNED FOR THE FUTURE)",
    "custom_commands": {
        ...
    }
}
```

### passwd.json
```json
{
    "password": "YOUR_ADMIN_PASSWORD_HERE"
}
```

## Usage

1. Run the bot:
   ```bash
   python bot.py
   ```

2. The web dashboard will be available at `http://localhost:5000`

3. Access the dashboard using the password set in `passwd.json`

## Custom Commands

The bot supports dynamic command creation through the web dashboard, and command generation with Qwen. You can create custom slash commands with Python scripts that have access to the interaction object. However, if you use Qwen, it will likely not work because Qwen uses code blocks even when told not to. The edit button in the active commands section is there for this exact reason.

## Appeal System

Users can submit appeals for moderation actions through the public logs page. Moderators can manage appeals through the dashboard.

## Contributing

Feel free to submit issues and enhancement requests.

## License

This project is licensed under the MIT License.
