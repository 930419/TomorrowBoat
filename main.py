# ceo_bot_full.py
import os, discord, random, json
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice
from typing import Optional
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

# -------------------------------
# 自訂 Bot class
# -------------------------------
class CEO_Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # 這裡只會觸發一次，用來同步斜槓指令
        try:
            synced = await self.tree.sync()
            print(f"已同步 {synced} 個斜槓指令")
        except Exception as e:
            print("同步斜槓指令時發生錯誤:", e)

bot = CEO_Bot()

# -------------------------------
# 載入 JSON
# -------------------------------
with open("jiname.json", "r", encoding="utf-8") as f:
    ji = json.load(f)
with open("sixstar.json", "r", encoding="utf-8") as f:
    sixstar = json.load(f)

# -------------------------------
# 處理角色池
# -------------------------------
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
# 抽卡核心邏輯（保留指定分隊）
# -------------------------------
async def do_ceo(interaction_or_channel,
                 theme: Optional[str] = None,
                 team: Optional[str] = None,
                 operator: Optional[str] = None,
                 ending_number: Optional[int] = None):

    messages = []

    # 判斷是 Interaction 還是 TextChannel
    if isinstance(interaction_or_channel, discord.Interaction):
        async def send(msg, ephemeral=False):
            if not interaction_or_channel.response.is_done():
                await interaction_or_channel.response.send_message(msg, ephemeral=ephemeral)
            else:
                await interaction_or_channel.followup.send(msg, ephemeral=ephemeral)
        channel = interaction_or_channel.channel
    else:
        async def send(msg, ephemeral=False):
            await interaction_or_channel.send(msg)
        channel = interaction_or_channel

    # ---------- 檢查指定分隊是否存在（精準 + 模糊 + 簡寫） ----------
    allowed_themes = list(ji.keys())
    chosen_team = None

    if team:
        team = team.strip()  # 去掉前後空白或不可見字符

    # 精準匹配
    filtered = [t for t, info in ji.items() if any(team == x.strip() for x in info.get("分隊", []))]

    if not filtered:
        # 模糊匹配（部分字串匹配）
        filtered = [t for t, info in ji.items() if any(team in x.strip() or x.strip() in team for x in info.get("分隊", []))]

    if not filtered:
        # 簡寫對應
        abbrev_map = {
            "狙醫": "遠程戰術分隊",
            "近鋒": "突擊戰術分隊",
            "重輔": "堡壘戰術分隊",
            "術特": "破壞戰術分隊",
            "代理人": "代理人分隊"  # 加上你提到的簡寫
        }
        mapped = abbrev_map.get(team)
        if mapped:
            filtered = [t for t, info in ji.items() if mapped in info.get("分隊", [])]
            team = mapped  # 直接把 team 改成完整名稱

    if filtered:
        allowed_themes = filtered
    else:
        messages.append(f"博士，沒有任何主題包含`{team}`哦! 將隨機抽取分隊")
        team = None

    # ---------- 主題抽取 ----------
    if theme == "random" or theme not in allowed_themes:
        if theme != "random":
            messages.append(f"博士，`{theme}`不適用於指定分隊或不存在，將隨機抽取主題")
        chosen_theme = random.choice(allowed_themes)
    else:
        chosen_theme = theme

    # ---------- 分隊抽取 ----------
    possible_teams = ji[chosen_theme].get("分隊", [])
    if team and team in possible_teams:
        chosen_team = team
    else:
        chosen_team = random.choice(possible_teams) if possible_teams else ""
        if team:
            messages.append(f"博士，`{team}`不適用於`{chosen_theme}`哦！將隨機抽取分隊")

    # ---------- 幹員抽取 ----------
    candidate_pool = TEAM_POOLS.get(chosen_team, ALL_OPERATORS)
    if operator in ALL_OPERATORS:
        chosen_operator = operator
    else:
        if operator:
            messages.append(f"博士，羅德島上沒有幹員`{operator}`哦！將隨機抽取幹員")
        chosen_operator = random.choice(candidate_pool)

    # ---------- 結局抽取 ----------
    possible_endings = ji[chosen_theme].get("結局", [])
    if ending_number is not None:
        if 1 <= ending_number <= len(possible_endings):
            chosen_ending = possible_endings[ending_number - 1]
        else:
            messages.append(f"博士，`{chosen_theme}`中沒有結局`{ending_number}`哦！將隨機抽取結局")
            chosen_ending = random.choice(possible_endings) if possible_endings else ""
    else:
        chosen_ending = random.choice(possible_endings) if possible_endings else ""

    # 發送提示訊息
    if messages:
        await send("\n".join(messages))

    # 發送抽取結果
    await send(
        f"抽取結果：\n"
        f"{chosen_theme}\n"
        f"{chosen_team}\n"
        f"{chosen_operator}開\n"
        f"{chosen_ending}"
    )

# -------------------------------
# Slash command /ceo（只下拉主題）
# -------------------------------
@bot.tree.command(
    name="ceo",
    description="尊貴的羅德島CEO將協助您得償所願！（未選填將隨機抽選）"
)
@app_commands.choices(
    theme=[
        Choice(name="傀影與猩紅孤鑽", value="傀影與猩紅孤鑽"),
        Choice(name="水月與深藍之樹", value="水月與深藍之樹"),
        Choice(name="探索者的銀凇止境", value="探索者的銀凇止境"),
        Choice(name="薩卡茲的無終奇語", value="薩卡茲的無終奇語"),
        Choice(name="歲的界園誌異", value="歲的界園誌異"),
        Choice(name="隨機", value="random"),
    ]
)
async def ceo(
    interaction: discord.Interaction,
    theme: Choice[str],
    team: Optional[str] = None,
    operator: Optional[str] = None,
    ending_number: Optional[int] = None
):
    await do_ceo(interaction, theme.value, team=team, operator=operator, ending_number=ending_number)

# -------------------------------
# on_message 監聽訊息 (@機器人 集)
# -------------------------------
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if "集" in message.content and bot.user in message.mentions:
        await do_ceo(message.channel)
    await bot.process_commands(message)

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
        print("The Discord servers denied the connection for making too many requests")
        print("Get help from https://stackoverflow.com/questions/66724687/in-discord-py-how-to-solve-the-error-for-toomanyrequests")
    else:
        raise e