import os
from pathlib import Path
import discord
from discord.ext import commands
import google.generativeai as genai

# =========================
# GEMINI API SETUP
# =========================

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel(
    "gemini-2.0-flash-lite"
)

# =========================
# DISCORD BOT SETUP
# =========================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# =========================
# BOT READY EVENT
# =========================

@bot.event
async def on_ready():
    print(f"Zalogowano jako {bot.user}")

# =========================
# HELLO COMMAND
# =========================

@bot.command()
async def hello(ctx):
    await ctx.send(f"Witam, to jest {bot.user}")

# =========================
# QUIZ COMMAND
# =========================

@bot.command()
async def quiz(ctx, *, topic="random"):

    await ctx.send("🧠 Generuję pytanie AI...")

    if topic.lower() == "random":

        prompt = """
        Generate ONE random fun quiz question.

        Return EXACTLY in this format:

        QUESTION: question
        A: answer
        B: answer
        C: answer
        D: answer
        CORRECT: one correct letter

        The correct answer must sometimes be A,
        sometimes B, sometimes C, sometimes D.

        ONLY return:
        A or B or C or D in CORRECT.

        Example:
        CORRECT: C
        """

    else:

        prompt = f"""
        Generate ONE quiz question about {topic}.

        Return EXACTLY in this format:

        QUESTION: question
        A: answer
        B: answer
        C: answer
        D: answer
        CORRECT: one correct letter

        The correct answer must sometimes be A,
        sometimes B, sometimes C, sometimes D.

        ONLY return:
        A or B or C or D in CORRECT.

        Example:
        CORRECT: D
        """

    response = model.generate_content(prompt)

    text = response.text.strip()

    print(text)

    try:

        lines = text.split("\n")

        question = lines[0].replace("QUESTION:", "").strip()

        a = lines[1].replace("A:", "").strip()
        b = lines[2].replace("B:", "").strip()
        c = lines[3].replace("C:", "").strip()
        d = lines[4].replace("D:", "").strip()

        correct = lines[5].replace("CORRECT:", "").strip().upper()

    except:

        await ctx.send("❌ AI zwróciło błędny format.")
        return

    embed = discord.Embed(
        title=f"🎮 Quiz: {topic}",
        description=question,
        color=discord.Color.blue()
    )

    embed.add_field(name="A", value=a, inline=False)
    embed.add_field(name="B", value=b, inline=False)
    embed.add_field(name="C", value=c, inline=False)
    embed.add_field(name="D", value=d, inline=False)

    embed.set_footer(text="Napisz A, B, C lub D")

    await ctx.send(embed=embed)

    def check(message):
        return (
            message.author == ctx.author
            and message.channel == ctx.channel
        )

    try:

        msg = await bot.wait_for(
            "message",
            timeout=15.0,
            check=check
        )

        user_answer = msg.content.upper().strip()

        if user_answer == correct:

            await ctx.send("✅ Dobra odpowiedź!")

        else:

            await ctx.send(
                f"❌ Zła odpowiedź!\n"
                f"Poprawna odpowiedź: {correct}"
            )

    except:

        await ctx.send("⏰ Koniec czasu!")

# =========================
# DISCORD TOKEN
# =========================

def get_discord_token():

    token = os.getenv("DISCORD_TOKEN")

    if token:
        return token.strip().strip('"\'')
    
    path = Path(__file__).resolve().parent / "token.txt"

    if path.exists():
        return path.read_text(
            encoding="utf-8"
        ).strip().strip('"\'')

    raise SystemExit(
        "Nie znaleziono tokena Discord."
    )

# =========================
# START BOT
# =========================

bot.run(os.getenv("DISCORD_TOKEN"))