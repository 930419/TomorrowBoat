import os, discord, random, json

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)

# 載入 JSON
with open("jiname.json", "r", encoding="utf-8") as f:
    ji = json.load(f)
with open("sixstar.json", "r", encoding="utf-8") as f:
    sixstar = json.load(f)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.strip()

    if "集" in content and client.user in message.mentions:
        # 抽主題
        theme = random.choice(list(ji.keys()))
        # 抽分隊
        team = random.choice(ji[theme]["分隊"])
        # 抽結局
        ending = random.choice(ji[theme]["結局"])
        # 抽六星
        selected_sixstar = random.choice(sixstar)

        await message.channel.send(
            f"抽取結果：\n"
            f"{theme}\n"
            f"{team}\n"
            f"{selected_sixstar}開\n"
            f"{ending}"
        )

try:
  token = os.getenv("TOKEN") or ""
  if token == "":
    raise Exception("Please add your token to the Secrets pane.")
  keep_alive()
  client.run(token)
except discord.HTTPException as e:
    if e.status == 429:
        print(
            "The Discord servers denied the connection for making too many requests"
        )
        print(
            "Get help from https://stackoverflow.com/questions/66724687/in-discord-py-how-to-solve-the-error-for-toomanyrequests"
        )
    else:
        raise e