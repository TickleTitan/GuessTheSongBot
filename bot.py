import json
import random
import discord
from discord.ext import commands
from discord import app_commands
from discord import ButtonStyle, SelectOption, ui

try:
    with open("config.json") as f:
        config = json.load(f)
except FileNotFoundError:
    raise RuntimeError("config.json file not found.")

TOKEN = config.get("DISCORD_TOKEN")
BOT_ID = config.get("DISCORD_BOT_ID")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN not found in config.json.")
if not BOT_ID:
    raise RuntimeError("DISCORD_BOT_ID not found in config.json.")

BOT_ID = int(BOT_ID)

button_colors = [
    ButtonStyle.red,
    ButtonStyle.green,
    ButtonStyle.blurple,
    ButtonStyle.gray,
]

user_guess_counter: dict[int, int] = {}
user_hint_counter: dict[int, int] = {}
user_category: dict[int, str] = {}

#Logging>Print
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger("guessbot")

class GuessBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            help_command=None,
            is_case_insensitive=True,
            intents=discord.Intents.default(),
        )

    async def setup_hook(self):
        # Correct place to sync slash commands
        await self.tree.sync()
        logger.info("Slash commands synced successfully")

bot = GuessBot()

class CategorySelect(ui.Select):
    def __init__(self):
        options = [
            SelectOption(label="Pop"),
            SelectOption(label="Rock"),
            SelectOption(label="Jazz"),
        ]
        super().__init__(
            placeholder="Choose a category",
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        user_category[interaction.user.id] = self.values[0]
        await interaction.response.send_message(
            f"You selected **{self.values[0]}** category!",
            ephemeral=True,
        )

class GuessView(ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=60)
        self.user_id = user_id

        # Guess button with random color
        self.add_item(
            ui.Button(
                label="Guess",
                style=random.choice(button_colors),
            )
        )

        # Category select menu
        self.add_item(CategorySelect())

def get_hint_count(user_id: int) -> int:
    return user_hint_counter.get(user_id, 0)

@bot.event
async def on_ready():
    logger.info(f"Bot logged in as {bot.user} (ID: {bot.user.id})")
    if bot.user.id != BOT_ID:
        logger.error(
            f"Bot ID mismatch: expected {BOT_ID}, got {bot.user.id}"
        )
        raise RuntimeError(
            f"Bot ID mismatch: expected {BOT_ID}, got {bot.user.id}"
        ):
    print(f"Bot logged in as {bot.user} (ID: {bot.user.id})")
    if bot.user.id != BOT_ID:
        raise RuntimeError(
            f"Bot ID mismatch: expected {BOT_ID}, got {bot.user.id}"
        )

@bot.tree.command(
    name="guess",
    description="Guess the song from the lyrics.",
)
async def guess(interaction: discord.Interaction):
    user_id = interaction.user.id

    # Guess counter
    user_guess_counter[user_id] = user_guess_counter.get(user_id, 0) + 1

    await interaction.response.send_message(
        content=(
            "🎵 **Guess registered!**\n"
            f"Guesses: {user_guess_counter[user_id]}\n"
            f"Hints used: {get_hint_count(user_id)}\n"
            f"Category: {user_category.get(user_id, 'Not selected')}"
        ),
        view=GuessView(user_id),
        ephemeral=True,
    )

bot.run(TOKEN)
