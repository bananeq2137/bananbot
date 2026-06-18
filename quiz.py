import os
import json
from pathlib import Path
import sqlite3

import discord
from discord.ext import commands
from google import genai

# =========================
# GEMINI SETUP
# =========================

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

conn = sqlite3.connect("scores.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS scores (
    user_id TEXT PRIMARY KEY,
    points INTEGER NOT NULL
)
""")

conn.commit()



# =========================
# DISCORD BOT SETUP
# =========================

intents = discord.Intents.default()
intents.message_content = True
intents.presences = True
intents.members = True

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
    await ctx.send(f"Witam, to jest {bot.user}")

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

    await ctx.send("🧠 Generuję pytanie AI...")

    if topic.lower() == "random":
        topic = "random topic"

    prompt = f"""
Create ONE quiz question about: {topic}

Return ONLY valid JSON.

Example:

{{
  "question": "What is the capital of France?",
  "A": "Berlin",
  "B": "Paris",
  "C": "Madrid",
  "D": "Rome",
  "correct": "B"
}}

Rules:
- No markdown
- No code blocks
- No explanations
- Return ONLY JSON
- correct must be A, B, C or D
- Randomize the correct answer position
"""

    try:

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

        text = response.text.strip()

        print("RAW RESPONSE:")
        print(text)

        # usuwanie ewentualnych ```json
        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

        quiz_data = json.loads(text)

    except Exception as e:

        print("GEMINI ERROR:")
        print(e)

        await ctx.send(
            "⚠️ Gemini jest obecnie przeciążone. Spróbuj ponownie za chwilę."
        )
        return

    try:

        question = quiz_data["question"]
        a = quiz_data["A"]
        b = quiz_data["B"]
        c = quiz_data["C"]
        d = quiz_data["D"]
        correct = quiz_data["correct"].upper()

    except Exception as e:

        print("JSON ERROR:")
        print(e)

        await ctx.send(
            "❌ AI zwróciło niepoprawny format."
        )

        return

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

            user_id = str(ctx.author.id)

            cursor.execute(
                "SELECT points FROM scores WHERE user_id = ?",
                (user_id,)
            )

            result = cursor.fetchone()

            if result:
                points = result[0] + 1

                cursor.execute(
                    "UPDATE scores SET points = ? WHERE user_id = ?",
                    (points, user_id)
                )
            else:
                points = 1

                cursor.execute(
                    "INSERT INTO scores (user_id, points) VALUES (?, ?)",
                    (user_id, points)
                )

            conn.commit()

            await ctx.send(
                f"✅ Dobra odpowiedź!\n🏆 Punkty: {points}"
            )

        else:

            await ctx.send(
                f"❌ Zła odpowiedź!\nPoprawna odpowiedź: {correct}"
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
            f"⏳ Poczekaj {round(error.retry_after, 1)} sekund!"
        )

# =========================
# START BOT
# =========================


@bot.command()
async def rank(ctx):

    cursor.execute(
        "SELECT user_id, points FROM scores ORDER BY points DESC LIMIT 10"
    )

    scores = cursor.fetchall()

    if not scores:
        await ctx.send("📊 Ranking jest pusty.")
        return

    text = "🏆 Ranking:\n\n"

    for place, (user_id, points) in enumerate(scores, start=1):

        try:
            user = await bot.fetch_user(int(user_id))
            name = user.name
        except:
            name = f"User {user_id}"

        text += f"{place}. {name} - {points} pkt\n"

    await ctx.send(text)




TASKS_FILE = Path("tasks.json")


def load_tasks():
    if TASKS_FILE.exists():
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_tasks(tasks):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=4, ensure_ascii=False)


@bot.command()
async def addtask(ctx, *, task: str):
    tasks = load_tasks()
    user_id = str(ctx.author.id)

    if user_id not in tasks:
        tasks[user_id] = []

    tasks[user_id].append(task)
    save_tasks(tasks)

    await ctx.send(f"✅ Dodano zadanie:\n{len(tasks[user_id])}. {task}")

@bot.command()
async def tasks(ctx):

    tasks = load_tasks()
    user_id = str(ctx.author.id)

    if user_id not in tasks or len(tasks[user_id]) == 0:
        await ctx.send("📭 Nie masz żadnych zadań.")
        return

    text = "📝 Twoje zadania:\n\n"

    for i, task in enumerate(tasks[user_id], start=1):
        text += f"{i}. {task}\n"

    await ctx.send(text)

@bot.command()
async def done(ctx, number: int):

    tasks = load_tasks()
    user_id = str(ctx.author.id)

    if user_id not in tasks:
        await ctx.send("📭 Nie masz zadań.")
        return

    if number < 1 or number > len(tasks[user_id]):
        await ctx.send("❌ Nieprawidłowy numer zadania.")
        return

    removed = tasks[user_id].pop(number - 1)

    save_tasks(tasks)

    await ctx.send(
        f"✅ Wykonano zadanie:\n{removed}"
    )

bot.run(
    os.getenv("DISCORD_TOKEN")
)