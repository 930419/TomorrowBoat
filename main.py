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

@bot.hybrid_command(name="ceo", description="尊貴的羅德島CEO將協助您得償所願！（未選填將隨機抽選）")
async def ceo(
    ctx,
    theme: Optional[str] = commands.parameter(
        description="主題"
    ),
    team: Optional[str] = commands.parameter(
        description="分隊"
    ),
    operator: Optional[str] = commands.parameter(
        description="幹員"
    ),
    ending_number: Optional[int] = commands.parameter(
        description="結局編號（數字）"
    )
):
    messages = []

    # 主題
    if theme in ji.keys():
        chosen_theme = theme
    else:
        if theme:
            messages.append(f"博士，並沒有`{theme}`可以打哦!將進行隨機抽取")
        chosen_theme = random.choice(list(ji.keys()))

    # 分隊
    possible_teams = ji[chosen_theme].get("分隊", [])
    if team in possible_teams:
        chosen_team = team
    else:
        if team:
            messages.append(f"博士，`{team}`並不存在於`{chosen_theme}`中哦！將進行隨機抽取")
        if possible_teams:
            chosen_team = random.choice(possible_teams)
        else:
            chosen_team = random.choice(list(TEAM_POOLS.keys()))

    # 幹員
    candidate_pool = TEAM_POOLS.get(chosen_team, ALL_OPERATORS)
    if operator in ALL_OPERATORS:
        chosen_operator = operator
    else:
        if operator:
            messages.append(f"博士，羅德島上並沒有幹員`{operator}`哦！將進行隨機抽取")
        chosen_operator = random.choice(candidate_pool)

    # 結局（數字選）
    possible_endings = ji[chosen_theme].get("結局", [])
    chosen_ending = "未知結局"
    if possible_endings:
        if ending_number is not None:
            if 1 <= ending_number <= len(possible_endings):
                chosen_ending = possible_endings[ending_number - 1]
            else:
                messages.append(f"博士， `{chosen_theme}`中沒有`{ending_number}`哦！將進行隨機抽取")
                chosen_ending = random.choice(possible_endings)
        else:
            chosen_ending = random.choice(possible_endings)

    # 先把警告訊息發給使用者
    if messages:
        await ctx.send("\n".join(messages))

    # 發送抽取結果
    await ctx.send(
        f"抽取結果：\n"
        f"{chosen_theme}\n"
        f"{chosen_team}\n"
        f"{chosen_operator}開\n"
        f"{chosen_ending}"
    )

# 啟動 bot
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