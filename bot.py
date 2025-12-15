import json
import random
import discord
from discord.ext import commands
from discord import app_commands
from discord import ButtonStyle

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

class GuessBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            help_command=None,
            is_case_insensitive=True,
            intents=discord.Intents.default(),
        )
    
    async def setup_hook(self):
        await self.tree.sync()

bot = GuessBot()

#User hint counter
user_hint_counter = {}

def user_hint(user_id):
    user_hint_counter[user_id]= user_hint_counter.get(user_id,0)+1
    return user_hint_counter[user_id]

#Button colors (random)
#comment for branch issue2
button_colors = [ButtonStyle.red,ButtonStyle.green,ButtonStyle.blurple,ButtonStyle.gray]
button = discord.ui.Button(label="Guess", style=random.choice(button_colors))
button = button

@bot.event
async def on_ready():
    print("Ready!")
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} commands")

#User guess tracking
user_guess_counter = {}
@bot.tree.command(
    name="guess",
    description="Guess the song from the lyrics.",
)
async def guess(interaction: discord.Interaction):
    user_id = interaction.user.id
    user_guess_counter[user_id] = user_guess_counter.get(user_id, 0) + 1
    await interaction.response.send_message(f"You have guessed {user_guess_counter[user_id]} time(s)!",ephemeral=True)


bot.run(TOKEN)