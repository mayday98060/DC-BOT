import os
import db
import sys
import json
import math
import random
import psutil
import atexit
import locale
import discord
import sqlite3
import asyncio
import datetime
import calendar
import requests
import subprocess
from queue import Queue
from typing import Optional
from langdetect import detect
from collections import Counter
from discord import app_commands
from keep_alive import keep_alive
from discord.ui import Select, View
from question_pool import question_pool
from discord.ext import commands, tasks
from discord.ui import Modal, TextInput
from discord import FFmpegPCMAudio, PCMVolumeTransformer
from database2 import nirvana_costs, body_training_costs
from database import song_list, fortune_rewards, items, item_prices, enemies
from mafia42 import class_skills, class_skills_3, class_skills_4_to_6, class_weights

intents = discord.Intents.default()
intents.message_content = True
intents.typing = False
intents.presences = False
bot = commands.Bot(command_prefix="/", intents=intents)
bot.remove_command("help")
restart_message_id = None
start_time = datetime.datetime.now()
IMMORTAL_KING_ID = 887261477919133739
song_queue = Queue()
command_lock = {}
user_stats = {}
battle_states = {}
profession_image_folder = "images_mafia42"
skill_icon_folder = "icons_mafia42"
db.init_db()
conn = db.get_conn()
cursor = db.get_cursor()

#顯示機器人名稱，並定義在discord上的狀態
@bot.event
async def on_ready():
    print(f"目前登入身份 --> {bot.user}")
    activity=discord.CustomActivity("衝破空間壁障中~")
    #online,offline,idle,dnd,invisible
    await bot.change_presence(status=discord.Status.online, activity=activity)
    try:
        synced = await bot.tree.sync()
        print(f"✅ 成功同步 {len(synced)} 個指令！")
    except Exception as e:
        print(f"❌ 無法同步指令: {e}")

@bot.tree.command(name="help", description="指令列表")
async def slash_help(interaction: discord.Interaction):
    help_embed = discord.Embed(title="🌸指令列表🌸",
                               description="",
                               color=discord.Color.green())
    help_embed.add_field(name="☯入道☯", value="成為修煉者", inline=True)
    help_embed.add_field(name="😺猜拳😺", value="跟電腦玩猜拳(消耗10靈石)", inline=True)
    help_embed.add_field(name="😺play1A2B😺", value="玩1A2B", inline=True)
    help_embed.add_field(name="🔊加入語音🔊", value="機器人加入語音聊天室", inline=True)
    help_embed.add_field(name="🔈離開語音🔈", value="機器人離開語音聊天室", inline=True)
    help_embed.add_field(name="▶️播放 歌曲編號▶️", value="播放歌曲(請先加入語音)", inline=True)
    help_embed.add_field(name="🔀隨機播放🔀", value="歌單隨機選音樂", inline=True)
    help_embed.add_field(name="♪⏸️暫停⏸️", value="停止音樂", inline=True)
    help_embed.add_field(name="▶️繼續▶️", value="繼續上次播放的歌曲", inline=True)
    help_embed.add_field(name="🔊調整音量 數值🔊",
                         value="音量調整範圍(0.0~2.0)",
                         inline=True)
    help_embed.add_field(name="♪歌單♪", value="歌曲清單", inline=True)
    help_embed.add_field(name="♪查看播放順序♪", value="歌曲連續播放的順序", inline=True)
    help_embed.add_field(name="📖狀態📖", value="查看機器人資訊", inline=True)
    help_embed.add_field(name="📖修仙世界📖", value="修仙指南", inline=True)
    help_embed.add_field(name="🏆rank🏆", value="排行榜列表", inline=True)
    help_embed.add_field(name="❓問答遊戲❓", value="答案四選一", inline=True)

    await interaction.response.send_message(embed=help_embed, ephemeral=True)

@bot.tree.command(name="修仙世界", description="修仙指南")
async def slash_修仙世界(interaction: discord.Interaction):
    修仙世界 = discord.Embed(title="🌸修仙指南🌸",
                         description="歡迎您來到進步飛速的未來修仙世界",
                         color=discord.Color.blue())
    修仙世界.add_field(name="⏰/感悟⏰", value="每日簽到(UTC +8)", inline=False)
    修仙世界.add_field(name="🔮/占卜🔮", value="每日算命(UTC +8)", inline=False)
    修仙世界.add_field(name="🪪/查看修為🪪", value="查看個人資訊", inline=False)
    修仙世界.add_field(name="🪪/查看能量🪪", value="查看當前能量", inline=False)
    修仙世界.add_field(name="☯/渡劫☯", value="提升境界層數", inline=False)
    修仙世界.add_field(name="☯/煉體☯", value="提升肉身境界階級", inline=False)
    修仙世界.add_field(name="☯/靈石☯", value="查看靈石數量", inline=False)
    修仙世界.add_field(name="⚔️/pve⚔️", value="打怪", inline=False)
    修仙世界.add_field(name="🔎/探索🔎", value="探索列表", inline=False)
    修仙世界.add_field(name="🏪/商店🏪", value="商品列表(買了即用)", inline=False)

    await interaction.response.send_message(embed=修仙世界, ephemeral=True)

def use_item(user_id, item_name, in_combat):
    try:
        cursor.execute(
            "SELECT quantity, effect, use_restriction FROM inventory WHERE user_id = ? AND item_name = ?",
            (user_id, item_name),
        )
        result = cursor.fetchone()

        if not result:
            return "你沒有這個道具！"

        quantity, effect, use_restriction = result

        if quantity <= 0:
            return "你沒有足夠的道具！"

        if in_combat and use_restriction == 'non_combat':
            return "這個道具只能在戰鬥外使用！"
        if not in_combat and use_restriction == 'combat':
            return "這個道具只能在戰鬥中使用！"

        cursor.execute(
            "UPDATE inventory SET quantity = quantity - 1 WHERE user_id = ? AND item_name = ?",
            (user_id, item_name),
        )

        if effect == "heal":
            cursor.execute(
                "SELECT health, current_health FROM users WHERE user_id = ?",
                (user_id, ))
            max_health, current_health = cursor.fetchone()
            new_health = min(current_health + 50, max_health)
            cursor.execute(
                "UPDATE users SET current_health = ? WHERE user_id = ?",
                (new_health, user_id))
        elif effect == "buff_attack":
            cursor.execute("SELECT temp_attack FROM users WHERE user_id = ?",
                           (user_id, ))
            temp_attack = cursor.fetchone()[0]
            new_temp_attack = temp_attack + 10
            cursor.execute(
                "UPDATE users SET temp_attack = ? WHERE user_id = ?",
                (new_temp_attack, user_id))
        elif effect == "buff_defense":
            cursor.execute("SELECT temp_defense FROM users WHERE user_id = ?",
                           (user_id, ))
            temp_defense = cursor.fetchone()[0]
            new_temp_defense = temp_defense + 5
            cursor.execute(
                "UPDATE users SET temp_defense = ? WHERE user_id = ?",
                (new_temp_defense, user_id))
        elif effect == "gain_cultivation":
            cursor.execute("SELECT cultivation FROM users WHERE user_id = ?",
                           (user_id, ))
            current_cultivation = cursor.fetchone()[0]
            new_cultivation = current_cultivation + 100
            cursor.execute(
                "UPDATE users SET cultivation = ? WHERE user_id = ?",
                (new_cultivation, user_id))
        elif effect == "gain_quench":
            cursor.execute("SELECT quench FROM users WHERE user_id = ?",
                           (user_id, ))
            current_quench = cursor.fetchone()[0]
            new_quench = current_quench + 100
            cursor.execute("UPDATE users SET quench = ? WHERE user_id = ?",
                           (new_quench, user_id))
        else:
            return "未知效果的道具無法使用！"

        conn.commit()
        return f"你成功使用了 {item_name}！"

    except Exception as e:
        import traceback
        traceback.print_exc()
        return "發生錯誤，無法使用道具！"

