import discord
from discord import app_commands
from discord.ext import commands
import threading
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
import json
import os
import asyncio
import logging
from typing import Optional
from datetime import datetime
import subprocess


# external variables
from log_helper import add_log
from moderation import Moderation, notify_user_of_appeal


logging.basicConfig(level=logging.INFO)

CONFIG_FILE = 'config.json'
LOGS_FILE = 'logs.json'
PASS_FILE = 'passwd.json'
APPEALS_FILE = 'appeals.json'

# Configuration Management
def load_json_file(filename, default):
    if not os.path.exists(filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(default, f, indent=4)
        return default
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading {filename}: {e}")
        return default

def save_json_file(filename, data):
    import tempfile
    import os
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', dir=os.path.dirname(filename), encoding='utf-8') as f:
            json.dump(data, f, indent=4)
            temp_name = f.name
        os.replace(temp_name, filename)
    except Exception as e:
        logging.error(f"Error saving {filename}: {e}")
        if 'temp_name' in locals():
            try:
                os.unlink(temp_name)
            except:
                pass

config = load_json_file(CONFIG_FILE, {"token": "", "log_channel_id": "", "custom_commands": {}})
pass_config = load_json_file(PASS_FILE, {"password"})

# Bot Setup
class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self.user_cache = {}

    async def setup_hook(self):
        for name, script in config.get('custom_commands', {}).items():
            try:
                self.create_dynamic_command(name, script)
            except Exception as e:
                logging.error(f"Failed to load command {name}: {e}")
        # Add Moderation command group
        self.tree.add_command(Moderation(self))
        await self.tree.sync()

    async def resolve_user(self, user_id):
        user_id = int(user_id)
        # Check local cache first
        if user_id in self.user_cache:
            return self.user_cache[user_id]
        
        # Check bot cache
        user = self.get_user(user_id)
        if user:
            self.user_cache[user_id] = user.name
            return user.name

        # Fetch from API (fallback)
        try:
            user = await self.fetch_user(user_id)
            self.user_cache[user_id] = user.name
            return user.name
        except:
            return None

    def create_dynamic_command(self, name, script):
        existing = self.tree.get_command(name)
        if existing:
            self.tree.remove_command(name)

        async def dynamic_callback(interaction: discord.Interaction):
            local_vars = {
                'interaction': interaction, 
                'client': self, 
                'discord': discord,
                'app_commands': app_commands
            }
            exec_globals = globals().copy()
            exec_globals.update(local_vars)
            try:
                indented_script = "\n    ".join(script.splitlines())
                exec_code = f"async def _eval_coro(interaction, client, discord, app_commands):\n    {indented_script}"
                exec(exec_code, exec_globals)
                await exec_globals['_eval_coro'](interaction, self, discord, app_commands)
            except Exception as e:
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"Execution Error: {e}", ephemeral=True)
                logging.error(f"Dynamic command error ({name}): {e}")

        new_command = app_commands.Command(
            name=name,
            description=f"Dynamic command: {name}",
            callback=dynamic_callback
        )
        self.tree.add_command(new_command)

bot = DiscordBot()
app = Flask(__name__, template_folder='.')
app.secret_key = 'super_secret_dev_key_change_in_prod'

# --- Middleware ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# --- Flask Routes ---

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        if request.form.get('password') == pass_config.get('password'):
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid Password")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('logs'))

@app.route('/')
@login_required
def index():
    return render_template('dashboard.html', commands=config.get('custom_commands', {}))

@app.route('/logs')
def logs():
    # Logs are public so users can appeal
    search_query = request.args.get('search', '').strip()
    all_logs = load_json_file(LOGS_FILE, [])
    
    # Filter logs
    if search_query:
        filtered_logs = [log for log in all_logs if search_query.lower() in str(log.get('user_id', '')).lower()]
    else:
        filtered_logs = all_logs

    # Resolve Usernames
    for log in filtered_logs:
        if 'user_id' in log:
            try:
                future = asyncio.run_coroutine_threadsafe(bot.resolve_user(log['user_id']), bot.loop)
                username = future.result(timeout=1) # 1 sec timeout
                if username:
                    log['username'] = username
            except Exception:
                pass 

    filtered_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return render_template('logs.html', logs=filtered_logs, search_query=search_query)

