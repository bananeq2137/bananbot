import os

import discord
from discord.ext import commands
from openai import OpenAI

# =========================
# OPENROUTER SETUP
# =========================

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
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

    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Game("Quizy AI 🎮")
    )

# =========================
# HELLO COMMAND
# =========================

@bot.command()
async def hello(ctx):

    await ctx.send(
        f"Witam, to jest {bot.user}"
    )

# =========================
# QUIZ COMMAND
# =========================

@commands.cooldown(
    1,
    10,
    commands.BucketType.user
)
@bot.command()
async def quiz(ctx, *, topic="random"):

    await ctx.send(
        "🧠 Generuję pytanie AI..."
    )

    if topic.lower() == "random":

        prompt = """
        Generate ONE fun random quiz question.

        Return EXACTLY in this format:

        QUESTION: question
        A: answer
        B: answer
        C: answer
        D: answer
        CORRECT: letter

        The correct answer should sometimes be:
        A, B, C or D.

        ONLY return the quiz.
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
        CORRECT: letter

        The correct answer should sometimes be:
        A, B, C or D.

        ONLY return the quiz.
        """

    # =========================
    # OPENROUTER REQUEST
    # =========================

    try:

        response = client.chat.completions.create(
            model="google/gemma-3-27b-it:free",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        text = response.choices[0].message.content.strip()

        print(text)

    except Exception as e:

        print("OPENROUTER ERROR:")
        print(e)

        await ctx.send(
            f"⚠️ Error:\n{e}"
        )

        return

    # =========================
    # PARSE QUIZ
    # =========================

    try:

        lines = text.split("\n")

        question = lines[0].replace(
            "QUESTION:",
            ""
        ).strip()

        a = lines[1].replace(
            "A:",
            ""
        ).strip()

        b = lines[2].replace(
            "B:",
            ""
        ).strip()

        c = lines[3].replace(
            "C:",
            ""
        ).strip()

        d = lines[4].replace(
            "D:",
            ""
        ).strip()

        correct = lines[5].replace(
            "CORRECT:",
            ""
        ).strip().upper()

    except Exception as e:

        print("PARSING ERROR:")
        print(e)

        await ctx.send(
            "❌ AI zwróciło błędny format."
        )

        return

    # =========================
    # EMBED
    # =========================

    embed = discord.Embed(
        title=f"🎮 Quiz: {topic}",
        description=question,
        color=discord.Color.blue()
    )

    embed.add_field(
        name="A",
        value=a,
        inline=False
    )

    embed.add_field(
        name="B",
        value=b,
        inline=False
    )

    embed.add_field(
        name="C",
        value=c,
        inline=False
    )

    embed.add_field(
        name="D",
        value=d,
        inline=False
    )

    embed.set_footer(
        text="Napisz A, B, C lub D"
    )

    await ctx.send(embed=embed)

    # =========================
    # ANSWER CHECK
    # =========================

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

            await ctx.send(
                "✅ Dobra odpowiedź!"
            )

        else:

            await ctx.send(
                f"❌ Zła odpowiedź!\n"
                f"Poprawna odpowiedź: {correct}"
            )

    except:

        await ctx.send(
            "⏰ Koniec czasu!"
        )

# =========================
# COOLDOWN ERROR
# =========================

@quiz.error
async def quiz_error(ctx, error):

    if isinstance(
        error,
        commands.CommandOnCooldown
    ):

        await ctx.send(
            f"⏳ Poczekaj "
            f"{round(error.retry_after, 1)} sekund!"
        )

# =========================
# START BOT
# =========================

bot.run(
    os.getenv("DISCORD_TOKEN")
)