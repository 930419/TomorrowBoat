import os, discord, random, json

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)

# 從 JSON 載入集成資料
with open("jiname.json", "r", encoding="utf-8") as f:
    ji = json.load(f)

# 從 JSON 載入六星
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

    # 判斷訊息開頭是 "集"，且有標註機器人
    if "集" in content and client.user in message.mentions:
        # 先抽外層主題
        theme = random.choice(list(ji.keys()))
        # 再抽內層分隊
        team = random.choice(ji[theme])
        # 抽開局六星
        selected_sixstar = random.choice(sixstar)
        # 抽結局
        selected_out = random.randint(1,5)
        await message.channel.send(
            f"抽取結果：\n{theme}\n{team}\n{selected_sixstar}開\n{selected_out}結局"
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