@app.route('/appeals')
@login_required
def appeals():
    all_appeals = load_json_file(APPEALS_FILE, [])
    return render_template('appeals.html', appeals=all_appeals)

@app.route('/add_cmd', methods=['POST'])
@login_required
def add_cmd():
    name = request.form.get('name', '').strip().lower()
    script = request.form.get('script', '').strip()
    if name and script:
        config['custom_commands'][name] = script
        save_json_file(CONFIG_FILE, config)
        bot.create_dynamic_command(name, script)
        asyncio.run_coroutine_threadsafe(bot.tree.sync(), bot.loop)
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Invalid name or script"}), 400

@app.route('/delete_cmd', methods=['POST'])
@login_required
def delete_cmd():
    name = request.form.get('name', '').strip().lower()
    if name in config['custom_commands']:
        del config['custom_commands'][name]
        save_json_file(CONFIG_FILE, config)
        bot.tree.remove_command(name)
        asyncio.run_coroutine_threadsafe(bot.tree.sync(), bot.loop)
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Command not found"}), 404

@app.route('/edit_cmd', methods=['POST'])
@login_required
def edit_cmd():
    old_name = request.form.get('old_name', '').strip().lower()
    new_name = request.form.get('name', '').strip().lower()
    new_script = request.form.get('script', '').strip()
    if not old_name or not new_name or not new_script:
        return jsonify({"status": "error", "message": "All fields required"}), 400
    if old_name not in config['custom_commands']:
        return jsonify({"status": "error", "message": "Command not found"}), 404
    # Remove old
    del config['custom_commands'][old_name]
    # Add new
    config['custom_commands'][new_name] = new_script
    logging.info(f"Updated command {old_name} to {new_name}")
    save_json_file(CONFIG_FILE, config)
    logging.info("Config saved")
    # Update bot
    bot.tree.remove_command(old_name)
    bot.create_dynamic_command(new_name, new_script)
    asyncio.run_coroutine_threadsafe(bot.tree.sync(), bot.loop)
    return jsonify({"status": "success"})

