import json
import random
import discord
from discord.ext import commands
from discord import app_commands
from discord import ButtonStyle
from discord import SelectOption, ui

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

#Button colors (random)
#comment for branch issue2
button_colors = [ButtonStyle.red,ButtonStyle.green,ButtonStyle.blurple,ButtonStyle.gray]
button = discord.ui.Button(label="Guess", style=random.choice(button_colors))
button = button

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

#Adding selection options
class CategorySelect(ui.Select):
    @ui.select(placeholder="Choose a category",
               options=[SelectOption(label="Pop"),
                        SelectOption(label="Rock"),
                        SelectOption(label="Jazz")
                    ]
                )

    async def select_callback(self, select, interaction: discord.Interaction):
        await interaction.response.send_message(f"You selected {self.values[0]} category!",ephemeral=True)

class GuessView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.add_item(discord.ui.Button(label="Guess", style=random.choice(button_colors)))


bot = GuessBot()

#User hint counter
user_hint_counter = {}

def user_hint(user_id):
    user_hint_counter[user_id]= user_hint_counter.get(user_id,0)+1
    return user_hint_counter[user_id]

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
    await interaction.response.send_message(content=(f"🎵 Guess registered!\n"
                                                     f"Guesses: {user_guess_counter[user_id]}\n"
                                                     f"Hints used: {user_hint_counter[user_id]}"),view=GuessView(user_id),ephemeral=True
)


bot.run(TOKEN)