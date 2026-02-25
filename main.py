# ceo_bot_full.py
import os, discord, random, json
from discord.ext import commands
from typing import Optional
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 載入 JSON
with open("jiname.json", "r", encoding="utf-8") as f:
    ji = json.load(f)
with open("sixstar.json", "r", encoding="utf-8") as f:
    sixstar = json.load(f)

# 處理角色池
ALL_OPERATORS = []
for job_list in sixstar.values():
    ALL_OPERATORS.extend(job_list)

TEAM_RULES = {
    "突擊戰術分隊": ["先鋒", "近衛"],
    "堡壘戰術分隊": ["重裝", "輔助"],
    "遠程戰術分隊": ["狙擊", "醫療"],
    "破壞戰術分隊": ["術師", "特種"]
}
TEAM_POOLS = {}
for team, jobs in TEAM_RULES.items():
    pool = []
    for job in jobs:
        pool.extend(sixstar[job])
    TEAM_POOLS[team] = pool

# -------------------------------
# 抽卡核心邏輯，給 hybrid command 和 on_message 共用
# -------------------------------
async def do_ceo(channel,
                     theme: Optional[str] = None,
                     team: Optional[str] = None,
                     operator: Optional[str] = None,
                     ending_number: Optional[int] = None):

    messages = []

    # 主題
    if theme in ji.keys():
        chosen_theme = theme
    else:
        if theme:
            messages.append(f"博士，並沒有`{theme}`可以打哦！將進行隨機抽取")
        chosen_theme = random.choice(list(ji.keys()))

    # 分隊
    possible_teams = ji[chosen_theme].get("分隊", [])
    if team in possible_teams:
        chosen_team = team
    else:
        if team:
            messages.append(f"博士，`{team}`並不存在於`{chosen_theme}`中哦！將進行隨機抽取")
        chosen_team = random.choice(possible_teams)

    # 幹員
    candidate_pool = TEAM_POOLS.get(chosen_team, ALL_OPERATORS)
    if operator in ALL_OPERATORS:
        chosen_operator = operator
    else:
        if operator:
            messages.append(f"博士，羅德島上並沒有幹員`{operator}`哦！將進行隨機抽取")
        chosen_operator = random.choice(candidate_pool)

    # 結局
    possible_endings = ji[chosen_theme].get("結局", [])
    chosen_ending = ""
    if possible_endings:
        if ending_number is not None:
            if 1 <= ending_number <= len(possible_endings):
                chosen_ending = possible_endings[ending_number - 1]
            else:
                messages.append(f"博士， `{chosen_theme}`中沒有`{ending_number}`結局哦！將進行隨機抽取")
                chosen_ending = random.choice(possible_endings)
        else:
            chosen_ending = random.choice(possible_endings)

    # 發送警告訊息
    if messages:
        await channel.send("\n".join(messages))

    # 發送抽取結果
    await channel.send(
        f"抽取結果：\n"
        f"{chosen_theme}\n"
        f"{chosen_team}\n"
        f"{chosen_operator}開\n"
        f"{chosen_ending}"
    )

# -------------------------------
# Hybrid command (/ceo)
# -------------------------------
@bot.hybrid_command(
    name="ceo",
    description="尊貴的羅德島CEO將協助您得償所願！（未選填將隨機抽選）"
)
async def ceo(
    ctx,
    theme: Optional[str] = commands.parameter(
    description="選擇主題",
    choices=["傀影與猩紅孤鑽", "水月與深藍之樹", "探索者的銀凇止境", "薩卡茲的無終奇語", "歲的界園誌異"]  # 這裡列出可選主題
    )
    team: Optional[str] = commands.parameter(description="分隊"),
    operator: Optional[str] = commands.parameter(description="幹員"),
    ending_number: Optional[int] = commands.parameter(description="結局編號（數字）")
):
    await do_ceo(ctx, theme, team, operator, ending_number)

# -------------------------------
# on_message 監聽訊息 (@機器人 集)
# -------------------------------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if "集" in message.content and bot.user in message.mentions:
        await do_ceo(message.channel)

    await bot.process_commands(message)  # 不要忘了這行，否則 hybrid command 不會觸發

# -------------------------------
# on_ready 事件：登入成功後同步斜槓指令
# -------------------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        # 同步所有斜槓指令到 Discord
        synced = await bot.tree.sync()
        print(f"Synced {synced} commands")
    except Exception as e:
        print("同步指令時發生錯誤:", e)

# -------------------------------
# 啟動 bot
# -------------------------------
try:
    token = os.getenv("TOKEN") or ""
    if token == "":
        raise Exception("Please add your token to the Secrets pane.")
    keep_alive()
    bot.run(token)
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