def end_combat(user_id):
    cursor.execute(
        "UPDATE users SET temp_attack = 0, temp_defense = 0 WHERE user_id = ?",
        (user_id, ),
    )
    conn.commit()
    return "戰鬥結束，臨時加成已清除！"

class PurchaseView(View):

    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.add_item(PurchaseSelect(user_id))

class PurchaseSelect(Select):

    def __init__(self, user_id):
        self.user_id = user_id
        options = [
            discord.SelectOption(
                label=item_name,
                description=
                f"價格：{item_prices[item_name]} 靈石 | 類型：{items[item_name]['type']}",
                value=item_name,
            ) for item_name in items
        ]
        super().__init__(
            placeholder="選擇你想購買的道具...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        item_name = self.values[0]

        await interaction.response.edit_message(
            content=f"你選擇了 **{item_name}**，請選擇購買數量：",
            view=QuantitySelectView(self.user_id, item_name),
        )

class QuantitySelectView(View):

    def __init__(self, user_id, item_name):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.item_name = item_name
        self.add_item(QuantitySelect(user_id, item_name))

class QuantitySelect(Select):

    def __init__(self, user_id, item_name):
        self.user_id = user_id
        self.item_name = item_name
        options = [
            discord.SelectOption(label=str(i),
                                 description=f"購買 {i} 個",
                                 value=str(i)) for i in range(1, 11)
        ]
        super().__init__(
            placeholder="選擇購買數量...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        quantity = int(self.values[0])

        user_id = self.user_id
        item_name = self.item_name

        price = item_prices[item_name]
        total_cost = price * quantity

        cursor.execute("SELECT spirit_stone FROM users WHERE user_id = ?",
                       (user_id, ))
        result = cursor.fetchone()
        if not result or result[0] < total_cost:
            await interaction.response.send_message(
                f"你的靈石不足！購買 **{item_name}** {quantity} 個需要 {total_cost} 靈石。",
                ephemeral=True
            )
            return

        cursor.execute(
            "UPDATE users SET spirit_stone = spirit_stone - ? WHERE user_id = ?",
            (total_cost, user_id),
        )
        cursor.execute(
            """
            INSERT INTO inventory (user_id, item_name, quantity)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, item_name)
            DO UPDATE SET quantity = quantity + ?;
            """,
            (user_id, item_name, quantity, quantity),
        )
        conn.commit()

        await interaction.response.send_message(
            f"成功購買 **{item_name}** {quantity} 個！花費了 {total_cost} 靈石。",
            ephemeral=True,
        )

@bot.tree.command(name="購買道具", description="使用靈石購買")
async def 商店(interaction: discord.Interaction):
    user_id = interaction.user.id
    try:
        cursor.execute("SELECT spirit_stone FROM users WHERE user_id = ?",
                       (user_id, ))
        result = cursor.fetchone()
        if not result:
            await interaction.response.send_message("你還不是修煉者！使用 /入道 指令進入修仙之旅。",
                                                    ephemeral=True)
            return

        view = PurchaseView(user_id)
        await interaction.response.send_message("選擇你想購買的道具：",
                                                view=view,
                                                ephemeral=True)
    except Exception as e:
        import traceback
        traceback.print_exc()
        await interaction.response.send_message("發生錯誤，請稍後再試！", ephemeral=True)

@bot.tree.command(name="使用道具", description="在戰鬥中或戰鬥外使用道具")
async def 使用道具(interaction: discord.Interaction):
    user_id = interaction.user.id
    in_combat = user_id in battle_states

    cursor.execute(
        "SELECT item_name, quantity, use_restriction FROM inventory WHERE user_id = ? AND quantity > 0",
        (user_id, ))
    inventory_items = cursor.fetchall()

    if not inventory_items:
        await interaction.response.send_message("你沒有任何可用的道具！", ephemeral=True)
        return

    options = [
        discord.SelectOption(label=item[0],
                             description=f"數量: {item[1]}",
                             value=item[0]) for item in inventory_items
        if item[2] in ["both", "combat" if in_combat else "non_combat"]
    ]

    if not options:
        await interaction.response.send_message("你目前沒有可用的道具！", ephemeral=True)
        return

    view = UseItemView(user_id, options, in_combat=in_combat)
    await interaction.response.send_message("選擇你要使用的道具：",
                                            view=view,
                                            ephemeral=True)

class UseItemView(discord.ui.View):

    def __init__(self, user_id, options, in_combat):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.in_combat = in_combat  # 添加 in_combat 屬性
        self.add_item(UseItemSelect(user_id, options, in_combat))

class UseItemSelect(discord.ui.Select):

    def __init__(self, user_id, options, in_combat):
        self.user_id = user_id
        self.in_combat = in_combat
        super().__init__(placeholder="選擇一個道具使用...", options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("這不是你的道具，無法操作！",
                                                    ephemeral=True)
            return

        item_name = self.values[0]
        result_message = use_item(self.user_id, item_name,
                                  self.in_combat)  # 傳遞 in_combat 狀態

        await interaction.response.send_message(result_message, ephemeral=True)

@bot.command()
async def rank(ctx):
    rank = discord.Embed(title="🌸排行榜清單🌸",
                         description="",
                         color=discord.Color.gold())
    rank.add_field(name="🏆/境界rank🏆", value="境界層數排行榜", inline=False)
    rank.add_field(name="🏆/問答遊戲rank🏆", value="問答遊戲排行榜", inline=False)

    await ctx.send(embed=rank, ephemeral=True)

@bot.tree.command(name="狀態", description="查看機器人狀態")
async def 狀態(interaction: discord.Interaction):
    server_count = len(bot.guilds)

    def get_user_count():
        cursor.execute("SELECT COUNT(*) FROM users")
        result = cursor.fetchone()
        if result:
            user_count = result[0]
            return user_count
        else:
            return 0

    user_count = get_user_count()

    uptime = datetime.datetime.now() - start_time

    memory_info = psutil.virtual_memory()
    total_memory = memory_info.total // (1024 * 1024)
    used_memory = memory_info.used // (1024 * 1024)

    embed = discord.Embed(title="🌸小新#6500🌸",
                          description="版本:1.0.3",
                          color=discord.Color.pink())
    embed.add_field(name="💻伺服器💻", value=f"{server_count}", inline=False)
    embed.add_field(name="👤成員👤", value=f"{user_count}", inline=False)
    embed.add_field(name="⏰已運行時長⏰", value=f"{uptime}", inline=False)
    embed.add_field(name="🖥️開機時間🖥️", value=f"{start_time}", inline=False)
    embed.add_field(name="💾記憶體狀況💾",
                    value=f"{memory_info.percent}%",
                    inline=False)
    embed.add_field(name="💾總內存💾", value=f"{total_memory}MB", inline=False)
    embed.add_field(name="💾已使用內存💾", value=f"{used_memory}MB", inline=False)
    embed.add_field(name="✶1.1.0更新內容✶", value=f"將傳統指令轉換成slash指令", inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


def get_user_data(user_id):
    if user_id not in user_stats:
        user_stats[user_id] = {
            "total_draws": 0,
            "tier_counts": {
                3: 0,
                4: 0,
                5: 0,
                6: 0
            }
        }
    return user_stats[user_id]

def get_profession_image(profession_name):
    image_path = os.path.join(profession_image_folder,
                              f"{profession_name}.jpg")
    if os.path.exists(image_path):
        return image_path
    return None

def get_skill_icon(skill_name):
    icon_path = os.path.join(skill_icon_folder, f"{skill_name}.jpg")
    if os.path.exists(icon_path):
        return icon_path
    return None

@bot.tree.command(name="抽卡", description="mafia42抽卡")
async def slash_抽卡(interaction: discord.Interaction):
    user_id = interaction.user.id
    user_data = get_user_data(user_id)

    profession = random.choices(list(class_weights.keys()),
                                weights=list(class_weights.values()),
                                k=1)[0]

    tier_probabilities = [0.89091, 0.09899, 0.01, 0.0001]
    tier = random.choices([3, 4, 5, 6], weights=tier_probabilities, k=1)[0]

    user_data["total_draws"] += 1
    user_data["tier_counts"][tier] += 1

    skills = {}

    for level in range(1, min(3, tier + 1)):
        skills[level] = class_skills[profession][level - 1]

    if tier >= 3:
        skills[3] = random.choice(class_skills_3[profession])

    if tier >= 4:
        available_skills = class_skills_4_to_6[profession]
        selected_skills = random.sample(available_skills, k=tier - 3)
        for level, skill in enumerate(selected_skills, start=4):
            skills[level] = skill

    card_embed = discord.Embed(title="🎴 抽卡结果 🎴",
                               description="抽取的卡片内容如下:",
                               color=discord.Color.blue())
    card_embed.add_field(name="職業", value=profession, inline=False)
    card_embed.add_field(name="階級", value=f"{tier}階", inline=False)

    files = []

    profession_image_path = get_profession_image(profession)
    if profession_image_path and os.path.exists(profession_image_path):
        files.append(
            discord.File(profession_image_path,
                         filename=os.path.basename(profession_image_path)))
        card_embed.set_thumbnail(
            url=f"attachment://{os.path.basename(profession_image_path)}")

    skills_info = ""
    skill_files = []
    for level, skill in skills.items():
        icon_path = get_skill_icon(skill)
        if icon_path and os.path.exists(icon_path):
            skill_files.append(
                discord.File(icon_path, filename=f"icon_{level}.jpg"))
            skills_info += f"**{level}階**:  {skill}\n"
        else:
            skills_info += f"**{level}階**: {skill}\n"

    card_embed.add_field(name="技能", value=skills_info, inline=False)

    files.extend(skill_files)

    await interaction.response.send_message(embed=card_embed, files=files, ephemeral=True)

@bot.tree.command(name="抽卡統計", description="查看自己的抽卡统计")
async def slash_抽卡統計(interaction: discord.Interaction):
    user_id = interaction.user.id
    user_data = get_user_data(user_id)

    stats_embed = discord.Embed(title="📊 抽卡統計 📊",
                                description="你的抽卡統計如下：",
                                color=discord.Color.green())
    stats_embed.add_field(name="總抽卡次數",
                          value=str(user_data["total_draws"]),
                          inline=False)

    tier_counts = user_data["tier_counts"]
    tier_info = "\n".join(
        [f"{tier}階: {count} 張" for tier, count in tier_counts.items()])
    stats_embed.add_field(name="階級分佈", value=tier_info, inline=False)

    await interaction.response.send_message(embed=stats_embed)

def clean_up_cache():
    global restart_message_id
    if restart_message_id:
        restart_message_id = None

@bot.tree.command(name="重啟", description="重新啟動")
async def slash_重啟(interaction: discord.Interaction):
    if interaction.user.id == IMMORTAL_KING_ID:
        await interaction.response.send_message("世界意志重啟中...", ephemeral=True)

        atexit.register(clean_up_cache)

        await interaction.followup.send("世界意志重啟成功！", ephemeral=True)
        subprocess.Popen([sys.executable, "bot.py"])
        await bot.close()
    else:
        await interaction.response.send_message("世界基礎規則，凡人無法撼動。", ephemeral=True)

@bot.command()
async def 關閉(ctx):
    if ctx.author.id == IMMORTAL_KING_ID:
        restart_message = await ctx.send('世界意志即將關閉...', ephemeral=True)
        await ctx.message.delete()
        await restart_message.delete()
        await ctx.send("世界意志關閉完成！", ephemeral=True)
        await bot.close()
    else:
        await ctx.send('世界基礎規則，凡人無法撼動。', ephemeral=True)

@bot.tree.command(name="加入語音", description="讓機器人加入您的語音頻道")
async def 加入語音(interaction: discord.Interaction):
    if interaction.user.voice is None:
        await interaction.response.send_message("您不在任何語音頻道中！", ephemeral=True)
        return

    channel = interaction.user.voice.channel
    await channel.connect()
    await interaction.response.send_message(f"已加入語音頻道：{channel.name}", ephemeral=True)

@bot.tree.command(name="離開語音", description="讓機器人離開語音頻道")
async def 離開語音(interaction: discord.Interaction):
    if interaction.guild.voice_client is None:
        await interaction.response.send_message("目前沒有連接到語音頻道！", ephemeral=True)
        return

    await interaction.guild.voice_client.disconnect()
    await interaction.response.send_message("已離開語音頻道。", ephemeral=True)

@bot.tree.command(name="播放", description="從播放清單選擇歌曲")
async def 播放(interaction: discord.Interaction):
    items_per_page = 25
    pages = math.ceil(len(song_list) / items_per_page)

    def get_options(page):
        start_index = page * items_per_page
        end_index = start_index + items_per_page
        return [
            discord.SelectOption(label=f"{key}: {value}", value=str(key))
            for key, value in list(song_list.items())[start_index:end_index]
        ]

    class SongSelectView(View):

        def __init__(self):
            super().__init__()
            self.current_page = 0
            self.update_select_menu()

        def update_select_menu(self):
            self.clear_items()
            options = get_options(self.current_page)
            select = discord.ui.Select(placeholder="選擇一首歌曲",
                                       options=options,
                                       custom_id="select_song")
            select.callback = self.select_callback
            self.add_item(select)

            if pages > 1:
                prev_button = discord.ui.Button(
                    label="上一頁", style=discord.ButtonStyle.primary)
                prev_button.callback = self.previous_page
                next_button = discord.ui.Button(
                    label="下一頁", style=discord.ButtonStyle.primary)
                next_button.callback = self.next_page

                self.add_item(prev_button)
                self.add_item(next_button)

        async def select_callback(self,
                                  select_interaction: discord.Interaction):
            song_number = int(select_interaction.data['values'][0])
            mp3_file = os.path.join("music", song_list[song_number])
            if os.path.exists(mp3_file):
                song_queue.put((mp3_file, 0.5))  # 預設音量為 0.5
                song_name = os.path.basename(mp3_file)
                await select_interaction.response.send_message(
                    f"{song_name} 已加入播放隊列", ephemeral=True)

                if not interaction.guild.voice_client.is_playing():
                    await play_next_song(interaction)
            else:
                await select_interaction.response.send_message(
                    f"找不到歌曲 {song_number}", ephemeral=True)

        async def previous_page(self, button_interaction: discord.Interaction):
            if self.current_page > 0:
                self.current_page -= 1
                self.update_select_menu()
                await button_interaction.response.edit_message(view=self)

        async def next_page(self, button_interaction: discord.Interaction):
            if self.current_page < pages - 1:
                self.current_page += 1
                self.update_select_menu()
                await button_interaction.response.edit_message(view=self)

    view = SongSelectView()
    await interaction.response.send_message("請選擇一首歌曲：",
                                            view=view,
                                            ephemeral=True)

async def play_next_song(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if not song_queue.empty():
        mp3_file, volume = song_queue.get()

        # 1) 先建立 FFmpegPCMAudio
        source = FFmpegPCMAudio(executable="ffmpeg", source=mp3_file)
        # 2) 再用 PCMVolumeTransformer 包起來，初始音量 = volume
        transformed_source = PCMVolumeTransformer(source, volume=volume)

        # 3) 播放 transformed_source
        voice_client.play(
            transformed_source,
            after=lambda e: asyncio.run_coroutine_threadsafe(
                play_next_song(interaction), bot.loop),
        )
    else:
        await interaction.channel.send("播放隊列已清空！", ephemeral=True)

@bot.tree.command(name="查看播放順序", description="查看當前播放隊列")
async def 查看播放順序(interaction: discord.Interaction):
    if song_queue.empty():
        await interaction.response.send_message("沒有正在排隊的歌曲。", ephemeral=True)
    else:
        queued_songs = list(song_queue.queue)
        song_list_message = "\n".join([
            f"{i + 1}. {os.path.basename(song[0])} (音量: {song[1]})"
            for i, song in enumerate(queued_songs)
        ])
        await interaction.response.send_message(f"歌曲播放順序：\n{song_list_message}", ephemeral=True
                                                )

@bot.tree.command(name="調整音量", description="調整當前播放的音量0.0~2.0")
async def 調整音量(interaction: discord.Interaction, volume: float):
    if 0.0 <= volume <= 2.0:
        voice_client = interaction.guild.voice_client
        if voice_client.is_playing():
            voice_client.source.volume = volume
            await interaction.response.send_message(f"音量已調整為 {volume}", ephemeral=True)
        else:
            await interaction.response.send_message("沒有正在播放的歌曲",
                                                    ephemeral=True)
    else:
        await interaction.response.send_message("請輸入有效的音量範圍（0.0 到 2.0）",
                                                ephemeral=True)

@bot.tree.command(name="暫停", description="暫停當前播放的歌曲")
async def 暫停(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client.is_playing():
        voice_client.pause()
        await interaction.response.send_message("歌曲已暫停", ephemeral=True)
    else:
        await interaction.response.send_message("沒有正在播放的歌曲", ephemeral=True)

@bot.tree.command(name="繼續", description="繼續播放暫停的歌曲")
async def 繼續(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client.is_paused():
        voice_client.resume()
        await interaction.response.send_message("歌曲已繼續播放", ephemeral=True)
    else:
        await interaction.response.send_message("歌曲並未暫停", ephemeral=True)

@bot.tree.command(name="隨機播放", description="隨機播放一首歌曲")
async def 隨機播放(interaction: discord.Interaction):
    if not song_list:
        await interaction.response.send_message("歌曲列表為空", ephemeral=True)
        return

    voice_client = interaction.guild.voice_client
    if voice_client.is_playing():
        await interaction.response.send_message("請先停止正在播放的歌曲再隨機播放",
                                                ephemeral=True)
        return

    random_song = random.choice(list(song_list.values()))
    mp3_file = os.path.join("music", random_song)

    if os.path.exists(mp3_file):
        source = FFmpegPCMAudio(executable="ffmpeg", source=mp3_file)
        transformed_source = PCMVolumeTransformer(source, volume=0.5)
        voice_client.play(transformed_source)
        await interaction.response.send_message(f"已隨機播放歌曲: {random_song}", ephemeral=True)
    else:
        await interaction.response.send_message(f"找不到歌曲 {random_song}",
                                                ephemeral=True)

@bot.tree.command(name="循環播放", description="啟動循環播放模式")
async def 循環播放(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client

    while True:
        random_song = random.choice(list(song_list.values()))
        mp3_file = os.path.join("music", random_song)

        if os.path.exists(mp3_file):
            source = FFmpegPCMAudio(executable="ffmpeg", source=mp3_file)
            transformed_source = PCMVolumeTransformer(source, volume=0.5)
            voice_client.play(transformed_source)

            while voice_client.is_playing():
                await asyncio.sleep(1)
        else:
            await interaction.response.send_message(f"找不到歌曲 {random_song}",
                                                    ephemeral=True)

@bot.tree.command(name="歌單", description="歌曲清單")
async def 歌單(interaction: discord.Interaction):
    song_list_message = "可用的歌曲清單：\n"
    for number, song_name in song_list.items():
        song_list_message += f"{number}: {song_name}\n"
    embed = discord.Embed(title="歌曲清單",
                          description=song_list_message,
                          color=discord.Color.gold())
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="入道", description="開始你的修煉之旅！")
async def 入道(interaction: discord.Interaction):
    user_id = interaction.user.id

    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    existing_user = cursor.fetchone()

    if existing_user:
        await interaction.response.send_message("你已經是修煉者，無需再次入道。")
    else:
        cursor.execute(
            """INSERT INTO users (user_id, spirit_stone, level, layer, body_level, body_layer, attack, health, defense, cultivation, quench) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, 0, '凡人', '一層', '凡人肉體', '一階', 20, 100, 10, 0, 0)
        )
        conn.commit()
        await interaction.response.send_message("歡迎您踏入修仙之旅，請試著摸索其他指令")

@bot.tree.command(name="感悟", description="每日簽到，獲得靈石獎勵！")
async def 感悟(interaction: discord.Interaction):
    user_id = interaction.user.id
    today = str(datetime.date.today())

    cursor.execute(
        "SELECT last_checkin, spirit_stone FROM users WHERE user_id=?",
        (user_id, ))
    result = cursor.fetchone()

    if not result:
        await interaction.response.send_message("您還不是修煉者，請先使用【入道】指令。", ephemeral=True)
        return

    last_checkin, spirit_stone = result

    if last_checkin == today:
        await interaction.response.send_message("今天已經感悟過了，請明天再來！", ephemeral=True)
    else:
        new_spirit_stone = spirit_stone + 100
        cursor.execute(
            "UPDATE users SET spirit_stone=?, last_checkin=? WHERE user_id=?",
            (new_spirit_stone, today, user_id))
        conn.commit()
        await interaction.response.send_message(
            f"感悟成功！你的靈石數量增加了，目前靈石：{new_spirit_stone}", ephemeral=True)

@bot.tree.command(name="占卜", description="每日占卜，獲得靈石獎勵！")
async def 占卜(interaction: discord.Interaction):
    user_id = interaction.user.id
    today = str(datetime.date.today())

    cursor.execute("SELECT last_draw, spirit_stone FROM users WHERE user_id=?",
                   (user_id, ))
    result = cursor.fetchone()

    if not result:
        await interaction.response.send_message("您還不是修煉者，請先使用【入道】指令。", ephemeral=True)
        return

    last_draw, spirit_stone = result

    if last_draw == today:
        await interaction.response.send_message("你今天已經占卜過了，請明天再來。", ephemeral=True)
    else:
        fortune = [
            '上籤', '上上籤', '上中籤', '上平籤', '上下籤', '大吉籤', '上吉籤', '中吉籤', '下吉籤', '中籤',
            '中上籤', '中平籤', '中中籤', '中下籤', '下籤', '下上籤', '下中籤', '下下籤', '下兇籤', '不吉籤'
        ]
        prob = [1] * len(fortune)
        drawn_fortune = random.choices(fortune, weights=prob)[0]
        rewards = {
            '上籤': 400,
            '上上籤': 200,
            '上中籤': 190,
            '上平籤': 180,
            '上下籤': 170,
            '大吉籤': 160,
            '上吉籤': 150,
            '中吉籤': 140,
            '下吉籤': 130,
            '中籤': 120,
            '中上籤': 110,
            '中平籤': 100,
            '中中籤': 90,
            '中下籤': 80,
            '下籤': 70,
            '下上籤': 60,
            '下中籤': 50,
            '下下籤': 40,
            '下兇籤': 30,
            '不吉籤': 20
        }
        reward = rewards.get(drawn_fortune, 0)
        spirit_stone += reward

        cursor.execute(
            "UPDATE users SET last_draw=?, spirit_stone=? WHERE user_id=?",
            (today, spirit_stone, user_id))
        conn.commit()

        embed = discord.Embed(
            title=f"你抽到了「{drawn_fortune}」!",
            description=f"獲得了獎勵：{reward}靈石。\n目前靈石：{spirit_stone}",
            color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="靈石", description="查看你當前的靈石數量。")
async def 靈石(interaction: discord.Interaction):
    user_id = interaction.user.id

    cursor.execute("SELECT spirit_stone FROM users WHERE user_id=?",
                   (user_id, ))
    result = cursor.fetchone()

    if not result:
        await interaction.response.send_message("您還不是修煉者，請先使用【入道】指令。", ephemeral=True)
    else:
        spirit_stone = result[0]
        await interaction.response.send_message(f"你目前持有的靈石數量：{spirit_stone}", ephemeral=True)

@bot.command()
async def 修改靈石(ctx, user: discord.User, 靈石: int):
    if ctx.author.id != IMMORTAL_KING_ID:
        await ctx.send("世界基礎規則，凡人無法撼動。", ephemeral=True)
        return

    user_id = user.id

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id, ))
    users = cursor.fetchone()

    if users is None:
        await ctx.send("您還不是修煉者，請先使用【入道】指令。", ephemeral=True)
        return

    cursor.execute("UPDATE users SET spirit_stone=? WHERE user_id=?",
                   (靈石, user_id))
    conn.commit()

    await ctx.send(f"用戶 {user.mention} 的靈石數量已更新。", ephemeral=True)

@bot.command()
async def 查看修煉者資料(ctx):
    if ctx.author.id != IMMORTAL_KING_ID:
        await ctx.send("世界基礎規則，凡人無法撼動。", ephemeral=True)
        return

    cursor.execute("SELECT user_id, spirit_stone, level, layer FROM users")
    users = cursor.fetchall()

    users_table = "```\n"
    users_table += f"{'用户ID': <20}{'靈石': <10}{'境界': <10}{'層數': <10}\n"
    for data in users:
        user_id, spirit_stone, level, layer = data
        users_table += f"{str(user_id): <20}{str(spirit_stone): <10}{str(level): <10}{str(layer): <10}\n"
    users_table += "```"

    await ctx.send(f"修練者資料總表：\n{users_table}", ephemeral=True)

@bot.tree.command(name="渡劫", description="突破境界！")
async def 渡劫(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id in command_lock and command_lock[user_id]:
        await interaction.response.send_message("請等待當前指令執行完畢後再使用。",
                                                ephemeral=True)
        return

    command_lock[user_id] = True

    cursor.execute(
        "SELECT cultivation, level, layer, attack, health, defense FROM users WHERE user_id=?",
        (user_id, ))
    result = cursor.fetchone()
    if result:
        cultivation, level, layer, attack, health, defense = result
    else:
        await interaction.response.send_message("您還不是修煉者，請先使用【入道】指令。",
                                                ephemeral=True)
        return

    breakthrough_conditions = nirvana_costs.get(level, None)

    if not breakthrough_conditions:
        await interaction.response.send_message("您已達到最高境界，無法再升級。",
                                                ephemeral=True)
    else:
        current_layer = layer if layer in breakthrough_conditions else "一層"

        if current_layer != "大圓滿":
            current_cultivation = cultivation
            required_cultivation = breakthrough_conditions[current_layer]

            if current_cultivation >= required_cultivation:
                new_cultivation = current_cultivation - required_cultivation
                new_layer = list(breakthrough_conditions.keys())[
                    list(breakthrough_conditions).index(current_layer) + 1]
                new_attack = attack + 10
                new_health = health + 55
                new_defense = defense + 3
                cursor.execute(
                    "UPDATE users SET cultivation=?, layer=?, attack=?, health=?, defense=? WHERE user_id=?",
                    (new_cultivation, new_layer, new_attack, new_health,
                     new_defense, user_id))
                conn.commit()
                text = discord.Embed(
                    title="恭喜您成功渡劫！",
                    description=
                    f"您的境界提升到了 {level} {new_layer}。\n⚔️攻擊 : {attack} ➟ {new_attack}\n🛡️防禦 : {defense} ➟ {new_defense}\n🩸氣血 : {health} ➟ {new_health}",
                    color=discord.Color.blue()
                )
                await interaction.response.send_message(embed=text, ephemeral=True)
            else:
                await interaction.response.send_message(
                    f"您的修為不足以渡劫到下一層。所需修為：{required_cultivation}，您的修為：{current_cultivation}",
                    ephemeral=True)
        else:
            next_level_index = list(nirvana_costs.keys()).index(level) + 1
            if next_level_index < len(nirvana_costs):
                next_level = list(nirvana_costs.keys())[next_level_index]
                next_layer = "一層"
                required_cultivation = nirvana_costs[next_level][next_layer]

                if cultivation >= required_cultivation:
                    new_cultivation = cultivation - required_cultivation
                    new_attack = attack + 20
                    new_health = health + 100
                    new_defense = defense + 6
                    cursor.execute(
                        "UPDATE users SET cultivation=?, level=?, layer=?, attack=?, health=?, defense=? WHERE user_id=?",
                        (new_cultivation, next_level, next_layer, new_attack,
                         new_health, new_defense, user_id))
                    conn.commit()
                    text = discord.Embed(
                        title="恭喜您成功渡劫！",
                        description=
                        f"您的境界提升到了 {next_level} {next_layer}。\n⚔️攻擊 : {attack} ➟ {new_attack}\n🛡️防禦 : {defense} ➟ {new_defense}\n🩸氣血 : {health} ➟ {new_health}",
                        color=discord.Color.blue(),
                    )
                    await interaction.response.send_message(embed=text, ephemeral=True)
                else:
                    await interaction.response.send_message(
                        f"您的修為不足以渡劫到下一境界的第一層。所需修為：{required_cultivation}，您的修為：{cultivation}",
                        ephemeral=True)
            else:
                await interaction.response.send_message("您已達到最高境界，無法再升級。",
                                                        ephemeral=True)

    command_lock[user_id] = False

@bot.tree.command(name="煉體", description="淬鍊肉身！")
async def 煉體(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id in command_lock and command_lock[user_id]:
        await interaction.response.send_message("請等待當前指令執行完畢後再使用。",
                                                ephemeral=True)
        return

    command_lock[user_id] = True

    cursor.execute(
        "SELECT quench, body_level, body_layer, attack, health, defense FROM users WHERE user_id=?",
        (user_id, ))
    result = cursor.fetchone()
    if result:
        quench, body_level, body_layer, attack, health, defense = result
    else:
        await interaction.response.send_message("您還不是修煉者，請先使用【入道】指令。",
                                                ephemeral=True)
        return

    breakthrough_conditions2 = body_training_costs.get(body_level, None)

    if not breakthrough_conditions2:
        await interaction.response.send_message("您已達到最高煉體境界，無法再升級。",
                                                ephemeral=True)
    else:
        current_body_layer = body_layer if body_layer in breakthrough_conditions2 else "一階"

        if current_body_layer != "大圓滿":
            current_quench = quench
            required_quench = breakthrough_conditions2[current_body_layer]

            if current_quench >= required_quench:
                new_quench = current_quench - required_quench
                new_body_layer = list(breakthrough_conditions2.keys())[
                    list(breakthrough_conditions2).index(current_body_layer) +
                    1]
                new_attack = attack + 4
                new_health = health + 200
                new_defense = defense + 6
                cursor.execute(
                    "UPDATE users SET quench=?, body_layer=?, attack=?, health=?, defense=? WHERE user_id=?",
                    (new_quench, new_body_layer, new_attack, new_health,
                     new_defense, user_id))
                conn.commit()
                text = discord.Embed(
                    title="恭喜您成功淬煉！",
                    description=
                    f"您的煉體境界提升到了 {body_level} {new_body_layer}。\n⚔️攻擊 : {attack} ➟ {new_attack}\n🛡️防禦 : {defense} ➟ {new_defense}\n🩸氣血 : {health} ➟ {new_health}",
                    color=discord.Color.blue(),
                )
                await interaction.response.send_message(embed=text, ephemeral=True)
            else:
                await interaction.response.send_message(
                    f"您的精華不足以淬煉到下一階。所需精華：{required_quench}，您的精華：{current_quench}",
                    ephemeral=True)
        else:
            next_body_level_index = list(
                body_training_costs.keys()).index(body_level) + 1
            if next_body_level_index < len(body_training_costs):
                next_body_level = list(
                    body_training_costs.keys())[next_body_level_index]
                next_body_layer = "一階"
                required_quench = body_training_costs[next_body_level][
                    next_body_layer]

                if quench >= required_quench:
                    new_quench = quench - required_quench
                    new_attack = attack + 10
                    new_health = health + 400
                    new_defense = defense + 9
                    cursor.execute(
                        "UPDATE users SET quench=?, body_level=?, body_layer=?, attack=?, health=?, defense=? WHERE user_id=?",
                        (new_quench, next_body_level, next_body_layer,
                         new_attack, new_health, new_defense, user_id))
                    conn.commit()
                    text = discord.Embed(
                        title="恭喜您成功淬煉！",
                        description=
                        f"您的煉體境界提升到了 {next_body_level} {next_body_layer}。\n⚔️攻擊 : {attack} ➟ {new_attack}\n🛡️防禦 : {defense} ➟ {new_defense}\n🩸氣血 : {health} ➟ {new_health}",
                        color=discord.Color.blue(),
                    )
                    await interaction.response.send_message(embed=text, ephemeral=True)
                else:
                    await interaction.response.send_message(
                        f"您的精華不足以淬煉到下一期的第一階。所需精華：{required_quench}，您的精華：{quench}",
                        ephemeral=True)
            else:
                await interaction.response.send_message("您已達到最高煉體境界，無法再淬煉。",
                                                        ephemeral=True)

    command_lock[user_id] = False

@bot.command()
async def 修為(ctx, member: discord.Member, amount: int):
    if ctx.author.id == IMMORTAL_KING_ID:
        user_id = member.id

        cursor.execute("SELECT cultivation FROM users WHERE user_id=?",
                       (user_id, ))
        user_cultivation = cursor.fetchone()

        if user_cultivation is None:
            await ctx.send("您還不是修煉者，請先使用【入道】指令。", ephemeral=True)
            return

        cursor.execute("UPDATE users SET cultivation=? WHERE user_id=?",
                       (amount, user_id))
        conn.commit()
        await ctx.send(f"成功設定 {member.mention} 的修為為：{amount}", ephemeral=True)
    else:
        await ctx.send("世界基礎規則，凡人無法撼動。", ephemeral=True)

@bot.command()
async def 精華(ctx, member: discord.Member, amount: int):
    if ctx.author.id == IMMORTAL_KING_ID:
        user_id = member.id

        cursor.execute("SELECT quench FROM users WHERE user_id=?", (user_id, ))
        user_quench = cursor.fetchone()

        if user_quench is None:
            await ctx.send("您還不是修煉者，請先使用【入道】指令。", ephemeral=True)
            return

        cursor.execute("UPDATE users SET quench=? WHERE user_id=?",
                       (amount, user_id))
        conn.commit()
        await ctx.send(f"成功設定 {member.mention} 的精華為：{amount}", ephemeral=True)
    else:
        await ctx.send("世界基礎規則，凡人無法撼動。", ephemeral=True)

@bot.tree.command(name="查看修為", description="查看你的修練者詳細資料")
async def 查看修為(interaction: discord.Interaction):
    user_id = interaction.user.id

    cursor.execute(
        "SELECT level, layer, body_level, body_layer, cultivation, quench, attack, defense, health, current_health, spirit_stone FROM users WHERE user_id=?",
        (user_id, ))
    user_info = cursor.fetchone()

    if not user_info:
        await interaction.response.send_message("您還不是修煉者，請先使用【入道】指令。",
                                                ephemeral=True)
        return

    current_level, current_layer, current_body_level, current_body_layer, cultivation, quench, attack, defense, health, current_health, spirit_stone = user_info

    required_cultivation = nirvana_costs.get(current_level,
                                             {}).get(current_layer, "基礎數值未定義")

    required_quench = body_training_costs.get(current_body_level,
                                              {}).get(current_body_layer,
                                                      "基礎數值未定義")

    資料 = discord.Embed(title="修練者資料",
                       description="以下是您的資料：",
                       color=discord.Color.orange())
    資料.add_field(name="修為：", value=f"{cultivation}", inline=True)
    資料.add_field(name="境界 : ", value=f"{current_level}", inline=True)
    資料.add_field(name="層數 : ", value=f"{current_layer}", inline=True)
    資料.add_field(name="當前境界所需修為 : ",
                 value=f"{required_cultivation}",
                 inline=True)
    資料.add_field(name="精華：", value=f"{quench}", inline=True)
    資料.add_field(name="煉體 : ", value=f"{current_body_level}", inline=True)
    資料.add_field(name="階級 : ", value=f"{current_body_layer}", inline=True)
    資料.add_field(name="當前煉體階級所需精華：", value=f"{required_quench}", inline=True)
    資料.add_field(name="攻擊 : ", value=f"{attack}", inline=True)
    資料.add_field(name="防禦 : ", value=f"{defense}", inline=True)
    資料.add_field(name="氣血上限/當前氣血 : ",
                 value=f"{health}/{current_health}",
                 inline=True)
    資料.add_field(name="靈石 : ", value=f"{spirit_stone}", inline=True)

    await interaction.response.send_message(embed=資料, ephemeral=True)


class BattleView(discord.ui.View):

    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id
    
    async def battle_action(self, interaction, action):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("這不是你的戰鬥，無法操作！", ephemeral=True)
            return
    
        if action == "attack":
            await self.attack(interaction)
        elif action == "use_item":
            await self.use_item(interaction)
        elif action == "flee":
            await self.flee(interaction)
    
    @discord.ui.button(label="攻擊", style=discord.ButtonStyle.red)
    async def attack_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.battle_action(interaction, "attack")
    
    @discord.ui.button(label="使用道具", style=discord.ButtonStyle.green)
    async def use_item_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.battle_action(interaction, "use_item")
    
    @discord.ui.button(label="逃跑", style=discord.ButtonStyle.gray)
    async def flee_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.battle_action(interaction, "flee")

    async def attack(self, interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("這不是你的戰鬥，無法操作！",
                                                    ephemeral=True)
            return

        user_id = interaction.user.id

        if user_id not in battle_states:
            await interaction.response.send_message(
                "你現在沒有在戰鬥中！請使用 `/挑戰` 開始戰鬥！", ephemeral=True)
            return

        state = battle_states[user_id]
        player = state["player"]
        enemy = state["enemy"]

        # 計算玩家對敵人的傷害
        damage_to_enemy = max(
            (player["attack"] + player.get("temp_attack", 0)) -
            enemy["defense"], 0)
        enemy["health"] -= damage_to_enemy

        if enemy["health"] <= 0:
            del battle_states[user_id]
            await interaction.response.send_message(
                f"你對 **{enemy['name']}** 造成了 {damage_to_enemy} 點傷害，並擊敗了它！獲得50顆靈石🎉",
                ephemeral=False
            )
            # 獎勵邏輯
            cursor.execute(
                "UPDATE users SET spirit_stone = spirit_stone + 50, temp_attack = 0, temp_defense = 0 WHERE user_id = ?",
                (user_id, ),
            )
            conn.commit()
            return

        # 計算敵人對玩家的反擊傷害
        damage_to_player = max(enemy["attack"] - player["defense"], 0)
        player["current_health"] -= damage_to_player

        if player["current_health"] <= 0:
            del battle_states[user_id]
            await interaction.response.send_message(
                f"你對 **{enemy['name']}** 造成了 {damage_to_enemy} 點傷害，但 **{enemy['name']}** 對你造成了 {damage_to_player} 點傷害，你被擊敗了！💀",ephemeral=False,
            )
            # 更新玩家數據（重置當前血量並清除臨時加成）
            cursor.execute(
                "UPDATE users SET current_health = health, temp_attack = 0, temp_defense = 0 WHERE user_id = ?",
                (user_id, ),
            )
            conn.commit()
            return

        # 回應戰鬥狀態
        await interaction.response.edit_message(
            content=(f"你對 **{enemy['name']}** 造成了 {damage_to_enemy} 點傷害！\n"
                     f"**{enemy['name']}** 的生命值剩餘：{enemy['health']}。\n\n"
                     f"**{enemy['name']}** 對你造成了 {damage_to_player} 點傷害！\n"
                     f"你的當前生命值剩餘：{player['current_health']}。"))

    async def use_item(self, interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("這不是你的戰鬥，無法操作！",
                                                    ephemeral=True)
            return

        # 確保用戶在戰鬥中
        user_id = interaction.user.id
        if user_id not in battle_states:
            await interaction.response.send_message("你現在沒有在戰鬥中！",
                                                    ephemeral=True)
            return

        # 查詢玩家擁有的道具
        cursor.execute(
            "SELECT item_name, quantity FROM inventory WHERE user_id = ? AND quantity > 0",
            (user_id, ),
        )
        inventory_items = cursor.fetchall()

        if not inventory_items:
            await interaction.response.send_message("你沒有任何可用的道具！",
                                                    ephemeral=True)
            return

        # 動態生成道具選單
        options = [
            discord.SelectOption(label=item[0],
                                 description=f"數量: {item[1]}",
                                 value=item[0]) for item in inventory_items
            if item[0] in items
        ]

        if not options:
            await interaction.response.send_message("你沒有任何有效的道具！",
                                                    ephemeral=True)
            return

        in_combat = True
        view = UseItemView(user_id, options, in_combat)
        await interaction.response.send_message("選擇你要使用的道具：",
                                                view=view,
                                                ephemeral=True)

    async def flee(self, interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("這不是你的戰鬥，無法操作！",
                                                    ephemeral=True)
            return

        user_id = interaction.user.id

        if user_id not in battle_states:
            await interaction.response.send_message("你現在沒有在戰鬥中！",
                                                    ephemeral=True)
            return

        del battle_states[user_id]
        cursor.execute(
            "UPDATE users SET temp_attack = 0, temp_defense = 0 WHERE user_id = ?",
            (user_id, ),
        )
        conn.commit()
        await interaction.response.send_message(content="你成功逃離了戰鬥！🏃‍♂️",
                                                view=None, ephemeral=True)

@bot.tree.command(name="挑戰", description="挑戰一個敵人！")
async def 挑戰(interaction: discord.Interaction):
    user_id = interaction.user.id

    if user_id not in battle_states:
        battle_states[user_id] = {}

    cursor.execute(
        "SELECT attack + temp_attack, defense + temp_defense, health, current_health FROM users WHERE user_id = ?",
        (user_id, ),
    )
    result = cursor.fetchone()

    if not result:
        await interaction.response.send_message("您還不是修煉者，請先使用【入道】指令。",
                                                ephemeral=True)
        return

    player_attack, player_defense, max_health, current_health = result
    player = {
        "attack": player_attack,
        "defense": player_defense,
        "health": max_health,
        "current_health": current_health,
    }

    enemy_name, enemy_stats = random.choice(list(enemies.items()))
    battle_states[user_id] = {
        "player": player,
        "enemy": {
            "name": enemy_name,
            **enemy_stats
        },
    }

    enemy = battle_states[user_id]["enemy"]
    view = BattleView(user_id)

    await interaction.response.send_message(
        f"你遇到了 **{enemy['name']}**！\n\n**屬性：**\n🩸 生命值：{enemy['health']}\n⚔️ 攻擊力：{enemy['attack']}\n🛡️ 防禦力：{enemy['defense']}",
        view=view, ephemeral=True
    )


class QuizView(discord.ui.View):

    def __init__(self, user_id, correct_answer_index):
        super().__init__(timeout=20)
        self.user_id = user_id
        self.correct_answer_index = correct_answer_index
        self.answer_selected = False

    @discord.ui.button(label="選項 1", style=discord.ButtonStyle.primary, row=0)
    async def option_1(self, interaction: discord.Interaction,
                       button: discord.ui.Button):
        await self.handle_answer(interaction, 0)

    @discord.ui.button(label="選項 2", style=discord.ButtonStyle.primary, row=0)
    async def option_2(self, interaction: discord.Interaction,
                       button: discord.ui.Button):
        await self.handle_answer(interaction, 1)

    @discord.ui.button(label="選項 3", style=discord.ButtonStyle.primary, row=1)
    async def option_3(self, interaction: discord.Interaction,
                       button: discord.ui.Button):
        await self.handle_answer(interaction, 2)

    @discord.ui.button(label="選項 4", style=discord.ButtonStyle.primary, row=1)
    async def option_4(self, interaction: discord.Interaction,
                       button: discord.ui.Button):
        await self.handle_answer(interaction, 3)

    async def handle_answer(self, interaction: discord.Interaction,
                            answer_index):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("這不是你的問答遊戲！",
                                                    ephemeral=True)
            return

        if self.answer_selected:
            await interaction.response.send_message("你已經回答過這個問題！",
                                                    ephemeral=True)
            return

        self.answer_selected = True

        if answer_index == self.correct_answer_index:
            await interaction.response.send_message(
                f"{interaction.user.mention} 回答正確！", ephemeral=True)
            cursor.execute(
                "UPDATE users SET correct_answers = correct_answers + 1 WHERE user_id = ?",
                (self.user_id, ))
            conn.commit()
        else:
            await interaction.response.send_message(
                f"{interaction.user.mention} 回答錯誤。", ephemeral=True)

        self.stop()


@bot.tree.command(name="問答遊戲", description="進行一場問答遊戲")
async def 問答遊戲(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id in command_lock and command_lock[user_id]:
        await interaction.response.send_message("請等待當前指令執行完畢後再使用。",
                                                ephemeral=True)
        return

    command_lock[user_id] = True

    try:
        selected_question = random.choice(question_pool)
        question = selected_question['question']
        options = selected_question['options']

        random.shuffle(options)
        correct_answer_index = options.index(
            selected_question['correct_answer'])

        view = QuizView(user_id, correct_answer_index)
        for i, option in enumerate(options):
            view.children[i].label = option

        await interaction.response.send_message(f"問答遊戲：\n\n{question}",
                                                view=view, ephemeral=True)

        await view.wait()

        if not view.answer_selected:
            await interaction.followup.send(
                f"{interaction.user.mention} 答題超時，請在時間內作答。", ephemeral=True)
    finally:
        command_lock[user_id] = False


def get_leaderboard():
    cursor.execute(
        "SELECT user_id, level, layer FROM users ORDER BY level DESC, layer ASC LIMIT 10"
    )
    leaderboard_data = cursor.fetchall()
    return leaderboard_data


def get_quiz_game_leaderboard():
    cursor.execute(
        "SELECT user_id, correct_answers FROM users WHERE correct_answers > 0 ORDER BY correct_answers DESC LIMIT 10"
    )
    leaderboard_data = cursor.fetchall()
    return leaderboard_data


@bot.tree.command(name="境界rank", description="查看境界排行榜")
async def 境界rank(interaction: discord.Interaction):
    leaderboard_data = get_leaderboard()

    if leaderboard_data:
        leaderboard_message = ""
        for index, (user_id, level, layer) in enumerate(leaderboard_data,
                                                        start=1):
            user = interaction.guild.get_member(user_id)
            if user:
                leaderboard_message += f"{index}. {user.display_name} - {level} {layer}\n"
            else:
                leaderboard_message += f"{index}. UserID: {user_id} - {level} {layer}\n"

        embed = discord.Embed(title="境界排行榜 :",
                              description=leaderboard_message,
                              color=discord.Color.gold())
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message("暫無排行榜數據。", ephemeral=True)


@bot.tree.command(name="問答遊戲rank", description="查看問答遊戲的排行榜")
async def 問答遊戲rank(interaction: discord.Interaction):
    leaderboard_data = get_quiz_game_leaderboard()

    if leaderboard_data:
        leaderboard_message = ""
        for index, (user_id, correct_answers) in enumerate(leaderboard_data,
                                                           start=1):
            user = interaction.guild.get_member(user_id)
            if user:
                leaderboard_message += f"{index}. {user.display_name} - 答對次數：{correct_answers}\n"
            else:
                leaderboard_message += f"{index}. UserID: {user_id} - 答對次數：{correct_answers}\n"

        embed = discord.Embed(title="問答遊戲排行榜：",
                              description=leaderboard_message,
                              color=discord.Color.gold())
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message("暫無排行榜數據。", ephemeral=True)


@bot.tree.command(name="猜拳", description="參加猜拳遊戲，賺取或損失靈石！")
async def 猜拳(interaction: discord.Interaction):
    user_id = interaction.user.id

    if command_lock.get(user_id):
        await interaction.response.send_message("請等待當前指令執行完畢後再使用。",
                                                ephemeral=True)
        return

    command_lock[user_id] = True

    try:
        cursor.execute("SELECT spirit_stone FROM users WHERE user_id=?",
                       (user_id, ))
        result = cursor.fetchone()

        if not result:
            await interaction.response.send_message("請先使用/入道，獲取靈石",
                                                    ephemeral=True)
            return

        spirit_stone = result[0]

        if spirit_stone < 10:
            await interaction.response.send_message("請達到 10 靈石再來參加遊戲！",
                                                    ephemeral=True)
            return

        class GuessView(discord.ui.View):

            def __init__(self, user_id: int, spirit_stone: int):
                super().__init__(timeout=15)
                self.user_id = user_id
                self.spirit_stone = spirit_stone

            async def process_choice(self, interaction: discord.Interaction,
                                     player_choice: str):
                if interaction.user.id != self.user_id:
                    await interaction.response.send_message("這不是你的遊戲！",
                                                            ephemeral=True)
                    return

                bot_choice = random.choice(["✊", "✋", "✌️"])
                win_relations = {"✊": "✌️", "✋": "✊", "✌️": "✋"}

                if player_choice == bot_choice:
                    result_message = f"平局！你選擇了 {player_choice}，機器人選擇了 {bot_choice}。\n平局 ! 靈石數量不變。"
                elif win_relations[player_choice] == bot_choice:
                    self.spirit_stone += 10
                    result_message = f"你贏了！你選擇了 {player_choice}，機器人選擇了 {bot_choice}。\n靈石+10，你現在有 {self.spirit_stone} 靈石！"
                else:
                    self.spirit_stone -= 10
                    result_message = f"你輸了！你選擇了 {player_choice}，機器人選擇了 {bot_choice}。\n靈石-10，你現在有 {self.spirit_stone} 靈石！"

                cursor.execute(
                    "UPDATE users SET spirit_stone=? WHERE user_id=?",
                    (self.spirit_stone, self.user_id))
                conn.commit()

                await interaction.response.edit_message(content=result_message,
                                                        view=None, ephemeral=True)

            @discord.ui.button(label="石頭",
                               emoji="✊",
                               style=discord.ButtonStyle.primary)
            async def rock(self, interaction: discord.Interaction,
                           button: discord.ui.Button):
                await self.process_choice(interaction, "✊")

            @discord.ui.button(label="布",
                               emoji="✋",
                               style=discord.ButtonStyle.success)
            async def paper(self, interaction: discord.Interaction,
                            button: discord.ui.Button):
                await self.process_choice(interaction, "✋")

            @discord.ui.button(label="剪刀",
                               emoji="✌️",
                               style=discord.ButtonStyle.danger)
            async def scissors(self, interaction: discord.Interaction,
                               button: discord.ui.Button):
                await self.process_choice(interaction, "✌️")

        view = GuessView(user_id=user_id, spirit_stone=spirit_stone)
        await interaction.response.send_message("猜拳遊戲開始！請選擇你的拳頭：", view=view, ephemeral=True)

    except Exception as e:
        print(f"發生錯誤: {e}")
        await interaction.followup.send("發生錯誤，請稍後再試。", ephemeral=True)

    finally:
        command_lock[user_id] = False


@bot.tree.command(name="play1a2b", description="來挑戰 1A2B 遊戲，賺取靈石！")
async def play1a2b(interaction: discord.Interaction):
    user_id = interaction.user.id

    if command_lock.get(user_id):
        await interaction.response.send_message("請等待當前指令執行完畢後再使用。",
                                                ephemeral=True)
        return

    if interaction.channel.type != discord.ChannelType.private:
        await interaction.response.send_message("此指令僅在私訊中可用，請私訊機器人後再試！",
                                                ephemeral=True)
        return

    command_lock[user_id] = True

    try:
        cursor.execute("SELECT spirit_stone FROM users WHERE user_id=?",
                       (user_id, ))
        result = cursor.fetchone()

        if not result:
            await interaction.response.send_message("請另尋財路，找不到你的帳戶。",
                                                    ephemeral=True)
            return

        spirit_stone = result[0]
        if spirit_stone < 10:
            await interaction.response.send_message(
                "你的靈石不足以參加遊戲，請確保有至少 10 靈石！", ephemeral=True)
            return

        answer = random.sample(range(1, 10), 4)
        a, b, attempts = 0, 0, 0

        await interaction.response.send_message(
            "1A2B 遊戲開始！請輸入一個不重複的四位數字（每次限時 60 秒）。", ephemeral=True)

        def check_guess(message: discord.Message):
            return (message.author == interaction.user
                    and message.channel == interaction.channel
                    and len(message.content) == 4
                    and message.content.isdigit()
                    and len(set(message.content)) == 4)

        while a != 4:
            try:
                guess_message = await bot.wait_for("message",
                                                   timeout=60,
                                                   check=check_guess)
                user_guess = list(map(int, guess_message.content))
                attempts += 1
                a, b = 0, 0

                for i in range(4):
                    if user_guess[i] == answer[i]:
                        a += 1
                    elif user_guess[i] in answer:
                        b += 1

                await interaction.followup.send(f"{a}A{b}B", ephemeral=True)

            except asyncio.TimeoutError:
                await interaction.followup.send("操作超時，遊戲結束。", ephemeral=True)
                command_lock[user_id] = False
                return

        new_spirit_stone = spirit_stone + 10
        cursor.execute("UPDATE users SET spirit_stone=? WHERE user_id=?",
                       (new_spirit_stone, user_id))
        conn.commit()

        await interaction.followup.send(
            f"恭喜你答對了！答案是 {''.join(map(str, answer))}，總共猜了 {attempts} 次。\n靈石 +10，你現在有 {new_spirit_stone} 靈石！",
            ephemeral=True,
        )

    except Exception as e:
        print(f"發生錯誤: {e}")
        await interaction.followup.send("發生錯誤，請稍後再試。", ephemeral=True)

    finally:
        command_lock[user_id] = False

if __name__ == "__main__":
    keep_alive()
    TOKEN = os.getenv("DISCORD_TOKEN")
    bot.run(TOKEN)
