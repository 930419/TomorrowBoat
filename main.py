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
# 抽卡核心邏輯
# -------------------------------
async def do_ceo(interaction_or_channel,
                 theme: Optional[str] = None,
                 team: Optional[str] = None,
                 operator: Optional[str] = None,
                 ending_number: Optional[int] = None):

    messages = []

    # 判斷來源
    if isinstance(interaction_or_channel, discord.Interaction):
        # ⭐ 這裡只用 followup（因為 slash 已經 defer）
        async def send(msg, ephemeral=False):
            await interaction_or_channel.followup.send(msg, ephemeral=ephemeral)

        channel = interaction_or_channel.channel
    else:
        async def send(msg, ephemeral=False):
            await interaction_or_channel.send(msg)

        channel = interaction_or_channel

    # ---------- 分隊過濾 ----------
    allowed_themes = list(ji.keys())
    chosen_team = None

    if team:
        team = team.strip()

    if team:
        # 精準匹配
        filtered = [
            t for t, info in ji.items()
            if any(team == x.strip() for x in info.get("分隊", []))
        ]

        # 模糊匹配
        if not filtered:
            filtered = [
                t for t, info in ji.items()
                if any(team in x.strip() or x.strip() in team for x in info.get("分隊", []))
            ]

        # 簡寫
        if not filtered:
            abbrev_map = {
                "狙醫": "遠程戰術分隊",
                "近鋒": "突擊戰術分隊",
                "重輔": "堡壘戰術分隊",
                "術特": "破壞戰術分隊",
            }

            mapped = abbrev_map.get(team)
            if mapped:
                filtered = [
                    t for t, info in ji.items()
                    if mapped in info.get("分隊", [])
                ]
                team = mapped

        if filtered:
            allowed_themes = filtered
        else:
            messages.append(f"博士，沒有任何主題包含 `{team}` 哦！將隨機抽取分隊")
            team = None

    # ---------- 主題 ----------
    if theme is None or theme == "random" or theme not in allowed_themes:
        if theme != "random":
            messages.append(f"博士，`{theme}` 不存在或不適用，將隨機抽取主題")
        chosen_theme = random.choice(allowed_themes)
    else:
        chosen_theme = theme

    # ---------- 分隊 ----------
    possible_teams = ji[chosen_theme].get("分隊", [])

    if team and team in possible_teams:
        chosen_team = team
    else:
        chosen_team = random.choice(possible_teams) if possible_teams else ""
        if team:
            messages.append(f"博士，`{team}` 不適用於 `{chosen_theme}`，將隨機抽取分隊")

    # ---------- 幹員 ----------
    candidate_pool = TEAM_POOLS.get(chosen_team, ALL_OPERATORS)

    if operator in ALL_OPERATORS:
        chosen_operator = operator
    else:
        if operator:
            messages.append(f"博士，羅德島上沒有幹員 `{operator}` 哦！將隨機抽取幹員")
        chosen_operator = random.choice(candidate_pool)

    # ---------- 結局 ----------
    possible_endings = ji[chosen_theme].get("結局", [])

    if ending_number is not None:
        if 1 <= ending_number <= len(possible_endings):
            chosen_ending = possible_endings[ending_number - 1]
        else:
            messages.append(f"博士，`{chosen_theme}` 沒有結局 `{ending_number}`，將隨機抽取結局")
            chosen_ending = random.choice(possible_endings) if possible_endings else ""
    else:
        chosen_ending = random.choice(possible_endings) if possible_endings else ""

    # ---------- 發送 ----------
    if messages:
        await send("\n".join(messages))

    await send(
        f"抽取結果：\n"
        f"{chosen_theme}\n"
        f"{chosen_team}\n"
        f"{chosen_operator} 開\n"
        f"{chosen_ending}"
    )


# -------------------------------
# Slash command
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
    # ⭐⭐⭐ 關鍵修正
    await interaction.response.defer()

    await do_ceo(
        interaction,
        theme.value,
        team=team,
        operator=operator,
        ending_number=ending_number
    )


# -------------------------------
# @機器人 集
# -------------------------------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if "集" in message.content and bot.user in message.mentions:
        await do_ceo(message.channel)

    await bot.process_commands(message)


# -------------------------------
# 啟動
# -------------------------------
try:
    token = os.getenv("TOKEN") or ""
    if token == "":
        raise Exception("Please add your token to the Secrets pane.")

    keep_alive()
    bot.run(token)

except discord.HTTPException as e:
    if e.status == 429:
        print("Too many requests.")
    else:
        raise e