@app.route('/generate_cmd', methods=['POST'])
@login_required
def generate_cmd():
    name = request.form.get('name', '').strip().lower()
    description = request.form.get('description', '').strip()
    if not name or not description:
        return jsonify({"status": "error", "message": "Name and description required"}), 400
    try:
        prompt = f"Generate Python code for a Discord slash command that {description}. Output only the executable Python statements for the command handler, no function definitions, explanations, or markdown. The code should use 'interaction' to respond."
        logging.info(f"Running qwen.cmd with prompt: {prompt}")
        result = subprocess.run(['qwen.cmd', prompt], capture_output=True, text=True, timeout=30)
        logging.info(f"Qwen result: returncode={result.returncode}, stdout='{result.stdout}', stderr='{result.stderr}'")
        if result.returncode == 0:
            script = result.stdout.strip()
            if script:
                config['custom_commands'][name] = script
                save_json_file(CONFIG_FILE, config)
                bot.create_dynamic_command(name, script)
                asyncio.run_coroutine_threadsafe(bot.tree.sync(), bot.loop)
                return jsonify({"status": "success"})
            else:
                return jsonify({"status": "error", "message": "No code generated"}), 400
        else:
            return jsonify({"status": "error", "message": f"Qwen failed: {result.stderr}"}), 500
    except Exception as e:
        logging.error(f"Exception in generate_cmd: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/submit_appeal', methods=['POST'])
def submit_appeal():
    # Public route
    log_id = request.form.get('log_id')
    appeal_text = request.form.get('appeal_text')
    
    if not log_id or not appeal_text:
        return jsonify({"status": "error", "message": "Missing fields"}), 400
    
    # Verify log exists
    all_logs = load_json_file(LOGS_FILE, [])
    log_entry = next((item for item in all_logs if item["id"] == log_id), None)
    
    if not log_entry:
        return jsonify({"status": "error", "message": "Invalid Log ID"}), 400

    new_appeal = {
        "log_id": log_id,
        "user_id": log_entry.get('user_id'),
        "text": appeal_text,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    all_appeals = load_json_file(APPEALS_FILE, [])
    all_appeals.insert(0, new_appeal) # Newest first
    save_json_file(APPEALS_FILE, all_appeals)
    
    return jsonify({"status": "success", "message": "Appeal submitted"})

@app.route('/dismiss_appeal', methods=['POST'])
@login_required
def dismiss_appeal():
    user_id = request.form.get('user_id')
    log_id = request.form.get('log_id')
    
    if not user_id or not log_id:
        return jsonify({"status": "error", "message": "Missing IDs"}), 400
        
    all_appeals = load_json_file(APPEALS_FILE, [])
    # Filter out the appeal that matches both user_id and log_id
    new_appeals = [a for a in all_appeals if not (a.get('user_id') == user_id and a.get('log_id') == log_id)]
    
    if len(new_appeals) == len(all_appeals):
         return jsonify({"status": "error", "message": "Appeal not found"}), 404
         
    save_json_file(APPEALS_FILE, new_appeals)
    return jsonify({"status": "success", "message": "Appeal dismissed"})

@app.route('/open_case', methods=['POST'])
@login_required
def open_case():
    user_id = request.form.get('user_id')
    log_id = request.form.get('log_id')
    
    if not user_id or not log_id:
        return jsonify({"status": "error", "message": "Missing IDs"}), 400

    async def _create_thread_task():
        channel_id = config.get('app_channel_id')
        if not channel_id:
            return "App channel ID not configured in config.json."
        
        try:
            channel = bot.get_channel(int(channel_id))
            if not channel:
                # Try fetching if not in cache
                channel = await bot.fetch_channel(int(channel_id))
        except Exception:
            return "Could not find configured log channel."

        try:
            # Send initial message
            msg_content = f"Appeal Case - <@{user_id}> [Log ID: {log_id}]"
            message = await channel.send(msg_content)
            
            # Create thread
            thread = await message.create_thread(name=f"appeal-{user_id}", auto_archive_duration=1440)
            
            # Attempt to add user (Note: May fail if user is banned and not in the server)
            try:
                user = await bot.fetch_user(int(user_id))
                await thread.add_user(user)
                thread_result = "Thread created and user added."
            except discord.Forbidden:
                await thread.send("Created thread, but could not add user (Permissions error or user banned).")
                thread_result = "Thread created (User add failed: Forbidden)."
            except Exception as e:
                await thread.send(f"Created thread, but error adding user: {e}")
                thread_result = f"Thread created (User add failed: {e})."
            
            # Send invite link DM to user
            invite_link = config.get('application_invite_link', 'https://discord.gg/invalid')
            try:
                await notify_user_of_appeal(bot, user_id, invite_link)
                thread_result += " User notified via DM."
            except Exception as e:
                logging.error(f"Failed to notify user {user_id}: {e}")
                
            return thread_result
                
        except Exception as e:
            return f"Bot Error: {e}"

    # Execute async task from Flask
    future = asyncio.run_coroutine_threadsafe(_create_thread_task(), bot.loop)
    try:
        result = future.result(timeout=10)
        return jsonify({"status": "success", "message": result})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Timeout or Error: {str(e)}"}), 500

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

async def main():
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    token = config.get('token')
    if token:
        async with bot:
            await bot.start(token)
    else:
        logging.error("No Discord token provided in config.json")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass