import json
import random
import threading
import logging
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
import discord
from discord.ext import commands
from discord import ButtonStyle, SelectOption, ui

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("guessbot")

try:
    with open("config.json") as f:
        config = json.load(f)
except FileNotFoundError:
    raise RuntimeError("config.json file not found.")

TOKEN = config.get("DISCORD_TOKEN")
BOT_ID = int(config.get("DISCORD_BOT_ID", 0))
SPOTIFY_CLIENT_ID = config.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = config.get("SPOTIFY_CLIENT_SECRET")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN missing")
if not BOT_ID:
    raise RuntimeError("DISCORD_BOT_ID missing")
if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise RuntimeError("Spotify credentials missing")

SPOTIFY_REDIRECT_URI = "http://localhost:8080/callback"
SPOTIFY_SCOPE = "user-read-private user-read-email"

button_colors = [
    ButtonStyle.red,
    ButtonStyle.green,
    ButtonStyle.blurple,
    ButtonStyle.gray,
]

user_guess_counter: dict[int, int] = {}
user_hint_counter: dict[int, int] = {}
user_category: dict[int, str] = {}
spotify_tokens: dict[int, str] = {}
oauth_states: dict[str, int] = {}

def generate_spotify_auth_url(user_id: int) -> str:
    state = str(user_id)
    oauth_states[state] = user_id

    params = {
        "client_id": SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "scope": SPOTIFY_SCOPE,
        "state": state,
    }

    return "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(params)


class SpotifyCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)

        code = params.get("code", [None])[0]
        state = params.get("state", [None])[0]

        if not code or state not in oauth_states:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Authorization failed")
            return

        user_id = oauth_states.pop(state)

        res = requests.post(
            "https://accounts.spotify.com/api/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": SPOTIFY_REDIRECT_URI,
                "client_id": SPOTIFY_CLIENT_ID,
                "client_secret": SPOTIFY_CLIENT_SECRET,
            },
            timeout=10,
        )

        token_data = res.json()
        spotify_tokens[user_id] = token_data.get("access_token")

        logger.info(f"Spotify connected for user {user_id}")

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Spotify connected! You can close this window.")



def start_callback_server():
    server = HTTPServer(("localhost", 8080), SpotifyCallbackHandler)
    logger.info("Spotify OAuth callback server started on port 8080")
    server.serve_forever()


threading.Thread(target=start_callback_server, daemon=True).start()

class GuessBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            help_command=None,
            intents=discord.Intents.default(),
        )

    async def setup_hook(self):
        await self.tree.sync()
        logger.info("Slash commands synced")


bot = GuessBot()

class CategorySelect(ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="Choose a category",
            options=[
                SelectOption(label="Pop"),
                SelectOption(label="Rock"),
                SelectOption(label="Jazz"),
            ],
        )

    async def callback(self, interaction: discord.Interaction):
        user_category[interaction.user.id] = self.values[0]
        await interaction.response.send_message(
            f"Category set to **{self.values[0]}**",
            ephemeral=True,
        )


class GuessView(ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=60)
        self.user_id = user_id

        self.add_item(
            ui.Button(label="Guess", style=random.choice(button_colors))
        )
        self.add_item(CategorySelect())


@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    if bot.user.id != BOT_ID:
        raise RuntimeError("Bot ID mismatch")


@bot.event
async def on_connect():
    logger.info("Bot connected to Discord")


@bot.event
async def on_disconnect():
    logger.warning("Bot disconnected from Discord")


@bot.tree.command(name="guess", description="Guess the song from the lyrics")
async def guess(interaction: discord.Interaction):
    user_id = interaction.user.id
    user_guess_counter[user_id] = user_guess_counter.get(user_id, 0) + 1

    await interaction.response.send_message(
        content=(
            "**Guess registered!**\n"
            f"Guesses: {user_guess_counter[user_id]}\n"
            f"Hints used: {user_hint_counter.get(user_id, 0)}\n"
            f"Category: {user_category.get(user_id, 'Not selected')}\n"
            f"Spotify connected: {'Yes' if user_id in spotify_tokens else 'No'}"
        ),
        view=GuessView(user_id),
        ephemeral=True,
    )


@bot.tree.command(name="spotify_login", description="Connect your Spotify account")
async def spotify_login(interaction: discord.Interaction):
    url = generate_spotify_auth_url(interaction.user.id)
    await interaction.response.send_message(
        f" **Spotify Login**\n[Click here to connect]({url})",
        ephemeral=True,
    )


bot.run(TOKEN)